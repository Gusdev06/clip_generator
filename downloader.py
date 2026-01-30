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
        Get yt-dlp options - OPTIMIZED FOR VPS/HOSTINGER
        """
        ydl_opts = {
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
            'ignoreerrors': True, # Importante para não travar a fila se um falhar
            'nocheckcertificate': True, # Ajuda em alguns ambientes SSL estritos
            
            # --- CONFIGURAÇÕES DE EVASÃO DE BOT ---
            
            # 1. User Agent Dinâmico (deixe o yt-dlp escolher ou use um muito comum)
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },

            # 2. Configurações do Extrator (CORRIGIDO)
            # REMOVEMOS 'player_skip': ['webpage'] pois isso causa o erro de Login
            'extractor_args': {
                'youtube': {
                    # 'web' e 'ios' são mais confiáveis que 'android' em datacenters hoje
                    'player_client': ['web', 'ios'],
                }
            },

            # 3. Intervalos para parecer humano
            'sleep_interval': 3,
            'max_sleep_interval': 10,
        }

        # Carregamento de Cookies
        if self.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
        elif self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
            print(f"  Using cookies from file: {self.cookies_file}")

        # Nome do arquivo
        if filename:
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, f'{filename}.%(ext)s')

        # Configurações de Áudio/Vídeo
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

        return ydl_opts
        
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
            # Ignore errors for unavailable formats and try alternatives
            'ignoreerrors': False,
            # Allow downloading age-restricted videos
            'age_limit': None,
            # Prefer free formats over premium
            'prefer_free_formats': True,
            # Add User-Agent to simulate a real browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Sec-Fetch-Mode': 'navigate',
            },
            # Extractor arguments to bypass bot detection
            'extractor_args': {
                'youtube': {
                    # Use Android/iOS clients which are less restricted
                    'player_client': ['android', 'ios', 'web'],
                    # Skip problematic extraction methods
                    'player_skip': ['webpage'],
                }
            },
            # Retry configuration
            'retries': 3,
            'fragment_retries': 3,
            # Sleep between requests to avoid rate limiting
            'sleep_interval': 1,
            'max_sleep_interval': 3,
        }

        # Add cookies if available
        if self.cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookies_from_browser,)
            print(f"  Using cookies from browser: {self.cookies_from_browser}")
        elif self.cookies_file and os.path.exists(self.cookies_file):
            ydl_opts['cookiefile'] = self.cookies_file
            print(f"  Using cookies from file: {self.cookies_file}")
            # Verify file is readable
            try:
                with open(self.cookies_file, 'r') as f:
                    cookie_content = f.read()
                    cookie_lines = [line for line in cookie_content.split('\n') if line and not line.startswith('#')]
                    print(f"  Cookies file loaded: {len(cookie_lines)} cookie entries found")
            except Exception as e:
                print(f"  WARNING: Could not read cookies file: {e}")
        else:
            print(f"  WARNING: No cookies configured! This may cause bot detection.")
            print(f"  Looking for cookies at: {self.cookies_file}")
            print(f"  File exists: {os.path.exists(self.cookies_file) if self.cookies_file else 'No path set'}")

        # Custom filename
        if filename:
            ydl_opts['outtmpl'] = os.path.join(self.download_dir, f'{filename}.%(ext)s')

        # Audio-only settings
        if audio_only:
            # More flexible audio format selection
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # More flexible video format selection with fallbacks
            # Try best video+audio, then best single file, then any available format
            ydl_opts['format'] = (
                'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/'  # Best H.264 MP4 + M4A audio
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/'  # Any MP4 + M4A audio, or best MP4
                'bestvideo+bestaudio/best'  # Fallback to any video+audio or best available
            )
            # Merge into MP4 container
            ydl_opts['merge_output_format'] = 'mp4'

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
                # Use Android client for metadata extraction
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios', 'web'],
                        'player_skip': ['webpage'],
                    }
                },
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
