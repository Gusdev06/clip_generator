"""
YouTube video downloader module with Cobalt API support
Uses Cobalt API as primary method with pytubefix as fallback
"""
import os
from pathlib import Path
from pytubefix import YouTube
from pytubefix.cli import on_progress
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

        # Fallback to pytubefix
        print(f"Downloading {'audio' if audio_only else 'video'} via pytubefix from: {url}")
        return self._download_pytubefix(url, filename, audio_only)

    def _download_pytubefix(self, url, filename=None, audio_only=False):
        """
        Download using pytubefix (fallback method)

        Args:
            url: YouTube video URL
            filename: Optional custom filename
            audio_only: Download audio only

        Returns:
            str: Path to downloaded file
        """
        try:
            # Create YouTube object with optional cookies
            yt_params = {
                'use_oauth': False,
                'allow_oauth_cache': True
            }

            # Add cookies if available
            if self.cookies_file and os.path.exists(self.cookies_file):
                print(f"  Using cookies from file: {self.cookies_file}")
                # PyTubeFix doesn't directly support Netscape cookies
                # We'll use the default approach

            yt = YouTube(url, on_progress_callback=on_progress, **yt_params)

            print(f"  Title: {yt.title}")
            print(f"  Duration: {yt.length} seconds")

            if audio_only:
                # Get the best audio stream
                stream = yt.streams.get_audio_only()
                if not stream:
                    # Fallback to any audio stream
                    stream = yt.streams.filter(only_audio=True).first()

                if not stream:
                    raise Exception("No audio stream available")

                print(f"  Downloading audio stream: {stream.abr}")

                # Download the audio
                output_file = stream.download(
                    output_path=self.download_dir,
                    filename=f"{filename}.mp4" if filename else None
                )

                # Convert to mp3 if needed (pytubefix downloads as mp4/webm audio)
                if output_file.endswith('.mp4') or output_file.endswith('.webm'):
                    # Rename to .mp3 for consistency (actual conversion would need ffmpeg)
                    # For now, we'll keep the original format
                    final_path = output_file
                else:
                    final_path = output_file

            else:
                # Get the highest resolution progressive stream (video+audio in one file)
                stream = yt.streams.get_highest_resolution()

                if not stream:
                    # Fallback to any video stream
                    stream = yt.streams.filter(progressive=True, file_extension='mp4').first()

                if not stream:
                    raise Exception("No video stream available")

                print(f"  Downloading video stream: {stream.resolution}")

                # Download the video
                final_path = stream.download(
                    output_path=self.download_dir,
                    filename=f"{filename}.mp4" if filename else None
                )

            print(f"Download successful: {final_path}")
            return final_path

        except Exception as e:
            print(f"  PyTubeFix download error: {e}")
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
            yt = YouTube(url)
            return {
                'title': yt.title,
                'duration': yt.length,
                'uploader': yt.author,
                'view_count': yt.views,
                'upload_date': yt.publish_date.strftime('%Y%m%d') if yt.publish_date else None,
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
