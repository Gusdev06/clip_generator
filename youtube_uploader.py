"""
YouTube Uploader - Upload videos to YouTube Shorts
Handles OAuth2 authentication and video upload to YouTube using the YouTube Data API v3.
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

class YouTubeUploader:
    """
    YouTube uploader for Shorts videos.

    Features:
    - OAuth2 authentication with Google
    - Video upload to YouTube
    - Automatic Shorts categorization (videos < 60 seconds)
    - Metadata configuration (title, description, tags, category)
    """

    def __init__(
        self,
        client_secrets_file: str = 'client_secrets.json',
        credentials_file: str = 'youtube_credentials.pickle'
    ):
        """
        Initialize YouTube uploader.

        Args:
            client_secrets_file: Path to OAuth2 client secrets JSON file
            credentials_file: Path to store/load credentials pickle file
        """
        self.client_secrets_file = client_secrets_file
        self.credentials_file = credentials_file
        self.credentials = None
        self.youtube = None

    def authenticate(self) -> bool:
        """
        Authenticate with YouTube using OAuth2.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing credentials if available
            if os.path.exists(self.credentials_file):
                logger.info("Loading existing credentials...")
                with open(self.credentials_file, 'rb') as token:
                    self.credentials = pickle.load(token)

            # Refresh credentials if expired
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing expired credentials...")
                self.credentials.refresh(Request())

            # Get new credentials if needed
            if not self.credentials or not self.credentials.valid:
                if not os.path.exists(self.client_secrets_file):
                    logger.error(f"Client secrets file not found: {self.client_secrets_file}")
                    logger.error("Please download OAuth2 credentials from Google Cloud Console")
                    return False

                logger.info("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file,
                    SCOPES
                )
                self.credentials = flow.run_local_server(port=0)

                # Save credentials for future use
                with open(self.credentials_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
                logger.info("Credentials saved successfully")

            # Build YouTube API client
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            logger.info("YouTube API client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[list] = None,
        category_id: str = "22",  # 22 = People & Blogs
        privacy_status: str = "public",
        is_short: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a video to YouTube.

        Args:
            video_path: Path to the video file
            title: Video title (max 100 characters for Shorts)
            description: Video description
            tags: List of tags/keywords
            category_id: YouTube category ID (22 = People & Blogs, 24 = Entertainment)
            privacy_status: 'public', 'private', or 'unlisted'
            is_short: Whether this is a YouTube Short (< 60 seconds)

        Returns:
            Dict with upload response data or None if failed
        """
        if not self.youtube:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None

        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title[:100] if is_short else title,  # Shorts titles limited to 100 chars
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }

            # Add #Shorts hashtag for Shorts videos
            if is_short and '#Shorts' not in description and '#shorts' not in description:
                body['snippet']['description'] = f"{description}\n\n#Shorts"

            # Create media upload
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True,
                mimetype='video/mp4'
            )

            # Execute upload
            logger.info(f"Uploading video: {video_path}")
            logger.info(f"Title: {title}")
            logger.info(f"Privacy: {privacy_status}")

            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            shorts_url = f"https://www.youtube.com/shorts/{video_id}"

            logger.info(f"Upload successful!")
            logger.info(f"Video ID: {video_id}")
            logger.info(f"URL: {video_url}")
            if is_short:
                logger.info(f"Shorts URL: {shorts_url}")

            return {
                'video_id': video_id,
                'video_url': video_url,
                'shorts_url': shorts_url if is_short else None,
                'title': title,
                'privacy_status': privacy_status
            }

        except HttpError as e:
            logger.error(f"HTTP error occurred: {e}")
            if e.resp.status == 403:
                logger.error("Quota exceeded or API not enabled. Check Google Cloud Console.")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            return None

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[list] = None,
        privacy_status: str = "public"
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a YouTube Short (simplified method).

        Args:
            video_path: Path to the video file
            title: Video title (max 100 characters)
            description: Video description
            tags: List of tags/keywords
            privacy_status: 'public', 'private', or 'unlisted'

        Returns:
            Dict with upload response data or None if failed
        """
        return self.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id="24",  # Entertainment category for Shorts
            privacy_status=privacy_status,
            is_short=True
        )

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an uploaded video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with video information or None if failed
        """
        if not self.youtube:
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        try:
            request = self.youtube.videos().list(
                part='snippet,status,statistics',
                id=video_id
            )
            response = request.execute()

            if response['items']:
                return response['items'][0]
            else:
                logger.error(f"Video not found: {video_id}")
                return None

        except HttpError as e:
            logger.error(f"Failed to get video info: {e}")
            return None


def main():
    """Test the YouTube uploader."""
    # Example usage
    uploader = YouTubeUploader()

    # Authenticate
    if not uploader.authenticate():
        print("Authentication failed!")
        return

    print("Authentication successful!")
    print("\nTo upload a video, use:")
    print("uploader.upload_short(")
    print("    video_path='path/to/video.mp4',")
    print("    title='My YouTube Short',")
    print("    description='Check out this awesome short!',")
    print("    tags=['shorts', 'viral', 'entertainment']")
    print(")")


if __name__ == "__main__":
    main()
