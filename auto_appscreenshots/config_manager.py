"""Configuration management following Single Responsibility and Dependency Inversion principles."""

from .models import ImageStyle, Screenshot, ScreenshotConfig, TextStyle, Theme
from .preset_themes import PresetThemes
from .style_merger import StyleMerger


class ConfigManager:
    """Manages screenshot configuration and style resolution."""

    def __init__(self, config: ScreenshotConfig, theme_validator: PresetThemes | None = None):
        """Initialize config manager with configuration and theme validator."""
        self.config = config
        self.theme_validator = theme_validator or PresetThemes()
        self.style_merger = StyleMerger()

    def get_languages_to_generate(self, specific_language: str | None = None) -> list[str]:
        """Get list of languages to generate."""
        if specific_language:
            return [specific_language]
        elif self.config.languages:
            return self.config.languages
        else:
            # Extract all unique languages from screenshots
            all_languages: set[str] = set()
            for screenshot in self.config.screenshots:
                all_languages.update(screenshot.text.main_text.keys())
            if all_languages:
                return sorted(all_languages)
            else:
                raise ValueError("No languages defined in configuration")

    def get_theme_style(self, screenshot: Screenshot) -> Theme:
        """Get theme style configuration for a screenshot."""
        theme_name = screenshot.theme or self.config.default_theme

        # Validate preset theme
        if not PresetThemes.is_valid_theme(theme_name):
            raise ValueError(f"Invalid preset theme: {theme_name}. Available: {PresetThemes.list_themes()}")

        # Get theme-specific style if exists
        theme_style = self.config.theme_styles.get(theme_name)

        # Return theme style or empty theme
        return theme_style or Theme(
            text_area_height=None,
            background_color=None,
            image_style=None,
            main_text_style=None,
            sub_text_style=None,
        )

    def _get_text_style(self, screenshot: Screenshot, language: str, style_type: str) -> TextStyle:
        """Generic method to get text style for a screenshot."""
        theme_style = self.get_theme_style(screenshot)

        # Get theme style and screenshot style based on type
        theme_localized_style = getattr(theme_style, f"{style_type}_text_style", None)
        screenshot_localized_style = getattr(screenshot, f"{style_type}_text_style", None)

        # Get default language for fallback
        default_language = self.config.default_language

        # Get theme style if defined
        theme_text_style = (
            self.style_merger.get_style_for_language(theme_localized_style, language, default_language)
            if theme_localized_style
            else TextStyle()
        )

        # If screenshot has specific style, merge it with theme style
        if screenshot_localized_style:
            screenshot_style = self.style_merger.get_style_for_language(
                screenshot_localized_style, language, default_language
            )
            return self.style_merger.merge_text_styles(theme_text_style, screenshot_style)

        return theme_text_style

    def get_main_text_style(self, screenshot: Screenshot, language: str) -> TextStyle:
        """Get main text style for a screenshot."""
        return self._get_text_style(screenshot, language, "main")

    def get_sub_text_style(self, screenshot: Screenshot, language: str) -> TextStyle:
        """Get subtitle text style for a screenshot."""
        return self._get_text_style(screenshot, language, "sub")

    def get_text_area_height(self, screenshot: Screenshot) -> int:
        """Get text area height for a screenshot."""
        theme_style = self.get_theme_style(screenshot)
        return theme_style.text_area_height or 400

    def get_background_color(self, screenshot: Screenshot) -> str:
        """Get background color for a screenshot."""
        theme_style = self.get_theme_style(screenshot)
        return theme_style.background_color or "#F5F5F5"

    def get_image_style(self, screenshot: Screenshot) -> ImageStyle:
        """Get image style for a screenshot."""
        theme_style = self.get_theme_style(screenshot)
        return theme_style.image_style or ImageStyle(corner_radius=0, padding=0)

    def get_text_layout(self, screenshot: Screenshot) -> str:
        """Get text layout mode for a screenshot (determined by preset theme)."""
        theme_name = screenshot.theme or self.config.default_theme
        return PresetThemes.get_text_layout(theme_name)
