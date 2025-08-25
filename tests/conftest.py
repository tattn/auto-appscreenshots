"""Shared pytest fixtures for tests."""

import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from auto_appscreenshots.models import (
    ImageStyle,
    LocalizedTextContent,
    LocalizedTextStyle,
    Screenshot,
    ScreenshotConfig,
    TextStyle,
    Theme,
)


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image(temp_dir: Path) -> Path:
    """Create a sample test image."""
    image_path = temp_dir / "test_image.png"
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
    img.save(image_path)
    return image_path


@pytest.fixture
def text_style() -> TextStyle:
    """Create a sample TextStyle."""
    return TextStyle(
        font_family="Arial",
        font_size=72,
        color="#FFFFFF",
        offset=(0, 0),
        shadow=True,
        shadow_color="#000000",
        shadow_offset=(2, 2),
        shadow_blur=4,
    )


@pytest.fixture
def localized_text_style() -> LocalizedTextStyle:
    """Create a sample LocalizedTextStyle."""
    return LocalizedTextStyle(
        font_family={"default": "Arial"},
        font_size={"default": 72},
        color={"default": "#FFFFFF"},
        offset=None,
        shadow=None,
        shadow_color=None,
        shadow_offset=None,
        shadow_blur=None,
    )


@pytest.fixture
def localized_text_content() -> LocalizedTextContent:
    """Create a sample LocalizedTextContent."""
    return LocalizedTextContent(
        main_text={"en": "Test Main Text", "ja": "テストメインテキスト"},
        sub_text={"en": "Test Sub Text", "ja": "テストサブテキスト"},
    )


@pytest.fixture
def screenshot(sample_image: Path) -> Screenshot:
    """Create a sample Screenshot."""
    return Screenshot(
        input_image=str(sample_image),
        text=LocalizedTextContent(
            main_text={"en": "English Text", "ja": "日本語テキスト"},
            sub_text={"en": "English Subtitle", "ja": "日本語サブタイトル"},
        ),
        output_name="test_output_{lang}",
        theme="standard",
    )


@pytest.fixture
def image_style() -> ImageStyle:
    """Create a sample ImageStyle."""
    return ImageStyle(corner_radius=0, padding=50)


@pytest.fixture
def theme() -> Theme:
    """Create a sample Theme."""
    return Theme(
        text_area_height=400,
        background_color="#F5F5F5",
        image_style=ImageStyle(corner_radius=0, padding=50),
        main_text_style=LocalizedTextStyle(
            font_family="Arial",
            font_size=72,
            color="#000000",
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        ),
        sub_text_style=LocalizedTextStyle(
            font_family="Arial",
            font_size=48,
            color="#666666",
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        ),
    )


@pytest.fixture
def screenshot_config(screenshot: Screenshot) -> ScreenshotConfig:
    """Create a sample ScreenshotConfig."""
    return ScreenshotConfig(
        languages=["en", "ja"],
        output_sizes=[(1320, 2868), (2064, 2752)],
        theme_styles={
            "defaults": Theme(
                text_area_height=None,
                background_color=None,
                image_style=None,
                main_text_style=LocalizedTextStyle(
                    font_family="Arial",
                    font_size=72,
                    color="#1A1A1A",
                    offset=None,
                    shadow=None,
                    shadow_color=None,
                    shadow_offset=None,
                    shadow_blur=None,
                ),
                sub_text_style=None,
            )
        },
        default_theme="standard",
        screenshots=[screenshot],
        default_language="en",
        background_color=None,
    )


@pytest.fixture
def mock_font(mocker: Any) -> Any:
    """Mock font loading to avoid system font dependencies."""
    from PIL import ImageFont

    # Create a mock Image for mask
    mock_mask = Image.new("L", (100, 50), 255)

    mock_font = mocker.MagicMock(spec=ImageFont.FreeTypeFont)
    # Mock getmask2 to return a real image mask with its core
    mock_font.getmask2.return_value = (mock_mask.im, (0, 0))
    # Mock getmask as fallback - return the ImagingCore
    mock_font.getmask.return_value = mock_mask.im
    # Mock getbbox to return proper values for text measurement
    mock_font.getbbox.return_value = (0, 0, 100, 50)
    mocker.patch("auto_appscreenshots.font_finder.FontFinder.load_font", return_value=mock_font)
    mocker.patch("auto_appscreenshots.text_renderer.FontFinder.load_font", return_value=mock_font)
    return mock_font
