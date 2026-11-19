"""Animaciones pro del 19-nov.

x_bp_ (balón de pentágonos, Telstar 1970), x_pk_ (penalti a lo Panenka, 1976),
x_cu_ (¿qué pasaría si el balón fuera un cubo?).
"""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageDraw

from . import anim as A
from .anim_extra import person, font
from .anim_robot import ball, SKINS
from .anim_serie import _glow, text_c, stamp
from .anim_pro import grad, pitch_persp, vignette

WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN = (255, 214, 10), (40, 230, 255)
GREEN, RED = (60, 200, 110), (220, 45, 55)


def _e(x):
    return A._ease(x)


# ------------------------------------------------------------------ balón 3D
_PHI = (1 + 5 ** 0.5) / 2
_ICO = np.array([(0, s1, s2 * _PHI) for s1 in (-1, 1) for s2 in (-1, 1)]
                + [(s1, s2 * _PHI, 0) for s1 in (-1, 1) for s2 in (-1, 1)]
                + [(s2 * _PHI, 0, s1) for s1 in (-1, 1) for s2 in (-1, 1)], dtype=float)
_ICO /= np.linalg.norm(_ICO, axis=1, keepdims=True)


def _rot(ay, ax):
    cy, sy, cx, sx = math.cos(ay), math.sin(ay), math.cos(ax), math.sin(ax)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return rx @ ry


def ball3d(im, cx, cy, R, ay, ax=0.35, pent=INK, base=(245, 245, 245), seams=True, scale=1.0):
    """Balón tipo icosaedro truncado: 12 pentágonos (negros) + costuras."""
    d = ImageDraw.Draw(im)
    d.ellipse([cx - R + 10, cy - R + 16, cx + R + 10, cy + R + 16], fill=(0, 0, 0))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=base)
    M = _rot(ay, ax)
    V = _ICO @ M.T
    ang = 0.37 * scale
    for v in V:
        if v[2] < -0.15:
            continue
        a = np.cross(v, [0.3, 1, 0.1]); a /= np.linalg.norm(a)
        b = np.cross(v, a)
        pts = []
        for i in range(5):
            th = 2 * math.pi * i / 5
            p = v * math.cos(ang) + (a * math.cos(th) + b * math.sin(th)) * math.sin(ang)
            pts.append((cx + p[0] * R, cy - p[1] * R, p[2]))
        if v[2] > 0:
            d.polygon([(x, y) for x, y, _ in pts], fill=pent)
        if seams:
            for x, y, z in pts:
                if z > 0:
                    q = np.array([(x - cx) / R, -(y - cy) / R, z]) * 1.35 - v * 0.35
                    q /= np.linalg.norm(q)
                    if q[2] > 0:
                        d.line([(x, y), (cx + q[0] * R, cy - q[1] * R)], fill=(150, 150, 160), width=3)
    # sombreado y brillo
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for i in range(10):
        k = i / 10
        ld.arc([cx - R + k * 4, cy - R + k * 4, cx + R - k * 4, cy + R - k * 4], 0, 180,
               fill=(0, 0, 0, int(70 * (1 - k))), width=int(R * 0.05))
    ld.ellipse([cx - R * 0.55, cy - R * 0.7, cx - R * 0.1, cy - R * 0.4], fill=(255, 255, 255, 120))
    im.paste(lay, (0, 0), lay)
    ImageDraw.Draw(im).ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK, width=5)


