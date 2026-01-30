"""
YouTube video downloader module using yt-dlp
"""
import os
from pathlib import Path
import yt_dlp
import config


class VideoDownloader:
    def __init__(self, download_dir=None, cookies_from_browser=None, cookies_file=None):
        """
        Initialize the video downloader

        Args:
            download_dir: Directory to save downloaded videos (default: from config)
            cookies_from_browser: Browser name to extract cookies from (e.g., 'chrome', 'firefox')
            cookies_file: Path to Netscape cookies.txt file
        """
        self.download_dir = download_dir or config.DOWNLOAD_DIR
        self.cookies_from_browser = cookies_from_browser or config.YT_COOKIES_FROM_BROWSER
        self.cookies_file = cookies_file or config.YT_COOKIES_FILE
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

    def _get_ydl_opts(self, audio_only=False, filename=None):
        """
        Get yt-dlp options

        Args:
            audio_only: If True, download only audio
            filename: Optional custom filename (without extension)

        Returns:
            dict: yt-dlp options
        """
        # Base options
        ydl_opts = {
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
        }

        # Add cookies if available
        if self.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
            print(f"  Using cookies from browser: {self.cookies_from_browser}")
        elif self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
            print(f"  Using cookies from file: {self.cookies_file}")

        # Custom filename
        if filename:
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, f'{filename}.%(ext)s')

        # Audio-only settings
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # Best video + best audio
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        return ydl_opts

    def _progress_hook(self, d):
        """
        Progress hook for yt-dlp

        Args:
            d: Download progress dictionary
        """
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                print(f"\r  Downloading: {percent:.1f}%", end='', flush=True)
            elif '_percent_str' in d:
                print(f"\r  Downloading: {d['_percent_str']}", end='', flush=True)
        elif d['status'] == 'finished':
            print(f"\n  Download complete, processing...")

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
        print(f"Downloading {'audio' if audio_only else 'video'} from: {url}")

        ydl_opts = self._get_ydl_opts(audio_only=audio_only, filename=filename)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info to get the filename
                info = ydl.extract_info(url, download=True)

                # Get the downloaded file path
                if audio_only:
                    # For audio, the file will be converted to mp3
                    if filename:
                        final_path = os.path.join(self.download_dir, f'{filename}.mp3')
                    else:
                        final_path = os.path.join(self.download_dir, f"{info['title']}.mp3")
                else:
                    # For video
                    if filename:
                        final_path = os.path.join(self.download_dir, f'{filename}.mp4')
                    else:
                        final_path = ydl.prepare_filename(info)

                print(f"Download successful: {final_path}")
                return final_path

        except Exception as e:
            print(f"  Download error: {e}")
            raise

    def get_video_info(self, url):
        """
        Get video information without downloading

        Args:
            url: YouTube video URL

        Returns:
            dict: Video information
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }

            # Add cookies if available
            if self.cookies_from_browser:
                ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
            elif self.cookies_file and os.path.exists(self.cookies_file):
                ydl_opts['cookiefile'] = self.cookies_file

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None


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
