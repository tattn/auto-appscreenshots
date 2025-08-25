"""Tests for configuration validator."""

from pathlib import Path
from typing import Any

import yaml

from auto_appscreenshots.models import ScreenshotConfig
from auto_appscreenshots.validator import ConfigValidator


class TestConfigValidator:
    """Test ConfigValidator class."""

    def test_validate_missing_file(self, temp_dir: Path) -> None:
        """Test validation with missing configuration file."""
        validator = ConfigValidator()
        config_path = temp_dir / "nonexistent.yml"

        is_valid, config = validator.validate_config_file(str(config_path))

        assert is_valid is False
        assert config is None
        assert len(validator.errors) > 0
        assert "not found" in validator.errors[0]

    def test_validate_invalid_yaml(self, temp_dir: Path) -> None:
        """Test validation with invalid YAML syntax."""
        validator = ConfigValidator()
        config_path = temp_dir / "invalid.yml"

        # Write invalid YAML
        config_path.write_text("invalid: yaml: syntax: here")

        is_valid, config = validator.validate_config_file(str(config_path))

        assert is_valid is False
        assert config is None
        assert len(validator.errors) > 0

    def test_validate_valid_config(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation with valid configuration."""
        validator = ConfigValidator()
        config_path = temp_dir / "valid.yml"

        # Write valid config
        config_data: dict[str, Any] = {
            "screenshots": [{"input_image": str(sample_image), "text": {"main_text": {"en": "Test"}}}]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, config = validator.validate_config_file(str(config_path))

        assert is_valid is True
        assert config is not None
        assert isinstance(config, ScreenshotConfig)

    def test_validate_screenshot_missing_input(self, temp_dir: Path) -> None:
        """Test validation warns about missing input images."""
        validator = ConfigValidator(verbose=True)
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "screenshots": [{"input_image": "nonexistent.png", "text": {"main_text": {"en": "Test"}}}]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is True  # Warning, not error
        assert len(validator.warnings) > 0
        assert "Input image not found" in validator.warnings[0]

    def test_validate_invalid_theme(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation with invalid theme name."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "screenshots": [
                {"input_image": str(sample_image), "text": {"main_text": {"en": "Test"}}, "theme": "invalid_theme"}
            ]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is False
        assert len(validator.errors) > 0
        assert "Invalid theme" in validator.errors[0]

    def test_validate_empty_text(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation with empty text."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {"screenshots": [{"input_image": str(sample_image), "text": {}}]}
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is False
        assert len(validator.errors) > 0
        assert "Field required" in validator.errors[0]

    def test_validate_style_format_warning(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation warns about style format."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "screenshots": [
                {
                    "input_image": str(sample_image),
                    "text": {"main_text": {"en": "Test"}},
                    "main_text_style": {},  # Empty style
                }
            ]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is True
        assert len(validator.warnings) > 0
        assert "should have at least one property defined" in validator.warnings[0]

    def test_validate_theme_styles(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation of theme styles."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "theme_styles": {"invalid_theme": {"layout": {"padding": 50}}},
            "screenshots": [{"input_image": str(sample_image), "text": {"main_text": {"en": "Test"}}}],
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is True
        assert len(validator.warnings) > 0
        assert "does not match any preset theme" in validator.warnings[0]

    def test_validate_languages(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation of language configurations."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "languages": ["en", "ja", "fr"],
            "screenshots": [
                {
                    "input_image": str(sample_image),
                    "text": {
                        "main_text": {"en": "English", "ja": "Japanese"}
                        # Note: fr is configured but not used
                    },
                }
            ],
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is True
        assert len(validator.warnings) > 0
        # Should warn about fr being configured but not used
        assert "fr" in str(validator.warnings)

    def test_validate_duplicate_output_names(self, temp_dir: Path, sample_image: Path) -> None:
        """Test validation warns about duplicate output names."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        config_data: dict[str, Any] = {
            "screenshots": [
                {"input_image": str(sample_image), "text": {"main_text": {"en": "Test1"}}, "output_name": "duplicate"},
                {"input_image": str(sample_image), "text": {"main_text": {"en": "Test2"}}, "output_name": "duplicate"},
            ]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, _ = validator.validate_config_file(str(config_path))

        assert is_valid is True
        assert len(validator.warnings) > 0
        assert "Duplicate output_name" in validator.warnings[0]

    def test_validation_error_pydantic(self, temp_dir: Path) -> None:
        """Test validation with Pydantic validation error."""
        validator = ConfigValidator()
        config_path = temp_dir / "config.yml"

        # Invalid data type for font_size
        config_data: dict[str, Any] = {
            "screenshots": [
                {
                    "input_image": "test.png",
                    "text": {"main_text": {"en": "Test"}},
                    "main_text_style": {
                        "font_size": {
                            "default": "not_a_number"  # Should be int
                        }
                    },
                }
            ]
        }
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        is_valid, config = validator.validate_config_file(str(config_path))

        assert is_valid is False
        assert config is None
        assert len(validator.errors) > 0
