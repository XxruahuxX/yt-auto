"""«La Concentración», capítulo 4: La fiesta. Parodia animada con caricaturas.
Uso: python -m ytauto.b3d.cap04 SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import os
import random
import sys

import bpy
from mathutils import Vector

from . import cap01 as C1
from .cap01 import reparto
from .core import all_fcurves, apoyar_pies, cube, key, mat, pivot, setup_render, sphere, srgb
from .droides import droide, encender_ojos, hablar_droide
from .hotel import BED_Y, HAB10_Y, fiesta_anim, habitacion, pasillo
from .video_anime import hablar
from .video_penalti import FPS, F, camera, vida

KITS = [(200, 16, 46), (120, 185, 235), (252, 214, 30), (190, 18, 32), (22, 36, 92), (200, 18, 38), (246, 246, 250)]
COLS = [(1.0, 0.0, 0.8), (0.0, 0.8, 1.0), (1.0, 0.85, 0.0), (0.4, 1.0, 0.2)]


# ------------------------------------------------------------------ decorado de fiesta
def sala_fiesta(dur_f):
    """La habitación 10 de noche, con bola de discoteca, luces de colores, guirnalda de botas y tele."""
    habitacion(C1.OUT, noche=True, piernas=())
    bpy.data.objects.remove(bpy.data.objects["cuadro"])
    # guirnalda de botas en la pared del fondo
    cube("cordel", (0, 2.46, 2.38), (2.2, 0.005, 0.005), mat("cordel_m", srgb(240, 240, 240), 0.6))
    for i in range(12):
        x = -2.0 + i * 0.36
        z = 2.3 - 0.06 * math.sin(i * 1.3)
        b = cube(f"bota_g{i}", (x, 2.42, z - 0.1), (0.045, 0.12, 0.045), mat(f"bota_g_{i % 7}", srgb(*KITS[i % 7]), 0.4))
        b.rotation_euler = (math.radians(90), math.radians(15 * math.sin(i)), 0)
    # tele en la pared del fondo, sobre el cabecero
    cube("tele_marco", (0, 2.47, 1.72), (0.62, 0.03, 0.36), mat("tele_marco", srgb(20, 20, 22), 0.3))
    pantalla = mat("tele_pantalla", srgb(10, 10, 12), 0.2, emit=0.0)
    cube("tele_pantalla", (0, 2.435, 1.72), (0.57, 0.005, 0.31), pantalla)
    # bola de discoteca que gira
    bola = sphere("bola_disco", (0, 0.2, 2.45), (0.17,) * 3, mat("espejo", srgb(230, 230, 235), 0.05, coat=1.0), None, 24, 12)
    cube("bola_hilo", (0, 0.2, 2.65), (0.004, 0.004, 0.06), mat("cordel_m", srgb(240, 240, 240), 0.6))
    key(bola, 1, rotation_euler=(0, 0, 0))
    key(bola, dur_f, rotation_euler=(0, 0, math.radians(2.5 * dur_f)))
    # luces de colores que cambian a golpes
    luces = []
    for j, (x, y) in enumerate(((-1.6, -1.0), (1.6, -0.8), (0.0, 1.8))):
        bpy.ops.object.light_add(type="POINT", location=(x, y, 2.3))
        L = bpy.context.active_object
        L.data.energy, L.data.shadow_soft_size = 90, 0.2
        luces.append(L)
        for i, f in enumerate(range(1, dur_f + 1, 6)):
            L.data.color = COLS[(i + j) % 4]
            L.data.keyframe_insert("color", frame=f)
    return pantalla


def tarta(loc):
    m = mat("bizcocho", srgb(230, 190, 140), 0.6)
    nata = mat("nata", srgb(250, 246, 240), 0.5)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=0.16, location=(loc[0], loc[1], loc[2] + 0.08))
    o = bpy.context.active_object
    o.name = "tarta"
    o.data.materials.append(nata)
    for k in range(5):
        a = k * 2 * math.pi / 5
        cube(f"vela{k}", (loc[0] + 0.12 * math.cos(a), loc[1] + 0.12 * math.sin(a), loc[2] + 0.21), (0.008, 0.008, 0.05),
             mat("vela", srgb(240, 80, 120), 0.5))
        sphere(f"llama{k}", (loc[0] + 0.12 * math.cos(a), loc[1] + 0.12 * math.sin(a), loc[2] + 0.28), (0.012, 0.012, 0.022),
               mat("llama", srgb(255, 190, 60), 0.5, emit=8.0))
    return o, m


def bailar(p, f0, f1, cada=8, amp=1.0, fase=0):
    """Baile de discoteca: brazo arriba alterno, cadera que gira y rebote."""
    for i, f in enumerate(range(f0, f1 + 1, cada)):
        k = (i + fase) % 4
        up = ((-2.8 * amp, 0.4), (0.1, -0.3)) if k in (0, 1) else ((0.1, 0.3), (-2.8 * amp, -0.4))
        p.pose(f, hips=(-0.15 if k % 2 else 0.05, 0.05 if k % 2 else -0.15), knees=(0.35, 0.35) if k % 2 else (0.1, 0.1),
               shoulders=up, elbows=(-0.4, -0.4), lean=0.05, pelvis_z=-0.06 if k % 2 else 0.0,
               twist=0.35 * amp * (1 if k < 2 else -1))


# ------------------------------------------------------------------ escenas
def s_abren(sc, dur):
    ps = reparto(["cr7", "messi"])
    cr, me = ps["cr7"], ps["messi"]
    fiesta, luz, _ = pasillo()
    fiesta_anim(fiesta, luz, F(dur), cada=5)
    hinge = bpy.data.objects["hinge10"]
    key(hinge, 1, rotation_euler=(0, 0, math.radians(-35)))
    key(hinge, F(1.2), rotation_euler=(0, 0, math.radians(-35)))
    key(hinge, F(1.8), rotation_euler=(0, 0, math.radians(-105)))
    cr.place((0.25, HAB10_Y - 0.65, 0), math.pi / 2, 1)
    me.place((0.1, HAB10_Y + 0.15, 0), math.pi / 2, 1)
    for p in (cr, me):
        p.reposo(1)
        p.expresion(1, "neutral")
    cr.pose(F(1.0), shoulders=((-1.4, 0.0), (0.05, -0.12)), elbows=(-0.2, -0.2))     # empuja la puerta
    cr.reposo(F(1.8))
    for p in (cr, me):
        p.expresion(F(1.9), "sorpresa")
        p.cabeza(F(2.0), 0, 0.1, 0)
    vida(cr, dur, 100)
    vida(me, dur, 101)
    camera(sc, "c1", 0, dur, (-0.6, HAB10_Y - 2.4, 1.75), (-0.55, HAB10_Y - 2.0, 1.7), (0.6, HAB10_Y, 1.1), lens=24)


def s_fiesta(sc, dur):
    ps = reparto(["neymar"])
    ne = ps["neymar"]
    sala_fiesta(F(dur))
    ne.place((0, -0.3, 0), 0, 1)
    ne.expresion(1, "feliz")
    bailar(ne, 1, F(dur), cada=7)
    ne.cabeza(F(1.5), 0.2, 0.1, 0.1)
    ne.cabeza(F(2.5), -0.2, 0.1, -0.1)
    vida(ne, dur, 102)
    camera(sc, "c1", 0, dur, (0.4, -2.3, 1.45), (0.25, -2.0, 1.5), (0, 0.4, 1.35), (0, 0.6, 1.5), lens=22)


def s_jura(sc, dur):
    ps = reparto(["neymar"])
    ne = ps["neymar"]
    sala_fiesta(F(dur))
    ne.place((0, -0.3, 0), 0, 1)
    ne.pose(1, shoulders=((-1.2, 0.2), (-2.6, -0.4)), elbows=(-1.0, -0.3))   # bota en una mano, la otra arriba
    ne.expresion(1, "sorpresa")
    hablar(ne, F(0.2), F(dur - 0.3), "picaro", "grito", cada=5)
    ne.cabeza(F(1.0), 0.25, 0, 0.1)
    ne.cabeza(F(2.2), -0.25, 0, -0.1)
    # bota con lazo rojo agarrada en la mano izquierda (va emparentada a la mano)
    from .core import attach
    mano = bpy.data.objects["ney_manoL"]
    sc.frame_set(1)
    bpy.context.view_layer.update()
    h = mano.matrix_world.translation.copy()
    bt = cube("bota_lazo", (h.x, h.y - 0.06, h.z + 0.02), (0.05, 0.13, 0.05), mat("bota_neg", srgb(25, 25, 28), 0.4))
    attach(bt, mano)
    lazo = mat("lazo", srgb(220, 20, 40), 0.5)
    for sx in (-1, 1):
        attach(sphere(f"lazo{sx}", (h.x + sx * 0.05, h.y - 0.08, h.z + 0.09), (0.05, 0.02, 0.03), lazo), mano)
    vida(ne, dur, 103)
    camera(sc, "c1", 0, dur, (0.15, -2.2, 1.7), (0.1, -2.0, 1.68), (-0.05, -0.3, 1.4), lens=28)


def s_tarta(sc, dur):
    ps = reparto(["haaland", "mbappe"])
    ha, mb = ps["haaland"], ps["mbappe"]
    sala_fiesta(F(dur))
    cube("mesa", (-0.55, -0.6, 0.38), (0.35, 0.3, 0.38), mat("mesa_m", srgb(110, 70, 42), 0.5), bevel=0.02)
    tarta((-0.55, -0.6, 0.76))
    ha.place((-0.55, -0.15, 0), 0, 1)
    ha.expresion(1, "feliz")
    for i, f in enumerate(range(1, F(dur), 8)):                # a puñados, de la tarta a la boca
        arriba = i % 2 == 0
        ha.pose(f, shoulders=((-0.9, 0.1), (-1.6, -0.2) if arriba else (-0.7, -0.1)), elbows=(-0.6, -2.3 if arriba else -0.5),
                lean=0.15)
        ha.expresion(f, "grito" if arriba else "feliz")
    mb.place((0.75, -0.4, 0), -0.2, 1)
    mb.expresion(1, "picaro")
    bailar(mb, 1, F(dur), cada=4, amp=1.0, fase=1)              # el doble de rápido
    vida(ha, dur, 104)
    vida(mb, dur, 105)
    camera(sc, "c1", 0, dur, (0.1, -2.45, 1.55), (0.1, -2.3, 1.5), (0.1, -0.4, 1.15), lens=20)


def s_tele(sc, dur):
    ps = reparto(["cr7", "messi", "neymar", "mbappe"])
    pant = sala_fiesta(F(dur))
    s = pant.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    c = pant.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]
    rng = random.Random(7)
    for f in range(1, F(dur) + 1, 2):                         # se enciende sola: ruido blanco
        on = f >= F(0.5)
        s.default_value = rng.uniform(1.0, 4.0) if on else 0.0
        s.keyframe_insert("default_value", frame=f)
        g = rng.uniform(0.5, 1.0)
        c.default_value = (g, g, g, 1)
        c.keyframe_insert("default_value", frame=f)
    # ojos rojos que aparecen en la pantalla
    rojo = mat("ojos_tele", srgb(255, 30, 20), 0.3, emit=0.0)
    for sx in (-1, 1):
        sphere(f"tele_ojo{sx}", (sx * 0.14, 2.425, 1.76), (0.06, 0.005, 0.04), rojo)
    encender_ojos(rojo, F(1.6), F(1.9))
    pos = [("cr7", -1.55, -0.2), ("messi", -0.85, 0.05), ("neymar", 0.85, -0.25), ("mbappe", 1.55, -0.1)]
    for j, (k, x, y) in enumerate(pos):
        p = ps[k]
        p.place((x, y - 0.6, 0), math.pi, 1)                    # de espaldas a cámara, mirando la tele
        p.reposo(1)
        p.expresion(1, "feliz")
        p.cabeza(F(0.7 + 0.08 * j), 0, 0.15, 0)
        p.expresion(F(0.8), "sorpresa")
        vida(p, dur, 106 + j)
    bailar(ps["neymar"], 1, F(0.5), cada=6)
    ps["neymar"].reposo(F(0.8))
    camera(sc, "c1", 0, dur, (0.0, -2.45, 1.75), (0.0, -2.0, 1.75), (0.0, 2.4, 1.6), lens=24)


def s_droide(sc, dur):
    w = bpy.data.worlds.new("espacio")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.03, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    r, ojos, boca = droide("droide1", (0, 0, 0))
    encender_ojos(ojos, 1, F(0.4))
    hablar_droide(boca, F(0.3), F(dur - 0.2))
    key(r, 1, rotation_euler=(0, 0, 0.1))
    key(r, F(dur), rotation_euler=(0, 0, -0.08))
    panel = mat("panel_azul", srgb(40, 120, 255), 0.4, emit=3.0)
    for i in range(7):                                         # fondo: paneles de luz de la nave
        cube(f"panel{i}", (-1.8 + i * 0.6, 1.5, 1.0 + 0.6 * (i % 2)), (0.02, 0.01, 0.5), panel)
    cube("fondo_nave", (0, 1.55, 1.5), (3, 0.02, 2), mat("nave", srgb(18, 20, 28), 0.4))
    for loc, col, e in (((1.2, -1.0, 2.2), (1.0, 0.2, 0.15), 140), ((-1.4, -0.8, 1.5), (0.2, 0.5, 1.0), 110),
                        ((0, 1.0, 2.5), (0.6, 0.7, 1.0), 160)):
        bpy.ops.object.light_add(type="AREA", location=loc)
        L = bpy.context.active_object
        L.data.energy, L.data.size, L.data.color = e, 1.0, col
        L.rotation_euler = (Vector((0, 0, 1.6)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    camera(sc, "c1", 0, dur, (0.0, -2.2, 1.6), (0.0, -1.55, 1.62), (0, 0, 1.55), lens=32)


def s_caras(sc, dur):
    ps = reparto(["cr7", "messi", "neymar"])
    sala_fiesta(F(dur))
    for j, (k, x) in enumerate((("cr7", -0.5), ("messi", 0.0), ("neymar", 0.5))):
        p = ps[k]
        p.place((x, -0.6 - 0.1 * (j % 2), 0), 0, 1)
        p.reposo(1)
        p.expresion(1, "sorpresa")
        p.mirar(1, 0, 0.1)
        p.expresion(F(1.2 + 0.1 * j), "grito")
        p.pose(F(1.3), shoulders=((-0.6, 0.6), (-0.6, -0.6)), elbows=(-1.9, -1.9))   # manos a la cabeza
        vida(p, dur, 110 + j)
    camera(sc, "c1", 0, dur, (0.0, -2.45, 1.7), (0.0, -2.25, 1.68), (0, -0.6, 1.5), lens=26)


def s_kane(sc, dur):
    ps = reparto(["kane"])
    ka = ps["kane"]
    sala_fiesta(F(dur))
    ka.place((0.2, -0.4, 0), 0.25, 1)
    ka.expresion(1, "neutral")
    poses = [((-1.6, 0.0), (0.05, -0.1)), ((-1.6, 0.0), (-1.6, 0.0)), ((0.05, 1.5), (0.05, -1.5)), ((-3.0, 0.2), (0.05, -0.1))]
    for i, f in enumerate(range(1, F(dur), 10)):              # baile de robot: posturas rígidas a golpes
        sh = poses[i % 4]
        ka.pose(f, shoulders=sh, elbows=(-1.57 if i % 2 else 0.0, -1.57 if i % 2 else 0.0), twist=0.3 * (1 if i % 2 else -1))
        ka.pose(f + 4, shoulders=sh, elbows=(-1.57 if i % 2 else 0.0, -1.57 if i % 2 else 0.0), twist=0.3 * (1 if i % 2 else -1))
        ka.cabeza(f, 0.3 * (1 if i % 2 else -1), 0, 0)
        ka.cabeza(f + 4, 0.3 * (1 if i % 2 else -1), 0, 0)
    vida(ka, dur, 120)
    camera(sc, "c1", 0, dur, (0.5, -2.45, 1.55), (0.4, -2.2, 1.55), (0.2, -0.4, 1.2), lens=26)


def s_champions(sc, dur):
    ps = reparto(["kane", "cr7", "messi"])
    ka, cr, me = ps["kane"], ps["cr7"], ps["messi"]
    sala_fiesta(F(dur))
    ka.place((0.55, -0.2, 0), -0.3, 1)
    ka.reposo(1)
    ka.expresion(1, "neutral")
    ka.pose(F(0.3), shoulders=((0.05, 0.12), (-2.9, -0.2)), elbows=(-0.2, -0.3))   # levanta la mano
    hablar(ka, F(0.4), F(dur - 0.6), "neutral", "sorpresa", cada=5)
    for j, (p, x) in enumerate(((cr, -0.75), (me, -0.15))):
        p.place((x, 0.0, 0), 0.35, 1)
        p.reposo(1)
        p.expresion(1, "sorpresa")
        p.cabeza(F(0.8), -0.5, 0, 0)                           # se giran a mirarle
        p.mirar(F(0.8), -0.4, 0)
        p.expresion(F(1.0 + 0.2 * j), "enfadado")
        vida(p, dur, 121 + j)
    me.pose(F(1.6), shoulders=((-1.0, 0.1), (0.05, -0.12)), elbows=(-2.3, -0.2))   # mano a la cara
    vida(ka, dur, 123)
    camera(sc, "c1", 0, dur, (-0.05, -2.75, 1.6), (-0.05, -2.5, 1.6), (-0.05, 0, 1.35), lens=24)


ESCENAS = {"kane": s_kane, "champions": s_champions, "abren": s_abren, "fiesta": s_fiesta, "jura": s_jura, "tarta": s_tarta, "tele": s_tele,
           "droide": s_droide, "caras": s_caras}


def main():
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    C1.OUT = out
    rw, rh = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (576, 1024)
    only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ESCENAS[name](sc, dur)
    print("HUNDIMIENTO", name, round(apoyar_pies(sc, 1, F(dur), solo_medir=bool(os.environ.get("SOLO_MEDIR"))), 3),
          flush=True)
    if os.environ.get("SOLO_MEDIR"):
        return
    cuts = sorted(m.frame for m in sc.timeline_markers if m.frame > 1)
    for o in bpy.data.objects:
        for fc in all_fcurves(o):
            if fc.modifiers:
                continue
            kps = sorted(fc.keyframe_points, key=lambda k: k.co.x)
            for i, kp in enumerate(kps):
                kp.interpolation = "BEZIER"
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
