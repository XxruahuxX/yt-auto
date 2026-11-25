"""Estilo «cacahuete»: personajes de cabeza redonda, cuerpo ovalado y piernas de palo, cara seria,
sobre escenarios con perspectiva real y sombreado plano (aspecto de 3D dibujado).
Prefijo de escenas: x_bn_ (demo). Reutiliza el lienzo C (supersampling) y la cámara de anim_toon."""
from __future__ import annotations

import math
import random

from PIL import Image

from . import anim as A
from .anim_serie import stamp
from .anim_toon import C, K, OUT, WHITE, YEL, RED, shade, camera, vignette, ball, confetti, stars, _e

SKIN = [(246, 214, 186), (228, 186, 150), (190, 136, 98), (122, 84, 60)]
INK = (14, 12, 20)
BLANCO = (250, 250, 248)


def dutch(img, ang):
    """Plano inclinado (sin bordes negros: escala un poco)."""
    if not ang:
        return img
    W, H = img.size
    a = math.radians(abs(ang))
    k = math.cos(a) + (H / W) * math.sin(a) + 0.01
    big = img.resize((int(W * k), int(H * k)), Image.BICUBIC).rotate(ang, resample=Image.BICUBIC)
    x0, y0 = (big.width - W) // 2, (big.height - H) // 2
    return big.crop((x0, y0, x0 + W, y0 + H))


def rain(img, t, n=90, ang=0.25):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    rnd = random.Random(5)
    for i in range(n):
        x0, sp, ln = rnd.uniform(-200, W), rnd.uniform(1400, 2200), rnd.uniform(40, 90)
        y = (rnd.uniform(0, H) + t * sp) % (H + 100) - 50
        x = x0 + (y + 50) * ang
        d.line([(x, y), (x + ln * ang, y + ln)], fill=(220, 230, 255, 150), width=2)
    return img


def sign(img, txt, cx, cy, t0, t, size=86, bg=(222, 52, 40), fg=WHITE):
    """Cartel rojo recto con borde negro, entra con un pequeño rebote (como «-1.000 L»)."""
    if t < t0:
        return
    k = min(1.0, (t - t0) / 0.22)
    sc = 1 + 0.25 * math.sin(k * math.pi) * (1 - k) + (0.6 * (1 - k) if k < 0.4 else 0)
    from .anim_extra import font
    f = font(int(size * sc))
    c = C((img.size[0], img.size[1]), "RGBA", (0, 0, 0, 0))
    tw = c.d.textlength(txt, font=font(int(size * sc * K))) / K
    pw, ph = tw / 2 + 34 * sc, size * sc * 0.72
    c.r(cx - pw, cy - ph, cx + pw, cy + ph, 22 * sc, bg, INK, 7 * sc)
    c.text(cx, cy - size * sc * 0.62, txt, size * sc, fg, 0)
    lay = c.im.resize(img.size, Image.LANCZOS)
    img.paste(lay, (0, 0), lay)


def ball2(c, x, y, r, rot=0.0):
    """Balón con pentágonos de verdad, sombreado y brillo."""
    from PIL import ImageDraw
    S = int(2 * r * K) + 4
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    o, R_ = S / 2, r * K

    def pent(px, py, rr, a0):
        return [(px + rr * math.cos(a0 + i * 2 * math.pi / 5), py + rr * math.sin(a0 + i * 2 * math.pi / 5)) for i in range(5)]
    d.ellipse([o - R_, o - R_, o + R_, o + R_], fill=(250, 250, 250))
    d.ellipse([o - R_ * 0.7, o - R_ * 0.55, o + R_ * 1.15, o + R_ * 1.2], fill=(214, 218, 226))
    d.ellipse([o - R_ * 1.0, o - R_ * 1.0, o + R_ * 0.75, o + R_ * 0.75], fill=(250, 250, 250))
    cp = pent(o, o, R_ * 0.30, rot - math.pi / 2)
    d.polygon(cp, fill=INK)
    for i in range(5):
        a = rot - math.pi / 2 + i * 2 * math.pi / 5
        vx, vy = cp[i]
        ex, ey = o + R_ * 0.62 * math.cos(a), o + R_ * 0.62 * math.sin(a)
        d.line([(vx, vy), (ex, ey)], fill=INK, width=max(2, int(R_ * 0.06)))
        d.polygon(pent(o + R_ * 0.97 * math.cos(a + math.pi / 5), o + R_ * 0.97 * math.sin(a + math.pi / 5), R_ * 0.26, a + math.pi / 5),
                  fill=INK)
        d.line([(ex, ey), (o + R_ * 0.78 * math.cos(a + math.pi / 5) * 0.98, o + R_ * 0.78 * math.sin(a + math.pi / 5) * 0.98)],
               fill=INK, width=max(2, int(R_ * 0.06)))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([o - R_, o - R_, o + R_, o + R_], fill=255)
    lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", (S, S), 0), mask))
    d2 = ImageDraw.Draw(lay)
    d2.ellipse([o - R_, o - R_, o + R_, o + R_], outline=INK, width=max(3, int(R_ * 0.05)))
    c.im.alpha_composite(lay, (int(x * K - S / 2), int(y * K - S / 2)))


def ball_fx(c, pts, r, ground=None):
    """Estela del balón (posiciones anteriores) y sombra en el suelo."""
    if ground is not None:
        x, _ = pts[-1]
        c.e(x - r * 1.1, ground - r * 0.25, x + r * 1.1, ground + r * 0.25, (0, 0, 0, 70), w=0)
    n = len(pts)
    for i, (x, y) in enumerate(pts[:-1]):
        a = int(110 * (i + 1) / n)
        c.c(x, y, r * (0.5 + 0.5 * (i + 1) / n), (255, 255, 255, a), w=0)


