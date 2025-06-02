#!/usr/bin/env python3
"""
Test script để kiểm tra bot với link phim cụ thể
"""

import asyncio
from link_extractor import VideoLinkExtractor

async def test_video_extraction():
    """Test trích xuất video từ link cụ thể"""
    test_url = "https://phim1080.app/chien-tranh-giua-cac-vi-sao-andor-phan-2/tap-1/"
    
    print(f"🔍 Testing video extraction from: {test_url}")
    print("=" * 50)
    
    try:
        async with VideoLinkExtractor() as extractor:
            # Kiểm tra domain có được hỗ trợ không
            if not extractor.is_supported_domain(test_url):
                print("⚠️ Domain không trong danh sách hỗ trợ")
                print("Thêm 'tvhay.fm' vào SUPPORTED_DOMAINS trong config.py")
                return
            
            print("✅ Domain được hỗ trợ")
            print("🔄 Đang trích xuất video links...")
            
            # Trích xuất video links
            videos = await extractor.extract_video_links(test_url)
            
            if videos:
                print(f"✅ Tìm thấy {len(videos)} video links:")
                for i, video in enumerate(videos, 1):
                    print(f"\n🎬 Video {i}:")
                    print(f"  📂 Filename: {video.get('filename', 'Unknown')}")
                    print(f"  🎭 Quality: {video.get('quality', 'Unknown')}")
                    print(f"  📄 Extension: {video.get('extension', 'Unknown')}")
                    print(f"  🔗 URL: {video.get('url', '')}")
            else:
                print("❌ Không tìm thấy video links")
                print("Có thể do:")
                print("• Trang web sử dụng JavaScript động")
                print("• Video player được bảo vệ")
                print("• Cần đăng nhập để xem")
                
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    asyncio.run(test_video_extraction())
