"""Reto «Solo el 1 % encuentra a…» (x_ck_): fan zone en una plaza llena de aficionados con camisetas de
selecciones; hay que encontrar a 3 cracks caricaturizados (estilo cacahuete, sin escudos ni fotos).
Se reconocen por camiseta + dorsal + pelo/barba; hay señuelos con la misma camiseta y otro dorsal.
La plaza se dibuja una vez y se cachea: nada cambia de sitio ni de tamaño."""
from __future__ import annotations

import random
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

from . import anim as A
from .anim_bean import C, K, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, vignette, _e
from .anim_busca import _clock

KITS = {   # camisetas de selección (solo colores, sin escudos)
    "ARG": (120, 176, 226), "POR": (190, 28, 40), "ESP": (206, 24, 34), "BRA": (250, 214, 40),
    "MEX": (20, 120, 70), "COL": (252, 206, 30), "FRA": (30, 50, 120), "URU": (110, 170, 230),
}
FAM = {"POR": "rojo", "ESP": "rojo", "ARG": "celeste", "URU": "celeste", "BRA": "amarillo", "COL": "amarillo",
       "MEX": "verde", "FRA": "azul"}
HCOL = [(40, 30, 26), (120, 70, 30), (230, 190, 90), (20, 20, 24), (160, 160, 160)]

# cada reto: semilla y los 3 cracks (fila, columna, kit, dorsal, pelo, color de pelo, barba)
RETOS = {
    "messi_cr_yamal": dict(seed=7, targets=[
        dict(name="Messi", row=6, col=9, kit="ARG", num="10", hair="pelo", hcol=(70, 44, 28), beard=True),
        dict(name="Cristiano", row=3, col=2, kit="POR", num="7", hair="tupe", hcol=(20, 20, 24), beard=False),
        dict(name="Yamal", row=9, col=4, kit="ESP", num="19", hair="rizos", hcol=(34, 24, 18), beard=False),
    ]),
    "valderrama_ronaldinho_hugo": dict(seed=31, scene="playa", targets=[
        dict(name="Valderrama", row=4, col=8, kit="COL", num="10", hair="afro", hcol=(236, 180, 70), beard=False),
        dict(name="Ronaldinho", row=8, col=2, kit="BRA", num="10", hair="cinta", hcol=(30, 22, 18), beard=False),
        dict(name="Hugo Sánchez", row=10, col=9, kit="MEX", num="9", hair="pelo", hcol=(30, 22, 18), beard=False,
             bigote=True),
    ]),
    "puyol_ronaldo_maradona": dict(seed=44, scene="estadio", targets=[
        dict(name="Puyol", row=5, col=3, kit="ESP", num="5", hair="melenon", hcol=(70, 46, 30), beard=False),
        dict(name="Ronaldo", row=7, col=10, kit="BRA", num="9", hair="cascao", hcol=(30, 24, 20), beard=False),
        dict(name="Maradona", row=10, col=6, kit="ARG", num="10", hair="rizado", hcol=(26, 20, 18), beard=False),
    ]),
}
ROWS, COLS = 12, 12


def _row(H, r):
    """Fila r (0 = fondo): y de los pies y escala, con perspectiva."""
    k = r / (ROWS - 1)
    y = H * (0.50 + 0.50 * k ** 1.15)
    s = 0.13 + 0.20 * k
    return y, s


