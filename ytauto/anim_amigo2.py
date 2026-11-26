"""Serie «Todos tenemos un amigo que…», ep. 2: el que nunca pasa el balón (el chupón).
Misma pista de barrio que el ep. 1 (anim_amigo.barrio). Escenas x_ch_*. Cámara con glide() y personajes vivos."""
from __future__ import annotations

import math

from PIL import Image

from . import anim as A
from .anim_amigo import AMIGOS, barrio, mochila
from .anim_bean import C, INK, BLANCO, WHITE, bean, bean_head, ball2, sign, dutch, vignette, _e, dust, burst, speed_lines
from .anim_reglamento import alive, shot, trail

CHUPON = dict(body=(240, 120, 30), skin=BLANCO, hair="tupe", hcol=(60, 36, 20), num="10")
VECINA = dict(body=(150, 80, 170), skin=BLANCO, hair="melena", hcol=(176, 176, 182))


def _regate(t, x0, y0, w):
    """Posición del chupón y del balón pegado al pie mientras zigzaguea."""
    x = x0 + w * math.sin(t * 2.2)
    return x, y0, x + 70 * math.cos(t * 2.2) + 20, y0 - 18


def _balcon(c, x, y, s, t, con_balon=False, enfado=False):
    """Balcón de un quinto con la vecina detrás de la barandilla."""
    c.r(x - 120 * s, y - 230 * s, x + 120 * s, y, 4 * s, (176, 130, 110), INK, 3 * s)
    c.r(x - 80 * s, y - 210 * s, x + 80 * s, y - 40 * s, 4 * s, (90, 110, 140), INK, 3 * s)
    bean(c, x, y + 60 * s, 0.42 * s, emo="enfado" if enfado else "serio", t=t, look=0.4 * math.sin(t),
         arms="jarras" if enfado else "relax", **VECINA)
    if con_balon:
        hx, hy = bean_head(x, y + 60 * s, 0.42 * s)
        ball2(c, hx - 50 * s, hy + 60 * s, 22 * s, 0)
    c.r(x - 130 * s, y - 8 * s, x + 130 * s, y + 8 * s, 2 * s, (70, 74, 86), INK, 3 * s)
    for k in range(9):
        xx = x - 120 * s + k * 30 * s
        c.l([(xx, y - 80 * s), (xx, y)], (70, 74, 86), 4 * s)
    c.l([(x - 130 * s, y - 80 * s), (x + 130 * s, y - 80 * s)], (70, 74, 86), 6 * s)


