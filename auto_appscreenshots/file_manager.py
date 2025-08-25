"""File management utilities following Single Responsibility Principle."""

import logging
from pathlib import Path

from PIL import Image

from .models import Screenshot

logger = logging.getLogger(__name__)


class FileManager:
    """Handles file operations and path management."""

    def __init__(self, base_output_dir: Path, config_dir: Path | None = None):
        """Initialize file manager with base output directory.

        Args:
            base_output_dir: Base directory for output files
            config_dir: Directory containing the config file (for resolving relative paths)
        """
        self.base_output_dir = base_output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir = config_dir or Path.cwd()

    def create_output_path(
        self,
        language: str,
        resolution_width: int,
        resolution_height: int,
        screenshot: Screenshot,
        index: int | None = None,
    ) -> Path:
        """Generate output path for a screenshot.

        Args:
            language: Language code
            resolution_width: Output width
            resolution_height: Output height
            screenshot: Screenshot configuration
            index: Optional index for ordering

        Returns:
            Path object for output file
        """
        resolution_str = f"{resolution_width}x{resolution_height}"

        if screenshot.output_name:
            output_filename = self._process_output_name(
                screenshot.output_name, language, resolution_width, resolution_height
            )
        else:
            output_filename = self._generate_default_filename(screenshot.input_image, resolution_str, index)

        # Build full path with language and resolution directories
        output_path = self.base_output_dir / language / resolution_str / output_filename

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def save_image(self, image: Image.Image, path: Path, quality: int = 95) -> None:
        """Save image to specified path.

        Args:
            image: PIL Image to save
            path: Output path
            quality: JPEG/PNG compression quality (0-100)
        """
        try:
            # Convert RGBA to RGB to remove alpha channel
            if image.mode == "RGBA":
                # Create RGB image with white background
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = rgb_image
            elif image.mode != "RGB":
                # Convert other modes to RGB
                image = image.convert("RGB")

            image.save(path, quality=quality)
            logger.debug(f"Saved image to: {path}")
        except Exception as e:
            logger.error(f"Failed to save image to {path}: {e}")
            raise

    def check_input_exists(self, path: str) -> bool:
        """Check if input file exists.

        Args:
            path: Path to check (absolute or relative to config file)

        Returns:
            True if file exists, False otherwise
        """
        input_path = Path(path)
        if not input_path.is_absolute():
            input_path = self.config_dir / input_path
        return input_path.exists()

    def get_output_directories(self) -> list[Path]:
        """Get list of output directories created.

        Returns:
            List of Path objects for each output directory
        """
        return list(self.base_output_dir.glob("*/*/"))

    def _process_output_name(self, output_name: str, language: str, width: int, height: int) -> str:
        """Process output name with placeholder replacements.

        Args:
            output_name: Original output name with possible placeholders
            language: Language code to replace {lang}
            width: Width to replace {width}
            height: Height to replace {height}

        Returns:
            Processed filename with .png extension
        """
        # Replace placeholders
        processed = output_name

        if "{lang}" in processed:
            processed = processed.replace("{lang}", language)
        if "{size}" in processed:
            processed = processed.replace("{size}", f"{width}x{height}")
        if "{width}" in processed:
            processed = processed.replace("{width}", str(width))
        if "{height}" in processed:
            processed = processed.replace("{height}", str(height))

        # Ensure .png extension
        if not processed.endswith(".png"):
            processed = f"{processed}.png"

        return processed

    def _generate_default_filename(self, input_path: str, resolution_str: str, index: int | None = None) -> str:
        """Generate default filename when no output_name is specified.

        Args:
            input_path: Path to input image
            resolution_str: Resolution string (e.g., "1920x1080")
            index: Optional index for ordering

        Returns:
            Generated filename
        """
        # Extract base name from input path
        path = Path(input_path)
        if not path.is_absolute():
            path = self.config_dir / path
        base_name = path.stem

        # Add index prefix if provided
        filename = f"{index:02d}_" if index else ""
        filename += f"{base_name}_with_text_{resolution_str}.png"

        return filename

    def resolve_input_path(self, path: str) -> Path:
        """Resolve input path relative to config directory.

        Args:
            path: Path to resolve (absolute or relative to config file)

        Returns:
            Resolved absolute path
        """
        input_path = Path(path)
        if not input_path.is_absolute():
            input_path = self.config_dir / input_path
        return input_path
