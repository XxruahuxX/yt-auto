"""Vestuario 3D para la serie «La Concentración»: suelo de baldosas, taquillas con nombres, banco, puerta y luces.
Sala: x de -4,5 a 4,5; y de -3 a 5,2 (la pared del fondo, con las taquillas, en y = 5,2); techo a 3 m."""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

from .core import cube, key, mat, pivot, srgb
from .personaje import _font

X0, X1, YF, ZT = -4.5, 4.5, 5.2, 3.0
PUERTA = (-4.48, 0.9)          # bisagra en la pared izquierda
TAQUILLAS = [("CRISTIANO", (200, 16, 46)), ("MESSI", (120, 185, 235)), ("NEYMAR", (252, 214, 30)),
             ("LAMINE", (190, 18, 32)), ("MBAPPÉ", (22, 36, 92)), ("HAALAND", (200, 18, 38)),
             ("KANE", (246, 246, 250))]
LUCES: list = []


def _baldosas():
    m = bpy.data.materials.new("baldosa")
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    b = nt["Principled BSDF"]
    ck = nt.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 22
    ck.inputs["Color1"].default_value = (*srgb(205, 210, 214), 1)
    ck.inputs["Color2"].default_value = (*srgb(176, 184, 192), 1)
    ln.new(ck.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Coat Weight"].default_value = 0.3
    return m


def texto(nombre, body, loc, size, m, rot=(math.pi / 2, 0, 0), extrude=0.004):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = nombre
    o.data.body = body
    o.data.align_x, o.data.align_y = "CENTER", "CENTER"
    o.data.size = size
    o.data.extrude = extrude
    f = _font()
    if f:
        o.data.font = f
    o.data.materials.append(m)
    return o


def vestuario():
    LUCES.clear()
    sc = bpy.context.scene
    w = bpy.data.worlds.new("interior")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*srgb(60, 66, 80), 1)
    bg.inputs[1].default_value = 0.25
    # suelo, paredes y techo
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 1.1, 0))
    fl = bpy.context.active_object
    fl.name, fl.scale = "suelo", (X1 - X0, 8.4, 1)
    fl.data.materials.append(_baldosas())
    pared = mat("pared", srgb(232, 228, 216), 0.8)
    zocalo = mat("zocalo", srgb(40, 90, 150), 0.5)
    cube("pared_fondo", (0, YF + 0.05, ZT / 2), ((X1 - X0) / 2, 0.05, ZT / 2), pared)
    cube("pared_izq", (X0 - 0.05, 1.1, ZT / 2), (0.05, 4.2, ZT / 2), pared)
    cube("pared_der", (X1 + 0.05, 1.1, ZT / 2), (0.05, 4.2, ZT / 2), pared)
    cube("techo", (0, 1.1, ZT + 0.05), ((X1 - X0) / 2, 4.2, 0.05), mat("techo", srgb(240, 240, 238), 0.9))
    cube("franja_fondo", (0, YF - 0.005, 1.0), ((X1 - X0) / 2, 0.01, 0.12), zocalo)
    cube("franja_izq", (X0 + 0.005, 1.1, 1.0), (0.01, 4.2, 0.12), zocalo)
    cube("franja_der", (X1 - 0.005, 1.1, 1.0), (0.01, 4.2, 0.12), zocalo)
    # taquillas con el nombre de cada uno
    metal = mat("taquilla_marco", srgb(70, 76, 88), 0.35, coat=0.5)
    blanco = mat("rotulo", srgb(250, 250, 250), 0.4)
    for i, (nm, col) in enumerate(TAQUILLAS):
        x = (i - 3) * 1.0
        cube(f"taq_{i}", (x, YF - 0.3, 1.05), (0.47, 0.28, 1.05), metal)
        puerta = mat(f"taq_puerta_{i}", srgb(*col), 0.45, coat=0.4)
        cube(f"taq_p_{i}", (x, YF - 0.585, 1.0), (0.42, 0.01, 0.92), puerta)
        for k in range(4):
            cube(f"taq_rej_{i}_{k}", (x, YF - 0.6, 1.75 - k * 0.05), (0.25, 0.006, 0.01), metal)
        cube(f"taq_tir_{i}", (x + 0.3, YF - 0.605, 1.05), (0.02, 0.012, 0.09), metal)
        cube(f"taq_placa_{i}", (x, YF - 0.6, 2.2), (0.44, 0.01, 0.1), mat("placa", srgb(30, 34, 42), 0.4))
        texto(f"taq_nom_{i}", nm, (x, YF - 0.615, 2.2), 0.13, blanco)
        # perchas con camiseta colgada
        cube(f"perchero_{i}", (x, YF - 0.1, 2.38), (0.4, 0.1, 0.015), metal)
    # banco largo
    madera = mat("madera", srgb(176, 120, 70), 0.5, coat=0.3)
    cube("banco", (0, 4.0, 0.44), (3.6, 0.22, 0.035), madera)
    for x in (-3.3, -1.1, 1.1, 3.3):
        cube(f"banco_pata{x}", (x, 4.0, 0.21), (0.04, 0.18, 0.21), metal)
    # puerta con bisagra (pivote) y rendija de luz
    hinge = pivot("puerta_bisagra", (PUERTA[0], PUERTA[1], 0))
    pm = mat("puerta", srgb(120, 80, 50), 0.55)
    cube("puerta", (PUERTA[0] + 0.03, PUERTA[1] + 0.5, 1.05), (0.03, 0.5, 1.05), pm, hinge)
    cube("puerta_pomo", (PUERTA[0] + 0.08, PUERTA[1] + 0.88, 1.0), (0.03, 0.03, 0.03), metal, hinge)
    cube("marco_puerta", (PUERTA[0] + 0.01, PUERTA[1] + 0.5, 2.15), (0.03, 0.56, 0.05), metal)
    cube("salida", (PUERTA[0] + 0.03, PUERTA[1] + 0.5, 2.45), (0.02, 0.22, 0.08), mat("salida", srgb(30, 200, 90),
                                                                                       0.4, emit=4.0))
    # luces de techo (pantallas que brillan + luces de área)
    pant = mat("pantalla", srgb(255, 250, 240), 0.3, emit=6.0)
    for i, (x, y) in enumerate(((-2.6, 0.3), (0, 0.3), (2.6, 0.3), (-2.6, 3.0), (0, 3.0), (2.6, 3.0))):
        cube(f"pantalla_{i}", (x, y, ZT - 0.02), (0.55, 0.12, 0.02), pant)
        bpy.ops.object.light_add(type="AREA", location=(x, y, ZT - 0.08))
        L = bpy.context.active_object
        L.data.energy, L.data.size, L.data.color = 160, 1.1, (1.0, 0.96, 0.9)
        LUCES.append(L)
    bpy.ops.object.light_add(type="AREA", location=(0, -3.0, 1.8))
    L = bpy.context.active_object
    L.name = "relleno_cam"
    L.data.energy, L.data.size = 120, 4.0
    L.rotation_euler = (math.radians(80), 0, 0)
    LUCES.append(L)
    return hinge


