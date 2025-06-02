"""
Security utilities for the Telegram Movie Link Extractor Bot.
Handles token validation, URL sanitization, and security checks.
"""

import re
import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional, List
import hashlib

from config import (
    ALLOWED_SCHEMES, BLOCKED_DOMAINS, MAX_URL_LENGTH, MIN_URL_LENGTH,
    URL_VALIDATION_REGEX, SUPPORTED_DOMAINS
)

logger = logging.getLogger(__name__)


def validate_bot_token(token: str) -> bool:
    """
    Validate Telegram bot token format.
    
    Args:
        token: Bot token to validate
        
    Returns:
        True if token format is valid, False otherwise
    """
    if not token:
        logger.error("Token bot không được để trống")
        return False
    
    # Telegram bot token pattern: NNNNNNNNNN:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    token_pattern = r'^\d{8,10}:[a-zA-Z0-9_-]{35}$'
    
    if not re.match(token_pattern, token):
        logger.error("Token bot không đúng định dạng Telegram")
        return False
    
    logger.info("Token bot đã được xác thực")
    return True


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate URL for security.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL or None if invalid
    """
    if not url:
        return None
    
    # Remove whitespace and normalize
    url = url.strip()
    
    # Check length
    if len(url) < MIN_URL_LENGTH or len(url) > MAX_URL_LENGTH:
        logger.warning(f"URL length invalid: {len(url)}")
        return None
    
    # Basic regex validation
    if not re.match(URL_VALIDATION_REGEX, url, re.IGNORECASE):
        logger.warning(f"URL failed regex validation: {url}")
        return None
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in ALLOWED_SCHEMES:
            logger.warning(f"Invalid scheme: {parsed.scheme}")
            return None
        
        # Check for blocked domains
        hostname = parsed.hostname
        if hostname in BLOCKED_DOMAINS:
            logger.warning(f"Blocked domain: {hostname}")
            return None
        
        # Check for private IP ranges (basic check)
        if _is_private_ip(hostname):
            logger.warning(f"Private IP detected: {hostname}")
            return None
        
        # Remove potentially dangerous query parameters
        cleaned_url = _clean_query_params(url)
        
        logger.debug(f"URL sanitized successfully: {cleaned_url}")
        return cleaned_url
        
    except Exception as e:
        logger.error(f"Error sanitizing URL {url}: {str(e)}")
        return None


def validate_video_url(url: str) -> bool:
    """
    Additional validation specifically for video URLs.
    
    Args:
        url: Video URL to validate
        
    Returns:
        True if URL appears to be a valid video URL
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have valid domain
        if not parsed.netloc:
            return False
        
        # Check against suspicious patterns
        suspicious_patterns = [
            r'javascript:',
            r'data:',
            r'file:',
            r'ftp:',
            r'mailto:',
            r'<script',
            r'eval\(',
            r'alert\(',
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                logger.warning(f"Suspicious pattern detected in URL: {pattern}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating video URL: {str(e)}")
        return False


def is_supported_domain(url: str) -> bool:
    """
    Check if URL domain is in supported list.
    
    Args:
        url: URL to check
        
    Returns:
        True if domain is supported
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check exact match or subdomain
        for supported in SUPPORTED_DOMAINS:
            if domain == supported or domain.endswith('.' + supported):
                return True
        
        logger.info(f"Domain not in supported list: {domain}")
        return False
        
    except Exception:
        return False


def generate_request_id(user_id: int, url: str) -> str:
    """
    Generate unique request ID for logging and tracking.
    
    Args:
        user_id: Telegram user ID
        url: Request URL
        
    Returns:
        Unique request ID
    """
    import time
    
    data = f"{user_id}:{url}:{time.time()}"
    return hashlib.md5(data.encode()).hexdigest()[:12]


def rate_limit_key(user_id: int) -> str:
    """
    Generate rate limit key for user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Rate limit key
    """
    return f"rate_limit:{user_id}"


def _is_private_ip(hostname: str) -> bool:
    """Check if hostname is a private IP address."""
    if not hostname:
        return False
    
    # Basic private IP ranges
    private_patterns = [
        r'^10\.',
        r'^192\.168\.',
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
        r'^127\.',
        r'^169\.254\.',
        r'^::1$',
        r'^fc00:',
        r'^fe80:'
    ]
    
    for pattern in private_patterns:
        if re.match(pattern, hostname):
            return True
    
    return False


def _clean_query_params(url: str) -> str:
    """Remove potentially dangerous query parameters."""
    try:
        parsed = urlparse(url)
        
        if not parsed.query:
            return url
        
        # List of potentially dangerous parameters to remove
        dangerous_params = [
            'callback', 'jsonp', 'eval', 'exec', 'script',
            'onload', 'onerror', 'onclick', 'javascript'
        ]
        
        query_params = parse_qs(parsed.query)
        
        # Remove dangerous parameters
        cleaned_params = {
            k: v for k, v in query_params.items() 
            if k.lower() not in dangerous_params
        }
        
        # Reconstruct URL
        from urllib.parse import urlencode, urlunparse
        
        cleaned_query = urlencode(cleaned_params, doseq=True)
        cleaned_parsed = parsed._replace(query=cleaned_query)
        
        return urlunparse(cleaned_parsed)
        
    except Exception:
        # If cleaning fails, return original URL
        return url


def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters for Telegram.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    if not text:
        return ""
    
    # Characters that need escaping in Telegram Markdown
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def validate_user_input(text: str, max_length: int = 2000) -> bool:
    """
    Validate user input for basic security.
    
    Args:
        text: User input to validate
        max_length: Maximum allowed length
        
    Returns:
        True if input is valid
    """
    if not text:
        return False
    
    if len(text) > max_length:
        return False
    
    # Check for basic injection patterns
    injection_patterns = [
        r'<script',
        r'javascript:',
        r'eval\(',
        r'exec\(',
        r'system\(',
        r'shell_exec\(',
        r'passthru\(',
        r'file_get_contents\(',
        r'curl_exec\(',
        r'`.*`',  # Backticks
        r'\$\(',  # Command substitution
    ]
    
    text_lower = text.lower()
    for pattern in injection_patterns:
        if re.search(pattern, text_lower):
            logger.warning(f"Suspicious pattern in user input: {pattern}")
            return False
    
    return True
