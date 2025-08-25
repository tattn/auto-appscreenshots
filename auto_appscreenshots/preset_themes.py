"""Built-in preset themes for screenshot generation."""

from enum import Enum
from typing import Any


class PresetThemeName(str, Enum):
    """Available preset theme names."""

    STANDARD = "standard"
    STANDARD_INVERTED = "standard_inverted"


class PresetThemes:
    """Manages built-in preset themes."""

    # Define preset theme configurations
    THEMES: dict[str, dict[str, Any]] = {
        PresetThemeName.STANDARD: {
            "text_layout": "standard",
            "description": "Standard layout with main text on top, sub text on bottom",
        },
        PresetThemeName.STANDARD_INVERTED: {
            "text_layout": "inverted",
            "description": "Inverted layout with sub text on top, main text on bottom",
        },
    }

    @classmethod
    def get_theme_config(cls, theme_name: str) -> dict[str, Any]:
        """Get configuration for a preset theme."""
        if theme_name not in cls.THEMES:
            raise ValueError(f"Unknown preset theme: {theme_name}. Available themes: {list(cls.THEMES.keys())}")
        return cls.THEMES[theme_name]

    @classmethod
    def get_text_layout(cls, theme_name: str) -> str:
        """Get text layout mode for a preset theme."""
        config = cls.get_theme_config(theme_name)
        return str(config["text_layout"])

    @classmethod
    def is_valid_theme(cls, theme_name: str) -> bool:
        """Check if a theme name is valid."""
        return theme_name in cls.THEMES

    @classmethod
    def list_themes(cls) -> list[str]:
        """List all available preset theme names."""
        return list(cls.THEMES.keys())
