"""Interior de autobús para «La Concentración». Techo a 2,7 m (los muñecos miden más de 2 m con la cabeza). El bus mira a -Y (conductor delante, en y≈-1); fila del fondo en y=7.
El paisaje (árboles, carretera) se mueve hacia +Y para simular la marcha."""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from .core import cube, key, mat, pivot, sphere, srgb

FILAS = [1.0, 2.1, 3.2, 4.3, 5.4]      # y de cada fila de asientos (izquierda x=-0.72, derecha x=0.72)
FONDO_Y = 6.7
LUCES_BUS: list = []


def asiento(nombre, x, y, ancho=0.42, tapiz=None):
    tapiz = tapiz or mat("tapiz", srgb(40, 70, 140), 0.7, sheen=0.4)
    cube(nombre + "_base", (x, y, 0.42), (ancho, 0.24, 0.07), tapiz)
    cube(nombre + "_resp", (x, y + 0.26, 0.82), (ancho, 0.06, 0.36), tapiz)
    cube(nombre + "_pata", (x, y, 0.18), (0.05, 0.05, 0.18), mat("metal_bus", srgb(150, 150, 158), 0.3))


def autobus(dur, velocidad=9.0, en_marcha=True):
    LUCES_BUS.clear()
    sc = bpy.context.scene
    w = bpy.data.worlds.new("cielo_bus")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb(150, 195, 240), 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    sun = bpy.context.active_object
    sun.data.energy, sun.data.angle = 3.0, math.radians(3)
    sun.rotation_euler = (math.radians(50), math.radians(20), math.radians(70))
    # carrocería
    chapa = mat("chapa_int", srgb(225, 225, 230), 0.5)
    suelo = mat("suelo_bus", srgb(70, 72, 80), 0.7)
    cube("bus_suelo", (0, 2.6, -0.02), (1.32, 4.6, 0.02), suelo)
    cube("bus_techo", (0, 2.6, 2.72), (1.32, 4.6, 0.03), chapa)
    for sx in (-1, 1):
        cube(f"bus_lat{sx}", (sx * 1.3, 2.6, 0.45), (0.03, 4.6, 0.45), chapa)
        cube(f"bus_marco{sx}", (sx * 1.3, 2.6, 2.55), (0.03, 4.6, 0.15), chapa)
        for k in range(10):
            cube(f"bus_pilar{sx}_{k}", (sx * 1.3, -1.6 + k * 0.95, 1.7), (0.035, 0.05, 0.85), chapa)
        cube(f"bus_barra{sx}", (sx * 0.95, 2.6, 2.45), (0.015, 4.4, 0.015), mat("metal_bus", srgb(150, 150, 158), 0.3))
    cube("bus_trasera", (0, 7.2, 1.36), (1.32, 0.03, 1.36), chapa)
    cube("bus_pasillo", (0, 2.6, 0.003), (0.32, 4.4, 0.003), mat("alfombra", srgb(150, 30, 40), 0.8))
    tap = mat("tapiz", srgb(40, 70, 140), 0.7, sheen=0.4)
    for i, y in enumerate(FILAS):
        asiento(f"as_L{i}", -0.72, y, tapiz=tap)
        asiento(f"as_R{i}", 0.72, y, tapiz=tap)
    asiento("as_fondo", 0, FONDO_Y, ancho=1.22, tapiz=tap)
    # puesto del conductor
    asiento("as_cond", -0.72, -0.9, tapiz=mat("tapiz_cond", srgb(30, 30, 36), 0.6))
    bpy.ops.mesh.primitive_torus_add(location=(-0.72, -1.38, 1.05), major_radius=0.2, minor_radius=0.02,
                                     rotation=(math.radians(60), 0, 0))
    bpy.context.active_object.data.materials.append(mat("volante", srgb(20, 20, 24), 0.4))
    cube("salpicadero", (0, -1.55, 0.75), (1.28, 0.12, 0.12), mat("salpicadero", srgb(35, 35, 40), 0.5))
    # gorra del conductor (se queda en el asiento cuando desaparece)
    gorra = sphere("gorra", (-0.72, -0.95, 0.53), (0.13, 0.13, 0.07), mat("gorra_m", srgb(25, 40, 90), 0.5))
    cube("gorra_visera", (-0.72, -1.08, 0.5), (0.1, 0.06, 0.01), mat("gorra_m", srgb(25, 40, 90), 0.5))
    # luces interiores suaves
    for i, y in enumerate((0.5, 3.0, 5.5)):
        bpy.ops.object.light_add(type="AREA", location=(0, y, 2.65))
        L = bpy.context.active_object
        L.data.energy, L.data.size = 70, 0.8
        LUCES_BUS.append(L)
    # paisaje que pasa: carretera + árboles + postes
    paisaje = pivot("paisaje", (0, 0, 0))
    cube("carretera", (0, -60, -0.6), (4.0, 140, 0.02), mat("asfalto", srgb(60, 60, 66), 0.85), paisaje)
    cube("campo", (0, -60, -0.65), (80, 140, 0.02), mat("hierba_fuera", srgb(110, 160, 80), 0.9), paisaje)
    rng = random.Random(9)
    tronco = mat("tronco", srgb(100, 70, 45), 0.8)
    copa = mat("copa", srgb(60, 130, 60), 0.8)
    for i in range(70):
        y = -180 + i * 2.8 + rng.uniform(-1, 1)
        for sx in (-1, 1):
            if rng.random() < 0.35:
                continue
            x = sx * rng.uniform(5.5, 14)
            cube(f"tronco{i}{sx}", (x, y, 0.4), (0.12, 0.12, 1.0), tronco, paisaje)
            sphere(f"copa{i}{sx}", (x, y, 2.0), (1.0, 1.0, 1.2) if rng.random() < 0.5 else (0.8, 0.8, 1.5), copa,
                   paisaje, 16, 8)
    if en_marcha:
        frames = int(dur * 24) + 2
        for f in range(1, frames + 1, 6):
            key(paisaje, f, location=Vector((0, velocidad * (f - 1) / 24, 0)))
    return paisaje


def frenazo(paisaje, f_freno, dur, velocidad=9.0):
    """El paisaje se detiene de golpe en f_freno (deceleración en ~0,5 s)."""
    pos = velocidad * (f_freno - 1) / 24
    # se reescriben las claves a partir del frenazo
    from .core import all_fcurves
    for fc in all_fcurves(paisaje):
        for i in range(len(fc.keyframe_points) - 1, -1, -1):
            if fc.keyframe_points[i].co.x > f_freno:
                fc.keyframe_points.remove(fc.keyframe_points[i])
    key(paisaje, f_freno + 12, location=Vector((0, pos + velocidad * 0.25, 0)))
    key(paisaje, int(dur * 24) + 2, location=Vector((0, pos + velocidad * 0.25, 0)))
