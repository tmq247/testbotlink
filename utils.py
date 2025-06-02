import re
import logging
import time
from typing import Optional, List, Dict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simple rate limiter to prevent spam and abuse.
    """
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, deque] = defaultdict(deque)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to make a request.
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Remove old requests outside the window
        while user_queue and current_time - user_queue[0] > self.window_seconds:
            user_queue.popleft()
        
        # Check if user has exceeded the limit
        if len(user_queue) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current request
        user_queue.append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Get remaining requests for user in current window.
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Remove old requests
        while user_queue and current_time - user_queue[0] > self.window_seconds:
            user_queue.popleft()
        
        return max(0, self.max_requests - len(user_queue))
    
    def get_reset_time(self, user_id: int) -> float:
        """
        Get time when rate limit resets for user.
        """
        user_queue = self.user_requests[user_id]
        if not user_queue:
            return 0
        
        return user_queue[0] + self.window_seconds

def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2 format.
    MarkdownV2 requires escaping: _*[]()~`>#+-=|{}.!
    """
    if not text:
        return ""
    
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    # Escape each special character
    escaped_text = text
    for char in escape_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')
    
    return escaped_text

def is_valid_url(url: str) -> bool:
    """
    Validate if the provided string is a valid URL.
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    """
    # Remove invalid characters for filenames
    invalid_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(invalid_chars, '_', filename)
    
    # Remove extra spaces and dots
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\.+', '.', cleaned)
    
    return cleaned

def extract_video_info(url: str) -> dict:
    """
    Extract basic info from video URL.
    """
    info = {
        'url': url,
        'filename': '',
        'extension': '',
        'quality': 'Unknown'
    }
    
    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        if '/' in path:
            filename = path.split('/')[-1]
            info['filename'] = clean_filename(filename)
            
            if '.' in filename:
                info['extension'] = filename.split('.')[-1].lower()
        
        # Try to extract quality from URL or filename
        quality_patterns = [
            (r'1080p?', '1080p'),
            (r'720p?', '720p'),
            (r'480p?', '480p'),
            (r'360p?', '360p'),
            (r'4k|uhd', '4K'),
            (r'hd', 'HD')
        ]
        
        url_lower = url.lower()
        for pattern, quality in quality_patterns:
            if re.search(pattern, url_lower):
                info['quality'] = quality
                break
                
    except Exception as e:
        logger.error(f"Error extracting video info from {url}: {e}")
    
    return info

def format_telegram_message(header: str, links: List[Dict]) -> List[str]:
    """
    Format video links into Telegram messages with proper length limits.
    """
    messages = []
    current_message = f"{header}\n\n"
    
    for i, link in enumerate(links, 1):
        filename = link.get('filename', f'video_{i}')
        quality = link.get('quality', 'Unknown')
        extension = link.get('extension', 'unknown').upper()
        url = link.get('url', '')
        
        video_text = (
            f"🎬 **Video {i}**\n"
            f"📂 Tên: {filename}\n"
            f"🎭 Chất lượng: {quality}\n"
            f"📄 Định dạng: {extension}\n"
            f"🔗 Link: {url}\n\n"
        )
        
        # Check if adding this video would exceed Telegram's message limit
        if len(current_message + video_text) > 4000:
            messages.append(current_message.strip())
            current_message = f"📹 **Tiếp tục danh sách video**\n\n{video_text}"
        else:
            current_message += video_text
    
    if current_message.strip():
        messages.append(current_message.strip())
    
    return messages

def get_user_friendly_error(error_type: str, details: str = "") -> str:
    """
    Get user-friendly error message.
    """
    error_messages = {
        'invalid_url': (
            "❌ **Link không hợp lệ**\n\n"
            "Vui lòng gửi link đúng định dạng từ các trang web được hỗ trợ.\n\n"
            "Ví dụ: https://phimmoi.net/phim/ten-phim/"
        ),
        'timeout_error': (
            "⏰ **Hết thời gian xử lý**\n\n"
            "Trang web phản hồi quá chậm. Vui lòng thử lại sau vài phút."
        ),
        'server_error': (
            "⚠️ **Lỗi hệ thống**\n\n"
            "Có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại sau."
        ),
        'rate_limit': (
            "⏳ **Giới hạn tần suất**\n\n"
            "Bạn đã gửi quá nhiều yêu cầu. Vui lòng chờ và thử lại."
        )
    }
    
    message = error_messages.get(error_type, "❌ **Có lỗi xảy ra**\n\nVui lòng thử lại sau.")
    
    if details and error_type == 'server_error':
        message += f"\n\n🔧 Chi tiết: {details[:100]}"
    
    return message
