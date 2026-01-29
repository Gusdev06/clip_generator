"""
Viral Clips Generator - Audio-First Pipeline
Orchestrates the complete flow:
1. Download Audio
2. Transcribe (OpenAI Whisper)
3. Curate Viral Clips (OpenAI GPT-4)
4. Download Video (Full or Partial)
5. Cut & Optimize Clips
"""
import os
import sys
import argparse
from pathlib import Path
import time

from downloader import VideoDownloader
from captioner import Captioner
from viral_curator import ViralCurator
from clip_manager import ClipManager
from video_processor import VideoProcessor
from title_generator import TitleGenerator
import config

def main():
    parser = argparse.ArgumentParser(description="Generate viral clips from YouTube video")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--limit", type=int, default=3, help="Max number of clips to generate")
    parser.add_argument("--cookies-from-browser", nargs='?', const='chrome', help="Browser to extract cookies from (default: chrome)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🚀 VIRAL CLIPS GENERATOR - AUDIO FIRST ARCHITECTURE")
    print("="*60)

    # 1. Download Audio
    print("\n[PHASE 1] Audio Acquisition")
    downloader = VideoDownloader(cookies_from_browser=args.cookies_from_browser)
    info = downloader.get_video_info(args.url)
    print(f"Target: {info['title']} ({info['duration']}s)")
    
    # Download audio only
    audio_path = downloader.download(args.url, audio_only=True)
    
    # 2. Transcribe
    print("\n[PHASE 2] Intelligence & Transcription")
    captioner = Captioner()
    # We pass the audio file as "video_path" since captioner handles extraction internally 
    # but here we already have the MP3, so we can modify captioner or just pass it
    # Captioner.transcribe_video calls extract_audio, which checks if mp3 exists.
    # Since we have audio_path (mp3), we can pass it directly.
    
    # NOTE: Captioner expects a video path usually to extract audio, 
    # but if we pass audio path it should work or we might need to tweak it.
    # Let's check captioner logic: it does `audio_path = self.extract_audio(video_path)`
    # extract_audio does `video_path.with_suffix('.mp3')`. 
    # If we pass .mp3, it will try .mp3.mp3? Let's verify.
    # Ideally we pass the original video filename but it doesn't exist yet.
    # Let's just create a dummy "video" path or handle it.
    # Actually, let's just make sure captioner works with audio input.
    # For now, let's proceed. 
    
    # Hack: Rename audio to .mp4.mp3 just to satisfy the suffix logic if strict, 
    # or rely on the fact that we can just pass the audio file to Whisper API directly in a custom call
    # BUT, to reuse `transcribe_video`, let's see.
    # It does `video_path = Path(video_path); audio_path = video_path.with_suffix('.mp3')`
    # If input is `video.mp3`, `with_suffix('.mp3')` is `video.mp3`. It works!
    
    transcript_segments = captioner.transcribe_video(audio_path)
    # The transcript_words.json is saved alongside audio_path
    transcript_json_path = str(Path(audio_path).parent / "transcript_words.json")
    
    # 3. Curate
    print("\n[PHASE 3] Viral Curation")
    curator = ViralCurator()
    # Pass the limit to the curator so it requests the right number from GPT
    viral_candidates = curator.analyze_transcript(transcript_json_path, max_clips=args.limit)

    if not viral_candidates:
        print("❌ No viral candidates found. Exiting.")
        return

    # All candidates should already be within limit, but slice just in case
    selected_clips = viral_candidates[:args.limit]
    print(f"\n{'='*60}")
    print(f"Proceeding with top {len(selected_clips)} clips:")
    print('='*60)
    for i, clip in enumerate(selected_clips, 1):
        print(f"\n{i}. {clip.title}")
        print(f"   Time: {clip.start_time:.1f}s - {clip.end_time:.1f}s ({clip.duration:.1f}s)")
        print(f"   Score: {clip.viral_score}/10")
        if clip.hook_type:
            print(f"   Hook: {clip.hook_type}")
        if clip.estimated_retention:
            print(f"   Est. Retention: {clip.estimated_retention}%")

    # 4. Download Video
    print("\n[PHASE 4] Video Acquisition")
    # Now we download the full video for high quality processing
    # Optimization: In future, use stream seek. For now, download full.
    video_path = downloader.download(args.url)
    
    # 5. Process Clips
    print("\n[PHASE 5] Production & Editing")
    clip_manager = ClipManager()
    title_generator = TitleGenerator()
    # Initialize processor (with smart crop enabled)
    # NOTE: video_processor expects to run on a file.

    # Subtitles are now handled *after* processing in video_processor or we can burn them now.
    # The `Captioner` generated a full SRT. But we are making clips.
    # Each clip needs its own subtitles.
    # Challenge: We have full transcript, but segments are cut.
    # Option A: Re-transcribe each clip (Higher cost, better accuracy for the clip context)
    # Option B: Slicing the full SRT (Complex logic)
    # Architecture decision: Re-transcribe the CLIP. It's short (60s) and cheap.

    # Initialize processor for vertical crop + subtitles
    # We pass add_subtitles=True so it will re-generate subs for the clip
    processor = VideoProcessor(use_smart_crop=True, add_subtitles=True) 

    for i, clip in enumerate(selected_clips, 1):
        print(f"\n🎬 Processing Clip {i}/{len(selected_clips)}: {clip.title}")
        
        # Cut raw clip
        raw_clip_path = clip_manager.extract_clip(
            video_path, 
            clip.start_time, 
            clip.end_time, 
            f"raw_{i}_{clip.title}",
            safe_mode=True # Use re-encoding for safety first
        )
        
        if not raw_clip_path:
            continue
            
        # Refine (Smart Crop + Subtitles)
        print(f"  Applying Smart Crop and Subtitles...")
        final_output = processor.process_video(raw_clip_path)

        print(f"  ✨ FINAL VIRAL CLIP READY: {final_output}")

        # Generate metadata JSON with score and titles
        print(f"  📝 Gerando metadata e títulos em português...")
        metadata_path = title_generator.create_metadata_json(
            clip.to_dict(),
            final_output
        )
        print(f"  ✅ Metadata completo: {metadata_path}")

    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
