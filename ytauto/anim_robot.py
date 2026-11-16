"""Animación «un robot en un partido normal»: jugadores con ciclo de carrera, sombras y cámara que sigue la jugada."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import anim as A

BOLD = A.BOLD
WHITE = (255, 255, 255)
RED, BLUE = (220, 45, 55), (40, 100, 230)
SKINS = [(241, 194, 150), (198, 134, 90), (141, 85, 52), (224, 172, 125)]
CYAN = (40, 230, 255)


def _e(x):
    return A._ease(x)


def player(d, x, y, s, col, phase, num="", skin=(224, 172, 125), run=1.0):
    """Jugador humano visto en 3/4: (x, y) = pies. phase = fase del ciclo de carrera."""
    sw = math.sin(phase) * run
    d.ellipse([x - 22 * s, y - 6 * s, x + 22 * s, y + 6 * s], fill=(0, 0, 0, 90) if False else (20, 70, 35))
    hip = (x, y - 40 * s)
    for k, sg in ((0, 1), (1, -1)):
        knee = (x + sg * sw * 14 * s, y - 20 * s)
        foot = (x + sg * sw * 22 * s, y - max(0, sg * sw) * 10 * s)
        c = (230, 230, 235) if k else (205, 205, 215)
        d.line([hip, knee, foot], fill=c, width=int(9 * s), joint="curve")
        d.ellipse([foot[0] - 6 * s, foot[1] - 4 * s, foot[0] + 8 * s, foot[1] + 4 * s], fill=(25, 25, 30))
    d.rounded_rectangle([x - 15 * s, y - 50 * s, x + 15 * s, y - 36 * s], 4 * s, fill=(30, 30, 40))
    d.rounded_rectangle([x - 17 * s, y - 84 * s, x + 17 * s, y - 46 * s], 8 * s, fill=col)
    for sg in (1, -1):
        sh = (x + sg * 15 * s, y - 80 * s)
        hand = (x + sg * 20 * s - sg * sw * 4 * s, y - 58 * s - sg * sw * 12 * s)
        d.line([sh, hand], fill=skin, width=int(7 * s))
    if num:
        f = ImageFont.truetype(BOLD, max(8, int(20 * s)))
        d.text((x - d.textlength(num, font=f) / 2, y - 80 * s), num, font=f, fill=WHITE)
    d.ellipse([x - 11 * s, y - 108 * s, x + 11 * s, y - 86 * s], fill=skin)
    d.chord([x - 11 * s, y - 109 * s, x + 11 * s, y - 92 * s], 180, 360, fill=(40, 28, 20))


def robot(d, x, y, s, phase, run=1.0, eyes=CYAN, glow=0.0):
    """Robot humanoide plateado con el mismo ciclo de carrera."""
    sw = math.sin(phase) * run
    d.ellipse([x - 24 * s, y - 6 * s, x + 24 * s, y + 6 * s], fill=(20, 70, 35))
    if glow > 0:
        r = 60 * s
        d.ellipse([x - r, y - 8 * s - r * 0.3, x + r, y - 8 * s + r * 0.3], outline=CYAN, width=max(2, int(4 * s * glow)))
    hip = (x, y - 42 * s)
    for sg in (1, -1):
        knee = (x + sg * sw * 14 * s, y - 21 * s)
        foot = (x + sg * sw * 22 * s, y - max(0, sg * sw) * 10 * s)
        d.line([hip, knee, foot], fill=(150, 158, 172), width=int(10 * s), joint="curve")
        d.ellipse([knee[0] - 5 * s, knee[1] - 5 * s, knee[0] + 5 * s, knee[1] + 5 * s], fill=(90, 96, 110))
        d.rounded_rectangle([foot[0] - 7 * s, foot[1] - 5 * s, foot[0] + 10 * s, foot[1] + 4 * s], 2 * s, fill=(60, 64, 76))
    d.rounded_rectangle([x - 19 * s, y - 88 * s, x + 19 * s, y - 44 * s], 9 * s, fill=(196, 204, 216), outline=(90, 96, 110), width=max(1, int(2 * s)))
    d.ellipse([x - 7 * s, y - 74 * s, x + 7 * s, y - 60 * s], fill=eyes)
    for sg in (1, -1):
        sh = (x + sg * 19 * s, y - 82 * s)
        hand = (x + sg * 24 * s - sg * sw * 5 * s, y - 58 * s - sg * sw * 12 * s)
        d.line([sh, hand], fill=(150, 158, 172), width=int(8 * s))
    d.rounded_rectangle([x - 14 * s, y - 114 * s, x + 14 * s, y - 90 * s], 7 * s, fill=(210, 216, 226), outline=(90, 96, 110), width=max(1, int(2 * s)))
    d.rounded_rectangle([x - 11 * s, y - 108 * s, x + 11 * s, y - 99 * s], 4 * s, fill=(12, 16, 26))
    d.rectangle([x - 8 * s, y - 106 * s, x + 8 * s, y - 101 * s], fill=eyes)


def ball(d, x, y, r=9, h=0.0):
    d.ellipse([x - r, y - 3, x + r, y + 3], fill=(20, 70, 35))
    d.ellipse([x - r, y - r - h, x + r, y + r - h], fill=WHITE, outline=(20, 20, 20), width=2)


def cam(im, fx, fy, z):
    """Cámara: zoom z centrado en (fx, fy)."""
    W, H = im.size
    cw, ch = W / z, H / z
    x0 = min(max(fx - cw / 2, 0), W - cw)
    y0 = min(max(fy - ch / 2, 0), H - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)


def _field(im):
    A._pitch(im, 0, run=0, players=False)


def _team(t, focus, rng_seed=5):
    """Posiciones de 21 humanos que se mueven hacia el balón."""
    rng = random.Random(rng_seed)
    out = []
    for k in range(20):
        team = k % 2
        bx = rng.uniform(0.12, 0.88) * A.PW
        by = (rng.uniform(0.15, 0.48) if team == 0 else rng.uniform(0.52, 0.85)) * A.PH
        ph = rng.uniform(0, 6.28)
        x = bx + (focus[0] - bx) * 0.15 + 18 * math.sin(t * 1.4 + ph)
        y = by + (focus[1] - by) * 0.15 + 14 * math.cos(t * 1.1 + ph)
        out.append((x, y, BLUE if team else RED, str(rng.randint(2, 23)), SKINS[k % 4], ph))
    return out


def _draw_people(d, people, t, s=0.62, run=1.0):
    for x, y, col, num, skin, ph in sorted(people, key=lambda p: p[1]):
        player(d, x, y, s, col, t * 9 + ph, num, skin, run)


def render(kind, t, dur):
    """Devuelve la imagen (PW x PH) o None si `kind` no es de este módulo."""
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    if kind == "r_fichaje":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(16, 40, 110))
        f = ImageFont.truetype(BOLD, 34)
        for yy in range(0, PH, 90):
            for xx in range(-40 + (yy // 90 % 2) * 70, PW, 140):
                d.text((xx, yy), "DC", font=f, fill=(30, 62, 150))
        d.rectangle([0, PH * 0.66, PW, PH], fill=(22, 24, 34))
        rx, ry = PW / 2, PH * 0.66
        lift = _e((t - 0.8) / 0.6)
        robot(d, rx, ry, 1.5, 0, run=0)
        jx, jy = rx, ry - 340 - 50 * lift
        d.polygon([(jx - 70, jy), (jx - 40, jy - 22), (jx + 40, jy - 22), (jx + 70, jy), (jx + 50, jy + 22),
                   (jx + 40, jy + 10), (jx + 40, jy + 110), (jx - 40, jy + 110), (jx - 40, jy + 10), (jx - 50, jy + 22)],
                  fill=RED, outline=WHITE)
        f2 = ImageFont.truetype(BOLD, 60)
        d.text((jx - d.textlength("0", font=f2) / 2, jy + 12), "0", font=f2, fill=WHITE)
        for sg in (1, -1):
            d.line([(rx + sg * 28, ry - 124), (jx + sg * 40, jy + 100)], fill=(150, 158, 172), width=12)
        rng = random.Random(int(t * 6))
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for _ in range(3):
            x, y = rng.choice([rng.uniform(20, PW * 0.3), rng.uniform(PW * 0.7, PW - 20)]), rng.uniform(PH * 0.35, PH * 0.62)
            r = rng.uniform(14, 30)
            ld.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
            ld.ellipse([x - r * 1.7, y - r * 1.7, x + r * 1.7, y + r * 1.7], fill=(255, 255, 255, 90))
        bl = lay.filter(ImageFilter.GaussianBlur(4))
        im.paste(bl, (0, 0), bl)
        im = cam(im, rx, ry - 230, 1.2 + 0.2 * _e(t / 3))
        if t > 1.3:
            k = _e((t - 1.3) / 0.25)
            st = Image.new("RGBA", (640, 120), (0, 0, 0, 0))
            sd = ImageDraw.Draw(st)
            sd.rounded_rectangle([0, 0, 639, 119], 18, fill=(255, 214, 10), outline=(10, 12, 20), width=6)
            f3 = ImageFont.truetype(BOLD, 64)
            sd.text((320 - sd.textlength("¡FICHAJE OFICIAL!", font=f3) / 2, 18), "¡FICHAJE OFICIAL!", font=f3, fill=(10, 12, 20))
            sc = 1.6 - 0.6 * k
            st = st.resize((int(640 * sc), int(120 * sc))).rotate(-5, expand=True, resample=Image.BICUBIC)
            im.paste(st, (int(PW / 2 - st.width / 2), int(PH * 0.28 - st.height / 2)), st)
    elif kind == "r_partido":
        _field(im)
        d = ImageDraw.Draw(im)
        bxy = (PW / 2 + 120 * math.sin(t * 0.7), PH * 0.5 + 60 * math.sin(t * 1.1))
        ppl = _team(t, bxy)
        rx, ry = PW * 0.58 + 20 * math.sin(t), PH * 0.56
        _draw_people(d, [p for p in ppl if p[1] < ry], t)
        robot(d, rx, ry, 0.64, t * 9, glow=min(1, max(0, t - 1.5)))
        _draw_people(d, [p for p in ppl if p[1] >= ry], t)
        ball(d, *bxy)
        z = 1 + 1.1 * _e((t - 1.0) / 1.6)
        im = cam(im, rx * (z > 1.05) + PW / 2 * (z <= 1.05), ry - 40, z)
        if t > 1.8:
            d = ImageDraw.Draw(im)
            A._label(d, PW / 2, PH * 0.31, "Debut del n.º 0", 44, CYAN, center=True)
    elif kind == "r_scan":
        _field(im)
        d = ImageDraw.Draw(im)
        rx, ry = PW * 0.5, PH * 0.66
        ppl = _team(0.5, (rx, ry))
        _draw_people(d, ppl, 0.5, run=0.2)
        robot(d, rx, ry, 0.8, 0, run=0)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        a = -150 + 120 * ((t * 0.6) % 1)
        ld.pieslice([rx - 900, ry - 100 - 900, rx + 900, ry - 100 + 900], a - 18, a + 18, fill=CYAN + (55,))
        n = min(20, int(t * 8))
        for x, y, *_ in ppl[:n]:
            ld.rectangle([x - 22, y - 80, x + 22, y + 6], outline=CYAN + (230,), width=3)
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im)
        im = cam(im, rx, PH * 0.5, 1.25)
        d = ImageDraw.Draw(im)
        A._label(d, PW / 2, PH * 0.31, f"ANALIZANDO {n}/20 RIVALES", 40, CYAN, center=True)
    elif kind == "r_sprint":
        _field(im)
        d = ImageDraw.Draw(im)
        p = min(t / max(dur - 0.6, 1), 1)
        rx, ry = PW * 0.5 + 60 * math.sin(p * 6), PH * (0.8 - 0.5 * p)
        defs = [(PW * 0.38, PH * 0.62), (PW * 0.62, PH * 0.52), (PW * 0.45, PH * 0.42), (PW * 0.58, PH * 0.34)]
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        for k in range(1, 10):
            q = max(0, p - k * 0.012)
            tx, ty = PW * 0.5 + 60 * math.sin(q * 6), PH * (0.8 - 0.5 * q)
            ld.line([(tx - 18, ty - 60), (tx + 18, ty - 60)], fill=CYAN + (200 - 20 * k,), width=6)
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im)
        for i, (x, y) in enumerate(defs):
            passed = ry < y - 10
            player(d, x + (20 if passed else 0) * math.sin(t * 12), y, 0.66, BLUE, t * 4 + i, str(4 + i), SKINS[i], run=0.4 if passed else 1)
            if passed:
                f = ImageFont.truetype(BOLD, 34)
                d.text((x + 20, y - 130), "?!", font=f, fill=(255, 214, 10))
        robot(d, rx, ry, 0.72, t * 16)
        ball(d, rx + 16, ry - 2)
        im = cam(im, rx, ry - 50, 1.9)
        d = ImageDraw.Draw(im)
        A._label(d, 24, PH * 0.31, "36 km/h: el récord humano", 34, WHITE)
        A._label(d, 24, PH * 0.31 + 56, "Robot: sin cansarse", 34, CYAN)
    elif kind == "r_gol":
        sd = ImageDraw.Draw(im)
        for i in range(12):
            sd.rectangle([i * PW / 12, 0, (i + 1) * PW / 12, PH], fill=A.GRASS[i % 2])
        d = ImageDraw.Draw(im)
        gx, gy = PW / 2, PH * 0.44
        d.rectangle([gx - 230, gy, gx + 230, gy + 150], outline=WHITE, width=5)
        d.rectangle([gx - 110, gy, gx + 110, gy + 50], outline=WHITE, width=5)
        d.rectangle([gx - 100, gy - 70, gx + 100, gy], fill=(30, 90, 50))
        d.rectangle([gx - 100, gy - 70, gx + 100, gy], outline=WHITE, width=6)
        rx, ry = PW * 0.56, PH * 0.66
        shot = 0.7
        k = max(0.0, min((t - shot) / 0.35, 1))
        bx, by = rx + (gx + 70 - rx) * k, ry - 4 + (gy - 30 - ry + 4) * k
        dive = _e((t - shot - 0.1) / 0.4)
        player(d, gx - 70 * dive, gy + 30, 0.9, (255, 214, 10), 0, "1", SKINS[1], run=0)
        net = Image.new("RGBA", im.size, (0, 0, 0, 0))
        nd = ImageDraw.Draw(net)
        bulge = 14 * math.sin(min(max(t - shot - 0.35, 0) * 8, math.pi)) if t > shot + 0.35 else 0
        for i in range(9):
            x = gx - 100 + i * 25
            nd.line([(x, gy - 68 - bulge * (1 - abs(i - 6) / 6)), (x, gy)], fill=(255, 255, 255, 150), width=2)
        im.paste(net, (0, 0), net)
        d = ImageDraw.Draw(im)
        robot(d, rx, ry, 0.95, t * 8 if t < shot else 0, run=1.0 if t < shot else 0.0)
        if k > 0 and k < 1:
            for j in range(1, 8):
                q = max(0, k - j * 0.05)
                d.ellipse([rx + (gx + 70 - rx) * q - 7, ry + (gy - 30 - ry) * q - 7, rx + (gx + 70 - rx) * q + 7, ry + (gy - 30 - ry) * q + 7], fill=(255, 230 - 20 * j, 120))
        ball(d, bx, by, 10)
        z = 1.8 + 0.4 * _e((t - shot - 0.3) / 0.5)
        im = cam(im, gx, gy + 140, z - 0.3)
        if t > shot + 0.4:
            d = ImageDraw.Draw(im)
            f = ImageFont.truetype(BOLD, 150)
            sc = _e((t - shot - 0.4) / 0.3)
            txt = Image.new("RGBA", (700, 200), (0, 0, 0, 0))
            ImageDraw.Draw(txt).text((350 - d.textlength("¡GOL!", font=f) / 2, 10), "¡GOL!", font=f, fill=(255, 214, 10), stroke_width=8, stroke_fill=(10, 12, 20))
            txt = txt.resize((max(1, int(700 * sc)), max(1, int(200 * sc))))
            im.paste(txt, (int(PW / 2 - txt.width / 2), int(PH * 0.5 - txt.height / 2)), txt)
    elif kind == "r_roja":
        _field(im)
        d = ImageDraw.Draw(im)
        rx, ry = PW * 0.6, PH * 0.62
        ax = PW * 0.12 + (PW * 0.36 - PW * 0.12) * _e(t / 0.8)
        robot(d, rx, ry, 0.95, 0, run=0, eyes=(255, 60, 60) if t > 1.3 else CYAN)
        player(d, ax, ry + 10, 0.95, (20, 20, 24), t * 10, "", SKINS[0], run=1 - _e(t / 0.8))
        if t > 0.9:
            k = _e((t - 0.9) / 0.25)
            cx, cy = ax + 26, ry - 110 - 50 * k
            d.rounded_rectangle([cx - 20, cy - 30, cx + 20, cy + 30], 5, fill=(230, 30, 40), outline=WHITE, width=2)
        im = cam(im, (rx + ax) / 2, ry - 70, 2.2)
        if t > 1.2:
            d = ImageDraw.Draw(im)
            A._label(d, PW / 2, PH * 0.31, "Sin ficha no se juega", 44, (255, 90, 90), center=True)
    elif kind == "r_caida":
        _field(im)
        d = ImageDraw.Draw(im)
        rx, ry = PW * 0.5, PH * 0.64
        ang = 90 * _e((t - 0.6) / 0.5) if t > 0.6 else 0
        lay = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        robot(ImageDraw.Draw(lay), 150, 260, 1.0, t * 12 if t < 0.6 else 0, run=1 if t < 0.6 else 0)
        lay = lay.rotate(-ang, center=(150, 260), resample=Image.BICUBIC)
        im.paste(lay, (int(rx - 150), int(ry - 260)), lay)
        d = ImageDraw.Draw(im)
        bx = rx + 30 + 260 * _e((t - 0.5) / 1.0)
        ball(d, bx, ry, 10, h=60 * abs(math.sin(min(t, 2) * 5)) * max(0, 1 - t / 2))
        if t > 1.1:
            f = ImageFont.truetype(BOLD, 60)
            d.text((rx - 60, ry - 150), "*CLONK*", font=f, fill=(255, 214, 10), stroke_width=5, stroke_fill=(10, 12, 20))
        im = cam(im, rx + 80, ry - 60, 2.0)
        d = ImageDraw.Draw(im)
        A._label(d, PW / 2, PH * 0.31, "RoboCup: aún se caen mucho", 40, CYAN, center=True)
    else:
        return None
    return im
