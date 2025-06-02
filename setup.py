#!/usr/bin/env python3
"""
Setup script cho Telegram Video Extractor Bot
Tự động cài đặt tất cả dependencies và thiết lập môi trường
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Kiểm tra phiên bản Python"""
    if sys.version_info < (3, 8):
        print("❌ Yêu cầu Python 3.8 trở lên")
        print(f"Phiên bản hiện tại: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_package(package):
    """Cài đặt package"""
    try:
        print(f"📦 Đang cài đặt {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Đã cài đặt {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi cài đặt {package}: {e}")
        return False

def create_env_file():
    """Tạo file .env mẫu"""
    env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Rate Limiting (tùy chọn)
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=60

# Logging Level (tùy chọn: DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Đã tạo file .env mẫu")
        return True
    else:
        print("ℹ️ File .env đã tồn tại")
        return True

def main():
    """Hàm chính setup"""
    print("🚀 Thiết lập Telegram Video Extractor Bot")
    print("=" * 50)
    
    # Kiểm tra Python version
    if not check_python_version():
        sys.exit(1)
    
    # Danh sách packages cần thiết
    packages = [
        "python-telegram-bot==20.7",
        "aiohttp>=3.8.0",
        "trafilatura>=1.6.0",
        "lxml>=4.9.0",
        "requests>=2.28.0"
    ]
    
    # Cài đặt packages
    print("\n📦 Cài đặt dependencies...")
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Tạo file .env
    print("\n⚙️ Thiết lập cấu hình...")
    create_env_file()
    
    # Kết quả
    print("\n" + "=" * 50)
    if failed_packages:
        print("⚠️ Một số packages cài đặt thất bại:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        print("\nBạn có thể thử cài đặt thủ công:")
        for pkg in failed_packages:
            print(f"  pip install {pkg}")
    else:
        print("✅ Tất cả dependencies đã được cài đặt thành công!")
    
    print("\n📋 Bước tiếp theo:")
    print("1. Tạo bot Telegram với @BotFather")
    print("2. Cập nhật TELEGRAM_BOT_TOKEN trong file .env")
    print("3. Chạy: python main.py")
    print("\n🤖 Bot sẵn sàng sử dụng!")

if __name__ == "__main__":
    main()