"""
Website scraping module for fetching and processing web content.
Handles HTTP requests, user agents, and content extraction with enhanced security.
"""

import logging
import asyncio
import aiohttp
import ssl
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import random
import time

from config import (
    USER_AGENTS, REQUEST_TIMEOUT, CONNECT_TIMEOUT, MAX_RETRIES, 
    RETRY_DELAY, EXPONENTIAL_BACKOFF, DEFAULT_HEADERS
)
from security import sanitize_url
from utils import retry_async_operation

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Handles web scraping operations for movie websites with enhanced security and reliability."""
    
    def __init__(self):
        # User agents for rotation
        self.user_agents = USER_AGENTS
        
        # Request timeout settings
        self.timeout = aiohttp.ClientTimeout(
            total=REQUEST_TIMEOUT, 
            connect=CONNECT_TIMEOUT,
            sock_read=15
        )
        
        # SSL context for handling certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Request session configuration
        self.connector_limit = 10
        self.connector_limit_per_host = 3
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Minimum seconds between requests
    
    async def get_page_content(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Fetch page content from URL with enhanced error handling.
        
        Args:
            url: The URL to fetch
            headers: Optional custom headers
            
        Returns:
            Page content as string or None if failed
        """
        # Sanitize URL first
        clean_url = sanitize_url(url)
        if not clean_url:
            logger.error(f"URL failed sanitization: {url}")
            return None
        
        try:
            # Rate limiting per domain
            await self._rate_limit_request(clean_url)
            
            # Prepare headers
            request_headers = self._get_request_headers(headers)
            
            # Create session with custom settings
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=self.connector_limit,
                limit_per_host=self.connector_limit_per_host,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True)
            ) as session:
                
                # Fetch with retries
                content = await retry_async_operation(
                    lambda: self._fetch_url(session, clean_url),
                    max_retries=MAX_RETRIES,
                    delay=RETRY_DELAY,
                    exponential_backoff=EXPONENTIAL_BACKOFF,
                    exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
                )
                
                return content
                
        except Exception as e:
            logger.error(f"Error fetching page content from {clean_url}: {str(e)}")
            return None
    
    async def _fetch_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Internal method to fetch URL with session."""
        try:
            logger.debug(f"Fetching URL: {url}")
            
            async with session.get(
                url, 
                allow_redirects=True,
                max_redirects=5
            ) as response:
                
                # Check response status
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if not self._is_text_content(content_type):
                        logger.warning(f"Non-text content type: {content_type} for {url}")
                        return None
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                        logger.warning(f"Content too large: {content_length} bytes for {url}")
                        return None
                    
                    # Read content with encoding handling
                    content = await self._read_response_content(response)
                    
                    if content:
                        logger.info(f"Successfully fetched {len(content)} characters from {url}")
                        return content
                    
                elif response.status == 403:
                    logger.warning(f"Access forbidden for {url}")
                    # Try with different user agent
                    session.headers['User-Agent'] = random.choice(self.user_agents)
                    raise aiohttp.ClientError(f"HTTP 403 Forbidden for {url}")
                
                elif response.status == 429:
                    logger.warning(f"Rate limited for {url}")
                    await asyncio.sleep(random.uniform(2, 5))
                    raise aiohttp.ClientError(f"HTTP 429 Rate Limited for {url}")
                
                elif response.status in [404, 410]:
                    logger.warning(f"Resource not found: HTTP {response.status} for {url}")
                    return None
                
                elif response.status >= 500:
                    logger.warning(f"Server error: HTTP {response.status} for {url}")
                    raise aiohttp.ClientError(f"HTTP {response.status} Server Error for {url}")
                
                else:
                    logger.warning(f"Unexpected HTTP status {response.status} for {url}")
                    raise aiohttp.ClientError(f"HTTP {response.status} for {url}")
                    
        except aiohttp.ClientError:
            raise  # Re-raise for retry logic
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            raise aiohttp.ClientError(f"Unexpected error: {str(e)}")
        
        return None
    
    async def _read_response_content(self, response: aiohttp.ClientResponse) -> Optional[str]:
        """Read and decode response content with proper encoding handling."""
        try:
            # Try to get encoding from response
            encoding = 'utf-8'
            content_type = response.headers.get('content-type', '')
            
            if 'charset=' in content_type:
                try:
                    encoding = content_type.split('charset=')[1].split(';')[0].strip()
                except Exception:
                    encoding = 'utf-8'
            
            # Read raw bytes first
            raw_content = await response.read()
            
            # Try to decode with detected encoding
            try:
                content = raw_content.decode(encoding, errors='replace')
            except (UnicodeDecodeError, LookupError):
                # Fallback to utf-8 with error replacement
                content = raw_content.decode('utf-8', errors='replace')
            
            # Basic content validation
            if len(content.strip()) < 100:
                logger.warning("Content appears to be too short")
                return None
            
            return content
            
        except Exception as e:
            logger.error(f"Error reading response content: {str(e)}")
            return None
    
    def _is_text_content(self, content_type: str) -> bool:
        """Check if content type indicates text content."""
        text_types = [
            'text/html',
            'text/plain',
            'application/json',
            'application/javascript',
            'text/javascript',
            'application/xml',
            'text/xml'
        ]
        
        return any(text_type in content_type for text_type in text_types)
    
    async def _rate_limit_request(self, url: str):
        """Implement rate limiting per domain."""
        try:
            domain = urlparse(url).netloc
            current_time = time.time()
            
            if domain in self.last_request_time:
                time_since_last = current_time - self.last_request_time[domain]
                if time_since_last < self.min_request_interval:
                    sleep_time = self.min_request_interval - time_since_last
                    logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                    await asyncio.sleep(sleep_time)
            
            self.last_request_time[domain] = time.time()
            
        except Exception as e:
            logger.warning(f"Error in rate limiting: {str(e)}")
    
    def _get_request_headers(self, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get request headers with user agent rotation."""
        headers = DEFAULT_HEADERS.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    async def get_json_data(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch JSON data from URL with enhanced error handling.
        
        Args:
            url: The API endpoint URL
            headers: Optional custom headers
            
        Returns:
            JSON data as dictionary or None if failed
        """
        clean_url = sanitize_url(url)
        if not clean_url:
            return None
        
        try:
            await self._rate_limit_request(clean_url)
            
            request_headers = self._get_request_headers(headers)
            request_headers['Accept'] = 'application/json, text/plain, */*'
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers
            ) as session:
                
                async with session.get(clean_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched JSON data from {clean_url}")
                        return data
                    else:
                        logger.warning(f"HTTP {response.status} when fetching JSON from {clean_url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching JSON from {clean_url}: {str(e)}")
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
        clean_url = sanitize_url(url)
        if not clean_url:
            return None
        
        try:
            await self._rate_limit_request(clean_url)
            
            request_headers = self._get_request_headers(headers)
            request_headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=request_headers
            ) as session:
                
                async with session.post(clean_url, data=data) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"Successfully posted data to {clean_url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} when posting to {clean_url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error posting to {clean_url}: {str(e)}")
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
                'stream', 'video', 'play', 'hls', 'dash', 'media'
            ]
            
            return any(indicator in url_lower for indicator in video_indicators)
            
        except Exception:
            return False
