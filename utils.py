"""
Utility functions for the Telegram Movie Link Extractor Bot.
Contains helper functions for common operations.
"""

import re
import logging
import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a request."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > window_start
            ]
        else:
            self.requests[user_id] = []
        
        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True
        
        return False
    
    def get_reset_time(self, user_id: int) -> Optional[float]:
        """Get time when rate limit resets for user."""
        if user_id not in self.requests or not self.requests[user_id]:
            return None
        
        oldest_request = min(self.requests[user_id])
        return oldest_request + self.window_seconds


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        return ""


def clean_filename(filename: str) -> str:
    """Clean filename for safe usage."""
    if not filename:
        return "unknown"
    
    # Remove or replace unsafe characters
    unsafe_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(unsafe_chars, '_', filename)
    
    # Remove multiple consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores and spaces
    cleaned = cleaned.strip('_ ')
    
    # Ensure not empty
    if not cleaned:
        cleaned = "unknown"
    
    return cleaned


def parse_video_quality(text: str) -> str:
    """Parse video quality from text."""
    if not text:
        return "Không xác định"
    
    text_lower = text.lower()
    
    quality_map = {
        '4k': ['4k', '2160p', 'uhd', 'ultra hd'],
        '1080p': ['1080p', 'fullhd', 'fhd', 'full hd'],
        '720p': ['720p', 'hd', 'high def'],
        '480p': ['480p', 'sd', 'standard'],
        '360p': ['360p'],
        '240p': ['240p']
    }
    
    for quality, keywords in quality_map.items():
        for keyword in keywords:
            if keyword in text_lower:
                return quality
    
    return "Không xác định"


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def is_video_file_extension(url: str) -> bool:
    """Check if URL has video file extension."""
    video_extensions = [
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', 
        '.webm', '.m4v', '.3gp', '.ogv', '.m2ts', '.ts'
    ]
    
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in video_extensions)


def is_streaming_format(url: str) -> bool:
    """Check if URL is a streaming format."""
    streaming_formats = ['.m3u8', '.mpd', '.f4m', '.f4v']
    url_lower = url.lower()
    return any(url_lower.endswith(fmt) for fmt in streaming_formats)


def extract_video_info_from_url(url: str) -> Dict[str, str]:
    """Extract video information from URL."""
    info = {
        'type': 'unknown',
        'quality': 'Không xác định',
        'format': 'unknown'
    }
    
    if not url:
        return info
    
    url_lower = url.lower()
    
    # Detect type
    if is_streaming_format(url):
        if '.m3u8' in url_lower:
            info['type'] = 'm3u8'
            info['format'] = 'HLS'
        elif '.mpd' in url_lower:
            info['type'] = 'dash'
            info['format'] = 'DASH'
        else:
            info['type'] = 'stream'
            info['format'] = 'Stream'
    elif is_video_file_extension(url):
        info['type'] = 'video'
        # Extract format from extension
        for ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']:
            if url_lower.endswith(ext):
                info['format'] = ext[1:].upper()
                break
    
    # Extract quality
    info['quality'] = parse_video_quality(url)
    
    return info


def validate_video_link_quality(links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and sort video links by quality."""
    if not links:
        return []
    
    # Quality ranking (higher is better)
    quality_rank = {
        '4K': 6,
        '1080p': 5,
        '720p': 4,
        '480p': 3,
        '360p': 2,
        '240p': 1,
        'Không xác định': 0
    }
    
    # Add quality rank to each link
    for link in links:
        quality = link.get('quality', 'Không xác định')
        link['quality_rank'] = quality_rank.get(quality, 0)
    
    # Sort by quality (highest first)
    sorted_links = sorted(links, key=lambda x: x.get('quality_rank', 0), reverse=True)
    
    # Remove quality_rank field
    for link in sorted_links:
        link.pop('quality_rank', None)
    
    return sorted_links


async def retry_async_operation(
    operation,
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,)
):
    """Retry async operation with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = delay * (2 ** attempt if exponential_backoff else 1)
            logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {str(e)}")
            await asyncio.sleep(wait_time)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Create a text progress bar."""
    if total == 0:
        return "█" * length
    
    filled = int(length * current / total)
    bar = "█" * filled + "░" * (length - filled)
    percentage = int(100 * current / total)
    
    return f"{bar} {percentage}%"


def format_telegram_message(
    title: str,
    links: List[Dict[str, Any]],
    max_message_length: int = 4000
) -> List[str]:
    """Format video links for Telegram message with length limits."""
    messages = []
    current_message = f"**{title}**\n\n"
    
    for i, link in enumerate(links, 1):
        quality = link.get('quality', 'Không xác định')
        link_type = link.get('type', 'video')
        url = link.get('url', '')
        
        link_text = (
            f"**Link {i}:**\n"
            f"🎥 Chất lượng: {quality}\n"
            f"📹 Định dạng: {link_type}\n"
            f"🔗 Link: `{url}`\n\n"
        )
        
        # Check if adding this link would exceed message length
        if len(current_message + link_text) > max_message_length:
            # Send current message and start new one
            messages.append(current_message.strip())
            current_message = f"**{title} (tiếp theo)**\n\n{link_text}"
        else:
            current_message += link_text
    
    # Add the last message if it has content
    if current_message.strip():
        messages.append(current_message.strip())
    
    return messages


def get_user_friendly_error(error_code: str, details: str = "") -> str:
    """Get user-friendly error message."""
    error_messages = {
        'network_error': '🌐 Lỗi kết nối mạng. Vui lòng kiểm tra kết nối internet và thử lại.',
        'timeout_error': '⏱️ Quá thời gian chờ. Trang web phản hồi quá chậm.',
        'parsing_error': '📄 Lỗi phân tích trang web. Cấu trúc trang có thể đã thay đổi.',
        'no_links_found': '🔍 Không tìm thấy link video. Trang này có thể không chứa video hoặc bị bảo vệ.',
        'invalid_url': '❌ Link không hợp lệ. Vui lòng kiểm tra và thử lại.',
        'rate_limit': '⏳ Bạn đã gửi quá nhiều yêu cầu. Vui lòng chờ một chút rồi thử lại.',
        'server_error': '🔧 Lỗi máy chủ. Vui lòng thử lại sau ít phút.',
        'unsupported_site': '🚫 Trang web này chưa được hỗ trợ.'
    }
    
    base_message = error_messages.get(error_code, '❌ Đã xảy ra lỗi không xác định.')
    
    if details:
        return f"{base_message}\n\n🔍 Chi tiết: {details}"
    
    return base_message
