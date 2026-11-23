"""Storytime 050 «Mi abuela entrenadora»: se rieron de mí porque mi entrenadora era mi abuela.
Estilo cacahuete + mejora del día: ciclo de andar con balanceo de brazos (legs/arms="anda")."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, ball_fx, ripple, sign, dutch, rain,
                        locker_persp, pitch_persp, goal_persp, camera2, vignette, confetti, _e)
from .anim_dia22 import board

AZUL, ROJO, LILA = (40, 100, 210), (200, 50, 45), (150, 90, 170)
YO = dict(body=AZUL, skin=BLANCO, hair="pelo", hcol=(40, 30, 26), num="7")


def abuela(c, x, y, s, t, emo="aburrido", arms="relax", arm_r=None, talk=False, legs="pie", phase=0.0, agujas=False):
    bean(c, x, y, s, LILA, BLANCO, "melena", (200, 200, 210), emo=emo, t=t, arms=arms, arm_r=arm_r, talk=talk,
         legs=legs, phase=phase, legcol=(70, 60, 80))
    hx, hy = bean_head(x, y, s)
    # moño y gafas
    c.c(hx, hy - 64 * s * 1.05, 22 * s, (200, 200, 210), INK, 4 * s)
    for sg in (-1, 1):
        c.c(hx + sg * 24 * s, hy + 2 * s, 17 * s, None, INK, 4 * s)
    c.l([(hx - 7 * s, hy), (hx + 7 * s, hy)], INK, 4 * s)
    if agujas:
        # ovillo y agujas de punto delante del pecho
        bx, by = x, y - 150 * s - 200 * s * 0.42 + 30 * s
        c.c(bx, by + 20 * s, 30 * s, (220, 60, 80), INK, 4 * s)
        for k in range(3):
            c.arc(bx - 26 * s, by - 6 * s + k * 12 * s, bx + 26 * s, by + 40 * s + k * 4 * s, 200, 340, (160, 30, 50), 3 * s)
        w = 10 * math.sin(t * 9)
        c.l([(bx - 60 * s, by - 40 * s + w), (bx + 10 * s, by + 10 * s)], (190, 160, 110), 6 * s)
        c.l([(bx + 60 * s, by - 40 * s - w), (bx - 10 * s, by + 10 * s)], (190, 160, 110), 6 * s)


def silla(c, x, y, s):
    c.l([(x - 50 * s, y), (x + 40 * s, y - 120 * s)], (120, 120, 130), 7 * s)
    c.l([(x + 50 * s, y), (x - 40 * s, y - 120 * s)], (120, 120, 130), 7 * s)
    c.r(x - 60 * s, y - 130 * s, x + 60 * s, y - 112 * s, 5 * s, (60, 120, 80), INK, 3 * s)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, wet = [], 0, False
    if kind == "x_ya_llega":
        # mi abuela llega andando al campo; los rivales se ríen
        pitch_persp(b, W, H, t, seed=2)
        for i, xx in enumerate((0.16, 0.34)):
            bean(f, W * xx, H * 0.78, 0.75, ROJO, BLANCO, ["tupe", "pelo"][i], (30, 24, 30), emo="feliz", t=t,
                 talk=(t * 2 + i) % 1 < 0.5, arms="relax", arm_r="senala" if i == 0 else None, num=str(9 + i))
        ax = W * 1.05 - W * 0.40 * min(1.0, t / (dur * 0.75))
        abuela(f, ax, H * 0.95, 1.05, t, legs="anda" if t < dur * 0.75 else "pie", arms="anda" if t < dur * 0.75 else "relax",
               phase=t * 7)
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.55, H * 0.66, 1.3)], t, dur, W, H)
        signs.append(("JA JA JA", 0.22, dur * 0.5))
    elif kind == "x_ya_cafe":
        pitch_persp(b, W, H, t, seed=2)
        silla(f, W * 0.48, H * 0.95, 1.4)
        abuela(f, cx, H * 0.93, 1.35, t, arms="relax", arm_r="taza")
        hx, hy = bean_head(cx, H * 0.93, 1.35)
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.15), (hx + 20, hy + 90, 1.8)], t, dur, W, H)
        signs.append(("78 AÑOS", 0.22, 0.3))
    elif kind == "x_ya_derrotas":
        pitch_persp(b, W, H, t, seed=6)
        bean(f, cx, H * 0.95, 1.4, emo="aburrido", t=t, **YO)
        n = min(5, 1 + int(t / (dur / 5)))
        img = camera2(b.im, f.im, [(cx, H * 0.62, 1.2)], t, dur, W, H)
        signs.append((f"0 - {n}", 0.22, 0.2))
        wet = True
    elif kind == "x_ya_descanso":
        locker_persp(b, W, H, t)
        for i, xx in enumerate((0.20, 0.50, 0.80)):
            bean(f, W * xx, H * 0.95, 0.95, AZUL, BLANCO, ["pelo", "melena", "gorra"][i], (50, 34, 20), emo="miedo" if i != 1 else "aburrido",
                 t=t, num=str([7, 4, 10][i]), blink_off=i)
        img = camera2(b.im, f.im, [(cx, H * 0.60, 1.0), (W * 0.50, H * 0.55, 1.6)], t, dur, W, H)
        signs.append(("0 - 2", 0.22, 0.3))
        tilt = -3
    elif kind == "x_ya_pizarra":
        locker_persp(b, W, H, t)
        board(f, W, H, 11, t * 2)
        abuela(f, W * 0.80, H * 1.02, 1.2, t, arms="relax", agujas=True, talk=(t * 2) % 1 < 0.6)
        hx, hy = bean_head(W * 0.80, H * 1.02, 1.2)
        img = camera2(b.im, f.im, [(cx, H * 0.58, 1.0), (hx - 40, hy + 110, 1.7)], t, dur, W, H)
        signs.append(("PUNTO", 0.22, dur * 0.4))
    elif kind == "x_ya_tejer":
        pitch_persp(b, W, H, t, seed=2)
        abuela(f, cx, H * 1.0, 1.6, t, emo="serio", agujas=True, talk=True)
        hx, hy = bean_head(cx, H * 1.0, 1.6)
        img = camera2(b.im, f.im, [(hx, hy + 140, 1.6)], t, dur, W, H)
        signs.append(("EL HILO", 0.22, dur * 0.45))
    elif kind == "x_ya_pases":
        # pases cortos uno-dos entre dos jugadores, el rival persigue sin tocarla
        pitch_persp(b, W, H, t, seed=4)
        p1, p2 = (W * 0.24, H * 0.92), (W * 0.76, H * 0.90)
        k = (t * 1.6) % 1.0
        leg = int(t * 1.6) % 2
        a, c2 = (p1, p2) if leg == 0 else (p2, p1)
        bean(f, *p1, 0.95, num="7", emo="serio", t=t, kick=min(1.0, k * 3) if leg == 0 and k < 0.33 else None, kdir=1,
             **{k_: v for k_, v in YO.items() if k_ != "num"})
        bean(f, *p2, 0.95, AZUL, BLANCO, "melena", (50, 34, 20), num="4", emo="serio", t=t,
             kick=min(1.0, k * 3) if leg == 1 and k < 0.33 else None, kdir=-1)
        u = _e(max(0.0, (k - 0.2) / 0.7))
        pos = lambda uu: (a[0] + (c2[0] - a[0]) * uu + (40 if leg == 0 else -40), a[1] - 10 + (c2[1] - a[1]) * uu)
        bx, by = pos(u)
        rx = W * 0.5 + (bx - W * 0.5) * 0.6
        bean(f, rx, H * 0.80, 0.8, ROJO, BLANCO, "tupe", (30, 24, 30), emo="miedo", t=t, legs="corre", phase=t * 14, num="9")
        if 0 < u < 1:
            ball_fx(f, [pos(max(0, u - j * 0.05)) for j in range(5, 0, -1)] + [(bx, by)], 26, ground=by + 6)
        ball2(f, bx, by, 26, t * 9)
        img = camera2(b.im, f.im, [(cx, H * 0.74, 1.35)], t, dur, W, H)
        signs.append(("UNO, DOS", 0.22, 0.2))
    elif kind == "x_ya_gol":
        pitch_persp(b, W, H, t, seed=4)
        goal_persp(f, W * 0.08, H * 0.74, 1.0)
        T = dur * 0.25
        kick = t / T
        bean(f, W * 0.72, H * 0.96, 1.05, emo="serio" if kick < 1 else "feliz", t=t, kick=kick, kdir=-1,
             arms="arriba" if kick > 2 else "relax", **YO)
        u = _e(max(0.0, (t - T * 0.6) / (dur * 0.3)))
        pos = lambda uu: (W * 0.64 - (W * 0.64 - W * 0.20) * uu, H * 0.95 - (H * 0.95 - H * 0.62) * uu - 200 * math.sin(uu * math.pi))
        bx, by = pos(u)
        if 0 < u < 1:
            ball_fx(f, [pos(max(0, u - j * 0.04)) for j in range(5, 0, -1)] + [(bx, by)], 30 - 10 * u, ground=H * 0.95 - (H * 0.95 - H * 0.73) * u)
        ball2(f, bx, by, 30 - 10 * u, t * 9)
        tg = T * 0.6 + dur * 0.3
        ripple(f, W * 0.20, H * 0.62, t, tg)
        if t > tg:
            confetti(f, W, H, t, tg)
        img = camera2(b.im, f.im, [(W * 0.60, H * 0.72, 1.4), (W * 0.40, H * 0.64, 1.15)], t, dur, W, H,
                      shake=10 if 0 < t - tg < 0.25 else 0)
        if t > tg:
            signs.append(("3 - 2", 0.22, tg))
    elif kind == "x_ya_final":
        pitch_persp(b, W, H, t, seed=2)
        abuela(f, W * 0.62, H * 0.96, 1.25, t, emo="picaro", arms="relax", arm_r="taza")
        for i, xx in enumerate((0.16, 0.34)):
            bean(f, W * xx, H * 0.86, 0.8, ROJO, BLANCO, ["tupe", "pelo"][i], (30, 24, 30), emo="miedo", t=t,
                 num=str(9 + i), arms="cara" if i == 0 else "relax")
        img = camera2(b.im, f.im, [(cx, H * 0.64, 1.0), (W * 0.62, H * 0.56, 1.6)], t, dur, W, H)
        signs.append(("LA YAYA", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))
    img = dutch(img, tilt)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
