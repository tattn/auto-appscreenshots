"""Tests for image processing utilities."""

from pathlib import Path

from PIL import Image

from auto_appscreenshots.image_processor import ImageProcessor


class TestImageProcessor:
    """Test ImageProcessor class."""

    def test_create_canvas(self) -> None:
        """Test creating a canvas."""
        processor = ImageProcessor()
        canvas = processor.create_canvas(200, 300, (255, 0, 0, 255))

        assert canvas.size == (200, 300)
        assert canvas.mode == "RGBA"
        assert canvas.getpixel((0, 0)) == (255, 0, 0, 255)  # type: ignore[attr-defined, unused-ignore]

    def test_load_image(self, sample_image: Path) -> None:
        """Test loading an image."""
        processor = ImageProcessor()
        img = processor.load_image(str(sample_image))

        assert img.mode == "RGBA"
        assert img.size == (100, 100)

    def test_calculate_scale_factor(self) -> None:
        """Test calculating scale factor."""
        processor = ImageProcessor()

        # Test scaling down
        scale = processor.calculate_scale_factor(100, 200, 50, 50)
        assert scale == 0.25  # Limited by height

        scale = processor.calculate_scale_factor(200, 100, 50, 50)
        assert scale == 0.25  # Limited by width

        # Test scaling up
        scale = processor.calculate_scale_factor(50, 50, 200, 200)
        assert scale == 4.0

    def test_resize_image(self) -> None:
        """Test resizing an image."""
        processor = ImageProcessor()
        original = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))

        resized = processor.resize_image(original, 50, 50)

        assert resized.size == (50, 50)
        assert resized.mode == "RGBA"

    def test_calculate_screenshot_dimensions(self) -> None:
        """Test calculating screenshot dimensions and position."""
        processor = ImageProcessor()

        width, height, x, y = processor.calculate_screenshot_dimensions(
            canvas_width=1320,
            canvas_height=2868,
            text_area_height=400,
            padding_top=50,
            padding_right=50,
            padding_bottom=50,
            padding_left=50,
            original_width=1000,
            original_height=2000,
        )

        # Check that dimensions fit within available area
        available_width = 1320 - (50 * 2)  # 1220
        available_height = 2868 - 400 - (50 * 2)  # 2368

        assert width <= available_width
        assert height <= available_height
        assert x >= 0
        assert y >= 400  # Below text area

    def test_calculate_screenshot_dimensions_asymmetric_padding(self) -> None:
        """Test calculating screenshot dimensions with asymmetric padding."""
        processor = ImageProcessor()

        width, height, x, y = processor.calculate_screenshot_dimensions(
            canvas_width=1320,
            canvas_height=2868,
            text_area_height=400,
            padding_top=20,
            padding_right=40,
            padding_bottom=60,
            padding_left=80,
            original_width=1000,
            original_height=2000,
        )

        # Check that dimensions fit within available area
        available_width = 1320 - 80 - 40  # 1200
        available_height = 2868 - 400 - 20 - 60  # 2388

        assert width <= available_width
        assert height <= available_height
        assert x >= 80  # Should respect left padding
        assert y >= 420  # Should respect text area + top padding

    def test_compose_images(self) -> None:
        """Test composing images."""
        processor = ImageProcessor()
        canvas = Image.new("RGBA", (200, 200), color=(255, 255, 255, 255))
        screenshot = Image.new("RGBA", (50, 50), color=(255, 0, 0, 255))

        result = processor.compose_images(canvas, screenshot, 50, 50)

        assert result.size == (200, 200)
        assert result.getpixel((50, 50)) == (255, 0, 0, 255)  # type: ignore[attr-defined, unused-ignore]  # Screenshot color
        assert result.getpixel((0, 0)) == (255, 255, 255, 255)  # type: ignore[attr-defined, unused-ignore]  # Canvas color

    def test_parse_color_hex6(self) -> None:
        """Test parsing 6-character hex color."""
        processor = ImageProcessor()

        color = processor.parse_color("#FF0000")
        assert color == (255, 0, 0, 255)

        color = processor.parse_color("00FF00")  # Without #
        assert color == (0, 255, 0, 255)

    def test_parse_color_hex8(self) -> None:
        """Test parsing 8-character hex color with alpha."""
        processor = ImageProcessor()

        color = processor.parse_color("#FF000080")
        assert color == (255, 0, 0, 128)

        color = processor.parse_color("00FF0040")  # Without #
        assert color == (0, 255, 0, 64)

    def test_parse_color_invalid(self) -> None:
        """Test parsing invalid color returns black."""
        processor = ImageProcessor()

        color = processor.parse_color("invalid")
        assert color == (0, 0, 0, 255)

        color = processor.parse_color("#GGG")
        assert color == (0, 0, 0, 255)

    def test_apply_corner_radius(self) -> None:
        """Test applying corner radius to an image."""
        processor = ImageProcessor()

        # Create a solid color image
        original = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))

        # Test with radius = 0 (no rounding)
        rounded = processor.apply_corner_radius(original, 0, 0, 0, 0)
        assert rounded.size == (100, 100)
        assert rounded.mode == "RGBA"
        # Center pixel should remain the same
        assert rounded.getpixel((50, 50)) == (255, 0, 0, 255)  # type: ignore[attr-defined, unused-ignore]

        # Test with all corners having same radius > 0
        rounded = processor.apply_corner_radius(original, 20, 20, 20, 20)
        assert rounded.size == (100, 100)
        assert rounded.mode == "RGBA"
        # Center pixel should remain the same
        assert rounded.getpixel((50, 50)) == (255, 0, 0, 255)  # type: ignore[attr-defined, unused-ignore]
        # Corner pixel should be transparent
        assert rounded.getpixel((0, 0))[3] < 255  # type: ignore[attr-defined, unused-ignore]  # Alpha channel should be less than 255

    def test_apply_corner_radius_individual(self) -> None:
        """Test applying individual corner radii."""
        processor = ImageProcessor()

        # Create a solid color image
        original = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))

        # Test with only top corners rounded
        rounded = processor.apply_corner_radius(original, 20, 20, 0, 0)
        assert rounded.size == (100, 100)
        assert rounded.mode == "RGBA"

        # Top-left corner should be transparent
        assert rounded.getpixel((0, 0))[3] < 255  # type: ignore[attr-defined, unused-ignore]
        # Top-right corner should be transparent
        assert rounded.getpixel((99, 0))[3] < 255  # type: ignore[attr-defined, unused-ignore]
        # Bottom corners should be opaque
        assert rounded.getpixel((0, 99))[3] == 255  # type: ignore[attr-defined, unused-ignore]
        assert rounded.getpixel((99, 99))[3] == 255  # type: ignore[attr-defined, unused-ignore]

        # Test with only one corner rounded
        rounded = processor.apply_corner_radius(original, 20, 0, 0, 0)
        assert rounded.size == (100, 100)
        # Only top-left corner should be transparent
        assert rounded.getpixel((0, 0))[3] < 255  # type: ignore[attr-defined, unused-ignore]
        # Other corners should be opaque
        assert rounded.getpixel((99, 0))[3] == 255  # type: ignore[attr-defined, unused-ignore]
        assert rounded.getpixel((0, 99))[3] == 255  # type: ignore[attr-defined, unused-ignore]
        assert rounded.getpixel((99, 99))[3] == 255  # type: ignore[attr-defined, unused-ignore]
