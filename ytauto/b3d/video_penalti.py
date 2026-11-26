"""«Así se inventó el penalti» en 3D. Cada escena se renderiza en su propio proceso de Blender.
Uso: python -m ytauto.b3d.video_penalti SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]
Las imágenes quedan en SALIDA_DIR/x_3d_<escena>/f_0001.png ... (24 fps)."""
from __future__ import annotations

import math
import random
import sys

import bpy
from mathutils import Vector

from .core import all_fcurves, key, setup_render
from .escenario import GH, GW, GY, balon, estadio
from .personaje import PELVIS_Z, Personaje

FPS = 24
F = lambda s: int(round(1 + s * FPS))


# ------------------------------------------------------------------ utilidades
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


def vida(p, dur, seed, skip=()):
    """Parpadeos cada 2-4 s y respiración. skip: intervalos (t0, t1) sin parpadeo."""
    rng = random.Random(seed)
    t = rng.uniform(0.4, 1.4)
    while t < dur - 0.3:
        if not any(a - 0.25 <= t <= b for a, b in skip):
            p.parpadeo(F(t), 4)
        t += rng.uniform(2.0, 3.8)
    p.respirar(1, F(dur))


def chute(p, f0, loc, yaw=0.0):
    """Pierna atrás (f0), contacto (f0+3), acompañar (f0+9)."""
    p.place(loc, yaw, f0)
    p.pose(f0, hips=(-0.2, 1.0), knees=(0.2, 1.5), shoulders=((-0.2, 1.0), (0.3, -1.1)), elbows=(-0.4, -0.4), lean=0.05)
    p.pose(f0 + 3, hips=(-0.1, -0.6), knees=(0.15, 0.2), shoulders=((-0.3, 1.1), (0.2, -1.1)), elbows=(-0.4, -0.4),
           lean=-0.1)
    p.pose(f0 + 9, hips=(0.0, -1.3), knees=(0.1, 0.3), shoulders=((-0.2, 0.9), (0.2, -0.9)), elbows=(-0.4, -0.4),
           lean=-0.2)


def celebrar(p, f0, f1, p0, p1, yaw=0.0):
    p0, p1 = Vector(p0), Vector(p1)
    for f in range(f0, f1 + 1, 2):
        u = (f - f0) / max(1, f1 - f0)
        fase = 2 * math.pi * 2.4 * (f - f0) / FPS
        q = p0.lerp(p1, u)
        p.place((q.x, q.y, 0.12 * abs(math.sin(fase))), yaw, f)
        p.zancada(f, fase, 0.6)
        sw = 0.25 * math.sin(fase * 2)
        for nm, sg in (("L", 1), ("R", -1)):
            key(p.sh[nm], f, rotation_euler=(0.0, sg * (2.7 + sw), 0))
            key(p.el[nm], f, rotation_euler=(-0.3, 0, 0))


def encoger(p, f):
    """Encogerse de hombros: palmas arriba."""
    p.pose(f, shoulders=((-0.5, 0.5), (-0.5, -0.5)), elbows=(-1.4, -1.4))


def brazos_cruzados(p, f):
    p.pose(f, shoulders=((-0.75, -0.25), (-0.75, 0.25)), elbows=(-1.9, -1.9))


def jarras(p, f):
    p.pose(f, shoulders=((0.25, 0.75), (0.25, -0.75)), elbows=(-1.5, -1.5))


def bola(ball, f, loc, spin=None):
    key(ball, f, location=Vector(loc))
    if spin is not None:
        ball.rotation_mode = "XYZ"
        key(ball, f, rotation_euler=spin)


# ------------------------------------------------------------------ personajes
def P_del():
    return Personaje("del", kit=(40, 110, 215), num="9", pelo="pinchos").build()


def P_def():
    return Personaje("def", kit=(200, 30, 45), num="4", pelo="raya", pelo_col=(190, 120, 50),
                     piel=(255, 215, 185)).build()


