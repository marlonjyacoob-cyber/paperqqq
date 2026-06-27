"""
Mason's Dream Adventure - Animated YouTube Video Generator
3-minute animated story about Mason the astronaut dreamer
"""

import os
import math
import random
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ── Settings ──────────────────────────────────────────────────────────────────
W, H   = 1920, 1080
FPS    = 24
OUTDIR = "/home/user/paperqqq/mason_video/frames"
REF    = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/1425d1c0-IMG_5348.jpeg"
VIDEO  = "/home/user/paperqqq/mason_video/mason_dream_adventure.mp4"

os.makedirs(OUTDIR, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_text_centered(draw, text, y, font, fill=(255, 255, 255), shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if shadow:
        draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=fill)


def draw_wrapped_text(draw, text, y_center, font, fill=(255, 255, 255), max_width=1600):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = font.size + 10
    total_h = len(lines) * line_h
    y = y_center - total_h // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


def make_star_field(count=300, seed=42):
    rng = random.Random(seed)
    stars = [(rng.randint(0, W), rng.randint(0, H),
              rng.uniform(0.5, 2.5), rng.uniform(0.4, 1.0)) for _ in range(count)]
    return stars


def draw_stars(draw, stars, alpha_mult=1.0, twinkle_offset=0):
    for i, (x, y, r, base_a) in enumerate(stars):
        twinkle = 0.7 + 0.3 * math.sin((twinkle_offset + i * 0.7) * 0.15)
        a = int(min(255, base_a * alpha_mult * twinkle * 255))
        cr = int(r)
        draw.ellipse([x - cr, y - cr, x + cr, y + cr], fill=(255, 255, 220, a))


def deep_space_bg(t_frac=0.0):
    """Dark gradient space background."""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    r_top, g_top, b_top = 5, 5, 20
    r_bot, g_bot, b_bot = 15, 5, 40
    for row in range(H):
        f = row / H
        arr[row, :, 0] = int(r_top + (r_bot - r_top) * f)
        arr[row, :, 1] = int(g_top + (g_bot - g_top) * f)
        arr[row, :, 2] = int(b_top + (b_bot - b_top) * f)
    return Image.fromarray(arr, 'RGB')


def dream_bg():
    """Soft purple/blue dreamy gradient."""
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        f = row / H
        arr[row, :, 0] = int(60 + 80 * f)
        arr[row, :, 1] = int(20 + 40 * f)
        arr[row, :, 2] = int(100 + 100 * f)
    return Image.fromarray(arr, 'RGB')


def draw_planet(img, cx, cy, radius, color, ring=False, ring_color=None):
    draw = ImageDraw.Draw(img, 'RGBA')
    # Glow
    for i in range(20, 0, -1):
        ga = int(30 * i / 20)
        gr = radius + i * 3
        draw.ellipse([cx - gr, cy - gr, cx + gr, cy + gr],
                     fill=(*color[:3], ga))
    # Body
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    # Highlight
    hr = radius // 3
    draw.ellipse([cx - radius + 10, cy - radius + 10,
                  cx - radius + 10 + hr, cy - radius + 10 + hr],
                 fill=(255, 255, 255, 60))
    if ring and ring_color:
        rw = int(radius * 1.8)
        rh = int(radius * 0.3)
        draw.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                     outline=(*ring_color, 180), width=8)


def draw_rocket(img, cx, cy, scale=1.0, angle=0):
    """Draw a simple cartoon rocket."""
    draw = ImageDraw.Draw(img, 'RGBA')
    s = scale
    # Body
    body_pts = [
        (cx, cy - int(60 * s)),
        (cx + int(20 * s), cy + int(30 * s)),
        (cx - int(20 * s), cy + int(30 * s)),
    ]
    draw.polygon(body_pts, fill=(220, 60, 60, 240))
    # Window
    draw.ellipse([cx - int(10 * s), cy - int(15 * s),
                  cx + int(10 * s), cy + int(5 * s)], fill=(150, 220, 255, 220))
    # Fins left
    draw.polygon([
        (cx - int(20 * s), cy + int(10 * s)),
        (cx - int(40 * s), cy + int(40 * s)),
        (cx - int(20 * s), cy + int(30 * s)),
    ], fill=(200, 40, 40, 220))
    # Fins right
    draw.polygon([
        (cx + int(20 * s), cy + int(10 * s)),
        (cx + int(40 * s), cy + int(40 * s)),
        (cx + int(20 * s), cy + int(30 * s)),
    ], fill=(200, 40, 40, 220))
    # Flame
    for fi in range(3):
        fx = cx + random.randint(-8, 8) * int(s)
        fy_end = cy + int((50 + fi * 15) * s)
        flame_c = [(255, 200, 50, 200), (255, 120, 20, 180), (255, 80, 0, 150)][fi]
        draw.polygon([
            (cx - int(8 * s), cy + int(30 * s)),
            (cx + int(8 * s), cy + int(30 * s)),
            (fx, fy_end),
        ], fill=flame_c)


