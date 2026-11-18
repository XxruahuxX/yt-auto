"""Serie «Robot FC»: el equipo de robots que ficha lo que vota la gente.

Personajes originales: R-01 (robot protagonista) y Los Titanes del Volcán (rival).
Lienzo completo PW x PH (prefijo x_). Zona útil: 0.28-0.66 PH.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import anim as A
from .anim_robot import ball, cam

WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN, RED = (255, 214, 10), (40, 230, 255), (235, 50, 40)
LAVA = (255, 120, 20)


def _e(x):
    return A._ease(x)


def font(n):
    return ImageFont.truetype(A.BOLD, int(n))


def _glow(im, draw_fn, blur=18):
    """Dibuja draw_fn en una capa, la desenfoca y la suma (resplandor)."""
    lay = Image.new("RGB", im.size, (0, 0, 0))
    draw_fn(ImageDraw.Draw(lay))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    return Image.fromarray(__import__("numpy").minimum(
        __import__("numpy").asarray(im, dtype="uint16") + __import__("numpy").asarray(lay, dtype="uint16"), 255).astype("uint8"))


def text_c(d, x, y, s, size, fill=YEL, stroke=8):
    f = font(size)
    w = d.textlength(s, font=f)
    d.text((x - w / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=INK)


def stamp(im, text, cx, cy, t0, t, bg=YEL, fg=INK, size=64, rot=-4):
    if t < t0:
        return
    k = min((t - t0) / 0.25, 1)
    sc = 1.6 - 0.6 * k
    f = font(size)
    w = int(ImageDraw.Draw(im).textlength(text, font=f)) + 50
    h = int(size * 1.5)
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=bg + (255,), outline=INK + (255,), width=5)
    ld.text((25, h * 0.14), text, font=f, fill=fg)
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    im.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


# ---------------------------------------------------------------- personajes
def r01(d, x, y, s, t=0.0, on=1.0, kick=0.0, arm=0.0):
    """R-01: robot protagonista. (x, y) = pies. Altura ~ 300*s."""
    eye = tuple(int(30 + (c - 30) * on) for c in CYAN)
    bob = 3 * s * math.sin(t * 4) * on
    # sombra
    d.ellipse([x - 70 * s, y - 10 * s, x + 70 * s, y + 10 * s], fill=(0, 0, 0))
    # piernas
    for sg, kk in ((-1, 0.0), (1, kick)):
        hip = (x + sg * 26 * s, y - 120 * s)
        foot = (x + sg * 34 * s + kk * 70 * s, y - kk * 60 * s)
        knee = ((hip[0] + foot[0]) / 2 + sg * 6 * s, (hip[1] + foot[1]) / 2)
        d.line([hip, knee, foot], fill=(120, 130, 150), width=int(26 * s), joint="curve")
        d.ellipse([knee[0] - 15 * s, knee[1] - 15 * s, knee[0] + 15 * s, knee[1] + 15 * s], fill=(70, 78, 96))
        d.rounded_rectangle([foot[0] - 24 * s, foot[1] - 14 * s, foot[0] + 30 * s, foot[1] + 6 * s], 8 * s, fill=(40, 46, 60))
    by = y - 125 * s + bob
    # brazos
    for sg in (-1, 1):
        a = arm if sg == 1 else 0.0
        sh = (x + sg * 62 * s, by - 105 * s)
        hand = (x + sg * (82 - 30 * a) * s, by - (25 + 150 * a) * s)
        d.line([sh, hand], fill=(120, 130, 150), width=int(22 * s))
        d.ellipse([hand[0] - 16 * s, hand[1] - 16 * s, hand[0] + 16 * s, hand[1] + 16 * s], fill=(70, 78, 96))
    # torso con camiseta del equipo
    d.rounded_rectangle([x - 58 * s, by - 130 * s, x + 58 * s, by], 24 * s, fill=(30, 110, 235), outline=INK, width=int(4 * s))
    d.polygon([(x - 58 * s, by - 112 * s), (x - 82 * s, by - 128 * s), (x - 62 * s, by - 140 * s)], fill=(20, 80, 190))
    d.polygon([(x + 58 * s, by - 112 * s), (x + 82 * s, by - 128 * s), (x + 62 * s, by - 140 * s)], fill=(20, 80, 190))
    d.ellipse([x - 22 * s, by - 92 * s, x + 22 * s, by - 48 * s], fill=eye, outline=WHITE, width=int(3 * s))
    d.text((x - 16 * s, by - 88 * s), "1", font=font(34 * s), fill=INK)
    # cabeza
    hy = by - 140 * s
    d.line([(x, hy - 92 * s), (x, hy - 122 * s)], fill=(160, 170, 190), width=int(6 * s))
    d.ellipse([x - 11 * s, hy - 134 * s, x + 11 * s, hy - 112 * s], fill=RED if on > 0.5 and int(t * 3) % 2 else (120, 30, 30))
    d.rounded_rectangle([x - 62 * s, hy - 96 * s, x + 62 * s, hy], 30 * s, fill=(210, 218, 232), outline=INK, width=int(4 * s))
    d.rounded_rectangle([x - 48 * s, hy - 74 * s, x + 48 * s, hy - 28 * s], 18 * s, fill=(12, 16, 28))
    blink = 0.15 if (t % 3.1) < 0.12 else 1.0
    for sg in (-1, 1):
        ex = x + sg * 22 * s
        d.rounded_rectangle([ex - 12 * s, hy - 60 * s + 10 * s * (1 - blink), ex + 12 * s, hy - 40 * s - 10 * s * (1 - blink)], 6 * s, fill=eye)


def titan(d, x, y, s, t, phase=0.0):
    """Titán del Volcán: gigante oscuro con capa, cuernos y ojos rojos."""
    br = 0.6 + 0.4 * math.sin(t * 5 + phase)
    eye = (255, int(60 + 120 * br), 20)
    d.polygon([(x - 90 * s, y - 280 * s), (x + 90 * s, y - 280 * s), (x + 150 * s, y), (x - 150 * s, y)], fill=(70, 10, 14))
    d.rounded_rectangle([x - 80 * s, y - 300 * s, x + 80 * s, y - 60 * s], 30 * s, fill=(28, 24, 30), outline=(90, 20, 20), width=int(4 * s))
    d.polygon([(x - 26 * s, y - 230 * s), (x + 26 * s, y - 230 * s), (x, y - 170 * s)], fill=LAVA)
    for sg in (-1, 1):
        d.rounded_rectangle([x + sg * 80 * s - 22 * s, y - 290 * s, x + sg * 80 * s + 22 * s, y - 120 * s], 12 * s, fill=(36, 30, 38))
        d.rounded_rectangle([x + sg * 30 * s - 20 * s, y - 70 * s, x + sg * 30 * s + 20 * s, y], 8 * s, fill=(20, 18, 24))
    hy = y - 300 * s
    d.ellipse([x - 52 * s, hy - 100 * s, x + 52 * s, hy + 6 * s], fill=(22, 20, 26))
    for sg in (-1, 1):
        d.polygon([(x + sg * 40 * s, hy - 80 * s), (x + sg * 78 * s, hy - 150 * s), (x + sg * 20 * s, hy - 92 * s)], fill=(60, 50, 50))
        d.polygon([(x + sg * 30 * s, hy - 58 * s), (x + sg * 10 * s, hy - 46 * s), (x + sg * 34 * s, hy - 40 * s)], fill=eye)


def _lab(im, t):
    d = ImageDraw.Draw(im)
    PW, PH = im.size
    for i in range(30):
        c = int(10 + 20 * i / 30)
        d.rectangle([0, PH * i / 30, PW, PH * (i + 1) / 30], fill=(c // 2, c, c + 25))
    for i in range(0, PW, 60):
        d.line([(i, 0), (i, PH)], fill=(20, 40, 70), width=1)
    for j in range(0, PH, 60):
        d.line([(0, j), (PW, j)], fill=(20, 40, 70), width=1)
    return d


def _lava_sky(im, t):
    d = ImageDraw.Draw(im)
    PW, PH = im.size
    for i in range(40):
        k = i / 40
        d.rectangle([0, PH * k, PW, PH * (k + 1 / 40)], fill=(int(30 + 150 * k), int(8 + 40 * k), int(12 + 4 * k)))
    d.polygon([(-50, PH * 0.66), (PW * 0.3, PH * 0.42), (PW * 0.42, PH * 0.45), (PW * 0.6, PH * 0.38), (PW + 50, PH * 0.66)], fill=(26, 12, 12))
    d.polygon([(PW * 0.55, PH * 0.39), (PW * 0.65, PH * 0.39), (PW * 0.62, PH * 0.44), (PW * 0.58, PH * 0.44)], fill=LAVA)
    d.rectangle([0, PH * 0.66, PW, PH], fill=(20, 10, 10))
    rnd = random.Random(3)
    for _ in range(40):
        x0, sp, ph = rnd.uniform(0, PW), rnd.uniform(60, 160), rnd.random()
        yy = PH * 0.7 - ((t * sp + ph * PH) % (PH * 0.6))
        r = rnd.uniform(2, 5)
        d.ellipse([x0 - r, yy - r, x0 + r, yy + r], fill=(255, rnd.randint(120, 200), 40))
    return d


# ---------------------------------------------------------------- escenas
def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    if kind == "x_rb_lab":
        d = _lab(im, t)
        on = _e((t - 1.4) / 0.4)
        # plataforma
        py = PH * 0.64
        d.ellipse([cx - 200, py - 30, cx + 200, py + 30], fill=(30, 50, 80), outline=CYAN, width=4)
        r01(d, cx, py, 1.3, t, on=on)
        # láser de escaneo
        if t < 1.4:
            ly = PH * 0.3 + (py - PH * 0.3) * ((t * 1.4) % 1)
            im = _glow(im, lambda g: g.rectangle([cx - 220, ly - 4, cx + 220, ly + 4], fill=CYAN), 10)
            d = ImageDraw.Draw(im)
            d.line([(cx - 220, ly), (cx + 220, ly)], fill=(200, 255, 255), width=3)
        else:
            if t < 1.7:
                k = 1 - (t - 1.4) / 0.3
                ov = Image.new("RGB", im.size, (220, 255, 255))
                im = Image.blend(im, ov, 0.7 * k)
            im = _glow(im, lambda g: r01(g, cx, py, 1.3, t, on=on), 22)
            d = ImageDraw.Draw(im)
            r01(d, cx, py, 1.3, t, on=on)
            rnd = random.Random(int(t * 12))
            for _ in range(10):
                a = rnd.uniform(0, 2 * math.pi)
                rr = rnd.uniform(120, 260)
                sx, sy = cx + rr * math.cos(a), PH * 0.5 + rr * math.sin(a) * 0.8
                d.line([(sx, sy), (sx + 14 * math.cos(a), sy + 14 * math.sin(a))], fill=YEL, width=3)
            A._label(d, cx, PH * 0.29, "R-01 · ACTIVADO", 44, CYAN, center=True)
        return im
    if kind == "x_rb_escudo":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(12, 20, 50))
        cy = PH * 0.47
        for i in range(16):
            a = i / 16 * 2 * math.pi + t * 0.5
            d.polygon([(cx, cy), (cx + 1500 * math.cos(a), cy + 1500 * math.sin(a)),
                       (cx + 1500 * math.cos(a + 0.13), cy + 1500 * math.sin(a + 0.13))], fill=(22, 36, 84))
        k = _e(t / 0.5)
        sc = 0.2 + 0.8 * k + 0.08 * math.sin(min(t, 1.2) * 12) * (1 - min(t / 1.2, 1))
        w, h = 230 * sc, 270 * sc
        pts = [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h * 0.2), (cx, cy + h), (cx - w, cy + h * 0.2)]
        im = _glow(im, lambda g: g.polygon(pts, fill=(30, 110, 235)), 30)
        d = ImageDraw.Draw(im)
        d.polygon(pts, fill=(30, 110, 235), outline=WHITE)
        d.line(pts + [pts[0]], fill=WHITE, width=int(10 * sc) + 1)
        bolt = [(cx + 20 * sc, cy - 170 * sc), (cx - 70 * sc, cy + 10 * sc), (cx - 5 * sc, cy + 10 * sc),
                (cx - 30 * sc, cy + 170 * sc), (cx + 80 * sc, cy - 30 * sc), (cx + 10 * sc, cy - 30 * sc)]
        d.polygon(bolt, fill=YEL, outline=INK)
        if t > 0.6:
            text_c(d, cx, PH * 0.29, "ROBOT FC", 96, WHITE, 10)
        return im
    if kind == "x_rb_titanes":
        d = _lava_sky(im, t)
        for i, (dx, sc) in enumerate([(-300, 0.8), (300, 0.8), (-160, 0.95), (160, 0.95), (0, 1.15)]):
            rise = _e((t - i * 0.2) / 0.6)
            titan(d, cx + dx, PH * 0.66 + 260 * (1 - rise), sc, t, i)
        z = 1 + 0.12 * min(t / max(dur, 1), 1)
        im = cam(im, cx, PH * 0.5, z)
        stamp(im, "LOS TITANES DEL VOLCÁN", cx, PH * 0.31, 1.3, t, bg=RED, fg=WHITE, size=50)
        return im
    if kind == "x_rb_disparo":
        d = ImageDraw.Draw(im)
        for i in range(10):
            d.rectangle([0, PH * i / 10, PW, PH * (i + 1) / 10], fill=(34, 120, 62) if i % 2 else (40, 134, 70))
        gx, gy, gw, gh = cx, PH * 0.56, 330, 230
        hit = t > 1.2
        bul = 30 * math.sin(min(max(t - 1.2, 0), 0.6) / 0.6 * math.pi) if hit else 0
        d.rectangle([gx - gw - 20, gy - gh - 40, gx + gw + 20, gy - gh], fill=(20, 80, 40))
        for k in range(-gw, gw + 1, 30):
            d.line([(gx + k, gy - gh), (gx + k * (1 + bul / 400), gy - bul)], fill=(220, 220, 220), width=2)
        for k in range(0, gh + 1, 30):
            d.line([(gx - gw, gy - gh + k), (gx + gw, gy - gh + k)], fill=(220, 220, 220), width=2)
        d.line([(gx - gw, gy), (gx - gw, gy - gh), (gx + gw, gy - gh), (gx + gw, gy)], fill=WHITE, width=14)
        d.line([(0, gy), (PW, gy)], fill=WHITE, width=5)
        dive = _e((t - 0.7) / 0.4)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        r01(ImageDraw.Draw(lay), gx + 40 + 170 * dive, gy + 30, 0.7, t, arm=dive)
        lay = lay.rotate(-60 * dive, center=(gx + 40 + 170 * dive, gy - 60), resample=Image.BICUBIC)
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im)
        p = min(t / 1.2, 1)
        sx, sy, ex, ey = PW * 0.2, PH * 0.66, gx - 150, gy - 140
        def pos(q):
            return sx + (ex - sx) * q, sy + (ey - sy) * q - 120 * math.sin(q * math.pi)
        if not hit:
            def trail(g):
                for k in range(16):
                    tx, ty = pos(max(p - k * 0.025, 0))
                    r = 40 - k * 2
                    g.ellipse([tx - r, ty - r, tx + r, ty + r], fill=(255, 80 + k * 10, 20))
            im = _glow(im, trail, 16)
            d = ImageDraw.Draw(im)
            trail(d)
            bx, by = pos(p)
            ball(d, bx, by, 26)
        else:
            k = t - 1.2
            if k < 0.3:
                im = Image.blend(im, Image.new("RGB", im.size, (255, 200, 120)), 0.8 * (1 - k / 0.3))
                d = ImageDraw.Draw(im)
            ball(d, ex, ey - bul, 26)
            n = min(10, 1 + int(k * 6))
            d.rounded_rectangle([cx - 280, PH * 0.27, cx + 280, PH * 0.27 + 120], 18, fill=INK)
            text_c(d, cx - 200, PH * 0.27 + 36, "ROB", 40, (150, 190, 255), 0)
            text_c(d, cx + 200, PH * 0.27 + 36, "TIT", 40, (255, 140, 100), 0)
            text_c(d, cx, PH * 0.27 + 10, f"0-{n}", 90, YEL, 0)
            if k > 0.3:
                text_c(d, cx, PH * 0.6, "¡TIRO VOLCÁN!", 70, LAVA, 8)
        return im
    if kind == "x_rb_plantilla":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(22, 70, 40))
        x0, y0, x1, y1 = 50, PH * 0.28, PW - 160, PH * 0.64
        d.rounded_rectangle([x0, y0, x1, y1], 20, outline=WHITE, width=5)
        d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=WHITE, width=4)
        d.ellipse([cx - 60, (y0 + y1) / 2 - 60, cx + 60, (y0 + y1) / 2 + 60], outline=WHITE, width=4)
        rows = [[0.5], [0.15, 0.38, 0.62, 0.85], [0.25, 0.5, 0.75], [0.3, 0.7], [0.5]]
        ys = [0.92, 0.74, 0.52, 0.3, 0.1]
        i = 0
        for row, yy in zip(rows, ys):
            for xx in row:
                px, py = x0 + (x1 - x0) * xx, y0 + (y1 - y0) * yy
                if i == 0:
                    d.ellipse([px - 42, py - 42, px + 42, py + 42], fill=(30, 110, 235), outline=WHITE, width=4)
                    d.text((px - 30, py - 22), "R-01", font=font(26), fill=WHITE)
                else:
                    pu = 1 + 0.12 * math.sin(t * 5 + i)
                    r = 34 * pu
                    d.ellipse([px - r, py - r, px + r, py + r], fill=(40, 40, 50), outline=YEL, width=3)
                    f = font(40)
                    d.text((px - 12, py - 26), "?", font=f, fill=YEL)
                i += 1
        stamp(im, "FALTAN 10", cx, PH * 0.47, 0.8, t, size=70)
        return im
    if kind == "x_rb_votar":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(18, 18, 24))
        cards = [("Un portero pulpo con 8 brazos", 1.0), ("Un delantero cohete", 0.55), ("Un defensa muro de hormigón", 0.3)]
        for i, (txt, w) in enumerate(cards):
            k = _e((t - i * 0.35) / 0.4)
            y = PH * (0.31 + 0.085 * i)
            x = 60 - 700 * (1 - k)
            d.rounded_rectangle([x, y, x + PW - 120, y + 120], 22, fill=(34, 34, 44), outline=(70, 70, 90), width=2)
            d.ellipse([x + 20, y + 25, x + 90, y + 95], fill=[(30, 110, 235), (230, 120, 30), (60, 170, 90)][i])
            d.text((x + 110, y + 22), "@tú", font=font(28), fill=(160, 160, 180))
            d.text((x + 110, y + 60), txt, font=font(34), fill=WHITE)
            likes = int(999 * w * _e((t - 0.8) / 1.6)) if t > 0.8 else 0
            hx = x + PW - 210
            d.text((hx, y + 40), f"♥ {likes}", font=font(36), fill=(255, 70, 90) if i == 0 else (200, 200, 210))
        if t > 2.4:
            stamp(im, "EL MÁS VOTADO JUEGA", cx, PH * 0.255, 2.4, t, size=52)
        return im
    if kind == "x_rb_comentario":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(12, 12, 18))
        for i in range(16):
            a = i / 16 * 2 * math.pi + t * 0.4
            d.polygon([(cx, PH * 0.47), (cx + 1500 * math.cos(a), PH * 0.47 + 1500 * math.sin(a)),
                       (cx + 1500 * math.cos(a + 0.12), PH * 0.47 + 1500 * math.sin(a + 0.12))], fill=(26, 26, 40))
        from pathlib import Path
        src = Path(__file__).resolve().parent.parent / "assets" / "robotfc" / "comentario_ep2.png"
        c = Image.open(src).convert("RGB")
        box = (12, 30, 72, 92)  # avatar: pixelado
        av = c.crop(box).resize((6, 6)).resize((box[2] - box[0], box[3] - box[1]), Image.NEAREST)
        c.paste(av, box[:2])
        k = _e(t / 0.5)
        w = int((PW - 60) * (0.6 + 0.4 * k))
        c = c.resize((w, int(w * c.height / c.width)), Image.BICUBIC)
        y = int(PH * 0.42 + 300 * (1 - k))
        im = _glow(im, lambda g: g.rounded_rectangle([cx - w / 2 - 10, y - 10, cx + w / 2 + 10, y + c.height + 10], 20, fill=(30, 110, 235)), 30)
        im.paste(c, (int(cx - w / 2), y))
        ImageDraw.Draw(im).rounded_rectangle([cx - w / 2 - 6, y - 6, cx + w / 2 + 6, y + c.height + 6], 18, outline=CYAN, width=5)
        stamp(im, "EL MÁS VOTADO", cx, PH * 0.32, 0.6, t, size=60)
        return im
    if kind in ("x_rb_fichaje", "x_rb_ultra"):
        from .anim_extra import person
        d = _lab(im, t)
        py = PH * 0.64
        ultra = kind == "x_rb_ultra"
        k = _e(t / 0.8) if not ultra else 1.0
        pw = _e((t - 0.3) / 1.2) if ultra else 0.0
        if not ultra:
            r = 260 * k
            im = _glow(im, lambda g: g.ellipse([cx - r, PH * 0.47 - r * 1.3, cx + r, PH * 0.47 + r * 1.3], outline=CYAN, width=30), 25)
            d = ImageDraw.Draw(im)
        else:
            fl = 0.7 + 0.3 * math.sin(t * 25)
            def aura(g):
                for i in range(3):
                    rr = (150 + 40 * i) * pw * fl
                    g.ellipse([cx - rr, py - 380 - rr * 1.2, cx + rr, py + 20], fill=(int(120 * pw), int(200 * pw), int(255 * pw)))
            im = _glow(im, aura, 35)
            d = ImageDraw.Draw(im)
            rnd = random.Random(int(t * 15))
            for _ in range(int(6 * pw)):
                x0 = cx + rnd.uniform(-220, 220)
                pts = [(x0, PH * 0.28)]
                for j in range(5):
                    pts.append((pts[-1][0] + rnd.uniform(-40, 40), pts[-1][1] + PH * 0.07))
                d.line(pts, fill=(220, 240, 255), width=4)
        person(d, cx, py + 30 * (1 - k), 2.0, (30, 110, 235), (224, 172, 125), "tupe", (30, 22, 16), "7",
               pose="brazos_cruzados" if not ultra else "", arm_up=pw, mouth="sonrisa" if not ultra else "abierta")
        if ultra:
            for sg in (-1, 1):
                ex = cx + sg * 26
                d.ellipse([ex - 9, py - 2.0 * 205 - 9, ex + 9, py - 2.0 * 205 + 9], fill=(200, 240, 255))
        if not ultra:
            stamp(im, "FICHAJE: CR7 2008", cx, PH * 0.30, 0.8, t, size=58)
        elif t > 1.0:
            text_c(ImageDraw.Draw(im), cx, PH * 0.27, "MODO ULTRA", 90, (200, 240, 255), 10)
        return im
    if kind == "x_rb_golazo":
        d = _lava_sky(im, t)
        for i, dx in enumerate((-260, 0, 260)):
            titan(d, cx + dx, PH * 0.62, 0.65, t, i)
        T = max(dur * 0.62, 0.9)
        p = min(t / T, 1)
        bx, by = PW * 0.1 + PW * 0.8 * p, PH * 0.66 - PH * 0.30 * p
        def beam(g):
            g.line([(PW * 0.1, PH * 0.66), (bx, by)], fill=(150, 220, 255), width=40)
        im = _glow(im, beam, 20)
        d = ImageDraw.Draw(im)
        d.line([(PW * 0.1, PH * 0.66), (bx, by)], fill=WHITE, width=10)
        ball(d, bx, by, 26)
        if t > T:
            if t < T + 0.25:
                im = Image.blend(im, Image.new("RGB", im.size, (220, 240, 255)), 0.8 * (1 - (t - T) / 0.25))
                d = ImageDraw.Draw(im)
            text_c(d, cx, PH * 0.30, "¡GOL!", 150, YEL, 12)
            text_c(d, cx, PH * 0.45, "1 - 0", 110, WHITE, 10)
        return im
    if kind == "x_rb_remontada":
        d = _lava_sky(im, t)
        for i, dx in enumerate((-300, -150, 0, 150, 300)):
            titan(d, cx + dx, PH * 0.66, 0.75 + 0.1 * (i == 2), t, i)
        n = 1 + min(4, int(max(t - 0.3, 0) * 3))
        d.rounded_rectangle([cx - 260, PH * 0.27, cx + 260, PH * 0.27 + 130], 20, fill=INK)
        text_c(d, cx - 180, PH * 0.27 + 40, "ROB", 40, (150, 190, 255), 0)
        text_c(d, cx + 180, PH * 0.27 + 40, "TIT", 40, (255, 140, 100), 0)
        text_c(d, cx, PH * 0.27 + 14, f"1-{n}", 96, YEL, 0)
        stamp(im, "TODAVÍA NO BASTA", cx, PH * 0.40, 1.9, t, bg=RED, fg=WHITE, size=56)
        return im
    if kind == "x_rb_plantilla2":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(22, 70, 40))
        x0, y0, x1, y1 = 50, PH * 0.28, PW - 160, PH * 0.64
        d.rounded_rectangle([x0, y0, x1, y1], 20, outline=WHITE, width=5)
        d.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=WHITE, width=4)
        rows = [[0.5], [0.15, 0.38, 0.62, 0.85], [0.25, 0.5, 0.75], [0.3, 0.7], [0.5]]
        ys = [0.92, 0.74, 0.52, 0.3, 0.1]
        i = 0
        for row, yy in zip(rows, ys):
            for xx in row:
                px, py = x0 + (x1 - x0) * xx, y0 + (y1 - y0) * yy
                if i == 0 or (i == 9 and t > 0.4):
                    s2 = 1 if i == 0 else _e((t - 0.4) / 0.3)
                    r = 44 * s2
                    d.ellipse([px - r, py - r, px + r, py + r], fill=(30, 110, 235), outline=WHITE, width=4)
                    d.text((px - 30, py - 20), "R-01" if i == 0 else "CR7", font=font(26), fill=WHITE)
                else:
                    r = 34 * (1 + 0.12 * math.sin(t * 5 + i))
                    d.ellipse([px - r, py - r, px + r, py + r], fill=(40, 40, 50), outline=YEL, width=3)
                    d.text((px - 12, py - 26), "?", font=font(40), fill=YEL)
                i += 1
        stamp(im, "FALTAN 9", cx, PH * 0.47, 1.0, t, size=70)
        return im
    return None
