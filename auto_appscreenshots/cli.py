"""Command-line interface for screenshot generation."""

import sys
from pathlib import Path

import click

from .cli_runner import CliRunner


@click.command()
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=False,
    help="Path to YML configuration file",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("./output"),
    help="Output directory (default: ./output)",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option("--validate-only", is_flag=True, help="Validate configuration without generating images")
@click.option("-l", "--language", help="Specific language to generate (generates all if not specified)")
@click.option("--show-options", is_flag=True, help="Show all available configuration options with descriptions")
def main(config: Path, output: Path, verbose: bool, validate_only: bool, language: str, show_options: bool) -> None:
    """Generate App Store Connect screenshots with text overlays.

    This tool reads a YML configuration file and generates screenshots
    with customizable text overlays for App Store Connect submissions.

    Example:
        appscreenshots -c config.yml
    """
    # Initialize CLI runner
    runner = CliRunner(verbose=verbose)

    # Handle --show-options flag
    if show_options:
        runner.show_options()
        return

    # Check if config is required
    if not config:
        click.echo("Error: -c/--config option is required", err=True)
        sys.exit(1)

    # Execute screenshot generation
    exit_code = runner.generate_screenshots(
        config_path=config, output_dir=output, language=language, validate_only=validate_only
    )

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
