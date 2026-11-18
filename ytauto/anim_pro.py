"""Animaciones «pro» a pantalla completa para los vídeos de datos de YouTube.

Prefijos: x_gk_ (color del portero), x_sd_ (Mundial bajo techo), x_tj_ (tarjetas).
Lienzo PW x PH (virtual 860 de ancho). Zona útil 0.28-0.66 PH.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

from . import anim as A
from .anim_extra import person, stamp, font, BLAU, RED
from .anim_robot import ball, SKINS
from .anim_serie import _glow, text_c

WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN = (255, 214, 10), (40, 230, 255)
GREEN = (60, 200, 110)


def _e(x):
    return A._ease(x)


def grad(im, top, bot):
    d = ImageDraw.Draw(im)
    PW, PH = im.size
    for i in range(48):
        k = i / 47
        c = tuple(int(top[j] * (1 - k) + bot[j] * k) for j in range(3))
        d.rectangle([0, PH * i / 48, PW, PH * (i + 1) / 48 + 1], fill=c)
    return d


def pitch_persp(im, t, horizon=0.30):
    """Césped en perspectiva con franjas y líneas (look de retransmisión)."""
    PW, PH = im.size
    d = grad(im, (8, 14, 30), (16, 30, 54))
    hy = PH * horizon
    # gradas y focos
    d.rectangle([0, hy - 120, PW, hy], fill=(24, 30, 48))
    rnd = random.Random(4)
    for _ in range(260):
        x, y = rnd.uniform(0, PW), rnd.uniform(hy - 115, hy - 5)
        d.point((x, y), fill=rnd.choice([(200, 60, 60), (60, 90, 200), (220, 220, 220), (90, 90, 110)]))
    for fx in (PW * 0.12, PW * 0.88):
        im2 = _glow(im, lambda g: g.ellipse([fx - 40, hy - 200, fx + 40, hy - 160], fill=(255, 250, 220)), 30)
        im.paste(im2)
        d = ImageDraw.Draw(im)
        d.rectangle([fx - 30, hy - 190, fx + 30, hy - 170], fill=(255, 255, 240))
    # franjas en perspectiva
    n = 9
    for i in range(n):
        y0 = hy + (PH - hy) * ((i / n) ** 1.6)
        y1 = hy + (PH - hy) * (((i + 1) / n) ** 1.6)
        d.rectangle([0, y0, PW, y1], fill=(36, 128, 64) if i % 2 else (44, 144, 74))
    d.line([(PW * 0.5 - 40, hy), (-PW * 0.6, PH)], fill=(230, 240, 230), width=5)
    d.line([(PW * 0.5 + 40, hy), (PW * 1.6, PH)], fill=(230, 240, 230), width=5)
    return d


def vignette(im, k=0.55):
    PW, PH = im.size
    m = Image.new("L", (PW // 8, PH // 8), 0)
    md = ImageDraw.Draw(m)
    md.ellipse([-PW // 16, -PH // 20, PW // 8 + PW // 16, PH // 8 + PH // 20], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(14)).resize((PW, PH), Image.BILINEAR)
    dark = Image.new("RGB", (PW, PH), (0, 0, 0))
    return Image.composite(im, Image.blend(im, dark, k), m)


def card(d, cx, cy, w, h, col, rot=0.0, im=None):
    """Tarjeta de árbitro con brillo; si se pasa im se dibuja rotada."""
    lay = Image.new("RGBA", (int(w * 1.6), int(h * 1.6)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ox, oy = w * 0.3, h * 0.3
    ld.rounded_rectangle([ox + 8, oy + 10, ox + w + 8, oy + h + 10], 14, fill=(0, 0, 0, 110))
    ld.rounded_rectangle([ox, oy, ox + w, oy + h], 14, fill=col + (255,), outline=(255, 255, 255, 255), width=4)
    ld.polygon([(ox + 10, oy + 10), (ox + w * 0.5, oy + 10), (ox + 10, oy + h * 0.45)], fill=(255, 255, 255, 70))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    im.paste(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)), lay)


def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    # ------------------------------------------------ 024 color del portero
    if kind == "x_gk_kits":
        d = pitch_persp(im, t)
        xs = [0.14, 0.32, 0.5, 0.68, 0.86]
        for i, xx in enumerate(xs):
            k = _e((t - 0.1 * i) / 0.4)
            y = PH * 0.62 + 30 * (1 - k)
            gk = i == 2
            col = (40, 220, 120) if gk else (30, 90, 210)
            if gk and t > 1.0:
                im = _glow(im, lambda g: g.ellipse([PW * xx - 110, y - 420, PW * xx + 110, y + 10], fill=(40, 160, 90)), 30)
                d = ImageDraw.Draw(im)
            person(d, PW * xx, y, 1.45, col, SKINS[i % 4], "corto", (30, 20, 10), "1" if gk else str(i + 3),
                   pose="brazos_cruzados" if gk else "")
        if t > 1.0:
            A._label(d, PW * 0.5, PH * 0.29, "Solo uno va de otro color", 42, YEL, center=True)
        return vignette(im)
    if kind == "x_gk_mano":
        d = pitch_persp(im, t, 0.28)
        # área grande en perspectiva
        d.polygon([(PW * 0.18, PH * 0.40), (PW * 0.82, PH * 0.40), (PW * 0.95, PH * 0.64), (PW * 0.05, PH * 0.64)],
                  outline=WHITE, width=5)
        half = t < dur / 2
        x = PW * (0.38 if half else 0.62)
        col = (40, 220, 120) if half else (30, 90, 210)
        person(d, x, PH * 0.62, 1.6, col, SKINS[1], "corto", (30, 20, 10), "1" if half else "4", arm_up=1.0, mouth="abierta")
        ball(d, x + 60, PH * 0.62 - 400 + 20 * math.sin(t * 6), 26)
        loc = t if half else t - dur / 2
        if loc > 0.5:
            if half:
                stamp(im, "PORTERO: VÁLIDO", cx, PH * 0.32, 0.5, loc, bg=GREEN, fg=WHITE, size=54)
            else:
                stamp(im, "DEFENSA: ¡PENALTI!", cx, PH * 0.32, 0.5, loc, bg=RED, fg=WHITE, size=54)
        return vignette(im)
    if kind == "x_gk_1912":
        d = grad(im, (10, 18, 34), (14, 40, 30))
        x0, y0, x1, y1 = 90, PH * 0.30, PW - 90, PH * 0.64
        d.rectangle([x0, y0, x1, y1], fill=(40, 140, 72), outline=WHITE, width=5)
        my = (y0 + y1) / 2
        d.line([(x0, my), (x1, my)], fill=WHITE, width=4)
        d.ellipse([cx - 70, my - 70, cx + 70, my + 70], outline=WHITE, width=4)
        d.rectangle([cx - 200, y1 - 150, cx + 200, y1], outline=WHITE, width=4)
        k = _e((t - 1.4) / 0.9)
        zy0 = my + (y1 - 150 - my) * k
        zx0 = x0 + (cx - 200 - x0) * k
        zx1 = x1 - (x1 - cx - 200) * k
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rectangle([zx0, zy0, zx1, y1], fill=(255, 214, 10, 110))
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im)
        text_c(d, cx, PH * 0.27, "ANTES DE 1912" if t < 1.4 else "DESDE 1912", 56, YEL, 6)
        A._label(d, cx, (zy0 + y1) / 2 - 20, "Zona de manos", 40, WHITE, center=True)
        return vignette(im, 0.45)
    # ------------------------------------------------ 026 Mundial bajo techo
    if kind == "x_sd_domo":
        d = grad(im, (20, 40, 90), (120, 160, 220))
        gy = PH * 0.62
        d.rectangle([0, gy, PW, PH], fill=(40, 110, 60))
        # estadio
        d.rectangle([60, gy - 160, PW - 60, gy], fill=(150, 156, 170), outline=INK, width=4)
        for i in range(12):
            d.rectangle([80 + i * 60, gy - 130, 110 + i * 60, gy - 100], fill=(90, 100, 120))
        k = _e((t - 0.3) / 1.4)
        # cúpula que se cierra desde los lados
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.pieslice([60, gy - 160 - 260, PW - 60, gy - 160 + 260], 180, 180 + 180 * k, fill=(235, 238, 245, 255), outline=(150, 156, 170, 255), width=6)
        for i in range(1, 6):
            a = math.radians(180 + 30 * i)
            if 30 * i <= 180 * k:
                ld.line([(cx, gy - 160), (cx + (PW / 2 - 60) * math.cos(a), gy - 160 + 260 * math.sin(a))], fill=(200, 205, 215, 255), width=3)
        im.paste(lay, (0, 0), lay)
        d = ImageDraw.Draw(im)
        if t > 1.6:
            text_c(d, cx, PH * 0.28, "PONTIAC SILVERDOME", 58, WHITE, 8)
            A._label(d, cx, PH * 0.66 - 70, "Detroit · 1994", 40, YEL, center=True)
        return vignette(im, 0.35)
    if kind == "x_sd_hierba":
        d = grad(im, (14, 16, 26), (30, 30, 40))
        # techo que tapa el sol
        sx, sy = cx, PH * 0.30
        im = _glow(im, lambda g: g.ellipse([sx - 60, sy - 60, sx + 60, sy + 60], fill=(255, 210, 80)), 25)
        d = ImageDraw.Draw(im)
        d.ellipse([sx - 50, sy - 50, sx + 50, sy + 50], fill=(255, 220, 90))
        d.rectangle([0, PH * 0.36, PW, PH * 0.40], fill=(200, 205, 215))
        k = _e((t - 0.4) / 1.6)
        gy = PH * 0.64
        for i in range(36):
            x = 40 + i * (PW - 80) / 35
            h = 140 - 70 * k * (0.6 + 0.4 * math.sin(i))
            lean = 40 * k * (1 if i % 2 else -1)
            col = (int(60 + 120 * k), int(170 - 40 * k), int(70 - 30 * k))
            d.line([(x, gy), (x + lean, gy - h)], fill=col, width=9)
        d.rectangle([0, gy, PW, PH], fill=(70, 50, 34))
        if t > 1.2:
            stamp(im, "SIN SOL NO CRECE", cx, PH * 0.48, 1.2, t, bg=(230, 90, 40), fg=WHITE, size=54)
        return vignette(im, 0.4)
    if kind == "x_sd_hex":
        d = grad(im, (12, 20, 36), (20, 34, 58))
        r = 70
        cols, rows = 6, 5
        x0, y0 = cx - (cols - 1) * r * 1.5 / 2, PH * 0.36
        n = 0
        for j in range(rows):
            for i in range(cols):
                hx = x0 + i * r * 1.5
                hy = y0 + j * r * 1.73 + (r * 0.86 if i % 2 else 0)
                q = _e((t - n * 0.05) / 0.35)
                n += 1
                if q <= 0:
                    continue
                oy = (1 - q) * -PH * 0.5
                d.regular_polygon((hx, hy + oy, r * 0.96), 6, rotation=0, fill=(50, 160, 80) if (i + j) % 2 else (60, 176, 90), outline=(20, 70, 40))
        if t > 1.6:
            text_c(d, cx, PH * 0.27, "Un puzle de césped", 54, YEL, 6)
        return vignette(im, 0.4)
    # ------------------------------------------------ 030 tarjetas
    if kind == "x_tj_semaforo":
        d = grad(im, (16, 18, 30), (36, 30, 40))
        # calle
        d.rectangle([0, PH * 0.6, PW, PH], fill=(40, 40, 46))
        for i in range(6):
            d.rectangle([i * 160 + ((t * 200) % 160), PH * 0.66, i * 160 + 80 + ((t * 200) % 160), PH * 0.675], fill=(230, 230, 230))
        sx, sy = PW * 0.30, PH * 0.30
        d.rectangle([sx - 10, sy + 300, sx + 10, PH * 0.62], fill=(60, 64, 70))
        d.rounded_rectangle([sx - 70, sy, sx + 70, sy + 300], 30, fill=(24, 26, 30), outline=(80, 84, 90), width=4)
        phase = 0 if t < 0.8 else (1 if t < 1.8 else 2)
        cols = [(60, 220, 90), (255, 190, 20), (240, 50, 40)]
        for i in range(3):
            on = (2 - i) == phase
            y = sy + 50 + i * 100
            c = cols[2 - i] if on else (50, 50, 54)
            if on:
                im = _glow(im, lambda g: g.ellipse([sx - 60, y - 60, sx + 60, y + 60], fill=c), 28)
                d = ImageDraw.Draw(im)
            d.ellipse([sx - 38, y - 38, sx + 38, y + 38], fill=c)
        if phase >= 1:
            card(d, PW * 0.68, PH * 0.42, 130, 190, (255, 200, 20), -8 + 4 * math.sin(t * 3), im)
        if phase == 2:
            card(d, PW * 0.80, PH * 0.46, 130, 190, (230, 40, 40), 10 + 4 * math.sin(t * 3), im)
        return vignette(im, 0.45)
    if kind == "x_tj_idiomas":
        d = pitch_persp(im, t)
        person(d, cx - 170, PH * 0.64, 1.5, RED, SKINS[2], "corto", (20, 10, 5), "8", mouth="abierta")
        person(d, cx + 150, PH * 0.64, 1.5, (20, 20, 24), SKINS[0], "corto", (60, 40, 20), "", arm_up=1.0 if t > 1.2 else 0.0)
        langs = ["Was?", "Quoi?", "What?", "¿Qué?"]
        for i, w in enumerate(langs):
            if t > 0.2 + i * 0.25 and t < 1.2:
                A._label(d, cx - 160 + (i - 1.5) * 90, PH * 0.32 + (i % 2) * 60, w, 38, WHITE, center=True)
        if t > 1.2:
            card(d, cx + 230, PH * 0.38 - 30 * _e((t - 1.2) / 0.3), 110, 160, (255, 200, 20), -6, im)
            A._label(d, cx, PH * 0.29, "Lo entiende todo el mundo", 40, YEL, center=True)
        return vignette(im)
    if kind == "x_tj_1974":
        d = grad(im, (40, 6, 10), (12, 4, 8))
        for i in range(18):
            a = i / 18 * 2 * math.pi + t * 0.3
            d.polygon([(cx, PH * 0.47), (cx + 1500 * math.cos(a), PH * 0.47 + 1500 * math.sin(a)),
                       (cx + 1500 * math.cos(a + 0.1), PH * 0.47 + 1500 * math.sin(a + 0.1))], fill=(70, 10, 16))
        k = _e(t / 0.5)
        n = int(1900 + 74 * _e(t / 0.9))
        text_c(d, cx, PH * 0.27, str(n), 150, WHITE, 10)
        card(d, cx, PH * 0.52 + 200 * (1 - k), 200, 290, (230, 40, 40), -6 + 3 * math.sin(t * 2), im)
        return vignette(im, 0.35)
    return None
