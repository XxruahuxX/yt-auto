"""Storytime con personajes «toon» de calidad (prefijo x_mt_): historia «Mentí para jugar la final».

Se dibuja a resolución doble (K=2) y se reduce al encuadrar: bordes suaves.
Personajes con contorno, sombreado, ojos con pupilas y parpadeo, cejas y bocas por emoción.
Fondo y personajes en capas: el fondo se desenfoca en los primeros planos.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFilter

from . import anim as A
from .anim_extra import font
from .anim_serie import stamp

K = 2
OUT = (16, 14, 24)
WHITE = (255, 255, 255)
YEL, RED, GREEN, CYAN = (255, 214, 10), (225, 50, 60), (60, 200, 110), (60, 200, 255)
SKIN = [(255, 214, 180), (236, 180, 140), (196, 134, 92), (130, 86, 58)]
TEAM = (30, 110, 230)
RIVAL = (220, 50, 60)
KEEPER = (255, 150, 30)


def _e(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class C:
    """Lienzo a resolución K con coordenadas virtuales."""

    def __init__(self, size, mode="RGB", fill=(0, 0, 0)):
        self.im = Image.new(mode, (int(size[0] * K), int(size[1] * K)), fill)
        self.d = ImageDraw.Draw(self.im)

    def e(self, x0, y0, x1, y1, fill, ol=OUT, w=3.0):
        self.d.ellipse([x0 * K, y0 * K, x1 * K, y1 * K], fill=fill, outline=ol if w else None, width=max(1, int(w * K)) if w else 0)

    def c(self, x, y, r, fill, ol=OUT, w=3.0):
        self.e(x - r, y - r, x + r, y + r, fill, ol, w)

    def p(self, pts, fill, ol=OUT, w=3.0):
        P = [(x * K, y * K) for x, y in pts]
        self.d.polygon(P, fill=fill)
        if w:
            self.d.line(P + [P[0]], fill=ol, width=int(w * K), joint="curve")

    def l(self, pts, fill, w):
        self.d.line([(x * K, y * K) for x, y in pts], fill=fill, width=max(1, int(w * K)), joint="curve")

    def r(self, x0, y0, x1, y1, rad, fill, ol=OUT, w=3.0):
        self.d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], int(rad * K), fill=fill, outline=ol if w else None,
                                 width=max(1, int(w * K)) if w else 0)

    def arc(self, x0, y0, x1, y1, a0, a1, fill, w):
        self.d.arc([x0 * K, y0 * K, x1 * K, y1 * K], a0, a1, fill=fill, width=max(1, int(w * K)))

    def chord(self, x0, y0, x1, y1, a0, a1, fill, ol=OUT, w=3.0):
        self.d.chord([x0 * K, y0 * K, x1 * K, y1 * K], a0, a1, fill=fill, outline=ol, width=max(1, int(w * K)))

    def text(self, x, y, s, size, fill, stroke=6, center=True):
        f = font(size * K)
        tw = self.d.textlength(s, font=f)
        self.d.text((x * K - (tw / 2 if center else 0), y * K), s, font=f, fill=fill, stroke_width=int(stroke * K), stroke_fill=OUT)


def limb(c, pts, col, w):
    c.l(pts, OUT, w + 6)
    for x, y in (pts[0], pts[-1]):
        c.c(x, y, (w + 6) / 2, OUT, w=0)
    c.l(pts, col, w)
    for x, y in pts:
        c.c(x, y, w / 2, col, w=0)


# ------------------------------------------------------------------ personaje
ARMS = {
    "relax": lambda sg, sh, hy, t: ((sg * 46, sh + 48), (sg * 50, sh + 96)),
    "arriba": lambda sg, sh, hy, t: ((sg * 58, sh - 40), (sg * 66 + 6 * math.sin(t * 14 + sg), sh - 100)),
    "cara": lambda sg, sh, hy, t: ((sg * 52, sh + 34), (sg * 30, hy + 22)),
    "ojos": lambda sg, sh, hy, t: ((sg * 52, sh + 30), (sg * 20, hy - 2)),
    "abiertos": lambda sg, sh, hy, t: ((sg * 74, sh + 6), (sg * 112, sh - 26 + 4 * math.sin(t * 6))),
    "jarras": lambda sg, sh, hy, t: ((sg * 64, sh + 40), (sg * 36, sh + 86)),
}


def toon(c, x, y, s=1.0, shirt=TEAM, skin=SKIN[0], hair="corto", hcol=(60, 38, 22), shorts=(28, 30, 44),
         emo="feliz", talk=False, t=0.0, look=(0.0, 0.0), arms="relax", arm_r=None, legs="pie", phase=0.0,
         sq=1.0, num="", gloves=None, socks=(240, 240, 245), back=False, extra=(), blink_off=0.0, sweat=False):
    """(x, y) = pies. Altura ≈ 300*s. arms: postura de los dos brazos; arm_r: postura solo del derecho."""
    sy, sx = s * sq, s / math.sqrt(sq)
    hip = y - 92 * sy
    sh = y - 178 * sy
    hy = y - 236 * sy
    hr = 54 * s
    # sombra
    c.e(x - 62 * sx, y - 9 * s, x + 62 * sx, y + 9 * s, (0, 0, 0, 70) if c.im.mode == "RGBA" else shade((40, 120, 60), 0.7), w=0)
    # piernas
    for sg in (-1, 1):
        if legs == "abiertas":
            knee, foot = (x + sg * 34 * sx, y - 48 * sy), (x + sg * 50 * sx, y - 6)
        elif legs == "corre":
            k = math.sin(phase + (0 if sg > 0 else math.pi))
            knee, foot = (x + sg * 10 * sx + k * 26 * sx, y - 50 * sy), (x + sg * 8 * sx + k * 40 * sx, y - 8 - max(0, k) * 24 * s)
        else:
            knee, foot = (x + sg * 18 * sx, y - 48 * sy), (x + sg * 20 * sx, y - 6)
        h0 = (x + sg * 18 * sx, hip)
        limb(c, [h0, knee], skin, 22 * s)
        limb(c, [knee, foot], socks, 22 * s)
        c.e(foot[0] - 22 * s + sg * 6 * s, foot[1] - 12 * s, foot[0] + 22 * s + sg * 6 * s, foot[1] + 8 * s, (30, 30, 36))
    # pantalón
    c.r(x - 44 * sx, hip - 22 * sy, x + 44 * sx, hip + 30 * sy, 12 * s, shorts)

    def arm(sg, pose):
        el, ha = ARMS.get(pose, ARMS["relax"])(sg, 0, hy - sh, t)
        elp = (x + el[0] * sx, sh + el[1] * sy)
        hap = (x + ha[0] * sx, sh + ha[1] * sy)
        if pose in ("cara", "ojos"):
            hap = (x + ha[0] * sx, hy + (ha[1] - (hy - sh)) * sy)
        shp = (x + sg * 38 * sx, sh + 14 * sy)
        limb(c, [shp, elp], shirt, 24 * s)
        limb(c, [elp, hap], skin, 20 * s)
        if gloves:
            c.c(hap[0], hap[1], 22 * s, gloves)
            c.l([(hap[0] - 12 * s, hap[1] - 4 * s), (hap[0] + 12 * s, hap[1] - 4 * s)], shade(gloves, 0.7), 4 * s)
        elif pose == "ojos":
            c.r(hap[0] - 19 * s, hap[1] - 22 * s, hap[0] + 19 * s, hap[1] + 20 * s, 12 * s, skin)
            for j in (-1, 0, 1):
                c.l([(hap[0] + j * 9 * s, hap[1] - 18 * s), (hap[0] + j * 9 * s, hap[1] - 4 * s)], shade(skin, 0.75), 2.5 * s)
        else:
            c.c(hap[0], hap[1], 13 * s, skin)
        return hap

    poses = {-1: arms, 1: arm_r or arms}
    front_cover = poses[1] in ("cara", "ojos") or poses[-1] in ("cara", "ojos")
    if not front_cover:
        arm(-1, poses[-1]); arm(1, poses[1])
    # torso con sombreado
    c.r(x - 48 * sx, sh - 8 * sy, x + 48 * sx, hip + 8 * sy, 26 * s, shirt)
    c.r(x + 14 * sx, sh, x + 44 * sx, hip + 2 * sy, 20 * s, shade(shirt, 0.82), w=0)
    c.p([(x - 16 * sx, sh - 6 * sy), (x, sh + 12 * sy), (x + 16 * sx, sh - 6 * sy)], shade(shirt, 0.6), w=0)
    if num:
        c.text(x - 2 * sx, sh + 18 * sy if not back else sh + 4 * sy, num, (46 if back else 34) * s, WHITE, 3 * s)
    # cabeza
    c.c(x - hr * 0.96, hy + 6 * s, 13 * s, skin)
    c.c(x + hr * 0.96, hy + 6 * s, 13 * s, skin)
    if hair == "largo":
        c.r(x - hr * 1.12, hy - hr * 0.9, x + hr * 1.12, hy + hr * 1.25, 30 * s, hcol)
    c.c(x, hy, hr, shade(skin, 0.9) if not back else skin)
    if not back:
        c.c(x - 6 * s, hy - 4 * s, hr - 7 * s, skin, w=0)
    if back:
        c.chord(x - hr * 1.04, hy - hr * 1.06, x + hr * 1.04, hy + hr * 0.95, 160, 380, hcol)
        if front_cover is False:
            pass
        return
    # pelo
    if hair in ("corto", "largo", "mono"):
        c.chord(x - hr * 1.04, hy - hr * 1.12, x + hr * 1.04, hy + hr * 0.42, 180, 360, hcol)
        c.p([(x - hr * 0.2, hy - hr * 1.05), (x + hr * 0.15, hy - hr * 1.35), (x + hr * 0.3, hy - hr * 0.95)], hcol)
        if hair == "mono":
            c.c(x, hy - hr * 1.15, hr * 0.42, hcol)
    elif hair == "rizo":
        for i in range(9):
            a = math.pi + i / 8 * math.pi
            c.c(x + hr * 0.92 * math.cos(a), hy + hr * 0.75 * math.sin(a) - 6 * s, hr * 0.32, hcol)
    elif hair == "gorra":
        c.chord(x - hr * 1.04, hy - hr * 1.2, x + hr * 1.04, hy + hr * 0.0, 180, 360, (40, 40, 60))
        c.r(x - hr * 0.3, hy - hr * 0.68, x + hr * 1.3, hy - hr * 0.5, 6 * s, (30, 30, 48))
    # cara
    ex = 20 * s
    eyy = hy - 4 * s
    blink = ((t + blink_off) % 3.3) < 0.11
    big = 1.25 if emo in ("sorpresa", "miedo") else 1.0
    for sg in (-1, 1):
        exx = x + sg * ex
        if emo == "dolor":
            c.l([(exx - 9 * s, eyy - 9 * s), (exx + 9 * s, eyy + 9 * s)], OUT, 5 * s)
            c.l([(exx - 9 * s, eyy + 9 * s), (exx + 9 * s, eyy - 9 * s)], OUT, 5 * s)
            continue
        if emo == "cerrados":
            c.arc(exx - 12 * s, eyy - 12 * s, exx + 12 * s, eyy + 6 * s, 20, 160, OUT, 5 * s)
            continue
        if emo == "feliz" and not talk:
            c.arc(exx - 11 * s, eyy - 8 * s, exx + 11 * s, eyy + 10 * s, 200, 340, OUT, 5 * s)
            continue
        if blink:
            c.l([(exx - 11 * s, eyy), (exx + 11 * s, eyy)], OUT, 4 * s)
            continue
        c.e(exx - 13 * s * big, eyy - 16 * s * big, exx + 13 * s * big, eyy + 16 * s * big, WHITE, w=2.5 * s)
        pr = (5 if emo == "miedo" else 8) * s
        px, py = exx + look[0] * 5 * s, eyy + 2 * s + look[1] * 6 * s
        c.c(px, py, pr, OUT, w=0)
        c.c(px - 2.5 * s, py - 3 * s, 2.5 * s, WHITE, w=0)
    # cejas
    br = {"feliz": (2, 2), "enfado": (8, -6), "miedo": (-8, 6), "sorpresa": (-4, -4), "determinado": (8, -4),
          "llora": (-8, 6), "cerrados": (-8, 6), "dolor": (6, -6), "picaro": (6, -4)}.get(emo, (0, 0))
    for sg in (-1, 1):
        exx = x + sg * ex
        ins = br[0] if sg < 0 else br[0]
        c.l([(exx - sg * 12 * s, eyy - 26 * s - ins * s * 0.2 * (1 if sg < 0 else 1) + (br[1] * s if True else 0)),
             (exx + sg * 12 * s, eyy - 26 * s - br[0] * s)], OUT, 5 * s)
    # nariz y mejillas
    c.arc(x - 6 * s, hy + 6 * s, x + 6 * s, hy + 16 * s, 300, 120, shade(skin, 0.7), 3 * s)
    for sg in (-1, 1):
        c.e(x + sg * 30 * s - 9 * s, hy + 14 * s, x + sg * 30 * s + 9 * s, hy + 22 * s, (255, 150, 150), w=0)
    if "tirita" in extra:
        c.r(x - 13 * s, hy + 4 * s, x + 13 * s, hy + 14 * s, 4 * s, (240, 200, 150), w=2 * s)
    if "bigote" in extra:
        c.chord(x - 22 * s, hy + 12 * s, x + 22 * s, hy + 32 * s, 180, 360, (60, 50, 40), w=2 * s)
    # boca
    my = hy + 28 * s
    if talk:
        o = 4 + 10 * abs(math.sin(t * 17))
        c.e(x - 12 * s, my - 2 * s, x + 12 * s, my + o * s, (120, 30, 40), w=2.5 * s)
    elif emo in ("feliz", "picaro"):
        c.chord(x - 20 * s, my - 14 * s, x + 20 * s, my + 14 * s, 0, 180, (120, 30, 40), w=2.5 * s)
        c.chord(x - 10 * s, my + 2 * s, x + 10 * s, my + 13 * s, 0, 180, (240, 110, 120), w=0)
    elif emo in ("sorpresa", "dolor"):
        c.e(x - 10 * s, my - 4 * s, x + 10 * s, my + 18 * s, (120, 30, 40), w=2.5 * s)
    elif emo in ("miedo", "llora", "cerrados"):
        pts = [(x - 16 * s + i * 4 * s, my + 6 * s + (3 if i % 2 else -3) * s) for i in range(9)]
        c.l(pts, OUT, 4 * s)
    elif emo == "enfado":
        c.arc(x - 16 * s, my + 2 * s, x + 16 * s, my + 22 * s, 200, 340, OUT, 5 * s)
    else:
        c.l([(x - 12 * s, my + 6 * s), (x + 12 * s, my + 6 * s)], OUT, 5 * s)
    if emo == "llora":
        for sg in (-1, 1):
            ty = eyy + 16 * s + (t * 160 % 50) * s
            c.e(x + sg * ex - 5 * s, ty, x + sg * ex + 5 * s, ty + 14 * s, CYAN, w=0)
    if sweat or emo == "miedo":
        dy = (t * 60 % 30) * s
        c.p([(x + hr * 0.95, hy - 30 * s + dy), (x + hr * 0.95 - 8 * s, hy - 14 * s + dy), (x + hr * 0.95 + 8 * s, hy - 14 * s + dy)], CYAN, w=2 * s)
        c.c(x + hr * 0.95, hy - 12 * s + dy, 8 * s, CYAN, w=2 * s)
    if front_cover:
        arm(-1, poses[-1]); arm(1, poses[1])


def toon_rot(c, ang, pivot, *a, **kw):
    """Dibuja un toon girado `ang` grados (antihorario) alrededor de `pivot` (coords virtuales)."""
    tmp = C((c.im.size[0] / K, c.im.size[1] / K), "RGBA", (0, 0, 0, 0))
    toon(tmp, *a, **kw)
    im = tmp.im.rotate(ang, resample=Image.BICUBIC, center=(pivot[0] * K, pivot[1] * K))
    c.im.alpha_composite(im)


def head_pos(x, y, s=1.0, sq=1.0):
    return x, y - 236 * s * sq


# ------------------------------------------------------------------ escenarios
def stadium(c, t, W, H, horizon=0.40, night=True, seed=3, glow=True):
    hy = H * horizon
    top, bot = ((10, 14, 40), (40, 50, 100)) if night else ((90, 160, 230), (190, 220, 250))
    for i in range(40):
        k = i / 39
        col = tuple(int(top[j] * (1 - k) + bot[j] * k) for j in range(3))
        c.r(0, hy * i / 40 - 1, W, hy * (i + 1) / 40 + 1, 0, col, w=0)
    # gradas con público vivo
    c.r(0, hy - 260, W, hy + 4, 0, (34, 38, 62), w=0)
    rnd = random.Random(seed)
    for row in range(9):
        yy = hy - 245 + row * 28
        for i in range(int(W / 26) + 2):
            xx = i * 26 + (row % 2) * 13 + rnd.uniform(-4, 4)
            col = rnd.choice([(230, 60, 70), (60, 120, 230), (240, 240, 240), (250, 200, 60), (120, 120, 150)])
            hop = max(0, math.sin(t * 7 + i * 0.7 + row)) * 6 * (1 if rnd.random() < 0.6 else 0)
            c.r(xx - 9, yy + 6 - hop, xx + 9, yy + 26 - hop, 5, shade(col, 0.8), w=0)
            c.c(xx, yy - hop, 7.5, rnd.choice(SKIN), w=0)
    # vallas publicitarias
    c.r(0, hy - 6, W, hy + 30, 0, (20, 24, 40), w=0)
    for i, txt in enumerate(["DATOCRACK", "COPA DEL PUEBLO", "DATOCRACK", "FINAL"]):
        c.text(W * (0.12 + i * 0.26), hy - 2, txt, 22, YEL if i % 2 else WHITE, 2)
    # césped
    for i in range(14):
        y0 = hy + 30 + (H - hy) * ((i / 14) ** 1.5)
        y1 = hy + 30 + (H - hy) * (((i + 1) / 14) ** 1.5)
        c.r(0, y0, W, y1 + 1, 0, (44, 150, 76) if i % 2 else (52, 164, 86), w=0)


def flares(img, pts, t):
    """Destellos de focos sumados (sobre imagen a resolución K)."""
    lay = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x, y in pts:
        r = 60 + 6 * math.sin(t * 3)
        d.ellipse([(x - r) * K, (y - r) * K, (x + r) * K, (y + r) * K], fill=(160, 150, 110))
    lay = lay.filter(ImageFilter.GaussianBlur(30 * K))
    import numpy as np
    return Image.fromarray(np.minimum(np.asarray(img, dtype="uint16") + np.asarray(lay, dtype="uint16"), 255).astype("uint8"))


def goal_front(c, cx, gb, w, h):
    x0, x1, gt = cx - w / 2, cx + w / 2, gb - h
    c.r(x0, gt, x1, gb, 0, (36, 120, 66), w=0)
    for i in range(0, int(w) + 1, 26):
        c.l([(x0 + i, gt), (x0 + i, gb)], (210, 230, 220), 1.5)
    for j in range(0, int(h) + 1, 26):
        c.l([(x0, gt + j), (x1, gt + j)], (210, 230, 220), 1.5)
    c.r(x0 - 12, gt - 12, x1 + 12, gt + 2, 4, WHITE, w=2)
    c.r(x0 - 12, gt - 12, x0 + 2, gb, 4, WHITE, w=2)
    c.r(x1 - 2, gt - 12, x1 + 12, gb, 4, WHITE, w=2)


def ball(c, x, y, r, rot=0.0):
    c.c(x, y, r, WHITE, w=3)
    for i in range(5):
        a = rot + i / 5 * 2 * math.pi
        px, py = x + r * 0.55 * math.cos(a), y + r * 0.55 * math.sin(a)
        c.c(px, py, r * 0.2, OUT, w=0)
    c.c(x, y, r * 0.24, OUT, w=0)


def speedlines(c, cx, cy, W, H, t, n=40, col=(255, 255, 255), inner=0.35):
    rnd = random.Random(int(t * 12))
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r0 = rnd.uniform(inner, inner + 0.15) * max(W, H)
        r1 = max(W, H) * 1.2
        w = rnd.uniform(2, 7)
        c.p([(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a - 0.01 * w), cy + r1 * math.sin(a - 0.01 * w)),
             (cx + r1 * math.cos(a + 0.01 * w), cy + r1 * math.sin(a + 0.01 * w))], col, w=0)


def confetti(c, W, H, t, t0, n=120):
    if t < t0:
        return
    rnd = random.Random(9)
    for i in range(n):
        x0 = rnd.uniform(0, W)
        v = rnd.uniform(180, 380)
        y = -40 + (t - t0) * v - rnd.uniform(0, 400)
        if y < -40 or y > H:
            continue
        x = x0 + 30 * math.sin((t - t0) * 3 + i)
        a = (t - t0) * 8 + i
        col = rnd.choice([YEL, RED, CYAN, GREEN, WHITE, (255, 120, 200)])
        w, h = 12 * abs(math.cos(a)) + 2, 18
        c.p([(x - w, y - h / 2), (x + w, y - h / 2 + 4), (x + w, y + h / 2), (x - w, y + h / 2 - 4)], col, w=0)


def stars(c, x, y, t, r=70, n=5):
    for i in range(n):
        a = t * 5 + i / n * 2 * math.pi
        sx, sy = x + r * math.cos(a), y + r * 0.35 * math.sin(a)
        rr = 14
        c.p([(sx + rr * math.cos(b * math.pi / 5 - math.pi / 2) * (1 if b % 2 == 0 else 0.45),
              sy + rr * math.sin(b * math.pi / 5 - math.pi / 2) * (1 if b % 2 == 0 else 0.45)) for b in range(10)], YEL, w=2)


# ------------------------------------------------------------------ cámara
def camera(bg, fg, shots, t, dur, W, H, blur_close=True, shake=0.0, flash=True, grade=None):
    n = len(shots)
    seg = dur / n
    i = min(int(t / seg), n - 1)
    fx, fy, z = shots[i][:3]
    lt = t - i * seg
    z *= 1 + 0.05 * min(1.0, lt / max(seg, 0.1))
    if i > 0 and lt < 0.1:
        z *= 1.06 - 0.06 * lt / 0.1
    if blur_close and z > 1.35:
        bg = bg.filter(ImageFilter.GaussianBlur(min(10, (z - 1.25) * 6) * K))
    img = bg.copy()
    if fg is not None:
        img.paste(fg, (0, 0), fg)
    jx = 5 * math.sin(t * 2.3) + shake * math.sin(t * 61)
    jy = 4 * math.sin(t * 1.9 + 1) + shake * math.cos(t * 53)
    cw, ch = W / z, H / z
    x0 = min(max(fx + jx - cw / 2, 0), W - cw)
    y0 = min(max(fy + jy - ch / 2, 0), H - ch)
    out = img.crop((int(x0 * K), int(y0 * K), int((x0 + cw) * K), int((y0 + ch) * K))).resize((int(W), int(H)), Image.LANCZOS)
    if flash and i > 0 and lt < 0.07:
        out = Image.blend(out, Image.new("RGB", out.size, WHITE), 0.3 * (1 - lt / 0.07))
    return out


def vignette(im, k=0.45):
    W, H = im.size
    m = Image.new("L", (W // 8, H // 8), 0)
    ImageDraw.Draw(m).ellipse([-W // 18, -H // 22, W // 8 + W // 18, H // 8 + H // 22], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(12)).resize((W, H), Image.BILINEAR)
    return Image.composite(im, Image.blend(im, Image.new("RGB", (W, H)), k), m)


# ------------------------------------------------------------------ escenas
def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    FY = H * 0.70
    bgc = C((W, H))
    fgc = C((W, H), "RGBA", (0, 0, 0, 0))
    b, f = bgc, fgc
    post = []

    if kind == "x_mt_mentira":
        # vestuario: el entrenador pregunta, yo levanto la mano… con los dedos cruzados detrás
        b.r(0, 0, W, H, 0, (46, 58, 84), w=0)
        for i in range(7):
            x0 = i * W / 6 - 30
            b.r(x0, H * 0.22, x0 + W / 6 - 16, H * 0.62, 10, (74, 96, 138))
            b.r(x0 + 24, H * 0.27, x0 + 70, H * 0.28, 3, (40, 50, 70), w=0)
            b.c(x0 + W / 6 - 44, H * 0.42, 6, (200, 200, 210), w=1)
        b.r(0, H * 0.62, W, H, 0, (150, 128, 108), w=0)
        b.r(0, H * 0.58, W, H * 0.63, 6, (170, 120, 70))
        up = _e((t - dur * 0.25) / 0.4)
        toon(f, W * 0.27, FY, 1.35, (70, 70, 84), SKIN[1], "gorra", shorts=(70, 70, 84), emo="miedo" if t < dur * 0.25 else "sorpresa",
             talk=t < dur * 0.25, t=t, arms="jarras", extra=("bigote",), look=(1, 0))
        toon(f, W * 0.70, FY + 10, 1.35, TEAM, SKIN[0], "corto", emo="picaro" if up > 0.5 else "miedo", t=t, num="7",
             arm_r="arriba" if up > 0.5 else "relax", look=(-1, 0), sweat=up > 0.5)
        hx, hy = head_pos(W * 0.70, FY + 10, 1.35)
        chx, chy = head_pos(W * 0.27, FY, 1.35)
        shots = [(cx, H * 0.48, 1.0), (chx + 20, chy + 30, 2.3), (hx, hy + 40, 2.4), None]
        n = min(int(t / (dur / 4)), 3)
        hdx, hdy = W * 0.70 + 66 * 1.35, FY + 10 - 178 * 1.35 - 100 * 1.35
        if up > 0.5:
            # dedos cruzados en la mano levantada
            limb(f, [(hdx - 4, hdy - 6), (hdx + 12, hdy - 44)], SKIN[0], 9)
            limb(f, [(hdx + 6, hdy - 6), (hdx - 10, hdy - 46)], SKIN[0], 9)
            f.c(hdx, hdy, 17, SKIN[0])
        shots[3] = (hdx - 20, hdy + 40, 3.0)
        if n == 3:
            post.append(("stamp", "DEDOS CRUZADOS", 0.21, 3 * dur / 4, YEL, OUT, 48))
        img = camera(bgc.im, fgc.im, shots, t, dur, W, H)
        if t < dur * 0.25:
            post.append(("stamp", "¿ALGUIEN SABE PARAR?", 0.21, 0.2, WHITE, OUT, 44))
    elif kind == "x_mt_dedo":
        b.r(0, 0, W, H, 0, (230, 236, 244), w=0)
        b.r(0, H * 0.62, W, H, 0, (190, 200, 214), w=0)
        b.r(W * 0.05, H * 0.30, W * 0.95, H * 0.62, 30, (245, 248, 252))
        b.r(W * 0.35, H * 0.33, W * 0.65, H * 0.40, 10, (225, 60, 70))
        b.text(cx, H * 0.345, "+ ENFERMERÍA", 36, WHITE, 3)
        toon(f, cx, FY, 1.55, KEEPER, SKIN[2], "rizo", hcol=(30, 20, 14), emo="llora", t=t, arms="relax", arm_r="arriba", num="1")
        # dedo gigante vendado
        hx, hy = head_pos(cx, FY, 1.55)
        fxp, fyp = cx + 66 * 1.55 + 6 * math.sin(t * 14 + 1), FY - 178 * 1.55 - 100 * 1.55
        f.r(fxp - 16, fyp - 90, fxp + 16, fyp + 10, 14, WHITE)
        for j in range(4):
            f.l([(fxp - 16, fyp - 70 + j * 20), (fxp + 16, fyp - 62 + j * 20)], (200, 200, 210), 3)
        img = camera(bgc.im, fgc.im, [(cx, H * 0.48, 1.0), (hx, hy + 30, 2.3), (fxp, fyp - 30, 2.6)], t, dur, W, H)
        post.append(("stamp", "DEDO ROTO", 0.21, dur * 0.3, RED, WHITE, 56))
    elif kind == "x_mt_nunca":
        stadium(b, t, W, H, 0.42)
        k = min(1.0, t / dur)
        slip = _e((t - dur * 0.55) / 0.3)
        sq = 1.0 - 0.15 * math.sin(min(1, slip) * math.pi)
        toon(f, cx + 40 * slip, FY + 6, 1.6, KEEPER, SKIN[0], "corto", emo="miedo" if slip < 0.5 else "sorpresa",
             t=t, num="1", gloves=(120, 240, 120), arms="abiertos", legs="abiertas", sq=sq, look=(0.5 * math.sin(t * 5), 0))
        if slip > 0.3:
            # un guante sale volando
            gx, gy = cx + 140 + 320 * (slip - 0.3), FY - 420 - 260 * math.sin((slip - 0.3) * 2)
            f.c(gx, gy, 30, (120, 240, 120))
        hx, hy = head_pos(cx + 40 * slip, FY + 6, 1.6, sq)
        img = camera(bgc.im, fgc.im, [(cx, H * 0.47, 1.0), (hx, hy + 30, 2.2), (cx + 120, H * 0.40, 1.4)], t, dur, W, H)
        post.append(("stamp", "NUNCA HABÍA SIDO PORTERO", 0.21, 0.3, RED, WHITE, 40))
    elif kind == "x_mt_goles":
        stadium(b, t, W, H, 0.38)
        goal_front(b, cx, H * 0.62, 600, 240)
        half = dur / 2
        n = 1 if t < half else 2
        lt = t - (0 if n == 1 else half)
        dive = _e((lt - 0.25) / 0.35)
        side = 1 if n == 1 else -1
        kx = cx - side * 110 * dive
        ang = side * 75 * dive
        toon_rot(f, ang, (kx, H * 0.62 - 120 * dive), kx, H * 0.62 - 60 * math.sin(dive * math.pi), 1.05, KEEPER, SKIN[0], "corto",
                 emo="miedo" if dive < 0.9 else "dolor", t=t, num="1", gloves=(120, 240, 120), arms="arriba" if dive > 0.2 else "abiertos",
                 legs="abiertas")
        u = _e(lt / 0.5)
        bx = cx + side * 200 * u
        by = H * 0.88 - (H * 0.88 - H * 0.50) * u
        if u < 1:
            for j in range(6):
                f.c(bx - side * 0 + (bx - cx) * -0.04 * j, by + 30 * j, 26 - 3 * j, (255, 255, 255, 60 - 9 * j), w=0)
        ball(f, bx, by, 30 - 6 * u, t * 8)
        # marcador
        post.append(("score", f"0 - {n if u >= 1 else n - 1}"))
        img = camera(bgc.im, fgc.im, [(cx, H * 0.47, 1.0), (cx, H * 0.52, 1.35)], lt % half, half, W, H, shake=6 if u >= 1 and lt < 0.9 else 0)
        if u >= 1:
            post.append(("stamp", "GOL… OTRA VEZ" if n == 2 else "GOL EN EL MINUTO 1", 0.21, (0 if n == 1 else half) + 0.5, RED, WHITE, 46))
    elif kind == "x_mt_madre":
        # mi madre en la grada se tapa los ojos
        stadium(b, t, W, H, 0.75)
        b.r(0, H * 0.70, W, H, 0, (34, 38, 62), w=0)
        toon(f, W * 0.30, H * 0.98, 1.6, (200, 80, 160), SKIN[1], "largo", hcol=(110, 60, 30), shorts=(60, 60, 80),
             emo="miedo", t=t, arms="ojos", blink_off=1)
        toon(f, W * 0.75, H * 0.99, 1.45, (90, 160, 90), SKIN[0], "mono", hcol=(150, 150, 150), emo="sorpresa", t=t, arms="cara",
             extra=("bigote",))
        mx, my = head_pos(W * 0.30, H * 0.98, 1.6)
        img = camera(bgc.im, fgc.im, [(mx + 60, my + 60, 1.8), (cx, my + 60, 1.4)], t, dur, W, H)
        post.append(("stamp", "MI MADRE NO PUEDE MIRAR", 0.21, 0.4, YEL, OUT, 42))
    elif kind == "x_mt_remontada":
        stadium(b, t, W, H, 0.40)
        n = min(2, int(t / (dur / 2.6)))
        for i2, xx in enumerate((0.25, 0.5, 0.75)):
            hop = abs(math.sin(t * 8 + i2)) * 40
            toon(f, W * xx, FY - hop, 1.05, TEAM, SKIN[(i2 + 1) % 4], ["corto", "rizo", "mono"][i2], emo="feliz", t=t,
                 arms="arriba", num=str(9 + i2), blink_off=i2)
        post.append(("score", f"{n} - 2"))
        confetti(f, W, H, t, dur * 0.7, 80)
        img = camera(bgc.im, fgc.im, [(cx, H * 0.47, 1.0), (W * 0.5, H * 0.42, 1.5), (cx, H * 0.40, 1.2)], t, dur, W, H)
        if n >= 2:
            post.append(("stamp", "¡PENALTIS!", 0.21, 2 * dur / 2.6, RED, WHITE, 64))
    elif kind == "x_mt_ultimo":
        # suspense: plano desde detrás del lanzador, empuje lento hacia mi cara
        stadium(b, t, W, H, 0.34, seed=5)
        goal_front(b, cx, H * 0.60, 640, 260)
        breathe = 1 + 0.02 * math.sin(t * 9)
        toon(f, cx, H * 0.60, 1.05 * breathe, KEEPER, SKIN[0], "corto", emo="miedo", t=t, num="1",
             gloves=(120, 240, 120), arms="abiertos", legs="abiertas", look=(0, 0.6))
        toon(f, cx - 230, H * 1.0, 1.9, RIVAL, SKIN[3], "corto", hcol=(20, 14, 10), back=True, num="10", arms="relax")
        ball(f, cx + 40, H * 0.84, 34)
        hx, hy = head_pos(cx, H * 0.60, 1.05)
        z = 1.0 + 2.2 * _e(t / dur)
        img = camera(bgc.im, fgc.im, [(cx, H * 0.48 + (hy - H * 0.48) * _e(t / dur), z)], t, dur, W, H, blur_close=False, flash=False)
        # latido: viñeta roja que pulsa
        beat = max(0.0, math.sin(t * 7.5)) ** 8
        red = Image.new("RGB", img.size, (140, 0, 20))
        img = Image.blend(img, red, 0.18 * beat)
        img = vignette(img, 0.55 + 0.2 * beat)
        post.append(("stamp", "SI LO PARO, CAMPEONES", 0.21, 0.3, YEL, OUT, 44))
    elif kind == "x_mt_nariz":
        stadium(b, t, W, H, 0.34, seed=5)
        goal_front(b, cx, H * 0.66, 700, 300)
        T = dur * 0.38
        hit = t >= T
        if not hit:
            # cámara lenta: el balón se acerca a mi cara, ojos cerrados
            u = t / T
            toon(f, cx, H * 0.70, 1.6, KEEPER, SKIN[0], "corto", emo="cerrados", t=t, num="1", gloves=(120, 240, 120),
                 arms="abiertos", legs="abiertas", sweat=True)
            hx, hy = head_pos(cx, H * 0.70, 1.6)
            r = 20 + 150 * u ** 2
            ball(f, cx + 8, hy + 20 + (1 - u) * 80, r, t * 2)
            speedlines(f, cx, hy, W, H, t, 26, (255, 255, 255), 0.45)
            img = camera(bgc.im, fgc.im, [(cx, hy + 40, 2.0)], t, T, W, H, flash=False)
            post.append(("text", "CÁMARA LENTA", 0.20))
        else:
            lt = t - T
            sq = 0.82 if lt < 0.12 else 1.0
            toon(f, cx, H * 0.70, 1.6, KEEPER, SKIN[0], "corto", emo="dolor" if lt < 1.4 else "feliz", t=t, num="1",
                 gloves=(120, 240, 120), arms="arriba" if lt > 1.4 else "abiertos", legs="abiertas", sq=sq,
                 extra=("tirita",) if lt > 1.4 else ())
            hx, hy = head_pos(cx, H * 0.70, 1.6, sq)
            if lt < 1.4:
                stars(f, hx, hy - 70, t, 80)
            bu = min(1.0, lt / 0.9)
            ball(f, cx + 300 * bu, hy - 40 - 380 * math.sin(bu * math.pi * 0.8), 36, t * 12)
            confetti(f, W, H, t, T + 1.2)
            img = camera(bgc.im, fgc.im, [(hx, hy + 40, 2.0), (cx, H * 0.50, 1.1)], lt, dur - T, W, H, shake=14 if lt < 0.35 else 0)
            if lt < 0.06:
                img = Image.new("RGB", img.size, WHITE)       # fotograma de impacto
            elif lt < 0.12:
                from PIL import ImageOps
                img = ImageOps.invert(img)
            if lt < 1.4:
                post.append(("stamp", "¡PARADA… CON LA NARIZ!", 0.21, T + 0.15, YEL, OUT, 46))
            if lt > 1.4:
                post.append(("stamp", "¡CAMPEONES!", 0.21, T + 1.4, GREEN, WHITE, 64))
    elif kind == "x_mt_muro":
        # cartel del pueblo con mi cara: «EL MURO»
        b.r(0, 0, W, H, 0, (120, 170, 230), w=0)
        b.r(0, H * 0.66, W, H, 0, (160, 150, 130), w=0)
        for i in range(5):
            b.r(i * W / 4 - 40, H * 0.44, i * W / 4 + 60, H * 0.66, 6, shade((210, 190, 160), 0.9 + 0.05 * (i % 2)))
        b.r(W * 0.12, H * 0.20, W * 0.88, H * 0.58, 16, (250, 245, 230), OUT, 6)
        b.r(W * 0.12, H * 0.20, W * 0.88, H * 0.27, 16, RED, OUT, 6)
        b.text(cx, H * 0.207, "HÉROE DEL PUEBLO", 40, WHITE, 3)
        pc = C((W, H), "RGBA", (0, 0, 0, 0))
        toon(pc, cx, H * 0.62, 1.5, KEEPER, SKIN[0], "corto", emo="picaro", t=t, num="1", gloves=(120, 240, 120),
             arms="relax", arm_r="arriba", extra=("tirita",))
        crop = pc.im.crop((int(W * 0.18 * K), int(H * 0.27 * K), int(W * 0.82 * K), int(H * 0.52 * K)))
        b.im.paste(crop, (int(W * 0.18 * K), int(H * 0.28 * K)), crop)
        b.text(cx, H * 0.505, "«EL MURO»", 70, YEL, 6)
        toon(f, W * 0.78, H * 0.98, 1.5, TEAM, SKIN[0], "corto", emo="picaro", talk=t < dur * 0.7, t=t, num="7",
             look=(-1, -0.3), arms="relax", arm_r="arriba", extra=("tirita",))
        img = camera(bgc.im, fgc.im, [(cx, H * 0.40, 1.15), (cx, H * 0.38, 1.6), (W * 0.74, H * 0.62, 1.9)], t, dur, W, H)
        if t > dur * 0.6:
            post.append(("stamp", "Y FUE CON LA NARIZ", 0.21, dur * 0.6, RED, WHITE, 44))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = vignette(img, 0.38) if kind != "x_mt_ultimo" else img
    d = ImageDraw.Draw(img)
    for p in post:
        if p[0] == "stamp":
            _, txt, yy, t0, bgcol, fgcol, size = p
            stamp(img, txt, cx, H * yy, t0, t, bg=bgcol, fg=fgcol, size=size)
        elif p[0] == "score":
            sc = C((W, H), "RGBA", (0, 0, 0, 0))
            sc.r(cx - 150, H * 0.285, cx + 150, H * 0.335, 16, (16, 18, 30, 235), YEL, 4)
            sc.text(cx, H * 0.288, p[1], 54, WHITE, 4)
            img.paste(sc.im.resize((int(W), int(H)), Image.LANCZOS), (0, 0), sc.im.resize((int(W), int(H)), Image.LANCZOS))
        elif p[0] == "text":
            from .anim_serie import text_c
            text_c(d, cx, H * p[2], p[1], 44, WHITE, 6)
    return img
