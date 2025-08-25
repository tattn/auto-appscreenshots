"""Screenshot generator with text overlay functionality."""

import logging
from pathlib import Path

from PIL import Image, ImageDraw

from .config_manager import ConfigManager
from .file_manager import FileManager
from .image_processor import ImageProcessor
from .models import Screenshot, ScreenshotConfig
from .preset_themes import PresetThemes
from .text_renderer import TextPosition, TextRenderer
from .ui_reporter import ConsoleReporter, UIReporter

logger = logging.getLogger(__name__)


class ScreenshotGenerator:
    """Generate App Store Connect screenshots with text overlays."""

    def __init__(
        self,
        config: ScreenshotConfig,
        output_dir: Path,
        config_path: Path | None = None,
        ui_reporter: UIReporter | None = None,
    ):
        """Initialize generator with configuration.

        Args:
            config: Screenshot configuration
            output_dir: Output directory path
            config_path: Path to the config file (for resolving relative paths)
            ui_reporter: UI reporter for progress updates
        """
        self.config = config
        self.config_manager = ConfigManager(config, PresetThemes())
        config_dir = config_path.parent if config_path else Path.cwd()
        self.file_manager = FileManager(output_dir, config_dir=config_dir)
        self.image_processor = ImageProcessor()
        self.text_renderer = TextRenderer()
        self.ui_reporter = ui_reporter or ConsoleReporter()

    def generate_all(self, language: str | None = None) -> list[Path]:
        """Generate all screenshots defined in configuration."""
        generated_files: list[Path] = []
        languages = self.config_manager.get_languages_to_generate(language)

        for lang in languages:
            logger.debug(f"Generating screenshots for language: {lang}")
            self.ui_reporter.report_language_start(lang)

            for i, screenshot in enumerate(self.config.screenshots, 1):
                try:
                    # Format input image path for display (using first size)
                    first_size = self.config.output_sizes[0] if self.config.output_sizes else None
                    input_image_path = screenshot.format_input_image(lang, first_size)
                    screenshot_name = Path(input_image_path).stem
                    self.ui_reporter.report_screenshot_start(i, len(self.config.screenshots), screenshot_name)

                    output_paths = self.generate_screenshot(screenshot, index=i, language=lang)
                    generated_files.extend(output_paths)
                    self.ui_reporter.report_screenshot_success(output_paths)

                except Exception as e:
                    self.ui_reporter.report_screenshot_error(e)
                    logger.error(f"Failed to generate screenshot {i} for language {lang}: {e}")
                    raise

        return generated_files

    def generate_screenshot(self, screenshot: Screenshot, index: int | None = None, language: str = "en") -> list[Path]:
        """Generate screenshots with text header in multiple sizes."""

        # Get text for the specified language
        try:
            main_text, sub_text = screenshot.get_text_for_language(language)
            logger.debug(f"Text for {language}: main='{main_text}', sub='{sub_text}'")
        except ValueError as e:
            logger.error(f"Failed to get text for language {language}: {e}")
            raise

        # Generate for each size
        generated_paths: list[Path] = []
        for size_width, size_height in self.config.output_sizes:
            # Format input image path with placeholders
            size = (size_width, size_height)
            input_image_path = screenshot.format_input_image(language, size)

            # Validate input
            if not self.file_manager.check_input_exists(input_image_path):
                raise FileNotFoundError(f"Input image not found: {input_image_path}")

            # Load original screenshot
            resolved_path = self.file_manager.resolve_input_path(input_image_path)
            original = self.image_processor.load_image(str(resolved_path))
            orig_width, orig_height = original.size
            logger.debug(
                f"Loaded image: {orig_width}x{orig_height} from {input_image_path} for size {size_width}x{size_height}"
            )

            generated_path = self._generate_single_size(
                screenshot=screenshot,
                original=original,
                main_text=main_text,
                sub_text=sub_text,
                canvas_width=size_width,
                canvas_height=size_height,
                index=index,
                language=language,
            )
            generated_paths.append(generated_path)

        return generated_paths

    def _generate_single_size(
        self,
        screenshot: Screenshot,
        original: Image.Image,
        main_text: str,
        sub_text: str | None,
        canvas_width: int,
        canvas_height: int,
        index: int | None = None,
        language: str = "en",
    ) -> Path:
        """Generate a single screenshot at a specific size."""
        # Get style configuration
        text_area_height = self.config_manager.get_text_area_height(screenshot)
        background_color = self.config_manager.get_background_color(screenshot)
        image_style = self.config_manager.get_image_style(screenshot)
        orig_width, orig_height = original.size

        # Get padding values as (top, right, bottom, left)
        padding_top, padding_right, padding_bottom, padding_left = image_style.get_padding_values()

        # Calculate dimensions for screenshot placement
        scaled_width, scaled_height, x_pos, y_pos = self.image_processor.calculate_screenshot_dimensions(
            canvas_width,
            canvas_height,
            text_area_height,
            padding_top,
            padding_right,
            padding_bottom,
            padding_left,
            orig_width,
            orig_height,
        )

        # Resize screenshot and create canvas
        screenshot_resized = self.image_processor.resize_image(original, scaled_width, scaled_height)

        # Apply corner radius if specified
        radius_tl, radius_tr, radius_br, radius_bl = image_style.get_corner_radius_values()
        if radius_tl > 0 or radius_tr > 0 or radius_br > 0 or radius_bl > 0:
            screenshot_resized = self.image_processor.apply_corner_radius(
                screenshot_resized, radius_tl, radius_tr, radius_br, radius_bl
            )

        background_color_parsed = self.image_processor.parse_color(background_color)
        canvas = self.image_processor.create_canvas(canvas_width, canvas_height, background_color_parsed)

        # Compose screenshot onto canvas
        canvas = self.image_processor.compose_images(canvas, screenshot_resized, x_pos, y_pos)
        draw = ImageDraw.Draw(canvas)

        # Render text on canvas
        self._render_texts(draw, screenshot, main_text, sub_text, canvas_width, text_area_height, language)

        # Save image
        output_path = self.file_manager.create_output_path(language, canvas_width, canvas_height, screenshot, index)
        self.file_manager.save_image(canvas, output_path)

        return output_path

    def _render_texts(
        self,
        draw: ImageDraw.ImageDraw,
        screenshot: Screenshot,
        main_text: str,
        sub_text: str | None,
        canvas_width: int,
        text_area_height: int,
        language: str,
    ) -> None:
        """Render main and sub text on the canvas."""
        text_layout = self.config_manager.get_text_layout(screenshot)
        main_style = self.config_manager.get_main_text_style(screenshot, language)
        sub_style = self.config_manager.get_sub_text_style(screenshot, language) if sub_text else None

        is_inverted = text_layout == "inverted"
        has_sub_text = bool(sub_text)

        # Render main text
        main_position = TextPosition(
            x=0,
            y=0,
            width=canvas_width,
            height=0,
            text_area_height=text_area_height,
            is_main=True,
            has_sub_text=has_sub_text,
            is_inverted=is_inverted,
        )
        self.text_renderer.render_text(draw, main_text, main_position, main_style)

        # Render sub text if present
        if sub_text and sub_style:
            sub_position = TextPosition(
                x=0,
                y=0,
                width=canvas_width,
                height=0,
                text_area_height=text_area_height,
                is_main=False,
                has_sub_text=True,
                is_inverted=is_inverted,
            )
            self.text_renderer.render_text(draw, sub_text, sub_position, sub_style)
