#!/usr/bin/env python3
"""
Debug script to check cookies and yt-dlp configuration
"""
import os
import sys

print("=" * 70)
print("COOKIES & YT-DLP DEBUG SCRIPT")
print("=" * 70)

# Check 1: Environment variables
print("\n[1] Environment Variables:")
print(f"  YT_COOKIES_FILE: {os.getenv('YT_COOKIES_FILE', 'NOT SET')}")
print(f"  YT_COOKIES_FROM_BROWSER: {os.getenv('YT_COOKIES_FROM_BROWSER', 'NOT SET')}")

# Check 2: Cookies file exists
cookies_path = os.getenv('YT_COOKIES_FILE', 'cookies.txt')
print(f"\n[2] Cookies File Check:")
print(f"  Path: {cookies_path}")
print(f"  Exists: {os.path.exists(cookies_path)}")

if os.path.exists(cookies_path):
    try:
        with open(cookies_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            cookie_lines = [l for l in lines if l and not l.startswith('#')]

            print(f"  Total lines: {len(lines)}")
            print(f"  Cookie entries: {len(cookie_lines)}")
            print(f"  File size: {len(content)} bytes")

            # Check if it's Netscape format
            if lines and '# Netscape HTTP Cookie File' in lines[0]:
                print(f"  Format: ✅ Netscape HTTP Cookie File")
            else:
                print(f"  Format: ⚠️  NOT Netscape format (first line: {lines[0] if lines else 'empty'})")

            # Show first few cookies (domain only, for privacy)
            print(f"\n  Sample domains:")
            for line in cookie_lines[:5]:
                parts = line.split('\t')
                if len(parts) > 0:
                    print(f"    - {parts[0]}")

    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
else:
    print(f"  ❌ File not found!")

# Check 3: Node.js availability
print(f"\n[3] JavaScript Runtime Check:")
import subprocess
try:
    result = subprocess.run(['node', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"  Node.js: ✅ {result.stdout.strip()}")
    else:
        print(f"  Node.js: ❌ Not working")
except FileNotFoundError:
    print(f"  Node.js: ❌ Not found in PATH")

# Check 4: yt-dlp version
print(f"\n[4] yt-dlp Check:")
try:
    import yt_dlp
    print(f"  yt-dlp version: {yt_dlp.version.__version__}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Check 5: Test YouTube access with cookies
print(f"\n[5] Test YouTube Access:")
print(f"  Testing with cookies from: {cookies_path}")

try:
    import yt_dlp

    test_url = "https://www.youtube.com/watch?v=lXP_JM6dBuk"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    # Add cookies if file exists
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(test_url, download=False)
        print(f"  ✅ SUCCESS!")
        print(f"  Title: {info.get('title', 'Unknown')}")
        print(f"  Duration: {info.get('duration', 0)} seconds")
        print(f"  Available formats: {len(info.get('formats', []))}")

except Exception as e:
    print(f"  ❌ FAILED: {str(e)[:200]}")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
