"""Animaciones de personajes a pantalla completa: Messi y Cristiano, campo redondo, la abuela y el VAR madre."""
from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFont

from . import anim as A
from .anim_robot import ball, cam, player, SKINS

BOLD = A.BOLD
WHITE, INK = (255, 255, 255), (10, 12, 20)
YEL, CYAN = (255, 214, 10), (40, 230, 255)
BLAU, RED, MAD = (20, 60, 150), (220, 45, 55), (245, 245, 245)


def _e(x):
    return A._ease(x)


def font(n):
    return ImageFont.truetype(BOLD, int(n))


def stripes(im, cols=((34, 120, 62), (40, 134, 70))):
    d = ImageDraw.Draw(im)
    for i in range(12):
        d.rectangle([i * A.PW / 12, 0, (i + 1) * A.PW / 12, A.PH], fill=cols[i % 2])
    return d


def person(d, x, y, s, shirt, skin, hair="corto", hair_col=(40, 28, 20), num="", name="", phase=0.0, run=0.0,
           pose="", glasses=False, shorts=(30, 30, 40), legs=None, skirt=False, mouth="sonrisa", arm_up=0.0):
    """Personaje de dibujo grande (cabeza grande). (x, y) = pies."""
    sw = math.sin(phase) * run
    d.ellipse([x - 40 * s, y - 8 * s, x + 40 * s, y + 8 * s], fill=(0, 0, 0) if False else (24, 80, 40))
    lc = legs or skin
    hip = (x, y - 70 * s)
    for sg in (1, -1):
        knee = (x + sg * (8 + sw * 18) * s, y - 36 * s)
        foot = (x + sg * (10 + sw * 28) * s, y - max(0, sg * sw) * 14 * s)
        d.line([(x + sg * 9 * s, hip[1]), knee, foot], fill=lc, width=int(15 * s), joint="curve")
        d.ellipse([foot[0] - 12 * s, foot[1] - 7 * s, foot[0] + 14 * s, foot[1] + 6 * s], fill=(25, 25, 30))
    if skirt:
        d.polygon([(x - 34 * s, y - 50 * s), (x + 34 * s, y - 50 * s), (x + 24 * s, y - 92 * s), (x - 24 * s, y - 92 * s)], fill=shorts)
    else:
        d.rounded_rectangle([x - 26 * s, y - 92 * s, x + 26 * s, y - 62 * s], 8 * s, fill=shorts)
    d.rounded_rectangle([x - 30 * s, y - 150 * s, x + 30 * s, y - 86 * s], 14 * s, fill=shirt)
    for sg in (1, -1):
        sh = (x + sg * 27 * s, y - 142 * s)
        up = arm_up if sg == 1 else 0
        if pose == "brazos_cruzados":
            hand = (x - sg * 14 * s, y - 116 * s)
        elif pose == "senala" and sg == 1:
            hand = (x + 70 * s, y - 170 * s)
        elif pose == "cielo" and sg == 1:
            hand = (x + 22 * s, y - 250 * s)
        elif pose == "siu":
            hand = (x + sg * 62 * s, y - 112 * s)
        else:
            hand = (x + sg * (36 - 10 * sw * sg) * s, y - (102 + 120 * up) * s - sg * sw * 18 * s)
        d.line([sh, hand], fill=skin, width=int(13 * s))
        d.ellipse([hand[0] - 9 * s, hand[1] - 9 * s, hand[0] + 9 * s, hand[1] + 9 * s], fill=skin)
    if num:
        f = font(34 * s)
        d.text((x - d.textlength(num, font=f) / 2, y - 144 * s), num, font=f, fill=WHITE)
    # cabeza
    hx, hy, hr = x, y - 188 * s, 40 * s
    if hair == "melena":
        d.ellipse([hx - hr * 1.15, hy - hr * 1.15, hx + hr * 1.15, hy + hr * 0.5], fill=hair_col)
        for sg in (-1, 1):
            d.rounded_rectangle(sorted([hx + sg * hr * 1.18, hx + sg * hr * 0.7]) and [min(hx + sg * hr * 1.18, hx + sg * hr * 0.7), hy - hr * 0.3, max(hx + sg * hr * 1.18, hx + sg * hr * 0.7), hy + hr * 1.35], 10 * s, fill=hair_col)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=skin)
    if hair == "corto":
        d.chord([hx - hr, hy - hr * 1.08, hx + hr, hy + hr * 0.5], 180, 360, fill=hair_col)
    elif hair == "tupe":
        d.chord([hx - hr, hy - hr * 1.15, hx + hr, hy + hr * 0.4], 180, 360, fill=hair_col)
        d.ellipse([hx - hr * 0.2, hy - hr * 1.35, hx + hr * 0.9, hy - hr * 0.6], fill=hair_col)
    elif hair == "barba":
        d.chord([hx - hr, hy - hr * 1.08, hx + hr, hy + hr * 0.5], 180, 360, fill=hair_col)
        d.chord([hx - hr * 0.9, hy - hr * 0.2, hx + hr * 0.9, hy + hr * 1.02], 0, 180, fill=hair_col)
    elif hair == "mono":
        d.chord([hx - hr, hy - hr * 1.05, hx + hr, hy + hr * 0.3], 180, 360, fill=hair_col)
        d.ellipse([hx - hr * 0.45, hy - hr * 1.55, hx + hr * 0.45, hy - hr * 0.75], fill=hair_col)
    elif hair == "melena":
        d.chord([hx - hr * 1.05, hy - hr * 1.12, hx + hr * 1.05, hy + hr * 0.2], 180, 360, fill=hair_col)
    for sg in (-1, 1):
        d.ellipse([hx + sg * 14 * s - 5 * s, hy - 6 * s, hx + sg * 14 * s + 5 * s, hy + 6 * s], fill=INK)
    if glasses:
        for sg in (-1, 1):
            d.ellipse([hx + sg * 15 * s - 12 * s, hy - 11 * s, hx + sg * 15 * s + 12 * s, hy + 11 * s], outline=INK, width=max(1, int(3 * s)))
        d.line([(hx - 4 * s, hy), (hx + 4 * s, hy)], fill=INK, width=max(1, int(3 * s)))
    if mouth == "sonrisa":
        d.arc([hx - 14 * s, hy + 4 * s, hx + 14 * s, hy + 24 * s], 20, 160, fill=INK, width=max(1, int(4 * s)))
    elif mouth == "abierta":
        d.ellipse([hx - 11 * s, hy + 10 * s, hx + 11 * s, hy + 28 * s], fill=(120, 30, 30))
    elif mouth == "enfado":
        d.arc([hx - 12 * s, hy + 16 * s, hx + 12 * s, hy + 30 * s], 200, 340, fill=INK, width=max(1, int(4 * s)))
        for sg in (-1, 1):
            d.line([(hx + sg * 22 * s, hy - 16 * s), (hx + sg * 6 * s, hy - 10 * s)], fill=INK, width=max(1, int(4 * s)))
    if name:
        A._label(d, x, y + 16 * s, name, 30 * min(s, 1.4), YEL, center=True)


