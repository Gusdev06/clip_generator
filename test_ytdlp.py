#!/usr/bin/env python3
"""
Test script to verify yt-dlp is working correctly with cookies
"""
import yt_dlp
import os

# Test URL
test_url = "https://www.youtube.com/watch?v=lXP_JM6dBuk"

print("=" * 60)
print("Testing yt-dlp with cookies")
print("=" * 60)

# Test 1: List available formats
print("\n[TEST 1] Listing available formats...")
ydl_opts = {
    'quiet': True,
    'cookiefile': '/app/cookies.txt' if os.path.exists('/app/cookies.txt') else 'cookies.txt',
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(test_url, download=False)
        print(f"\nVideo: {info.get('title')}")
        print(f"Duration: {info.get('duration')} seconds")
        print(f"\nAvailable formats:")
        for f in info.get('formats', [])[:10]:  # Show first 10 formats
            print(f"  - {f.get('format_id')}: {f.get('format')} ({f.get('ext')})")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Try downloading audio
print("\n[TEST 2] Testing audio download...")
ydl_opts_audio = {
    'format': 'bestaudio/best',
    'cookiefile': '/app/cookies.txt' if os.path.exists('/app/cookies.txt') else 'cookies.txt',
    'quiet': True,
    'outtmpl': 'test_audio.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }],
}

try:
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([test_url])
    print("✅ Audio download successful!")
except Exception as e:
    print(f"❌ Audio download failed: {e}")

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)
