"""Formato «¿Lo encuentras?»: grada llena de aficionados cacahuete y uno escondido (árbitro, portero…).
Escenas: x_bs_reto_<obj> (grada + cuenta atrás de 10 s), x_bs_sol_<obj> (se apaga todo menos él y zoom).
La grada se dibuja una vez y se cachea: nada se mueve de su sitio ni cambia de tamaño."""
from __future__ import annotations

import math
import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from . import anim as A
from .anim_bean import (C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, vignette, _e, SKIN, pitch_persp,
                        goal_persp, camera, dutch, burst, speed_lines)

REF = dict(body=(26, 26, 30), skin=BLANCO, hair="pelo", hcol=(20, 20, 24), num="", ref=True, legcol=(18, 18, 22))
JUG = dict(skin=BLANCO, hair="pelo", hcol=(40, 30, 26))

# equipos de la grada: casa (rojo/blanco) y visitante (azul/amarillo)
TEAMS = [(200, 46, 44), (240, 240, 236), (200, 46, 44), (40, 100, 210), (250, 205, 40), (200, 46, 44),
         (30, 40, 80), (90, 160, 90)]
HAIRS = ["pelo", "gorra", "tupe", "melena"]
HCOL = [(40, 30, 26), (120, 70, 30), (230, 190, 90), (20, 20, 24), (160, 160, 160)]

# objetivo escondido: fila, columna y qué es
PUZZLES = {
    "arbitro": dict(seed=11, row=8, col=8, what="arbitro"),
    "portero": dict(seed=23, row=5, col=2, what="portero"),
    "balon": dict(seed=37, row=3, col=4, what="balon"),
}
ROWS, COLS = 14, 13
Y0, DY = 0.245, 0.0585          # pies de la primera fila y separación (fracción de H)


def _fan_pos(W, H, r, c):
    off = (r % 2) * 0.5
    x = W * (0.04 + (c + off) * 0.92 / (COLS - 0.5))
    y = H * (Y0 + r * DY)
    return x, y


