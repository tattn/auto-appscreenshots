"""Tests for preset themes."""

import pytest

from auto_appscreenshots.preset_themes import PresetThemeName, PresetThemes


class TestPresetThemes:
    """Test PresetThemes class."""

    def test_get_theme_config_standard(self) -> None:
        """Test getting standard theme configuration."""
        config = PresetThemes.get_theme_config(PresetThemeName.STANDARD)

        assert config["text_layout"] == "standard"
        assert "description" in config

    def test_get_theme_config_standard_inverted(self) -> None:
        """Test getting standard_inverted theme configuration."""
        config = PresetThemes.get_theme_config(PresetThemeName.STANDARD_INVERTED)

        assert config["text_layout"] == "inverted"
        assert "description" in config

    def test_get_theme_config_invalid(self) -> None:
        """Test error with invalid theme name."""
        with pytest.raises(ValueError) as exc_info:
            PresetThemes.get_theme_config("invalid_theme")
        assert "Unknown preset theme" in str(exc_info.value)

    def test_get_text_layout(self) -> None:
        """Test getting text layout for themes."""
        assert PresetThemes.get_text_layout("standard") == "standard"
        assert PresetThemes.get_text_layout("standard_inverted") == "inverted"

    def test_is_valid_theme(self) -> None:
        """Test theme validation."""
        assert PresetThemes.is_valid_theme("standard") is True
        assert PresetThemes.is_valid_theme("standard_inverted") is True
        assert PresetThemes.is_valid_theme("invalid") is False

    def test_list_themes(self) -> None:
        """Test listing available themes."""
        themes = PresetThemes.list_themes()

        assert "standard" in themes
        assert "standard_inverted" in themes
        assert len(themes) == 2
