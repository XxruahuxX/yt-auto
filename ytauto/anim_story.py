"""Storytime de fútbol (prefijo x_st_): historia original en primera persona con planos de cerca
y cortes cada ~1,5 s. Historia: «El portero que no sabía que era portero».
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from . import anim as A
from .anim_extra import person, font, bubble
from .anim_robot import ball, SKINS
from .anim_serie import _glow, text_c, stamp
from .anim_pro import grad, pitch_persp, vignette

WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN = (255, 214, 10), (40, 230, 255)
GREEN, RED = (60, 200, 110), (220, 45, 55)
BLUE = (30, 90, 210)
GLOVE = (255, 140, 40)


def _e(x):
    return A._ease(max(0.0, min(1.0, x)))


def head(x, y, s):
    return x, y - 188 * s


def shoot(im, shots, t, dur):
    """Aplica el plano activo. shots = [(fx, fy, zoom), ...]; corte cada dur/len."""
    PW, PH = im.size
    n = len(shots)
    seg = max(dur / n, 0.8)
    i = min(int(t / seg), n - 1)
    fx, fy, z = shots[i]
    lt = t - i * seg
    z = z * (1 + 0.06 * min(1.0, lt / seg))          # empuje lento dentro del plano
    if lt < 0.12 and i > 0:
        z *= 1.08 - 0.08 * lt / 0.12                   # golpe de zoom en el corte
    cw, ch = PW / z, PH / z
    x0 = min(max(fx - cw / 2, 0), PW - cw)
    y0 = min(max(fy - ch / 2, 0), PH - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((PW, PH), Image.BICUBIC)


def gloves(d, x, y, s, up=0.0):
    for sg in (1, -1):
        u = up if sg == 1 else 0
        hx, hy = x + sg * 36 * s, y - (102 + 120 * u) * s
        d.ellipse([hx - 24 * s, hy - 24 * s, hx + 24 * s, hy + 24 * s], fill=GLOVE, outline=INK, width=max(2, int(3 * s)))


def marcos(d, x, y, s=1.9, mouth="sonrisa", run=0.0, phase=0.0, up=0.0):
    person(d, x, y, s, (40, 200, 120), SKINS[3], "barba", (30, 20, 10), "1", mouth=mouth, run=run, phase=phase, arm_up=up)
    gloves(d, x, y, s, up)


def yo(d, x, y, s=1.3, mouth="sonrisa", **kw):
    person(d, x, y, s, BLUE, SKINS[0], "corto", (60, 40, 20), "7", mouth=mouth, **kw)


def coach(d, x, y, s=1.4, mouth="enfado", pose=""):
    person(d, x, y, s, (60, 60, 70), SKINS[1], "corto", (90, 90, 90), "", mouth=mouth, glasses=True, pose=pose, shorts=(60, 60, 70))


def locker_room(im, t):
    PW, PH = im.size
    d = grad(im, (40, 50, 70), (24, 30, 44))
    for i in range(8):
        x = i * PW / 7 - 20
        d.rectangle([x, PH * 0.30, x + PW / 7 - 14, PH * 0.62], fill=(70, 90, 120), outline=INK, width=4)
        d.rectangle([x + 20, PH * 0.34, x + 60, PH * 0.345], fill=INK)
    d.rectangle([0, PH * 0.62, PW, PH], fill=(120, 110, 100))
    d.rectangle([0, PH * 0.56, PW, PH * 0.6], fill=(150, 110, 70))   # banco
    return d


def side_pitch(im, t):
    PW, PH = im.size
    d = grad(im, (20, 30, 60), (40, 60, 100))
    rnd = random.Random(2)
    d.rectangle([0, PH * 0.28, PW, PH * 0.42], fill=(30, 36, 56))
    for _ in range(500):
        x, y = rnd.uniform(0, PW), rnd.uniform(PH * 0.29, PH * 0.41)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=rnd.choice([(200, 60, 60), (220, 220, 220), (60, 90, 200)]))
    d.rectangle([0, PH * 0.42, PW, PH], fill=(44, 140, 70))
    for i in range(8):
        d.rectangle([i * PW / 8, PH * 0.42, i * PW / 8 + PW / 16, PH], fill=(52, 154, 80))
    return d


def goal_side(d, gx, gb, h=260, w=120, flip=False):
    sg = -1 if flip else 1
    d.line([(gx, gb), (gx, gb - h), (gx + sg * w, gb - h + 30), (gx + sg * w, gb)], fill=WHITE, width=10)
    for i in range(6):
        d.line([(gx, gb - h + i * h / 6), (gx + sg * w, gb - h + 30 + i * (h - 30) / 6)], fill=(200, 220, 210), width=2)


def render(kind, t, dur):
    if kind.startswith("x_st_arb_"):
        return render2(kind, t, dur)
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    FY = PH * 0.64
    if kind == "x_st_racha":
        d = locker_room(im, t)
        d.rounded_rectangle([cx - 230, PH * 0.20, cx + 230, PH * 0.28], 14, fill=(14, 16, 26), outline=RED, width=5)
        text_c(d, cx, PH * 0.215, "10 PARTIDOS SIN GANAR", 40, RED, 4)
        for i, (x, sk) in enumerate(((0.2, 1), (0.8, 2))):
            person(d, PW * x, FY, 1.2, BLUE, SKINS[sk], "corto", (40, 28, 20), str(i + 3), mouth="enfado")
        yo(d, cx, FY, 1.4, mouth="enfado")
        hx, hy = head(cx, FY, 1.4)
        return shoot(im, [(cx, PH * 0.42, 1.0), (hx, hy + 60, 2.2), (cx, PH * 0.30, 1.25)], t, dur)
    if kind == "x_st_llega":
        d = locker_room(im, t)
        # puerta con luz
        im = _glow(im, lambda g: g.rectangle([cx - 150, PH * 0.20, cx + 150, PH * 0.64], fill=(140, 130, 90)), 40)
        d = ImageDraw.Draw(im)
        d.rectangle([cx - 140, PH * 0.20, cx + 140, PH * 0.64], outline=INK, width=8)
        marcos(d, cx, FY, 1.9)
        for x, sk in ((0.12, 1), (0.88, 2)):
            person(d, PW * x, FY + 40, 1.2, BLUE, SKINS[sk], "corto", (40, 28, 20), "", mouth="abierta", arm_up=0.7 + 0.3 * math.sin(t * 12))
        hx, hy = head(cx, FY, 1.9)
        return shoot(im, [(cx, PH * 0.40, 1.0), (hx, hy + 30, 2.3), (cx + 70, FY - 190, 2.6), (PW * 0.12, FY - 200, 2.0)], t, dur)
    if kind == "x_st_porteria":
        d = side_pitch(im, t)
        goal_side(d, 40, FY, flip=False)
        goal_side(d, PW - 40, FY, flip=True)
        u = _e((t - dur * 0.35) / (dur * 0.5))
        mx = cx + (PW - 170 - cx) * u
        coach(d, 150, FY + 30, 1.35, mouth="abierta", pose="senala" if t < dur * 0.4 else "")
        marcos(d, mx, FY, 1.5, run=1.0 if 0 < u < 1 else 0, phase=t * 12)
        chx, chy = head(150, FY + 30, 1.35)
        im = shoot(im, [(chx + 60, chy + 40, 2.2), (cx, PH * 0.45, 1.0), (mx, FY - 200, 1.8)], t, dur)
        if u >= 1:
            stamp(im, "PORTERÍA EQUIVOCADA", cx, PH * 0.36, dur * 0.85, t, bg=RED, fg=WHITE, size=46)
        return im
    if kind == "x_st_aparta":
        d = side_pitch(im, t)
        goal_side(d, PW - 60, FY, h=320, w=150, flip=True)
        dodge = _e((t - dur * 0.35) / 0.25)
        mx = PW - 200 + 0 * dodge
        my = FY
        u = _e((t - dur * 0.2) / (dur * 0.35))
        bx = 80 + (PW - 120 - 80) * u
        by = FY - 160 - 120 * math.sin(math.pi * u)
        marcos(d, mx - 140 * dodge, my, 1.6, mouth="abierta" if dodge > 0 else "sonrisa")
        ball(d, bx, by, 26)
        if u >= 1:
            bubble(d, mx - 140, FY - 420, "¡ME IBA A DAR!", 40)
        hx, hy = head(mx - 140 * dodge, my, 1.6)
        im = shoot(im, [(cx, PH * 0.45, 1.0), (hx, hy + 40, 2.3), (cx, PH * 0.40, 1.3)], t, dur)
        if u >= 1:
            stamp(im, "¡GOL DEL RIVAL!", cx, PH * 0.36, dur * 0.6, t, bg=RED, fg=WHITE, size=52)
        return im
    if kind == "x_st_descanso":
        d = locker_room(im, t)
        d.rounded_rectangle([cx - 160, PH * 0.20, cx + 160, PH * 0.28], 14, fill=(14, 16, 26), outline=YEL, width=5)
        text_c(d, cx, PH * 0.21, "0 - 3", 56, WHITE, 5)
        coach(d, PW * 0.28, FY, 1.45, mouth="enfado")
        marcos(d, PW * 0.70, FY, 1.75, up=0.9 if t > dur * 0.5 else 0.0, mouth="sonrisa")
        if t > dur * 0.5:
            bubble(d, PW * 0.68, PH * 0.27, "¡SON PARA EL FRÍO!", 40)
        else:
            bubble(d, PW * 0.30, PH * 0.30, "¿TÚ NO ERAS PORTERO?", 40)
        chx, chy = head(PW * 0.28, FY, 1.45)
        mhx, mhy = head(PW * 0.70, FY, 1.75)
        return shoot(im, [(chx, chy - 20, 2.0), (cx, PH * 0.40, 1.0), (mhx, mhy - 40, 2.0), (mhx + 40, mhy + 60, 2.6)], t, dur)
    if kind == "x_st_cabeza":
        d = side_pitch(im, t)
        goal_side(d, PW - 60, FY, h=320, w=150, flip=True)
        n = min(3, int(t / (dur / 3.2)))
        lt = t - n * dur / 3.2
        u = _e(lt / 0.6)
        jump = 120 * math.sin(math.pi * min(1, lt / 0.6))
        marcos(d, PW * 0.55, FY - jump, 1.5, mouth="abierta")
        hx, hy = head(PW * 0.55, FY - jump, 1.5)
        bx = 60 + (hx - 60) * u if u < 1 else hx + (PW - 120 - hx) * _e((lt - 0.6) / 0.25)
        by = hy - 40 - 140 * math.sin(math.pi * u) if u < 1 else hy - 40
        ball(d, bx, by, 26)
        d.rounded_rectangle([cx - 160, PH * 0.20, cx + 160, PH * 0.28], 14, fill=(14, 16, 26), outline=YEL, width=5)
        text_c(d, cx, PH * 0.21, f"{n} - 3", 56, WHITE, 5)
        im = shoot(im, [(cx, PH * 0.42, 1.0), (hx, hy + 30, 1.9), (cx, PH * 0.32, 1.3)], t, dur)
        if n >= 3:
            stamp(im, "¡HAT-TRICK DE CABEZA!", cx, PH * 0.36, 3 * dur / 3.2, t, bg=YEL, fg=INK, size=46)
        return im
    if kind == "x_st_final":
        d = side_pitch(im, t)
        im = _glow(im, lambda g: g.ellipse([cx - 300, PH * 0.25, cx + 300, PH * 0.65], fill=(90, 80, 20)), 50)
        d = ImageDraw.Draw(im)
        hop = abs(math.sin(t * 6)) * 30
        for x, sk in ((0.18, 1), (0.82, 2)):
            person(d, PW * x, FY, 1.2, BLUE, SKINS[sk], "corto", (40, 28, 20), "", mouth="abierta", arm_up=1.0)
        marcos(d, cx, FY - 60 - hop, 1.7, up=1.0, mouth="abierta")
        text_c(d, cx, PH * 0.20, "MÁXIMO GOLEADOR", 54, YEL, 7)
        hx, hy = head(cx, FY - 60, 1.7)
        im = shoot(im, [(cx, PH * 0.40, 1.0), (hx + 40, hy + 100, 2.4), (cx, PH * 0.36, 1.2)], t, dur)
        if t > dur * 0.5:
            stamp(im, "¿PARTE 2?", cx, PH * 0.36, dur * 0.5, t, bg=RED, fg=WHITE, size=60)
        return im
    return im


# ---------------------------------------------------------------- storytime 2: el árbitro del silbato nuevo
REF = (24, 24, 28)


def arbitro(d, x, y, s=1.6, mouth="sonrisa", pose="", up=0.0, whistle=True, t=0.0):
    person(d, x, y, s, REF, SKINS[2], "corto", (20, 14, 10), "", mouth=mouth, pose=pose, arm_up=up, shorts=(20, 20, 24))
    hx, hy = head(x, y, s)
    if whistle:
        d.ellipse([hx + 4 * s, hy + 14 * s, hx + 30 * s, hy + 30 * s], fill=(210, 215, 225), outline=INK, width=max(2, int(3 * s)))
        d.line([(hx + 26 * s, hy + 18 * s), (hx + 60 * s, hy + 40 * s)], fill=(250, 200, 40), width=max(2, int(4 * s)))


def priit(d, x, y, t, n=6):
    for i in range(n):
        a = i / n * 2 * math.pi + t * 3
        r0, r1 = 40, 90 + 20 * math.sin(t * 20 + i)
        d.line([(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], fill=YEL, width=8)


def talk(t, on=True):
    return "abierta" if on and int(t * 9) % 3 else "sonrisa"


def compose(bg, fg, shots, t, dur):
    """Plano con profundidad: el fondo se desenfoca en los primeros planos, cámara en mano y corte con golpe."""
    from PIL import ImageFilter
    PW, PH = bg.size
    n = len(shots)
    seg = max(dur / n, 0.8)
    i = min(int(t / seg), n - 1)
    z = shots[i][2]
    if z > 1.3:
        bg = bg.filter(ImageFilter.GaussianBlur(min(9, (z - 1.2) * 6)))
    img = bg.copy()
    img.paste(fg, (0, 0), fg)
    # cámara en mano: pequeño vaivén
    fx, fy, zz = shots[i]
    jx, jy = 6 * math.sin(t * 2.1) * zz, 5 * math.sin(t * 1.7 + 1) * zz
    sh = [(a + jx, b + jy, c) for a, b, c in shots]
    out = shoot(img, sh, t, dur)
    lt = t - i * seg
    if i > 0 and lt < 0.06:  # destello blanco muy corto en el corte
        out = Image.blend(out, Image.new("RGB", out.size, (255, 255, 255)), 0.35 * (1 - lt / 0.06))
    return out


def bob(t, s, k=1.0):
    return 4 * s * math.sin(t * 3.2) * k


def render2(kind, t, dur):
    from .anim_pro import card
    PW, PH = A.PW, A.PH
    bg = Image.new("RGB", (PW, PH))
    fg = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(fg)
    cx = PW / 2
    FY = PH * 0.64
    if kind == "x_st_arb_llega":
        side_pitch(bg, t)
        k = _e(t / 0.9)
        ax = -100 + (cx + 100) * k
        walking = k < 1
        arbitro(d, ax, FY + (0 if walking else bob(t, 1.8)), 1.8, mouth="sonrisa", t=t) if not walking else \
            person(d, ax, FY, 1.8, REF, SKINS[2], "corto", (20, 14, 10), "", phase=t * 11, run=1.0, shorts=(20, 20, 24))
        hx, hy = head(ax, FY, 1.8)
        if t > dur * 0.4:
            for i2 in range(5):
                a = t * 4 + i2 * 1.25
                sx, sy, r = hx + 40 + 80 * math.cos(a), hy + 30 + 55 * math.sin(a), 18 + 6 * math.sin(t * 9 + i2)
                d.polygon([(sx, sy - r), (sx + r * 0.3, sy - r * 0.3), (sx + r, sy), (sx + r * 0.3, sy + r * 0.3),
                           (sx, sy + r), (sx - r * 0.3, sy + r * 0.3), (sx - r, sy), (sx - r * 0.3, sy - r * 0.3)], fill=YEL)
        im = compose(bg, fg, [(cx, PH * 0.42, 1.0), (hx, hy + 30, 2.0), (hx + 40, hy + 40, 3.2)], t, dur)
        if t > dur * 0.4:
            stamp(im, "SILBATO NUEVO", cx, PH * 0.36, dur * 0.4, t, bg=YEL, fg=INK, size=48)
        return im
    if kind == "x_st_arb_saque":
        side_pitch(bg, t)
        blown = t > dur * 0.35
        yo(d, cx - 40, FY + bob(t, 1.3), 1.3, mouth="abierta" if blown else "sonrisa", run=0.0 if blown else 0.3, phase=t * 6)
        ball(d, cx + 40, FY, 26)
        ry = FY + 20 + bob(t + 1, 1.5)
        arbitro(d, PW * 0.80, ry, 1.5, mouth="abierta" if blown else "sonrisa", up=1.0 if blown else 0)
        hx, hy = head(PW * 0.80, ry, 1.5)
        if blown:
            priit(d, hx + 50, hy + 30, t)
        im = compose(bg, fg, [(cx, PH * 0.42, 1.0), (hx, hy + 40, 2.2), (cx - 40, FY - 230, 2.0)], t, dur)
        if blown:
            stamp(im, "¡PRIIIT! ¡FALTA!", cx, PH * 0.36, dur * 0.35, t, bg=RED, fg=WHITE, size=52)
        return im
    if kind == "x_st_arb_tarjeta":
        side_pitch(bg, t)
        yo(d, PW * 0.30, FY + bob(t, 1.45), 1.45, mouth=talk(t, t > dur * 0.6))
        ry = FY + bob(t + 1, 1.55)
        arbitro(d, PW * 0.68, ry, 1.55, mouth="enfado", up=1.0)
        cx2, cy2 = PW * 0.68 + 36 * 1.55, ry - 222 * 1.55 - 40
        card(d, cx2, cy2, 70, 100, (250, 210, 30), rot=8 * math.sin(t * 6), im=fg)
        yhx, yhy = head(PW * 0.30, FY, 1.45)
        im = compose(bg, fg, [(cx, PH * 0.42, 1.0), (cx2, cy2 + 60, 2.4), (yhx, yhy + 40, 2.3)], t, dur)
        stamp(im, "AMARILLA POR RESPIRAR", cx, PH * 0.36, dur * 0.3, t, bg=YEL, fg=INK, size=42)
        return im
    if kind == "x_st_arb_contador":
        locker_room(bg, t)
        dd = ImageDraw.Draw(bg)
        dd.rounded_rectangle([60, PH * 0.32, PW - 60, PH * 0.54], 20, fill=(14, 16, 26), outline=YEL, width=6)
        text_c(dd, cx, PH * 0.34, "DESCANSO · 0 - 0", 46, WHITE, 5)
        n = int(min(1.0, t / (dur * 0.7)) * 47)
        text_c(dd, cx, PH * 0.40, f"{n} FALTAS", 96, YEL, 8)
        text_c(dd, cx, PH * 0.495, "Y 11 AMARILLAS", 44, WHITE, 5)
        return compose(bg, fg, [(cx, PH * 0.43, 1.0), (cx, PH * 0.43, 1.25)], t, dur)
    if kind == "x_st_arb_auto":
        side_pitch(bg, t)
        walking = t > dur * 0.65
        ax = PW * 0.50 + (PW * 0.45 * _e((t - dur * 0.65) / (dur * 0.35)))
        if walking:
            person(d, ax, FY, 1.75, REF, SKINS[2], "corto", (20, 14, 10), "", mouth="enfado", phase=t * 9, run=0.8, shorts=(20, 20, 24))
        else:
            arbitro(d, ax, FY + bob(t, 1.75), 1.75, mouth="enfado", up=1.0 if t > dur * 0.3 else 0)
        hx, hy = head(ax, FY, 1.75)
        if dur * 0.3 < t < dur * 0.65:
            card(d, ax + 36 * 1.75, FY - 222 * 1.75 - 40, 70, 100, (220, 40, 50), rot=-6, im=fg)
        for x, sk in ((0.12, 1), (0.30, 0)):
            person(d, PW * x, FY + 30 + bob(t + x * 5, 1.1), 1.1, BLUE, SKINS[sk], "corto", (40, 28, 20), "", mouth="abierta")
        im = compose(bg, fg, [(hx, hy + 40, 2.2), (ax + 60, FY - 400, 2.2), (cx, PH * 0.42, 1.0)], t, dur)
        if t > dur * 0.3:
            stamp(im, "¡SE EXPULSA A SÍ MISMO!", cx, PH * 0.36, dur * 0.3, t, bg=RED, fg=WHITE, size=44)
        return im
    if kind == "x_st_arb_final":
        side_pitch(bg, t)
        bg = _glow(bg, lambda g: g.ellipse([cx - 300, PH * 0.25, cx + 300, PH * 0.65], fill=(90, 80, 20)), 50)
        for x, sk in ((0.2, 1), (0.8, 2)):
            hop = abs(math.sin(t * 7 + x * 4)) * 30
            person(d, PW * x, FY - hop, 1.2, BLUE, SKINS[sk], "corto", (40, 28, 20), "", mouth="abierta", arm_up=1.0)
        person(d, cx, FY + bob(t, 1.5), 1.5, (240, 140, 40), SKINS[0], "mono", (120, 120, 120), "", mouth=talk(t), glasses=True)
        hx, hy = head(cx, FY, 1.5)
        im = compose(bg, fg, [(cx, PH * 0.42, 1.0), (hx, hy + 40, 2.3), (cx, PH * 0.36, 1.2)], t, dur)
        stamp(im, "0 FALTAS", cx, PH * 0.36, 0.4, t, bg=GREEN, fg=WHITE, size=56)
        if t > dur * 0.55:
            stamp(im, "¿PARTE 2?", cx, PH * 0.46, dur * 0.55, t, bg=RED, fg=WHITE, size=56)
        return im
    return Image.new("RGB", (PW, PH))