def draw_astronaut(img, cx, cy, scale=1.0, wave=False, frame=0):
    """Draw a simple cartoon astronaut boy."""
    draw = ImageDraw.Draw(img, 'RGBA')
    s = scale

    # Body suit
    draw.ellipse([cx - int(30 * s), cy - int(20 * s),
                  cx + int(30 * s), cy + int(40 * s)],
                 fill=(220, 220, 240, 255))
    # Head / helmet
    draw.ellipse([cx - int(28 * s), cy - int(65 * s),
                  cx + int(28 * s), cy - int(5 * s)],
                 fill=(200, 215, 240, 255))
    # Visor
    draw.ellipse([cx - int(18 * s), cy - int(58 * s),
                  cx + int(18 * s), cy - int(18 * s)],
                 fill=(80, 180, 255, 200))
    # Face
    draw.ellipse([cx - int(10 * s), cy - int(48 * s),
                  cx + int(10 * s), cy - int(30 * s)],
                 fill=(255, 220, 190, 255))
    # Eyes
    draw.ellipse([cx - int(7 * s), cy - int(46 * s),
                  cx - int(3 * s), cy - int(42 * s)], fill=(30, 30, 30, 255))
    draw.ellipse([cx + int(3 * s), cy - int(46 * s),
                  cx + int(7 * s), cy - int(42 * s)], fill=(30, 30, 30, 255))
    # Smile
    draw.arc([cx - int(6 * s), cy - int(42 * s),
              cx + int(6 * s), cy - int(34 * s)], 0, 180, fill=(30, 30, 30, 200), width=2)

    # Hair (long black hair peeking out)
    hair_pts = [
        (cx - int(26 * s), cy - int(12 * s)),
        (cx - int(35 * s), cy + int(10 * s)),
        (cx - int(30 * s), cy + int(20 * s)),
        (cx - int(25 * s), cy + int(10 * s)),
    ]
    draw.polygon(hair_pts, fill=(20, 15, 15, 220))
    hair_pts_r = [
        (cx + int(26 * s), cy - int(12 * s)),
        (cx + int(35 * s), cy + int(10 * s)),
        (cx + int(30 * s), cy + int(20 * s)),
        (cx + int(25 * s), cy + int(10 * s)),
    ]
    draw.polygon(hair_pts_r, fill=(20, 15, 15, 220))

    # Arms
    wave_offset = int(10 * math.sin(frame * 0.2) * s) if wave else 0
    # Left arm
    draw.ellipse([cx - int(50 * s), cy - int(5 * s) + wave_offset,
                  cx - int(30 * s), cy + int(15 * s) + wave_offset],
                 fill=(220, 220, 240, 255))
    # Right arm (waving)
    if wave:
        draw.ellipse([cx + int(30 * s), cy - int(20 * s) - wave_offset,
                      cx + int(50 * s), cy - int(0 * s) - wave_offset],
                     fill=(220, 220, 240, 255))
    else:
        draw.ellipse([cx + int(30 * s), cy - int(5 * s),
                      cx + int(50 * s), cy + int(15 * s)],
                     fill=(220, 220, 240, 255))

    # Legs
    draw.ellipse([cx - int(25 * s), cy + int(30 * s),
                  cx - int(5 * s), cy + int(70 * s)], fill=(220, 220, 240, 255))
    draw.ellipse([cx + int(5 * s), cy + int(30 * s),
                  cx + int(25 * s), cy + int(70 * s)], fill=(220, 220, 240, 255))
    # Boots
    draw.ellipse([cx - int(28 * s), cy + int(60 * s),
                  cx - int(2 * s), cy + int(78 * s)], fill=(60, 60, 80, 255))
    draw.ellipse([cx + int(2 * s), cy + int(60 * s),
                  cx + int(28 * s), cy + int(78 * s)], fill=(60, 60, 80, 255))
    # Flag / backpack
    draw.rectangle([cx + int(28 * s), cy - int(10 * s),
                    cx + int(38 * s), cy + int(15 * s)], fill=(180, 180, 200, 255))


