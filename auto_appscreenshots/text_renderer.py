"""Text rendering utilities following Single Responsibility Principle."""

import logging

from PIL import ImageDraw, ImageFont

from .font_finder import FontFinder
from .image_processor import ImageProcessor
from .models import TextStyle

logger = logging.getLogger(__name__)


class TextPosition:
    """Represents text position and layout information."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text_area_height: int,
        is_main: bool,
        has_sub_text: bool,
        is_inverted: bool,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text_area_height = text_area_height
        self.is_main = is_main
        self.has_sub_text = has_sub_text
        self.is_inverted = is_inverted


class TextRenderer:
    """Handles text rendering operations."""

    def __init__(self) -> None:
        self.image_processor = ImageProcessor()

    def render_text(self, draw: ImageDraw.ImageDraw, text: str, position: TextPosition, style: TextStyle) -> None:
        """Render text with specified style at given position."""
        font = self._load_font(style.font_family, style.font_size, style.font_weight, style.font_style)

        # Calculate text dimensions and position
        x, y = self._calculate_text_position(draw, text, font, position, style)

        # Draw shadow if enabled
        if style.shadow:
            self._draw_shadow(draw, text, x, y, font, style)

        # Draw main text
        text_color = self.image_processor.parse_color(style.color)
        draw.text((x, y), text, font=font, fill=text_color)  # type: ignore[attr-defined, unused-ignore]

    def _load_font(
        self, font_family: str, font_size: int, font_weight: str | None = None, font_style: str = "normal"
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Load font with fallback to default."""
        font = FontFinder.load_font(font_family, font_size, font_weight, font_style)
        if font:
            return font
        else:
            return ImageFont.load_default()

    def _calculate_text_position(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        position: TextPosition,
        style: TextStyle,
    ) -> tuple[int, int]:
        """Calculate final text position including offsets."""
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = int(bbox[2] - bbox[0])
        text_height = int(bbox[3] - bbox[1])

        # Center text horizontally
        x = (position.width - text_width) // 2

        # Calculate vertical position
        y = self._calculate_vertical_position(
            position.text_area_height,
            text_height,
            int(bbox[1]),
            position.is_main,
            position.has_sub_text,
            position.is_inverted,
        )

        # Apply user-defined offset
        offset_x, offset_y = style.offset
        x += offset_x
        y += offset_y

        return x, y

    def _calculate_vertical_position(
        self,
        text_area_height: int,
        text_height: int,
        bbox_top: int,
        is_main: bool,
        has_sub_text: bool,
        is_inverted: bool,
    ) -> int:
        """Calculate vertical position based on layout configuration."""
        if is_inverted:
            # Inverted layout: sub_text on top, main_text on bottom
            if is_main:
                if has_sub_text:
                    y = int(text_area_height * 0.65) - text_height // 2
                else:
                    y = (text_area_height - text_height) // 2 - bbox_top
            else:
                y = int(text_area_height * 0.25) - text_height // 2
        else:
            # Standard layout: main_text on top, sub_text on bottom
            if is_main:
                if has_sub_text:
                    y = int(text_area_height * 0.25) - text_height // 2
                else:
                    y = (text_area_height - text_height) // 2 - bbox_top
            else:
                y = int(text_area_height * 0.65) - text_height // 2

        return y

    def _draw_shadow(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        style: TextStyle,
    ) -> None:
        """Draw text shadow."""
        shadow_offset_x, shadow_offset_y = style.shadow_offset
        shadow_color = self.image_processor.parse_color(style.shadow_color)
        draw.text((x + shadow_offset_x, y + shadow_offset_y), text, font=font, fill=shadow_color)  # type: ignore[attr-defined, unused-ignore]
