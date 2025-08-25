"""Dynamic configuration documentation generator from Pydantic models."""

from typing import Any, get_args, get_origin

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .models import ImageStyle, Screenshot, ScreenshotConfig, TextStyle


def get_type_string(type_hint: Any) -> str:
    """Convert Python type hint to readable string."""
    origin = get_origin(type_hint)

    if origin is None:
        if hasattr(type_hint, "__name__"):
            return str(type_hint.__name__)
        return str(type_hint)

    if origin is list or origin is list:
        args = get_args(type_hint)
        if args:
            return f"list[{get_type_string(args[0])}]"
        return "list"

    if origin is dict or origin is dict:
        args = get_args(type_hint)
        if len(args) == 2:
            return f"dict[{get_type_string(args[0])}, {get_type_string(args[1])}]"
        return "dict"

    if origin is tuple:
        args = get_args(type_hint)
        if args:
            return f"tuple[{', '.join(get_type_string(arg) for arg in args)}]"
        return "tuple"

    # Handle Optional/Union types
    args = get_args(type_hint)
    if args and type(None) in args:
        # This is Optional[T], return T
        non_none_types = [arg for arg in args if arg is not type(None)]
        if non_none_types:
            return get_type_string(non_none_types[0])

    return str(type_hint)


def extract_field_info(model: type[BaseModel], field_name: str) -> tuple[str, Any, bool, str]:
    """Extract field information from Pydantic model.

    Returns:
        Tuple of (type_string, default_value, is_required, description)
    """
    field_info = model.model_fields[field_name]
    field_type = field_info.annotation
    is_required = field_info.is_required()

    # Get default value
    default = field_info.default
    if default is ... or default is PydanticUndefined:
        default = None
    elif callable(default):
        try:
            default = default()
        except Exception:
            default = None

    # Get description
    description = field_info.description or ""

    # Get type string
    type_str = get_type_string(field_type)

    return type_str, default, is_required, description


