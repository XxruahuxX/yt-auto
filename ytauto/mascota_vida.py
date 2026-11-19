"""Vida de la mascota: capa de movimiento natural encima de las posturas de mascota.py.

Qué añade frente a los senos fijos de shorts._draw_mascot:
  - Ojos que parpadean a intervalos irregulares (a veces doble) y miran a sitios.
  - Respiración: pecho que se estira y hombros que suben un poco.
  - Cambio de peso: la cadera se mueve con los pies clavados en el suelo (IK de 2 huesos).
  - Ruido suave en vez de senos: nunca se repite el mismo ciclo.
  - Muelles por hueso: los antebrazos y la cabeza llegan tarde y rebotan (follow-through).
  - Gestos nuevos: asiente, niega, encoge hombros, se rasca, sorpresa, se ríe, aplaude,
    impaciente y salto con anticipación y aplastamiento.

Los Shorts la usan a través de frame() (aprobada el 19-nov).
Posturas para el campo "pose" de las escenas: las de mascota.POSES más asiente, niega,
encoge, rasca, sorpresa, rie, aplaude e impaciente.

    python -m ytauto.mascota_vida   -> vídeo demo en oficina/propuestas
"""
from __future__ import annotations

import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import mascota as m

OUT = Path("/mnt/project-files/yt-auto/oficina/propuestas/2026-11-19_mascota_natural.mp4")
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_R = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

# posturas nuevas (mismos convenios que mascota.POSES)
EXTRA = {
    "encoge": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=118, lfa=175, rua=62, rfa=5, lift=0, tilt=12, sh_up=14),
    "rasca": dict(spine=-88, lth=100, lsh=96, rth=80, rsh=84, lua=112, lfa=98, rua=-55, rfa=-95, lift=0, tilt=14),
    "sorpresa": dict(spine=-102, lth=104, lsh=94, rth=76, rsh=86, lua=-150, lfa=-100, rua=-40, rfa=-85, lift=0, tilt=-10, sh_up=10),
    "rie": dict(spine=-84, lth=100, lsh=96, rth=80, rsh=84, lua=100, lfa=40, rua=80, rfa=150, lift=0, tilt=-8),
    "aplaude": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=28, lfa=-30, rua=28, rfa=-30, lift=0, tilt=4),
    "niega": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=112, lfa=98, rua=30, rfa=-75, lift=0),
    # saludo con la mano por fuera de la cara (el de mascota.py la tapaba al rebotar)
    "saluda": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=112, lfa=98, rua=5, rfa=-68, lift=0, tilt=4),
    "impaciente": dict(spine=-90, lth=100, lsh=96, rth=80, rsh=84, lua=130, lfa=40, rua=50, rfa=130, lift=0, tilt=-6),
}
POSES = {**m.POSES, **EXTRA}

# rigidez (rad/s) y amortiguación de cada hueso: los finales de cadena son más blandos
SPRING = {
    "spine": (16, 0.8), "tilt": (9, 0.45), "lift": (40, 0.9), "stretch": (22, 0.5), "sh_up": (18, 0.6),
    "lua": (14, 0.55), "rua": (14, 0.55), "lfa": (10, 0.42), "rfa": (10, 0.42),
    "lth": (24, 0.85), "rth": (24, 0.85), "lsh": (24, 0.85), "rsh": (24, 0.85),
}


def noise(t: float, seed: int = 0) -> float:
    """Ruido 1D suave en -1..1 (valor interpolado con smoothstep)."""
    i = math.floor(t)
    f = t - i

    def h(n):
        x = math.sin((n + seed * 101.3) * 127.1) * 43758.5453
        return (x - math.floor(x)) * 2 - 1

    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def plant(pose: dict, hdx: float, hdy: float) -> dict:
    """Mueve la cadera (hdx, hdy) dejando los pies donde estaban: recalcula muslo y espinilla."""
    j = m.solve(pose, 0)
    out = dict(pose)
    for s in "lr":
        hs = (j[s + "hs"][0] + hdx, j[s + "hs"][1] + hdy)
        fx, fy = j[s + "f"]
        vx, vy = fx - hs[0], fy - hs[1]
        a, b = m.L["thigh"], m.L["shin"]
        dist = min(math.hypot(vx, vy), (a + b) * 0.999)
        base = math.degrees(math.atan2(vy, vx))
        ang = math.degrees(math.acos((a * a + dist * dist - b * b) / (2 * a * dist)))
        th = base - ang  # rodilla hacia delante (a la derecha)
        kx = hs[0] + a * math.cos(math.radians(th))
        ky = hs[1] + a * math.sin(math.radians(th))
        out[s + "th"] = th
        out[s + "sh"] = math.degrees(math.atan2(fy - ky, fx - kx))
    return out


