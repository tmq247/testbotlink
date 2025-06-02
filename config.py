"""
Configuration settings for the Telegram Movie Link Extractor Bot.
Contains bot token, supported domains, and other configuration parameters.
"""

import os
from typing import List

# Bot Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7078453005:AAFDnjrzItKTLAMWqXfphubnF4I8lbW_ahA")

# Supported movie website domains (common Vietnamese movie sites)
SUPPORTED_DOMAINS: List[str] = [
    "phimmoi.net",
    "fimplus.org",
    "phim3s.info",
    "motphim.net",
    "xemphim.app",
    "phimhay.org",
    "bilutv.org",
    "kkphim.vip",
    "phim1080.org",
    "hdviet.tv",
    "thuvienhd.com",
    "phimkk.com",
    "luotphim.org",
    "vuviphim.org",
    "phimdinhcao.com",
    "lauphim.tv"
]

# Request timeout settings
REQUEST_TIMEOUT = 30  # seconds
MAX_PROCESSING_TIME = 45  # seconds for overall processing

# User agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

# Video link extraction settings
MAX_LINKS_PER_PAGE = 10  # Maximum number of links to return
MIN_URL_LENGTH = 20  # Minimum length for valid video URLs

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Log settings
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# Quality detection patterns
QUALITY_PATTERNS = {
    "4K": r"(4k|2160p|uhd)",
    "1080p": r"(1080p|fullhd|fhd)",
    "720p": r"(720p|hd)",
    "480p": r"(480p|sd)",
    "360p": r"(360p)",
    "240p": r"(240p)"
}

# Video file extensions to detect
VIDEO_EXTENSIONS = [
    "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "3gp", "ogv"
]

# Streaming format extensions
STREAMING_EXTENSIONS = [
    "m3u8", "mpd", "f4m", "f4v", "ts"
]

# Common streaming keywords to look for
STREAMING_KEYWORDS = [
    "stream", "video", "play", "hls", "dash", "cdn", "media", "content"
]

# Headers for requests
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

# Error messages in Vietnamese
ERROR_MESSAGES = {
    "invalid_url": "❌ Link không hợp lệ. Vui lòng gửi link hợp lệ của trang tập phim.",
    "no_links_found": "❌ Không tìm thấy link streaming. Trang web có thể có bảo vệ chống bot hoặc link không chính xác.",
    "processing_timeout": "⏱️ Quá thời gian xử lý. Trang web phản hồi quá chậm.",
    "processing_error": "❌ Đã xảy ra lỗi khi xử lý link. Vui lòng thử lại sau.",
    "unsupported_site": "❌ Trang web này chưa được hỗ trợ.",
    "network_error": "❌ Lỗi kết nối mạng. Vui lòng thử lại sau."
}

# Success messages
SUCCESS_MESSAGES = {
    "links_found": "✅ Đã tìm thấy link streaming!",
    "processing": "🔍 Đang tìm link streaming...",
    "extracting": "📹 Đang trích xuất video links..."
}

# Bot command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Khởi động bot và hiển thị hướng dẫn",
    "help": "Hiển thị hướng dẫn sử dụng chi tiết"
}

# Validation settings
MIN_DOMAIN_LENGTH = 5
MAX_URL_LENGTH = 2000

# Rate limiting (if needed in future)
RATE_LIMIT_REQUESTS = 10  # requests per minute per user
RATE_LIMIT_WINDOW = 60  # seconds

# Feature flags
ENABLE_IFRAME_EXTRACTION = True
ENABLE_JAVASCRIPT_EXTRACTION = True
ENABLE_API_EXTRACTION = True
ENABLE_QUALITY_DETECTION = True

# Debug settings
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE_LOGGING = os.getenv("VERBOSE", "false").lower() == "true"
