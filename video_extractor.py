import re
import asyncio
import aiohttp
import logging
import trafilatura
from typing import List, Optional, Dict
from urllib.parse import urljoin, urlparse
from config import SUPPORTED_DOMAINS, VIDEO_EXTENSIONS, USER_AGENT, REQUEST_TIMEOUT, MAX_RETRIES
from utils import extract_domain, extract_video_info

logger = logging.getLogger(__name__)

class VideoExtractor:
    """
    Extract video links from Vietnamese movie websites.
    """
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def is_supported_domain(self, url: str) -> bool:
        """
        Check if the domain is supported.
        """
        domain = extract_domain(url)
        if not domain:
            return False
        
        return any(supported in domain for supported in SUPPORTED_DOMAINS)
    
    async def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch page content with retries.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully fetched content from {url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
            
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def extract_video_links_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract video links from HTML content.
        """
        video_links = []
        
        # Common patterns for video links in Vietnamese movie sites
        patterns = [
            # Direct video file links
            r'(?:src|href|data-src|data-href)=["\']([^"\']*\.(?:mp4|m3u8|mkv|avi|mov|webm)[^"\']*)["\']',
            
            # M3U8 playlist links
            r'(?:src|href|data-src|data-href)=["\']([^"\']*\.m3u8[^"\']*)["\']',
            
            # Video streaming URLs
            r'(?:src|href|data-src|data-href)=["\']([^"\']*(?:stream|video|play)[^"\']*\.(?:mp4|m3u8)[^"\']*)["\']',
            
            # JavaScript variable assignments with video URLs
            r'(?:videoUrl|video_url|streamUrl|stream_url|playUrl|play_url)\s*[:=]\s*["\']([^"\']+\.(?:mp4|m3u8|mkv))["\']',
            
            # Common Vietnamese movie site patterns
            r'["\']([^"\']*(?:googleapis|googleusercontent|drive\.google|mega\.nz|fshare|4shared)[^"\']*\.(?:mp4|m3u8|mkv))["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                # Clean and validate the URL
                if match.startswith('//'):
                    match = 'https:' + match
                elif match.startswith('/'):
                    match = urljoin(base_url, match)
                elif not match.startswith('http'):
                    match = urljoin(base_url, match)
                
                # Check if it's a valid video URL
                if self.is_valid_video_url(match):
                    video_links.append(match)
        
        # Use trafilatura to extract clean text and look for video URLs
        try:
            clean_text = trafilatura.extract(html)
            if clean_text:
                # Look for URLs in clean text
                url_pattern = r'https?://[^\s<>"\']+\.(?:mp4|m3u8|mkv|avi|mov|webm)'
                text_urls = re.findall(url_pattern, clean_text, re.IGNORECASE)
                for url in text_urls:
                    if self.is_valid_video_url(url):
                        video_links.append(url)
        except Exception as e:
            logger.error(f"Error using trafilatura: {e}")
        
        # Remove duplicates while preserving order
        unique_links = []
        seen = set()
        for link in video_links:
            if link not in seen:
                unique_links.append(link)
                seen.add(link)
        
        return unique_links
    
    def is_valid_video_url(self, url: str) -> bool:
        """
        Check if URL is a valid video URL.
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check if URL ends with video extension
            path_lower = parsed.path.lower()
            for ext in VIDEO_EXTENSIONS:
                if ext in path_lower:
                    return True
            
            # Check for streaming services patterns
            streaming_patterns = [
                r'stream',
                r'video',
                r'play',
                r'embed',
                r'watch'
            ]
            
            url_lower = url.lower()
            for pattern in streaming_patterns:
                if pattern in url_lower and any(ext in url_lower for ext in VIDEO_EXTENSIONS):
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def extract_videos(self, url: str) -> List[Dict]:
        """
        Extract video links from a Vietnamese movie website.
        """
        if not self.is_supported_domain(url):
            logger.warning(f"Unsupported domain: {extract_domain(url)}")
            return []
        
        html_content = await self.fetch_page_content(url)
        if not html_content:
            logger.error(f"Could not fetch content from {url}")
            return []
        
        video_links = self.extract_video_links_from_html(html_content, url)
        
        # Process video links to extract info
        videos = []
        for link in video_links:
            try:
                video_info = extract_video_info(link)
                videos.append(video_info)
                logger.info(f"Found video: {video_info['filename']} ({video_info['quality']})")
            except Exception as e:
                logger.error(f"Error processing video link {link}: {e}")
        
        return videos
    
    async def get_video_file_size(self, url: str) -> Optional[int]:
        """
        Get video file size by making a HEAD request.
        """
        try:
            async with self.session.head(url) as response:
                if response.status == 200:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        return int(content_length)
        except Exception as e:
            logger.error(f"Error getting file size for {url}: {e}")
        
        return None
