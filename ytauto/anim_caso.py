"""Formato «Expediente»: casos reales del fútbol contados como cine negro.

Primer caso (041): la Copa del Mundo robada en Londres en 1966 y Pickles, el perro que la encontró.
Animaciones x_ca_*. Todas comparten personajes (Pickles, el dueño, el bobby, la Copa) y la misma
luz: fondo azul noche, focos cálidos, grano de película y viñeta.

Sincronía con la voz: shorts.py deja en anim.SYNC las palabras de la escena con su segundo,
y w("perro") devuelve cuándo se dice esa palabra.
"""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import anim as A

BOLD = A.BOLD
MONO = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

NIGHT, NIGHT2 = (9, 13, 26), (18, 26, 48)
WARM = (255, 232, 180)
GOLD, GOLD_L, GOLD_D = (236, 184, 52), (255, 226, 120), (160, 110, 25)
LAPIS, LAPIS_D = (38, 70, 160), (22, 40, 100)
INK, WHITE = (10, 12, 20), (255, 255, 255)
DOG, DOG_W = (30, 30, 36), (242, 240, 232)
COLLAR, RED = (210, 40, 50), (215, 40, 50)
BOBBY, SKIN = (24, 32, 64), (236, 192, 152)
COAT, CAP = (122, 88, 58), (70, 70, 78)
YEL, GREEN = (255, 214, 10), (70, 200, 120)


def _e(x):
    return A._ease(x)


def _c(x):
    return min(max(x, 0.0), 1.0)


def font(n, path=BOLD):
    return ImageFont.truetype(path, int(n))


def w(word: str, default: float = 0.0, nth: int = 0) -> float:
    """Segundo (desde el inicio de la escena) en que la voz dice `word`."""
    hits = [t for x, t in A.SYNC.get("words", []) if x.strip(".,¿?¡!:;…").lower() == word.lower()]
    return hits[nth] if len(hits) > nth else default


# ------------------------------------------------------------------ cámara, luz y textura
def cam(im, fx, fy, z, rot=0.0):
    """Cámara con subpíxel (sin saltos en zooms lentos): zoom z centrado en (fx, fy)."""
    W, H = im.size
    cw, ch = W / z, H / z
    x0 = min(max(fx - cw / 2, 0), W - cw)
    y0 = min(max(fy - ch / 2, 0), H - ch)
    out = im.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC)
    if rot:
        out = out.rotate(rot, resample=Image.BICUBIC, fillcolor=NIGHT)
    return out


def add(im, lay):
    """Suma de luz (modo «add»)."""
    a = np.asarray(im, dtype=np.uint16) + np.asarray(lay, dtype=np.uint16)
    return Image.fromarray(np.minimum(a, 255).astype(np.uint8))


def glow(im, fn, blur=22, strength=1.0):
    lay = Image.new("RGB", im.size, (0, 0, 0))
    fn(ImageDraw.Draw(lay))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    if strength != 1.0:
        lay = Image.fromarray((np.asarray(lay) * strength).clip(0, 255).astype(np.uint8))
    return add(im, lay)


