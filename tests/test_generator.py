"""Tests for screenshot generator."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image, ImageDraw

from auto_appscreenshots.generator import ScreenshotGenerator
from auto_appscreenshots.models import (
    ImageStyle,
    LocalizedTextContent,
    LocalizedTextStyle,
    Screenshot,
    ScreenshotConfig,
    Theme,
)
from auto_appscreenshots.ui_reporter import UIReporter


class TestScreenshotGenerator:
    """Test ScreenshotGenerator class."""

    @pytest.fixture
    def mock_reporter(self) -> Mock:
        """Create mock UI reporter."""
        reporter = MagicMock(spec=UIReporter)
        return reporter

    @pytest.fixture
    def generator_config(self, sample_image: Path) -> ScreenshotConfig:
        """Create a test configuration."""
        screenshot = Screenshot(
            input_image=str(sample_image),
            text=LocalizedTextContent(
                main_text={"en": "English", "ja": "日本語"}, sub_text={"en": "Subtitle", "ja": "サブタイトル"}
            ),
        )
        config = ScreenshotConfig(
            languages=["en", "ja"],
            default_language="en",
            background_color="#FFFFFF",
            output_sizes=[(1320, 2868)],
            screenshots=[screenshot],
            theme_styles={
                "default": Theme(
                    text_area_height=400,
                    background_color="#F5F5F5",
                    image_style=ImageStyle(corner_radius=0, padding=50),
                    main_text_style=LocalizedTextStyle(font_family="Arial", font_size=72),
                    sub_text_style=LocalizedTextStyle(font_family="Arial", font_size=48),
                )
            },
        )
        return config

    def test_init(self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock) -> None:
        """Test generator initialization."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        assert generator.config == generator_config
        assert generator.file_manager.base_output_dir == temp_dir
        assert generator.ui_reporter == mock_reporter

    def test_generate_all_languages(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, mock_font: Mock
    ) -> None:
        """Test generating screenshots for all languages."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        # Mock image processing
        with patch.object(generator.image_processor, "load_image") as mock_load:
            # Create a real image instead of mock for proper behavior
            real_image = Image.new("RGBA", (1000, 2000), color=(255, 255, 255, 255))
            mock_load.return_value = real_image

            generated_files = generator.generate_all()

        # Should generate 2 languages × 1 resolution × 1 screenshot = 2 files
        assert len(generated_files) == 2

        # Check that reporter was called for each language
        assert mock_reporter.report_language_start.call_count == 2
        mock_reporter.report_language_start.assert_any_call("en")
        mock_reporter.report_language_start.assert_any_call("ja")

    def test_generate_specific_language(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, mock_font: Mock
    ) -> None:
        """Test generating screenshots for specific language."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        with patch.object(generator.image_processor, "load_image") as mock_load:
            real_image = Image.new("RGBA", (1000, 2000), color=(255, 255, 255, 255))
            mock_load.return_value = real_image

            generated_files = generator.generate_all(language="ja")

        # Should only generate for Japanese
        assert len(generated_files) == 1
        mock_reporter.report_language_start.assert_called_once_with("ja")

    def test_generate_screenshot_missing_input(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock
    ) -> None:
        """Test error handling for missing input file."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        # Set invalid input path
        generator_config.screenshots[0].input_image = "nonexistent.png"

        with pytest.raises(FileNotFoundError) as exc_info:
            generator.generate_screenshot(generator_config.screenshots[0], index=1, language="en")
        assert "Input image not found" in str(exc_info.value)

    def test_generate_screenshot_missing_language(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, sample_image: Path
    ) -> None:
        """Test error handling for missing language text."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        with pytest.raises(ValueError) as exc_info:
            generator.generate_screenshot(
                generator_config.screenshots[0],
                index=1,
                language="fr",  # Not defined
            )
        assert "No main_text defined for language 'fr'" in str(exc_info.value)

    def test_generate_single_resolution(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, mock_font: Mock
    ) -> None:
        """Test generating a single resolution screenshot."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        with patch.object(generator.image_processor, "load_image") as mock_load:
            real_image = Image.new("RGBA", (1000, 2000), color=(255, 255, 255, 255))
            mock_load.return_value = real_image

            paths = generator.generate_screenshot(generator_config.screenshots[0], index=1, language="en")

        assert len(paths) == 1  # One resolution
        assert paths[0].parent.parent.name == "en"
        assert "1320x2868" in str(paths[0])

    def test_render_texts(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, mock_font: Mock
    ) -> None:
        """Test text rendering on canvas."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        mock_draw = MagicMock(spec=ImageDraw.ImageDraw)
        screenshot = generator_config.screenshots[0]

        # Mock text renderer
        with patch.object(generator.text_renderer, "render_text") as mock_render:
            # Test rendering both main and sub text
            generator._render_texts(
                draw=mock_draw,
                screenshot=screenshot,
                main_text="Main",
                sub_text="Sub",
                canvas_width=1320,
                text_area_height=400,
                language="en",
            )

            # Should render both texts
            assert mock_render.call_count == 2

    def test_render_texts_no_subtitle(
        self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock, mock_font: Mock
    ) -> None:
        """Test text rendering without subtitle."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        mock_draw = MagicMock(spec=ImageDraw.ImageDraw)
        screenshot = generator_config.screenshots[0]

        # Mock text renderer
        with patch.object(generator.text_renderer, "render_text") as mock_render:
            generator._render_texts(
                draw=mock_draw,
                screenshot=screenshot,
                main_text="Main",
                sub_text=None,  # No subtitle
                canvas_width=1320,
                text_area_height=400,
                language="en",
            )

            # Should only render main text
            assert mock_render.call_count == 1

    def test_error_reporting(self, generator_config: ScreenshotConfig, temp_dir: Path, mock_reporter: Mock) -> None:
        """Test that errors are properly reported."""
        generator = ScreenshotGenerator(config=generator_config, output_dir=temp_dir, ui_reporter=mock_reporter)

        # Make screenshot fail
        generator_config.screenshots[0].input_image = "nonexistent.png"

        with pytest.raises(Exception):
            generator.generate_all()

        # Should report error
        mock_reporter.report_screenshot_error.assert_called()

    def test_multiple_resolutions(
        self, temp_dir: Path, mock_reporter: Mock, sample_image: Path, mock_font: Mock
    ) -> None:
        """Test generating multiple resolutions."""
        screenshot = Screenshot(input_image=str(sample_image), text=LocalizedTextContent(main_text={"en": "Test"}))
        config = ScreenshotConfig(
            languages=["en"],
            output_sizes=[(1320, 2868), (2064, 2752)],
            screenshots=[screenshot],
            default_language="en",
            background_color="#FFFFFF",
        )

        generator = ScreenshotGenerator(config=config, output_dir=temp_dir, ui_reporter=mock_reporter)

        with patch.object(generator.image_processor, "load_image") as mock_load:
            real_image = Image.new("RGBA", (1000, 2000), color=(255, 255, 255, 255))
            mock_load.return_value = real_image

            paths = generator.generate_screenshot(screenshot, index=1, language="en")

        assert len(paths) == 2  # Two resolutions
        assert any("1320x2868" in str(p) for p in paths)
        assert any("2064x2752" in str(p) for p in paths)
