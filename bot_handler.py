"""
Telegram bot handlers for processing user messages and commands.
Handles bot commands and URL processing for video link extraction.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction
import asyncio

from link_extractor import VideoLinkExtractor
from config import SUPPORTED_DOMAINS, MAX_PROCESSING_TIME

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """Handles Telegram bot interactions and message processing."""
    
    def __init__(self):
        self.link_extractor = VideoLinkExtractor()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🎬 **Chào mừng bạn đến với Bot Tìm Link Phim!**\n\n"
            "📝 **Cách sử dụng:**\n"
            "• Gửi link tập phim từ các trang web xem phim\n"
            "• Bot sẽ tìm và trả về link stream hoặc m3u8\n\n"
            "🌐 **Hỗ trợ các trang:**\n"
            "• Các trang phim Việt Nam phổ biến\n"
            "• Tự động phát hiện link streaming\n\n"
            "❓ Gõ /help để xem thêm hướng dẫn"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🆘 **Hướng dẫn sử dụng Bot**\n\n"
            "**Các lệnh có sẵn:**\n"
            "• `/start` - Khởi động bot\n"
            "• `/help` - Hiển thị hướng dẫn\n\n"
            "**Cách tìm link phim:**\n"
            "1. Truy cập trang web xem phim\n"
            "2. Vào trang tập phim cụ thể\n"
            "3. Copy link và gửi cho bot\n"
            "4. Chờ bot trả về link streaming\n\n"
            "**Định dạng hỗ trợ:**\n"
            "• Link stream trực tiếp (.mp4, .mkv)\n"
            "• Link playlist m3u8\n"
            "• Link embed player\n\n"
            "**Lưu ý:**\n"
            "• Chỉ gửi link tập phim, không phải link trang chủ\n"
            "• Bot có thể mất vài giây để xử lý\n"
            "• Nếu không tìm thấy link, hãy thử link khác"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_url_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle URL messages from users."""
        url = update.message.text.strip()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        logger.info(f"Processing URL from user {user_id}: {url}")
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Validate URL format
        if not self._is_valid_url(url):
            await update.message.reply_text(
                "❌ **Link không hợp lệ**\n\n"
                "Vui lòng gửi link hợp lệ của trang tập phim.\n"
                "Ví dụ: https://example.com/phim/tap-1",
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔍 **Đang tìm link streaming...**\n"
            "Vui lòng chờ trong giây lát...",
            parse_mode='Markdown'
        )
        
        try:
            # Extract video links with timeout
            links = await asyncio.wait_for(
                self.link_extractor.extract_video_links(url),
                timeout=MAX_PROCESSING_TIME
            )
            
            if links:
                await self._send_extracted_links(update, processing_msg, links, url)
            else:
                await self._send_no_links_found(update, processing_msg, url)
                
        except asyncio.TimeoutError:
            await processing_msg.edit_text(
                "⏱️ **Quá thời gian xử lý**\n\n"
                "Trang web phản hồi quá chậm hoặc không khả dụng.\n"
                "Vui lòng thử lại sau hoặc sử dụng link khác.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            await processing_msg.edit_text(
                "❌ **Lỗi xử lý**\n\n"
                "Đã xảy ra lỗi khi xử lý link của bạn.\n"
                "Vui lòng thử lại sau hoặc sử dụng link khác.",
                parse_mode='Markdown'
            )
    
    async def _send_extracted_links(self, update: Update, processing_msg, links: list, original_url: str):
        """Send extracted video links to user."""
        response = "✅ **Đã tìm thấy link streaming!**\n\n"
        
        for i, link_info in enumerate(links, 1):
            quality = link_info.get('quality', 'Không xác định')
            link_type = link_info.get('type', 'video')
            url = link_info.get('url', '')
            
            response += f"**Link {i}:**\n"
            response += f"🎥 Chất lượng: {quality}\n"
            response += f"📹 Định dạng: {link_type}\n"
            response += f"🔗 Link: `{url}`\n\n"
        
        response += "💡 **Hướng dẫn:**\n"
        response += "• Copy link và dán vào trình phát video\n"
        response += "• Link m3u8 cần trình phát hỗ trợ HLS\n"
        response += "• Một số link có thể cần VPN"
        
        try:
            await processing_msg.edit_text(response, parse_mode='Markdown')
        except Exception as e:
            # If message is too long, send in parts
            logger.warning(f"Message too long, sending in parts: {e}")
            await processing_msg.edit_text(
                "✅ **Đã tìm thấy link streaming!**\n"
                "Đang gửi kết quả...",
                parse_mode='Markdown'
            )
            
            for i, link_info in enumerate(links, 1):
                link_msg = (
                    f"**Link {i}:**\n"
                    f"🎥 Chất lượng: {link_info.get('quality', 'Không xác định')}\n"
                    f"📹 Định dạng: {link_info.get('type', 'video')}\n"
                    f"🔗 Link: `{link_info.get('url', '')}`"
                )
                await update.message.reply_text(link_msg, parse_mode='Markdown')
    
    async def _send_no_links_found(self, update: Update, processing_msg, url: str):
        """Send message when no video links are found."""
        await processing_msg.edit_text(
            "❌ **Không tìm thấy link streaming**\n\n"
            "Có thể do:\n"
            "• Trang web có bảo vệ chống bot\n"
            "• Link không phải trang tập phim\n"
            "• Video player sử dụng mã hóa đặc biệt\n"
            "• Trang web tạm thời không khả dụng\n\n"
            "💡 **Gợi ý:**\n"
            "• Thử link tập phim khác\n"
            "• Kiểm tra link có đúng định dạng\n"
            "• Thử lại sau vài phút",
            parse_mode='Markdown'
        )
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format and domain."""
        import re
        from urllib.parse import urlparse
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except Exception:
            return False
    
    async def handle_unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-URL messages."""
        await update.message.reply_text(
            "❓ **Tin nhắn không được hỗ trợ**\n\n"
            "Vui lòng gửi link trang tập phim để tìm link streaming.\n"
            "Gõ /help để xem hướng dẫn chi tiết.",
            parse_mode='Markdown'
        )


def setup_bot_handlers(application):
    """Setup all bot command and message handlers."""
    handler = TelegramBotHandler()
    
    # Command handlers
    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    
    # URL message handler (messages containing http/https)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'https?://'), 
        handler.handle_url_message
    ))
    
    # Unknown message handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handler.handle_unknown_message
    ))
    
    logger.info("Bot handlers setup complete")