def crt(im, box, content, t):
    """Tele antigua: dibuja content (imagen) en blanco y negro dentro del marco."""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    d.rounded_rectangle([x0 - 40, y0 - 40, x1 + 40, y1 + 110], 40, fill=(110, 72, 40), outline=INK, width=6)
    for i in range(6):
        d.line([(x0 - 20, y1 + 30 + i * 12), (x0 + 120, y1 + 30 + i * 12)], fill=(70, 44, 24), width=4)
    for k, kx in enumerate((x1 - 90, x1 - 30)):
        d.ellipse([kx - 22, y1 + 40, kx + 22, y1 + 84], fill=(40, 40, 40), outline=(200, 200, 200), width=3)
    d.line([((x0 + x1) / 2, y0 - 40), ((x0 + x1) / 2 - 120, y0 - 190)], fill=(60, 60, 60), width=6)
    d.line([((x0 + x1) / 2, y0 - 40), ((x0 + x1) / 2 + 120, y0 - 190)], fill=(60, 60, 60), width=6)
    w, h = int(x1 - x0), int(y1 - y0)
    g = content.resize((w, h)).convert("L")
    arr = np.asarray(g, dtype=np.int16)
    rnd = np.random.default_rng(int(t * 30))
    arr = arr + rnd.integers(-22, 22, arr.shape)
    arr[::4, :] = (arr[::4, :] * 0.75).astype(np.int16)
    g = Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).convert("RGB")
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 50, fill=255)
    im.paste(g, (int(x0), int(y0)), m)


def _mini_pitch(w, h, telstar, t, seed=0):
    sub = Image.new("RGB", (w, h), (70, 150, 80))
    sd = ImageDraw.Draw(sub)
    for i in range(8):
        sd.rectangle([i * w / 8, 0, (i + 1) * w / 8, h], fill=(70, 150, 80) if i % 2 else (82, 165, 92))
    sd.line([(w / 2, 0), (w / 2, h)], fill=(235, 235, 235), width=4)
    bx = w * (0.3 + 0.4 * (0.5 + 0.5 * math.sin(t * 1.6 + seed)))
    by = h * 0.55
    if telstar:
        ball3d(sub, bx, by, 34, t * 4, seams=False)
    else:
        sd.ellipse([bx - 34, by - 34, bx + 34, by + 34], fill=(150, 150, 150))
    return sub