class Vida:
    """Animador con estado: llámalo una vez por fotograma con la postura objetivo."""

    def __init__(self, seed: int = 7, pose: str = "quieto"):
        self.rng = random.Random(seed)
        self.seed = seed
        self.x = dict(POSES[pose])
        self.v = {k: 0.0 for k in self.x}
        self.next_blink = 0.8
        self.blink_t = -9.0
        self.double = False
        self.look = [0.0, 0.0]
        self.look_to = (0.0, 0.0)
        self.next_look = 1.2
        self.t = 0.0

    # --- capas ------------------------------------------------------------
    def idle(self, p: dict, t: float, level: float, weight: float = 1.0) -> dict:
        """Respiración, cambio de peso y microgestos (weight 0 = sin cambio de peso)."""
        p = dict(p)
        br = math.sin(2 * math.pi * t / 3.4)  # una respiración cada ~3,4 s
        p["stretch"] = p.get("stretch", 0) + 0.014 * br
        p["sh_up"] = p.get("sh_up", 0) + 3.5 * br
        p["lua"] += 2.5 * br
        p["rua"] -= 2.5 * br
        p["tilt"] = p.get("tilt", 0) + 3 * noise(t * 0.45, self.seed) + 6 * level * math.sin(t * 8.5)
        p["lua"] += 3 * noise(t * 0.6, self.seed + 1)
        p["rua"] += 3 * noise(t * 0.55, self.seed + 2)
        p["spine"] += 1.5 * noise(t * 0.3, self.seed + 3)
        if weight:
            hx = 14 * noise(t * 0.22, self.seed + 4) * weight
            hy = (3 + 3 * abs(noise(t * 0.22, self.seed + 4))) * weight
            p = plant(p, hx, hy)
            p["spine"] -= 0.12 * hx  # el tronco compensa el peso
        return p

    def face(self, t: float, extra: dict | None = None) -> dict:
        extra = extra or {}
        # parpadeo: cada 2-5 s, 140 ms, a veces doble
        if t >= self.next_blink:
            self.blink_t = t
            self.double = self.rng.random() < 0.2
            self.next_blink = t + self.rng.uniform(2.0, 5.0) + (0.3 if self.double else 0)
        a = t - self.blink_t
        blink = 0.0
        for start in ((0.0, 0.22) if self.double else (0.0,)):
            u = (a - start) / 0.14
            if 0 <= u <= 1:
                blink = max(blink, 1 - abs(2 * u - 1))
        blink = min(1.0, blink * 1.6)
        # mirada: miradas rápidas (sacádicas) a puntos al azar
        if "look" in extra:
            self.look_to = extra["look"]
        elif t >= self.next_look:
            self.look_to = (self.rng.choice([-0.6, 0.0, 0.5, 0.9]), self.rng.choice([-0.5, 0.0, 0.0, 0.4]))
            self.next_look = t + self.rng.uniform(1.2, 3.5)
        for i in (0, 1):
            self.look[i] += (self.look_to[i] - self.look[i]) * 0.45
        f = {"blink": max(blink, extra.get("blink", 0.0)), "look": tuple(self.look)}
        f.update({k: v for k, v in extra.items() if k not in ("look", "blink")})
        return f

    def step(self, target: dict, dt: float) -> dict:
        """Muelles amortiguados por hueso hacia la postura objetivo."""
        for k, tv in target.items():
            if k not in self.x:
                self.x[k], self.v[k] = tv, 0.0
            w, z = SPRING.get(k, (18, 0.7))
            for _ in range(4):
                h = dt / 4
                d = tv - self.x[k]
                if k not in m.LINEAR:
                    d = (d + 180) % 360 - 180
                self.v[k] += (w * w * d - 2 * z * w * self.v[k]) * h
                self.x[k] += self.v[k] * h
        return dict(self.x)


