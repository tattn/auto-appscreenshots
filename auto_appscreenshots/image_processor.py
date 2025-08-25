"""Image processing utilities following Single Responsibility Principle."""

import numpy as np
from PIL import Image


class ImageProcessor:
    """Handles image processing operations."""

    @staticmethod
    def create_canvas(width: int, height: int, background_color: tuple[int, int, int, int]) -> Image.Image:
        """Create a new RGBA canvas with specified dimensions and background color."""
        return Image.new("RGBA", (width, height), background_color)

    @staticmethod
    def load_image(path: str) -> Image.Image:
        """Load and convert an image to RGBA format."""
        return Image.open(path).convert("RGBA")

    @staticmethod
    def calculate_scale_factor(
        original_width: int, original_height: int, target_width: int, target_height: int
    ) -> float:
        """Calculate scale factor to fit image in target dimensions while maintaining aspect ratio."""
        scale_width = target_width / original_width
        scale_height = target_height / original_height
        return min(scale_width, scale_height)

    @staticmethod
    def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
        """Resize image to specified dimensions using high-quality resampling."""
        return image.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def calculate_screenshot_dimensions(
        canvas_width: int,
        canvas_height: int,
        text_area_height: int,
        padding_top: int,
        padding_right: int,
        padding_bottom: int,
        padding_left: int,
        original_width: int,
        original_height: int,
    ) -> tuple[int, int, int, int]:
        """Calculate dimensions and position for screenshot placement.

        Returns:
            Tuple of (scaled_width, scaled_height, x_position, y_position)
        """
        # Calculate available area for screenshot
        available_width = canvas_width - padding_left - padding_right
        available_height = canvas_height - text_area_height - padding_top - padding_bottom

        # Calculate scale to fit
        scale = ImageProcessor.calculate_scale_factor(
            original_width, original_height, available_width, available_height
        )

        # Calculate scaled dimensions
        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)

        # Calculate centered position within padded area
        x_position = padding_left + (available_width - scaled_width) // 2
        y_position = text_area_height + padding_top + (available_height - scaled_height) // 2

        return scaled_width, scaled_height, x_position, y_position

    @staticmethod
    def _generate_squircle_mask(
        width: int, height: int, radius_tl: int, radius_tr: int, radius_br: int, radius_bl: int, n: float = 4.0
    ) -> np.ndarray:
        """Generate a squircle (superellipse) mask with individual corner radii and anti-aliasing.

        Args:
            width: Width of the mask
            height: Height of the mask
            radius_tl: Top-left corner radius
            radius_tr: Top-right corner radius
            radius_br: Bottom-right corner radius
            radius_bl: Bottom-left corner radius
            n: Superellipse parameter (4.0 gives Apple-like squircle)

        Returns:
            Numpy array representing the mask with anti-aliasing
        """
        # Use supersampling for better anti-aliasing (2x resolution)
        scale = 2
        ss_width = width * scale
        ss_height = height * scale

        # Start with a fully opaque mask at higher resolution
        mask = np.ones((ss_height, ss_width), dtype=np.float32) * 255

        # Create coordinate grids at higher resolution
        y, x = np.ogrid[:ss_height, :ss_width]

        # Helper function to apply smooth transition
        def apply_corner(corner_x, corner_y, radius, cx, cy):
            """Apply anti-aliased corner cutout."""
            if radius <= 0:
                return

            # Calculate distance for superellipse at higher resolution
            scaled_radius = radius * scale
            dx = np.abs(corner_x - cx) / scaled_radius
            dy = np.abs(corner_y - cy) / scaled_radius
            distance = np.power(dx, n) + np.power(dy, n)

            # Apply smooth transition (anti-aliasing)
            # Values between 0.98 and 1.02 get smooth transition
            transition_width = 0.015
            alpha = np.where(
                distance < (1 - transition_width),
                255,  # Inside: fully opaque
                np.where(
                    distance > (1 + transition_width),
                    0,  # Outside: fully transparent
                    # Smooth transition zone
                    255 * (1 + transition_width - distance) / (2 * transition_width),
                ),
            )

            # Apply the alpha values
            mask[corner_y, corner_x] = np.minimum(mask[corner_y, corner_x], alpha)

        # Process each corner with its own radius
        # Top-left corner
        if radius_tl > 0:
            r = radius_tl * scale
            corner_x, corner_y = np.meshgrid(np.arange(r), np.arange(r))
            apply_corner(corner_x, corner_y, radius_tl, r - 0.5, r - 0.5)

        # Top-right corner
        if radius_tr > 0:
            r = radius_tr * scale
            corner_x, corner_y = np.meshgrid(np.arange(ss_width - r, ss_width), np.arange(r))
            apply_corner(corner_x, corner_y, radius_tr, ss_width - r + 0.5, r - 0.5)

        # Bottom-right corner
        if radius_br > 0:
            r = radius_br * scale
            corner_x, corner_y = np.meshgrid(np.arange(ss_width - r, ss_width), np.arange(ss_height - r, ss_height))
            apply_corner(corner_x, corner_y, radius_br, ss_width - r + 0.5, ss_height - r + 0.5)

        # Bottom-left corner
        if radius_bl > 0:
            r = radius_bl * scale
            corner_x, corner_y = np.meshgrid(np.arange(r), np.arange(ss_height - r, ss_height))
            apply_corner(corner_x, corner_y, radius_bl, r - 0.5, ss_height - r + 0.5)

        # Downsample back to original resolution using averaging
        # This provides additional anti-aliasing
        mask = mask.reshape((height, scale, width, scale)).mean(axis=(1, 3))

        return mask.astype(np.uint8)

    @staticmethod
    def apply_corner_radius(
        image: Image.Image, radius_tl: int, radius_tr: int, radius_br: int, radius_bl: int
    ) -> Image.Image:
        """Apply corner radius to an image using Apple-style squircle shape.

        Args:
            image: Input image
            radius_tl: Top-left corner radius
            radius_tr: Top-right corner radius
            radius_br: Bottom-right corner radius
            radius_bl: Bottom-left corner radius

        Returns:
            Image with rounded corners
        """
        # If all radii are 0, return the original image
        if radius_tl <= 0 and radius_tr <= 0 and radius_br <= 0 and radius_bl <= 0:
            return image

        width, height = image.size

        # Generate squircle mask using superellipse algorithm with individual radii
        mask_array = ImageProcessor._generate_squircle_mask(width, height, radius_tl, radius_tr, radius_br, radius_bl)
        mask = Image.fromarray(mask_array)

        # Apply the mask to the image
        output = Image.new("RGBA", image.size, (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)

        return output

    @staticmethod
    def compose_images(canvas: Image.Image, screenshot: Image.Image, x: int, y: int) -> Image.Image:
        """Compose screenshot onto canvas at specified position."""
        canvas.paste(screenshot, (x, y), screenshot)
        return canvas

    @staticmethod
    def parse_color(color: str) -> tuple[int, int, int, int]:
        """Parse color string to RGBA tuple.

        Args:
            color: Hex color string (e.g., "#FFFFFF" or "#FFFFFF00")

        Returns:
            RGBA tuple
        """
        if color.startswith("#"):
            color = color[1:]

        if len(color) == 6:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            return (r, g, b, 255)
        elif len(color) == 8:
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            a = int(color[6:8], 16)
            return (r, g, b, a)

        return (0, 0, 0, 255)