def spotlight(im, x, top, bx, by, half_w, k=1.0, col=WARM):
    """Cono de luz desde (x, top) hasta una elipse en el suelo (bx, by)."""
    lay = Image.new("RGB", im.size, (0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = tuple(int(v * 0.22 * k) for v in col)
    d.polygon([(x - 30, top), (x + 30, top), (bx + half_w, by), (bx - half_w, by)], fill=c)
    c2 = tuple(int(v * 0.35 * k) for v in col)
    d.ellipse([bx - half_w, by - half_w * 0.22, bx + half_w, by + half_w * 0.22], fill=c2)
    lay = lay.filter(ImageFilter.GaussianBlur(26))
    return add(im, lay)


def motes(d, x, top, bx, by, half_w, t, n=26, seed=3):
    """Polvo flotando dentro del cono de luz."""
    rng = random.Random(seed)
    for _ in range(n):
        v = rng.random()
        u = (rng.random() - 0.5) * 2
        yy = top + (by - top) * ((v + t * rng.uniform(0.01, 0.04)) % 1)
        k = (yy - top) / max(1, by - top)
        xx = x + (bx - x) * k + u * (30 + (half_w - 30) * k) + 8 * math.sin(t * 0.8 + v * 9)
        r = rng.uniform(1.2, 2.6)
        a = int(140 * math.sin(math.pi * k))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(a, a, int(a * 0.85)))


def fog(im, t, y, alpha=40, seed=1):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = random.Random(seed)
    PW = im.size[0]
    for _ in range(9):
        cx = (rng.uniform(-200, PW + 200) + t * rng.uniform(10, 30)) % (PW + 400) - 200
        cy = y + rng.uniform(-60, 60)
        rx, ry = rng.uniform(160, 300), rng.uniform(30, 60)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(170, 180, 210, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(30))
    im.paste(lay, (0, 0), lay)


def grain(im, t, k=4):
    """Grano suave: cambia cada 3 fotogramas y a media resolución (si no, el vídeo pesa 10 veces más)."""
    a = np.asarray(im, dtype=np.int16)
    rng = np.random.default_rng(int(t * 10) + 11)
    h, w_ = a.shape[0] // 3 + 1, a.shape[1] // 3 + 1
    n = np.repeat(np.repeat(rng.integers(-k, k + 1, (h, w_), dtype=np.int16), 3, 0), 3, 1)
    n = n[: a.shape[0], : a.shape[1], None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def vignette(im, k=0.6):
    PW, PH = im.size
    m = Image.new("L", (PW // 8, PH // 8), 0)
    ImageDraw.Draw(m).ellipse([-PW // 14, -PH // 22, PW // 8 + PW // 14, PH // 8 + PH // 22], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(12)).resize((PW, PH), Image.BILINEAR)
    return Image.composite(im, Image.blend(im, Image.new("RGB", (PW, PH)), k), m)


def finish(im, t, vig=0.6):
    return grain(vignette(im, vig), t)


def bg(im, top=NIGHT2, bot=NIGHT):
    d = ImageDraw.Draw(im)
    PW, PH = im.size
    for i in range(64):
        k = i / 63
        c = tuple(int(top[j] * (1 - k) + bot[j] * k) for j in range(3))
        d.rectangle([0, PH * i / 64, PW, PH * (i + 1) / 64 + 1], fill=c)
    return d


# ------------------------------------------------------------------ rótulos
def typed(d, x, y, text, t, t0=0.0, cps=22, size=40, col=WARM, center=False):
    """Texto a máquina de escribir con cursor."""
    n = int(max(0.0, t - t0) * cps)
    if t < t0:
        return
    f = font(size, MONO)
    s = text[:n]
    tw = d.textlength(text, font=f)
    x0 = x - tw / 2 if center else x
    d.text((x0 + 3, y + 3), s, font=f, fill=(0, 0, 0))
    d.text((x0, y), s, font=f, fill=col)
    if n < len(text) or int(t * 3) % 2:
        cx = x0 + d.textlength(s, font=f)
        d.rectangle([cx + 2, y + 4, cx + size * 0.55, y + size * 0.95], fill=col)


def rubber(im, text, cx, cy, t0, t, col=RED, size=78, rot=-8, sub=None):
    """Sello de goma de expediente: cae, aplasta y queda con textura."""
    if t < t0:
        return
    k = _c((t - t0) / 0.18)
    sc = 2.2 - 1.2 * _e(k) if k < 1 else 1.0 + 0.04 * math.exp(-(t - t0 - 0.18) * 12) * math.sin((t - t0) * 50)
    f = font(size)
    probe = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    tw = int(probe.textlength(text, font=f))
    h = int(size * 1.45) + (int(size * 0.5) if sub else 0)
    wdt = tw + 70
    lay = Image.new("RGBA", (wdt, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([4, 4, wdt - 5, h - 5], 16, fill=(242, 236, 222, 235), outline=col + (255,), width=9)
    ld.text((35, size * 0.16), text, font=f, fill=col + (255,))
    if sub:
        fs = font(size * 0.36)
        sw = ld.textlength(sub, font=fs)
        ld.text(((wdt - sw) / 2, size * 1.22), sub, font=fs, fill=col + (255,))
    a = np.asarray(lay).copy()
    rng = np.random.default_rng(len(text))
    holes = (rng.random(a.shape[:2]) < 0.035) & (a[..., :3].sum(axis=2) < 600)
    a[..., 3] = np.where(holes, (a[..., 3] * 0.35).astype(np.uint8), a[..., 3])
    lay = Image.fromarray(a).rotate(rot, expand=True, resample=Image.BICUBIC)
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.BICUBIC)
    if k < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * (0.4 + 0.6 * k))))
    im.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


def label(d, cx, y, text, size=56, col=WHITE, stroke=8):
    f = font(size)
    tw = d.textlength(text, font=f)
    d.text((cx - tw / 2, y), text, font=f, fill=col, stroke_width=stroke, stroke_fill=INK)


# ------------------------------------------------------------------ personajes
def trophy(im, cx, by, s=1.0, shine=0.0, t=0.0):
    """Copa Jules Rimet: base de lapislázuli y victoria alada de oro sosteniendo un vaso octogonal.

    (cx, by) = centro de la base en el suelo. Alto total ~ 330*s.
    """
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (cx + x * s, by + y * s)

    # base
    d.polygon([P(-62, 0), P(62, 0), P(52, -70), P(-52, -70)], fill=LAPIS, outline=INK, width=max(2, int(4 * s)))
    d.polygon([P(-58, -10), P(-20, -10), P(-24, -64), P(-50, -64)], fill=LAPIS_D)
    d.rectangle([P(-56, -46), P(56, -36)], fill=GOLD)
    d.polygon([P(-50, -70), P(50, -70), P(40, -84), P(-40, -84)], fill=GOLD_D, outline=INK, width=max(2, int(3 * s)))
    # alas (detrás)
    for sg in (-1, 1):
        d.polygon([P(sg * 10, -170), P(sg * 70, -260), P(sg * 82, -300), P(sg * 52, -250), P(sg * 20, -200)],
                  fill=GOLD_D, outline=INK, width=max(2, int(3 * s)))
        d.polygon([P(sg * 12, -175), P(sg * 62, -250), P(sg * 70, -285), P(sg * 40, -238)], fill=GOLD)
    # cuerpo (túnica)
    d.polygon([P(-34, -84), P(34, -84), P(18, -150), P(14, -205), P(-14, -205), P(-18, -150)],
              fill=GOLD, outline=INK, width=max(2, int(4 * s)))
    for k in range(4):
        x = -18 + k * 12
        d.line([P(x, -92), P(x * 0.6, -190)], fill=GOLD_D, width=max(1, int(3 * s)))
    # cabeza y brazos hacia arriba
    d.ellipse([P(-12, -232), P(12, -206)], fill=GOLD, outline=INK, width=max(2, int(3 * s)))
    for sg in (-1, 1):
        d.line([P(sg * 12, -196), P(sg * 30, -250), P(sg * 34, -282)], fill=GOLD, width=max(3, int(9 * s)), joint="curve")
    # vaso octogonal
    d.polygon([P(-62, -330), P(62, -330), P(46, -282), P(-46, -282)], fill=GOLD, outline=INK, width=max(2, int(4 * s)))
    d.polygon([P(-62, -330), P(62, -330), P(54, -340), P(-54, -340)], fill=GOLD_L, outline=INK, width=max(2, int(3 * s)))
    for x in (-30, 0, 30):
        d.line([P(x, -330), P(x * 0.75, -284)], fill=GOLD_D, width=max(1, int(3 * s)))
    # brillo que recorre la copa
    if shine > 0:
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        sx = -120 + 240 * ((t * 0.6) % 1.0)
        ld.polygon([P(sx - 10, -340), P(sx + 14, -340), P(sx - 30, -90), P(sx - 54, -90)],
                   fill=(255, 255, 230, int(150 * shine)))
        mk = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(mk)
        md.polygon([P(-62, -340), P(62, -340), P(46, -282), P(18, -150), P(34, -84), P(-34, -84), P(-18, -150), P(-46, -282)], fill=255)
        im.paste(lay, (0, 0), Image.fromarray(np.minimum(np.asarray(lay.getchannel("A")), np.asarray(mk))))


def trophy_glow(im, cx, by, s=1.0, k=1.0):
    return glow(im, lambda d: d.ellipse([cx - 120 * s, by - 380 * s, cx + 120 * s, by - 40 * s],
                                        fill=(int(255 * k), int(200 * k), int(90 * k))), blur=60)


def dog(d, x, y, s=1.0, f=1, pose="stand", phase=0.0, wag=0.0, blink=False, tongue=False,
        head=(0.0, 0.0), medal=False, bowtie=False, happy=False):
    """Pickles: collie mestizo negro y blanco con collar rojo. (x, y) = suelo bajo el cuerpo.

    f=1 mira a la derecha, f=-1 a la izquierda. pose: stand, walk, sniff, sit.
    """
    def P(dx, dy):
        return (x + f * dx * s, y + dy * s)

    def E(cx, cy, rx, ry, **kw):
        a, b = P(cx - rx, cy - ry), P(cx + rx, cy + ry)
        d.ellipse([min(a[0], b[0]), a[1], max(a[0], b[0]), b[1]], **kw)

    lw = max(2, int(4 * s))
    d.ellipse([x - 70 * s, y - 8 * s, x + 70 * s, y + 8 * s], fill=(0, 0, 0))
    hx, hy = head
    if pose == "sit":
        # cola en el suelo moviéndose
        ta = wag
        d.line([P(-40, -10), P(-80 - 10 * math.sin(ta), -14 - 22 * abs(math.sin(ta)))], fill=DOG, width=int(16 * s), joint="curve")
        E(-6, -56, 46, 50, fill=DOG, outline=INK, width=lw)  # cuerpo sentado
        for dx in (-26, 26):  # patas traseras
            E(dx * 0.6 - 14, -14, 26, 16, fill=DOG, outline=INK, width=lw)
        for dx in (18, 34):  # patas delanteras rectas
            d.line([P(dx, -70), P(dx, -6)], fill=DOG, width=int(15 * s))
            E(dx + 4, -6, 11, 7, fill=DOG_W, outline=INK, width=max(1, lw - 1))
        E(28, -88, 22, 32, fill=DOG_W)  # pecho blanco
        nx, ny = 34 + hx, -142 + hy
    else:
        sw = math.sin(phase) if pose == "walk" else 0.0
        # cola
        ta = wag
        d.line([P(-54, -76), P(-80, -96 - 18 * math.sin(ta)), P(-94 - 8 * math.cos(ta), -122 - 10 * math.sin(ta))],
               fill=DOG, width=int(14 * s), joint="curve")
        # patas (las del fondo más oscuras)
        legs = [(-36, 1), (30, -1), (-24, -1), (40, 1)]
        for k, (dx, ph) in enumerate(legs):
            sw_k = sw * ph * 22
            top = P(dx, -60)
            knee = P(dx + sw_k * 0.4, -30)
            foot = P(dx + sw_k, -4 + (-8 * max(0.0, -sw * ph) if pose == "walk" else 0))
            col = (20, 20, 26) if k >= 2 else DOG
            d.line([top, knee, foot], fill=col, width=int(14 * s), joint="curve")
            E(dx + sw_k + 4, -4, 11, 6, fill=DOG_W if k < 2 else (200, 200, 195), outline=INK, width=max(1, lw - 1))
        E(0, -68, 60, 30, fill=DOG, outline=INK, width=lw)
        E(44, -64, 22, 22, fill=DOG_W)  # pecho blanco
        if pose == "sniff":
            nx, ny = 84 + hx, -66 + hy
        else:
            nx, ny = 66 + hx, -112 + hy
    # cuello
    d.line([P(nx - 34, ny + 52), P(nx - 6, ny + 8)] if pose != "sit" else [P(20, -100), P(nx - 4, ny + 10)],
           fill=DOG, width=int(30 * s))
    # collar
    cxp, cyp = P(nx - 18, ny + 30) if pose != "sit" else P(nx - 8, ny + 30)
    d.line([(cxp - 16 * s, cyp - 12 * s), (cxp + 14 * s, cyp + 10 * s)], fill=COLLAR, width=int(9 * s))
    d.ellipse([cxp - 6 * s, cyp + 4 * s, cxp + 6 * s, cyp + 16 * s], fill=GOLD, outline=INK, width=1)
    # cabeza
    E(nx, ny, 32, 30, fill=DOG, outline=INK, width=lw)
    d.polygon([P(nx + 4, ny - 30), P(nx + 16, ny - 28), P(nx + 30, ny + 2), P(nx + 12, ny + 6)], fill=DOG_W)  # mancha
    E(nx + 30, ny + 10, 22, 15, fill=DOG_W, outline=INK, width=lw)  # hocico
    E(nx + 50, ny + 4, 7, 6, fill=INK)  # nariz
    if tongue:
        E(nx + 38, ny + 26, 7, 10, fill=(235, 110, 130), outline=INK, width=1)
    # oreja caída
    d.polygon([P(nx - 22, ny - 24), P(nx - 4, ny - 32), P(nx - 10, ny + 4), P(nx - 26, ny + 8)], fill=(18, 18, 22),
              outline=INK)
    # ojo
    ex, ey = P(nx + 12, ny - 6)
    if blink or happy:
        d.arc([ex - 8 * s, ey - 4 * s, ex + 8 * s, ey + 8 * s], 200, 340, fill=WHITE, width=max(2, int(4 * s)))
    else:
        d.ellipse([ex - 8 * s, ey - 8 * s, ex + 8 * s, ey + 8 * s], fill=WHITE)
        d.ellipse([ex - 4 * s + f * 2 * s, ey - 4 * s, ex + 4 * s + f * 2 * s, ey + 4 * s], fill=INK)
        d.ellipse([ex - 1 * s + f * 3 * s, ey - 4 * s, ex + 2 * s + f * 3 * s, ey - 1 * s], fill=WHITE)
    if bowtie:
        bx, by = P(nx - 10, ny + 40)
        d.polygon([(bx, by), (bx - 18 * s, by - 10 * s), (bx - 18 * s, by + 10 * s)], fill=RED, outline=INK)
        d.polygon([(bx, by), (bx + 18 * s, by - 10 * s), (bx + 18 * s, by + 10 * s)], fill=RED, outline=INK)
        d.ellipse([bx - 5 * s, by - 5 * s, bx + 5 * s, by + 5 * s], fill=(150, 20, 30))
    if medal:
        mx, my = P(nx - 6, ny + 74) if pose == "sit" else P(nx - 12, ny + 66)
        d.polygon([(mx - 10 * s, my - 30 * s), (mx + 10 * s, my - 30 * s), (mx + 4 * s, my - 4 * s), (mx - 4 * s, my - 4 * s)],
                  fill=(40, 90, 200))
        d.ellipse([mx - 16 * s, my - 6 * s, mx + 16 * s, my + 26 * s], fill=(210, 214, 222), outline=INK, width=max(2, lw - 1))
        d.ellipse([mx - 8 * s, my + 2 * s, mx + 8 * s, my + 18 * s], outline=(150, 150, 160), width=max(1, int(2 * s)))


def man(d, x, y, s=1.0, f=1, phase=0.0, run=0.0, arm=0.0, face="normal", sweat=0.0, t=0.0, seated=False):
    """El dueño (David Corbett): gorra plana, abrigo marrón. (x, y) = pies. Visto de 3/4."""
    def P(dx, dy):
        return (x + f * dx * s, y + dy * s)

    lw = max(2, int(4 * s))
    sw = math.sin(phase) * run
    if not seated:
        d.ellipse([x - 50 * s, y - 8 * s, x + 50 * s, y + 8 * s], fill=(0, 0, 0))
        for k, sg in enumerate((1, -1)):
            knee = P(sg * sw * 16, -48)
            foot = P(sg * sw * 30, -4 + (-10 * max(0.0, sg * sw)))
            d.line([P(sg * 8, -96), knee, foot], fill=(70, 72, 84) if k else (56, 58, 70), width=int(17 * s), joint="curve")
            d.ellipse([foot[0] - 14 * s, foot[1] - 7 * s, foot[0] + 16 * s, foot[1] + 6 * s], fill=INK)
    # abrigo
    d.polygon([P(-30, -100), P(30, -100), P(36, -78) if not seated else P(30, -100), P(26, -186), P(-26, -186),
               P(-36, -78) if not seated else P(-30, -100)], fill=COAT, outline=INK, width=lw)
    d.line([P(0, -184), P(4, -104)], fill=(90, 62, 40), width=max(2, int(3 * s)))
    d.polygon([P(-12, -186), P(12, -186), P(0, -160)], fill=(230, 230, 220))
    # brazo trasero y delantero
    d.line([P(-22, -176), P(-30 - sw * 10, -132), P(-28 - sw * 16, -100)], fill=(100, 70, 46), width=int(14 * s), joint="curve")
    hand = P(30 + 20 * math.cos(arm), -120 - 40 * math.sin(arm))
    d.line([P(22, -176), P(34, -146), hand], fill=COAT, width=int(15 * s), joint="curve")
    d.ellipse([hand[0] - 8 * s, hand[1] - 8 * s, hand[0] + 8 * s, hand[1] + 8 * s], fill=SKIN, outline=INK, width=1)
    # cabeza
    hx, hy = P(4, -222)
    d.ellipse([hx - 30 * s, hy - 32 * s, hx + 30 * s, hy + 30 * s], fill=SKIN, outline=INK, width=lw)
    # gorra plana
    d.chord([hx - 33 * s, hy - 40 * s, hx + 33 * s, hy + 4 * s], 180, 360, fill=CAP, outline=INK, width=lw)
    d.polygon([(hx + f * 10 * s, hy - 14 * s), (hx + f * 46 * s, hy - 10 * s), (hx + f * 30 * s, hy - 4 * s)], fill=(50, 50, 58))
    # cara
    ex = hx + f * 10 * s
    if face == "worried":
        d.ellipse([ex - 6 * s, hy - 4 * s, ex + 6 * s, hy + 8 * s], fill=WHITE, outline=INK, width=1)
        d.ellipse([ex - 2 * s, hy, ex + 3 * s, hy + 5 * s], fill=INK)
        d.line([(ex - 9 * s, hy - 10 * s), (ex + 7 * s, hy - 14 * s)], fill=INK, width=max(2, int(3 * s)))
        d.arc([hx + f * 2 * s - 9 * s, hy + 12 * s, hx + f * 2 * s + 9 * s, hy + 24 * s], 200, 340, fill=INK, width=max(2, int(3 * s)))
    elif face == "shock":
        d.ellipse([ex - 7 * s, hy - 6 * s, ex + 7 * s, hy + 8 * s], fill=WHITE, outline=INK, width=1)
        d.ellipse([ex - 2 * s, hy - 1 * s, ex + 3 * s, hy + 4 * s], fill=INK)
        d.ellipse([hx + f * 4 * s - 6 * s, hy + 12 * s, hx + f * 4 * s + 6 * s, hy + 24 * s], fill=INK)
    else:
        d.ellipse([ex - 3 * s, hy - 2 * s, ex + 3 * s, hy + 4 * s], fill=INK)
        d.arc([hx + f * 4 * s - 9 * s, hy + 6 * s, hx + f * 4 * s + 9 * s, hy + 18 * s], 20, 160, fill=INK, width=max(2, int(3 * s)))
    d.line([(hx + f * 22 * s, hy - 2 * s), (hx + f * 30 * s, hy + 8 * s), (hx + f * 22 * s, hy + 10 * s)], fill=INK, width=max(1, int(2 * s)))
    if sweat > 0:
        for k in range(3):
            p = (t * 1.3 + k / 3) % 1
            sx = hx + (-26 + 22 * k) * s
            sy = hy - 20 * s + p * 50 * s
            r = 5 * s
            d.polygon([(sx, sy - 2.2 * r), (sx - r, sy), (sx + r, sy)], fill=(140, 200, 255))
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(140, 200, 255))


def bobby(d, x, y, s=1.0, f=1, sil=False, arm=0.0):
    """Policía londinense con casco de «bobby». sil=True: silueta."""
    def P(dx, dy):
        return (x + f * dx * s, y + dy * s)

    col = (6, 8, 16) if sil else BOBBY
    lw = max(2, int(4 * s))
    for sg in (1, -1):
        d.line([P(sg * 10, -96), P(sg * 12, -6)], fill=col, width=int(18 * s))
    d.rounded_rectangle([x - 34 * s, y - 196 * s, x + 34 * s, y - 92 * s], int(12 * s), fill=col,
                        outline=None if sil else INK, width=lw)
    if not sil:
        for k in range(4):
            d.ellipse([x - 3 * s, y - (182 - 24 * k) * s, x + 3 * s, y - (176 - 24 * k) * s], fill=(200, 200, 210))
    hand = P(46 + 30 * math.cos(arm), -150 - 30 * math.sin(arm))
    d.line([P(28, -186), hand], fill=col, width=int(15 * s))
    hx, hy = x, y - 226 * s
    d.ellipse([hx - 26 * s, hy - 26 * s, hx + 26 * s, hy + 28 * s], fill=col if sil else SKIN,
              outline=None if sil else INK, width=lw)
    # casco
    d.pieslice([hx - 30 * s, hy - 92 * s, hx + 30 * s, hy + 4 * s], 180, 360, fill=col if sil else (16, 22, 46),
               outline=None if sil else INK, width=lw)
    d.rectangle([hx - 30 * s, hy - 46 * s, hx + 30 * s, hy - 12 * s], fill=col if sil else (16, 22, 46))
    d.ellipse([hx - 7 * s, hy - 100 * s, hx + 7 * s, hy - 86 * s], fill=col if sil else (200, 200, 210))
    d.rectangle([hx - 36 * s, hy - 14 * s, hx + 36 * s, hy - 6 * s], fill=col if sil else (16, 22, 46))
    if not sil:
        d.polygon([(hx, hy - 52 * s), (hx - 9 * s, hy - 38 * s), (hx, hy - 24 * s), (hx + 9 * s, hy - 38 * s)], fill=(210, 210, 220))
        ex = hx + f * 10 * s
        d.ellipse([ex - 3 * s, hy + 2 * s, ex + 3 * s, hy + 8 * s], fill=INK)
        d.line([(hx - 4 * s, hy + 18 * s), (hx + 14 * s * f, hy + 16 * s)], fill=INK, width=max(2, int(3 * s)))
        d.rectangle([hx - 14 * s, hy + 12 * s, hx + 16 * s, hy + 16 * s], fill=(60, 40, 30))  # bigote


def glove(d, x, y, s=1.0, grab=0.0):
    """Mano con guante negro que baja desde arriba. (x, y) = palma."""
    d.line([(x, y - 30 * s), (x - 30 * s, y - 900 * s)], fill=(14, 14, 20), width=int(70 * s))
    d.rounded_rectangle([x - 46 * s, y - 50 * s, x + 46 * s, y + 30 * s], int(24 * s), fill=(20, 20, 28), outline=(60, 60, 80), width=3)
    for k in range(4):
        fx = x - 36 * s + k * 24 * s
        ln = (70 - 8 * abs(k - 1.5)) * s * (1 - 0.55 * grab)
        d.line([(fx, y + 10 * s), (fx + 8 * grab * s, y + 10 * s + ln)], fill=(20, 20, 28), width=int(20 * s))
    d.line([(x + 44 * s, y - 10 * s), (x + 70 * s - 30 * grab * s, y + 40 * s)], fill=(20, 20, 28), width=int(22 * s))


def case(d, cx, by, s=1.0, empty=False):
    """Pedestal y vitrina de cristal. by = suelo."""
    d.polygon([(cx - 130 * s, by), (cx + 130 * s, by), (cx + 110 * s, by - 260 * s), (cx - 110 * s, by - 260 * s)],
              fill=(36, 30, 40), outline=INK, width=4)
    d.rectangle([cx - 140 * s, by - 290 * s, cx + 140 * s, by - 258 * s], fill=(54, 44, 56), outline=INK, width=4)
    d.rectangle([cx - 90 * s, by - 180 * s, cx + 90 * s, by - 150 * s], fill=(160, 130, 70))
    f = font(18 * s)
    lab = "COPA DEL MUNDO"
    d.text((cx - d.textlength(lab, font=f) / 2, by - 176 * s), lab, font=f, fill=INK)


def case_glass(im, cx, by, s=1.0):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    top = by - 290 * s
    ld.rectangle([cx - 130 * s, top - 420 * s, cx + 130 * s, top], fill=(160, 190, 230, 22), outline=(190, 210, 240, 140), width=3)
    ld.polygon([(cx - 100 * s, top - 400 * s), (cx - 60 * s, top - 400 * s), (cx - 120 * s, top - 20 * s), (cx - 126 * s, top - 120 * s)],
               fill=(255, 255, 255, 30))
    im.paste(lay, (0, 0), lay)


def newspaper(d, x0, y0, x1, y1):
    """Hoja de periódico genérica (sin titulares inventados)."""
    d.rectangle([x0, y0, x1, y1], fill=(226, 220, 200), outline=INK, width=3)
    hh = max(10, (x1 - x0) * 0.07)
    d.rectangle([x0 + 14, y0 + 12, x1 - 14, y0 + 12 + hh], fill=(60, 58, 54))
    d.rectangle([x0 + 14, y0 + 20 + hh, x0 + (x1 - x0) * 0.6, y0 + 20 + hh * 1.5], fill=(90, 88, 80))
    yy = y0 + 30 + hh * 1.8
    cols = 3
    cw = (x1 - x0 - 28) / cols
    rng = random.Random(5)
    while yy < y1 - 12:
        for c in range(cols):
            lx = x0 + 14 + c * cw
            d.line([(lx, yy), (lx + cw * rng.uniform(0.6, 0.9), yy)], fill=(120, 116, 104), width=3)
        yy += 12


def hedge(d, x0, x1, y, h, seed=2, col=(22, 58, 36)):
    rng = random.Random(seed)
    d.rectangle([x0, y - h * 0.7, x1, y], fill=(14, 40, 24))
    for _ in range(int((x1 - x0) / 14)):
        cx = rng.uniform(x0, x1)
        cy = y - rng.uniform(0.2, 1.0) * h
        r = rng.uniform(24, 46)
        c = tuple(int(v * rng.uniform(0.8, 1.25)) for v in col)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)


def flashbulb(im, x, y, k):
    if k <= 0:
        return im
    return glow(im, lambda d: (d.ellipse([x - 90, y - 90, x + 90, y + 90], fill=(int(255 * k),) * 3),
                               d.polygon([(x - 260, y), (x, y - 14), (x + 260, y), (x, y + 14)], fill=(int(255 * k),) * 3),
                               d.polygon([(x, y - 260), (x + 14, y), (x, y + 260), (x - 14, y)], fill=(int(255 * k),) * 3)),
                blur=10)


def press(d, x, y, s=1.0, f=1):
    """Fotógrafo de prensa (silueta) con cámara de fuelle y flash de bombilla."""
    d.rounded_rectangle([x - 40 * s, y - 120 * s, x + 40 * s, y + 200 * s], int(20 * s), fill=(8, 10, 18))
    d.ellipse([x - 30 * s, y - 180 * s, x + 30 * s, y - 116 * s], fill=(8, 10, 18))
    d.rectangle([x - 46 * s, y - 166 * s, x + 46 * s, y - 154 * s], fill=(8, 10, 18))
    d.rectangle([x - 26 * s, y - 192 * s, x + 26 * s, y - 160 * s], fill=(8, 10, 18))
    d.rectangle([x - 14 * s, y - 188 * s, x + 6 * s, y - 176 * s], fill=(220, 220, 210))  # cartel PRESS
    cx = x + f * 50 * s
    d.rectangle([cx - 30 * s, y - 130 * s, cx + 30 * s, y - 80 * s], fill=(20, 22, 30), outline=(70, 70, 80), width=2)
    d.ellipse([cx + f * 22 * s - 14 * s, y - 118 * s, cx + f * 22 * s + 14 * s, y - 90 * s], fill=(50, 60, 80))
    d.line([(cx - f * 10 * s, y - 130 * s), (cx - f * 10 * s, y - 170 * s)], fill=(70, 70, 80), width=int(5 * s))
    d.pieslice([cx - f * 10 * s - 26 * s, y - 200 * s, cx - f * 10 * s + 26 * s, y - 150 * s], 180, 360, fill=(190, 190, 200))


def big_ben(d, x, base, s=1.0, t=0.0):
    col = (6, 9, 20)
    d.rectangle([x - 46 * s, base - 620 * s, x + 46 * s, base], fill=col)
    d.rectangle([x - 56 * s, base - 700 * s, x + 56 * s, base - 600 * s], fill=col)
    d.polygon([(x - 56 * s, base - 700 * s), (x + 56 * s, base - 700 * s), (x, base - 900 * s)], fill=col)
    d.line([(x, base - 900 * s), (x, base - 960 * s)], fill=col, width=int(6 * s))
    for k in range(-1, 2):
        d.rectangle([x + k * 30 * s - 4 * s, base - 590 * s, x + k * 30 * s + 4 * s, base - 40 * s], fill=(12, 16, 30))


def clockface(d, x, y, r, t):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 226, 150), outline=(6, 9, 20), width=4)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line([(x + 0.8 * r * math.cos(a), y + 0.8 * r * math.sin(a)), (x + 0.92 * r * math.cos(a), y + 0.92 * r * math.sin(a))],
               fill=(60, 40, 20), width=3)
    a1 = -math.pi / 2 + t * 0.4
    a2 = -math.pi / 2 + 2.2
    d.line([(x, y), (x + 0.75 * r * math.cos(a1), y + 0.75 * r * math.sin(a1))], fill=(30, 20, 10), width=4)
    d.line([(x, y), (x + 0.5 * r * math.cos(a2), y + 0.5 * r * math.sin(a2))], fill=(30, 20, 10), width=6)


