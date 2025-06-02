#!/usr/bin/env python3
"""
Main entry point for the Telegram Movie Link Extractor Bot.
This bot extracts streaming video links from Vietnamese movie websites.
"""

import logging
import os
import sys
import asyncio
from telegram.ext import Application
from aiohttp import web
from aiohttp.web import Application as AIOHTTPApplication

from bot_handler import setup_bot_handlers
from config import BOT_TOKEN, DEBUG_MODE, LOG_LEVEL
from web_interface import create_web_app
from security import validate_bot_token

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL),
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def start_bot():
    """Initialize and start the Telegram bot."""
    try:
        # Validate bot token
        if not validate_bot_token(BOT_TOKEN):
            logger.error("Token bot không hợp lệ. Vui lòng thiết lập biến môi trường TELEGRAM_BOT_TOKEN.")
            return None

        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup bot handlers
        setup_bot_handlers(application)
        
        logger.info("Bot Telegram đã được khởi tạo thành công")
        
        # Initialize the application
        await application.initialize()
        await application.start()
        
        # Start polling in background
        await application.updater.start_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
        logger.info("Bot Telegram đang chạy...")
        return application
        
    except Exception as e:
        logger.error(f"Lỗi khởi động bot: {e}")
        return None


async def create_app():
    """Create the web application with bot integration."""
    # Start the bot
    bot_app = await start_bot()
    
    if not bot_app:
        logger.error("Không thể khởi động bot Telegram")
        sys.exit(1)
    
    # Create web interface
    web_app = create_web_app(bot_app)
    
    return web_app


async def cleanup(app):
    """Cleanup function for graceful shutdown."""
    bot_app = app.get('bot_app')
    if bot_app:
        logger.info("Đang tắt bot Telegram...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


def main():
    """Main function to start the application."""
    try:
        logger.info("Đang khởi động Bot Telegram Trích Xuất Link Phim...")
        
        # Setup routes and start server
        async def init():
            web_app = await create_app()
            # Setup cleanup for the web app
            web_app.on_cleanup.append(cleanup)
            return web_app
        
        # Try different ports if 5000 is busy
        ports_to_try = [5000, 8080, 3000, 8000]
        
        for port in ports_to_try:
            try:
                logger.info(f"Thử khởi động trên port {port}...")
                web.run_app(
                    init(),
                    host='0.0.0.0',
                    port=port,
                    access_log=logger if DEBUG_MODE else None
                )
                break
            except OSError as e:
                if "Address already in use" in str(e):
                    logger.warning(f"Port {port} đã được sử dụng, thử port tiếp theo...")
                    continue
                else:
                    raise e
        else:
            logger.error("Không thể tìm port trống để khởi động server")
        
    except KeyboardInterrupt:
        logger.info("Bot đã được dừng bởi người dùng")
    except Exception as e:
        logger.error(f"Lỗi không mong muốn: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
