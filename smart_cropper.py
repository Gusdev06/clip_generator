"""
Smart Cropper - Intelligent dynamic cropping that follows the active speaker
Integrates:
  1. Face Detection (MediaPipe)
  2. Speaker Diarization (pyannote)
  3. Lip Sync Detection
  4. Dynamic Smooth Tracking
"""
import cv2
import numpy as np
from collections import deque
import warnings

from face_tracker import FaceTracker
from audio_analyzer import AudioAnalyzer
from lip_sync_detector import MultiPersonLipSync
import config


class SmartCropper:
    """
    Intelligent cropping system that:
    - Detects all faces in frame
    - Identifies who is speaking (audio + lip sync)
    - Dynamically crops to follow active speaker
    - Smooth transitions between speakers
    """

    def __init__(self, hf_token=None, smoothing_window=20):
        """
        Initialize smart cropper

        Args:
            hf_token: HuggingFace token for speaker diarization (optional)
            smoothing_window: Frames for smooth crop transitions
        """
        # Initialize components
        self.face_tracker = FaceTracker()
        self.audio_analyzer = AudioAnalyzer(hf_token=hf_token)
        self.lip_sync = MultiPersonLipSync(num_faces=4)

        # Crop smoothing
        self.smoothing_window = smoothing_window
        self.crop_history = deque(maxlen=smoothing_window)

        # Speaker tracking
        self.current_speaker_id = None
        self.speaker_stability_counter = 0
        self.min_speaker_switch_frames = 15  # Minimum frames before switching speakers

        # Audio sync
        self.audio_energy_per_frame = None
        self.speaker_timeline = None

    def preprocess_video(self, video_path, test_duration=None):
        """
        Preprocess video to extract audio and speaker timeline

        Args:
            video_path: Path to video file
            test_duration: Optional duration limit in seconds (for testing)

        Returns:
            dict: Preprocessing results
        """
        print("Preprocessing video...")

        # Extract audio
        print("  1. Extracting audio...")
        audio, sr = self.audio_analyzer.extract_audio_from_video(video_path)

        # Limit audio to test_duration if specified
        if test_duration:
            max_samples = int(test_duration * sr)
            if len(audio) > max_samples:
                print(f"  ⚡ Limiting audio to first {test_duration} seconds for testing")
                audio = audio[:max_samples]

        # Detect voice activity
        print("  2. Detecting voice activity...")
        vad_segments = self.audio_analyzer.detect_voice_activity(audio, sr)

        # Speaker diarization (if available)
        print("  3. Speaker diarization...")
        import tempfile
        import soundfile as sf
        from pathlib import Path

        temp_audio = Path(tempfile.mkdtemp()) / "audio.wav"
        sf.write(str(temp_audio), audio, sr)

        diarization = self.audio_analyzer.diarize_speakers(str(temp_audio))

        # Calculate audio energy per frame
        print("  4. Calculating audio energy...")
        fps = config.OUTPUT_FPS
        self.audio_energy_per_frame = self.audio_analyzer.get_audio_energy_per_frame(
            audio, sr, fps=fps
        )

        # Align speaker timeline with frames
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        # Limit total_frames if test_duration is specified
        if test_duration:
            max_frames = int(test_duration * video_fps)
            total_frames = min(total_frames, max_frames)

        self.speaker_timeline = self.audio_analyzer.get_speaker_per_frame(
            diarization['timeline'], fps, total_frames
        )

        print(f"  ✓ Preprocessing complete")
        print(f"    - Duration: {len(audio) / sr:.1f}s")
        print(f"    - Speech segments: {len(vad_segments)}")
        print(f"    - Speakers detected: {diarization['num_speakers']}")

        return {
            'audio': audio,
            'sample_rate': sr,
            'vad_segments': vad_segments,
            'diarization': diarization,
            'audio_energy': self.audio_energy_per_frame,
            'speaker_timeline': self.speaker_timeline
        }

    def detect_faces_in_frame(self, frame, timestamp_ms=0):
        """
        Detect all faces in a frame

        Args:
            frame: OpenCV frame
            timestamp_ms: Video timestamp in milliseconds

        Returns:
            list: List of face data dicts (one per detected face)
        """
        # For now, using single face tracker
        # TODO: Extend to multi-face detection
        face_data = self.face_tracker.detect_face(frame, timestamp_ms)

        if face_data:
            return [face_data]
        else:
            return []

    def identify_active_speaker(self, faces, frame_idx):
        """
        Identify which face is the active speaker

        Args:
            faces: List of detected faces with landmarks
            frame_idx: Current frame index

        Returns:
            int: Index of active speaker face, or None
        """
        if not faces:
            return None

        # Get audio energy for this frame
        if self.audio_energy_per_frame is not None and frame_idx < len(self.audio_energy_per_frame):
            audio_energy = self.audio_energy_per_frame[frame_idx]
        else:
            audio_energy = 0.0

        # Get speaker from timeline (if available)
        timeline_speaker = None
        if self.speaker_timeline and frame_idx < len(self.speaker_timeline):
            timeline_speaker = self.speaker_timeline[frame_idx]

        # If only one face, that's the speaker
        if len(faces) == 1:
            return 0

        # Use lip sync to identify speaker
        face_landmarks = [face.get('landmarks') for face in faces]
        lip_sync_result = self.lip_sync.analyze_frame(face_landmarks, audio_energy)

        active_speaker = lip_sync_result['active_speaker_id']

        # Smooth speaker transitions (avoid rapid switching)
        if active_speaker != self.current_speaker_id:
            self.speaker_stability_counter += 1

            if self.speaker_stability_counter >= self.min_speaker_switch_frames:
                # Switch speaker
                self.current_speaker_id = active_speaker
                self.speaker_stability_counter = 0
        else:
            # Same speaker, reset counter
            self.speaker_stability_counter = 0

        return self.current_speaker_id if self.current_speaker_id is not None else 0

    def calculate_smart_crop(self, faces, active_speaker_id, frame_width, frame_height):
        """
        Calculate optimal crop box focusing on active speaker

        Args:
            faces: List of detected faces
            active_speaker_id: Index of active speaker
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            tuple: (x, y, width, height) crop box in pixels
        """
        if not faces or active_speaker_id is None:
            # Default center crop
            crop_height = frame_height
            crop_width = int(crop_height * 9 / 16)
            if crop_width > frame_width:
                crop_width = frame_width
                crop_height = int(crop_width * 16 / 9)

            x = (frame_width - crop_width) // 2
            y = (frame_height - crop_height) // 2
            return (x, y, crop_width, crop_height)

        # Get active speaker face
        active_face = faces[active_speaker_id] if active_speaker_id < len(faces) else faces[0]

        # Use FaceTracker to calculate crop box
        crop_box = self.face_tracker.calculate_crop_box(
            active_face, frame_width, frame_height
        )

        return crop_box

    def smooth_crop_box(self, crop_box):
        """
        Apply smoothing to crop box for fluid transitions

        Args:
            crop_box: Current crop box (x, y, w, h)

        Returns:
            tuple: Smoothed crop box
        """
        self.crop_history.append(crop_box)

        if len(self.crop_history) < 2:
            return crop_box

        # Exponential weighted average
        weights = np.exp(np.linspace(-2, 0, len(self.crop_history)))
        weights /= weights.sum()

        smoothed = np.average(
            np.array(self.crop_history),
            weights=weights,
            axis=0
        )

        # Round to integers
        return tuple(int(v) for v in smoothed)

    def process_frame(self, frame, frame_idx):
        """
        Process a single frame with smart cropping

        Args:
            frame: OpenCV frame
            frame_idx: Frame index

        Returns:
            tuple: (cropped_frame, debug_info)
        """
        h, w = frame.shape[:2]

        # Calculate timestamp for MediaPipe
        timestamp_ms = int((frame_idx / config.OUTPUT_FPS) * 1000)

        # Detect all faces
        faces = self.detect_faces_in_frame(frame, timestamp_ms)

        # Smooth face tracking for main face
        if faces:
            faces[0] = self.face_tracker.get_smoothed_position(faces[0])

        # Identify active speaker
        active_speaker_id = self.identify_active_speaker(faces, frame_idx)

        # Calculate crop box
        crop_box = self.calculate_smart_crop(faces, active_speaker_id, w, h)

        # Smooth crop transitions
        smoothed_crop = self.smooth_crop_box(crop_box)

        # Apply crop
        x, y, cw, ch = smoothed_crop
        x, y, cw, ch = max(0, x), max(0, y), min(cw, w - x), min(ch, h - y)

        cropped = frame[y:y + ch, x:x + cw]

        # Resize to target resolution
        output = cv2.resize(cropped, (config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT))

        # Debug info
        debug_info = {
            'num_faces': len(faces),
            'active_speaker': active_speaker_id,
            'crop_box': smoothed_crop,
            'audio_energy': self.audio_energy_per_frame[frame_idx] if self.audio_energy_per_frame is not None and frame_idx < len(self.audio_energy_per_frame) else 0.0
        }

        return output, debug_info

    def draw_debug_overlay(self, frame, faces, active_speaker_id, crop_box):
        """
        Draw debug visualization on frame

        Args:
            frame: OpenCV frame
            faces: Detected faces
            active_speaker_id: Active speaker ID
            crop_box: Crop box

        Returns:
            frame with debug overlay
        """
        debug_frame = frame.copy()
        h, w = frame.shape[:2]

        # Draw crop box
        x, y, cw, ch = crop_box
        cv2.rectangle(debug_frame, (x, y), (x + cw, y + ch), (0, 255, 0), 3)

        # Draw faces
        for i, face in enumerate(faces):
            is_active = (i == active_speaker_id)
            color = (0, 255, 255) if is_active else (255, 0, 0)

            # Draw face box
            if face.get('landmarks'):
                landmarks = face['landmarks']
                eyes_center = (int(landmarks['eyes_center'][0] * w),
                              int(landmarks['eyes_center'][1] * h))
                cv2.circle(debug_frame, eyes_center, 10, color, -1)

                # Label
                label = f"{'SPEAKING' if is_active else 'Silent'}"
                cv2.putText(debug_frame, label, (eyes_center[0] + 15, eyes_center[1]),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        return debug_frame

    def reset(self):
        """Reset all tracking state"""
        self.face_tracker.reset()
        self.lip_sync.reset()
        self.crop_history.clear()
        self.current_speaker_id = None
        self.speaker_stability_counter = 0


if __name__ == "__main__":
    import sys

    print("Smart Cropper - Intelligent Dynamic Cropping System")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUsage: python smart_cropper.py <video_file> [hf_token]")
        print("\nThis will:")
        print("  1. Detect all faces in each frame")
        print("  2. Analyze audio to identify when people speak")
        print("  3. Use lip sync to identify which face is speaking")
        print("  4. Dynamically crop to follow the active speaker")
        print("  5. Apply smooth transitions between speakers")
        sys.exit(1)

    video_path = sys.argv[1]
    hf_token = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\nProcessing: {video_path}")

    # Initialize
    cropper = SmartCropper(hf_token=hf_token)

    # Preprocess
    preprocess_info = cropper.preprocess_video(video_path)

    print("\nReady to process video with smart cropping!")
    print("Integrate this with video_processor.py for full pipeline")
