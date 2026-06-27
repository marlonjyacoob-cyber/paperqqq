"""
Mason's Dream Adventure — v3
~80 seconds to match voiceover. No text overlays.
"""

import os
import math
import random
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H   = 1920, 1080
FPS    = 24
OUTDIR = "/home/user/paperqqq/mason_video/frames"
VIDEO  = "/home/user/paperqqq/mason_video/mason_dream_adventure.mp4"

IMG_WAVING   = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/e34fbba9-IMG_5347.jpeg"
IMG_BEDROOM  = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/1425d1c0-IMG_5348.jpeg"
IMG_COCKPIT  = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/2bec565a-IMG_5349.jpeg"
IMG_FLOATING = "/root/.claude/uploads/f34888cd-2a9e-5a9d-91c4-23c61db3ed6a/be98b1e1-IMG_5350.jpeg"

os.makedirs(OUTDIR, exist_ok=True)

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


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
    return Image.fromarray(((1 - t) * a_arr + t * b_arr).astype(np.uint8), 'RGB')


def overlay_color(img, color, alpha):
    ov = Image.new('RGBA', (W, H), (*color, int(alpha)))
    return Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')


def vignette(img, strength=0.3):
    arr = np.array(img.convert('RGB'), dtype=float)
    cols = np.linspace(-1, 1, W)
    rows = np.linspace(-1, 1, H)
    x, y = np.meshgrid(cols, rows)
    mask = np.clip(1 - strength * (x ** 2 + y ** 2), 0, 1)
    arr *= mask[:, :, np.newaxis]
    return Image.fromarray(arr.astype(np.uint8), 'RGB')


def sparkle_layer(frame, count=20, seed=0):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed + frame // 3)
    for _ in range(count):
        sx, sy = rng.randint(0, W), rng.randint(0, H)
        sr = rng.uniform(2, 6)
        sa = rng.randint(60, 180)
        sc = rng.choice([(255, 240, 120), (200, 220, 255), (255, 200, 180)])
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(*sc, sa))
    return layer


def space_bg():
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for row in range(H):
        f = row / H
        arr[row, :] = [int(5 + 20 * f), int(3 + 10 * f), int(25 + 55 * f)]
    return Image.fromarray(arr, 'RGB')


def save_frame(img, n):
    img.convert('RGB').save(os.path.join(OUTDIR, f"frame_{n:06d}.jpg"), quality=93)


# ── Load images ────────────────────────────────────────────────────────────────
print("Loading images...")
img_waving   = Image.open(IMG_WAVING).convert('RGB').resize((W, H), Image.LANCZOS)
img_bedroom  = Image.open(IMG_BEDROOM).convert('RGB').resize((W, H), Image.LANCZOS)
img_cockpit  = Image.open(IMG_COCKPIT).convert('RGB').resize((W, H), Image.LANCZOS)
img_floating = Image.open(IMG_FLOATING).convert('RGB').resize((W, H), Image.LANCZOS)
space_img    = space_bg()

STARS   = make_star_field(350, seed=7)
FONT_T  = load_font(78)
FONT_S  = load_font(44)

frame_n = 0

def advance(img):
    global frame_n
    save_frame(img, frame_n)
    frame_n += 1


# ── Scene durations (total ≈ 80 s to match voiceover) ─────────────────────────
#  S1 waving intro    12 s
#  S2 bedroom         14 s
#  S3 transition       9 s
#  S4 cockpit         17 s
#  S5 floating        20 s
#  S6 wake/end         8 s
#  Total              80 s


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 1 — Mason waving / intro  (0:00–0:12)  12 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 1: Mason waving...")
S1 = FPS * 12

