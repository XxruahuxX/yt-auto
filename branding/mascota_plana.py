"""Mascota de DatoCrack: futbolista en estilo plano, proporciones normales (dibujo propio)."""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 1600
INK = (30, 30, 38)
WHITE = (255, 255, 255)
YELLOW, GREEN_D = (255, 214, 10), (6, 46, 28)
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
OUT = Path("/mnt/project-files/yt-auto/canal/mascota")


def outlined(base, fn, fill, line=10):
    m = Image.new("L", base.size, 0)
    fn(ImageDraw.Draw(m), 255)
    base.paste(INK, (0, 0), m.filter(ImageFilter.MaxFilter(line * 2 + 1)))
    base.paste(fill, (0, 0), m)


def thick(d, a, b, w, f):
    d.line([a, b], fill=f, width=w)
    for p in (a, b):
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=f)


def ball(d, bx, by, r):
    d.ellipse([bx - r, by - r, bx + r, by + r], fill=WHITE, outline=INK, width=10)
    p = [(bx + r * .36 * math.cos(math.radians(-90 + 72 * i)), by + r * .36 * math.sin(math.radians(-90 + 72 * i))) for i in range(5)]
    d.polygon(p, fill=INK)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        d.line([(bx + r * .36 * math.cos(a), by + r * .36 * math.sin(a)), (bx + r * .85 * math.cos(a), by + r * .85 * math.sin(a))], fill=INK, width=8)


def player(skin, hair, beard=False, bg=True):
    skin_d = tuple(int(c * 0.86) for c in skin)
    img = Image.new("RGBA", (S, S), GREEN_D if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        for i in range(0, 8, 2):
            d.rectangle([i * S // 8, 0, (i + 1) * S // 8, S], fill=(9, 56, 34))
        d.ellipse([S / 2 - 600, S / 2 - 600, S / 2 + 600, S / 2 + 600], outline=(40, 110, 70), width=12)
        d.ellipse([560, 1470, 1200, 1530], fill=(4, 34, 20))
    cx = 800
    # piernas: muslo (piel), medias, botas. Pie derecho sobre el balón.
    outlined(img, lambda d, f: (thick(d, (740, 1100), (725, 1260), 92, f), thick(d, (860, 1100), (900, 1250), 92, f)), skin)
    outlined(img, lambda d, f: (thick(d, (725, 1250), (720, 1440), 86, f), thick(d, (900, 1245), (950, 1400), 86, f)), YELLOW)
    d = ImageDraw.Draw(img)
    d.line([(680, 1285), (768, 1285)], fill=GREEN_D, width=12)
    d.line([(865, 1290), (950, 1270)], fill=GREEN_D, width=12)
    ball(d, 1040, 1435, 85)
    outlined(img, lambda d, f: (d.rounded_rectangle([650, 1440, 790, 1495], 26, fill=f),
                                d.polygon([(915, 1385), (1040, 1360), (1060, 1405), (935, 1440)], fill=f)), (34, 34, 42))
    # brazos: izquierdo relajado, derecho señalando arriba ("¡dato!")
    outlined(img, lambda d, f: (thick(d, (625, 640), (575, 830), 70, f), thick(d, (575, 830), (590, 990), 62, f),
                                d.ellipse([555, 970, 630, 1045], fill=f),
                                thick(d, (975, 640), (1080, 520), 70, f), thick(d, (1080, 520), (1120, 380), 62, f),
                                d.ellipse([1080, 330, 1160, 410], fill=f)), skin)
    # pantalón
    outlined(img, lambda d, f: d.polygon([(650, 950), (950, 950), (975, 1150), (815, 1160), (800, 1080), (785, 1160), (625, 1150)], fill=f), WHITE)
    # camiseta
    outlined(img, lambda d, f: (d.rounded_rectangle([630, 560, 970, 990], 70, fill=f),
                                d.polygon([(660, 570), (580, 640), (560, 760), (640, 770)], fill=f),
                                d.polygon([(940, 570), (1040, 580), (1080, 690), (980, 740)], fill=f)), YELLOW)
    d = ImageDraw.Draw(img)
    d.line([(632, 975), (968, 975)], fill=GREEN_D, width=12)
    # escudo DC
    d.ellipse([cx - 78, 690, cx + 78, 846], fill=GREEN_D, outline=INK, width=8)
    d.ellipse([cx - 66, 702, cx + 66, 834], outline=YELLOW, width=5)
    fd = ImageFont.truetype(BOLD, 78)
    d.text((cx - d.textlength("DC", font=fd) / 2, 718), "DC", font=fd, fill=YELLOW)
    # cuello y cabeza
    outlined(img, lambda d, f: (d.rectangle([cx - 48, 470, cx + 48, 590], fill=f),
                                d.ellipse([cx - 145, 225, cx + 145, 545], fill=f),
                                d.ellipse([cx - 168, 360, cx - 118, 430], fill=f),
                                d.ellipse([cx + 118, 360, cx + 168, 430], fill=f)), skin)
    d = ImageDraw.Draw(img)
    d.polygon([(cx - 60, 560), (cx + 60, 560), (cx, 620)], fill=GREEN_D)  # cuello V
    d.polygon([(cx - 40, 560), (cx + 40, 560), (cx, 600)], fill=skin)
    if beard:
        d.chord([cx - 140, 300, cx + 140, 545], 15, 165, fill=skin_d)
    # pelo corto con raya
    outlined(img, lambda d, f: (d.chord([cx - 152, 200, cx + 152, 470], 180, 360, fill=f),
                                d.polygon([(cx - 152, 335), (cx - 140, 400), (cx - 120, 330)], fill=f),
                                d.polygon([(cx + 152, 335), (cx + 140, 400), (cx + 120, 330)], fill=f),
                                d.polygon([(cx - 60, 215), (cx + 120, 190), (cx + 150, 280)], fill=f)), hair)
    d = ImageDraw.Draw(img)
    d.line([(cx - 40, 225), (cx - 20, 300)], fill=tuple(min(255, c + 40) for c in hair), width=8)
    # cara: ojos de punto, cejas, nariz y sonrisa
    for ex in (cx - 55, cx + 55):
        d.ellipse([ex - 13, 372, ex + 13, 398], fill=INK)
    d.line([(cx - 80, 345), (cx - 32, 340)], fill=hair, width=12)
    d.line([(cx + 32, 340), (cx + 80, 345)], fill=hair, width=12)
    d.line([(cx + 4, 395), (cx + 14, 440), (cx - 6, 445)], fill=skin_d, width=8, joint="curve")
    d.arc([cx - 55, 430, cx + 55, 495], 25, 155, fill=INK, width=10)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    a = player((236, 190, 150), (60, 40, 30))
    b = player((176, 120, 84), (24, 20, 20), beard=True)
    for name, im in (("plana_a", a), ("plana_b", b)):
        im.convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT / f"mascota_{name}.png")
    player((236, 190, 150), (60, 40, 30), bg=False).resize((800, 800), Image.LANCZOS).save(OUT / "mascota_plana_a_transparente.png")
    g = Image.new("RGB", (1600, 800))
    g.paste(Image.open(OUT / "mascota_plana_a.png"), (0, 0))
    g.paste(Image.open(OUT / "mascota_plana_b.png"), (800, 0))
    g.save(OUT / "mascota_plana_dos.png")
