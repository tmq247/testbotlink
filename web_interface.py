"""
Web interface for the Telegram Movie Link Extractor Bot.
Provides a simple web dashboard for monitoring and testing.
"""

import logging
from aiohttp import web, ClientSession
from aiohttp.web import Application, Request, Response, RouteTableDef
import json
import asyncio

from link_extractor import VideoLinkExtractor
from config import BOT_TOKEN, DEBUG_MODE
from security import sanitize_url, validate_user_input
from utils import format_file_size, extract_domain

logger = logging.getLogger(__name__)
routes = RouteTableDef()


class WebInterface:
    """Web interface for bot monitoring and testing."""
    
    def __init__(self, bot_app=None):
        self.bot_app = bot_app
        self.link_extractor = VideoLinkExtractor()
        self.stats = {
            'requests_processed': 0,
            'links_found': 0,
            'errors': 0,
            'uptime_start': None
        }
    
    async def get_bot_info(self) -> dict:
        """Get basic bot information."""
        if not self.bot_app:
            return {'status': 'Bot not initialized'}
        
        try:
            bot = self.bot_app.bot
            bot_info = await bot.get_me()
            
            return {
                'status': 'Active',
                'username': bot_info.username,
                'first_name': bot_info.first_name,
                'id': bot_info.id,
                'can_join_groups': bot_info.can_join_groups,
                'can_read_all_group_messages': bot_info.can_read_all_group_messages,
                'supports_inline_queries': bot_info.supports_inline_queries
            }
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return {'status': 'Error', 'error': str(e)}


@routes.get('/')
async def index(request: Request) -> Response:
    """Main dashboard page."""
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return Response(text=html_content, content_type='text/html')


@routes.get('/api/status')
async def api_status(request: Request) -> Response:
    """API endpoint for bot status."""
    web_interface = request.app['web_interface']
    
    try:
        bot_info = await web_interface.get_bot_info()
        
        status_data = {
            'bot': bot_info,
            'stats': web_interface.stats,
            'server': {
                'debug_mode': DEBUG_MODE,
                'uptime': 'Running'
            }
        }
        
        return Response(
            text=json.dumps(status_data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error in status API: {e}")
        return Response(
            text=json.dumps({'error': str(e)}, ensure_ascii=False),
            content_type='application/json',
            status=500
        )


@routes.post('/api/extract')
async def api_extract(request: Request) -> Response:
    """API endpoint for testing video link extraction."""
    web_interface = request.app['web_interface']
    
    try:
        data = await request.json()
        url = data.get('url', '').strip()
        
        # Validate input
        if not validate_user_input(url):
            return Response(
                text=json.dumps({'error': 'Invalid URL format'}, ensure_ascii=False),
                content_type='application/json',
                status=400
            )
        
        # Sanitize URL
        clean_url = sanitize_url(url)
        if not clean_url:
            return Response(
                text=json.dumps({'error': 'URL failed security validation'}, ensure_ascii=False),
                content_type='application/json',
                status=400
            )
        
        # Extract links
        web_interface.stats['requests_processed'] += 1
        
        try:
            links = await web_interface.link_extractor.extract_video_links(clean_url)
            
            if links:
                web_interface.stats['links_found'] += len(links)
                
                result = {
                    'success': True,
                    'url': clean_url,
                    'domain': extract_domain(clean_url),
                    'links_count': len(links),
                    'links': links
                }
            else:
                result = {
                    'success': False,
                    'url': clean_url,
                    'domain': extract_domain(clean_url),
                    'links_count': 0,
                    'message': 'No video links found'
                }
            
            return Response(
                text=json.dumps(result, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
            
        except asyncio.TimeoutError:
            web_interface.stats['errors'] += 1
            return Response(
                text=json.dumps({'error': 'Request timeout'}, ensure_ascii=False),
                content_type='application/json',
                status=408
            )
        
    except Exception as e:
        logger.error(f"Error in extract API: {e}")
        web_interface.stats['errors'] += 1
        return Response(
            text=json.dumps({'error': str(e)}, ensure_ascii=False),
            content_type='application/json',
            status=500
        )


@routes.get('/static/{filename}')
async def static_files(request: Request) -> Response:
    """Serve static files."""
    filename = request.match_info['filename']
    
    # Security check
    if '..' in filename or '/' in filename:
        raise web.HTTPNotFound()
    
    try:
        import os
        static_path = os.path.join(os.getcwd(), 'static', filename)
        
        if not os.path.exists(static_path):
            raise web.HTTPNotFound()
        
        if filename.endswith('.css'):
            with open(static_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(text=content, content_type='text/css')
        
        elif filename.endswith('.js'):
            with open(static_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(text=content, content_type='application/javascript')
        
        else:
            raise web.HTTPNotFound()
    
    except FileNotFoundError:
        raise web.HTTPNotFound()
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        raise web.HTTPNotFound()


def create_web_app(bot_app=None) -> Application:
    """Create and configure the web application."""
    app = Application()
    
    # Add web interface instance
    web_interface = WebInterface(bot_app)
    app['web_interface'] = web_interface
    app['bot_app'] = bot_app
    
    # Add routes
    app.router.add_routes(routes)
    
    # Simple error handling without middleware for now
    # app.middlewares.append(error_handler)
    
    logger.info("Web interface đã được khởi tạo")
    return app
