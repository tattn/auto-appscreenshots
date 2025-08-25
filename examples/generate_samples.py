"""Generate sample screenshots for testing."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from auto_appscreenshots.font_finder import FontFinder


def create_sample_screenshot(
    filename: str | Path,
    size: tuple[int, int] = (1290, 2796),  # iPhone 14 Pro Max
    bg_color: str = "#007AFF",
    text: str = "Sample",
    font_name: str = "Arial",
    font_weight: str = "normal",
) -> None:
    """Create a sample screenshot for testing."""
    image = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(image)

    # Load font using FontFinder
    font = FontFinder.load_font(font_name, 120, weight=font_weight)

    if not font:
        print(f"Warning: Could not load font '{font_name}'. Using fallback.")
        # Try fallback fonts
        for fallback_name in ["Arial", "Helvetica", "sans-serif"]:
            font = FontFinder.load_font(fallback_name, 120)
            if font:
                break

        if not font:
            # Last resort: use default font
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    draw.text((x, y), text, fill="white", font=font)  # type: ignore[attr-defined, unused-ignore]

    image.save(filename)
    print(f"Created: {filename}")


if __name__ == "__main__":
    screenshots_dir = Path("screenshots")

    # Define device sizes
    sizes = {
        "iphone": (1320, 2868),  # iPhone 15 Pro Max
        "ipad": (2064, 2752),  # iPad Pro 12.9"
    }

    # Define languages with appropriate fonts
    language_configs = {
        "ja": {
            "font": "Hiragino Sans",
            "weight": "normal",
            "texts": ["ホーム", "機能 1", "設定"],
        },
        "en": {
            "font": "Arial",
            "weight": "normal",
            "texts": ["HOME", "FEATURE 1", "SETTINGS"],
        },
        "zh-Hans": {
            "font": "STHeiti",
            "weight": "medium",
            "texts": ["主页", "功能 1", "设置"],
        },
    }

    # Define sample colors
    sample_colors = ["#007AFF", "#34C759", "#FF9500"]

    # Create directories and generate screenshots
    for lang, config in language_configs.items():
        lang_dir = screenshots_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)

        for i, (color, text) in enumerate(zip(sample_colors, config["texts"]), 1):
            for size in sizes.values():
                # Filename format: {index}_{widthxheight}.png
                filename = f"{i}_{size[0]}x{size[1]}.png"
                filepath = lang_dir / filename
                create_sample_screenshot(
                    filepath,
                    size=size,
                    bg_color=color,
                    text=text,
                    font_name=config["font"],
                    font_weight=config["weight"],
                )

    total_created = len(language_configs) * len(sample_colors) * len(sizes)
    print(f"\n✅ Created {total_created} sample screenshots in '{screenshots_dir}' directory")
