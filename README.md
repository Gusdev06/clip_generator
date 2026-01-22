# YouTube to Vertical Clips Generator

Automatically download YouTube videos and create vertical 9:16 format clips with intelligent face tracking and cropping. Perfect for creating content for Instagram Reels, TikTok, YouTube Shorts, and other vertical video platforms.

## Features

- **YouTube Download**: Download videos directly from YouTube URLs
- **Face Detection & Tracking**: Uses MediaPipe for accurate face detection with 468 facial landmarks
- **Smart Cropping**: Automatically crops to 9:16 format keeping the speaker centered
- **Smooth Tracking**: Applies smoothing to prevent jittery camera movements
- **Configurable**: Easy to adjust tracking, positioning, and output settings
- **Two Processing Modes**: OpenCV (built-in) or FFmpeg (better quality)

### 🆕 NEW: Intelligent Speaker-Tracking Crop (Experimental)

The new **Smart Crop** mode uses AI to create professional TikTok-style clips:

- **Speaker Diarization**: Identifies who is speaking when (multi-person support)
- **Lip Sync Detection**: Correlates mouth movement with audio
- **Dynamic Crop**: Automatically follows the active speaker
- **Smooth Transitions**: Fluid camera movement between speakers
- **Voice Activity Detection**: Removes silent moments

See [SMART_CROP_GUIDE.md](SMART_CROP_GUIDE.md) for detailed usage.

### 🔥 NEW: Viral Clips AI Curator (Audio-First Pipeline)

The **Viral Curator** is an AI-powered system that analyzes video transcripts to identify the highest-potential viral clips using science-backed viral mechanics:

#### Key Features:
- **4 Hook Types Analysis**: Question Hook, Pattern Interrupt, Proof-First, Combo Hook
- **8 Psychological Triggers**: Emotion, Humor, Relatability, Awe, Social Currency, etc.
- **STEPPS Framework**: Based on Jonah Berger's viral content research
- **Open Loop Detection**: Identifies curiosity gaps that drive watch-through
- **Retention Prediction**: Estimates retention % and share probability
- **Quality-First**: Only returns clips with Viral Potential Score (VPS) ≥9/10

#### Usage:
```bash
# Generate viral clips from a YouTube video
python run_viral.py "https://youtube.com/watch?v=VIDEO_ID" --limit 3
```

#### What You Get:
Each clip includes detailed viral metrics:
- **Viral Score** (0-10)
- **Hook Type** (e.g., "Pattern Interrupt")
- **Psychological Triggers** (e.g., Humor, Relatability)
- **STEPPS Score** (Social Currency, Emotion, etc.)
- **Estimated Retention %**
- **Share Probability** (Low/Medium/High)

#### The Process:
1. **Audio Download**: Fast audio-only download from YouTube
2. **AI Transcription**: Word-level timestamps using OpenAI Whisper
3. **Viral Analysis**: GPT-4 analyzes transcript against viral mechanics
4. **Smart Selection**: Returns only clips with VPS ≥9/10
5. **Video Processing**: Downloads full video and creates optimized clips
6. **Final Output**: Vertical 9:16 clips with subtitles, ready to post

#### Research-Backed:
Based on analysis of 50+ viral videos and research from:
- Jonah Berger's "Contagious" (STEPPS Framework)
- Journal of Consumer Psychology
- TikTok/Reels algorithm studies
- NYU, Buffer, Hootsuite social media research

See [VIRAL_MECHANICS.md](VIRAL_MECHANICS.md) for complete documentation.

## Requirements

- Python 3.8 or higher
- FFmpeg (optional, for better video quality)

## Installation

### Easy Setup (Recommended)

Run the setup script which creates a virtual environment and installs all dependencies:

```bash
./setup.sh
```

### Manual Setup

1. **Create a virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

### Optional: Install FFmpeg (Recommended for better quality)

- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following keys:

```bash
# Required for Viral Curator (AI-powered clip selection)
OPENAI_API_KEY=your_openai_api_key_here

# Required for full transcription
TRANSCRIPTAPI_KEY=your_transcriptapi_key_here
```

**Note**: The TranscriptAPI key is pre-configured for basic usage. For the Viral Curator feature, you'll need your own OpenAI API key.

See `.env.example` for reference.

## Quick Start

### Interactive Mode

**Easy way (using run script)**:
```bash
./run.sh
```

**Or activate the virtual environment and run**:
```bash
source venv/bin/activate
python main.py
```

The program will guide you through the process.

### Command Line Usage

**Download and process a YouTube video**:
```bash
./run.sh "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Or with virtual environment**:
```bash
source venv/bin/activate
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Process an existing video file**:
```bash
python main.py -f /path/to/video.mp4
```

**Specify custom output name**:
```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" -o my_vertical_clip
```

**Use FFmpeg for better quality** (requires FFmpeg installed):
```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --ffmpeg
```

## Command Line Arguments

