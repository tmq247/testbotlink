# Telegram Bot Trích Xuất Link Video Phim Việt Nam

Bot Telegram tự động tìm và trích xuất link video từ các trang web xem phim Việt Nam phổ biến.

## 🌟 Tính năng

- ✅ Trích xuất link video từ nhiều trang web phim Việt Nam
- 🎭 Tự động phát hiện chất lượng video (4K, 1080p, 720p, 480p...)
- 📱 Hỗ trợ nhiều định dạng: MP4, M3U8, MKV, AVI, WebM
- ⚡ Rate limiting để tránh spam
- 🛡️ Kiểm tra bảo mật link
- 🔄 Xử lý bất đồng bộ với retry logic

## 🌐 Trang web được hỗ trợ

- phimmoi.net
- bilutv.com
- phim3s.info
- motphim.tv
- xemphim.com
- fimfast.com
- phimhay.org

## 📦 Cài đặt

### Yêu cầu hệ thống
- Python 3.8 trở lên
- Các thư viện Python được liệt kê trong dependencies

### Bước 1: Clone/Download mã nguồn
```bash
# Download tất cả các file và đặt vào một thư mục
```

### Bước 2: Cài đặt dependencies
```bash
# Chạy script tự động cài đặt
python install_dependencies.py

# Hoặc cài đặt thủ công
pip install python-telegram-bot==20.7
pip install aiohttp==3.9.1
pip install trafilatura==1.6.4
pip install lxml==4.9.3
pip install requests==2.31.0
```

### Bước 3: Tạo Bot Telegram
1. Mở Telegram và tìm @BotFather
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu Bot Token mà BotFather cung cấp

### Bước 4: Cấu hình Bot Token
```bash
# Linux/macOS
export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Windows
set TELEGRAM_BOT_TOKEN=your_bot_token_here

# Hoặc chỉnh sửa file config.py
BOT_TOKEN = "your_bot_token_here"
```

### Bước 5: Chạy Bot
```bash
python main.py
```

## 🚀 Sử dụng

1. Tìm bot trên Telegram và gửi `/start`
2. Gửi link trang tập phim từ các website được hỗ trợ
3. Bot sẽ tự động phân tích và trả về link video

### Ví dụ link hợp lệ:
- `https://phimmoi.net/phim/ten-phim/tap-1/`
- `https://bilutv.com/phim/ten-phim-tap-5.html`

## 📝 Cấu trúc file

```
telegram-bot/
├── main.py                 # File chính để chạy bot
├── config.py              # Cấu hình bot
├── bot_handler.py         # Xử lý tin nhắn và lệnh
├── link_extractor.py      # Trích xuất link video
├── security.py            # Bảo mật và validation
├── utils.py               # Các hàm tiện ích
├── rate_limiter.py        # Giới hạn tần suất
├── video_extractor.py     # Trích xuất video (legacy)
├── install_dependencies.py # Script cài đặt
└── README.md              # Hướng dẫn này
```

## ⚙️ Cấu hình nâng cao

### Rate Limiting
```python
# config.py
RATE_LIMIT_REQUESTS = 5    # Số yêu cầu tối đa
RATE_LIMIT_WINDOW = 60     # Trong vòng 60 giây
```

### Timeout Settings
```python
REQUEST_TIMEOUT = 30       # Timeout cho mỗi request
MAX_PROCESSING_TIME = 60   # Timeout tổng cộng
```

### Thêm trang web mới
```python
# config.py
SUPPORTED_DOMAINS = [
    "phimmoi.net",
    "your-new-domain.com"   # Thêm domain mới
]
```

## 🔧 Lệnh Bot

- `/start` - Khởi động bot
- `/help` - Hiển thị hướng dẫn
- `/status` - Kiểm tra trạng thái bot

## ⚠️ Lưu ý

- Bot chỉ hoạt động với link trang tập phim, không phải trang chủ
- Một số link có thể cần VPN để truy cập
- Link M3U8 cần app hỗ trợ HLS để phát video
- Bot không lưu trữ video, chỉ tìm link streaming

## 🛠️ Troubleshooting

### Lỗi Import Error
```bash
# Cài đặt lại dependencies
pip install --upgrade python-telegram-bot==20.7
```

### Lỗi MarkdownV2 Parsing
Bot đã được fix để xử lý MarkdownV2 an toàn

### Bot không phản hồi
1. Kiểm tra Bot Token
2. Kiểm tra kết nối internet
3. Xem log để tìm lỗi cụ thể

## 📞 Hỗ trợ

Nếu gặp vấn đề khi cài đặt hoặc sử dụng:
1. Kiểm tra log trong terminal
2. Đảm bảo đã cài đặt đúng tất cả dependencies
3. Kiểm tra Bot Token có đúng không

## ⚖️ Disclaimer

Bot được phát triển cho mục đích học tập và nghiên cứu. Người dùng có trách nhiệm tuân thủ các quy định pháp luật về bản quyền khi sử dụng.