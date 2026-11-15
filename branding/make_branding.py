"""Genera banner (2560x1440) y avatar (800x800) del canal."""
import sys
from PIL import Image, ImageDraw, ImageFont

BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
SEMI = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
GREEN_D, GREEN_L, YELLOW, WHITE = (6, 46, 28), (14, 92, 52), (255, 214, 10), (255, 255, 255)
out = sys.argv[1] if len(sys.argv) > 1 else "."


def pitch(w, h):
    img = Image.new("RGB", (w, h), GREEN_D)
    d = ImageDraw.Draw(img)
    stripe = w // 16
    for i in range(0, 16, 2):
        d.rectangle([i * stripe, 0, (i + 1) * stripe, h], fill=(9, 56, 34))
    lw = max(4, w // 400)
    d.line([(w // 2, 0), (w // 2, h)], fill=(40, 110, 70), width=lw)
    r = h // 4
    d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], outline=(40, 110, 70), width=lw)
    return img, d


# Banner: el área segura visible en todos los dispositivos es 1546x423 centrada.
img, d = pitch(2560, 1440)
cx, cy = 1280, 720
f1, f2 = ImageFont.truetype(BOLD, 190), ImageFont.truetype(SEMI, 54)
w1 = d.textlength("DATO", font=f1); w2 = d.textlength("CRACK", font=f1)
x = cx - (w1 + 30 + w2) / 2
d.text((x, cy - 150), "DATO", font=f1, fill=WHITE)
d.text((x + w1 + 30, cy - 150), "CRACK", font=f1, fill=YELLOW)
sub = "Datos, retos y curiosidades del fútbol · Shorts cada día"
d.text((cx - d.textlength(sub, font=f2) / 2, cy + 80), sub, font=f2, fill=WHITE)
img.save(f"{out}/banner_2560x1440.png")

# Avatar: se recorta en círculo.
img, d = pitch(800, 800)
d.ellipse([60, 60, 740, 740], fill=YELLOW)
f = ImageFont.truetype(BOLD, 300)
t = "DC"
d.text((400 - d.textlength(t, font=f) / 2, 235), t, font=f, fill=GREEN_D)  # centrado óptico
img.save(f"{out}/avatar_800x800.png")