def bubble(d, x, y, text, size=48, col=WHITE, fg=INK):
    f = font(size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x - w / 2 - 22, y - size * 0.75, x + w / 2 + 22, y + size * 0.75], 26, fill=col, outline=INK, width=4)
    d.polygon([(x - 14, y + size * 0.72), (x + 14, y + size * 0.72), (x, y + size * 1.3)], fill=col)
    d.text((x - w / 2, y - size * 0.62), text, font=f, fill=fg)


def stamp(im, text, cx, cy, t0, t, bg=YEL, fg=INK, size=70, rot=-5):
    if t < t0:
        return
    k = _e((t - t0) / 0.25)
    f = font(size)
    w = int(ImageDraw.Draw(im).textlength(text, font=f)) + 60
    st = Image.new("RGBA", (w, int(size * 1.7)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([0, 0, w - 1, st.height - 1], 18, fill=bg, outline=INK, width=6)
    sd.text((30, size * 0.2), text, font=f, fill=fg)
    sc = 1.6 - 0.6 * k
    st = st.resize((max(1, int(st.width * sc)), max(1, int(st.height * sc)))).rotate(rot, expand=True, resample=Image.BICUBIC)
    im.paste(st, (int(cx - st.width / 2), int(cy - st.height / 2)), st)


def trophy(d, x, y, s, col=(230, 190, 60)):
    d.polygon([(x - 30 * s, y - 120 * s), (x + 30 * s, y - 120 * s), (x + 18 * s, y - 60 * s), (x - 18 * s, y - 60 * s)], fill=col)
    for sg in (-1, 1):
        d.arc([x + sg * 30 * s - 22 * s, y - 116 * s, x + sg * 30 * s + 22 * s, y - 80 * s], 90 if sg > 0 else 270, 270 if sg > 0 else 90, fill=col, width=int(7 * s))
    d.rectangle([x - 6 * s, y - 60 * s, x + 6 * s, y - 30 * s], fill=col)
    d.rounded_rectangle([x - 26 * s, y - 32 * s, x + 26 * s, y], 6 * s, fill=(70, 50, 30))


def round_pitch(im, t, k=1.0, players=True):
    """Campo que pasa de rectangular (k=0) a redondo (k=1)."""
    PW, PH = A.PW, A.PH
    d = stripes(im)
    cx, cy = PW / 2, PH * 0.5
    hw, hh = PW * 0.42, PH * 0.3
    r = min(hw, hh) * 0 + (hw if hw < hh else hh)
    rad = k * hw
    d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], int(rad), outline=WHITE, width=6)
    d.line([(cx - hw, cy), (cx + hw, cy)], fill=WHITE, width=5)
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], outline=WHITE, width=5)
    for sg in (-1, 1):
        y0 = cy + sg * hh
        d.rectangle([cx - 140, min(y0, y0 - sg * 100), cx + 140, max(y0, y0 - sg * 100)], outline=WHITE, width=5)
        d.rectangle([cx - 50, min(y0, y0 + sg * 14), cx + 50, max(y0, y0 + sg * 14)], fill=WHITE)
    return d, (cx, cy, hw, hh)


