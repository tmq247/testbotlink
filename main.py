#!/usr/bin/env python3
"""
Main entry point for the Telegram Movie Link Extractor Bot.
This bot extracts streaming video links from Vietnamese movie websites.
"""

import logging
import os
import sys
from telegram.ext import Application

from bot_handler import setup_bot_handlers
from config import BOT_TOKEN

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main function to start the bot."""
    try:
        # Validate bot token
        if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
            logger.error("Bot token not found. Please set TELEGRAM_BOT_TOKEN environment variable.")
            sys.exit(1)
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup bot handlers
        setup_bot_handlers(application)
        
        logger.info("Starting Telegram Movie Link Extractor Bot...")
        
        # Start the bot
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
