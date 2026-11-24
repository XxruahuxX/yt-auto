"""24-nov. Storytime «El Adivino» (x_cl_: celebraba los goles antes de que entraran) y
«¿Por qué el área tiene una media luna?» (x_ml_). Estilo cacahuete (anim_bean).
Mejora del día: derrape celebrando con estela de polvo (slide_dust)."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, ball_fx, ripple, sign, dutch, rain,
                        locker_persp, pitch_persp, goal_persp, camera, camera2, vignette, confetti, _e, dust, burst,
                        speed_lines, shade)
from .anim_apagon import focos, glow, dark

AZUL = (40, 100, 210)
YO = dict(body=AZUL, skin=BLANCO, hair="tupe", hcol=(40, 30, 26), num="11")
COMP = [dict(body=AZUL, skin=BLANCO, hair=h, hcol=c, num=n) for h, c, n in
        (("pelo", (60, 40, 30), "4"), ("gorra", (40, 30, 26), "8"), ("melena", (200, 160, 80), "6"))]
GK = dict(body=(255, 140, 30), skin=BLANCO, hair="pelo", hcol=(30, 26, 24), num="1")
REF = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(20, 20, 24), num="", ref=True, legcol=(18, 18, 22))


def slide_dust(c, xs, y, t, s=1.0):
    """Estela de polvo detrás de un derrape: xs = posiciones x pasadas (más antigua primero)."""
    n = len(xs)
    for i, x in enumerate(xs):
        k = (i + 1) / n
        r = (10 + 22 * (1 - k)) * s
        a = int(200 * k)
        c.c(x, y - 10 * s - 14 * (1 - k) * s, r, (236, 228, 214, a), (60, 52, 46, a), 2)


def _proj(X, Y, W, H):
    """Campo visto desde detrás del área (metros). Y=0 línea de gol (arriba), Y crece hacia la cámara."""
    d = max(1.5, 45.0 - Y)
    return W / 2 + X * 560.0 / d, 30.5 + 29634.0 / d


def penalty_area(c, W, H, t, arc_k=1.0, hl=0.0, circle=0.0):
    """Área grande, pequeña, punto de penalti y media luna en perspectiva. hl = brillo del arco."""
    P = lambda X, Y: _proj(X, Y, W, H)
    c.p([(0, 0), (W, 0), (W, H * 0.40), (0, H * 0.40)], (44, 48, 70), w=0)        # grada al fondo
    rnd = __import__("random").Random(5)
    for i in range(260):
        x, y = rnd.uniform(0, W), rnd.uniform(H * 0.02, H * 0.36)
        c.c(x, y, 5, rnd.choice([(200, 46, 44), (240, 240, 236), (40, 100, 210), (250, 205, 40)]), w=0)
    c.p([(0, H * 0.375), (W, H * 0.375), (W, H * 0.40), (0, H * 0.40)], (200, 46, 44), w=0)
    c.p([(0, H * 0.40), (W, H * 0.40), (W, H), (0, H)], (70, 160, 80), w=0)
    for i in range(7):                                   # franjas de césped
        y0, y1 = -4 + i * 4.5, -4 + i * 4.5 + 2.25
        a, b2 = P(-60, y0), P(60, y0)
        c2_, d2 = P(60, y1), P(-60, y1)
        c.p([a, b2, c2_, d2], (78, 172, 88), w=0)
    lw = 6
    c.l([P(-40, 0), P(40, 0)], WHITE, lw)                                         # línea de gol
    c.l([P(-20.16, 0), P(-20.16, 16.5), P(20.16, 16.5), P(20.16, 0)], WHITE, lw)  # área grande
    c.l([P(-9.16, 0), P(-9.16, 5.5), P(9.16, 5.5), P(9.16, 0)], WHITE, lw)        # área pequeña
    sx, sy = P(0, 11)
    c.c(sx, sy, 7, WHITE, w=0)
    # media luna: arco de radio 9,15 alrededor del punto, solo fuera del área
    pts = []
    a0 = math.acos(5.5 / 9.15)
    n = 40
    for i in range(n + 1):
        th = -a0 + 2 * a0 * i / n
        if i / n <= arc_k:
            pts.append(P(9.15 * math.sin(th), 11 + 9.15 * math.cos(th)))
    if len(pts) > 1:
        if hl > 0:
            c.l(pts, (255, 214, 40, int(200 * hl)), lw + 14)
        c.l(pts, WHITE, lw)
    if circle > 0:                                       # círculo completo de 9,15 m que se dibuja
        cp = []
        for i in range(int(72 * circle) + 1):
            th = i * 2 * math.pi / 72
            cp.append(P(9.15 * math.sin(th), 11 + 9.15 * math.cos(th)))
        if len(cp) > 1:
            c.l(cp, (255, 214, 40), 5)
    # portería al fondo
    gl, gr = P(-3.66, 0), P(3.66, 0)
    h = (gr[0] - gl[0]) * 0.33
    c.l([gl, (gl[0], gl[1] - h), (gr[0], gr[1] - h), gr], WHITE, 9)
    c.l([gl, (gl[0], gl[1] - h), (gr[0], gr[1] - h), gr], INK, 2)
    return P


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, wet, darkk, img = [], 0, False, 0.0, None

    # ------------------------------------------------------------ storytime «El Adivino»
    if kind == "x_cl_sinmirar":
        pitch_persp(b, W, H, t, seed=2)
        goal_persp(f, W * 0.08, H * 0.70, 0.9)
        T = dur * 0.30
        kick = (t - T * 0.4) / (T * 0.9) if t < T * 1.4 else None
        cel = t > T + 0.2
        px, py = W * 0.70, H * 0.95
        bean(f, px, py, 1.0, emo="feliz" if cel else "serio", t=t, kick=kick, kdir=-1,
             arms="arriba" if cel else "relax", look=0.8 if cel else -0.6, **YO)
        T0, T1 = T, T + dur * 0.45
        def bpos(tt):
            u = _e(max(0.0, min(1.0, (tt - T0) / (T1 - T0))))
            return (W * 0.62 - (W * 0.62 - W * 0.24) * u, H * 0.94 - (H * 0.94 - H * 0.60) * u - 180 * math.sin(u * math.pi)), u
        (bx, by), u = bpos(t)
        if 0 < u < 1:
            ball_fx(f, [bpos(t - k * 0.04)[0] for k in range(5, 0, -1)] + [(bx, by)], 30 - 10 * u, ground=H * 0.93 - (H * 0.93 - H * 0.69) * u)
        ball2(f, bx, by, 30 - 10 * u, t * 9)
        ripple(f, W * 0.24, H * 0.60, t, T1)
        hx, hy = bean_head(px, py, 1.0)
        img = camera2(b.im, f.im, [(px - 40, H * 0.72, 1.5), (cx, H * 0.62, 1.0)], t, dur, W, H)
        if cel:
            signs.append(("SIN MIRAR", 0.22, T + 0.2))

    elif kind == "x_cl_risas":
        locker_persp(b, W, H, t)
        for i, (xx, kw) in enumerate(zip((0.20, 0.50, 0.80), COMP)):
            bean(f, W * xx, H * 0.86, 0.95, emo="feliz", t=t, talk=(t * 2 + i * 0.3) % 1 < 0.5,
                 arms="relax", arm_r="senala" if i == 1 else "relax", blink_off=i * 0.7, look=0.5 - i * 0.4, **kw)
        img = camera2(b.im, f.im, [(cx, H * 0.58, 1.0), (W * 0.50, H * 0.55, 1.6)], t, dur, W, H)
        signs.append(("EL ADIVINO", 0.22, dur * 0.4))
        tilt = 0 if t < dur / 2 else 4

    elif kind == "x_cl_final":
        pitch_persp(b, W, H, t, seed=7, night=True)
        focos(f, W, H, 1, t)
        bean(f, cx, H * 1.02, 1.45, emo="serio", t=t, look=-0.3, **YO)
        ball2(f, cx - 150, H * 0.99, 46, 0.4)
        hx, hy = bean_head(cx, H * 1.02, 1.45)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0 + 0.12 * t / dur)], t, dur, W, H)
        img = glow(img, [(W * 0.06, H * 0.035), (W * 0.94, H * 0.035)], 1.0, t)
        signs.append(("MINUTO 90", 0.22, 0.3))
        wet, tilt = True, 3

    elif kind == "x_cl_chuto":
        pitch_persp(b, W, H, t, seed=7, night=True)
        T = dur * 0.30
        kick = (t - T * 0.3) / (T * 0.8) if t < T * 1.2 else None
        cel = t > T + 0.15
        bean(f, cx + 60, H * 1.0, 1.35, emo="feliz" if cel else "serio", t=t, kick=kick, kdir=-1,
             arms="arriba" if cel else "relax", talk=cel, look=0.5 if cel else -0.7, **YO)
        u = _e(max(0.0, min(1.0, (t - T) / 0.45)))
        if u < 1:
            ball2(f, cx - 40 - 500 * u, H * 0.98 - 420 * u, 44 - 26 * u, u * 8)
        speed_lines(f, cx - 40, H * 0.97, t, T, n=12, r0=60, r1=170)
        img = camera(b.im, f.im, [(cx + 40, H * 0.66, 1.25)], t, dur, W, H, shake=6 if cel and t < T + 0.4 else 0)
        if cel:
            signs.append(("¡GOOOL!", 0.22, T + 0.15))
        wet = True

    elif kind == "x_cl_poste":
        pitch_persp(b, W, H, t, seed=7, night=True)
        gx = W * 0.10
        goal_persp(f, gx, H * 0.72, 1.1)
        T = dur * 0.25                                   # golpea el palo
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        dive = _e(min(1.0, t / (dur * 0.25)))
        kx, ky = W * 0.48 + 120 * dive, H * 0.72 - 60 * math.sin(dive * math.pi)
        bean(tmp, kx, ky, 0.7, emo="miedo", t=t, arms="arriba", legs="abiertas", **GK)
        f.im.alpha_composite(tmp.im.rotate(-70 * dive, resample=Image.BICUBIC, center=(kx * K, (ky - 160) * K)))
        post = (W * 0.13, H * 0.58)
        if t < T:
            u = _e(t / T)
            bx, by = W * 0.70 - (W * 0.70 - post[0]) * u, H * 0.80 - (H * 0.80 - post[1]) * u
        else:
            v = min(1.0, (t - T) / (dur * 0.6))
            bx, by = post[0] + (W * 0.44 - post[0]) * v, post[1] + (H * 0.90 - post[1]) * v - 120 * math.sin(v * math.pi)
        ball2(f, bx, by, 26, t * 8)
        burst(f, "¡CLONK!", W * 0.30, H * 0.48, t, T, 44, col=(255, 255, 255))
        img = camera(b.im, f.im, [(W * 0.34, H * 0.62, 1.35)], t, dur, W, H, shake=10 if 0 < t - T < 0.3 else 0)
        if t > T:
            signs.append(("AL PALO", 0.22, T + 0.3))
        wet, tilt = True, -5

    elif kind == "x_cl_solo":
        pitch_persp(b, W, H, t, seed=7, night=True)
        # compañeros al fondo con las manos en la cabeza
        for i, (xx, kw) in enumerate(zip((0.18, 0.40, 0.84), COMP)):
            bean(f, W * xx, H * 0.70, 0.55, emo="miedo", t=t, arms="cara", blink_off=i, **kw)
        u = _e(min(1.0, t / (dur * 0.75)))
        px = W * 0.90 - W * 0.42 * u
        xs = [W * 0.90 - W * 0.42 * _e(min(1.0, max(0.0, (t - k * 0.06) / (dur * 0.75)))) for k in range(10, 0, -1)]
        slide_dust(f, xs, H * 0.97, t, 1.1)
        bean(f, px, H * 0.97, 1.15, emo="feliz", t=t, arms="arriba", legs="abiertas", talk=True, look=0.6, **YO)
        img = camera(b.im, f.im, [(px, H * 0.66, 1.2)], t, dur, W, H)
        darkk = 0.35
        signs.append(("SOLO", 0.22, dur * 0.35))
        wet, tilt = True, 4

    elif kind == "x_cl_tacon":
        pitch_persp(b, W, H, t, seed=7, night=True)
        gx = W * 0.10
        goal_persp(f, gx, H * 0.72, 1.1)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        bean(tmp, W * 0.30, H * 0.80, 0.7, emo="dolor", t=t, arms="arriba", legs="abiertas", **GK)
        f.im.alpha_composite(tmp.im.rotate(70, resample=Image.BICUBIC, center=(W * 0.30 * K, (H * 0.80 - 160) * K)))
        T = dur * 0.35                                   # el rebote me da en el tacón
        px = W * 0.60
        bean(f, px, H * 0.96, 1.0, emo="feliz" if t < T else "sorpresa", t=t, arms="arriba", legs="abiertas", look=0.8, **YO)
        heel = (px - 40, H * 0.95)
        if t < T:
            u = t / T
            bx, by = W * 0.14 + (heel[0] - W * 0.14) * u, H * 0.80 + (heel[1] - H * 0.80) * u
        else:
            v = _e(min(1.0, (t - T) / (dur * 0.45)))
            bx, by = heel[0] + (W * 0.22 - heel[0]) * v, heel[1] + (H * 0.66 - heel[1]) * v
        ball2(f, bx, by, 28, t * 5)
        burst(f, "¡TOC!", heel[0] - 60, heel[1] - 150, t, T, 38, col=(255, 255, 255))
        T2 = T + dur * 0.45
        ripple(f, W * 0.22, H * 0.64, t, T2)
        img = camera(b.im, f.im, [(W * 0.40, H * 0.70, 1.25)], t, dur, W, H, shake=8 if 0 < t - T2 < 0.25 else 0)
        if t > T2:
            signs.append(("GOL", 0.22, T2))
            confetti(f, W, H, t, T2)
        wet = True

    elif kind == "x_cl_arbitro":
        pitch_persp(b, W, H, t, seed=7, night=True)
        T = dur * 0.35
        bean(f, cx, H * 1.05, 1.5, emo="serio", t=t, talk=T < t < dur * 0.7, arms="relax",
             arm_r="senala" if t > T else "relax", look=0.2, **REF)
        hx, hy = bean_head(cx, H * 1.05, 1.5)
        img = camera(b.im, f.im, [(hx, hy + 120, 1.2)], t, dur, W, H)
        if t > T:
            signs.append(("VALE", 0.22, T))
        wet, tilt = True, -4

    elif kind == "x_cl_entreno":
        pitch_persp(b, W, H, t, seed=2)
        goal_persp(f, W * 0.08, H * 0.70, 0.8)
        for i, (xx, kw) in enumerate(zip((0.40, 0.62, 0.84), [YO] + COMP[:2])):
            bean(f, W * xx, H * 0.95, 0.85, emo="feliz", t=t, arms="arriba", blink_off=i, look=0.6, **kw)
        u = _e(min(1.0, t / (dur * 0.6)))
        ball2(f, W * 0.30 - W * 0.45 * u, H * 0.92 - H * 0.40 * u, 26 - 8 * u, t * 9)
        img = camera(b.im, f.im, [(cx, H * 0.66, 1.15)], t, dur, W, H)
        signs.append(("ÚLTIMOS", 0.22, dur * 0.45))

    # ------------------------------------------------------------ ¿Por qué la media luna?
    elif kind == "x_ml_area":
        P = penalty_area(b, W, H, t, arc_k=1.0, hl=0.5 + 0.5 * math.sin(t * 5))
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0 + 0.15 * t / dur)], t, dur, W, H)
        signs.append(("¿Y ESTO?", 0.22, 0.2))

    elif kind == "x_ml_distancia":
        P = penalty_area(b, W, H, t, arc_k=0.0, circle=_e(min(1.0, t / (dur * 0.7))))
        sx, sy = P(0, 11)
        ex, ey = P(0, 16.5)
        f.l([(sx, sy), (ex, ey)], (222, 52, 40), 7)
        f.r(ex + 14, (sy + ey) / 2 - 26, ex + 150, (sy + ey) / 2 + 26, 10, WHITE, INK, 3)
        f.text(ex + 82, (sy + ey) / 2 - 24, "5,5 m", 38, (222, 52, 40), 0)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.1)], t, dur, W, H)
        signs.append(("MUY CERCA", 0.22, dur * 0.5))

    elif kind == "x_ml_jugadores":
        P = penalty_area(b, W, H, t, arc_k=1.0, hl=0.6)
        sx, sy = P(0, 11)
        bean(f, sx + 30, sy + 10, 15.0 / 34, (200, 46, 44), BLANCO, "pelo", emo="serio", t=t, num="9", look=-0.2)
        ball2(f, sx, sy, 10, 0.3)
        for i, X in enumerate((-16, -8, 0, 8, 16)):
            Y = 11 + 9.6 if abs(X) < 9 else 17.5
            Y = max(Y, 11 + math.sqrt(max(0.0, 9.6 ** 2 - X ** 2)))
            x, y = P(X, Y)
            sc = 15.0 / (45 - Y)
            bean(f, x, y, sc, (40, 100, 210) if i % 2 else (200, 46, 44), BLANCO, ["pelo", "gorra", "melena", "tupe", "pelo"][i],
                 emo="serio", t=t, num=str(3 + i), blink_off=i)
        img = camera(b.im, f.im, [(cx, H * 0.60, 1.25)], t, dur, W, H)
        signs.append(("A 9,15 M", 0.22, 0.4))

    elif kind == "x_ml_1937":
        P = penalty_area(b, W, H, t, arc_k=_e(min(1.0, t / (dur * 0.6))), hl=0.8)
        b.im = b.im.filter(ImageFilter.GaussianBlur(2 * K))
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.15)], t, dur, W, H)
        signs.append(("1937", 0.22, 0.3))

    elif kind == "x_ml_cola":
        P = penalty_area(b, W, H, t, arc_k=1.0, hl=0.4)
        x, y = P(0, 19)
        bean(f, x, y + 260, 1.3, (255, 140, 30), BLANCO, "pelo", emo="picaro", t=t, num="1", arms="relax", arm_r="senala",
             look=-0.4)
        img = camera(b.im, f.im, [(cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("SÍGUENOS", 0.22, dur * 0.5))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    if darkk:
        img = dark(img, darkk, t, phones=False)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