def P_gk():
    return Personaje("gk", kit=(255, 140, 30), num="1", pelo="rizos", guantes=True, pelo_col=(20, 14, 10),
                     piel=(170, 110, 75)).build()


def P_mc():
    # portero irlandés de 1890 (sin guantes): personaje genérico, no un retrato
    return Personaje("mc", kit=(30, 150, 80), num="1", pelo="rapado", pelo_col=(120, 60, 30),
                     piel=(255, 214, 190), ojos=(60, 110, 70)).build()


def P_cab(n="cab", pelo="rapado", pc=(25, 20, 18), piel=(240, 200, 170)):
    return Personaje(n, kit=(245, 245, 245), num="2", pelo=pelo, pelo_col=pc, piel=piel, pantalon=(25, 25, 30),
                     medias=(25, 25, 30), ribete=(25, 25, 30)).build()


# ------------------------------------------------------------------ escenas
def s_gancho(sc, dur):
    d, m = P_del(), P_def()
    ball = balon()
    tf = 1.55
    d.expresion(1, "enfadado")
    d.correr(1, F(tf), (0.2, 9.5, 0), (0.1, 4.6, 0), pasos_s=2.6)
    for f in range(1, F(tf) + 1, 2):
        u = (f - 1) / (F(tf) - 1)
        y = 9.5 - 4.9 * u - 0.75
        bola(ball, f, (0.1, y, 0.11 + 0.05 * abs(math.sin(u * 12))), (-u * 30, 0, 0))
    m.expresion(1, "picaro")
    m.correr(1, F(tf - 0.2), (3.2, 7.5, 0), (0.75, 5.0, 0), yaw=math.radians(-55), pasos_s=2.8)
    # entrada: pierna por delante, barriendo
    m.place((0.55, 4.9, 0), math.radians(-70), F(tf))
    m.pose(F(tf), hips=(-0.2, -1.3), knees=(0.6, 0.1), shoulders=((0.3, 1.2), (0.3, -1.2)), elbows=(-0.3, -0.3),
           lean=-0.4, pelvis_z=-0.25)
    # el delantero sale volando hacia delante
    d.root.rotation_mode = "XYZ"
    d.expresion(F(tf), "sorpresa")
    key(d.root, F(tf), location=Vector((0.1, 4.6, 0)), rotation_euler=(0, 0, 0))
    key(d.root, F(tf + 0.3), location=Vector((0.1, 3.6, 0.5)), rotation_euler=(math.radians(60), 0, 0))
    key(d.root, F(tf + 0.6), location=Vector((0.1, 3.1, 0.0)), rotation_euler=(math.radians(88), 0, 0))
    d.pose(F(tf + 0.3), hips=(0.6, -0.4), knees=(0.8, 0.4), shoulders=((0.2, 2.4), (0.2, -2.4)), elbows=(0, 0))
    d.expresion(F(tf + 0.35), "grito")
    bola(ball, F(tf), (0.1, 3.85, 0.11))
    bola(ball, F(tf + 1.2), (-0.8, 0.5, 0.11), (-40, 0, 0))
    # el defensa se levanta silbando
    m.place((0.55, 4.9, 0), math.radians(-70), F(tf + 0.7))
    m.reposo(F(tf + 1.1))
    m.place((0.9, 5.2, 0), math.radians(160), F(tf + 1.1))
    m.cabeza(F(tf + 1.1), 0.0, -0.2, 0.15)
    m.mirar(F(tf + 1.1), 0.4, 0.25)
    m.place((0.7, 6.1, 0), math.radians(170), F(dur))
    vida(d, dur, 1, skip=[(tf - 0.2, tf + 0.8)])
    vida(m, dur, 2)
    camera(sc, "c1", 0, 2.1, (4.2, 9.0, 1.6), (4.0, 3.2, 1.4), None, lens=26, follow=bpy.data.objects["del_cuerpo"])
    camera(sc, "c2", 2.1, dur, (0.1, 8.6, 1.8), (0.0, 8.2, 1.8), (0.9, 5.2, 1.6), (0.7, 6.1, 1.6), lens=30)


