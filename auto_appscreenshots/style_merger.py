"""Style merging utilities following Single Responsibility Principle."""

from typing import Any

from .models import ImageStyle, LocalizedTextStyle, TextStyle, Theme


class StyleMerger:
    """Handles merging of text styles and theme configurations."""

    @staticmethod
    def merge_text_styles(defaults: TextStyle, override: TextStyle) -> TextStyle:
        """Merge two text styles with override taking precedence."""
        merged = defaults.model_copy()
        for field_name, field_value in override.model_dump(exclude_unset=True).items():
            setattr(merged, field_name, field_value)
        return merged

    @staticmethod
    def merge_localized_text_styles(
        defaults_style: LocalizedTextStyle | None, override_style: LocalizedTextStyle | None
    ) -> LocalizedTextStyle | None:
        """Merge two localized text styles with override taking precedence."""
        if not override_style:
            return defaults_style
        if not defaults_style:
            return override_style

        merged = defaults_style.model_copy()

        # Merge each property
        for field_name in LocalizedTextStyle.model_fields:
            defaults_value = getattr(defaults_style, field_name, None)
            override_value = getattr(override_style, field_name, None)

            if override_value is not None:
                if isinstance(defaults_value, dict) and isinstance(override_value, dict):
                    # Both are dicts, merge them
                    merged_dict: dict[str, Any] = {}
                    merged_dict.update(defaults_value)  # type: ignore[arg-type, unused-ignore]
                    merged_dict.update(override_value)  # type: ignore[arg-type, unused-ignore]
                    setattr(merged, field_name, merged_dict)
                else:
                    # Override value takes precedence
                    setattr(merged, field_name, override_value)

        return merged

    @staticmethod
    def merge_themes(defaults_theme: Theme, override_theme: Theme) -> Theme:
        """Merge two themes with override taking precedence."""
        merged = defaults_theme.model_copy()

        # Merge text_area_height
        if override_theme.text_area_height is not None:
            merged.text_area_height = override_theme.text_area_height

        # Merge background_color
        if override_theme.background_color is not None:
            merged.background_color = override_theme.background_color

        # Merge image_style
        if override_theme.image_style:
            merged.image_style = (
                StyleMerger.merge_image_styles(merged.image_style, override_theme.image_style)
                if merged.image_style
                else override_theme.image_style
            )

        # Merge text styles
        if override_theme.main_text_style:
            merged.main_text_style = StyleMerger.merge_localized_text_styles(
                merged.main_text_style, override_theme.main_text_style
            )

        if override_theme.sub_text_style:
            merged.sub_text_style = StyleMerger.merge_localized_text_styles(
                merged.sub_text_style, override_theme.sub_text_style
            )

        return merged

    @staticmethod
    def merge_image_styles(defaults_style: ImageStyle, override_style: ImageStyle) -> ImageStyle:
        """Merge two image style configs with override taking precedence."""
        defaults_dict = defaults_style.model_dump()
        override_dict = override_style.model_dump(exclude_unset=True)
        defaults_dict.update(override_dict)
        return ImageStyle(**defaults_dict)

    @staticmethod
    def get_style_for_language(
        localized_style: LocalizedTextStyle, language: str | None = None, default_language: str | None = None
    ) -> TextStyle:
        """Get text style for a specific language from localized style.

        Priority order:
        1. Language-specific value
        2. Default language value (if different from requested language)
        3. Direct value (not in dictionary)
        """
        style_dict: dict[str, Any] = {}

        # Build style dictionary by extracting values for the specified language
        for field_name in [
            "font_family",
            "font_style",
            "font_weight",
            "font_size",
            "color",
            "offset",
            "shadow",
            "shadow_color",
            "shadow_offset",
            "shadow_blur",
        ]:
            value = getattr(localized_style, field_name, None)

            if value is not None:
                if isinstance(value, dict):
                    # Try to get language-specific value
                    if language and language in value:
                        style_dict[field_name] = value[language]
                    elif default_language and default_language in value:
                        # Fallback to default language
                        style_dict[field_name] = value[default_language]
                else:
                    # Direct value (applies to all languages)
                    style_dict[field_name] = value

        # Use defaults from TextStyle for any missing values
        return TextStyle(**style_dict)
