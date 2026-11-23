"""Storytime 051 «Mi hermano gemelo»: portero contra su gemelo delantero en la final; el tic de la oreja.
Estilo cacahuete (anim_bean). Escenas x_gm_*."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, bean, bean_head, ball2, sign, dutch, rain, pitch_persp, goal_persp,
                        camera, camera2, vignette, confetti, _e, dust, burst, speed_lines)

NAR = (255, 140, 30)
ROJ = (200, 46, 44)
PELO = dict(skin=BLANCO, hair="pelo", hcol=(40, 30, 26))
YO = dict(body=NAR, num="1", **PELO)
HNO = dict(body=ROJ, num="9", **PELO)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, wet, img = [], 0, False, None

    if kind == "x_gm_gemelos":
        # los dos, cara a cara en el centro del campo; misma cara, distinta camiseta
        pitch_persp(b, W, H, t, seed=4, night=True)
        bean(f, W * 0.28, H * 0.95, 1.15, emo="serio", t=t, look=1, arms="jarras", **YO)
        bean(f, W * 0.72, H * 0.95, 1.15, emo="picaro", t=t, look=-1, arms="relax", blink_off=0.4, **HNO)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0), (cx, H * 0.62, 1.25)], t, dur, W, H)
        signs.append(("GEMELOS", 0.22, 0.3))
        tilt = 0 if t < dur / 2 else -4

    elif kind == "x_gm_oreja":
        # flashback: los dos de pequeños; él se toca la oreja y chuta a la derecha
        pitch_persp(b, W, H, t, seed=2)
        b.im = b.im.filter(ImageFilter.GaussianBlur(3 * K))
        goal_persp(f, W * 0.08, H * 0.70, 0.75)
        T = dur * 0.55
        bean(f, W * 0.24, H * 0.74, 0.55, (230, 200, 90), emo="miedo", t=t, arms="abiertos", legs="abiertas", **PELO)
        kick = (t - T) / 0.35 if t > T else None
        bean(f, W * 0.66, H * 0.95, 0.85, (90, 150, 220), emo="serio", t=t, look=-0.6,
             arms="relax", arm_r="oreja" if t < T else "relax", kick=kick, kdir=-1, **PELO)
        u = _e((t - T - 0.12) / 0.45)
        ball2(f, W * 0.58 - (W * 0.58 - W * 0.14) * u, H * 0.94 - (H * 0.94 - H * 0.62) * u - 90 * math.sin(u * math.pi),
              28 - 8 * u, u * 8)
        hx, hy = bean_head(W * 0.66, H * 0.95, 0.85)
        img = camera(b.im, f.im, [(hx - 30, hy + 50, 1.9), (cx, H * 0.70, 1.15)], t, dur, W, H)
        signs.append(("LA OREJA", 0.22, 0.4))
        if u >= 1:
            signs.append(("DERECHA", 0.29, T + 0.6))
        img = Image.blend(img, Image.new("RGB", img.size, (235, 210, 160)), 0.18)   # tono de recuerdo

    elif kind == "x_gm_secreto":
        # yo, primer plano, dedo en la boca (mano a la cara)
        pitch_persp(b, W, H, t, seed=4, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(8 * K))
        bean(f, cx, H * 1.08, 1.6, emo="picaro", t=t, arms="relax", arm_r="cara", **YO)
        hx, hy = bean_head(cx, H * 1.08, 1.6)
        img = camera(b.im, f.im, [(hx, hy + 70, 1.15 + 0.1 * t / dur)], t, dur, W, H, blur_close=False)
        signs.append(("SECRETO", 0.22, 0.3))
        tilt = 3

    elif kind == "x_gm_penaltis":
        # marcador 0-0 bajo la lluvia, porterías vacías
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.10, H * 0.68, 0.95)
        f.r(W * 0.56, H * 0.46, W * 0.94, H * 0.56, 12, (20, 22, 34), INK, 5)
        f.text(W * 0.75, H * 0.465, "0 - 0", 92, (255, 214, 40), 4)
        img = camera(b.im, f.im, [(W * 0.75, H * 0.52, 1.7), (cx, H * 0.58, 1.0)], t, dur, W, H)
        signs.append(("PENALTIS", 0.22, dur * 0.5))
        wet, tilt = True, -5

    elif kind == "x_gm_ultimo":
        # balón en el punto, él detrás; tensión
        pitch_persp(b, W, H, t, seed=7, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(7 * K))
        bean(f, W * 0.66, H * 0.84, 1.0, emo="serio", t=t, look=-0.3, **HNO)
        f.e(W * 0.12, H * 0.885, W * 0.62, H * 0.93, (235, 238, 235), INK, 4)
        ball2(f, W * 0.37, H * 0.80, 120, 0.3)
        img = camera(b.im, f.im, [(W * 0.45, H * 0.62, 1.0 + 0.12 * t / dur)], t, dur, W, H, blur_close=False)
        signs.append(("ÚLTIMO", 0.22, 0.3))
        wet, tilt = True, 3 * math.sin(t * 1.3)

    elif kind == "x_gm_mira":
        # contraplano: él me mira y se toca la oreja; yo lo veo
        pitch_persp(b, W, H, t, seed=7, night=True)
        half = dur * 0.5
        if t < half:
            bean(f, cx, H * 1.05, 1.55, emo="serio", t=t, look=-0.2,
                 arms="relax", arm_r="oreja" if t > half * 0.45 else "relax", **HNO)
            hx, hy = bean_head(cx, H * 1.05, 1.55)
            img = camera(b.im, f.im, [(hx, hy + 70, 1.2)], t, half, W, H)
            if t > half * 0.45:
                signs.append(("LA OREJA", 0.22, half * 0.45))
        else:
            goal_persp(f, W * 0.04, H * 0.92, 1.6)
            bean(f, cx, H * 1.02, 1.3, emo="sorpresa", t=t, arms="abiertos", legs="abiertas", look=0.0, **YO)
            hx, hy = bean_head(cx, H * 1.02, 1.3)
            img = camera(b.im, f.im, [(hx, hy + 80, 1.3)], t - half, dur - half, W, H)
            signs.append(("DERECHA", 0.22, half + 0.3))
        wet, tilt = True, (-5 if t < half else 5)

    elif kind == "x_gm_pica":
        # me tiro a la derecha; él la pica por el centro, despacio
        pitch_persp(b, W, H, t, seed=7, night=True)
        gx = W * 0.16
        goal_persp(f, W * 0.08, H * 0.72, 0.95)
        T0, TL = dur * 0.18, dur * 0.48
        dive = _e((t - T0) / (dur * 0.26))
        kx, ky = W * 0.30 - 150 * dive, H * 0.72 - 70 * math.sin(dive * math.pi)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        bean(tmp, kx, ky, 0.62, emo="miedo" if dive < 0.9 else "dolor", t=t, arms="arriba", legs="abiertas", **YO)
        f.im.alpha_composite(tmp.im.rotate(70 * dive, resample=Image.BICUBIC, center=(kx * K, (ky - 150) * K)))
        dust(f, kx - 20, H * 0.735, t, T0 + dur * 0.26, s=0.6)
        burst(f, "¡PUM!", W * 0.14, H * 0.55, t, T0 + dur * 0.26, 34, col=(255, 255, 255))
        u = (t - T0 - 0.1) / (dur * 0.55)
        u = max(0.0, min(1.0, u))
        bx = W * 0.62 - (W * 0.62 - W * 0.30) * u
        by = H * 0.95 - (H * 0.95 - H * 0.60) * u - 300 * math.sin(u * math.pi)
        ball2(f, bx, by, 32 - 12 * u, u * 3)
        bean(f, W * 0.80, H * 1.02, 1.0, emo="serio" if u < 1 else "feliz", t=t,
             arms="relax" if u < 1 else "arriba", **HNO)
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.0), (W * 0.36, H * 0.64, 1.5)], t, dur, W, H,
                     shake=6 if 0 < t - (T0 + dur * 0.26) < 0.25 else 0)
        if u >= 1:
            signs.append(("GOL", 0.22, T0 + 0.1 + dur * 0.55))
        wet, tilt = True, -3

    elif kind == "x_gm_abrazo":
        # me abraza y me lo cuenta al oído
        pitch_persp(b, W, H, t, seed=7, night=True)
        confetti(f, W, H, t, 0.0)
        bean(f, W * 0.40, H * 1.0, 1.35, emo="sorpresa" if t > dur * 0.35 else "aburrido",
             t=t, look=0.6, arms="relax", **YO)
        bean(f, W * 0.66, H * 1.0, 1.35, emo="picaro", t=t, look=-1, talk=t < dur * 0.7, arms="relax",
             arm_r="arriba", **HNO)
        a, c2 = bean_head(W * 0.40, H * 1.0, 1.35), bean_head(W * 0.66, H * 1.0, 1.35)
        img = camera(b.im, f.im, [((a[0] + c2[0]) / 2, a[1] + 90, 1.35), ((a[0] + c2[0]) / 2, a[1] + 70, 1.6)], t, dur, W, H)
        signs.append(("DESDE LOS 8", 0.22, dur * 0.35))
        tilt = 4

    elif kind == "x_gm_cierre":
        # ahora soy yo el que se toca la oreja
        pitch_persp(b, W, H, t, seed=2)
        goal_persp(f, W * 0.08, H * 0.70, 0.75)
        bean(f, W * 0.24, H * 0.74, 0.55, emo="miedo", t=t, arms="abiertos", legs="abiertas", **HNO)
        bean(f, W * 0.68, H * 0.98, 1.2, emo="picaro", t=t, look=-0.4,
             arms="relax", arm_r="oreja" if t > dur * 0.3 else "relax", **YO)
        ball2(f, W * 0.52, H * 0.96, 30, 0.2)
        hx, hy = bean_head(W * 0.68, H * 0.98, 1.2)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0), (hx - 20, hy + 60, 1.8)], t, dur, W, H)
        signs.append(("MI TURNO", 0.22, dur * 0.45))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
