"""
Mason's Dream Adventure — v2
Uses all 4 user-supplied cartoon images as scene backgrounds.
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
VIDEO  = "/home/user/paperqqq/mason_video/mason_dream_adventure.mp4"

IMG_WAVING   = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/e34fbba9-IMG_5347.jpeg"  # Mason standing/waving
IMG_BEDROOM  = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/1425d1c0-IMG_5348.jpeg"  # Bedroom/sleeping
IMG_COCKPIT  = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/2bec565a-IMG_5349.jpeg"  # Astronaut in cockpit
IMG_FLOATING = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/be98b1e1-IMG_5350.jpeg"  # Floating in space

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


def draw_wrapped_text(draw, text, y_center, font, fill=(255, 255, 255), max_width=1700):
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
        # Dark pill background for legibility
        draw.rectangle([x - 16, y - 8, x + tw + 16, y + font.size + 8],
                       fill=(0, 0, 0, 140))
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 140))
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


def make_star_field(count=300, seed=42):
    rng = random.Random(seed)
    return [(rng.randint(0, W), rng.randint(0, H),
             rng.uniform(0.5, 2.5), rng.uniform(0.4, 1.0)) for _ in range(count)]


def draw_stars(draw, stars, alpha_mult=1.0, twinkle_offset=0):
    for i, (x, y, r, base_a) in enumerate(stars):
        twinkle = 0.7 + 0.3 * math.sin((twinkle_offset + i * 0.7) * 0.15)
        a = int(min(255, base_a * alpha_mult * twinkle * 255))
        cr = int(r)
        draw.ellipse([x - cr, y - cr, x + cr, y + cr], fill=(255, 255, 220, a))


def ken_burns(base_img, t, zoom_start=1.0, zoom_end=1.08, pan_x=0.0, pan_y=0.0):
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
    a_arr = np.array(img_a.convert('RGB'), dtype=float)
    b_arr = np.array(img_b.convert('RGB'), dtype=float)
    blend = ((1 - t) * a_arr + t * b_arr).astype(np.uint8)
    return Image.fromarray(blend, 'RGB')


def vignette(img, strength=0.35):
    arr = np.array(img.convert('RGB'), dtype=float)
    rows = np.linspace(-1, 1, H)
    cols = np.linspace(-1, 1, W)
    x, y = np.meshgrid(cols, rows)
    mask = 1 - strength * (x ** 2 + y ** 2)
    mask = np.clip(mask, 0, 1)
    arr *= mask[:, :, np.newaxis]
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def overlay_color(img, color, alpha):
    overlay = Image.new('RGBA', (W, H), (*color, alpha))
    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')


def sparkle_layer(frame, count=30, seed=0):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed + frame // 3)
    for _ in range(count):
        sx = rng.randint(0, W)
        sy = rng.randint(0, H)
        sr = rng.uniform(2, 6)
        sa = rng.randint(80, 200)
        sc = rng.choice([(255, 240, 120), (200, 220, 255), (255, 200, 180)])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(*sc, sa))
    return layer


def save_frame(img, n):
    img.convert('RGB').save(os.path.join(OUTDIR, f"frame_{n:06d}.jpg"), quality=93)


# ── Load & scale all source images ────────────────────────────────────────────
print("Loading images...")
img_waving   = Image.open(IMG_WAVING).convert('RGB').resize((W, H), Image.LANCZOS)
img_bedroom  = Image.open(IMG_BEDROOM).convert('RGB').resize((W, H), Image.LANCZOS)
img_cockpit  = Image.open(IMG_COCKPIT).convert('RGB').resize((W, H), Image.LANCZOS)
img_floating = Image.open(IMG_FLOATING).convert('RGB').resize((W, H), Image.LANCZOS)

STARS     = make_star_field(350, seed=7)
FONT_TITLE = load_font(78)
FONT_SUB   = load_font(48)
FONT_NARR  = load_font(42)
FONT_SMALL = load_font(30)

frame_n = 0

def advance(img):
    global frame_n
    save_frame(img, frame_n)
    frame_n += 1


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 1 — Title card + Mason waving / excited  (0:00–0:30)  30 s = 720 frames
# Image: IMG_5347 — Mason standing, waving, happy
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 1: Mason waving (intro)...")
S1 = FPS * 30

for f in range(S1):
    t = f / S1

    # Soft warm background behind the character (white bg in source)
    base = ken_burns(img_waving, t, zoom_start=1.0, zoom_end=1.07, pan_x=0.05, pan_y=-0.05)
    # Warm-up tint so it feels like daytime
    base = overlay_color(base, (255, 240, 200), 30)
    base = vignette(base, 0.2)

    # Sparkles around Mason
    sp = sparkle_layer(f, count=20, seed=10)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')

    draw = ImageDraw.Draw(base, 'RGBA')

    # Title card first 4 s
    if f < FPS * 4:
        fade = min(1.0, f / (FPS * 0.6))
        black_a = int(160 * (1 - min(1.0, f / (FPS * 3.5))))
        draw.rectangle([0, 0, W, H], fill=(0, 0, 0, black_a))
        draw2 = ImageDraw.Draw(base)
        draw_text_centered(draw2, "Mason's Dream Adventure",
                           H // 2 - 70, FONT_TITLE, fill=(255, 240, 100, int(255 * fade)))
        draw_text_centered(draw2, "A Story About Dreaming Big",
                           H // 2 + 20, FONT_SUB, fill=(200, 220, 255, int(220 * fade)))

    # Narration
    if FPS * 4 <= f < S1 - FPS * 2:
        seg = (f - FPS * 4) / (S1 - FPS * 6)
        if seg < 0.4:
            narr = "Meet Mason — a six-year-old boy with the biggest imagination in the world!"
        elif seg < 0.75:
            narr = "Every single night, Mason dreamed of one thing..."
        else:
            narr = "Being an ASTRONAUT and exploring the stars!"
        fade = min(1.0, min(seg * 6, (1 - seg) * 6))
        draw2 = ImageDraw.Draw(base)
        draw_wrapped_text(draw2, narr, H - 140, FONT_NARR,
                          fill=(255, 255, 255, int(230 * fade)))

    # Fade in from black
    if f < FPS:
        base = overlay_color(base, (0, 0, 0), int(255 * (1 - f / FPS)))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 2 — Bedtime / falling asleep  (0:30–1:05)  35 s = 840 frames
# Image: IMG_5348 — cozy bedroom, Mason sleeping, rocket posters
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 2: Bedroom (sleeping)...")
S2 = FPS * 35

for f in range(S2):
    t = f / S2

    base = ken_burns(img_bedroom, t, zoom_start=1.0, zoom_end=1.09, pan_x=0.1, pan_y=0.08)
    # Gradually darken / blue-shift as Mason drifts to sleep
    dark = int(20 * t)
    base = overlay_color(base, (10, 10, 40), dark)
    base = vignette(base, 0.3)

    # Stars fading in over the bedroom as dreams begin
    if t > 0.5:
        star_t = (t - 0.5) / 0.5
        star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        star_draw = ImageDraw.Draw(star_layer)
        draw_stars(star_draw, STARS, alpha_mult=star_t * 0.6, twinkle_offset=f)
        base = Image.alpha_composite(base.convert('RGBA'), star_layer).convert('RGB')

    draw = ImageDraw.Draw(base)
    seg = t
    if seg < 0.35:
        narr = "Every night, six-year-old Mason snuggled into his cozy bed..."
    elif seg < 0.65:
        narr = "He stared at his rocket posters and the real stars outside his window."
    else:
        narr = "His eyes grew heavy... and something magical was about to begin."

    fade = min(1.0, min(seg * 5, (1 - seg) * 5))
    draw_wrapped_text(draw, narr, H - 140, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 3 — Dream transition  (1:05–1:25)  20 s = 480 frames
# Programmatic: bedroom fades into deep space with swirling stars
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 3: Dream transition...")
S3 = FPS * 20

# Space background for blend target
def space_bg():
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        f2 = row / H
        arr[row, :, 0] = int(5 + 20 * f2)
        arr[row, :, 1] = int(3 + 10 * f2)
        arr[row, :, 2] = int(25 + 55 * f2)
    return Image.fromarray(arr, 'RGB')

space_img = space_bg()

for f in range(S3):
    t = f / S3

    bedroom_kb = ken_burns(img_bedroom, 1.0, zoom_start=1.09, zoom_end=1.12)

    if t < 0.3:
        base = bedroom_kb.copy()
    else:
        bt = (t - 0.3) / 0.7
        base = crossfade(bedroom_kb, space_img, bt)

    # Stars swirling in
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=t * 1.5, twinkle_offset=f + 3000)
    base = Image.alpha_composite(base.convert('RGBA'), star_layer).convert('RGB')

    # Swirl sparkles
    draw2 = ImageDraw.Draw(base, 'RGBA')
    if t > 0.15:
        swirl_t = (t - 0.15) / 0.85
        for i in range(int(100 * swirl_t)):
            angle = i * 0.38 + f * 0.10
            dist = 80 + i * 4.5
            sx = int(W / 2 + dist * math.cos(angle))
            sy = int(H / 2 + dist * math.sin(angle) * 0.55)
            a = int(200 * swirl_t * (1 - i / 100))
            draw2.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 230, 120, a))

    draw3 = ImageDraw.Draw(base)
    if t < 0.4:
        narr = "Mason closed his eyes... and his imagination took over."
    else:
        narr = "The stars reached down and lifted him high into the sky!"

    fade = min(1.0, min(t * 6, (1 - t) * 6))
    draw_wrapped_text(draw3, narr, H - 140, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 4 — Piloting the rocket  (1:25–2:00)  35 s = 840 frames
# Image: IMG_5349 — Mason in astronaut suit inside rocket cockpit, waving
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 4: Rocket cockpit...")
S4 = FPS * 35

for f in range(S4):
    t = f / S4

    # Slow zoom in toward Mason's face
    base = ken_burns(img_cockpit, t, zoom_start=1.0, zoom_end=1.10, pan_x=0.0, pan_y=-0.1)
    base = vignette(base, 0.25)

    # Subtle color flash / light pulse through cockpit window (space passing by)
    pulse = 0.5 + 0.5 * math.sin(f * 0.18)
    base = overlay_color(base, (80, 140, 255), int(12 * pulse))

    # Sparkle stars on the cockpit window
    sp = sparkle_layer(f, count=15, seed=20)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')

    draw = ImageDraw.Draw(base)
    if t < 0.3:
        narr = "\"3... 2... 1... BLAST OFF!\" Mason was piloting his very own rocket!"
    elif t < 0.6:
        narr = "The planets zoomed past his window — orange Saturn, icy Neptune, glowing Mars!"
    else:
        narr = "\"I'm really doing it!\" he laughed, pushing the joystick toward the stars."

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw, narr, H - 140, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    # Fade in from space transition
    if f < FPS:
        base = overlay_color(base, (5, 5, 25), int(255 * (1 - f / FPS)))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 5 — Floating in space  (2:00–2:40)  40 s = 960 frames
# Image: IMG_5350 — Mason in full astronaut suit floating, waving at camera
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 5: Floating in space...")
S5 = FPS * 40

for f in range(S5):
    t = f / S5

    # Gentle sway: alternate pan left/right to simulate weightless drift
    pan_x = 0.15 * math.sin(t * math.pi * 2)
    zoom = 1.0 + 0.06 * t + 0.02 * math.sin(t * math.pi * 3)
    new_w = int(W * zoom)
    new_h = int(H * zoom)
    scaled = img_floating.resize((new_w, new_h), Image.LANCZOS)
    ox = int((new_w - W) / 2 + pan_x * (new_w - W) / 2)
    oy = int((new_h - H) / 2)
    ox = max(0, min(new_w - W, ox))
    oy = max(0, min(new_h - H, oy))
    base = scaled.crop((ox, oy, ox + W, oy + H))

    # Deep-space color boost
    base = overlay_color(base, (20, 0, 60), 18)
    base = vignette(base, 0.3)

    # Stars twinkling over the image
    star_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    star_draw = ImageDraw.Draw(star_layer)
    draw_stars(star_draw, STARS, alpha_mult=0.7, twinkle_offset=f + 6000)
    base = Image.alpha_composite(base.convert('RGBA'), star_layer).convert('RGB')

    # Orbit sparkles around Mason
    sp = sparkle_layer(f, count=25, seed=30)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')

    draw = ImageDraw.Draw(base)
    if t < 0.28:
        narr = "\"WHOA!\" Mason floated free — weightless among a billion glittering stars!"
    elif t < 0.55:
        narr = "He did a slow somersault and waved at Earth far, far below."
    elif t < 0.80:
        narr = "Rainbow nebulas swirled all around him like cotton candy clouds."
    else:
        narr = "No astronaut had ever smiled this wide in the whole history of space."

    fade = min(1.0, min(t * 5, (1 - t) * 5))
    draw_wrapped_text(draw, narr, H - 140, FONT_NARR,
                      fill=(255, 255, 255, int(230 * fade)))

    # Crossfade in from cockpit scene
    if f < FPS:
        base = overlay_color(base, (5, 5, 25), int(255 * (1 - f / FPS)))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 6 — Waking up / End card  (2:40–3:05)  25 s = 600 frames
# Crossfade back to bedroom image, then end card
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 6: Wake up + end card...")
S6 = FPS * 25

for f in range(S6):
    t = f / S6

    if t < 0.5:
        # Crossfade from floating-in-space image back to bedroom
        ct = t / 0.5
        space_frame  = img_floating.copy()
        bedroom_frame = ken_burns(img_bedroom, 0.0, zoom_start=1.12, zoom_end=1.12)
        base = crossfade(space_frame, bedroom_frame, ct)
        # Warm up color as bedroom takes over
        base = overlay_color(base, (255, 200, 100), int(30 * ct))
    else:
        # Full bedroom — morning light
        base = ken_burns(img_bedroom, 1.0, zoom_start=1.12, zoom_end=1.08)
        base = overlay_color(base, (255, 220, 150), 25)

    base = vignette(base, 0.2)
    draw = ImageDraw.Draw(base)

    if t < 0.35:
        narr = "Slowly... the stars faded. Mason felt his cozy blanket all around him."
    elif t < 0.6:
        narr = "He opened his eyes and smiled the biggest smile you've ever seen."
    else:
        # End card text
        fade_ec = (t - 0.6) / 0.4
        draw_text_centered(draw, "Sweet dreams, Mason.", H // 2 - 60, FONT_TITLE,
                           fill=(255, 240, 100, int(255 * fade_ec)))
        draw_text_centered(draw, "Keep dreaming big — the stars are waiting for you.",
                           H // 2 + 30, FONT_SUB,
                           fill=(255, 255, 255, int(200 * fade_ec)))
        draw_text_centered(draw, "Like & Subscribe for more adventures!",
                           H // 2 + 110, FONT_SMALL,
                           fill=(200, 220, 255, int(180 * fade_ec)))

    if t < 0.6:
        fade = min(1.0, min(t * 5, (1 - t) * 5))
        draw_wrapped_text(draw, narr, H - 140, FONT_NARR,
                          fill=(255, 255, 255, int(220 * fade)))

    # Fade to black at the very end
    if t > 0.88:
        fo = (t - 0.88) / 0.12
        base = overlay_color(base, (0, 0, 0), int(255 * fo))

    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# COMPILE
# ══════════════════════════════════════════════════════════════════════════════
print(f"\nTotal frames: {frame_n}  ({frame_n / FPS:.1f} s)")
print("Compiling with FFmpeg...")

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
    print(f"Done!  {VIDEO}  ({size_mb:.1f} MB)")
else:
    print("FFmpeg error:")
    print(result.stderr[-2000:])
