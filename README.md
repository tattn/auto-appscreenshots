# auto-appscreenshots

A tool for generating App Store Connect screenshots.

<img width="240" alt="01_home_en_1320x2868" src="https://github.com/user-attachments/assets/2eeddb54-175f-4c30-95b3-5244d1f1743b" /> <img width="240" alt="02_feature_en_1320x2868" src="https://github.com/user-attachments/assets/ef3d5afa-34e0-4664-b9ff-55418bd9dc27" /> <img width="240" alt="03_settings_en_1320x2868" src="https://github.com/user-attachments/assets/4fa726c7-1476-49fd-8e77-420707931f27" />

## Features

- Generate App Store Connect screenshots
- Multi-language support
- Multiple resolution outputs
- Preset themes
- YAML configuration file for metadata management
- Customizable fonts, sizes, colors, and positions

## Installation

### Using uv (Recommended)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
uv sync

# Run the tool
uv run appscreenshots -c examples/config.yml
```

<details>
<summary><h3>Using pip</h3></summary>

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

</details>

## Quick Start

### 1. Generate Sample Images (for testing)

```bash
cd examples
uv run python generate_samples.py
```

### 2. Create Configuration File

Create a `config.yml` file to define your screenshot settings:

```yaml
default_language: en
default_theme: standard

# Define shared configuration using YAML anchors
_fonts: &fonts
  ja: "Hiragino Sans"
  en: "Helvetica Neue"

# Theme style customizations
theme_styles:
    main_text_style:
      font_family: *fonts  # Use anchor reference
      font_weight: "bold"
      font_size: 120
      color: "#1A1A1A"
    
    sub_text_style:
      font_family: *fonts
      font_size: 80
      color: "#666666"

# Screenshot definitions
screenshots:
  - input_image: "./screenshots/{lang}/home_{width}x{height}.png"
    output_name: "01_home_{lang}_{width}x{height}"
    text:
      main_text:
        ja: "シンプルで使いやすい"
        en: "Simple and Easy to Use"
      sub_text:
        ja: "直感的なインターフェース"
        en: "Intuitive Interface"
  
  - input_image: "./screenshots/{lang}/feature_{width}x{height}.png"
    output_name: "02_feature_{lang}_{width}x{height}"
    theme: standard_inverted
    text:
      main_text:
        ja: "パワフルな機能"
        en: "Powerful Features"
      sub_text:
        ja: "プロフェッショナルな結果"
        en: "Professional Results"
```

### 3. Generate Screenshots

```bash
# Basic usage (Generate all languages)
uv run appscreenshots -c config.yml

# Specify output directory
uv run appscreenshots -c config.yml -o ./custom_output

# Validate configuration only
uv run appscreenshots -c config.yml --validate-only

# Enable verbose logging
uv run appscreenshots -c config.yml -v

# Generate for specific language
uv run appscreenshots -c config.yml -l ja
```

## Configuration Options

To see all available configuration options with descriptions, run:

```bash
uv run appscreenshots --show-options
```

## Development

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest tests/

# Run linter
uv run ruff check .

# Type checking
uv run mypy auto_appscreenshots
```