@lru_cache(maxsize=4)
def _crowd(W, H, key):
    P = PUZZLES[key]
    rnd = random.Random(P["seed"])
    b = C((W, H), "RGB", (60, 66, 84))
    # cielo/techo y gradas de hormigón por fila
    b.r(-10, -10, W + 10, H * 0.22, 0, (34, 38, 58), w=0)
    # techo del estadio con vigas y focos
    for i in range(8):
        xx = W * (i + 0.5) / 8
        b.l([(xx, H * 0.0), (xx + 40, H * 0.20)], (52, 58, 80), 8)
    b.r(-10, H * 0.19, W + 10, H * 0.215, 0, (200, 46, 44), INK, 3)
    for r in range(ROWS + 1):
        y = H * (Y0 + r * DY) - H * DY * 0.25
        b.p([(0, y), (W, y), (W, y + H * DY), (0, y + H * DY)], (92 + 6 * (r % 2), 98 + 6 * (r % 2), 118), INK, 2)
    fg = C((W, H), "RGBA", (0, 0, 0, 0))
    s = 0.22
    target = None
    for r in range(ROWS):
        for c in range(COLS):
            x, y = _fan_pos(W, H, r, c)
            x += rnd.uniform(-10, 10)
            is_t = (r, c) == (P["row"], P["col"])
            body = rnd.choice(TEAMS)
            hair = rnd.choice(HAIRS)
            arms = rnd.choice(["relax", "arriba", "arriba", "jarras", "abiertos"])
            arm_r = rnd.choice([None, None, "arriba", "senala"])
            emo = rnd.choice(["feliz", "sorpresa", "serio", "enfado", "picaro", "feliz"])
            kw = dict(body=body, skin=BLANCO, hair=hair, hcol=rnd.choice(HCOL), emo=emo, arms=arms, arm_r=arm_r,
                      num=rnd.choice(["", "", "7", "10", "9"]), blink_off=rnd.random(), t=0.0)
            if not is_t and rnd.random() < 0.10:
                kw.update(body=rnd.choice([(26, 26, 30), (34, 34, 40), (30, 40, 80)]))
            if is_t and P["what"] == "arbitro":
                kw.update(body=(26, 26, 30), hair="pelo", hcol=(20, 20, 24), emo="serio", arms="relax", arm_r="senala", num="",
                          ref=True, legcol=(18, 18, 22))
            elif is_t and P["what"] == "portero":
                kw.update(body=(255, 140, 30), hair="pelo", emo="miedo", arms="abiertos", arm_r=None, num="1")
            bean(fg, x, y, s, **kw)
            hx, hy = bean_head(x, y, s)
            # bufandas y tarjetas de señuelo
            hl = (x - 120 * s, y - 444 * s)
            hr_ = (x + 120 * s, y - 444 * s)
            if not is_t and arms == "arriba" and (arm_r in (None, "arriba")) and rnd.random() < 0.45:
                # bufanda estirada entre las dos manos
                col = rnd.choice(TEAMS)
                fg.l([hl, hr_], INK, 15)
                fg.l([hl, hr_], col, 10)
                for k in range(1, 5):
                    xx = hl[0] + (hr_[0] - hl[0]) * k / 5
                    fg.l([(xx, hl[1] - 4), (xx, hl[1] + 4)], WHITE if col != (240, 240, 236) else (200, 46, 44), 3)
            elif not is_t and arm_r == "arriba" and rnd.random() < 0.5:
                # señuelo: algo amarillo en la mano (bandera pequeña o móvil)
                if rnd.random() < 0.5:
                    fg.l([hr_, (hr_[0], hr_[1] - 40)], INK, 3)
                    fg.p([(hr_[0], hr_[1] - 40), (hr_[0] + 30, hr_[1] - 32), (hr_[0], hr_[1] - 22)], rnd.choice(TEAMS), INK, 2)
                else:
                    fg.r(hr_[0] - 8, hr_[1] - 30, hr_[0] + 10, hr_[1] - 2, 2, (250, 214, 30), INK, 2)
            if is_t:
                target = (hx, hy + 40 * s)
            if P["what"] == "balon" and is_t:
                pass
        # barandilla de la fila: tapa las piernas
        yb = H * (Y0 + r * DY) - H * DY * 0.10
        fg.r(-10, yb, W + 10, yb + H * DY * 0.32, 4, (70, 76, 96), INK, 3)
        fg.l([(-10, yb + 8), (W + 10, yb + 8)], (140, 146, 166), 3)
    if P["what"] == "balon":
        x, y = _fan_pos(W, H, P["row"], P["col"])
        bx, by = x + 46, H * (Y0 + P["row"] * DY) - H * DY * 0.10 - 10
        ball2(fg, bx, by, 13, 0.4)
        target = (bx, by)
    b.im = b.im.convert("RGBA")
    b.im.alpha_composite(fg.im)
    img = b.im.convert("RGB").resize((int(W), int(H)), Image.LANCZOS)
    return img, target


def _clock(img, t, T0, n=10):
    """Cuenta atrás grande arriba a la derecha (número entero, sin moverse)."""
    W, H = img.size
    left = max(0, n - int(t - T0)) if t >= T0 else n
    lay = C((W, H), "RGBA", (0, 0, 0, 0))
    cx, cy, r = W * 0.5, H * 0.935, 60
    frac = 0 if t < T0 else min(1.0, (t - T0) / n)
    lay.c(cx, cy, r, (20, 22, 34, 235), INK, 6)
    if frac < 1:
        lay.arc(cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8, -90 + 360 * frac, 270, (222, 52, 40) if left <= 3 else (255, 214, 40), 12)
    lay.text(cx, cy - 52, str(left), 84, WHITE, 4)
    l = lay.im.resize(img.size, Image.LANCZOS)
    img.paste(l, (0, 0), l)


def _whistle(c, x, y, s):
    hx, hy = bean_head(x, y, s)
    c.c(hx + 12 * s, hy + 26 * s, 9 * s, (190, 190, 196), INK, 2 * s)


