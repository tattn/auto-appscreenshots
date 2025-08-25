"""CLI runner following Single Responsibility Principle."""

import logging
import os
import sys
from pathlib import Path
from typing import Any

import click

from .config_docs import format_configuration_docs
from .config_manager import ConfigManager
from .generator import ScreenshotGenerator
from .models import ScreenshotConfig
from .preset_themes import PresetThemes
from .ui_reporter import ConsoleReporter
from .validator import ConfigValidator

logger = logging.getLogger(__name__)


class ColoredWarningFormatter(logging.Formatter):
    """Custom formatter to make warning messages more prominent."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.use_colors = (
            hasattr(sys.stderr, "isatty")
            and sys.stderr.isatty()
            and not os.environ.get("NO_COLOR")
            and os.environ.get("TERM", "") != "dumb"
        )

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == logging.WARNING:
            msg = record.getMessage()
            if "⚠️" not in msg:
                record.msg = f"⚠️  {record.msg}"
            if self.use_colors:
                record.msg = f"\033[1;33m{record.msg}\033[0m"
        return super().format(record)


class CliRunner:
    """Handles CLI execution logic."""

    def __init__(self, verbose: bool = False):
        """Initialize CLI runner."""
        self.verbose = verbose
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on verbosity."""
        # Remove existing handlers
        logger_root = logging.getLogger()
        for handler in logger_root.handlers[:]:
            logger_root.removeHandler(handler)

        # Create console handler with custom formatter
        console_handler = logging.StreamHandler(sys.stderr)

        if self.verbose:
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        else:
            console_handler.setLevel(logging.WARNING)
            formatter = ColoredWarningFormatter("%(message)s")

        console_handler.setFormatter(formatter)

        # Configure root logger
        logger_root.setLevel(logging.DEBUG if self.verbose else logging.WARNING)
        logger_root.addHandler(console_handler)

    def show_options(self) -> None:
        """Display available configuration options."""
        click.echo(format_configuration_docs())

    def validate_config(self, config_path: Path) -> tuple[bool, ScreenshotConfig | None]:
        """Validate configuration file."""
        validator = ConfigValidator(verbose=self.verbose)
        return validator.validate_config_file(str(config_path))

    def generate_screenshots(
        self, config_path: Path, output_dir: Path, language: str | None = None, validate_only: bool = False
    ) -> int:
        """Generate screenshots from configuration.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Validate configuration
        is_valid, screenshot_config = self.validate_config(config_path)

        if not is_valid or screenshot_config is None:
            return 1

        if validate_only:
            validator = ConfigValidator(verbose=self.verbose)
            if not validator.warnings:
                click.echo("\n✅ Configuration is valid!")
            return 0

        logger.debug(f"Loaded configuration from {config_path}")
        logger.debug(f"Found {len(screenshot_config.screenshots)} screenshots to generate")

        # Display summary
        self._display_generation_summary(config_path, screenshot_config, language)

        try:
            # Create generator with appropriate reporter
            ui_reporter = ConsoleReporter(verbose=self.verbose)
            generator = ScreenshotGenerator(
                screenshot_config, output_dir=output_dir, config_path=config_path, ui_reporter=ui_reporter
            )

            # Generate screenshots
            generated_files = generator.generate_all(language=language)

            # Display results
            self._display_results(generated_files, output_dir, screenshot_config, language)

            return 0

        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            click.echo(f"❌ Error: {e}", err=True)
            return 1

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            click.echo(f"❌ Unexpected error: {e}", err=True)
            return 1

    def _display_generation_summary(self, config_path: Path, config: ScreenshotConfig, language: str | None) -> None:
        """Display generation summary before processing."""
        click.echo(f"\n📋 Configuration: {config_path.name}")
        click.echo(f"🖼  Screenshots: {len(config.screenshots)}")

        # Get languages and sizes for display
        config_manager = ConfigManager(config, PresetThemes())
        languages = config_manager.get_languages_to_generate(language)
        sizes = config.output_sizes
        total_count = len(config.screenshots) * len(languages) * len(sizes)

        click.echo(f"🌐 Languages: {', '.join(languages) if languages else 'None'}")
        click.echo(f"📐 Sizes: {', '.join([f'{w}×{h}' for w, h in sizes])}")
        click.echo()

        if language:
            count = len(config.screenshots) * len(sizes)
            click.echo(f"📱 Generating {count} screenshots for {language}...")
        else:
            click.echo(f"📱 Generating {total_count} screenshots...")

    def _display_results(
        self, generated_files: list[Path], output_dir: Path, config: ScreenshotConfig, language: str | None
    ) -> None:
        """Display generation results."""
        click.echo()
        click.echo(f"✅ Success! Generated {len(generated_files)} screenshots")
        click.echo(f"📁 Output: {output_dir}/")

        if self.verbose:
            # Show detailed file list in verbose mode
            config_manager = ConfigManager(config, PresetThemes())
            languages = config_manager.get_languages_to_generate(language)

            for lang in languages:
                lang_files = [f for f in generated_files if f"/{lang}/" in str(f)]
                if lang_files:
                    click.echo(f"\n  {lang}:")
                    for file in lang_files:
                        click.echo(f"    - {file.parent.name}/{file.name}")
