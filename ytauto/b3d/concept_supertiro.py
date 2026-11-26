"""Fotogramas de concepto para «SUPERTIRO» (fútbol épico estilo anime con nuestros personajes).
Uso: python -m ytauto.b3d.concept_supertiro SALIDA_DIR [plano] [ancho alto]"""
from __future__ import annotations

import math
import random
import sys

import bpy
from mathutils import Vector

from .core import key, setup_render, srgb
from .escenario import GH, GW, GY, balon, cielo, cesped, gradas, lineas, porteria, vallas
from .personaje import Personaje

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sup"
ONLY = sys.argv[2] if len(sys.argv) > 2 else ""
RW, RH = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (720, 1280)


# ------------------------------------------------------------------ materiales de efectos
def glow(name, col, strength=6.0, alpha=0.6, rim=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    out = nt["Material Output"]
    nt.remove(nt["Principled BSDF"])
    em = nt.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*col, 1)
    em.inputs["Strength"].default_value = strength
    tr = nt.new("ShaderNodeBsdfTransparent")
    mix = nt.new("ShaderNodeMixShader")
    if rim:
        lw = nt.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.35
        pw = nt.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.6
        mu = nt.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = alpha
        ln.new(lw.outputs["Facing"], pw.inputs[0])
        ln.new(pw.outputs[0], mu.inputs[0])
        ln.new(mu.outputs[0], mix.inputs["Fac"])
    else:
        mix.inputs["Fac"].default_value = alpha
    ln.new(tr.outputs[0], mix.inputs[1])
    ln.new(em.outputs[0], mix.inputs[2])
    ln.new(mix.outputs[0], out.inputs["Surface"])
    return m


def blob(name, loc, scale, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, segments=24, ring_count=12)
    o = bpy.context.active_object
    o.name, o.scale, o.rotation_euler = name, scale, rot
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def flame(name, base, d, length, r, m):
    d = Vector(d).normalized()
    a = Vector(base)
    b = a + d * length
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.0, depth=length, location=(a + b) / 2, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


# ------------------------------------------------------------------ efectos
def aura(center, height=2.2, col=(0.02, 0.35, 1.0), seed=1, cam_dir=None):
    rng = random.Random(seed)
    c = Vector(center)
    shell = glow("aura_capa", col, 2.2, 0.7, rim=True)
    blob("aura", c + Vector((0, 0, height * 0.52)), (0.75, 0.62, height * 0.62), shell)
    fl = glow("aura_llama", col, 2.5, 0.3)
    core = glow("aura_nucleo", (0.3, 0.7, 1.0), 3.0, 0.25)
    for i in range(22):
        a = 2 * math.pi * i / 22 + rng.uniform(-0.1, 0.1)
        if cam_dir is not None and math.cos(a) * cam_dir[0] + math.sin(a) * cam_dir[1] > 0.35:
            continue        # nada de llamas tapando la cara
        rr = rng.uniform(0.45, 0.62)
        base = c + Vector((math.cos(a) * rr, math.sin(a) * rr * 0.85, rng.uniform(0.1, height * 0.6)))
        d = (Vector((math.cos(a) * 0.25, math.sin(a) * 0.25, 1)) + Vector((rng.uniform(-.1, .1), rng.uniform(-.1, .1), 0)))
        flame(f"llama{i}", base, d, rng.uniform(0.6, 1.3), rng.uniform(0.06, 0.11), fl if i % 3 else core)
    # chispas
    sp = glow("chispa", (0.4, 0.8, 1.0), 6.0, 0.9)
    for i in range(40):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.5, 1.1)
        blob(f"chispa{i}", c + Vector((math.cos(a) * rr, math.sin(a) * rr, rng.uniform(0.2, height + 0.6))),
             (0.018,) * 3, sp)


