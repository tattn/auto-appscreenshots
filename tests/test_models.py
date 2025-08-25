"""Tests for data models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from auto_appscreenshots.models import (
    ImageStyle,
    LocalizedTextContent,
    LocalizedTextStyle,
    Screenshot,
    ScreenshotConfig,
    TextStyle,
    Theme,
)


class TestTextStyle:
    """Test TextStyle model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        style = TextStyle()
        assert style.font_family == "Arial"
        assert style.font_weight == "normal"
        assert style.font_size == 96
        assert style.color == "#FFFFFF"
        assert style.offset == (0, 0)
        assert style.shadow is False
        assert style.shadow_color == "#000000"
        assert style.shadow_offset == (2, 2)
        assert style.shadow_blur == 4

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        style = TextStyle(
            font_family="Helvetica", font_weight="bold", font_size=100, color="#FF0000", offset=(10, 20), shadow=False
        )
        assert style.font_family == "Helvetica"
        assert style.font_weight == "bold"
        assert style.font_size == 100
        assert style.color == "#FF0000"
        assert style.offset == (10, 20)
        assert style.shadow is False


class TestLocalizedTextStyle:
    """Test LocalizedTextStyle model."""

    def test_with_language_values(self) -> None:
        """Test with language-specific values."""
        style = LocalizedTextStyle(
            font_family={"ja": "Hiragino Sans", "en": "Helvetica"}, font_weight={"ja": "bold", "en": "normal"}
        )
        assert style.font_family == {"ja": "Hiragino Sans", "en": "Helvetica"}
        assert style.font_weight == {"ja": "bold", "en": "normal"}

    def test_font_weight_values(self) -> None:
        """Test font weight with direct and language-specific values."""
        # Direct value
        style = LocalizedTextStyle(font_weight="bold")
        assert style.font_weight == "bold"

        # Language-specific values
        style = LocalizedTextStyle(font_weight={"ja": "bold", "en": "medium"})
        assert style.font_weight == {"ja": "bold", "en": "medium"}

    def test_extra_fields_allowed(self) -> None:
        """Test that arbitrary language codes are allowed."""
        style = LocalizedTextStyle(font_size={"custom_lang": 100, "en": 72})
        assert style.font_size == {"custom_lang": 100, "en": 72}


class TestLocalizedTextContent:
    """Test LocalizedTextContent model."""

    def test_main_text_required(self) -> None:
        """Test that main_text is required."""
        with pytest.raises(ValidationError):
            LocalizedTextContent()  # type: ignore[call-arg]

    def test_with_main_text_only(self) -> None:
        """Test with main text only."""
        text = LocalizedTextContent(main_text={"en": "Main", "ja": "メイン"})
        assert text.main_text == {"en": "Main", "ja": "メイン"}
        assert text.sub_text is None

    def test_with_both_texts(self) -> None:
        """Test with both main and sub text."""
        text = LocalizedTextContent(main_text={"en": "Main", "ja": "メイン"}, sub_text={"en": "Sub", "ja": "サブ"})
        assert text.main_text == {"en": "Main", "ja": "メイン"}
        assert text.sub_text == {"en": "Sub", "ja": "サブ"}


class TestScreenshot:
    """Test Screenshot model."""

    def test_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Screenshot()  # type: ignore[call-arg]

    def test_minimal_screenshot(self, sample_image: Path) -> None:
        """Test minimal screenshot configuration."""
        screenshot = Screenshot(input_image=str(sample_image), text=LocalizedTextContent(main_text={"en": "Test"}))
        assert screenshot.input_image == str(sample_image)
        assert "en" in screenshot.text.main_text
        assert screenshot.output_name is None
        assert screenshot.theme is None

    def test_get_text_for_language(self, screenshot: Screenshot) -> None:
        """Test getting text for specific language."""
        main, sub = screenshot.get_text_for_language("en")
        assert main == "English Text"
        assert sub == "English Subtitle"

        main, sub = screenshot.get_text_for_language("ja")
        assert main == "日本語テキスト"
        assert sub == "日本語サブタイトル"

    def test_get_text_for_missing_language(self, screenshot: Screenshot) -> None:
        """Test error when language is not defined."""
        with pytest.raises(ValueError) as exc_info:
            screenshot.get_text_for_language("fr")
        assert "No main_text defined for language 'fr'" in str(exc_info.value)

    def test_localized_input_image(self, sample_image: Path) -> None:
        """Test input_image localization."""
        # Test with static input_image (no placeholders)
        screenshot = Screenshot(input_image=str(sample_image), text=LocalizedTextContent(main_text={"en": "Test"}))
        assert screenshot.format_input_image("en", None) == str(sample_image)
        assert screenshot.format_input_image("ja", None) == str(sample_image)

        # Test with language placeholder
        screenshot = Screenshot(
            input_image="path/to/{lang}.png",
            text=LocalizedTextContent(main_text={"en": "Test"}),
        )
        assert screenshot.format_input_image("en", None) == "path/to/en.png"
        assert screenshot.format_input_image("ja", None) == "path/to/ja.png"
        assert screenshot.format_input_image("fr", None) == "path/to/fr.png"

        # Test with size placeholder
        screenshot = Screenshot(
            input_image="path/to/{size}/image.png",
            text=LocalizedTextContent(main_text={"en": "Test"}),
        )
        assert screenshot.format_input_image("en", (1320, 2868)) == "path/to/1320x2868/image.png"


