"""Plano de prueba del estadio con personajes. Uso: python -m ytauto.b3d.demo_estadio SALIDA_DIR [frames]"""
from __future__ import annotations

import math
import sys
import time

import bpy
from mathutils import Vector

from .core import setup_render
from .escenario import GY, balon, estadio
from .personaje import Personaje

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/est"
FR = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [1]


def cam(loc, tgt, lens):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.active_object
    c.data.lens = lens
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = c
    return c


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    import os
    estadio(tmpdir=OUT, publico=os.environ.get("PUBLICO", "1") == "1")
    print("estadio", round(time.time() - t0, 1), "s", len(bpy.data.objects), "objetos")
    balon((0, 0, 0.11))
    yo = Personaje("yo", kit=(40, 110, 215), num="9", pelo="pinchos").build()
    yo.place((0.3, 1.2, 0), yaw=0)
    yo.expresion(1, "picaro")
    gk = Personaje("portero", kit=(255, 140, 30), num="1", pelo="rizos", guantes=True, pelo_col=(20, 14, 10),
                   piel=(170, 110, 75)).build()
    gk.place((0, GY + 0.4, 0), yaw=math.pi)
    gk.expresion(1, "enfadado")
    setup_render(sc, 540, 960, 24, 48, 20)
    views = {"detras": ((1.2, 5.5, 1.8), (0, GY, 1.6), 30), "lateral": ((9, -4, 1.6), (0, GY - 1, 2.2), 26),
             "portero": ((0.4, GY + 3.2, 1.7), (0, GY, 1.8), 40)}
    import os
    if os.environ.get("VISTAS"):
        views = {k: v for k, v in views.items() if k in os.environ["VISTAS"].split(",")}
    for nm, (l, t, lens) in views.items():
        t1 = time.time()
        cam(l, t, lens)
        for f in FR:
            sc.frame_set(f)
            sc.render.filepath = f"{OUT}/est_{nm}_{f:03d}.png"
            bpy.ops.render.render(write_still=True)
        print("vista", nm, round(time.time() - t1, 1), "s")
    print("total", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
