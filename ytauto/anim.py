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


def _pitch_v(im: Image.Image, t: float, run: float = 1.0) -> None:
    """Campo en vertical (pantalla completa): porterías arriba y abajo."""
    d = ImageDraw.Draw(im)
    for i in range(12):
        d.rectangle([i * PW / 12, 0, (i + 1) * PW / 12, PH], fill=GRASS[i % 2])
    m = 40
    x0, y0, x1, y1 = m, m, PW - m, PH - m
    lw = 6
    d.rectangle([x0, y0, x1, y1], outline=WHITE, width=lw)
    d.line([(x0, PH / 2), (x1, PH / 2)], fill=WHITE, width=lw)
    d.ellipse([PW / 2 - 80, PH / 2 - 80, PW / 2 + 80, PH / 2 + 80], outline=WHITE, width=lw)
    for y, s in ((y0, 1), (y1, -1)):
        d.rectangle([PW / 2 - 200, min(y, y + s * 130), PW / 2 + 200, max(y, y + s * 130)], outline=WHITE, width=lw)
        d.rectangle([PW / 2 - 50, min(y, y - s * 16), PW / 2 + 50, max(y, y - s * 16)], fill=WHITE)
    rng = random.Random(3)
    for team, col in ((0, (230, 50, 60)), (1, (40, 110, 240))):
        for k in range(11):
            bx = rng.uniform(0.12, 0.88)
            by = rng.uniform(0.1, 0.45) if team == 0 else rng.uniform(0.55, 0.9)
            ph = rng.uniform(0, 6.28)
            x = bx * PW + run * 22 * math.sin(t * 1.6 + ph)
            y = by * PH + run * 30 * math.cos(t * 1.3 + ph)
            d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=col, outline=(15, 15, 20), width=3)
    bx = PW / 2 + run * 120 * math.sin(t * 1.1)
    by = PH / 2 + run * 160 * math.sin(t * 1.7)
    d.ellipse([bx - 9, by - 9, bx + 9, by + 9], fill=WHITE, outline=(20, 20, 20), width=2)


def _pitch(im: Image.Image, t: float, run: float = 1.0, scale: float = 1.0) -> None:
    if PH > PW:
        return _pitch_v(im, t, run)
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
    d.ellipse([170, base - 20, PW - 170, base + 30], fill=(34, 120, 62))
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


BROWN, BROWN_D, BELLY = (140, 92, 52), (96, 62, 34), (196, 150, 104)
TOOTH = (255, 170, 60)


def _moon(im: Image.Image, t: float, lines: bool = True) -> None:
    """Suelo lunar gris con cráteres, cielo negro y la Tierra al fondo."""
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, PW, PH], fill=(6, 8, 14))
    rng = random.Random(11)
    for _ in range(90):
        x, y = rng.uniform(0, PW), rng.uniform(0, PH * 0.3)
        d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(200, 200, 210))
    ex, ey, er = PW * 0.78, PH * 0.12, 54
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(40, 110, 200))
    d.pieslice([ex - er, ey - er, ex + er, ey + er], 200, 320, fill=(60, 160, 80))
    d.ellipse([ex - er * 0.5, ey + er * 0.2, ex + er * 0.2, ey + er * 0.7], fill=(70, 170, 90))
    gy = PH * 0.3
    d.rectangle([0, gy, PW, PH], fill=(150, 150, 156))
    for _ in range(26):
        x, y = rng.uniform(0, PW), rng.uniform(gy + 20, PH)
        r = rng.uniform(10, 46) * (0.5 + (y - gy) / (PH - gy))
        d.ellipse([x - r, y - r * 0.45, x + r, y + r * 0.45], fill=(120, 120, 126))
        d.ellipse([x - r * 0.8, y - r * 0.32, x + r * 0.8, y + r * 0.4], fill=(104, 104, 110))
    if lines:
        x0, x1, y0, y1 = 60, PW - 60, gy + 40, PH - 40
        d.rectangle([x0, y0, x1, y1], outline=(235, 235, 240), width=5)
        d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=(235, 235, 240), width=5)
        d.ellipse([PW / 2 - 70, (y0 + y1) / 2 - 40, PW / 2 + 70, (y0 + y1) / 2 + 40], outline=(235, 235, 240), width=5)


