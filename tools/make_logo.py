"""Generate the SIA dashboard app logo and favicon.

The app icon is rendered at 4x resolution and downsampled with LANCZOS so the
rounded geometry stays crisp at both browser and favicon sizes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

PRIMARY = "#2F39A9"
SECONDARY = "#2E6FA0"
ACCENT = "#49A4BB"
HIGHLIGHT = "#15D8B3"
DARK_NAVY = "#080B24"


def _rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _gradient(size: tuple[int, int], colors: list[str], *, horizontal: bool = True) -> Image.Image:
    """Build a multi-stop RGBA gradient using only the brand palette."""

    width, height = size
    stops = np.linspace(0.0, 1.0, len(colors))
    axis = np.linspace(0.0, 1.0, width if horizontal else height)
    rgb = np.asarray([_rgb(color) for color in colors], dtype=np.float32)
    image = np.empty((height, width, 4), dtype=np.uint8)
    for channel in range(3):
        values = np.interp(axis, stops, rgb[:, channel])
        image[:, :, channel] = values[np.newaxis, :] if horizontal else values[:, np.newaxis]
    image[:, :, 3] = 255
    return Image.fromarray(image, mode="RGBA")


def _rounded_mask(size: tuple[int, int], box: tuple[int, int, int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def _composite_gradient(canvas: Image.Image, mask: Image.Image, colors: list[str], *, horizontal: bool = True) -> None:
    canvas.alpha_composite(Image.composite(_gradient(canvas.size, colors, horizontal=horizontal), Image.new("RGBA", canvas.size), mask))


def _shadow(canvas: Image.Image, mask: Image.Image, blur: int, alpha: int) -> None:
    shadow = mask.filter(ImageFilter.GaussianBlur(blur))
    shadow = shadow.point(lambda value: value * alpha // 255)
    shadow_layer = Image.new("RGBA", canvas.size, (*_rgb(DARK_NAVY), 0))
    shadow_layer.putalpha(shadow)
    canvas.alpha_composite(shadow_layer)


def draw_app_logo(size: int = 1024, scale: int = 4) -> Image.Image:
    working_size = size * scale
    canvas = Image.new("RGBA", (working_size, working_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    outer = (112 * scale, 112 * scale, 912 * scale, 912 * scale)
    outer_mask = _rounded_mask(canvas.size, outer, 220 * scale)
    _shadow(canvas, outer_mask, 34 * scale, 150)
    _composite_gradient(canvas, outer_mask, [PRIMARY, SECONDARY, ACCENT, HIGHLIGHT], horizontal=True)

    inner = (138 * scale, 138 * scale, 886 * scale, 886 * scale)
    inner_mask = _rounded_mask(canvas.size, inner, 194 * scale)
    inner_fill = Image.new("RGBA", canvas.size, (*_rgb(DARK_NAVY), 246))
    canvas.alpha_composite(Image.composite(inner_fill, Image.new("RGBA", canvas.size), inner_mask))

    # A restrained inner glow keeps the icon dimensional without adding new hues.
    glow_mask = _rounded_mask(canvas.size, (154 * scale, 154 * scale, 870 * scale, 870 * scale), 182 * scale)
    glow = Image.new("RGBA", canvas.size, (*_rgb(SECONDARY), 0))
    glow.putalpha(glow_mask.filter(ImageFilter.GaussianBlur(26 * scale)).point(lambda value: value // 7))
    canvas.alpha_composite(glow)

    # Rounded bars establish the rising analytics motif.
    bars = [
        (238, 594, 336, 770, [PRIMARY, SECONDARY]),
        (378, 500, 476, 770, [SECONDARY, ACCENT]),
        (518, 386, 616, 770, [ACCENT, HIGHLIGHT]),
        (658, 264, 756, 770, [PRIMARY, HIGHLIGHT]),
    ]
    for left, top, right, bottom, colors in bars:
        mask = _rounded_mask(canvas.size, (left * scale, top * scale, right * scale, bottom * scale), 30 * scale)
        _composite_gradient(canvas, mask, colors, horizontal=False)

    # A soft baseline makes the chart read as one deliberate mark.
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((216 * scale, 764 * scale, 780 * scale, 804 * scale), radius=20 * scale, fill=(*_rgb(HIGHLIGHT), 220))

    points = [(264 * scale, 614 * scale), (420 * scale, 536 * scale), (566 * scale, 438 * scale), (716 * scale, 318 * scale)]
    glow_line = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_line)
    glow_draw.line(points, fill=(*_rgb(ACCENT), 150), width=32 * scale, joint="curve")
    glow_line = glow_line.filter(ImageFilter.GaussianBlur(16 * scale))
    canvas.alpha_composite(glow_line)
    draw = ImageDraw.Draw(canvas)
    draw.line(points, fill=(*_rgb(HIGHLIGHT), 255), width=18 * scale, joint="curve")
    for x, y in points[:-1]:
        draw.ellipse((x - 18 * scale, y - 18 * scale, x + 18 * scale, y + 18 * scale), fill=(*_rgb(ACCENT), 255), outline=(*_rgb(HIGHLIGHT), 255), width=6 * scale)

    # The final node is the focal data point; the small four-point spark adds lift.
    node_x, node_y = points[-1]
    endpoint_glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    endpoint_draw = ImageDraw.Draw(endpoint_glow)
    endpoint_draw.ellipse((node_x - 60 * scale, node_y - 60 * scale, node_x + 60 * scale, node_y + 60 * scale), fill=(*_rgb(HIGHLIGHT), 165))
    canvas.alpha_composite(endpoint_glow.filter(ImageFilter.GaussianBlur(22 * scale)))
    draw.ellipse((node_x - 34 * scale, node_y - 34 * scale, node_x + 34 * scale, node_y + 34 * scale), fill=(*_rgb(HIGHLIGHT), 255), outline=(*_rgb(HIGHLIGHT), 255), width=9 * scale)
    draw.ellipse((node_x - 12 * scale, node_y - 12 * scale, node_x + 12 * scale, node_y + 12 * scale), fill=(*_rgb(HIGHLIGHT), 255))
    spark = [(790, 194), (806, 234), (846, 250), (806, 266), (790, 308), (774, 266), (734, 250), (774, 234)]
    draw.polygon([(x * scale, y * scale) for x, y in spark], fill=(*_rgb(HIGHLIGHT), 255))
    draw.ellipse((782 * scale, 242 * scale, 798 * scale, 258 * scale), fill=(*_rgb(SECONDARY), 255))

    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    app_logo = draw_app_logo()
    app_logo.save(ROOT / "logo1.png", format="PNG", optimize=True)
    app_logo.resize((256, 256), Image.Resampling.LANCZOS).save(ASSETS / "logo1_small.png", format="PNG", optimize=True)

    print(f"Created {ROOT / 'logo1.png'}")
    print(f"Created {ASSETS / 'logo1_small.png'}")


if __name__ == "__main__":
    main()