def estela(points, r0=0.22, col=(0.02, 0.35, 1.0), seed=2):
    """Estela de energía: esferas decrecientes del balón (points[0]) hacia atrás + chispas."""
    rng = random.Random(seed)
    pts = [Vector(p) for p in points]
    n = 46
    core = glow("estela_nucleo", (0.45, 0.8, 1.0), 4.0, 0.7)
    outer = glow("estela_fuera", col, 2.5, 0.18)
    for i in range(n):
        u = i / (n - 1)
        # interpolar por la polilínea
        seg = u * (len(pts) - 1)
        k = min(int(seg), len(pts) - 2)
        p = pts[k].lerp(pts[k + 1], seg - k)
        r = r0 * (1 - u) ** 0.8 + 0.01
        blob(f"est_c{i}", p, (r * 0.75,) * 3, core)
        wob = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * r * 0.35
        blob(f"est_o{i}", p + wob, (r * 1.35,) * 3, outer)
    sp = glow("est_chispa", (0.4, 0.8, 1.0), 6.0, 0.9)
    for i in range(50):
        u = rng.uniform(0, 0.8)
        seg = u * (len(pts) - 1)
        k = min(int(seg), len(pts) - 2)
        p = pts[k].lerp(pts[k + 1], seg - k)
        off = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized() * rng.uniform(0.2, 0.7)
        blob(f"est_s{i}", p + off, (0.02,) * 3, sp)


def onda(center, normal, radius, col=(1.0, 0.55, 0.1), name="onda"):
    bpy.ops.mesh.primitive_torus_add(location=center, major_radius=radius, minor_radius=radius * 0.012,
                                     major_segments=64, minor_segments=12)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector(normal).to_track_quat("Z", "Y")
    o.data.materials.append(glow(name + "_m", col, 3.5, 0.55))
    return o


def mano_gigante(center, normal, size=1.4, col=(1.0, 0.55, 0.12)):
    """Mano de energía del portero: palma + 4 dedos + pulgar, translúcida y brillante."""
    m = glow("mano_m", col, 3.0, 0.6)
    c = Vector(center)
    root = bpy.data.objects.new("mano", None)
    bpy.context.collection.objects.link(root)
    root.location = c
    root.rotation_mode = "QUATERNION"
    root.rotation_quaternion = Vector(normal).to_track_quat("Z", "Y")   # palma mirando a +normal
    s = size
    parts = [blob("palma", (0, 0, 0), (0.55 * s, 0.6 * s, 0.16 * s), m)]
    for i, x in enumerate((-0.36, -0.12, 0.12, 0.36)):
        ln = (0.55, 0.65, 0.62, 0.5)[i] * s
        parts.append(blob(f"dedo{i}", (x * s, 0.55 * s + ln / 2, 0.02 * s), (0.11 * s, ln / 2, 0.11 * s), m))
    parts.append(blob("pulgar", (-0.62 * s, 0.05 * s, 0.05 * s), (0.12 * s, 0.3 * s, 0.12 * s), m,
                      rot=(0, 0, math.radians(35))))
    for p in parts:
        p.parent = root
    return root


def ojos_brillo(p, col=(0.3, 0.75, 1.0), strength=4.0):
    b = p.m_iris.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = strength


def estadio_atardecer(tmp):
    cielo(sol_elev=9, sol_rot=230, fuerza=0.8)
    sun = bpy.data.objects["sol"]
    sun.data.color = (1.0, 0.72, 0.45)
    sun.data.energy = 3.5
    cesped()
    lineas()
    porteria()
    vallas(tmp)
    gradas(animar=False)


def cam(loc, tgt, lens):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.active_object
    c.data.lens = lens
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = c
    return c


# ------------------------------------------------------------------ planos
def p_aura():
    d = Personaje("del", kit=(40, 110, 215), num="9", pelo="pinchos").build()
    d.place((0, 2.0, 0), math.radians(90))
    d.pose(1, hips=(0.0, 0.0), knees=(0.25, 0.25), shoulders=((0.3, 0.55), (0.3, -0.55)), elbows=(-1.6, -1.6),
           lean=0.12, pelvis_z=-0.06)
    d.expresion(1, "enfadado")
    d.cabeza(1, 0, -0.08, 0)
    ojos_brillo(d)
    aura((0, 2.0, 0), cam_dir=(1, 0))
    cam((2.0, 1.55, 1.55), (0, 2.0, 1.55), 32)


