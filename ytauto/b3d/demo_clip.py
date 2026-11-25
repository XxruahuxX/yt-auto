"""Clip de prueba (≈9,5 s): penalti con expresiones, 7 planos con corte seco, estadio con público.
Uso: python -m ytauto.b3d.demo_clip SALIDA_DIR [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import sys

import bpy
from mathutils import Vector

from .core import all_fcurves, key, setup_render
from .escenario import GH, GW, GY, balon, estadio
from .personaje import PELVIS_Z, Personaje

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/clip"
RW, RH = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (540, 960)
ONLY = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
FPS, SECS = 24, 9.5
F = lambda s: int(round(1 + s * FPS))


def camera(sc, nm, t0, t1, p0, p1, tgt0, tgt1=None, lens=30, follow=None):
    bpy.ops.object.camera_add()
    cm = bpy.context.active_object
    cm.name = nm
    cm.data.lens = lens
    c = cm.constraints.new("TRACK_TO")
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    if follow is not None:
        c.target = follow
    else:
        bpy.ops.object.empty_add(location=tgt0)
        tr = bpy.context.active_object
        tr.name = nm + "_mira"
        c.target = tr
        key(tr, F(t0), location=Vector(tgt0))
        key(tr, F(t1), location=Vector(tgt1 or tgt0))
    key(cm, F(t0), location=Vector(p0))
    key(cm, F(t1), location=Vector(p1))
    mk = sc.timeline_markers.new(nm, frame=F(t0))
    mk.camera = cm
    if t0 == 0:
        sc.camera = cm
    return cm


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    # personajes primero (crear objetos con miles de aficionados en escena es más lento)
    yo = Personaje("yo", kit=(40, 110, 215), num="9", pelo="pinchos").build()
    gk = Personaje("portero", kit=(255, 140, 30), num="1", pelo="rizos", guantes=True, pelo_col=(20, 14, 10),
                   piel=(170, 110, 75)).build()
    ball = balon((0, 0, 0.11))
    estadio(tmpdir=OUT)
    N = F(SECS)

    # ---------------- lanzador
    start, spot = (0.9, 4.2, 0), (0.12, 0.42, 0)
    t_run, t_kick = 2.6, 4.0
    yo.place(start, 0, 1)
    yo.reposo(1)
    yo.expresion(1, "picaro")
    yo.mirar(1, 0.0, 0.05)
    yo.cabeza(1, 0, 0.05, 0.08)
    yo.parpadeo(F(0.7))
    yo.cabeza(F(1.2), 0, 0.0, 0.0)
    yo.reposo(F(t_run - 0.1))
    yo.place(start, 0, F(t_run - 0.1))
    yo.expresion(F(t_run), "enfadado")      # concentrado
    yo.correr(F(t_run), F(t_kick - 0.15), start, (0.2, 0.75, 0), yaw=math.radians(-8), pasos_s=2.2)
    # chute: pierna atrás, contacto, acompañar
    kp = (0.15, 0.62, 0)
    yo.place(kp, math.radians(-8), F(t_kick - 0.1))
    yo.pose(F(t_kick - 0.1), hips=(-0.2, 1.0), knees=(0.2, 1.5), shoulders=((-0.2, 1.0), (0.3, -1.1)),
            elbows=(-0.4, -0.4), lean=0.05)
    yo.pose(F(t_kick), hips=(-0.1, -0.6), knees=(0.15, 0.2), shoulders=((-0.3, 1.1), (0.2, -1.1)), elbows=(-0.4, -0.4),
            lean=-0.1)
    yo.pose(F(t_kick + 0.3), hips=(0.0, -1.3), knees=(0.1, 0.3), shoulders=((-0.2, 0.9), (0.2, -0.9)), elbows=(-0.4, -0.4),
            lean=-0.2)
    yo.place((0.1, 0.4, 0), math.radians(-8), F(t_kick + 0.3))
    yo.reposo(F(t_kick + 0.8))
    yo.expresion(F(t_kick + 0.6), "sorpresa")
    # celebración: corre hacia la cámara gritando con los brazos arriba
    t_cel = 5.8
    yo.place((0.1, 0.4, 0), 0, F(t_cel - 0.05))
    yo.expresion(F(t_cel), "grito")
    for f in range(F(t_cel), F(8.0) + 1, 2):
        u = (f - F(t_cel)) / (F(8.0) - F(t_cel))
        fase = 2 * math.pi * 2.4 * (f - F(t_cel)) / FPS
        yo.place((0.1 + 0.4 * u, 0.4 - 2.6 * u, 0.12 * abs(math.sin(fase))), 0, f)
        yo.zancada(f, fase, 0.7)
        sw = 0.25 * math.sin(fase * 2)
        for nm, sg in (("L", 1), ("R", -1)):
            key(yo.sh[nm], f, rotation_euler=(0.0, sg * (2.7 + sw), 0))
            key(yo.el[nm], f, rotation_euler=(-0.3, 0, 0))
    yo.expresion(F(7.2), "feliz")
    yo.parpadeo(F(7.5))
    yo.respirar(1, N)

    # ---------------- portero (mira hacia +y)
    gp = (0, GY + 0.45, 0)
    gk.place(gp, math.pi, 1)
    gk.pose(1, hips=(0.0, 0.0), knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25,
            pelvis_z=-0.08)
    gk.expresion(1, "enfadado")
    gk.mirar(1, 0.0, 0.0)
    for i, f in enumerate(range(1, F(t_kick) + 1, 6)):
        s = f / FPS
        x = 0.35 * math.sin(s * 2.6)
        gk.place((x, gp[1], 0.03 * abs(math.sin(s * 5.2))), math.pi, f)
        wave = 0.25 * math.sin(s * 5.2)
        gk.pose(f, hips=(0, 0), knees=(0.35, 0.35), shoulders=((0, 1.0 + wave), (0, -1.0 + wave)), elbows=(-0.3, -0.3),
                lean=0.25, pelvis_z=-0.08)
    gk.expresion(F(1.6), "grito")             # le grita al lanzador
    gk.expresion(F(2.3), "enfadado")
    gk.parpadeo(F(2.0))
    # estirada a su izquierda (+x del mundo)
    t_dive = t_kick + 0.12
    gk.place((0.2, gp[1], 0), math.pi, F(t_dive))
    gk.root.rotation_mode = "XYZ"
    key(gk.root, F(t_dive + 0.4), location=Vector((1.9, gp[1], 1.15)), rotation_euler=(0, math.radians(-78), math.pi))
    key(gk.root, F(t_dive + 0.95), location=Vector((2.5, gp[1] + 0.1, 0.35)), rotation_euler=(0, math.radians(-90), math.pi))
    gk.pose(F(t_dive + 0.35), hips=(0.1, -0.1), knees=(0.2, 0.4), shoulders=((0, 2.8), (0, -2.8)), elbows=(0, 0))
    gk.expresion(F(t_dive + 0.2), "sorpresa")
    gk.expresion(F(t_dive + 1.0), "triste")
    # sentado en el césped, hundido
    t_sad = 8.0
    sit = (1.7, GY + 0.9, 0)
    key(gk.root, F(t_sad - 0.05), location=Vector(sit), rotation_euler=(0, 0, math.pi + 0.3))
    gk.pose(F(t_sad - 0.05), hips=(-1.45, -1.3), knees=(0.5, 0.9), shoulders=((-0.6, 0.25), (-0.6, -0.25)),
            elbows=(-0.6, -0.6), lean=0.12, pelvis_z=-(PELVIS_Z - 0.16))
    gk.cabeza(F(t_sad - 0.05), 0, 0.1, 0)
    gk.cabeza(F(9.2), 0.12, 0.15, -0.08)
    gk.expresion(F(t_sad - 0.05), "triste")
    gk.mirar(F(t_sad - 0.05), 0, -0.25)
    gk.parpadeo(F(8.7), 6)
    gk.respirar(1, N)

    # ---------------- balón a la escuadra
    key(ball, F(t_kick), location=Vector((0, 0, 0.11)))
    tgt = Vector((GW - 0.45, GY - 0.05, GH - 0.35))
    p0 = Vector((0, 0, 0.11))
    for j in range(1, 9):
        u = j / 8
        p = p0.lerp(tgt, u)
        p.z += math.sin(u * math.pi) * 0.5
        key(ball, F(t_kick + 0.62 * u), location=p)
    key(ball, F(t_kick + 0.95), location=Vector((GW - 0.6, GY - 1.25, 1.3)))
    key(ball, F(t_kick + 1.35), location=Vector((GW - 0.8, GY - 1.35, 0.11)))
    key(ball, F(t_kick + 2.2), location=Vector((GW - 1.1, GY - 1.2, 0.11)))
    ball.rotation_mode = "XYZ"
    key(ball, F(t_kick), rotation_euler=(0, 0, 0))
    key(ball, F(t_kick + 1.4), rotation_euler=(-25, 6, 2))

    # ---------------- cámaras (7 planos)
    camera(sc, "c1_cara", 0, 1.4, (1.2, 2.3, 1.85), (1.1, 2.6, 1.85), (0.9, 4.2, 1.7), lens=36)
    camera(sc, "c2_portero", 1.4, t_run, (0.2, GY + 3.9, 1.55), (0.1, GY + 3.5, 1.6), (0, GY + 0.45, 1.5), lens=36)
    camera(sc, "c3_carrera", t_run, t_kick - 0.15, (2.0, 7.4, 2.0), (1.2, 4.2, 1.5), (0, -2, 1.0), (0, -5, 1.1), lens=28)
    camera(sc, "c4_chute", t_kick - 0.15, t_kick + 0.35, (2.2, -1.3, 0.35), (2.0, -1.4, 0.4), (0.1, 0.5, 0.85), lens=20)
    camera(sc, "c5_gol", t_kick + 0.35, 5.8, (7.0, GY + 2.2, 1.3), (6.4, GY + 1.6, 1.4), (2.2, GY - 0.2, 1.4),
           (2.6, GY - 0.6, 1.0), lens=30)
    camera(sc, "c6_celebra", 5.8, 8.0, (0.5, -2.2, 1.75), (0.7, -3.6, 1.85), None, lens=32,
           follow=bpy.data.objects["yo_cabeza"])
    camera(sc, "c7_triste", 8.0, SECS, (2.4, GY + 3.3, 0.75), (2.3, GY + 3.0, 0.75), (1.7, GY + 0.9, 1.0), lens=36)

    for o in bpy.data.objects:
        for fc in all_fcurves(o):
            if fc.modifiers:
                continue
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
    setup_render(sc, RW, RH, FPS, N, 16)
    if ONLY:
        for fr in ONLY:
            sc.frame_set(fr)
            sc.render.filepath = f"{OUT}/s_{fr:04d}.png"
            bpy.ops.render.render(write_still=True)
    else:
        sc.render.filepath = OUT + "/f_"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
