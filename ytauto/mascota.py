"""Mascota de DatoCrack: monigote de trazo grueso con esqueleto animable y boquita.

Cinemática directa: cada postura son ángulos de hueso (0 = derecha, 90 = abajo).
Los huesos tienen longitud fija, así que al interpolar no se estiran ni se encogen,
y las rodillas siempre doblan hacia delante (el monigote mira a la derecha).

    python -m ytauto.mascota   -> posturas en PNG + vídeo demo
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("/mnt/project-files/yt-auto/canal/mascota")
GREEN_D, STRIPE, YELLOW, WHITE, INK = (6, 46, 28), (9, 56, 34), (255, 214, 10), (255, 255, 255), (24, 24, 30)
K = 2
GROUND = 880
L = dict(spine=230, neck=26, head=92, thigh=150, shin=145, upper=118, fore=110, foot=62)

# ángulos en grados; lift = altura sobre el suelo (saltos)
POSES = {
    "quieto": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=115, lfa=100, rua=65, rfa=80, lift=0),
    "piensa": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=115, lfa=100, rua=45, rfa=-105, lift=0, tilt=10),
    "agacha": dict(spine=-88, lth=140, lsh=72, rth=40, rsh=108, lua=125, lfa=105, rua=55, rfa=75, lift=0),
    "salto": dict(spine=-92, lth=120, lsh=80, rth=60, rsh=100, lua=-145, lfa=-120, rua=-35, rfa=-60, lift=150),
    "celebra": dict(spine=-110, lth=118, lsh=100, rth=62, rsh=98, lua=155, lfa=148, rua=-50, rfa=-88, lift=0, tilt=-15),
    "chuta_atras": dict(spine=-96, lth=96, lsh=92, rth=118, rsh=165, lua=190, lfa=172, rua=40, rfa=70, lift=0),
    "explica": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=112, lfa=98, rua=35, rfa=-25, lift=0, tilt=5),
    "senala": dict(spine=-94, lth=100, lsh=96, rth=80, rsh=84, lua=115, lfa=100, rua=-62, rfa=-78, lift=0, tilt=-12),
    "chuta": dict(spine=-100, lth=98, lsh=96, rth=30, rsh=46, lua=200, lfa=188, rua=30, rfa=60, lift=0),
}


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_ang(a, b, t):
    d = (b - a + 180) % 360 - 180
    return a + d * t


def blend(p, q, t):
    keys = set(p) | set(q)
    return {k: (lerp(p.get(k, 0), q.get(k, 0), t) if k in ("lift", "tilt")
                else lerp_ang(p[k], q[k], t)) for k in keys}


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _go(p, ang, length):
    a = math.radians(ang)
    return (p[0] + length * math.cos(a), p[1] + length * math.sin(a))


def solve(pose, x=500):
    """Posiciones de articulaciones con la cadera en (x, ?) y los pies apoyados en GROUND."""
    hip = (x, 0.0)
    j = {"hip": hip}
    for s in "lr":
        hs = (hip[0] + (6 if s == "r" else -6), hip[1])
        j[s + "k"] = _go(hs, pose[s + "th"], L["thigh"])
        j[s + "f"] = _go(j[s + "k"], pose[s + "sh"], L["shin"])
        j[s + "hs"] = hs
    neck = _go(hip, pose["spine"], L["spine"])
    j["neck"] = neck
    j["sh"] = _go(neck, pose["spine"] + 180, 22)  # hombros un poco por debajo del cuello
    for s in "lr":
        j[s + "e"] = _go(j["sh"], pose[s + "ua"], L["upper"])
        j[s + "h"] = _go(j[s + "e"], pose[s + "fa"], L["fore"])
    j["head"] = _go(neck, pose["spine"] + pose.get("tilt", 0), L["neck"] + L["head"])
    low = max(j["lf"][1], j["rf"][1])
    dy = GROUND - low - pose.get("lift", 0)
    return {k: (v[0], v[1] + dy) for k, v in j.items()}


def _curve(a, j, b, n=40):
    """Curva cuadrática que pasa por la articulación j (codo/rodilla redondeados)."""
    c = (2 * j[0] - (a[0] + b[0]) / 2, 2 * j[1] - (a[1] + b[1]) / 2)
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0],
             (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in (i / n for i in range(n + 1))]


def _tube(d, pts, r0, r1, col):
    n = len(pts) - 1
    for i, (x, y) in enumerate(pts):
        r = lerp(r0, r1, i / n)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def draw(img, pose, col=WHITE, x=500, dx=0, dy=0, scale=1.0, mouth=0.0, k=K):
    j = solve(pose, x)
    s = scale * k
    P = {k: ((v[0] + dx) * s, (v[1] + dy) * s) for k, v in j.items()}
    d = ImageDraw.Draw(img)
    w = 30 * s
    # piernas
    for sd in "lr":
        _tube(d, _curve(P[sd + "hs"], P[sd + "k"], P[sd + "f"]), w, w * 0.8, col)
        fa = (pose[sd + "sh"] - 85) if sd == "r" else (pose[sd + "sh"] + 85)  # pies hacia fuera
        tip = _go(P[sd + "f"], fa, L["foot"] * s)
        _tube(d, [(lerp(P[sd + "f"][0], tip[0], u / 12), lerp(P[sd + "f"][1], tip[1], u / 12)) for u in range(13)], w * 0.8, w * 0.35, col)
    # tronco ligeramente curvo
    mid = ((P["hip"][0] + P["neck"][0]) / 2 + 10 * s, (P["hip"][1] + P["neck"][1]) / 2)
    _tube(d, _curve(P["neck"], mid, P["hip"]), w * 1.05, w * 1.1, col)
    # brazos y puños
    for sd in "lr":
        _tube(d, _curve(P["sh"], P[sd + "e"], P[sd + "h"]), w * 0.9, w * 0.72, col)
        hx, hy = P[sd + "h"]
        d.ellipse([hx - w * 1.15, hy - w * 1.05, hx + w * 1.15, hy + w * 1.05], fill=col)
    # cabeza: aro
    hx, hy = P["head"]
    r = L["head"] * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=col, width=int(w * 0.95))
    # boquita: sonrisa pequeña; abierta (óvalo) cuando habla
    mx, my = hx + r * 0.12, hy + r * 0.32
    if mouth > 0.08:
        mw, mh = r * 0.16, r * (0.06 + 0.16 * mouth)
        d.ellipse([mx - mw, my - mh, mx + mw, my + mh], fill=col)
    else:
        d.arc([mx - r * 0.24, my - r * 0.2, mx + r * 0.24, my + r * 0.1], 25, 155, fill=col, width=max(2, int(w * 0.32)))
    return j


def render_layer(pose, scale=0.35, mouth=0.0, col=WHITE):
    """Devuelve el monigote en una capa RGBA de (1000*scale)^2 px, suavizada."""
    size = int(1000 * scale)
    lay = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    draw(lay, pose, col=col, scale=scale, mouth=mouth, k=2)
    return lay.resize((size, size), Image.LANCZOS)


def ball(img, x, y, r=46, rot=0.0):
    d = ImageDraw.Draw(img)
    x, y, r = x * K, y * K, r * K
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=INK, width=6 * K)
    pts = [(x + r * .38 * math.cos(rot + math.radians(-90 + 72 * i)), y + r * .38 * math.sin(rot + math.radians(-90 + 72 * i))) for i in range(5)]
    d.polygon(pts, fill=INK)


def canvas(w=1000, h=1000, bg=True):
    img = Image.new("RGB" if bg else "RGBA", (w * K, h * K), GREEN_D if bg else (0, 0, 0, 0))
    if bg:
        d = ImageDraw.Draw(img)
        for i in range(0, 8, 2):
            d.rectangle([i * w * K // 8, 0, (i + 1) * w * K // 8, h * K], fill=STRIPE)
    return img


KEYS = [(0.0, "quieto"), (0.6, "quieto"), (1.0, "piensa"), (1.8, "piensa"), (2.1, "agacha"),
        (2.4, "salto"), (2.75, "celebra"), (3.6, "celebra"), (4.0, "quieto"), (4.4, "chuta_atras"),
        (4.62, "chuta"), (5.3, "chuta"), (5.8, "quieto"), (6.4, "quieto")]


def timeline(t):
    for (t0, a), (t1, b) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            return blend(POSES[a], POSES[b], ease((t - t0) / max(t1 - t0, 1e-6)))
    return POSES["quieto"]


def demo(out, fps=30, size=720):
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{size}x{size}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 56 * K)
    kick_x = None
    for i in range(int(6.4 * fps)):
        t = i / fps
        img = canvas()
        pose = timeline(t)
        j = draw(img, pose, dy=3 * math.sin(t * 5) if t < 1.9 or t > 5.8 else 0,
                 mouth=abs(math.sin(t * 12)) if 0.2 < t < 0.9 else 0.0)
        d = ImageDraw.Draw(img)
        if 2.75 < t < 3.6:
            d.text((690 * K, 140 * K), "¡DATO!", font=f, fill=YELLOW)
        if 1.0 < t < 1.8:
            d.text((640 * K, 170 * K), "?", font=f, fill=YELLOW)
        if t >= 3.9:
            bx, by = 640, GROUND - 46
            if t < 4.6:
                ball(img, bx, by)
            else:
                k = (t - 4.6) / 0.7
                ball(img, bx + 520 * k, by - 650 * k + 420 * k * k, rot=k * 12)
        proc.stdin.write(img.resize((size, size), Image.LANCZOS).tobytes())
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    names = ["quieto", "piensa", "agacha", "celebra", "chuta"]
    sheet = Image.new("RGB", (len(names) * 400, 400))
    for i, n in enumerate(names):
        img = canvas()
        draw(img, POSES[n])
        if n == "chuta":
            ball(img, 700, GROUND - 120)
        sheet.paste(img.resize((400, 400), Image.LANCZOS), (i * 400, 0))
    sheet.save(OUT / "monigote_poses.png")
    img = canvas(bg=False)
    draw(img, POSES["celebra"])
    img.resize((800, 800), Image.LANCZOS).save(OUT / "monigote_transparente.png")
    demo(OUT / "monigote_demo.mp4")
