#!/usr/bin/env python3
"""
Upload YouTube Shorts - Automated upload script for generated clips
Uploads processed video clips to YouTube Shorts with metadata from title generation.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from youtube_uploader import YouTubeUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_video_metadata(video_path: str) -> Optional[Dict[str, Any]]:
    """
    Find metadata file for a video clip.

    Args:
        video_path: Path to the video file

    Returns:
        Dict with metadata or None if not found
    """
    video_file = Path(video_path)

    # Look for metadata in various formats
    # 1. JSON file with same name
    metadata_json = video_file.with_suffix('.json')
    if metadata_json.exists():
        try:
            with open(metadata_json, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata from {metadata_json}: {e}")

    # 2. Look in parent directory for titles.json
    titles_file = video_file.parent / 'titles.json'
    if titles_file.exists():
        try:
            with open(titles_file, 'r', encoding='utf-8') as f:
                titles_data = json.load(f)
                video_name = video_file.stem

                # Search for matching clip
                for clip_data in titles_data.get('clips', []):
                    if video_name in clip_data.get('clip_file', ''):
                        return clip_data
        except Exception as e:
            logger.warning(f"Failed to load titles from {titles_file}: {e}")

    return None


def prepare_upload_metadata(
    video_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    custom_title: Optional[str] = None,
    custom_description: Optional[str] = None,
    custom_tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Prepare upload metadata from various sources.

    Args:
        video_path: Path to the video file
        metadata: Metadata dict from JSON files
        custom_title: Custom title override
        custom_description: Custom description override
        custom_tags: Custom tags override

    Returns:
        Dict with upload parameters
    """
    video_file = Path(video_path)

    # Default values
    title = custom_title or video_file.stem
    description = custom_description or ""
    tags = custom_tags or []

    # Extract from metadata if available
    if metadata:
        # Try different title sources
        if not custom_title:
            # From viral curator (Portuguese titles)
            if 'titles' in metadata and metadata['titles']:
                title = metadata['titles'][0]  # Use first title
            elif 'title' in metadata:
                title = metadata['title']
            elif 'viral_clip' in metadata:
                viral_data = metadata['viral_clip']
                if 'hook_text' in viral_data:
                    title = viral_data['hook_text'][:100]

        # Build description from metadata
        if not custom_description:
            desc_parts = []

            # Add original video info
            if 'original_video' in metadata:
                desc_parts.append(f"📹 Vídeo original: {metadata['original_video']}")

            # Add viral clip info
            if 'viral_clip' in metadata:
                viral_data = metadata['viral_clip']

                if 'hook_type' in viral_data:
                    desc_parts.append(f"\n🎯 Tipo de gancho: {viral_data['hook_type']}")

                if 'viral_mechanics' in viral_data:
                    mechanics = ', '.join(viral_data['viral_mechanics'][:3])
                    desc_parts.append(f"⚡ Mecânicas virais: {mechanics}")

                if 'retention_prediction' in viral_data:
                    desc_parts.append(f"📊 Retenção prevista: {viral_data['retention_prediction']}%")

            description = '\n'.join(desc_parts)

        # Extract tags
        if not custom_tags:
            tags = []

            # Add from metadata
            if 'tags' in metadata:
                tags.extend(metadata['tags'])

            # Add from viral mechanics
            if 'viral_clip' in metadata and 'viral_mechanics' in metadata['viral_clip']:
                tags.extend(metadata['viral_clip']['viral_mechanics'][:5])

            # Add default tags
            default_tags = ['shorts', 'viral', 'cortes']
            tags.extend([t for t in default_tags if t not in tags])

    # Ensure title is not too long for Shorts (100 char limit)
    if len(title) > 100:
        title = title[:97] + "..."

    return {
        'title': title,
        'description': description,
        'tags': tags[:15]  # YouTube allows max 15 tags
    }