def draw_moon(img, cx, cy, radius):
    draw = ImageDraw.Draw(img, 'RGBA')
    # Glow
    for i in range(15, 0, -1):
        ga = int(20 * i / 15)
        gr = radius + i * 4
        draw.ellipse([cx - gr, cy - gr, cx + gr, cy + gr],
                     fill=(255, 255, 200, ga))
    # Moon body
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=(240, 235, 200, 255))
    # Craters
    for (ox, oy, cr) in [(-20, 15, 12), (25, -20, 8), (-10, -30, 6), (30, 20, 5)]:
        draw.ellipse([cx + ox - cr, cy + oy - cr, cx + ox + cr, cy + oy + cr],
                     fill=(210, 205, 170, 255))


def draw_earth(img, cx, cy, radius):
    draw = ImageDraw.Draw(img, 'RGBA')
    # Atmosphere glow
    for i in range(20, 0, -1):
        ga = int(25 * i / 20)
        gr = radius + i * 3
        draw.ellipse([cx - gr, cy - gr, cx + gr, cy + gr],
                     fill=(100, 150, 255, ga))
    # Ocean
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                 fill=(30, 80, 200, 255))
    # Continents (rough blobs)
    draw.ellipse([cx - 20, cy - 30, cx + 40, cy + 20], fill=(50, 150, 60, 255))
    draw.ellipse([cx - 40, cy + 5, cx - 5, cy + 45], fill=(50, 150, 60, 255))
    draw.ellipse([cx + 15, cy + 20, cx + 50, cy + 55], fill=(50, 150, 60, 255))


def draw_galaxy_cloud(img, cx, cy, w, h, color, alpha=60):
    arr = np.array(img)
    # Simple gaussian blob
    for dy in range(-h, h):
        for dx in range(-w, w):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < W and 0 <= ny < H:
                dist = math.sqrt((dx / w) ** 2 + (dy / h) ** 2)
                if dist < 1.0:
                    a = int(alpha * (1 - dist) ** 2)
                    for c in range(3):
                        arr[ny, nx, c] = min(255, arr[ny, nx, c] + int(color[c] * a / 255))
    return Image.fromarray(arr, 'RGB')


def ken_burns(base_img, t, zoom_start=1.0, zoom_end=1.08, pan_x=0, pan_y=0):
    """Smooth slow zoom / pan on a still image."""
    zoom = zoom_start + (zoom_end - zoom_start) * t
    new_w = int(W * zoom)
    new_h = int(H * zoom)
    scaled = base_img.resize((new_w, new_h), Image.LANCZOS)
    ox = int((new_w - W) / 2 + pan_x * t * (new_w - W) / 2)
    oy = int((new_h - H) / 2 + pan_y * t * (new_h - H) / 2)
    ox = max(0, min(new_w - W, ox))
    oy = max(0, min(new_h - H, oy))
    return scaled.crop((ox, oy, ox + W, oy + H))


def crossfade(img_a, img_b, t):
    a = img_a.convert('RGBA')
    b = img_b.convert('RGBA')
    a_arr = np.array(a, dtype=float)
    b_arr = np.array(b, dtype=float)
    blend = ((1 - t) * a_arr + t * b_arr).astype(np.uint8)
    return Image.fromarray(blend, 'RGBA').convert('RGB')


def save_frame(img, n):
    img.convert('RGB').save(os.path.join(OUTDIR, f"frame_{n:06d}.jpg"), quality=92)


# ── Reference image ────────────────────────────────────────────────────────────
print("Loading reference image...")
ref_img = Image.open(REF).convert('RGB')
ref_img = ref_img.resize((W, H), Image.LANCZOS)

STARS = make_star_field(400, seed=7)
FONT_TITLE  = load_font(72)
FONT_SUB    = load_font(44)
FONT_NARR   = load_font(38)
FONT_SMALL  = load_font(28)