def format_configuration_docs() -> str:
    """Generate and format configuration documentation dynamically."""
    output: list[str] = []

    output.append("=" * 80)
    output.append("📋 auto-appscreenshots - Configuration Options")
    output.append("=" * 80)
    output.append("")

    # Root Level Configuration
    output.append("## Root Level Settings")
    output.append("   Options specified at the top level of the configuration file")
    output.append("")

    # Process ScreenshotConfig fields
    for field_name in ScreenshotConfig.model_fields:
        type_str, default, is_required, description = extract_field_info(ScreenshotConfig, field_name)

        # Format default value for display
        if default is None:
            default_str = "None"
        elif isinstance(default, str):
            default_str = f'"{default}"'
        elif isinstance(default, list):
            default_str = str(list(default))  # type: ignore[arg-type, unused-ignore]
        elif isinstance(default, dict):
            default_str = str(dict(default))  # type: ignore[call-overload, unused-ignore]
        else:
            default_str = str(default)

        required = "Required" if is_required else "Optional"

        output.append(f"  ▸ {field_name}")
        output.append(f"    Type: {type_str} | Default: {default_str} | {required}")
        output.append(f"    Description: {description}")
        output.append("")

    output.append("")

    # Theme Styles Configuration
    output.append("## Theme Style Settings (theme_styles)")
    output.append("   Customize the appearance of preset themes")
    output.append("")
    output.append("  ▸ theme_styles.[theme_name]")
    output.append("    Type: Theme | Default: None | Optional")
    output.append("    Description: Style settings for specific theme (e.g., 'standard', 'standard_inverted')")
    output.append("")
    output.append("")

    # Theme Configuration
    output.append("## Theme Settings (theme_styles.*)")
    output.append("   Configure text area and background")
    output.append("")
    output.append("  ▸ text_area_height")
    output.append("    Type: int | Default: 400 | Optional")
    output.append("    Description: Height of text area at top in pixels")
    output.append("")
    output.append("  ▸ background_color")
    output.append('    Type: str | Default: "#F5F5F5" | Optional')
    output.append("    Description: Background color for entire image")
    output.append("")

    # Image Style Configuration
    output.append("## Image Style Settings (theme_styles.*.image_style)")
    output.append("   Configure image appearance")
    output.append("")

    for field_name in ImageStyle.model_fields:
        type_str, default, is_required, description = extract_field_info(ImageStyle, field_name)

        if isinstance(default, str):
            default_str = f'"{default}"'
        else:
            default_str = str(default)

        output.append(f"  ▸ image_style.{field_name}")
        output.append(f"    Type: {type_str} | Default: {default_str} | Optional")
        output.append(f"    Description: {description}")
        output.append("")

    output.append("")

    # Text Style Configuration
    output.append("## Text Style Settings (main_text_style / sub_text_style)")
    output.append("   Configure text appearance for different languages")
    output.append("")

    output.append("  ▸ *.defaults")
    output.append("    Type: TextStyle | Default: None | Optional")
    output.append("    Description: Default text style applied to all languages")
    output.append("")

    output.append("  ▸ *.[lang_code]")
    output.append("    Type: TextStyle | Default: None | Optional")
    output.append("    Description: Language-specific text style (e.g., 'ja', 'en', 'ko', 'zh-Hans')")
    output.append("    Note: Supports any language code. Overrides defaults style.")
    output.append("")
    output.append("")

    # TextStyle Details
    output.append("## TextStyle Properties")
    output.append("   Available properties for each TextStyle")
    output.append("")

    for field_name in TextStyle.model_fields:
        type_str, default, is_required, description = extract_field_info(TextStyle, field_name)

        # Format default for display
        if isinstance(default, str):
            default_str = f'"{default}"'
        elif isinstance(default, tuple):
            tuple_as_list: list[Any] = list(default)  # type: ignore[arg-type, unused-ignore]
            default_str = str(tuple_as_list)
        else:
            default_str = str(default)

        output.append(f"  ▸ {field_name}")
        output.append(f"    Type: {type_str} | Default: {default_str} | Optional")
        output.append(f"    Description: {description}")
        output.append("")

    output.append("")

    # Screenshot Configuration
    output.append("## Screenshot Settings (screenshots[])")
    output.append("   Individual screenshot configuration")
    output.append("")

    for field_name in Screenshot.model_fields:
        type_str, default, is_required, description = extract_field_info(Screenshot, field_name)

        # Special formatting for certain fields
        if field_name == "text":
            output.append("  ▸ text")
            output.append("    Type: dict[str, LocalizedText] | Required")
            output.append("    Description: Localized text by language code")
            output.append("")
            output.append("  ▸ text.[lang_code].main_text")
            output.append("    Type: str | Required")
            output.append("    Description: Main text for the language")
            output.append("")
            output.append("  ▸ text.[lang_code].sub_text")
            output.append("    Type: str | Optional")
            output.append("    Description: Subtitle text for the language")
            output.append("")
        elif field_name in ["main_text_style", "sub_text_style"]:
            output.append(f"  ▸ {field_name}")
            output.append("    Type: LocalizedTextStyle | Optional")
            output.append(f"    Description: Override {field_name.replace('_', ' ')} for this screenshot")
            output.append("    Note: Same structure as theme_styles text styles")
            output.append("")
        else:
            default_str = "None" if default is None else str(default)
            required = "Required" if is_required else "Optional"

            output.append(f"  ▸ {field_name}")
            output.append(f"    Type: {type_str} | {required}")
            output.append(f"    Description: {description}")
            output.append("")

    output.append("")

    # Priority Note
    output.append("=" * 80)
    output.append("💡 Configuration Priority (highest to lowest):")
    output.append("   1. Individual screenshot settings")
    output.append("   2. Theme-specific settings (theme_styles.[theme_name])")
    output.append("   3. System default values")
    output.append("=" * 80)
    output.append("")

    return "\n".join(output)
