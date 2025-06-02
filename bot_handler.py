"""
Telegram bot handlers for processing user messages and commands.
Handles bot commands and URL processing for video link extraction.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction
import asyncio
import time

from link_extractor import VideoLinkExtractor
from config import MAX_PROCESSING_TIME, RATE_LIMIT_ENABLED, ERROR_MESSAGES, SUCCESS_MESSAGES
from security import sanitize_url, validate_user_input, escape_markdown, generate_request_id
from utils import RateLimiter, format_telegram_message, get_user_friendly_error

logger = logging.getLogger(__name__)

# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=10, window_seconds=60) if RATE_LIMIT_ENABLED else None


class TelegramBotHandler:
    """Handles Telegram bot interactions and message processing."""
    
    def __init__(self):
        self.link_extractor = VideoLinkExtractor()
        self.processing_users = set()  # Track users currently processing
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🎬 **Chào mừng bạn đến với Bot Trích Xuất Link Phim!**\n\n"
            "📝 **Cách sử dụng:**\n"
            "• Gửi link tập phim từ các trang web xem phim Việt Nam\n"
            "• Bot sẽ tự động tìm và trả về link streaming\n"
            "• Hỗ trợ nhiều định dạng: MP4, M3U8, MKV...\n\n"
            "🌐 **Các trang web được hỗ trợ:**\n"
            "• phimmoi.net, bilutv.org, kkphim.vip\n"
            "• motphim.net, phimhay.org, xemphim.app\n"
            "• Và nhiều trang khác...\n\n"
            "🔒 **Bảo mật:**\n"
            "• Tất cả link được kiểm tra an toàn\n"
            "• Không lưu trữ thông tin cá nhân\n\n"
            "❓ Gõ /help để xem hướng dẫn chi tiết\n"
            "📊 Gõ /status để kiểm tra trạng thái bot"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🆘 **Hướng dẫn sử dụng Bot**\n\n"
            "**Các lệnh có sẵn:**\n"
            "• `/start` - Khởi động bot và xem giới thiệu\n"
            "• `/help` - Hiển thị hướng dẫn này\n"
            "• `/status` - Kiểm tra trạng thái bot\n\n"
            "**Cách tìm link phim:**\n"
            "1️⃣ Truy cập trang web xem phim được hỗ trợ\n"
            "2️⃣ Vào trang tập phim cụ thể (không phải trang chủ)\n"
            "3️⃣ Copy link URL và gửi cho bot\n"
            "4️⃣ Chờ bot phân tích và trả về kết quả\n\n"
            "**Định dạng được hỗ trợ:**\n"
            "• 📹 Video trực tiếp: MP4, MKV, AVI, WebM\n"
            "• 🎥 Stream playlist: M3U8, MPD\n"
            "• 🔗 Link embed player\n\n"
            "**Chất lượng video:**\n"
            "• Tự động phát hiện: 4K, 1080p, 720p, 480p...\n"
            "• Sắp xếp theo chất lượng từ cao xuống thấp\n\n"
            "**Lưu ý quan trọng:**\n"
            "• ✅ Chỉ gửi link trang tập phim, không phải trang chủ\n"
            "• ⏱️ Bot có thể mất 10-30 giây để xử lý\n"
            "• 🔄 Nếu không tìm thấy, hãy thử link tập khác\n"
            "• 🌐 Một số link có thể cần VPN để truy cập\n"
            "• 📱 Link M3U8 cần app hỗ trợ HLS để phát\n\n"
            "**Giới hạn sử dụng:**\n"
            "• 🔢 Tối đa 10 yêu cầu/phút\n"
            "• ⚡ Ưu tiên xử lý theo thứ tự\n\n"
            "🤖 Bot được phát triển để hỗ trợ xem phim hợp pháp\\!"
        )
        await update.message.reply_text(help_message, parse_mode='MarkdownV2')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = update.effective_user.id
        
        # Check rate limit status
        if rate_limiter and not rate_limiter.is_allowed(user_id):
            reset_time = rate_limiter.get_reset_time(user_id)
            if reset_time:
                wait_minutes = max(0, int((reset_time - time.time()) / 60))
                rate_status = f"❌ Đã đạt giới hạn (reset sau {wait_minutes} phút)"
            else:
                rate_status = "❌ Đã đạt giới hạn"
        else:
            rate_status = "✅ Bình thường"
        
        # Bot status
        processing_count = len(self.processing_users)
        
        status_message = (
            "📊 **Trạng thái Bot**\n\n"
            f"🤖 **Bot:** ✅ Hoạt động bình thường\n"
            f"🔢 **Đang xử lý:** {processing_count} yêu cầu\n"
            f"⚡ **Rate limit:** {rate_status}\n"
            f"👤 **User ID:** `{user_id}`\n\n"
            "🔧 **Tính năng đang hoạt động:**\n"
            "• ✅ Trích xuất link trực tiếp\n"
            "• ✅ Xử lý JavaScript\n"
            "• ✅ Phân tích iframe\n"
            "• ✅ Phát hiện chất lượng\n"
            "• ✅ Kiểm tra bảo mật\n\n"
            "📝 Gõ /help để xem hướng dẫn sử dụng"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def handle_url_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle URL messages from users."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        url = update.message.text.strip()
        
        # Generate request ID for tracking
        request_id = generate_request_id(user_id, url)
        logger.info(f"[{request_id}] Processing URL from user {user_id}: {url}")
        
        # Check if user is already processing
        if user_id in self.processing_users:
            await update.message.reply_text(
                "⏳ **Đang xử lý yêu cầu trước**\n\n"
                "Vui lòng chờ yêu cầu hiện tại hoàn thành trước khi gửi link mới.",
                parse_mode='Markdown'
            )
            return
        
        # Rate limiting check
        if rate_limiter and not rate_limiter.is_allowed(user_id):
            reset_time = rate_limiter.get_reset_time(user_id)
            wait_time = max(0, int((reset_time - time.time()) / 60)) if reset_time else 1
            
            await update.message.reply_text(
                f"⏳ **Giới hạn tần suất**\n\n"
                f"Bạn đã gửi quá nhiều yêu cầu\\. "
                f"Vui lòng chờ {wait_time} phút rồi thử lại\\.\n\n"
                f"Giới hạn: 10 yêu cầu/phút",
                parse_mode='MarkdownV2'
            )
            return
        
        # Validate user input
        if not validate_user_input(url):
            await update.message.reply_text(
                get_user_friendly_error('invalid_url'),
                parse_mode='Markdown'
            )
            return
        
        # Sanitize URL
        sanitized_url = sanitize_url(url)
        if not sanitized_url:
            await update.message.reply_text(
                get_user_friendly_error('invalid_url'),
                parse_mode='Markdown'
            )
            return
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"🔍 **{SUCCESS_MESSAGES['processing']}**"
            f"🌐 Đang phân tích: {escape_markdown(extract_domain_from_url(sanitized_url))}"
            f"⏱️ Thời gian ước tính: 10-30 giây"
            f"🔄 Vui lòng chờ trong giây lát",
            parse_mode='MarkdownV2'
        )
        
        # Add user to processing set
        self.processing_users.add(user_id)
        
        try:
            # Extract video links with timeout
            links = await asyncio.wait_for(
                self.link_extractor.extract_video_links(sanitized_url),
                timeout=MAX_PROCESSING_TIME
            )
            
            if links:
                await self._send_extracted_links(update, processing_msg, links, sanitized_url, request_id)
            else:
                await self._send_no_links_found(update, processing_msg, sanitized_url, request_id)
                
        except asyncio.TimeoutError:
            logger.warning(f"[{request_id}] Timeout processing URL: {sanitized_url}")
            await processing_msg.edit_text(
                get_user_friendly_error('timeout_error'),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"[{request_id}] Error processing URL {sanitized_url}: {str(e)}")
            await processing_msg.edit_text(
                get_user_friendly_error('server_error', str(e)),
                parse_mode='Markdown'
            )
        finally:
            # Remove user from processing set
            self.processing_users.discard(user_id)
    
    async def _send_extracted_links(self, update: Update, processing_msg, links: list, original_url: str, request_id: str):
        """Send extracted video links to user."""
        logger.info(f"[{request_id}] Found {len(links)} video links")
        
        # Format messages with length limits
        messages = format_telegram_message(SUCCESS_MESSAGES['links_found'], links)
        
        # Edit the first message
        if messages:
            first_message = messages[0]
            first_message += (
                "\n\n💡 **Hướng dẫn sử dụng:**\n"
                "• Copy link và dán vào trình phát video\n"
                "• Link M3U8 cần app hỗ trợ HLS (VLC, MX Player...)\n"
                "• Link MP4 có thể phát trực tiếp trên browser\n"
                "• Một số link có thể cần VPN để truy cập\n\n"
                "🔄 Gửi link tập khác để tiếp tục tìm kiếm"
            )
            
            try:
                await processing_msg.edit_text(first_message, parse_mode='Markdown')
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to edit message, sending new: {e}")
                await update.message.reply_text(first_message, parse_mode='Markdown')
            
            # Send additional messages if needed
            for additional_msg in messages[1:]:
                await update.message.reply_text(additional_msg, parse_mode='Markdown')
    
    async def _send_no_links_found(self, update: Update, processing_msg, url: str, request_id: str):
        """Send message when no video links are found."""
        logger.warning(f"[{request_id}] No links found for URL: {url}")
        
        domain = extract_domain_from_url(url)
        
        await processing_msg.edit_text(
            f"❌ **Không tìm thấy link streaming**\n\n"
            f"🌐 **Trang web:** {escape_markdown(domain)}\n\n"
            f"**Có thể do:**\n"
            f"• 🛡️ Trang web có bảo vệ chống bot\n"
            f"• 🔗 Link không phải trang tập phim\n"
            f"• 🔐 Video player sử dụng mã hóa đặc biệt\n"
            f"• 🌐 Trang web tạm thời không khả dụng\n"
            f"• 📱 Cần phải đăng nhập để xem\n\n"
            f"💡 **Gợi ý khắc phục:**\n"
            f"• 🔄 Thử link tập phim khác cùng website\n"
            f"• 🎬 Kiểm tra link có đúng trang tập phim\n"
            f"• ⏰ Thử lại sau 5-10 phút\n"
            f"• 🌐 Thử website khác cùng bộ phim\n\n"
            f"📝 Gõ /help để xem danh sách trang web được hỗ trợ",
            parse_mode='MarkdownV2'
        )
    
    async def handle_unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-URL messages."""
        message_text = update.message.text
        
        # Check if it looks like a URL but failed validation
        if any(indicator in message_text.lower() for indicator in ['http', 'www.', '.com', '.net', '.org']):
            await update.message.reply_text(
                get_user_friendly_error('invalid_url'),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❓ **Tin nhắn không được hỗ trợ**\n\n"
                "Bot này chỉ xử lý link trang tập phim\\.\n\n"
                "📝 **Để sử dụng bot:**\n"
                "1\\. Truy cập trang web xem phim\n"
                "2\\. Vào trang tập phim cụ thể\n"
                "3\\. Copy link và gửi cho bot\n\n"
                "❓ Gõ /help để xem hướng dẫn chi tiết",
                parse_mode='MarkdownV2'
            )


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL for display."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return "unknown"


def setup_bot_handlers(application):
    """Setup all bot command and message handlers."""
    handler = TelegramBotHandler()
    
    # Command handlers
    application.add_handler(CommandHandler("start", handler.start_command))
    application.add_handler(CommandHandler("help", handler.help_command))
    application.add_handler(CommandHandler("status", handler.status_command))
    
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
    
    logger.info("Bot handlers đã được thiết lập thành công")