def s_caza(sc, dur):
    d, m, g = P_del(), P_def(), P_gk()
    ball = balon()
    g.place((0, GY + 0.5, 0), math.pi, 1)
    g.pose(1, knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25, pelvis_z=-0.08)
    g.expresion(1, "sorpresa")
    tf = 2.4
    d.expresion(1, "feliz")
    d.correr(1, F(tf), (0.0, 6.0, 0), (0.0, -1.5, 0), pasos_s=2.8)
    for f in range(1, F(tf) + 1, 2):
        u = (f - 1) / (F(tf) - 1)
        bola(ball, f, (0.05, 6.0 - 7.5 * u - 0.8, 0.11 + 0.05 * abs(math.sin(u * 16))), (-u * 40, 0, 0))
    m.expresion(1, "enfadado")
    m.correr(1, F(tf), (0.6, 8.3, 0), (0.35, -0.6, 0), pasos_s=3.0)
    m.place((0.3, -0.9, 0), 0, F(tf + 0.05))
    m.pose(F(tf + 0.05), hips=(-0.3, -1.2), knees=(0.5, 0.1), shoulders=((0.3, 1.1), (0.3, -1.1)), elbows=(-0.3, -0.3),
           lean=-0.3, pelvis_z=-0.2)
    m.expresion(F(tf + 0.1), "picaro")
    d.root.rotation_mode = "XYZ"
    key(d.root, F(tf), location=Vector((0.0, -1.5, 0)), rotation_euler=(0, 0, 0))
    key(d.root, F(tf + 0.35), location=Vector((0.0, -2.6, 0.3)), rotation_euler=(math.radians(70), 0, 0))
    key(d.root, F(tf + 0.6), location=Vector((0.0, -3.0, 0.0)), rotation_euler=(math.radians(88), 0, 0))
    d.expresion(F(tf + 0.05), "grito")
    bola(ball, F(tf), (0.05, -2.3, 0.11))
    bola(ball, F(tf + 1.0), (-1.2, -5.0, 0.11), (-30, 0, 0))
    # plano 2: sentado en el césped, mosqueado; el defensa se encoge de hombros
    t2 = 3.3
    key(d.root, F(t2), location=Vector((0.0, -2.0, 0)), rotation_euler=(0, 0, 0))
    d.pose(F(t2), hips=(-1.45, -1.3), knees=(0.5, 0.9), shoulders=((-0.5, 0.25), (-0.5, -0.25)),
           elbows=(-0.6, -0.6), lean=0.1, pelvis_z=-(PELVIS_Z - 0.16))
    d.expresion(F(t2), "enfadado")
    d.cabeza(F(t2), -0.35, -0.1, 0)
    d.mirar(F(t2), -0.35, 0.15)
    m.place((-0.9, -2.3, 0), math.radians(-20), F(t2))
    m.reposo(F(t2))
    m.expresion(F(t2), "picaro")
    encoger(m, F(t2 + 0.6))
    m.cabeza(F(t2 + 0.6), 0.0, 0.0, 0.18)
    encoger(m, F(t2 + 2.2))
    m.reposo(F(t2 + 2.8))
    m.expresion(F(t2 + 2.0), "feliz")
    vida(d, dur, 3, skip=[(tf - 0.2, tf + 0.8)])
    vida(m, dur, 4)
    vida(g, dur, 5)
    camera(sc, "c1", 0, t2, (2.2, 9.0, 1.9), (1.4, 2.0, 1.6), (0, 0, 1.0), (0, -4, 0.9), lens=28)
    camera(sc, "c2", t2, dur, (-0.7, -5.4, 1.2), (-0.6, -5.0, 1.25), (-0.4, -2.1, 1.0), lens=30)