frame_n = 0


def advance(img):
    global frame_n
    save_frame(img, frame_n)
    frame_n += 1


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 1 — Title card + Mason's bedroom  (0:00 – 0:30)  30 s  = 720 frames
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 1: Bedroom / Title...")
SCENE1_FRAMES = FPS * 30

for f in range(SCENE1_FRAMES):
    t = f / SCENE1_FRAMES

    # Ken Burns on bedroom image
    img = ken_burns(ref_img, t, zoom_start=1.0, zoom_end=1.06, pan_x=0.1, pan_y=0.05)

    # Dark overlay for title card at start
    if f < FPS * 5:
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, int(180 * (1 - f / (FPS * 5)))))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay).convert('RGB')

    draw = ImageDraw.Draw(img)

    # Title card (first 4 seconds)
    if f < FPS * 4:
        fade = min(1.0, f / (FPS * 0.8))
        # Title
        draw_text_centered(draw, "Mason's Dream Adventure",
                           H // 2 - 60, FONT_TITLE,
                           fill=(255, 240, 100, int(255 * fade)))
        draw_text_centered(draw, "A Story About Dreaming Big",
                           H // 2 + 30, FONT_SUB,
                           fill=(200, 220, 255, int(220 * fade)))

    # Narration subtitle (after title card)
    if FPS * 5 <= f < FPS * 28:
        narr_t = (f - FPS * 5) / (FPS * 23)
        if narr_t < 0.35:
            narr = "Every night, six-year-old Mason would snuggle into his cozy bed..."
        elif narr_t < 0.65:
            narr = "His room was full of rocket posters and dreams of the stars above."
        else:
            narr = "As his eyes grew heavy, something magical was about to begin..."

        fade = min(1.0, min(narr_t * 8, (1 - narr_t) * 8))
        draw_wrapped_text(draw, narr, H - 120, FONT_NARR,
                          fill=(255, 255, 255, int(230 * fade)))

    # Fade in from black at very start
    if f < FPS * 1:
        black = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - f / (FPS * 1)))))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, black).convert('RGB')

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 2 — Stars begin to swirl / Dream transition  (0:30 – 1:00)  30 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 2: Dream transition...")
SCENE2_FRAMES = FPS * 30

for f in range(SCENE2_FRAMES):
    t = f / SCENE2_FRAMES

    # Blend from bedroom → deep space
    bedroom = ken_burns(ref_img, 1.0, zoom_start=1.06, zoom_end=1.12)
    space = deep_space_bg()

    blend_start = 0.3
    if t < blend_start:
        img = bedroom.copy()
    else:
        bt = (t - blend_start) / (1 - blend_start)
        img = crossfade(bedroom, space, bt)

    # Overlay: stars fading in
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=t * 2.0, twinkle_offset=f)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, star_layer).convert('RGB')

    # Sparkle swirl overlay
    draw = ImageDraw.Draw(img, 'RGBA')
    if t > 0.2:
        swirl_t = (t - 0.2) / 0.8
        for i in range(int(80 * swirl_t)):
            angle = i * 0.4 + f * 0.08
            r_dist = 100 + i * 3.5
            sx = int(W / 2 + r_dist * math.cos(angle))
            sy = int(H / 2 + r_dist * math.sin(angle) * 0.6)
            a = int(200 * swirl_t * (1 - i / 80))
            draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3],
                         fill=(255, 240, 150, a))

    # Narration
    draw2 = ImageDraw.Draw(img)
    if t < 0.4:
        narr = "Mason closed his eyes and took a deep breath..."
    elif t < 0.7:
        narr = "The stars began to dance and swirl all around him..."
    else:
        narr = "And just like that — his imagination took over!"

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw2, narr, H - 120, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 3 — Mason suits up / launches into space  (1:00 – 1:40)  40 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 3: Rocket launch...")
SCENE3_FRAMES = FPS * 40

