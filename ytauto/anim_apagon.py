"""Storytime 045 «El Murciélago»: entrenaba los penaltis con los ojos vendados… hasta el apagón de la final.
Estilo cacahuete (anim_bean). Escenas x_ap_*."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, rain, locker_persp,
                        pitch_persp, goal_persp, camera, vignette, confetti, _e, shade)

AZUL = (40, 100, 210)
ROJO = (190, 44, 40)
YO = dict(body=AZUL, skin=BLANCO, hair="pelo", hcol=(40, 30, 26), num="7")
CAP = dict(body=AZUL, skin=BLANCO, hair="tupe", hcol=(26, 22, 30), num="10", chain=True)
COACH = dict(body=(70, 74, 86), skin=BLANCO, hair="gorra", legcol=(50, 50, 60))


def focos(c, W, H, on=1.0, t=0.0):
    """Dos torres de focos arriba a izquierda y derecha."""
    for x0, sg in ((W * 0.06, 1), (W * 0.94, -1)):
        c.l([(x0, H * 0.02), (x0 + sg * 10, H * 0.30)], (60, 64, 80), 10)
        c.r(x0 - 70, H * 0.00, x0 + 70, H * 0.07, 6, (50, 54, 70), INK, 3)
        for i in range(3):
            for j in range(2):
                col = (255, 250, 210) if on > 0.5 else (40, 44, 60)
                c.c(x0 - 45 + i * 45, H * 0.018 + j * H * 0.03, 16, col, INK, 2)


def glow(img, pts, on, t):
    if on <= 0:
        return img
    import numpy as np
    lay = Image.new("RGB", img.size, (0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(lay)
    for x, y in pts:
        r = 120
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 190, 140))
    lay = lay.filter(ImageFilter.GaussianBlur(50))
    a = np.asarray(img, dtype="uint16") + (np.asarray(lay, dtype="float32") * on).astype("uint16")
    return Image.fromarray(np.minimum(a, 255).astype("uint8"))


def dark(img, k, t, phones=True):
    """Apagón: oscurece y deja puntos de luz de móviles en la grada."""
    if k <= 0:
        return img
    out = Image.blend(img, Image.new("RGB", img.size, (6, 8, 20)), 0.80 * k)
    if phones:
        from PIL import ImageDraw
        d = ImageDraw.Draw(out)
        rnd = random.Random(3)
        W, H = img.size
        for i in range(40):
            if rnd.random() < k:
                x, y = rnd.uniform(0, W), rnd.uniform(H * 0.05, H * 0.40)
                r = 3 + 2 * abs(math.sin(t * 3 + i))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230))
    return out


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, wet, darkk = [], 0, False, 0.0
    light_pts = []

    if kind == "x_ap_venda":
        # entreno de día con los ojos vendados: chuto y gol
        pitch_persp(b, W, H, t, seed=2)
        goal_persp(f, W * 0.10, H * 0.66, 0.9)
        kick = _e((t - dur * 0.35) / 0.15)
        bean(f, W * 0.66, H * 0.92, 1.0, venda=1, emo="serio", t=t, arms="abiertos" if kick < 0.5 else "relax",
             legs="abiertas" if 0 < kick < 1 else "pie", **YO)
        u = _e((t - dur * 0.45) / 0.4)
        bx = W * 0.56 - (W * 0.56 - W * 0.30) * u
        by = H * 0.92 - (H * 0.92 - H * 0.58) * u - 120 * math.sin(u * math.pi)
        ball2(f, bx, by, 34 - 12 * u, u * 6)
        hx, hy = bean_head(W * 0.66, H * 0.92, 1.0)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0), (hx, hy + 60, 2.0), (W * 0.36, H * 0.62, 1.4)], t, dur, W, H)
        signs.append(("CON VENDA", 0.22, 0.3))

    elif kind == "x_ap_risas":
        locker_persp(b, W, H, t)
        for i, xx in enumerate((0.58, 0.82)):
            bean(f, W * xx, H * 0.78, 0.8, AZUL, BLANCO, ["pelo", "melena"][i], (50, 34, 20), emo="feliz", t=t,
                 talk=(t * 2 + i) % 1 < 0.5, num=str(4 + i), blink_off=i)
        bean(f, W * 0.30, H * 0.95, 1.25, emo="feliz", t=t, arms="relax", arm_r="senala", talk=(t * 2.3) % 1 < 0.6, look=1, **CAP)
        hx, hy = bean_head(W * 0.30, H * 0.95, 1.25)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0), (hx + 40, hy + 60, 1.9), (W * 0.70, H * 0.55, 1.6)], t, dur, W, H)
        tilt = 0 if t < dur / 3 else 4
        signs.append(("EL MURCIÉLAGO", 0.22, dur * 0.45))

    elif kind == "x_ap_banquillo":
        pitch_persp(b, W, H, t, seed=5)
        bean(f, cx, H * 0.86, 1.25, emo="aburrido", t=t, venda=0, **YO)
        # banquillo delante (tapa las piernas: parece sentado)
        f.p([(W * 0.0, H * 0.74), (W * 1.0, H * 0.70), (W * 1.0, H * 0.80), (W * 0.0, H * 0.84)], (90, 96, 120), INK, 4)
        f.p([(W * 0.0, H * 0.84), (W * 1.0, H * 0.80), (W * 1.0, H * 1.0), (W * 0.0, H * 1.0)], (60, 64, 84), INK, 4)
        f.p([(-W * 0.05, H * 0.45), (W * 1.05, H * 0.38), (W * 1.05, H * 0.42), (-W * 0.05, H * 0.49)], (180, 220, 240, 120), INK, 3)
        hx, hy = bean_head(cx, H * 0.86, 1.25)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0), (hx, hy + 50, 1.9)], t, dur, W, H)
        wet, tilt = True, -3
        signs.append(("0 MINUTOS", 0.22, 0.4))

    elif kind == "x_ap_final":
        pitch_persp(b, W, H, t, seed=7, night=True)
        focos(f, W, H, 1, t)
        goal_persp(f, W * 0.10, H * 0.70, 0.9)
        bean(f, W * 0.30, H * 0.70, 0.55, (255, 140, 30), BLANCO, "pelo", emo="miedo", t=t, arms="abiertos", legs="abiertas", num="1")
        bean(f, W * 0.68, H * 0.95, 1.0, emo="serio", t=t, **CAP)
        ball2(f, W * 0.55, H * 0.93, 30, 0.4)
        img = camera(b.im, f.im, [(cx, H * 0.50, 1.0), (W * 0.50, H * 0.70, 1.35)], t, dur, W, H)
        light_pts = [(W * 0.06, H * 0.035), (W * 0.94, H * 0.035)]
        img = glow(img, light_pts, 1.0, t)
        signs.append(("1 - 1", 0.22, 0.3))
        if t > dur * 0.55:
            signs.append(("PENALTIS", 0.29, dur * 0.55))

    elif kind == "x_ap_apagon":
        pitch_persp(b, W, H, t, seed=7, night=True)
        T = dur * 0.40
        flick = 1.0 if t < T else (0.0 if t > T + 0.45 else (1.0 if int((t - T) * 14) % 2 else 0.0))
        focos(f, W, H, flick, t)
        img = camera(b.im, f.im, [(cx, H * 0.30, 1.6), (cx, H * 0.45, 1.0)], t, dur, W, H, flash=False)
        img = glow(img, [(W * 0.06, H * 0.035), (W * 0.94, H * 0.035)], flick, t)
        if flick == 0 and t > T:
            darkk = min(1.0, (t - T - 0.45) / 0.3 + 0.7)
            signs.append(("APAGÓN", 0.22, T + 0.5))

    elif kind == "x_ap_capitan":
        pitch_persp(b, W, H, t, seed=7, night=True)
        kick = _e((t - dur * 0.45) / 0.15)
        bean(f, cx, H * 0.95, 1.4, emo="miedo", t=t, arms="abiertos" if kick > 0 else "relax", look=-0.5, **CAP)
        u = _e((t - dur * 0.50) / 0.5)
        if t < dur * 0.5:
            ball2(f, cx - 120, H * 0.93, 38, 0)
        else:
            ball2(f, cx - 120 - 200 * u, H * 0.93 - H * 0.85 * u, 38 - 20 * u, u * 8)
        hx, hy = bean_head(cx, H * 0.95, 1.4)
        img = camera(b.im, f.im, [(hx, hy + 80, 1.7), (cx, H * 0.55, 1.0)], t, dur, W, H, flash=False)
        darkk = 0.75
        if u >= 1:
            signs.append(("FALLA", 0.22, dur * 0.85))

    elif kind == "x_ap_tetoca":
        pitch_persp(b, W, H, t, seed=7, night=True)
        half = dur * 0.45
        bean(f, W * 0.28, H * 0.95, 1.3, emo="aburrido", talk=t < half, t=t, arms="jarras", look=1, **COACH)
        vd = _e((t - dur * 0.65) / 0.35)
        bean(f, W * 0.74, H * 0.95, 1.3, emo="sorpresa" if t < dur * 0.65 else "serio", t=t, look=-1, venda=vd,
             arms="relax", **YO)
        c1, c2 = bean_head(W * 0.28, H * 0.95, 1.3), bean_head(W * 0.74, H * 0.95, 1.3)
        img = camera(b.im, f.im, [(c1[0] + 40, c1[1] + 60, 1.9), (c2[0] - 20, c2[1] + 60, 1.9)], t, dur, W, H, flash=False)
        darkk = 0.55
        if t < half:
            signs.append(("TE TOCA", 0.22, 0.4))

    elif kind == "x_ap_gol":
        pitch_persp(b, W, H, t, seed=7, night=True)
        T = dur * 0.35            # chute
        L = dur * 0.55            # vuelve la luz
        on = 1.0 if t > L else 0.0
        focos(f, W, H, on, t)
        goal_persp(f, W * 0.10, H * 0.70, 0.9)
        u = _e((t - T) / 0.4)
        if t < T:
            b.im = b.im.filter(ImageFilter.GaussianBlur(8 * K))
            ball2(f, cx, H * 0.66, 200, 0.3)
            img = camera(b.im, f.im, [(cx, H * 0.58, 1.0 + 0.2 * t / T)], t, T, W, H, blur_close=False, flash=False)
        else:
            bean(f, W * 0.72, H * 0.96, 1.0, emo="serio" if t < L else "feliz", t=t, venda=1,
                 arms="relax" if t < L else "arriba", **YO)
            bean(f, W * 0.34, H * 0.70, 0.55, (255, 140, 30), BLANCO, "pelo", emo="dolor" if u >= 1 else "miedo", t=t,
                 arms="abiertos", legs="abiertas", num="1")
            ball2(f, W * 0.60 - (W * 0.60 - W * 0.16) * u, H * 0.94 - (H * 0.94 - H * 0.60) * u - 80 * math.sin(u * math.pi), 32 - 12 * u, u * 9)
            if t > L:
                confetti(f, W, H, t, L)
            img = camera(b.im, f.im, [(cx, H * 0.55, 1.0)], t - T, dur - T, W, H, flash=False, shake=8 if 0 < t - L < 0.3 else 0)
            img = glow(img, [(W * 0.06, H * 0.035), (W * 0.94, H * 0.035)], on, t)
            if u >= 1:
                signs.append(("GOL", 0.22, T + 0.4))
            if t > L:
                signs[:] = [("CAMPEONES", 0.22, L)]
                if t - L < 0.06:
                    img = Image.new("RGB", img.size, WHITE)
        if t < L:
            darkk = 0.7

    elif kind == "x_ap_perdon":
        pitch_persp(b, W, H, t, seed=2)
        goal_persp(f, W * 0.10, H * 0.66, 0.9)
        # el capitán entrena con venda y falla; yo miro con un café
        bean(f, W * 0.48, H * 0.80, 0.85, emo="miedo", t=t, venda=1, arms="abiertos", **CAP)
        u = ((t * 0.8) % 1.0)
        ball2(f, W * 0.40 + 300 * u, H * 0.78 - 260 * math.sin(u * math.pi), 24, u * 7)
        bean(f, W * 0.80, H * 1.0, 1.3, emo="aburrido", t=t, arms="relax", arm_r="taza", look=-1, **YO)
        hx, hy = bean_head(W * 0.80, H * 1.0, 1.3)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0), (hx - 40, hy + 70, 1.8)], t, dur, W, H)
        signs.append(("NUEVO MÉTODO", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    if darkk:
        img = dark(img, darkk, t)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
