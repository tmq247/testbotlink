#!/usr/bin/env python3
"""
Telegram Bot for Vietnamese Movie Link Extraction
Main entry point for the bot application.
"""

import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

# Import local modules
from config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT
from bot_handler import TelegramBotHandler

# Setup logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bot."""
    # Check if bot token is provided
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        logger.error("Please set your bot token in environment variables or config.py")
        return
    
    # Create bot handler
    handler = TelegramBotHandler()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Setup handlers
    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("status", handler.status_command))
    
    # URL message handler
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'https?://'), 
        handler.handle_url_message
    ))
    
    # Unknown message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handler.handle_unknown_message
    ))
    
    logger.info("🚀 Starting Telegram Video Extractor Bot...")
    logger.info("✅ Bot handlers configured successfully")
    
    try:
        # Start the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")

if __name__ == "__main__":
    main()