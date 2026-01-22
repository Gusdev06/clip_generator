"""
Video processing module for cropping and exporting vertical clips
Enhanced with intelligent speaker tracking
"""
import cv2
import os
import re
import unicodedata
from pathlib import Path
from face_tracker import FaceTracker
from smart_cropper import SmartCropper
import config


def sanitize_filename(filename):
    """
    Sanitize filename to avoid issues with special characters

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename safe for all filesystems
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    # Remove non-ASCII characters
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    # Trim spaces
    filename = filename.strip()
    # Limit length (keep extension)
    name_part, ext = os.path.splitext(filename)
    if len(name_part) > 200:
        name_part = name_part[:200]
    return name_part + ext


class VideoProcessor:
    def __init__(self, output_dir=None, use_smart_crop=False, hf_token=None, add_subtitles=False, whisper_model="base", test_duration=None):
        """
        Initialize the video processor

        Args:
            output_dir: Directory to save processed videos (default: from config)
            use_smart_crop: Use intelligent speaker-tracking crop (default: False)
            hf_token: HuggingFace token for speaker diarization (optional)
            add_subtitles: Add karaoke-style subtitles to video (default: False)
            whisper_model: Whisper model size for transcription (default: "base")
            test_duration: For testing: only process first N seconds (default: None = process all)
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self.use_smart_crop = use_smart_crop
        self.add_subtitles = add_subtitles
        self.test_duration = test_duration

        if use_smart_crop:
            print("Initializing Smart Cropper with speaker tracking...")
            self.smart_cropper = SmartCropper(hf_token=hf_token)
            self.face_tracker = None
        else:
            self.face_tracker = FaceTracker()
            self.smart_cropper = None

        # Initialize subtitle components if needed
        self.subtitle_generator = None
        self.subtitle_exporter = None
        if add_subtitles:
            from captioner import Captioner
            from subtitle_exporter import SubtitleExporter
            print("Initializing subtitle system...")
            self.subtitle_generator = Captioner(model_size=whisper_model)
            self.subtitle_exporter = SubtitleExporter()

    def _add_audio_and_subtitles(self, source_video, target_video, subtitle_file=None):
        """
        Add audio from source video to target video using FFmpeg
        Optionally burn subtitles into the video

        Args:
            source_video: Path to video with audio
            target_video: Path to video without audio
            subtitle_file: Optional path to ASS subtitle file (with embedded font)

        Returns:
            str: Path to final video with audio (and subtitles if provided)
        """
        import subprocess
        from pathlib import Path

        # Verify input files exist
        if not os.path.exists(target_video):
            raise RuntimeError(f"Target video file not found: {target_video}")

        if not os.path.exists(source_video):
            print(f"Warning: Source video not found: {source_video}")
            print(f"Returning video without audio: {target_video}")
            return target_video

        # Create output path with _final suffix
        target_path = Path(target_video)
        final_output = str(target_path.parent / f"{target_path.stem}_final{target_path.suffix}")

        # Build FFmpeg command
        if subtitle_file and os.path.exists(subtitle_file):
            print(f"Adding audio and burning subtitles with FFmpeg...")
            print(f"  Note: Font is embedded in the ASS file")

            # Escape paths for FFmpeg filter
            # For subtitles filter, we need to escape backslashes and colons
            # and wrap paths in single quotes
            subtitle_arg = subtitle_file.replace('\\', '/').replace("'", "'\\''").replace(':', '\\:')
            
            # Get fonts directory
            fonts_dir = str(config._CONFIG_DIR / "fonts").replace('\\', '/').replace("'", "'\\''").replace(':', '\\:')
            
            cmd = [
                'ffmpeg', '-y',
                '-i', target_video,      # Video source (no audio)
                '-i', source_video,      # Audio source
                '-map', '0:v:0',         # Take video from first input
                '-map', '1:a:0',         # Take audio from second input
                '-vf', f"subtitles='{subtitle_arg}':fontsdir='{fonts_dir}'",  # Use subtitles filter with explicit font dir
                '-c:v', 'libx264',       # H.264 codec
                '-preset', 'medium',     # Encoding speed/quality tradeoff
                '-crf', '23',            # Quality (lower = better, 18-28 range)
                '-c:a', 'aac',           # Encode audio as AAC
                '-b:a', '192k',          # Audio bitrate
                '-shortest',             # Match shortest stream duration
                final_output
            ]
        else:
            # No subtitles, just add audio
            cmd = [
                'ffmpeg', '-y',
                '-i', target_video,      # Video source (no audio)
                '-i', source_video,      # Audio source
                '-map', '0:v:0',         # Take video from first input
                '-map', '1:a:0',         # Take audio from second input
                '-c:v', 'copy',          # Copy video codec (no re-encoding)
                '-c:a', 'aac',           # Encode audio as AAC
                '-b:a', '192k',          # Audio bitrate
                '-shortest',             # Match shortest stream duration
                final_output
            ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if subtitle_file:
                print(f"✓ Audio and subtitles added successfully!")
            else:
                print(f"✓ Audio added successfully!")
            print(f"  Final output: {final_output}")

            # Remove temporary files
            os.remove(target_video)
            print(f"  Removed temporary file: {target_video}")

            if subtitle_file and os.path.exists(subtitle_file):
                os.remove(subtitle_file)
                print(f"  Removed temporary subtitle file: {subtitle_file}")

            return final_output

        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not add audio/subtitles. FFmpeg error:")
            print(e.stderr)
            print(f"Returning video without audio: {target_video}")
            return target_video
        except Exception as e:
            print(f"Warning: Unexpected error while adding audio/subtitles: {e}")
            print(f"Returning video without audio: {target_video}")
            return target_video

    def process_video(self, input_path, output_filename=None, progress_callback=None, debug_mode=False):
        """
        Process video to create vertical 9:16 clip with face tracking

        Args:
            input_path: Path to input video file
            output_filename: Optional custom output filename
            progress_callback: Optional callback function(current_frame, total_frames)
            debug_mode: Save debug visualization (default: False)

        Returns:
            str: Path to the output video file
        """
        # Preprocess if using smart cropper
        if self.use_smart_crop:
            print("\n" + "=" * 60)
            print("SMART CROPPING MODE - Speaker-Aware Processing")
            print("=" * 60)
            self.smart_cropper.preprocess_video(input_path, test_duration=self.test_duration)

        # Generate subtitles if enabled
        subtitle_segments = []
        if self.add_subtitles:
            print("\n" + "=" * 60)
            print("SUBTITLE GENERATION")
            print("=" * 60)
            subtitle_segments = self.subtitle_generator.transcribe_video(input_path)
            print(f"Generated {len(subtitle_segments)} subtitle segments")

        # Open input video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        input_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        input_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate max frames to process if test_duration is set
        max_frames_to_process = total_frames
        if self.test_duration:
            max_frames_to_process = int(self.test_duration * fps)
            print(f"\n⚡ TEST MODE: Processing only first {self.test_duration} seconds ({max_frames_to_process} frames)")

        print(f"\nInput video: {input_width}x{input_height}, {fps} fps, {total_frames} frames")
        if self.test_duration:
            print(f"Will process: {max_frames_to_process} frames (first {self.test_duration}s)")

        # Determine output filename
        if not output_filename:
            input_name = Path(input_path).stem
            suffix = "_smart" if self.use_smart_crop else "_vertical"
            output_filename = f"{input_name}{suffix}.mp4"

        # Sanitize filename to avoid issues with special characters
        output_filename = sanitize_filename(output_filename)
        output_path = os.path.join(self.output_dir, output_filename)

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            output_path,
            fourcc,
            config.OUTPUT_FPS,
            (config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT)
        )

        if not out.isOpened():
            raise ValueError("Could not initialize video writer")

        # Debug output
        debug_out = None
        if debug_mode:
            debug_path = output_path.replace('.mp4', '_debug.mp4')
            debug_out = cv2.VideoWriter(
                debug_path,
                fourcc,
                config.OUTPUT_FPS,
                (input_width, input_height)
            )

        print(f"\nProcessing video: {input_path}")
        print(f"Output: {output_path} ({config.OUTPUT_WIDTH}x{config.OUTPUT_HEIGHT})")

        # Reset trackers
        if self.use_smart_crop:
            self.smart_cropper.reset()
        else:
            self.face_tracker.reset()

        frame_count = 0
        processed_count = 0

        # Process each frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Stop if we've reached the test duration limit
            if frame_count > max_frames_to_process:
                print(f"\n⚡ Reached test duration limit ({self.test_duration}s), stopping...")
                break

            timestamp_ms = int((frame_count / fps) * 1000)

            if self.use_smart_crop:
                # Use smart cropper
                output_frame, debug_info = self.smart_cropper.process_frame(frame, frame_count - 1)

                # Debug visualization
                if debug_out:
                    faces = self.smart_cropper.detect_faces_in_frame(frame, timestamp_ms)
                    debug_frame = self.smart_cropper.draw_debug_overlay(
                        frame, faces, debug_info['active_speaker'], debug_info['crop_box']
                    )
                    debug_out.write(debug_frame)
            else:
                # Use basic face tracker
                face_data = self.face_tracker.detect_face(frame, timestamp_ms)
                smoothed_face = self.face_tracker.get_smoothed_position(face_data)

                h, w = frame.shape[:2]
                crop_box = self.face_tracker.calculate_crop_box(smoothed_face, w, h)
                x, y, crop_w, crop_h = crop_box

                cropped = frame[y:y+crop_h, x:x+crop_w]
                output_frame = cv2.resize(cropped, (config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT))

            # Note: Subtitles are now added via FFmpeg after video processing
            # This is much faster than rendering frame-by-frame

            # Write frame
            out.write(output_frame)
            processed_count += 1

            # Progress callback
            if progress_callback and frame_count % 30 == 0:
                progress_callback(frame_count, total_frames)

            # Print progress
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Progress: {frame_count}/{total_frames} frames ({progress:.1f}%)")

        # Cleanup
        cap.release()
        out.release()
        if debug_out:
            debug_out.release()

        print(f"\nProcessing complete!")
        print(f"Processed {processed_count} frames")

        # Verify the output file was created successfully
        if not os.path.exists(output_path):
            raise RuntimeError(f"Video processing failed: Output file not created at {output_path}")

        file_size = os.path.getsize(output_path)
        if file_size == 0:
            raise RuntimeError(f"Video processing failed: Output file is empty at {output_path}")

        print(f"Video frames saved to: {output_path}")
        print(f"  File size: {file_size / (1024 * 1024):.2f} MB")
        if debug_mode:
            print(f"Debug video: {debug_path}")

        # Generate subtitle file if needed
        subtitle_file = None
        if self.add_subtitles:
            if subtitle_segments:
                print(f"\nGenerating ASS subtitle file with embedded font...")
                subtitle_file = output_path.replace('.mp4', '.ass')
                self.subtitle_exporter.export_to_ass(subtitle_segments, subtitle_file)
                print(f"✓ Subtitle file created with {self.subtitle_exporter.font_name} font embedded: {subtitle_file}")
            else:
                print(f"\n⚠️  WARNING: Subtitles were requested but no subtitle segments were generated!")
                print(f"  This video will NOT have subtitles burned in.")
                print(f"  Check the transcription logs above for errors.")

        # Add audio (and subtitles if available) from original video using FFmpeg
        if subtitle_file:
            print(f"\nAdding audio and burning subtitles with FFmpeg...")
        else:
            print(f"\nAdding audio from original video...")

        output_with_audio = self._add_audio_and_subtitles(input_path, output_path, subtitle_file)

        return output_with_audio

    def process_with_ffmpeg(self, input_path, output_filename=None):
        """
        Alternative processing method using FFmpeg for better quality and compression

        Note: Requires FFmpeg to be installed on the system

        Args:
            input_path: Path to input video file
            output_filename: Optional custom output filename

        Returns:
            str: Path to the output video file
        """
        import subprocess

        # First, analyze video and get crop positions
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print("Analyzing video for face tracking...")

        crop_data = []
        frame_count = 0

        self.face_tracker.reset()

        # Sample frames for analysis (process every frame for accuracy)
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            timestamp_ms = int((frame_count / fps) * 1000)

            # Detect and track face
            face_data = self.face_tracker.detect_face(frame, timestamp_ms)
            smoothed_face = self.face_tracker.get_smoothed_position(face_data)

            # Calculate crop box
            h, w = frame.shape[:2]
            crop_box = self.face_tracker.calculate_crop_box(smoothed_face, w, h)

            crop_data.append(crop_box)

            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"Analysis: {frame_count}/{total_frames} frames ({progress:.1f}%)")

        cap.release()

        # For simplicity, use the median crop position
        # In production, you might want to use a more sophisticated approach
        import numpy as np
        crop_array = np.array(crop_data)
        avg_crop = np.median(crop_array, axis=0).astype(int)
        x, y, crop_w, crop_h = avg_crop

        print(f"\nAverage crop box: x={x}, y={y}, w={crop_w}, h={crop_h}")

        # Determine output filename
        if not output_filename:
            input_name = Path(input_path).stem
            output_filename = f"{input_name}_vertical.mp4"

        # Sanitize filename to avoid issues with special characters
        output_filename = sanitize_filename(output_filename)
        output_path = os.path.join(self.output_dir, output_filename)

        # Build FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f'crop={crop_w}:{crop_h}:{x}:{y},scale={config.OUTPUT_WIDTH}:{config.OUTPUT_HEIGHT}',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',  # Overwrite output file
            output_path
        ]

        print(f"\nProcessing with FFmpeg...")
        print(f"Command: {' '.join(ffmpeg_cmd)}")

        # Run FFmpeg
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            raise RuntimeError("FFmpeg processing failed")

        print(f"\nProcessing complete!")
        print(f"Output saved to: {output_path}")

        return output_path


if __name__ == "__main__":
    # Test the video processor
    processor = VideoProcessor()

    test_video = input("Enter path to test video: ")
    if not os.path.exists(test_video):
        print(f"File not found: {test_video}")
        exit(1)

    # Process video
    output = processor.process_video(test_video)
    print(f"\nDone! Output: {output}")
