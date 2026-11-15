"""Bocetos de mascota de DatoCrack (dibujo vectorial con Pillow, supermuestreo x2)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 1600
GREEN, GREEN_D, YELLOW, INK, WHITE = (18, 110, 60), (6, 46, 28), (255, 214, 10), (22, 22, 30), (255, 255, 255)
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
OUT = Path("/mnt/project-files/yt-auto/canal/mascota")


def poly(cx, cy, r, n=5, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + 360 * i / n)), cy + r * math.sin(math.radians(rot + 360 * i / n))) for i in range(n)]


def ball(d, cx, cy, r, outline=18):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=INK, width=outline)
    d.polygon(poly(cx, cy + r * 0.05, r * 0.28), fill=INK)
    for k in range(5):
        a = math.radians(-90 + 72 * k)
        px, py = cx + r * 0.78 * math.cos(a), cy + r * 0.05 + r * 0.78 * math.sin(a)
        d.polygon(poly(px, py, r * 0.22, rot=-90 + 72 * k + 36), fill=INK)
        d.line([(cx + r * 0.28 * math.cos(a), cy + r * 0.05 + r * 0.28 * math.sin(a)), (px, py)], fill=INK, width=10)
    # recorta lo que sale del círculo
    return


def clip_ball(img, cx, cy, r):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ball(ImageDraw.Draw(layer), cx, cy, r)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    img.paste(layer, (0, 0), Image.composite(layer, Image.new("RGBA", img.size, (0, 0, 0, 0)), mask))
    ImageDraw.Draw(img).ellipse([cx - r, cy - r, cx + r, cy + r], outline=INK, width=22)


def eye(d, cx, cy, r, look=(0.15, 0.1), wink=False):
    if wink:
        d.arc([cx - r, cy - r * 0.6, cx + r, cy + r * 0.8], 200, 340, fill=INK, width=22)
        return
    d.ellipse([cx - r, cy - r * 1.15, cx + r, cy + r * 1.15], fill=WHITE, outline=INK, width=14)
    px, py = cx + look[0] * r, cy + look[1] * r
    d.ellipse([px - r * 0.52, py - r * 0.6, px + r * 0.52, py + r * 0.6], fill=INK)
    d.ellipse([px - r * 0.05, py - r * 0.42, px + r * 0.25, py - r * 0.12], fill=WHITE)


def smile(d, cx, cy, w, open_=True):
    if open_:
        d.chord([cx - w, cy - w * 0.55, cx + w, cy + w * 0.75], 0, 180, fill=(120, 20, 30), outline=INK, width=14)
        d.chord([cx - w * 0.45, cy + w * 0.2, cx + w * 0.45, cy + w * 0.72], 180, 360, fill=(240, 90, 100))
        d.rectangle([cx - w * 0.6, cy + w * 0.08, cx + w * 0.6, cy + w * 0.2], fill=WHITE)
    else:
        d.arc([cx - w, cy - w * 0.6, cx + w, cy + w * 0.6], 20, 160, fill=INK, width=18)


def glove(d, x, y, r=60):
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=INK, width=14)


def boot(d, x, y, flip=False):
    s = -1 if flip else 1
    pts = [(x - 70 * s, y - 40), (x + 40 * s, y - 40), (x + 110 * s, y + 10), (x + 110 * s, y + 45), (x - 70 * s, y + 45)]
    d.polygon(pts, fill=YELLOW, outline=INK, width=14)
    for k in range(3):
        d.ellipse([x - 50 * s + k * 50 * s - 12, y + 45, x - 50 * s + k * 50 * s + 12, y + 70], fill=INK)


def bg(title):
    img = Image.new("RGBA", (S, S), GREEN_D)
    d = ImageDraw.Draw(img)
    for i in range(0, 8, 2):
        d.rectangle([i * S // 8, 0, (i + 1) * S // 8, S], fill=(9, 56, 34))
    d.ellipse([S / 2 - 520, S / 2 - 520, S / 2 + 520, S / 2 + 520], outline=(40, 110, 70), width=12)
    f = ImageFont.truetype(BOLD, 90)
    d.text(((S - d.textlength(title, font=f)) / 2, S - 150), title, font=f, fill=YELLOW)
    return img, d


def limbs(d, cx, cy, r, wave=True):
    # piernas
    for sx in (-1, 1):
        d.line([(cx + sx * r * 0.35, cy + r * 0.9), (cx + sx * r * 0.42, cy + r * 1.35)], fill=INK, width=26)
        boot(d, cx + sx * r * 0.42, cy + r * 1.38, flip=sx < 0)
    # brazos
    d.line([(cx - r * 0.95, cy + r * 0.2), (cx - r * 1.35, cy + r * 0.55)], fill=INK, width=26)
    glove(d, cx - r * 1.38, cy + r * 0.58)
    if wave:
        d.line([(cx + r * 0.95, cy + r * 0.1), (cx + r * 1.35, cy - r * 0.45)], fill=INK, width=26)
        glove(d, cx + r * 1.38, cy - r * 0.5)


def mascot_a():
    """Dato: balón empollón con gafas, saluda."""
    img, d = bg("DATO")
    cx, cy, r = S / 2, 680, 400
    limbs(d, cx, cy, r)
    clip_ball(img, cx, cy, r)
    d = ImageDraw.Draw(img)
    # cara sobre parche claro
    d.ellipse([cx - 300, cy - 170, cx + 300, cy + 330], fill=WHITE)
    eye(d, cx - 120, cy - 10, 85)
    eye(d, cx + 120, cy - 10, 85)
    for ex in (cx - 120, cx + 120):  # gafas
        d.ellipse([ex - 125, cy - 135, ex + 125, cy + 115], outline=INK, width=26)
    d.line([(cx - 10, cy - 30), (cx + 10, cy - 30)], fill=INK, width=26)
    smile(d, cx, cy + 190, 110)
    return img


def mascot_b():
    """Crack: balón chulito con gorra hacia atrás y guiño."""
    img, d = bg("CRACK")
    cx, cy, r = S / 2, 700, 400
    limbs(d, cx, cy, r)
    clip_ball(img, cx, cy, r)
    d = ImageDraw.Draw(img)
    # gorra amarilla del revés
    d.chord([cx - 330, cy - 440, cx + 330, cy - 70], 180, 360, fill=YELLOW, outline=INK, width=18)
    d.rounded_rectangle([cx - 420, cy - 280, cx - 220, cy - 220], 30, fill=YELLOW, outline=INK, width=16)
    f = ImageFont.truetype(BOLD, 110)
    d.text((cx - d.textlength("DC", font=f) / 2, cy - 395), "DC", font=f, fill=GREEN_D)
    d.ellipse([cx - 300, cy - 120, cx + 300, cy + 330], fill=WHITE)
    eye(d, cx - 120, cy + 10, 85, wink=True)
    eye(d, cx + 120, cy + 10, 85, look=(0.25, 0.05))
    # cejas
    d.line([(cx + 50, cy - 120), (cx + 200, cy - 95)], fill=INK, width=24)
    # sonrisa de lado
    d.arc([cx - 140, cy + 80, cx + 160, cy + 250], 10, 150, fill=INK, width=22)
    d.ellipse([cx + 120, cy + 135, cx + 175, cy + 190], fill=INK)
    return img


def mascot_c():
    """Búho futbolero: sabio de los datos con camiseta del canal."""
    img, d = bg("BÚHO")
    cx, cy = S / 2, 760
    BROWN, BROWN_L = (125, 82, 48), (196, 150, 104)
    # cuerpo y orejas
    d.polygon([(cx - 330, cy - 420), (cx - 220, cy - 280), (cx - 360, cy - 250)], fill=BROWN, outline=INK, width=14)
    d.polygon([(cx + 330, cy - 420), (cx + 220, cy - 280), (cx + 360, cy - 250)], fill=BROWN, outline=INK, width=14)
    d.ellipse([cx - 380, cy - 380, cx + 380, cy + 420], fill=BROWN, outline=INK, width=18)
    # camiseta amarilla
    d.chord([cx - 380, cy - 380, cx + 380, cy + 420], 15, 165, fill=YELLOW, outline=INK, width=18)
    d.rectangle([cx - 371, cy + 100, cx + 371, cy + 125], fill=YELLOW)
    f = ImageFont.truetype(BOLD, 150)
    d.text((cx - d.textlength("10", font=f) / 2, cy + 140), "10", font=f, fill=GREEN_D)
    # cara
    d.ellipse([cx - 290, cy - 290, cx + 10, cy + 20], fill=BROWN_L)
    d.ellipse([cx - 10, cy - 290, cx + 290, cy + 20], fill=BROWN_L)
    eye(d, cx - 140, cy - 140, 95, look=(0.1, 0.15))
    eye(d, cx + 140, cy - 140, 95, look=(-0.1, 0.15))
    for ex in (cx - 140, cx + 140):
        d.ellipse([ex - 135, ex * 0 + cy - 275, ex + 135, cy - 5], outline=INK, width=24)
    d.polygon([(cx - 45, cy - 10), (cx + 45, cy - 10), (cx, cy + 70)], fill=(255, 150, 30), outline=INK, width=12)
    # alas y balón
    d.chord([cx - 470, cy - 80, cx - 250, cy + 320], 90, 270, fill=BROWN, outline=INK, width=16)
    img2 = img
    clip_ball(img2, cx + 420, cy + 260, 150)
    d = ImageDraw.Draw(img2)
    d.chord([cx + 230, cy - 60, cx + 450, cy + 300], 270, 90, fill=BROWN, outline=INK, width=16)
    # patas
    for sx in (-1, 1):
        for k in (-1, 0, 1):
            d.line([(cx + sx * 140, cy + 400), (cx + sx * 140 + k * 40, cy + 470)], fill=(255, 150, 30), width=24)
    return img2


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    ims = []
    for name, fn in (("dato", mascot_a), ("crack", mascot_b), ("buho", mascot_c)):
        im = fn().convert("RGB").resize((800, 800), Image.LANCZOS)
        im.save(OUT / f"mascota_{name}.png")
        ims.append(im)
    grid = Image.new("RGB", (2400, 800))
    for i, im in enumerate(ims):
        grid.paste(im, (i * 800, 0))
    grid.save(OUT / "mascotas_bocetos.png")
