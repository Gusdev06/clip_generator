"""
Configuration settings for the video clips generator
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the directory where this config file is located
_CONFIG_DIR = Path(__file__).parent.absolute()

# Load environment variables from .env file
load_dotenv()

# Output video settings
OUTPUT_WIDTH = 1080  # 9:16 aspect ratio width
OUTPUT_HEIGHT = 1920  # 9:16 aspect ratio height
OUTPUT_FPS = 30  # Frames per second for output video

# Face tracking settings
MIN_DETECTION_CONFIDENCE = 0.5  # Minimum confidence for face detection
MIN_TRACKING_CONFIDENCE = 0.5  # Minimum confidence for face tracking

# Crop positioning
FACE_VERTICAL_POSITION = 0.35  # Face position in frame (0.0=top, 1.0=bottom)
# 0.35 means face will be in upper third, good for talking head videos

# Smoothing settings
SMOOTHING_WINDOW = 15  # Number of frames to use for smoothing crop position
# Higher = smoother but more lag, Lower = more responsive but jittery

# Download settings
DOWNLOAD_DIR = "downloads"  # Directory to store downloaded videos
OUTPUT_DIR = "outputs"  # Directory to store processed videos
VIDEO_QUALITY = "best"  # 'best', 'worst', or specific format code

# Margins and padding
HORIZONTAL_MARGIN = 1.5  # Multiplier for face width (1.5 = 50% extra space on sides)
VERTICAL_MARGIN = 2.0  # Multiplier for face height (2.0 = extra space top/bottom)

# Safety bounds
MIN_CROP_WIDTH = 480  # Minimum width for crop area in source video
MAX_ZOOM = 2.0  # Maximum zoom factor (to prevent too aggressive cropping)

# Subtitle settings
SUBTITLE_FONT_PATH = str(_CONFIG_DIR / "fonts" / "ArchivoBlack-Regular.ttf")  # Archivo Black font
SUBTITLE_FONT_SIZE = 120
SUBTITLE_POSITION = (0.5, 0.75)  # Position (x_ratio, y_ratio) - center, lower down
SUBTITLE_DEFAULT_COLOR = (255, 255, 255)  # Branco para palavras não destacadas
SUBTITLE_HIGHLIGHT_COLOR = (0, 255, 0)  # Verde para palavra atual
SUBTITLE_OUTLINE_COLOR = (20, 30, 80) # Preto (ou azul escuro: (40, 40, 100))
SUBTITLE_OUTLINE_WIDTH = 4
SUBTITLE_MAX_WORDS = 3

# OpenAI Whisper settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

WHISPER_MODEL = "whisper-1"  # OpenAI model name
WHISPER_LANGUAGE = "pt"  # Language code for transcription
# NOTE: Empty prompt works better than generic prompts.
# Generic prompts can cause hallucinations where Whisper returns the prompt itself.
# Use specific prompts only if you know the content (e.g., "Discussion about crime and rehabilitation")
WHISPER_PROMPT = ""  # Leave empty for best results, or use content-specific prompt

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET_NAME = "clips"
SUPABASE_TABLE_NAME = "generated_clips"

# YouTube Downloader settings
# To avoid bot detection, you can provide YouTube cookies
# Option 1: Use cookies from browser (e.g., 'chrome', 'firefox')
YT_COOKIES_FROM_BROWSER = os.getenv("YT_COOKIES_FROM_BROWSER")  # e.g., "chrome"
# Option 2: Path to a Netscape cookies.txt file
YT_COOKIES_FILE = os.getenv("YT_COOKIES_FILE")  # e.g., "/app/youtube_cookies.txt"

# Deprecated local whisper settings
# WHISPER_MODEL_SIZE = "large"
# WHISPER_DEVICE = "cpu"
# WHISPER_PREPROCESS_AUDIO = True
# WHISPER_TEMPERATURE = 0.0
# WHISPER_COMPRESSION_RATIO_THRESHOLD = 2.4
# WHISPER_LOGPROB_THRESHOLD = -1.0

WHISPER_NO_SPEECH_THRESHOLD = 0.6  # Silence detection threshold
WHISPER_BEAM_SIZE = 5  # Beam search size (higher = more accurate but slower)
WHISPER_BEST_OF = 5  # Number of candidates to consider (higher = better quality)
