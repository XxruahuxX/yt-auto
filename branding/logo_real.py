"""Logo realista: balón 3D sombreado, césped con textura y "DC" dorado con relieve."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 1600
OUT = sys.argv[1] if len(sys.argv) > 1 else "logo_real.png"
BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
rng = np.random.default_rng(3)


def grass(size):
    # ruido multiescala + briznas verticales + franjas de corte + viñeta
    base = np.zeros((size, size))
    for k, amp in ((8, 0.5), (32, 0.3), (128, 0.2)):
        small = rng.random((k, k))
        base += amp * np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)) / 255
    blades = rng.random((size // 3, size))
    blades = np.asarray(Image.fromarray((blades * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)) / 255
    stripes = 0.5 + 0.5 * (np.sin(np.linspace(0, 6 * np.pi, size))[None, :] > 0)
    v = 0.55 * base + 0.3 * blades + 0.15 * stripes
    y, x = np.mgrid[0:size, 0:size] / size
    vign = 1 - 0.9 * ((x - 0.5) ** 2 + (y - 0.42) ** 2)
    light = np.clip(vign, 0.15, 1)
    r = (12 + 40 * v) * light
    g = (60 + 110 * v) * light
    b = (22 + 40 * v) * light
    return Image.fromarray(np.dstack([r, g, b]).clip(0, 255).astype(np.uint8)).convert("RGBA")


def _coeffs(src, dst):
    """Coeficientes de Image.transform(PERSPECTIVE) que llevan dst -> src."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def pitch_lines(size):
    """Campo visto desde arriba (105x68 m, eje largo en vertical) y proyectado en perspectiva."""
    k = 20  # px por metro
    W, H = 68 * k, 105 * k
    m = 6 * k
    lay = Image.new("L", (W + 2 * m, H + 2 * m), 0)
    d = ImageDraw.Draw(lay)
    lw = int(0.12 * k * 6)
    X0, Y0 = m, m
    d.rectangle([X0, Y0, X0 + W, Y0 + H], outline=255, width=lw)
    d.line([X0, Y0 + H / 2, X0 + W, Y0 + H / 2], fill=255, width=lw)
    cx, cy = X0 + W / 2, Y0 + H / 2
    r = 9.15 * k
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=lw)
    d.ellipse([cx - 0.4 * k, cy - 0.4 * k, cx + 0.4 * k, cy + 0.4 * k], fill=255)
    for top in (True, False):
        y = Y0 if top else Y0 + H
        sgn = 1 if top else -1
        d.rectangle(sorted_box(cx - 20.16 * k, y, cx + 20.16 * k, y + sgn * 16.5 * k), outline=255, width=lw)
        d.rectangle(sorted_box(cx - 9.16 * k, y, cx + 9.16 * k, y + sgn * 5.5 * k), outline=255, width=lw)
        py = y + sgn * 11 * k
        d.ellipse([cx - 0.3 * k, py - 0.3 * k, cx + 0.3 * k, py + 0.3 * k], fill=255)
        bb = [cx - r, py - r, cx + r, py + r]
        d.arc(bb, 37 if top else 217, 143 if top else 323, fill=255, width=lw)
    # perspectiva: fondo estrecho arriba, primer plano ancho abajo
    src = [(0, 0), (lay.width, 0), (lay.width, lay.height), (0, lay.height)]
    dst = PITCH_DST(size)
    proj = lay.transform((size, size), Image.PERSPECTIVE, _coeffs(src, dst), Image.BICUBIC)
    # se desvanecen hacia el fondo
    fade = np.clip(0.55 + np.linspace(0, 1, size) * 0.6, 0, 1)[:, None] * np.ones((1, size))
    a = (np.asarray(proj, float) * fade * 0.85).astype(np.uint8)
    out = Image.new("RGBA", (size, size), (240, 255, 240, 0))
    out.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(1.2)))
    return out


def PITCH_DST(size):
    return [(size * 0.30, size * 0.30), (size * 0.70, size * 0.30), (size * 1.25, size * 1.30), (-size * 0.25, size * 1.30)]


def center_spot(size):
    """Dónde cae el centro del campo tras la perspectiva."""
    m, W, H = 120, 68 * 20, 105 * 20
    src = [(0, 0), (W + 2 * m, 0), (W + 2 * m, H + 2 * m), (0, H + 2 * m)]
    c = _coeffs(PITCH_DST(size), src)  # src -> dst
    x, y = m + W / 2, m + H / 2
    den = c[6] * x + c[7] * y + 1
    return (c[0] * x + c[1] * y + c[2]) / den, (c[3] * x + c[4] * y + c[5]) / den


