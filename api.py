from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import os
import uvicorn
from contextlib import asynccontextmanager

from downloader import VideoDownloader
from video_processor import VideoProcessor
import config

# Define request model
class ClipRequest(BaseModel):
    url: str
    output_name: Optional[str] = None
    smart_crop: bool = False
    hf_token: Optional[str] = None
    add_subtitles: bool = True
    whisper_model: str = "large"
    test_duration: Optional[int] = None

app = FastAPI(
    title="Clips Generator API",
    description="API for creating vertical 9:16 clips from YouTube videos",
    version="1.0.0"
)

def process_video_task(request: ClipRequest):
    """
    Background task to process the video
    """
    try:
        print(f"Starting processing for URL: {request.url}")
        
        # Initialize downloader
        downloader = VideoDownloader()
        
        # Download video
        print("Downloading video...")
        try:
            video_path = downloader.download(request.url, filename=request.output_name)
        except Exception as e:
            print(f"Error downloading video: {e}")
            return

        # Determine output filename
        output_filename = None
        if request.output_name:
            output_filename = f"{request.output_name}.mp4"
            
        # Initialize processor
        print(f"Initializing processor with subtitles={request.add_subtitles}")
        processor = VideoProcessor(
            use_smart_crop=request.smart_crop,
            hf_token=request.hf_token,
            add_subtitles=request.add_subtitles,
            whisper_model=request.whisper_model,
            test_duration=request.test_duration
        )

        # Process video
        print("Processing video...")
        try:
            output_path = processor.process_video(
                video_path,
                output_filename,
                debug_mode=False
            )
            print(f"Successfully created clip: {output_path}")
        except Exception as e:
            print(f"Error processing video: {e}")

    except Exception as e:
        print(f"Unexpected error in background task: {e}")

@app.post("/generate")
async def generate_clip(request: ClipRequest, background_tasks: BackgroundTasks):
    """
    Start video clip generation process
    """
    background_tasks.add_task(process_video_task, request)
    return {"message": "Video processing started", "url": request.url}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
