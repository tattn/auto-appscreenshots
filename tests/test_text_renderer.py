"""Tests for text rendering utilities."""

from typing import Any
from unittest.mock import MagicMock

from PIL import ImageDraw, ImageFont

from auto_appscreenshots.models import TextStyle
from auto_appscreenshots.text_renderer import TextPosition, TextRenderer


class TestTextPosition:
    """Test TextPosition class."""

    def test_text_position_init(self) -> None:
        """Test TextPosition initialization."""
        pos = TextPosition(
            x=10, y=20, width=300, height=400, text_area_height=500, is_main=True, has_sub_text=True, is_inverted=False
        )

        assert pos.x == 10
        assert pos.y == 20
        assert pos.width == 300
        assert pos.height == 400
        assert pos.text_area_height == 500
        assert pos.is_main is True
        assert pos.has_sub_text is True
        assert pos.is_inverted is False


class TestTextRenderer:
    """Test TextRenderer class."""

    def test_render_text_with_shadow(self, mocker: Any) -> None:
        """Test rendering text with shadow."""
        # Mock font loading
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        mocker.patch("auto_appscreenshots.font_finder.FontFinder.load_font", return_value=mock_font)

        # Create renderer and mock draw
        renderer = TextRenderer()
        mock_draw = MagicMock(spec=ImageDraw.ImageDraw)
        mock_draw.textbbox.return_value = (0, 0, 100, 50)  # Mock text dimensions

        # Create position and style
        position = TextPosition(
            x=0, y=0, width=500, height=100, text_area_height=400, is_main=True, has_sub_text=False, is_inverted=False
        )
        style = TextStyle(
            font_family="Arial",
            font_size=72,
            color="#FFFFFF",
            shadow=True,
            shadow_color="#000000",
            shadow_offset=(2, 2),
        )

        # Render text
        renderer.render_text(mock_draw, "Test Text", position, style)

        # Verify shadow was drawn
        assert mock_draw.text.call_count == 2  # Shadow + main text

        # Check shadow call (first call)
        shadow_call = mock_draw.text.call_args_list[0]
        assert shadow_call[0][1] == "Test Text"

        # Check main text call (second call)
        main_call = mock_draw.text.call_args_list[1]
        assert main_call[0][1] == "Test Text"

    def test_render_text_without_shadow(self, mocker: Any) -> None:
        """Test rendering text without shadow."""
        # Mock font loading
        mock_font = MagicMock(spec=ImageFont.FreeTypeFont)
        mocker.patch("auto_appscreenshots.font_finder.FontFinder.load_font", return_value=mock_font)

        # Create renderer and mock draw
        renderer = TextRenderer()
        mock_draw = MagicMock(spec=ImageDraw.ImageDraw)
        mock_draw.textbbox.return_value = (0, 0, 100, 50)

        # Create position and style without shadow
        position = TextPosition(
            x=0, y=0, width=500, height=100, text_area_height=400, is_main=True, has_sub_text=False, is_inverted=False
        )
        style = TextStyle(font_family="Arial", font_size=72, color="#FFFFFF", shadow=False)

        # Render text
        renderer.render_text(mock_draw, "Test Text", position, style)

        # Verify only main text was drawn (no shadow)
        assert mock_draw.text.call_count == 1

    def test_calculate_vertical_position_standard_main(self) -> None:
        """Test vertical position calculation for standard layout main text."""
        renderer = TextRenderer()

        # Standard layout, main text with subtitle
        y = renderer._calculate_vertical_position(
            text_area_height=400, text_height=50, bbox_top=0, is_main=True, has_sub_text=True, is_inverted=False
        )

        # Should be positioned at 25% of text area
        expected = int(400 * 0.25) - 50 // 2
        assert y == expected

    def test_calculate_vertical_position_standard_sub(self) -> None:
        """Test vertical position calculation for standard layout subtitle."""
        renderer = TextRenderer()

        # Standard layout, subtitle
        y = renderer._calculate_vertical_position(
            text_area_height=400, text_height=30, bbox_top=0, is_main=False, has_sub_text=True, is_inverted=False
        )

        # Should be positioned at 65% of text area
        expected = int(400 * 0.65) - 30 // 2
        assert y == expected

    def test_calculate_vertical_position_inverted_main(self) -> None:
        """Test vertical position calculation for inverted layout main text."""
        renderer = TextRenderer()

        # Inverted layout, main text with subtitle
        y = renderer._calculate_vertical_position(
            text_area_height=400, text_height=50, bbox_top=0, is_main=True, has_sub_text=True, is_inverted=True
        )

        # Should be positioned at 65% of text area (bottom)
        expected = int(400 * 0.65) - 50 // 2
        assert y == expected

    def test_calculate_vertical_position_inverted_sub(self) -> None:
        """Test vertical position calculation for inverted layout subtitle."""
        renderer = TextRenderer()

        # Inverted layout, subtitle
        y = renderer._calculate_vertical_position(
            text_area_height=400, text_height=30, bbox_top=0, is_main=False, has_sub_text=True, is_inverted=True
        )

        # Should be positioned at 25% of text area (top)
        expected = int(400 * 0.25) - 30 // 2
        assert y == expected

    def test_calculate_vertical_position_centered_no_subtitle(self) -> None:
        """Test vertical position for main text without subtitle."""
        renderer = TextRenderer()

        # Main text without subtitle should be centered
        y = renderer._calculate_vertical_position(
            text_area_height=400, text_height=50, bbox_top=10, is_main=True, has_sub_text=False, is_inverted=False
        )

        # Should be centered
        expected = (400 - 50) // 2 - 10
        assert y == expected

    def test_load_font_fallback(self, mocker: Any) -> None:
        """Test font loading with fallback to default."""
        # Mock font finder to return None (font not found)
        mocker.patch("auto_appscreenshots.font_finder.FontFinder.load_font", return_value=None)

        # Mock ImageFont.load_default
        mock_default_font = MagicMock()
        mocker.patch("PIL.ImageFont.load_default", return_value=mock_default_font)

        renderer = TextRenderer()
        font = renderer._load_font("NonexistentFont", 72)

        assert font == mock_default_font
