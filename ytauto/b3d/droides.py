"""Droides de «La Concentración»: cabeza metálica, visera negra, ojos rojos y antena. Originales."""
from __future__ import annotations

import random

import bpy
from mathutils import Vector

from .core import cube, key, limb, mat, pivot, sphere, srgb


def droide(n, loc, escala=1.0):
    """Busto de droide mirando a -Y. Devuelve (raíz, material de ojos, material de boca)."""
    metal = mat("droide_metal", srgb(70, 74, 84), 0.3, coat=0.7)
    oscuro = mat("droide_oscuro", srgb(30, 32, 38), 0.3, coat=0.8)
    ojos = mat(n + "_ojos", srgb(255, 30, 20), 0.3, emit=12.0)
    boca = mat(n + "_boca", srgb(255, 40, 30), 0.3, emit=6.0)
    r = pivot(n, (0, 0, 0))
    cube(n + "_cabeza", (0, 0, 1.65), (0.3, 0.27, 0.28), metal, r, bevel=0.08)
    cube(n + "_visera", (0, -0.27, 1.69), (0.25, 0.02, 0.1), oscuro, r, bevel=0.02)
    for sx in (-1, 1):
        sphere(f"{n}_ojo{sx}", (sx * 0.1, -0.29, 1.69), (0.05, 0.02, 0.035), ojos, r)
        cube(f"{n}_oreja{sx}", (sx * 0.32, 0, 1.65), (0.03, 0.1, 0.1), oscuro, r, bevel=0.02)
    cube(n + "_boca", (0, -0.275, 1.5), (0.12, 0.01, 0.016), boca, r)
    limb(n + "_antena", Vector((0.12, 0, 1.92)), Vector((0.16, 0, 2.15)), 0.012, oscuro, r)
    sphere(n + "_antena_luz", (0.16, 0, 2.16), (0.035,) * 3, ojos, r)
    cube(n + "_cuello", (0, 0, 1.33), (0.08, 0.08, 0.06), oscuro, r)
    cube(n + "_hombros", (0, 0, 1.08), (0.48, 0.24, 0.2), metal, r, bevel=0.08)
    cube(n + "_pecho", (0, -0.245, 1.08), (0.12, 0.01, 0.06), ojos, r)
    r.location = loc
    r.scale = (escala,) * 3
    return r, ojos, boca


def hablar_droide(boca, f0, f1, seed=1):
    """La barra de la boca se ilumina a golpes mientras habla."""
    s = boca.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    rng = random.Random(seed)
    s.default_value = 1.0
    s.keyframe_insert("default_value", frame=f0)
    for f in range(f0 + 2, f1, 3):
        s.default_value = rng.choice((2.0, 8.0, 14.0))
        s.keyframe_insert("default_value", frame=f)
    s.default_value = 1.0
    s.keyframe_insert("default_value", frame=f1)


def encender_ojos(ojos, f0, f1):
    s = ojos.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    s.default_value = 0.0
    s.keyframe_insert("default_value", frame=f0)
    s.default_value = 12.0
    s.keyframe_insert("default_value", frame=f1)
