"""Integration tests for the complete workflow."""

from pathlib import Path

import pytest
import yaml
from PIL import Image

from auto_appscreenshots.config_manager import ConfigManager
from auto_appscreenshots.generator import ScreenshotGenerator
from auto_appscreenshots.preset_themes import PresetThemes
from auto_appscreenshots.ui_reporter import ConsoleReporter
from auto_appscreenshots.validator import ConfigValidator


class TestIntegration:
    """Integration tests for the complete screenshot generation workflow."""

    @pytest.mark.integration
    def test_complete_workflow(self, temp_dir: Path) -> None:
        """Test complete workflow from config to generated screenshots."""
        # Create test images
        input_dir = temp_dir / "inputs"
        input_dir.mkdir()

        img1 = input_dir / "screen1.png"
        img2 = input_dir / "screen2.png"

        Image.new("RGBA", (750, 1334), color=(100, 100, 100, 255)).save(img1)
        Image.new("RGBA", (750, 1334), color=(150, 150, 150, 255)).save(img2)

        # Create configuration
        config_data = {
            "languages": ["en", "ja"],
            "default_language": "en",
            "output_sizes": [[1320, 2868]],
            "default_theme": "standard",
            "theme_styles": {
                "defaults": {
                    "text_area_height": 400,
                    "background_color": "#F5F5F5",
                    "image_style": {"corner_radius": 0, "padding": 50},
                    "main_text_style": {
                        "font_family": {"en": "Arial", "ja": "Hiragino Sans"},
                        "font_size": 72,  # Direct value
                        "color": "#1A1A1A",  # Direct value
                    },
                }
            },
            "screenshots": [
                {
                    "input_image": str(img1),
                    "text": {
                        "main_text": {"en": "Welcome", "ja": "ようこそ"},
                        "sub_text": {"en": "Get Started", "ja": "始めましょう"},
                    },
                    "output_name": "01_welcome_{lang}",
                },
                {
                    "input_image": str(img2),
                    "text": {"main_text": {"en": "Features", "ja": "機能"}},
                    "theme": "standard_inverted",
                },
            ],
        }

        # Save config
        config_path = temp_dir / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        # Validate configuration
        validator = ConfigValidator()
        is_valid, config = validator.validate_config_file(str(config_path))
        assert is_valid is True
        assert config is not None

        # Generate screenshots
        output_dir = temp_dir / "output"
        generator = ScreenshotGenerator(config=config, output_dir=output_dir, ui_reporter=ConsoleReporter())

        generated_files = generator.generate_all()

        # Verify output structure
        assert output_dir.exists()
        assert (output_dir / "en" / "1320x2868").exists()
        assert (output_dir / "ja" / "1320x2868").exists()

        # Should generate 2 screenshots × 2 languages × 1 resolution = 4 files
        assert len(generated_files) == 4

        # Check specific files
        assert (output_dir / "en" / "1320x2868" / "01_welcome_en.png").exists()
        assert (output_dir / "ja" / "1320x2868" / "01_welcome_ja.png").exists()

        # Load and verify generated image properties
        generated_img = Image.open(output_dir / "en" / "1320x2868" / "01_welcome_en.png")
        assert generated_img.size == (1320, 2868)
        assert generated_img.mode == "RGBA"

    @pytest.mark.integration
    def test_color_inheritance(self, temp_dir: Path) -> None:
        """Test color inheritance with language-specific configs."""
        # Create test image
        input_img = temp_dir / "test.png"
        Image.new("RGBA", (100, 100), color=(255, 255, 255, 255)).save(input_img)

        # Create configuration with complete theme style
        config_data = {
            "languages": ["en", "ja"],
            "default_language": "en",
            "output_sizes": [[1320, 2868]],
            "default_theme": "standard",
            "theme_styles": {
                "standard": {
                    "main_text_style": {
                        "font_family": {"ja": "Hiragino Sans", "en": "Helvetica"},
                        "font_size": 120,  # Direct value
                        "color": "#1A1A1A",  # Direct value
                        "offset": {"en": [0, 50]},
                    }
                },
            },
            "screenshots": [{"input_image": str(input_img), "text": {"main_text": {"en": "Test", "ja": "テスト"}}}],
        }

        # Parse configuration using validator
        config_path = temp_dir / "temp_config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        validator = ConfigValidator()
        is_valid, config = validator.validate_config_file(str(config_path))
        assert is_valid is True
        assert config is not None
        config_manager = ConfigManager(config, PresetThemes())

        # Test English style
        en_style = config_manager.get_main_text_style(config.screenshots[0], "en")
        assert en_style.color == "#1A1A1A", "Color should be set in theme"
        assert en_style.font_family == "Helvetica"
        assert en_style.font_size == 120

        # Test Japanese style
        ja_style = config_manager.get_main_text_style(config.screenshots[0], "ja")
        assert ja_style.color == "#1A1A1A", "Color should be set in theme"
        assert ja_style.font_family == "Hiragino Sans"
        assert ja_style.font_size == 120

    @pytest.mark.integration
    def test_screenshot_overrides(self, temp_dir: Path) -> None:
        """Test screenshot-level style overrides."""
        # Create test image
        input_img = temp_dir / "test.png"
        Image.new("RGBA", (100, 100), color=(255, 255, 255, 255)).save(input_img)

        config_data = {
            "default_theme": "standard",
            "default_language": "en",
            "theme_styles": {
                "standard": {
                    "text_area_height": 500,
                    "background_color": "#FFFFFF",
                    "image_style": {"corner_radius": 0, "padding": 50},
                    "main_text_style": {
                        "font_family": "BaseFont",  # Direct value
                        "font_size": 100,  # Direct value
                        "color": "#000000",  # Direct value
                    },
                },
            },
            "screenshots": [
                {
                    "input_image": str(input_img),
                    "text": {"main_text": {"en": "Test"}},
                    "theme": "standard",
                    "main_text_style": {
                        "font_size": 80,  # Override font size at screenshot level
                    },
                }
            ],
        }

        # Save config temporarily for validation
        config_path = temp_dir / "temp_config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        validator = ConfigValidator()
        is_valid, config = validator.validate_config_file(str(config_path))
        assert is_valid is True
        assert config is not None
        config_manager = ConfigManager(config, PresetThemes())

        # Get theme
        theme = config_manager.get_theme_style(config.screenshots[0])

        # Theme values should be from standard theme
        assert theme.text_area_height == 500
        assert theme.background_color == "#FFFFFF"
        assert theme.image_style is not None
        assert theme.image_style.padding == 50
        assert theme.image_style.corner_radius == 0

        # Text style should include screenshot overrides
        main_style_en = config_manager.get_main_text_style(config.screenshots[0], "en")
        assert main_style_en.font_family == "BaseFont"  # From theme
        assert main_style_en.font_size == 80  # From screenshot override
        assert main_style_en.color == "#000000"  # From theme

    @pytest.mark.integration
    def test_specific_language_generation(self, temp_dir: Path) -> None:
        """Test generating screenshots for a specific language only."""
        # Create test image
        input_img = temp_dir / "test.png"
        Image.new("RGBA", (100, 100), color=(255, 255, 255, 255)).save(input_img)

        config_data = {
            "screenshots": [
                {
                    "input_image": str(input_img),
                    "text": {"main_text": {"en": "English", "ja": "日本語", "fr": "Français"}},
                }
            ]
        }

        # Save config temporarily for validation
        config_path = temp_dir / "temp_config.yml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        validator = ConfigValidator()
        is_valid, config = validator.validate_config_file(str(config_path))
        assert is_valid is True
        assert config is not None
        output_dir = temp_dir / "output"

        generator = ScreenshotGenerator(config=config, output_dir=output_dir, ui_reporter=ConsoleReporter())

        # Generate only French screenshots
        generated = generator.generate_all(language="fr")

        # Should only generate French
        assert len(generated) == 2  # 2 resolutions
        assert (output_dir / "fr").exists()
        assert not (output_dir / "en").exists()
        assert not (output_dir / "ja").exists()
