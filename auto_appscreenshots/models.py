"""Data models for screenshot configuration."""

from typing import Any

from pydantic import BaseModel, Field, model_validator


class TextStyleProperty(BaseModel):
    """Language-specific text style property.

    Each property can have language-specific values.
    Example:
        font_family:
            ja: "Hiragino Sans"
            en: "Helvetica"
    """

    # Allow additional fields for language-specific values
    model_config = {"extra": "allow"}


class LocalizedTextStyle(BaseModel):
    """Text style with optional language-specific properties.

    Each property can be:
    - A direct value (applied to all languages): font_size: 120
    - A dictionary with language codes: font_size: {ja: 100, en: 120}
    """

    font_family: str | dict[str, str] | None = Field(default=None, description="Font family name")
    font_style: str | dict[str, str] | None = Field(default=None, description="Font style (normal, italic, oblique)")
    font_weight: str | dict[str, str] | None = Field(
        default=None, description="Font weight (e.g., light, normal, bold)"
    )
    font_size: int | dict[str, int] | None = Field(default=None, description="Font size in points")
    color: str | dict[str, str] | None = Field(default=None, description="Text color (hex color code)")
    offset: tuple[int, int] | dict[str, tuple[int, int]] | None = Field(
        default=None, description="Text offset position (x, y) in pixels"
    )
    shadow: bool | dict[str, bool] | None = Field(default=None, description="Enable/disable text shadow")
    shadow_color: str | dict[str, str] | None = Field(default=None, description="Shadow color (hex color code)")
    shadow_offset: tuple[int, int] | dict[str, tuple[int, int]] | None = Field(
        default=None, description="Shadow offset position (x, y) in pixels"
    )
    shadow_blur: int | dict[str, int] | None = Field(default=None, description="Shadow blur radius in pixels")

    @model_validator(mode="before")
    @classmethod
    def validate_properties(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate property structure."""
        # Check if this is old format (has language codes like 'ja', 'en' at top level)
        known_properties = {
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
        }
        top_level_keys = set(values.keys())

        # If we have language codes at top level (not known properties)
        if top_level_keys - known_properties:
            # This is old format, do NOT convert
            # Return as is and handle in get_style_for_language
            pass

        return values


class TextStyle(BaseModel):
    """Text style configuration."""

    font_family: str = Field(default="Arial", description="Font family name")
    font_style: str = Field(default="normal", description="Font style (normal, italic, oblique)")
    font_weight: str = Field(default="normal", description="Font weight (e.g., light, normal, bold)")
    font_size: int = Field(default=96, description="Font size in points")
    color: str = Field(default="#FFFFFF", description="Text color (hex color code)")
    offset: tuple[int, int] = Field(default=(0, 0), description="Text offset position (x, y) in pixels")
    shadow: bool = Field(default=False, description="Enable/disable text shadow")
    shadow_color: str = Field(default="#000000", description="Shadow color (hex color code)")
    shadow_offset: tuple[int, int] = Field(default=(2, 2), description="Shadow offset position (x, y) in pixels")
    shadow_blur: int = Field(default=4, description="Shadow blur radius in pixels")


class LocalizedTextContent(BaseModel):
    """Text content with language-specific values.

    Each text field can be a dictionary with language codes as keys.
    Example:
        main_text:
            ja: "日本語テキスト"
            en: "English Text"
    """

    main_text: dict[str, str] = Field(..., description="Main text by language")
    sub_text: dict[str, str] | None = Field(default=None, description="Optional subtitle text by language")


class Screenshot(BaseModel):
    """Individual screenshot configuration."""

    input_image: str = Field(
        ...,
        description=(
            "Path template to input screenshot image.\n"
            "Supports placeholders:\n"
            "- {lang}: Language code (e.g., 'ja', 'en')\n"
            "- {size}: Size as 'widthxheight' (e.g., '1320x2868')\n"
            "- {width}: Width in pixels\n"
            "- {height}: Height in pixels\n"
            "Example: 'screenshots/{lang}/{size}/home.png'"
        ),
    )
    text: LocalizedTextContent = Field(..., description="Text content with language-specific values")
    output_name: str | None = Field(
        default=None, description="Output filename without extension. Placeholders: {lang}, {width}, {height}"
    )
    theme: str | None = Field(default=None, description="Theme name to use for this screenshot")
    main_text_style: LocalizedTextStyle | None = None
    sub_text_style: LocalizedTextStyle | None = None

    def get_text_for_language(self, language: str) -> tuple[str, str | None]:
        """Get main and sub text for the specified language."""
        main_text = None
        sub_text = None

        # Get main text
        if language in self.text.main_text:
            main_text = self.text.main_text[language]
        else:
            raise ValueError(f"No main_text defined for language '{language}' in screenshot")

        # Get optional sub text
        if self.text.sub_text and language in self.text.sub_text:
            sub_text = self.text.sub_text[language]

        return main_text, sub_text

    def format_input_image(
        self,
        language: str,
        size: tuple[int, int] | None = None,
    ) -> str:
        """Format input image path with placeholders.

        Args:
            language: Target language code
            size: Target size as (width, height) tuple

        Returns:
            Formatted path to the input image
        """
        # Build replacement dictionary
        replacements = {
            "lang": language,
        }

        if size:
            replacements["size"] = f"{size[0]}x{size[1]}"
            replacements["width"] = str(size[0])
            replacements["height"] = str(size[1])

        # Replace placeholders
        path = self.input_image
        for key, value in replacements.items():
            path = path.replace(f"{{{key}}}", value)

        return path

    def get_input_image(
        self,
        language: str,
        size: tuple[int, int] | None = None,
        fallback_language: str | None = None,
    ) -> str:
        """Get input image path for specified language and size.

        Deprecated: Use format_input_image() instead.

        Args:
            language: Target language code
            size: Target size as (width, height) tuple
            fallback_language: Fallback language to use if target not found

        Returns:
            Path to the input image
        """
        return self.format_input_image(language, size)


class ImageStyle(BaseModel):
    """Image style configuration."""

    corner_radius: int | list[int] = Field(
        default=0,
        description=(
            "Corner radius for screenshot image. Can be:\n"
            "- Single value: Applied to all corners\n"
            "- 2 values: [top-left/bottom-right, top-right/bottom-left] (diagonal pairs)\n"
            "- 3 values: [top-left, top-right/bottom-left, bottom-right]\n"
            "- 4 values: [top-left, top-right, bottom-right, bottom-left] (clockwise from top-left)"
        ),
    )
    padding: int | list[int] = Field(
        default=0,
        description=(
            "Padding around screenshot. Can be:\n"
            "- Single value: Applied to all sides\n"
            "- 2 values [vertical, horizontal]: Applied to [top/bottom, left/right]\n"
            "- 3 values [top, horizontal, bottom]: Applied to [top, left/right, bottom]\n"
            "- 4 values [top, right, bottom, left]: Applied clockwise from top (CSS style)"
        ),
    )

    def get_padding_values(self) -> tuple[int, int, int, int]:
        """Get padding values as (top, right, bottom, left) tuple.

        Returns:
            Tuple of (top, right, bottom, left) padding values
        """
        if isinstance(self.padding, int):
            # Single value: all sides
            return (self.padding, self.padding, self.padding, self.padding)
        else:
            # Must be a list
            if len(self.padding) == 2:
                # [vertical, horizontal]
                return (self.padding[0], self.padding[1], self.padding[0], self.padding[1])
            elif len(self.padding) == 3:
                # [top, horizontal, bottom]
                return (self.padding[0], self.padding[1], self.padding[2], self.padding[1])
            elif len(self.padding) == 4:
                # [top, right, bottom, left]
                return (self.padding[0], self.padding[1], self.padding[2], self.padding[3])
            else:
                # Invalid length, use first value for all sides or 0
                value = self.padding[0] if self.padding else 0
                return (value, value, value, value)

    def get_corner_radius_values(self) -> tuple[int, int, int, int]:
        """Get corner radius values as (top-left, top-right, bottom-right, bottom-left) tuple.

        Returns:
            Tuple of (top-left, top-right, bottom-right, bottom-left) radius values
        """
        if isinstance(self.corner_radius, int):
            # Single value: all corners
            return (self.corner_radius, self.corner_radius, self.corner_radius, self.corner_radius)
        else:
            # Must be a list
            if len(self.corner_radius) == 2:
                # [top-left/bottom-right, top-right/bottom-left] (diagonal pairs)
                return (self.corner_radius[0], self.corner_radius[1], self.corner_radius[0], self.corner_radius[1])
            elif len(self.corner_radius) == 3:
                # [top-left, top-right/bottom-left, bottom-right]
                return (self.corner_radius[0], self.corner_radius[1], self.corner_radius[2], self.corner_radius[1])
            elif len(self.corner_radius) == 4:
                # [top-left, top-right, bottom-right, bottom-left]
                return (self.corner_radius[0], self.corner_radius[1], self.corner_radius[2], self.corner_radius[3])
            else:
                # Invalid length, use first value for all corners or 0
                value = self.corner_radius[0] if self.corner_radius else 0
                return (value, value, value, value)


class Theme(BaseModel):
    """Theme style configuration (for user customization of preset themes)."""

    text_area_height: int | None = Field(None, description="Height of text area at top in pixels")
    background_color: str | None = Field(None, description="Background color for entire image")
    image_style: ImageStyle | None = Field(None, description="Image style configuration for this theme")
    main_text_style: LocalizedTextStyle | None = Field(None, description="Main text style configuration for this theme")
    sub_text_style: LocalizedTextStyle | None = Field(
        None, description="Subtitle text style configuration for this theme"
    )


class ScreenshotConfig(BaseModel):
    """Root configuration for screenshot generation."""

    languages: list[str] | None = Field(None, description="List of languages to generate")
    default_language: str | None = Field("en", description="Default language for fallback")
    background_color: str | None = Field(None, description="Background color if resizing")

    # Output sizes (width x height)
    output_sizes: list[tuple[int, int]] = Field(
        default=[(1320, 2868), (2064, 2752)], description="List of output sizes (width, height) in pixels"
    )

    # Theme system - only style customizations for preset themes
    theme_styles: dict[str, Theme] = Field(default_factory=dict, description="Style customizations for preset themes")
    default_theme: str = Field(default="standard", description="Default preset theme to use")

    screenshots: list[Screenshot] = Field(..., description="List of screenshots to generate")
