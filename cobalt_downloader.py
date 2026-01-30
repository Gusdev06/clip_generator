"""
Cobalt API downloader - Alternative YouTube downloader
Cobalt.tools is a free, open-source media downloader that supports YouTube and many other platforms
"""
import os
import requests
from pathlib import Path
from typing import Optional, Dict
import config


class CobaltDownloader:
    def __init__(self, download_dir=None, api_url=None):
        """
        Initialize Cobalt API downloader

        Args:
            download_dir: Directory to save downloads
            api_url: Cobalt API endpoint (default: official instance)
        """
        self.download_dir = download_dir or config.DOWNLOAD_DIR
        self.api_url = api_url or config.COBALT_API_URL or "https://api.cobalt.tools"
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)

    def download(self, url: str, audio_only: bool = False, filename: Optional[str] = None) -> Optional[str]:
        """
        Download video or audio using Cobalt API

        Args:
            url: YouTube video URL
            audio_only: Download only audio (mp3)
            filename: Optional custom filename

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            print(f"  Attempting download via Cobalt API...")

            # Prepare request payload (Cobalt API v7+ format)
            payload = {
                "url": url,
                "videoQuality": "max",  # max, 2160, 1440, 1080, 720, 480, 360, 240, 144
                "audioFormat": "mp3" if audio_only else "best",  # best, mp3, ogg, wav, opus
                "filenameStyle": "basic",  # basic, pretty, nerdy
                "downloadMode": "audio" if audio_only else "auto",  # auto, audio, mute
            }

            # Send request to Cobalt API
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.api_url}/",  # Updated endpoint
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ⚠️  Cobalt API returned status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Error details: {error_data}")
                except:
                    print(f"  Response text: {response.text[:200]}")
                return None

            data = response.json()

            # Check response status (Cobalt API v7+)
            status = data.get("status")

            if status == "error" or status == "rate-limit":
                error_text = data.get("error", {}).get("code", "Unknown error")
                print(f"  ⚠️  Cobalt API error: {error_text}")
                return None

            # Get download URL - can be in 'url' field for direct downloads
            download_url = data.get("url")

            # Or in 'urls' array for picker mode
            if not download_url and "picker" in data:
                picker_items = data.get("picker", [])
                if picker_items:
                    download_url = picker_items[0].get("url")

            if not download_url:
                print(f"  ⚠️  No download URL in Cobalt response")
                print(f"  Debug: {data}")
                return None

            # Download the file
            print(f"  Downloading from Cobalt...")
            file_response = requests.get(download_url, stream=True, timeout=300)

            if file_response.status_code != 200:
                print(f"  ⚠️  Failed to download file: HTTP {file_response.status_code}")
                return None

            # Determine filename
            if filename:
                ext = 'mp3' if audio_only else 'mp4'
                output_path = os.path.join(self.download_dir, f"{filename}.{ext}")
            else:
                # Try to get filename from Content-Disposition header
                content_disposition = file_response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    suggested_name = content_disposition.split('filename=')[1].strip('"')
                    output_path = os.path.join(self.download_dir, suggested_name)
                else:
                    # Fallback to generic name
                    ext = 'mp3' if audio_only else 'mp4'
                    output_path = os.path.join(self.download_dir, f"cobalt_download.{ext}")

            # Save file
            with open(output_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"  ✅ Downloaded via Cobalt: {output_path}")
            return output_path

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Cobalt API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Cobalt API request error: {e}")
            return None
        except Exception as e:
            print(f"  ⚠️  Cobalt download error: {e}")
            return None

    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information (Cobalt doesn't provide metadata API, returns None)

        Args:
            url: Video URL

        Returns:
            None (Cobalt doesn't provide metadata endpoint)
        """
        # Cobalt API doesn't provide a metadata-only endpoint
        # We'll need to use yt-dlp for this
        return None
