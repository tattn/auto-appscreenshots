"""Tests for file management utilities."""

from pathlib import Path

from PIL import Image

from auto_appscreenshots.file_manager import FileManager
from auto_appscreenshots.models import LocalizedTextContent, Screenshot


class TestFileManager:
    """Test FileManager class."""

    def test_init_creates_directory(self, temp_dir: Path) -> None:
        """Test that initialization creates the base output directory."""
        output_dir = temp_dir / "test_output"
        assert not output_dir.exists()

        FileManager(output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_create_output_path_with_output_name(self, temp_dir: Path) -> None:
        """Test creating output path with custom output name."""
        manager = FileManager(temp_dir)
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name="custom_{lang}_{width}x{height}",
            theme=None,
        )

        path = manager.create_output_path(
            language="en", resolution_width=1320, resolution_height=2868, screenshot=screenshot, index=1
        )

        assert path == temp_dir / "en" / "1320x2868" / "custom_en_1320x2868.png"
        assert path.parent.exists()  # Directory should be created

    def test_create_output_path_without_output_name(self, temp_dir: Path) -> None:
        """Test creating output path with default naming."""
        manager = FileManager(temp_dir)
        screenshot = Screenshot(
            input_image="path/to/input_image.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme=None,
        )

        path = manager.create_output_path(
            language="en", resolution_width=1320, resolution_height=2868, screenshot=screenshot, index=5
        )

        expected = temp_dir / "en" / "1320x2868" / "05_input_image_with_text_1320x2868.png"
        assert path == expected

    def test_create_output_path_ensures_png_extension(self, temp_dir: Path) -> None:
        """Test that .png extension is added if missing."""
        manager = FileManager(temp_dir)
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name="no_extension",
            theme=None,
        )

        path = manager.create_output_path(
            language="en", resolution_width=1320, resolution_height=2868, screenshot=screenshot
        )

        assert path.suffix == ".png"
        assert path.name == "no_extension.png"

    def test_save_image(self, temp_dir: Path) -> None:
        """Test saving an image."""
        manager = FileManager(temp_dir)
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        output_path = temp_dir / "test_save.png"

        manager.save_image(image, output_path)

        assert output_path.exists()

        # Load and verify saved image
        loaded = Image.open(output_path)
        assert loaded.size == (100, 100)
        assert loaded.mode == "RGBA"

    def test_save_image_with_quality(self, temp_dir: Path) -> None:
        """Test saving an image with custom quality."""
        manager = FileManager(temp_dir)
        image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
        output_path = temp_dir / "test_quality.png"

        manager.save_image(image, output_path, quality=50)

        assert output_path.exists()

    def test_check_input_exists(self, temp_dir: Path, sample_image: Path) -> None:
        """Test checking if input file exists."""
        manager = FileManager(temp_dir)

        assert manager.check_input_exists(str(sample_image)) is True
        assert manager.check_input_exists("nonexistent.png") is False

    def test_get_output_directories(self, temp_dir: Path) -> None:
        """Test getting list of output directories."""
        manager = FileManager(temp_dir)

        # Create some directories
        (temp_dir / "en" / "1320x2868").mkdir(parents=True)
        (temp_dir / "ja" / "1320x2868").mkdir(parents=True)
        (temp_dir / "en" / "2064x2752").mkdir(parents=True)

        dirs = manager.get_output_directories()
        dir_names = [str(d.relative_to(temp_dir)) for d in dirs]

        assert len(dirs) == 3
        assert "en/1320x2868" in dir_names
        assert "ja/1320x2868" in dir_names
        assert "en/2064x2752" in dir_names

    def test_process_output_name_placeholders(self, temp_dir: Path) -> None:
        """Test processing output name placeholders."""
        manager = FileManager(temp_dir)
        screenshot = Screenshot(
            input_image="test.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name="test_{lang}_{width}_{height}",
            theme=None,
        )

        path = manager.create_output_path(
            language="ja", resolution_width=1080, resolution_height=1920, screenshot=screenshot
        )

        assert "test_ja_1080_1920.png" in str(path)

    def test_generate_default_filename_with_index(self, temp_dir: Path) -> None:
        """Test generating default filename with index."""
        manager = FileManager(temp_dir)
        screenshot = Screenshot(
            input_image="/path/to/screenshot.png",
            text=LocalizedTextContent(main_text={"en": "Test"}, sub_text=None),
            output_name=None,
            theme=None,
        )

        path = manager.create_output_path(
            language="en", resolution_width=1320, resolution_height=2868, screenshot=screenshot, index=42
        )

        assert path.name == "42_screenshot_with_text_1320x2868.png"
