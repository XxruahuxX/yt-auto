"""Storytime 062 «El Reglamento»: se reían de mí por saberme el reglamento de memoria; en la final, dos reglas
reales nos dan la copa (no hay fuera de juego en un saque de banda y el gol olímpico, directo de córner).
Movimiento fluido: nadie se queda quieto (respira, se balancea, mira), la cámara se desliza entre encuadres
con suavizado en lugar de cortar, y el balón deja estela. Escenas x_rg_*."""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, ball_fx, sign, dutch, pitch_persp,
                        goal_persp, locker_persp, camera, vignette, confetti, _e, dust, burst, speed_lines, ripple)

YO = dict(body=(46, 120, 210), num="4", skin=BLANCO, hair="pelo", hcol=(40, 30, 26), gafas=True)
EQ = [dict(body=(46, 120, 210), skin=BLANCO, hair=h, hcol=c, num=n)
      for h, c, n in (("tupe", (20, 20, 24), "9"), ("melena", (120, 70, 30), "7"), ("gorra", (30, 30, 30), "10"))]
RIV = [dict(body=(200, 46, 44), skin=BLANCO, hair=h, hcol=(30, 24, 20), num=n)
       for h, n in (("pelo", "5"), ("tupe", "3"), ("melena", "6"), ("pelo", "2"))]
ARB = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(20, 20, 24), ref=True, legcol=(18, 18, 22))
SEPIA = (235, 210, 160)


