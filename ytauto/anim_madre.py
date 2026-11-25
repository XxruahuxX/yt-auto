"""Storytime 061 «Mi entrenadora era mi madre»: para que nadie dijera que me enchufaba, nunca me sacaba.
En la final no queda nadie, salgo, marco... y a ella la expulsan por invadir el campo para abrazarme.
Estilo cacahuete (anim_bean). Escenas x_md_*."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, pitch_persp, goal_persp,
                        camera, vignette, confetti, _e, dust, burst, speed_lines, ripple, rain)

YO = dict(body=(46, 120, 210), num="14", skin=BLANCO, hair="pelo", hcol=(40, 30, 26))
MADRE = dict(body=(150, 70, 170), skin=BLANCO, hair="melenon", hcol=(130, 74, 34))
EQ = dict(body=(46, 120, 210), skin=BLANCO)
ARB = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(20, 20, 24), ref=True, legcol=(18, 18, 22))


def banco(c, x, y, w, s=1.0):
    """Banquillo con techo de metacrilato (por delante tapa las piernas)."""
    c.r(x - w / 2, y - 70 * s, x + w / 2, y - 40 * s, 6 * s, (230, 230, 236), INK, 4 * s)
    c.r(x - w / 2, y - 40 * s, x + w / 2, y, 4 * s, (60, 66, 84), INK, 4 * s)


def techo(c, x, y, w, h, s=1.0):
    c.r(x - w / 2 - 20 * s, y - h, x + w / 2 + 20 * s, y - h + 26 * s, 10 * s, (200, 220, 240), INK, 4 * s)
    for sg in (-1, 1):
        c.l([(x + sg * (w / 2 + 6 * s), y - h + 20 * s), (x + sg * (w / 2 + 6 * s), y)], (150, 160, 176), 8 * s)


def pizarra(c, x, y, s=1.0):
    c.r(x - 90 * s, y - 120 * s, x + 90 * s, y, 8 * s, WHITE, INK, 5 * s)
    c.r(x - 80 * s, y - 110 * s, x + 80 * s, y - 10 * s, 4 * s, (60, 150, 80), w=0)
    c.l([(x, y - 110 * s), (x, y - 10 * s)], WHITE, 3 * s)
    for dx, dy in ((-50, -80), (-40, -40), (30, -70), (50, -30)):
        c.c(x + dx * s, y + dy * s, 7 * s, (222, 52, 40), w=0)
    c.l([(x - 40 * s, y - 40 * s), (x + 30 * s, y - 70 * s)], WHITE, 3 * s)


def tarjeta(c, x, y, s, col=(222, 40, 40)):
    c.r(x - 22 * s, y - 34 * s, x + 22 * s, y + 34 * s, 5 * s, col, INK, 4 * s)


def camilla(c, x, y, s, t):
    c.r(x - 150 * s, y - 40 * s, x + 150 * s, y - 20 * s, 6 * s, (240, 240, 244), INK, 4 * s)
    for sg in (-1, 1):
        c.l([(x + sg * 150 * s, y - 30 * s), (x + sg * 190 * s, y - 30 * s)], (120, 120, 130), 8 * s)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img, wet = [], 0, None, False

    if kind == "x_md_madre":
        # mi madre, entrenadora, con la pizarra; yo detrás
        pitch_persp(b, W, H, t, seed=6)
        bean(f, W * 0.78, H * 0.90, 0.8, emo="aburrido", t=t, look=-1, arms="relax", **YO)
        bean(f, W * 0.38, H * 1.02, 1.3, emo="serio", t=t, look=0.4, arms="relax", arm_r="senala", talk=True, **MADRE)
        pizarra(f, W * 0.20, H * 0.80, 1.1)
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.0)], t, dur, W, H)
        signs.append(("MI MADRE", 0.22, 0.2))

    elif kind == "x_md_banquillo":
        # yo solo en el banquillo; la lluvia y el marcador avanzan
        pitch_persp(b, W, H, t, seed=6)
        b.im = b.im.filter(ImageFilter.GaussianBlur(3 * K))
        techo(f, cx, H * 0.97, W * 0.8, 520)
        bean(f, cx, H * 0.97 + 80, 1.2, emo="aburrido", t=t, look=0.3 * math.sin(t * 1.2), arms="relax", **YO)
        banco(f, cx, H * 0.97, W * 0.8, 1.6)
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.05), (cx, H * 0.60, 1.25)], t, dur, W, H)
        signs.append(("BANQUILLO", 0.22, 0.2))
        wet, tilt = True, -3

    elif kind == "x_md_lesion":
        # final: se lesionan; camilla tras camilla
        pitch_persp(b, W, H, t, seed=7, night=True)
        n = 3
        seg = dur / n
        i = min(n - 1, int(t / seg))
        u = (t - i * seg) / seg
        x0 = W * 1.2 - W * 1.5 * u
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        top = H * 0.92 - 40
        bean(tmp, x0, top + 190, 0.9, emo="dolor", t=t, arms="relax", **dict(EQ, hair=["pelo", "tupe", "melena"][i],
                                                                              hcol=(40, 30, 26), num=str(3 + i * 4)))
        f.im.alpha_composite(tmp.im.rotate(90, resample=Image.BICUBIC, center=(x0 * K, (top + 10) * K)))
        camilla(f, x0, H * 0.92 + 30, 1.0, t)
        for sg in (-1, 1):
            bean(f, x0 + sg * 300, H * 0.99, 0.85, (240, 240, 236), BLANCO, "gorra", (30, 30, 30), emo="serio", t=t,
                 look=-1, arms="relax", legs="anda", phase=t * 10)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("SOLO YO", 0.22, dur * 0.67))

    elif kind == "x_md_sal":
        # primer plano de mi madre: suspira y señala el campo
        pitch_persp(b, W, H, t, seed=7, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(8 * K))
        T = dur * 0.5
        bean(f, cx, H * 1.08, 1.6, emo="serio" if t < T else "picaro", t=t, look=0.0,
             arms="relax", arm_r="senala" if t > T else "relax", talk=t > T, **MADRE)
        hx, hy = bean_head(cx, H * 1.08, 1.6)
        img = camera(b.im, f.im, [(hx, hy + 80, 1.15 + 0.08 * t / dur)], t, dur, W, H, blur_close=False)
        if t > T:
            signs.append(("SAL", 0.22, T))
        tilt = 3

    elif kind == "x_md_gol":
        # minuto 90: chuto con los ojos cerrados y entra
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.06, H * 0.70, 0.95)
        T = dur * 0.3
        kick = (t - T) / 0.35 if t > T else None
        bean(f, W * 0.70, H * 0.98, 1.05, emo="cerrados", t=t, look=-0.6, arms="abiertos", kick=kick, kdir=-1, **YO)
        u = _e(min(1.0, max(0.0, (t - T - 0.1) / (dur * 0.4))))
        bx = W * 0.60 - (W * 0.60 - W * 0.18) * u
        by = H * 0.96 - (H * 0.96 - H * 0.60) * u - 120 * math.sin(u * math.pi)
        ball2(f, bx, by, 34 - 12 * u, u * 6)
        if u >= 1:
            ripple(f, bx, by, t, T + 0.1 + dur * 0.4)
            burst(f, "¡GOL!", W * 0.30, H * 0.48, t, T + 0.1 + dur * 0.4, 80)
        f.r(W * 0.56, H * 0.38, W * 0.94, H * 0.46, 10, (20, 22, 34), INK, 4)
        f.text(W * 0.75, H * 0.385, "90'", 70, (255, 214, 40), 3)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.36, H * 0.62, 1.3)], t, dur, W, H,
                     shake=6 if u >= 1 and t - (T + 0.1 + dur * 0.4) < 0.25 else 0)
        tilt = -3

    elif kind == "x_md_invade":
        # mi madre entra corriendo al campo a abrazarme; el árbitro pita
        pitch_persp(b, W, H, t, seed=7, night=True)
        confetti(f, W, H, t, 0.0, n=60)
        u = _e(min(1.0, t / (dur * 0.55)))
        mx = -W * 0.2 + (W * 0.40 + W * 0.2) * u
        bean(f, W * 0.64, H * 0.99, 1.05, emo="feliz" if u < 1 else "sorpresa", t=t, look=-1, arms="arriba", **YO)
        bean(f, mx, H * 1.0, 1.1, emo="feliz", t=t, look=1, arms="abiertos", legs="corre" if u < 1 else "pie",
             phase=t * 16, **MADRE)
        if u < 1:
            speed_lines(f, mx - 80, H * 0.72, t, 0.0, n=8, dur=dur)
        bean(f, W * 0.90, H * 0.86, 0.75, emo="enfado", t=t, look=-1, arms="relax", arm_r="arriba" if u >= 1 else "relax",
             **ARB)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        if u >= 1:
            signs.append(("¡PIII!", 0.22, dur * 0.55))

    elif kind == "x_md_roja":
        # el árbitro le saca la roja a mi madre
        pitch_persp(b, W, H, t, seed=7, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(5 * K))
        T = dur * 0.3
        bean(f, W * 0.70, H * 1.02, 1.25, emo="enfado", t=t, look=-1, arms="relax", arm_r="arriba" if t > T else "relax", **ARB)
        if t > T:
            hx, hy = bean_head(W * 0.70, H * 1.02, 1.25)
            k = _e(min(1.0, (t - T) / 0.25))
            tarjeta(f, W * 0.70 + 150, hy - 230 * k + 120 * (1 - k), 1.6)
        bean(f, W * 0.26, H * 1.02, 1.2, emo="sorpresa" if t > T else "feliz", t=t, look=1, arms="abiertos" if t > T else "relax",
             **MADRE)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.05), (W * 0.62, H * 0.56, 1.3)], t, dur, W, H,
                     shake=5 if 0 < t - T < 0.2 else 0)
        if t > T:
            signs.append(("ROJA", 0.22, T + 0.1))
        tilt = 4

    elif kind == "x_md_cierre":
        # ahora ella grita en la grada con la bufanda; yo juego de titular
        pitch_persp(b, W, H, t, seed=6)
        f.r(-10, H * 0.62, W + 10, H * 0.70, 0, (90, 96, 116), INK, 4)
        bean(f, W * 0.30, H * 0.66, 0.9, emo="feliz", t=t, look=1, talk=True, arms="arriba", **MADRE)
        hx, hy = bean_head(W * 0.30, H * 0.66, 0.9)
        f.r(hx - 60, hy + 54, hx + 60, hy + 74, 8, (46, 120, 210), INK, 3)
        burst(f, "¡VAMOS HIJO!", W * 0.36, H * 0.34, t, 0.4, 52, hold=99)
        bean(f, W * 0.70, H * 1.0, 1.05, emo="picaro", t=t, look=-1, arms="relax", **YO)
        ball2(f, W * 0.56, H * 0.97, 34, t)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("EN LA GRADA", 0.22, dur * 0.4))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
