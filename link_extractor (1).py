"""
Video link extraction module for finding streaming links from movie websites.
Supports various video formats including m3u8, mp4, and embedded players.
"""

import logging
import re
import json
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from website_scraper import WebsiteScraper
from config import MAX_LINKS_PER_PAGE, VIDEO_EXTENSIONS, STREAMING_EXTENSIONS
from security import validate_video_url
from utils import extract_video_info_from_url, validate_video_link_quality

logger = logging.getLogger(__name__)


class VideoLinkExtractor:
    """Extracts video streaming links from movie websites."""
    
    def __init__(self):
        self.scraper = WebsiteScraper()
        
        # Common video file extensions
        self.video_extensions = VIDEO_EXTENSIONS
        
        # Streaming formats
        self.streaming_formats = STREAMING_EXTENSIONS
        
        # Quality indicators
        self.quality_patterns = {
            '4K': r'(4k|2160p|uhd|ultra.*hd)',
            '1080p': r'(1080p|fullhd|fhd|full.*hd)',
            '720p': r'(720p|hd|high.*def)',
            '480p': r'(480p|sd|standard.*def)',
            '360p': r'(360p|low.*quality)',
            '240p': r'(240p|very.*low)'
        }
        
        # Enhanced patterns for better detection
        self.advanced_patterns = {
            'jwplayer': r'jwplayer\([^)]*\)\.setup\(\s*\{([^}]+)\}\s*\)',
            'flowplayer': r'flowplayer\([^)]*\,\s*\{([^}]+)\}\s*\)',
            'videojs': r'videojs\([^)]*\)\.src\(\s*([^)]+)\s*\)',
            'plyr': r'new\s+Plyr\([^)]*\,\s*\{([^}]+)\}\s*\)',
            'dplayer': r'new\s+DPlayer\(\s*\{([^}]+)\}\s*\)'
        }
    
    async def extract_video_links(self, url: str) -> List[Dict[str, str]]:
        """
        Extract video links from a movie website URL.
        
        Args:
            url: The episode/movie page URL
            
        Returns:
            List of dictionaries containing video link information
        """
        try:
            logger.info(f"Extracting video links from: {url}")
            
            # Get page content
            page_content = await self.scraper.get_page_content(url)
            
            if not page_content:
                logger.warning(f"No content retrieved from {url}")
                return []
            
            # Extract links using multiple methods
            links = []
            
            # Method 1: Direct video links in HTML
            direct_links = self._extract_direct_video_links(page_content, url)
            links.extend(direct_links)
            
            # Method 2: JavaScript embedded links
            js_links = self._extract_javascript_links(page_content, url)
            links.extend(js_links)
            
            # Method 3: Advanced player detection
            player_links = self._extract_player_links(page_content, url)
            links.extend(player_links)
            
            # Method 4: JSON/API endpoints
            api_links = self._extract_api_links(page_content, url)
            links.extend(api_links)
            
            # Method 5: iframe sources
            iframe_links = await self._extract_iframe_links(page_content, url)
            links.extend(iframe_links)
            
            # Method 6: Meta tags and link tags
            meta_links = self._extract_meta_links(page_content, url)
            links.extend(meta_links)
            
            # Remove duplicates and validate links
            unique_links = self._remove_duplicates(links)
            validated_links = self._validate_links(unique_links)
            
            # Sort by quality and limit results
            sorted_links = validate_video_link_quality(validated_links)
            final_links = sorted_links[:MAX_LINKS_PER_PAGE]
            
            logger.info(f"Found {len(final_links)} valid video links")
            return final_links
            
        except Exception as e:
            logger.error(f"Error extracting video links: {str(e)}")
            return []
    
    def _extract_direct_video_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract direct video links from HTML content."""
        links = []
        
        # Enhanced patterns for video sources
        video_patterns = [
            r'<video[^>]*src=["\']([^"\']+)["\']',
            r'<source[^>]*src=["\']([^"\']+)["\']',
            r'src=["\']([^"\']*\.(?:' + '|'.join(self.video_extensions + self.streaming_formats) + ')(?:\?[^"\']*)?)["\']',
            r'data-src=["\']([^"\']*\.(?:' + '|'.join(self.video_extensions + self.streaming_formats) + ')(?:\?[^"\']*)?)["\']',
            r'data-video=["\']([^"\']+)["\']',
            r'data-file=["\']([^"\']+)["\']'
        ]
        
        for pattern in video_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                video_url = match.group(1)
                full_url = urljoin(base_url, video_url)
                
                if self._is_likely_video_url(video_url):
                    link_info = {
                        'url': full_url,
                        'type': self._detect_link_type(full_url),
                        'quality': self._detect_quality(video_url),
                        'source': 'direct_html'
                    }
                    links.append(link_info)
        
        return links
    
    def _extract_javascript_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract video links from JavaScript code."""
        links = []
        
        # Enhanced JS patterns for video URLs
        js_patterns = [
            r'["\']([^"\']*\.(?:' + '|'.join(self.video_extensions + self.streaming_formats) + ')(?:\?[^"\']*)?)["\']',
            r'(?:url|src|file|source|video)\s*[:=]\s*["\']([^"\']+)["\']',
            r'(?:hls|dash|mp4|webm|mkv)\s*[:=]\s*["\']([^"\']+)["\']',
            r'playlist\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'manifest\s*[:=]\s*["\']([^"\']+\.mpd[^"\']*)["\']'
        ]
        
        # Look for script tags
        script_matches = re.finditer(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
        
        for script_match in script_matches:
            script_content = script_match.group(1)
            
            for pattern in js_patterns:
                matches = re.finditer(pattern, script_content, re.IGNORECASE)
                for match in matches:
                    video_url = match.group(1)
                    
                    # Filter out obviously non-video URLs
                    if self._is_likely_video_url(video_url):
                        full_url = urljoin(base_url, video_url)
                        
                        link_info = {
                            'url': full_url,
                            'type': self._detect_link_type(full_url),
                            'quality': self._detect_quality(video_url),
                            'source': 'javascript'
                        }
                        links.append(link_info)
        
        return links
    
    def _extract_player_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract video links from popular video players."""
        links = []
        
        for player_name, pattern in self.advanced_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                config_content = match.group(1)
                
                # Extract URLs from player configuration
                url_patterns = [
                    r'["\']file["\']\s*:\s*["\']([^"\']+)["\']',
                    r'["\']src["\']\s*:\s*["\']([^"\']+)["\']',
                    r'["\']source["\']\s*:\s*["\']([^"\']+)["\']',
                    r'["\']url["\']\s*:\s*["\']([^"\']+)["\']'
                ]
                
                for url_pattern in url_patterns:
                    url_matches = re.finditer(url_pattern, config_content, re.IGNORECASE)
                    for url_match in url_matches:
                        video_url = url_match.group(1)
                        
                        if self._is_likely_video_url(video_url):
                            full_url = urljoin(base_url, video_url)
                            
                            link_info = {
                                'url': full_url,
                                'type': self._detect_link_type(full_url),
                                'quality': self._detect_quality(video_url),
                                'source': f'{player_name}_player'
                            }
                            links.append(link_info)
        
        return links
    
    def _extract_api_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract video links from JSON/API responses embedded in page."""
        links = []
        
        # Enhanced JSON patterns
        json_patterns = [
            r'(\{[^{}]*(?:"(?:url|src|file|source|video|hls|dash)"[^{}]*)+[^{}]*\})',
            r'(\[[^\[\]]*(?:"(?:url|src|file|source|video|hls|dash)"[^\[\]]*)+[^\[\]]*\])',
            r'var\s+\w+\s*=\s*(\{[^;]+\});',
            r'const\s+\w+\s*=\s*(\{[^;]+\});',
            r'let\s+\w+\s*=\s*(\{[^;]+\});'
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    json_str = match.group(1)
                    # Clean up JSON string
                    json_str = re.sub(r'[\r\n\t]', '', json_str)
                    json_str = re.sub(r'/\*.*?\*/', '', json_str)
                    json_str = re.sub(r'//.*', '', json_str)
                    
                    # Try to parse as JSON
                    data = json.loads(json_str)
                    
                    # Extract URLs from JSON structure
                    json_links = self._extract_urls_from_json(data, base_url)
                    links.extend(json_links)
                    
                except (json.JSONDecodeError, Exception):
                    # Not valid JSON, continue
                    continue
        
        return links
    
    def _extract_meta_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract video links from meta tags and link tags."""
        links = []
        
        # Meta tag patterns
        meta_patterns = [
            r'<meta[^>]*property=["\']og:video["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']twitter:player:stream["\'][^>]*content=["\']([^"\']+)["\']',
            r'<link[^>]*rel=["\']video_src["\'][^>]*href=["\']([^"\']+)["\']',
            r'<link[^>]*type=["\']video/[^"\']*["\'][^>]*href=["\']([^"\']+)["\']'
        ]
        
        for pattern in meta_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                video_url = match.group(1)
                
                if self._is_likely_video_url(video_url):
                    full_url = urljoin(base_url, video_url)
                    
                    link_info = {
                        'url': full_url,
                        'type': self._detect_link_type(full_url),
                        'quality': self._detect_quality(video_url),
                        'source': 'meta_tags'
                    }
                    links.append(link_info)
        
        return links
    
    async def _extract_iframe_links(self, content: str, base_url: str) -> List[Dict[str, str]]:
        """Extract video links from iframe sources."""
        links = []
        
        # Find iframe sources
        iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\']'
        iframe_matches = re.finditer(iframe_pattern, content, re.IGNORECASE)
        
        for match in iframe_matches:
            iframe_url = match.group(1)
            full_iframe_url = urljoin(base_url, iframe_url)
            
            # Skip non-video iframes
            if not self._is_likely_video_iframe(iframe_url):
                continue
            
            try:
                # Get iframe content with timeout
                iframe_content = await self.scraper.get_page_content(full_iframe_url)
                if iframe_content:
                    # Extract links from iframe using all methods
                    iframe_direct = self._extract_direct_video_links(iframe_content, full_iframe_url)
                    iframe_js = self._extract_javascript_links(iframe_content, full_iframe_url)
                    iframe_player = self._extract_player_links(iframe_content, full_iframe_url)
                    
                    # Mark as iframe source
                    all_iframe_links = iframe_direct + iframe_js + iframe_player
                    for link in all_iframe_links:
                        link['source'] = 'iframe'
                    
                    links.extend(all_iframe_links)
                    
            except Exception as e:
                logger.warning(f"Failed to process iframe {full_iframe_url}: {str(e)}")
        
        return links
    
    def _extract_urls_from_json(self, data, base_url: str) -> List[Dict[str, str]]:
        """Recursively extract URLs from JSON data structure."""
        links = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self._is_likely_video_url(value):
                    full_url = urljoin(base_url, value)
                    link_info = {
                        'url': full_url,
                        'type': self._detect_link_type(full_url),
                        'quality': self._detect_quality(value),
                        'source': f'json_{key}'
                    }
                    links.append(link_info)
                elif isinstance(value, (dict, list)):
                    links.extend(self._extract_urls_from_json(value, base_url))
                    
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and self._is_likely_video_url(item):
                    full_url = urljoin(base_url, item)
                    link_info = {
                        'url': full_url,
                        'type': self._detect_link_type(full_url),
                        'quality': self._detect_quality(item),
                        'source': 'json_array'
                    }
                    links.append(link_info)
                elif isinstance(item, (dict, list)):
                    links.extend(self._extract_urls_from_json(item, base_url))
        
        return links
    
    def _is_likely_video_url(self, url: str) -> bool:
        """Check if URL is likely a video link."""
        if not url or len(url) < 10:
            return False
        
        url_lower = url.lower()
        
        # Check for video extensions
        for ext in self.video_extensions + self.streaming_formats:
            if f'.{ext}' in url_lower:
                return True
        
        # Check for streaming keywords
        streaming_keywords = ['stream', 'video', 'play', 'hls', 'dash', 'cdn', 'media', 'mp4', 'm3u8']
        for keyword in streaming_keywords:
            if keyword in url_lower:
                return True
        
        # Exclude common non-video patterns
        exclude_patterns = [
            'css', 'js', 'json', 'xml', 'txt', 'html', 'php',
            'jpg', 'jpeg', 'png', 'gif', 'svg', 'ico', 'webp',
            'font', 'ttf', 'woff', 'eot',
            'api/track', 'analytics', 'ads', 'advertisement'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        return True
    
    def _is_likely_video_iframe(self, url: str) -> bool:
        """Check if iframe URL is likely to contain video."""
        url_lower = url.lower()
        
        # Common video iframe indicators
        video_indicators = [
            'player', 'embed', 'video', 'stream', 'play', 'watch',
            'movie', 'film', 'tv', 'episode', 'show'
        ]
        
        for indicator in video_indicators:
            if indicator in url_lower:
                return True
        
        # Exclude common non-video iframes
        exclude_indicators = [
            'ad', 'analytics', 'tracking', 'facebook', 'twitter',
            'comment', 'disqus', 'share', 'social'
        ]
        
        for indicator in exclude_indicators:
            if indicator in url_lower:
                return False
        
        return False
    
    def _detect_link_type(self, url: str) -> str:
        """Detect the type of video link."""
        url_lower = url.lower()
        
        if '.m3u8' in url_lower:
            return 'm3u8'
        elif '.mpd' in url_lower:
            return 'dash'
        elif '.f4m' in url_lower:
            return 'f4m'
        elif any(f'.{ext}' in url_lower for ext in self.video_extensions):
            # Detect specific video format
            for ext in self.video_extensions:
                if f'.{ext}' in url_lower:
                    return ext
            return 'video'
        else:
            return 'stream'
    
    def _detect_quality(self, url: str) -> str:
        """Detect video quality from URL."""
        url_lower = url.lower()
        
        for quality, pattern in self.quality_patterns.items():
            if re.search(pattern, url_lower, re.IGNORECASE):
                return quality
        
        return 'Không xác định'
    
    def _remove_duplicates(self, links: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate links based on URL."""
        seen_urls = set()
        unique_links = []
        
        for link in links:
            url = link.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_links.append(link)
        
        return unique_links
    
    def _validate_links(self, links: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate and filter video links."""
        valid_links = []
        
        for link in links:
            url = link.get('url', '')
            
            # Basic validation
            if not url or len(url) < 10:
                continue
            
            # Check if URL has valid scheme
            parsed = urlparse(url)
            if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                continue
            
            # Security validation
            if not validate_video_url(url):
                continue
            
            # Skip obviously invalid URLs
            if self._is_invalid_url(url):
                continue
            
            # Enhance link info
            video_info = extract_video_info_from_url(url)
            link.update(video_info)
            
            valid_links.append(link)
        
        return valid_links
    
    def _is_invalid_url(self, url: str) -> bool:
        """Check if URL is obviously invalid."""
        url_lower = url.lower()
        
        # Invalid patterns
        invalid_patterns = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'javascript:',
            'data:',
            'file:',
            'about:',
            'chrome:',
            'moz-extension:',
            'chrome-extension:'
        ]
        
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return True
        
        # Check for malformed URLs
        if url.count('http') > 1:
            return True
        
        # Check for suspicious query parameters
        suspicious_params = ['<script', 'javascript:', 'eval(', 'alert(']
        for param in suspicious_params:
            if param in url_lower:
                return True
        
        return False
