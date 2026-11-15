"""Mascota de DatoCrack: monigote de trazo grueso con esqueleto animable.

    python branding/monigote.py            -> PNG de poses + vídeo demo
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("/mnt/project-files/yt-auto/canal/mascota")
GREEN_D, STRIPE, YELLOW, WHITE, INK = (6, 46, 28), (9, 56, 34), (255, 214, 10), (255, 255, 255), (24, 24, 30)
K = 2  # supermuestreo

# Poses en un lienzo de 1000x1000 (cadera hacia el centro). Articulaciones:
# head, neck, hip, le, lh (codo/mano izq.), re, rh, lk, lf (rodilla/pie izq.), rk, rf
POSES = {
    "quieto": dict(head=(500, 250), neck=(500, 350), hip=(500, 600), le=(420, 470), lh=(395, 590),
                   re=(580, 470), rh=(605, 590), lk=(465, 740), lf=(455, 880), rk=(540, 740), rf=(550, 880)),
    "celebra": dict(head=(445, 250), neck=(490, 345), hip=(540, 590), le=(400, 470), lh=(320, 520),
                    re=(600, 260), rh=(610, 120), lk=(450, 720), lf=(510, 840), rk=(600, 720), rf=(650, 860)),
    "agacha": dict(head=(500, 330), neck=(500, 430), hip=(500, 660), le=(430, 540), lh=(440, 650),
                   re=(570, 540), rh=(560, 650), lk=(440, 760), lf=(455, 890), rk=(565, 760), rf=(550, 890)),
    "salto": dict(head=(500, 160), neck=(500, 260), hip=(500, 500), le=(400, 160), lh=(370, 50),
                  re=(600, 160), rh=(630, 50), lk=(450, 630), lf=(470, 740), rk=(560, 630), rf=(540, 740)),
    "piensa": dict(head=(500, 250), neck=(500, 350), hip=(500, 600), le=(420, 470), lh=(395, 590),
                   re=(600, 440), rh=(540, 330), lk=(465, 740), lf=(455, 880), rk=(540, 740), rf=(550, 880)),
    "chuta_atras": dict(head=(480, 250), neck=(490, 350), hip=(500, 600), le=(420, 430), lh=(360, 380),
                        re=(580, 470), rh=(640, 540), lk=(470, 740), lf=(460, 880), rk=(520, 720), rf=(420, 800)),
    "chuta": dict(head=(470, 260), neck=(485, 360), hip=(500, 600), le=(420, 440), lh=(360, 400),
                  re=(570, 470), rh=(630, 520), lk=(470, 740), lf=(460, 880), rk=(600, 730), rf=(680, 830)),
}


def lerp(a, b, t):
    return a + (b - a) * t


def blend(p, q, t):
    return {k: (lerp(p[k][0], q[k][0], t), lerp(p[k][1], q[k][1], t)) for k in p}


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def stroke(d, a, b, r0, r1, col, n=24):
    for i in range(n + 1):
        t = i / n
        x, y, r = lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(r0, r1, t)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def draw(img, pose, col=WHITE, dx=0, dy=0, scale=1.0, head_r=92):
    d = ImageDraw.Draw(img)
    s = scale * K

    def P(k):
        x, y = pose[k]
        return (x * s + dx * K, y * s + dy * K)
    w = 32 * s
    # tronco: curva cuello -> cadera
    n0, h0 = P("neck"), P("hip")
    c = ((n0[0] + h0[0]) / 2 + (h0[1] - n0[1]) * 0.18, (n0[1] + h0[1]) / 2)
    pts = [((1 - t) ** 2 * n0[0] + 2 * (1 - t) * t * c[0] + t * t * h0[0],
            (1 - t) ** 2 * n0[1] + 2 * (1 - t) * t * c[1] + t * t * h0[1]) for t in (i / 30 for i in range(31))]
    for p, q in zip(pts, pts[1:]):
        stroke(d, p, q, w * 1.05, w * 1.05, col, 3)
    # extremidades (más gruesas cerca del cuerpo)
    for a, b, e in (("neck", "le", "lh"), ("neck", "re", "rh"), ("hip", "lk", "lf"), ("hip", "rk", "rf")):
        stroke(d, P(a), P(b), w * 0.95, w * 0.8, col)
        stroke(d, P(b), P(e), w * 0.8, w * 0.6, col)
    for h in ("lh", "rh"):  # puños
        x, y = P(h)
        d.ellipse([x - w * 1.25, y - w * 1.15, x + w * 1.25, y + w * 1.15], fill=col)
    for k_, f in (("lk", "lf"), ("rk", "rf")):  # pies
        x, y = P(f)
        kx = P(k_)[0]
        sgn = 1
        d.polygon([(x - w * 0.6, y - w * 0.6), (x + w * 0.4, y - w * 0.6), (x + sgn * w * 2.2, y + w * 0.7), (x - w * 0.6, y + w * 0.7)], fill=col)
    # cabeza: aro grueso
    x, y = P("head")
    r = head_r * s
    d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=int(w * 0.95))


def ball(img, x, y, r=48, rot=0.0):
    d = ImageDraw.Draw(img)
    x, y, r = x * K, y * K, r * K
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=INK, width=6 * K)
    pts = [(x + r * .38 * math.cos(rot + math.radians(-90 + 72 * i)), y + r * .38 * math.sin(rot + math.radians(-90 + 72 * i))) for i in range(5)]
    d.polygon(pts, fill=INK)


def canvas(w=1000, h=1000, bg=True):
    img = Image.new("RGBA" if not bg else "RGB", (w * K, h * K), GREEN_D if bg else (0, 0, 0, 0))
    if bg:
        d = ImageDraw.Draw(img)
        for i in range(0, 8, 2):
            d.rectangle([i * w * K // 8, 0, (i + 1) * w * K // 8, h * K], fill=STRIPE)
    return img


def timeline(t):
    """Demo de ~6 s: quieto, piensa, celebra con salto, chuta."""
    keys = [(0.0, "quieto"), (0.6, "quieto"), (1.0, "piensa"), (1.8, "piensa"), (2.1, "agacha"),
            (2.35, "salto"), (2.6, "celebra"), (3.6, "celebra"), (4.0, "quieto"), (4.4, "chuta_atras"),
            (4.65, "chuta"), (5.3, "chuta"), (5.8, "quieto"), (6.4, "quieto")]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return blend(POSES[a], POSES[b], ease((t - t0) / max(t1 - t0, 1e-6)))
    return POSES["quieto"]


def demo(out, fps=30, size=720):
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{size}x{size}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", "-crf", "20", str(out)], stdin=subprocess.PIPE)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 56 * K)
    for i in range(int(6.4 * fps)):
        t = i / fps
        img = canvas()
        pose = timeline(t)
        bob = 4 * math.sin(t * 6) if t < 2 or t > 6 else 0
        draw(img, pose, dy=bob)
        if t > 2.6 and t < 3.6:  # texto de celebración
            d = ImageDraw.Draw(img)
            d.text((700 * K, 150 * K), "¡DATO!", font=f, fill=YELLOW)
        if 1.0 < t < 1.8:
            d = ImageDraw.Draw(img)
            d.text((630 * K, 170 * K), "?", font=f, fill=YELLOW)
        # balón: quieto delante del pie y sale disparado al chutar
        if t >= 3.9:
            if t < 4.65:
                ball(img, 700, 885)
            else:
                k = (t - 4.65) / 0.7
                ball(img, 700 + 500 * k, 885 - 700 * k + 450 * k * k, rot=k * 12)
        proc.stdin.write(img.resize((size, size), Image.LANCZOS).tobytes())
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    names = ["quieto", "piensa", "celebra", "chuta"]
    sheet = Image.new("RGB", (4 * 500, 500))
    for i, n in enumerate(names):
        img = canvas()
        draw(img, POSES[n])
        if n == "chuta":
            ball(img, 760, 840)
        sheet.paste(img.resize((500, 500), Image.LANCZOS), (i * 500, 0))
    sheet.save(OUT / "monigote_poses.png")
    img = canvas(bg=False)
    draw(img, POSES["celebra"])
    img.resize((800, 800), Image.LANCZOS).save(OUT / "monigote_transparente.png")
    demo(OUT / "monigote_demo.mp4")
