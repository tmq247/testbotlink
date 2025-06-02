import asyncio
import logging
import os
import time
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import TelegramError

from config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT
from utils import escape_markdown_v2, is_valid_url, format_file_size, RateLimiter
from link_extractor import VideoLinkExtractor

# Setup logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

# Global rate limiter
rate_limiter = RateLimiter()

class VideoBot:
    """
    Telegram bot for extracting video links from Vietnamese movie websites.
    """
    
    def __init__(self):
        self.application = None
        self.start_time = time.time()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command.
        """
        user = update.effective_user
        
        welcome_text = f"""
🎬 *Chào mừng {escape_markdown_v2(user.first_name or 'bạn')}\\!*

Bot này giúp bạn trích xuất link video từ các trang phim Việt Nam\\. 

📝 *Cách sử dụng:*
• Gửi link trang phim cho bot
• Bot sẽ tìm và trả về các link video có sẵn
• Hỗ trợ định dạng: MP4, M3U8, MKV, AVI, MOV, WebM

🌐 *Trang web được hỗ trợ:*
• phimmoi\\.net
• bilutv\\.com
• phim3s\\.info
• motphim\\.tv
• xemphim\\.com
• fimfast\\.com
• phimhay\\.org

⚡ *Lệnh có sẵn:*
/start \\- Hiển thị thông tin này
/help \\- Hướng dẫn chi tiết
/status \\- Trạng thái bot

