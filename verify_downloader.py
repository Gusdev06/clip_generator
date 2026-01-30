
from downloader import VideoDownloader
import os

def test_downloader_init():
    try:
        downloader = VideoDownloader()
        print("✅ VideoDownloader initialized successfully")
        
        # Test getting options to see if methods are linked correctly
        opts = downloader._get_ydl_opts(audio_only=True)
        print("✅ _get_ydl_opts executed successfully")
        assert opts['format'] == 'bestaudio/best'
        
        # Test with filename
        opts = downloader._get_ydl_opts(filename="test_video")
        print("✅ _get_ydl_opts with filename executed successfully")
        assert "test_video" in opts['outtmpl']
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_downloader_init()
