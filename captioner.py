"""
Subtitle generator (Captioner) using OpenAI Whisper API
Produces word-level timestamps and supports karaoke-style subtitles.
"""
import os
import json
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
from openai import OpenAI
import config
import warnings

# Suppress unnecessary warnings
warnings.filterwarnings("ignore", category=UserWarning)

class WordTimestamp:
    """Represents a word with its timing information"""
    def __init__(self, word: str, start: float, end: float):
        self.word = word.strip().upper()
        self.start = start
        self.end = end

    def to_dict(self):
        return {
            "word": self.word,
            "start": self.start,
            "end": self.end
        }

    def __repr__(self):
        return f"WordTimestamp('{self.word}', {self.start:.2f}s - {self.end:.2f}s)"


class SubtitleSegment:
    """Represents a subtitle segment with multiple words"""
    def __init__(self, words: List[WordTimestamp]):
        self.words = words
        self.start = words[0].start if words else 0
        self.end = words[-1].end if words else 0
        self.text = " ".join([w.word for w in words])

    def get_active_word_index(self, timestamp: float) -> int:
        """
        Get the index of the word that should be highlighted at given timestamp
        Returns -1 if no word is active
        """
        for i, word in enumerate(self.words):
            if word.start <= timestamp < word.end:
                return i
        return -1

    def is_active(self, timestamp: float) -> bool:
        """Check if this segment should be displayed at given timestamp"""
        return self.start <= timestamp < self.end

    def __repr__(self):
        return f"SubtitleSegment({len(self.words)} words, {self.start:.2f}s - {self.end:.2f}s): '{self.text}'"