# --- gestos: (postura, función que añade movimiento, cara, cambio de peso) ---------------
def g_habla(p, u, f):
    lv = _voz(u)
    p["rfa"] += 26 * lv * math.sin(u * 5)
    p["rua"] += 10 * lv * math.sin(u * 5 + 0.6)
    return lv


def g_asiente(p, u, f):
    p["tilt"] += 9 * math.sin(u * 2 * math.pi * 2.2) * (1 if u < 1.6 else 0)
    f.update(happy=1 if 0.4 < u < 1.8 else 0)
    return 0


def g_niega(p, u, f):
    s = math.sin(u * 2 * math.pi * 2.6)
    p["rfa"] += 16 * s
    p["tilt"] += 3 * s
    f.update(look=(0.9 * s, 0.0), shape="flat")
    return 0


def g_encoge(p, u, f):
    f.update(look=(0.2, -0.7), shape="flat")
    return 0


def g_rasca(p, u, f):
    p["rfa"] += 9 * math.sin(u * 2 * math.pi * 4.5)
    f.update(look=(-0.4, -0.8), blink=0.3)
    return 0


def g_sorpresa(p, u, f):
    p["lift"] = p.get("lift", 0) + (45 * math.sin(math.pi * u / 0.35) if u < 0.35 else 0)
    f.update(eyes=1.45, shape="o", look=(0.8, 0))
    return 0.6


def g_rie(p, u, f):
    b = abs(math.sin(u * 2 * math.pi * 3))
    p["sh_up"] = p.get("sh_up", 0) + 6 * b
    p["tilt"] += -4 * b
    p["spine"] += 3 * b
    f.update(happy=1, shape="grin")
    return b


def g_aplaude(p, u, f):
    s = abs(math.sin(u * math.pi * 2.6))  # 2,6 palmadas por segundo, cierre seco
    p["lfa"] += 60 * s
    p["lua"] += 22 * s
    p["rfa"] -= 30 * s
    f.update(happy=1, shape="grin")
    return 0.3


def g_impaciente(p, u, f):
    tap = max(0.0, math.sin(u * 2 * math.pi * 2.4))
    p["rth"] -= 10 * tap
    p["rsh"] -= 4 * tap
    f.update(look=(-0.3, -0.8), blink=0.45, shape="flat")
    return 0


def g_salto(p, u, f):
    """Anticipación (se agacha), salto estirado, aterriza aplastado y rebota."""
    if u < 0.3:  # se carga
        k = math.sin(math.pi / 2 * u / 0.3)
        q = m.blend(POSES["quieto"], POSES["agacha"], k)
        q["stretch"] = -0.06 * k
    elif u < 0.8:  # en el aire
        k = (u - 0.3) / 0.5
        q = dict(POSES["celebra"])
        q["lift"] = 210 * 4 * k * (1 - k)
        q["stretch"] = 0.07 * (1 - k)
    elif u < 1.05:  # aterriza
        k = math.sin(math.pi * (u - 0.8) / 0.25)
        q = plant(POSES["celebra"], 0, 55 * k)
        q["stretch"] = -0.07 * k
    else:
        q = dict(POSES["celebra"])
    p.clear()
    p.update(q)
    f.update(happy=1 if u > 0.3 else 0, shape="grin" if u > 0.3 else "smile",
             blink=0.5 if u < 0.3 else 0)
    return 0


def g_piensa(p, u, f):
    p["rfa"] += 4 * math.sin(u * 3)
    f.update(look=(0.5, -0.9))
    return 0


def _voz(u):
    """Volumen sintético de voz: sílabas con pausas."""
    if (u % 2.2) > 1.7:
        return 0.0
    return max(0.0, 0.55 + 0.45 * math.sin(u * 15) * noise(u * 3, 9))


