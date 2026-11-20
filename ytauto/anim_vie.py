"""Animaciones pro del 20-nov.

x_nv_ (¿por qué 90 minutos?), x_mz_ (Maracanazo 1950), x_cs_ (¿y si el campo tuviera cuesta?).
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from . import anim as A
from .anim_extra import person, font
from .anim_robot import ball, SKINS
from .anim_serie import _glow, text_c, stamp
from .anim_pro import grad, pitch_persp, vignette

WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN = (255, 214, 10), (40, 230, 255)
GREEN, RED = (60, 200, 110), (220, 45, 55)
BRA_Y, BRA_G = (250, 215, 40), (20, 150, 70)
URU = (110, 180, 240)


def _e(x):
    return A._ease(max(0.0, min(1.0, x)))


def clock(d, x, y, r, ang, face=(250, 250, 245)):
    d.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8], fill=INK)
    d.ellipse([x - r, y - r, x + r, y + r], fill=face)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        d.line([(x + r * 0.82 * math.sin(a), y - r * 0.82 * math.cos(a)), (x + r * 0.95 * math.sin(a), y - r * 0.95 * math.cos(a))], fill=INK, width=5)
    d.line([(x, y), (x + r * 0.75 * math.sin(ang), y - r * 0.75 * math.cos(ang))], fill=RED, width=8)
    d.line([(x, y), (x + r * 0.5 * math.sin(ang / 12), y - r * 0.5 * math.cos(ang / 12))], fill=INK, width=10)
    d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=INK)


def crest(d, x, y, w, col, txt, sub=""):
    h = w * 1.2
    d.polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h * 0.1), (x, y + h / 2), (x - w / 2, y + h * 0.1)],
              fill=col, outline=WHITE)
    d.line([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h * 0.1), (x, y + h / 2), (x - w / 2, y + h * 0.1), (x - w / 2, y - h / 2)], fill=WHITE, width=6)
    f = font(w * 0.22)
    tw = d.textlength(txt, font=f)
    d.text((x - tw / 2, y - w * 0.2), txt, font=f, fill=WHITE, stroke_width=4, stroke_fill=INK)
    if sub:
        text_c(d, x, y + h / 2 + 14, sub, 34, YEL, 5)


def crowd(d, x0, y0, x1, y1, t, cols, seed=1, n=900, grey=0.0, jump=1.0):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        c = rnd.choice(cols)
        if grey:
            g = int(sum(c) / 3 * 0.6)
            c = tuple(int(c[j] * (1 - grey) + g * grey) for j in range(3))
        hop = abs(math.sin(t * 6 + x * 0.05)) * 5 * jump
        d.ellipse([x - 5, y - 5 - hop, x + 5, y + 5 - hop], fill=c)


def shirt(d, x, y, s, body, sleeve=None, collar=None, num=""):
    sleeve = sleeve or body
    w, h = 160 * s, 190 * s
    d.polygon([(x - w * 0.5, y - h * 0.4), (x - w * 0.9, y - h * 0.1), (x - w * 0.75, y + h * 0.08), (x - w * 0.45, y - h * 0.12)], fill=sleeve, outline=INK)
    d.polygon([(x + w * 0.5, y - h * 0.4), (x + w * 0.9, y - h * 0.1), (x + w * 0.75, y + h * 0.08), (x + w * 0.45, y - h * 0.12)], fill=sleeve, outline=INK)
    d.rounded_rectangle([x - w * 0.5, y - h * 0.45, x + w * 0.5, y + h * 0.55], 18 * s, fill=body, outline=INK, width=6)
    d.ellipse([x - w * 0.16, y - h * 0.52, x + w * 0.16, y - h * 0.32], fill=collar or body, outline=INK, width=5)
    if num:
        f = font(80 * s)
        d.text((x - d.textlength(num, font=f) / 2, y - h * 0.1), num, font=f, fill=collar or INK)


def tilted_pitch(im, ang, t, home=(220, 45, 55), away=(30, 90, 210)):
    """Campo visto de lado con cuesta (ang en grados). Devuelve (base_y, f(x)->y suelo)."""
    PW, PH = im.size
    d = grad(im, (90, 160, 230), (190, 225, 250))
    # montañas
    d.polygon([(0, PH * 0.42), (PW * 0.3, PH * 0.30), (PW * 0.6, PH * 0.40), (PW, PH * 0.28), (PW, PH), (0, PH)], fill=(120, 170, 120))
    m = math.tan(math.radians(ang))
    yc = PH * 0.55

    def gy(x):
        return yc + (x - PW / 2) * m
    pts = [(-10, gy(-10)), (PW + 10, gy(PW + 10)), (PW + 10, PH), (-10, PH)]
    d.polygon(pts, fill=(44, 140, 70))
    for i in range(10):
        x0 = i * PW / 10
        x1 = x0 + PW / 20
        d.polygon([(x0, gy(x0)), (x1, gy(x1)), (x1, gy(x1) + 400), (x0, gy(x0) + 400)], fill=(52, 156, 80))
    d.line([(-10, gy(-10)), (PW + 10, gy(PW + 10))], fill=WHITE, width=6)
    # porterías
    for gx, col in ((50, home), (PW - 50, away)):
        b = gy(gx)
        d.rectangle([gx - 6, b - 150, gx + 6, b], fill=WHITE)
        d.line([(gx, b - 150), (gx + (60 if gx < PW / 2 else -60), b - 150)], fill=WHITE, width=8)
    return d, gy


def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    # ===================================================== 035 ¿por qué 90 minutos?
    if kind == "x_nv_sin_reloj":
        # atardecer: el sol cae y nadie sabe cuándo acabar
        k = min(1.0, t / max(dur, 0.1))
        top = tuple(int(a * (1 - k) + b * k) for a, b in zip((80, 150, 230), (40, 20, 70)))
        bot = tuple(int(a * (1 - k) + b * k) for a, b in zip((250, 200, 140), (230, 90, 60)))
        d = grad(im, top, bot)
        sy = PH * 0.30 + PH * 0.22 * k
        im = _glow(im, lambda g: g.ellipse([cx - 120, sy - 120, cx + 120, sy + 120], fill=(255, 160, 60)), 40)
        d = ImageDraw.Draw(im)
        d.ellipse([cx - 80, sy - 80, cx + 80, sy + 80], fill=(255, 200, 90))
        d.rectangle([0, PH * 0.52, PW, PH], fill=(40, 110, 60))
        for i, xx in enumerate((0.2, 0.42, 0.62, 0.82)):
            person(d, PW * xx, PH * 0.66, 1.5, (200, 40, 50) if i % 2 else (240, 240, 240), SKINS[i % 4], "corto",
                   (40, 28, 20), mouth="abierta", phase=t * (8 - 6 * k), run=1 - 0.8 * k)
        ball(d, PW * 0.52 + 120 * math.sin(t * 2), PH * 0.66, 22)
        clock(d, PW * 0.82, PH * 0.34, 70, t * 9)
        text_c(d, cx, PH * 0.27, "¿CUÁNDO SE ACABA?", 54, WHITE, 7)
        if t > dur * 0.55:
            stamp(im, "SIN REGLA DE TIEMPO", cx, PH * 0.40, dur * 0.55, t, bg=RED, fg=WHITE, size=46)
        return vignette(im, 0.35)
    if kind == "x_nv_1866":
        d = grad(im, (20, 24, 50), (40, 30, 70))
        k = _e(t / 0.6)
        crest(d, cx - 260 * k - 20, PH * 0.42, 210, (30, 60, 150), "LONDRES")
        crest(d, cx + 260 * k + 20, PH * 0.42, 210, (180, 30, 40), "SHEFFIELD")
        text_c(d, cx, PH * 0.27, "1866", 80, YEL, 8)
        if t > 0.9:
            k2 = _e((t - 0.9) / 0.5)
            r = 90 * k2
            im = _glow(im, lambda g: g.ellipse([cx - r - 20, PH * 0.42 - r - 20, cx + r + 20, PH * 0.42 + r + 20], fill=(120, 100, 20)), 30)
            d = ImageDraw.Draw(im)
            if k2 > 0.2:
                clock(d, cx, PH * 0.42, r, min(1, (t - 0.9) / 1.2) * math.pi * 3)
        if t > 2.2:
            stamp(im, "PACTAN: 90 MINUTOS", cx, PH * 0.58, 2.2, t, bg=YEL, fg=INK, size=52)
        return vignette(im, 0.4)
    if kind == "x_nv_1897":
        d = grad(im, (30, 22, 16), (60, 40, 26))
        d.rectangle([0, PH * 0.56, PW, PH], fill=(90, 58, 34))
        k = _e(t / 0.9)
        bx0, by0, bw, bh = cx, PH * 0.32, 330, 440
        # libro abriéndose
        d.rounded_rectangle([cx - bw - 14, by0 - 10, cx + bw + 14, by0 + bh + 16], 16, fill=(110, 30, 30))
        d.rectangle([cx - bw * k, by0, cx, by0 + bh], fill=(245, 236, 210), outline=(150, 130, 100), width=3)
        d.rectangle([cx, by0, cx + bw, by0 + bh], fill=(250, 242, 220), outline=(150, 130, 100), width=3)
        d.line([(cx, by0), (cx, by0 + bh)], fill=(150, 130, 100), width=6)
        f = font(30)
        for i in range(9):
            d.line([(cx + 30, by0 + 60 + i * 38), (cx + bw - 30 - (i % 3) * 30, by0 + 60 + i * 38)], fill=(170, 160, 140), width=6)
        if k > 0.6:
            for i in range(9):
                d.line([(cx - bw * k + 30, by0 + 60 + i * 38), (cx - 30 - (i % 2) * 40, by0 + 60 + i * 38)], fill=(170, 160, 140), width=6)
        d.text((cx + 40, by0 + 14), "REGLAS · 1897", font=f, fill=(110, 30, 30))
        if t > 1.1:
            kk = _e((t - 1.1) / 0.4)
            d.rounded_rectangle([cx + 20, by0 + 190, cx + 20 + (bw - 40) * kk, by0 + 270], 10, fill=YEL)
            if kk >= 1:
                d.text((cx + 40, by0 + 205), "90 MINUTOS", font=font(40), fill=INK)
        text_c(d, cx, PH * 0.26, "QUEDA POR ESCRITO", 52, YEL, 7)
        return vignette(im, 0.4)
    if kind == "x_nv_descanso":
        d = pitch_persp(im, t, 0.30)
        first = t < dur * 0.5
        # viento: flechas que cruzan
        for i in range(6):
            x = (t * 260 + i * 170) % (PW + 200) - 100
            y = PH * 0.36 + (i % 3) * 50
            d.line([(x - 70, y), (x, y)], fill=(230, 240, 255), width=6)
            d.polygon([(x, y - 12), (x + 22, y), (x, y + 12)], fill=(230, 240, 255))
        side = 1 if first else -1
        kk = _e((t - dur * 0.5) / 0.6) if not first else 0
        for i in range(3):
            xr = cx + side * (180 + i * 70) * (1 if first else 1) if first else cx + (180 + i * 70) * (1 - 2 * kk)
            xb = cx - (180 + i * 70) if first else cx - (180 + i * 70) * (1 - 2 * kk)
            person(d, xr, PH * 0.64, 1.3, (200, 40, 50), SKINS[i % 4], "corto", (40, 28, 20), run=1 if not first else 0, phase=t * 10)
            person(d, xb, PH * 0.64, 1.3, (240, 240, 240), SKINS[(i + 1) % 4], "corto", (40, 28, 20), run=1 if not first else 0, phase=t * 10)
        text_c(d, cx, PH * 0.27, "1.ª PARTE" if first else "DESCANSO: CAMBIO DE CAMPO", 50 if first else 42, YEL, 6)
        if not first:
            stamp(im, "MISMO VIENTO Y SOL PARA LOS DOS", cx, PH * 0.47, dur * 0.5 + 0.6, t, bg=GREEN, fg=WHITE, size=36)
        return vignette(im)
    # ===================================================== 036 Maracanazo
    if kind == "x_mz_estadio":
        d = grad(im, (10, 20, 50), (30, 40, 80))
        k = _e(t / 1.0)
        # cuenco del estadio
        d.ellipse([-PW * 0.3, PH * 0.30, PW * 1.3, PH * 0.80], fill=(60, 60, 80))
        crowd(d, -PW * 0.1, PH * 0.32, PW * 1.1, PH * 0.47, t, [BRA_Y, BRA_G, WHITE, (40, 80, 200)], n=int(1400 * k) + 1)
        d.ellipse([PW * 0.05, PH * 0.45, PW * 0.95, PH * 0.66], fill=(44, 140, 70), outline=WHITE, width=5)
        d.line([(cx, PH * 0.45), (cx, PH * 0.66)], fill=WHITE, width=4)
        d.ellipse([cx - 50, PH * 0.535, cx + 50, PH * 0.575], outline=WHITE, width=4)
        text_c(d, cx, PH * 0.26, "MARACANÁ · 1950", 60, YEL, 7)
        return vignette(im, 0.4)
    if kind == "x_mz_empate":
        d = grad(im, (12, 40, 26), (8, 20, 14))
        d.rounded_rectangle([70, PH * 0.33, PW - 70, PH * 0.58], 24, fill=(14, 16, 26), outline=YEL, width=6)
        text_c(d, cx, PH * 0.35, "ÚLTIMO PARTIDO", 40, CYAN, 5)
        text_c(d, cx - 190, PH * 0.41, "BRASIL", 56, BRA_Y, 6)
        text_c(d, cx + 190, PH * 0.41, "URUGUAY", 56, URU, 6)
        text_c(d, cx, PH * 0.41, "vs", 44, WHITE, 5)
        if t > 0.8:
            text_c(d, cx, PH * 0.49, "A BRASIL LE VALE EL EMPATE", 40, WHITE, 5)
        if t > 1.6:
            stamp(im, "YA LO DAN POR GANADO", cx, PH * 0.60, 1.6, t, bg=BRA_Y, fg=INK, size=44)
        return vignette(im, 0.35)
    if kind == "x_mz_goles":
        d = pitch_persp(im, t, 0.30)
        d.rounded_rectangle([60, PH * 0.33, PW - 60, PH * 0.45], 22, fill=(14, 16, 26), outline=WHITE, width=5)
        evs = [(0.0, 0, 0, ""), (0.22, 1, 0, "47'"), (0.52, 1, 1, "66'"), (0.80, 1, 2, "79'")]
        a = b = 0
        last = ""
        idx = 0
        for i, (u, x, y, m) in enumerate(evs):
            if t >= u * dur:
                a, b, last, idx = x, y, m, i
        text_c(d, cx - 210, PH * 0.355, "BRA", 52, BRA_Y, 6)
        text_c(d, cx + 210, PH * 0.355, "URU", 52, URU, 6)
        text_c(d, cx, PH * 0.345, f"{a} - {b}", 80, WHITE, 8)
        # línea de tiempo
        y = PH * 0.52
        d.line([(80, y), (PW - 80, y)], fill=WHITE, width=6)
        for i, (u, x, yy, m) in enumerate(evs[1:], 1):
            px = 80 + (PW - 160) * int(m[:-1]) / 90
            col = BRA_Y if i == 1 else URU
            if t >= u * dur:
                d.ellipse([px - 20, y - 20, px + 20, y + 20], fill=col, outline=INK, width=4)
                text_c(d, px, y + 26, m, 34, WHITE, 4)
            else:
                d.ellipse([px - 10, y - 10, px + 10, y + 10], fill=(90, 90, 90))
        u0 = evs[idx][0] * dur
        if idx > 0 and t - u0 < 1.0:
            im = _glow(im, lambda g: g.rectangle([60, PH * 0.33, PW - 60, PH * 0.45], fill=(100, 90, 30)), 30)
            stamp(im, "¡GOL!", cx, PH * 0.60, u0, t, bg=(BRA_Y if idx == 1 else URU), fg=INK, size=60)
        return vignette(im)
    if kind == "x_mz_silencio":
        d = grad(im, (10, 20, 50), (30, 40, 80))
        g = _e((t - 0.3) / 1.4)
        d.ellipse([-PW * 0.3, PH * 0.30, PW * 1.3, PH * 0.80], fill=(60, 60, 80))
        crowd(d, -PW * 0.1, PH * 0.32, PW * 1.1, PH * 0.47, t, [BRA_Y, BRA_G, WHITE, (40, 80, 200)], n=1400, grey=g, jump=1 - g)
        d.ellipse([PW * 0.05, PH * 0.45, PW * 0.95, PH * 0.66], fill=(44, 140, 70), outline=WHITE, width=5)
        # medidor de ruido que cae
        lvl = 1 - g
        for i in range(10):
            on = i < int(lvl * 10 + 0.5)
            col = (60, 200, 110) if i < 6 else (255, 180, 40) if i < 8 else RED
            d.rectangle([cx - 250 + i * 50, PH * 0.56, cx - 214 + i * 50, PH * 0.60], fill=col if on else (50, 50, 60))
        text_c(d, cx, PH * 0.26, "MÁS DE 170.000 EN SILENCIO" if g > 0.5 else "MARACANÁ", 44 if g > 0.5 else 60, WHITE, 7)
        return vignette(im, 0.45)
    if kind == "x_mz_camiseta":
        d = grad(im, (12, 30, 24), (8, 16, 14))
        k = _e((t - dur * 0.4) / 0.7)
        if k < 0.5:
            shirt(d, cx, PH * 0.47, 1.5 * (1 - k * 0.4), (245, 245, 245), collar=(30, 80, 160))
            text_c(d, cx, PH * 0.27, "BLANCA HASTA 1950", 50, WHITE, 6)
            if t > dur * 0.2:
                d.line([(cx - 160, PH * 0.36), (cx + 160, PH * 0.58)], fill=RED, width=16)
        else:
            im = _glow(im, lambda g: g.ellipse([cx - 220, PH * 0.32, cx + 220, PH * 0.62], fill=(90, 80, 10)), 40)
            d = ImageDraw.Draw(im)
            shirt(d, cx, PH * 0.47, 1.5 * (0.8 + 0.2 * k), BRA_Y, sleeve=BRA_G, collar=BRA_G)
            text_c(d, cx, PH * 0.27, "NUEVA CAMISETA: AMARILLA", 46, BRA_Y, 6)
        return vignette(im, 0.4)
    # ===================================================== 037 campo en cuesta
    if kind.startswith("x_cs_"):
        ang = 13
        if kind == "x_cs_campo":
            ang = 13 * _e(t / 0.8)
            d, gy = tilted_pitch(im, ang, t)
            u = max(0, t - 0.9)
            bx = cx + 0.5 * 140 * u * u if u > 0 else cx
            bx = min(bx, PW - 70)
            by = gy(bx) - 26
            d.ellipse([bx - 26, by - 26, bx + 26, by + 26], fill=WHITE, outline=INK, width=4)
            d.line([(bx, by), (bx + 22 * math.cos(u * 8), by + 22 * math.sin(u * 8))], fill=INK, width=4)
            text_c(d, cx, PH * 0.27, "UN CAMPO CON CUESTA", 54, WHITE, 7)
            if bx >= PW - 70:
                stamp(im, "SE VA SOLO A LA PORTERÍA", cx, PH * 0.40, 0, t - 2.0, bg=YEL, fg=INK, size=44)
            return im
        d, gy = tilted_pitch(im, ang, t)
        if kind == "x_cs_ataque":
            # rojos bajan a toda velocidad, azules suben agotados
            for i in range(3):
                x = (PW * 0.25 + i * 60 + t * 140) % (PW * 0.8)
                person(d, x, gy(x), 1.4, (220, 45, 55), SKINS[i % 4], "corto", (40, 28, 20), phase=t * 14, run=1.2, mouth="sonrisa")
            for i in range(2):
                x = PW * 0.75 - i * 90 - t * 20
                person(d, x, gy(x), 1.4, (30, 90, 210), SKINS[(i + 2) % 4], "corto", (40, 28, 20), phase=t * 4, run=0.5, mouth="abierta")
                for j in range(3):
                    yy = gy(x) - 240 + ((t * 120 + j * 30) % 60)
                    d.ellipse([x + 40 + j * 10, yy - 60, x + 52 + j * 10, yy + 16], fill=CYAN)
            text_c(d, cx, PH * 0.27, "CUESTA ABAJO: VELOCIDAD x2", 42, YEL, 6)
            text_c(d, cx, PH * 0.33, "CUESTA ARRIBA: SUFRIMIENTO", 40, WHITE, 6)
            return im
        if kind == "x_cs_porteros":
            # portero de arriba (izquierda) aburrido, el de abajo (derecha) recibiendo balones
            xl = 120
            person(d, xl, gy(xl), 1.4, (40, 220, 120), SKINS[0], "corto", (40, 28, 20), "1", pose="brazos_cruzados")
            for i in range(3):
                d.text((xl + 50 + i * 30, gy(xl) - 380 - i * 30 - (t * 30 % 20)), "z", font=font(40 + i * 10), fill=WHITE, stroke_width=4, stroke_fill=INK)
            xr = PW - 150
            person(d, xr, gy(xr), 1.4, (255, 140, 40), SKINS[1], "corto", (40, 28, 20), "1", arm_up=1.0, mouth="abierta")
            for i in range(5):
                u = (t * 0.9 + i * 0.2) % 1.0
                bx = PW * 0.3 + (xr - 60 - PW * 0.3) * u
                ball(d, bx, gy(bx) - 22 - 60 * math.sin(math.pi * u), 20)
            text_c(d, cx, PH * 0.27, "UN PORTERO DUERME", 46, WHITE, 6)
            text_c(d, cx, PH * 0.33, "EL OTRO NO PARA", 46, YEL, 6)
            return im
        if kind == "x_cs_descanso":
            k = _e((t - 0.6) / 1.0)
            ang2 = 13 * (1 - 2 * k)
            d, gy = tilted_pitch(im, ang2, t)
            text_c(d, cx, PH * 0.27, "DESCANSO: SE CAMBIA DE CAMPO", 40, WHITE, 6)
            if t > 1.8:
                stamp(im, "AHORA OS TOCA SUBIR", cx, PH * 0.62, 1.8, t, bg=RED, fg=WHITE, size=50)
            for i in range(3):
                x = PW * 0.25 + i * 190
                person(d, x, gy(x), 1.4, (220, 45, 55), SKINS[i % 4], "corto", (40, 28, 20), mouth="abierta" if k > 0.5 else "sonrisa")
            return im
        if kind == "x_cs_saque":
            x0 = cx
            person(d, cx - 70, gy(cx - 70), 1.5, (30, 90, 210), SKINS[2], "tupe", (40, 28, 20), "9", mouth="abierta" if t > 1.0 else "sonrisa")
            u = max(0, t - 0.4)
            bx = max(80, x0 - 0.5 * 160 * u * u)
            by = gy(bx) - 24
            d.ellipse([bx - 24, by - 24, bx + 24, by + 24], fill=WHITE, outline=INK, width=4)
            text_c(d, cx, PH * 0.27, "SAQUE DE CENTRO… CUESTA ARRIBA", 38, WHITE, 6)
            if bx <= 80:
                im = _glow(im, lambda g: g.rectangle([30, gy(50) - 160, 140, gy(50)], fill=(120, 40, 40)), 30)
                stamp(im, "¡AUTOGOL!", cx, PH * 0.62, 0, t - 2.4, bg=RED, fg=WHITE, size=64)
            return im
    return im