def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    im = Image.new("RGB", (PW, PH))
    cx = PW / 2
    # ======================================================== 032 balón Telstar
    if kind == "x_bp_tv":
        grad(im, (40, 26, 20), (18, 12, 10))
        d = ImageDraw.Draw(im)
        d.rectangle([0, PH * 0.66, PW, PH], fill=(60, 40, 28))
        tel = t > dur * 0.5
        sub = _mini_pitch(560, 400, tel, t)
        crt(im, (cx - 280, PH * 0.36, cx + 280, PH * 0.36 + 400), sub, t)
        d = ImageDraw.Draw(im)
        text_c(d, cx, PH * 0.27, "TELE EN BLANCO Y NEGRO", 50, WHITE, 6)
        loc = t - (dur * 0.5 if tel else 0)
        if tel:
            stamp(im, "AHORA SÍ SE VE", cx, PH * 0.57, 0.3, loc, bg=GREEN, fg=WHITE, size=54)
        else:
            stamp(im, "¿DÓNDE ESTÁ EL BALÓN?", cx, PH * 0.57, 0.6, loc, bg=RED, fg=WHITE, size=50)
        return vignette(im, 0.45)
    if kind == "x_bp_telstar":
        grad(im, (10, 16, 40), (30, 20, 60))
        d = ImageDraw.Draw(im)
        rnd = random.Random(2)
        for _ in range(120):
            x, y = rnd.uniform(0, PW), rnd.uniform(0, PH)
            d.point((x, y), fill=(200, 200, 230))
        k = _e(t / 0.6)
        R = 230 * (0.4 + 0.6 * k)
        im = _glow(im, lambda g: g.ellipse([cx - R - 30, PH * 0.47 - R - 30, cx + R + 30, PH * 0.47 + R + 30], fill=(80, 90, 160)), 40)
        ball3d(im, cx, PH * 0.47, R, t * 1.3, 0.3 + 0.2 * math.sin(t))
        d = ImageDraw.Draw(im)
        text_c(d, cx, PH * 0.27, "TELSTAR", 76, YEL, 8)
        if t > 0.8:
            text_c(d, cx, PH * 0.585, "MÉXICO 1970", 56, WHITE, 7)
        return vignette(im, 0.4)
    if kind == "x_bp_32":
        grad(im, (12, 20, 40), (10, 40, 50))
        d = ImageDraw.Draw(im)
        n = min(32, int(t / max(dur * 0.65, 0.1) * 32) + 1)
        cols, sz = 8, 82
        x0, y0 = cx - cols * sz / 2 + sz / 2, PH * 0.36
        for i in range(n):
            x = x0 + (i % cols) * sz
            y = y0 + (i // cols) * sz
            pent = i < 12
            r = 34
            sides = 5 if pent else 6
            pts = [(x + r * math.cos(2 * math.pi * j / sides - math.pi / 2), y + r * math.sin(2 * math.pi * j / sides - math.pi / 2)) for j in range(sides)]
            d.polygon(pts, fill=INK if pent else (245, 245, 245), outline=(120, 120, 140))
        text_c(d, cx, PH * 0.27, f"{min(n, 12)} PENTÁGONOS" + (f" + {n - 12} HEXÁGONOS" if n > 12 else ""), 40, YEL, 6)
        if n >= 32:
            stamp(im, "32 PIEZAS", cx, PH * 0.58, dur * 0.65, t, bg=YEL, fg=INK, size=64)
        return vignette(im, 0.4)
    if kind == "x_bp_satelite":
        d = grad(im, (2, 4, 14), (8, 10, 30))
        rnd = random.Random(7)
        for _ in range(220):
            x, y = rnd.uniform(0, PW), rnd.uniform(0, PH)
            d.point((x, y), fill=(230, 230, 255))
        # Tierra
        d.ellipse([-PW * 0.4, PH * 0.62, PW * 1.4, PH * 1.5], fill=(30, 80, 170))
        d.ellipse([PW * 0.1, PH * 0.66, PW * 0.5, PH * 0.78], fill=(60, 140, 80))
        k = _e((t - dur * 0.45) / 0.6)
        sx, sy = cx + 80 * math.sin(t * 0.8), PH * 0.46
        if k < 1:
            # satélite esférico con paneles
            r = 120 * (1 - k * 0.3)
            for sg in (-1, 1):
                d.rectangle([min(sx + sg * r * 1.1, sx + sg * r * 2.3), sy - 30, max(sx + sg * r * 1.1, sx + sg * r * 2.3), sy + 30], fill=(40, 70, 140), outline=(180, 200, 255), width=3)
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(180, 180, 190), outline=INK, width=4)
            for a in range(0, 360, 40):
                d.line([(sx, sy), (sx + r * math.cos(math.radians(a + t * 40)), sy + r * math.sin(math.radians(a + t * 40)))], fill=(120, 120, 130), width=3)
        if k > 0:
            ball3d(im, sx, sy, 140 * k + 1, t * 1.5)
        d = ImageDraw.Draw(im)
        text_c(d, cx, PH * 0.27, "SATÉLITE TELSTAR" if k < 0.5 else "BALÓN TELSTAR", 56, YEL, 7)
        return im
    # ======================================================== 033 Panenka
    if kind == "x_pk_final":
        d = pitch_persp(im, t, 0.30)
        # marcador de estadio
        d.rounded_rectangle([60, PH * 0.34, PW - 60, PH * 0.56], 24, fill=(14, 16, 26), outline=YEL, width=5)
        text_c(d, cx, PH * 0.355, "FINAL EUROCOPA 1976", 40, YEL, 4)
        text_c(d, cx, PH * 0.40, "CHECOSLOVAQUIA  2-2  ALEMANIA FED.", 34, WHITE, 4)
        if t > 0.9:
            text_c(d, cx, PH * 0.46, "PRÓRROGA... Y PENALTIS", 44, CYAN, 5)
        stamp(im, "BELGRADO", cx, PH * 0.59, 0.3, t, bg=RED, fg=WHITE, size=50)
        return vignette(im)
    if kind == "x_pk_carrera":
        # vista desde detrás del lanzador
        d = grad(im, (8, 14, 30), (16, 30, 54))
        hy = PH * 0.30
        d.rectangle([0, hy - 120, PW, hy], fill=(24, 30, 48))
        rnd = random.Random(5)
        for _ in range(300):
            d.point((rnd.uniform(0, PW), rnd.uniform(hy - 115, hy - 5)), fill=rnd.choice([(200, 60, 60), (220, 220, 220), (60, 90, 200)]))
        d.rectangle([0, hy, PW, PH], fill=(40, 136, 70))
        gx0, gx1, gt, gb = cx - 300, cx + 300, PH * 0.34, PH * 0.50
        d.rectangle([gx0, gt, gx1, gb], fill=(30, 110, 60))
        for i in range(0, 600, 30):
            d.line([(gx0 + i, gt), (gx0 + i, gb)], fill=(200, 220, 210), width=1)
        for j in range(0, int(gb - gt), 30):
            d.line([(gx0, gt + j), (gx1, gt + j)], fill=(200, 220, 210), width=1)
        d.rectangle([gx0 - 10, gt - 10, gx1 + 10, gt + 4], fill=WHITE)
        d.rectangle([gx0 - 10, gt - 10, gx0 + 4, gb], fill=WHITE)
        d.rectangle([gx1 - 4, gt - 10, gx1 + 10, gb], fill=WHITE)
        # portero que se balancea
        kx = cx + 40 * math.sin(t * 3)
        person(d, kx, gb + 6, 0.95, (40, 40, 44), SKINS[0], "corto", (60, 40, 20), "1", arm_up=0.6)
        ball(d, cx, PH * 0.60, 26)
        k = _e(t / max(dur, 0.1))
        s = 2.4 - 0.5 * k
        px = cx - 260 + 180 * k
        person(d, px, PH * 0.66 + 120 * (1 - k), s, (225, 40, 50), SKINS[0], "corto", (60, 40, 20), "", phase=t * 10, run=1.0)
        text_c(d, cx, PH * 0.27, "4-3 EN LA TANDA · ÚLTIMO PENALTI", 36, YEL, 5)
        return vignette(im)
    if kind == "x_pk_vaselina":
        d = grad(im, (8, 14, 30), (16, 30, 54))
        hy = PH * 0.30
        d.rectangle([0, hy, PW, PH], fill=(40, 136, 70))
        gx0, gx1, gt, gb = cx - 330, cx + 330, PH * 0.33, PH * 0.56
        d.rectangle([gx0, gt, gx1, gb], fill=(30, 110, 60))
        for i in range(0, 660, 33):
            d.line([(gx0 + i, gt), (gx0 + i, gb)], fill=(200, 220, 210), width=1)
        for j in range(0, int(gb - gt), 33):
            d.line([(gx0, gt + j), (gx1, gt + j)], fill=(200, 220, 210), width=1)
        d.rectangle([gx0 - 12, gt - 12, gx1 + 12, gt + 4], fill=WHITE)
        d.rectangle([gx0 - 12, gt - 12, gx0 + 4, gb], fill=WHITE)
        d.rectangle([gx1 - 4, gt - 12, gx1 + 12, gb], fill=WHITE)
        T0 = 0.35
        u = max(0.0, t - T0)
        dive = _e(u / 0.6)
        # portero se tira a su izquierda: cuerpo tumbado
        kx = cx - 230 * dive
        if dive < 0.3:
            person(d, kx, gb + 4, 1.25, (40, 40, 44), SKINS[0], "corto", (60, 40, 20), "1", arm_up=0.8)
        else:
            lay = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
            person(ImageDraw.Draw(lay), 250, 470, 1.25, (40, 40, 44), SKINS[0], "corto", (60, 40, 20), "1", arm_up=1.0, mouth="abierta")
            lay = lay.rotate(70 * dive, resample=Image.BICUBIC)
            im.paste(lay, (int(kx - 250), int(gb - 380)), lay)
            d = ImageDraw.Draw(im)
        # balón en parábola lenta hacia el centro
        bt = min(1.0, u / max(dur - T0 - 0.4, 0.5))
        bx = cx
        by0, by1 = PH * 0.70, gb - 90
        by = by0 + (by1 - by0) * bt - 260 * math.sin(math.pi * bt)
        br = 40 - 18 * bt
        d.ellipse([bx - br, by0 + (by1 - by0) * bt + 40 - 8, bx + br, by0 + (by1 - by0) * bt + 40 + 8], fill=(20, 70, 35))
        ball(d, bx, by, br)
        if u > 0.2:
            text_c(d, cx, PH * 0.27, "CÁMARA LENTA", 40, WHITE, 5)
        if bt >= 1:
            stamp(im, "¡CAMPEONES!", cx, PH * 0.60, 0, u - (dur - T0 - 0.4), bg=YEL, fg=INK, size=64)
            im = _glow(im, lambda g: g.ellipse([bx - 80, by - 80, bx + 80, by + 80], fill=(255, 230, 120)), 30)
        return vignette(im)
    if kind == "x_pk_nombre":
        d = grad(im, (40, 10, 20), (12, 8, 24))
        for i in range(16):
            a = i / 16 * 2 * math.pi + t * 0.4
            d.polygon([(cx, PH * 0.46), (cx + 1200 * math.cos(a), PH * 0.46 + 1200 * math.sin(a)),
                       (cx + 1200 * math.cos(a + 0.12), PH * 0.46 + 1200 * math.sin(a + 0.12))], fill=(70, 18, 30))
        k = _e(t / 0.5)
        text_c(d, cx, PH * 0.30, "HOY SE LLAMA", 50, WHITE, 6)
        f = 96 * (0.5 + 0.5 * k)
        im = _glow(im, lambda g: text_c(g, cx, PH * 0.42, "«PANENKA»", f, YEL, 0), 22)
        d = ImageDraw.Draw(im)
        text_c(d, cx, PH * 0.42, "«PANENKA»", f, YEL, 9)
        if t > 0.9:
            text_c(d, cx, PH * 0.56, "PICARLA POR EL CENTRO", 44, CYAN, 6)
        return vignette(im, 0.4)
    # ======================================================== 034 balón cubo
    if kind.startswith("x_cu_"):
        d = pitch_persp(im, t, 0.30)
        cube = YEL

        def cubo(x, y, s, a):
            s *= 1.7
            pts = [(x + s * math.cos(a + math.pi / 4 + i * math.pi / 2), y + s * math.sin(a + math.pi / 4 + i * math.pi / 2)) for i in range(4)]
            d.polygon([(px + 10, py + 14) for px, py in pts], fill=(10, 40, 20))
            d.polygon(pts, fill=WHITE, outline=INK, width=5)
            d.polygon([(x + (px - x) * 0.4, y + (py - y) * 0.4) for px, py in pts], fill=INK)

        if kind == "x_cu_saque":
            k = _e(t / 0.5)
            px = cx - 200
            person(d, px, PH * 0.62, 1.5, (30, 90, 210), SKINS[1], "corto", (30, 20, 10), "9",
                   phase=t * 10, run=1.0 if t < 0.6 else 0, mouth="sonrisa" if t < 0.8 else "abierta")
            u = max(0, t - 0.6)
            bx = cx + 40 + 90 * (1 - math.exp(-u * 8))
            cubo(bx, PH * 0.62 - 50, 55, 0)
            if t > 0.75:
                stamp(im, "¡CLONC!", cx + 160, PH * 0.42, 0.75, t, bg=YEL, fg=INK, size=64, rot=8)
            if t > 1.3:
                text_c(d, cx, PH * 0.27, "AVANZA 2 METROS Y SE PARA", 40, WHITE, 6)
            return im
        if kind == "x_cu_regate":
            px = cx - 140 + 60 * math.sin(t * 2)
            fall = _e((t - dur * 0.55) / 0.4)
            if fall < 0.05:
                person(d, px, PH * 0.62, 1.5, (30, 90, 210), SKINS[2], "tupe", (30, 20, 10), "10", phase=t * 12, run=1.0)
            else:
                lay = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
                person(ImageDraw.Draw(lay), 250, 480, 1.5, (30, 90, 210), SKINS[2], "tupe", (30, 20, 10), "10", mouth="abierta")
                lay = lay.rotate(-85 * fall, resample=Image.BICUBIC)
                im.paste(lay, (int(px - 250), int(PH * 0.62 - 440 + 120 * fall)), lay)
                d = ImageDraw.Draw(im)
                for i in range(3):
                    a = t * 6 + i * 2.1
                    d.text((px + 90 + 50 * math.cos(a), PH * 0.48 + 20 * math.sin(a)), "★", font=font(40), fill=YEL)
            hop = abs(math.sin(t * 7)) * 40
            cubo(px + 130, PH * 0.62 - 50 - hop, 50, t * 3)
            if fall > 0.3:
                stamp(im, "REGATE CANCELADO", cx, PH * 0.32, 0, t, bg=RED, fg=WHITE, size=50)
            return im
        if kind == "x_cu_cabeza":
            u = min(1.0, t / 0.8)
            by = PH * 0.22 + (PH * 0.40 - PH * 0.22) * u
            person(d, cx, PH * 0.64, 1.7, (30, 90, 210), SKINS[0], "barba", (30, 20, 10), "5",
                   mouth="abierta" if t > 0.8 else "sonrisa", arm_up=0.3)
            cubo(cx + (0 if u < 1 else 200 * (t - 0.8)), by - (0 if u < 1 else 300 * (t - 0.8)), 60, t * 4)
            if t > 0.8:
                hx, hy = cx, PH * 0.64 - 188 * 1.7
                d.ellipse([hx - 30, hy - 90, hx + 30, hy - 50], fill=(240, 120, 120))
                stamp(im, "¡AUCH!", cx - 170, PH * 0.36, 0.8, t, bg=RED, fg=WHITE, size=64, rot=-8)
                for i in range(4):
                    a = t * 5 + i * 1.6
                    d = ImageDraw.Draw(im)
                    d.text((hx - 20 + 90 * math.cos(a), hy - 110 + 25 * math.sin(a)), "★", font=font(40), fill=YEL)
            return im
        if kind == "x_cu_gol":
            gx0, gx1, gt, gb = cx - 280, cx + 280, PH * 0.34, PH * 0.50
            d.rectangle([gx0, gt, gx1, gb], fill=(30, 110, 60))
            for i in range(0, 560, 28):
                d.line([(gx0 + i, gt), (gx0 + i, gb)], fill=(200, 220, 210), width=1)
            d.rectangle([gx0 - 10, gt - 10, gx1 + 10, gt + 4], fill=WHITE)
            d.rectangle([gx0 - 10, gt - 10, gx0 + 4, gb], fill=WHITE)
            d.rectangle([gx1 - 4, gt - 10, gx1 + 10, gb], fill=WHITE)
            # el cubo bota en zigzag imposible
            path = [(cx, PH * 0.68), (cx + 220, PH * 0.60), (cx - 200, PH * 0.55), (cx + 120, PH * 0.50), (cx - 60, PH * 0.44)]
            u = min(0.999, t / max(dur * 0.7, 0.1)) * (len(path) - 1)
            i = int(u)
            f = u - i
            bx = path[i][0] + (path[i + 1][0] - path[i][0]) * f
            by = path[i][1] + (path[i + 1][1] - path[i][1]) * f - 60 * math.sin(math.pi * f)
            target = path[min(i + 1, len(path) - 1)][0]
            kx = cx + (target - cx) * 0.3 * (-1 if i % 2 else 1)
            person(d, kx, gb + 6, 1.05, (40, 220, 120), SKINS[1], "corto", (30, 20, 10), "1", arm_up=0.8,
                   mouth="abierta")
            cubo(bx, by, 40 - 10 * (u / 4), t * 6)
            if t > dur * 0.7:
                im = _glow(im, lambda g: g.rectangle([gx0, gt, gx1, gb], fill=(120, 110, 40)), 30)
                stamp(im, "¡GOL IMPOSIBLE!", cx, PH * 0.30, dur * 0.7, t, bg=YEL, fg=INK, size=60)
            return im
        if kind == "x_cu_fabrica":
            d = grad(im, (20, 24, 34), (40, 44, 56))
            d.rectangle([0, PH * 0.58, PW, PH * 0.62], fill=(70, 70, 80))
            for i in range(-1, 7):
                x = (i * 200 + t * 160) % (PW + 200) - 100
                if x > cx + 90:
                    ball3d(im, x, PH * 0.535, 62, t * 3 + i, seams=False)
                    d = ImageDraw.Draw(im)
                else:
                    cubo(x, PH * 0.535, 40, 0)
            d.rectangle([cx - 110, PH * 0.34, cx + 110, PH * 0.48], fill=(90, 90, 110), outline=INK, width=5)
            text_c(d, cx, PH * 0.40, "LIMA", 50, YEL, 5)
            if int(t * 8) % 2:
                for sp in range(6):
                    a = sp * 1.05
                    d.line([(cx, PH * 0.51), (cx + 60 * math.cos(a), PH * 0.51 + 30 * math.sin(a))], fill=YEL, width=4)
            text_c(d, cx, PH * 0.27, "SOLUCIÓN: LIMAR ESQUINAS", 40, WHITE, 6)
            if t > dur * 0.5:
                stamp(im, "= BALÓN REDONDO", cx, PH * 0.61, dur * 0.5, t, bg=GREEN, fg=WHITE, size=54)
            return im
    # ======================================================== contador de dato clave
    # Uso en guion: anim: "x_dc_contador|32|PIEZAS|12 + 20" (desglose opcional)
    if kind.startswith("x_dc_contador"):
        parts = (kind.split("|") + ["", "", ""])[1:4]
        val, unidad, desg = parts
        try:
            target = float(val.replace(",", "."))
        except ValueError:
            target = 0.0
        dec = len(val.replace(".", ",").split(",")[1]) if ("," in val or "." in val) else 0
        d = grad(im, (10, 16, 36), (20, 30, 60))
        cy, R = PH * 0.46, 210
        k = _e(min(1, max(0, (t - 0.2) / min(1.6, dur * 0.5))))
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(40, 50, 80), width=26)
        if k > 0:
            im = _glow(im, lambda g: g.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * k, fill=YEL, width=26), 18)
            d = ImageDraw.Draw(im)
            d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * k, fill=YEL, width=26)
        n = target * k
        txt = (f"{n:.{dec}f}".replace(".", ",") if dec else f"{int(round(n)):,}".replace(",", "."))
        size = 150 if len(txt) <= 3 else max(80, 150 - 18 * (len(txt) - 3))
        text_c(d, cx, cy - size * 0.62, txt, size, WHITE, 9)
        if unidad:
            text_c(d, cx, cy + 70, unidad, 44, YEL, 6)
        t1 = min(1.6, dur * 0.5) + 0.3
        if t > t1:
            text_c(d, cx, PH * 0.29, "DATO CLAVE", 50, YEL, 6)
        if desg and t > t1:
            kk = min(1, (t - t1) / 0.3)
            w = 460
            d.rounded_rectangle([cx - w / 2, PH * 0.64 - 40, cx - w / 2 + w * kk, PH * 0.64 + 34], 20, fill=GREEN)
            if kk >= 1:
                text_c(d, cx, PH * 0.64 - 30, desg, 46, WHITE, 5)
        return vignette(im, 0.35)
    return im
