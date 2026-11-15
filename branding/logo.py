"""Tres propuestas de logo (800x800). Se dibuja a 3x y se reduce para suavizar bordes."""
import math
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2400
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
GREEN_D, GREEN, GREEN_L = (4, 34, 20), (10, 80, 45), (22, 130, 72)
YELLOW, YELLOW_D, WHITE, INK = (255, 214, 10), (230, 160, 0), (255, 255, 255), (12, 18, 14)
out = sys.argv[1] if len(sys.argv) > 1 else "."


def radial(size, inner, outer):
    img = Image.new("RGB", (size, size), outer)
    d = ImageDraw.Draw(img)
    for r in range(size // 2, 0, -6):
        k = r / (size / 2)
        c = tuple(int(inner[i] * (1 - k) + outer[i] * k) for i in range(3))
        d.ellipse([size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r], fill=c)
    return img


def pentagon(cx, cy, r, rot=-90):
    return [(cx + r * math.cos(math.radians(rot + 72 * i)), cy + r * math.sin(math.radians(rot + 72 * i)))
            for i in range(5)]


def ball(size, line=INK, fill=WHITE):
    """Balón clásico: pentágono central, 5 pentágonos de borde y costuras."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, R = size / 2, size / 2 - size * 0.02
    d.ellipse([c - R, c - R, c + R, c + R], fill=fill)
    pr = R * 0.30
    center = pentagon(c, c, pr)
    d.polygon(center, fill=line)
    w = max(2, int(size * 0.018))
    for i, (x, y) in enumerate(center):
        ang = math.atan2(y - c, x - c)
        ox, oy = c + R * 0.98 * math.cos(ang), c + R * 0.98 * math.sin(ang)
        d.line([(x, y), (c + R * 0.70 * math.cos(ang), c + R * 0.70 * math.sin(ang))], fill=line, width=w)
        d.polygon(pentagon(ox, oy, pr * 0.85, math.degrees(ang) + 180), fill=line)
    # recorte circular + borde
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([c - R, c - R, c + R, c + R], fill=255)
    im.putalpha(Image.composite(im.getchannel("A"), mask, mask))
    d = ImageDraw.Draw(im)
    d.ellipse([c - R, c - R, c + R, c + R], outline=line, width=int(size * 0.035))
    # brillo
    shine = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shine).ellipse([c - R * 0.75, c - R * 0.85, c - R * 0.15, c - R * 0.45], fill=(255, 255, 255, 90))
    im.alpha_composite(shine.filter(ImageFilter.GaussianBlur(size * 0.03)))
    return im


def shadow(im, offset, blur, alpha=140):
    a = im.getchannel("A").point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a)
    return sh.filter(ImageFilter.GaussianBlur(blur)), offset


def text_layer(text, font, fill, stroke=0, stroke_fill=None, size=S):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = d.textlength(text, font=font)
    bb = d.textbbox((0, 0), text, font=font, stroke_width=stroke)
    d.text(((size - w) / 2, (size - (bb[3] - bb[1])) / 2 - bb[1]), text, font=font, fill=fill,
           stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def paste_centered(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def finish(img, name):
    img.convert("RGB").resize((800, 800), Image.LANCZOS).save(f"{out}/{name}.png")


# A: balón grande con "DC" en franja amarilla diagonal
img = radial(S, GREEN_L, GREEN_D).convert("RGBA")
b = ball(1500)
sh, _ = shadow(b, 0, 40)
img.alpha_composite(sh, (470, 520))
img.alpha_composite(b, (450, 450))
band = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(band).rectangle([-200, S / 2 - 260, S + 200, S / 2 + 260], fill=YELLOW)
band = band.rotate(-12, resample=Image.BICUBIC)
sh, _ = shadow(band, 0, 30, 160)
img.alpha_composite(sh, (0, 25))
img.alpha_composite(band)
t = text_layer("DC", ImageFont.truetype(BLACK, 560), GREEN_D).rotate(-12, resample=Image.BICUBIC)
img.alpha_composite(t)
finish(img, "logo_A_balon_franja")

# B: monograma — la "C" rodea un balón, la "D" a la izquierda
img = radial(S, GREEN_L, GREEN_D).convert("RGBA")
ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
rd = ImageDraw.Draw(ring)
rd.ellipse([260, 260, S - 260, S - 260], outline=YELLOW, width=110)
img.alpha_composite(ring)
f = ImageFont.truetype(BLACK, 1150)
dl = text_layer("D", f, WHITE)
sh, _ = shadow(dl, 0, 25)
img.alpha_composite(sh, (-330, 30))
img.alpha_composite(dl, (-360, 0))
cl = text_layer("C", f, YELLOW)
sh, _ = shadow(cl, 0, 25)
img.alpha_composite(sh, (410, 30))
img.alpha_composite(cl, (380, 0))
b = ball(430)
sh, _ = shadow(b, 0, 20)
paste_centered(img, sh, S / 2 + 640, S / 2 + 40)
paste_centered(img, b, S / 2 + 620, S / 2 + 20)
finish(img, "logo_B_monograma")

# C: escudo tipo club con balón y "DC"
img = radial(S, GREEN_L, GREEN_D).convert("RGBA")
shield = Image.new("RGBA", (S, S), (0, 0, 0, 0))
sd = ImageDraw.Draw(shield)
pts = [(S * .2, S * .17), (S * .8, S * .17), (S * .8, S * .55), (S * .5, S * .88), (S * .2, S * .55)]
sd.polygon(pts, fill=YELLOW)
inner = [(S * .25, S * .22), (S * .75, S * .22), (S * .75, S * .53), (S * .5, S * .81), (S * .25, S * .53)]
sd.polygon(inner, fill=GREEN_D)
sh, _ = shadow(shield, 0, 40, 170)
img.alpha_composite(sh, (0, 40))
img.alpha_composite(shield)
b = ball(560)
paste_centered(img, b, S / 2, S * .36)
t = text_layer("DC", ImageFont.truetype(BLACK, 430), YELLOW)
paste_centered(img, t, S / 2, S * .62)
finish(img, "logo_C_escudo")