def ripple(c, x, y, t, t0, n=3):
    """Ondas en la red cuando entra el balón."""
    if t < t0:
        return
    for i in range(n):
        k = (t - t0) * 2.2 - i * 0.18
        if 0 < k < 1:
            r = 30 + 160 * k
            c.e(x - r, y - r * 0.6, x + r, y + r * 0.6, None, (255, 255, 255, int(220 * (1 - k))), 5)


def camera2(bg, fg, shots, t, dur, W, H, **kw):
    """camera() con barrido (whip pan) en cada corte en lugar del destello blanco."""
    import numpy as np
    kw.setdefault("flash", False)
    img = camera(bg, fg, shots, t, dur, W, H, **kw)
    n = len(shots)
    seg = dur / n
    i = min(int(t / seg), n - 1)
    lt = t - i * seg
    if i > 0 and lt < 0.12:
        k = 1 - lt / 0.12
        a = np.asarray(img, dtype="float32")
        acc = np.zeros_like(a)
        steps = 7
        for j in range(steps):
            acc += np.roll(a, int((j - steps // 2) * 26 * k), axis=1)
        img = Image.fromarray((acc / steps).astype("uint8"))
    return img


# ------------------------------------------------------------------ personaje
def bean(c, x, y, s=1.0, body=(240, 170, 40), skin=SKIN[1], hair="pelo", hcol=(40, 30, 26), emo="serio",
         talk=False, t=0.0, arms="relax", arm_r=None, legs="pie", phase=0.0, vest=False, beard=False,
         num="", look=0.0, prop=None, chain=False, blink_off=0.0, sq=1.0, legcol=(36, 44, 92), venda=None, kick=None, kdir=-1, ref=False, gloves=False, bigote=False):
    """(x, y) = pies. Altura total ≈ 470*s."""
    if kick is not None and kick >= 1:
        kick = None
    if kick is not None:
        # anticipación (se encoge) y estirón al golpear
        sq = sq * (1 - 0.08 * math.sin(min(1, kick / 0.45) * math.pi) + 0.06 * max(0, math.sin((kick - 0.45) / 0.55 * math.pi)))
    if legs == "anda":
        y = y - abs(math.sin(phase)) * 8 * s           # rebote al andar
    sy = s * sq
    hip = y - 150 * s
    bh, bw = 200 * sy, 66 * s / math.sqrt(sq)
    by = hip - bh * 0.42                      # centro del cuerpo
    hr = 64 * s
    hy = by - bh * 0.5 - hr * 0.62
    breath = 1 + 0.015 * math.sin(t * 3 + x)
    # sombra en el suelo
    c.e(x - 70 * s, y - 10 * s, x + 70 * s, y + 10 * s, (0, 0, 0, 60) if c.im.mode == "RGBA" else (60, 60, 70), w=0)
    # piernas de palo
    for sg in (-1, 1):
        if kick is not None and sg == -kdir:
            # pierna de chute: atrás (carga), barrido y seguimiento
            if kick < 0.45:
                a = -0.9 * _e(kick / 0.45)
            else:
                a = -0.9 + 2.3 * _e((kick - 0.45) / 0.3)
            a *= kdir
            h0 = (x + sg * 22 * s, hip + 10 * s)
            L = 150 * s
            foot = (h0[0] + L * math.sin(a), h0[1] + L * math.cos(a) * 0.95)
            knee = (h0[0] + L * 0.5 * math.sin(a) + kdir * 14 * s, h0[1] + L * 0.5 * math.cos(a))
            pts = [h0, knee, foot]
        elif legs == "anda":
            k = math.sin(phase + (0 if sg > 0 else math.pi))
            foot = (x + sg * 16 * s + k * 34 * s, y + 8 * s * abs(math.sin(phase)) - max(0, k) * 14 * s)
            knee = (x + sg * 18 * s + k * 22 * s, y - 72 * s)
            pts = [(x + sg * 22 * s, hip + 10 * s), knee, foot]
        elif legs == "corre":
            k = math.sin(phase + (0 if sg > 0 else math.pi))
            foot = (x + sg * 14 * s + k * 50 * s, y - max(0, k) * 30 * s)
            knee = (x + sg * 14 * s + k * 30 * s, y - 70 * s)
            pts = [(x + sg * 22 * s, hip + 10 * s), knee, foot]
        elif legs == "abiertas":
            pts = [(x + sg * 24 * s, hip + 10 * s), (x + sg * 56 * s, y)]
        else:
            pts = [(x + sg * 22 * s, hip + 10 * s), (x + sg * 24 * s, y)]
        c.l(pts, legcol, 9 * s)
        fx, fy = pts[-1]
        c.e(fx - 22 * s + sg * 10 * s, fy - 10 * s, fx + 22 * s + sg * 10 * s, fy + 6 * s, (40, 30, 26), INK, 3 * s)

    def arm(sg, pose):
        shx, shy = x + sg * bw * 0.82, by - bh * 0.18
        if pose == "arriba":
            hx, hy2 = x + sg * 120 * s, by - 210 * s + 8 * s * math.sin(t * 12 + sg)
            el = (x + sg * 104 * s, by - 100 * s)
        elif pose == "anda":
            sw = math.sin(phase + (math.pi if sg > 0 else 0))
            el, (hx, hy2) = (x + sg * 86 * s + sw * 18 * s, by + 26 * s), (x + sg * 84 * s + sw * 46 * s, by + 92 * s)
        elif pose == "jarras":
            el, (hx, hy2) = (x + sg * 128 * s, by + 10 * s), (x + sg * bw * 0.95, by + 40 * s)
        elif pose == "senala":
            el, (hx, hy2) = (x + sg * 110 * s, by - 50 * s), (x + sg * 190 * s, by - 80 * s)
        elif pose == "taza":
            el, (hx, hy2) = (x + sg * 96 * s, by + 10 * s), (x + sg * 58 * s, by - bh * 0.12)
        elif pose == "oreja":
            el, (hx, hy2) = (x + sg * 104 * s, by - 40 * s), (x + sg * hr * 1.0, hy + 6 * s)
        elif pose == "cara":
            el, (hx, hy2) = (x + sg * 96 * s, by - 10 * s), (x + sg * 46 * s, hy + 6 * s)
        elif pose == "abiertos":
            el, (hx, hy2) = (x + sg * 118 * s, by - 60 * s), (x + sg * 176 * s, by - 120 * s + 6 * s * math.sin(t * 6))
        else:
            el, (hx, hy2) = (x + sg * 92 * s, by + 30 * s), (x + sg * 98 * s, by + 96 * s + 3 * s * math.sin(t * 2 + sg))
        c.l([(shx, shy), el, (hx, hy2)], INK, 13 * s)
        c.l([(shx, shy), el, (hx, hy2)], shade(body, 0.75), 8 * s)
        if gloves:   # guantes de portero: mano grande lima con puño blanco
            c.r(hx - 15 * s, hy2 + 8 * s, hx + 15 * s, hy2 + 20 * s, 4 * s, WHITE, INK, 3 * s)
            c.c(hx, hy2, 21 * s, (170, 230, 60), INK, 4 * s)
            c.l([(hx - 8 * s, hy2 - 12 * s), (hx - 8 * s, hy2 + 2 * s)], (110, 170, 30), 3 * s)
            c.l([(hx + 6 * s, hy2 - 12 * s), (hx + 6 * s, hy2 + 2 * s)], (110, 170, 30), 3 * s)
        else:
            c.c(hx, hy2, 11 * s, skin, INK, 3 * s)
        return hx, hy2

    poses = {-1: arms, 1: arm_r or arms}
    front = {k for k, v in poses.items() if v in ("taza", "cara", "oreja")}
    for sg in (-1, 1):
        if sg not in front:
            arm(sg, poses[sg])
    # cuerpo ovalado con volumen (sombra a la derecha, brillo a la izquierda)
    w2, h2 = bw * breath, bh / 2 * breath
    c.e(x - w2, by - h2, x + w2, by + h2, shade(body, 0.78), INK, 6 * s)
    c.e(x - w2 + 5 * s, by - h2 + 5 * s, x + w2 - 22 * s, by + h2 - 12 * s, body, w=0)
    c.e(x - w2 * 0.62, by - h2 * 0.7, x - w2 * 0.25, by - h2 * 0.1, shade(body, 1.12), w=0)
    if vest:
        for yy in (0.05, 0.28):
            c.r(x - w2 + 6 * s, by + h2 * yy - 6 * s, x + w2 - 6 * s, by + h2 * yy + 6 * s, 3 * s, (235, 235, 230), w=0)
        c.r(x - 7 * s, by - h2 + 10 * s, x + 7 * s, by + h2 - 8 * s, 4 * s, (40, 70, 160), w=0)
        for j in range(4):
            c.c(x, by - h2 * 0.6 + j * h2 * 0.45, 3.5 * s, (220, 220, 230), w=0)
    if num:
        c.text(x - 4 * s, by - h2 * 0.55, num, 58 * s, WHITE, 3 * s)
    if ref:
        _ref_kit(c, x, y, s, by, w2, h2)
    if chain:
        c.arc(x - 40 * s, by - h2 - 30 * s, x + 40 * s, by - h2 + 50 * s, 30, 150, (236, 196, 60), 5 * s)
    # pelo que va detrás de la cabeza
    if hair == "afro":
        for k in range(14):
            a = math.pi * (0.95 + 1.1 * k / 13)
            c.c(x + math.cos(a) * hr * 1.15, hy - hr * 0.25 + math.sin(a) * hr * 1.05, hr * 0.42, hcol, INK, 4 * s)
        c.c(x, hy - hr * 0.55, hr * 1.12, hcol, w=0)
    elif hair == "melenon":
        # melena rizada hasta los hombros (detrás)
        for sg in (-1, 1):
            for j in range(4):
                c.c(x + sg * hr * 1.05, hy - hr * 0.4 + hr * 0.42 * j, hr * 0.32, hcol, INK, 4 * s)
    elif hair == "cinta":
        c.r(x - hr * 1.18, hy - hr * 0.6, x + hr * 1.18, hy + hr * 1.25, hr * 0.5, hcol, INK, 5 * s)
        for sg in (-1, 1):
            for j in range(3):
                c.c(x + sg * hr * 1.12, hy + hr * (0.0 + 0.45 * j), hr * 0.24, hcol, INK, 3 * s)
    # cabeza con volumen
    c.c(x, hy, hr, shade(skin, 0.86), INK, 6 * s)
    c.c(x - 7 * s, hy - 6 * s, hr - 10 * s, skin, w=0)
    if beard:
        c.chord(x - hr + 6 * s, hy - hr * 0.1, x + hr - 6 * s, hy + hr - 4 * s, 10, 170, shade(skin, 0.72), w=0)
    # pelo / gorra
    if hair == "gorra":
        c.chord(x - hr * 1.02, hy - hr * 1.08, x + hr * 1.02, hy + hr * 0.25, 180, 360, (214, 66, 40), INK, 5 * s)
        c.r(x - hr * 1.05, hy - hr * 0.42, x + hr * 0.85, hy - hr * 0.28, 5 * s, (180, 50, 30), INK, 4 * s)
    elif hair == "tupe":
        c.chord(x - hr * 1.04, hy - hr * 1.1, x + hr * 1.04, hy + hr * 0.2, 180, 360, hcol, INK, 5 * s)
        c.e(x - hr * 0.75, hy - hr * 1.85, x + hr * 1.35, hy - hr * 0.65, hcol, INK, 5 * s)
        c.chord(x - hr * 1.04, hy - hr * 1.1, x + hr * 1.04, hy + hr * 0.2, 180, 360, hcol, w=0)
        c.arc(x - hr * 0.5, hy - hr * 1.7, x + hr * 1.1, hy - hr * 0.9, 200, 320, (130, 130, 170), 6 * s)
    elif hair == "pelo":
        c.chord(x - hr * 1.03, hy - hr * 1.06, x + hr * 1.03, hy + hr * 0.05, 180, 360, hcol, INK, 5 * s)
    elif hair == "melena":
        c.chord(x - hr * 1.1, hy - hr * 1.12, x + hr * 1.1, hy + hr * 0.6, 160, 380, hcol, INK, 5 * s)
    elif hair == "afro":
        for k in range(7):
            a = math.pi * (1.1 + 0.8 * k / 6)
            c.c(x + math.cos(a) * hr * 0.85, hy - hr * 0.2 + math.sin(a) * hr * 0.8, hr * 0.36, hcol, w=0)
        for k in range(6):
            c.c(x + (k - 2.5) * hr * 0.3, hy - hr * 1.45 - 6 * s * (k % 2), 7 * s, tuple(min(255, v + 30) for v in hcol), w=0)
    elif hair == "cinta":
        c.chord(x - hr * 1.05, hy - hr * 1.12, x + hr * 1.05, hy + hr * 0.1, 180, 360, hcol, INK, 5 * s)
        c.r(x - hr * 1.0, hy - hr * 0.62, x + hr * 1.0, hy - hr * 0.42, 6 * s, WHITE, INK, 4 * s)
    elif hair == "melenon":
        for k in range(8):
            a = math.pi * (1.0 + k / 7)
            c.c(x + math.cos(a) * hr * 0.92, hy - hr * 0.15 + math.sin(a) * hr * 0.92, hr * 0.32, hcol, INK, 4 * s)
        c.chord(x - hr * 0.95, hy - hr * 1.05, x + hr * 0.95, hy + hr * 0.05, 180, 360, hcol, w=0)
    elif hair == "rizado":
        # mata de rizos oscuros, sin puntas de color
        c.chord(x - hr * 1.05, hy - hr * 1.06, x + hr * 1.05, hy + hr * 0.2, 180, 360, hcol, INK, 5 * s)
        for k in range(9):
            a = math.pi * (1.0 + k / 8)
            c.c(x + math.cos(a) * hr * 0.98, hy - hr * 0.12 + math.sin(a) * hr * 0.98, hr * 0.27, hcol, INK, 4 * s)
        c.chord(x - hr * 0.9, hy - hr * 0.98, x + hr * 0.9, hy + hr * 0.1, 180, 360, hcol, w=0)
    elif hair == "cascao":
        # cabeza rapada con un triángulo de pelo delante
        c.p([(x - hr * 0.34, hy - hr * 0.66), (x + hr * 0.34, hy - hr * 0.66), (x, hy - hr * 0.97)], hcol, INK, 3 * s)
    elif hair == "rizos":
        # lados cortos y mata de rizos arriba con las puntas rubias
        c.chord(x - hr * 1.03, hy - hr * 1.04, x + hr * 1.03, hy + hr * 0.1, 180, 360, hcol, INK, 5 * s)
        curls = [(-0.78, -0.72), (-0.5, -1.0), (-0.15, -1.12), (0.2, -1.1), (0.52, -0.98), (0.8, -0.72),
                 (-0.32, -0.8), (0.05, -0.85), (0.38, -0.8)]
        for ox, oy in curls:
            c.c(x + ox * hr, hy + oy * hr, hr * 0.27, hcol, INK, 4 * s)
        for ox, oy in curls[1:6]:
            c.c(x + ox * hr - hr * 0.04, hy + oy * hr - hr * 0.08, hr * 0.12, (222, 176, 92), w=0)
    # cara seria: ojos pequeños, cejas gruesas
    ex, ey = 24 * s, hy + 2 * s
    blink = ((t + blink_off) % 3.7) < 0.12
    for sg in (-1, 1):
        px = x + sg * ex + look * 6 * s
        if emo in ("feliz", "cerrados") or blink:
            a0, a1 = (200, 340) if emo == "feliz" else (20, 160)
            c.arc(px - 10 * s, ey - 8 * s, px + 10 * s, ey + 8 * s, a0, a1, INK, 4 * s)
        elif emo == "dolor":
            c.l([(px - 8 * s, ey - 8 * s), (px + 8 * s, ey + 8 * s)], INK, 4 * s)
            c.l([(px - 8 * s, ey + 8 * s), (px + 8 * s, ey - 8 * s)], INK, 4 * s)
        elif emo in ("sorpresa", "miedo"):
            c.c(px, ey, 13 * s, WHITE, INK, 3 * s)
            c.c(px + look * 3 * s, ey + 1 * s, 5 * s, INK, w=0)
        elif emo == "aburrido":
            c.c(px, ey + 4 * s, 6 * s, INK, w=0)
            c.l([(px - 15 * s, ey - 2 * s), (px + 15 * s, ey - 2 * s)], INK, 6 * s)
            c.l([(px - 13 * s, ey - 11 * s), (px + 13 * s, ey - 11 * s)], INK, 5 * s)
        elif emo == "serio":
            c.l([(px - 11 * s, ey), (px + 11 * s, ey)], INK, 5 * s)
        else:
            c.c(px, ey, 5.5 * s, INK, w=0)
    br = {"serio": (6, 0), "enfado": (12, -10), "picaro": (10, -6), "miedo": (-6, 8), "sorpresa": (-10, 0),
          "feliz": (-4, 0), "dolor": (8, -6), "cerrados": (-4, 6)}.get(emo, (0, 0))
    for sg in (-1, 1):
        px = x + sg * ex
        c.l([(px - sg * 16 * s, ey - 22 * s - br[0] * 0.2 * s + br[1] * s), (px + sg * 14 * s, ey - 22 * s - br[0] * s * 0.6)], INK, 7 * s)
    # boca
    my = hy + 34 * s
    if talk:
        o = 3 + 9 * abs(math.sin(t * 16))
        c.e(x - 9 * s, my - 3 * s, x + 9 * s, my + o * s, (90, 20, 30), INK, 3 * s)
    elif emo in ("feliz", "picaro"):
        c.arc(x - 16 * s, my - 14 * s, x + 16 * s, my + 6 * s, 20, 160, INK, 4 * s)
    elif emo in ("sorpresa", "dolor"):
        c.e(x - 8 * s, my - 4 * s, x + 8 * s, my + 14 * s, (90, 20, 30), INK, 3 * s)
    elif emo == "miedo":
        c.l([(x - 14 * s + i * 4 * s, my + (3 if i % 2 else -3) * s) for i in range(8)], INK, 3.5 * s)
    else:  # serio / enfado: boca pequeña hacia abajo
        c.arc(x - 12 * s, my - 2 * s, x + 12 * s, my + 14 * s, 200, 340, INK, 4 * s)
    if bigote:   # bigote espeso
        for sg in (-1, 1):
            c.e(x + sg * 2 * s - (30 * s if sg < 0 else 0), hy + 20 * s, x + sg * 2 * s + (30 * s if sg > 0 else 0), hy + 38 * s,
                (40, 28, 22), INK, 3 * s)
    if venda is not None:
        # venda negra: venda=0 en la frente, venda=1 tapando los ojos
        vy = (hy - hr * 0.62) + (ey - (hy - hr * 0.62)) * max(0.0, min(1.0, venda))
        c.r(x - hr * 1.03, vy - 15 * s, x + hr * 1.03, vy + 15 * s, 8 * s, (34, 34, 44), INK, 3 * s)
        for k2 in (0, 1):
            ang = 0.5 + k2 * 0.5 + 0.15 * math.sin(t * 5 + k2)
            c.l([(x + hr * 0.98, vy), (x + hr * 0.98 + 44 * s * math.cos(ang), vy + 44 * s * math.sin(ang))], (34, 34, 44), 10 * s)
    for sg in (-1, 1):
        if sg in front:
            hx, hy2 = arm(sg, poses[sg])
            if poses[sg] == "taza":
                # taza de café: cuerpo ancho, asa, café dentro y vapor ondulado
                mw, mh = 30 * s, 46 * s
                mx, mt = hx, hy2 - mh * 0.75
                c.arc(mx + mw - 10 * s, mt + 8 * s, mx + mw + 22 * s, mt + 34 * s, 270, 90, INK, 7 * s)
                c.r(mx - mw, mt, mx + mw, mt + mh, 8 * s, (236, 236, 240), INK, 4 * s)
                c.r(mx - mw, mt + mh * 0.35, mx + mw, mt + mh * 0.55, 0, (200, 60, 50), w=0)
                c.e(mx - mw, mt - 6 * s, mx + mw, mt + 8 * s, (110, 70, 40), INK, 4 * s)
                c.c(hx - mw * 0.2, hy2 + 4 * s, 11 * s, BLANCO if False else (250, 250, 248), INK, 3 * s)
                for j in (-1, 1):
                    ph = t * 3 + j
                    pts = [(mx + j * 10 * s + 7 * s * math.sin(ph + k * 0.9), mt - 14 * s - k * 12 * s) for k in range(6)]
                    c.l(pts, (230, 232, 240), 4 * s)


def _ref_kit(c, x, y, s, by, w2, h2):
    """Uniforme de árbitro: cuello blanco en V, escudo, bolsillo con tarjetas, silbato al cuello, medias con raya."""
    top = by - h2
    # medias negras con vuelta blanca
    for sg in (-1, 1):
        lx = x + sg * 23 * s
        c.r(lx - 9 * s, y - 52 * s, lx + 9 * s, y - 40 * s, 3 * s, WHITE, INK, 2 * s)
    # cuello blanco en V
    c.p([(x - 40 * s, top + 12 * s), (x, top + 58 * s), (x + 40 * s, top + 12 * s), (x + 24 * s, top + 4 * s),
         (x, top + 34 * s), (x - 24 * s, top + 4 * s)], WHITE, INK, 3 * s)
    # cordón y silbato plateado
    c.l([(x - 18 * s, top + 10 * s), (x - 6 * s, top + 70 * s), (x + 8 * s, top + 78 * s)], (226, 226, 232), 3 * s)
    c.l([(x + 18 * s, top + 10 * s), (x + 14 * s, top + 60 * s), (x + 8 * s, top + 78 * s)], (226, 226, 232), 3 * s)
    c.r(x - 4 * s, top + 70 * s, x + 34 * s, top + 92 * s, 9 * s, (214, 216, 224), INK, 3 * s)
    c.c(x + 1 * s, top + 81 * s, 8 * s, (150, 152, 160), INK, 2 * s)
    # escudo en el pecho (lado derecho del dibujo)
    c.p([(x + 26 * s, top + 52 * s), (x + 48 * s, top + 52 * s), (x + 48 * s, top + 70 * s), (x + 37 * s, top + 80 * s),
         (x + 26 * s, top + 70 * s)], (250, 205, 40), INK, 3 * s)
    # bolsillo con tarjeta amarilla y roja asomando
    px, py = x - 40 * s, top + 64 * s
    c.r(px - 6 * s, py - 18 * s, px + 6 * s, py + 2 * s, 2 * s, (250, 214, 30), INK, 2 * s)
    c.r(px + 2 * s, py - 14 * s, px + 14 * s, py + 2 * s, 2 * s, (222, 40, 36), INK, 2 * s)
    c.r(px - 14 * s, py, px + 16 * s, py + 22 * s, 3 * s, (30, 30, 36), (230, 230, 236), 2.5 * s)


def bean_head(x, y, s=1.0):
    bh = 200 * s
    by = y - 150 * s - bh * 0.42
    return x, by - bh * 0.5 - 64 * s * 0.62


# ------------------------------------------------------------------ escenarios con perspectiva
def _lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def locker_persp(c, W, H, t, vp=(0.62, 0.40)):
    """Vestuario visto en diagonal: pared del fondo, pared izquierda en fuga, suelo de baldosas."""
    vx, vy = W * vp[0], H * vp[1]
    c.r(0, 0, W, H, 0, (70, 82, 120), w=0)
    back = [(W * 0.45, H * 0.10), (W * 1.05, H * 0.10), (W * 1.05, H * 0.60), (W * 0.45, H * 0.60)]
    c.p(back, (92, 106, 150), INK, 4)
    # taquillas en la pared del fondo
    for i in range(5):
        x0 = W * 0.47 + i * W * 0.12
        c.r(x0, H * 0.16, x0 + W * 0.11, H * 0.58, 6, (110, 128, 178), INK, 3)
        c.r(x0 + 14, H * 0.20, x0 + W * 0.07, H * 0.21, 2, (60, 70, 100), w=0)
    # pared izquierda en fuga (cel shading: tono más oscuro)
    c.p([(0, -H * 0.1), (W * 0.45, H * 0.10), (W * 0.45, H * 0.60), (0, H * 0.86)], (58, 68, 104), INK, 4)
    for i in range(1, 4):
        k = i / 4
        top, bot = _lerp((0, -H * 0.1), (W * 0.45, H * 0.10), k), _lerp((0, H * 0.86), (W * 0.45, H * 0.60), k)
        c.l([top, bot], (40, 48, 80), 4)
    # suelo con baldosas que fugan
    c.p([(0, H * 0.86), (W * 0.45, H * 0.60), (W * 1.05, H * 0.60), (W * 1.05, H * 1.05), (0, H * 1.05)], (150, 150, 162), INK, 4)
    for i in range(-6, 10):
        x1 = W * 0.45 + i * W * 0.10
        c.l([(x1, H * 0.60), (W * 0.45 + (x1 - W * 0.45) * 3.2, H * 1.05)], (126, 126, 140), 2.5)
    for j in range(1, 6):
        yy = H * 0.60 + (H * 0.45) * (j / 6) ** 1.6
        c.l([(0, yy + (H * 0.86 - H * 0.60) * (1 - (yy - H * 0.60) / (H * 0.26)) if yy < H * 0.86 else yy), (W, yy)], (126, 126, 140), 2.5)
    # banco
    c.p([(W * 0.50, H * 0.55), (W * 0.98, H * 0.55), (W * 0.98, H * 0.575), (W * 0.50, H * 0.575)], (170, 120, 70), INK, 3)


def pitch_persp(c, W, H, t, seed=4, night=False):
    """Campo visto desde un lateral bajo: grada en fuga, césped con franjas diagonales, cielo de tarde."""
    for i in range(30):
        k = i / 29
        col = tuple(int(a * (1 - k) + b * k) for a, b in zip(*(((14, 18, 44), (40, 46, 90)) if night else ((120, 160, 220), (238, 200, 160)))))
        c.r(0, H * 0.30 * i / 30, W, H * 0.30 * (i + 1) / 30 + 1, 0, col, w=0)
    # grada en diagonal
    gr = [(-W * 0.1, H * 0.06), (W * 1.1, H * 0.24), (W * 1.1, H * 0.40), (-W * 0.1, H * 0.46)]
    c.p(gr, (70, 74, 100), INK, 4)
    rnd = random.Random(seed)
    for row in range(7):
        for i in range(30):
            k = i / 29
            top = _lerp(gr[0], gr[1], k)
            bot = _lerp(gr[3], gr[2], k)
            p = _lerp(top, bot, (row + 0.6) / 7.5)
            sz = 9 * (1.25 - 0.5 * k)
            hop = max(0, math.sin(t * 6 + i + row)) * 5 if rnd.random() < 0.5 else 0
            col = rnd.choice([(220, 70, 60), (70, 110, 210), (235, 235, 235), (240, 190, 60)])
            c.r(p[0] - sz, p[1] - hop, p[0] + sz, p[1] + sz * 1.6 - hop, 3, shade(col, 0.8), w=0)
            c.c(p[0], p[1] - sz * 0.8 - hop, sz * 0.75, rnd.choice(SKIN), w=0)
    # valla publicitaria en fuga
    c.p([(-W * 0.1, H * 0.46), (W * 1.1, H * 0.40), (W * 1.1, H * 0.43), (-W * 0.1, H * 0.50)], (230, 60, 50), INK, 3)
    # césped con franjas que fugan
    c.p([(-W * 0.1, H * 0.50), (W * 1.1, H * 0.43), (W * 1.1, H * 1.05), (-W * 0.1, H * 1.05)], (70, 150, 80), INK, 0)
    for i in range(-4, 12, 2):
        a = (W * 0.1 * i, H * 0.48 - i * 0.006 * H)
        b = (W * 0.1 * (i + 1), H * 0.48 - (i + 1) * 0.006 * H)
        c.p([a, b, (b[0] * 2.4 - W * 0.6, H * 1.05), (a[0] * 2.4 - W * 0.6, H * 1.05)], (84, 166, 92), w=0)
    c.l([(-W * 0.1, H * 0.62), (W * 1.1, H * 0.50)], (240, 240, 240), 6)


def goal_persp(c, x, y, s=1.0):
    """Portería vista de tres cuartos (poste cerca grande, lejos pequeño)."""
    near = [(x, y), (x, y - 300 * s)]
    far = [(x + 430 * s, y - 70 * s), (x + 430 * s, y - 300 * s)]
    c.p([near[1], far[1], (far[1][0] + 60 * s, far[1][1] - 30 * s), (near[1][0] + 80 * s, near[1][1] - 40 * s)], (230, 236, 240, 120), w=0)
    c.p([near[0], far[0], far[1], near[1]], (220, 230, 235, 70), w=0)
    for i in range(1, 12):
        k = i / 12
        c.l([_lerp(near[0], far[0], k), _lerp(near[1], far[1], k)], (235, 240, 245, 150), 1.5)
    for j in range(1, 8):
        k = j / 8
        c.l([_lerp(near[0], near[1], k), _lerp(far[0], far[1], k)], (235, 240, 245, 150), 1.5)
    c.l([near[0], near[1], far[1], far[0]], WHITE, 14 * s)
    c.l([near[0], near[1], far[1], far[0]], INK, 3)


def dust(c, x, y, t, t0, n=7, s=1.0):
    """Nubecillas de polvo que salen a ras de suelo al aterrizar y se desvanecen (0,7 s)."""
    k = (t - t0) / 0.7
    if not 0 <= k <= 1:
        return
    rnd = random.Random(int(x) * 7 + int(y))
    a = int(220 * (1 - k) ** 1.5)
    for i in range(n):
        d = -1 if i % 2 else 1
        sp = rnd.uniform(0.4, 1.0)
        px = x + d * (30 + 150 * sp * _e(k)) * s
        py = y - (8 + 40 * sp * k) * s
        r = (14 + 26 * sp) * (0.6 + 0.8 * k) * s
        c.c(px, py, r, (236, 228, 214, a), (60, 52, 46, a), 2.5)


def burst(c, txt, x, y, t, t0, size=74, col=(255, 214, 40), hold=0.9, ang=-8):
    """Onomatopeya cómic: estrella de pinchos + texto. Entra con rebote, queda fija y se apaga."""
    k = t - t0
    if not 0 <= k <= hold + 0.2:
        return
    sc = min(1.0, k / 0.12) * (1 + 0.18 * math.sin(min(1.0, k / 0.3) * math.pi))
    a = 255 if k < hold else int(255 * (1 - (k - hold) / 0.2))
    R, r, N = 120 * sc * size / 74, 78 * sc * size / 74, 12
    pts = []
    for i in range(2 * N):
        rr = R if i % 2 == 0 else r
        th = math.radians(ang) + i * math.pi / N
        pts.append((x + rr * math.cos(th) * 1.25, y + rr * math.sin(th)))
    c.p(pts, col + (a,), INK + (a,), 5)
    if sc > 0.3:
        from .anim_extra import font
        fs = size * sc
        tw = c.d.textlength(txt, font=font(int(fs * K))) / K
        c.d.text(((x - tw / 2) * K, (y - fs * 0.62) * K), txt, font=font(int(fs * K)), fill=(230, 40, 30, a),
                 stroke_width=int(6 * K), stroke_fill=INK + (a,))


def speed_lines(c, x, y, t, t0, n=14, r0=90, r1=230, dur=0.35):
    """Líneas de velocidad radiales alrededor del impacto."""
    k = (t - t0) / dur
    if not 0 <= k <= 1:
        return
    rnd = random.Random(int(t0 * 100))
    for i in range(n):
        th = i * 2 * math.pi / n + rnd.uniform(-0.15, 0.15)
        a, b = r0 + 60 * k, r1 + 40 * k
        c.l([(x + a * math.cos(th), y + a * math.sin(th)), (x + b * math.cos(th), y + b * math.sin(th))],
            INK + (int(230 * (1 - k)),), 5)


# ------------------------------------------------------------------ escenas demo
def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs = []
    if kind == "x_bn_vestuario":
        locker_persp(b, W, H, t)
        bean(f, W * 0.72, H * 0.80, 0.95, (230, 160, 40), BLANCO, "gorra", vest=True, emo="aburrido",
             t=t, arms="relax", legcol=(40, 50, 100))
        bean(f, W * 0.24, H * 0.98, 1.45, (120, 40, 30), BLANCO, "tupe", (30, 24, 34), emo="picaro", t=t,
             arms="relax", arm_r="taza", chain=True, talk=dur * 0.5 < t < dur * 0.8, look=0.6)
        hx, hy = bean_head(W * 0.24, H * 0.98, 1.45)
        px, py = bean_head(W * 0.72, H * 0.80, 0.95)
        img = camera(b.im, f.im, [(cx, H * 0.52, 1.0), (px, py + 80, 1.9), (hx + 60, hy + 60, 1.7)], t, dur, W, H)
        signs.append(("¿PORTERO?", 0.22, dur * 0.36))
        tilt = 0 if t < dur / 3 else (5 if t < 2 * dur / 3 else -4)
    elif kind == "x_bn_campo":
        pitch_persp(b, W, H, t)
        goal_persp(f, W * 0.12, H * 0.80, 1.1)
        dive = _e((t - dur * 0.45) / 0.3)
        kx, ky = W * 0.42 + 110 * dive, H * 0.80 - 90 * math.sin(dive * math.pi)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        bean(tmp, kx, ky, 0.9, (255, 140, 30), BLANCO, "pelo", emo="miedo" if dive < 0.9 else "dolor", t=t,
             arms="abiertos" if dive < 0.2 else "arriba", legs="abiertas", num="1")
        f.im.alpha_composite(tmp.im.rotate(-75 * dive, resample=Image.BICUBIC, center=(kx * K, (ky - 200) * K)))
        u = _e((t - dur * 0.40) / 0.45)
        ball2(f, W * 0.95 - (W * 0.95 - W * 0.24) * u, H * 0.92 - (H * 0.92 - H * 0.70) * u - 160 * math.sin(u * math.pi), 30 - 8 * u, t * 9)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0), (W * 0.52, H * 0.62, 1.45)], t, dur, W, H, shake=8 if dive > 0.95 and t < dur * 0.9 else 0)
        if dive >= 1:
            signs.append(("0 - 1", 0.22, dur * 0.78))
        tilt, wet = (-6 if t > dur / 2 else 0), True
    elif kind == "x_bn_balon":
        # primer plano del balón en el punto de penalti, bajo la lluvia, estadio desenfocado detrás
        pitch_persp(b, W, H, t)
        from PIL import ImageFilter
        b.im = b.im.filter(ImageFilter.GaussianBlur(9 * K))
        f.e(W * 0.22, H * 0.735, W * 0.78, H * 0.785, (235, 238, 235), INK, 4)
        f.e(W * 0.26, H * 0.74, W * 0.74, H * 0.77, (40, 70, 40, 90), w=0)
        bb = 1.0
        ball2(f, cx, H * 0.62, 210 * bb, 0.3)
        img = camera(b.im, f.im, [(cx, H * 0.55, 1.0 + 0.15 * t / dur)], t, dur, W, H, blur_close=False)
        signs.append(("ÚLTIMO PENALTI", 0.22, 0.2))
        tilt, wet = 3 * math.sin(t * 1.5), True
    elif kind in ("x_bn_chute", "x_bn_pum"):
        # demo de mejoras: chute con carga, estela y sombra, estirada girada, red que ondea, barridos entre planos
        pitch_persp(b, W, H, t, seed=3)
        goal_persp(f, W * 0.08, H * 0.72, 0.95)
        seg = dur / 3
        kick = t / (seg * 0.9)
        px, py = W * 0.74, H * 0.96
        bean(f, px, py, 1.1, (40, 100, 210), BLANCO, "pelo", emo="serio" if kick < 0.5 else ("sorpresa" if kick < 2.3 else "feliz"), t=t, num="9",
             kick=kick, kdir=-1, arms="abiertos" if 0.3 < kick < 0.9 else ("arriba" if kick > 2.3 else "relax"))
        T0, T1 = seg * 0.62, seg * 2.15                        # vuelo del balón
        gx, gy = W * 0.20, H * 0.60                            # punto de entrada en la red
        def bpos(tt):
            u = _e(max(0.0, min(1.0, (tt - T0) / (T1 - T0))))
            return (W * 0.66 - (W * 0.66 - gx) * u, H * 0.95 - (H * 0.95 - gy) * u - 260 * math.sin(u * math.pi)), u
        (bx, by), u = bpos(t)
        dive = _e((t - seg * 1.3) / (seg * 0.6))
        kx, ky = W * 0.30 + 120 * dive, H * 0.72 - 70 * math.sin(dive * math.pi)
        tmp = C((W, H), "RGBA", (0, 0, 0, 0))
        bean(tmp, kx, ky, 0.62, (255, 140, 30), BLANCO, "pelo", emo="miedo" if dive < 0.8 else "dolor", t=t, num="1",
             arms="abiertos" if dive < 0.2 else "arriba", legs="abiertas")
        f.im.alpha_composite(tmp.im.rotate(-70 * dive, resample=Image.BICUBIC, center=(kx * K, (ky - 150) * K)))
        if 0 < u < 1:
            trail = [bpos(t - k * 0.035)[0] for k in range(6, 0, -1)] + [(bx, by)]
            ball_fx(f, trail, 30 - 10 * u, ground=H * 0.94 - (H * 0.94 - H * 0.71) * u)
        ball2(f, bx + (6 * math.sin(t * 50) if u >= 1 and t - T1 < 0.3 else 0), by, 30 - 10 * u, t * 10)
        ripple(f, gx, gy, t, T1)
        if kind == "x_bn_pum":
            TL = seg * 1.9                                     # el portero toca el suelo
            speed_lines(f, W * 0.66, H * 0.93, t, T0)
            burst(f, "¡PAM!", W * 0.57, H * 0.88, t, T0, 46)
            dust(f, kx + 30, H * 0.735, t, TL, s=0.6)
            burst(f, "¡PUM!", W * 0.38, H * 0.52, t, TL, 40, col=(255, 255, 255))
        if u >= 1:
            confetti(f, W, H, t, T1 + 0.2)
        img = camera2(b.im, f.im, [(px - 40, H * 0.74, 1.6), (W * 0.48, H * 0.66, 1.05), (gx + 60, gy + 40, 1.9)], t, dur, W, H,
                      shake=10 if 0 < t - T1 < 0.25 else 0)
        if u >= 1:
            signs.append(("GOL", 0.22, T1))
        tilt, wet = (4 if t < seg else (0 if t < 2 * seg else -3)), False
    else:
        return Image.new("RGB", (int(W), int(H)))
    if kind == "x_bn_vestuario":
        wet = False
    img = dutch(img, tilt)
    if wet:
        img = rain(img, t)
    img = vignette(img, 0.3)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
