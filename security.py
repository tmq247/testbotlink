import re
import hashlib
import urllib.parse
from typing import Optional

def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate URL for security.
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Basic URL validation
    if not re.match(r'^https?://', url, re.IGNORECASE):
        return None
    
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return None
        
        # Reconstruct clean URL
        clean_url = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return clean_url
    except Exception:
        return None

def validate_user_input(text: str) -> bool:
    """
    Validate user input for basic security checks.
    """
    if not text or len(text) > 2048:
        return False
    
    # Check for potentially malicious patterns
    malicious_patterns = [
        r'<script',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'onclick',
        r'onerror'
    ]
    
    text_lower = text.lower()
    for pattern in malicious_patterns:
        if re.search(pattern, text_lower):
            return False
    
    return True

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown.
    """
    if not text:
        return ""
    
    # Escape characters that have special meaning in Markdown
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def generate_request_id(user_id: int, url: str) -> str:
    """
    Generate a unique request ID for tracking.
    """
    import time
    timestamp = str(int(time.time()))
    data = f"{user_id}_{url}_{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()[:8]