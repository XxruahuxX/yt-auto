"""Storytime 057 «De portero como castigo»: llegaba tarde, el entrenador lo pone de portero, aprende a parar
entrenando con su perro y en la final para el penalti... y sale corriendo con el balón como el perro.
Estilo cacahuete (anim_bean). Escenas x_pc_*."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, pitch_persp, goal_persp,
                        camera, vignette, confetti, _e, dust, burst, speed_lines, ripple)

NAR = (255, 140, 30)
YO = dict(body=(46, 120, 210), num="8", skin=BLANCO, hair="pelo", hcol=(40, 30, 26))
YOP = dict(YO, body=NAR, num="1", gloves=True)
MISTER = dict(body=(60, 64, 76), skin=BLANCO, hair="gorra", hcol=(30, 30, 30), beard=True)
RIVAL = dict(body=(200, 46, 44), num="9", skin=BLANCO, hair="tupe", hcol=(30, 24, 20))
PERRO = (196, 140, 84)


def dog(c, x, y, s, t, run=0.0, ball=False, look=1):
    """Perro cacahuete: cuerpo ovalado, orejas caídas, cola que se mueve. (x, y) = patas."""
    sg = look
    by = y - 70 * s
    for i, dx in enumerate((-48, -24, 26, 50)):
        sw = math.sin(t * 18 + i * 1.7) * 14 * s * run
        c.l([(x + dx * s * sg, by + 10 * s), (x + dx * s * sg + sw, y)], INK, 9 * s)
        c.l([(x + dx * s * sg, by + 10 * s), (x + dx * s * sg + sw, y)], (150, 100, 56), 5 * s)
    wag = math.sin(t * 14) * 0.5
    tx, ty = x - 72 * s * sg, by - 18 * s
    c.l([(tx, ty), (tx - 30 * s * sg, ty - 40 * s + 12 * s * wag)], INK, 9 * s)
    c.l([(tx, ty), (tx - 30 * s * sg, ty - 40 * s + 12 * s * wag)], PERRO, 5 * s)
    c.e(x - 80 * s, by - 38 * s, x + 80 * s, by + 30 * s, (160, 110, 64), INK, 5 * s)
    c.e(x - 72 * s, by - 32 * s, x + 60 * s, by + 18 * s, PERRO, w=0)
    hx, hy = x + 82 * s * sg, by - 50 * s
    c.c(hx, hy, 42 * s, PERRO, INK, 5 * s)
    c.e(hx - 52 * s, hy - 30 * s, hx - 26 * s, hy + 20 * s, (120, 80, 46), INK, 4 * s)
    c.e(hx + 26 * s, hy - 30 * s, hx + 52 * s, hy + 20 * s, (120, 80, 46), INK, 4 * s)
    for e in (-14, 14):
        c.c(hx + e * s + 6 * s * sg, hy - 6 * s, 5 * s, INK, w=0)
    c.c(hx + 30 * s * sg, hy + 12 * s, 9 * s, INK, w=0)
    if ball:
        ball2(c, hx + 40 * s * sg, hy + 34 * s, 30 * s, t * 2)
    return hx, hy


def _clock_icon(c, x, y, r, t):
    c.c(x, y, r, WHITE, INK, 6)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        c.l([(x + math.cos(a) * r * 0.82, y + math.sin(a) * r * 0.82), (x + math.cos(a) * r * 0.92, y + math.sin(a) * r * 0.92)], INK, 3)
    a = -math.pi / 2 + t * 6
    c.l([(x, y), (x + math.cos(a) * r * 0.7, y + math.sin(a) * r * 0.7)], (222, 52, 40), 6)
    c.l([(x, y), (x + r * 0.45, y)], INK, 7)
    c.c(x, y, 6, INK, w=0)


def _cup(c, x, y, s):
    """Copa dorada (base en (x, y))."""
    g, gd = (240, 196, 60), (196, 150, 30)
    c.r(x - 60 * s, y - 30 * s, x + 60 * s, y, 6 * s, (90, 60, 40), INK, 4 * s)
    c.r(x - 14 * s, y - 90 * s, x + 14 * s, y - 30 * s, 4 * s, gd, INK, 4 * s)
    for sg in (-1, 1):
        c.arc(x + sg * 70 * s - 40 * s, y - 200 * s, x + sg * 70 * s + 40 * s, y - 120 * s,
              90 + sg * 90 - 90, 90 + sg * 90 + 90, INK, 10 * s)
        c.arc(x + sg * 70 * s - 40 * s, y - 200 * s, x + sg * 70 * s + 40 * s, y - 120 * s,
              90 + sg * 90 - 90, 90 + sg * 90 + 90, g, 5 * s)
    c.chord(x - 80 * s, y - 260 * s, x + 80 * s, y - 70 * s, 0, 180, g, INK, 5 * s)
    c.r(x - 80 * s, y - 170 * s, x + 80 * s, y - 160 * s, 0, gd, w=0)
    c.e(x - 50 * s, y - 150 * s, x - 30 * s, y - 110 * s, (255, 240, 170), w=0)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img = [], 0, None

    if kind == "x_pc_tarde":
        # llego corriendo con la mochila; el míster de brazos en jarras y el reloj
        pitch_persp(b, W, H, t, seed=3)
        bean(f, W * 0.72, H * 0.93, 1.05, emo="serio", t=t, look=-1, arms="jarras", **MISTER)
        u = _e(min(1.0, t / (dur * 0.6)))
        rx = -W * 0.1 + (W * 0.32 + W * 0.1) * u
        bean(f, rx, H * 0.96, 0.95, emo="miedo", t=t, look=1, arms="anda", legs="corre" if u < 1 else "pie",
             phase=t * 16, **YO)
        if u < 1:
            speed_lines(f, rx - 60, H * 0.70, t, 0.0, n=8, dur=dur)
        _clock_icon(f, W * 0.78, H * 0.30, 80, t)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("TARDE", 0.22, 0.3))

    elif kind == "x_pc_castigo":
        # el míster señala la portería; me da los guantes
        pitch_persp(b, W, H, t, seed=3)
        goal_persp(f, W * 0.04, H * 0.66, 0.85)
        bean(f, W * 0.70, H * 0.98, 1.2, emo="enfado", t=t, look=-1, arms="relax", arm_r="senala" if False else "relax",
             talk=t < dur * 0.6, **MISTER)
        hx, hy = bean_head(W * 0.70, H * 0.98, 1.2)
        bean(f, W * 0.30, H * 1.0, 1.15, emo="sorpresa" if t > dur * 0.4 else "serio", t=t, look=1,
             arms="relax", gloves=t > dur * 0.4, **YO)
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.05), (W * 0.42, H * 0.62, 1.3)], t, dur, W, H)
        signs.append(("DE PORTERO", 0.22, dur * 0.4))
        tilt = 3

    elif kind == "x_pc_goles":
        # me meten todo: tres balones seguidos me pasan
        pitch_persp(b, W, H, t, seed=5)
        goal_persp(f, W * 0.10, H * 0.80, 1.25)
        gx, gy = W * 0.50, H * 0.80
        n = 3
        seg = dur / n
        i = min(n - 1, int(t / seg))
        lt = (t - i * seg) / seg
        side = (-1, 1, -1)[i]
        dive = _e(min(1.0, max(0.0, (lt - 0.25) / 0.4)))
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        kx = gx - side * 120 * dive
        bean(tmp, kx, gy - 40 * math.sin(dive * math.pi), 0.8, emo="miedo", t=t, arms="arriba", legs="abiertas", **YOP)
        f.im.alpha_composite(tmp.im.rotate(-side * 60 * dive, resample=Image.BICUBIC, center=(kx * K, (gy - 160) * K)))
        u = min(1.0, lt / 0.6)
        bx = W * 0.5 + side * W * 0.30 * u
        by = H * 0.98 - (H * 0.98 - H * 0.62) * u
        ball2(f, bx, by, 50 - 22 * u, t * 6)
        if u >= 1:
            ripple(f, bx, by, t, i * seg + 0.6 * seg)
            burst(f, "GOL", bx, by - 80, t, i * seg + 0.6 * seg, 60, hold=0.5)
        f.r(W * 0.62, H * 0.38, W * 0.94, H * 0.46, 10, (20, 22, 34), INK, 4)
        f.text(W * 0.78, H * 0.385, f"0 - {5 + i}", 70, (255, 214, 40), 3)
        img = camera(b.im, f.im, [(cx, H * 0.64, 1.0)], t, dur, W, H, shake=4 if lt > 0.6 and lt < 0.7 else 0)

    elif kind == "x_pc_risas":
        # mis compañeros se ríen; yo con los guantes, cabizbajo
        pitch_persp(b, W, H, t, seed=5)
        b.im = b.im.filter(ImageFilter.GaussianBlur(4 * K))
        for j, (xx, ss) in enumerate(((0.12, 0.8), (0.88, 0.8), (0.25, 0.95), (0.75, 0.95))):
            bean(f, W * xx, H * (0.80 + 0.06 * (ss > 0.9)), ss, (46, 120, 210), BLANCO, ["pelo", "gorra", "tupe", "melena"][j],
                 (40, 30, 26), emo="feliz", t=t, talk=True, arms="arriba" if j % 2 else "jarras", blink_off=j * 0.3,
                 look=1 if xx < 0.5 else -1)
        bean(f, cx, H * 1.02, 1.25, emo="aburrido", t=t, arms="relax", **YOP)
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.0), (cx, H * 0.58, 1.2)], t, dur, W, H)
        signs.append(("EL COLADOR", 0.22, 0.3))

    elif kind == "x_pc_perro":
        # en el jardín de casa: el perro salta a por la pelota con las patas por delante; yo lo imito
        b.r(0, 0, W, H * 0.5, 0, (150, 200, 240), w=0)
        b.r(0, H * 0.32, W, H * 0.5, 0, (200, 170, 120), INK, 3)
        for xx in range(0, int(W) + 40, 46):
            b.r(xx, H * 0.30, xx + 30, H * 0.50, 4, (226, 196, 140), INK, 2)
        b.r(0, H * 0.5, W, H, 0, (110, 176, 80), w=0)
        for i in range(10):
            b.l([(0, H * (0.52 + i * 0.05)), (W, H * (0.52 + i * 0.05))], (100, 164, 72), 3)
        half = dur * 0.5
        jump = math.sin(min(1.0, max(0.0, (t % half) / (half * 0.7))) * math.pi)
        dog(f, W * 0.30, H * 0.84 - 200 * jump, 1.5, t, run=0.6, ball=jump > 0.6)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        kx, ky = W * 0.72, H * 0.98 - 120 * jump * (t > half)
        bean(tmp, kx, ky, 0.95, emo="serio" if t < half else "picaro", t=t, look=-1,
             arms="arriba" if t > half else "jarras", legs="abiertas" if t > half else "pie", **YOP)
        f.im.alpha_composite(tmp.im.rotate(20 * jump * (t > half), resample=Image.BICUBIC, center=(kx * K, (ky - 200) * K)))
        if jump <= 0.6:
            ball2(f, W * 0.30 + 200, H * 0.56 + 40 * math.sin(t * 3), 30, t * 3)
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.0)], t, dur, W, H)
        signs.append(("MI PERRO", 0.22, 0.3))
        if t > half:
            signs.append(("COMO ÉL", 0.29, half + 0.2))

    elif kind == "x_pc_final":
        # final de noche, penaltis, 4-4, el delantero rival coloca el balón
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.08, H * 0.68, 0.95)
        f.r(W * 0.56, H * 0.40, W * 0.94, H * 0.50, 12, (20, 22, 34), INK, 5)
        f.text(W * 0.75, H * 0.405, "4 - 4", 92, (255, 214, 40), 4)
        bean(f, W * 0.66, H * 0.98, 1.1, emo="serio", t=t, look=-0.6, arms="relax", **RIVAL)
        ball2(f, W * 0.40, H * 0.93, 46, 0.2)
        img = camera(b.im, f.im, [(W * 0.70, H * 0.55, 1.3), (cx, H * 0.62, 1.05)], t, dur, W, H)
        signs.append(("PENALTIS", 0.22, dur * 0.5))
        tilt = -4

    elif kind == "x_pc_para":
        # chuta; salto como el perro, en plancha, y la atrapo
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.06, H * 0.74, 1.05)
        T0 = dur * 0.25
        dive = _e(min(1.0, max(0.0, (t - T0) / (dur * 0.3))))
        kx, ky = W * 0.45 - 200 * dive, H * 0.74 - 160 * math.sin(min(1.0, dive) * math.pi * 0.8)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        bean(tmp, kx, ky, 0.75, emo="enfado" if dive < 1 else "sorpresa", t=t, arms="arriba", legs="abiertas", **YOP)
        f.im.alpha_composite(tmp.im.rotate(75 * dive, resample=Image.BICUBIC, center=(kx * K, (ky - 180) * K)))
        u = _e(min(1.0, max(0.0, (t - T0 + 0.1) / (dur * 0.3))))
        bx = W * 0.55 - (W * 0.55 - W * 0.22) * u
        by = H * 0.98 - (H * 0.98 - H * 0.48) * u
        ball2(f, bx, by, 44 - 16 * u, u * 4)
        if dive >= 1:
            speed_lines(f, bx, by, t, T0 + dur * 0.3, n=12)
        burst(f, "¡PARADA!", W * 0.32, H * 0.44, t, T0 + dur * 0.3, 70)
        img = camera(b.im, f.im, [(cx, H * 0.64, 1.0), (W * 0.30, H * 0.60, 1.4)], t, dur, W, H,
                     shake=7 if 0 < t - (T0 + dur * 0.3) < 0.25 else 0)
        tilt = -3

    elif kind == "x_pc_corre":
        # salgo corriendo con el balón como el perro; el árbitro me persigue
        pitch_persp(b, W, H, t, seed=7, night=True)
        u = (t / dur)
        x0 = W * 0.60 - W * 0.32 * u
        bean(f, x0 + W * 0.36, H * 0.97, 0.9, (26, 26, 30), BLANCO, "pelo", (20, 20, 24), emo="enfado", t=t, look=-1,
             arms="anda", legs="corre", phase=t * 15, ref=True, legcol=(18, 18, 22), talk=True)
        bean(f, x0, H * 0.99, 1.0, emo="picaro", t=t, look=-1, arms="anda", legs="corre", phase=t * 17, **YOP)
        hx, hy = bean_head(x0, H * 0.99, 1.0)
        ball2(f, hx - 70, hy + 150, 40, t * 2)
        dust(f, x0 + 60, H * 0.98, t, 0.2, s=0.6)
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.05)], t, dur, W, H)
        signs.append(("NO LA SUELTO", 0.22, 0.3))
        tilt = 4

    elif kind == "x_pc_campeones":
        # campeones: levanto la copa, el perro al lado
        pitch_persp(b, W, H, t, seed=7, night=True)
        confetti(f, W, H, t, 0.0)
        bean(f, W * 0.42, H * 1.0, 1.25, emo="feliz", t=t, arms="arriba", **YOP)
        hx, hy = bean_head(W * 0.42, H * 1.0, 1.25)
        _cup(f, hx, hy - 105, 1.0)
        dog(f, W * 0.80, H * 0.98, 0.9, t, look=-1)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0)], t, dur, W, H)
        signs.append(("CAMPEONES", 0.22, 0.3))

    elif kind == "x_pc_cierre":
        # ahora llego tarde a propósito, con los guantes puestos y el perro
        pitch_persp(b, W, H, t, seed=3)
        _clock_icon(f, W * 0.20, H * 0.32, 80, t)
        bean(f, W * 0.78, H * 0.93, 1.0, emo="aburrido", t=t, look=-1, arms="jarras", **MISTER)
        u = _e(min(1.0, t / (dur * 0.5)))
        bean(f, W * 0.1 + W * 0.30 * u, H * 0.97, 1.0, emo="picaro", t=t, look=1, arms="anda", legs="anda" if u < 1 else "pie",
             phase=t * 8, **YOP)
        dog(f, W * -0.08 + W * 0.30 * u, H * 0.99, 0.75, t, run=1.0 if u < 1 else 0.0)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("A PROPÓSITO", 0.22, dur * 0.4))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