def _backdrop(c, W, H):
    # cielo de tarde, edificios con ventanas, pantalla gigante y banderines
    c.r(-10, -10, W + 10, H * 0.45, 0, (250, 190, 120), w=0)
    c.r(-10, H * 0.16, W + 10, H * 0.45, 0, (245, 170, 110), w=0)
    rnd = random.Random(2)
    x = -20
    while x < W:
        w = rnd.uniform(110, 190)
        h = rnd.uniform(H * 0.16, H * 0.28)
        col = rnd.choice([(196, 120, 96), (176, 150, 120), (214, 190, 150), (150, 110, 100)])
        c.r(x, H * 0.42 - h, x + w, H * 0.45, 0, col, INK, 3)
        for yy in range(int(H * 0.42 - h + 18), int(H * 0.40), 34):
            for xx in range(int(x + 14), int(x + w - 18), 30):
                c.r(xx, yy, xx + 16, yy + 20, 2, (250, 226, 150) if rnd.random() < 0.4 else (90, 80, 96), INK, 1.5)
        x += w + rnd.uniform(-10, 6)
    # pantalla gigante
    c.r(W * 0.30, H * 0.18, W * 0.70, H * 0.33, 10, (24, 26, 36), INK, 5)
    c.r(W * 0.32, H * 0.19, W * 0.68, H * 0.32, 6, (60, 150, 80), w=0)
    c.l([(W * 0.50, H * 0.19), (W * 0.50, H * 0.32)], WHITE, 3)
    c.c(W * 0.50, H * 0.255, 28, (60, 150, 80), WHITE, 3)
    c.l([(W * 0.48, H * 0.33), (W * 0.47, H * 0.40)], (60, 60, 70), 10)
    c.l([(W * 0.52, H * 0.33), (W * 0.53, H * 0.40)], (60, 60, 70), 10)
    # banderines de colores (genéricos)
    for j, yy in enumerate((H * 0.12, H * 0.15)):
        pts = [(x2, yy + 30 * ((x2 / W - 0.5) ** 2) * 4) for x2 in range(-20, int(W) + 40, 40)]
        c.l(pts, (60, 50, 40), 2)
        for i, (px, py) in enumerate(pts[:-1]):
            col = list(KITS.values())[(i + j) % len(KITS)]
            c.p([(px, py), (px + 32, py + 2), (px + 16, py + 34)], col, INK, 1.5)
    # suelo de la plaza
    c.r(-10, H * 0.45, W + 10, H + 10, 0, (196, 184, 166), w=0)
    for i in range(14):
        y = H * (0.45 + 0.04 * i * (1 + i * 0.12))
        c.l([(-10, y), (W + 10, y)], (176, 164, 146), 2)


