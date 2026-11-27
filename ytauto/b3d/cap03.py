"""«La Concentración», capítulo 3: Las habitaciones. Parodia animada con caricaturas.
Uso: python -m ytauto.b3d.cap03 SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import random
import sys

import bpy
from mathutils import Vector

from . import cap01 as C1
from .cap01 import ojos_cerrados, reparto
from .core import all_fcurves, cube, key, mat, setup_render, srgb
from .famosos import ALTURAS
from .hotel import BED_Y, HAB10_Y, MATT, bota, fiesta_anim, habitacion, pasillo, sombra
from .video_anime import hablar
from .video_penalti import FPS, F, camera, vida

LADO = {"cr7": -0.45, "messi": 0.45}
KITS = [(200, 16, 46), (120, 185, 235), (252, 214, 30), (190, 18, 32), (22, 36, 92), (246, 246, 250), (20, 20, 24)]


def en_cama(p, f, lean=0.0, brazos=None):
    p.pose(f, hips=(-1.5, -1.5), knees=(0.05, 0.05), shoulders=brazos or ((0.05, 0.2), (0.05, -0.2)),
           elbows=(-0.4, -0.4), lean=lean, pelvis_z=-0.15)


def acostar(p, clave, f=1, dy=0.0):
    """dy=0: la cabeza cae en la almohada al tumbarse (sin atravesar el cabecero)."""
    k = ALTURAS[clave] / 1.80
    p.place((LADO[clave], BED_Y + dy, MATT - 0.475 * k), 0, f)


def maleta(nombre, loc, col):
    cube(nombre, loc, (0.2, 0.1, 0.3), mat(f"maleta_{nombre}", srgb(*col), 0.4), bevel=0.03)
    cube(nombre + "_asa", (loc[0], loc[1], loc[2] + 0.33), (0.07, 0.015, 0.03), mat("asa", srgb(30, 30, 30), 0.5))


# ------------------------------------------------------------------ escenas
def s_llegan(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    habitacion(C1.OUT)
    cr.place((-0.42, -0.75, 0), math.pi, 1)
    me.place((0.42, -0.75, 0), math.pi, 1)
    maleta("maleta_cr", (-0.85, -0.85, 0.3), (230, 230, 235))
    maleta("maleta_me", (0.85, -0.85, 0.3), (40, 40, 48))
    for p in (cr, me):
        p.reposo(1)
        p.expresion(1, "feliz")
        p.mirar(1, 0, -0.2)
        p.cabeza(1, 0, 0.15, 0)
        p.expresion(F(1.2), "sorpresa")
    t2 = 2.9
    # se miran el uno al otro
    cr.cabeza(F(t2 + 0.2), 0.35, 0, 0)
    cr.mirar(F(t2 + 0.2), 0.4, 0)
    me.cabeza(F(t2 + 0.2), -0.35, 0, 0)
    me.mirar(F(t2 + 0.2), -0.4, 0)
    cr.expresion(F(t2 + 0.4), "enfadado")
    me.expresion(F(t2 + 0.5), "triste")
    cr.pose(F(t2 + 0.5), shoulders=((-0.3, 0.3), (0.05, -0.12)), elbows=(-1.6, -0.2))     # señala la cama
    vida(cr, dur, 80)
    vida(me, dur, 81)
    camera(sc, "c1", 0, t2, (0.7, 2.25, 1.95), (0.6, 2.2, 1.9), (0, -0.4, 1.0), lens=22)
    camera(sc, "c2", t2, dur, (0.05, 1.75, 1.78), (0.02, 1.65, 1.76), (0, -0.75, 1.5), lens=34)


def s_abdos(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    habitacion(C1.OUT, noche=True)
    acostar(cr, "cr7")
    acostar(me, "messi")
    nuca = ((0.3, 2.6), (0.3, -2.6))
    for i, f in enumerate(range(1, F(dur) + 1, 9)):          # abdominales sin parar
        arriba = i % 2 == 1
        cr.pose(f, hips=(-1.5, -1.5), knees=(0.05, 0.05), shoulders=nuca, elbows=(-2.2, -2.2),
                lean=0.25 if arriba else -1.3, pelvis_z=-0.15)
        cr.expresion(f, "grito" if arriba else "enfadado")
    en_cama(me, 1, lean=-1.0)
    me.expresion(1, "neutral")
    ojos_cerrados(me, 1)
    ojos_cerrados(me, F(1.4))
    me.expresion(F(1.6), "enfadado")
    me.cabeza(F(1.6), 0, 0, 0)
    me.cabeza(F(2.0), -0.6, 0.25, 0)                           # gira la cabeza hacia Cristiano
    me.mirar(F(2.0), -0.45, 0)
    me.expresion(F(3.0), "triste")
    vida(me, dur, 82, skip=((0, 1.6),))
    camera(sc, "c1", 0, dur, (0.25, -1.25, 1.85), (0.2, -1.05, 1.8), (0, BED_Y + 0.4, 0.75), lens=24)


def s_reloj(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    r1, r2 = habitacion(C1.OUT, noche=True)
    tc = 0.5
    for o, vis in ((r1, True), (r2, False)):
        o.hide_render = not vis
        o.keyframe_insert("hide_render", frame=1)
        o.hide_render = vis
        o.keyframe_insert("hide_render", frame=F(tc))
    acostar(cr, "cr7")
    acostar(me, "messi")
    t2 = 1.3
    for j, p in enumerate((cr, me)):
        en_cama(p, 1, lean=-1.3)
        p.expresion(1, "neutral")
        ojos_cerrados(p, 1)
        en_cama(p, F(t2), lean=-1.3)
        en_cama(p, F(t2 + 0.25), lean=0.15)                     # se incorporan de golpe
        p.expresion(F(t2 + 0.15), "sorpresa")
        p.cabeza(F(t2 + 0.4), 0.0, 0, 0)
        p.cabeza(F(t2 + 0.8), 0.55, 0.05, 0)                    # miran hacia la puerta (izquierda)
        p.mirar(F(t2 + 0.8), 0.45, 0)
        vida(p, dur, 83 + j, skip=((0, t2 + 0.2),))
    me.pose(F(t2 + 0.9), hips=(-1.5, -1.5), knees=(0.05, 0.05), shoulders=((-0.9, 0.0), (-0.9, -0.1)),
            elbows=(-1.4, -1.4), lean=0.1, pelvis_z=-0.15)      # Messi se tapa con las manos
    camera(sc, "c1", 0, t2, (1.17, BED_Y + 0.25, 0.72), (1.2, BED_Y + 0.35, 0.7), (1.38, BED_Y + 0.8, 0.62),
           lens=40)
    camera(sc, "c2", t2, dur, (0.1, -1.1, 1.55), (0.05, -0.95, 1.55), (0, BED_Y + 0.4, 1.0), lens=26)


def _rastro(rng, y0, y1, hacia_puerta=True):
    y = y0
    i = 0
    while y < y1:
        x = rng.uniform(-0.35, 0.35) + (0.5 * (y - (y1 - 1.5)) / 1.5 if hacia_puerta and y > y1 - 1.5 else 0)
        bota(f"bota{i}", (x, y, 0.05), KITS[i % len(KITS)], rng.uniform(-1, 1))
        y += rng.uniform(0.5, 0.9)
        i += 1


def s_pasillo(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    fiesta, luz, _ = pasillo()
    fiesta_anim(fiesta, luz, F(dur))
    _rastro(random.Random(3), 2.0, HAB10_Y + 0.3)
    # la sombra cruza el fondo y se mete en la 10
    s = sombra((0, 0, 0))
    t0, t1, t2 = 0.05, 1.6, 2.2
    pts = []
    for f in range(F(t0), F(t2) + 1, 3):
        if f <= F(t1):
            u = (f - F(t0)) / (F(t1) - F(t0))
            loc = Vector((0.0, 7.2 + u * (HAB10_Y - 7.2), 0))
            yaw = math.pi
        else:
            u = (f - F(t1)) / (F(t2) - F(t1))
            loc = Vector((u * 1.6, HAB10_Y, 0))
            yaw = math.pi / 2
        loc.z = 0.03 * abs(math.sin(f * 0.5))
        pts.append(f)
        key(s, f, location=loc, rotation_euler=(0, 0.06 * math.sin(f * 0.5), yaw))
    key(s, F(t2) + 1, location=Vector((3.0, HAB10_Y, 0)))
    # Cristiano y Messi asoman la cabeza por su puerta
    cr.place((-0.62, 0.95, 0), math.pi + 0.15, 1)
    me.place((-0.2, 1.1, 0), math.pi + 0.1, 1)
    for p in (cr, me):
        p.reposo(1)
        p.expresion(1, "sorpresa")
        p.mirar(1, 0, 0)
    tc = 2.4
    cr.expresion(F(tc + 0.3), "grito")
    me.pose(F(tc + 0.3), shoulders=((-0.9, 0.0), (-0.9, -0.1)), elbows=(-1.6, -1.6))
    hablar(cr, F(tc + 0.3), F(dur - 0.3), "sorpresa", "grito", cada=5)
    vida(cr, dur, 85)
    vida(me, dur, 86)
    camera(sc, "c1", 0, tc, (0.3, -0.9, 1.85), (0.25, -0.4, 1.8), (0, 7.5, 1.0), (0, 9.0, 1.0), lens=30)
    camera(sc, "c2", tc, dur, (0.1, 2.9, 1.72), (0.08, 2.75, 1.7), (-0.4, 1.0, 1.58), lens=26)


def s_fiesta(sc, dur):
    fiesta, luz, _ = pasillo()
    fiesta_anim(fiesta, luz, F(dur), cada=5)
    _rastro(random.Random(3), 2.0, HAB10_Y + 0.3)
    camera(sc, "c1", 0, dur, (-0.55, HAB10_Y - 2.4, 1.25), (-0.5, HAB10_Y - 1.9, 1.1), (0.7, HAB10_Y - 0.3, 0.75),
           (0.8, HAB10_Y - 0.2, 0.9), lens=26)


def cruzados(p, f):
    p.pose(f, hips=(-1.5, -1.5), knees=(0.05, 0.05), shoulders=((-0.75, -0.25), (-0.75, 0.25)), elbows=(-1.9, -1.9),
           lean=0.05, pelvis_z=-0.15)


def s_frontera(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    habitacion(C1.OUT)
    blanco = mat("sabana", srgb(246, 246, 242), 0.8, sheen=0.3)
    from .core import sphere
    for i in range(4):                                         # la frontera de almohadas
        sphere(f"frontera{i}", (0, BED_Y - 0.35 + i * 0.32, MATT + 0.4), (0.12, 0.24, 0.22), blanco)
    acostar(cr, "cr7", dy=0.38)
    acostar(me, "messi", dy=0.38)
    for j, (p, sg) in enumerate(((cr, 1), (me, -1))):
        cruzados(p, 1)
        p.expresion(1, "enfadado")
        p.cabeza(1, 0, 0.05, 0)
        p.cabeza(F(1.0), -0.5 * sg, 0, 0)                      # se miran de reojo
        p.mirar(F(1.0), -0.45 * sg, 0)
        p.cabeza(F(2.2), 0, 0.05, 0)
        p.mirar(F(2.2), 0, 0)
        p.expresion(F(2.4), "picaro" if p is cr else "enfadado")
        vida(p, dur, 90 + j)
    camera(sc, "c1", 0, dur, (0.0, -1.35, 1.6), (0.0, -1.1, 1.55), (0, BED_Y + 0.35, 1.05), lens=26)


def s_mil(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    habitacion(C1.OUT, noche=True)
    acostar(cr, "cr7")
    acostar(me, "messi")
    nuca = ((0.3, 2.6), (0.3, -2.6))
    tl = 1.3                                                   # sale la almohada
    th = tl + 0.35                                             # le da en la cara
    for i, f in enumerate(range(1, F(0.9), 8)):
        arriba = i % 2 == 1
        cr.pose(f, hips=(-1.5, -1.5), knees=(0.05, 0.05), shoulders=nuca, elbows=(-2.2, -2.2),
                lean=0.25 if arriba else -1.2, pelvis_z=-0.15)
        cr.expresion(f, "grito" if arriba else "enfadado")
    en_cama(cr, F(1.0), lean=0.2, brazos=((-2.6, 0.5), (-2.6, -0.5)))   # ¡mil! brazos arriba
    cr.expresion(F(1.0), "feliz")
    en_cama(cr, F(th), lean=0.2, brazos=((-2.6, 0.5), (-2.6, -0.5)))
    en_cama(cr, F(th + 0.25), lean=-1.3)
    cr.expresion(F(th + 0.05), "sorpresa")
    ojos_cerrados(cr, F(th + 0.3))
    en_cama(me, 1, lean=-0.9)
    me.expresion(1, "enfadado")
    me.cabeza(1, -0.4, 0.2, 0)
    en_cama(me, F(0.8), lean=0.1, brazos=((-2.7, 0.6), (0.05, -0.2)))          # coge impulso
    en_cama(me, F(tl), lean=0.25, brazos=((-1.0, -0.4), (0.05, -0.2)))          # lanza
    me.expresion(F(tl), "grito")
    me.expresion(F(tl + 0.6), "picaro")
    en_cama(me, F(tl + 0.9), lean=-0.9)
    me.cabeza(F(tl + 1.0), 0, 0.15, 0)
    alm = sphere_alm = None
    from .core import sphere
    alm = sphere("almohada_vuela", (0.45, BED_Y + 0.88, MATT + 0.06), (0.3, 0.15, 0.08),
                 mat("sabana", srgb(246, 246, 242), 0.8, sheen=0.3))
    bpy.data.objects.remove(bpy.data.objects["almohada1"])
    key(alm, 1, location=Vector((0.45, BED_Y + 0.88, MATT + 0.06)), rotation_euler=(0, 0, 0))
    key(alm, F(0.8), location=Vector((0.45, BED_Y + 0.88, MATT + 0.06)), rotation_euler=(0, 0, 0))
    key(alm, F(tl), location=Vector((0.4, BED_Y + 0.3, 1.75)), rotation_euler=(math.radians(80), 0, 0))
    key(alm, F(th), location=Vector((-0.42, BED_Y + 0.12, 1.62)), rotation_euler=(math.radians(90), 0.4, 0.3))
    key(alm, F(th + 0.25), location=Vector((-0.45, BED_Y + 0.75, 0.82)), rotation_euler=(0.2, 0.3, 0.3))
    vida(me, dur, 93)
    camera(sc, "c1", 0, dur, (0.15, -1.15, 1.6), (0.12, -0.95, 1.58), (0, BED_Y + 0.35, 1.05), lens=26)


def s_siguen(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    fiesta, luz, _ = pasillo()
    fiesta_anim(fiesta, luz, F(dur))
    _rastro(random.Random(3), 2.0, HAB10_Y + 0.3)
    y0, y1 = 2.6, 5.4
    cr.correr(1, F(dur), (-0.42, y0, 0), (-0.42, y1, 0), yaw=math.pi, pasos_s=1.4, amp=0.35)
    me.correr(1, F(dur), (0.38, y0 - 0.2, 0), (0.38, y1 - 0.2, 0), yaw=math.pi, pasos_s=1.4, amp=0.35)
    for j, p in enumerate((cr, me)):
        p.expresion(1, "sorpresa", 0.6)
        p.mirar(F(0.8), 0.4, -0.1)
        p.mirar(F(1.8), -0.4, -0.1)
        p.mirar(F(2.8), 0, -0.3)
        vida(p, dur, 95 + j)
    camera(sc, "c1", 0, dur, (0.05, y0 + 2.6, 1.65), (0.05, y1 + 2.4, 1.65), (0, y0, 1.25), (0, y1, 1.25), lens=24)


ESCENAS = {"frontera": s_frontera, "mil": s_mil, "siguen": s_siguen, "llegan": s_llegan, "abdos": s_abdos, "reloj": s_reloj, "pasillo": s_pasillo, "fiesta": s_fiesta}


def main():
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    C1.OUT = out
    rw, rh = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (576, 1024)
    only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ESCENAS[name](sc, dur)
    cuts = sorted(m.frame for m in sc.timeline_markers if m.frame > 1)
    for o in bpy.data.objects:
        for fc in all_fcurves(o):
            if fc.modifiers or fc.data_path == "hide_render":
                continue
            kps = sorted(fc.keyframe_points, key=lambda k: k.co.x)
            for i, kp in enumerate(kps):
                kp.interpolation = "LINEAR" if o.name == "sombra" else "BEZIER"
                if i + 1 < len(kps):
                    nf = kps[i + 1].co.x
                    if any(kp.co.x < c and c <= nf <= c + 1 for c in cuts):
                        kp.interpolation = "CONSTANT"
    setup_render(sc, rw, rh, FPS, F(dur), 12)
    sc.cycles.light_sampling_threshold = 0.05
    d = f"{out}/x_3d_{name}"
    if only:
        for fr in only:
            sc.frame_set(fr)
            sc.render.filepath = f"{d}/s_{fr:04d}.png"
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = d + "/f_"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