# (texto, postura, gesto, duración, cambio de peso)
SEGMENTOS = [
    ("Parpadeo y mirada", "quieto", None, 3.6, 1.0),
    ("Respira y cambia el peso", "quieto", None, 3.2, 1.0),
    ("Habla y gesticula", "explica", g_habla, 3.6, 0.6),
    ("Piensa", "piensa", g_piensa, 2.4, 0.5),
    ("Asiente", "quieto", g_asiente, 2.2, 0.4),
    ("Niega", "niega", g_niega, 2.2, 0.4),
    ("Encoge los hombros", "encoge", g_encoge, 2.2, 0.3),
    ("Se rasca la cabeza", "rasca", g_rasca, 2.4, 0.5),
    ("Sorpresa", "sorpresa", g_sorpresa, 2.0, 0.0),
    ("Se ríe", "rie", g_rie, 2.4, 0.0),
    ("Aplaude", "aplaude", g_aplaude, 2.2, 0.3),
    ("Impaciente", "impaciente", g_impaciente, 2.4, 0.0),
    ("Salto: carga, vuela y aterriza", "quieto", g_salto, 2.0, 0.0),
    ("Saluda", "saluda", None, 2.4, 0.5),
]


def g_saluda(p, u, f):
    p["rfa"] += 20 * math.sin(u * 7)
    p["rua"] += 5 * math.sin(u * 7 + 0.8)
    f.update(happy=1 if u > 0.4 else 0)
    return 0


def g_senala(p, u, f):
    p["rfa"] += 6 * math.sin(u * 6)
    f.update(look=(0.9, -0.3))
    return 0


# gesto que acompaña a cada postura y cuánto cambia el peso (0 = pies quietos)
GESTOS = {
    "piensa": (g_piensa, 0.5), "saluda": (g_saluda, 0.5), "senala": (g_senala, 0.5),
    "celebra": (g_salto, 0.0), "asiente": (g_asiente, 0.4), "niega": (g_niega, 0.4),
    "encoge": (g_encoge, 0.3), "rasca": (g_rasca, 0.5), "sorpresa": (g_sorpresa, 0.0),
    "rie": (g_rie, 0.0), "aplaude": (g_aplaude, 0.3), "impaciente": (g_impaciente, 0.0),
}
POSES["asiente"] = POSES["quieto"]


def frame(vida: Vida, cur: str, local: float, now: float, level: float, dt: float):
    """Un fotograma de la mascota en los Shorts: (postura, cara, boca).

    cur: postura de la escena; local: segundos desde que empezó; level: volumen de la voz (0-1).
    """
    p = {"tilt": 0, "sh_up": 0, "stretch": 0, "lift": 0, **POSES.get(cur, POSES["explica"])}
    f = {}
    gesto, weight = GESTOS.get(cur, (None, 1.0))
    extra = gesto(p, local, f) if gesto else 0.0
    if cur in ("explica", "quieto"):  # gesticula con la mano mientras habla
        p["rfa"] += 26 * level * math.sin(now * 5)
        p["rua"] += 10 * level * math.sin(now * 5 + 0.6)
    pose = vida.step(vida.idle(p, now, level, weight), dt)
    face = vida.face(now, f)
    if gesto is g_rie:
        mouth = max(extra, level)
    elif gesto is g_sorpresa and level < 0.1:
        mouth = 0.6
    else:
        mouth = min(1.0, level * 1.6)
    if level > 0.1 and face.get("shape") in ("flat", "o"):
        face["shape"] = "smile"  # al hablar manda la boca de la voz
    return pose, face, mouth


def _old_idle(t, level):
    """Lo que hacen hoy los Shorts (copia de shorts._draw_mascot en reposo)."""
    p = dict(POSES["explica"] if level else POSES["quieto"])
    p["spine"] += 2.5 * math.sin(t * 2.0)
    p["tilt"] = p.get("tilt", 0) + 4 * math.sin(t * 1.3) + 7 * level * math.sin(t * 9)
    p["lua"] += 4 * math.sin(t * 1.7)
    p["rua"] += 4 * math.sin(t * 1.9 + 1)
    p["rfa"] += 22 * level * math.sin(t * 5)
    p["rua"] += 10 * level * math.sin(t * 5 + 0.6)
    return p


def _label(img, title, sub, fonts):
    d = ImageDraw.Draw(img)
    f, fs = fonts
    W = img.width
    d.text(((W - d.textlength(title, font=f)) / 2, 70 * m.K), title, font=f, fill=m.YELLOW)
    if sub:
        d.text(((W - d.textlength(sub, font=fs)) / 2, 150 * m.K), sub, font=fs, fill=(170, 210, 185))