class TestImageStyle:
    """Test ImageStyle model."""

    def test_default_values(self) -> None:
        """Test default image style values."""
        style = ImageStyle()
        assert style.corner_radius == 0
        assert style.padding == 0

    def test_custom_values(self) -> None:
        """Test custom image style values."""
        style = ImageStyle(corner_radius=20, padding=100)
        assert style.corner_radius == 20
        assert style.padding == 100

    def test_padding_single_value(self) -> None:
        """Test padding with single value."""
        style = ImageStyle(padding=50)
        assert style.get_padding_values() == (50, 50, 50, 50)

    def test_padding_two_values(self) -> None:
        """Test padding with two values (vertical, horizontal)."""
        style = ImageStyle(padding=[10, 20])
        assert style.get_padding_values() == (10, 20, 10, 20)

    def test_padding_three_values(self) -> None:
        """Test padding with three values (top, horizontal, bottom)."""
        style = ImageStyle(padding=[10, 20, 30])
        assert style.get_padding_values() == (10, 20, 30, 20)

    def test_padding_four_values(self) -> None:
        """Test padding with four values (top, right, bottom, left)."""
        style = ImageStyle(padding=[10, 20, 30, 40])
        assert style.get_padding_values() == (10, 20, 30, 40)

    def test_padding_invalid_list(self) -> None:
        """Test padding with invalid list length."""
        style = ImageStyle(padding=[10, 20, 30, 40, 50])  # 5 values
        # Should use first value for all sides
        assert style.get_padding_values() == (10, 10, 10, 10)

        style = ImageStyle(padding=[])  # Empty list
        assert style.get_padding_values() == (0, 0, 0, 0)

    def test_corner_radius_single_value(self) -> None:
        """Test corner radius with single value."""
        style = ImageStyle(corner_radius=20)
        assert style.get_corner_radius_values() == (20, 20, 20, 20)

    def test_corner_radius_two_values(self) -> None:
        """Test corner radius with two values (diagonal pairs)."""
        style = ImageStyle(corner_radius=[10, 20])
        # top-left/bottom-right = 10, top-right/bottom-left = 20
        assert style.get_corner_radius_values() == (10, 20, 10, 20)

    def test_corner_radius_three_values(self) -> None:
        """Test corner radius with three values."""
        style = ImageStyle(corner_radius=[10, 20, 30])
        # top-left = 10, top-right/bottom-left = 20, bottom-right = 30
        assert style.get_corner_radius_values() == (10, 20, 30, 20)

    def test_corner_radius_four_values(self) -> None:
        """Test corner radius with four values."""
        style = ImageStyle(corner_radius=[10, 20, 30, 40])
        # top-left = 10, top-right = 20, bottom-right = 30, bottom-left = 40
        assert style.get_corner_radius_values() == (10, 20, 30, 40)

    def test_corner_radius_invalid_list(self) -> None:
        """Test corner radius with invalid list length."""
        style = ImageStyle(corner_radius=[10, 20, 30, 40, 50])  # 5 values
        # Should use first value for all corners
        assert style.get_corner_radius_values() == (10, 10, 10, 10)

        style = ImageStyle(corner_radius=[])  # Empty list
        assert style.get_corner_radius_values() == (0, 0, 0, 0)


class TestTheme:
    """Test Theme model."""

    def test_empty_theme(self) -> None:
        """Test empty theme."""
        theme = Theme(
            text_area_height=None,
            background_color=None,
            image_style=None,
            main_text_style=None,
            sub_text_style=None,
        )
        assert theme.text_area_height is None
        assert theme.background_color is None
        assert theme.image_style is None
        assert theme.main_text_style is None
        assert theme.sub_text_style is None

    def test_full_theme(self) -> None:
        """Test theme with all components."""
        theme = Theme(
            text_area_height=300,
            background_color="#FFFFFF",
            image_style=ImageStyle(corner_radius=10, padding=20),
            main_text_style=LocalizedTextStyle(font_size={"en": 100}),
            sub_text_style=LocalizedTextStyle(font_size={"en": 50}),
        )
        assert theme.text_area_height == 300
        assert theme.background_color == "#FFFFFF"
        assert theme.image_style is not None
        assert theme.image_style.corner_radius == 10
        assert theme.image_style.padding == 20
        assert theme.main_text_style is not None
        assert theme.main_text_style.font_size == {"en": 100}
        assert theme.sub_text_style is not None
        assert theme.sub_text_style.font_size == {"en": 50}


class TestScreenshotConfig:
    """Test ScreenshotConfig model."""

    def test_minimal_config(self, screenshot: Screenshot) -> None:
        """Test minimal configuration."""
        config = ScreenshotConfig(
            screenshots=[screenshot],
            languages=None,
            default_language="en",
            background_color=None,
        )
        assert len(config.screenshots) == 1
        assert config.languages is None
        assert config.default_theme == "standard"
        assert config.output_sizes == [(1320, 2868), (2064, 2752)]

    def test_full_config(self, screenshot: Screenshot) -> None:
        """Test full configuration."""
        config = ScreenshotConfig(
            languages=["en", "ja", "fr"],
            default_language="en",
            background_color="#FFFFFF",
            output_sizes=[(1080, 1920)],
            theme_styles={
                "defaults": Theme(
                    text_area_height=400,
                    background_color="#F5F5F5",
                    image_style=ImageStyle(padding=0),
                    main_text_style=None,
                    sub_text_style=None,
                )
            },
            default_theme="standard_inverted",
            screenshots=[screenshot],
        )
        assert config.languages == ["en", "ja", "fr"]
        assert config.default_language == "en"
        assert config.background_color == "#FFFFFF"
        assert config.output_sizes == [(1080, 1920)]
        assert "defaults" in config.theme_styles
        assert config.default_theme == "standard_inverted"

    def test_screenshots_required(self) -> None:
        """Test that screenshots field is required."""
        with pytest.raises(ValidationError):
            ScreenshotConfig()  # type: ignore[call-arg]
