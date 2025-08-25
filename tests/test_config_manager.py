"""Tests for configuration management."""

import pytest

from auto_appscreenshots.config_manager import ConfigManager
from auto_appscreenshots.models import (
    ImageStyle,
    LocalizedTextContent,
    LocalizedTextStyle,
    Screenshot,
    ScreenshotConfig,
    Theme,
)
from auto_appscreenshots.preset_themes import PresetThemes


class TestConfigManager:
    """Test ConfigManager class."""

    def test_get_languages_from_config(self) -> None:
        """Test getting languages from config."""
        config = ScreenshotConfig(
            languages=["en", "ja"],
            screenshots=[],
            default_language="en",
            background_color=None,
            default_theme="standard",
        )
        manager = ConfigManager(config, PresetThemes())

        languages = manager.get_languages_to_generate()
        assert languages == ["en", "ja"]

    def test_get_languages_with_specific_language(self) -> None:
        """Test getting specific language."""
        config = ScreenshotConfig(
            languages=["en", "ja", "fr"],
            screenshots=[],
            default_language="en",
            background_color=None,
            default_theme="standard",
        )
        manager = ConfigManager(config, PresetThemes())

        languages = manager.get_languages_to_generate(specific_language="fr")
        assert languages == ["fr"]

    def test_get_languages_from_screenshots(self, screenshot: Screenshot) -> None:
        """Test extracting languages from screenshots when not specified."""
        config = ScreenshotConfig(
            screenshots=[screenshot],
            languages=None,
            default_language="en",
            background_color=None,
            default_theme="standard",
        )
        manager = ConfigManager(config, PresetThemes())

        languages = manager.get_languages_to_generate()
        assert set(languages) == {"en", "ja"}

    def test_get_languages_no_languages_defined(self) -> None:
        """Test error when no languages defined."""
        config = ScreenshotConfig(
            screenshots=[], languages=None, default_language="en", background_color=None, default_theme="standard"
        )
        manager = ConfigManager(config, PresetThemes())

        with pytest.raises(ValueError) as exc_info:
            manager.get_languages_to_generate()
        assert "No languages defined" in str(exc_info.value)

    def test_get_theme_style_with_standard(self) -> None:
        """Test getting theme style with standard theme."""
        config = ScreenshotConfig(
            languages=None,
            default_language="en",
            background_color=None,
            theme_styles={
                "standard": Theme(
                    style=None,
                    main_text_style=LocalizedTextStyle(
                        font_family={"en": "Arial"},
                        font_size=None,
                        color={"en": "#1A1A1A"},
                        offset={"en": (0, 50)},
                        shadow=None,
                        shadow_color=None,
                        shadow_offset=None,
                        shadow_blur=None,
                    ),
                    sub_text_style=None,
                ),
            },
            default_theme="standard",
            screenshots=[],
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme="standard",
        )
        manager = ConfigManager(config, PresetThemes())

        theme_style = manager.get_theme_style(screenshot)

        # Should get standard theme settings
        if theme_style.main_text_style:
            assert theme_style.main_text_style.font_family == {"en": "Arial"}
            assert theme_style.main_text_style.color == {"en": "#1A1A1A"}
            assert theme_style.main_text_style.offset == {"en": (0, 50)}

    def test_get_theme_style_invalid_theme(self) -> None:
        """Test error with invalid theme name."""
        config = ScreenshotConfig(
            theme_styles={},
            default_theme="standard",
            screenshots=[],
            languages=None,
            default_language="en",
            background_color=None,
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme="invalid_theme",
        )
        manager = ConfigManager(config, PresetThemes())

        with pytest.raises(ValueError) as exc_info:
            manager.get_theme_style(screenshot)
        assert "Invalid preset theme" in str(exc_info.value)

    def test_get_main_text_style(self) -> None:
        """Test getting main text style with merging."""
        config = ScreenshotConfig(
            languages=None,
            default_language="en",
            background_color=None,
            theme_styles={
                "standard": Theme(
                    style=None,
                    main_text_style=LocalizedTextStyle(
                        font_family={"en": "Arial"},
                        color={"en": "#1A1A1A"},
                        font_size={"en": 120},
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
            screenshots=[],
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme=None,
            main_text_style=LocalizedTextStyle(
                font_family=None,
                font_size={"en": 100},
                color=None,
                offset=None,
                shadow=None,
                shadow_color=None,
                shadow_offset=None,
                shadow_blur=None,
            ),
        )
        manager = ConfigManager(config, PresetThemes())

        style = manager.get_main_text_style(screenshot, "en")

        assert style.font_family == "Arial"  # From theme
        assert style.color == "#1A1A1A"  # From theme
        assert style.font_size == 100  # From screenshot override

    def test_get_sub_text_style(self) -> None:
        """Test getting subtitle text style."""
        config = ScreenshotConfig(
            languages=None,
            default_language="en",
            background_color=None,
            theme_styles={
                "standard": Theme(
                    style=None,
                    main_text_style=None,
                    sub_text_style=LocalizedTextStyle(
                        font_family={"en": "Arial"},
                        font_size={"en": 48},
                        color=None,
                        offset=None,
                        shadow=None,
                        shadow_color=None,
                        shadow_offset=None,
                        shadow_blur=None,
                    ),
                )
            },
            default_theme="standard",
            screenshots=[],
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text={"en": "Sub"}),
            output_name=None,
            theme=None,
            sub_text_style=LocalizedTextStyle(
                font_family=None,
                font_size=None,
                color={"en": "#FF0000"},
                offset=None,
                shadow=None,
                shadow_color=None,
                shadow_offset=None,
                shadow_blur=None,
            ),
        )
        manager = ConfigManager(config, PresetThemes())

        style = manager.get_sub_text_style(screenshot, "en")

        assert style.font_family == "Arial"  # From theme
        assert style.font_size == 48  # From theme
        assert style.color == "#FF0000"  # From screenshot override

    def test_get_theme_values(self) -> None:
        """Test getting theme configuration values."""
        config = ScreenshotConfig(
            languages=None,
            default_language="en",
            background_color=None,
            theme_styles={
                "standard": Theme(
                    text_area_height=500,
                    background_color="#FFFFFF",
                    image_style=ImageStyle(corner_radius=10, padding=100),
                    main_text_style=None,
                    sub_text_style=None,
                )
            },
            default_theme="standard",
            screenshots=[],
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme=None,
        )
        manager = ConfigManager(config, PresetThemes())

        text_area_height = manager.get_text_area_height(screenshot)
        background_color = manager.get_background_color(screenshot)
        image_style = manager.get_image_style(screenshot)

        assert text_area_height == 500
        assert background_color == "#FFFFFF"
        assert image_style.corner_radius == 10
        assert image_style.padding == 100

    def test_get_theme_values_default(self) -> None:
        """Test getting default theme values when not defined."""
        config = ScreenshotConfig(
            theme_styles={},
            default_theme="standard",
            screenshots=[],
            languages=None,
            default_language="en",
            background_color=None,
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme=None,
        )
        manager = ConfigManager(config, PresetThemes())

        text_area_height = manager.get_text_area_height(screenshot)
        background_color = manager.get_background_color(screenshot)
        image_style = manager.get_image_style(screenshot)

        assert text_area_height == 400  # Default
        assert background_color == "#F5F5F5"  # Default
        assert image_style.corner_radius == 0  # Default
        assert image_style.padding == 0  # Default

    def test_get_text_layout(self) -> None:
        """Test getting text layout from preset theme."""
        config = ScreenshotConfig(
            theme_styles={},
            default_theme="standard",
            screenshots=[],
            languages=None,
            default_language="en",
            background_color=None,
        )
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme="standard_inverted",
        )
        manager = ConfigManager(config, PresetThemes())

        layout = manager.get_text_layout(screenshot)

        assert layout == "inverted"