def _astro(d: ImageDraw.ImageDraw, x: float, y: float, s: float = 1.0, col=(230, 50, 60)) -> None:
    """Jugador-astronauta: (x, y) = pies."""
    d.line([(x - 12 * s, y), (x - 6 * s, y - 40 * s)], fill=(240, 240, 245), width=int(12 * s))
    d.line([(x + 12 * s, y), (x + 6 * s, y - 40 * s)], fill=(240, 240, 245), width=int(12 * s))
    d.rounded_rectangle([x - 24 * s, y - 92 * s, x + 24 * s, y - 36 * s], 12 * s, fill=col)
    d.ellipse([x - 26 * s, y - 140 * s, x + 26 * s, y - 88 * s], fill=(240, 240, 245))
    d.ellipse([x - 17 * s, y - 128 * s, x + 17 * s, y - 104 * s], fill=(40, 60, 110))


def _ball(d, x, y, r=16):
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=(20, 20, 20), width=3)


def _label(d, x, y, text, size=46, col=(255, 214, 10), center=False):
    f = ImageFont.truetype(BOLD, size)
    w = d.textlength(text, font=f)
    if center:
        x -= w / 2 + 16
    d.rounded_rectangle([x, y, x + w + 32, y + size * 1.35], 16, fill=(10, 12, 20))
    d.text((x + 16, y + size * 0.12), text, font=f, fill=col)


def _feet() -> float:
    """Altura de los pies del castor: en pantalla completa, por encima de los subtítulos."""
    return min(PH - 30, PH * 0.78)


def _beaver(im: Image.Image, x: float, y: float, s: float, bite: float = 0.0, tail: float = 0.0,
            kit=(230, 50, 60), arms_up: float = 0.0) -> None:
    """Castor de dibujo con camiseta y el 7. (x, y) = pies; s = escala (1 ≈ 220 px de alto)."""
    d = ImageDraw.Draw(im)
    # cola (pala plana) detrás
    ta = math.radians(-20 + 50 * tail)
    tx, ty = x + 70 * s * math.cos(ta), y - 20 * s + 70 * s * math.sin(ta)
    pts = []
    for a in range(0, 360, 20):
        r = math.radians(a)
        px, py = 48 * s * math.cos(r), 20 * s * math.sin(r)
        pts.append((tx + px * math.cos(ta) - py * math.sin(ta), ty + px * math.sin(ta) + py * math.cos(ta)))
    d.polygon(pts, fill=(70, 46, 30), outline=(40, 26, 16))
    # piernas
    for dx in (-28, 28):
        d.rounded_rectangle([x + dx * s - 16 * s, y - 40 * s, x + dx * s + 16 * s, y], 10 * s, fill=BROWN_D)
        d.ellipse([x + dx * s - 24 * s, y - 12 * s, x + dx * s + 24 * s, y + 6 * s], fill=BROWN_D)
    # cuerpo con camiseta
    d.ellipse([x - 66 * s, y - 150 * s, x + 66 * s, y - 24 * s], fill=kit, outline=(30, 20, 20), width=max(1, int(4 * s)))
    f = ImageFont.truetype(BOLD, max(8, int(54 * s)))
    d.text((x - d.textlength("7", font=f) / 2, y - 122 * s), "7", font=f, fill=WHITE)
    # brazos
    for side in (-1, 1):
        ax0, ay0 = x + side * 58 * s, y - 120 * s
        ang = math.radians(90 + side * (30 + 120 * arms_up))
        ax1, ay1 = ax0 + side * abs(48 * s * math.cos(ang)), ay0 + 48 * s * math.sin(ang) * (1 - 2 * arms_up)
        d.line([(ax0, ay0), (ax1, ay1)], fill=BROWN, width=max(2, int(20 * s)))
        d.ellipse([ax1 - 12 * s, ay1 - 12 * s, ax1 + 12 * s, ay1 + 12 * s], fill=BROWN_D)
    # cabeza
    hx, hy, hr = x, y - 190 * s, 58 * s
    for ex in (-1, 1):
        d.ellipse([hx + ex * 40 * s - 14 * s, hy - 58 * s, hx + ex * 40 * s + 14 * s, hy - 30 * s], fill=BROWN_D)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr * 0.95], fill=BROWN, outline=(60, 40, 22), width=max(1, int(3 * s)))
    d.ellipse([hx - 36 * s, hy + 2 * s, hx + 36 * s, hy + 44 * s], fill=BELLY)
    for ex in (-1, 1):
        d.ellipse([hx + ex * 24 * s - 10 * s, hy - 26 * s, hx + ex * 24 * s + 10 * s, hy - 4 * s], fill=WHITE)
        d.ellipse([hx + ex * 24 * s - 5 * s, hy - 20 * s, hx + ex * 24 * s + 5 * s, hy - 8 * s], fill=(15, 15, 20))
    d.ellipse([hx - 12 * s, hy + 2 * s, hx + 12 * s, hy + 16 * s], fill=(40, 26, 20))
    # paletas
    tw, th = 15 * s, (30 + 10 * bite) * s
    ty0 = hy + 26 * s
    if bite > 0:
        d.ellipse([hx - 22 * s, ty0 - 2 * s, hx + 22 * s, ty0 + th + 8 * s], fill=(60, 20, 20))
    for side in (-1, 1):
        x0 = hx + (0 if side > 0 else -tw) + side * 1 * s
        d.rounded_rectangle([x0, ty0, x0 + tw, ty0 + th], 4 * s, fill=TOOTH, outline=(120, 70, 20), width=max(1, int(2 * s)))


