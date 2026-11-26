"""Caricaturas 3D de jugadores conocidos (parodia respetuosa: sin escudos ni logos, colores de selección).
Uso hoja: python -m ytauto.b3d.famosos SALIDA_DIR"""
from __future__ import annotations

import math
import sys

import bpy
import bmesh
from mathutils import Vector

from .core import attach, mat, smooth, sphere, srgb
from .personaje import HEAD_C, HEAD_R, Personaje


# ------------------------------------------------------------------ piezas
def barba(p, col, grosor=0.018, bigote=True, perilla=False, densa=True):
    """Concha de barba sobre la mandíbula con hueco para la boca."""
    c, R = HEAD_C, HEAD_R
    me = bpy.data.meshes.new(p.n + "_barba")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64, radius=1.0)
    top = -0.1 if densa else -0.3

    def fuera(v):
        x, y, z = v.co
        if z > top or y > 0.35:
            return True
        if y < -0.2 and abs(x) < 0.3 and -0.72 < z < -0.3:     # boca
            return True
        if not densa and abs(x) > 0.55 and z > -0.55:           # barba fina: solo mentón y bigote
            return True
        return False

    bmesh.ops.delete(bm, geom=[v for v in bm.verts if fuera(v)], context="VERTS")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(p.n + "_barba", me)
    bpy.context.collection.objects.link(o)
    o.location, o.scale = tuple(c), (R + 0.012, R + 0.012, R + 0.012)
    m = mat(p.n + "_barba_m", srgb(*col), 0.7)
    o.data.materials.append(m)
    attach(o, p.neck)
    smooth(o)
    sol = o.modifiers.new("grosor", "SOLIDIFY")
    sol.thickness = grosor / (R + 0.012)
    if bigote:
        for sx in (-1, 1):
            b = sphere(f"{p.n}_bigote{sx}", (sx * 0.05, -R + 0.006, c.z - 0.098), (0.06, 0.022, 0.018), m, p.neck)
            b.rotation_euler = (0, math.radians(sx * 12), 0)
    if perilla:
        sphere(p.n + "_perilla", (0, -R + 0.03, c.z - 0.27), (0.05, 0.035, 0.04), m, p.neck)
    return o


def tupe_cr(p, col):
    """Pelo corto en los lados y arriba más largo, peinado hacia arriba y atrás."""
    c, R = HEAD_C, HEAD_R
    m = mat(p.n + "_tupe_m", srgb(*col), 0.45)
    t = sphere(p.n + "_tupe", (0.0, 0.0, c.z + R - 0.05), (0.27, 0.29, 0.1), m, p.neck)
    t.rotation_euler = (math.radians(-12), 0, 0)
    f = sphere(p.n + "_tupe_frente", (0.0, -0.17, c.z + R - 0.05), (0.23, 0.11, 0.11), m, p.neck)
    f.rotation_euler = (math.radians(-38), 0, 0)


def rayas(p, a, b, n=16):
    """Camiseta a rayas verticales (a/b en sRGB 0-255)."""
    m = p.m_shirt
    nt, ln = m.node_tree.nodes, m.node_tree.links
    bsdf = nt["Principled BSDF"]
    tc = nt.new("ShaderNodeTexCoord")
    sep = nt.new("ShaderNodeSeparateXYZ")
    mul = nt.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = n
    sn = nt.new("ShaderNodeMath")
    sn.operation = "SINE"
    gt = nt.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.0
    mix = nt.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (*srgb(*a), 1)
    mix.inputs["B"].default_value = (*srgb(*b), 1)
    ln.new(tc.outputs["Object"], sep.inputs[0])
    ln.new(sep.outputs["X"], mul.inputs[0])
    ln.new(mul.outputs[0], sn.inputs[0])
    ln.new(sn.outputs[0], gt.inputs[0])
    ln.new(gt.outputs[0], mix.inputs["Factor"])
    ln.new(mix.outputs["Result"], bsdf.inputs["Base Color"])