for f in range(S1):
    t = f / S1
    base = ken_burns(img_waving, t, zoom_start=1.0, zoom_end=1.07, pan_x=0.05, pan_y=-0.05)
    base = overlay_color(base, (255, 240, 200), 25)
    base = vignette(base, 0.2)
    sp = sparkle_layer(f, count=15, seed=10)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')
    # Title card first 3 s
    if f < FPS * 3:
        fade = min(1.0, f / (FPS * 0.5))
        black_a = int(130 * (1 - min(1.0, f / (FPS * 2.5))))
        base = overlay_color(base, (0, 0, 0), black_a)
        draw = ImageDraw.Draw(base)
        bbox = draw.textbbox((0, 0), "Mason's Dream Adventure", font=FONT_T)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x + 3, H // 2 - 57), "Mason's Dream Adventure", font=FONT_T, fill=(0, 0, 0, 160))
        draw.text((x, H // 2 - 60), "Mason's Dream Adventure", font=FONT_T,
                  fill=(255, 240, 100, int(255 * fade)))
    # Fade in
    if f < FPS * 0.5:
        base = overlay_color(base, (0, 0, 0), int(255 * (1 - f / (FPS * 0.5))))
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 2 — Bedroom / falling asleep  (0:12–0:26)  14 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 2: Bedroom...")
S2 = FPS * 14

for f in range(S2):
    t = f / S2
    base = ken_burns(img_bedroom, t, zoom_start=1.0, zoom_end=1.09, pan_x=0.1, pan_y=0.08)
    base = overlay_color(base, (10, 10, 40), int(25 * t))
    base = vignette(base, 0.3)
    if t > 0.5:
        star_t = (t - 0.5) / 0.5
        sl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_stars(ImageDraw.Draw(sl), STARS, alpha_mult=star_t * 0.5, twinkle_offset=f)
        base = Image.alpha_composite(base.convert('RGBA'), sl).convert('RGB')
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 3 — Dream transition  (0:26–0:35)  9 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 3: Transition...")
S3 = FPS * 9

for f in range(S3):
    t = f / S3
    bedroom_kb = ken_burns(img_bedroom, 1.0, zoom_start=1.09, zoom_end=1.12)
    base = bedroom_kb if t < 0.25 else crossfade(bedroom_kb, space_img, (t - 0.25) / 0.75)
    sl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_stars(ImageDraw.Draw(sl), STARS, alpha_mult=t * 1.5, twinkle_offset=f + 3000)
    base = Image.alpha_composite(base.convert('RGBA'), sl).convert('RGB')
    if t > 0.15:
        swirl_t = (t - 0.15) / 0.85
        d = ImageDraw.Draw(base, 'RGBA')
        for i in range(int(80 * swirl_t)):
            angle = i * 0.38 + f * 0.12
            dist  = 80 + i * 5
            sx = int(W / 2 + dist * math.cos(angle))
            sy = int(H / 2 + dist * math.sin(angle) * 0.55)
            a  = int(180 * swirl_t * (1 - i / 80))
            d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 230, 120, a))
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 4 — Rocket cockpit  (0:35–0:52)  17 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 4: Cockpit...")
S4 = FPS * 17

for f in range(S4):
    t = f / S4
    base = ken_burns(img_cockpit, t, zoom_start=1.0, zoom_end=1.10, pan_x=0.0, pan_y=-0.1)
    base = vignette(base, 0.25)
    pulse = 0.5 + 0.5 * math.sin(f * 0.18)
    base = overlay_color(base, (80, 140, 255), int(12 * pulse))
    sp = sparkle_layer(f, count=12, seed=20)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')
    if f < FPS:
        base = overlay_color(base, (5, 5, 25), int(255 * (1 - f / FPS)))
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 5 — Floating in space  (0:52–1:12)  20 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 5: Floating...")
S5 = FPS * 20

for f in range(S5):
    t = f / S5
    pan_x = 0.15 * math.sin(t * math.pi * 2)
    zoom  = 1.0 + 0.06 * t + 0.02 * math.sin(t * math.pi * 3)
    new_w, new_h = int(W * zoom), int(H * zoom)
    scaled = img_floating.resize((new_w, new_h), Image.LANCZOS)
    ox = int((new_w - W) / 2 + pan_x * (new_w - W) / 2)
    oy = int((new_h - H) / 2)
    ox = max(0, min(new_w - W, ox))
    base = scaled.crop((ox, oy, ox + W, oy + H))
    base = overlay_color(base, (20, 0, 60), 18)
    base = vignette(base, 0.3)
    sl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_stars(ImageDraw.Draw(sl), STARS, alpha_mult=0.7, twinkle_offset=f + 6000)
    base = Image.alpha_composite(base.convert('RGBA'), sl).convert('RGB')
    sp = sparkle_layer(f, count=20, seed=30)
    base = Image.alpha_composite(base.convert('RGBA'), sp).convert('RGB')
    if f < FPS:
        base = overlay_color(base, (5, 5, 25), int(255 * (1 - f / FPS)))
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# SCENE 6 — Wake up / end card  (1:12–1:20)  8 s
# ══════════════════════════════════════════════════════════════════════════════
print("Scene 6: Wake up...")
S6 = FPS * 8

for f in range(S6):
    t = f / S6
    if t < 0.5:
        base = crossfade(img_floating, ken_burns(img_bedroom, 0.0), t / 0.5)
        base = overlay_color(base, (255, 200, 100), int(30 * (t / 0.5)))
    else:
        base = ken_burns(img_bedroom, 1.0, zoom_start=1.12, zoom_end=1.08)
        base = overlay_color(base, (255, 220, 150), 25)
    base = vignette(base, 0.2)
    # Fade to black at end
    if t > 0.75:
        base = overlay_color(base, (0, 0, 0), int(255 * ((t - 0.75) / 0.25)))
    advance(base)


# ══════════════════════════════════════════════════════════════════════════════
# COMPILE
# ══════════════════════════════════════════════════════════════════════════════
total_s = frame_n / FPS
print(f"\nTotal frames: {frame_n}  ({total_s:.1f} s)")
print("Compiling video...")

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", os.path.join(OUTDIR, "frame_%06d.jpg"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    VIDEO
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    print(f"Done! {VIDEO}  ({os.path.getsize(VIDEO)/1024/1024:.1f} MB)")
else:
    print(result.stderr[-2000:])
