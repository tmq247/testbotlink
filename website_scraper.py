"""
Website scraping module for fetching and processing web content.
Handles HTTP requests, user agents, and content extraction.
"""

import logging
import asyncio
import aiohttp
import ssl
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import random

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Handles web scraping operations for movie websites."""
    
    def __init__(self):
        # Common user agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        # Request timeout settings
        self.timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        # SSL context for handling certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def get_page_content(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Fetch page content from URL.
        
        Args:
            url: The URL to fetch
            headers: Optional custom headers
            
        Returns:
            Page content as string or None if failed
        """
        try:
            # Prepare headers
            request_headers = self._get_default_headers()
            if headers:
                request_headers.update(headers)
            
            # Create session with custom settings
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=10,
                limit_per_host=5
            )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers
            ) as session:
                
                # Make request with retries
                content = await self._fetch_with_retries(session, url)
                return content
                
        except Exception as e:
            logger.error(f"Error fetching page content from {url}: {str(e)}")
            return None
    
    async def _fetch_with_retries(self, session: aiohttp.ClientSession, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch URL with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                async with session.get(url, allow_redirects=True) as response:
                    # Check if response is successful
                    if response.status == 200:
                        content = await response.text(encoding='utf-8', errors='ignore')
                        logger.info(f"Successfully fetched {len(content)} characters from {url}")
                        return content
                    
                    elif response.status == 403:
                        logger.warning(f"Access forbidden for {url}, trying with different headers")
                        # Try with different user agent
                        session.headers['User-Agent'] = random.choice(self.user_agents)
                        continue
                    
                    elif response.status == 429:
                        logger.warning(f"Rate limited for {url}, waiting before retry")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        if attempt == max_retries - 1:
                            return None
                        continue
                        
            except aiohttp.ClientError as e:
                last_exception = e
                logger.warning(f"Request failed for {url} (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Progressive delay
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                break
        
        logger.error(f"Failed to fetch {url} after {max_retries} attempts. Last error: {last_exception}")
        return None
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers for requests."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
    
    async def get_json_data(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch JSON data from URL.
        
        Args:
            url: The API endpoint URL
            headers: Optional custom headers
            
        Returns:
            JSON data as dictionary or None if failed
        """
        try:
            request_headers = self._get_default_headers()
            request_headers['Accept'] = 'application/json, text/plain, */*'
            
            if headers:
                request_headers.update(headers)
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers
            ) as session:
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched JSON data from {url}")
                        return data
                    else:
                        logger.warning(f"HTTP {response.status} when fetching JSON from {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching JSON from {url}: {str(e)}")
            return None
    
    async def post_data(self, url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Send POST request with data.
        
        Args:
            url: The URL to post to
            data: Data to send in POST body
            headers: Optional custom headers
            
        Returns:
            Response content or None if failed
        """
        try:
            request_headers = self._get_default_headers()
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            if headers:
                request_headers.update(headers)
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers
            ) as session:
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully posted data to {url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} when posting to {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error posting to {url}: {str(e)}")
            return None
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    def is_valid_video_url(self, url: str) -> bool:
        """Check if URL appears to be a valid video URL."""
        try:
            parsed = urlparse(url)
            
            # Must have valid scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for video-like patterns
            url_lower = url.lower()
            video_indicators = [
                '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
                '.m3u8', '.mpd', '.f4m',
                'stream', 'video', 'play', 'hls', 'dash'
            ]
            
            return any(indicator in url_lower for indicator in video_indicators)
            
        except Exception:
            return False
