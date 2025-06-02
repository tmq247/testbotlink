# Bot Telegram Trích Xuất Link Phim

Bot Telegram để tự động trích xuất link streaming (m3u8, mp4) từ các trang web xem phim trực tuyến.

## Tính năng

- 🎬 Trích xuất link streaming từ các trang web phim
- 📹 Hỗ tqợ nhiều định dạng: m3u8, mp4, mkv, webm
- 🔍 Tự động phát hiện chất lượng video (1080p, 720p, 480p...)
- 🌐 Hỗ tqợ các trang web phim Việt Nam phổ biến
- 🛡️ Xử lý iframe và JavaScript embedded links
- 🔄 Retry logic khi trang web chậm phản hồi

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/[username]/testbotlink.git
cd testbotlink
```

2. Cài đặt dependencies:
```bash
uv add python-telegram-bot==21.6 aiohttp beautifulsoup4
```

3. Tạo bot Telegram:
   - Nhắn tin cho @BotFather trên Telegram
   - Gời lệnh `/newbot`
   - Làm theo hướng dẫn và lưu token

4. Cấu hình token:
   - Mở file `config.py`
   - Thay đổi `BOT_TOKEN` thành token bot của bạn

## Sử dụng

1. Khởi động bot:
```bash
python main.py
```

2. Trên Telegram:
   - Tìm bot của bạn bằng username
   - Gửi `/start` để bắt đầu
   - Gửi link trang tập phim
   - Bot sẽ trả về link streaming

## Cấu trúc dự án

```
testbotlink/
├── main.py              # Entry point chính
├── bot_handler.py       # Xử lý tin nhắn Telegram
├── link_extractor.py    # Engine trích xuất link
├── website_scraper.py   # Scraping web content
├── config.py           # Cấu hình bot
├── pyproject.toml      # Dependencies
└── README.md           # Hướng dẫn
```

## Các trang web được hỗ tqợ

- phimmoi.net
- fimplus.org
- phim3s.info
- motphim.net
- xemphim.app
- phimhay.org
- bilutv.org
- kkphim.vip
- Và nhiều trang khác...

## Lệnh bot

- `/start` - Khởi động bot và hiển thị hướng dẫn
- `/help` - Hiển thị hướng dẫn chi tiết

## Lưu í

- Chỉ gửi link trang tập phim cụ thể, không phải trang chủ
- Bot có thể mất vài giây để xử lí
- Một số link có thể cần VPN để truy cập
- Tuân thủ bản quyền và điều khoản sử dụng của các trang web

## License

MIT License - Sử dụng tự do cho mục đích cá nhân và học tập.