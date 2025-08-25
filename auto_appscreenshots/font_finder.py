"""Weight-based font finder using standard OpenType weight values."""

import logging
import os
from typing import Any

from PIL import ImageFont

logger = logging.getLogger(__name__)


class FontFinder:
    """Find and load fonts based on standard weight values (100-900)."""

    # Standard weight name to value mapping
    WEIGHT_MAP = {
        "thin": 100,
        "hairline": 100,
        "ultralight": 200,
        "extralight": 200,
        "light": 300,
        "normal": 400,
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "demibold": 600,
        "bold": 700,
        "extrabold": 800,
        "ultrabold": 800,
        "black": 900,
        "heavy": 900,
    }

    # Cache for TTC font mappings: font_path -> (weight, style) -> index
    _ttc_cache: dict[str, dict[tuple[int, str], int]] = {}

    @classmethod
    def load_font(
        cls, font_name: str, size: int, weight: str | None = None, style: str = "normal"
    ) -> ImageFont.FreeTypeFont | None:
        """Load font with specified weight and style.

        Args:
            font_name: Font family name or file path
            size: Font size in points
            weight: Font weight name or value (100-900)
            style: Font style ('normal', 'italic', or 'oblique')

        Returns:
            Loaded font or None if not found
        """
        # Convert weight to numeric value
        weight_value = cls._get_weight_value(weight)

        # Find font file
        font_path = cls._find_font_file(font_name, weight_value)
        if not font_path:
            logger.warning(f"Font '{font_name}' not found. Using default font.")
            return None

        # Load font based on file type
        if font_path.lower().endswith(".ttc"):
            return cls._load_ttc_font(font_path, size, weight_value, style)
        else:
            return cls._load_regular_font(font_path, size, weight_value)

    @classmethod
    def _get_weight_value(cls, weight: str | int | None) -> int:
        """Convert weight name to numeric value."""
        if weight is None:
            return 400  # Default to normal

        if isinstance(weight, int):
            return weight

        return cls.WEIGHT_MAP.get(weight.lower(), 400)

    @classmethod
    def _find_font_file(cls, font_name: str, weight_value: int | None = None) -> str | None:
        """Find font file by name using matplotlib, considering weight for multiple matches."""
        try:
            # Try matplotlib's findfont
            import matplotlib.font_manager as fm

            # Find all fonts with matching name
            matching_fonts = [font for font in fm.fontManager.ttflist if font.name.lower() == font_name.lower()]

            if matching_fonts:
                # If weight specified, find the closest match
                if weight_value is not None:
                    best_font = min(matching_fonts, key=lambda f: abs(int(f.weight) - weight_value))
                    logger.debug(f"Selected font with weight {best_font.weight} (target: {weight_value})")
                    return best_font.fname
                else:
                    # Return the first match if no weight specified
                    return matching_fonts[0].fname

            # Fallback to matplotlib's default search
            font_prop = fm.FontProperties(family=font_name)
            font_file = fm.findfont(font_prop)

            if font_file and os.path.exists(font_file):
                # Avoid fallback fonts
                if "DejaVu" not in font_file or "DejaVu" in font_name:
                    return font_file
        except Exception as e:
            logger.debug(f"Failed to find font using matplotlib: {e}")

        return None

    @classmethod
    def _load_ttc_font(cls, font_path: str, size: int, weight_value: int, style: str) -> ImageFont.FreeTypeFont | None:
        """Load font from TTC file using weight-based selection."""
        # Build cache if not exists
        if font_path not in cls._ttc_cache:
            cls._build_ttc_cache(font_path)

        # Find best matching font index
        cache = cls._ttc_cache.get(font_path, {})
        if not cache:
            # Fallback to first font if cache building failed
            return cls._load_font_at_index(font_path, size, 0)

        best_index = cls._find_best_match(cache, weight_value, style)
        return cls._load_font_at_index(font_path, size, best_index)

    @classmethod
    def _load_regular_font(cls, font_path: str, size: int, weight_value: int) -> ImageFont.FreeTypeFont | None:
        """Load regular TTF/OTF font."""
        try:
            font = ImageFont.truetype(font_path, size)

            # Try to apply weight for variable fonts
            try:
                font.set_variation_by_axes([weight_value])  # type: ignore[attr-defined, unused-ignore]
                logger.debug(f"Applied variable font weight: {weight_value}")
            except (AttributeError, OSError):
                # Not a variable font, which is fine
                pass

            return font
        except Exception as e:
            logger.error(f"Failed to load font {font_path}: {e}")
            return None

    @classmethod
    def _load_font_at_index(cls, font_path: str, size: int, index: int) -> ImageFont.FreeTypeFont | None:
        """Load font from TTC at specific index."""
        try:
            font = ImageFont.truetype(font_path, size, index=index)
            logger.debug(f"Loaded font from {os.path.basename(font_path)} at index {index}")
            return font
        except Exception as e:
            logger.error(f"Failed to load font at index {index}: {e}")
            return None

    @classmethod
    def _build_ttc_cache(cls, font_path: str) -> None:
        """Build weight/style mapping for TTC file."""
        try:
            from fontTools.ttLib import TTCollection  # type: ignore[import-untyped, unused-ignore]

            cls._ttc_cache[font_path] = {}
            ttc = TTCollection(font_path)

            for index, ttfont in enumerate(ttc):  # type: ignore[var-annotated, unused-ignore]
                weight = cls._get_font_weight(ttfont)  # type: ignore[arg-type, unused-ignore]
                style = cls._get_font_style(ttfont)  # type: ignore[arg-type, unused-ignore]

                # Store mapping: (weight, style) -> index
                key = (weight, style)
                cls._ttc_cache[font_path][key] = index

                logger.debug(f"TTC {os.path.basename(font_path)} [{index}]: weight={weight}, style={style}")
        except ImportError:
            logger.warning("fontTools not installed. TTC weight selection may not work correctly.")
            # Fallback: create simple mapping for common cases
            cls._ttc_cache[font_path] = {
                (400, "normal"): 0,  # Regular
                (700, "normal"): 1,  # Bold (common position)
            }
        except Exception as e:
            logger.error(f"Failed to analyze TTC file {font_path}: {e}")

    @classmethod
    def _get_font_weight(cls, ttfont: Any) -> int:
        """Extract weight value from TTFont object."""
        try:
            os2_table = ttfont.get("OS/2")
            if os2_table and hasattr(os2_table, "usWeightClass"):
                return int(os2_table.usWeightClass)  # type: ignore[no-any-return, unused-ignore]
        except Exception:
            pass
        return 400  # Default to normal

    @classmethod
    def _get_font_style(cls, ttfont: Any) -> str:
        """Extract style from TTFont object."""
        try:
            name_table = ttfont.get("name")
            if name_table:
                for record in name_table.names:
                    if record.nameID == 2:  # Subfamily name
                        subfamily = record.toUnicode().lower()
                        if "italic" in subfamily or "cursiva" in subfamily:
                            return "italic"
                        elif "oblique" in subfamily or "oblicua" in subfamily:
                            return "oblique"
        except Exception:
            pass
        return "normal"

    @classmethod
    def _find_best_match(cls, cache: dict[tuple[int, str], int], target_weight: int, target_style: str) -> int:
        """Find best matching font index from cache."""
        # Try exact match
        key = (target_weight, target_style)
        if key in cache:
            return cache[key]

        # Find closest weight with matching style
        best_index = 0
        min_diff = float("inf")

        for (weight, style), index in cache.items():
            if style == target_style:
                diff = abs(weight - target_weight)
                if diff < min_diff:
                    min_diff = diff
                    best_index = index

        # If no style match found, find closest weight ignoring style
        if min_diff == float("inf"):
            for (weight, _), index in cache.items():
                diff = abs(weight - target_weight)
                if diff < min_diff:
                    min_diff = diff
                    best_index = index

        return best_index