```
usage: main.py [-h] [-o OUTPUT] [-f FILE] [--ffmpeg] [--skip-download] [url]

positional arguments:
  url                   YouTube video URL

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output filename (without extension)
  -f FILE, --file FILE  Process existing video file instead of downloading
  --ffmpeg              Use FFmpeg for processing (requires FFmpeg installed)
  --skip-download       Skip download if video already exists
```

## Configuration

Edit `config.py` to customize the behavior:

### Output Settings
```python
OUTPUT_WIDTH = 1080      # Width in pixels (9:16 aspect ratio)
OUTPUT_HEIGHT = 1920     # Height in pixels
OUTPUT_FPS = 30          # Frames per second
```

### Face Tracking
```python
MIN_DETECTION_CONFIDENCE = 0.5  # Face detection sensitivity (0.0-1.0)
MIN_TRACKING_CONFIDENCE = 0.5   # Face tracking sensitivity (0.0-1.0)
FACE_VERTICAL_POSITION = 0.35   # Where to position face (0.0=top, 1.0=bottom)
```

### Smoothing
```python
SMOOTHING_WINDOW = 15    # Number of frames for smoothing
                         # Higher = smoother but more lag
                         # Lower = more responsive but jittery
```

### Margins
```python
HORIZONTAL_MARGIN = 1.5  # Extra space around face horizontally
VERTICAL_MARGIN = 2.0    # Extra space around face vertically
```

## Project Structure

```
clips_generator/
├── main.py              # Entry point
├── downloader.py        # YouTube download functionality
├── face_tracker.py      # Face detection and tracking
├── video_processor.py   # Video cropping and export
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── downloads/           # Downloaded videos (created automatically)
└── outputs/             # Processed vertical clips (created automatically)
```

## How It Works

1. **Download**: Uses `yt-dlp` to download the video from YouTube
2. **Detect**: MediaPipe detects faces in each frame
3. **Track**: Smoothing algorithm tracks face movement over time
4. **Crop**: Calculates optimal 9:16 crop box centered on the speaker
5. **Export**: Outputs the final vertical video

## Examples

### Basic Usage
```bash
# Download and process a video
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Advanced Usage
```bash
# Process with FFmpeg for best quality
python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --ffmpeg \
  -o my_awesome_clip
```

### Process Local File
```bash
# Process a video you already have
python main.py -f ~/Videos/interview.mp4 -o interview_vertical
```

### 🆕 Smart Crop Mode (AI-Powered)
```bash
# Basic smart crop (single speaker)
python main.py "video.mp4" --smart

# Full smart crop with speaker diarization (multi-speaker)
python main.py "podcast.mp4" --smart --hf-token YOUR_HF_TOKEN

# With debug visualization
python main.py "interview.mp4" --smart --hf-token YOUR_HF_TOKEN --debug
```

**What you get**:
- Automatic speaker detection and tracking
- Professional framing following the active speaker
- Smooth transitions between speakers
- Perfect for podcasts, interviews, and multi-person content

See [SMART_CROP_GUIDE.md](SMART_CROP_GUIDE.md) for complete documentation.

## Testing Individual Components

Each module can be tested independently:

### Test Face Tracker (with webcam)
```bash
python face_tracker.py
```

### Test Downloader
  python main.py https://www.youtube.com/watch?v=AJngV_2Sg3s --test-duration 15 --subtitles
python main.py https://www.youtube.com/watch?v=AJngV_2Sg3s --subtitles --whisper-model medium
  python main.py https://www.youtube.com/watch?v=AJngV_2Sg3s --subtitles
```bash
python downloader.py
```

### Test Video Processor
```bash
python video_processor.py
```

## Tips for Best Results

1. **Video Quality**: Use high-quality source videos for best results
2. **Speaker Position**: Works best when speaker is clearly visible and centered
3. **Lighting**: Better lighting improves face detection accuracy
4. **Smoothing**: Increase `SMOOTHING_WINDOW` for smoother tracking
5. **Face Position**: Adjust `FACE_VERTICAL_POSITION` to control where face appears in frame
   - `0.35` (default): Upper third, good for talking heads
   - `0.5`: Center
   - `0.25`: Near top

## Troubleshooting

### "Could not open video file"
- Check that the file path is correct
- Ensure the video format is supported (MP4, AVI, MOV, etc.)

### "FFmpeg processing failed"
- Make sure FFmpeg is installed and in your PATH
- Try using OpenCV mode (without `--ffmpeg` flag)

### Face not detected
- Ensure the speaker's face is clearly visible
- Adjust `MIN_DETECTION_CONFIDENCE` in config.py (lower = more sensitive)
- Check lighting conditions in the source video

### Jittery tracking
- Increase `SMOOTHING_WINDOW` in config.py
- Use FFmpeg mode which calculates average crop position

### Video too zoomed in/out
- Adjust `HORIZONTAL_MARGIN` and `VERTICAL_MARGIN` in config.py
- Modify `MAX_ZOOM` to limit maximum zoom level

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Acknowledgments

- **yt-dlp**: YouTube downloading
- **MediaPipe**: Face detection and tracking
- **OpenCV**: Video processing
- **FFmpeg**: Video encoding and compression
