import os
import logging

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7078453005:AAFMBQaV5ppIE1iqe2K8dPbCIubxnH2Pd5A")

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 5  # requests per minute per user
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_ENABLED = True

# Processing limits
MAX_PROCESSING_TIME = 60  # seconds

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Video extraction configuration
SUPPORTED_DOMAINS = [
    "phimmoi.net",
    "bilutv.com", 
    "phim3s.info",
    "motphim.tv",
    "xemphim.com",
    "fimfast.com",
    "phimhay.org",
    "tvhay.fm",
    "phim1080.app"
]

VIDEO_EXTENSIONS = [".mp4", ".m3u8", ".mkv", ".avi", ".mov", ".webm"]

# Request timeout settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# User agent for web scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Error messages
ERROR_MESSAGES = {
    'invalid_url': '❌ **Link không hợp lệ**\n\nVui lòng gửi link đúng định dạng từ các trang web được hỗ trợ.',
    'timeout_error': '⏰ **Hết thời gian xử lý**\n\nTrang web phản hồi quá chậm. Vui lòng thử lại sau.',
    'server_error': '⚠️ **Lỗi hệ thống**\n\nCó lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại.',
    'rate_limit': '⏳ **Giới hạn tần suất**\n\nBạn đã gửi quá nhiều yêu cầu. Vui lòng chờ và thử lại.'
}

# Success messages
SUCCESS_MESSAGES = {
    'processing': 'Đang xử lý yêu cầu',
    'links_found': '✅ **Tìm thấy link video**'
}
