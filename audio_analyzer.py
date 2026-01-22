"""
Audio analysis module for voice activity detection and audio energy
100% offline - no APIs or external tokens required
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
import warnings

try:
    import webrtcvad
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    warnings.warn("webrtcvad not available. Using energy-based VAD instead.")


class AudioAnalyzer:
    """
    Analyzes audio to detect:
    1. Voice Activity Detection (VAD) - when someone is speaking
    2. Audio energy levels - for detecting emphasis and important moments
    3. Simple speaker tracking using audio clusters

    100% offline - no external APIs or tokens needed
    """

    def __init__(self, hf_token=None):
        """
        Initialize audio analyzer

        Args:
            hf_token: Optional HuggingFace token for speaker diarization
        """
        self.pipeline = None
        self.hf_token = hf_token

        # Try to load speaker diarization pipeline if token provided
        if hf_token:
            try:
                from pyannote.audio import Pipeline
                # Try new parameter name first, fallback to old one
                try:
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        token=hf_token  # New parameter name
                    )
                except TypeError:
                    # Fallback to old parameter name
                    self.pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
            except Exception as e:
                warnings.warn(f"Could not load speaker diarization pipeline: {e}")
                self.pipeline = None

    def extract_audio_from_video(self, video_path, output_path=None):
        """
        Extract audio from video file

        Args:
            video_path: Path to video file
            output_path: Path to save audio (optional)

        Returns:
            tuple: (audio_array, sample_rate)
        """
        import subprocess
        import tempfile

        if output_path is None:
            temp_dir = tempfile.mkdtemp()
            output_path = Path(temp_dir) / "audio.wav"

        # Use ffmpeg to extract audio
        cmd = [
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Fallback: use librosa to load audio directly
            warnings.warn(f"FFmpeg extraction failed, using librosa: {e}")
            y, sr = librosa.load(video_path, sr=16000, mono=True)
            sf.write(str(output_path), y, sr)
            return y, sr

        # Load the extracted audio
        y, sr = librosa.load(str(output_path), sr=16000, mono=True)
        return y, sr

    def detect_voice_activity(self, audio, sample_rate, frame_duration_ms=30):
        """
        Detect voice activity (when someone is speaking)

        Args:
            audio: Audio array
            sample_rate: Sample rate
            frame_duration_ms: Frame duration in milliseconds (10, 20, or 30)

        Returns:
            list: List of tuples (start_time, end_time, is_speech)
        """
        if WEBRTC_AVAILABLE:
            return self._webrtc_vad(audio, sample_rate, frame_duration_ms)
        else:
            return self._energy_based_vad(audio, sample_rate)

    def _webrtc_vad(self, audio, sample_rate, frame_duration_ms=30):
        """WebRTC VAD (more accurate)"""
        vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3 (3 = most aggressive)

        # Resample to 16kHz if needed (WebRTC requires this)
        if sample_rate != 16000:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            sample_rate = 16000

        # Convert to int16
        audio_int16 = (audio * 32768).astype(np.int16)

        # Frame duration in samples
        frame_length = int(sample_rate * frame_duration_ms / 1000)

        # Detect voice activity
        voice_segments = []
        is_speaking = False
        segment_start = 0

        for i in range(0, len(audio_int16) - frame_length, frame_length):
            frame = audio_int16[i:i + frame_length].tobytes()

            try:
                is_speech = vad.is_speech(frame, sample_rate)
            except:
                is_speech = False

            timestamp = i / sample_rate

            if is_speech and not is_speaking:
                # Start of speech
                segment_start = timestamp
                is_speaking = True
            elif not is_speech and is_speaking:
                # End of speech
                voice_segments.append((segment_start, timestamp, True))
                is_speaking = False

        # Close last segment if still speaking
        if is_speaking:
            voice_segments.append((segment_start, len(audio_int16) / sample_rate, True))

        return voice_segments

    def _energy_based_vad(self, audio, sample_rate, threshold_db=-40):
        """Simple energy-based VAD (fallback)"""
        # Calculate short-time energy
        hop_length = int(sample_rate * 0.01)  # 10ms hop
        frame_length = int(sample_rate * 0.03)  # 30ms frames

        energy = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]

        # Convert to dB
        energy_db = librosa.amplitude_to_db(energy, ref=np.max)

        # Threshold
        is_speech = energy_db > threshold_db

        # Convert to time segments
        voice_segments = []
        is_speaking = False
        segment_start = 0

        for i, speech in enumerate(is_speech):
            timestamp = i * hop_length / sample_rate

            if speech and not is_speaking:
                segment_start = timestamp
                is_speaking = True
            elif not speech and is_speaking:
                voice_segments.append((segment_start, timestamp, True))
                is_speaking = False

        if is_speaking:
            voice_segments.append((segment_start, len(audio) / sample_rate, True))

        return voice_segments

    def diarize_speakers(self, audio_path):
        """
        Perform speaker diarization (identify who speaks when)

        Args:
            audio_path: Path to audio file

        Returns:
            dict: {
                'timeline': [(start, end, speaker_id), ...],
                'num_speakers': int
            }
        """
        if not self.pipeline:
            warnings.warn("Speaker diarization not available. Using VAD only.")
            # Fallback to simple VAD
            audio, sr = librosa.load(audio_path, sr=16000, mono=True)
            vad_segments = self.detect_voice_activity(audio, sr)
            return {
                'timeline': [(start, end, 'SPEAKER_00') for start, end, _ in vad_segments],
                'num_speakers': 1
            }

        try:
            # Run diarization
            diarization = self.pipeline(audio_path)

            # Convert to timeline format
            timeline = []
            speakers = set()

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                timeline.append((turn.start, turn.end, speaker))
                speakers.add(speaker)

            return {
                'timeline': timeline,
                'num_speakers': len(speakers)
            }

        except Exception as e:
            warnings.warn(f"Diarization failed: {e}")
            return {
                'timeline': [],
                'num_speakers': 0
            }

    def get_audio_energy_per_frame(self, audio, sample_rate, fps=30):
        """
        Get audio energy for each video frame

        Args:
            audio: Audio array
            sample_rate: Sample rate
            fps: Video frames per second

        Returns:
            np.array: Energy value for each frame
        """
        samples_per_frame = int(sample_rate / fps)
        num_frames = int(len(audio) / samples_per_frame)

        energy_per_frame = []

        for i in range(num_frames):
            start = i * samples_per_frame
            end = start + samples_per_frame
            frame_audio = audio[start:end]

            # Calculate RMS energy
            if len(frame_audio) > 0:
                energy = np.sqrt(np.mean(frame_audio ** 2))
            else:
                energy = 0.0

            energy_per_frame.append(energy)

        return np.array(energy_per_frame)

    def align_speech_with_frames(self, speech_segments, fps, total_frames):
        """
        Align speech segments with video frames

        Args:
            speech_segments: List of (start, end, speaker) tuples
            fps: Video frames per second
            total_frames: Total number of frames in video

        Returns:
            np.array: Boolean array indicating if each frame has speech
        """
        speech_mask = np.zeros(total_frames, dtype=bool)

        for start_time, end_time, _ in speech_segments:
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)

            # Clamp to valid range
            start_frame = max(0, min(start_frame, total_frames - 1))
            end_frame = max(0, min(end_frame, total_frames))

            speech_mask[start_frame:end_frame] = True

        return speech_mask

    def get_speaker_per_frame(self, speech_segments, fps, total_frames):
        """
        Get which speaker is active for each frame

        Args:
            speech_segments: List of (start, end, speaker) tuples
            fps: Video frames per second
            total_frames: Total number of frames

        Returns:
            list: Speaker ID for each frame (None if no speech)
        """
        speaker_per_frame = [None] * total_frames

        for start_time, end_time, speaker in speech_segments:
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)

            start_frame = max(0, min(start_frame, total_frames - 1))
            end_frame = max(0, min(end_frame, total_frames))

            for frame_idx in range(start_frame, end_frame):
                speaker_per_frame[frame_idx] = speaker

        return speaker_per_frame


if __name__ == "__main__":
    import sys

    print("Audio Analyzer Test")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Usage: python audio_analyzer.py <video_or_audio_file> [hf_token]")
        print("\nTo use speaker diarization:")
        print("1. Get HuggingFace token: https://huggingface.co/settings/tokens")
        print("2. Accept model license: https://huggingface.co/pyannote/speaker-diarization")
        print("3. Run: python audio_analyzer.py video.mp4 your_hf_token")
        sys.exit(1)

    file_path = sys.argv[1]
    hf_token = sys.argv[2] if len(sys.argv) > 2 else None

    # Initialize analyzer
    analyzer = AudioAnalyzer(hf_token=hf_token)

    print(f"\nAnalyzing: {file_path}")

    # Extract audio
    print("\n1. Extracting audio...")
    audio, sr = analyzer.extract_audio_from_video(file_path)
    print(f"   Duration: {len(audio) / sr:.2f}s")
    print(f"   Sample rate: {sr} Hz")

    # Voice activity detection
    print("\n2. Detecting voice activity...")
    vad_segments = analyzer.detect_voice_activity(audio, sr)
    print(f"   Found {len(vad_segments)} speech segments")
    total_speech_time = sum(end - start for start, end, _ in vad_segments)
    print(f"   Total speech time: {total_speech_time:.2f}s")

    # Speaker diarization
    if hf_token:
        print("\n3. Performing speaker diarization...")
        import tempfile
        temp_audio = Path(tempfile.mkdtemp()) / "audio.wav"
        sf.write(str(temp_audio), audio, sr)

        diarization = analyzer.diarize_speakers(str(temp_audio))
        print(f"   Number of speakers: {diarization['num_speakers']}")
        print(f"   Timeline segments: {len(diarization['timeline'])}")

        # Show first few segments
        print("\n   First segments:")
        for start, end, speaker in diarization['timeline'][:5]:
            print(f"   {start:.2f}s - {end:.2f}s: {speaker}")
    else:
        print("\n3. Speaker diarization skipped (no HF token)")
        print("   To enable: provide HuggingFace token as second argument")

    # Energy analysis
    print("\n4. Analyzing audio energy...")
    energy = analyzer.get_audio_energy_per_frame(audio, sr, fps=30)
    print(f"   Mean energy: {np.mean(energy):.6f}")
    print(f"   Max energy: {np.max(energy):.6f}")
    print(f"   Peak frames: {np.sum(energy > np.percentile(energy, 90))}")

    print("\nAnalysis complete!")
