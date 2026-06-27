"""
Dreamy, colourful Pillow illustrations for Mason's bedtime story.
21 segments, each 1920x1080 with soft warm child-friendly style.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os, random
from pathlib import Path

W, H = 1920, 1080
rng = random.Random(7)


def font(size):
    for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def text_overlay(img, text, color=(255, 250, 235)):
    import textwrap
    draw = ImageDraw.Draw(img)
    f = font(50)
    lines = textwrap.wrap(text, width=52)
    lh = 62
    total = len(lines) * lh + 20
    oy = H - total - 35
    ov = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(ov)
    od.rectangle([(60, oy-14), (W-60, H-20)], fill=(0,0,0,165))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(img)
    y = oy
    for line in lines:
        bb = draw.textbbox((0,0), line, font=f)
        x = (W-(bb[2]-bb[0]))//2
        draw.text((x+2,y+2), line, fill=(0,0,0), font=f)
        draw.text((x,y), line, fill=color, font=f)
        y += lh
    return img


def vignette(img, strength=120):
    v = Image.new("RGBA", (W,H), (0,0,0,0))
    vd = ImageDraw.Draw(v)
    for i in range(300):
        a = int(strength*(i/300)**1.8)
        vd.rectangle([i,i,W-i,H-i], outline=(0,0,0,a))
    return Image.alpha_composite(img.convert("RGBA"), v).convert("RGB")


def grad(draw, top, bot, y0=0, y1=H):
    for y in range(y0, y1):
        t = (y-y0)/(y1-y0)
        r = int(top[0]+(bot[0]-top[0])*t)
        g = int(top[1]+(bot[1]-top[1])*t)
        b = int(top[2]+(bot[2]-top[2])*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))


def stars(draw, n=200, alpha_range=(80,220), size_range=(1,3)):
    for _ in range(n):
        sx = rng.randint(0,W)
        sy = rng.randint(0,H//2)
        sr = rng.randint(*size_range)
        sa = rng.randint(*alpha_range)
        c = rng.randint(200,255)
        draw.ellipse([(sx-sr,sy-sr),(sx+sr,sy+sr)], fill=(c,c,min(255,c+20)))


def moon(draw, cx, cy, r, col=(255,245,200)):
    draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)], fill=col)
    draw.ellipse([(cx-r+8,cy-r+8),(cx+r-8,cy+r-8)], fill=(min(255,col[0]+10),min(255,col[1]+10),min(255,col[2]+15)))


def mason_boy(draw, x, y, scale=1.0, eyes_closed=False, spacesuit=False):
    """Draw Mason: light skin, long black hair, warm smile."""
    s = scale
    # hair (long black, slightly wavy — drawn behind head)
    hair_col = (25, 18, 12)
    # hair sides hanging down
    draw.ellipse([int(x-32*s), int(y-105*s), int(x-8*s), int(y-20*s)], fill=hair_col)
    draw.ellipse([int(x+8*s), int(y-105*s), int(x+32*s), int(y-20*s)], fill=hair_col)
    # hair top/back
    draw.ellipse([int(x-28*s), int(y-120*s), int(x+28*s), int(y-58*s)], fill=hair_col)

    if spacesuit:
        # white helmet ring
        draw.ellipse([int(x-42*s), int(y-125*s), int(x+42*s), int(y-35*s)],
                     fill=(220,220,225), outline=(180,180,185), width=4)
        # visor (blue-tinted)
        draw.ellipse([int(x-32*s), int(y-115*s), int(x+32*s), int(y-45*s)],
                     fill=(140,180,220))
        # visor glare
        draw.ellipse([int(x-22*s), int(y-108*s), int(x-5*s), int(y-88*s)],
                     fill=(200,225,250))

    # head / face
    skin = (225, 195, 165)
    draw.ellipse([int(x-26*s), int(y-95*s), int(x+26*s), int(y-45*s)], fill=skin)
    # eyes
    if not spacesuit:
        if eyes_closed:
            draw.arc([int(x-16*s),int(y-80*s),int(x-4*s),int(y-70*s)], 0,180, fill=(50,35,25), width=3)
            draw.arc([int(x+4*s), int(y-80*s),int(x+16*s),int(y-70*s)], 0,180, fill=(50,35,25), width=3)
        else:
            draw.ellipse([int(x-15*s),int(y-82*s),int(x-5*s),int(y-70*s)], fill=(60,40,25))
            draw.ellipse([int(x+5*s), int(y-82*s),int(x+15*s),int(y-70*s)], fill=(60,40,25))
            draw.ellipse([int(x-13*s),int(y-80*s),int(x-7*s),int(y-74*s)], fill=(20,12,8))
            draw.ellipse([int(x+7*s), int(y-80*s),int(x+13*s),int(y-74*s)], fill=(20,12,8))
        # smile
        draw.arc([int(x-12*s),int(y-65*s),int(x+12*s),int(y-53*s)], 0,180, fill=(180,90,90), width=3)

    # body
    if spacesuit:
        body_col = (230,232,235)
        draw.rectangle([int(x-32*s),int(y-45*s),int(x+32*s),int(y+60*s)], fill=body_col)
        # MASON name tag
        nf = font(max(10, int(18*s)))
        draw.rectangle([int(x-24*s),int(y-28*s),int(x+24*s),int(y-14*s)], fill=(180,30,30))
        draw.text((int(x-18*s), int(y-28*s)), "MASON", fill=(255,255,255), font=nf)
        # silver trim
        draw.rectangle([int(x-32*s),int(y-45*s),int(x+32*s),int(y-38*s)], fill=(180,182,188))
        draw.rectangle([int(x-32*s),int(y+53*s),int(x+32*s),int(y+60*s)], fill=(180,182,188))
        # arms
        draw.rectangle([int(x+30*s),int(y-38*s),int(x+55*s),int(y+25*s)], fill=body_col)
        draw.rectangle([int(x-55*s),int(y-38*s),int(x-30*s),int(y+25*s)], fill=body_col)
        draw.ellipse([int(x+48*s),int(y+10*s),int(x+62*s),int(y+30*s)], fill=(190,192,195))
        draw.ellipse([int(x-62*s),int(y+10*s),int(x-48*s),int(y+30*s)], fill=(190,192,195))
        # legs
        draw.rectangle([int(x-28*s),int(y+58*s),int(x-6*s),int(y+130*s)], fill=body_col)
        draw.rectangle([int(x+6*s), int(y+58*s),int(x+28*s),int(y+130*s)], fill=body_col)
        draw.rectangle([int(x-30*s),int(y+125*s),int(x-4*s),int(y+145*s)], fill=(160,162,165))
        draw.rectangle([int(x+4*s), int(y+125*s),int(x+30*s),int(y+145*s)], fill=(160,162,165))
    else:
        pj_col = (100,140,200)
        draw.rectangle([int(x-28*s),int(y-45*s),int(x+28*s),int(y+55*s)], fill=pj_col)
        draw.rectangle([int(x+26*s),int(y-38*s),int(x+48*s),int(y+20*s)], fill=pj_col)
        draw.rectangle([int(x-48*s),int(y-38*s),int(x-26*s),int(y+20*s)], fill=pj_col)
        draw.ellipse([int(x+42*s),int(y+8*s),int(x+54*s),int(y+24*s)], fill=skin)
        draw.ellipse([int(x-54*s),int(y+8*s),int(x-42*s),int(y+24*s)], fill=skin)
        draw.rectangle([int(x-24*s),int(y+53*s),int(x-5*s),int(y+120*s)], fill=(60,80,120))
        draw.rectangle([int(x+5*s), int(y+53*s),int(x+24*s),int(y+120*s)], fill=(60,80,120))


def alien_friend(draw, x, y, scale=1.0):
    s = scale
    body_col = (160, 100, 220)
    # body (round)
    draw.ellipse([int(x-30*s),int(y-30*s),int(x+30*s),int(y+30*s)], fill=body_col)
    # big purple eyes
    draw.ellipse([int(x-20*s),int(y-22*s),int(x-4*s),int(y-6*s)], fill=(60,20,120))
    draw.ellipse([int(x+4*s), int(y-22*s),int(x+20*s),int(y-6*s)], fill=(60,20,120))
    draw.ellipse([int(x-17*s),int(y-19*s),int(x-9*s),int(y-11*s)], fill=(220,180,255))
    draw.ellipse([int(x+9*s), int(y-19*s),int(x+17*s),int(y-11*s)], fill=(220,180,255))
    # tiny wings
    draw.ellipse([int(x-55*s),int(y-25*s),int(x-25*s),int(y+5*s)], fill=(180,230,255))
    draw.ellipse([int(x+25*s), int(y-25*s),int(x+55*s),int(y+5*s)], fill=(180,230,255))
    # smile
    draw.arc([int(x-14*s),int(y+2*s),int(x+14*s),int(y+18*s)], 0,180, fill=(255,200,255), width=3)
    # tiny antenna
    draw.line([(x,int(y-30*s)),(x,int(y-50*s))], fill=body_col, width=3)
    draw.ellipse([int(x-6*s),int(y-58*s),int(x+6*s),int(y-46*s)], fill=(255,200,80))


def rocket(draw, cx, cy, scale=1.0, flame=True):
    s = scale
    # body
    draw.rectangle([int(cx-28*s),int(cy-120*s),int(cx+28*s),int(cy+80*s)], fill=(225,228,235))
    draw.rectangle([int(cx-22*s),int(cy-115*s),int(cx+22*s),int(cy+75*s)], fill=(240,242,248))
    # nose cone
    draw.polygon([
        (int(cx),        int(cy-160*s)),
        (int(cx-28*s),   int(cy-120*s)),
        (int(cx+28*s),   int(cy-120*s)),
    ], fill=(220,60,60))
    # window
    draw.ellipse([int(cx-16*s),int(cy-70*s),int(cx+16*s),int(cy-38*s)], fill=(140,195,235))
    draw.ellipse([int(cx-11*s),int(cy-65*s),int(cx+11*s),int(cy-43*s)], fill=(170,215,250))
    # fins
    draw.polygon([
        (int(cx-28*s),int(cy+40*s)),
        (int(cx-58*s),int(cy+80*s)),
        (int(cx-28*s),int(cy+80*s)),
    ], fill=(200,50,50))
    draw.polygon([
        (int(cx+28*s),int(cy+40*s)),
        (int(cx+58*s),int(cy+80*s)),
        (int(cx+28*s),int(cy+80*s)),
    ], fill=(200,50,50))
    # flame
    if flame:
        for fi, (fc, fw) in enumerate([((255,200,50),30),((255,140,20),20),((255,80,10),12)]):
            draw.polygon([
                (int(cx-fw*s), int(cy+78*s)),
                (int(cx+fw*s), int(cy+78*s)),
                (int(cx),      int(cy+(130+fi*20)*s)),
            ], fill=fc)


# ── SCENE BUILDERS ──────────────────────────────────────────────────────────

def s00(text):  # cozy bedroom
    img = Image.new("RGB",(W,H))
    d = ImageDraw.Draw(img)
    grad(d, (25,18,45), (55,35,70))
    # floor
    d.rectangle([(0,780),(W,H)], fill=(100,70,50))
    for x in range(0,W,80):
        d.line([(x,780),(x,H)], fill=(85,58,40), width=2)
    # walls
    d.rectangle([(0,0),(W,780)], fill=(55,35,65))
    grad(d, (45,28,58),(65,42,75),0,780)
    # window with starry sky
    wx,wy,ww,wh = 800,80,320,320
    d.rectangle([(wx,wy),(wx+ww,wy+wh)], fill=(8,10,35))
    stars(d,120,(100,255),(1,3))
    moon(d,wx+220,wy+80,40)
    d.rectangle([(wx-10,wy-10),(wx+ww+10,wy+wh+10)], outline=(180,150,100),width=10)
    d.line([(wx+ww//2,wy),(wx+ww//2,wy+wh)], fill=(180,150,100),width=6)
    d.line([(wx,wy+wh//2),(wx+ww,wy+wh//2)], fill=(180,150,100),width=6)
    # bed
    d.rectangle([(500,700),(1420,900)], fill=(180,100,80))
    d.rectangle([(500,650),(1420,710)], fill=(140,70,60))
    d.rectangle([(520,700),(1400,780)], fill=(220,180,140))
    # rocket ship duvet pattern
    for rx in range(560,1380,120):
        d.polygon([(rx,720),(rx-12,755),(rx+12,755)], fill=(200,60,60))
        d.rectangle([(rx-5,755),(rx+5,775)], fill=(180,50,50))
    # pillow
    d.ellipse([(580,660),(820,720)], fill=(240,230,215))
    # Mason in pyjamas, eyes closing
    mason_boy(d, 700, 780, scale=0.9, eyes_closed=True)
    # bedside lamp glow
    d.ellipse([(1350,500),(1480,700)], fill=(255,230,150))
    d.ellipse([(1370,520),(1460,680)], fill=(255,245,180))
    d.rectangle([(1400,698),(1430,780)], fill=(120,90,60))
    img = vignette(img,100)
    return text_overlay(img,text,(255,240,210))

def s01(text):  # boy at window
    img = Image.new("RGB",(W,H))
    d = ImageDraw.Draw(img)
    grad(d,(15,10,40),(35,22,58))
    stars(d,300,(120,255),(1,3))
    moon(d,1400,180,90)
    # Milky Way streak
    for i in range(200):
        sx=rng.randint(200,1700); sy=rng.randint(20,350)
        d.ellipse([(sx,sy),(sx+2,sy+2)],fill=(200,200,230))
    # floor
    d.rectangle([(0,820),(W,H)],fill=(80,55,40))
    # wall
    d.rectangle([(0,0),(W,820)],fill=(40,28,55))
    # big window
    d.rectangle([(660,60),(1260,740)],fill=(0,5,25))
    stars(d,400,(150,255),(1,4))
    moon(d,1050,250,80)
    d.rectangle([(650,50),(1270,750)],outline=(160,130,90),width=14)
    d.line([(960,50),(960,750)],fill=(160,130,90),width=8)
    d.line([(650,400),(1270,400)],fill=(160,130,90),width=8)
    # curtains
    d.polygon([(650,50),(650,750),(720,700),(740,50)],fill=(120,60,90))
    d.polygon([(1270,50),(1270,750),(1200,700),(1180,50)],fill=(120,60,90))
    # Mason standing at window, looking up, pyjamas
    mason_boy(d,960,820,scale=1.05,eyes_closed=False)
    # dream glow from window
    glow = Image.new("RGBA",(W,H),(0,0,0,0))
    gd = ImageDraw.Draw(glow)
    for r in range(200,0,-1):
        a=int(18*(1-r/200))
        gd.ellipse([(960-r,400-r),(960+r,400+r)],fill=(180,160,255,a))
    img=Image.alpha_composite(img.convert("RGBA"),glow).convert("RGB")
    img=vignette(img,130)
    return text_overlay(img,text,(220,210,255))

def s02(text):  # sleeping in bed
    img=s00("")
    # dim everything and make eyes fully closed
    dim=Image.new("RGBA",(W,H),(0,0,0,60))
    img=Image.alpha_composite(img.convert("RGBA"),dim).convert("RGB")
    d=ImageDraw.Draw(img)
    # floating ZZZs
    zf=font(60)
    for zi,(zx,zy,za) in enumerate([(780,580,180),(830,520,140),(890,470,100)]):
        d.text((zx,zy),"z"*(zi+1),fill=(200,200,255,za),font=zf)
    return text_overlay(img,text,(200,195,255))

def s03(text):  # magical transformation / dream portal
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(10,5,30),(40,15,60))
    stars(d,200,(100,255),(1,3))
    # swirling portal
    cx,cy=W//2,H//2
    for r in range(400,0,-8):
        t=r/400
        hue_r=int(80+120*math.sin(t*math.pi*3))
        hue_g=int(30+80*math.sin(t*math.pi*3+2))
        hue_b=int(150+105*math.sin(t*math.pi*3+4))
        a=int(200*(1-t))
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(cx-r,cy-r),(cx+r,cy+r)],outline=(hue_r,hue_g,hue_b,a),width=6)
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
        d=ImageDraw.Draw(img)
    # bright centre glow
    for r in range(120,0,-4):
        a=int(180*(1-r/120))
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(cx-r,cy-r),(cx+r,cy+r)],fill=(220,200,255,a))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
        d=ImageDraw.Draw(img)
    # bedroom remnants (fading)
    d.rectangle([(0,800),(W,H)],fill=(40,25,35))
    mason_boy(d,cx,850,scale=0.85,eyes_closed=False)
    img=vignette(img,140)
    return text_overlay(img,text,(240,220,255))

def s04(text):  # spacesuit reveal
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(5,5,20),(20,10,45))
    stars(d,400,(120,255),(1,4))
    # nebula background
    for _ in range(6):
        nx=rng.randint(100,W-100); ny=rng.randint(50,H-200)
        nr=rng.randint(100,250)
        nc=(rng.randint(80,160),rng.randint(20,80),rng.randint(150,255))
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(nx-nr,ny-nr),(nx+nr,ny+nr)],fill=(*nc,30))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
        d=ImageDraw.Draw(img)
    # ground (moon-like)
    d.rectangle([(0,820),(W,H)],fill=(60,58,65))
    for cx in range(0,W,200):
        cr=rng.randint(20,60)
        d.ellipse([(cx-cr,805),(cx+cr,820)],fill=(50,48,55))
    # Mason in spacesuit, hero pose
    mason_boy(d,W//2,880,scale=1.2,spacesuit=True)
    # golden light around him
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(160,0,-4):
        a=int(40*(1-r/160))
        od.ellipse([(W//2-r,880-200-r),(W//2+r,880-200+r)],fill=(255,230,100,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    img=vignette(img,110)
    return text_overlay(img,text,(240,240,255))

def s05(text):  # rocket on launchpad
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(8,8,30),(25,15,55))
    stars(d,300,(140,255),(1,3))
    moon(d,200,120,70,(255,240,190))
    # ground / launchpad
    d.rectangle([(0,860),(W,H)],fill=(50,50,55))
    d.rectangle([(700,830),(1220,870)],fill=(80,80,88))
    for sx in range(720,1200,30):
        d.line([(sx,830),(sx,870)],fill=(60,60,68),width=2)
    # launch tower
    d.rectangle([(1230,400),(1280,870)],fill=(90,88,95))
    for ty in range(420,870,60):
        d.line([(1230,ty),(1330,ty)],fill=(80,78,85),width=4)
    # searchlights
    for lx in [400,1500]:
        for r in range(80,0,-8):
            a=int(60*(1-r/80))
            ov=Image.new("RGBA",(W,H),(0,0,0,0))
            od=ImageDraw.Draw(ov)
            od.ellipse([(lx-r,H-r*3),(lx+r,H+r*3)],fill=(255,255,200,a))
            img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
            d=ImageDraw.Draw(img)
    # BIG ROCKET
    rocket(d,960,680,scale=2.0)
    # Mason tiny in window
    d.ellipse([(900,500),(1020,590)],fill=(140,195,235))
    d.ellipse([(920,515),(1000,575)],fill=(170,215,250))
    img=vignette(img,130)
    return text_overlay(img,text,(255,245,200))

def s06(text):  # blast off through clouds
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    # gradient: black to purple to blue
    grad(d,(5,3,15),(50,20,100))
    stars(d,250,(150,255),(1,3))
    # clouds (below, rushing past)
    for cy in range(600,H,80):
        for cx in range(0,W,180):
            cr=rng.randint(60,130)
            d.ellipse([(cx-cr,cy-30),(cx+cr,cy+30)],fill=(200,195,210))
    # rocket streak upward
    rocket(d,960,400,scale=1.6)
    # fire trail
    for i in range(20):
        ty=500+i*30; tw=int(50*(1-i/20))
        d.ellipse([(960-tw,ty),(960+tw,ty+25)],
                  fill=(255,max(0,200-i*10),0))
    img=vignette(img,120)
    return text_overlay(img,text,(255,230,180))

def s07(text):  # Earth from space
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(2,2,15),(8,5,25))
    stars(d,500,(100,255),(1,3))
    # Earth
    ex,ey,er=680,540,420
    d.ellipse([(ex-er,ey-er),(ex+er,ey+er)],fill=(20,80,200))
    # continents (rough)
    for cx,cy,cw,ch,cc in [
        (580,400,180,120,(40,160,60)),
        (680,490,140,180,(40,160,60)),
        (550,560,100,100,(40,160,60)),
        (780,430,120,90, (40,160,60)),
        (630,320,80,70,  (40,150,55)),
    ]:
        d.ellipse([(cx,cy),(cx+cw,cy+ch)],fill=cc)
    # cloud swirls
    for _,(cx,cy,cr) in enumerate([(620,350,80),(750,500,60),(550,480,70),(680,600,65)]):
        d.ellipse([(cx-cr,cy-20),(cx+cr,cy+20)],fill=(230,235,240))
    # atmosphere glow
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(er+60,er-1,-2):
        a=int(80*(1-(r-er)/60)) if r>er else 0
        od.ellipse([(ex-r,ey-r),(ex+r,ey+r)],outline=(100,160,255,a),width=4)
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # rocket window frame (right side)
    d.rectangle([(1300,200),(1880,880)],fill=(30,28,35))
    d.rectangle([(1330,230),(1850,850)],fill=(12,12,22))
    d.rectangle([(1290,190),(1890,890)],outline=(160,158,165),width=18)
    # Mason tiny at window (spacesuit)
    mason_boy(d,1590,810,scale=0.7,spacesuit=True)
    img=vignette(img,100)
    return text_overlay(img,text,(200,220,255))

def s08(text):  # studying star maps
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(5,3,18),(18,10,38))
    stars(d,200,(100,200),(1,2))
    # cockpit interior
    d.rectangle([(0,600),(W,H)],fill=(28,25,35))
    # control panels
    for px in range(100,W-100,200):
        d.rectangle([(px,620),(px+160,780)],fill=(35,32,45))
        for by in range(640,760,35):
            for bx in range(px+15,px+145,35):
                bc=(rng.randint(150,255),rng.randint(50,200),rng.randint(20,100))
                d.ellipse([(bx,by),(bx+20,by+20)],fill=bc)
    # central glowing screen (star map)
    d.rectangle([(500,350),(1420,620)],fill=(5,15,45))
    # star map dots and lines
    map_stars=[(rng.randint(520,1400),rng.randint(370,600)) for _ in range(80)]
    for mx,my in map_stars:
        d.ellipse([(mx-3,my-3),(mx+3,my+3)],fill=(200,220,255))
    for i in range(0,len(map_stars)-1,3):
        d.line([map_stars[i],map_stars[i+1]],fill=(100,120,200),width=1)
    # highlighted target planet (purple dot)
    d.ellipse([(1100,450),(1140,490)],fill=(180,80,255))
    for r in range(40,0,-5):
        a=int(120*(1-r/40))
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(1120-r,470-r),(1120+r,470+r)],fill=(200,120,255,a))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
        d=ImageDraw.Draw(img)
    d.rectangle([(498,348),(1422,622)],outline=(80,120,200),width=4)
    # Mason studying (spacesuit, leaning toward screen)
    mason_boy(d,960,740,scale=0.9,spacesuit=True)
    img=vignette(img,110)
    return text_overlay(img,text,(180,210,255))

def s09(text):  # landing on alien planet
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(20,5,40),(55,15,80))
    # three moons
    moon(d,300,120,55,(255,180,220))   # pink
    moon(d,960,80,65,(160,200,255))    # blue
    moon(d,1650,150,48,(220,220,240))  # silver
    stars(d,250,(140,255),(1,3))
    # alien planet surface
    grad(d,(40,10,70),(80,20,120),500,H)
    # crystal formations
    for ci in range(25):
        cx=rng.randint(0,W); cy=rng.randint(520,820)
        ch=rng.randint(40,160); cw=rng.randint(15,45)
        cc=(rng.randint(150,255),rng.randint(50,150),rng.randint(200,255))
        d.polygon([(cx,cy-ch),(cx-cw,cy),(cx+cw,cy)],fill=cc)
        d.polygon([(cx,cy-ch),(cx-cw//2,cy-ch+20),(cx+cw//2,cy-ch+20)],
                  fill=(min(255,cc[0]+50),min(255,cc[1]+50),min(255,cc[2]+30)))
    # sparkling ground
    for _ in range(600):
        gx=rng.randint(0,W); gy=rng.randint(820,H)
        gc=rng.randint(150,255)
        d.ellipse([(gx,gy),(gx+2,gy+2)],fill=(gc,gc//2,gc))
    d.rectangle([(0,820),(W,H)],fill=(55,15,85))
    # rocket landed
    rocket(d,1550,680,scale=1.2,flame=False)
    # Mason stepping out (spacesuit, small, beside rocket)
    mason_boy(d,1350,860,scale=0.85,spacesuit=True)
    img=vignette(img,120)
    return text_overlay(img,text,(230,200,255))

def s10(text):  # sparkling alien surface (3 moons)
    img=s09("")
    d=ImageDraw.Draw(img)
    # extra glowing plants
    for pi in range(12):
        px=rng.randint(200,1600); py=rng.randint(700,850)
        ph=rng.randint(50,130)
        pc=(rng.randint(80,180),rng.randint(200,255),rng.randint(150,230))
        d.line([(px,py),(px+rng.randint(-20,20),py-ph)],fill=pc,width=5)
        d.ellipse([(px-18,py-ph-18),(px+18,py-ph+18)],fill=pc)
    return text_overlay(img,text,(220,255,230))

def s11(text):  # meeting alien friend
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(20,5,45),(55,15,80))
    stars(d,180,(130,220),(1,3))
    moon(d,400,100,55,(255,190,230))
    # ground
    d.rectangle([(0,800),(W,H)],fill=(55,15,85))
    for _ in range(400):
        gx=rng.randint(0,W); gy=rng.randint(800,H)
        d.ellipse([(gx,gy),(gx+3,gy+3)],fill=(180,80,220))
    # big glowing rock
    d.ellipse([(800,680),(1100,840)],fill=(80,40,120))
    d.ellipse([(820,690),(1080,830)],fill=(95,50,140))
    for r in range(60,0,-8):
        a=int(80*(1-r/60))
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(950-r,760-r),(950+r,760+r)],fill=(200,150,255,a))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
        d=ImageDraw.Draw(img)
    # Mason kneeling (spacesuit)
    mason_boy(d,780,840,scale=0.9,spacesuit=True,eyes_closed=False)
    # alien friend peeking from behind rock
    alien_friend(d,1020,750,scale=0.9)
    img=vignette(img,115)
    return text_overlay(img,text,(255,220,255))

def s12(text):  # hand outstretched to alien
    img=s11("")
    d=ImageDraw.Draw(img)
    # warm glow between them
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(100,0,-5):
        a=int(60*(1-r/100))
        od.ellipse([(900-r,780-r),(900+r,780+r)],fill=(255,220,150,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    return text_overlay(img,text,(255,240,200))

def s13(text):  # alien smiles, planet lights up
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(30,10,55),(80,25,110))
    stars(d,300,(160,255),(1,4))
    moon(d,300,100,55,(255,200,230))
    moon(d,960,60,65,(170,210,255))
    moon(d,1650,140,48,(230,230,245))
    # rainbow explosion from centre
    for angle in range(0,360,8):
        rad=math.radians(angle)
        for r in range(50,500,12):
            hue=angle/360
            import colorsys
            rgb=colorsys.hsv_to_rgb(hue,0.9,1.0)
            rc=tuple(int(c*255) for c in rgb)
            ex=int(960+r*math.cos(rad)); ey=int(500+r*math.sin(rad))
            d.ellipse([(ex-4,ey-4),(ex+4,ey+4)],fill=rc)
    # ground
    d.rectangle([(0,840),(W,H)],fill=(70,20,100))
    # glowing plants
    for pi in range(20):
        px=rng.randint(0,W); py=rng.randint(750,850)
        ph=rng.randint(60,180)
        pc=(rng.randint(100,200),rng.randint(220,255),rng.randint(150,240))
        d.line([(px,py),(px,py-ph)],fill=pc,width=6)
        d.ellipse([(px-22,py-ph-22),(px+22,py-ph+22)],fill=pc)
    mason_boy(d,780,870,scale=0.9,spacesuit=True)
    alien_friend(d,1100,800,scale=1.1)
    img=vignette(img,100)
    return text_overlay(img,text,(255,255,200))

def s14(text):  # crystal bridge exploration
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(15,5,40),(45,12,70))
    stars(d,200,(120,220),(1,3))
    # purple river below
    grad(d,(80,20,160),(100,30,180),600,750)
    for rx in range(0,W,40):
        d.ellipse([(rx,600),(rx+rng.randint(20,60),620)],fill=(120,40,200))
    # crystal bridge
    for bx in range(200,W-200,30):
        by=620; bh=rng.randint(15,35)
        d.rectangle([(bx,by-bh),(bx+25,by)],fill=(180,230,255))
        d.rectangle([(bx+2,by-bh+2),(bx+23,by-2)],fill=(210,245,255))
    d.rectangle([(200,580),(W-200,600)],fill=(160,220,250))
    # ancient stone door
    d.rectangle([(840,200),(1080,620)],fill=(90,80,70))
    d.rectangle([(855,215),(1065,605)],fill=(100,88,78))
    # glowing symbols
    sf=font(28)
    for sym,sx,sy in [("✦",870,250),("◈",950,300),("⬡",1020,250),
                       ("◉",870,360),("✧",950,410),("◈",1020,360)]:
        d.text((sx,sy),sym,fill=(255,220,80),font=sf)
    # door glow
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(120,0,-8):
        a=int(60*(1-r/120))
        od.ellipse([(960-r,400-r),(960+r,400+r)],fill=(255,200,80,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # Mason crossing bridge
    mason_boy(d,500,640,scale=0.85,spacesuit=True)
    alien_friend(d,650,620,scale=0.7)
    img=vignette(img,120)
    return text_overlay(img,text,(220,240,255))

def s15(text):  # stars bursting free
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(5,3,15),(20,8,40))
    # EXPLOSION of stars from open door
    for _ in range(800):
        angle=rng.uniform(0,2*math.pi)
        dist=rng.uniform(50,700)
        sx=int(960+dist*math.cos(angle))
        sy=int(400+dist*math.sin(angle)*0.6)
        sr=rng.randint(1,5)
        sc=rng.randint(180,255)
        d.ellipse([(sx-sr,sy-sr),(sx+sr,sy+sr)],fill=(sc,sc,min(255,sc+40)))
    # streaking shooting stars
    for _ in range(30):
        sx=rng.randint(100,W-100); sy=rng.randint(50,500)
        sl=rng.randint(30,120)
        angle=rng.uniform(-0.8,0.8)
        ex2=int(sx+sl*math.cos(angle)); ey2=int(sy-sl)
        d.line([(sx,sy),(ex2,ey2)],fill=(255,255,200),width=rng.randint(1,3))
    # open door glow at centre
    d.rectangle([(840,200),(1080,650)],fill=(255,240,180))
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(250,0,-5):
        a=int(80*(1-r/250))
        od.ellipse([(960-r,420-r),(960+r,420+r)],fill=(255,235,150,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # ground
    d.rectangle([(0,850),(W,H)],fill=(35,10,60))
    mason_boy(d,800,880,scale=0.9,spacesuit=True)
    alien_friend(d,1050,850,scale=0.85)
    img=vignette(img,110)
    return text_overlay(img,text,(255,250,200))

def s16(text):  # goodbye, hugging alien
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(18,5,42),(50,15,75))
    stars(d,200,(130,240),(1,3))
    moon(d,400,110,55,(255,195,225))
    moon(d,1620,130,48,(230,232,248))
    # planet surface
    d.rectangle([(0,820),(W,H)],fill=(55,15,82))
    for _ in range(300):
        gx=rng.randint(0,W); gy=rng.randint(820,H)
        d.ellipse([(gx,gy),(gx+3,gy+3)],fill=(170,70,210))
    # rocket glowing ready to leave
    rocket(d,1500,640,scale=1.2,flame=True)
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    for r in range(120,0,-6):
        a=int(50*(1-r/120))
        od.ellipse([(1500-r,640-r),(1500+r,640+r)],fill=(255,200,80,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # Mason and alien hug
    mason_boy(d,820,870,scale=0.95,spacesuit=True)
    alien_friend(d,1020,840,scale=1.0)
    # warm glow between them
    ov2=Image.new("RGBA",(W,H),(0,0,0,0))
    od2=ImageDraw.Draw(ov2)
    for r in range(80,0,-4):
        a=int(55*(1-r/80))
        od2.ellipse([(920-r,850-r),(920+r,850+r)],fill=(255,230,180,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov2).convert("RGB")
    img=vignette(img,115)
    return text_overlay(img,text,(255,235,215))

def s17(text):  # rocket lifting off planet
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(10,4,30),(35,10,60))
    stars(d,350,(140,255),(1,3))
    # planet surface receding at bottom
    grad(d,(55,15,85),(80,25,115),820,H)
    d.ellipse([(-200,880),(W+200,1200)],fill=(65,18,100))
    # crystals tiny at bottom
    for ci in range(15):
        cx=rng.randint(0,W); cy=rng.randint(850,920)
        d.polygon([(cx,cy-30),(cx-10,cy),(cx+10,cy)],fill=(180,80,240))
    # rocket ascending
    rocket(d,960,380,scale=1.5,flame=True)
    # big flame trail
    for i in range(25):
        ty=560+i*28; tw=int(60*(1-i/25))
        a=255-i*8
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(960-tw,ty),(960+tw,ty+20)],fill=(255,max(0,180-i*7),0,a))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    # alien waving tiny at bottom
    alien_friend(d,rng.randint(400,600),H-60,scale=0.5)
    img=vignette(img,125)
    return text_overlay(img,text,(220,200,255))

def s18(text):  # sailing through galaxy home
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(3,2,12),(15,8,30))
    # rich galaxy
    stars(d,600,(80,255),(1,4))
    # colourful nebula clouds
    for nx,ny,nr,nc in [
        (400,300,280,(100,30,180)),
        (1400,200,220,(20,100,200)),
        (800,700,200,(180,50,100)),
        (1600,700,180,(50,180,150)),
        (200,600,160,(160,80,200)),
    ]:
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        od=ImageDraw.Draw(ov)
        od.ellipse([(nx-nr,ny-nr),(nx+nr,ny+nr)],fill=(*nc,45))
        img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # comets
    for cx2,cy2 in [(300,200),(1600,350),(500,700)]:
        d.line([(cx2,cy2),(cx2+120,cy2-40)],fill=(255,255,220),width=3)
        for ti in range(5):
            d.line([(cx2-ti*15,cy2+ti*5),(cx2-ti*15+80,cy2+ti*5-25)],
                   fill=(255,255,200-ti*30),width=max(1,3-ti))
    # Earth visible ahead
    ex2,ey2,er2=1500,500,200
    d.ellipse([(ex2-er2,ey2-er2),(ex2+er2,ey2+er2)],fill=(20,80,200))
    d.ellipse([(1420,420),(1560,520)],fill=(40,160,60))
    d.ellipse([(1480,480),(1580,560)],fill=(40,160,60))
    # rocket heading toward Earth
    rocket(d,700,540,scale=1.1,flame=False)
    img=vignette(img,100)
    return text_overlay(img,text,(210,230,255))

def s19(text):  # dream fading back to bedroom
    img=s00("")
    ov=Image.new("RGBA",(W,H),(0,0,0,0))
    od=ImageDraw.Draw(ov)
    # space elements fading in from edges
    for r in range(300,0,-10):
        a=int(90*(r/300))
        od.ellipse([(W//2-r,H//2-r),(W//2+r,H//2+r)],fill=(80,50,150,a))
    img=Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")
    d=ImageDraw.Draw(img)
    # faint stars overlaid
    for _ in range(80):
        sx=rng.randint(0,W); sy=rng.randint(0,H//2)
        d.ellipse([(sx,sy),(sx+2,sy+2)],fill=(200,200,255))
    return text_overlay(img,text,(220,215,255))

def s20(text):  # Mason sleeping, stars smiling
    img=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(img)
    grad(d,(18,12,38),(40,25,55))
    # warm bedroom glow
    d.rectangle([(0,750),(W,H)],fill=(90,55,38))
    for x in range(0,W,80):
        d.line([(x,750),(x,H)],fill=(75,45,30),width=2)
    # walls
    grad(d,(38,25,52),(52,35,65),0,750)
    # window stars — smiling night
    wx2,wy2,ww2,wh2=750,60,420,380
    d.rectangle([(wx2,wy2),(wx2+ww2,wy2+wh2)],fill=(6,8,28))
    stars(d,200,(150,255),(2,4))
    # smiley moon
    moon(d,wx2+300,wy2+100,65)
    d2=ImageDraw.Draw(img)
    d2.arc([(wx2+270,wy2+100),(wx2+330,wy2+140)],0,180,fill=(180,150,60),width=4)
    d2.ellipse([(wx2+283,wy2+85),(wx2+294,wy2+96)],fill=(180,150,60))
    d2.ellipse([(wx2+306,wy2+85),(wx2+317,wy2+96)],fill=(180,150,60))
    d2.rectangle([(wx2-10,wy2-10),(wx2+ww2+10,wy2+wh2+10)],outline=(160,130,90),width=12)
    # bed
    d2.rectangle([(420,720),(1500,920)],fill=(170,90,72))
    d2.rectangle([(420,670),(1500,730)],fill=(130,62,54))
    d2.rectangle([(440,720),(1480,800)],fill=(215,172,135))
    for rx in range(480,1460,120):
        d2.polygon([(rx,738),(rx-10,768),(rx+10,768)],fill=(195,52,52))
        d2.rectangle([(rx-4,768),(rx+4,788)],fill=(175,42,42))
    # pillow
    d2.ellipse([(480,672),(740,732)],fill=(238,228,212))
    # Mason sleeping, huge smile
    mason_boy(d2,640,800,scale=0.88,eyes_closed=True)
    # bedside lamp
    d2.ellipse([(1340,490),(1470,690)],fill=(255,225,145))
    d2.ellipse([(1358,508),(1452,672)],fill=(255,242,175))
    d2.rectangle([(1388,688),(1418,770)],fill=(115,85,55))
    # tiny floating stars/sparkles around Mason
    for _,(sx,sy) in enumerate([(580,650),(720,620),(640,590),(560,710),(740,680)]):
        d2.ellipse([(sx-5,sy-5),(sx+5,sy+5)],fill=(255,230,120))
        d2.line([(sx-9,sy),(sx+9,sy)],fill=(255,230,120),width=2)
        d2.line([(sx,sy-9),(sx,sy+9)],fill=(255,230,120),width=2)
    img=vignette(img,90)
    return text_overlay(img,text,(255,248,215))


SCENES = [s00,s01,s02,s03,s04,s05,s06,s07,s08,s09,
          s10,s11,s12,s13,s14,s15,s16,s17,s18,s19,s20]


if __name__=="__main__":
    import json, sys
    sys.path.insert(0,"/home/user/paperqqq")
    with open("/home/user/paperqqq/output/mason-the-brave-astronaut/script.json") as f:
        segments=json.load(f)
    out="/home/user/paperqqq/output/mason-the-brave-astronaut/images"
    os.makedirs(out,exist_ok=True)
    for i,(scene_fn,seg) in enumerate(zip(SCENES,segments)):
        path=f"{out}/segment_{i:03d}.png"
        print(f"  🖼️  Scene {i+1}/21 ...")
        img=scene_fn(seg["text"])
        img.save(path)
    print("All scenes done.")