def ease(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def glide(keys, t):
    """Cámara suave: interpola (tiempo, x, y, zoom) con suavizado; nunca corta."""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t <= t1:
            k = ease((t - t0) / max(1e-6, t1 - t0))
            return tuple(u + (v - u) * k for u, v in zip(a, b))
    return keys[-1][1:]


def shot(b, f, keys, t, dur, W, H, **kw):
    x, y, z = glide(keys, t)
    kw.setdefault("blur_close", False)
    kw.setdefault("flash", False)
    return camera(b.im, f.im, [(x, y, z)], 0.0, 1.0, W, H, **kw)


def alive(c, x, y, s, t, ph=0.0, sway=1.0, **kw):
    """Personaje vivo: balanceo lateral, respiración y mirada que va y viene (todo continuo)."""
    dx = math.sin(1.6 * t + ph) * 6 * s * sway
    kw.setdefault("look", 0.6 * math.sin(1.1 * t + ph))
    bean(c, x + dx, y, s, t=t + ph, **kw)
    return x + dx


def arc_ball(p0, p1, h, u):
    x = p0[0] + (p1[0] - p0[0]) * u
    y = p0[1] + (p1[1] - p0[1]) * u - h * math.sin(u * math.pi)
    return x, y


def trail(f, p0, p1, h, u, r, curve=0.0):
    pts = []
    for j in range(7):
        uu = max(0.0, u - 0.035 * (6 - j))
        x, y = arc_ball(p0, p1, h, uu)
        pts.append((x + curve * math.sin(uu * math.pi), y))
    ball_fx(f, pts, r)
    return pts[-1]


def libro(c, x, y, s, t):
    """Reglamento: libro amarillo abierto con páginas que pasan."""
    c.r(x - 70 * s, y - 50 * s, x + 70 * s, y + 40 * s, 6 * s, (250, 206, 40), INK, 4 * s)
    c.r(x - 62 * s, y - 42 * s, x - 4 * s, y + 32 * s, 3 * s, WHITE, INK, 2 * s)
    c.r(x + 4 * s, y - 42 * s, x + 62 * s, y + 32 * s, 3 * s, WHITE, INK, 2 * s)
    for j in range(4):
        c.l([(x - 54 * s, y - 28 * s + j * 16 * s), (x - 12 * s, y - 28 * s + j * 16 * s)], (150, 150, 160), 3 * s)
        c.l([(x + 12 * s, y - 28 * s + j * 16 * s), (x + 54 * s, y - 28 * s + j * 16 * s)], (150, 150, 160), 3 * s)
    k = (t * 0.8) % 1
    px = x + 58 * s * math.cos(k * math.pi)
    c.p([(x, y - 42 * s), (px, y - 42 * s - 10 * s * math.sin(k * math.pi)), (px, y + 32 * s), (x, y + 32 * s)],
        (245, 245, 245), INK, 2 * s)


def dato(img, txt, t, t0, W, H):
    """Rótulo de dato real: banda amarilla con «DATO REAL» que entra deslizando desde la izquierda."""
    if t < t0:
        return img
    k = ease((t - t0) / 0.35)
    lay = C((W, H), "RGBA", (0, 0, 0, 0))
    x0 = -W + W * k
    y = H * 0.30
    lay.r(x0 + 24, y, x0 + W - 24, y + 170, 18, (255, 214, 40), INK, 5)
    lay.r(x0 + 60, y - 28, x0 + 290, y + 22, 10, (222, 52, 40), INK, 4)
    lay.text(x0 + 175, y - 26, "DATO REAL", 36, WHITE, 0)
    lines = txt.split("|")
    for j, ln in enumerate(lines):
        lay.text(x0 + W / 2, y + 32 + j * 62, ln, 54, INK, 0)
    l = lay.im.resize(img.size, Image.LANCZOS)
    img = img.copy()
    img.paste(l, (0, 0), l)
    return img


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img, datos = [], 0, None, []

    if kind == "x_rg_empollon":
        # yo en el banquillo leyendo el reglamento; la cámara se acerca despacio
        pitch_persp(b, W, H, t, seed=6)
        b.im = b.im.filter(ImageFilter.GaussianBlur(3 * K))
        alive(f, cx, H * 1.0, 1.35, t, arms="relax", arm_r="taza" if False else "relax", emo="picaro", **YO)
        hx, hy = bean_head(cx, H * 1.0, 1.35)
        libro(f, cx, hy + 250 + 6 * math.sin(t * 2), 1.5, t)
        img = shot(b, f, [(0, cx, H * 0.66, 1.0), (dur, cx, H * 0.58, 1.25)], t, dur, W, H)
        signs.append(("EL EMPOLLÓN", 0.22, 0.3))

    elif kind == "x_rg_once":
        # dato: el penalti a 11 metros = 12 yardas; un balón rueda hasta el punto
        pitch_persp(b, W, H, t, seed=6)
        goal_persp(f, W * 0.08, H * 0.70, 0.95)
        u = ease(t / (dur * 0.5))
        ball2(f, W * 0.95 - (W * 0.95 - W * 0.46) * u, H * 0.90, 36, u * 9)
        f.e(W * 0.44, H * 0.90 - 6, W * 0.48, H * 0.90 + 6, WHITE, w=0)
        if t > dur * 0.45:
            k = ease((t - dur * 0.45) / 0.5)
            f.l([(W * 0.46, H * 0.86), (W * 0.46 - (W * 0.46 - W * 0.18) * k, H * 0.86 - (H * 0.86 - H * 0.70) * k)], (255, 214, 40), 6)
        alive(f, W * 0.82, H * 1.02, 1.05, t, arms="relax", arm_r="senala", emo="picaro", talk=True, **YO)
        img = shot(b, f, [(0, cx, H * 0.64, 1.0), (dur, W * 0.45, H * 0.66, 1.12)], t, dur, W, H)
        datos.append(("Penalti: 11 metros|porque antes eran 12 yardas", dur * 0.35))

    elif kind == "x_rg_risas":
        # mis compañeros se ríen; todos se mueven sin parar
        locker_persp(b, W, H, t)
        for j, (xx, ss) in enumerate(((0.16, 0.95), (0.84, 0.95), (0.50, 0.85))):
            alive(f, W * xx, H * (0.90 if ss < 0.9 else 0.97), ss, t, ph=j * 1.3, sway=2.0, emo="feliz", talk=True,
                  arms="arriba" if j != 2 else "jarras", blink_off=j * 0.3, **EQ[j])
        alive(f, cx, H * 1.08, 1.3, t, ph=2.0, arms="relax", emo="aburrido", **YO)
        img = shot(b, f, [(0, cx, H * 0.60, 1.0), (dur, cx, H * 0.64, 1.15)], t, dur, W, H)
        signs.append(("EMPOLLÓN", 0.22, 0.3))

    elif kind == "x_rg_final":
        # final 0-1, minuto 88; marcador y cámara que baja hasta el campo
        pitch_persp(b, W, H, t, seed=7, night=True)
        f.r(W * 0.20, H * 0.30, W * 0.80, H * 0.40, 12, (20, 22, 34), INK, 5)
        f.text(cx, H * 0.305, "0 - 1", 100, (255, 214, 40), 4)
        f.text(cx, H * 0.415, "88'", 60, WHITE, 3)
        for j in range(3):
            alive(f, W * (0.2 + 0.3 * j), H * 0.95, 0.85, t, ph=j, emo="miedo" if j == 1 else "serio", arms="relax",
                  **(YO if j == 1 else EQ[j]))
        img = shot(b, f, [(0, cx, H * 0.38, 1.3), (dur * 0.7, cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("LA FINAL", 0.22, 0.2))

    elif kind == "x_rg_banda":
        # saque de banda: la defensa sube para dejarme en fuera de juego... pero no existe en un saque de banda
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.04, H * 0.66, 0.8)
        T = dur * 0.35
        k = ease((t - 0.2) / (dur * 0.3))
        for j in range(4):
            x = W * (0.30 + 0.15 * j) + W * 0.22 * k
            bean(f, x, H * (0.80 + 0.025 * j), 0.78, legs="corre" if 0 < k < 1 else "pie", phase=t * 14 + j,
                 arms="abiertos" if k >= 1 else "anda", t=t + j, look=1, emo="picaro", **RIV[j])
        bean(f, W * 0.28, H * 0.86, 0.85, emo="sorpresa" if k >= 1 else "serio", t=t, look=-1, arms="relax", **YO)
        # balón del saque, en arco hacia mí
        u = ease((t - T) / (dur * 0.35))
        if t > T:
            trail(f, (W * 0.98, H * 0.70), (W * 0.30, H * 0.80), 160, u, 26)
        img = shot(b, f, [(0, W * 0.55, H * 0.66, 1.0), (dur, W * 0.40, H * 0.68, 1.1)], t, dur, W, H)
        datos.append(("En un saque de banda|no hay fuera de juego", dur * 0.55))

    elif kind == "x_rg_empate":
        # me quedo solo y marco: 1-1; carrera continua con estela
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.06, H * 0.72, 1.0)
        T = dur * 0.4
        run = ease(t / T)
        px = W * 0.85 - W * 0.30 * run
        kick = (t - T) / 0.35 if t > T else None
        bean(f, px, H * 0.98, 1.0, legs="corre" if run < 1 else "pie", phase=t * 15, arms="anda" if run < 1 else "abiertos",
             kick=kick, kdir=-1, t=t, emo="serio", look=-1, **YO)
        if t <= T:
            ball2(f, px - 70, H * 0.96, 30, t * 10)
        else:
            u = ease((t - T - 0.1) / (dur * 0.3))
            x, y = trail(f, (px - 70, H * 0.96), (W * 0.18, H * 0.62), 90, u, 30)
            ball2(f, x, y, 30 - 10 * u, u * 8)
            if u >= 1:
                ripple(f, x, y, t, T + 0.1 + dur * 0.3)
                burst(f, "1 - 1", W * 0.36, H * 0.46, t, T + 0.1 + dur * 0.3, 80)
        img = shot(b, f, [(0, W * 0.65, H * 0.66, 1.1), (dur, W * 0.40, H * 0.64, 1.2)], t, dur, W, H,
                   shake=5 if 0 < t - (T + 0.1 + dur * 0.3) < 0.2 else 0)

    elif kind == "x_rg_corner":
        # minuto 90, córner; todos me gritan que centre
        pitch_persp(b, W, H, t, seed=7, night=True)
        f.l([(W * 0.92, H * 0.66), (W * 0.92, H * 0.56)], (220, 220, 220), 5)
        f.p([(W * 0.92, H * 0.56), (W * 0.98, H * 0.58), (W * 0.92, H * 0.60)], (255, 214, 40), INK, 2)
        ball2(f, W * 0.86, H * 0.97, 30, 0)
        for j in range(3):
            alive(f, W * (0.12 + 0.2 * j), H * 0.80, 0.7, t, ph=j * 0.9, sway=2.5, emo="enfado", talk=True,
                  arms="arriba", **EQ[j])
        alive(f, W * 0.74, H * 1.04, 1.2, t, ph=0.4, arms="relax", arm_r="cara", emo="serio", look=-0.5, **YO)
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, W * 0.62, H * 0.66, 1.2)], t, dur, W, H)
        signs.append(("¡CENTRA!", 0.22, 0.2))
        tilt = -3 * math.sin(t * 0.8)

    elif kind == "x_rg_1924":
        # flashback en sepia: 1924, Argentina - Uruguay, el primer gol olímpico (directo de córner)
        pitch_persp(b, W, H, t, seed=2)
        f.l([(W * 0.94, H * 0.70), (W * 0.94, H * 0.60)], (220, 220, 220), 5)
        goal_persp(f, W * 0.04, H * 0.68, 0.8)
        u = ease((t - 0.4) / (dur * 0.55))
        bean(f, W * 0.90, H * 0.80, 0.75, (120, 176, 226), BLANCO, "pelo", (30, 24, 20), emo="serio", t=t, look=-1,
             kick=(t - 0.1) / 0.35 if t > 0.1 else None, kdir=-1)
        x, y = trail(f, (W * 0.88, H * 0.79), (W * 0.18, H * 0.58), 200, u, 24, curve=-60)
        ball2(f, x, y, 24, u * 6)
        if u >= 1:
            ripple(f, x, y, t, 0.4 + dur * 0.55)
        img = shot(b, f, [(0, W * 0.70, H * 0.66, 1.1), (dur, W * 0.38, H * 0.62, 1.1)], t, dur, W, H)
        img = Image.blend(img.convert("L").convert("RGB"), Image.new("RGB", img.size, SEPIA), 0.35)
        signs.append(("1924", 0.22, 0.2))
        datos.append(("Primer gol olímpico: 1924,|directo de córner a Uruguay", dur * 0.3))

    elif kind == "x_rg_olimpico":
        # chuto directo de córner: el balón hace la curva y entra por el primer palo
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.04, H * 0.68, 0.9)
        T = dur * 0.2
        kick = (t - T) / 0.35 if t > T else None
        bean(f, W * 0.86, H * 0.98, 1.0, emo="serio", t=t, look=-1, kick=kick, kdir=-1, arms="abiertos", **YO)
        for j in range(3):
            alive(f, W * (0.26 + 0.16 * j), H * 0.74, 0.62, t, ph=j, sway=1.5, emo="sorpresa", arms="abiertos", **RIV[j])
        u = ease((t - T - 0.1) / (dur * 0.5))
        if t > T:
            x, y = trail(f, (W * 0.80, H * 0.96), (W * 0.14, H * 0.58), 260, u, 30, curve=-90)
            ball2(f, x, y, 30 - 10 * u, u * 10)
            if u >= 1:
                ripple(f, x, y, t, T + 0.1 + dur * 0.5)
                burst(f, "¡GOL!", W * 0.34, H * 0.45, t, T + 0.1 + dur * 0.5, 86)
        img = shot(b, f, [(0, W * 0.70, H * 0.68, 1.15), (T + dur * 0.25, W * 0.45, H * 0.62, 1.0),
                          (dur, W * 0.32, H * 0.60, 1.2)], t, dur, W, H,
                   shake=6 if 0 < t - (T + 0.1 + dur * 0.5) < 0.25 else 0)

    elif kind == "x_rg_vale":
        # protestan «¡no vale!»; el árbitro lo mira y señala el centro
        pitch_persp(b, W, H, t, seed=7, night=True)
        b.im = b.im.filter(ImageFilter.GaussianBlur(4 * K))
        T = dur * 0.5
        for j in range(2):
            alive(f, W * (0.18 + 0.2 * j), H * 0.98, 0.95, t, ph=j, sway=2.5, emo="enfado", talk=t < T, arms="abiertos", **RIV[j])
        alive(f, W * 0.72, H * 1.02, 1.15, t, ph=1.0, emo="serio", arms="relax", arm_r="senala" if t > T else "relax",
              look=-0.3, **ARB)
        img = shot(b, f, [(0, W * 0.40, H * 0.64, 1.05), (dur, W * 0.62, H * 0.60, 1.2)], t, dur, W, H)
        signs.append(("¡NO VALE!", 0.22, 0.2))
        if t > T:
            signs.append(("VALE", 0.29, T))

    elif kind == "x_rg_cierre":
        # campeones; me mantean y el reglamento vuela; ahora me llaman el Reglamento
        pitch_persp(b, W, H, t, seed=7, night=True)
        confetti(f, W, H, t, 0.0)
        for j in range(3):
            alive(f, W * (0.25 + 0.25 * j), H * 1.0, 0.95, t, ph=j * 0.7, sway=1.5, emo="feliz", arms="arriba", **EQ[j])
        up = abs(math.sin(t * 2.4)) * 160
        bean(f, cx, H * 0.80 - up, 0.95, emo="feliz", t=t, arms="arriba", legs="abiertas", **YO)
        libro(f, cx + 170, H * 0.50 - up * 0.6, 0.9, t)
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, cx, H * 0.56, 1.1)], t, dur, W, H)
        signs.append(("EL REGLAMENTO", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    img = vignette(img, 0.28)
    for txt, t0 in datos:
        img = dato(img, txt, t, t0, W, H)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
