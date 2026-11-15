"""Mascota de DatoCrack: serpiente futbolera (dibujo propio con Pillow, supermuestreo x2)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 1600
INK, WHITE = (22, 30, 26), (255, 255, 255)
G, G_L, G_D = (96, 190, 96), (190, 236, 150), (60, 140, 64)
YELLOW, GREEN_D = (255, 214, 10), (6, 46, 28)
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
OUT = Path("/mnt/project-files/yt-auto/canal/mascota")


def bez(p0, p1, p2, p3, n):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                  for a, b, c, d in zip(p0, p1, p2, p3)) for t in (i / n for i in range(n + 1))]


def tube(d, pts, radii, fill, line=14, belly=None):
    for (x, y), r in zip(pts, radii):
        d.ellipse([x - r - line, y - r - line, x + r + line, y + r + line], fill=INK)
    for (x, y), r in zip(pts, radii):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    if belly:
        for (x, y), r in zip(pts, radii):
            d.ellipse([x - r * 0.45, y - r * 0.15, x + r * 0.45, y + r * 0.75], fill=belly)


def ball(d, bx, by, r):
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=WHITE, outline=INK, width=14)
    p = [(bx + r * .36 * math.cos(math.radians(-90 + 72 * i)), by + r * .36 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    d.polygon(p, fill=INK)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        d.line([(bx + r * .36 * math.cos(a), by + r * .36 * math.sin(a)), (bx + r * .85 * math.cos(a), by + r * .85 * math.sin(a))], fill=INK, width=10)


def snake(bg=True):
    img = Image.new("RGBA", (S, S), GREEN_D if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        for i in range(0, 8, 2):
            d.rectangle([i * S // 8, 0, (i + 1) * S // 8, S], fill=(9, 56, 34))
        d.ellipse([S / 2 - 560, S / 2 - 560, S / 2 + 560, S / 2 + 560], outline=(40, 110, 70), width=12)
        d.ellipse([360, 1380, 1240, 1500], fill=(4, 34, 20))
    cx, cy, rx, ry = 800, 1300, 360, 120
    # enrollado: mitad trasera, cola, mitad delantera
    back = [(cx + rx * math.cos(a), cy - ry * math.sin(a)) for a in [math.pi * i / 60 for i in range(61)]]
    tail = bez((cx + rx, cy), (cx + rx + 120, cy + 40), (cx + rx + 160, cy - 60), (cx + rx + 230, cy - 120), 30)
    tube(d, tail, [70 - 50 * i / 30 for i in range(31)], G)
    tube(d, back, [95] * len(back), G_D)
    front = [(cx - rx * math.cos(a), cy + ry * math.sin(a)) for a in [math.pi * i / 60 for i in range(61)]]
    front = front[::-1]  # de derecha a izquierda por delante
    tube(d, front, [100] * len(front), G)
    # escamas: rombos amarillos en la parte delantera
    for i in range(6, len(front) - 4, 8):
        x, y = front[i]
        d.polygon([(x, y - 34), (x + 26, y), (x, y + 34), (x - 26, y)], fill=YELLOW, outline=INK, width=6)
    # cuerpo que sube desde la izquierda
    up = bez((cx - rx, cy), (cx - rx - 120, 900), (1050, 900), (820, 560), 90)
    radii = [100 - 10 * i / 90 for i in range(91)]
    tube(d, up, radii, G)
    # camiseta en el tramo alto (tubo amarillo con cuello y dorsal)
    a, b = 40, 78
    tube(d, up[a:b], radii[a:b], YELLOW, line=12)
    x, y = up[(a + b) // 2]
    f = ImageFont.truetype(BOLD, 120)
    d.text((x - d.textlength("10", font=f) / 2, y - 70), "10", font=f, fill=GREEN_D)
    xc, yc = up[b - 2]
    d.polygon([(xc - 60, yc - 30), (xc + 60, yc - 30), (xc, yc + 40)], fill=GREEN_D)
    # cabeza
    hx, hy = 830, 450
    d.ellipse([hx - 200 - 14, hy - 150 - 14, hx + 200 + 14, hy + 140 + 14], fill=INK)
    d.ellipse([hx - 200, hy - 150, hx + 200, hy + 140], fill=G)
    d.ellipse([hx - 130, hy + 20, hx + 130, hy + 130], fill=G_L)
    # cinta amarilla en la frente (recortada a la cabeza)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([hx - 200, hy - 150, hx + 200, hy + 140], fill=255)
    band = Image.new("L", img.size, 0)
    ImageDraw.Draw(band).rectangle([0, hy - 135, S, hy - 75], fill=255)
    from PIL import ImageChops
    img.paste(YELLOW, (0, 0), ImageChops.multiply(m, band))
    d = ImageDraw.Draw(img)
    for yy in (hy - 135, hy - 75):
        half = 200 * math.sqrt(max(0, 1 - ((yy - (hy - 5)) / 145) ** 2))
        d.line([(hx - half, yy), (hx + half, yy)], fill=INK, width=8)
    for ex in (hx - 85, hx + 85):
        d.ellipse([ex - 70, hy - 80, ex + 70, hy + 50], fill=WHITE, outline=INK, width=12)
        d.ellipse([ex - 18, hy - 40, ex + 42, hy + 30], fill=INK)
        d.ellipse([ex + 4, hy - 32, ex + 22, hy - 12], fill=WHITE)
    d.arc([hx - 120, hy, hx + 120, hy + 110], 20, 160, fill=INK, width=14)  # sonrisa
    # lengua bífida
    d.line([(hx, hy + 104), (hx, hy + 175)], fill=(220, 40, 60), width=16)
    d.line([(hx, hy + 170), (hx - 25, hy + 210)], fill=(220, 40, 60), width=14)
    d.line([(hx, hy + 170), (hx + 25, hy + 210)], fill=(220, 40, 60), width=14)
    for nx in (hx - 25, hx + 25):
        d.ellipse([nx - 8, hy + 50, nx + 8, hy + 62], fill=INK)
    ball(d, 1395, 975, 100)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    snake().convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT / "mascota_serpiente.png")
    snake(bg=False).resize((800, 800), Image.LANCZOS).save(OUT / "mascota_serpiente_transparente.png")