def _render(kind: str, t: float, dur: float):
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
        y = PH * 0.3 + PH * 0.45 * p
        _rock(d, x, y, 34, t * 4, -1, 0.75)
        f = ImageFont.truetype(BOLD, 48)
        d.rounded_rectangle([20, 20, 60 + d.textlength("+40.000 km/h", font=f), 88], 16, fill=(10, 12, 20))
        d.text((40, 26), "+40.000 km/h", font=f, fill=(255, 214, 10))
    elif kind == "airburst":
        _sky(im, t)
        _stadium(im)
        bx, by = PW * 0.55, PH * 0.28
        if t < AIRBURST:
            p = t / AIRBURST
            _rock(d, PW + 40 - (PW + 40 - bx) * p, 60 + (by - 60) * p, 18, t * 5, -1, 0.5)
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
            _rock(d, cx + 300 * (1 - p), cy - (cy - 90) * (1 - p) ** 1.2, 20 + 40 * p, t * 5, -0.6, 1)
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
    elif kind == "castor":
        _pitch(im, t, run=0.6)
        k = _ease(t / 0.5)
        _beaver(im, PW / 2, _feet() + 200 * (1 - k), 1.2, tail=0.5 + 0.5 * math.sin(t * 3))
    elif kind == "paletas":
        for y in range(PH):
            ImageDraw.Draw(im).line([(0, y), (PW, y)], fill=(255, 214 - y // 8, 10 + y // 6))
        z = 1.6 + 0.6 * _ease(t / 0.8)
        _beaver(im, PW / 2, PH / 2 + 160 * z, z, bite=0.3 * (1 + math.sin(t * 8)) if t > 1 else 0)
        f = ImageFont.truetype(BOLD, 44)
        if t > 1.2:
            s1 = "Fe = HIERRO"
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([20, 20, 40 + d.textlength(s1, font=f), 82], 16, fill=(10, 12, 20))
            d.text((30, 24), s1, font=f, fill=TOOTH)
    elif kind == "mordisco":
        _pitch(im, t, run=0)
        d = ImageDraw.Draw(im)
        ex = PW / 2 - 40
        hit = 0.9
        if t < hit:
            p = t / hit
            bx, by = 40 + (ex + 40 - 40) * p, PH / 2 - 60 * math.sin(p * math.pi)
            d.ellipse([bx - 22, by - 22, bx + 22, by + 22], fill=WHITE, outline=(20, 20, 20), width=3)
        _beaver(im, ex + 70, _feet(), 1.1, bite=1.0 if hit - 0.15 < t < hit + 0.4 else 0.0)
        if t >= hit:
            q = t - hit
            d = ImageDraw.Draw(im)
            rng = random.Random(4)
            for _ in range(14):
                a = rng.uniform(0, 6.28)
                v = rng.uniform(120, 260)
                x = ex - 10 + math.cos(a) * v * min(q, 1)
                y = PH / 2 - 150 + math.sin(a) * v * min(q, 1) + 200 * q * q
                d.polygon([(x, y), (x + 18, y + 4), (x + 6, y + 16)], fill=WHITE if rng.random() > 0.4 else (30, 30, 30))
            if q < 1.2:
                f = ImageFont.truetype(BOLD, 70)
                d.text((60, 40), "¡ÑAM!", font=f, fill=(255, 214, 10))
    elif kind == "presa":
        _pitch(im, t, run=0)
        d = ImageDraw.Draw(im)
        gx = PW - 60
        n = int(min(t / 0.18, 12))
        for i in range(n):
            row, col = divmod(i, 3)
            y0 = PH / 2 - 120 + col * 85
            x0 = gx - 70 - row * 34
            d.rounded_rectangle([x0, y0, x0 + 30, y0 + 80], 12, fill=(120, 80, 44), outline=(70, 46, 26), width=3)
            d.ellipse([x0 + 4, y0 + 2, x0 + 26, y0 + 18], fill=(196, 150, 104))
        _beaver(im, gx - 230, _feet(), 0.9, tail=0.5 + 0.5 * math.sin(t * 6))
        if t > 2.4:
            q = (t - 2.4) % 1.4
            bx = 120 + 400 * min(q / 0.6, 1) - 300 * max(0.0, q - 0.6)
            by = PH / 2 - 80 * math.sin(min(q, 1.4) * 2.2)
            d = ImageDraw.Draw(im)
            d.ellipse([bx - 18, by - 18, bx + 18, by + 18], fill=WHITE, outline=(20, 20, 20), width=3)
    elif kind == "cola":
        _pitch(im, t, run=0)
        swing = math.sin(min(t / 0.6, 1) * math.pi)
        _beaver(im, PW / 2 - 60, _feet(), 1.1, tail=swing)
        d = ImageDraw.Draw(im)
        if t > 0.35:
            q = t - 0.35
            bx, by = PW / 2 + 40 + 700 * q, PH / 2 + 60 - 500 * q + 300 * q * q
            d.ellipse([bx - 18, by - 18, bx + 18, by + 18], fill=WHITE, outline=(20, 20, 20), width=3)
            if q < 0.6:
                f = ImageFont.truetype(BOLD, 64)
                d.text((PW - 360, 30), "¡PLAF!", font=f, fill=(255, 214, 10))
    elif kind == "porteria_cero":
        _pitch(im, 0, run=0)
        im = Image.blend(im, Image.new("RGB", im.size, (10, 12, 20)), 0.5)
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(BOLD, 44)
        s1 = "GOLES ENCAJADOS"
        d.text((PW / 2 - d.textlength(s1, font=f) / 2, 26), s1, font=f, fill=WHITE)
        f2 = ImageFont.truetype(BOLD, 150)
        d.text((PW / 2 - d.textlength("0", font=f2) / 2 + 220, 90), "0", font=f2, fill=(255, 214, 10))
        _beaver(im, PW / 2 - 120, _feet(), 0.95, arms_up=min(1.0, t / 0.4), tail=0.5 + 0.5 * math.sin(t * 7))
    elif kind == "luna":
        _moon(im, t)
        d = ImageDraw.Draw(im)
        gy = PH * 0.3
        rng = random.Random(2)
        for k in range(8):
            bx, by = rng.uniform(0.12, 0.78) * PW, PH * rng.uniform(0.45, 0.72)
            hop = abs(math.sin(t * 1.2 + k)) * 60
            _astro(d, bx, by - hop, 0.7, (230, 50, 60) if k % 2 else (40, 110, 240))
        _ball(d, PW / 2 + 160 * math.sin(t), PH * 0.6 - abs(math.sin(t * 1.3)) * 140)
    elif kind == "luna_salto":
        _moon(im, t, lines=False)
        d = ImageDraw.Draw(im)
        gy = PH * 0.72
        d.line([(PW / 2, PH * 0.32), (PW / 2, PH * 0.74)], fill=(40, 40, 50), width=4)
        ph = (t % 2.0) / 2.0
        j = math.sin(ph * math.pi)
        _astro(d, PW * 0.27, gy - 60 * j, 0.9, (40, 110, 240))
        _astro(d, PW * 0.73, gy - 240 * j, 0.9, (230, 50, 60))
        _label(d, PW * 0.27, PH * 0.33, "TIERRA", 40, WHITE, center=True)
        _label(d, PW * 0.73, PH * 0.33, "LUNA x6", 40, center=True)
    elif kind == "luna_chut":
        _moon(im, t, lines=False)
        d = ImageDraw.Draw(im)
        gy = PH * 0.7
        x0 = 90
        _astro(d, x0, gy, 0.8)
        p = min(t / 2.4, 1)
        for i, (span, hgt, col) in enumerate(((PW * 0.22, 90, (120, 170, 255)), (PW - 160, 300, (255, 214, 10)))):
            pts = [(x0 + 20 + span * q, gy - 20 - hgt * 4 * q * (1 - q)) for q in [k / 40 * p for k in range(41)]]
            d.line(pts, fill=col, width=5)
            _ball(d, *pts[-1], r=14)
        _label(d, PW * 0.08, gy - 160, "Tierra", 36, (120, 170, 255))
        if p >= 1:
            _label(d, PW / 2, PH * 0.31, "¡6 veces más lejos!", 44, center=True)
    elif kind == "sin_efecto":
        _moon(im, t, lines=False)
        d = ImageDraw.Draw(im)
        gy = PH * 0.7
        gx0, gx1 = PW * 0.58, PW * 0.92
        d.rectangle([gx0, gy - 200, gx1, gy], outline=WHITE, width=8)
        sx, sy = 90, gy - 20
        p = min(t / 1.6, 1)
        tx, ty = (gx0 + gx1) / 2, gy - 90
        curve = [(sx + (tx - sx) * q, sy + (ty - sy) * q - 260 * math.sin(q * math.pi)) for q in [k / 40 * p for k in range(41)]]
        straight = [(sx + (gx0 - 40 - sx) * q, sy + (gy - 330 - sy) * q) for q in [k / 40 * p for k in range(41)]]
        for i in range(0, 40, 3):
            d.line(curve[i:i + 2], fill=(120, 170, 255), width=5)
        d.line(straight, fill=(255, 214, 10), width=6)
        _ball(d, *straight[-1])
        _label(d, 30, PH * 0.34, "- - Tierra (con efecto)", 34, (120, 170, 255))
        _label(d, 30, PH * 0.34 + 62, "— Luna (sin aire, recto)", 34)
    elif kind == "silencio":
        _moon(im, t)
        d = ImageDraw.Draw(im)
        cx, cy = PW / 2, PH * 0.52
        for k in range(3):
            r = 70 + 50 * k + 20 * ((t * 2) % 1)
            d.arc([cx - r, cy - r, cx + r, cy + r], -50, 50, fill=(255, 214, 10), width=8)
            d.arc([cx - r, cy - r, cx + r, cy + r], 130, 230, fill=(255, 214, 10), width=8)
        d.ellipse([cx - 60, cy - 36, cx + 60, cy + 36], fill=(60, 60, 70), outline=WHITE, width=4)
        d.rectangle([cx + 40, cy - 14, cx + 110, cy + 14], fill=(60, 60, 70), outline=WHITE, width=4)
        if t > 0.8:
            d.line([(cx - 230, cy - 230), (cx + 230, cy + 230)], fill=(220, 40, 50), width=22)
            _label(d, PW / 2, PH * 0.31, "Sin aire no hay sonido", 44, WHITE, center=True)
    elif kind == "temperatura":
        _moon(im, t, lines=False)
        d = ImageDraw.Draw(im)
        for i, (x, top, txt, col) in enumerate(((PW * 0.3, 0.9, "+120 °C", (240, 70, 40)), (PW * 0.7, 0.15, "-170 °C", (90, 170, 255)))):
            y0, y1 = PH * 0.42, PH * 0.66
            d.rounded_rectangle([x - 34, y0, x + 34, y1], 34, fill=(235, 235, 240))
            lvl = min(y1 - 12, y1 - (y1 - y0 - 30) * top * _ease(t / 1.0))
            d.rounded_rectangle([x - 18, lvl, x + 18, y1 - 10], 18, fill=col)
            d.ellipse([x - 56, y1 - 40, x + 56, y1 + 72], fill=col)
            _label(d, x, PH * 0.31, ("DÍA " if i == 0 else "NOCHE ") + txt, 40, col, center=True)
    else:
        raise ValueError(f"anim desconocida: {kind}")
    return im, shake


FULL_TOP, FULL_H = 400, 1170   # zona de la animación a pantalla completa (px reales)


def draw(img: Image.Image, kind: str, t: float, dur: float, box: tuple[int, int, int, int],
         full: bool = False) -> None:
    """Dibuja la animación `kind` en el instante t (s desde el inicio de la escena).

    full=True: ocupa toda la pantalla. El centro se dibuja a 860 px de ancho y se escala;
    arriba y abajo se prolongan la primera y la última fila para rellenar sin cortes.
    """
    global PW, PH
    W, H = img.size
    PW, PH = (860, round(860 * FULL_H / W)) if full else (860, 460)
    try:
        im, shake = _render(kind, t, dur)
    finally:
        PW, PH = 860, 460
    if not full:
        img.paste(im, (box[0] + shake[0], box[1] + shake[1]), _mask)
        return
    big = im.resize((W, FULL_H), Image.BICUBIC)
    import numpy as np
    a = np.asarray(big)
    top = Image.fromarray(np.median(a[:30], axis=0).astype("uint8")[None]).resize((W, FULL_TOP + 40))
    bot = Image.fromarray(np.median(a[-30:], axis=0).astype("uint8")[None]).resize((W, H - FULL_TOP - FULL_H + 40))
    sx, sy = int(shake[0] * W / 860), int(shake[1] * W / 860)
    img.paste(top, (sx, sy - 40))
    img.paste(bot, (sx, FULL_TOP + FULL_H + sy))
    img.paste(big, (sx, FULL_TOP + sy))