def render(kind, t, dur):
    W, H = A.PW, A.PH
    cx = W / 2
    b = C((W, H))
    f = C((W, H), "RGBA", (0, 0, 0, 0))
    signs, tilt, img = [], 0, None

    if kind == "x_ch_intro":
        # el chupón regatea en círculos; los demás piden el balón con los brazos arriba
        barrio(b, W, H, t)
        x, y, bx, by = _regate(t, cx, H * 0.97, 140)
        for j, (xx, ss) in enumerate(((0.12, 0.85), (0.88, 0.85), (0.30, 0.72))):
            alive(f, W * xx, H * (0.90 if ss > 0.8 else 0.82), ss, t, ph=j * 1.3, emo="enfado" if t > 1.0 else "serio",
                  arms="arriba", talk=t > 1.0, **AMIGOS[j])
        bean(f, x, y, 1.1, emo="picaro", t=t, look=math.cos(t * 2.2), arms="abiertos", legs="anda", phase=t * 10, **CHUPON)
        ball2(f, bx, by, 42, t * 6)
        img = shot(b, f, [(0, cx, H * 0.66, 1.0), (dur, cx, H * 0.70, 1.12)], t, dur, W, H)
        signs.append(("EL CHUPÓN", 0.22, 0.25))

    elif kind == "x_ch_solo":
        # tú solo delante de la portería de mochilas gritando; él regatea a tres
        barrio(b, W, H, t)
        mochila(b, W * 0.10, H * 0.74, 0.7)
        mochila(b, W * 0.34, H * 0.74, 0.7, (200, 70, 60))
        alive(f, W * 0.24, H * 0.83, 0.75, t, ph=0.4, emo="sorpresa", arms="arriba", talk=True, **AMIGOS[0])
        x, y, bx, by = _regate(t * 1.3, W * 0.68, H * 1.0, 110)
        for j, xx in enumerate((0.48, 0.70, 0.90)):
            alive(f, W * xx, H * 0.92 - j * 10, 0.85, t, ph=j * 0.8, emo="sorpresa", arms="abiertos",
                  legs="abiertas", **AMIGOS[j + 1])
        bean(f, x, y, 1.05, emo="picaro", t=t, look=math.cos(t * 2.9), arms="abiertos", legs="anda", phase=t * 12,
             **CHUPON)
        ball2(f, bx, by, 40, t * 7)
        img = shot(b, f, [(0, W * 0.30, H * 0.70, 1.2), (dur * 0.45, W * 0.30, H * 0.70, 1.2),
                          (dur * 0.7, W * 0.62, H * 0.72, 1.05), (dur, W * 0.62, H * 0.72, 1.05)], t, dur, W, H)
        signs.append(("¡ESTOY SOLO!", 0.22, 0.2))

    elif kind == "x_ch_pierde":
        # se la roban a la primera; se tira al suelo pidiendo falta
        barrio(b, W, H, t)
        T = dur * 0.35
        u = _e(min(1.0, max(0.0, (t - T) / 0.5)))
        bean(f, W * 0.34, H * 0.98, 1.05, emo="dolor" if t > T else "picaro", t=t, arms="abiertos",
             legs="abiertas" if t > T else "anda", phase=t * 10, **CHUPON)
        thief_x = W * 0.72 + W * 0.22 * u
        alive(f, thief_x, H * 0.95, 0.95, t, ph=1.1, emo="feliz" if t > T else "serio", arms="relax",
              legs="anda" if 0 < u < 1 else "pie", phase=t * 10, **AMIGOS[2])
        ball2(f, W * 0.50 + (thief_x + 60 - W * 0.50) * u, H * 0.97, 40, t * 6)
        dust(f, W * 0.40, H * 0.98, t, T, s=0.8)
        img = shot(b, f, [(0, W * 0.45, H * 0.70, 1.15), (dur, W * 0.55, H * 0.70, 1.05)], t, dur, W, H,
                   shake=5 if 0 < t - T < 0.2 else 0)
        signs.append(("LA PIERDE", 0.22, T))
        tilt = -3

    elif kind == "x_ch_mia":
        # cuando el balón lo tienes tú: «¡MÍA, MÍA, MÍA!»
        barrio(b, W, H, t)
        alive(f, W * 0.78, H * 1.02, 1.0, t, ph=0.7, emo="aburrido", arms="relax", **AMIGOS[1])
        ball2(f, W * 0.66, H * 0.98, 40, 0)
        jump = abs(math.sin(t * 7)) * 40
        bean(f, W * 0.32, H * 0.98 - jump, 1.2, emo="enfado", t=t, look=1, arms="arriba", talk=True, **CHUPON)
        for k in range(3):
            if t > 0.3 + k * 0.45:
                burst(f, "¡MÍA!", W * (0.34 + 0.18 * k), H * (0.50 + 0.05 * (k % 2)), t, 0.3 + k * 0.45, 70)
        img = shot(b, f, [(0, cx, H * 0.66, 1.0), (dur, W * 0.40, H * 0.64, 1.15)], t, dur, W, H)
        tilt = 3

    elif kind == "x_ch_quinto":
        # por fin le pasas... y la manda al balcón del quinto
        barrio(b, W, H, t)
        T = dur * 0.3
        k = min(1.0, max(0.0, (t - T) / (dur * 0.5)))
        bean(f, W * 0.36, H * 0.99, 1.05, emo="feliz" if t < T else "sorpresa", t=t, look=1, arms="abiertos" if t > T else "relax",
             kick=(t - T + 0.25) / 0.5 if T - 0.25 < t < T + 0.25 else None, **CHUPON)
        alive(f, W * 0.82, H * 0.95, 0.85, t, ph=0.3, emo="sorpresa" if t > T else "serio", arms="abiertos" if t > T else "relax",
              look=-1, **AMIGOS[0])
        _balcon(b, W * 0.74, H * 0.22, 1.0, t)
        if t < T:
            ball2(f, W * 0.36 + 300 * (1 - t / T), H * 0.96, 40, t * 5)
        elif k < 1:
            trail(f, (W * 0.42, H * 0.95), (W * 0.74, H * 0.18), 380, k, 40 - 22 * k, curve=-40)
        img = shot(b, f, [(0, W * 0.45, H * 0.72, 1.1), (T + 0.2, W * 0.50, H * 0.66, 1.0),
                          (dur, W * 0.66, H * 0.36, 1.35)], t, dur, W, H)
        signs.append(("AL QUINTO", 0.22, T + 0.6))

    elif kind == "x_ch_vecina":
        # la vecina no devuelve balones
        barrio(b, W, H, t)
        _balcon(f, cx, H * 0.40, 2.0, t, con_balon=True, enfado=t > 0.6)
        img = shot(b, f, [(0, cx, H * 0.36, 1.0), (dur, cx, H * 0.36, 1.12)], t, dur, W, H)
        signs.append(("NO DEVUELVE", 0.72, 0.4))

    elif kind == "x_ch_cierre":
        # al día siguiente: «soy como Messi»; los demás, con la mano en la cara
        barrio(b, W, H, t)
        bean(f, W * 0.30, H * 0.99, 1.15, emo="picaro", t=t, look=1, arms="jarras", **CHUPON)
        for j, xx in enumerate((0.64, 0.84)):
            alive(f, W * xx, H * 0.93, 0.9, t, ph=j * 0.9, emo="aburrido", arms="relax", arm_r="cara", look=-1,
                  **AMIGOS[j + 1])
        img = shot(b, f, [(0, cx, H * 0.64, 1.0), (dur, W * 0.40, H * 0.62, 1.12)], t, dur, W, H)
        signs.append(("«SOY MESSI»", 0.22, 0.3))
    else:
        return Image.new("RGB", (int(W), int(H)))

    img = dutch(img, tilt)
    img = vignette(img, 0.28)
    for txt, yy, t0 in signs:
        sign(img, txt, cx, H * yy, t0, t)
    return img
