"""Serie «Todos tenemos un amigo que…» (ep. 1: el que trae el balón y se lo lleva si pierde).
Fútbol de barrio en una pista de asfalto, estilo cacahuete. Escenas x_am_*."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, camera, vignette, _e,
                        dust, burst, speed_lines)

DUENO = dict(body=(250, 200, 40), skin=BLANCO, hair="gorra", hcol=(30, 26, 24), num="10")
AMIGOS = [dict(body=(46, 120, 210), skin=BLANCO, hair="pelo", hcol=(40, 30, 26)),
          dict(body=(60, 170, 90), skin=BLANCO, hair="melena", hcol=(120, 70, 30)),
          dict(body=(200, 46, 44), skin=BLANCO, hair="tupe", hcol=(20, 20, 24)),
          dict(body=(150, 90, 200), skin=BLANCO, hair="rizos", hcol=(40, 28, 20)),
          dict(body=(240, 240, 236), skin=BLANCO, hair="pelo", hcol=(160, 110, 60))]


def barrio(c, W, H, t, evening=False):
    """Pista de barrio: bloques de pisos, tapia con dibujos, asfalto con líneas pintadas y una farola."""
    sky = (250, 170, 110) if evening else (150, 205, 245)
    c.r(-10, -10, W + 10, H * 0.42, 0, sky, w=0)
    rnd = random.Random(9)
    x = -30
    while x < W:
        w = rnd.uniform(150, 230)
        h = rnd.uniform(H * 0.20, H * 0.34)
        col = rnd.choice([(214, 160, 120), (190, 190, 176), (226, 206, 160), (176, 130, 110)])
        c.r(x, H * 0.42 - h, x + w, H * 0.42, 0, col, INK, 3)
        for yy in range(int(H * 0.42 - h + 20), int(H * 0.40), 46):
            for xx in range(int(x + 16), int(x + w - 28), 40):
                lit = rnd.random() < (0.5 if evening else 0.15)
                c.r(xx, yy, xx + 24, yy + 30, 2, (255, 226, 140) if lit else (110, 140, 170), INK, 2)
                c.r(xx - 4, yy + 30, xx + 28, yy + 34, 0, (230, 230, 230), INK, 1.5)
        x += w + rnd.uniform(4, 18)
    # tapia con manchas de colores (sin letras ni marcas)
    c.r(-10, H * 0.40, W + 10, H * 0.52, 0, (210, 196, 176), INK, 4)
    for i in range(9):
        xx = W * (i / 8)
        c.e(xx - 50, H * 0.42 + (i % 3) * 18, xx + 40, H * 0.47 + (i % 2) * 24,
            [(240, 90, 80), (80, 170, 230), (250, 200, 60), (120, 200, 120)][i % 4], w=0)
    for i in range(int(W // 70) + 2):
        c.l([(i * 70, H * 0.40), (i * 70, H * 0.52)], (190, 176, 156), 2)
    # asfalto con línea de medio campo en perspectiva
    c.r(-10, H * 0.52, W + 10, H + 10, 0, (110, 112, 120), w=0)
    for i in range(10):
        y = H * (0.54 + 0.05 * i * (1 + i * 0.1))
        c.l([(-10, y), (W + 10, y)], (100, 102, 110), 2)
    c.l([(W * 0.50, H * 0.53), (W * 0.62, H + 10)], WHITE, 6)
    c.e(W * 0.36, H * 0.70, W * 0.82, H * 0.80, None, WHITE, 6)
    # farola
    c.r(W * 0.92, H * 0.18, W * 0.935, H * 0.52, 3, (60, 64, 76), INK, 3)
    c.r(W * 0.86, H * 0.17, W * 0.94, H * 0.195, 6, (60, 64, 76), INK, 3)
    if evening:
        c.c(W * 0.875, H * 0.20, 16, (255, 236, 150), INK, 2)


def mochila(c, x, y, s, col=(60, 80, 160)):
    c.r(x - 46 * s, y - 100 * s, x + 46 * s, y, 18 * s, col, INK, 5 * s)
    c.r(x - 30 * s, y - 50 * s, x + 30 * s, y - 14 * s, 8 * s, tuple(int(v * 0.8) for v in col), INK, 4 * s)
    c.arc(x - 26 * s, y - 128 * s, x + 26 * s, y - 80 * s, 180, 360, INK, 7 * s)


def lata(c, x, y, s, rot=0.0):
    tmp_w, tmp_h = 34 * s, 56 * s
    c.r(x - tmp_w / 2, y - tmp_h, x + tmp_w / 2, y, 6 * s, (200, 60, 50), INK, 4 * s)
    c.r(x - tmp_w / 2, y - tmp_h * 0.62, x + tmp_w / 2, y - tmp_h * 0.38, 0, (240, 240, 240), w=0)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img = [], 0, None

    if kind == "x_am_intro":
        # llega con el balón en alto; todos lo reciben como a un rey
        barrio(b, W, H, t)
        u = _e(min(1.0, t / (dur * 0.45)))
        dx = W * 0.5 + W * 0.6 * (1 - u)
        for j, (xx, ss) in enumerate(((0.12, 0.85), (0.30, 0.95), (0.88, 0.85))):
            bean(f, W * xx, H * 0.92, ss, emo="sorpresa" if t > dur * 0.3 else "aburrido", t=t, look=1 if xx < 0.5 else -1,
                 arms="arriba" if t > dur * 0.45 else "relax", blink_off=j * 0.4, **AMIGOS[j])
        bean(f, dx, H * 0.99, 1.1, emo="picaro", t=t, look=-1, arms="relax", arm_r="arriba",
             legs="anda" if u < 1 else "pie", phase=t * 9, **DUENO)
        hx, hy = bean_head(dx, H * 0.99, 1.1)
        ball2(f, hx + 132, hy - 150 + 6 * math.sin(t * 5), 48, t)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("EL DEL BALÓN", 0.22, 0.3))

    elif kind == "x_am_equipos":
        # elige equipo: señala a los buenos; los otros, resignados
        barrio(b, W, H, t)
        bean(f, W * 0.24, H * 0.99, 1.15, emo="picaro", t=t, look=1, arms="relax", arm_r="senala", **DUENO)
        ball2(f, W * 0.10, H * 0.96, 40, 0)
        for j, xx in enumerate((0.58, 0.74, 0.90)):
            chosen = t > dur * (0.25 + 0.2 * j) and j < 2
            bean(f, W * xx, H * 0.90, 0.85, emo="feliz" if chosen else "aburrido", t=t, look=-1,
                 arms="arriba" if chosen else "relax", blink_off=j * 0.3, **AMIGOS[j + 1])
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.62, H * 0.62, 1.25)], t, dur, W, H)
        signs.append(("ELIJO YO", 0.22, 0.3))

    elif kind == "x_am_porteria":
        # porterías de mochilas: la suya se estrecha cuando le atacan
        barrio(b, W, H, t)
        k = _e(min(1.0, max(0.0, (t - dur * 0.35) / (dur * 0.35))))
        gap = 240 - 150 * k
        mochila(f, cx - gap, H * 0.80, 0.9)
        mochila(f, cx + gap, H * 0.80, 0.9, (200, 70, 60))
        bean(f, cx, H * 0.84, 0.8, emo="picaro" if k > 0.5 else "serio", t=t, arms="abiertos", legs="abiertas", **DUENO)
        if k > 0:
            for sg in (-1, 1):
                f.l([(cx + sg * (gap + 70), H * 0.75), (cx + sg * (gap + 120), H * 0.75)], INK, 6)
                f.p([(cx + sg * (gap + 60), H * 0.75), (cx + sg * (gap + 80), H * 0.74 - 14), (cx + sg * (gap + 80), H * 0.75 + 14)], INK)
        bean(f, W * 0.80, H * 1.02, 1.05, emo="enfado", t=t, look=-1, arms="jarras", **AMIGOS[0])
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.15)], t, dur, W, H)
        signs.append(("TRAMPA", 0.22, dur * 0.6))

    elif kind == "x_am_falta":
        # le rozas y se tira: falta
        barrio(b, W, H, t)
        T = dur * 0.3
        fall = _e(min(1.0, max(0.0, (t - T) / 0.35)))
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        kx, ky = W * 0.66, H * 0.95
        bean(tmp, kx, ky, 1.0, emo="dolor" if fall > 0.5 else "serio", t=t, arms="abiertos" if fall > 0 else "relax",
             legs="abiertas" if fall > 0 else "pie", talk=fall >= 1, **DUENO)
        f.im.alpha_composite(tmp.im.rotate(80 * fall, resample=Image.BICUBIC, center=(kx * K, ky * K)))
        bean(f, W * 0.88, H * 0.90, 0.85, emo="sorpresa" if fall > 0 else "serio", t=t, look=-1, arms="abiertos" if fall > 0 else "relax",
             **AMIGOS[2])
        dust(f, kx - 200, H * 0.95, t, T + 0.2, s=0.8)
        burst(f, "¡FALTA!", W * 0.40, H * 0.66, t, T + 0.4, 74)
        img = camera(b.im, f.im, [(cx, H * 0.70, 1.0)], t, dur, W, H, shake=5 if 0 < t - T - 0.3 < 0.2 else 0)
        tilt = -4

    elif kind == "x_am_novale":
        # marcamos nosotros: no vale, «era mano»
        barrio(b, W, H, t)
        mochila(f, W * 0.24, H * 0.76, 0.7)
        mochila(f, W * 0.56, H * 0.76, 0.7, (200, 70, 60))
        u = _e(min(1.0, t / (dur * 0.35)))
        ball2(f, W * 0.80 - (W * 0.80 - W * 0.40) * u, H * 0.96 - (H * 0.96 - H * 0.72) * u, 40 - 10 * u, t * 4)
        bean(f, W * 0.86, H * 1.02, 1.0, emo="feliz" if t > dur * 0.35 else "serio", t=t, look=-1,
             arms="arriba" if t > dur * 0.35 else "relax", **AMIGOS[3])
        if t > dur * 0.45:
            bean(f, W * 0.22, H * 1.0, 1.15, emo="enfado", t=t, look=1, arms="relax", arm_r="senala", talk=True, **DUENO)
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.0)], t, dur, W, H)
        if t > dur * 0.45:
            signs.append(("NO VALE", 0.22, dur * 0.45))

    elif kind == "x_am_marcador":
        # vamos 5-0: marcador pintado con tiza en la tapia; él mira el reloj
        barrio(b, W, H, t, evening=True)
        b.r(W * 0.20, H * 0.41, W * 0.80, H * 0.51, 6, (40, 70, 60), INK, 4)
        b.text(cx, H * 0.425, "5 - 0", 100, WHITE, 0)
        bean(f, W * 0.50, H * 1.02, 1.3, emo="miedo", t=t, look=0.4, arms="relax", arm_r="cara", **DUENO)
        img = camera(b.im, f.im, [(cx, H * 0.50, 1.25), (cx, H * 0.62, 1.05)], t, dur, W, H)
        signs.append(("PIERDE", 0.22, dur * 0.5))
        tilt = 3

    elif kind == "x_am_cena":
        # «¡A CENAR!» a las cinco: coge el balón y se va
        barrio(b, W, H, t, evening=True)
        b.r(W * 0.06, H * 0.20, W * 0.20, H * 0.26, 4, (255, 226, 140), INK, 3)
        u = _e(min(1.0, max(0.0, (t - dur * 0.35) / (dur * 0.6))))
        x0 = W * 0.50 - W * 0.65 * u
        bean(f, x0, H * 0.98, 1.05, emo="picaro", t=t, look=-1, arms="relax", arm_r="arriba" if u > 0 else "relax",
             legs="anda" if 0 < u < 1 else "pie", phase=t * 9, **DUENO)
        hx, hy = bean_head(x0, H * 0.98, 1.05)
        if u > 0:
            ball2(f, hx + 126, hy - 140, 44, 0)
        else:
            ball2(f, hx + 40, H * 0.95, 44, 0)
        for j, xx in enumerate((0.74, 0.90)):
            bean(f, W * xx, H * 0.92, 0.85, emo="sorpresa", t=t, look=-1, arms="abiertos", blink_off=j * 0.3, **AMIGOS[j])
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("¡A CENAR!", 0.22, 0.2))
        signs.append(("17:00", 0.29, dur * 0.35))

    elif kind == "x_am_lata":
        # nos quedamos jugando con una lata
        barrio(b, W, H, t, evening=True)
        u = (t * 0.8) % 1
        lata(f, W * 0.30 + W * 0.40 * u, H * 0.95, 1.2)
        for j, xx in enumerate((0.16, 0.84)):
            bean(f, W * xx, H * 0.99, 1.0, emo="aburrido", t=t, look=1 if xx < 0.5 else -1, arms="relax", blink_off=j * 0.5,
                 **AMIGOS[j])
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.05)], t, dur, W, H)
        signs.append(("UNA LATA", 0.22, 0.3))

    elif kind == "x_am_cierre":
        # al día siguiente vuelve con el balón... y le dejamos elegir otra vez
        barrio(b, W, H, t)
        bean(f, W * 0.30, H * 0.99, 1.1, emo="picaro", t=t, look=1, arms="relax", arm_r="arriba", **DUENO)
        hx, hy = bean_head(W * 0.30, H * 0.99, 1.1)
        ball2(f, hx + 132, hy - 150 + 6 * math.sin(t * 5), 48, t)
        for j, xx in enumerate((0.62, 0.80)):
            bean(f, W * xx, H * 0.93, 0.9, emo="feliz", t=t, look=-1, arms="arriba", blink_off=j * 0.3, **AMIGOS[j])
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("OTRO DÍA", 0.22, 0.2))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    img = vignette(img, 0.28)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
