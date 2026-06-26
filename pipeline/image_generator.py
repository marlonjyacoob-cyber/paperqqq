"""
Offline image generator using Pillow.
Creates cinematic dark-gradient frames with styled text overlays —
the style used by many successful faceless YouTube channels.
"""

import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

WIDTH, HEIGHT = 1920, 1080

# Cinematic color palettes  [bg_top, bg_bottom, accent, text]
PALETTES = [
    [(10, 10, 30),   (30, 15, 50),   (180, 100, 255), (230, 210, 255)],  # deep purple
    [(5,  15, 35),   (15, 35, 60),   (0,  180, 255),  (200, 235, 255)],  # dark blue
    [(30, 10, 10),   (55, 20, 15),   (255, 120, 50),  (255, 230, 200)],  # dark red/orange
    [(10, 25, 15),   (15, 45, 25),   (50,  220, 120), (200, 255, 220)],  # dark green
    [(20, 20, 20),   (40, 35, 25),   (255, 210, 50),  (255, 245, 200)],  # dark gold
]


def _gradient_background(draw: ImageDraw, palette: list) -> None:
    top, bottom = palette[0], palette[1]
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


def _add_grid_lines(draw: ImageDraw, palette: list) -> None:
    accent = palette[2]
    line_color = (*accent, 18)
    for x in range(0, WIDTH, 120):
        draw.line([(x, 0), (x, HEIGHT)], fill=line_color[:3], width=1)
    for y in range(0, HEIGHT, 120):
        draw.line([(0, y), (WIDTH, y)], fill=line_color[:3], width=1)


def _add_accent_bar(draw: ImageDraw, palette: list, y_pos: int) -> None:
    accent = palette[2]
    draw.rectangle([(140, y_pos), (WIDTH - 140, y_pos + 4)], fill=accent)


def _wrap_text(text: str, max_chars: int = 52) -> list[str]:
    return textwrap.wrap(text, width=max_chars)


def generate_frame(text: str, segment_num: int, output_path: str, total: int) -> str:
    palette = PALETTES[segment_num % len(PALETTES)]
    accent_color = palette[2]
    text_color = palette[3]

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    _gradient_background(draw, palette)
    _add_grid_lines(draw, palette)

    # Vignette overlay
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for i in range(300):
        alpha = int(160 * (i / 300) ** 2)
        vdraw.rectangle([i, i, WIDTH - i, HEIGHT - i], outline=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Segment counter dots
    dot_y = 80
    dot_spacing = 28
    dot_start_x = WIDTH // 2 - (total * dot_spacing) // 2
    for i in range(total):
        color = accent_color if i == segment_num else (80, 80, 80)
        r = 7 if i == segment_num else 5
        cx = dot_start_x + i * dot_spacing
        draw.ellipse([cx - r, dot_y - r, cx + r, dot_y + r], fill=color)

    # Accent bar above text
    text_block_y = 320
    _add_accent_bar(draw, palette, text_block_y - 30)

    # Main text — try to load a font, fall back to default
    font_size = 72
    small_font_size = 36
    try:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        font = None
        small_font = None
        for fp in font_paths:
            if Path(fp).exists():
                font = ImageFont.truetype(fp, font_size)
                small_font = ImageFont.truetype(fp, small_font_size)
                break
        if font is None:
            font = ImageFont.load_default()
            small_font = font
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    lines = _wrap_text(text, max_chars=48)
    line_height = font_size + 18
    total_text_h = len(lines) * line_height
    y = (HEIGHT - total_text_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        # shadow
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0), font=font)
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_height

    # Bottom label
    label = "GAS PIPELINE SECRETS"
    bbox = draw.textbbox((0, 0), label, font=small_font)
    lw = bbox[2] - bbox[0]
    draw.text(((WIDTH - lw) // 2, HEIGHT - 90), label, fill=accent_color, font=small_font)

    _add_accent_bar(draw, palette, HEIGHT - 105)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def generate_visuals(segments: list[dict], work_dir: str) -> list[str]:
    image_paths = []
    total = len(segments)
    for i, seg in enumerate(segments):
        path = os.path.join(work_dir, "images", f"segment_{i:03d}.png")
        print(f"  🖼️  Frame {i + 1}/{total}...")
        generate_frame(seg["text"], i, path, total)
        image_paths.append(path)
    return image_paths
