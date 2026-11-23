"""23-nov: «¿Por qué el portero no puede coger una cesión?» (x_ce_) y «¿Y si el portero usara las manos en todo el campo?» (x_mn_)."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, ball_fx, ripple, sign, dutch, rain,
                        pitch_persp, goal_persp, camera2, vignette, confetti, _e)

AZUL, NAR, ROJO = (40, 100, 210), (255, 140, 30), (200, 50, 45)


def clock(c, x, y, r, t, spd=1.0):
    c.c(x, y, r, WHITE, INK, 6)
    for i in range(12):
        a = i / 12 * 2 * math.pi
        c.l([(x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a)), (x + r * 0.92 * math.cos(a), y + r * 0.92 * math.sin(a))], INK, 4)
    a = t * spd * 2 * math.pi - math.pi / 2
    c.l([(x, y), (x + r * 0.75 * math.cos(a), y + r * 0.75 * math.sin(a))], (210, 40, 40), 6)
    c.l([(x, y), (x + r * 0.5 * math.cos(a / 12), y + r * 0.5 * math.sin(a / 12))], INK, 8)
    c.c(x, y, 8, INK, w=0)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt = [], 0
    if kind == "x_ce_mano":
        pitch_persp(b, W, H, t, seed=3)
        goal_persp(f, W * 0.06, H * 0.78, 1.1)
        bean(f, W * 0.40, H * 0.86, 1.2, NAR, BLANCO, "pelo", emo="aburrido", t=t, arms="abiertos", num="1")
        ball2(f, W * 0.40 + 150 * 1.2 * 0.98, H * 0.86 - 1.2 * 330, 34, 0.3)
        f.l([(W * 0.40 + 120, H * 0.86 - 1.2 * 380), (W * 0.40 + 240, H * 0.86 - 1.2 * 280)], ROJO, 14)
        f.l([(W * 0.40 + 240, H * 0.86 - 1.2 * 380), (W * 0.40 + 120, H * 0.86 - 1.2 * 280)], ROJO, 14)
        hx, hy = bean_head(W * 0.40, H * 0.86, 1.2)
        img = camera2(b.im, f.im, [(cx, H * 0.58, 1.0), (hx + 80, hy + 80, 1.7)], t, dur, W, H)
        signs.append(("PROHIBIDO", 0.22, 0.3))
    elif kind == "x_ce_tiempo":
        # cesión, la coge, la vuelve a pasar… el reloj corre
        pitch_persp(b, W, H, t, seed=5)
        goal_persp(f, W * 0.06, H * 0.78, 1.1)
        k = (t * 0.9) % 1.0
        dx = W * 0.72
        bean(f, W * 0.34, H * 0.84, 0.95, NAR, BLANCO, "pelo", emo="aburrido", t=t, arms="abiertos" if k > 0.5 else "relax", num="1")
        bean(f, dx, H * 0.92, 1.0, AZUL, BLANCO, "pelo", emo="aburrido", t=t, num="4", kick=min(1.0, k * 2.2) if k < 0.45 else None, kdir=-1)
        u = _e(max(0.0, (k - 0.2) / 0.3))
        bx = dx - 60 - (dx - 60 - W * 0.40) * u
        by = H * 0.90 - (H * 0.90 - H * 0.70) * u
        if k < 0.55:
            ball2(f, bx, by, 30, t * 8)
        else:
            ball2(f, W * 0.34 + 110, H * 0.84 - 260, 30, 0)
        clock(f, W * 0.78, H * 0.36, 90, t, 0.7)
        img = camera2(b.im, f.im, [(cx, H * 0.60, 1.0)], t, dur, W, H)
        signs.append(("1990", 0.22, 0.3))
    elif kind == "x_ce_bostezo":
        pitch_persp(b, W, H, t, seed=7)
        for i, xx in enumerate((0.22, 0.50, 0.78)):
            bean(f, W * xx, H * 0.95, 0.95, (230, 230, 235), BLANCO, ["pelo", "gorra", "melena"][i], (90, 60, 40),
                 emo="cerrados", t=t, arms="cara" if i == 1 else "relax", blink_off=i)
        zz = (t * 0.8) % 1
        from .anim_extra import font
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.50, H * 0.55, 1.6)], t, dur, W, H)
        signs.append(("1992: CAMBIA", 0.22, dur * 0.55))
    elif kind == "x_ce_patada":
        pitch_persp(b, W, H, t, seed=3)
        goal_persp(f, W * 0.06, H * 0.78, 1.1)
        kick = t / (dur * 0.35)
        bean(f, W * 0.42, H * 0.86, 1.15, NAR, BLANCO, "pelo", emo="serio" if kick < 1 else "feliz", t=t, num="1",
             kick=kick, kdir=1)
        u = _e(max(0.0, (t - dur * 0.18) / (dur * 0.5)))
        pos = lambda uu: (W * 0.52 + W * 0.6 * uu, H * 0.84 - 520 * math.sin(uu * math.pi * 0.8))
        bx, by = pos(u)
        if 0 < u < 1:
            ball_fx(f, [pos(max(0, u - k2 * 0.04)) for k2 in range(5, 0, -1)] + [(bx, by)], 30, ground=H * 0.86)
        ball2(f, bx, by, 30, t * 9)
        img = camera2(b.im, f.im, [(W * 0.45, H * 0.66, 1.35)], t, dur, W, H)
        signs.append(("¡FUERA!", 0.22, dur * 0.3))
        tilt = 3
    elif kind == "x_ce_sigue":
        pitch_persp(b, W, H, t, seed=3)
        bean(f, cx, H * 0.95, 1.4, NAR, BLANCO, "pelo", emo="aburrido", t=t, arms="jarras", num="1")
        img = camera2(b.im, f.im, [(cx, H * 0.66, 1.5)], t, dur, W, H)
        signs.append(("SÍGUENOS", 0.22, 0.3))

    elif kind == "x_mn_atrapa":
        pitch_persp(b, W, H, t, seed=4)
        up = _e(t / (dur * 0.4))
        bean(f, cx, H * 0.92, 1.2, NAR, BLANCO, "pelo", emo="picaro" if up >= 1 else "sorpresa", t=t, arms="arriba", num="1")
        ball2(f, cx + 110 * 1.2 - 40 * (1 - up), H * 0.92 - 1.2 * 420 - 300 * (1 - up), 32, t * (1 - up) * 9)
        hx, hy = bean_head(cx, H * 0.92, 1.2)
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.0), (hx + 40, hy, 1.7)], t, dur, W, H)
        signs.append(("MEDIO CAMPO", 0.22, 0.3))
    elif kind == "x_mn_corre":
        pitch_persp(b, W, H, t, seed=4)
        run = t / dur
        for i, (xx, yy) in enumerate(((0.20, 0.80), (0.42, 0.86))):
            bean(f, W * xx + 40 * run, H * yy, 0.8, ROJO, BLANCO, "pelo", emo="sorpresa", t=t, legs="corre", phase=t * 10 + i, num=str(5 + i))
        px = W * 0.55 + W * 0.25 * run
        bean(f, px, H * 0.94, 1.0, NAR, BLANCO, "pelo", emo="feliz", t=t, legs="corre", phase=t * 13, num="1", arms="relax", arm_r="arriba")
        ball2(f, px + 110, H * 0.94 - 400 + 6 * math.sin(t * 13), 28, 0)
        img = camera2(b.im, f.im, [(cx + 80, H * 0.68, 1.15)], t, dur, W, H)
        signs.append(("¡CON LA MANO!", 0.22, 0.3))
    elif kind == "x_mn_lanza":
        pitch_persp(b, W, H, t, seed=4)
        goal_persp(f, W * 0.08, H * 0.74, 1.0)
        T = dur * 0.35
        u = _e(max(0.0, (t - T) / (dur * 0.3)))
        bean(f, W * 0.76, H * 0.95, 1.05, NAR, BLANCO, "pelo", emo="feliz", t=t, num="1", arms="relax", arm_r="arriba" if t < T else "senala")
        pos = lambda uu: (W * 0.80 - (W * 0.80 - W * 0.22) * uu, H * 0.52 + (H * 0.62 - H * 0.52) * uu - 140 * math.sin(uu * math.pi))
        bx, by = pos(u)
        if 0 < u < 1:
            ball_fx(f, [pos(max(0, u - k2 * 0.05)) for k2 in range(5, 0, -1)] + [(bx, by)], 28)
        ball2(f, bx, by, 28, t * 7)
        ripple(f, W * 0.22, H * 0.62, t, T + dur * 0.3)
        img = camera2(b.im, f.im, [(W * 0.62, H * 0.70, 1.5), (W * 0.30, H * 0.62, 1.5)], t, dur, W, H, shake=8 if 0 < t - T - dur * 0.3 < 0.25 else 0)
        if u >= 1:
            signs.append(("GOL", 0.22, T + dur * 0.3))
    elif kind == "x_mn_arbitro":
        pitch_persp(b, W, H, t, seed=4)
        bean(f, cx, H * 0.95, 1.4, (30, 30, 34), BLANCO, "pelo", emo="sorpresa" if t < dur * 0.5 else "aburrido", t=t,
             arms="cara" if t < dur * 0.5 else "jarras")
        img = camera2(b.im, f.im, [(cx, H * 0.60, 1.0), (cx, H * 0.50, 1.6)], t, dur, W, H)
        signs.append(("¿Y AHORA QUÉ?", 0.22, 0.3))
    elif kind == "x_mn_sigue":
        pitch_persp(b, W, H, t, seed=4)
        bean(f, cx, H * 0.95, 1.4, NAR, BLANCO, "pelo", emo="picaro", t=t, arms="relax", arm_r="arriba", num="1")
        ball2(f, cx + 110 * 1.4, H * 0.95 - 1.4 * 420, 36, 0)
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.5)], t, dur, W, H)
        signs.append(("SÍGUENOS", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))
    img = dutch(img, tilt)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