def render(kind, t, dur):
    PW, PH = A.PW, A.PH
    if kind[:5] in ("x_gk_", "x_sd_", "x_tj_"):
        from .anim_pro import render as rp
        return rp(kind, t, dur)
    if kind[:5] in ("x_ce_", "x_mn_"):
        from .anim_dia23 import render as r23
        return r23(kind, t, dur)
    if kind[:5] == "x_ya_":
        from .anim_yaya import render as rya
        return rya(kind, t, dur)
    if kind[:5] in ("x_dz_", "x_bm_"):
        from .anim_dia22 import render as r22
        return r22(kind, t, dur)
    if kind.startswith("x_ck_"):
        from .anim_cracks import render as rck
        return rck(kind, t, dur)
    if kind[:5] in ("x_cl_", "x_ml_"):
        from .anim_dia24 import render as r24
        return r24(kind, t, dur)
    if kind.startswith("x_bs_"):
        from .anim_busca import render as rbs
        return rbs(kind, t, dur)
    if kind.startswith("x_pc_"):
        from .anim_portero import render as rpc
        return rpc(kind, t, dur)
    if kind.startswith("x_am_"):
        from .anim_amigo import render as ram
        return ram(kind, t, dur)
    if kind.startswith("x_md_"):
        from .anim_madre import render as rmd
        return rmd(kind, t, dur)
    if kind.startswith("x_gm_"):
        from .anim_gemelos import render as rgm
        return rgm(kind, t, dur)
    if kind.startswith("x_ap_"):
        from .anim_apagon import render as rap
        return rap(kind, t, dur)
    if kind.startswith("x_bn_"):
        from .anim_bean import render as rb
        return rb(kind, t, dur)
    if kind.startswith("x_mt_"):
        from .anim_toon import render as rt
        return rt(kind, t, dur)
    if kind.startswith("x_st_"):
        from .anim_story import render as rst
        return rst(kind, t, dur)
    if kind[:5] in ("x_ym_", "x_pi_", "x_pm_"):
        from .anim_sab import render as rsab
        return rsab(kind, t, dur)
    if kind[:5] in ("x_nv_", "x_mz_", "x_cs_"):
        from .anim_vie import render as rv
        return rv(kind, t, dur)
    if kind[:5] in ("x_bp_", "x_pk_", "x_cu_", "x_dc_"):
        from .anim_jue import render as rj
        return rj(kind, t, dur)
    if kind.startswith("x_rb_"):
        from .anim_serie import render as rs
        return rs(kind, t, dur)
    im = Image.new("RGB", (PW, PH))
    # ---------- Messi y Cristiano ----------
    if kind == "x_mc_presenta":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(14, 18, 34))
        for i in range(14):
            a = i / 14 * 2 * math.pi + t * 0.3
            d.polygon([(PW / 2, PH * 0.5), (PW / 2 + 1400 * math.cos(a), PH * 0.5 + 1400 * math.sin(a)),
                       (PW / 2 + 1400 * math.cos(a + 0.12), PH * 0.5 + 1400 * math.sin(a + 0.12))], fill=(24, 30, 56))
        k = _e(t / 0.6)
        person(d, PW / 2 - 150 - 300 * (1 - k), PH * 0.66, 1.5, (100, 170, 230), SKINS[0], "barba", (90, 60, 30), "10", "MESSI", pose="brazos_cruzados")
        person(d, PW / 2 + 150 + 300 * (1 - k), PH * 0.66, 1.5, (100, 170, 230), SKINS[0], "tupe", (30, 22, 16), "7", "CRISTIANO", pose="brazos_cruzados")
        stamp(im, "MISMO EQUIPO", PW / 2, PH * 0.3, 1.0, t)
    elif kind == "x_mc_champions":
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, PW, PH], fill=(10, 16, 40))
        rng = random.Random(4)
        for _ in range(60):
            x, y = rng.uniform(0, PW), rng.uniform(0, PH)
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(200, 210, 255))
        n = min(9, int(t / 0.3) + 1)
        for i in range(n):
            row, col = (0, i) if i < 4 else (1, i - 4)
            x = PW / 2 + (col - (1.5 if row == 0 else 2)) * 150
            y = PH * (0.48 if row == 0 else 0.66)
            trophy(d, x, y, 1.1, (230, 190, 60))
        A._label(d, 40, PH * 0.3, "MESSI: 4", 44, (100, 170, 230))
        A._label(d, PW - 300, PH * 0.3, "CR7: 5", 44, (255, 120, 120))
        if n == 9:
            stamp(im, "9 CHAMPIONS", PW / 2, PH * 0.78, 9 * 0.3, t)
    elif kind == "x_mc_falta":
        d = stripes(im)
        bx, by = PW / 2, PH * 0.6
        k = _e(t / 1.0)
        person(d, bx - 260 + 130 * k, by + 40, 1.3, (100, 170, 230), SKINS[0], "barba", (90, 60, 30), "10", phase=t * 8, run=1 - k)
        person(d, bx + 260 - 130 * k, by + 40, 1.3, (100, 170, 230), SKINS[0], "tupe", (30, 22, 16), "7", phase=t * 8 + 1, run=1 - k)
        ball(d, bx, by + 30, 16)
        if t > 1.0:
            bubble(d, bx - 170, by - 330, "¡MÍA!", 50)
        if t > 1.5:
            bubble(d, bx + 170, by - 330, "¡NO, MÍA!", 50)
        im = cam(im, bx, by - 120, 1.1 + 0.15 * _e((t - 1) / 2))
    elif kind == "x_mc_rival":
        d = stripes(im)
        for i in range(4):
            x = PW / 2 + (i - 1.5) * 150
            y = PH * 0.62
            shake = 6 * math.sin(t * 40 + i)
            person(d, x + shake, y, 1.0, (40, 40, 40), SKINS[i], "corto", (30, 20, 10), str(i + 2), pose="brazos_cruzados", mouth="abierta")
            for j in range(2):
                q = (t * 1.5 + j * 0.5 + i * 0.2) % 1
                dx, dy = x + 30 + shake, y - 230 + 60 * q
                d.ellipse([dx - 6, dy - 9, dx + 6, dy + 9], fill=(120, 200, 255))
        A._label(d, PW / 2, PH * 0.3, "La barrera… temblando", 44, WHITE, center=True)
    elif kind == "x_mc_gol":
        d = stripes(im)
        j = abs(math.sin(t * 3)) * 80
        person(d, PW / 2 + 150, PH * 0.66 - j, 1.4, (100, 170, 230), SKINS[0], "tupe", (30, 22, 16), "7", pose="siu", mouth="abierta")
        person(d, PW / 2 - 150, PH * 0.66, 1.4, (100, 170, 230), SKINS[0], "barba", (90, 60, 30), "10", pose="cielo")
        if t > 0.4:
            f = font(110)
            d.text((PW / 2 - 230, PH * 0.3), "¡SIUUU!", font=f, fill=YEL, stroke_width=8, stroke_fill=INK)
        stamp(im, "¡GOL!", PW / 2, PH * 0.84, 0.2, t)
    # ---------- Campo redondo ----------
    elif kind == "x_red_cambio":
        k = _e((t - 0.6) / 1.4)
        d, (cx, cy, hw, hh) = round_pitch(im, t, k)
        A._label(d, PW / 2, PH * 0.27, "Rectangular  →  Redondo", 40, YEL, center=True)
    elif kind == "x_red_regla":
        d, _ = round_pitch(im, t, 0)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([PW * 0.12, PH * 0.32, PW * 0.88, PH * 0.6], 30, fill=(245, 240, 225), outline=INK, width=6)
        f = font(48)
        d.text((PW * 0.17, PH * 0.35), "REGLA 1", font=f, fill=RED)
        f2 = font(40)
        for i, l in enumerate(["«El terreno de juego", "será rectangular»"]):
            d.text((PW * 0.17, PH * 0.42 + i * 56), l, font=f2, fill=INK)
    elif kind == "x_red_corner":
        d, (cx, cy, hw, hh) = round_pitch(im, t, 1)
        p = min(t / 1.2, 1)
        bx, by = cx + (hw - 10) * math.cos(-0.7) * p + 0, cy - hh * 0.9 * p
        ball(d, cx + hw * 0.7 * p, cy - hh * 0.75 * p, 14)
        person(d, cx + hw * 0.55, cy - hh * 0.2, 0.9, RED, SKINS[2], "corto", (20, 10, 5), "9", mouth="abierta")
        if t > 1.2:
            bubble(d, cx + hw * 0.55, cy - hh * 0.2 - 260, "¿Córner? ¿Dónde?", 40)
    elif kind == "x_red_carrera":
        d, (cx, cy, hw, hh) = round_pitch(im, t, 1)
        for i in range(8):
            a = t * 1.4 + i * 2 * math.pi / 8
            x, y = cx + hw * 0.9 * math.cos(a), cy + hh * 0.9 * math.sin(a)
            person(d, x, y + 40, 0.55, RED if i % 2 else BLAU, SKINS[i % 4], "corto", (30, 20, 10), str(i + 2), phase=t * 10 + i, run=1)
        A._label(d, PW / 2, PH * 0.27, "Sin esquinas: carrera infinita", 38, YEL, center=True)
    elif kind == "x_red_medidas":
        d, (cx, cy, hw, hh) = round_pitch(im, t, 1)
        k = _e(t / 0.8)
        d.line([(cx, cy - hh), (cx, cy - hh + 2 * hh * k)], fill=YEL, width=8)
        if k >= 1:
            A._label(d, cx + 30, cy - 30, "90-120 m", 50, YEL)
    # ---------- La abuela ----------
    elif kind.startswith("x_ab_"):
        d = stripes(im)
        gx, gy = PW / 2, PH * 0.66
        abu = dict(shirt=(110, 60, 140), skin=SKINS[0], hair="mono", hair_col=(200, 200, 205), glasses=True, shorts=(60, 40, 80), skirt=True, legs=(220, 190, 170))
        if kind == "x_ab_entra":
            d.rectangle([0, 0, PW, PH * 0.3], fill=(10, 16, 50))
            for i in range(8):
                a = i / 8 * 2 * math.pi
                sx, sy = PW / 2 + 140 * math.cos(a), PH * 0.15 + 90 * math.sin(a)
                d.regular_polygon((sx, sy, 22), 5, rotation=t * 30, fill=WHITE)
            x = PW * 0.1 + PW * 0.4 * _e(t / 2.2)
            person(d, x, gy, 1.5, run=0.6, phase=t * 4, **abu)
            d.line([(x + 50, gy - 160), (x + 70, gy)], fill=(120, 80, 40), width=10)
            stamp(im, "FICHAJE: LA ABUELA", PW / 2, PH * 0.38, 1.4, t, size=56)
        elif kind == "x_ab_regate":
            p = min(t / 2.0, 1)
            x = PW * 0.25 + PW * 0.5 * p
            fall = _e((t - 1.0) / 0.4)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            person(ImageDraw.Draw(lay), PW * 0.55, gy, 1.2, BLAU, SKINS[2], "corto", (20, 10, 5), "5", mouth="abierta")
            lay = lay.rotate(-80 * fall, center=(PW * 0.55, gy), resample=Image.BICUBIC)
            im.paste(lay, (0, 0), lay)
            d = ImageDraw.Draw(im)
            person(d, x, gy, 1.4, run=0.8, phase=t * 6, **abu)
            d.line([(x + 50, gy - 150), (x + 90, gy - 6)], fill=(120, 80, 40), width=10)
            ball(d, x + 100, gy - 4, 14)
            if t > 1.3:
                f = font(64)
                d.text((PW * 0.08, PH * 0.32), "¡CAÑO CON BASTÓN!", font=f, fill=YEL, stroke_width=6, stroke_fill=INK)
        elif kind == "x_ab_record":
            person(d, gx - 200, gy, 1.3, (230, 230, 240), SKINS[0], "corto", (150, 150, 150), "1", pose="brazos_cruzados")
            f = font(260)
            n = int(43 * _e(t / 0.8))
            d.text((gx - 80, PH * 0.32), str(n), font=f, fill=YEL, stroke_width=10, stroke_fill=INK)
            A._label(d, PW / 2, PH * 0.27, "43 años en la Champions", 40, WHITE, center=True)
        elif kind == "x_ab_croquetas":
            d.rectangle([0, 0, PW, PH], fill=(60, 44, 34))
            d.rectangle([0, PH * 0.6, PW, PH], fill=(120, 84, 50))
            person(d, gx, gy, 1.6, pose="", arm_up=0.6, **abu)
            tx, ty = gx + 200, gy - 250 - 20 * math.sin(t * 3)
            d.rounded_rectangle([tx - 90, ty - 40, tx + 90, ty + 30], 14, fill=(200, 230, 255), outline=INK, width=4)
            for i in range(5):
                d.ellipse([tx - 70 + i * 30, ty - 25, tx - 44 + i * 30, ty + 10], fill=(200, 130, 50), outline=(120, 70, 20), width=2)
            stamp(im, "DESCANSO: CROQUETAS", PW / 2, PH * 0.3, 0.6, t, size=56)
        else:
            return None
    # ---------- El VAR es tu madre ----------
    elif kind.startswith("x_var_"):
        mama = dict(shirt=(200, 60, 110), skin=SKINS[1], hair="melena", hair_col=(60, 34, 20), shorts=(40, 40, 70), legs=(40, 40, 70))
        if kind == "x_var_jugada":
            d = stripes(im)
            fall = _e((t - 0.6) / 0.4)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            person(ImageDraw.Draw(lay), PW * 0.45, PH * 0.66, 1.3, RED, SKINS[0], "corto", (40, 20, 10), "9", mouth="abierta", phase=t * 8, run=1 - fall)
            lay = lay.rotate(70 * fall, center=(PW * 0.45, PH * 0.66), resample=Image.BICUBIC)
            im.paste(lay, (0, 0), lay)
            d = ImageDraw.Draw(im)
            person(d, PW * 0.78, PH * 0.66, 1.2, (20, 20, 24), SKINS[3], "corto", (20, 10, 5), arm_up=0.5 * _e((t - 1.2) / 0.3))
            if t > 1.4:
                bubble(d, PW * 0.72, PH * 0.32, "Revisa el VAR…", 42)
        elif kind == "x_var_monitor":
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, PW, PH], fill=(16, 18, 26))
            mx0, my0, mx1, my1 = PW * 0.08, PH * 0.3, PW * 0.92, PH * 0.66
            d.rounded_rectangle([mx0, my0, mx1, my1], 24, fill=(30, 34, 46), outline=(90, 96, 110), width=10)
            d.rectangle([mx0 + 20, my0 + 20, mx1 - 20, my1 - 20], fill=(80, 140, 200))
            person(d, PW / 2, my1 + 120, 2.4, mouth="enfado", **mama)
            d = ImageDraw.Draw(im)
            d.rectangle([mx0, my1, mx1, PH], fill=(16, 18, 26))
            d.rounded_rectangle([mx0, my0, mx1, my1], 24, outline=(90, 96, 110), width=10)
            if int(t * 2) % 2 == 0:
                d.ellipse([mx0 + 40, my0 + 40, mx0 + 70, my0 + 70], fill=(255, 50, 50))
            A._label(d, mx0 + 90, my0 + 34, "VAR · REVISANDO", 40, WHITE)
        elif kind == "x_var_veredicto":
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, PW, PH], fill=(200, 210, 230))
            person(d, PW / 2, PH * 0.72, 2.2, mouth="enfado", pose="senala", **mama)
            bubble(d, PW / 2, PH * 0.27, "¿Has recogido tu cuarto?", 46)
        elif kind == "x_var_tarjeta":
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, PW, PH], fill=(200, 210, 230))
            person(d, PW / 2 - 60, PH * 0.72, 2.2, mouth="enfado", arm_up=1.0, **mama)
            k = _e((t - 0.4) / 0.3)
            cx, cy = PW / 2 + 20, PH * 0.72 - 2.2 * 222 - 40 * k
            d.rounded_rectangle([cx - 50, cy - 75, cx + 50, cy + 75], 10, fill=(230, 30, 40), outline=WHITE, width=4)
            stamp(im, "SIN CENAR", PW / 2, PH * 0.82, 0.9, t, bg=(230, 30, 40), fg=WHITE)
        else:
            return None
    # ---------- Partido sin árbitro ----------
    elif kind.startswith("x_sa_"):
        refe = dict(shirt=(250, 210, 30), skin=SKINS[0], hair="corto", hair_col=(30, 22, 16), shorts=(20, 20, 24))
        gy = PH * 0.66
        if kind == "x_sa_salida":
            d = stripes(im)
            x = PW * 0.5 + PW * 0.75 * _e((t - 0.5) / 2.2)
            person(d, x, gy, 1.4, run=0.6 if t > 0.5 else 0.0, phase=t * 5, arm_up=0.0 if t > 0.5 else 0.8, **refe)
            d.ellipse([x + 46, gy - 260, x + 74, gy - 240], fill=(200, 200, 210), outline=INK, width=3)
            stamp(im, "SIN ÁRBITRO", PW / 2, PH * 0.32, 0.9, t, bg=RED, fg=WHITE)
        elif kind == "x_sa_caos":
            d = stripes(im)
            txt = ["¡Era falta!", "¡Que no!", "¡Penalti!", "¡Fuera!"]
            for i in range(4):
                x = PW * (0.14 + 0.19 * i)
                sh = 10 * math.sin(t * 30 + i * 2)
                col = RED if i % 2 == 0 else BLAU
                person(d, x + sh, gy + (i % 2) * 60, 1.2, col, SKINS[i], "corto", (30, 20, 10), str(4 + i * 2), mouth="enfado", pose="senala")
                if t > 0.3 + i * 0.35:
                    bubble(d, x, PH * (0.30 + 0.07 * (i % 2)), txt[i], 36)
        elif kind == "x_sa_piscina":
            d = stripes(im)
            fall = _e((t - 0.6) / 0.5)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            person(ImageDraw.Draw(lay), PW * 0.3, gy, 1.4, RED, SKINS[1], "tupe", (30, 20, 10), "11", mouth="abierta", arm_up=fall)
            lay = lay.rotate(-90 * fall, center=(PW * 0.3, gy), resample=Image.BICUBIC)
            im.paste(lay, (0, 0), lay)
            d = ImageDraw.Draw(im)
            for i in range(6):
                q = ((t - 1.0) * 1.2 + i / 6) % 1 if t > 1.0 else 0
                if t > 1.0:
                    dx, dy = PW * 0.4 + 200 * math.cos(i) * q, gy - 40 - 160 * q
                    d.ellipse([dx - 10, dy - 14, dx + 10, dy + 14], fill=(120, 200, 255))
            stamp(im, "NADIE PITA", PW / 2, PH * 0.32, 1.4, t)
        elif kind == "x_sa_1891":
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, PW, PH], fill=(14, 18, 34))
            n = int(1800 + 91 * _e(t / 1.0))
            f = font(220)
            w = d.textlength(str(n), font=f)
            d.text((PW / 2 - w / 2, PH * 0.30), str(n), font=f, fill=YEL, stroke_width=10, stroke_fill=INK)
            person(d, PW / 2, PH * 0.80, 1.3, arm_up=1.0 if t > 1.2 else 0.0, **refe)
            A._label(d, PW / 2, PH * 0.27, "El árbitro entra al campo", 40, WHITE, center=True)
        elif kind == "x_sa_pachanga":
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, PW, PH], fill=(150, 150, 160))
            d.rectangle([0, PH * 0.55, PW, PH], fill=(120, 110, 100))
            person(d, PW * 0.3, gy, 1.2, (60, 160, 90), SKINS[2], "corto", (20, 10, 5), "", mouth="enfado")
            person(d, PW * 0.68, gy - 20 * abs(math.sin(t * 4)), 1.4, (240, 140, 30), SKINS[0], "corto", (90, 50, 20), "", mouth="sonrisa", arm_up=1.0)
            ball(d, PW * 0.68 + 60, gy - 330 - 20 * abs(math.sin(t * 4)), 34)
            if t > 0.5:
                bubble(d, PW * 0.62, PH * 0.29, "Mi balón, mis reglas", 42)
        else:
            return None
    # ---------- Drenaje del césped ----------
    elif kind.startswith("x_dr_"):
        d = ImageDraw.Draw(im)
        top = PH * 0.34
        layers = [("CÉSPED", (40, 140, 60), 50), ("ARENA", (222, 196, 130), 230), ("GRAVA", (140, 140, 150), 180)]
        def section(d, cut=True):
            d.rectangle([0, 0, PW, top], fill=(70, 90, 120))
            y = top
            for name, col, h in layers:
                d.rectangle([0, y, PW, y + h], fill=col)
                if name == "GRAVA":
                    rnd = random.Random(2)
                    for _ in range(120):
                        gx, gy2, r = rnd.uniform(0, PW), rnd.uniform(y, y + h), rnd.uniform(5, 12)
                        d.ellipse([gx - r, gy2 - r, gx + r, gy2 + r], fill=(110, 110, 120), outline=(90, 90, 100))
                elif name == "ARENA":
                    rnd = random.Random(1)
                    for _ in range(400):
                        gx, gy2 = rnd.uniform(0, PW), rnd.uniform(y, y + h)
                        d.point((gx, gy2), fill=(190, 160, 100))
                else:
                    for gx in range(0, int(PW), 14):
                        d.polygon([(gx, y), (gx + 7, y - 22), (gx + 14, y)], fill=(50, 170, 70))
                y += h
            d.rectangle([0, y, PW, PH], fill=(90, 60, 40))
            return y
        if kind == "x_dr_lluvia":
            bot = section(d)
            rnd = random.Random(5)
            for _ in range(140):
                x0, ph = rnd.uniform(0, PW), rnd.random()
                yy = (t * 900 + ph * top) % top
                d.line([(x0, yy), (x0 - 6, yy + 24)], fill=(170, 200, 255), width=3)
            stamp(im, "DILUVIO", PW / 2, PH * 0.30, 0.3, t, bg=(40, 90, 200), fg=WHITE)
        elif kind in ("x_dr_capas", "x_dr_tubos"):
            bot = section(d)
            y = top
            for name, col, h in layers:
                A._label(d, PW * 0.05, y + h / 2 - 20, name, 36, WHITE)
                y += h
            # tubos perforados en la grava
            ty = top + 50 + 230 + 100
            for tx in (PW * 0.3, PW * 0.7):
                d.ellipse([tx - 34, ty - 34, tx + 34, ty + 34], fill=(60, 60, 70), outline=WHITE, width=4)
                d.ellipse([tx - 20, ty - 20, tx + 20, ty + 20], fill=(30, 30, 40))
            rnd = random.Random(7)
            for i in range(50):
                x0, ph = rnd.uniform(PW * 0.15, PW * 0.85), rnd.random()
                q = (t * 0.5 + ph) % 1
                yy = top - 10 + (ty - top + 10) * q
                xx = x0 + ((PW * 0.3 if x0 < PW / 2 else PW * 0.7) - x0) * max(0, (q - 0.6) / 0.4)
                d.ellipse([xx - 7, yy - 9, xx + 7, yy + 9], fill=(70, 150, 255), outline=(30, 80, 200))
            if kind == "x_dr_tubos":
                k = (t * 300) % 200
                for tx in (PW * 0.3, PW * 0.7):
                    d.line([(tx, ty), (tx + (PW - tx) * 0.9, ty)], fill=(70, 150, 255), width=10)
                    for j in range(4):
                        ax = tx + 60 + (k + j * 200) % (PW - tx)
                        d.polygon([(ax, ty - 14), (ax + 22, ty), (ax, ty + 14)], fill=WHITE)
                A._label(d, PW / 2, PH * 0.285, "Tubos con agujeros", 42, WHITE, center=True)
            else:
                A._label(d, PW / 2, PH * 0.285, "El agua baja capa a capa", 42, WHITE, center=True)
        elif kind == "x_dr_maceta":
            d.rectangle([0, 0, PW, PH], fill=(30, 40, 60))
            cx, cy = PW / 2, PH * 0.50
            d.polygon([(cx - 200, cy - 150), (cx + 200, cy - 150), (cx + 150, cy + 170), (cx - 150, cy + 170)], fill=(200, 100, 60), outline=INK)
            d.rectangle([cx - 210, cy - 180, cx + 210, cy - 150], fill=(220, 120, 70), outline=INK)
            d.rectangle([cx - 190, cy - 150, cx + 190, cy - 110], fill=(60, 160, 70))
            for i in range(-2, 3):
                hx = cx + i * 50
                d.ellipse([hx - 10, cy + 160, hx + 10, cy + 176], fill=INK)
                q = (t * 1.2 + (i + 2) * 0.2) % 1
                d.ellipse([hx - 9, cy + 180 + q * 160, hx + 9, cy + 200 + q * 160], fill=(70, 150, 255))
            A._label(d, cx, PH * 0.29, "Como una maceta gigante", 42, YEL, center=True)
        else:
            return None
    # ---------- Portería gigante ----------
    elif kind.startswith("x_pg_"):
        d = stripes(im)
        gy = PH * 0.62
        k = {"x_pg_crece": 1 + _e((t - 0.6) / 1.2), "x_pg_portero": 2.0, "x_pg_goles": 2.0}[kind]
        gw, gh = 200 * k, 133 * k
        for xx in range(int(PW / 2 - gw), int(PW / 2 + gw) + 1, 26):
            d.line([(xx, gy - gh), (xx, gy)], fill=(220, 220, 220), width=2)
        for yy in range(int(gy - gh), int(gy) + 1, 26):
            d.line([(PW / 2 - gw, yy), (PW / 2 + gw, yy)], fill=(220, 220, 220), width=2)
        d.line([(PW / 2 - gw, gy), (PW / 2 - gw, gy - gh), (PW / 2 + gw, gy - gh), (PW / 2 + gw, gy)], fill=WHITE, width=12)
        d.line([(0, gy), (PW, gy)], fill=WHITE, width=4)
        if kind == "x_pg_crece":
            A._label(d, PW / 2, PH * 0.29, "7,32 m  →  14,64 m", 46, YEL, center=True)
            person(d, PW / 2, gy + 4, 0.85, (240, 200, 40), SKINS[0], "corto", (30, 20, 10), "1", mouth="abierta")
        elif kind == "x_pg_portero":
            x = PW / 2 + (gw - 40) * math.sin(t * 4)
            person(d, x, gy + 4, 0.85, (240, 200, 40), SKINS[0], "corto", (30, 20, 10), "1", mouth="abierta", run=1.0, phase=t * 10)
            for i in range(4):
                q = (t * 1.5 + i * 0.25) % 1
                sx, sy = x + 40, gy - 150 - q * 60
                d.ellipse([sx - 5, sy - 8, sx + 5, sy + 8], fill=(120, 200, 255))
            stamp(im, "IMPOSIBLE CUBRIRLA", PW / 2, PH * 0.30, 0.5, t, size=52)
        else:
            person(d, PW / 2 - gw + 60, gy + 4, 0.85, (240, 200, 40), SKINS[0], "corto", (30, 20, 10), "1", mouth="abierta")
            for i in range(5):
                q = min(max((t - i * 0.4) / 0.5, 0), 1)
                bx = PW * 0.5 + (gw - 60 - i * 40) * q
                by = PH * 0.9 - (PH * 0.9 - gy + 60 + i * 20) * q
                ball(d, bx, by, 14)
            n = min(7, int(t * 2.5))
            A._label(d, PW / 2, PH * 0.29, f"9 - {n}", 70, WHITE, center=True)
        return im
    else:
        return None
    return im
