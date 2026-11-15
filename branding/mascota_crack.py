"""Mascota de DatoCrack: futbolista chibi (dibujo propio con Pillow, supermuestreo x2)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 1600
INK, WHITE = (24, 24, 32), (255, 255, 255)
SKIN, SKIN_D, BLUSH = (244, 196, 152), (222, 166, 122), (240, 150, 140)
HAIR, HAIR_L = (52, 34, 28), (92, 62, 48)
YELLOW, YELLOW_D, GREEN_D = (255, 214, 10), (230, 180, 0), (6, 46, 28)
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
OUT = Path("/mnt/project-files/yt-auto/canal/mascota")


def outlined(base, fn, fill, line=14):
    m = Image.new("L", base.size, 0)
    fn(ImageDraw.Draw(m), 255)
    base.paste(INK, (0, 0), m.filter(ImageFilter.MaxFilter(line * 2 + 1)))
    base.paste(fill, (0, 0), m)
    return m


def thick(d, a, b, w, f):
    d.line([a, b], fill=f, width=w)
    for p in (a, b):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=f)


def ball(d, bx, by, r):
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=WHITE, outline=INK, width=14)
    p = [(bx + r * .36 * math.cos(math.radians(-90 + 72 * i)), by + r * .36 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    d.polygon(p, fill=INK)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        d.line([(bx + r * .36 * math.cos(a), by + r * .36 * math.sin(a)), (bx + r * .85 * math.cos(a), by + r * .85 * math.sin(a))], fill=INK, width=10)


def crack(bg=True, face="feliz"):
    img = Image.new("RGBA", (S, S), GREEN_D if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        for i in range(0, 8, 2):
            d.rectangle([i * S // 8, 0, (i + 1) * S // 8, S], fill=(9, 56, 34))
        d.ellipse([S / 2 - 560, S / 2 - 560, S / 2 + 560, S / 2 + 560], outline=(40, 110, 70), width=12)
        d.ellipse([520, 1440, 1240, 1520], fill=(4, 34, 20))

    # piernas (piel) + medias + botas
    outlined(img, lambda d, f: (thick(d, (730, 1180), (715, 1400), 92, f), thick(d, (870, 1180), (885, 1400), 92, f)), SKIN)
    outlined(img, lambda d, f: (d.rounded_rectangle([668, 1290, 762, 1420], 20, fill=f),
                                d.rounded_rectangle([838, 1290, 932, 1420], 20, fill=f)), YELLOW, 12)
    d = ImageDraw.Draw(img)
    for x in (715, 885):
        d.line([(x - 46, 1315), (x + 46, 1315)], fill=GREEN_D, width=14)
    outlined(img, lambda d, f: (d.rounded_rectangle([620, 1400, 770, 1475], 34, fill=f),
                                d.rounded_rectangle([830, 1400, 980, 1475], 34, fill=f)), (36, 36, 44), 12)
    d = ImageDraw.Draw(img)
    for x0 in (640, 850):
        for k in range(4):
            d.ellipse([x0 + 15 + 35 * k - 10, 1470, x0 + 15 + 35 * k + 10, 1490], fill=INK)
    ball(d, 1110, 1395, 95)

    # brazos (detrás de la camiseta): izquierdo en la cadera, derecho con pulgar arriba
    outlined(img, lambda d, f: (thick(d, (650, 900), (560, 1060), 74, f), d.ellipse([515, 1030, 605, 1120], fill=f),
                                thick(d, (950, 900), (1060, 980), 74, f), thick(d, (1060, 980), (1110, 860), 74, f),
                                d.ellipse([1055, 790, 1165, 900], fill=f),
                                *[d.rounded_rectangle([1110 + 42 * math.cos(a) - 19, 845 + 42 * math.sin(a) - 19,
                                                       1110 + 105 * math.cos(a) + 19, 845 + 105 * math.sin(a) + 19], 19, fill=f)
                                  if False else thick(d, (1110 + 40 * math.cos(a), 845 + 40 * math.sin(a)),
                                                      (1110 + 100 * math.cos(a), 845 + 100 * math.sin(a)), 36, f)
                                  for a in [math.radians(x) for x in (-130, -100, -75, -50, -5)]]), SKIN)
    # pantalón
    outlined(img, lambda d, f: d.polygon([(640, 1060), (960, 1060), (985, 1230), (815, 1240), (800, 1170), (785, 1240), (615, 1230)], fill=f), WHITE, 12)
    # camiseta con mangas
    outlined(img, lambda d, f: (d.rounded_rectangle([630, 820, 970, 1100], 60, fill=f),
                                d.polygon([(660, 830), (570, 930), (630, 985), (680, 920)], fill=f),
                                d.polygon([(940, 830), (1030, 930), (970, 985), (920, 920)], fill=f)), YELLOW, 12)
    d = ImageDraw.Draw(img)
    d.polygon([(740, 822), (860, 822), (800, 890)], fill=GREEN_D)
    d.polygon([(760, 822), (840, 822), (800, 865)], fill=SKIN)
    d.line([(632, 1085), (968, 1085)], fill=GREEN_D, width=14)
    f = ImageFont.truetype(BOLD, 150)
    # escudo DC en el pecho
    d.ellipse([800 - 95, 885, 800 + 95, 1075], fill=GREEN_D, outline=INK, width=10)
    d.ellipse([800 - 80, 900, 800 + 80, 1060], outline=YELLOW, width=6)
    fd = ImageFont.truetype(BOLD, 96)
    d.text((800 - d.textlength("DC", font=fd) / 2, 918), "DC", font=fd, fill=YELLOW)

    # cabeza
    hx, hy, r = 800, 520, 290
    outlined(img, lambda d, f: (d.ellipse([hx - r - 45, hy - 20, hx - r + 45, hy + 90], fill=f),
                                d.ellipse([hx + r - 45, hy - 20, hx + r + 45, hy + 90], fill=f),
                                d.rounded_rectangle([hx - 60, hy + 230, hx + 60, hy + 320], 20, fill=f),
                                d.ellipse([hx - r, hy - r, hx + r, hy + r * 0.95], fill=f)), SKIN)
    # pelo: casquete con tupé
    def hair(d, f):
        d.chord([hx - r - 10, hy - r - 30, hx + r + 10, hy + r * 0.6], 180, 360, fill=f)
        for k, (dx, dy, rr) in enumerate([(-170, -230, 120), (-50, -300, 130), (90, -290, 125), (200, -210, 110)]):
            d.ellipse([hx + dx - rr, hy + dy - rr, hx + dx + rr, hy + dy + rr], fill=f)
        d.polygon([(hx + 60, hy - 400), (hx + 170, hy - 330), (hx + 40, hy - 300)], fill=f)  # mechón
    outlined(img, hair, HAIR)
    d = ImageDraw.Draw(img)
    # flequillo sobre la frente
    d.chord([hx - r + 10, hy - 260, hx + r - 10, hy - 40], 180, 360, fill=HAIR)
    d.pieslice([hx - 140, hy - 200, hx + 40, hy - 50], 0, 180, fill=HAIR)
    d.arc([hx - 160, hy - 330, hx + 60, hy - 180], 200, 300, fill=HAIR_L, width=14)
    # cara
    for ex in (hx - 110, hx + 110):
        d.ellipse([ex - 55, hy - 30, ex + 55, hy + 100], fill=INK)
        d.ellipse([ex - 25, hy - 8, ex + 8, hy + 28], fill=WHITE)
        d.ellipse([ex + 12, hy + 45, ex + 28, hy + 62], fill=WHITE)
    for ex, s in ((hx - 110, 1), (hx + 110, -1)):
        d.line([(ex - 55, hy - 70 + 10 * s), (ex + 55, hy - 70 - 10 * s)], fill=HAIR, width=18)
    d.ellipse([hx - 230, hy + 100, hx - 150, hy + 150], fill=BLUSH)
    d.ellipse([hx + 150, hy + 100, hx + 230, hy + 150], fill=BLUSH)
    d.arc([hx - 22, hy + 70, hx + 22, hy + 110], 20, 160, fill=SKIN_D, width=10)
    d.chord([hx - 95, hy + 110, hx + 95, hy + 230], 0, 180, fill=(120, 30, 40), outline=INK, width=10)
    d.chord([hx - 50, hy + 175, hx + 50, hy + 228], 180, 360, fill=(240, 100, 110))
    d.rectangle([hx - 70, hy + 168, hx + 70, hy + 182], fill=WHITE)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    crack().convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT / "mascota_crack.png")
    crack(bg=False).resize((800, 800), Image.LANCZOS).save(OUT / "mascota_crack_transparente.png")
