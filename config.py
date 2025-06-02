"""
Configuration settings for the Telegram Movie Link Extractor Bot.
Contains bot token, supported domains, and other configuration parameters.
"""

import os
from typing import List

# Bot Configuration - Using environment variables for security
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7078453005:AAFDnjrzItKTLAMWqXfphubnF4I8lbW_ahA")

# Validate bot token exists
if not BOT_TOKEN:
    print("CẢNH BÁO: Không tìm thấy TELEGRAM_BOT_TOKEN trong biến môi trường!")
    print("Vui lòng thiết lập: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")

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
    "lauphim.tv",
    "phimmoichills.net",
    "ophim.tv",
    "nguonphim.tv",
    "phimhd.bz"
]

# Request timeout settings
REQUEST_TIMEOUT = 30  # seconds
MAX_PROCESSING_TIME = 45  # seconds for overall processing
CONNECT_TIMEOUT = 10  # seconds for connection

# User agent rotation for avoiding detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

# Video link extraction settings
MAX_LINKS_PER_PAGE = 15  # Maximum number of links to return
MIN_URL_LENGTH = 20  # Minimum length for valid video URLs
MAX_URL_LENGTH = 2000  # Maximum URL length

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
EXPONENTIAL_BACKOFF = True

# Log settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "bot.log"
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
VERBOSE_LOGGING = os.getenv("VERBOSE", "false").lower() == "true"

# Quality detection patterns
QUALITY_PATTERNS = {
    "4K": r"(4k|2160p|uhd|ultra.*hd)",
    "1080p": r"(1080p|fullhd|fhd|full.*hd)",
    "720p": r"(720p|hd|high.*def)",
    "480p": r"(480p|sd|standard.*def)",
    "360p": r"(360p|low.*quality)",
    "240p": r"(240p|very.*low)"
}

# Video file extensions to detect
VIDEO_EXTENSIONS = [
    "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v", "3gp", "ogv", "mts", "m2ts"
]

# Streaming format extensions
STREAMING_EXTENSIONS = [
    "m3u8", "mpd", "f4m", "f4v", "ts", "m2ts"
]

# Common streaming keywords to look for
STREAMING_KEYWORDS = [
    "stream", "video", "play", "hls", "dash", "cdn", "media", "content", 
    "player", "embed", "watch", "live", "vod"
]

# Headers for requests
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8,en-US;q=0.7",
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
    "network_error": "❌ Lỗi kết nối mạng. Vui lòng thử lại sau.",
    "invalid_token": "❌ Token bot không hợp lệ.",
    "rate_limited": "❌ Đã vượt quá giới hạn request. Vui lòng chờ một chút."
}

# Success messages
SUCCESS_MESSAGES = {
    "links_found": "✅ Đã tìm thấy link streaming!",
    "processing": "🔍 Đang tìm link streaming...",
    "extracting": "📹 Đang trích xuất video links...",
    "validating": "🔍 Đang kiểm tra tính hợp lệ của links..."
}

# Bot command descriptions
COMMAND_DESCRIPTIONS = {
    "start": "Khởi động bot và hiển thị hướng dẫn",
    "help": "Hiển thị hướng dẫn sử dụng chi tiết",
    "status": "Kiểm tra trạng thái bot"
}

# Validation settings
MIN_DOMAIN_LENGTH = 5
URL_VALIDATION_REGEX = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'

# Rate limiting settings
RATE_LIMIT_REQUESTS = 10  # requests per minute per user
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Feature flags
ENABLE_IFRAME_EXTRACTION = True
ENABLE_JAVASCRIPT_EXTRACTION = True
ENABLE_API_EXTRACTION = True
ENABLE_QUALITY_DETECTION = True
ENABLE_WEB_INTERFACE = True

# Security settings
ALLOWED_SCHEMES = ["http", "https"]
BLOCKED_DOMAINS = ["localhost", "127.0.0.1", "0.0.0.0"]  # Block local access for security
MAX_CONCURRENT_REQUESTS = 5

# Cache settings (if implementing caching in future)
CACHE_ENABLED = False
CACHE_TTL = 300  # 5 minutes
CACHE_MAX_SIZE = 1000