def _intro(kind, t, dur, W, H):
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt = [], 0
    if kind == "x_bs_pita":
        # minuto 90: el árbitro señala el punto de penalti; el delantero se tira, el defensa protesta
        pitch_persp(b, W, H, t, seed=7, night=True)
        goal_persp(f, W * 0.10, H * 0.70, 0.9)
        bean(f, W * 0.30, H * 0.80, 0.6, (40, 100, 210), emo="dolor", t=t, arms="abiertos", legs="abiertas", num="9", **JUG)
        bean(f, W * 0.46, H * 0.84, 0.7, (200, 46, 44), emo="enfado", t=t, arms="abiertos", num="4", talk=True, **JUG)
        T = dur * 0.35
        bean(f, W * 0.72, H * 0.98, 1.2, emo="serio", t=t, look=-1, arms="relax", arm_r="senala" if t > T else "relax", **REF)
        hx, hy = bean_head(W * 0.72, H * 0.98, 1.2)
        if t > T:
            speed_lines(f, hx + 12 * 1.2, hy + 26 * 1.2, t, T, n=10, r0=40, r1=110)
        img = camera(b.im, f.im, [(hx - 40, hy + 80, 1.7), (cx, H * 0.62, 1.0)], t, dur, W, H)
        signs.append(("MINUTO 90", 0.22, 0.2))
        if t > T:
            signs[:] = [("PENALTI", 0.22, T)]
        tilt = 0 if t < dur / 2 else -4
    elif kind == "x_bs_huye":
        # la grada se enfada y el árbitro sale corriendo hacia ella
        pitch_persp(b, W, H, t, seed=7, night=True)
        u = _e(t / dur)
        x = W * 0.85 - W * 0.70 * u
        y = H * 0.95 - H * 0.20 * u
        sc = 1.1 - 0.55 * u
        bean(f, x, y, sc, emo="miedo", t=t, look=-1, arms="arriba", legs="corre", phase=t * 16, **REF)
        img = camera(b.im, f.im, [(cx, H * 0.58, 1.0)], t, dur, W, H, shake=4)
        signs.append(("¡HUYE!", 0.22, 0.3))
        tilt = 5 if t < dur / 2 else -5
    elif kind == "x_bs_grada":
        # la grada enfadada; él ya se ha metido dentro: solo se ve la grada, con «¿?»
        base, _ = _crowd(int(W), int(H), "arbitro")
        k = 1.35 - 0.35 * _e(t / dur)
        cw, ch = W / k, H / k
        img = base.crop((int((W - cw) / 2), int((H - ch) * 0.55), int((W + cw) / 2), int((H - ch) * 0.55 + ch))).resize((int(W), int(H)), Image.LANCZOS)
        signs.append(("¿DÓNDE ESTÁ?", 0.22, dur * 0.3))
        img = dutch(img, 3 if t < dur / 2 else 0)
        img = vignette(img, 0.3)
        for txt, yy, t0 in signs:
            sign(img, txt, cx, H * yy, t0, t)
        return img
    img = dutch(img, tilt)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    if kind in ("x_bs_pita", "x_bs_huye", "x_bs_grada"):
        return _intro(kind, t, dur, W, H)
    parts = kind.split("_")
    key = parts[3] if len(parts) > 3 else "arbitro"
    base, (tx, ty) = _crowd(int(W), int(H), key)
    img = base.copy()
    if kind.startswith("x_bs_reto"):
        _clock(img, t, 0.0, n=max(3, int(round(dur - 0.3))))
    elif kind.startswith("x_bs_sol"):
        k = _e(min(1.0, t / 1.0))
        z = 1 + 1.2 * _e(min(1.0, max(0.0, (t - 1.0) / 0.8)))
        # foco: oscurece todo salvo un círculo alrededor del escondido
        mask = Image.new("L", img.size, 0)
        r = 110 - 30 * k
        ImageDraw.Draw(mask).ellipse([tx - r, ty - r * 1.3, tx + r, ty + r * 1.1], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(6))
        darkimg = Image.blend(img, Image.new("RGB", img.size, (6, 8, 20)), 0.75 * k)
        img = Image.composite(img, darkimg, mask)
        d = ImageDraw.Draw(img)
        d.ellipse([tx - r, ty - r * 1.3, tx + r, ty + r * 1.1], outline=(222, 52, 40), width=8)
        if z > 1:
            cw, ch = W / z, H / z
            x0 = min(max(tx - cw / 2, 0), W - cw)
            y0 = min(max(ty - ch / 2, 0), H - ch)
            img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((int(W), int(H)), Image.LANCZOS)
        sign(img, "AQUÍ", cx, H * 0.22, 1.6, t)
    img = vignette(img, 0.25)
    return img
