"""Tests for style merging utilities."""

from auto_appscreenshots.models import ImageStyle, LocalizedTextStyle, TextStyle, Theme
from auto_appscreenshots.style_merger import StyleMerger


class TestMergeTextStyles:
    """Test merge_text_styles method."""

    def test_merge_with_override(self) -> None:
        """Test merging with override taking precedence."""
        defaults = TextStyle(font_family="Arial", font_size=72, color="#000000")
        override = TextStyle(font_size=100, color="#FFFFFF")

        merged = StyleMerger.merge_text_styles(defaults, override)

        assert merged.font_family == "Arial"  # Kept from defaults
        assert merged.font_size == 100  # Overridden
        assert merged.color == "#FFFFFF"  # Overridden

    def test_merge_preserves_unset_values(self) -> None:
        """Test that unset values in override don't affect defaults."""
        defaults = TextStyle(font_family="Arial", font_size=72, color="#000000", shadow=True, shadow_blur=4)
        override = TextStyle(font_size=100)

        merged = StyleMerger.merge_text_styles(defaults, override)

        assert merged.font_family == "Arial"
        assert merged.font_size == 100
        assert merged.color == "#000000"
        assert merged.shadow is True
        assert merged.shadow_blur == 4


class TestMergeLocalizedTextStyles:
    """Test merge_localized_text_styles method - Critical for color bug fix."""

    def test_merge_language_specific_styles(self) -> None:
        """Test merging language-specific styles."""
        defaults_style = LocalizedTextStyle(
            font_family={"en": "Arial", "ja": "Hiragino Sans"},
            font_size={"en": 72},
            color={"en": "#1A1A1A"},
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )
        override_style = LocalizedTextStyle(
            font_family=None,
            font_size={"en": 100},
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        merged = StyleMerger.merge_localized_text_styles(defaults_style, override_style)

        assert merged is not None
        assert merged.font_family == {"en": "Arial", "ja": "Hiragino Sans"}
        assert merged.font_size == {"en": 100}
        assert merged.color == {"en": "#1A1A1A"}

    def test_merge_language_specific_overrides(self) -> None:
        """Test that merging language styles preserves values correctly."""
        defaults_style = LocalizedTextStyle(
            font_family={"ja": "Hiragino Sans", "en": "Helvetica"},
            font_size={"en": 120},
            color={"en": "#1A1A1A"},
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )
        override_style = LocalizedTextStyle(
            font_family=None,
            font_size=None,
            color={"ja": "#FF0000", "en": "#0000FF"},
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        merged = StyleMerger.merge_localized_text_styles(defaults_style, override_style)

        # Check values are preserved and merged
        assert merged is not None
        assert merged.font_family == {"ja": "Hiragino Sans", "en": "Helvetica"}
        assert merged.color == {"en": "#0000FF", "ja": "#FF0000"}
        assert merged.font_size == {"en": 120}

    def test_merge_with_none_override(self) -> None:
        """Test merging when override is None."""
        defaults_style = LocalizedTextStyle(
            font_family={"en": "Arial"},
            font_size=None,
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        merged = StyleMerger.merge_localized_text_styles(defaults_style, None)

        assert merged == defaults_style

    def test_merge_with_none_defaults(self) -> None:
        """Test merging when defaults is None."""
        override_style = LocalizedTextStyle(
            font_family={"en": "Helvetica"},
            font_size=None,
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        merged = StyleMerger.merge_localized_text_styles(None, override_style)

        assert merged == override_style

    def test_merge_new_language_styles(self) -> None:
        """Test merging adds new language styles."""
        defaults_style = LocalizedTextStyle(
            font_family={"en": "Arial"},
            font_size={"en": 72},
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )
        override_style = LocalizedTextStyle(
            font_family={"fr": "Helvetica"},
            font_size={"fr": 100},
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        merged = StyleMerger.merge_localized_text_styles(defaults_style, override_style)

        # Both language styles should be present
        assert merged is not None
        assert merged.font_family == {"en": "Arial", "fr": "Helvetica"}
        assert merged.font_size == {"en": 72, "fr": 100}


class TestMergeThemes:
    """Test merge_themes method."""

    def test_merge_themes_with_style(self) -> None:
        """Test merging themes with style changes."""
        defaults_theme = Theme(
            text_area_height=400,
            background_color="#F5F5F5",
            image_style=ImageStyle(corner_radius=0, padding=50),
            main_text_style=None,
            sub_text_style=None,
        )
        override_theme = Theme(
            text_area_height=None,
            background_color="#FFFFFF",
            image_style=ImageStyle(corner_radius=10, padding=100),
            main_text_style=None,
            sub_text_style=None,
        )

        merged = StyleMerger.merge_themes(defaults_theme, override_theme)

        assert merged.text_area_height == 400  # From defaults (not overridden)
        assert merged.background_color == "#FFFFFF"  # Overridden
        assert merged.image_style is not None
        assert merged.image_style.corner_radius == 10  # Overridden
        assert merged.image_style.padding == 100  # Overridden

    def test_merge_themes_with_text_styles(self) -> None:
        """Test merging themes with text style changes."""
        defaults_theme = Theme(
            text_area_height=None,
            background_color=None,
            image_style=None,
            main_text_style=LocalizedTextStyle(
                font_family={"en": "Arial"},
                color={"en": "#000000"},
                font_size=None,
                offset=None,
                shadow=None,
                shadow_color=None,
                shadow_offset=None,
                shadow_blur=None,
            ),
            sub_text_style=None,
        )
        override_theme = Theme(
            text_area_height=None,
            background_color=None,
            image_style=None,
            main_text_style=LocalizedTextStyle(
                font_family=None,
                color=None,
                font_size={"en": 100},
                offset=None,
                shadow=None,
                shadow_color=None,
                shadow_offset=None,
                shadow_blur=None,
            ),
            sub_text_style=None,
        )

        merged = StyleMerger.merge_themes(defaults_theme, override_theme)

        assert merged.main_text_style is not None
        assert merged.main_text_style.font_family == {"en": "Arial"}
        assert merged.main_text_style.color == {"en": "#000000"}
        assert merged.main_text_style.font_size == {"en": 100}


class TestMergeImageStyles:
    """Test merge_image_styles method."""

    def test_merge_image_styles(self) -> None:
        """Test merging image style configurations."""
        defaults_style = ImageStyle(corner_radius=0, padding=50)
        override_style = ImageStyle(corner_radius=10, padding=100)

        merged = StyleMerger.merge_image_styles(defaults_style, override_style)

        assert merged.corner_radius == 10  # Overridden
        assert merged.padding == 100  # Overridden


class TestGetStyleForLanguage:
    """Test get_style_for_language method."""

    def test_get_language_specific_style(self) -> None:
        """Test getting language-specific style."""
        localized = LocalizedTextStyle(
            font_family={"ja": "Hiragino Sans", "en": "Helvetica"},
            font_size={"ja": 100, "en": 72},
            color={"ja": "#FF0000", "en": "#0000FF"},
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        style = StyleMerger.get_style_for_language(localized, "ja")

        assert style.font_family == "Hiragino Sans"
        assert style.font_size == 100
        assert style.color == "#FF0000"

    def test_get_style_for_missing_language(self) -> None:
        """Test getting style for language not in dict - falls back to defaults."""
        localized = LocalizedTextStyle(
            font_family={"en": "Helvetica"},
            font_size={"en": 72},
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        style = StyleMerger.get_style_for_language(localized, "fr")

        assert style.font_family == "Arial"  # Falls back to TextStyle default
        assert style.font_size == 96  # Falls back to TextStyle default

    def test_direct_values(self) -> None:
        """Test handling direct values (not dictionaries)."""
        localized = LocalizedTextStyle(
            font_family="Helvetica",  # Direct value
            font_size=100,  # Direct value
            color={"en": "#FF0000"},  # Dictionary
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        # Direct values apply to all languages
        style_ja = StyleMerger.get_style_for_language(localized, "ja")
        assert style_ja.font_family == "Helvetica"
        assert style_ja.font_size == 100
        assert style_ja.color == "#FFFFFF"  # Falls back to TextStyle default

        style_en = StyleMerger.get_style_for_language(localized, "en")
        assert style_en.font_family == "Helvetica"
        assert style_en.font_size == 100
        assert style_en.color == "#FF0000"

    def test_default_language_fallback(self) -> None:
        """Test fallback to default_language when specific language not defined."""
        localized = LocalizedTextStyle(
            font_family={"en": "Helvetica", "ja": "Hiragino Sans"},
            font_size={"en": 100, "ja": 90},
            color=None,
            offset=None,
            shadow=None,
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        # Test with default_language="en"
        style = StyleMerger.get_style_for_language(localized, "fr", default_language="en")
        assert style.font_family == "Helvetica"  # Falls back to default_language (en)
        assert style.font_size == 100  # Falls back to default_language (en)

        # Test with default_language="ja"
        style = StyleMerger.get_style_for_language(localized, "fr", default_language="ja")
        assert style.font_family == "Hiragino Sans"  # Falls back to default_language (ja)
        assert style.font_size == 90  # Falls back to default_language (ja)

    def test_mixed_value_formats(self) -> None:
        """Test mixing direct values and language-specific values."""
        localized = LocalizedTextStyle(
            font_family={"ja": "Hiragino Sans"},
            font_size=120,  # Direct value
            color={"en": "#FF0000", "ja": "#0000FF"},
            offset={"en": (10, 10)},
            shadow=True,  # Direct value
            shadow_color=None,
            shadow_offset=None,
            shadow_blur=None,
        )

        # Test Japanese
        style_ja = StyleMerger.get_style_for_language(localized, "ja")
        assert style_ja.font_family == "Hiragino Sans"
        assert style_ja.font_size == 120
        assert style_ja.color == "#0000FF"
        assert style_ja.offset == (0, 0)  # Uses TextStyle default
        assert style_ja.shadow is True

        # Test English
        style_en = StyleMerger.get_style_for_language(localized, "en")
        assert style_en.font_family == "Arial"  # Uses TextStyle default
        assert style_en.font_size == 120
        assert style_en.color == "#FF0000"
        assert style_en.offset == (10, 10)
        assert style_en.shadow is True

        # Test fallback with default_language
        style_fr = StyleMerger.get_style_for_language(localized, "fr", default_language="en")
        assert style_fr.font_family == "Arial"  # Uses TextStyle default
        assert style_fr.font_size == 120
        assert style_fr.color == "#FF0000"  # Falls back to default_language (en)
        assert style_fr.offset == (10, 10)  # Falls back to default_language (en)
        assert style_fr.shadow is True
