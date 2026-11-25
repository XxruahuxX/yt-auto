"""Hoja de personaje: primeros planos con cada expresión y cuerpo entero (frente, perfil, espalda).
Uso: python -m ytauto.b3d.demo_hoja SALIDA_DIR [pelo] [solo=caras|cuerpo]"""
from __future__ import annotations

import math
import sys

import bpy
from mathutils import Vector

from .core import mat, setup_render, srgb
from .personaje import EXPRESIONES, Personaje

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/hoja"
PELO = sys.argv[2] if len(sys.argv) > 2 else "pinchos"
SOLO = sys.argv[3] if len(sys.argv) > 3 else ""


def estudio():
    sc = bpy.context.scene
    w = bpy.data.worlds.new("estudio")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*srgb(150, 190, 235), 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    bpy.context.active_object.data.materials.append(mat("suelo", srgb(84, 170, 84), 0.9))
    for nm, loc, energy, size, col in (("clave", (-2.5, -3, 3.5), 450, 2.0, (1, 0.95, 0.88)),
                                       ("relleno", (3, -2.5, 2.2), 180, 3.0, (0.85, 0.9, 1)),
                                       ("contra", (0.5, 3, 3.2), 600, 1.5, (1, 1, 1))):
        bpy.ops.object.light_add(type="AREA", location=loc)
        L = bpy.context.active_object
        L.name = nm
        L.data.energy, L.data.size, L.data.color = energy, size, col
        d = Vector((0, 0, 1.6)) - Vector(loc)
        L.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def camara(loc, target, lens):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.active_object
    c.data.lens = lens
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = c
    return c


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    estudio()
    if SOLO == "plantilla":
        estudio_cast = [("pinchos", (40, 110, 215), "9", (48, 32, 22), (250, 203, 170), "feliz"),
                        ("rizos", (255, 140, 30), "1", (20, 14, 10), (170, 110, 75), "enfadado"),
                        ("raya", (200, 30, 45), "10", (190, 120, 50), (255, 215, 185), "picaro"),
                        ("coleta", (30, 150, 80), "7", (90, 50, 25), (225, 170, 130), "sorpresa"),
                        ("rapado", (250, 250, 250), "4", (25, 20, 18), (120, 80, 55), "neutral")]
        for i, (pelo, kit, num, pc, piel, ex) in enumerate(estudio_cast):
            q = Personaje(f"p{i}", kit=kit, num=num, pelo=pelo, pelo_col=pc, piel=piel,
                          guantes=(pelo == "rizos")).build()
            q.place(((i - 2) * 1.05, 0, 0), 0)
            q.reposo(1)
            q.expresion(1, ex)
        setup_render(sc, 1400, 800, 24, 10, 24)
        camara((0, -7.2, 1.25), (0, 0, 1.1), 38)
        sc.frame_set(1)
        sc.render.filepath = f"{OUT}/plantilla.png"
        bpy.ops.render.render(write_still=True)
        return
    p = Personaje("yo", kit=(40, 110, 215), num="9", pelo=PELO).build()
    names = list(EXPRESIONES)
    for i, nm in enumerate(names):
        p.expresion(i * 10 + 1, nm)
    p.mirar(1, 0, 0)
    if SOLO != "cuerpo":
        setup_render(sc, 600, 600, 24, 100, 24)
        cam = camara((0.25, -1.75, 2.0), (0, 0, 1.9), 55)
        for i, nm in enumerate(names):
            sc.frame_set(i * 10 + 1)
            sc.render.filepath = f"{OUT}/cara_{i}_{nm}.png"
            bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam)
    if SOLO != "caras":
        setup_render(sc, 500, 900, 24, 100, 24)
        sc.frame_set(1)
        for nm, yaw in (("frente", 0), ("perfil", 90), ("espalda", 180)):
            p.root.rotation_euler = (0, 0, math.radians(yaw))
            cam = camara((0, -5.2, 1.3), (0, 0, 1.15), 42)
            sc.render.filepath = f"{OUT}/cuerpo_{nm}.png"
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(cam)


if __name__ == "__main__":
    main()
