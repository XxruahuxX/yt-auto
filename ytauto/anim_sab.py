"""Animaciones pro del 21-nov (formato corto).

x_ym_ (penalti a 11 metros = 12 yardas), x_pi_ (la Copa robada en 1966 y el perro que la encontró),
x_pm_ (¿y si las porterías se movieran?).
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
GOLD, GOLD2 = (240, 190, 50), (200, 140, 20)


def _e(x):
    return A._ease(max(0.0, min(1.0, x)))


def cup(d, x, y, s):
    """Copa dorada genérica. (x, y) = base."""
    d.rounded_rectangle([x - 70 * s, y - 40 * s, x + 70 * s, y], 8 * s, fill=(60, 40, 20), outline=INK, width=4)
    d.polygon([(x - 30 * s, y - 40 * s), (x + 30 * s, y - 40 * s), (x + 14 * s, y - 120 * s), (x - 14 * s, y - 120 * s)], fill=GOLD2, outline=INK)
    d.pieslice([x - 85 * s, y - 300 * s, x + 85 * s, y - 90 * s], 0, 180, fill=GOLD, outline=INK, width=4)
    d.rectangle([x - 85 * s, y - 200 * s, x + 85 * s, y - 195 * s], fill=GOLD2)
    for sg in (-1, 1):
        d.arc([x + sg * 70 * s - 40 * s, y - 260 * s, x + sg * 70 * s + 40 * s, y - 170 * s], 270 if sg > 0 else 90,
              90 if sg > 0 else 270, fill=GOLD2, width=int(12 * s))
    d.ellipse([x - 40 * s, y - 185 * s, x - 10 * s, y - 150 * s], fill=(255, 240, 170))


def dog(d, x, y, s, t, sniff=False, wag=True):
    """Perro de dibujo original. (x, y) = patas."""
    col, dark = (200, 140, 80), (120, 80, 40)
    by = y - 70 * s + (math.sin(t * 10) * 3 * s if sniff else 0)
    for i, lx in enumerate((-60, -35, 35, 60)):
        ph = math.sin(t * 12 + i) * 6 * s if sniff else 0
        d.rounded_rectangle([x + lx * s - 9 * s, by + 10 * s, x + lx * s + 9 * s, y + ph * 0], 6 * s, fill=col, outline=INK, width=3)
    d.rounded_rectangle([x - 80 * s, by - 35 * s, x + 80 * s, by + 25 * s], 30 * s, fill=col, outline=INK, width=4)
    a = math.sin(t * 14) * 0.6 if wag else 0
    tx, ty = x - 80 * s, by - 20 * s
    d.line([(tx, ty), (tx - 45 * s * math.cos(a), ty - 45 * s * abs(math.sin(a + 1)))], fill=col, width=int(12 * s))
    hx, hy = x + 95 * s, by - 50 * s + (12 * s if sniff else 0)
    d.ellipse([hx - 42 * s, hy - 38 * s, hx + 42 * s, hy + 38 * s], fill=col, outline=INK, width=4)
    d.ellipse([hx + 20 * s, hy - 4 * s, hx + 62 * s, hy + 26 * s], fill=(230, 180, 120), outline=INK, width=3)
    d.ellipse([hx + 50 * s, hy + 2 * s, hx + 64 * s, hy + 14 * s], fill=INK)
    d.ellipse([hx + 4 * s, hy - 16 * s, hx + 16 * s, hy - 4 * s], fill=INK)
    d.polygon([(hx - 34 * s, hy - 20 * s), (hx - 10 * s, hy - 30 * s), (hx - 30 * s, hy + 30 * s)], fill=dark, outline=INK)
    d.rectangle([x + 40 * s, by - 32 * s, x + 56 * s, by + 10 * s], fill=RED)


def goal_front(d, cx, gb, w, h):
    gx0, gx1, gt = cx - w / 2, cx + w / 2, gb - h
    d.rectangle([gx0, gt, gx1, gb], fill=(30, 110, 60))
    for i in range(0, int(w), 30):
        d.line([(gx0 + i, gt), (gx0 + i, gb)], fill=(200, 220, 210), width=1)
    for j in range(0, int(h), 30):
        d.line([(gx0, gt + j), (gx1, gt + j)], fill=(200, 220, 210), width=1)
    d.rectangle([gx0 - 10, gt - 10, gx1 + 10, gt + 4], fill=WHITE)
    d.rectangle([gx0 - 10, gt - 10, gx0 + 4, gb], fill=WHITE)
    d.rectangle([gx1 - 4, gt - 10, gx1 + 10, gb], fill=WHITE)


def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    # ===================================================== 038 penalti a 11 m
    if kind == "x_ym_regla":
        d = pitch_persp(im, t, 0.30)
        gb = PH * 0.42
        goal_front(d, cx, gb, 520, 150)
        k = _e((t - 0.3) / 1.0)
        spot = PH * 0.42 + (PH * 0.62 - PH * 0.42) * k
        # cinta métrica desde la línea al punto
        d.line([(cx, gb + 6), (cx, spot)], fill=YEL, width=14)
        for i in range(int(12 * k) + 1):
            yy = gb + 6 + (spot - gb - 6) * (i / 12 if k else 0)
            d.line([(cx - 20, yy), (cx + 20, yy)], fill=INK, width=4)
        d.ellipse([cx - 14, spot - 8, cx + 14, spot + 8], fill=WHITE)
        if k >= 1:
            ball(d, cx, spot - 4, 26)
            stamp(im, "12 YARDAS", cx + 200, (gb + spot) / 2, 1.3, t, bg=YEL, fg=INK, size=50, rot=8)
        text_c(d, cx, PH * 0.27, "¿POR QUÉ 11 METROS?", 54, WHITE, 7)
        return vignette(im)
    if kind == "x_ym_ingles":
        d = grad(im, (16, 22, 48), (30, 40, 80))
        # regla de yardas que se convierte en metros
        k = _e((t - 0.8) / 0.8)
        y0 = PH * 0.40
        L = 720
        x0 = cx - L / 2
        d.rounded_rectangle([x0 - 10, y0 - 40, x0 + L + 10, y0 + 70], 12, fill=(250, 220, 90) if k < 0.5 else (120, 220, 255), outline=INK, width=5)
        n = 12 if k < 0.5 else 11
        for i in range(n + 1):
            xx = x0 + L * i / (12 if k < 0.5 else 10.97)
            if xx <= x0 + L + 1:
                d.line([(xx, y0 - 40), (xx, y0 + 10)], fill=INK, width=4)
                if i % (3 if k < 0.5 else 1) == 0 or i == n:
                    f = font(26)
                    s = str(i)
                    d.text((xx - d.textlength(s, font=f) / 2, y0 + 16), s, font=f, fill=INK)
        text_c(d, cx, PH * 0.27, "REGLAS NACIDAS EN INGLATERRA", 44, YEL, 6)
        text_c(d, cx, PH * 0.50, "YARDAS" if k < 0.5 else "METROS", 64, WHITE, 7)
        if k >= 1:
            stamp(im, "12 YARDAS = 10,97 m", cx, PH * 0.59, 0.8 + 0.8, t, bg=GREEN, fg=WHITE, size=48)
        return vignette(im, 0.35)
    if kind == "x_ym_tiro":
        d = pitch_persp(im, t, 0.30)
        gb = PH * 0.48
        goal_front(d, cx, gb, 600, 190)
        kx = cx + 140 * math.sin(t * 2.5) * (1 if t < 1.2 else 0)
        dive = _e((t - 1.2) / 0.4)
        if dive < 0.2:
            person(d, kx, gb + 4, 1.1, (40, 40, 44), SKINS[0], "corto", (60, 40, 20), "1", arm_up=0.6)
        else:
            lay = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
            person(ImageDraw.Draw(lay), 250, 470, 1.1, (40, 40, 44), SKINS[0], "corto", (60, 40, 20), "1", arm_up=1.0, mouth="abierta")
            lay = lay.rotate(-70 * dive, resample=Image.BICUBIC)
            im.paste(lay, (int(kx + 180 * dive - 250), int(gb - 360)), lay)
            d = ImageDraw.Draw(im)
        u = _e((t - 1.1) / 0.35)
        bx = cx + (-220) * u
        by = PH * 0.64 + (gb - 120 - PH * 0.64) * u
        ball(d, bx, by, 30 - 10 * u)
        if u >= 1:
            im = _glow(im, lambda g: g.rectangle([cx - 300, gb - 190, cx + 300, gb], fill=(110, 100, 30)), 30)
            stamp(im, "¡GOL!", cx, PH * 0.60, 1.5, t, bg=YEL, fg=INK, size=64)
        text_c(d, cx, PH * 0.27, "A 11 METROS EXACTOS", 50, WHITE, 6)
        return vignette(im)
    # ===================================================== 039 la Copa y el perro
    if kind == "x_pi_vitrina":
        d = grad(im, (20, 16, 30), (40, 30, 50))
        d.rectangle([0, PH * 0.62, PW, PH], fill=(70, 40, 40))
        # vitrina
        d.rectangle([cx - 200, PH * 0.30, cx + 200, PH * 0.62], outline=(200, 220, 255), width=6)
        d.rectangle([cx - 220, PH * 0.60, cx + 220, PH * 0.64], fill=(90, 60, 50))
        gone = t > dur * 0.45
        if not gone:
            im = _glow(im, lambda g: g.ellipse([cx - 150, PH * 0.34, cx + 150, PH * 0.58], fill=(120, 90, 20)), 35)
            d = ImageDraw.Draw(im)
            cup(d, cx, PH * 0.60, 1.0)
        else:
            d.text((cx - 50, PH * 0.42), "?", font=font(140), fill=(255, 255, 255), stroke_width=8, stroke_fill=INK)
            stamp(im, "ROBADA", cx, PH * 0.47, dur * 0.45, t, bg=RED, fg=WHITE, size=72, rot=-8)
        text_c(d, cx, PH * 0.26, "LONDRES · MARZO DE 1966", 46, YEL, 6)
        return vignette(im, 0.45)
    if kind == "x_pi_perro":
        d = grad(im, (40, 60, 100), (120, 150, 190))
        # calle y seto
        d.rectangle([0, PH * 0.60, PW, PH], fill=(90, 90, 100))
        d.rectangle([0, PH * 0.44, PW, PH * 0.60], fill=(40, 110, 50))
        rnd = random.Random(3)
        for _ in range(120):
            x, y = rnd.uniform(0, PW), rnd.uniform(PH * 0.44, PH * 0.6)
            d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=rnd.choice([(30, 100, 45), (50, 130, 60), (40, 115, 50)]))
        # paquete de periódico
        px, py = PW * 0.70, PH * 0.60
        d.rounded_rectangle([px - 70, py - 90, px + 70, py], 14, fill=(225, 220, 205), outline=INK, width=4)
        for i in range(5):
            d.line([(px - 55, py - 75 + i * 14), (px + 55 - (i % 2) * 30, py - 75 + i * 14)], fill=(150, 150, 150), width=4)
        k = _e(t / 1.2)
        dog(d, PW * 0.18 + (px - 300 - PW * 0.18) * k, PH * 0.66, 1.7, t, sniff=k > 0.9)
        if t > 1.4:
            d.text((px - 30, py - 190), "!", font=font(110), fill=YEL, stroke_width=8, stroke_fill=INK)
        text_c(d, cx, PH * 0.27, "UN PERRO OLFATEA UN PAQUETE", 42, WHITE, 6)
        return vignette(im, 0.35)
    if kind == "x_pi_heroe":
        d = grad(im, (40, 10, 30), (14, 8, 30))
        for i in range(16):
            a = i / 16 * 2 * math.pi + t * 0.5
            d.polygon([(cx, PH * 0.46), (cx + 1200 * math.cos(a), PH * 0.46 + 1200 * math.sin(a)),
                       (cx + 1200 * math.cos(a + 0.12), PH * 0.46 + 1200 * math.sin(a + 0.12))], fill=(70, 20, 40))
        k = _e(t / 0.5)
        im = _glow(im, lambda g: g.ellipse([cx - 230, PH * 0.32, cx + 230, PH * 0.62], fill=(100, 80, 20)), 40)
        d = ImageDraw.Draw(im)
        cup(d, cx + 170, PH * 0.60, 1.2 * k + 0.01)
        dog(d, cx - 190, PH * 0.62, 1.6, t)
        text_c(d, cx, PH * 0.27, "SE LLAMABA PICKLES", 56, YEL, 7)
        if t > 1.0:
            stamp(im, "HÉROE NACIONAL", cx, PH * 0.66 - 30, 1.0, t, bg=YEL, fg=INK, size=48)
        return vignette(im, 0.4)
    # ===================================================== 040 porterías que se mueven
    if kind.startswith("x_pm_"):
        d = pitch_persp(im, t, 0.30)
        gb = PH * 0.50
        if kind == "x_pm_huye":
            gx = cx + 260 * math.sin(t * 2.2)
            goal_front(d, gx, gb, 380, 150)
            for sg in (-1, 1):
                fx = gx + sg * 150
                ph = math.sin(t * 18 + sg) * 10
                d.ellipse([fx - 26, gb - 6 + ph, fx + 26, gb + 16 + ph], fill=(240, 240, 240), outline=INK, width=3)
            person(d, cx, PH * 0.68, 1.4, (30, 90, 210), SKINS[1], "corto", (30, 20, 10), "9", mouth="abierta")
            ball(d, cx + 70, PH * 0.68, 26)
            text_c(d, cx, PH * 0.27, "LA PORTERÍA SE ESCAPA", 52, WHITE, 7)
            return im
        if kind == "x_pm_portero":
            gx = cx + 220 * math.sin(t * 2.6)
            goal_front(d, gx, gb, 380, 150)
            run = gx - 0  # el portero corre detrás de su portería
            kx = gx - 120 * math.copysign(1, math.cos(t * 2.6))
            person(d, kx, gb + 6, 1.15, (40, 220, 120), SKINS[0], "corto", (30, 20, 10), "1", phase=t * 14, run=1.2, mouth="abierta")
            for i in range(3):
                yy = gb - 260 + ((t * 120 + i * 30) % 60)
                d.ellipse([kx + 30 + i * 10, yy, kx + 42 + i * 10, yy + 16], fill=CYAN)
            text_c(d, cx, PH * 0.27, "EL PORTERO, A PERSEGUIRLA", 46, YEL, 6)
            return im
        if kind == "x_pm_gol":
            gx = cx - 200 + 120 * t
            goal_front(d, gx, gb, 380, 150)
            u = _e((t - 0.4) / 0.8)
            bx = cx + (gx - cx) * u
            by = PH * 0.68 + (gb - 70 - PH * 0.68) * u
            ball(d, bx, by, 28 - 8 * u)
            person(d, cx + 160, PH * 0.70, 1.4, (30, 90, 210), SKINS[2], "tupe", (30, 20, 10), "9", pose="siu" if u >= 1 else "")
            if u >= 1:
                stamp(im, "¡GOL! ¿O NO?", cx, PH * 0.38, 1.2, t, bg=YEL, fg=INK, size=56)
            text_c(d, cx, PH * 0.27, "LA PORTERÍA VA A POR EL BALÓN", 40, WHITE, 6)
            return im
        if kind == "x_pm_var":
            d = grad(im, (10, 14, 30), (20, 26, 50))
            d.rounded_rectangle([90, PH * 0.33, PW - 90, PH * 0.56], 20, fill=(20, 24, 40), outline=CYAN, width=6)
            text_c(d, cx, PH * 0.35, "VAR", 70, CYAN, 6)
            dots = "." * (int(t * 3) % 4)
            text_c(d, cx, PH * 0.45, "REVISANDO" + dots, 50, WHITE, 6)
            if t > dur * 0.5:
                stamp(im, "¿GOL DEL 9 O DE LA PORTERÍA?", cx, PH * 0.59, dur * 0.5, t, bg=YEL, fg=INK, size=36)
            return vignette(im, 0.35)
    return im
