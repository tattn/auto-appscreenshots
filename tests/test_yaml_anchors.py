"""Tests for YAML anchor and alias functionality."""

import yaml

from auto_appscreenshots.config_manager import ConfigManager
from auto_appscreenshots.models import ScreenshotConfig
from auto_appscreenshots.preset_themes import PresetThemes


class TestYamlAnchorsAndAliases:
    """Test YAML anchors and aliases for configuration reuse."""

    def test_basic_anchor_alias(self) -> None:
        """Test basic anchor and alias functionality."""
        yaml_config = """
_fonts: &fonts
  ja: "Hiragino Sans"
  en: "Helvetica"

theme_styles:
  standard:
    main_text_style:
      font_family: *fonts
      font_size: 120
    sub_text_style:
      font_family: *fonts
      font_size: 80

screenshots:
  - input_image: "test.png"
    text:
      main_text: {en: "Test"}
"""
        config_data = yaml.safe_load(yaml_config)

        # Verify both styles have the same font configuration
        assert config_data["theme_styles"]["standard"]["main_text_style"]["font_family"] == {
            "ja": "Hiragino Sans",
            "en": "Helvetica",
        }
        assert config_data["theme_styles"]["standard"]["sub_text_style"]["font_family"] == {
            "ja": "Hiragino Sans",
            "en": "Helvetica",
        }

        # Test with Pydantic models
        config = ScreenshotConfig(**config_data)
        assert config is not None

    def test_merge_with_overrides(self) -> None:
        """Test YAML merge with property overrides."""
        yaml_config = """
_common_text: &common_text
  color: "#1A1A1A"
  shadow: true
  shadow_blur: 5

theme_styles:
  standard:
    main_text_style:
      <<: *common_text
      font_size: 120
    sub_text_style:
      <<: *common_text
      font_size: 80
      color: "#666666"  # Override color
      shadow: false      # Override shadow

screenshots:
  - input_image: "test.png"
    text:
      main_text: {en: "Test"}
"""
        config_data = yaml.safe_load(yaml_config)

        # Check main_text_style inherited common properties
        main_style = config_data["theme_styles"]["standard"]["main_text_style"]
        assert main_style["color"] == "#1A1A1A"
        assert main_style["shadow"] is True
        assert main_style["shadow_blur"] == 5
        assert main_style["font_size"] == 120

        # Check sub_text_style overrides
        sub_style = config_data["theme_styles"]["standard"]["sub_text_style"]
        assert sub_style["color"] == "#666666"  # Overridden
        assert sub_style["shadow"] is False  # Overridden
        assert sub_style["shadow_blur"] == 5  # Inherited
        assert sub_style["font_size"] == 80

        # Test with Pydantic models
        config = ScreenshotConfig(**config_data)
        config_manager = ConfigManager(config, PresetThemes())

        main_style_obj = config_manager.get_main_text_style(config.screenshots[0], "en")
        sub_style_obj = config_manager.get_sub_text_style(config.screenshots[0], "en")

        assert main_style_obj.color == "#1A1A1A"
        assert main_style_obj.shadow is True
        assert sub_style_obj.color == "#666666"
        assert sub_style_obj.shadow is False

    def test_nested_anchors(self) -> None:
        """Test nested anchors and aliases."""
        yaml_config = """
_fonts: &fonts
  ja: "Hiragino Sans"
  en: "Helvetica"

_shadow_config: &shadow
  shadow: true
  shadow_color: "#00000040"
  shadow_offset: [3, 3]
  shadow_blur: 5

_main_base: &main_base
  font_family: *fonts
  <<: *shadow
  font_size: 120

theme_styles:
  standard:
    main_text_style: *main_base
    sub_text_style:
      font_family: *fonts
      font_size: 80
      shadow: false

screenshots:
  - input_image: "test.png"
    text:
      main_text:
        en: "Test"
        ja: "テスト"
"""
        config_data = yaml.safe_load(yaml_config)

        # Verify nested references work
        main_style = config_data["theme_styles"]["standard"]["main_text_style"]
        assert main_style["font_family"]["ja"] == "Hiragino Sans"
        assert main_style["shadow"] is True
        assert main_style["shadow_blur"] == 5
        assert main_style["font_size"] == 120

        # Test with Pydantic models
        config = ScreenshotConfig(**config_data)
        config_manager = ConfigManager(config, PresetThemes())

        # Test that styles are correctly applied
        style_ja = config_manager.get_main_text_style(config.screenshots[0], "ja")
        assert style_ja.font_family == "Hiragino Sans"
        assert style_ja.shadow is True
        assert style_ja.shadow_blur == 5
        assert style_ja.font_size == 120

    def test_anchor_with_direct_values(self) -> None:
        """Test anchors combined with direct values."""
        yaml_config = """
_fonts: &fonts
  ja: "Hiragino Sans"
  en: "Helvetica"

theme_styles:
  standard:
    main_text_style:
      font_family: *fonts
      font_size: 120      # Direct value
      color: "#1A1A1A"    # Direct value
    sub_text_style:
      font_family: *fonts
      font_size: 80       # Direct value
      color: "#666666"    # Direct value

screenshots:
  - input_image: "test.png"
    text:
      main_text:
        en: "Test"
        ja: "テスト"
"""
        config_data = yaml.safe_load(yaml_config)
        config = ScreenshotConfig(**config_data)
        config_manager = ConfigManager(config, PresetThemes())

        # Test English
        style_en = config_manager.get_main_text_style(config.screenshots[0], "en")
        assert style_en.font_family == "Helvetica"
        assert style_en.font_size == 120
        assert style_en.color == "#1A1A1A"

        # Test Japanese
        style_ja = config_manager.get_main_text_style(config.screenshots[0], "ja")
        assert style_ja.font_family == "Hiragino Sans"
        assert style_ja.font_size == 120
        assert style_ja.color == "#1A1A1A"
