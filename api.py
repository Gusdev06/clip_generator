from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
import json
import uuid
from datetime import datetime
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from downloader import VideoDownloader
from video_processor import VideoProcessor
from captioner import Captioner
from viral_curator import ViralCurator
from clip_manager import ClipManager
from title_generator import TitleGenerator
import config

# In-memory job storage (for production, use Redis or a database)
jobs: Dict[str, Dict] = {}

# Define request models
class ClipRequest(BaseModel):
    url: str
    output_name: Optional[str] = None
    smart_crop: bool = False
    hf_token: Optional[str] = None
    add_subtitles: bool = True
    whisper_model: str = "large"
    test_duration: Optional[int] = None

class ViralRequest(BaseModel):
    url: str
    limit: int = 3

app = FastAPI(
    title="Clips Generator API",
    description="API for creating vertical 9:16 clips from YouTube videos",
    version="1.0.0"
)

def process_video_task(request: ClipRequest):
    """
    Background task to process the video (Simple processing)
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

def cleanup_job_files(files_to_delete: list):
    """
    Delete all generated files after successful upload to Supabase

    Args:
        files_to_delete: List of file paths to delete
    """
    deleted_count = 0
    failed_count = 0

    for file_path in files_to_delete:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_count += 1
                print(f"  🗑️  Deleted: {os.path.basename(file_path)}")
        except Exception as e:
            failed_count += 1
            print(f"  ⚠️  Failed to delete {file_path}: {e}")

    print(f"\n🧹 Cleanup complete: {deleted_count} files deleted, {failed_count} failed")

def process_viral_task(job_id: str, request: ViralRequest):
    """
    Background task to process viral clips (Audio First Pipeline)
    """
    # Track files to delete after processing
    files_to_delete = []

    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"]["phase"] = "downloading_audio"

        print(f"Starting viral processing for URL: {request.url}")

        # 1. Download Audio
        print("\n[PHASE 1] Audio Acquisition")
        downloader = VideoDownloader()

        # Try to get video info (optional, may fail due to bot detection)
        info = downloader.get_video_info(request.url)
        if info:
            print(f"Target: {info['title']} ({info['duration']}s)")
            jobs[job_id]["video_title"] = info['title']
        else:
            print(f"⚠️  Could not fetch video metadata (continuing anyway...)")
            jobs[job_id]["video_title"] = "Unknown Title"

        audio_path = downloader.download(request.url, audio_only=True)
        files_to_delete.append(audio_path)  # Mark audio for deletion

        # 2. Transcribe
        print("\n[PHASE 2] Intelligence & Transcription")
        jobs[job_id]["progress"]["phase"] = "transcribing"
        captioner = Captioner()
        transcript_segments = captioner.transcribe_video(audio_path)
        transcript_json_path = str(Path(audio_path).parent / "transcript_words.json")
        files_to_delete.append(transcript_json_path)  # Mark transcript for deletion

        # 3. Curate
        print("\n[PHASE 3] Viral Curation")
        jobs[job_id]["progress"]["phase"] = "curating"
        curator = ViralCurator()
        viral_candidates = curator.analyze_transcript(transcript_json_path, max_clips=request.limit)

        if not viral_candidates:
            print("❌ No viral candidates found.")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "No viral candidates found"
            return

        selected_clips = viral_candidates[:request.limit]
        jobs[job_id]["progress"]["total_clips"] = len(selected_clips)

        print(f"\nProceeding with top {len(selected_clips)} clips:")
        for i, clip in enumerate(selected_clips, 1):
            print(f"{i}. {clip.title} (Score: {clip.viral_score})")

        # 4. Download Video
        print("\n[PHASE 4] Video Acquisition")
        jobs[job_id]["progress"]["phase"] = "downloading_video"
        video_path = downloader.download(request.url)
        files_to_delete.append(video_path)  # Mark video for deletion

        # 5. Process Clips
        print("\n[PHASE 5] Production & Editing")
        jobs[job_id]["progress"]["phase"] = "processing_clips"
        clip_manager = ClipManager()
        title_generator = TitleGenerator()
        processor = VideoProcessor(use_smart_crop=True, add_subtitles=True)

        # Initialize Supabase Manager
        from supabase_manager import SupabaseManager
        supabase_manager = SupabaseManager()

        for i, clip in enumerate(selected_clips, 1):
            jobs[job_id]["progress"]["current_clip"] = i
            print(f"\n🎬 Processing Clip {i}/{len(selected_clips)}: {clip.title}")

            raw_clip_path = clip_manager.extract_clip(
                video_path,
                clip.start_time,
                clip.end_time,
                f"raw_{i}_{clip.title}",
                safe_mode=True
            )

            if not raw_clip_path:
                print(f"Skipping clip {i} due to extraction failure")
                continue

            files_to_delete.append(raw_clip_path)  # Mark raw clip for deletion

            print(f"  Applying Smart Crop and Subtitles...")
            try:
                final_output = processor.process_video(raw_clip_path)
                print(f"  ✨ FINAL VIRAL CLIP READY: {final_output}")
                files_to_delete.append(final_output)  # Mark final clip for deletion

                print(f"  📝 Generating metadata...")
                metadata_path = title_generator.create_metadata_json(
                    clip.to_dict(),
                    final_output
                )
                print(f"  ✅ Metadata saved: {metadata_path}")
                files_to_delete.append(metadata_path)  # Mark metadata for deletion

                # --- Supabase Integration ---
                clip_record = None
                if supabase_manager.client:
                    print(f"  Uploading to Supabase...")
                    video_filename = os.path.basename(final_output)
                    json_filename = os.path.basename(metadata_path)

                    # Upload Video
                    video_key = f"{video_filename}"
                    video_url = supabase_manager.upload_file(final_output, video_key, "video/mp4")

                    # Upload JSON
                    json_key = f"{json_filename}"
                    json_url = supabase_manager.upload_file(metadata_path, json_key, "application/json")

                    if video_url and json_url:
                        # Read metadata content
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata_content = json.load(f)

                        # Save to Database and get the response
                        clip_record = supabase_manager.save_clip_data(
                            metadata_content,
                            video_url,
                            json_url,
                            request.url,
                            job_id  # Pass job_id for tracking
                        )

                        # Add to job clips list
                        if clip_record:
                            jobs[job_id]["clips"].append(clip_record)
                # -----------------------------

            except Exception as e:
                print(f"  ❌ Error processing clip {i}: {e}")
                jobs[job_id]["errors"].append({
                    "clip": i,
                    "title": clip.title,
                    "error": str(e)
                })

        print("\n✅ VIRAL PIPELINE COMPLETE")
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

        # Clean up all generated files after successful processing
        print("\n🧹 Cleaning up generated files...")
        cleanup_job_files(files_to_delete)

    except Exception as e:
        print(f"Error in viral processing task: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

        # Even on failure, attempt cleanup to free disk space
        print("\n🧹 Attempting cleanup after error...")
        cleanup_job_files(files_to_delete)

@app.post("/generate")
async def generate_clip(request: ClipRequest, background_tasks: BackgroundTasks):
    """
    Start simple video clip generation process
    """
    background_tasks.add_task(process_video_task, request)
    return {"message": "Video processing started", "url": request.url}

@app.post("/viral")
async def generate_viral(request: ViralRequest, background_tasks: BackgroundTasks):
    """
    Start viral clip generation process (Audio-First Pipeline)

    Returns a job_id to track the progress
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Initialize job status
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",  # pending, processing, completed, failed
        "url": request.url,
        "limit": request.limit,
        "video_title": None,
        "progress": {
            "phase": "pending",  # pending, downloading_audio, transcribing, curating, downloading_video, processing_clips
            "current_clip": 0,
            "total_clips": 0
        },
        "clips": [],  # Will store the database records
        "errors": [],
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None
    }

    # Start background task
    background_tasks.add_task(process_viral_task, job_id, request)

    return {
        "message": "Viral processing started",
        "job_id": job_id,
        "url": request.url,
        "limit": request.limit,
        "status_endpoint": f"/status/{job_id}"
    }

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a viral clip generation job

    Returns:
        - status: pending, processing, completed, failed
        - progress: current phase and clip number
        - clips: list of generated clips (when completed)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Return different data based on status
    if job["status"] == "completed":
        return {
            "job_id": job_id,
            "status": job["status"],
            "video_title": job["video_title"],
            "created_at": job["created_at"],
            "completed_at": job["completed_at"],
            "clips": job["clips"],
            "total_clips": len(job["clips"]),
            "errors": job["errors"] if job["errors"] else None
        }
    elif job["status"] == "failed":
        return {
            "job_id": job_id,
            "status": job["status"],
            "error": job["error"],
            "created_at": job["created_at"]
        }
    else:
        # pending or processing - include clips generated so far
        return {
            "job_id": job_id,
            "status": job["status"],
            "url": job["url"],
            "video_title": job["video_title"],
            "progress": job["progress"],
            "clips": job["clips"],  # Include clips already generated
            "total_clips_generated": len(job["clips"]),
            "created_at": job["created_at"]
        }

@app.get("/jobs")
async def list_jobs():
    """
    List all jobs (most recent first)
    """
    jobs_list = [
        {
            "job_id": job["job_id"],
            "status": job["status"],
            "url": job["url"],
            "video_title": job.get("video_title"),
            "created_at": job["created_at"],
            "completed_at": job.get("completed_at"),
            "clips_count": len(job["clips"])
        }
        for job in sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)
    ]
    return {"jobs": jobs_list, "total": len(jobs_list)}

@app.get("/clips/{job_id}")
async def get_clips_by_job(job_id: str):
    """
    Get clips from the database by job_id

    This endpoint queries the Supabase database directly,
    so it works even if the server was restarted and lost the in-memory job data.
    """
    from supabase_manager import SupabaseManager

    supabase_manager = SupabaseManager()

    if not supabase_manager.client:
        raise HTTPException(status_code=503, detail="Supabase not configured")

    try:
        # Query clips from database by job_id
        response = supabase_manager.client.table(supabase_manager.table_name)\
            .select("*")\
            .eq("job_id", job_id)\
            .order("created_at", desc=False)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"No clips found for job_id: {job_id}")

        return {
            "job_id": job_id,
            "clips": response.data,
            "total": len(response.data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching clips: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
