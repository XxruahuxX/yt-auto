"""Serie «Todos tenemos un amigo que…», ep. 3 en 3D: el que se cree que tiene AURA.
Uso: python -m ytauto.b3d.video_aura SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import sys

import bpy
from mathutils import Vector

from .core import all_fcurves, cube, key, mat, pivot, setup_render, sphere, srgb
from .escenario import GY, balon, estadio
from .personaje import PELVIS_Z, Personaje
from .video_anime import arrodillado, aura_anim
from .video_penalti import FPS, F, bola, camera, chute, vida

LEJOS = (40, 60, 0)
ORO = (1.0, 0.45, 0.0)


# ------------------------------------------------------------------ reparto (pachanga: cada uno con su camiseta)
def AU():
    p = Personaje("au", kit=(28, 28, 34), num="7", pelo="raya", pelo_col=(240, 205, 110), piel=(235, 185, 150),
                  pantalon=(28, 28, 34), ribete=(255, 196, 40)).build()
    p.gafas = gafas(p)
    return p


def AM1():
    return Personaje("am1", kit=(40, 110, 215), num="9", pelo="pinchos").build()


def AM2():
    return Personaje("am2", kit=(30, 150, 80), num="5", pelo="rizos", pelo_col=(30, 20, 14),
                     piel=(170, 110, 75)).build()


def GK():
    return Personaje("gk", kit=(255, 140, 30), num="1", pelo="rapado", pelo_col=(25, 20, 18), guantes=True,
                     piel=(250, 210, 180)).build()


def gafas(p):
    """Gafas de sol colgadas del cuello (siguen a la cabeza). Devuelve el pivote para subirlas/bajarlas."""
    g = pivot(p.n + "_gafas", (0, 0, 1.92), p.neck)
    neg = mat("gafas_m", srgb(12, 12, 16), 0.08, coat=1.0)
    mont = mat("gafas_mont", srgb(25, 25, 30), 0.3)
    for sx in (-1, 1):
        sphere(f"{p.n}_lente{sx}", (sx * 0.125, -0.345, 1.968), (0.118, 0.028, 0.098), neg, g)
        cube(f"{p.n}_patilla{sx}", (sx * 0.272, -0.15, 1.99), (0.009, 0.12, 0.009), mont, g)
    cube(p.n + "_puente", (0, -0.36, 1.99), (0.035, 0.008, 0.01), mont, g)
    cube(p.n + "_barra", (0, -0.355, 2.045), (0.235, 0.01, 0.012), mont, g)
    return g


# ------------------------------------------------------------------ poses
def sentado(p, f):
    p.pose(f, hips=(-1.45, -1.3), knees=(0.5, 0.9), shoulders=((-0.5, 0.25), (-0.5, -0.25)), elbows=(-0.6, -0.6),
           lean=0.1, pelvis_z=-(PELVIS_Z - 0.16))


def facepalm(p, f):
    p.pose(f, shoulders=((0.05, 0.12), (-1.0, -0.9)), elbows=(-0.2, -2.4))
    p.cabeza(f, 0.0, 0.3, 0.0)


def impaciente(p, f0, f1):
    """Mira al cielo y golpea el suelo con el pie."""
    p.cabeza(f0, 0.1, -0.25, 0)
    p.mirar(f0, 0.1, 0.4)
    for i, f in enumerate(range(f0, f1, 6)):
        key(p.hip["R"], f, rotation_euler=(0.0 if i % 2 else -0.22, 0, 0))


def andar_chulo(p, f0, f1, p0, p1, yaw=0.0):
    """Paseo a cámara lenta: pasos largos y lentos, brazos sueltos."""
    p.correr(f0, f1, p0, p1, yaw=yaw, pasos_s=0.75, amp=0.38)
    for f in range(f0, f1 + 1, 2):
        s = (f - f0) / FPS
        key(p.torso, f, rotation_euler=(-0.06, 0, 0.1 * math.sin(2 * math.pi * 0.75 * s)))


# ------------------------------------------------------------------ escenas
def s_intro(sc, dur):
    a, m1, m2 = AU(), AM1(), AM2()
    a.expresion(1, "picaro")
    a.cabeza(1, 0, -0.1, 0)
    andar_chulo(a, 1, F(dur), (0, 7.0, 0), (0, 1.6, 0))
    for p, loc, yaw, s in ((m1, (-1.7, 0.2, 0), math.radians(160), 2), (m2, (1.8, 0.4, 0), math.radians(-160), 3)):
        p.place(loc, yaw, 1)
        p.reposo(1)
        p.expresion(1, "neutral")
        p.mirar(1, 0, 0.1)
        vida(p, dur, s)
    impaciente(m1, F(2.4), F(dur))
    m2.pose(F(2.6), shoulders=((0.25, 0.75), (0.25, -0.75)), elbows=(-1.5, -1.5))
    m2.cabeza(F(3.2), 0.0, 0.0, 0.18)
    m2.expresion(F(3.0), "triste")
    m1.expresion(F(3.0), "neutral")
    vida(a, dur, 1)
    camera(sc, "c1", 0, 2.6, (0.55, 3.6, 0.5), (0.45, 1.1, 0.5), None, lens=26,
           follow=bpy.data.objects["au_cabeza"])
    camera(sc, "c2", 2.6, dur, (0.0, -5.2, 1.4), (0.0, -4.6, 1.45), (0, 2.0, 1.2), (0, 1.8, 1.25), lens=30)


def s_medias(sc, dur):
    a, m1, m2 = AU(), AM1(), AM2()
    ball = balon((0.25, -0.45, 0.11))
    a.place((0, 0, 0), 0, 1)
    a.expresion(1, "picaro")
    for i, f in enumerate(range(1, F(2.9), 7)):              # se sube las medias, se las baja, se las vuelve a subir
        d = 0.18 if i % 2 else 0.0
        a.pose(f, hips=(-0.15, 0.0), knees=(0.25, 0.1), shoulders=((-1.05 - d, 0.15), (-1.05 - d, -0.15)),
               elbows=(-0.2, -0.2), lean=0.75, pelvis_z=-0.06 + 0.03 * (i % 2))
    a.cabeza(1, 0, 0.35, 0)
    a.reposo(F(3.3))
    a.cabeza(F(3.3), 0, -0.1, 0)
    a.pose(F(3.7), shoulders=((0.05, 0.12), (-0.4, -2.5)), elbows=(-0.2, -2.0))           # se peina
    a.pose(F(4.2), shoulders=((0.05, 0.12), (-0.4, -2.6)), elbows=(-0.2, -1.8))
    a.reposo(F(4.7))
    a.expresion(F(3.4), "feliz")
    # plano 2: los demás esperando
    t2 = 2.9
    a.place((0, 0, 0), 0, F(t2) - 1)
    a.place(LEJOS, 0, F(t2))
    for p in (m1, m2):
        p.place(LEJOS, 0, 1)
        p.place(LEJOS, 0, F(t2) - 1)
    m1.place((5.2, 0.0, 0), math.radians(25), F(t2))
    sentado(m1, F(t2))
    m1.expresion(F(t2), "triste")
    m1.cabeza(F(t2), 0.0, 0.15, 0.0)
    m2.place((6.3, 0.3, 0), math.radians(-20), F(t2))
    m2.reposo(F(t2))
    m2.expresion(F(t2), "enfadado")
    impaciente(m2, F(t2), F(dur))
    m2.pose(F(t2 + 0.6), shoulders=((0.25, 0.75), (0.25, -0.75)), elbows=(-1.5, -1.5))
    vida(a, t2, 4)
    vida(m1, dur, 5)
    vida(m2, dur, 6)
    camera(sc, "c1", 0, t2, (2.7, -2.3, 0.95), (2.5, -2.1, 1.0), (0, 0, 0.8), (0, 0, 0.9), lens=30)
    camera(sc, "c2", t2, dur, (5.75, -3.2, 1.2), (5.75, -2.9, 1.25), (5.75, 0.1, 1.1), lens=32)
    # el plano 1 recupera al aura cuando vuelve (no hace falta: la escena acaba en el plano 2)


def s_celebra(sc, dur):
    a, m1 = AU(), AM1()
    ball = balon((0.5, GY + 8.6, 0.11))
    # el 9 chuta y marca
    m1.place((0.6, GY + 9.2, 0), 0, 1)
    m1.reposo(1)
    m1.expresion(1, "enfadado")
    chute(m1, F(0.25), (0.6, GY + 9.0, 0), 0.0)
    tb = 0.25 + 3 / FPS
    bola(ball, F(tb), (0.5, GY + 8.6, 0.11))
    bola(ball, F(tb + 0.55), (-1.6, GY - 0.6, 1.4), (-25, 0, 0))
    bola(ball, F(tb + 0.8), (-1.7, GY - 1.6, 0.8))
    bola(ball, F(tb + 1.2), (-1.7, GY - 1.7, 0.11))
    m1.expresion(F(1.0), "feliz")
    m1.pose(F(1.1), shoulders=((0.0, 2.4), (0.0, -2.4)), elbows=(-0.3, -0.3))
    # el aura sale disparado a celebrarlo... y se tira de rodillas
    a.expresion(1, "picaro")
    a.place((3.2, GY + 12.0, 0), math.radians(180), 1)
    a.reposo(1)
    ts = 2.4
    a.correr(F(0.7), F(ts), (3.2, GY + 12.0, 0), (1.7, GY + 6.6, 0), yaw=math.radians(-15), pasos_s=3.0)
    a.expresion(F(0.9), "grito")
    a.place((1.7, GY + 6.6, 0), math.radians(-15), F(ts))
    arrodillado(a, F(ts + 0.1), lean=-0.25)
    a.pose(F(ts + 0.15), hips=(-0.15, -0.15), knees=(1.6, 1.6), shoulders=((0.0, 2.5), (0.0, -2.5)),
           elbows=(-0.2, -0.2), lean=-0.3, pelvis_z=-0.31)
    a.place((1.45, GY + 5.3, 0), math.radians(-15), F(ts + 0.6))
    a.cabeza(F(ts + 0.2), 0, -0.3, 0)
    # el 9 se señala: «¿perdona? el gol es mío»
    m1.expresion(F(2.2), "sorpresa")
    m1.pose(F(2.4), shoulders=((0.05, 0.12), (-1.0, -0.2)), elbows=(-0.2, -1.6))
    m1.place((0.6, GY + 9.0, 0), math.radians(-150), F(2.2))
    vida(m1, dur, 7)
    vida(a, dur, 8, skip=[(0.8, dur)])
    camera(sc, "c1", 0, 1.3, (2.4, GY + 13.5, 1.6), (2.0, GY + 13.0, 1.6), (0, GY, 1.0), lens=28)
    camera(sc, "c2", 1.3, dur, (0.6, GY + 3.2, 0.9), (0.7, GY + 3.5, 0.9), (2.2, GY + 8.0, 1.0), (1.6, GY + 6.0, 1.0),
           lens=28)


def s_panenka(sc, dur):
    a, g = AU(), GK()
    ball = balon((0, GY + 11, 0.11))
    g.place((0, GY + 0.45, 0), math.pi, 1)
    g.reposo(1)
    g.expresion(1, "neutral")
    a.place((0.9, GY + 13.6, 0), math.radians(-170), 1)
    a.reposo(1)
    a.expresion(1, "picaro")
    a.correr(F(0.15), F(0.85), (0.9, GY + 13.6, 0), (0.25, GY + 11.45, 0), yaw=math.radians(-170), pasos_s=2.2)
    # Panenka: toque suave por debajo
    a.place((0.15, GY + 11.4, 0), math.pi, F(0.9))
    a.pose(F(0.9), hips=(-0.1, 0.5), knees=(0.1, 0.9), shoulders=((0.2, 0.9), (0.2, -0.9)), elbows=(-0.3, -0.3))
    a.pose(F(1.05), hips=(-0.1, -0.5), knees=(0.1, 0.1), shoulders=((0.1, 1.2), (0.1, -1.2)), elbows=(-0.3, -0.3),
           lean=-0.12)
    a.reposo(F(1.6))
    tk = 1.0
    bola(ball, F(tk), (0, GY + 11, 0.11), (0, 0, 0))
    for j in range(1, 9):
        u = j / 8
        p = Vector((0, GY + 11, 0.11)).lerp(Vector((0, GY + 0.75, 1.3)), u)
        p.z += math.sin(u * math.pi) * 2.0
        bola(ball, F(tk + 1.4 * u), tuple(p), (-u * 3, 0, 0))
    for f in range(F(tk + 1.4), F(dur) + 1, 6):
        bola(ball, f, (0, GY + 0.75, 1.3), (-3, 0, 0))
    # el portero ni se mueve: la coge
    g.pose(F(tk + 1.15), shoulders=((-1.3, 0.25), (-1.3, -0.25)), elbows=(-0.7, -0.7))
    g.mirar(F(tk + 0.4), 0, 0.45)
    g.mirar(F(tk + 1.3), 0, 0)
    g.expresion(F(tk + 1.6), "picaro")
    g.cabeza(F(tk + 1.8), 0.0, 0.0, 0.15)
    a.expresion(F(tk + 1.5), "sorpresa")
    vida(a, dur, 9)
    vida(g, dur, 10)
    camera(sc, "c1", 0, 1.7, (0.9, GY + 16.5, 1.7), (0.8, GY + 15.8, 1.6), (0, GY, 1.3), lens=30)
    camera(sc, "c2", 1.7, dur, (1.4, GY + 3.4, 1.55), (1.3, GY + 3.1, 1.55), (0, GY + 0.6, 1.45), lens=34)


def s_cierre(sc, dur):
    a, m1, m2 = AU(), AM1(), AM2()
    a.place((0, 0, 0), 0, 1)
    a.reposo(1)
    a.expresion(1, "triste")
    # se vuelve a poner las gafas: de la frente a los ojos
    key(a.gafas, 1, location=Vector((0, 0.04, 2.1)), rotation_euler=(-0.4, 0, 0))
    key(a.gafas, F(0.5), location=Vector((0, 0.04, 2.1)), rotation_euler=(-0.5, 0, 0))
    key(a.gafas, F(0.95), location=Vector((0, 0, 1.92)), rotation_euler=(0, 0, 0))
    a.pose(F(0.4), shoulders=((-0.5, 2.3), (-0.5, -2.3)), elbows=(-1.6, -1.6))
    a.pose(F(1.0), shoulders=((-0.3, 2.0), (-0.3, -2.0)), elbows=(-1.9, -1.9))
    a.expresion(F(1.0), "picaro")
    a.reposo(F(1.4))
    a.pose(F(1.9), shoulders=((0.05, 0.12), (-1.45, -0.1)), elbows=(-0.2, 0.0))          # te señala a ti
    a.cabeza(F(1.9), 0.0, -0.08, 0.1)
    aura_anim((0, 0, 0), F(1.3), F(1.8), cam_dir=(0, -1), seed=11, col=ORO, height=2.1)
    for p, loc, yaw, s in ((m1, (-1.05, 1.5, 0), math.radians(12), 12), (m2, (1.1, 1.6, 0), math.radians(-12), 13)):
        p.place(loc, yaw, 1)
        p.reposo(1)
        p.expresion(1, "neutral")
        p.expresion(F(1.6), "triste")
        facepalm(p, F(1.7))
        vida(p, dur, s)
    vida(a, dur, 14)
    camera(sc, "c1", 0, dur, (0.25, -3.0, 1.55), (0.2, -2.6, 1.6), (0, 0.5, 1.55), (0, 0.5, 1.65), lens=30)


ESCENAS = {"intro": s_intro, "medias": s_medias, "celebra": s_celebra, "panenka": s_panenka, "cierre": s_cierre}


def main():
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    rw, rh = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (576, 1024)
    only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ESCENAS[name](sc, dur)
    estadio(tmpdir=out)
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
    setup_render(sc, rw, rh, FPS, F(dur), 14)
    sc.cycles.transparent_max_bounces = 64
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
