"""
Export subtitles to various formats (ASS, SRT) for FFmpeg
Supports karaoke-style word highlighting using ASS format
"""
from typing import List
from captioner import SubtitleSegment
import config
import os


class SubtitleExporter:
    """
    Export subtitle segments to file formats compatible with FFmpeg
    """

    def __init__(
        self,
        font_name: str = None,
        font_size: int = None,
        primary_color: str = "&H00FFFFFF",  # White (AABBGGRR format)
        highlight_color: str = "&H0000FF00",  # Green (AABBGGRR format)
        outline_color: str = "&H00000000",  # Black
        outline_width: int = None,
        video_width: int = None,
        video_height: int = None
    ):
        """
        Initialize subtitle exporter

        Args:
            font_name: Font name or path to font file
            font_size: Font size
            primary_color: Default text color in ASS format (&HAABBGGRR)
            highlight_color: Highlighted word color in ASS format
            outline_color: Outline color in ASS format
            outline_width: Outline width
            video_width: Video width for positioning
            video_height: Video height for positioning
        """
        if font_name is None:
            font_path = config.SUBTITLE_FONT_PATH
            font_filename = os.path.basename(font_path)  # Define ANTES do try
            
            try:
                from PIL import ImageFont
                temp_font = ImageFont.truetype(font_path, 12)
                if hasattr(temp_font, 'getname'):
                    self.font_name = temp_font.getname()[0]  # Get family name
                else:
                    self.font_name = os.path.splitext(font_filename)[0]
            except Exception:
                # Fallback: detecta pelo nome do arquivo
                if "archivoblack" in font_filename.lower():
                    self.font_name = "Archivo Black"
                else:
                    self.font_name = os.path.splitext(font_filename)[0]
            
            # Store full path for ASS file if font is not installed
            self.font_path = os.path.abspath(font_path)
        else:
            self.font_name = font_name
            self.font_path = None

        self.font_size = font_size or config.SUBTITLE_FONT_SIZE
        self.primary_color = primary_color
        self.highlight_color = highlight_color
        self.outline_color = outline_color
        self.outline_width = outline_width or config.SUBTITLE_OUTLINE_WIDTH
        self.video_width = video_width or config.OUTPUT_WIDTH
        self.video_height = video_height or config.OUTPUT_HEIGHT

    def _rgb_to_ass_color(self, rgb: tuple) -> str:
        """
        Convert RGB tuple to ASS color format (&HAABBGGRR)

        Args:
            rgb: (R, G, B) tuple

        Returns:
            ASS color string
        """
        r, g, b = rgb
        return f"&H00{b:02X}{g:02X}{r:02X}"

    def export_to_ass(self, segments: List[SubtitleSegment], output_path: str) -> str:
        """
        Export subtitle segments to ASS file with karaoke effects
        Embeds the custom font directly in the ASS file

        Args:
            segments: List of SubtitleSegment objects
            output_path: Path to save ASS file

        Returns:
            Path to created ASS file
        """
        # Convert RGB colors from config to ASS format if needed
        if hasattr(config, 'SUBTITLE_DEFAULT_COLOR'):
            self.primary_color = self._rgb_to_ass_color(config.SUBTITLE_DEFAULT_COLOR)
        if hasattr(config, 'SUBTITLE_HIGHLIGHT_COLOR'):
            self.highlight_color = self._rgb_to_ass_color(config.SUBTITLE_HIGHLIGHT_COLOR)
        if hasattr(config, 'SUBTITLE_OUTLINE_COLOR'):
            self.outline_color = self._rgb_to_ass_color(config.SUBTITLE_OUTLINE_COLOR)

        # Calculate vertical margin from bottom based on config
        # Position is (x, y) ratio from top-left. ASS MarginV is distance from bottom.
        y_ratio = config.SUBTITLE_POSITION[1]
        margin_v = int(self.video_height * (1.0 - y_ratio))

        # ASS file header with font attachment support and word wrapping
        ass_content = f"""[Script Info]
Title: Auto-generated Subtitles
ScriptType: v4.00+
WrapStyle: 2
ScaledBorderAndShadow: yes
PlayResX: {self.video_width}
PlayResY: {self.video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.font_name},{self.font_size},{self.highlight_color},{self.primary_color},{self.outline_color},&H00000000,0,0,0,0,100,100,0,0,1,{self.outline_width},2,2,50,50,{margin_v},1

"""

        # Embed font file in ASS
        if self.font_path and os.path.exists(self.font_path):
            import base64

            with open(self.font_path, 'rb') as f:
                font_data = f.read()

            # Encode font to base64
            font_base64 = base64.b64encode(font_data).decode('ascii')

            # Split into 80-character lines as per ASS spec
            font_lines = [font_base64[i:i+80] for i in range(0, len(font_base64), 80)]

            ass_content += "[Fonts]\n"
            ass_content += f"fontname: {os.path.basename(self.font_path)}\n"
            for line in font_lines:
                ass_content += line + "\n"
            ass_content += "\n"

        ass_content += "[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

        # Add each segment with karaoke effect
        for segment in segments:
            if not segment.words:
                continue

            # Calculate timing for karaoke effect
            start_time = self._format_ass_time(segment.start)
            end_time = self._format_ass_time(segment.end)

            # Build karaoke text with timing tags and word wrapping
            karaoke_text = self._build_karaoke_text(segment)

            # Add dialogue line
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}\n"

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        print(f"  Subtitle file created with {self.font_name} font embedded: {output_path}")

        return output_path

    def _format_ass_time(self, seconds: float) -> str:
        """
        Format time in seconds to ASS time format (H:MM:SS.CC)

        Args:
            seconds: Time in seconds

        Returns:
            ASS formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _build_karaoke_text(self, segment: SubtitleSegment) -> str:
        """
        Build karaoke-style text with ASS tags for word highlighting
        Adds line breaks to prevent text overflow

        Args:
            segment: SubtitleSegment with word timings

        Returns:
            ASS formatted text with karaoke tags and line breaks
        """
        # ASS karaoke format: {\k<duration_centisecs>}word
        # Duration is how long until the word gets highlighted

        parts = []
        current_line_length = 0
        max_chars_per_line = 15  # Archvio Black is wide, so we need fewer chars per line

        for i, word_obj in enumerate(segment.words):
            # Calculate duration in centiseconds (1/100 second)
            word_duration = (word_obj.end - word_obj.start) * 100

            # Build word with karaoke tag
            word_with_tag = f"{{\\k{int(word_duration)}}}{word_obj.word}"

            # Check if adding this word would exceed line length
            if current_line_length > 0 and current_line_length + len(word_obj.word) + 1 > max_chars_per_line:
                # Add line break (ASS uses \N for hard line break)
                parts.append("\\N")
                current_line_length = 0

            # Add space before word if not at start of line
            if current_line_length > 0:
                parts.append(" ")
                current_line_length += 1

            parts.append(word_with_tag)
            current_line_length += len(word_obj.word)

        return "".join(parts)

    def export_to_srt(self, segments: List[SubtitleSegment], output_path: str) -> str:
        """
        Export subtitle segments to simple SRT file (no karaoke effects)

        Args:
            segments: List of SubtitleSegment objects
            output_path: Path to save SRT file

        Returns:
            Path to created SRT file
        """
        srt_content = ""

        for i, segment in enumerate(segments, 1):
            if not segment.words:
                continue

            # Format: 1\n00:00:00,000 --> 00:00:02,000\nText\n\n
            start_time = self._format_srt_time(segment.start)
            end_time = self._format_srt_time(segment.end)
            text = " ".join([w.word for w in segment.words])

            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)

        return output_path

    def _format_srt_time(self, seconds: float) -> str:
        """
        Format time in seconds to SRT time format (HH:MM:SS,mmm)

        Args:
            seconds: Time in seconds

        Returns:
            SRT formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


if __name__ == "__main__":
    # Test the exporter
    from captioner import WordTimestamp, SubtitleSegment

    print("Subtitle Exporter Test")
    print("=" * 60)

    # Create test segments
    words1 = [
        WordTimestamp("Olá", 0.0, 0.5),
        WordTimestamp("mundo", 0.5, 1.0),
        WordTimestamp("teste", 1.0, 1.5)
    ]
    words2 = [
        WordTimestamp("Segunda", 2.0, 2.5),
        WordTimestamp("linha", 2.5, 3.0),
    ]

    segments = [
        SubtitleSegment(words1),
        SubtitleSegment(words2)
    ]

    # Test ASS export
    exporter = SubtitleExporter()
    print(f"Font name detected: {exporter.font_name}")
    print(f"Font path: {exporter.font_path}")
    
    ass_path = "test_subtitles.ass"
    exporter.export_to_ass(segments, ass_path)
    print(f"ASS file created: {ass_path}")

    # Test SRT export
    srt_path = "test_subtitles.srt"
    exporter.export_to_srt(segments, srt_path)
    print(f"SRT file created: {srt_path}")

    print("\nTest complete!")