class Captioner:
    """
    Generate subtitles with word-level timestamps using OpenAI Whisper API
    """
    def __init__(self, model_size=None, device=None):
        """
        Initialize OpenAI client
        Note: model_size and device are kept for compatibility but not used with API
        """
        api_key = config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.segments = []
        print("Initialized OpenAI Captioner")

    def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file to MP3 format
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted MP3 file
        """
        video_path = Path(video_path)
        audio_path = video_path.with_suffix('.mp3')
        
        # If audio already exists, return it
        if audio_path.exists():
            print(f"  Audio already extracted: {audio_path}")
            return str(audio_path)
            
        print(f"  Extracting audio to: {audio_path}")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-q:a', '0',  # Best variable bit rate
            '-map', 'a',
            str(audio_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(audio_path)
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e}")
            raise RuntimeError(f"FFmpeg failed to extract audio: {e.stderr}")

    def _split_audio(self, audio_path: str, chunk_duration: int = 600) -> List[str]:
        """
        Split audio file into chunks for processing large files

        Args:
            audio_path: Path to audio file
            chunk_duration: Duration of each chunk in seconds (default: 10 minutes)

        Returns:
            List of paths to chunk files
        """
        import subprocess

        # Get audio duration
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]

        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        total_duration = float(result.stdout.strip())

        # Calculate number of chunks
        num_chunks = int(total_duration / chunk_duration) + 1

        print(f"  Splitting audio into {num_chunks} chunks ({chunk_duration}s each)...")

        chunk_paths = []
        audio_dir = os.path.dirname(audio_path)
        audio_name = os.path.splitext(os.path.basename(audio_path))[0]

        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = os.path.join(audio_dir, f"{audio_name}_chunk_{i}.mp3")

            split_cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'libmp3lame',
                '-ab', '128k',  # Lower bitrate to reduce file size
                chunk_path
            ]

            subprocess.run(split_cmd, capture_output=True, check=True)
            chunk_paths.append(chunk_path)

        return chunk_paths

    def transcribe_video(self, video_path: str, language=None, initial_prompt=None, preprocess_audio=None) -> List[SubtitleSegment]:
        """
        Transcribe video and generate word-level timestamps using OpenAI API

        Args:
            video_path: Path to video file
            language: Language code (default: from config)
            initial_prompt: Optional prompt (default: from config)
            preprocess_audio: Ignored for API (compatibility)

        Returns:
            List of SubtitleSegment objects
        """
        print(f"Transcribing audio from: {video_path}")

        # Use config defaults if not specified
        language = language or config.WHISPER_LANGUAGE
        initial_prompt = initial_prompt or config.WHISPER_PROMPT

        # 1. Extract Audio
        audio_path = self.extract_audio(video_path)

        # 2. Check file size and split if necessary (OpenAI Whisper limit: 25MB)
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"  Audio file size: {file_size_mb:.2f}MB")

        all_words = []
        chunk_paths = []
        failed_chunks = []

        if file_size_mb > 24:  # Use 24MB to be safe
            print(f"  ⚠️  File exceeds 25MB limit, processing in chunks...")
            chunk_paths = self._split_audio(audio_path, chunk_duration=600)  # 10 min chunks

            time_offset = 0
            # Process each chunk
            for i, chunk_path in enumerate(chunk_paths):
                print(f"  Processing chunk {i+1}/{len(chunk_paths)}...")

                try:
                    with open(chunk_path, "rb") as audio_file:
                        transcript = self.client.audio.transcriptions.create(
                            model=config.WHISPER_MODEL,
                            file=audio_file,
                            language=language,
                            prompt=initial_prompt,
                            response_format="verbose_json",
                            timestamp_granularities=["word"]
                        )

                    # Process words with time offset
                    chunk_word_count = 0
                    if hasattr(transcript, 'words'):
                        for word_data in transcript.words:
                            if isinstance(word_data, dict):
                                word_text = word_data.get('word', '')
                                start = word_data.get('start', 0) + time_offset
                                end = word_data.get('end', 0) + time_offset
                            else:
                                word_text = getattr(word_data, 'word', '')
                                start = getattr(word_data, 'start', 0) + time_offset
                                end = getattr(word_data, 'end', 0) + time_offset

                            word = WordTimestamp(word=word_text, start=start, end=end)
                            if word.word:
                                all_words.append(word)
                                chunk_word_count += 1

                    print(f"  ✓ Chunk {i+1}: {chunk_word_count} words transcribed")

                    # Update offset for next chunk
                    time_offset += 600

                except Exception as e:
                    print(f"  ❌ ERROR processing chunk {i+1}: {e}")
                    failed_chunks.append(i+1)
                    time_offset += 600  # Still increment offset to keep timing correct
                    continue
                finally:
                    # Clean up chunk file
                    if os.path.exists(chunk_path):
                        try:
                            os.remove(chunk_path)
                        except:
                            pass

            # Warn user if chunks failed
            if failed_chunks:
                print(f"\n  ⚠️  WARNING: {len(failed_chunks)}/{len(chunk_paths)} chunks failed to transcribe!")
                print(f"  Failed chunks: {failed_chunks}")
                print(f"  The video may have missing subtitles in those sections.")

        else:
            # 2. Call OpenAI API for single file
            print("  Sending audio to OpenAI Whisper API...")
            try:
                with open(audio_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=config.WHISPER_MODEL,
                        file=audio_file,
                        language=language,
                        prompt=initial_prompt,
                        response_format="verbose_json",
                        timestamp_granularities=["word"]
                    )
            except Exception as e:
                print(f"Error calling OpenAI API: {e}")
                # Clean up audio file on error if we created it
                if os.path.exists(audio_path) and audio_path != video_path:
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                raise

            # 4. Process Word Timestamps
            if hasattr(transcript, 'words'):
                for word_data in transcript.words:
                    # Handle OpenAI object or dict response
                    if isinstance(word_data, dict):
                        word_text = word_data.get('word', '')
                        start = word_data.get('start', 0)
                        end = word_data.get('end', 0)
                    else:
                        word_text = getattr(word_data, 'word', '')
                        start = getattr(word_data, 'start', 0)
                        end = getattr(word_data, 'end', 0)

                    word = WordTimestamp(
                        word=word_text,
                        start=start,
                        end=end
                    )
                    if word.word:
                        all_words.append(word)
            else:
                print("Warning: No word timestamps returned from API")

        # 3. Clean up audio file
        if os.path.exists(audio_path) and audio_path != video_path:
            try:
                os.remove(audio_path)
                print(f"  Cleaned up temporary audio file")
            except:
                pass

        # Validate that Whisper didn't just return the prompt as transcription
        if len(all_words) > 0 and initial_prompt and len(initial_prompt.strip()) > 0:
            # Check if transcription matches the prompt (hallucination)
            # This can happen with generic prompts
            transcribed_text = " ".join([w.word for w in all_words]).lower()
            prompt_normalized = initial_prompt.lower().replace("este é um ", "").replace("este é uma ", "").replace(".", "").strip()

            # Only check if prompt is substantial (more than 3 words)
            if len(prompt_normalized.split()) >= 3:
                if prompt_normalized in transcribed_text or transcribed_text in prompt_normalized:
                    print(f"\n  ⚠️  WARNING: Whisper returned the prompt as transcription (hallucination)!")
                    print(f"  This usually means the generic prompt is interfering with transcription.")
                    print(f"  Transcribed text: '{transcribed_text[:100]}...'")
                    print(f"  Prompt: '{prompt_normalized}'")
                    print(f"  TIP: Try using an empty prompt or a content-specific one.")
                    all_words = []  # Clear the hallucinated transcription

        if len(all_words) == 0:
            print(f"\n  ⚠️  WARNING: No words were transcribed!")
            print(f"  This video will NOT have subtitles.")
            print(f"  Possible causes:")
            print(f"    - Audio file is silent or corrupted")
            print(f"    - Whisper API failed to detect speech")
            print(f"    - All chunks failed (if file was split)")
            print(f"    - Whisper hallucinated and returned the prompt")
        else:
            print(f"  ✓ Transcription complete: {len(all_words)} words detected")

        # 5. Save transcript_words.json (only if we have valid words)
        if len(all_words) > 0:
            json_output_path = str(Path(video_path).with_name("transcript_words.json"))
            self._save_words_json(all_words, json_output_path)

        # 6. Group words into segments (max 3 words per segment as per config)
        max_words = config.SUBTITLE_MAX_WORDS if hasattr(config, 'SUBTITLE_MAX_WORDS') else 3
        self.segments = self._group_words_into_segments(all_words, max_words=max_words)

        print(f"  Created {len(self.segments)} subtitle segments")

        # 7. Auto-export SRT (only if we have segments)
        if len(self.segments) > 0:
            srt_output_path = str(Path(video_path).with_name("transcript.srt"))
            self.export_srt(srt_output_path)

        return self.segments

    def _save_words_json(self, words: List[WordTimestamp], output_path: str):
        """Save exact word timestamps to JSON"""
        data = [w.to_dict() for w in words]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved word timestamps to: {output_path}")

    def _group_words_into_segments(self, words: List[WordTimestamp], max_words: int = 3) -> List[SubtitleSegment]:
        """Group words into subtitle segments"""
        segments = []
        current_group = []

        for word in words:
            current_group.append(word)

            if len(current_group) >= max_words:
                segments.append(SubtitleSegment(current_group))
                current_group = []

        if current_group:
            segments.append(SubtitleSegment(current_group))

        return segments

    def export_srt(self, output_path: str):
        """Export subtitles to SRT format"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(self.segments, 1):
                start_time = self._format_srt_timestamp(segment.start)
                end_time = self._format_srt_timestamp(segment.end)

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment.text}\n")
                f.write("\n")

        print(f"  Exported subtitles to: {output_path}")

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format timestamp as SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python captioner.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"Error: File not found: {video_path}")
        sys.exit(1)

    try:
        # Generate subtitles
        captioner = Captioner()
        segments = captioner.transcribe_video(video_path)

        # Print segments
        print("\nGenerated segments:")
        for i, segment in enumerate(segments[:10], 1):
            print(f"{i}. {segment}")

        if len(segments) > 10:
            print(f"... and {len(segments) - 10} more segments")
            
    except Exception as e:
        print(f"Error: {e}")
