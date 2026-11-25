"""Serie «Así se inventó…» (fútbol). Ep. 1: las tarjetas (Ken Aston, Mundial 1966, el semáforo; estreno en
México 1970). Humor con un solo protagonista y datos reales. Movimiento fluido con las herramientas de
anim_reglamento (cámara que se desliza, personajes siempre vivos). Escenas x_iv_*."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, pitch_persp, camera, vignette,
                        confetti, _e, burst, speed_lines, dust)
from .anim_reglamento import shot, alive, ease, dato

ARB = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(20, 20, 24), ref=True, legcol=(18, 18, 22))
KEN = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(170, 170, 170), ref=True, legcol=(18, 18, 22))
JUG = dict(body=(120, 176, 226), skin=BLANCO, hair="pelo", hcol=(30, 24, 20), num="10")
AMA, ROJ = (255, 214, 40), (222, 40, 40)


def bocadillo(c, x, y, txt, size=54, t=0.0, t0=0.0):
    """Bocadillo de cómic que aparece con un pequeño rebote."""
    if t < t0:
        return
    k = ease((t - t0) / 0.25)
    s = 0.6 + 0.4 * k + 0.06 * math.sin(min(1.0, (t - t0) / 0.4) * math.pi)
    w, h = (len(txt) * size * 0.62 + 50) * s, size * 1.6 * s
    c.r(x - w / 2, y - h, x + w / 2, y, 24 * s, WHITE, INK, 5)
    c.p([(x - 20 * s, y - 4), (x + 10 * s, y - 4), (x - 30 * s, y + 34 * s)], WHITE, INK, 5)
    c.r(x - 18 * s, y - 10, x + 8 * s, y + 2, 0, WHITE, w=0)
    c.text(x, y - h + 10 * s, txt, size * s, INK, 0)


def tarjeta(c, x, y, s, col, ang=0.0):
    w, h = 44 * s, 66 * s
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    c.p([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], col, INK, 4 * s)


def ciudad(c, W, H, off, night=False):
    """Calle de Londres en scroll lateral: edificios de ladrillo, farolas y acera."""
    c.r(-10, -10, W + 10, H * 0.62, 0, (70, 80, 120) if night else (180, 200, 220), w=0)
    rnd = random.Random(3)
    blocks = []
    x = 0
    while x < W * 4:
        w = rnd.uniform(160, 260)
        blocks.append((x, w, rnd.uniform(H * 0.22, H * 0.40), rnd.choice([(170, 80, 60), (150, 90, 70), (196, 170, 140), (120, 110, 120)])))
        x += w
    span = x
    for bx, w, h, col in blocks:
        xx = (bx - off) % span - 200
        if xx > W + 10 or xx + w < -10:
            continue
        c.r(xx, H * 0.62 - h, xx + w, H * 0.62, 0, col, INK, 3)
        for yy in range(int(H * 0.62 - h + 24), int(H * 0.58), 54):
            for wx in range(int(xx + 18), int(xx + w - 30), 44):
                c.r(wx, yy, wx + 24, yy + 34, 2, (255, 226, 140) if night and (wx + yy) % 3 == 0 else (110, 140, 170), INK, 2)
    c.r(-10, H * 0.62, W + 10, H * 0.68, 0, (160, 160, 166), INK, 3)
    c.r(-10, H * 0.68, W + 10, H + 10, 0, (70, 72, 80), w=0)
    for i in range(-1, 8):
        xx = (i * 220 - off * 1.4) % (220 * 8) - 220
        c.r(xx, H * 0.83, xx + 110, H * 0.845, 0, WHITE, w=0)


def coche(c, x, y, s, t, moving=True, driver=None):
    """Coche clásico de lado con conductor; las ruedas giran y la carrocería vibra."""
    bob = math.sin(t * 22) * 2 * s if moving else 0
    yy = y + bob
    drv = (x + 10 * s, yy + 23 * s, 0.55 * s)
    c.r(x - 170 * s, yy - 150 * s, x + 170 * s, yy - 40 * s, 40 * s, (40, 90, 60), INK, 5 * s)
    c.r(x - 80 * s, yy - 230 * s, x + 90 * s, yy - 140 * s, 30 * s, (40, 90, 60), INK, 5 * s)
    c.r(x - 62 * s, yy - 216 * s, x + 72 * s, yy - 150 * s, 18 * s, (190, 220, 240), INK, 3 * s)
    if driver:   # el conductor se ve por la ventanilla (solo de cintura para arriba)
        tmp = C((c.im.size[0] // K, c.im.size[1] // K), "RGBA", (0, 0, 0, 0))
        bean(tmp, *drv, t=t, arms="relax", **driver)
        cut = int((yy - 150 * s) * K)
        tmp.im.paste((0, 0, 0, 0), (0, cut, tmp.im.size[0], tmp.im.size[1]))
        c.im.alpha_composite(tmp.im)
        c.r(x - 170 * s, yy - 150 * s, x + 170 * s, yy - 40 * s, 40 * s, (40, 90, 60), INK, 5 * s)
        c.r(x - 62 * s, yy - 216 * s, x + 72 * s, yy - 150 * s, 18 * s, None, INK, 3 * s)
    c.c(x + 160 * s, yy - 110 * s, 14 * s, (255, 236, 150), INK, 3 * s)
    for dx in (-100, 100):
        c.c(x + dx * s, y - 30 * s, 42 * s, (30, 30, 34), INK, 4 * s)
        c.c(x + dx * s, y - 30 * s, 18 * s, (190, 190, 196), INK, 3 * s)
        a = -t * 14 if moving else 0
        c.l([(x + dx * s, y - 30 * s), (x + dx * s + math.cos(a) * 18 * s, y - 30 * s + math.sin(a) * 18 * s)], INK, 4 * s)


def semaforo(c, x, y, s, luz):
    c.r(x - 8 * s, y - 40 * s, x + 8 * s, y + 380 * s, 4 * s, (50, 54, 64), INK, 3 * s)
    c.r(x - 50 * s, y - 210 * s, x + 50 * s, y, 16 * s, (36, 38, 46), INK, 5 * s)
    for i, (col, on) in enumerate((((222, 40, 40), luz == "rojo"), ((255, 190, 30), luz == "ambar"), ((60, 200, 90), luz == "verde"))):
        cy = y - 175 * s + i * 66 * s
        if on:
            c.c(x, cy, 44 * s, col + (90,), w=0)
        c.c(x, cy, 26 * s, col if on else tuple(v // 4 for v in col), INK, 3 * s)


def bombilla(c, x, y, s, t):
    k = 0.5 + 0.5 * math.sin(t * 8)
    c.c(x, y, 60 * s, (255, 236, 120, int(60 + 60 * k)), w=0)
    c.c(x, y, 32 * s, (255, 236, 120), INK, 4 * s)
    c.r(x - 14 * s, y + 26 * s, x + 14 * s, y + 46 * s, 3 * s, (170, 170, 176), INK, 3 * s)
    for i in range(8):
        a = i / 8 * 2 * math.pi + t
        c.l([(x + math.cos(a) * 44 * s, y + math.sin(a) * 44 * s), (x + math.cos(a) * 62 * s, y + math.sin(a) * 62 * s)],
            (255, 214, 40), 4 * s)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img, datos = [], 0, None, []

    if kind == "x_iv_gancho":
        # árbitro sin tarjetas buscando en los bolsillos; el jugador se encoge de hombros
        pitch_persp(b, W, H, t, seed=5)
        alive(f, W * 0.30, H * 1.0, 1.15, t, emo="enfado", talk=True, arms="jarras", **ARB)
        alive(f, W * 0.74, H * 0.97, 1.0, t, ph=1.5, sway=2.0, emo="picaro", arms="abiertos", look=-0.6, **JUG)
        bocadillo(f, W * 0.30, H * 0.45, "¿Y las tarjetas?", 50, t, 0.3)
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, W * 0.42, H * 0.60, 1.15)], t, dur, W, H)
        signs.append(("ASÍ NACIERON", 0.22, 0.2))

    elif kind == "x_iv_palabra":
        # 1966: te expulsaban de palabra; el árbitro grita y señala
        pitch_persp(b, W, H, t, seed=5, night=False)
        alive(f, W * 0.32, H * 1.02, 1.2, t, emo="enfado", talk=True, arms="relax", arm_r="senala", **ARB)
        alive(f, W * 0.76, H * 0.96, 0.95, t, ph=1.0, sway=1.5, emo="serio", arms="jarras", look=-0.4, **JUG)
        bocadillo(f, W * 0.36, H * 0.46, "¡FUERA!", 70, t, dur * 0.35)
        img = shot(b, f, [(0, cx, H * 0.60, 1.05), (dur, W * 0.38, H * 0.62, 1.2)], t, dur, W, H)
        signs.append(("MUNDIAL 1966", 0.22, 0.2))

    elif kind == "x_iv_idioma":
        # no se entienden: interrogaciones, mímica cada vez más exagerada
        pitch_persp(b, W, H, t, seed=5)
        sw = math.sin(t * 3.2)
        alive(f, W * 0.30, H * 1.02, 1.15, t, emo="enfado", talk=True, arms="abiertos", **ARB)
        alive(f, W * 0.74, H * 0.98, 1.05, t, ph=0.8, sway=2.5, emo="sorpresa", arms="abiertos", look=-0.6, **JUG)
        bocadillo(f, W * 0.30, H * 0.47, "#$%&!", 60, t, 0.2)
        bocadillo(f, W * 0.72, H * 0.52, "¿Qué?", 60, t, dur * 0.4)
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, cx, H * 0.60, 1.12)], t, dur, W, H)
        tilt = 3 * math.sin(t * 1.5)

    elif kind == "x_iv_minutos":
        # el jugador no se va: reloj que corre y él sentado en el césped
        pitch_persp(b, W, H, t, seed=5)
        alive(f, W * 0.26, H * 1.0, 1.0, t, emo="aburrido", arms="jarras", **ARB)
        alive(f, W * 0.70, H * 0.98, 1.0, t, ph=0.6, emo="picaro", arms="relax", look=-0.3, **JUG)
        f.c(W * 0.70, H * 0.36, 90, WHITE, INK, 6)
        a = -math.pi / 2 + t * 4
        f.l([(W * 0.70, H * 0.36), (W * 0.70 + math.cos(a) * 70, H * 0.36 + math.sin(a) * 70)], ROJ, 7)
        f.l([(W * 0.70, H * 0.36), (W * 0.70 + math.cos(a / 12) * 45, H * 0.36 + math.sin(a / 12) * 45)], INK, 8)
        img = shot(b, f, [(0, cx, H * 0.58, 1.0), (dur, W * 0.62, H * 0.52, 1.15)], t, dur, W, H)
        signs.append(("MINUTOS", 0.22, 0.2))

    elif kind == "x_iv_coche":
        # Ken Aston vuelve a casa en coche por Londres, pensativo (scroll continuo)
        ciudad(b, W, H, t * 260)
        coche(f, cx, H * 0.86, 1.25, t, True, dict(KEN, emo="serio", look=0.3))
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, cx, H * 0.66, 1.1)], t, dur, W, H)
        signs.append(("KEN ASTON", 0.22, 0.3))

    elif kind == "x_iv_semaforo":
        # el coche frena; ámbar... rojo; se enciende la bombilla
        T1, T2 = dur * 0.30, dur * 0.60
        stop = ease(t / T1)
        off = 260 * (t - 0.5 * T1 * stop * stop / max(stop, 1e-6)) if False else 260 * T1 * (1 - (1 - stop) ** 2) / 2
        ciudad(b, W, H, off, night=True)
        luz = "ambar" if t < T2 else "rojo"
        semaforo(f, W * 0.80, H * 0.40, 1.1, luz)
        coche(f, W * 0.42, H * 0.86, 1.25, t, stop < 1, dict(KEN, emo="sorpresa" if t > T2 else "serio", look=0.8))
        if t > T2 + 0.3:
            hx = W * 0.42 + 10 * 1.25
            bombilla(f, hx, H * 0.86 - 400, 1.1, t)
        img = shot(b, f, [(0, W * 0.50, H * 0.64, 1.0), (dur, W * 0.58, H * 0.58, 1.18)], t, dur, W, H)
        signs.append(("ÁMBAR" if t < T2 else "ROJO", 0.22, 0.2 if t < T2 else T2))

    elif kind == "x_iv_idea":
        # Ken con una tarjeta en cada mano: amarilla «cuidado», roja «fuera»
        pitch_persp(b, W, H, t, seed=6)
        b.im = b.im.filter(ImageFilter.GaussianBlur(4 * K))
        alive(f, cx, H * 1.04, 1.4, t, emo="picaro", arms="arriba", **KEN)
        hx, hy = bean_head(cx, H * 1.04, 1.4)
        wob = math.sin(t * 3) * 6
        tarjeta(f, cx - 168, hy - 210 + 8 * math.sin(t * 12), 2.2, AMA, wob)
        tarjeta(f, cx + 168, hy - 210 + 8 * math.sin(t * 12 + 1), 2.2, ROJ, -wob)
        img = shot(b, f, [(0, cx, H * 0.60, 1.0), (dur, cx, H * 0.56, 1.12)], t, dur, W, H)
        datos.append(("Amarilla: cuidado.|Roja: fuera del campo.", dur * 0.3))

    elif kind == "x_iv_1970":
        # estreno en el Mundial de México 1970: el árbitro saca la primera amarilla; la grada lo celebra
        pitch_persp(b, W, H, t, seed=8)
        T = dur * 0.3
        alive(f, W * 0.34, H * 1.0, 1.15, t, emo="serio", arms="relax", arm_r="arriba" if t > T else "relax", **ARB)
        if t > T:
            hx, hy = bean_head(W * 0.34, H * 1.0, 1.15)
            k = ease((t - T) / 0.25)
            tarjeta(f, W * 0.34 + 138, hy - 230 * k + 140 * (1 - k), 1.8, AMA)
        alive(f, W * 0.76, H * 0.97, 1.0, t, ph=1.2, emo="sorpresa" if t > T else "serio", arms="relax", look=-0.5, **JUG)
        img = shot(b, f, [(0, cx, H * 0.62, 1.0), (dur, W * 0.44, H * 0.56, 1.2)], t, dur, W, H)
        signs.append(("MÉXICO 1970", 0.22, 0.2))
        datos.append(("Las tarjetas se estrenaron|en el Mundial de 1970", dur * 0.45))

    elif kind == "x_iv_cierre":
        # el árbitro nos mira a cámara y nos saca la amarilla
        pitch_persp(b, W, H, t, seed=6)
        b.im = b.im.filter(ImageFilter.GaussianBlur(6 * K))
        T = dur * 0.25
        alive(f, cx, H * 1.08, 1.6, t, emo="picaro", arms="relax", arm_r="arriba" if t > T else "relax", look=0.0, **ARB)
        if t > T:
            hx, hy = bean_head(cx, H * 1.08, 1.6)
            k = ease((t - T) / 0.3)
            tarjeta(f, cx + 192, hy - 330 * k + 200 * (1 - k), 2.6 + 0.6 * k, AMA, 8 * math.sin(t * 2))
        img = shot(b, f, [(0, cx, H * 0.58, 1.05), (dur, cx, H * 0.50, 1.2)], t, dur, W, H)
        signs.append(("¿CUÁL MAÑANA?", 0.22, dur * 0.4))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    img = vignette(img, 0.28)
    for txt, t0 in datos:
        img = dato(img, txt, t, t0, W, H)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