def _backdrop_playa(c, W, H):
    # cielo, sol, mar con olas, barco, sombrillas y arena
    c.r(-10, -10, W + 10, H * 0.30, 0, (130, 200, 245), w=0)
    c.r(-10, H * 0.18, W + 10, H * 0.30, 0, (170, 220, 250), w=0)
    c.c(W * 0.82, H * 0.08, 70, (255, 226, 90), INK, 4)
    for xx, yy in ((0.15, 0.07), (0.45, 0.12)):
        for dx, r in ((-40, 30), (0, 42), (40, 32)):
            c.c(W * xx + dx, H * yy, r, WHITE, w=0)
    c.r(-10, H * 0.30, W + 10, H * 0.46, 0, (40, 140, 200), INK, 3)
    for i in range(5):
        y = H * (0.32 + 0.03 * i)
        c.l([(x2, y + 6 * ((x2 // 40) % 2)) for x2 in range(-20, int(W) + 40, 40)], (230, 245, 255), 3)
    c.p([(W * 0.14, H * 0.305), (W * 0.26, H * 0.305), (W * 0.24, H * 0.32), (W * 0.16, H * 0.32)], (220, 80, 60), INK, 3)
    c.l([(W * 0.20, H * 0.305), (W * 0.20, H * 0.25)], INK, 3)
    c.p([(W * 0.20, H * 0.25), (W * 0.25, H * 0.295), (W * 0.20, H * 0.295)], WHITE, INK, 2)
    c.r(-10, H * 0.45, W + 10, H + 10, 0, (240, 214, 160), w=0)
    c.l([(x2, H * 0.455 + 8 * ((x2 // 60) % 2)) for x2 in range(-20, int(W) + 60, 60)], WHITE, 6)
    for i in range(12):
        y = H * (0.47 + 0.04 * i * (1 + i * 0.12))
        c.l([(-10, y), (W + 10, y)], (228, 200, 146), 2)
    rnd = random.Random(5)
    for xx in (0.06, 0.40, 0.70, 0.95):
        x, y = W * xx, H * 0.47
        col = rnd.choice([(230, 60, 50), (40, 120, 220), (250, 200, 40), (60, 170, 90)])
        c.l([(x, y), (x, y - 120)], (120, 90, 60), 5)
        c.chord(x - 80, y - 170, x + 80, y - 70, 180, 360, col, INK, 3)


def _backdrop_estadio(c, W, H):
    # cola para entrar al estadio: fachada con arcos, puertas numeradas, banderas y taquilla
    c.r(-10, -10, W + 10, H * 0.45, 0, (120, 170, 230), w=0)
    c.r(-10, H * 0.06, W + 10, H * 0.45, 0, (150, 190, 236), w=0)
    c.chord(-W * 0.4, H * 0.04, W * 1.4, H * 0.60, 180, 360, (200, 204, 214), INK, 5)
    c.chord(-W * 0.3, H * 0.10, W * 1.3, H * 0.60, 180, 360, (176, 182, 196), INK, 3)
    for i in range(9):
        x = W * (-0.05 + i * 0.14)
        c.r(x, H * 0.20, x + 56, H * 0.33, 26, (90, 100, 124), INK, 3)
    for i in range(3):
        x = W * (0.10 + i * 0.32)
        c.r(x, H * 0.34, x + 150, H * 0.45, 8, (60, 64, 80), INK, 4)
        for k in range(5):
            c.l([(x + 12 + k * 31, H * 0.345), (x + 12 + k * 31, H * 0.45)], (150, 156, 170), 4)
        c.r(x + 25, H * 0.305, x + 125, H * 0.335, 6, (222, 52, 40), INK, 3)
        c.text(x + 75, H * 0.304, str(i + 1), 36, WHITE, 0)
    for i, col in enumerate(KITS.values()):
        x = W * (0.03 + i * 0.13)
        c.l([(x, H * 0.04), (x, H * 0.17)], (90, 90, 96), 4)
        c.p([(x, H * 0.04), (x + 60, H * 0.065), (x, H * 0.09)], col, INK, 2)
    c.r(-10, H * 0.45, W + 10, H + 10, 0, (186, 180, 170), w=0)
    for i in range(14):
        y = H * (0.45 + 0.04 * i * (1 + i * 0.12))
        c.l([(-10, y), (W + 10, y)], (170, 164, 154), 2)


@lru_cache(maxsize=2)
def _plaza(W, H, key):
    P = RETOS[key]
    rnd = random.Random(P["seed"])
    b = C((W, H))
    {"playa": _backdrop_playa, "estadio": _backdrop_estadio}.get(P.get("scene"), _backdrop)(b, W, H)
    fg = C((W, H), "RGBA", (0, 0, 0, 0))
    tmap = {(t["row"], t["col"]): t for t in P["targets"]}
    found = {}
    kits = list(KITS)
    for r in range(ROWS):
        y0, s = _row(H, r)
        n = COLS + (1 if r % 2 else 0)
        for c in range(n):
            x = W * (-0.02 + (c + (0 if r % 2 else 0.5)) * 1.04 / COLS) + rnd.uniform(-8, 8)
            y = y0 + rnd.uniform(-6, 6)
            t = tmap.get((r, c))
            kit = rnd.choice(kits)
            kw = dict(body=KITS[kit], skin=BLANCO, hair=rnd.choice(["pelo", "gorra", "tupe", "melena", "pelo"]),
                      hcol=rnd.choice(HCOL), emo=rnd.choice(["feliz", "sorpresa", "serio", "picaro", "feliz", "enfado"]),
                      arms=rnd.choice(["relax", "arriba", "arriba", "jarras", "abiertos"]),
                      arm_r=rnd.choice([None, None, "arriba", "senala"]),
                      num=rnd.choice(["", "", "5", "9", "11", "8", "10", "7", "19"]), blink_off=rnd.random(),
                      beard=rnd.random() < 0.12, t=0.0)
            # señuelos: misma camiseta que un crack pero otro dorsal, o mismo dorsal sin el pelo/barba
            if t is None:
                for tg in P["targets"]:
                    if FAM[kit] == FAM[tg["kit"]] and kw["num"] == tg["num"]:
                        kw["num"] = "9" if tg["num"] != "9" else "8"
            else:
                kw.update(body=KITS[t["kit"]], num=t["num"], hair=t["hair"], hcol=t["hcol"], beard=t["beard"], bigote=t.get("bigote", False),
                          emo="serio", arms="relax", arm_r="arriba" if t["name"] != "Messi" else None)
            bean(fg, x, y, s, **kw)
            if t is not None:
                hx, hy = bean_head(x, y, s)
                found[t["name"]] = (hx, hy + 90 * s, s)
    b.im = b.im.convert("RGBA")
    b.im.alpha_composite(fg.im)
    return b.im.convert("RGB").resize((int(W), int(H)), Image.LANCZOS), found


def _card(c, x, y, s, tg, t, name_size=48, label=True):
    """Ficha de un crack: fondo redondeado, el personaje y su nombre debajo."""
    w, h = 300 * s, 420 * s
    c.r(x - w / 2, y - h, x + w / 2, y + 16 * s, 26 * s, (255, 250, 238), INK, 6 * s)
    bean(c, x, y - 20 * s, 0.78 * s, KITS[tg["kit"]], BLANCO, tg["hair"], tg["hcol"], emo="picaro", t=t,
         num=tg["num"], beard=tg["beard"], bigote=tg.get("bigote", False), arms="relax", blink_off=hash(tg["name"]) % 3)
    if label:
        from .anim_extra import font
        f = font(int(name_size * s * K))
        tw = c.d.textlength(tg["name"], font=f) / K
        if tw > w - 40 * s:   # nombres largos: letra más pequeña para que no se pisen
            name_size *= (w - 40 * s) / tw
            f = font(int(name_size * s * K))
            tw = c.d.textlength(tg["name"], font=f) / K
        c.r(x - tw / 2 - 16 * s, y + 4 * s, x + tw / 2 + 16 * s, y + 4 * s + name_size * s * 1.25, 12 * s,
            (222, 52, 40), INK, 4 * s)
        c.text(x, y + 2 * s, tg["name"], name_size * s, WHITE, 0)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    parts = kind.split("_", 3)
    key = parts[3] if len(parts) > 3 else "messi_cr_yamal"
    img, found = _plaza(int(W), int(H), key)
    img = img.copy()
    tgs = RETOS[key]["targets"]
    if kind.startswith("x_ck_fichas"):
        # presentación: plaza desenfocada y oscura, las 3 fichas entran una a una con su nombre
        img = Image.blend(img.filter(ImageFilter.GaussianBlur(10)), Image.new("RGB", img.size, (10, 12, 24)), 0.45)
        lay = C((W, H), "RGBA", (0, 0, 0, 0))
        for i, tg in enumerate(tgs):
            t0 = 0.30 * i - 0.18   # la primera ya está en el primer fotograma
            if t < t0:
                continue
            k = min(1.0, (t - t0) / 0.18)
            sc = 0.95 * (1 + 0.12 * (1 - k))
            _card(lay, W * (0.18 + 0.32 * i), H * 0.66, sc * 0.92, tg, t)
        l = lay.im.resize(img.size, Image.LANCZOS)
        img.paste(l, (0, 0), l)
        return vignette(img, 0.22)
    if kind.startswith("x_ck_reto"):
        # recordatorio: las 3 fichas en pequeño sobre la pantalla gigante, fijas durante toda la búsqueda
        lay = C((W, H), "RGBA", (0, 0, 0, 0))
        for i, tg in enumerate(tgs):
            _card(lay, W * (0.30 + 0.20 * i), H * 0.395, 0.42, tg, 0.0, name_size=58)
        l = lay.im.resize(img.size, Image.LANCZOS)
        img.paste(l, (0, 0), l)
        _clock(img, t, 0.0, n=max(3, int(round(dur - 0.3))))
    elif kind.startswith("x_ck_sol"):
        k = _e(min(1.0, t / 0.6))
        mask = Image.new("L", img.size, 0)
        dm = ImageDraw.Draw(mask)
        for name, (x, y, s) in found.items():
            r = 240 * s
            dm.ellipse([x - r, y - r * 1.25, x + r, y + r * 1.15], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(5))
        darkimg = Image.blend(img, Image.new("RGB", img.size, (6, 8, 20)), 0.72 * k)
        img = Image.composite(img, darkimg, mask)
        d = ImageDraw.Draw(img)
        from .anim_extra import font
        f = font(34)
        for i, (name, (x, y, s)) in enumerate(found.items()):
            if t < 0.3 + 0.35 * i:
                continue
            r = 240 * s
            d.ellipse([x - r, y - r * 1.25, x + r, y + r * 1.15], outline=(222, 52, 40), width=7)
            tw = d.textlength(name, font=f)
            ly = y + r * 1.15 + 8
            d.rounded_rectangle([x - tw / 2 - 12, ly, x + tw / 2 + 12, ly + 46], 10, fill=(222, 52, 40), outline=INK, width=3)
            d.text((x - tw / 2, ly + 4), name, font=f, fill=WHITE)
    img = vignette(img, 0.22)
    return img