def _shadow(img, x, lift, scale=1.0):
    d = ImageDraw.Draw(img)
    sw = (150 - 0.5 * lift) * scale * m.K
    cx, cy = x * m.K, (m.GROUND + 8) * m.K
    d.ellipse([cx - sw, cy - 12 * m.K, cx + sw, cy + 14 * m.K], fill=(4, 32, 19))


def demo(out=OUT, fps=30, size=1080):
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{size}x{size}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(out)],
                            stdin=subprocess.PIPE)
    fonts = (ImageFont.truetype(FONT, 60 * m.K), ImageFont.truetype(FONT_R, 34 * m.K))
    big = ImageFont.truetype(FONT, 56 * m.K)
    dt = 1 / fps

    # 1) antes / ahora, en reposo y hablando
    vida = Vida(seed=3)
    n = int(7.0 * fps)
    for i in range(n):
        t = i * dt
        lv = _voz(t - 3.5) if t > 3.5 else 0.0
        img = m.canvas()
        _label(img, "Antes  vs  Ahora", "reposo y luego hablando", fonts)
        d = ImageDraw.Draw(img)
        for x, txt in ((270, "ANTES"), (730, "AHORA")):
            d.text((x * m.K - d.textlength(txt, font=fonts[1]) / 2, 930 * m.K), txt, font=fonts[1], fill=m.WHITE)
        sc = 0.85
        _shadow(img, 270, 0, sc)
        _shadow(img, 730, 0, sc)
        # en draw, x es la cadera antes de escalar: x_final = x * scale
        m.draw(img, _old_idle(t, lv), x=270 / sc, dy=m.GROUND * (1 - sc) / sc, scale=sc, mouth=min(1, lv * 1.6))
        tgt = POSES["explica"] if lv else POSES["quieto"]
        q = vida.idle(tgt, t, lv)
        if lv:
            q["rfa"] += 26 * lv * math.sin(t * 5)
        pose = vida.step(q, dt)
        m.draw(img, pose, x=730 / sc, dy=m.GROUND * (1 - sc) / sc, scale=sc, mouth=min(1, lv * 1.6),
               face=vida.face(t))
        proc.stdin.write(img.resize((size, size), Image.LANCZOS).tobytes())

    # 2) repertorio de gestos, uno detrás de otro, con transiciones por muelles
    vida = Vida(seed=11)
    t0 = 0.0
    for title, base, gesto, dur, weight in SEGMENTOS:
        for i in range(int(dur * fps)):
            u = i * dt
            t = t0 + u
            p = {"tilt": 0, "sh_up": 0, "stretch": 0, "lift": 0, **POSES[base]}
            f = {}
            lv = gesto(p, u, f) if gesto else 0.0
            if title.startswith("Saluda"):
                p["rfa"] += 28 * math.sin(u * 7)
                p["rua"] += 6 * math.sin(u * 7 + 0.8)
                f.update(happy=1 if u > 0.4 else 0)
            talk = lv if gesto in (g_habla,) else 0.0
            q = vida.idle(p, t, talk, weight)
            pose = vida.step(q, dt)
            face = vida.face(t, f)
            if gesto is g_rie:
                mouth = lv
            elif gesto is g_sorpresa:
                mouth = 0.6
            else:
                mouth = min(1.0, talk * 1.6)
            img = m.canvas()
            _shadow(img, 500, pose.get("lift", 0))
            _label(img, title, None, fonts)
            m.draw(img, pose, mouth=mouth, face=face)
            d = ImageDraw.Draw(img)
            if gesto is g_piensa and u > 0.4:
                d.text((660 * m.K, 220 * m.K), "?", font=big, fill=m.YELLOW)
            if gesto is g_sorpresa and u > 0.15:
                d.text((660 * m.K, 230 * m.K), "!", font=big, fill=m.YELLOW)
            if gesto is g_salto and 0.45 < u < 1.5:
                d.text((690 * m.K, 230 * m.K), "¡DATO!", font=big, fill=m.YELLOW)
            proc.stdin.write(img.resize((size, size), Image.LANCZOS).tobytes())
        t0 += dur
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg falló")
    return out


if __name__ == "__main__":
    print(demo())
