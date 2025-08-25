"""Configuration validator for screenshot generation."""

from pathlib import Path

import click
import yaml
from pydantic import ValidationError

from .models import LocalizedTextStyle, ScreenshotConfig
from .preset_themes import PresetThemes


class ConfigValidator:
    """Validates and provides warnings for configuration files."""

    def __init__(self, verbose: bool = False):
        """Initialize validator with verbosity setting."""
        self.verbose = verbose
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def validate_config_file(self, config_path: str) -> tuple[bool, ScreenshotConfig | None]:
        """
        Validate configuration file and return validation result.

        Returns:
            tuple of (is_valid, config object or None)
        """
        self.warnings = []
        self.errors = []

        # Check if file exists
        config_file = Path(config_path)
        if not config_file.exists():
            self.errors.append(f"Configuration file not found: {config_path}")
            self._print_validation_results()
            return False, None

        # Store config directory for resolving relative paths
        self.config_dir = config_file.parent

        # Load YAML
        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parsing error: {e}")
            self._print_validation_results()
            return False, None
        except Exception as e:
            self.errors.append(f"Failed to read configuration file: {e}")
            self._print_validation_results()
            return False, None

        # Validate with Pydantic model
        try:
            config = ScreenshotConfig(**config_data)
        except ValidationError as e:
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                self.errors.append(f"{location}: {error['msg']}")
            self._print_validation_results()
            return False, None
        except Exception as e:
            self.errors.append(f"Configuration validation failed: {e}")
            self._print_validation_results()
            return False, None

        # Run custom validations
        self._validate_screenshot_config(config)
        self._validate_theme_styles(config)
        self._validate_languages(config)
        self._validate_file_paths(config)

        # Print results
        self._print_validation_results()

        return len(self.errors) == 0, config if len(self.errors) == 0 else None

    def _validate_screenshot_config(self, config: ScreenshotConfig) -> None:
        """Validate individual screenshot configurations."""
        for i, screenshot in enumerate(config.screenshots, 1):
            # Check for each language and size combination
            languages = config.languages or list(screenshot.text.main_text.keys())
            for lang in languages:
                for size in config.output_sizes:
                    # Format the path with placeholders
                    formatted_path = screenshot.format_input_image(lang, size)
                    input_path = Path(formatted_path)

                    # Resolve relative paths relative to config directory
                    if not input_path.is_absolute() and hasattr(self, "config_dir"):
                        input_path = self.config_dir / input_path

                    # Check if file exists
                    if not input_path.exists():
                        size_str = f"{size[0]}x{size[1]}"
                        self.warnings.append(
                            f"Screenshot {i}: Input image not found for "
                            f"lang='{lang}', size='{size_str}': {formatted_path}"
                        )

            # Validate theme
            if screenshot.theme:
                if not PresetThemes.is_valid_theme(screenshot.theme):
                    self.errors.append(
                        f"Screenshot {i}: Invalid theme '{screenshot.theme}'. "
                        f"Available themes: {PresetThemes.list_themes()}"
                    )

            # Check for empty text
            if not screenshot.text or not screenshot.text.main_text:
                self.errors.append(f"Screenshot {i}: No main_text defined")

            # Validate text style format
            if screenshot.main_text_style:
                self._validate_style_format(screenshot.main_text_style, f"Screenshot {i} main_text_style")

            if screenshot.sub_text_style:
                self._validate_style_format(screenshot.sub_text_style, f"Screenshot {i} sub_text_style")

    def _validate_style_format(self, style: LocalizedTextStyle, location: str) -> None:
        """Validate that style has at least one property defined."""
        style_dict = style.model_dump(exclude_none=True)

        if not style_dict:
            self.warnings.append(f"{location}: Style should have at least one property defined")

    def _validate_theme_styles(self, config: ScreenshotConfig) -> None:
        """Validate theme style configurations."""
        # Check for invalid theme names
        for theme_name in config.theme_styles.keys():
            if not PresetThemes.is_valid_theme(theme_name):
                self.warnings.append(
                    f"Theme style '{theme_name}' does not match any preset theme. "
                    f"Available themes: {PresetThemes.list_themes()}"
                )

        # Validate style formats
        for theme_name, theme in config.theme_styles.items():
            if theme.main_text_style:
                self._validate_style_format(theme.main_text_style, f"theme_styles.{theme_name}.main_text_style")

            if theme.sub_text_style:
                self._validate_style_format(theme.sub_text_style, f"theme_styles.{theme_name}.sub_text_style")

    def _validate_languages(self, config: ScreenshotConfig) -> None:
        """Validate language configurations."""
        # Get all languages used in screenshots
        used_languages: set[str] = set()
        for screenshot in config.screenshots:
            if screenshot.text:
                used_languages.update(screenshot.text.main_text.keys())

        # Check if configured languages match used languages
        if config.languages:
            configured_languages = set(config.languages)

            # Warn about unused configured languages
            unused = configured_languages - used_languages
            if unused:
                self.warnings.append(f"Configured languages not used in any screenshot: {', '.join(unused)}")

            # Warn about used but not configured languages
            unconfigured: set[str] = used_languages - configured_languages
            if unconfigured:
                self.warnings.append(
                    f"Languages used in screenshots but not in 'languages' field: {', '.join(unconfigured)}"
                )

    def _validate_file_paths(self, config: ScreenshotConfig) -> None:
        """Validate file paths and output settings."""
        # Check for duplicate output names
        output_names: dict[str, int] = {}
        for i, screenshot in enumerate(config.screenshots, 1):
            if screenshot.output_name:
                if screenshot.output_name in output_names:
                    self.warnings.append(
                        f"Screenshot {i}: Duplicate output_name '{screenshot.output_name}' "
                        f"(also used in screenshot {output_names[screenshot.output_name]})"
                    )
                else:
                    output_names[screenshot.output_name] = i

    def _print_validation_results(self) -> None:
        """Print validation errors and warnings."""
        if self.errors:
            click.echo("\n❌ Validation Errors:", err=True)
            for error in self.errors:
                click.echo(f"   • {error}", err=True)

        if self.warnings:
            click.echo("\n⚠️  Warnings:")
            for warning in self.warnings:
                click.echo(f"   • {warning}")

        if self.errors:
            click.echo("\n❌ Configuration validation failed", err=True)
        elif self.warnings:
            click.echo("\n✅ Configuration is valid (with warnings)")
        elif self.verbose:
            click.echo("\n✅ Configuration is valid")
