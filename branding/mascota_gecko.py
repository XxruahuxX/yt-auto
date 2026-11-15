"""Mascota de DatoCrack: salamanquesa futbolera (dibujo propio con Pillow, supermuestreo x2)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 1600
INK, WHITE = (22, 30, 26), (255, 255, 255)
G, G_L, G_D = (112, 186, 104), (178, 224, 150), (74, 138, 72)
YELLOW, YELLOW_D, GREEN_D = (255, 214, 10), (226, 176, 0), (6, 46, 28)
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
OUT = Path("/mnt/project-files/yt-auto/canal/mascota")


def bez(p0, p1, p2, p3, n=80):
    for i in range(n + 1):
        t = i / n
        yield tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                    for a, b, c, d in zip(p0, p1, p2, p3)), t


def thick(d, a, b, w, fill):
    d.line([a, b], fill=fill, width=w)
    for p in (a, b):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=fill)


def outlined(base, draw_fn, fill, line=16):
    """Dibuja una forma (en máscara) con contorno oscuro y la pega en base."""
    m = Image.new("L", base.size, 0)
    draw_fn(ImageDraw.Draw(m), 255)
    edge = m.filter(ImageFilter.MaxFilter(line * 2 + 1))
    base.paste(INK, (0, 0), edge)
    base.paste(fill, (0, 0), m)
    return m


def hand(d, x, y, side, fill):
    d.ellipse([x - 38, y - 38, x + 38, y + 38], fill=fill)
    for k in range(4):
        a = math.radians((-60 + 40 * k) if side > 0 else (240 - 40 * k))
        fx, fy = x + 85 * math.cos(a), y + 85 * math.sin(a)
        d.line([(x, y), (fx, fy)], fill=fill, width=24)
        d.ellipse([fx - 22, fy - 22, fx + 22, fy + 22], fill=fill)


def gecko(pose="saludo", bg=True):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    if bg:
        img = Image.new("RGBA", (S, S), GREEN_D)
        d = ImageDraw.Draw(img)
        for i in range(0, 8, 2):
            d.rectangle([i * S // 8, 0, (i + 1) * S // 8, S], fill=(9, 56, 34))
        d.ellipse([S / 2 - 560, S / 2 - 560, S / 2 + 560, S / 2 + 560], outline=(40, 110, 70), width=12)
        d.ellipse([480, 1440, 1180, 1520], fill=(4, 34, 20))  # sombra

    # --- cuerpo de la salamanquesa (una sola silueta) ---
    def body(d, f):
        for p, t in bez((720, 1140), (420, 1300), (180, 1150), (260, 900)):  # cola
            r = 95 - 65 * t
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=f)
        thick(d, (720, 1180), (610, 1390), 120, f)  # pierna izq.
        thick(d, (900, 1180), (1010, 1380), 120, f)  # pierna dcha.
        d.ellipse([610, 640, 1000, 1240], fill=f)  # tronco
        d.ellipse([660, 520, 960, 800], fill=f)  # cuello
        d.ellipse([600, 330, 1080, 650], fill=f)  # cabeza
        for ex in (735, 955):  # cuencas de los ojos
            d.ellipse([ex - 100, 230, ex + 100, 420], fill=f)
        # brazos
        thick(d, (650, 820), (470, 940), 78, f)
        if pose == "saludo":
            thick(d, (960, 800), (1150, 600), 78, f)
        else:
            thick(d, (960, 820), (1140, 930), 78, f)
        hand(d, 450, 960, -1, f)
        if pose == "saludo":
            hand(d, 1165, 570, 1, f)
        else:
            hand(d, 1160, 950, 1, f)
    mask = outlined(img, body, G)
    d = ImageDraw.Draw(img)
    # luz en la tripa y escamas en la cola
    belly = Image.new("L", img.size, 0)
    ImageDraw.Draw(belly).ellipse([690, 560, 960, 760], fill=255)
    img.paste(G_L, (0, 0), Image.composite(belly, Image.new("L", img.size, 0), mask))
    for p, t in bez((720, 1140), (420, 1300), (180, 1150), (260, 900), 14):
        if 0.1 < t < 0.9:
            r = (95 - 65 * t) * 0.35
            d.ellipse([p[0] - r, p[1] - r * 0.6 - 20, p[0] + r, p[1] + r * 0.6 - 20], fill=G_D)

    # --- equipación ---
    def shorts(d, f):
        d.polygon([(625, 1050), (985, 1050), (1030, 1250), (830, 1270), (805, 1170), (780, 1270), (580, 1250)], fill=f)
    outlined(img, shorts, WHITE, 12)

    def shirt(d, f):
        d.chord([610, 640, 1000, 1240], 180, 360, fill=f)
        d.rectangle([612, 930, 998, 1080], fill=f)
        d.polygon([(640, 760), (560, 860), (610, 900), (660, 840)], fill=f)  # manga izq.
        d.polygon([(970, 760), (1050, 850), (1000, 890), (950, 840)], fill=f)  # manga dcha.
    outlined(img, shirt, YELLOW, 12)
    d = ImageDraw.Draw(img)
    d.polygon([(745, 655), (865, 655), (805, 760)], fill=GREEN_D)  # cuello en V
    d.polygon([(770, 655), (840, 655), (805, 720)], fill=G)
    d.line([(612, 1075), (998, 1075)], fill=GREEN_D, width=14)
    f = ImageFont.truetype(BOLD, 170)
    d.text((805 - d.textlength("10", font=f) / 2, 800), "10", font=f, fill=GREEN_D)
    fs = ImageFont.truetype(BOLD, 44)
    d.text((660, 770), "DC", font=fs, fill=GREEN_D)

    # medias y botas
    for x0, x1, flip in ((640, 600, -1), (980, 1015, 1)):
        thick(d, (x0, 1300), (x1, 1385), 128, INK)
        thick(d, (x0, 1300), (x1, 1385), 104, YELLOW)
        d.line([(x0 - 52, 1320), (x0 + 52, 1320)], fill=GREEN_D, width=14)
        bx = x1
        d.rounded_rectangle([bx - 90 if flip > 0 else bx - 120, 1395, bx + 120 if flip > 0 else bx + 90, 1470],
                            36, fill=(40, 40, 46), outline=INK, width=14)
        for k in range(4):
            sx = bx - 70 + 45 * k
            d.ellipse([sx - 12, 1466, sx + 12, 1488], fill=INK)

    # --- cara ---
    for ex in (735, 955):
        d.ellipse([ex - 85, 245, ex + 85, 410], fill=WHITE, outline=INK, width=12)
        px = ex + 18
        d.ellipse([px - 34, 300, px + 34, 372], fill=INK)
        d.ellipse([px - 6, 308, px + 14, 330], fill=WHITE)
    d.arc([700, 400, 1040, 590], 15, 165, fill=INK, width=18)  # sonrisa
    d.chord([780, 470, 960, 590], 20, 160, fill=(200, 70, 80))
    d.arc([700, 400, 1040, 590], 15, 165, fill=INK, width=18)
    for nx in (850, 900):
        d.ellipse([nx - 9, 440, nx + 9, 455], fill=INK)
    d.ellipse([650, 470, 710, 510], fill=(150, 210, 130))  # moflete
    d.ellipse([1000, 470, 1060, 510], fill=(150, 210, 130))

    # balón junto al pie
    if pose != "saludo" or True:
        bx, by, r = 1230, 1380, 100
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=WHITE, outline=INK, width=14)
        pts = [(bx + 36 * math.cos(math.radians(-90 + 72 * i)), by + 36 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
        d.polygon(pts, fill=INK)
        for i in range(5):
            a = math.radians(-90 + 72 * i)
            d.line([(bx + 36 * math.cos(a), by + 36 * math.sin(a)), (bx + 85 * math.cos(a), by + 85 * math.sin(a))], fill=INK, width=10)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    im = gecko().convert("RGB").resize((800, 800), Image.LANCZOS)
    im.save(OUT / "mascota_salamanquesa.png")
    gecko(bg=False).resize((800, 800), Image.LANCZOS).save(OUT / "mascota_salamanquesa_transparente.png")
