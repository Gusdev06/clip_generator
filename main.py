#!/usr/bin/env python3
"""
Main entry point for the YouTube to Vertical Clips Generator
"""
import sys
import os
import argparse
from pathlib import Path

from downloader import VideoDownloader
from video_processor import VideoProcessor
import config


def main():
    """Main function to orchestrate video download and processing"""
    parser = argparse.ArgumentParser(
        description='Download YouTube videos and create vertical 9:16 clips with face tracking'
    )
    parser.add_argument(
        'url',
        nargs='?',
        help='YouTube video URL'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output filename (without extension)',
        default=None
    )
    parser.add_argument(
        '-f', '--file',
        help='Process existing video file instead of downloading',
        default=None
    )
    parser.add_argument(
        '--ffmpeg',
        action='store_true',
        help='Use FFmpeg for processing (requires FFmpeg installed)'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip download if video already exists'
    )
    parser.add_argument(
        '--smart',
        action='store_true',
        help='Use intelligent speaker-tracking crop (EXPERIMENTAL)'
    )
    parser.add_argument(
        '--hf-token',
        help='HuggingFace token for speaker diarization (required for --smart)',
        default=None
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Save debug visualization video'
    )
    parser.add_argument(
        '--subtitles',
        action='store_true',
        help='Add karaoke-style subtitles to the video'
    )
    parser.add_argument(
        '--whisper-model',
        help='Whisper model size for subtitles (tiny, base, small, medium, large)',
        default='base'
    )
    parser.add_argument(
        '--test-duration',
        type=int,
        help='For testing: only process first N seconds of video (e.g., 60 for 1 minute)',
        default=None
    )

    args = parser.parse_args()

    # Interactive mode if no URL or file provided
    if not args.url and not args.file:
        print("=" * 60)
        print("YouTube to Vertical Clips Generator")
        print("=" * 60)
        print("\nThis tool will:")
        print("1. Download a YouTube video")
        print("2. Detect and track the speaker's face")
        print("3. Create a vertical 9:16 clip with smart cropping")
        print("=" * 60)

        choice = input("\nDo you want to (1) Download from YouTube or (2) Process local file? [1/2]: ").strip()

        if choice == '2':
            args.file = input("Enter path to video file: ").strip()
        else:
            args.url = input("\nEnter YouTube URL: ").strip()

    try:
        video_path = None

        # Step 1: Get the video file (download or use existing)
        if args.file:
            # Process existing file
            if not os.path.exists(args.file):
                print(f"Error: File not found: {args.file}")
                return 1

            video_path = args.file
            print(f"\nUsing existing video: {video_path}")

        else:
            # Download from YouTube
            if not args.url:
                print("Error: No URL or file provided")
                return 1

            print(f"\nStep 1/2: Downloading video...")
            print("-" * 60)

            downloader = VideoDownloader()

            # Get video info first
            try:
                info = downloader.get_video_info(args.url)
                print(f"\nVideo Information:")
                print(f"  Title: {info['title']}")
                print(f"  Duration: {info['duration']} seconds ({info['duration']//60}:{info['duration']%60:02d})")
                print(f"  Uploader: {info['uploader']}")
            except Exception as e:
                print(f"Warning: Could not fetch video info: {e}")

            # Download video
            try:
                video_path = downloader.download(args.url, filename=args.output)
            except Exception as e:
                print(f"Error downloading video: {e}")
                return 1

        # Step 2: Process the video
        print(f"\nStep 2/2: Processing video...")
        print("-" * 60)
        print(f"Output resolution: {config.OUTPUT_WIDTH}x{config.OUTPUT_HEIGHT} (9:16)")

        if args.smart:
            print(f"Mode: SMART CROP (Speaker-Aware)")
            print(f"  ✓ Face Detection with 468 landmarks")
            print(f"  ✓ Audio analysis & voice activity detection")
            if args.hf_token:
                print(f"  ✓ Speaker diarization (multi-speaker)")
            print(f"  ✓ Lip sync detection")
            print(f"  ✓ Dynamic crop following active speaker")
        else:
            print(f"Mode: Basic face tracking")
            print(f"Face tracking: Enabled")
            print(f"Smoothing: {config.SMOOTHING_WINDOW} frames")

        print("-" * 60)

        if args.test_duration:
            print(f"\n⚡ TEST MODE: Processing only first {args.test_duration} seconds")
            print("-" * 60)

        if args.subtitles:
            print(f"\nSubtitle Settings:")
            print(f"  ✓ Karaoke-style subtitles enabled")
            print(f"  ✓ Whisper model: {args.whisper_model}")
            font_name = os.path.basename(config.SUBTITLE_FONT_PATH).split('.')[0]
            print(f"  ✓ Font: {font_name}")
            print(f"  ✓ Max 3 words per segment")
            print(f"  ✓ Green highlighting as words are spoken")
            print("-" * 60)

        processor = VideoProcessor(
            use_smart_crop=args.smart,
            hf_token=args.hf_token,
            add_subtitles=args.subtitles,
            whisper_model=args.whisper_model,
            test_duration=args.test_duration
        )

        # Determine output filename
        output_filename = None
        if args.output:
            output_filename = f"{args.output}.mp4"

        # Process video
        try:
            if args.ffmpeg and not args.smart:
                print("\nUsing FFmpeg processing mode...")
                output_path = processor.process_with_ffmpeg(video_path, output_filename)
            else:
                if args.ffmpeg and args.smart:
                    print("\nNote: FFmpeg mode not compatible with Smart Crop, using OpenCV...")
                print("\nProcessing...")
                output_path = processor.process_video(
                    video_path,
                    output_filename,
                    debug_mode=args.debug
                )

            print("\n" + "=" * 60)
            print("SUCCESS!")
            print("=" * 60)
            print(f"\nVertical clip created: {output_path}")
            print(f"Resolution: {config.OUTPUT_WIDTH}x{config.OUTPUT_HEIGHT}")

            # Get file size
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")

            print("\nYou can now upload this video to:")
            print("  - Instagram Stories/Reels")
            print("  - TikTok")
            print("  - YouTube Shorts")
            print("  - Snapchat")
            print("=" * 60)

            return 0

        except Exception as e:
            print(f"\nError processing video: {e}")
            import traceback
            traceback.print_exc()
            return 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