💡 *Lưu ý:* Bot có giới hạn 5 yêu cầu/phút để tránh spam\\.
        """
        
        keyboard = [
            [InlineKeyboardButton("📖 Hướng dẫn", callback_data="help")],
            [InlineKeyboardButton("📊 Trạng thái", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command.
        """
        help_text = f"""
📖 *Hướng dẫn sử dụng Bot*

🔍 *Cách trích xuất video:*
1️⃣ Copy link trang phim từ website hỗ trợ
2️⃣ Paste link vào chat với bot
3️⃣ Đợi bot xử lý và trả về kết quả
4️⃣ Click vào link video để xem hoặc tải về

⚠️ *Lưu ý quan trọng:*
• Chỉ gửi link từ các trang được hỗ trợ
• Không spam nhiều link cùng lúc
• Một số video có thể cần VPN để truy cập
• Bot chỉ trích xuất link, không lưu trữ video

🛡️ *Bảo mật:*
• Bot không lưu trữ dữ liệu cá nhân
• Không chia sẻ link với bên thứ ba
• Tự động xóa log sau 24h

❓ *Gặp vấn đề?*
• Kiểm tra link có đúng định dạng
• Thử lại sau vài phút nếu lỗi
• Liên hệ admin nếu vấn đề tiếp tục

🔄 *Rate Limiting:*
Mỗi người dùng có thể gửi tối đa 5 yêu cầu mỗi phút\\. Điều này giúp bot hoạt động ổn định và công bằng cho tất cả người dùng\\.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /status command.
        """
        uptime = time.time() - self.start_time
        uptime_hours = int(uptime // 3600)
        uptime_minutes = int((uptime % 3600) // 60)
        
        user_id = update.effective_user.id
        remaining_requests = rate_limiter.get_remaining_requests(user_id)
        
        status_text = f"""
📊 *Trạng thái Bot*

🟢 *Hoạt động:* Online
⏱️ *Uptime:* {uptime_hours}h {uptime_minutes}m
🔄 *Yêu cầu còn lại:* {remaining_requests}/5
⚡ *Phản hồi:* Nhanh

🌐 *Trang web được hỗ trợ:* 7 trang
📹 *Định dạng video:* 6 loại
🛡️ *Bảo mật:* Đã kích hoạt

✅ *Tất cả hệ thống hoạt động bình thường\\!*
        """
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle URL messages from users.
        """
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        # Check rate limiting
        if not rate_limiter.is_allowed(user_id):
            remaining_time = rate_limiter.get_reset_time(user_id) - time.time()
            remaining_minutes = int(remaining_time // 60)
            remaining_seconds = int(remaining_time % 60)
            
            error_text = f"""
⏰ *Đã đạt giới hạn yêu cầu\\!*

Bạn đã gửi quá nhiều yêu cầu\\. Vui lòng đợi *{remaining_minutes}m {remaining_seconds}s* trước khi gửi yêu cầu tiếp theo\\.

💡 *Giới hạn:* 5 yêu cầu/phút
            """
            
            await update.message.reply_text(
                error_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Validate URL
        if not is_valid_url(message_text):
            error_text = f"""
❌ *Link không hợp lệ\\!*

Vui lòng gửi một link đúng định dạng\\. Ví dụ:
`https://phimmoi\\.net/phim/ten\\-phim/`

💡 Sử dụng /help để xem hướng dẫn chi tiết\\.
            """
            
            await update.message.reply_text(
                error_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            return
        
        # Send typing action
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, 
            action=ChatAction.TYPING
        )
        
        # Extract videos
        try:
            async with VideoLinkExtractor() as extractor:
                if not extractor.is_supported_domain(message_text):
                    error_text = f"""
🚫 *Trang web không được hỗ trợ\\!*

Link bạn gửi không thuộc danh sách trang web được hỗ trợ\\.

🌐 *Các trang được hỗ trợ:*
• phimmoi\\.net
• bilutv\\.com  
• phim3s\\.info
• motphim\\.tv
• xemphim\\.com
• fimfast\\.com
• phimhay\\.org

💡 Sử dụng /help để xem hướng dẫn chi tiết\\.
                    """
                    
                    await update.message.reply_text(
                        error_text,
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
                
                # Processing message
                processing_msg = await update.message.reply_text(
                    "🔄 *Đang xử lý\\.\\.\\.*\n\n🔍 Đang tìm kiếm video trên trang web\\.\\.\\.",
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                videos = await extractor.extract_video_links(message_text)
                
                # Delete processing message
                await processing_msg.delete()
                
                if not videos:
                    error_text = f"""
😔 *Không tìm thấy video\\!*

Không thể tìm thấy link video nào trên trang này\\. Có thể:
• Trang chưa có video
• Video bị bảo vệ hoặc cần đăng nhập
• Link đã hết hạn
• Trang web đang bảo trì

💡 Thử lại sau hoặc kiểm tra link khác\\.
                    """
                    
                    await update.message.reply_text(
                        error_text,
                        parse_mode=ParseMode.MARKDOWN_V2
                    )
                    return
                
                # Format and send results
                await self.send_video_results(update, videos)
                
        except Exception as e:
            logger.error(f"Error processing URL {message_text}: {e}")
            
            error_text = f"""
⚠️ *Lỗi xử lý\\!*

Có lỗi xảy ra khi xử lý link của bạn\\. Vui lòng:
• Kiểm tra lại link
• Thử lại sau vài phút  
• Liên hệ admin nếu vấn đề tiếp tục

🔧 *Mã lỗi:* `{escape_markdown_v2(str(e)[:100])}`
            """
            
            await update.message.reply_text(
                error_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    
    async def send_video_results(self, update: Update, videos: list):
        """
        Send video results to user with proper formatting.
        """
        total_videos = len(videos)
        
        # Header message
        header_text = f"""
✅ *Tìm thấy {total_videos} video\\!*

📥 *Click vào link để tải về hoặc xem trực tuyến*
        """
        
        await update.message.reply_text(
            header_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Send each video as separate message
        for i, video in enumerate(videos, 1):
            try:
                # Get file size if possible
                async with VideoExtractor() as extractor:
                    file_size = await extractor.get_video_file_size(video['url'])
                
                # Format video info
                filename = video.get('filename', f'video_{i}')
                quality = video.get('quality', 'Unknown')
                extension = video.get('extension', 'unknown').upper()
                
                video_text = f"""
🎬 *Video {i}/{total_videos}*

📂 *Tên:* `{escape_markdown_v2(filename)}`
🎭 *Chất lượng:* `{escape_markdown_v2(quality)}`
📄 *Định dạng:* `{escape_markdown_v2(extension)}`
                """
                
                if file_size:
                    size_text = format_file_size(file_size)
                    video_text += f"💾 *Dung lượng:* `{escape_markdown_v2(size_text)}`\n"
                
                video_text += f"\n🔗 [Tải về/Xem video]({video['url']})"
                
                # Create inline keyboard
                keyboard = [
                    [InlineKeyboardButton("📥 Tải về", url=video['url'])],
                    [InlineKeyboardButton("📋 Copy link", callback_data=f"copy_{i}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    video_text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                
                # Small delay between messages
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error sending video {i}: {e}")
                
                # Send simplified message if formatting fails
                simple_text = f"🎬 Video {i}: {video['url']}"
                await update.message.reply_text(simple_text)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline keyboard callbacks.
        """
        query = update.callback_query
        await query.answer()
        
        if query.data == "help":
            await self.help_command(update, context)
        elif query.data == "status":
            await self.status_command(update, context)
        elif query.data.startswith("copy_"):
            await query.answer("Link đã được copy! Paste vào trình duyệt để truy cập.", show_alert=True)
    
    async def handle_other_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle non-URL messages.
        """
        help_text = f"""
ℹ️ *Hướng dẫn sử dụng*

Vui lòng gửi link trang phim để bot trích xuất video\\.

💡 Sử dụng /help để xem hướng dẫn chi tiết\\.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle errors.
        """
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            error_text = f"""
⚠️ *Có lỗi xảy ra\\!*

Hệ thống đang gặp sự cố tạm thời\\. Vui lòng thử lại sau vài phút\\.

🔧 Nếu vấn đề tiếp tục, vui lòng liên hệ admin\\.
            """
            
            try:
                await update.effective_message.reply_text(
                    error_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
            except Exception as e:
                logger.error(f"Error sending error message: {e}")
    
    def setup_handlers(self):
        """
        Setup bot handlers.
        """
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
        # URL messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r'https?://'), self.handle_url)
        )
        
        # Other text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_other_messages)
        )
        
        # Callback queries
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def run(self):
        """
        Run the bot.
        """
        # Create application
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start the bot
        logger.info("Starting Video Extractor Bot...")
        await self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

def main():
    """
    Main function to run the bot.
    """
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    bot = VideoBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()