def skyline(d, PW, base, seed=4, col=(12, 16, 32), hmin=120, hmax=320, lit=0.25, t=0.0):
    rng = random.Random(seed)
    x = -20
    while x < PW + 20:
        bw = rng.uniform(60, 140)
        h = rng.uniform(hmin, hmax)
        d.rectangle([x, base - h, x + bw, base], fill=col)
        for wy in range(int(base - h + 20), int(base - 20), 34):
            for wx in range(int(x + 12), int(x + bw - 16), 26):
                if rng.random() < lit:
                    fl = 0.8 + 0.2 * math.sin(t * 3 + wx)
                    d.rectangle([wx, wy, wx + 12, wy + 16], fill=(int(250 * fl), int(210 * fl), int(120 * fl)))
        x += bw + rng.uniform(4, 20)


def calendar(im, cx, cy, t, t0, pages=7, start=20):
    """Taco de calendario que pasa hojas: 20 → 27 de marzo."""
    d = ImageDraw.Draw(im)
    k = _c((t - t0) / 0.9)
    day = start + int(round(k * pages))
    d.rounded_rectangle([cx - 90, cy - 100, cx + 90, cy + 110], 14, fill=(240, 236, 226), outline=INK, width=5)
    d.rectangle([cx - 90, cy - 100, cx + 90, cy - 50], fill=RED, outline=INK, width=5)
    f1, f2 = font(30), font(96)
    d.text((cx - d.textlength("MARZO", font=f1) / 2, cy - 94), "MARZO", font=f1, fill=WHITE)
    s = str(day)
    d.text((cx - d.textlength(s, font=f2) / 2, cy - 44), s, font=f2, fill=INK)
    if 0 < k < 1:  # hoja que vuela
        fl = (k * pages) % 1
        pts = [(cx - 90 + 200 * fl, cy - 50 - 160 * fl), (cx + 90 + 220 * fl, cy - 50 - 100 * fl),
               (cx + 90 + 160 * fl, cy + 110 - 260 * fl), (cx - 90 + 120 * fl, cy + 110 - 300 * fl)]
        d.polygon(pts, fill=(230, 226, 214), outline=INK)