def s_mccrum(sc, dur):
    mc = P_mc()
    mc.place((0, GY + 0.6, 0), math.pi, 1)
    mc.reposo(1)
    mc.expresion(1, "enfadado")
    jarras(mc, F(0.3))
    for i, t in enumerate((0.5, 0.9, 1.3, 1.7)):
        mc.cabeza(F(t), 0.35 * (1 if i % 2 else -1), 0.05, 0)
    mc.cabeza(F(2.0), 0, 0, 0)
    mc.expresion(F(2.0), "grito")
    mc.pose(F(2.3), shoulders=((0, 2.6), (0, -2.6)), elbows=(-0.4, -0.4))
    mc.pose(F(2.7), shoulders=((0, 2.3), (0, -2.3)), elbows=(-0.6, -0.6))
    mc.pose(F(3.1), shoulders=((0, 2.6), (0, -2.6)), elbows=(-0.4, -0.4))
    vida(mc, dur, 6, skip=[(1.9, 3.2)])
    camera(sc, "c1", 0, dur, (0.35, GY + 3.2, 1.75), (0.25, GY + 2.6, 1.8), (0, GY + 0.6, 1.65), lens=34)


def s_idea(sc, dur):
    mc, d, g = P_mc(), P_del(), P_gk()
    ball = balon((0, 0, 0.11))
    # plano 1: se le enciende la bombilla
    mc.place((0, GY + 6.0, 0), math.pi, 1)
    mc.reposo(1)
    mc.expresion(1, "neutral")
    mc.mirar(1, 0.3, 0.35)
    mc.cabeza(1, 0.1, -0.15, 0.1)
    mc.expresion(F(0.7), "sorpresa")
    mc.pose(F(0.9), shoulders=((0.05, 0.12), (-0.2, -2.9)), elbows=(-0.2, 0.0))
    mc.expresion(F(1.3), "feliz")
    mc.mirar(F(1.0), 0, 0)
    mc.cabeza(F(1.0), 0, 0, 0)
    # plano 2: doce yardas, solo tú contra el portero
    mc.place((40, 60, 0), 0, F(2.3))       # fuera de plano tras el corte
    d.place((0.2, 1.4, 0), 0, 1)
    d.reposo(1)
    d.expresion(1, "picaro")
    g.place((0, GY + 0.45, 0), math.pi, 1)
    g.pose(1, knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25, pelvis_z=-0.08)
    g.expresion(1, "sorpresa")
    for f in range(F(2.3), F(dur) + 1, 6):
        s = f / FPS
        g.place((0.3 * math.sin(s * 2.4), GY + 0.45, 0), math.pi, f)
    # línea amarilla de 11 m que se dibuja desde la línea de gol hasta el punto
    from .core import mat, srgb
    bpy.ops.mesh.primitive_plane_add(location=(0, GY, 0.012))
    ln = bpy.context.active_object
    ln.data.materials.append(mat("doce", srgb(255, 215, 40), 0.4, emit=2.5))
    ln.data.vertices.foreach_set("co", [-0.08, 0, 0, 0.08, 0, 0, -0.08, 1, 0, 0.08, 1, 0])
    ln.data.update()
    key(ln, F(2.6), scale=(1, 0.001, 1))
    key(ln, F(3.6), scale=(1, -GY - 0.15, 1))
    vida(mc, 2.3, 7, skip=[(0.6, 1.4)])
    vida(d, dur, 8)
    vida(g, dur, 9)
    camera(sc, "c1", 0, 2.3, (0.3, GY + 8.4, 1.8), (0.25, GY + 7.9, 1.8), (0, GY + 6.0, 1.75), lens=34)
    camera(sc, "c2", 2.3, dur, (2.6, 5.6, 4.2), (1.8, 4.6, 3.6), (0, -4.0, 0.6), (0, -5.0, 0.8), lens=26)