for f in range(SCENE3_FRAMES):
    t = f / SCENE3_FRAMES

    img = deep_space_bg()
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=1.0, twinkle_offset=f + 800)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, star_layer).convert('RGB')

    # Earth in background bottom-left
    draw_earth(img, 250, H - 150, 200)

    # Moon top-right
    draw_moon(img, W - 250, 200, 100)

    # Rocket streaking upward
    if t < 0.4:
        # Rocket on launchpad / lifting off
        rocket_y = int(H * 0.75 - (H * 0.3) * (t / 0.4))
        rocket_x = W // 2
        draw_rocket(img, rocket_x, rocket_y, scale=1.8, angle=0)
        # Launch glow
        draw = ImageDraw.Draw(img, 'RGBA')
        for i in range(8):
            ga = int(60 * (1 - i / 8))
            draw.ellipse([rocket_x - 30 - i * 8, rocket_y + 50 - i * 4,
                          rocket_x + 30 + i * 8, rocket_y + 80 + i * 4],
                         fill=(255, 160, 30, ga))
    else:
        # Rocket zooming up into distance (shrinking)
        zoom_t = (t - 0.4) / 0.6
        scale = max(0.2, 1.8 - 1.6 * zoom_t)
        rocket_x = int(W // 2 + 200 * zoom_t)
        rocket_y = int(H * 0.45 - H * 0.35 * zoom_t)
        draw_rocket(img, rocket_x, rocket_y, scale=scale)

        # Contrail
        draw = ImageDraw.Draw(img, 'RGBA')
        for i in range(30):
            tx = rocket_x - int(i * 6 * zoom_t)
            ty = rocket_y + int(i * 12)
            a = int(150 * (1 - i / 30))
            draw.ellipse([tx - 6, ty - 6, tx + 6, ty + 6], fill=(255, 200, 80, a))

    # Mason (astronaut) visible in cockpit area (early phase)
    if t < 0.35:
        draw_astronaut(img, W // 2, int(H * 0.75 - (H * 0.3) * (t / 0.4)) - 90,
                       scale=0.8, frame=f)

    draw2 = ImageDraw.Draw(img)
    if t < 0.3:
        narr = "Mason became Astronaut Mason — ready for the greatest adventure!"
    elif t < 0.65:
        narr = "3... 2... 1... BLAST OFF! His rocket shot into the night sky!"
    else:
        narr = "Higher and higher he flew, leaving Earth far below..."

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw2, narr, H - 120, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 4 — Mason floats in outer space  (1:40 – 2:15)  35 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 4: Floating in space...")
SCENE4_FRAMES = FPS * 35

for f in range(SCENE4_FRAMES):
    t = f / SCENE4_FRAMES

    img = deep_space_bg()

    # Nebula clouds
    img = draw_galaxy_cloud(img, W // 2 - 200, H // 2, 350, 200, (80, 30, 120), alpha=80)
    img = draw_galaxy_cloud(img, W // 2 + 300, H // 3, 280, 180, (20, 60, 130), alpha=70)

    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=1.0, twinkle_offset=f + 2000)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, star_layer).convert('RGB')

    # Planets
    draw_planet(img, 200, 300, 90, (200, 100, 60, 255))          # orange rocky planet
    draw_planet(img, W - 280, 200, 70, (150, 180, 220, 255))     # blue ice planet
    draw_planet(img, W - 150, H - 180, 110, (220, 180, 80, 255), # Saturn-like
                ring=True, ring_color=(200, 160, 70))

    # Earth small in background
    draw_earth(img, 150, H - 180, 80)

    # Mason floating — gentle bob
    bob = int(20 * math.sin(f * 0.08))
    spin = math.sin(f * 0.04) * 0.05
    mason_x = int(W // 2 + 50 * math.sin(f * 0.03))
    mason_y = H // 2 - 30 + bob
    draw_astronaut(img, mason_x, mason_y, scale=1.4, wave=True, frame=f)

    # Stars/sparkles around Mason
    draw3 = ImageDraw.Draw(img, 'RGBA')
    for i in range(8):
        angle = i * (2 * math.pi / 8) + f * 0.05
        sx = mason_x + int(120 * math.cos(angle))
        sy = mason_y + int(60 * math.sin(angle))
        a = int(180 * abs(math.sin(f * 0.1 + i)))
        draw3.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(255, 240, 120, a))

    draw2 = ImageDraw.Draw(img)
    if t < 0.3:
        narr = "\"Whoa!\" said Mason, floating weightlessly among the stars."
    elif t < 0.6:
        narr = "Colorful planets swirled all around him — just like he always imagined!"
    else:
        narr = "He spun and tumbled and laughed, free as a comet in the cosmos."

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw2, narr, H - 120, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 5 — Racing through a colorful galaxy  (2:15 – 2:40)  25 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 5: Galaxy race...")
SCENE5_FRAMES = FPS * 25

for f in range(SCENE5_FRAMES):
    t = f / SCENE5_FRAMES

    # Bright galaxy background
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        frac = row / H
        arr[row, :, 0] = int(10 + 30 * frac)
        arr[row, :, 1] = int(5 + 15 * frac)
        arr[row, :, 2] = int(25 + 50 * frac)
    img = Image.fromarray(arr, 'RGB')

    # Nebula streaks (speed lines)
    draw = ImageDraw.Draw(img, 'RGBA')
    for i in range(80):
        streak_x = (i * 137 + f * 60) % W
        streak_y = (i * 73) % H
        streak_len = random.Random(i * 100).randint(50, 200)
        streak_col = random.Random(i).choice([
            (150, 100, 255), (80, 180, 255), (255, 150, 80), (100, 255, 180)
        ])
        a = random.Random(i * 7 + f).randint(40, 120)
        draw.line([(streak_x, streak_y), (streak_x - streak_len, streak_y)],
                  fill=(*streak_col, a), width=2)

    # Colored stars / many star field
    rng2 = random.Random(99)
    for _ in range(500):
        sx = rng2.randint(0, W)
        sy = rng2.randint(0, H)
        sc = rng2.choice([(255, 255, 200), (200, 180, 255), (180, 230, 255), (255, 200, 150)])
        sr = rng2.randint(1, 3)
        a = rng2.randint(100, 220)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(*sc, a))

    # Colorful nebula blobs
    img = draw_galaxy_cloud(img, W // 3, H // 2, 400, 280, (120, 30, 200), alpha=100)
    img = draw_galaxy_cloud(img, 2 * W // 3, H // 3, 300, 200, (30, 120, 200), alpha=90)
    img = draw_galaxy_cloud(img, W // 4, H // 3, 250, 180, (200, 80, 50), alpha=70)

    # Mason in rocket zooming right
    rocket_y = int(H // 2 + 30 * math.sin(f * 0.12))
    rocket_x = int(W * 0.35 + 50 * math.sin(f * 0.05))
    draw_rocket(img, rocket_x, rocket_y, scale=2.0)

    # Contrail
    draw2 = ImageDraw.Draw(img, 'RGBA')
    for i in range(40):
        tx = rocket_x - int(i * 10)
        ty = rocket_y + random.Random(i + f).randint(-5, 5)
        a = int(160 * (1 - i / 40))
        cr = max(1, 8 - i // 6)
        col = [(255, 200, 60), (255, 140, 30), (255, 80, 10)][i % 3]
        draw2.ellipse([tx - cr, ty - cr, tx + cr, ty + cr], fill=(*col, a))

    # Passing planets
    for pi, (px_base, py, pr, pc) in enumerate([
        (W + 100, 200, 80, (180, 120, 60, 255)),
        (W + 600, H - 150, 60, (100, 160, 220, 255)),
        (W + 1100, 350, 50, (200, 80, 120, 255)),
    ]):
        px = (px_base - int(t * W * 1.4)) % (W + 400) - 200
        draw_planet(img, px, py, pr, pc)

    draw3 = ImageDraw.Draw(img)
    if t < 0.4:
        narr = "Zoom! Mason's rocket blazed through the heart of the galaxy!"
    elif t < 0.7:
        narr = "Rainbow nebulas and shooting stars whizzed past his window."
    else:
        narr = "He had the BIGGEST imagination of any astronaut in the universe!"

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw3, narr, H - 120, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 6 — Landing on the Moon / planting flag  (2:40 – 3:00)  20 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 6: Moon landing...")
SCENE6_FRAMES = FPS * 20

moon_surface_color = (220, 215, 190)

for f in range(SCENE6_FRAMES):
    t = f / SCENE6_FRAMES

    # Moon surface scene
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        frac = row / H
        # Sky (dark space at top, lighter near horizon)
        arr[row, :, 0] = int(5 + 15 * frac)
        arr[row, :, 1] = int(3 + 10 * frac)
        arr[row, :, 2] = int(20 + 40 * frac)
    img = Image.fromarray(arr, 'RGB')

    # Stars in sky
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=1.2, twinkle_offset=f + 5000)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, star_layer).convert('RGB')

    # Earth in sky
    draw_earth(img, W - 300, 180, 120)

    # Moon surface (bottom strip)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, H - 280, W, H], fill=moon_surface_color)
    # Surface undulations
    for i in range(0, W, 80):
        draw.ellipse([i - 100, H - 310, i + 100, H - 230],
                     fill=(215, 210, 180))

    # Crater details
    for (cx2, cy2, cr2) in [(300, H - 200, 40), (900, H - 220, 25), (W - 400, H - 200, 35)]:
        draw.ellipse([cx2 - cr2, cy2 - cr2, cx2 + cr2, cy2 + cr2],
                     fill=(200, 195, 165))

    # Big moon in background
    draw_moon(img, W // 2 - 400, 180, 80)

    # Mason standing on the moon
    mason_x = W // 2 + 80
    mason_y = H - 360
    bob = int(5 * math.sin(f * 0.15))
    draw_astronaut(img, mason_x, mason_y + bob, scale=1.6, wave=t > 0.5, frame=f)

    # Flag
    flag_x = mason_x + 120
    flag_y = H - 420
    draw2 = ImageDraw.Draw(img)
    draw2.line([(flag_x, flag_y), (flag_x, flag_y + 120)], fill=(180, 180, 180), width=4)
    # Flag panel with stars
    draw2.rectangle([flag_x, flag_y, flag_x + 70, flag_y + 45], fill=(200, 30, 30))
    draw2.rectangle([flag_x, flag_y, flag_x + 30, flag_y + 25], fill=(20, 30, 120))
    for si in range(6):
        sx = flag_x + 5 + (si % 3) * 9
        sy = flag_y + 5 + (si // 3) * 9
        draw2.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 255, 200))

    # Rocket landed nearby
    draw_rocket(img, mason_x - 200, H - 380, scale=1.2)

    # Ending narration + fade out
    draw3 = ImageDraw.Draw(img)
    if t < 0.35:
        narr = "Mason landed on the Moon and planted his flag with a giant smile!"
    elif t < 0.65:
        narr = "\"I made it!\" he shouted across the stars. \"I'm really an astronaut!\""
    else:
        narr = "Dreams this BIG? They just might come true, Mason. Sweet dreams."

    fade = min(1.0, min(t * 6, (1 - t) * 6))
    draw_wrapped_text(draw3, narr, H - 120, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    # Final fade to black
    if t > 0.75:
        fade_out = (t - 0.75) / 0.25
        black = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * fade_out)))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, black).convert('RGB')

    advance(img)