def sorted_box(x0, y0, x1, y1):
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def icosa():
    p = (1 + 5 ** 0.5) / 2
    v = []
    for a in (-1, 1):
        for b in (-p, p):
            v += [(0, a, b), (a, b, 0), (b, 0, a)]
    v = np.array(v, float)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def ball(size, rot=(0.35, -0.5)):
    R = size / 2
    y, x = (np.mgrid[0:size, 0:size] + 0.5 - R) / R
    r2 = x ** 2 + y ** 2
    inside = r2 <= 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    n = np.stack([x, -y, z], -1)  # normal en el espacio de la vista
    # rotación del balón
    ax, ay = rot
    Rx = np.array([[1, 0, 0], [0, np.cos(ax), -np.sin(ax)], [0, np.sin(ax), np.cos(ax)]])
    Ry = np.array([[np.cos(ay), 0, np.sin(ay)], [0, 1, 0], [-np.sin(ay), 0, np.cos(ay)]])
    p = n @ (Ry @ Rx).T
    pent = icosa()  # 12 centros de pentágono
    # 20 centros de hexágono = centros de las caras del icosaedro
    faces = []
    for i in range(12):
        for j in range(i + 1, 12):
            for k in range(j + 1, 12):
                if all(np.dot(pent[a], pent[b]) > 0.4 for a, b in ((i, j), (j, k), (i, k))):
                    c = pent[i] + pent[j] + pent[k]
                    faces.append(c / np.linalg.norm(c))
    centers = np.vstack([pent, np.array(faces)])
    dots = p @ centers.T
    order = np.sort(dots, axis=-1)
    best = np.argmax(dots, -1)
    is_pent = best < 12
    seam = (order[..., -1] - order[..., -2]) < 0.012
    albedo = np.where(is_pent, 0.07, 0.94)
    albedo = np.where(seam, 0.35, albedo)
    # iluminación: luz de estadio arriba a la izquierda
    L = np.array([-0.45, 0.6, 0.66]); L /= np.linalg.norm(L)
    diff = np.clip(n @ L, 0, 1)
    H = L + np.array([0, 0, 1]); H /= np.linalg.norm(H)
    spec = np.clip(n @ H, 0, 1) ** 60 * 0.9
    rim = (1 - z) ** 3 * 0.25
    shade = 0.18 + 0.82 * diff
    col = albedo[..., None] * shade[..., None] * np.array([1.0, 1.0, 0.98]) + spec[..., None] + rim[..., None] * np.array([0.3, 0.7, 0.4])
    rgb = (col.clip(0, 1) * 255).astype(np.uint8)
    edge = np.clip((1 - np.sqrt(r2)) * R * 1.5, 0, 1)  # antialias del borde
    a = (inside * edge * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


def gold_text(text, font_size, size):
    font = ImageFont.truetype(BLACK, font_size)
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    bb = d.textbbox((0, 0), text, font=font)
    pos = ((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1])
    d.text(pos, text, font=font, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # sombra proyectada
    sh = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sh.putalpha(mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v * 0.8))
    out.alpha_composite(sh, (16, 30))
    # extrusión 3D
    for k in range(22, 0, -1):
        c = int(70 + 2 * k)
        layer = Image.new("RGBA", (size, size), (c + 40, c, 0, 255))
        layer.putalpha(mask)
        out.alpha_composite(layer, (k // 2, k))
    # cara frontal: degradado dorado + bisel
    h = np.linspace(0, 1, size)[:, None] * np.ones((1, size))
    stops = np.array([[255, 236, 140], [255, 200, 30], [214, 140, 0], [255, 214, 60]])
    t = h * 3
    i = np.clip(t.astype(int), 0, 2)
    f = (t - i)[..., None]
    grad = (stops[i] * (1 - f) + stops[i + 1] * f).astype(np.uint8)
    face = Image.fromarray(grad, "RGB").convert("RGBA")
    bevel = mask.filter(ImageFilter.GaussianBlur(10))
    emb = ImageChops.subtract(bevel, bevel.transform(bevel.size, Image.AFFINE, (1, 0, 6, 0, 1, 8)))
    hl = Image.new("RGBA", (size, size), (255, 255, 230, 0)); hl.putalpha(emb.point(lambda v: min(255, v * 3)))
    face.alpha_composite(hl)
    face.putalpha(mask)
    out.alpha_composite(face)
    # contorno oscuro fino
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(9)), mask)
    ol = Image.new("RGBA", (size, size), (60, 30, 0, 255)); ol.putalpha(edge)
    out.alpha_composite(ol)
    return out


img = grass(S)
img.alpha_composite(pitch_lines(S))
# foco de estadio
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([S * .1, -S * .4, S * .9, S * .35], fill=(255, 255, 220, 70))
img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
B = int(S * 0.44)
spot_x, spot_y = center_spot(S)
b = ball(B)
# sombra de contacto del balón
sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(sh).ellipse([spot_x - B * .42, spot_y - B * .06, spot_x + B * .50, spot_y + B * .07], fill=(0, 0, 0, 170))
img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
img.alpha_composite(b, (int(spot_x - B / 2), int(spot_y - B * 0.97)))
img.alpha_composite(gold_text("DC", int(S * 0.34), S), (0, int(S * 0.24)))
img.convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT)