def s_insulto(sc, dur):
    a = P_cab("cab", "rapado", (25, 20, 18), (240, 200, 170))
    b = P_cab("cab2", "raya", (200, 150, 70), (255, 220, 195))
    a.place((-0.45, 0, 0), math.radians(8), 1)
    b.place((0.55, 0.3, 0), math.radians(-10), 1)
    for p in (a, b):
        p.reposo(1)
        p.expresion(1, "neutral")
    a.expresion(F(1.2), "sorpresa")
    b.expresion(F(1.4), "sorpresa")
    a.mirar(F(1.2), -0.3, 0)
    b.mirar(F(1.4), 0.35, 0)
    a.cabeza(F(1.6), -0.3, 0, 0)
    b.cabeza(F(1.8), 0.3, 0, 0)
    a.expresion(F(2.6), "enfadado")
    b.expresion(F(2.8), "enfadado")
    jarras(a, F(2.8))
    brazos_cruzados(b, F(3.0))
    # «un caballero no hace faltas a propósito»: barbilla arriba, ofendidísimo
    t3 = 4.4
    a.cabeza(F(t3), 0, -0.28, 0.06)
    a.mirar(F(t3), 0, -0.2)
    a.expresion(F(t3), "picaro")
    brazos_cruzados(a, F(t3 + 0.3))
    a.cabeza(F(dur), 0.08, -0.3, 0.06)
    b.cabeza(F(t3 + 0.4), 0, -0.25, -0.05)
    b.cabeza(F(t3 + 0.8), 0, -0.1, -0.05)
    b.cabeza(F(t3 + 1.2), 0, -0.25, -0.05)
    vida(a, dur, 10, skip=[(1.1, 1.7)])
    vida(b, dur, 11, skip=[(1.3, 1.9)])
    camera(sc, "c1", 0, t3, (0.1, -3.4, 1.55), (0.05, -2.9, 1.6), (0.05, 0.1, 1.5), lens=32)
    camera(sc, "c2", t3, dur, (-0.3, -2.3, 1.6), (-0.35, -2.0, 1.65), (-0.45, 0, 1.75), lens=34)


def s_fallo(sc, dur):
    a = P_cab("cab", "rapado", (25, 20, 18), (240, 200, 170))
    k = P_cab("cabgk", "raya", (200, 150, 70), (255, 220, 195))
    d = P_del()
    g = P_gk()
    ball = balon((0, 0, 0.11))
    # plano 1: el caballero lo tira fuera aposta
    a.expresion(1, "picaro")
    a.place((0.7, 2.6, 0), 0, 1)
    a.reposo(1)
    a.correr(F(0.3), F(1.0), (0.7, 2.6, 0), (0.25, 0.75, 0), yaw=math.radians(-10), pasos_s=2.0)
    chute(a, F(1.05), (0.15, 0.6, 0), math.radians(-10))
    a.reposo(F(1.9))
    a.cabeza(F(2.0), 0, -0.2, 0.1)
    g.place((0, GY + 0.45, 0), math.pi, 1)
    g.pose(1, knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25, pelvis_z=-0.08)
    g.expresion(1, "neutral")
    g.expresion(F(1.6), "sorpresa")
    g.mirar(F(1.6), -0.5, 0.2)
    bola(ball, F(1.2), (0, 0, 0.11), (0, 0, 0))
    bola(ball, F(2.0), (7.5, GY - 1.0, 4.5), (-20, 4, 0))
    bola(ball, F(2.6), (11.0, GY - 6.0, 6.5), (-30, 6, 0))
    # plano 2: cuando el penalti era en contra, su portero se apartaba
    t2 = 2.6
    lejos = (40, 60, 0)
    for p in (k, d):            # fuera de plano hasta el corte
        p.place(lejos, 0, 1)
        p.place(lejos, 0, F(t2) - 2)
    g.place((0, GY + 0.45, 0), math.pi, F(t2) - 2)
    g.place(lejos, 0, F(t2))
    a.place((0.15, 0.6, 0), math.radians(-10), F(t2) - 2)
    a.place(lejos, 0, F(t2))
    k.place((-GW - 0.3, GY + 0.2, 0), math.pi + 0.5, F(t2))
    k.reposo(F(t2))
    brazos_cruzados(k, F(t2))
    k.expresion(F(t2), "picaro")
    k.cabeza(F(t2), 0, -0.15, 0.1)
    d.place((0.7, 2.3, 0), 0, F(t2))
    d.reposo(F(t2))
    d.expresion(F(t2), "sorpresa")
    d.correr(F(t2 + 0.2), F(t2 + 0.8), (0.7, 2.3, 0), (0.25, 0.75, 0), yaw=math.radians(-10), pasos_s=2.0)
    chute(d, F(t2 + 0.85), (0.15, 0.6, 0), math.radians(-10))
    d.reposo(F(t2 + 1.6))
    d.expresion(F(t2 + 1.2), "feliz")
    bola(ball, F(t2), (0, 0, 0.11), (0, 0, 0))
    bola(ball, F(t2 + 1.0), (0, 0, 0.11))
    bola(ball, F(t2 + 1.5), (0.4, GY - 0.6, 0.4), (-12, 0, 0))
    bola(ball, F(t2 + 2.0), (0.5, GY - 1.4, 0.11))
    for p, s in ((a, 12), (k, 13), (d, 14), (g, 15)):
        vida(p, dur, s)
    camera(sc, "c1", 0, t2, (1.1, 5.4, 1.8), (1.3, 4.6, 1.7), (0.2, -3.0, 1.2), (3.5, -6.0, 2.4), lens=28)
    camera(sc, "c2", t2, dur, (-6.2, GY + 5.2, 1.5), (-5.9, GY + 4.8, 1.5), (-2.9, GY + 0.4, 1.2), (-2.6, GY + 0.2, 1.1),
           lens=26)