# ══════════════════════════════════════════════════════════════════════════════
# END CARD — 5 seconds
# ══════════════════════════════════════════════════════════════════════════════
print("End card...")
END_FRAMES = FPS * 5

for f in range(END_FRAMES):
    t = f / END_FRAMES
    img = Image.new('RGB', (W, H), (5, 5, 20))
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=1.0, twinkle_offset=f + 9000)
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, star_layer).convert('RGB')

    draw = ImageDraw.Draw(img)
    fade = min(1.0, t * 3)
    draw_text_centered(draw, "The End", H // 2 - 60, FONT_TITLE,
                       fill=(255, 240, 120, int(255 * fade)))
    draw_text_centered(draw, "Keep dreaming big ✨", H // 2 + 20, FONT_SUB,
                       fill=(200, 220, 255, int(200 * fade)))
    draw_text_centered(draw, "Like & Subscribe for more adventures!", H // 2 + 100, FONT_SMALL,
                       fill=(180, 200, 255, int(180 * fade)))

    advance(img)

# ══════════════════════════════════════════════════════════════════════════════
# COMPILE with FFmpeg
# ══════════════════════════════════════════════════════════════════════════════
print(f"\nTotal frames generated: {frame_n}")
print("Compiling video with FFmpeg...")

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUTDIR, "frame_%06d.jpg"),
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    VIDEO
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size_mb = os.path.getsize(VIDEO) / (1024 * 1024)
    print(f"Video saved: {VIDEO}  ({size_mb:.1f} MB)")
else:
    print("FFmpeg error:")
    print(result.stderr[-2000:])