def p_chut():
    d = Personaje("del", kit=(40, 110, 215), num="9", pelo="pinchos").build()
    d.root.rotation_mode = "XYZ"
    d.place((0.0, 1.0, 0.75), 0)
    d.root.rotation_euler = (math.radians(-20), math.radians(-25), 0)
    d.pose(1, hips=(0.7, -1.7), knees=(1.4, 0.05), shoulders=((0.3, 1.5), (-0.5, -1.3)), elbows=(-0.5, -0.3),
           lean=-0.35)
    d.expresion(1, "grito")
    ojos_brillo(d)
    b = balon((0.0, -2.6, 1.45))
    b.scale = (1.2,) * 3
    estela([(0.0, -2.6, 1.45), (0.05, -1.4, 1.3), (0.15, -0.2, 1.05), (0.3, 0.6, 0.85)], r0=0.3)
    aura((0.0, 1.0, 0.75), height=1.9, seed=3, cam_dir=(0.8, -0.6))
    cam((5.2, 0.1, 0.9), (0.0, -0.5, 1.3), 20)


def p_choque():
    g = Personaje("gk", kit=(255, 140, 30), num="1", pelo="rizos", guantes=True, pelo_col=(20, 14, 10),
                  piel=(170, 110, 75)).build()
    g.place((0, GY + 0.5, 0), math.pi)
    g.pose(1, hips=(-0.2, 0.3), knees=(0.5, 0.6), shoulders=((-1.5, 0.15), (-1.3, -0.3)), elbows=(-0.1, -0.1),
           lean=0.25, pelvis_z=-0.12)
    g.expresion(1, "grito")
    ojos_brillo(g, (1.0, 0.6, 0.15), 3.0)
    hand = Vector((0.1, GY + 1.9, 1.55))
    mano_gigante(hand, (0, 1, 0), 1.25)
    b = balon(tuple(hand + Vector((0, 0.35, 0.05))))
    b.scale = (1.2,) * 3
    estela([hand + Vector((0, 0.35, 0.05)), hand + Vector((0.1, 2.5, -0.2)), hand + Vector((0.2, 5.5, -0.5))], r0=0.32)
    for i, r in enumerate((0.9, 1.6, 2.4)):
        onda(tuple(hand + Vector((0, 0.3 + 0.15 * i, 0.05))), (0, 1, 0), r, name=f"onda{i}")
    cam((2.4, GY + 5.0, 1.2), (0.1, GY + 1.3, 1.5), 24)


def p_fuera():
    b = balon((-2.2, GY - 4.5, 7.2))
    b.scale = (2.2,) * 3
    estela([(-2.2, GY - 4.5, 7.2), (-1.8, GY - 2.5, 4.0), (-1.4, GY - 1.6, 1.8), (-0.6, GY + 3.0, 1.3)], r0=0.5)
    # la red rota: un agujero (quitamos unas caras del fondo de la red) + trozos volando
    net = bpy.data.objects.get("red_fondo")
    if net:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(net.data)
        kill = [f for f in bm.faces if (f.calc_center_median() - Vector((-1.4, GY - 1.6, 1.6))).length < 0.75]
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(net.data)
        bm.free()
    d = Personaje("del", kit=(40, 110, 215), num="9", pelo="pinchos").build()
    d.place((0.35, -0.6, 0), math.radians(10))
    d.pose(1, shoulders=((-0.2, 0.5), (-0.2, -0.5)), elbows=(-0.6, -0.6))
    d.expresion(1, "sorpresa")
    d.mirar(1, 0, 0.5)
    d.cabeza(1, 0, -0.4, 0)
    cam((1.5, 2.2, 0.6), (-0.9, GY - 2, 4.3), 18)


def p_heroe():
    """Contrapicado del 9 en el aire gritando la técnica (para el rótulo)."""
    p_chut()
    cam((1.9, 1.4, 0.3), (0.0, 1.0, 1.75), 18)


PLANOS = {"aura": p_aura, "chut": p_chut, "choque": p_choque, "fuera": p_fuera, "heroe": p_heroe}


def main():
    names = ONLY.split(",") if ONLY else ["aura", "chut", "heroe", "choque"]
    for nm in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        sc = bpy.context.scene
        if nm == "fuera":
            estadio_atardecer(OUT)
            PLANOS[nm]()
        else:
            PLANOS[nm]()
            estadio_atardecer(OUT)
        setup_render(sc, RW, RH, 24, 1, 24)
        sc.cycles.transparent_max_bounces = 64
        sc.frame_set(1)
        sc.render.filepath = f"{OUT}/raw_{nm}.png"
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