def s_primero(sc, dur):
    d, g = P_del(), P_gk()
    ball = balon((0, 0, 0.11))
    d.place((0.9, 3.4, 0), 0, 1)
    d.reposo(1)
    d.expresion(1, "enfadado")
    d.correr(F(0.1), F(0.85), (0.9, 3.4, 0), (0.25, 0.75, 0), yaw=math.radians(-8), pasos_s=2.4)
    chute(d, F(0.9), (0.15, 0.62, 0), math.radians(-8))
    d.reposo(F(1.6))
    d.expresion(F(1.4), "sorpresa")
    g.place((0, GY + 0.45, 0), math.pi, 1)
    g.pose(1, knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25, pelvis_z=-0.08)
    g.expresion(1, "enfadado")
    # el portero se tira al otro lado
    td = 1.0
    g.root.rotation_mode = "XYZ"
    g.place((0, GY + 0.45, 0), math.pi, F(td))
    key(g.root, F(td + 0.4), location=Vector((-1.8, GY + 0.45, 1.0)), rotation_euler=(0, math.radians(78), math.pi))
    key(g.root, F(td + 0.9), location=Vector((-2.4, GY + 0.5, 0.35)), rotation_euler=(0, math.radians(90), math.pi))
    g.pose(F(td + 0.35), hips=(0.1, -0.1), knees=(0.2, 0.4), shoulders=((0, 2.8), (0, -2.8)), elbows=(0, 0))
    g.expresion(F(td + 0.2), "sorpresa")
    tk = 0.9 + 3 / FPS
    bola(ball, F(tk), (0, 0, 0.11), (0, 0, 0))
    tgt = Vector((GW - 0.5, GY - 0.05, GH - 0.4))
    for j in range(1, 7):
        u = j / 6
        p = Vector((0, 0, 0.11)).lerp(tgt, u)
        p.z += math.sin(u * math.pi) * 0.4
        bola(ball, F(tk + 0.6 * u), tuple(p))
    bola(ball, F(tk + 0.95), (GW - 0.6, GY - 1.3, 1.2), (-25, 5, 0))
    bola(ball, F(tk + 1.4), (GW - 0.8, GY - 1.4, 0.11))
    t3 = 3.0
    d.place((0.1, 0.4, 0), 0, F(t3))
    d.expresion(F(t3), "grito")
    celebrar(d, F(t3), F(dur), (0.1, 0.4, 0), (0.5, -1.8, 0))
    d.expresion(F(t3 + 1.0), "feliz")
    vida(d, dur, 16, skip=[(t3 - 0.1, t3 + 0.5)])
    vida(g, dur, 17)
    camera(sc, "c1", 0, 1.3, (1.9, 6.6, 1.9), (1.2, 4.6, 1.6), (0, -3, 1.0), (0, -6, 1.1), lens=28)
    camera(sc, "c2", 1.3, t3, (7.0, GY + 2.2, 1.3), (6.4, GY + 1.6, 1.4), (1.6, GY - 0.2, 1.3), (2.4, GY - 0.6, 1.0),
           lens=30)
    camera(sc, "c3", t3, dur, (0.5, -2.2, 1.75), (0.7, -3.4, 1.85), None, lens=32,
           follow=bpy.data.objects["del_cabeza"])