def upload_single_video(
    uploader: YouTubeUploader,
    video_path: str,
    privacy: str = "public",
    custom_title: Optional[str] = None,
    custom_description: Optional[str] = None,
    custom_tags: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Upload a single video to YouTube Shorts.

    Args:
        uploader: YouTubeUploader instance
        video_path: Path to video file
        privacy: Privacy status ('public', 'private', 'unlisted')
        custom_title: Optional custom title
        custom_description: Optional custom description
        custom_tags: Optional custom tags

    Returns:
        Upload response dict or None
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {video_path}")
    logger.info(f"{'='*60}")

    # Find metadata
    metadata = find_video_metadata(video_path)
    if metadata:
        logger.info("✓ Found metadata file")
    else:
        logger.info("⚠ No metadata found, using defaults")

    # Prepare upload parameters
    upload_params = prepare_upload_metadata(
        video_path=video_path,
        metadata=metadata,
        custom_title=custom_title,
        custom_description=custom_description,
        custom_tags=custom_tags
    )

    logger.info(f"\nUpload parameters:")
    logger.info(f"  Title: {upload_params['title']}")
    logger.info(f"  Description: {upload_params['description'][:100]}...")
    logger.info(f"  Tags: {', '.join(upload_params['tags'])}")
    logger.info(f"  Privacy: {privacy}")

    # Upload
    result = uploader.upload_short(
        video_path=video_path,
        title=upload_params['title'],
        description=upload_params['description'],
        tags=upload_params['tags'],
        privacy_status=privacy
    )

    return result


def upload_batch(
    video_paths: List[str],
    privacy: str = "public",
    client_secrets: str = 'client_secrets.json',
    credentials: str = 'youtube_credentials.pickle'
) -> List[Dict[str, Any]]:
    """
    Upload multiple videos to YouTube Shorts.

    Args:
        video_paths: List of video file paths
        privacy: Privacy status for all videos
        client_secrets: Path to OAuth2 client secrets
        credentials: Path to credentials file

    Returns:
        List of upload results
    """
    # Initialize uploader
    uploader = YouTubeUploader(
        client_secrets_file=client_secrets,
        credentials_file=credentials
    )

    # Authenticate
    logger.info("Authenticating with YouTube...")
    if not uploader.authenticate():
        logger.error("Authentication failed!")
        return []

    logger.info("✓ Authentication successful!\n")

    # Upload each video
    results = []
    for i, video_path in enumerate(video_paths, 1):
        logger.info(f"\nUploading video {i}/{len(video_paths)}")

        result = upload_single_video(
            uploader=uploader,
            video_path=video_path,
            privacy=privacy
        )

        if result:
            results.append(result)
            logger.info(f"✓ Upload successful!")
            logger.info(f"  Shorts URL: {result['shorts_url']}")
        else:
            logger.error(f"✗ Upload failed for {video_path}")

    return results


def find_clips_in_directory(directory: str, pattern: str = "*.mp4") -> List[str]:
    """
    Find all video clips in a directory.

    Args:
        directory: Directory to search
        pattern: File pattern to match

    Returns:
        List of video file paths
    """
    clips_dir = Path(directory)
    if not clips_dir.exists():
        logger.error(f"Directory not found: {directory}")
        return []

    video_files = sorted(clips_dir.glob(pattern))
    return [str(f) for f in video_files]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Upload video clips to YouTube Shorts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a single video
  python run_upload_shorts.py video.mp4

  # Upload all clips from outputs/clips directory
  python run_upload_shorts.py --directory outputs/clips

  # Upload with custom title and as unlisted
  python run_upload_shorts.py video.mp4 --title "My Awesome Short" --privacy unlisted

  # Upload batch with custom client secrets
  python run_upload_shorts.py --directory outputs/clips --client-secrets my_secrets.json
        """
    )

    # Video input
    parser.add_argument(
        'video',
        nargs='?',
        help='Path to video file to upload'
    )
    parser.add_argument(
        '--directory', '-d',
        help='Upload all MP4 files from this directory'
    )

    # Upload options
    parser.add_argument(
        '--privacy', '-p',
        choices=['public', 'private', 'unlisted'],
        default='public',
        help='Privacy status (default: public)'
    )
    parser.add_argument(
        '--title', '-t',
        help='Custom video title (overrides metadata)'
    )
    parser.add_argument(
        '--description',
        help='Custom video description (overrides metadata)'
    )
    parser.add_argument(
        '--tags',
        help='Custom tags, comma-separated (overrides metadata)'
    )

    # Authentication
    parser.add_argument(
        '--client-secrets',
        default='client_secrets.json',
        help='Path to OAuth2 client secrets file (default: client_secrets.json)'
    )
    parser.add_argument(
        '--credentials',
        default='youtube_credentials.pickle',
        help='Path to credentials file (default: youtube_credentials.pickle)'
    )

    args = parser.parse_args()

    # Validate input
    if not args.video and not args.directory:
        parser.error("Either provide a video file or --directory")

    # Get video files
    video_files = []
    if args.directory:
        video_files = find_clips_in_directory(args.directory)
        if not video_files:
            logger.error(f"No video files found in {args.directory}")
            return 1
        logger.info(f"Found {len(video_files)} video(s) to upload")
    else:
        if not os.path.exists(args.video):
            logger.error(f"Video file not found: {args.video}")
            return 1
        video_files = [args.video]

    # Parse custom tags
    custom_tags = None
    if args.tags:
        custom_tags = [tag.strip() for tag in args.tags.split(',')]

    # Upload
    if len(video_files) == 1:
        # Single upload
        uploader = YouTubeUploader(
            client_secrets_file=args.client_secrets,
            credentials_file=args.credentials
        )

        if not uploader.authenticate():
            logger.error("Authentication failed!")
            return 1

        result = upload_single_video(
            uploader=uploader,
            video_path=video_files[0],
            privacy=args.privacy,
            custom_title=args.title,
            custom_description=args.description,
            custom_tags=custom_tags
        )

        if result:
            print(f"\n{'='*60}")
            print("✓ UPLOAD SUCCESSFUL!")
            print(f"{'='*60}")
            print(f"Video ID: {result['video_id']}")
            print(f"Watch URL: {result['video_url']}")
            print(f"Shorts URL: {result['shorts_url']}")
            print(f"{'='*60}\n")
            return 0
        else:
            logger.error("Upload failed!")
            return 1
    else:
        # Batch upload
        results = upload_batch(
            video_paths=video_files,
            privacy=args.privacy,
            client_secrets=args.client_secrets,
            credentials=args.credentials
        )

        # Summary
        print(f"\n{'='*60}")
        print(f"UPLOAD SUMMARY")
        print(f"{'='*60}")
        print(f"Total videos: {len(video_files)}")
        print(f"Successful: {len(results)}")
        print(f"Failed: {len(video_files) - len(results)}")
        print(f"{'='*60}")

        if results:
            print("\nUploaded videos:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   {result['shorts_url']}")

        return 0 if len(results) == len(video_files) else 1


if __name__ == "__main__":
    sys.exit(main())