# ------------------------------------------------------------------ escenas
def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    floor = PH * 0.62  # suelo de la sala (queda encima de los subtítulos)

    if kind in ("x_ca_robo", "x_ca_final"):
        # misma sala, mismo foco: el final enlaza con el principio (bucle)
        d = bg(im, (16, 20, 38), (6, 8, 16))
        d.rectangle([0, floor, PW, PH], fill=(14, 14, 24))
        for k in range(9):
            d.line([(cx + (k - 4) * 60, floor), (cx + (k - 4) * 260, PH)], fill=(22, 22, 36), width=3)
        if kind == "x_ca_robo":
            tp = w("encontró", dur * 0.5) - 0.25
            grab = _c((t - 0.3) / 0.2)
            up = _e(_c((t - 0.5) / 0.35))
            if t < tp:
                im = spotlight(im, cx, 0, cx, floor, 240, 1.0)
                d = ImageDraw.Draw(im)
                case(d, cx, floor)
                if t < 0.5:
                    im = trophy_glow(im, cx, floor - 290, 0.9, 0.35)
                    d = ImageDraw.Draw(im)
                    trophy(im, cx, floor - 290, 0.9, 0.5, t)
                gy = floor - 290 - 160 - 700 * up - 900 * (1 - _e(_c((t - 0.1) / 0.2)))
                if t < 0.9:
                    if t >= 0.5:
                        trophy(im, cx, gy + 170 - 20, 0.9)
                    glove(ImageDraw.Draw(im), cx + 10, gy, 1.0, grab)
                case_glass(im, cx, floor)
                d = ImageDraw.Draw(im)
                # alarma: luz roja que barre la sala
                if t > 0.55:
                    a = 0.5 + 0.5 * math.sin((t - 0.55) * 10)
                    lay = Image.new("RGB", im.size, (int(120 * a), 0, int(10 * a)))
                    im = add(im, lay)
                    d = ImageDraw.Draw(im)
                    typed(d, cx, PH * 0.24, "LONDRES · 1966", t, 0.6, 30, 46, WARM, True)
                im = cam(im, cx, floor - 300, 1.08 + 0.10 * _c(t / tp))
            else:
                lt = t - tp
                im = spotlight(im, cx, 0, cx, floor, 300, 1.15)
                im = trophy_glow(im, cx + 110, floor - 10, 0.75, 0.8)
                d = ImageDraw.Draw(im)
                motes(d, cx, 0, cx, floor, 300, t)
                trophy(im, cx + 110, floor - 10, 0.75, 1.0, t)
                pop = _e(_c(lt / 0.3))
                dog(ImageDraw.Draw(im), cx - 130, floor + 10 + 120 * (1 - pop), 1.25, 1, "sit", wag=t * 14,
                    tongue=True, happy=lt > 0.5 and int(lt * 2) % 3 == 0)
                im = cam(im, cx, floor - 220, 1.18 - 0.08 * _c(lt / 1.2))
            return finish(im, t, 0.62)
        # final: sala vacía, hueco con la forma del perro (enlaza con el inicio)
        im = spotlight(im, cx, 0, cx, floor, 240, 0.9 + 0.1 * math.sin(t * 9) * (t < 0.6))
        d = ImageDraw.Draw(im)
        motes(d, cx, 0, cx, floor, 240, t + 3)
        case(d, cx, floor)
        case_glass(im, cx, floor)
        d = ImageDraw.Draw(im)
        k = _c((t - 0.25) / 0.5)
        if k > 0:
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            dog(ld, cx - 235, floor + 40, 1.3, 1, "sit")
            a = np.asarray(lay)[..., 3] > 0
            edge = a & ~np.roll(a, 4, 0) | a & ~np.roll(a, -4, 0) | a & ~np.roll(a, 4, 1) | a & ~np.roll(a, -4, 1)
            yy, xx = np.nonzero(edge)
            dash = ((xx + yy) // 14) % 2 == 0
            arr = np.asarray(im).copy()
            c = np.array([170, 210, 255]) * k
            arr[yy[dash], xx[dash]] = np.maximum(arr[yy[dash], xx[dash]], c.astype(np.uint8))
            im = Image.fromarray(arr)
        im = cam(im, cx, floor - 300, 1.08 + 0.10 * _e(_c(t / max(dur, 0.1))))
        return finish(im, t, 0.66)

    if kind == "x_ca_londres":
        d = bg(im, (24, 34, 66), (8, 10, 22))
        pan = _e(_c((t - w("feria", dur * 0.5) + 0.35) / 0.6))
        my = 330 - 900 * pan
        d.ellipse([PW - 260, my - 60, PW - 140, my + 60], fill=(240, 236, 210))
        im = glow(im, lambda dd: dd.ellipse([PW - 290, my - 90, PW - 110, my + 90], fill=(110, 110, 100)), 40)
        d = ImageDraw.Draw(im)
        base = PH * 0.72 - 900 * pan
        skyline(d, PW, base, 4, (10, 14, 30), 140, 360, 0.18, t)
        big_ben(d, 230, base + 4, 1.0, t)
        clockface(d, 230, base - 650, 40, t)
        im = glow(im, lambda dd: dd.ellipse([190, base - 690, 270, base - 610], fill=(120, 100, 50)), 24)
        fog(im, t, base - 60, 50, 2)
        d = ImageDraw.Draw(im)
        if pan < 1:
            typed(d, cx, PH * 0.24, "LONDRES · 1966", t, 0.1, 28, 48, WARM, True)
        # interior: feria de sellos
        if pan > 0:
            y0 = base + 30
            sub = Image.new("RGB", (PW, PH), (40, 30, 34))
            sd = ImageDraw.Draw(sub)
            for i in range(0, PW, 60):
                sd.rectangle([i, 0, i + 30, PH], fill=(46, 34, 40))
            rng = random.Random(9)
            cols = [(200, 60, 60), (60, 110, 200), (60, 160, 90), (220, 170, 60), (150, 80, 180)]
            for r in range(2):
                for c in (0, 3):
                    sx = 70 + c * 190 + rng.uniform(-8, 8)
                    sy = 200 + r * 230 + rng.uniform(-8, 8)
                    sd.rectangle([sx, sy, sx + 140, sy + 170], fill=(236, 230, 214))
                    for z in range(0, 140, 14):  # borde dentado
                        sd.ellipse([sx + z - 5, sy - 5, sx + z + 5, sy + 5], fill=(40, 30, 34))
                        sd.ellipse([sx + z - 5, sy + 165, sx + z + 5, sy + 175], fill=(40, 30, 34))
                    sd.rectangle([sx + 14, sy + 14, sx + 126, sy + 130], fill=cols[(r * 4 + c) % 5])
                    sd.ellipse([sx + 44, sy + 40, sx + 96, sy + 100], fill=(236, 230, 214))
                    sd.text((sx + 14, sy + 136), f"{rng.randint(1, 9)}d", font=font(26), fill=INK)
            sfloor = PH * 0.66
            sd.rectangle([0, sfloor, PW, PH], fill=(26, 20, 24))
            sub = spotlight(sub, cx, 0, cx, sfloor, 230, 1.0)
            sd = ImageDraw.Draw(sub)
            case(sd, cx, sfloor, 0.9)
            sub = trophy_glow(sub, cx, sfloor - 262, 0.8, 0.5)
            trophy(sub, cx, sfloor - 262, 0.8, 0.8, t)
            case_glass(sub, cx, sfloor, 0.9)
            bobby(ImageDraw.Draw(sub), cx - 270, sfloor + 40, 1.1, 1)
            rubber(sub, "FERIA DE SELLOS", cx, 90, w("sellos", dur * 0.7) - y0 * 0, t, (200, 50, 50), 50, 4)
            im.paste(sub.crop((0, 0, PW, int(PH - max(0, y0)))), (0, int(max(0, y0))))
        im = cam(im, cx, PH * 0.45, 1.06 + 0.04 * t / max(dur, 0.1))
        return finish(im, t, 0.55)

    if kind == "x_ca_vacia":
        d = bg(im, (30, 22, 30), (10, 8, 14))
        sfloor = PH * 0.66
        d.rectangle([0, sfloor, PW, PH], fill=(22, 16, 20))
        tv = w("desaparece", dur * 0.6)
        flick = 1.0 if t < tv - 0.1 else (0.25 if int(t * 18) % 3 == 0 else 1.0) * (0.6 if t > tv + 0.25 else 1)
        im = spotlight(im, cx, 0, cx, sfloor, 230, flick)
        d = ImageDraw.Draw(im)
        case(d, cx, sfloor, 0.9)
        if t < tv:
            trophy(im, cx, sfloor - 262, 0.8, 0.6, t)
        else:  # silueta de polvo donde estaba
            k = _c((t - tv) / 0.35)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            trophy(lay, cx, sfloor - 262, 0.8)
            a = np.asarray(lay).copy()
            a[..., 3] = (a[..., 3] * (1 - k) * 0.9).astype(np.uint8)
            rng = np.random.default_rng(3)
            m = rng.random(a.shape[:2]) < k
            a[m, 3] = 0
            im.paste(Image.fromarray(a), (0, 0), Image.fromarray(a))
            d = ImageDraw.Draw(im)
            rng2 = random.Random(1)
            for _ in range(40):
                px = cx + rng2.uniform(-60, 60) + (t - tv) * rng2.uniform(-80, 80)
                py = sfloor - 262 - rng2.uniform(0, 300) - (t - tv) * rng2.uniform(20, 120)
                r = 3 * (1 - k * 0.6)
                d.ellipse([px - r, py - r, px + r, py + r], fill=(200, 170, 90))
            if t > tv + 0.2:
                label(d, cx, PH * 0.30, "?", 210, YEL, 10)
        case_glass(im, cx, sfloor, 0.9)
        d = ImageDraw.Draw(im)
        typed(d, cx, PH * 0.25, "DOMINGO, 20 DE MARZO", t, 0.05, 30, 40, WARM, True)
        z = 1.0 + 0.25 * _e(_c((t - tv + 0.1) / 0.4))
        im = cam(im, cx, sfloor - 400, 1.04 + z - 1)
        return finish(im, t, 0.6)

    if kind == "x_ca_nota":
        # escritorio visto desde arriba con lámpara
        d = bg(im, (54, 34, 22), (30, 18, 12))
        for i in range(0, PH, 46):
            d.line([(0, i), (PW, i + 20)], fill=(48, 30, 20), width=3)
        im = glow(im, lambda dd: dd.ellipse([cx - 380, PH * 0.22, cx + 380, PH * 0.72], fill=(140, 110, 60)), 70)
        d = ImageDraw.Draw(im)
        op = _e(_c((t - 0.2) / 0.5))
        # caja abierta
        bx, by = cx - 160, PH * 0.42
        d.rectangle([bx - 140, by - 110, bx + 140, by + 110], fill=(150, 110, 70), outline=INK, width=5)
        d.rectangle([bx - 120, by - 90, bx + 120, by + 90], fill=(90, 64, 40))
        d.polygon([(bx - 140, by - 110), (bx + 140, by - 110), (bx + 140 - 60 * op, by - 110 - 140 * op), (bx - 140 + 60 * op, by - 110 - 140 * op)],
                  fill=(170, 128, 84), outline=INK)
        # trozo de la copa (forro dorado)
        pk = _e(_c((t - w("trozo", 0.6)) / 0.4))
        px, py = bx, by - 80 * pk
        im = glow(im, lambda dd: dd.ellipse([px - 90, py - 50, px + 90, py + 50], fill=(int(150 * pk), int(110 * pk), int(30 * pk))), 30)
        d = ImageDraw.Draw(im)
        d.polygon([(px - 70, py - 24), (px + 70, py - 24), (px + 52, py + 30), (px - 52, py + 30)], fill=GOLD, outline=INK, width=4)
        d.polygon([(px - 70, py - 24), (px + 70, py - 24), (px + 62, py - 34), (px - 62, py - 34)], fill=GOLD_L, outline=INK)
        # nota de rescate
        nk = _e(_c((t - w("nota", dur * 0.55) + 0.2) / 0.35))
        nx, ny = cx + 170 - 40 * (1 - nk), PH * 0.56 + 300 * (1 - nk)
        note = Image.new("RGBA", (330, 360), (0, 0, 0, 0))
        nd = ImageDraw.Draw(note)
        nd.rectangle([0, 0, 329, 359], fill=(236, 232, 218), outline=INK, width=4)
        fm = font(30, MONO)
        for i in range(7):  # líneas a máquina (ilegibles) y la cifra
            if i == 3:
                nd.text((30, 22 + i * 44), "£ ? ? ?", font=font(64, MONO), fill=(180, 20, 30))
                continue
            nd.line([(24, 44 + i * 44), (24 + 260 * (0.5 + 0.5 * ((i * 37) % 10) / 10), 44 + i * 44)], fill=(70, 70, 70), width=5)
        note = note.rotate(-7 + 5 * (1 - nk), expand=True, resample=Image.BICUBIC)
        im.paste(note, (int(nx - note.width / 2), int(ny - note.height / 2)), note)
        d = ImageDraw.Draw(im)
        label(d, cx, PH * 0.255, "RESCATE", 64, YEL, 9)
        im = cam(im, cx + 60 * nk, PH * 0.46, 1.05 + 0.12 * nk)
        return finish(im, t, 0.55)

    if kind == "x_ca_pista":
        # tablón de investigación con hilo rojo y linterna
        d = bg(im, (20, 24, 40), (8, 10, 18))
        bx0, by0, bx1, by1 = 50, PH * 0.17, PW - 50, PH * 0.64
        d.rectangle([bx0, by0, bx1, by1], fill=(150, 108, 66), outline=(70, 46, 26), width=14)
        rng = random.Random(2)
        for _ in range(500):
            x, y = rng.uniform(bx0 + 10, bx1 - 10), rng.uniform(by0 + 10, by1 - 10)
            d.point((x, y), fill=(120, 84, 50))
        cards = [(cx - 180, by0 + 150, "LADRÓN", -6), (cx + 170, by0 + 130, "¿COPA?", 5), (cx - 150, by1 - 190, "MAPA", 4),
                 (cx + 170, by1 - 170, "RESCATE", -4)]
        pins = []
        for x, y, txt, r in cards:
            c = Image.new("RGBA", (230, 250), (0, 0, 0, 0))
            cd = ImageDraw.Draw(c)
            cd.rectangle([0, 0, 229, 249], fill=(236, 232, 220), outline=INK, width=3)
            cd.rectangle([16, 16, 213, 190], fill=(40, 44, 56))
            if txt == "LADRÓN":
                cd.ellipse([80, 40, 150, 110], fill=(10, 12, 20))
                cd.rectangle([60, 110, 170, 190], fill=(10, 12, 20))
                cd.text((90, 52), "?", font=font(54), fill=WHITE)
            elif txt == "¿COPA?":
                trophy(c, 115, 186, 0.48)
            elif txt == "MAPA":
                for k in range(8):
                    cd.line([(16, 30 + k * 22), (213, 40 + k * 18)], fill=(80, 90, 110), width=3)
                cd.line([(60, 16), (120, 190)], fill=(80, 90, 110), width=6)
                cd.ellipse([120, 90, 140, 110], fill=RED)
            else:
                cd.text((70, 70), "£ ?", font=font(52, MONO), fill=(220, 60, 60))
            cd.text((115 - cd.textlength(txt, font=font(28)) / 2, 202), txt, font=font(28), fill=INK)
            c = c.rotate(r, expand=True, resample=Image.BICUBIC)
            im.paste(c, (int(x - c.width / 2), int(y - c.height / 2)), c)
            pins.append((x, y - 110))
        d = ImageDraw.Draw(im)
        for a, b in ((0, 1), (1, 3), (3, 2), (2, 0), (0, 3)):
            d.line([pins[a], pins[b]], fill=(200, 30, 40), width=5)
        for p in pins:
            d.ellipse([p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11], fill=(230, 40, 50), outline=INK, width=2)
        # detenido: tarjeta del rescate con «DETENIDO»
        tp = w("pilla", dur * 0.25)
        rubber(im, "DETENIDO", cx + 170, by1 - 190, tp + 0.1, t, (40, 160, 90), 44, -10)
        # linterna que barre el tablón
        lx = cx + 260 * math.sin(t * 1.6)
        ly = PH * 0.40 + 120 * math.sin(t * 1.1 + 1)
        dark = Image.new("L", im.size, 0)
        ImageDraw.Draw(dark).ellipse([lx - 260, ly - 260, lx + 260, ly + 260], fill=255)
        dark = dark.filter(ImageFilter.GaussianBlur(50))
        im = Image.composite(im, Image.blend(im, Image.new("RGB", im.size), 0.55), dark)
        tr = w("rastro", dur * 0.8)
        rubber(im, "NI RASTRO", cx, PH * 0.42, tr - 0.15, t, RED, 92, -9)
        bobby(ImageDraw.Draw(im), 110, PH * 0.80, 1.35, 1, sil=True, arm=0.6)
        im = cam(im, cx, PH * 0.42, 1.04 + 0.08 * _c(t / max(dur, 0.1)), 1.2 * math.sin(t * 0.7))
        return finish(im, t, 0.6)

    if kind == "x_ca_paseo":
        d = bg(im, (30, 40, 74), (12, 16, 32))
        horizon = PH * 0.47
        scroll = t * 90
        # casas adosadas (parallax lento)
        for layer, (sp, col, base, lit) in enumerate(((0.3, (18, 24, 46), horizon - 40, 0.15),
                                                      (0.7, (26, 22, 34), horizon + 20, 0.3))):
            off = -(scroll * sp) % 220
            for k in range(-1, 6):
                hx = k * 220 + off - 60
                d.rectangle([hx, base - 300, hx + 210, base], fill=col)
                d.polygon([(hx - 10, base - 300), (hx + 220, base - 300), (hx + 105, base - 380)], fill=col)
                d.rectangle([hx + 150, base - 380, hx + 175, base - 330], fill=col)
                rng = random.Random(k * 7 + layer + int((scroll * sp) // 220))
                for wy in (base - 250, base - 150):
                    for wx in (hx + 30, hx + 120):
                        if rng.random() < lit + 0.3:
                            d.rectangle([wx, wy, wx + 50, wy + 60], fill=(250, 210, 120) if rng.random() < 0.7 else (60, 60, 80))
        d.rectangle([0, horizon + 20, PW, PH], fill=(26, 26, 34))
        d.rectangle([0, horizon + 20, PW, horizon + 36], fill=(60, 60, 70))
        # farolas con su cono
        off = -(scroll * 1.0) % 420
        for k in range(-1, 3):
            lx = k * 420 + off + 120
            im = spotlight(im, lx, horizon - 330, lx, horizon + 120, 170, 0.8)
            d = ImageDraw.Draw(im)
            d.line([(lx, horizon + 110), (lx, horizon - 330)], fill=(8, 8, 14), width=12)
            d.rectangle([lx - 22, horizon - 360, lx + 22, horizon - 320], fill=(255, 230, 160))
        hedge(d, -40 - (scroll * 1.0) % 300, PW + 300, horizon + 70, 90, 3)
        gy = horizon + 300
        mxp = cx - 280
        man(d, mxp, gy, 1.7, 1, phase=t * 8, run=0.7, arm=-0.6)
        lead = (mxp + 1.7 * (30 + 20 * math.cos(-0.6)), gy + 1.7 * (-120 + 40 * math.sin(0.6)))
        dxp = cx + 10
        dog(d, dxp, gy + 10, 1.3, 1, "walk", phase=t * 10, wag=t * 12, tongue=True)
        d.line([lead, ((lead[0] + dxp + 40) / 2, gy - 60), (dxp + 1.3 * 50, gy - 1.3 * 84)], fill=(160, 40, 40), width=5)
        calendar(im, cx, PH * 0.30, t, 0.15)
        im = cam(im, cx, PH * 0.45, 1.03)
        return finish(im, t, 0.55)

    if kind == "x_ca_seto":
        d = bg(im, (22, 30, 54), (8, 10, 20))
        gy = PH * 0.56
        d.rectangle([0, gy, PW, PH], fill=(28, 30, 30))
        im = spotlight(im, PW - 150, 0, cx + 40, gy, 300, 0.9)
        d = ImageDraw.Draw(im)
        hedge(d, -60, PW + 60, gy - 20, 330, 8, (24, 70, 42))
        tstop = 0.35
        walk = 1 - _c(t / tstop)
        sniff = _c((t - w("seto", 0.9)) / 0.3)
        pk_t = w("paquete", dur * 0.55)
        pkg = _e(_c((t - pk_t + 0.15) / 0.4))
        # paquete bajo el seto, se ve más cuando aparta las hojas
        px, py = cx + 170, gy + 30
        newspaper(d, px - 150, py - 140, px + 150, py + 10)
        d.line([(px - 150, py - 65), (px + 150, py - 65)], fill=(120, 100, 70), width=7)
        d.line([(px, py - 140), (px, py + 10)], fill=(120, 100, 70), width=7)
        rng = random.Random(4)
        for _ in range(16):  # hojas delante que se apartan
            lx = px + rng.uniform(-140, 140)
            ly = py - rng.uniform(0, 120)
            lx += (lx - px) * 1.6 * pkg + math.copysign(60, lx - px) * pkg
            r = rng.uniform(26, 40)
            d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(22, 64, 38))
        nose_tw = 3 * math.sin(t * 40) * sniff
        dog(d, cx - 150 - 120 * walk, gy + 40, 1.5, 1, "sniff" if sniff > 0 else "walk", phase=t * 10 * walk + 2,
            wag=t * (4 + 12 * sniff), head=(nose_tw - 30 * (1 - sniff), 50 * (1 - sniff)))
        if sniff > 0:
            for k in range(3):  # líneas de olfateo
                p = (t * 2 + k / 3) % 1
                ox = cx + 40 + 30 * p
                d.arc([ox - 20, gy - 40 - 40 * p - 20, ox + 20, gy - 40 - 40 * p + 20], 300, 60,
                      fill=(int(220 * (1 - p)),) * 3, width=4)
        rubber(im, "¿QUÉ HAY AHÍ?", cx, PH * 0.29, w("paquete", dur * 0.6), t, (200, 150, 40), 58, 4)
        z = 1.05 + 0.35 * _e(_c((t - 0.6) / max(dur - 0.6, 0.1)))
        im = cam(im, cx + 80 * _c((t - 0.6) / max(dur, 0.1)), gy - 80, z)
        return finish(im, t, 0.68)

    if kind == "x_ca_abre":
        # primer plano: manos que abren el periódico, solo una rendija de luz dorada
        d = bg(im, (10, 12, 22), (4, 5, 10))
        k = _e(_c(t / max(dur, 0.1)))
        cy = PH * 0.45
        crack = 6 + 70 * k
        im = glow(im, lambda dd: dd.rectangle([cx - crack, cy - 220, cx + crack, cy + 220], fill=(255, 190, 70)), 30)
        d = ImageDraw.Draw(im)
        for sg in (-1, 1):
            x0 = cx + sg * crack
            x1 = x0 + sg * 420
            newspaper(d, min(x0, x1), cy - 260, max(x0, x1), cy + 260)
            # manos que sujetan el borde: dedos detrás, pulgar delante
            hx = x0 + sg * 34
            d.rectangle([hx + sg * 40 - 60, cy + 150, hx + sg * 40 + 60, cy + 520], fill=COAT, outline=INK, width=5)
            d.rounded_rectangle([hx - 52, cy + 40, hx + 52, cy + 170], 40, fill=SKIN, outline=INK, width=5)
            for k in range(3):  # nudillos sobre el borde del papel
                d.line([(hx - 36 + k * 30, cy + 70), (hx - 30 + k * 30, cy + 110)], fill=(190, 140, 110), width=4)
        im = cam(im, cx, cy, 1.0 + 0.12 * k)
        return finish(im, t, 0.75)

    if kind == "x_ca_revela":
        d = bg(im, (60, 40, 14), (14, 10, 4))
        cy = PH * 0.46
        rays = Image.new("RGB", im.size, (0, 0, 0))
        rd = ImageDraw.Draw(rays)
        for i in range(18):
            a = i / 18 * 2 * math.pi + t * 0.35
            rd.polygon([(cx, cy), (cx + 1600 * math.cos(a), cy + 1600 * math.sin(a)),
                        (cx + 1600 * math.cos(a + 0.12), cy + 1600 * math.sin(a + 0.12))], fill=(70, 50, 14))
        im = add(im, rays.filter(ImageFilter.GaussianBlur(6)))
        rise = _e(_c(t / 0.6))
        by = cy + 270 + 120 * (1 - rise)
        s = 1.5 + 0.05 * math.sin(t * 2)
        im = trophy_glow(im, cx, by, s, 1.0)
        trophy(im, cx, by, s, 1.0, t * 1.4)
        d = ImageDraw.Draw(im)
        rng = random.Random(7)
        for _ in range(36):  # destellos
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(120, 420) * (0.5 + 0.5 * _c(t / 0.8))
            x, y = cx + r * math.cos(a), cy + r * math.sin(a) * 1.2
            tw = 0.5 + 0.5 * math.sin(t * 10 + a * 5)
            L = 8 + 14 * tw
            col = (255, 240, 190)
            d.line([(x - L, y), (x + L, y)], fill=col, width=3)
            d.line([(x, y - L), (x, y + L)], fill=col, width=3)
        # papel roto que sale despedido
        for k in range(8):
            a = k / 8 * 2 * math.pi + 0.3
            r = 120 + 900 * _e(_c(t / 0.7))
            x, y = cx + r * math.cos(a), cy + 80 + r * math.sin(a)
            pts = [(x + 40 * math.cos(a + j), y + 30 * math.sin(a + j * 1.3)) for j in (0, 2, 4)]
            d.polygon(pts, fill=(226, 220, 200), outline=INK)
        rubber(im, "¡ENCONTRADA!", cx, PH * 0.28, 0.35, t, (60, 200, 110), 74, -6)
        im = cam(im, cx, cy, 1.12 - 0.08 * _c(t / max(dur, 0.1)))
        return finish(im, t, 0.45)

    if kind == "x_ca_interroga":
        d = bg(im, (26, 26, 30), (8, 8, 12))
        cy = PH * 0.40
        sw = 0.35 * math.sin(t * 2.4)
        lx, ly = cx + 420 * math.sin(sw), cy - 240 + 40 * (1 - math.cos(sw))
        # sombra del bobby en la pared
        shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        bobby(ImageDraw.Draw(shadow), cx + 230 - 160 * math.sin(sw), PH * 0.62, 1.9, -1, sil=True, arm=0.3)
        sa = np.asarray(shadow).copy()
        sa[..., 3] = (sa[..., 3] * 0.6).astype(np.uint8)
        shadow = Image.fromarray(sa).filter(ImageFilter.GaussianBlur(4))
        im.paste(shadow, (0, 0), shadow)
        d = ImageDraw.Draw(im)
        d.line([(cx, 0), (lx, ly)], fill=(20, 20, 24), width=5)
        im = spotlight(im, lx, ly, cx + 0.4 * (lx - cx), PH * 0.60, 280, 1.4)
        d = ImageDraw.Draw(im)
        d.polygon([(lx - 50, ly + 40), (lx + 50, ly + 40), (lx + 22, ly), (lx - 22, ly)], fill=(40, 44, 40))
        d.ellipse([lx - 16, ly + 30, lx + 16, ly + 52], fill=(255, 240, 200))
        man(d, cx - 30, PH * 0.63, 2.1, 1, face="worried", sweat=1.0, t=t, seated=True, arm=0.2)
        d.rectangle([cx - 330, PH * 0.56, cx + 330, PH * 0.60], fill=(70, 50, 36), outline=INK, width=4)
        d.rectangle([cx - 300, PH * 0.60, cx - 280, PH * 0.70], fill=(50, 36, 26))
        d.rectangle([cx + 280, PH * 0.60, cx + 300, PH * 0.70], fill=(50, 36, 26))
        rubber(im, "SOSPECHOSO", cx, PH * 0.27, w("sospechoso", dur * 0.7), t, RED, 70, -7)
        im = cam(im, cx - 30, PH * 0.42, 1.08 + 0.12 * _c(t / max(dur, 0.1)))
        return finish(im, t, 0.7)

    if kind == "x_ca_medalla":
        d = bg(im, (40, 34, 60), (12, 10, 20))
        floor_y = PH * 0.62
        d.rectangle([0, floor_y, PW, PH], fill=(60, 20, 30))
        im = spotlight(im, cx, 0, cx, floor_y, 260, 1.1)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([cx - 140, floor_y - 70, cx + 140, floor_y + 10], 10, fill=(200, 170, 80), outline=INK, width=5)
        d.text((cx - d.textlength("HÉROE", font=font(40)) / 2, floor_y - 58), "HÉROE", font=font(40), fill=INK)
        mk = _e(_c((t - w("medalla", dur * 0.6) + 0.2) / 0.35))
        dog(d, cx, floor_y - 66, 1.7, 1, "sit", wag=t * 16, happy=True, tongue=True, medal=mk > 0.5,
            head=(0, -10 * mk))
        if mk < 1 and mk > 0:  # la medalla baja hasta el cuello
            mx, my = cx + 40, floor_y - 480 + 280 * mk
            d.ellipse([mx - 22, my - 22, mx + 22, my + 22], fill=(210, 214, 222), outline=INK, width=3)
        for side, (px, ph) in enumerate(((90, 0.0), (PW - 90, 0.33), (160, 0.66))):
            press(d, px, PH * 0.80 - (side == 2) * -10, 1.15, 1 if px < cx else -1)
        fl = 0
        for k, (fx, fy, ft) in enumerate(((140, PH * 0.66, 0.25), (PW - 140, PH * 0.64, 0.6), (210, PH * 0.67, 1.0), (PW - 140, PH * 0.64, 1.35))):
            dt = t - ft
            if 0 <= dt < 0.25:
                fl = max(fl, 1 - dt / 0.25)
                im = flashbulb(im, fx + 60, fy - 90, 1 - dt / 0.25)
        if fl > 0:
            im = Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), 0.15 * fl)
        im = cam(im, cx, floor_y - 200, 1.10 + 0.06 * math.sin(t))
        return finish(im, t, 0.5)

    if kind == "x_ca_cena":
        tn = w("inglaterra", dur * 0.3) - 0.15
        tc = w("cena", dur * 0.75) - 0.25
        if t < tn:  # retrato con el nombre
            d = bg(im, (60, 30, 30), (20, 10, 14))
            for i in range(14):
                a = i / 14 * 2 * math.pi + t * 0.4
                d.polygon([(cx, PH * 0.45), (cx + 1500 * math.cos(a), PH * 0.45 + 1500 * math.sin(a)),
                           (cx + 1500 * math.cos(a + 0.11), PH * 0.45 + 1500 * math.sin(a + 0.11))], fill=(80, 40, 40))
            dog(d, cx - 40, PH * 0.66, 2.1, 1, "sit", wag=t * 14, tongue=True, bowtie=False)
            d.rounded_rectangle([cx - 250, PH * 0.66 - 10, cx + 250, PH * 0.66 + 110], 16, fill=(236, 230, 214), outline=INK, width=6)
            typed(d, cx, PH * 0.66 + 14, "PICKLES", t, 0.0, 16, 84, INK, True)
            im = cam(im, cx, PH * 0.48, 1.04 + 0.05 * t)
            return finish(im, t, 0.5)
        if t < tc:  # Inglaterra campeona
            lt = t - tn
            d = bg(im, (20, 40, 90), (8, 14, 36))
            rng = random.Random(3)
            for _ in range(90):  # confeti
                x = rng.uniform(0, PW)
                y = (rng.uniform(-PH, 0) + lt * rng.uniform(300, 600)) % PH
                c = rng.choice([(220, 40, 50), WHITE, (40, 80, 200)])
                d.rectangle([x, y, x + 10, y + 16], fill=c)
            im = trophy_glow(im, cx, PH * 0.66, 1.0, 0.8)
            trophy(im, cx, PH * 0.66, 1.0, 1.0, t)
            d = ImageDraw.Draw(im)
            rubber(im, "INGLATERRA", cx, PH * 0.28, 0.0, lt, (230, 40, 50), 70, -5, "CAMPEONA DEL MUNDO · 1966")
            im = cam(im, cx, PH * 0.44, 1.0 + 0.1 * _e(_c(lt / 0.8)))
            return finish(im, t, 0.5)
        # la cena de campeones
        lt = t - tc
        d = bg(im, (60, 40, 30), (24, 14, 10))
        d.rectangle([0, 0, PW, PH * 0.40], fill=(70, 46, 34))
        for x in range(60, PW, 180):  # lámparas
            im = glow(im, lambda dd, x=x: dd.ellipse([x - 40, PH * 0.12 - 40, x + 40, PH * 0.12 + 40], fill=(140, 110, 50)), 30)
        d = ImageDraw.Draw(im)
        rng = random.Random(6)
        for k in range(5):  # jugadores al fondo levantando copas
            x = 80 + k * 175
            y = PH * 0.50
            arm = 0.5 + 0.4 * math.sin(lt * 6 + k)
            d.rounded_rectangle([x - 42, y - 120, x + 42, y + 40], 16, fill=(200, 36, 46), outline=INK, width=4)
            d.ellipse([x - 32, y - 190, x + 32, y - 126], fill=rng.choice([(236, 192, 152), (220, 170, 130)]), outline=INK, width=4)
            d.chord([x - 32, y - 194, x + 32, y - 150], 180, 360, fill=(60, 40, 24))
            hx, hy = x + 50, y - 120 - 80 * arm
            d.line([(x + 34, y - 100), (hx, hy)], fill=(200, 36, 46), width=16)
            d.polygon([(hx - 12, hy - 34), (hx + 12, hy - 34), (hx + 4, hy), (hx - 4, hy)], fill=(230, 220, 160), outline=INK)
            d.arc([x - 14, y - 162, x + 14, y - 140], 20, 160, fill=INK, width=4)
        ty = PH * 0.56
        d.polygon([(-40, ty), (PW + 40, ty), (PW + 200, PH * 0.66), (-200, PH * 0.66)], fill=(240, 236, 226), outline=INK)
        d.rectangle([-200, PH * 0.66, PW + 200, PH * 0.70], fill=(210, 204, 190))
        for x in (120, 300, 560, 740):  # velas
            fl = 0.85 + 0.15 * math.sin(lt * 20 + x)
            d.rectangle([x - 8, ty - 70, x + 8, ty + 6], fill=(240, 236, 220), outline=INK, width=2)
            im = glow(im, lambda dd, x=x, fl=fl: dd.ellipse([x - 30, ty - 120, x + 30, ty - 60], fill=(int(200 * fl), int(150 * fl), 50)), 14)
            d = ImageDraw.Draw(im)
            d.ellipse([x - 7, ty - 100 - 4 * fl, x + 7, ty - 72], fill=(255, 220, 120))
        # Pickles en su silla con pajarita
        lick = math.sin(lt * 14) > 0.2 and lt > 0.6
        d.rectangle([cx - 90, PH * 0.42, cx + 90, PH * 0.58], fill=(110, 60, 40), outline=INK, width=4)
        dog(d, cx - 20, PH * 0.61, 1.55, 1, "sit", wag=lt * 16, tongue=lick, bowtie=True, happy=not lick)
        d.ellipse([cx - 90, ty + 6, cx + 130, ty + 50], fill=WHITE, outline=INK, width=3)
        d.ellipse([cx - 60, ty + 12, cx + 100, ty + 44], fill=(200, 120, 70))
        rubber(im, "CENA DE CAMPEONES", cx, PH * 0.29, 0.05, lt, (240, 200, 80), 52, -4)
        im = cam(im, cx, PH * 0.48, 1.05 + 0.1 * _c(lt / 1.5))
        return finish(im, t, 0.5)

    if kind == "x_ca_rio":
        d = bg(im, (40, 26, 60), (8, 6, 18))
        hor = PH * 0.58
        tr = w("roban", dur * 0.25)
        tn = w("nunca", dur * 0.7)
        # Pan de Azúcar y Corcovado con el Cristo
        d.polygon([(PW - 360, hor), (PW - 300, hor - 260), (PW - 240, hor - 330), (PW - 170, hor - 300), (PW - 120, hor - 120), (PW - 60, hor)],
                  fill=(10, 8, 22))
        d.polygon([(-60, hor), (60, hor - 380), (150, hor - 470), (250, hor - 380), (380, hor)], fill=(12, 10, 26))
        cxr, cyr = 150, hor - 470
        d.rectangle([cxr - 6, cyr - 70, cxr + 6, cyr], fill=(12, 10, 26))
        d.rectangle([cxr - 46, cyr - 60, cxr + 46, cyr - 50], fill=(12, 10, 26))
        d.ellipse([cxr - 10, cyr - 92, cxr + 10, cyr - 70], fill=(12, 10, 26))
        im = glow(im, lambda dd: dd.ellipse([cxr - 70, cyr - 120, cxr + 70, cyr + 10], fill=(70, 70, 110)), 30)
        d = ImageDraw.Draw(im)
        skyline(d, PW, hor + 40, 11, (14, 12, 26), 60, 200, 0.35, t)
        d.rectangle([0, hor + 40, PW, PH], fill=(10, 12, 30))
        for k in range(40):  # reflejos en el agua
            x = (k * 53) % PW
            y = hor + 60 + (k * 37) % 300
            ln = 20 + 20 * math.sin(t * 3 + k)
            d.line([(x, y), (x + ln, y)], fill=(160, 120, 60), width=3)
        typed(d, cx, PH * 0.24, "RÍO DE JANEIRO · 1983", t, 0.05, 30, 42, WARM, True)
        if t > tr:  # alarma
            a = 0.5 + 0.5 * math.sin((t - tr) * 10)
            im = add(im, Image.new("RGB", im.size, (int(110 * a), 0, int(16 * a))))
            d = ImageDraw.Draw(im)
            # vitrina vacía con la silueta de la copa
            case(d, cx + 190, PH * 0.72, 0.75)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            trophy(lay, cx + 190, PH * 0.72 - 218, 0.62)
            a2 = np.asarray(lay)
            edge = a2[..., 3] > 0
            e2 = edge & ~np.roll(edge, 3, 0) | edge & ~np.roll(edge, 3, 1)
            yy, xx = np.nonzero(e2)
            dash = ((xx + yy) // 10) % 2 == 0
            arr = np.asarray(im).copy()
            arr[yy[dash], xx[dash]] = (255, 214, 10)
            im = Image.fromarray(arr)
            case_glass(im, cx + 190, PH * 0.72, 0.75)
        rubber(im, "CASO ABIERTO", cx - 20, PH * 0.40, tn - 0.05, t, RED, 62, -6, "NUNCA APARECIÓ")
        im = cam(im, cx, PH * 0.46, 1.02 + 0.08 * _c(t / max(dur, 0.1)))
        return finish(im, t, 0.6)

    d = bg(im)
    label(d, cx, PH / 2, kind, 40)
    return im