def s_cierre(sc, dur):
    d, m = P_del(), P_def()
    d.place((-0.45, 0, 0), math.radians(6), 1)
    m.place((0.5, 0.15, 0), math.radians(-12), 1)
    d.reposo(1)
    m.reposo(1)
    d.expresion(1, "neutral")
    m.expresion(1, "picaro")
    m.mirar(1, 0.45, 0)
    m.cabeza(1, 0.25, 0, 0)
    # el defensa va a meter la pierna... mira a cámara... y se lo piensa
    m.pose(F(0.6), hips=(0.05, 0.9), knees=(0.05, 1.2), shoulders=((0.1, 0.5), (0.1, -0.5)), elbows=(-0.4, -0.4),
           lean=0.1)
    m.cabeza(F(0.9), 0.25, 0, 0)
    m.cabeza(F(1.3), 0, 0, 0)
    m.mirar(F(1.3), 0, 0)
    m.expresion(F(1.3), "sorpresa")
    m.reposo(F(1.8))
    m.expresion(F(2.1), "feliz")
    encoger(m, F(2.3))
    m.reposo(F(3.0))
    d.mirar(F(0.6), -0.45, 0)
    d.cabeza(F(0.6), -0.2, 0, 0)
    d.expresion(F(0.8), "enfadado")
    d.cabeza(F(2.6), 0, 0, 0)
    d.mirar(F(2.6), 0, 0)
    d.expresion(F(2.6), "feliz")
    # saluda a cámara: pregunta final
    for i, f in enumerate(range(F(2.8), F(dur) + 1, 5)):
        key(d.sh["R"], f, rotation_euler=(0, -2.5 + 0.0, 0))
        key(d.el["R"], f, rotation_euler=(0.5 * (1 if i % 2 else -1), 0, 0))
    vida(d, dur, 18)
    vida(m, dur, 19, skip=[(1.2, 1.5)])
    camera(sc, "c1", 0, dur, (0.05, -3.4, 1.5), (0.05, -2.8, 1.55), (0.05, 0.1, 1.4), (0.05, 0.1, 1.5), lens=34)


ESCENAS = {"gancho": s_gancho, "caza": s_caza, "mccrum": s_mccrum, "idea": s_idea, "insulto": s_insulto,
           "fallo": s_fallo, "primero": s_primero, "cierre": s_cierre}


def main():
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    rw, rh = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (576, 1024)
    only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ESCENAS[name](sc, dur)      # personajes y animación primero (más rápido)
    estadio(tmpdir=out)
    cuts = sorted(m.frame for m in sc.timeline_markers if m.frame > 1)
    for o in bpy.data.objects:
        for fc in all_fcurves(o):
            if fc.modifiers:
                continue
            kps = sorted(fc.keyframe_points, key=lambda k: k.co.x)
            for i, kp in enumerate(kps):
                kp.interpolation = "BEZIER"
                # corte de plano: mantener el valor hasta el corte (nada de deslizarse en el plano anterior)
                if i + 1 < len(kps):
                    nf = kps[i + 1].co.x
                    if any(kp.co.x < c and c <= nf <= c + 1 for c in cuts):
                        kp.interpolation = "CONSTANT"
    n = F(dur)
    setup_render(sc, rw, rh, FPS, n, 14)
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
