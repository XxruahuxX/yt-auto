"""22-nov: «¿Por qué el portero lleva el 1?» (x_dz_) y «¿Y si el balón tuviera miedo?» (x_bm_). Estilo cacahuete."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, rain, locker_persp,
                        pitch_persp, goal_persp, camera, vignette, confetti, _e)

AZUL = (40, 100, 210)
NAR = (255, 140, 30)


def ball_face(c, x, y, r, t, emo="miedo", rot=0.3, look=0.0):
    ball2(c, x, y, r, rot)
    c.e(x - r * 0.72, y - r * 0.55, x + r * 0.72, y + r * 0.62, (250, 250, 250), w=0)
    ex, ey, er = r * 0.32, y - r * 0.12, r * 0.22
    for sg in (-1, 1):
        px = x + sg * ex
        if emo == "ko":
            for a in (1, -1):
                c.l([(px - er * 0.7, ey - er * 0.7 * a), (px + er * 0.7, ey + er * 0.7 * a)], INK, r * 0.07)
            continue
        if emo == "guino" and sg > 0:
            c.arc(px - er, ey - er * 0.6, px + er, ey + er * 0.6, 200, 340, INK, r * 0.07)
            continue
        c.c(px, ey, er, WHITE, INK, r * 0.04)
        c.c(px + look * er * 0.4, ey + er * 0.15, er * 0.45, INK, w=0)
        if emo == "miedo":
            c.l([(px - er, ey - er * 1.3 - sg * er * 0.3), (px + er, ey - er * 1.3 + sg * er * 0.3)], INK, r * 0.06)
    my = y + r * 0.35
    if emo == "miedo":
        c.l([(x - r * 0.3 + i * r * 0.1, my + (r * 0.04 if i % 2 else -r * 0.04)) for i in range(7)], INK, r * 0.05)
    elif emo in ("guino", "feliz"):
        c.arc(x - r * 0.28, my - r * 0.2, x + r * 0.28, my + r * 0.12, 20, 160, INK, r * 0.06)
    else:
        c.e(x - r * 0.1, my - r * 0.06, x + r * 0.1, my + r * 0.16, (90, 20, 30), INK, r * 0.03)


def board(c, W, H, n, t):
    """Pizarra en perspectiva con la alineación 2-3-5 numerada desde la portería."""
    q = [(W * 0.10, H * 0.30), (W * 0.90, H * 0.30), (W * 1.02, H * 0.80), (W * -0.02, H * 0.80)]
    c.p([(q[0][0] - 20, q[0][1] - 20), (q[1][0] + 20, q[1][1] - 20), (q[2][0] + 24, q[2][1] + 24), (q[3][0] - 24, q[3][1] + 24)],
        (150, 100, 60), INK, 5)
    c.p(q, (40, 120, 70), INK, 4)
    c.l([(W * 0.06, H * 0.55), (W * 0.94, H * 0.55)], (230, 240, 230), 4)
    rows = [[0.5], [0.33, 0.67], [0.25, 0.5, 0.75], [0.08, 0.29, 0.5, 0.71, 0.92]]
    ys = [0.76, 0.66, 0.53, 0.38]
    k = 0
    for ri, row in enumerate(rows):
        for xx in row:
            k += 1
            if k > n:
                return
            yy = H * ys[ri]
            w = 1 - 0.18 * (0.76 - ys[ri]) / 0.38          # más pequeño al fondo
            px = W * 0.5 + (xx - 0.5) * W * 0.80 * w
            pop = min(1.0, max(0.0, (t * 3.2 - (k - 1) * 0.35)))
            r = 34 * w * (0.6 + 0.4 * pop)
            col = NAR if k == 1 else ((240, 70, 60) if k == 9 else WHITE)
            c.c(px, yy, r, col, INK, 4)
            c.text(px, yy - r * 0.7, str(k), r * 1.15, INK if k not in (1, 9) else WHITE, 0)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, wet = [], 0, False
    if kind == "x_dz_portero":
        pitch_persp(b, W, H, t, seed=3)
        goal_persp(f, W * 0.08, H * 0.80, 1.2)
        bean(f, cx + 40, H * 0.86, 1.3, NAR, BLANCO, "pelo", emo="serio", t=t, arms="jarras", num="1")
        hx, hy = bean_head(cx + 40, H * 0.86, 1.3)
        img = camera(b.im, f.im, [(cx, H * 0.56, 1.0), (cx + 40, hy + 200, 1.7)], t, dur, W, H)
        signs.append(("Nº 1", 0.22, 0.3))
    elif kind == "x_dz_pizarra":
        locker_persp(b, W, H, t)
        board(f, W, H, 11, t)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0 + 0.08 * t / dur)], t, dur, W, H)
        signs.append(("1939", 0.22, 0.3))
    elif kind == "x_dz_nueve":
        pitch_persp(b, W, H, t, seed=6)
        board(f, W, H, 11, 99)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0), (cx, H * 0.40, 2.0)], t, dur, W, H)
        signs.append(("EL 9 = 9º", 0.22, dur * 0.5))
    elif kind == "x_dz_cola":
        pitch_persp(b, W, H, t, seed=3)
        bean(f, W * 0.30, H * 0.92, 1.1, NAR, BLANCO, "pelo", emo="aburrido", t=t, num="1")
        bean(f, W * 0.72, H * 0.92, 1.1, (240, 70, 60), BLANCO, "tupe", (30, 24, 30), emo="feliz", t=t, num="9", arms="arriba")
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.0), (W * 0.30, H * 0.55, 1.6)], t, dur, W, H)
        signs.append(("SÍGUENOS", 0.22, 0.4))

    elif kind == "x_bm_huye":
        pitch_persp(b, W, H, t, seed=4)
        run = t / dur
        bean(f, W * 0.25 + 120 * run, H * 0.92, 1.1, AZUL, BLANCO, "pelo", emo="sorpresa", t=t, legs="corre", phase=t * 12, num="9")
        bx = W * 0.55 + 260 * run
        ball_face(f, bx, H * 0.88 - abs(math.sin(t * 9)) * 60, 70, t, "miedo", rot=-t * 6)
        img = camera(b.im, f.im, [(cx + 60, H * 0.70, 1.2), (bx, H * 0.80, 2.2)], t, dur, W, H)
        signs.append(("HUYE", 0.22, dur * 0.5))
    elif kind == "x_bm_portero":
        pitch_persp(b, W, H, t, seed=4)
        goal_persp(f, W * 0.10, H * 0.84, 1.2)
        peek = 0.5 + 0.5 * math.sin(t * 2)
        ball_face(f, W * 0.62 + 60 * peek, H * 0.78, 60, t, "miedo", look=1)
        bean(f, W * 0.56, H * 0.90, 1.3, NAR, BLANCO, "pelo", emo="sorpresa", t=t, arms="abiertos", num="1", look=1)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.62, H * 0.62, 1.7)], t, dur, W, H)
    elif kind == "x_bm_penalti":
        pitch_persp(b, W, H, t, seed=4, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(8 * K))
        f.e(W * 0.24, H * 0.735, W * 0.76, H * 0.785, (235, 238, 235), INK, 4)
        sh = 4 * math.sin(t * 40)
        ball_face(f, cx + sh, H * 0.62, 200, t, "miedo", look=0.3 * math.sin(t * 3))
        img = camera(b.im, f.im, [(cx, H * 0.56, 1.0 + 0.12 * t / dur)], t, dur, W, H, blur_close=False)
        wet, tilt = True, 3 * math.sin(t * 1.4)
        signs.append(("PENALTI", 0.22, 0.3))
    elif kind == "x_bm_gol":
        pitch_persp(b, W, H, t, seed=4)
        goal_persp(f, W * 0.10, H * 0.84, 1.2)
        u = _e(t / (dur * 0.4))
        emo = "miedo" if u < 1 else "ko"
        ball_face(f, W * 0.80 - (W * 0.80 - W * 0.28) * u, H * 0.92 - (H * 0.92 - H * 0.66) * u - 120 * math.sin(u * math.pi),
                  60 - 15 * u, t, emo, rot=u * 8)
        if u >= 1:
            confetti(f, W, H, t, dur * 0.4)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0), (W * 0.30, H * 0.62, 1.8)], t, dur, W, H, shake=8 if 0.4 * dur < t < 0.5 * dur else 0)
        if u >= 1:
            signs.append(("GOL", 0.22, dur * 0.4))
    elif kind == "x_bm_sigue":
        pitch_persp(b, W, H, t, seed=4)
        ball_face(f, cx, H * 0.62, 180, t, "guino" if (t % 2) > 1 else "feliz", rot=0.3)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0)], t, dur, W, H)
        signs.append(("SÍGUENOS", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))
    img = dutch(img, tilt)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
