"""
Pillow recreations of the 3 gas pipeline reference photos.
Each is 1920x1080, styled to match the real photos as closely as possible.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os
from pathlib import Path

W, H = 1920, 1080


def load_font(size):
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def add_text_overlay(img, text):
    """Adds subtitle-style text at the bottom of the image."""
    draw = ImageDraw.Draw(img)
    font = load_font(54)
    import textwrap
    lines = textwrap.wrap(text, width=50)
    line_h = 64
    total_h = len(lines) * line_h + 24
    bar_y = H - total_h - 40
    # semi-transparent black bar
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([(80, bar_y - 12), (W - 80, H - 30)], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    y = bar_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=font)
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += line_h
    return img


# ─── IMAGE 1: Yellow gas main being laid on city street ───────────────────────
def make_image1(text=""):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Overcast sky — grey-white gradient top third
    for y in range(360):
        t = y / 360
        c = int(180 + 40 * (1 - t))
        draw.line([(0, y), (W, y)], fill=(c, c + 2, c + 5))

    # Background buildings (right side)
    for bx, bw, bh, bc in [
        (1100, 280, 300, (110, 100, 95)),
        (1370, 220, 380, (90, 85, 80)),
        (1580, 180, 260, (105, 98, 92)),
        (1740, 200, 320, (95, 90, 85)),
    ]:
        draw.rectangle([(bx, 360 - bh), (bx + bw, 420)], fill=bc)
        # windows
        for wx in range(bx + 20, bx + bw - 10, 35):
            for wy in range(360 - bh + 20, 400, 45):
                draw.rectangle([(wx, wy), (wx + 20, wy + 28)],
                                fill=(160, 180, 200) if (wx + wy) % 3 != 0 else (80, 70, 60))

    # Blue tent (left background)
    draw.polygon([(140, 340), (380, 240), (620, 340)], fill=(50, 100, 200))
    draw.rectangle([(140, 340), (620, 430)], fill=(40, 90, 180))

    # Wet dark asphalt road
    for y in range(360, H):
        t = (y - 360) / (H - 360)
        grey = int(45 + 20 * (1 - t))
        draw.line([(0, y), (W, y)], fill=(grey, grey + 2, grey))

    # Wet sheen on asphalt
    for y in range(400, H, 4):
        alpha = int(30 * math.sin((y - 400) / 80))
        if alpha > 0:
            draw.line([(0, y), (W, y)], fill=(60 + alpha, 62 + alpha, 65 + alpha))

    # Construction barriers (orange/white striped, left)
    for bx in [30, 90, 150]:
        for i in range(6):
            col = (220, 100, 20) if i % 2 == 0 else (240, 240, 240)
            draw.rectangle([(bx, 380 + i * 30), (bx + 45, 380 + i * 30 + 30)], fill=col)

    # Metal fence/barrier posts
    for px in range(0, 700, 60):
        draw.rectangle([(px + 50, 340), (px + 56, 520)], fill=(140, 130, 120))
    draw.rectangle([(50, 370), (700, 378)], fill=(160, 150, 140))
    draw.rectangle([(50, 410), (700, 418)], fill=(160, 150, 140))

    # RED pipe fusion machine (centre-left)
    draw.rectangle([(320, 500), (680, 720)], fill=(160, 30, 30))
    draw.rectangle([(340, 520), (660, 700)], fill=(180, 40, 40))
    draw.rectangle([(380, 560), (480, 650)], fill=(120, 20, 20))
    draw.rectangle([(520, 560), (620, 650)], fill=(120, 20, 20))
    # machine wheels
    for wx, wy in [(370, 700), (560, 700), (650, 700)]:
        draw.ellipse([(wx - 30, wy - 30), (wx + 30, wy + 30)], fill=(50, 50, 50))
        draw.ellipse([(wx - 15, wy - 15), (wx + 15, wy + 15)], fill=(80, 80, 80))

    # BIG YELLOW PIPE — runs diagonally across the full image
    pipe_y_left = 420
    pipe_y_right = 480
    pipe_r = 90
    # pipe body (trapezoid approximation with many lines)
    for i in range(-pipe_r, pipe_r):
        t = i / pipe_r
        shade = int(220 - 60 * abs(t) + 20 * (1 - abs(t)))
        shade_g = int(180 - 50 * abs(t) + 15 * (1 - abs(t)))
        left_y = pipe_y_left + i + int(abs(t) * 8)
        right_y = pipe_y_right + i + int(abs(t) * 8)
        draw.line([(0, left_y), (W, right_y)], fill=(shade, shade_g, 0), width=2)
    # pipe highlight
    for i in range(-20, 5):
        t = i / pipe_r
        left_y = pipe_y_left + i - 30
        right_y = pipe_y_right + i - 30
        alpha = int(255 * (1 - abs(t) * 2))
        if alpha > 0:
            draw.line([(0, left_y), (W, right_y)],
                      fill=(min(255, 230 + alpha // 4), min(255, 210 + alpha // 4), 80), width=2)
    # pipe end cap (right side circle)
    cx, cy = W - 80, pipe_y_right
    draw.ellipse([(cx - pipe_r, cy - pipe_r), (cx + pipe_r, cy + pipe_r)], fill=(200, 160, 0))
    draw.ellipse([(cx - pipe_r + 12, cy - pipe_r + 12), (cx + pipe_r - 12, cy + pipe_r - 12)], fill=(30, 30, 30))

    # Worker 1 (right side, crouching)
    _draw_worker(draw, 1350, 560, facing='left', hivis=True)
    # Worker 2 (right side, standing)
    _draw_worker(draw, 1500, 500, facing='left', hivis=True)

    # Vignette
    img = _vignette(img)
    if text:
        img = add_text_overlay(img, text)
    return img


def _draw_worker(draw, x, y, facing='right', hivis=True):
    """Draw a simple but recognisable hi-vis worker."""
    jacket = (220, 210, 0) if hivis else (50, 100, 200)
    # hard hat
    hat_col = (240, 240, 240)
    draw.ellipse([(x - 20, y - 95), (x + 20, y - 55)], fill=hat_col)
    draw.rectangle([(x - 24, y - 72), (x + 24, y - 60)], fill=hat_col)
    # head/face
    draw.ellipse([(x - 16, y - 55), (x + 16, y - 25)], fill=(210, 175, 140))
    # jacket body
    draw.rectangle([(x - 28, y - 25), (x + 28, y + 60)], fill=jacket)
    # hi-vis stripes
    draw.rectangle([(x - 28, y + 5), (x + 28, y + 15)], fill=(220, 220, 220))
    draw.rectangle([(x - 28, y + 25), (x + 28, y + 35)], fill=(220, 220, 220))
    # arms
    arm_x = x + (30 if facing == 'right' else -30)
    draw.rectangle([(x + 20, y - 20), (x + 44, y + 30)], fill=jacket)
    draw.rectangle([(x - 44, y - 20), (x - 20, y + 30)], fill=jacket)
    # trousers
    draw.rectangle([(x - 24, y + 58), (x - 4, y + 130)], fill=(50, 55, 65))
    draw.rectangle([(x + 4, y + 58), (x + 24, y + 130)], fill=(50, 55, 65))
    # boots
    draw.rectangle([(x - 26, y + 128), (x - 2, y + 148)], fill=(30, 25, 20))
    draw.rectangle([(x + 2, y + 128), (x + 26, y + 148)], fill=(30, 25, 20))


# ─── IMAGE 2: Stack of yellow pipes end-on ────────────────────────────────────
def make_image2(text=""):
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Background: red/white striped barrier + grey sky
    for y in range(H):
        t = y / H
        c = int(150 + 50 * (1 - t))
        draw.line([(0, y), (W, y)], fill=(c, c, c))

    # Red/white diagonal stripes (barrier in background)
    stripe_w = 120
    for i in range(-2, W // stripe_w + 4):
        col = (200, 30, 30) if i % 2 == 0 else (240, 240, 240)
        pts = [
            (i * stripe_w, 0),
            (i * stripe_w + stripe_w, 0),
            (i * stripe_w + stripe_w - 200, H),
            (i * stripe_w - 200, H),
        ]
        draw.polygon(pts, fill=col)

    # Grey flatbed/trailer surface at bottom
    draw.rectangle([(0, 780), (W, H)], fill=(100, 95, 90))
    draw.rectangle([(0, 778), (W, 785)], fill=(70, 65, 60))

    # Stack of yellow pipes (circles from front)
    # Layout: 3 rows, roughly triangular stacking
    pipe_configs = []
    row_counts = [7, 6, 5, 4]
    base_y = 720
    r = 115
    gap = 8
    step = (r * 2 + gap)
    row_offset_y = int(step * 0.866)  # hex packing

    for row, count in enumerate(row_counts):
        total_w = count * step
        start_x = (W - total_w) // 2 + r + row * (step // 2)
        y = base_y - row * row_offset_y
        for col in range(count):
            x = start_x + col * step
            pipe_configs.append((x, y, r))

    # Draw pipes back to front (sort by y descending = front first in reverse)
    for x, y, r in sorted(pipe_configs, key=lambda p: -p[1]):
        # outer yellow ring
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=(180, 140, 0))
        # mid yellow
        draw.ellipse([(x - r + 10, y - r + 10), (x + r - 10, y + r - 10)], fill=(225, 180, 0))
        # pipe wall thickness
        draw.ellipse([(x - r + 22, y - r + 22), (x + r - 22, y + r - 22)], fill=(200, 155, 0))
        # hollow interior
        inner_r = r - 36
        draw.ellipse([(x - inner_r, y - inner_r), (x + inner_r, y + inner_r)], fill=(25, 20, 15))
        # interior rim highlight
        draw.ellipse([(x - inner_r + 4, y - inner_r + 4),
                      (x + inner_r - 4, y + inner_r - 4)], fill=(18, 14, 10), outline=(60, 50, 40), width=3)
        # top highlight on pipe face
        draw.ellipse([(x - r + 8, y - r + 8), (x - r + 55, y - r + 30)],
                     fill=(255, 220, 60))

    img = _vignette(img)
    if text:
        img = add_text_overlay(img, text)
    return img


# ─── IMAGE 3: Workers at gas compression / metering station ───────────────────
# Closely based on the reference photo: yellow foreground pipes with blue T-valve,
# 3 workers in blue coveralls + orange hard hats, white facility + barbed wire fence,
# gravel ground, red fire extinguisher bottom right, overcast sky.
def make_image3(text=""):
    import random
    rng = random.Random(42)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # ── Sky: flat overcast light grey ──
    for y in range(380):
        t = y / 380
        c = int(190 - 20 * t)
        draw.line([(0, y), (W, y)], fill=(c, c + 1, c + 3))

    # ── White industrial building (fills upper background) ──
    draw.rectangle([(0, 120), (W, 400)], fill=(215, 212, 208))
    # building panels / horizontal lines
    for py in range(140, 400, 55):
        draw.line([(0, py), (W, py)], fill=(195, 192, 188), width=2)
    # window strip near top
    for wx in range(80, W - 80, 140):
        draw.rectangle([(wx, 140), (wx + 90, 195)], fill=(160, 175, 190))
        draw.rectangle([(wx + 3, 143), (wx + 87, 192)], fill=(170, 185, 200))

    # ── Security fence with barbed wire across full width ──
    fence_y = 390
    for fx in range(0, W, 38):
        draw.rectangle([(fx, fence_y), (fx + 3, fence_y + 90)], fill=(90, 85, 80))
    draw.rectangle([(0, fence_y), (W, fence_y + 5)], fill=(100, 95, 90))
    draw.rectangle([(0, fence_y + 45), (W, fence_y + 50)], fill=(100, 95, 90))
    # chain-link mesh suggestion
    for fx in range(0, W, 18):
        draw.line([(fx, fence_y), (fx + 9, fence_y + 45)], fill=(110, 105, 100), width=1)
        draw.line([(fx + 9, fence_y), (fx, fence_y + 45)], fill=(110, 105, 100), width=1)
    # barbed wire coils on top
    for fx in range(0, W, 28):
        draw.ellipse([(fx, fence_y - 22), (fx + 22, fence_y + 2)],
                     outline=(160, 155, 145), width=2)

    # ── Gravel ground ──
    for y in range(480, H):
        t = (y - 480) / (H - 480)
        shade = int(155 - 35 * t)
        draw.line([(0, y), (W, y)], fill=(shade, shade - 6, shade - 10))
    for _ in range(5000):
        gx = rng.randint(0, W)
        gy = rng.randint(490, H - 5)
        gs = rng.randint(2, 6)
        gc = rng.randint(110, 165)
        draw.ellipse([(gx, gy), (gx + gs, gy + gs)],
                     fill=(gc, gc - 6, gc - 10))

    # ── LARGE YELLOW PIPES — dominant foreground, running left→right ──
    # Main pipe (biggest, lowest in frame)
    def draw_pipe_h(y_centre, radius, x0=0, x1=W, yellow=(215, 170, 0)):
        for i in range(-radius, radius):
            t = i / radius
            shade_r = int(yellow[0] * (1 - 0.55 * t * t))
            shade_g = int(yellow[1] * (1 - 0.55 * t * t))
            highlight = 40 if -0.45 < t < -0.05 else 0
            draw.line([(x0, y_centre + i), (x1, y_centre + i)],
                      fill=(min(255, shade_r + highlight),
                            min(255, shade_g + highlight), 0))

    # Three pipes stacked / branching
    draw_pipe_h(y_centre=680, radius=70)   # main large pipe foreground
    draw_pipe_h(y_centre=560, radius=52)   # upper secondary pipe
    draw_pipe_h(y_centre=790, radius=42, x0=400)  # lower branch

    # ── BLUE T-JUNCTION VALVE — prominent left-of-centre ──
    vx, vy = 480, 620
    # vertical riser pipe (yellow)
    draw_pipe_h(y_centre=vy, radius=48, x0=vx - 52, x1=vx + 52)
    # Blue valve body
    draw.rectangle([(vx - 65, vy - 55), (vx + 65, vy + 55)], fill=(25, 70, 185))
    draw.rectangle([(vx - 55, vy - 45), (vx + 55, vy + 45)], fill=(35, 85, 200))
    # flange bolts
    for angle in range(0, 360, 45):
        import math
        bx = vx + int(72 * math.cos(math.radians(angle)))
        by = vy + int(72 * math.sin(math.radians(angle)))
        draw.ellipse([(bx - 7, by - 7), (bx + 7, by + 7)], fill=(140, 130, 120))
    # valve stem going up
    draw.rectangle([(vx - 12, vy - 130), (vx + 12, vy - 55)], fill=(160, 150, 140))
    # handwheel
    wheel_y = vy - 145
    draw.ellipse([(vx - 45, wheel_y - 45), (vx + 45, wheel_y + 45)],
                 outline=(180, 170, 160), width=7)
    draw.line([(vx, wheel_y - 45), (vx, wheel_y + 45)], fill=(180, 170, 160), width=6)
    draw.line([(vx - 45, wheel_y), (vx + 45, wheel_y)], fill=(180, 170, 160), width=6)

    # ── More valves / fittings along the main pipe ──
    for fvx in [900, 1350]:
        draw.rectangle([(fvx - 42, 640), (fvx + 42, 720)], fill=(30, 75, 190))
        draw.rectangle([(fvx - 35, 635), (fvx + 35, 725)], fill=(40, 88, 205))
        draw.rectangle([(fvx - 10, 580), (fvx + 10, 640)], fill=(155, 145, 135))
        draw.ellipse([(fvx - 30, 545), (fvx + 30, 585)],
                     outline=(170, 160, 150), width=6)
        draw.line([(fvx - 30, 565), (fvx + 30, 565)], fill=(170, 160, 150), width=5)

    # Pipe end flange on far right
    draw.rectangle([(W - 30, 610), (W, 750)], fill=(170, 135, 0))
    draw.rectangle([(W - 50, 605), (W - 28, 755)], fill=(150, 120, 0))

    # ── Metal platform / raised walkway (right side) ──
    draw.rectangle([(1100, 620), (1900, 645)], fill=(110, 100, 90))
    for sx in range(1100, 1900, 30):
        draw.line([(sx, 620), (sx, 645)], fill=(85, 76, 68), width=2)
    # platform supports
    for px in [1150, 1400, 1650, 1850]:
        draw.rectangle([(px, 645), (px + 12, 800)], fill=(90, 82, 74))

    # ── Red FIRE EXTINGUISHER — bottom right ──
    ex, ey = 1800, 700
    draw.rectangle([(ex, ey), (ex + 42, ey + 170)], fill=(185, 28, 28))
    draw.rectangle([(ex + 10, ey - 22), (ex + 32, ey + 5)], fill=(155, 22, 22))
    draw.ellipse([(ex + 5, ey - 35), (ex + 37, ey - 10)], fill=(145, 20, 20))
    # hose
    draw.arc([(ex - 20, ey + 20), (ex + 20, ey + 80)], 0, 270, fill=(30, 25, 20), width=5)
    draw.rectangle([(ex - 20, ey + 165), (ex + 62, ey + 178)], fill=(80, 72, 65))

    # ── WORKERS — blue coveralls, orange hard hats ──
    # Worker 1: left-centre, leaning over pipe (crouching/bending)
    _draw_worker_station(draw, 700, 540, jacket=(38, 82, 175), hat=(215, 95, 15), crouching=True)
    # Worker 2: centre, standing upright working on valve
    _draw_worker_station(draw, 1000, 510, jacket=(38, 82, 175), hat=(215, 95, 15))
    # Worker 3: right, standing on platform
    _draw_worker_station(draw, 1280, 500, jacket=(38, 82, 175), hat=(215, 95, 15))

    img = _vignette(img)
    if text:
        img = add_text_overlay(img, text)
    return img


def _draw_worker_station(draw, x, y, jacket=(50, 100, 200), hat=(220, 100, 20), crouching=False):
    if crouching:
        # bent-over pose: torso angled forward
        draw.ellipse([(x - 18, y - 52), (x + 18, y - 14)], fill=hat)
        draw.rectangle([(x - 22, y - 30), (x + 22, y - 18)], fill=hat)
        draw.ellipse([(x - 14, y - 14), (x + 14, y + 14)], fill=(205, 170, 135))
        draw.polygon([(x - 28, y + 12), (x + 28, y + 12), (x + 50, y + 75), (x - 8, y + 75)], fill=jacket)
        draw.rectangle([(x - 28, y + 73), (x - 8, y + 130)], fill=(45, 50, 60))
        draw.rectangle([(x + 14, y + 73), (x + 50, y + 130)], fill=(45, 50, 60))
        draw.rectangle([(x - 30, y + 128), (x - 6, y + 146)], fill=(25, 20, 18))
        draw.rectangle([(x + 12, y + 128), (x + 52, y + 146)], fill=(25, 20, 18))
        draw.rectangle([(x + 26, y + 12), (x + 58, y + 55)], fill=jacket)
    else:
        draw.ellipse([(x - 18, y - 90), (x + 18, y - 52)], fill=hat)
        draw.rectangle([(x - 22, y - 68), (x + 22, y - 56)], fill=hat)
        draw.ellipse([(x - 14, y - 52), (x + 14, y - 24)], fill=(205, 170, 135))
        draw.rectangle([(x - 25, y - 24), (x + 25, y + 55)], fill=jacket)
        draw.rectangle([(x - 25, y + 8), (x + 25, y + 16)], fill=(220, 220, 60))
        draw.rectangle([(x + 22, y - 18), (x + 42, y + 28)], fill=jacket)
        draw.rectangle([(x - 42, y - 18), (x - 22, y + 28)], fill=jacket)
        draw.rectangle([(x - 22, y + 53), (x - 4, y + 120)], fill=(45, 50, 60))
        draw.rectangle([(x + 4, y + 53), (x + 22, y + 120)], fill=(45, 50, 60))
        draw.rectangle([(x - 24, y + 118), (x - 2, y + 136)], fill=(25, 20, 18))
        draw.rectangle([(x + 2, y + 118), (x + 24, y + 136)], fill=(25, 20, 18))


def _vignette(img):
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(280):
        alpha = int(140 * (i / 280) ** 2)
        vd.rectangle([i, i, W - i, H - i], outline=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")


if __name__ == "__main__":
    import json
    with open("output/secrets-of-gas-pipelines-no-one-knows/script.json") as f:
        segments = json.load(f)

    out = "output/secrets-of-gas-pipelines-no-one-knows/images"
    os.makedirs(out, exist_ok=True)

    print("Generating photo recreations...")
    # Assign: image1 → seg 0 (hidden world intro), seg 1 (3M miles)
    #         image2 → seg 2 (pressure facts), seg 3 (pig robot)
    #         image3 → seg 4 (unknown maps), seg 5 (mercaptan)
    # Keep Pillow text frames for segs 6,7,8 (darker/dramatic segments)

    assignments = {0: make_image1, 1: make_image1, 2: make_image2,
                   3: make_image2, 4: make_image3, 5: make_image3}

    for seg_i, fn in assignments.items():
        path = f"{out}/segment_{seg_i:03d}.png"
        print(f"  🖼️  Segment {seg_i+1} ({fn.__name__})...")
        img = fn(segments[seg_i]["text"])
        img.save(path)
        print(f"     Saved {path}")

    print("Done.")
