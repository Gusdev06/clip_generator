"""
YouTube video downloader module
"""
import os
import yt_dlp
from pathlib import Path
import config


class VideoDownloader:
    def __init__(self, download_dir=None, cookies_from_browser=None):
        """
        Initialize the video downloader

        Args:
            download_dir: Directory to save downloaded videos (default: from config)
            cookies_from_browser: Browser name to extract cookies from (e.g., 'chrome', 'firefox')
        """
        self.download_dir = download_dir or config.DOWNLOAD_DIR
        self.cookies_from_browser = cookies_from_browser
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

    def download(self, url, filename=None, audio_only=False):
        """
        Download a YouTube video or just audio
        
        Args:
            url: YouTube video URL
            filename: Optional custom filename (without extension)
            audio_only: If True, download only audio (mp3)
            
        Returns:
            str: Path to the downloaded file
        """
        # Configure yt-dlp options
        if audio_only:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
            }
        else:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',
            }

        # Add cookies from browser if specified
        if self.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

        # Use custom filename if provided
        if filename:
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, f'{filename}.%(ext)s')

        print(f"Downloading {'audio' if audio_only else 'video'} from: {url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info = ydl.extract_info(url, download=True)

            # Get the actual downloaded file path
            if filename:
                ext = 'mp3' if audio_only else 'mp4'
                file_path = os.path.join(self.download_dir, f'{filename}.{ext}')
            else:
                # Use yt-dlp's prepare_filename -> but we need to handle mp3 conversion path
                # Ideally, we should trust prepare_filename but postprocessors might change ext
                file_path = ydl.prepare_filename(info)
                if audio_only:
                    file_path = os.path.splitext(file_path)[0] + '.mp3'

            print(f"Download successful: {file_path}")
            return file_path

    def get_video_info(self, url):
        """
        Get video information without downloading

        Args:
            url: YouTube video URL

        Returns:
            dict: Video information
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        if self.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count'),
                'upload_date': info.get('upload_date'),
            }


if __name__ == "__main__":
    # Test the downloader
    downloader = VideoDownloader()
    test_url = input("Enter YouTube URL to test: ")

    # Get video info first
    info = downloader.get_video_info(test_url)
    print(f"\nVideo Info:")
    print(f"Title: {info['title']}")
    print(f"Duration: {info['duration']} seconds")
    print(f"Uploader: {info['uploader']}")

    # Download
    video_path = downloader.download(test_url)
    print(f"\nDownloaded to: {video_path}")
