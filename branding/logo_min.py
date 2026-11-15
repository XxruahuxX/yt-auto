"""Logo minimalista: silueta del campo vista desde arriba y "DC" en el círculo central."""
import sys
from PIL import Image, ImageDraw, ImageFont

S = 2400
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"


def logo(bg, line, ink, out):
    img = Image.new("RGB", (S, S), bg)
    d = ImageDraw.Draw(img)
    lw = 46
    # campo vertical (proporción 68x105) centrado
    h = S * 0.80
    w = h * 68 / 105
    x0, y0 = (S - w) / 2, (S - h) / 2
    x1, y1 = x0 + w, y0 + h
    cx, cy = S / 2, S / 2
    d.rounded_rectangle([x0, y0, x1, y1], radius=60, outline=line, width=lw)
    d.line([x0, cy, x1, cy], fill=line, width=lw)
    k = h / 105
    for top in (True, False):
        y = y0 if top else y1
        sgn = 1 if top else -1
        bw, bh = 40.3 * k, 16.5 * k
        box = [cx - bw / 2, min(y, y + sgn * bh), cx + bw / 2, max(y, y + sgn * bh)]
        d.rectangle(box, outline=line, width=lw)
        gw, gh = 18.3 * k, 5.5 * k
        d.rectangle([cx - gw / 2, min(y, y + sgn * gh), cx + gw / 2, max(y, y + sgn * gh)], outline=line, width=lw)
    # círculo central relleno con el monograma
    r = 18 * k
    d.ellipse([cx - r - lw * 1.5, cy - r - lw * 1.5, cx + r + lw * 1.5, cy + r + lw * 1.5], fill=bg)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=line)
    f = ImageFont.truetype(BLACK, int(r * 1.05))
    bb = d.textbbox((0, 0), "DC", font=f)
    d.text((cx - (bb[2] + bb[0]) / 2, cy - (bb[3] + bb[1]) / 2), "DC", font=f, fill=ink)
    img.resize((800, 800), Image.LANCZOS).save(out)


o = sys.argv[1] if len(sys.argv) > 1 else "."
logo((10, 22, 15), (255, 214, 10), (10, 22, 15), f"{o}/logo_min_amarillo.png")
logo((10, 22, 15), (182, 255, 59), (10, 22, 15), f"{o}/logo_min_lima.png")
logo((255, 214, 10), (10, 22, 15), (255, 214, 10), f"{o}/logo_min_invertido.png")
