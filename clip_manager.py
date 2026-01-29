"""
Clip Manager - Handles video cutting and FFmpeg operations
Optimized for speed using stream copying and seeking.
"""
import os
import subprocess
from pathlib import Path
import json

class ClipManager:
    """Manages video clipping operations"""
    
    def __init__(self, output_dir="outputs/clips"):
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def extract_clip(self, input_video: str, start_time: float, end_time: float, 
                    title: str, safe_mode=True) -> str:
        """
        Extract a clip from a video file
        
        Args:
            input_video: Path to source video
            start_time: Start time in seconds
            end_time: End time in seconds
            title: Title for the clip filename
            safe_mode: If True, re-encodes to ensure keyframes are handled (slower but safer)
                       If False, uses codec copy (filesize same, instant speed, but might have artifacts)
        
        Returns:
            Path to extracted clip
        """
        # Sanitize filename
        safe_title = "".join([c for c in title if c.isalnum() or c in " -_"]).strip()
        safe_title = safe_title.replace(" ", "_").lower()
        
        output_path = os.path.join(self.output_dir, f"{safe_title}.mp4")
        
        duration = end_time - start_time
        
        # FFmpeg command
        if safe_mode:
            # Re-encoding with DUAL SEEKING for speed + accuracy
            # 1. Fast seek (-ss before -i): Jumps to approximate position quickly
            # 2. Accurate seek (-ss after -i): Fine-tunes to exact frame
            # This prevents subtitle sync issues while staying reasonably fast

            # Calculate fast seek position (5 seconds before target for safety)
            fast_seek = max(0, start_time - 5)
            # Then accurate seek the remaining distance
            accurate_seek = start_time - fast_seek

            cmd = [
                'ffmpeg', '-y',
                '-ss', str(fast_seek),      # Fast seek to approximate position
                '-i', input_video,
                '-ss', str(accurate_seek),  # Accurate seek to exact frame
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                output_path
            ]
        else:
            # Stream copy (Instant)
            # Note: might not start exactly on keyframe
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', input_video,
                '-t', str(duration),
                '-c', 'copy',
                output_path
            ]
            
        print(f"Extracting clip: {title} ({duration:.1f}s)")
        print(f"  Command: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ Clip saved to: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"  Error extracting clip: {e}")
            print(f"  Stderr: {e.stderr.decode('utf-8') if e.stderr else 'No stderr'}")
            return None

if __name__ == "__main__":
    # Test ClipManager
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python clip_manager.py <video_path> <start_time> <end_time>")
        sys.exit(1)
        
    video = sys.argv[1]
    start = float(sys.argv[2])
    end = float(sys.argv[3])
    
    manager = ClipManager()
    manager.extract_clip(video, start, end, "test_clip")
