#!/usr/bin/env python3
"""
Installation script for Telegram Video Extractor Bot dependencies.
Run this script to install all required packages.
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command}")
            return True
        else:
            print(f"❌ {command}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run: {command}")
        print(f"Error: {e}")
        return False

def main():
    """Main installation function."""
    print("🔧 Installing Telegram Video Extractor Bot Dependencies...")
    print("=" * 50)
    
    # Required packages
    packages = [
        "python-telegram-bot==20.7",
        "aiohttp==3.9.1", 
        "trafilatura==1.6.4",
        "lxml==4.9.3",
        "requests==2.31.0"
    ]
    
    print("📦 Installing Python packages...")
    
    # Install packages one by one
    for package in packages:
        print(f"Installing {package}...")
        if not run_command(f"pip install {package}"):
            print(f"⚠️ Failed to install {package}")
    
    print("\n" + "=" * 50)
    print("✅ Installation completed!")
    print("\n📋 Next steps:")
    print("1. Set your TELEGRAM_BOT_TOKEN environment variable")
    print("2. Run: python main.py")
    print("\n🤖 Your bot is ready to use!")

if __name__ == "__main__":
    main()