def abrir_puerta(hinge, f0, f1, ang=-80):
    hinge.rotation_mode = "XYZ"
    key(hinge, f0, rotation_euler=(0, 0, 0))
    key(hinge, f1, rotation_euler=(0, 0, math.radians(ang)))


def cerrar_puerta(hinge, f0, f1, ang=-80):
    hinge.rotation_mode = "XYZ"
    key(hinge, f0, rotation_euler=(0, 0, math.radians(ang)))
    key(hinge, f1, rotation_euler=(0, 0, 0))


def apagar(f0, f1, resto=0.0):
    """Apaga las luces del techo y las pantallas entre f0 y f1 (resto: fracción que queda)."""
    for L in LUCES:
        e = L.data.energy
        L.data.keyframe_insert("energy", frame=f0)
        L.data.energy = e * resto
        L.data.keyframe_insert("energy", frame=f1)
        L.data.energy = e
    pm = bpy.data.materials.get("pantalla")
    if pm:
        s = pm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        s.keyframe_insert("default_value", frame=f0)
        v = s.default_value
        s.default_value = 0.0
        s.keyframe_insert("default_value", frame=f1)
        s.default_value = v
    bg = bpy.context.scene.world.node_tree.nodes["Background"].inputs[1]
    bg.keyframe_insert("default_value", frame=f0)
    v = bg.default_value
    bg.default_value = v * 0.08
    bg.keyframe_insert("default_value", frame=f1)
    bg.default_value = v
