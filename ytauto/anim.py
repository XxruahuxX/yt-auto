"""Animaciones dibujadas dentro del panel del estilo karaoke (todo procedural, sin material ajeno).

Uso en el guion: `anim: campo | aviso | meteorito | airburst | impacto | crater | suspendido`.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
PW, PH = 860, 460
IMPACT = 1.0          # segundo de la escena en que el meteorito toca el suelo
AIRBURST = 0.9
GRASS = ((34, 120, 62), (40, 134, 70))
WHITE = (255, 255, 255)

_mask = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(_mask).rounded_rectangle([0, 0, PW - 1, PH - 1], 44, fill=255)


def _ease(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def _pitch(im: Image.Image, t: float, run: float = 1.0, scale: float = 1.0) -> None:
    d = ImageDraw.Draw(im)
    for i in range(12):
        d.rectangle([i * PW / 12, 0, (i + 1) * PW / 12, PH], fill=GRASS[i % 2])
    m = 40
    x0, y0, x1, y1 = m, m, PW - m, PH - m
    lw = 5
    d.rectangle([x0, y0, x1, y1], outline=WHITE, width=lw)
    d.line([(PW / 2, y0), (PW / 2, y1)], fill=WHITE, width=lw)
    d.ellipse([PW / 2 - 60, PH / 2 - 60, PW / 2 + 60, PH / 2 + 60], outline=WHITE, width=lw)
    for x, s in ((x0, 1), (x1, -1)):
        d.rectangle(sorted([x, x + s * 110]) and [min(x, x + s * 110), PH / 2 - 110, max(x, x + s * 110), PH / 2 + 110], outline=WHITE, width=lw)
        d.rectangle([min(x, x - s * 14), PH / 2 - 36, max(x, x - s * 14), PH / 2 + 36], fill=WHITE)
    rng = random.Random(3)
    for team, col in ((0, (230, 50, 60)), (1, (40, 110, 240))):
        for k in range(11):
            bx = rng.uniform(0.12, 0.45) if team == 0 else rng.uniform(0.55, 0.88)
            by = rng.uniform(0.15, 0.85)
            ph = rng.uniform(0, 6.28)
            x = bx * PW + run * 26 * math.sin(t * 1.6 + ph)
            y = by * PH + run * 18 * math.cos(t * 1.3 + ph)
            d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col, outline=(15, 15, 20), width=3)
    bx = PW / 2 + run * 150 * math.sin(t * 1.1)
    by = PH / 2 + run * 70 * math.sin(t * 1.7)
    d.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=WHITE, outline=(20, 20, 20), width=2)


def _sky(im: Image.Image, t: float) -> None:
    d = ImageDraw.Draw(im)
    for y in range(PH):
        k = y / PH
        d.line([(0, y), (PW, y)], fill=(int(10 + 30 * k), int(14 + 26 * k), int(40 + 40 * k)))
    rng = random.Random(9)
    for _ in range(70):
        x, y = rng.uniform(0, PW), rng.uniform(0, PH * 0.8)
        a = 120 + int(100 * (0.5 + 0.5 * math.sin(t * 3 + x)))
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(a, a, a))


def _stadium(im: Image.Image) -> None:
    d = ImageDraw.Draw(im)
    base = PH - 70
    d.polygon([(60, PH), (130, base), (PW - 130, base), (PW - 60, PH)], fill=(28, 34, 52))
    d.ellipse([170, base - 20, PW - 170, base + 60], fill=(34, 120, 62))
    for x in (110, PW - 110):
        d.line([(x, base), (x, base - 120)], fill=(70, 80, 100), width=6)
        d.rectangle([x - 26, base - 140, x + 26, base - 118], fill=(255, 245, 200))


def _rock(d: ImageDraw.ImageDraw, x: float, y: float, r: float, ang: float, dx: float, dy: float) -> None:
    # estela de fuego
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    for k in range(18, 0, -1):
        tx, ty = x - ux * r * k * 0.9, y - uy * r * k * 0.9
        rr = r * (1.25 - k * 0.055)
        if rr <= 1:
            continue
        c = (255, max(60, 230 - k * 10), max(0, 120 - k * 12))
        d.ellipse([tx - rr, ty - rr, tx + rr, ty + rr], fill=c)
    d.ellipse([x - r * 1.35, y - r * 1.35, x + r * 1.35, y + r * 1.35], fill=(255, 210, 90))
    pts = []
    for i in range(9):
        a = ang + i * 2 * math.pi / 9
        rr = r * (0.85 + 0.18 * math.sin(i * 2.7))
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=(90, 70, 60), outline=(50, 38, 32))
    d.ellipse([x - r * 0.35, y - r * 0.45, x - r * 0.05, y - r * 0.15], fill=(60, 46, 40))


def _rings(d, cx, cy, p, rmax, col=(255, 240, 200)):
    for k in range(3):
        q = p - k * 0.12
        if 0 < q < 1:
            r = rmax * _ease(q)
            w = max(1, int(14 * (1 - q)))
            d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55], outline=col, width=w)


def _debris(d, cx, cy, p):
    rng = random.Random(5)
    for _ in range(40):
        a = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        v = rng.uniform(250, 600)
        x = cx + math.cos(a) * v * p
        y = cy + math.sin(a) * v * p + 500 * p * p
        s = rng.uniform(4, 11) * (1 - p * 0.6)
        d.rectangle([x - s, y - s, x + s, y + s], fill=rng.choice([(110, 80, 50), (80, 60, 40), (255, 160, 60)]))


def _crater(d, cx, cy, rx, ry, glow=0.0):
    d.ellipse([cx - rx * 1.12, cy - ry * 1.12, cx + rx * 1.12, cy + ry * 1.12], fill=(120, 92, 60))
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(70, 50, 34))
    d.ellipse([cx - rx * 0.7, cy - ry * 0.62, cx + rx * 0.7, cy + ry * 0.75], fill=(48, 34, 24))
    if glow > 0:
        g = int(255 * glow)
        d.ellipse([cx - rx * 0.35, cy - ry * 0.3, cx + rx * 0.35, cy + ry * 0.35], fill=(g, int(g * 0.45), 0))


def _smoke(im, cx, cy, t, n=7):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(n):
        q = (t * 0.4 + k / n) % 1
        x = cx + 40 * math.sin(k * 2.1 + t)
        y = cy - 260 * q
        r = 30 + 70 * q
        a = int(150 * (1 - q))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(130, 130, 140, a))
    im.paste(lay.filter(ImageFilter.GaussianBlur(6)), (0, 0), lay.filter(ImageFilter.GaussianBlur(6)))


def draw(img: Image.Image, kind: str, t: float, dur: float, box: tuple[int, int, int, int]) -> None:
    """Dibuja la animación `kind` en el instante t (s desde el inicio de la escena)."""
    im = Image.new("RGB", (PW, PH))
    d = ImageDraw.Draw(im)
    shake = (0, 0)
    if kind == "campo":
        _pitch(im, t)
    elif kind == "aviso":
        _pitch(im, t, run=max(0.0, 1 - t / 1.2))
        p = _ease(t / max(dur, 1))
        x, y = PW - 120 - 60 * p, 70 + 30 * p
        r = 4 + 12 * p
        glow = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([x - r * 4, y - r * 4, x + r * 4, y + r * 4], fill=(255, 200, 80, 90))
        gd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 220, 255))
        im.paste(glow, (0, 0), glow)
        f = ImageFont.truetype(BOLD, 40)
        d.rounded_rectangle([20, 18, 150, 76], 14, fill=(10, 12, 20))
        d.text((36, 22), "70'", font=f, fill=(255, 214, 10))
    elif kind == "meteorito":
        _sky(im, t)
        p = (t / max(dur, 0.1))
        x = PW + 60 - (PW + 200) * p
        y = -40 + (PH + 60) * p * 0.75
        _rock(d, x, y, 34, t * 4, -1, 0.75)
        f = ImageFont.truetype(BOLD, 44)
        d.text((24, PH - 70), "+40.000 km/h", font=f, fill=(255, 214, 10))
    elif kind == "airburst":
        _sky(im, t)
        _stadium(im)
        bx, by = PW * 0.55, PH * 0.28
        if t < AIRBURST:
            p = t / AIRBURST
            _rock(d, PW + 40 - (PW + 40 - bx) * p, -40 + (by + 40) * p, 18, t * 5, -1, 0.5)
        else:
            q = (t - AIRBURST)
            fl = max(0.0, 1 - q / 0.35)
            r = (40 + 160 * _ease(q / 0.6)) * max(0.0, 1 - max(0.0, q - 0.9) / 1.2)
            if r > 2:
                d.ellipse([bx - r, by - r, bx + r, by + r], fill=(255, int(180 + 60 * fl), int(80 + 150 * fl)))
            if q > 0.8:
                _smoke(im, bx, by + 60, q - 0.8, n=9)
                d = ImageDraw.Draw(im)
            _rings(d, bx, by, q / 1.6, 520)
            if fl > 0:
                im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 240)), 0.8 * fl)
            if q < 0.6:
                shake = (int(10 * math.sin(q * 70)), int(7 * math.cos(q * 60)))
    elif kind == "impacto":
        cx, cy = PW / 2, PH / 2 + 20
        if t < IMPACT:
            _pitch(im, t, run=max(0.0, 1 - t / 0.6))
            p = t / IMPACT
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse([cx - 90 * p, cy - 40 * p, cx + 90 * p, cy + 40 * p], fill=(0, 0, 0, int(120 * p)))
            im.paste(sh, (0, 0), sh)
            d = ImageDraw.Draw(im)
            _rock(d, cx + 300 * (1 - p), cy - 420 * (1 - p) ** 1.2, 20 + 40 * p, t * 5, -0.6, 1)
        else:
            q = t - IMPACT
            _pitch(im, t, run=0)
            d = ImageDraw.Draw(im)
            k = _ease(q / 0.4)
            _crater(d, cx, cy, 250 * k + 5, 130 * k + 3, glow=max(0.0, 1 - q / 2.5))
            _rings(d, cx, cy, q / 1.2, 700)
            if q < 1.2:
                _debris(d, cx, cy, q / 1.2)
            if q > 0.3:
                _smoke(im, cx, cy - 40, q)
            fl = max(0.0, 1 - q / 0.3)
            if fl > 0:
                im = Image.blend(im, Image.new("RGB", im.size, (255, 250, 230)), fl)
            if q < 0.7:
                a = 22 * (1 - q / 0.7)
                shake = (int(a * math.sin(q * 80)), int(a * math.cos(q * 65)))
    elif kind == "crater":
        d.rectangle([0, 0, PW, PH], fill=(176, 140, 96))
        cx, cy = PW / 2, PH / 2 + 10
        rx = 400 * _ease(t / 0.5) + 2
        _crater(d, cx, cy, rx, rx * 0.5)
        f = ImageFont.truetype(BOLD, 40)
        n = 11
        pw = 2 * 400 * 0.88 / n
        for i in range(n):
            t0 = 0.6 + i * 0.16
            if t < t0:
                break
            x = cx - pw * n / 2 + i * pw
            dd = ImageDraw.Draw(im)
            dd.rectangle([x + 2, cy - 22, x + pw - 2, cy + 22], fill=(40, 134, 70), outline=WHITE, width=2)
            dd.line([(x + pw / 2, cy - 22), (x + pw / 2, cy + 22)], fill=WHITE, width=1)
        if t > 0.6 + n * 0.16:
            d.rounded_rectangle([PW / 2 - 200, 20, PW / 2 + 200, 80], 16, fill=(10, 12, 20))
            s = "1,2 km = 11 campos"
            d.text((PW / 2 - d.textlength(s, font=f) / 2, 26), s, font=f, fill=(255, 214, 10))
    elif kind == "suspendido":
        _pitch(im, 0, run=0)
        im = Image.blend(im, Image.new("RGB", im.size, (10, 12, 20)), 0.55)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([PW / 2 - 260, 60, PW / 2 + 260, 250], 26, fill=(12, 14, 22), outline=(80, 90, 120), width=4)
        f = ImageFont.truetype(BOLD, 110)
        s = "1 - 1"
        d.text((PW / 2 - d.textlength(s, font=f) / 2, 90), s, font=f, fill=(255, 214, 10))
        f2 = ImageFont.truetype(BOLD, 34)
        d.text((PW / 2 - 225, 70), "70'", font=f2, fill=WHITE)
        if t > 0.5:
            k = _ease((t - 0.5) / 0.25)
            st = Image.new("RGBA", (560, 120), (0, 0, 0, 0))
            sd = ImageDraw.Draw(st)
            sd.rounded_rectangle([0, 0, 559, 119], 18, fill=(220, 40, 50), outline=WHITE, width=6)
            f3 = ImageFont.truetype(BOLD, 72)
            s3 = "SUSPENDIDO"
            sd.text((280 - sd.textlength(s3, font=f3) / 2, 16), s3, font=f3, fill=WHITE)
            sc = 1.8 - 0.8 * k
            st = st.resize((int(560 * sc), int(120 * sc)), Image.BILINEAR).rotate(-6, expand=True, resample=Image.BICUBIC)
            im.paste(st, (int(PW / 2 - st.width / 2), int(330 - st.height / 2)), st)
    else:
        raise ValueError(f"anim desconocida: {kind}")
    x0, y0 = box[0] + shake[0], box[1] + shake[1]
    img.paste(im, (x0, y0), _mask)
