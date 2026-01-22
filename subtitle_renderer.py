"""
Subtitle renderer with karaoke-style word highlighting
Renders subtitles with custom fonts and color effects on video frames
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple
from captioner import SubtitleSegment
import config


class SubtitleRenderer:
    """
    Renders subtitles on video frames with karaoke-style highlighting
    """
    def __init__(
        self,
        font_path: str = None,
        font_size: int = None,
        position: Tuple[float, float] = None,
        default_color: Tuple[int, int, int] = None,
        highlight_color: Tuple[int, int, int] = None,
        outline_color: Tuple[int, int, int] = None,
        outline_width: int = None
    ):
        """
        Initialize subtitle renderer

        Args:
            font_path: Path to TTF font file
            font_size: Font size in points
            position: Subtitle position as (x_ratio, y_ratio) where 0.5 is center
            default_color: RGB color for non-highlighted words (white)
            highlight_color: RGB color for highlighted words (green)
            outline_color: RGB color for text outline (black)
            outline_width: Width of text outline in pixels
        """
        # Use config defaults if not specified
        self.font_path = font_path or config.SUBTITLE_FONT_PATH
        self.font_size = font_size or config.SUBTITLE_FONT_SIZE
        self.position = position or config.SUBTITLE_POSITION
        self.default_color = default_color or config.SUBTITLE_DEFAULT_COLOR
        self.highlight_color = highlight_color or config.SUBTITLE_HIGHLIGHT_COLOR
        self.outline_color = outline_color or config.SUBTITLE_OUTLINE_COLOR
        self.outline_width = outline_width if outline_width is not None else config.SUBTITLE_OUTLINE_WIDTH

        # Load font
        try:
            self.font = ImageFont.truetype(self.font_path, self.font_size)
        except Exception as e:
            print(f"Warning: Could not load font {self.font_path}: {e}")
            print("Using default font")
            self.font = ImageFont.load_default()

    def render_subtitle_on_frame(
        self,
        frame: np.ndarray,
        segment: SubtitleSegment,
        timestamp: float
    ) -> np.ndarray:
        """
        Render subtitle on video frame with karaoke highlighting

        Args:
            frame: Video frame (numpy array, BGR format)
            segment: SubtitleSegment to render
            timestamp: Current timestamp in seconds

        Returns:
            Frame with subtitle rendered
        """
        if segment is None or not segment.words:
            return frame

        # Convert frame to PIL Image for better text rendering
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_image)

        # Get frame dimensions
        height, width = frame.shape[:2]

        # Calculate position
        center_x = int(width * self.position[0])
        center_y = int(height * self.position[1])

        # Get which word should be highlighted
        active_word_idx = segment.get_active_word_index(timestamp)

        # Calculate text metrics for each word
        word_positions = []
        total_width = 0
        max_height = 0

        for i, word_obj in enumerate(segment.words):
            bbox = draw.textbbox((0, 0), word_obj.word.upper() + " ", font=self.font)
            word_width = bbox[2] - bbox[0]
            word_height = bbox[3] - bbox[1]

            word_positions.append({
                'word': word_obj.word.upper(),
                'width': word_width,
                'height': word_height,
                'is_active': i == active_word_idx
            })

            total_width += word_width
            max_height = max(max_height, word_height)

        # Calculate starting X position to center the text
        current_x = center_x - (total_width // 2)
        current_y = center_y - (max_height // 2)

        # Draw each word
        for word_info in word_positions:
            word = word_info['word']
            color = self.highlight_color if word_info['is_active'] else self.default_color

            # Draw outline (draw multiple times with offset for thicker outline)
            for offset_x in range(-self.outline_width, self.outline_width + 1):
                for offset_y in range(-self.outline_width, self.outline_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        draw.text(
                            (current_x + offset_x, current_y + offset_y),
                            word,
                            font=self.font,
                            fill=self.outline_color
                        )

            # Draw main text
            draw.text(
                (current_x, current_y),
                word,
                font=self.font,
                fill=color
            )

            # Move to next word position
            current_x += word_info['width']

        # Convert back to OpenCV format
        frame_with_subtitle = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        return frame_with_subtitle

    def render_subtitle_with_shadow(
        self,
        frame: np.ndarray,
        segment: SubtitleSegment,
        timestamp: float,
        shadow_offset: int = 3,
        shadow_opacity: float = 0.5
    ) -> np.ndarray:
        """
        Render subtitle with drop shadow effect

        Args:
            frame: Video frame
            segment: SubtitleSegment to render
            timestamp: Current timestamp
            shadow_offset: Shadow offset in pixels
            shadow_opacity: Shadow opacity (0.0 - 1.0)

        Returns:
            Frame with subtitle and shadow
        """
        if segment is None or not segment.words:
            return frame

        # Create a copy for shadow
        shadow_frame = frame.copy()

        # Temporarily adjust position for shadow
        original_position = self.position
        self.position = (
            self.position[0] + (shadow_offset / frame.shape[1]),
            self.position[1] + (shadow_offset / frame.shape[0])
        )

        # Temporarily change colors for shadow
        original_default = self.default_color
        original_highlight = self.highlight_color
        shadow_color = (50, 50, 50)
        self.default_color = shadow_color
        self.highlight_color = shadow_color

        # Render shadow
        shadow_frame = self.render_subtitle_on_frame(shadow_frame, segment, timestamp)

        # Restore original settings
        self.position = original_position
        self.default_color = original_default
        self.highlight_color = original_highlight

        # Blend shadow with original frame
        blended = cv2.addWeighted(frame, 1.0, shadow_frame, shadow_opacity, 0)

        # Render main subtitle on blended frame
        final_frame = self.render_subtitle_on_frame(blended, segment, timestamp)

        return final_frame


if __name__ == "__main__":
    # Test the subtitle renderer
    import sys
    from captioner import WordTimestamp, SubtitleSegment

    print("Subtitle Renderer Test")
    print("=" * 60)

    # Create a test frame (blue background)
    test_frame = np.full((1920, 1080, 3), (200, 150, 100), dtype=np.uint8)

    # Create test subtitle
    words = [
        WordTimestamp("Olá", 0.0, 0.5),
        WordTimestamp("mundo", 0.5, 1.0),
        WordTimestamp("teste", 1.0, 1.5)
    ]
    segment = SubtitleSegment(words)

    # Initialize renderer
    renderer = SubtitleRenderer()

    # Render at different timestamps
    timestamps = [0.25, 0.75, 1.25]
    for i, ts in enumerate(timestamps):
        print(f"Rendering frame at {ts}s...")
        result = renderer.render_subtitle_on_frame(test_frame.copy(), segment, ts)

        # Save test image
        output_path = f"test_subtitle_{i}.jpg"
        cv2.imwrite(output_path, result)
        print(f"  Saved: {output_path}")

    print("\nTest complete!")