# ------------------------------------------------------------------ jugadores
def CR7(n="cr7"):
    p = Personaje(n, kit=(200, 16, 46), num="7", pelo="rapado", pelo_col=(38, 26, 18), piel=(222, 168, 128),
                  ojos=(70, 45, 25), pantalon=(0, 105, 62), medias=(200, 16, 46), ribete=(0, 105, 62)).build()
    tupe_cr(p, (38, 26, 18))
    return p


def MESSI(n="messi"):
    p = Personaje(n, kit=(245, 245, 250), num="10", pelo="raya", pelo_col=(92, 58, 32), piel=(238, 192, 158),
                  ojos=(80, 55, 30), pantalon=(22, 22, 30), medias=(245, 245, 250), ribete=(120, 185, 235)).build()
    rayas(p, (245, 245, 250), (120, 185, 235), n=15)
    barba(p, (102, 66, 38), densa=True)
    return p


def NEYMAR(n="ney"):
    p = Personaje(n, kit=(252, 214, 30), num="10", pelo="rizos", pelo_col=(48, 32, 20), piel=(196, 140, 100),
                  ojos=(60, 40, 24), pantalon=(20, 60, 160), medias=(250, 250, 250), ribete=(0, 140, 70)).build()
    barba(p, (40, 28, 18), grosor=0.01, densa=False, perilla=True)
    return p


def LAMINE(n="lamine"):
    return Personaje(n, kit=(190, 18, 32), num="19", pelo="rizos", pelo_col=(16, 12, 10), piel=(132, 84, 54),
                     ojos=(45, 28, 18), pantalon=(20, 30, 80), medias=(20, 30, 80), ribete=(250, 196, 0)).build()


def MBAPPE(n="mbappe"):
    return Personaje(n, kit=(22, 36, 92), num="10", pelo="rapado", pelo_col=(28, 20, 16), piel=(118, 76, 50),
                     ojos=(40, 26, 16), pantalon=(245, 245, 250), medias=(200, 20, 40), ribete=(200, 20, 40)).build()


def HAALAND(n="haaland"):
    return Personaje(n, kit=(200, 18, 38), num="9", pelo="coleta", pelo_col=(236, 202, 125), piel=(252, 214, 190),
                     ojos=(70, 110, 150), pantalon=(245, 245, 250), medias=(20, 34, 90), ribete=(20, 34, 90)).build()


def KANE(n="kane"):
    return Personaje(n, kit=(246, 246, 250), num="9", pelo="raya", pelo_col=(140, 100, 62), piel=(250, 206, 178),
                     ojos=(70, 95, 120), pantalon=(24, 30, 72), medias=(246, 246, 250), ribete=(24, 30, 72)).build()


FAMOSOS = {"cr7": CR7, "messi": MESSI, "neymar": NEYMAR, "lamine": LAMINE, "mbappe": MBAPPE, "haaland": HAALAND,
           "kane": KANE}


# ------------------------------------------------------------------ hoja de personajes
def main():
    from .core import setup_render
    from .demo_hoja import camara, estudio
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/famosos"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    estudio()
    ex = {"cr7": "picaro", "messi": "feliz", "neymar": "feliz", "lamine": "picaro", "mbappe": "feliz",
          "haaland": "grito", "kane": "neutral"}
    k0 = (len(FAMOSOS) - 1) / 2
    ps = []
    for i, (k, fn) in enumerate(FAMOSOS.items()):
        p = fn()
        p.place(((i - k0) * 1.05, 0, 0), 0)
        p.reposo(1)
        p.expresion(1, ex[k])
        ps.append(p)
    setup_render(sc, 2100, 900, 24, 10, 32)
    sc.frame_set(1)
    camara((0, -8.6, 1.3), (0, 0, 1.15), 40)
    sc.render.filepath = f"{out}/famosos_cuerpo.png"
    bpy.ops.render.render(write_still=True)
    # caras
    setup_render(sc, 600, 600, 24, 10, 32)
    for i, k in enumerate(FAMOSOS):
        x = (i - k0) * 1.05
        camara((x + 0.25, -1.75, 2.0), (x, 0, 1.9), 55)
        sc.frame_set(1)
        sc.render.filepath = f"{out}/cara_{k}.png"
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
