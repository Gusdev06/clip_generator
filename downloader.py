"""
YouTube video downloader module with Cobalt API support
Uses Cobalt API as primary method with yt-dlp as fallback
"""
import os
import yt_dlp
from pathlib import Path
import config
from cobalt_downloader import CobaltDownloader


class VideoDownloader:
    def __init__(self, download_dir=None, cookies_from_browser=None, cookies_file=None, use_cobalt=True):
        """
        Initialize the video downloader

        Args:
            download_dir: Directory to save downloaded videos (default: from config)
            cookies_from_browser: Browser name to extract cookies from (e.g., 'chrome', 'firefox')
            cookies_file: Path to Netscape cookies.txt file
            use_cobalt: Try Cobalt API first before yt-dlp (default: True)
        """
        self.download_dir = download_dir or config.DOWNLOAD_DIR
        self.cookies_from_browser = cookies_from_browser or config.YT_COOKIES_FROM_BROWSER
        self.cookies_file = cookies_file or config.YT_COOKIES_FILE
        self.use_cobalt = use_cobalt and config.USE_COBALT_API
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

        # Initialize Cobalt downloader if enabled
        if self.use_cobalt:
            self.cobalt = CobaltDownloader(download_dir=self.download_dir)
        else:
            self.cobalt = None

    def download(self, url, filename=None, audio_only=False):
        """
        Download a YouTube video or just audio

        Tries Cobalt API first, falls back to yt-dlp if Cobalt fails

        Args:
            url: YouTube video URL
            filename: Optional custom filename (without extension)
            audio_only: If True, download only audio (mp3)

        Returns:
            str: Path to the downloaded file
        """
        # Try Cobalt API first if enabled
        if self.cobalt:
            print(f"Downloading {'audio' if audio_only else 'video'} from: {url}")
            cobalt_result = self.cobalt.download(url, audio_only=audio_only, filename=filename)
            if cobalt_result:
                return cobalt_result
            else:
                print(f"  Cobalt failed, falling back to yt-dlp...")

        # Fallback to yt-dlp
        print(f"Downloading {'audio' if audio_only else 'video'} via yt-dlp from: {url}")
        return self._download_ytdlp(url, filename, audio_only)

    def _download_ytdlp(self, url, filename=None, audio_only=False):
        """
        Download using yt-dlp (fallback method)

        Args:
            url: YouTube video URL
            filename: Optional custom filename
            audio_only: Download audio only

        Returns:
            str: Path to downloaded file
        """
        # Configure yt-dlp options
        if audio_only:
            ydl_opts = {
                # More flexible audio format selection
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
                'prefer_ffmpeg': True,
            }
        else:
            ydl_opts = {
                # More flexible video format selection with fallbacks
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',
                'prefer_ffmpeg': True,
            }

        # Anti-bot headers to avoid YouTube blocking
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }

        # Cookie authentication (priority order)
        # 1. Use cookies file if provided
        if self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
            print(f"  Using cookies from file: {self.cookies_file}")

        # 2. Use cookies from browser if specified
        elif self.cookies_from_browser:
            try:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
                print(f"  Using cookies from browser: {self.cookies_from_browser}")
            except Exception as e:
                print(f"  Warning: Could not extract cookies from {self.cookies_from_browser}: {e}")

        # 3. Try to use Chrome cookies by default (helps avoid bot detection)
        elif os.path.exists(os.path.expanduser('~/.config/google-chrome')) or \
             os.path.exists(os.path.expanduser('~/Library/Application Support/Google/Chrome')):
            try:
                ydl_opts['cookiesfrombrowser'] = ('chrome',)
                print("  Using Chrome cookies for authentication")
            except Exception:
                pass  # If fails, continue without cookies

        # Use custom filename if provided
        if filename:
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, f'{filename}.%(ext)s')

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

        # Add anti-bot headers
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }

        # Use cookies if available (same priority as download method)
        if self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
        elif self.cookies_from_browser:
            try:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
            except Exception:
                pass

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
