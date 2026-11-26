"""«¿Y si un equipo de ANIME jugara contra uno normal?» en 3D. Equipo y técnicas inventados por nosotros.
Uso: python -m ytauto.b3d.video_anime SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]
Las imágenes quedan en SALIDA_DIR/x_3d_<escena>/f_0001.png ... (24 fps)."""
from __future__ import annotations

import math
import random
import sys

import bpy
from mathutils import Matrix, Vector

from .concept_supertiro import aura, glow, mano_gigante, onda
from .core import all_fcurves, attach, cube, key, mat, setup_render, sphere, srgb, world
from .escenario import GY, balon, estadio
from .personaje import PELVIS_Z, Personaje
from .video_penalti import FPS, F, bola, brazos_cruzados, camera, celebrar, chute, encoger, jarras, vida

AZUL = (0.02, 0.35, 1.0)
FUEGO = (1.0, 0.45, 0.08)
LEJOS = (40, 60, 0)


# ------------------------------------------------------------------ plantillas
def A10():
    """El 10 del equipo de anime: pelo de pinchos azul eléctrico, blanco y oro."""
    return Personaje("a10", kit=(242, 242, 250), num="10", pelo="pinchos", pelo_col=(30, 110, 255),
                     ojos=(40, 90, 200), pantalon=(30, 40, 90), ribete=(255, 196, 40)).build()


def A7():
    return Personaje("a7", kit=(242, 242, 250), num="7", pelo="coleta", pelo_col=(235, 60, 90),
                     piel=(255, 220, 195), pantalon=(30, 40, 90), ribete=(255, 196, 40)).build()


def A4():
    return Personaje("a4", kit=(242, 242, 250), num="4", pelo="pinchos", pelo_col=(250, 250, 250),
                     piel=(190, 130, 90), pantalon=(30, 40, 90), ribete=(255, 196, 40)).build()


def AG():
    return Personaje("ag", kit=(255, 196, 40), num="1", pelo="raya", pelo_col=(130, 60, 210), guantes=True,
                     piel=(240, 195, 160), pantalon=(30, 40, 90)).build()


def N9():
    """Equipo normal: granate, pelos de toda la vida."""
    return Personaje("n9", kit=(165, 30, 45), num="9", pelo="rizos", pelo_col=(40, 28, 20),
                     piel=(225, 170, 130), pantalon=(25, 25, 30)).build()


def N4():
    return Personaje("n4", kit=(165, 30, 45), num="4", pelo="rapado", pelo_col=(25, 20, 18),
                     piel=(250, 205, 175), pantalon=(25, 25, 30)).build()


def N5():
    return Personaje("n5", kit=(165, 30, 45), num="5", pelo="raya", pelo_col=(120, 80, 40),
                     piel=(255, 215, 185), pantalon=(25, 25, 30)).build()


def ARB():
    return Personaje("arb", kit=(30, 30, 36), num="", pelo="rapado", pelo_col=(60, 60, 60),
                     piel=(240, 200, 170), pantalon=(30, 30, 36), ribete=(30, 30, 36)).build()


# ------------------------------------------------------------------ efectos animados
def _agrupar(center, build):
    """Crea objetos con build() y los cuelga de un vacío en center (para escalar/girar el grupo)."""
    antes = set(bpy.data.objects)
    build()
    nuevos = [o for o in bpy.data.objects if o not in antes]
    e = bpy.data.objects.new("fx_grupo", None)
    bpy.context.collection.objects.link(e)
    e.location = center
    inv = Matrix.Translation(Vector(center)).inverted()
    for o in nuevos:
        if o.parent is None:
            o.parent = e
            o.matrix_parent_inverse = inv
    return e


def aura_anim(center, f_on, f_full, f_off=None, f_gone=None, **kw):
    antes = set(bpy.data.materials)
    e = _agrupar(center, lambda: aura(center, **kw))
    for m in bpy.data.materials:            # de día hace falta más brillo
        if m not in antes and m.node_tree:
            k = 0.7 if m.name.startswith("aura_capa") else 1.6
            for nd in m.node_tree.nodes:
                if nd.type == "EMISSION":
                    nd.inputs["Strength"].default_value *= k
    e.rotation_mode = "XYZ"
    key(e, 1, scale=(0.001,) * 3)
    key(e, f_on, scale=(0.001,) * 3)
    key(e, f_full, scale=(1.08, 1.08, 1.08))
    end = f_off or F(12)
    for f in range(f_full + 4, end, 4):          # latido de las llamas
        s = 1.0 + 0.05 * math.sin(f * 0.9)
        key(e, f, scale=(s, s, 1.0 + 0.07 * math.sin(f * 1.3)), rotation_euler=(0, 0, 0.04 * math.sin(f * 0.5)))
    if f_off:
        key(e, f_off, scale=(1, 1, 1))
        key(e, f_gone, scale=(0.001,) * 3)
    return e


def brillo_ojos(p, keys, col=(0.3, 0.75, 1.0)):
    """keys: [(fotograma, fuerza)]. Los iris pasan a emitir luz."""
    b = p.m_iris.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1)
    s = b.inputs["Emission Strength"]
    s.default_value = 0
    s.keyframe_insert("default_value", frame=1)
    for f, v in keys:
        s.default_value = v
        s.keyframe_insert("default_value", frame=f)


def ondas(center, f0, n=3, col=AZUL, normal=(0, 0, 1)):
    for i in range(n):
        o = onda(center, normal, 1.0, col, name=f"onda{f0}_{i}")
        fa = f0 + i * 5
        key(o, 1, scale=(0.001,) * 3)
        key(o, fa, scale=(0.05,) * 3)
        key(o, fa + 12, scale=(2.6,) * 3)
        key(o, fa + 13, scale=(0.001,) * 3)


def hablar(p, f0, f1, base="enfadado", abierta="grito", cada=3):
    for i, f in enumerate(range(f0, f1, cada)):
        p.expresion(f, abierta if i % 2 else base, 1.0 if i % 2 else 1.0)
    p.expresion(f1, base)


def bostezo(p, f0):
    p.expresion(f0, "neutral")
    p.expresion(f0 + 5, "grito")
    for up in p.lids_up:
        key(up, f0 + 5, rotation_euler=(math.radians(55), 0, 0))
        key(up, f0 + 26, rotation_euler=(math.radians(55), 0, 0))
    p.pose(f0, shoulders=((0.05, 0.12), (0.05, -0.12)), elbows=(-0.2, -0.2))
    p.pose(f0 + 8, shoulders=((0.0, 2.7), (0.0, -2.7)), elbows=(-0.9, -0.9), lean=-0.12)
    p.pose(f0 + 24, shoulders=((0.0, 2.8), (0.0, -2.8)), elbows=(-1.0, -1.0), lean=-0.15)
    p.cabeza(f0 + 8, 0, -0.25, 0)
    p.cabeza(f0 + 26, 0, -0.25, 0)
    p.expresion(f0 + 26, "grito")
    p.expresion(f0 + 32, "neutral")
    for up in p.lids_up:
        key(up, f0 + 32, rotation_euler=(math.radians(-30), 0, 0))
    p.cabeza(f0 + 34, 0, 0, 0)
    p.reposo(f0 + 34)


def rascarse(p, f0, f1):
    """Mano derecha a la cabeza, rascando."""
    for i, f in enumerate(range(f0, f1, 4)):
        p.pose(f, shoulders=((0.05, 0.12), (-0.4, -2.5 - 0.12 * (i % 2))), elbows=(-0.2, -2.0 - 0.15 * (i % 2)))
    p.reposo(f1 + 4)


def arrodillado(p, f, lean=0.25):
    p.pose(f, hips=(-0.15, -0.15), knees=(1.6, 1.6), shoulders=((-0.3, 0.2), (-0.3, -0.2)), elbows=(-0.4, -0.4),
           lean=lean, pelvis_z=-0.31)


def lagrimas(p, f0, f1, seed=0):
    """Gotas que caen de los ojos (construir ANTES de colocar al personaje)."""
    rng = random.Random(seed)
    m = glow(p.n + "_lagrima", (0.35, 0.7, 1.0), 2.0, 0.85)
    for sx in (-1, 1):
        for k in range(3):
            o = sphere(f"{p.n}_lag{sx}{k}", (sx * 0.12, -0.31, 1.9), (0.022, 0.018, 0.03), m, p.neck, seg=12, rings=6)
            sc0 = (0.022, 0.018, 0.03)
            o.scale = (0.001,) * 3
            per = 18
            f = f0 + k * 6 + rng.randint(0, 3)
            while f < f1:
                key(o, f - 1, scale=(0.001,) * 3)
                key(o, f, location=Vector((sx * 0.12, -0.31, 1.9)), scale=sc0)
                key(o, f + per - 1, location=Vector((sx * 0.16, -0.27, 1.62)), scale=(sc0[0], sc0[1], sc0[2] * 1.4))
                key(o, f + per, scale=(0.001,) * 3)
                f += per + rng.randint(0, 4)


def tarjeta(p, lado="R"):
    """Tarjeta roja en la mano (oculta hasta que se anima su escala)."""
    hand = bpy.data.objects[f"{p.n}_mano{lado}"]
    pos = world(hand).translation
    c = cube(p.n + "_roja", tuple(pos + Vector((0, -0.03, -0.1))), (0.045, 0.006, 0.065),
             mat("roja", srgb(230, 20, 30), 0.4, emit=0.6), p.el[lado])
    c.scale = (0.001,) * 3
    return c


def silbato(p, f, dur=6):
    p.expresion(f, "sorpresa")
    p.expresion(f + dur, "enfadado")


# ------------------------------------------------------------------ escenas
def s_gancho(sc, dur):
    a, n = A10(), N9()
    a.place((-0.62, 0, 0), math.radians(70), 1)
    n.place((0.62, 0, 0), math.radians(-70), 1)
    a.reposo(1)
    n.reposo(1)
    a.expresion(1, "enfadado")
    brazos_cruzados(a, F(0.3))
    a.cabeza(F(0.3), 0, -0.12, 0)
    a.pose(F(1.1), knees=(0.2, 0.2), shoulders=((0.3, 0.6), (0.3, -0.6)), elbows=(-1.7, -1.7), lean=0.1,
           pelvis_z=-0.05)
    a.expresion(F(1.1), "grito")
    a.expresion(F(1.6), "enfadado")
    brillo_ojos(a, [(F(1.0), 0), (F(1.3), 4.5)])
    aura_anim((-0.62, 0, 0), F(0.9), F(1.4), cam_dir=(0.2, -1), seed=4)
    ondas((-0.62, 0, 0.05), F(1.1))
    n.expresion(1, "neutral")
    n.mirar(1, 0.3, 0)
    n.expresion(F(1.3), "sorpresa")
    n.cabeza(F(1.3), 0.1, 0, 0)
    n.expresion(F(1.9), "neutral")
    t2 = 2.6
    bostezo(n, F(t2 + 0.1))
    rascarse(n, F(t2 + 1.5), F(dur - 0.3))
    n.expresion(F(t2 + 1.6), "picaro")
    vida(a, dur, 1)
    vida(n, dur, 2, skip=[(t2, t2 + 1.6)])
    camera(sc, "c1", 0, t2, (0.0, -4.6, 1.35), (0.0, -3.7, 1.45), (0, 0, 1.35), (0, 0, 1.45), lens=30)
    camera(sc, "c2", t2, dur, (-0.15, -1.75, 1.8), (-0.05, -1.55, 1.82), (0.6, 0, 1.85), lens=36)


def s_discurso(sc, dur):
    a, t7, t4, n9, n5 = A10(), A7(), A4(), N9(), N5()
    # plano 1: discurso con los ojos brillando; los compañeros, emocionados
    a.place((0, 0, 0), 0, 1)
    a.reposo(1)
    a.pose(F(0.2), shoulders=((-1.2, 0.3), (0.05, -0.12)), elbows=(-0.3, -0.2))        # puño al frente
    a.pose(F(1.6), shoulders=((-0.6, 0.5), (-0.9, -0.2)), elbows=(-1.6, -1.8))         # mano al pecho
    a.pose(F(2.8), shoulders=((0.0, 2.6), (0.0, -2.6)), elbows=(-0.2, -0.2))          # brazos al cielo
    hablar(a, F(0.1), F(3.6), "enfadado", "grito")
    a.cabeza(F(0.1), 0, -0.1, 0)
    a.cabeza(F(2.8), 0, -0.25, 0)
    brillo_ojos(a, [(F(0.2), 4.0)])
    aura_anim((0, 0, 0), F(0.1), F(0.5), cam_dir=(0, -1), seed=5, height=2.0)
    for p, loc, yaw, s in ((t7, (-0.95, 1.2, 0), math.radians(-20), 3), (t4, (0.95, 1.3, 0), math.radians(20), 4)):
        p.place(loc, yaw, 1)
        p.reposo(1)
        p.expresion(1, "triste")
        brillo_ojos(p, [(F(0.4), 2.0)])
        p.pose(F(1.0), shoulders=((-0.7, 0.3), (-0.7, -0.3)), elbows=(-1.8, -1.8))    # puños apretados
        for i, t in enumerate((1.2, 1.7, 2.2, 2.7)):
            p.cabeza(F(t), 0, 0.15 if i % 2 else -0.05, 0)                            # asienten
        vida(p, dur, s)
    t2 = 3.7
    for p in (a, t7, t4):
        p.place(p.root.location[:], p.root.rotation_euler[2], F(t2) - 1)
        p.place(LEJOS, 0, F(t2))
    # plano 2: el equipo normal esperando
    for p in (n9, n5):
        p.place(LEJOS, 0, 1)
        p.place(LEJOS, 0, F(t2) - 1)
    n9.place((6.0, 0, 0), math.radians(12), F(t2))
    n5.place((7.1, 0.25, 0), math.radians(-15), F(t2))
    n9.reposo(F(t2))
    n5.reposo(F(t2))
    n9.expresion(F(t2), "neutral")
    n5.expresion(F(t2), "neutral")
    for i, f in enumerate(range(F(t2), F(dur), 6)):                                    # golpea el suelo con el pie
        key(n9.hip["R"], f, rotation_euler=(0.0 if i % 2 else -0.25, 0, 0))
    n9.mirar(F(t2 + 0.6), -0.45, 0)
    n5.mirar(F(t2 + 0.6), 0.45, 0)
    n9.cabeza(F(t2 + 0.6), -0.3, 0, 0)
    n5.cabeza(F(t2 + 0.6), 0.3, 0, 0)
    n5.cabeza(F(t2 + 1.4), 0.3, 0, 0.15)
    n5.expresion(F(t2 + 1.2), "picaro")
    n9.expresion(F(t2 + 1.3), "picaro")
    vida(a, t2, 6)
    vida(n9, dur, 7)
    vida(n5, dur, 8)
    camera(sc, "c1", 0, t2, (0.35, -2.0, 1.45), (0.25, -1.6, 1.5), (0, 0, 1.85), (0, 0, 1.95), lens=30)
    camera(sc, "c2", t2, dur, (6.55, -3.6, 1.55), (6.55, -3.3, 1.55), (6.55, 0.1, 1.45), lens=32)


def s_gol(sc, dur):
    a, t7, t4, g, n9 = A10(), A7(), A4(), AG(), N9()
    ball = balon((1.5, 1.0, 0.11))
    # el anime sigue en el círculo central escuchando el discurso
    a.place((0, 0.6, 0), math.pi, 1)
    a.reposo(1)
    a.pose(F(0.1), shoulders=((0.0, 2.6), (0.0, -2.6)), elbows=(-0.2, -0.2))
    hablar(a, F(0.1), F(dur), "enfadado", "grito")
    brillo_ojos(a, [(1, 4.0)])
    for p, loc, s in ((t7, (-0.9, 1.9, 0), 3), (t4, (0.9, 2.0, 0), 4), (g, (0.1, 2.6, 0), 5)):
        yaw = math.atan2(-(loc[0] - 0), (loc[1] - 0.6)) + math.pi
        p.place(loc, yaw, 1)
        p.reposo(1)
        p.expresion(1, "triste")
        brillo_ojos(p, [(1, 2.0)])
        vida(p, dur, s)
    # el 9 normal se va solo hacia la portería vacía
    tk = 2.1
    n9.expresion(1, "picaro")
    n9.correr(1, F(tk - 0.05), (1.5, 1.9, 0), (0.55, -6.2, 0), yaw=math.radians(7), pasos_s=2.7)
    for f in range(1, F(tk) + 1, 2):
        u = (f - 1) / (F(tk) - 1)
        bola(ball, f, (1.5 - 0.95 * u, 1.0 - 7.3 * u, 0.11 + 0.05 * abs(math.sin(u * 14))), (-u * 40, 0, 0))
    chute(n9, F(tk), (0.5, -6.25, 0), math.radians(7))
    tb = tk + 3 / FPS
    bola(ball, F(tb), (0.35, -7.0, 0.11))
    bola(ball, F(tb + 0.55), (0.2, GY - 0.6, 0.9), (-30, 0, 0))
    bola(ball, F(tb + 0.8), (0.15, GY - 1.6, 0.6))
    bola(ball, F(tb + 1.2), (0.1, GY - 1.7, 0.11))
    n9.expresion(F(tk + 0.4), "feliz")
    celebrar(n9, F(tk + 0.6), F(dur), (0.5, -6.25, 0), (1.6, -7.2, 0), yaw=math.radians(-150))
    vida(n9, dur, 9)
    camera(sc, "c1", 0, tk - 0.4, (5.0, 3.4, 3.4), (3.6, -4.6, 2.6), None, lens=24,
           follow=bpy.data.objects["n9_cuerpo"])
    camera(sc, "c2", tk - 0.4, dur, (4.2, GY + 0.6, 1.2), (4.0, GY + 0.9, 1.25), (0.4, -6.5, 1.0), (0.5, -8.0, 0.9),
           lens=24)


def s_carga(sc, dur):
    a = A10()
    ball = balon((0, -2.45, 0.11))
    a.place((0, -2.0, 0), 0, 1)
    a.reposo(1)
    a.expresion(1, "enfadado")
    a.pose(F(0.3), knees=(0.35, 0.35), shoulders=((0.35, 0.5), (0.35, -0.5)), elbows=(-1.7, -1.7), lean=0.18,
           pelvis_z=-0.1)
    brillo_ojos(a, [(F(0.5), 0), (F(0.9), 5.0)])
    aura_anim((0, -2.0, 0), F(0.5), F(1.1), cam_dir=(0, -1), seed=6, height=2.4)
    ondas((0, -2.0, 0.05), F(1.0), n=3)
    a.expresion(F(1.3), "grito")
    a.pose(F(1.5), knees=(0.2, 0.2), shoulders=((0.0, 2.3), (0.0, -2.3)), elbows=(-0.3, -0.3), lean=-0.15)
    a.cabeza(F(1.5), 0, -0.3, 0)
    # el balón se eleva girando delante de él
    ball.rotation_mode = "XYZ"
    bola(ball, F(1.2), (0, -2.45, 0.11), (0, 0, 0))
    bola(ball, F(2.6), (0, -2.75, 1.35), (6, 0, 9))
    for f in range(F(2.6), F(dur) + 1, 4):
        s = f / FPS
        bola(ball, f, (0.05 * math.sin(s * 5), -2.75, 1.35 + 0.05 * math.sin(s * 4)), (s * 4, 0, s * 6))
    t2 = 3.0
    a.pose(F(t2), hips=(0.0, 0.4), knees=(0.15, 0.6), shoulders=((0.6, 1.6), (0.6, -1.6)), elbows=(-0.5, -0.5),
           lean=-0.25)
    a.expresion(F(t2), "grito")
    a.cabeza(F(t2), 0, -0.15, 0)
    ondas((0, -2.75, 1.35), F(t2 + 0.2), n=2, normal=(0, 1, 0))
    vida(a, dur, 10, skip=[(0.4, dur)])
    camera(sc, "c1", 0, t2, (-2.4, -5.6, 1.1), (2.3, -5.4, 1.5), (0, -2.0, 1.2), (0, -2.0, 1.5), lens=26)
    camera(sc, "c2", t2, dur, (0.85, -4.3, 0.3), (0.95, -4.5, 0.25), (0, -2.3, 1.7), lens=19)


def s_robo(sc, dur):
    a, d = A10(), N4()
    ball = balon((0, -2.75, 1.35))
    a.place((0, -2.0, 0), 0, 1)
    a.pose(1, hips=(0.0, 0.4), knees=(0.15, 0.6), shoulders=((0.6, 1.6), (0.6, -1.6)), elbows=(-0.5, -0.5),
           lean=-0.25)
    hablar(a, 1, F(3.3), "grito", "enfadado", cada=5)
    a.cabeza(1, 0, -0.15, 0)
    brillo_ojos(a, [(1, 5.0), (F(3.4), 5.0), (F(3.8), 0.0)])
    aura_anim((0, -2.0, 0), 1, 2, F(3.4), F(3.9), cam_dir=(0, -1), seed=6, height=2.4)
    for f in range(1, F(1.6), 4):
        s = f / FPS
        bola(ball, f, (0.05 * math.sin(s * 5), -2.75, 1.35 + 0.05 * math.sin(s * 4)), (s * 4, 0, s * 6))
    # el defensa llega andando, baja el balón con el pecho y se lo lleva
    d.expresion(1, "neutral")
    d.correr(1, F(1.4), (3.6, -2.2, 0), (0.85, -2.75, 0), yaw=math.radians(-79), pasos_s=1.7, amp=0.45)
    d.reposo(F(1.5))
    d.place((0.85, -2.75, 0), math.radians(-90), F(1.5))
    d.pose(F(1.7), shoulders=((0.05, 0.4), (0.05, -0.4)), elbows=(-0.3, -0.3), lean=-0.2)        # control con pecho
    bola(ball, F(1.6), (0.3, -2.75, 1.3))
    bola(ball, F(1.75), (0.6, -2.75, 1.25))
    bola(ball, F(2.2), (0.55, -2.85, 0.11), (-3, 0, 0))
    d.expresion(F(2.0), "picaro")
    d.mirar(F(2.0), 0, 0)
    d.cabeza(F(2.0), 0.0, 0, 0.05)
    d.correr(F(2.3), F(dur), (0.85, -2.75, 0), (3.6, -4.5, 0), yaw=math.radians(58), pasos_s=1.7, amp=0.45)
    for f in range(F(2.3), F(dur) + 1, 2):
        u = (f - F(2.3)) / (F(dur) - F(2.3))
        bola(ball, f, (0.85 + 2.75 * u + 0.3, -2.75 - 1.75 * u - 0.2, 0.11), (-u * 12, 0, 0))
    # el 10 se da cuenta
    a.expresion(F(3.4), "sorpresa")
    a.reposo(F(3.7))
    a.mirar(F(3.5), 0, -0.45)
    a.cabeza(F(3.5), 0, 0.3, 0)
    a.expresion(F(4.2), "triste")
    a.cabeza(F(4.3), -0.25, 0.1, 0)
    a.mirar(F(4.3), 0.3, -0.1)
    vida(d, dur, 11)
    vida(a, dur, 12, skip=[(0, 3.4)])
    camera(sc, "c1", 0, 3.4, (1.6, -6.4, 1.5), (1.2, -6.0, 1.45), (0.2, -2.5, 1.25), (0.0, -2.6, 1.2), lens=26)
    camera(sc, "c2", 3.4, dur, (0.35, -3.65, 1.85), (0.3, -3.45, 1.85), (0, -2.0, 1.85), lens=36)


def s_mano(sc, dur):
    g, n9, r = AG(), N9(), ARB()
    card = tarjeta(r, "R")
    ball = balon((0.3, 3.0, 0.11))
    # el portero de anime, fuera del área, saca la mano de fuego
    g.place((0, -1.6, 0), math.pi, 1)
    g.pose(1, knees=(0.35, 0.35), shoulders=((0, 0.9), (0, -0.9)), elbows=(-0.3, -0.3), lean=0.25, pelvis_z=-0.08)
    g.expresion(1, "enfadado")
    g.pose(F(0.5), hips=(-0.2, 0.3), knees=(0.5, 0.6), shoulders=((-1.5, 0.15), (-1.3, -0.3)), elbows=(-0.1, -0.1),
           lean=0.25, pelvis_z=-0.12)
    g.expresion(F(0.5), "grito")
    brillo_ojos(g, [(F(0.4), 0), (F(0.6), 3.5)], col=(1.0, 0.6, 0.15))
    hand = Vector((0.1, -0.35, 1.5))
    antes = set(bpy.data.materials)
    e = _agrupar(tuple(hand), lambda: mano_gigante(tuple(hand), (0, 1, 0), 1.15, (1.0, 0.3, 0.02)))
    for m in bpy.data.materials:
        if m not in antes and m.node_tree:
            for nd in m.node_tree.nodes:
                if nd.type == "EMISSION":
                    nd.inputs["Strength"].default_value *= 1.8
    key(e, 1, scale=(0.001,) * 3)
    key(e, F(0.5), scale=(0.001,) * 3)
    key(e, F(0.8), scale=(1.1,) * 3)
    key(e, F(0.95), scale=(1.0,) * 3)
    key(e, F(2.2), scale=(1.0,) * 3)
    key(e, F(2.4), scale=(0.001,) * 3)
    aura_anim((0, -1.6, 0), F(0.4), F(0.8), F(2.2), F(2.4), cam_dir=(0.4, 1), seed=7, col=FUEGO, height=2.0)
    n9.place((0.35, 2.6, 0), math.pi, 1)
    n9.reposo(1)
    n9.expresion(1, "enfadado")
    chute(n9, F(0.6), (0.35, 2.25, 0), math.pi)
    bola(ball, F(0.6 + 3 / FPS), (0.3, 2.0, 0.11), (0, 0, 0))
    bola(ball, F(1.1), (0.15, 0.0, 1.45), (25, 0, 0))
    bola(ball, F(1.6), (0.15, 0.05, 1.45), (27, 0, 0))
    bola(ball, F(2.0), (0.2, 0.7, 0.11))
    n9.expresion(F(1.2), "sorpresa")
    ondas(tuple(hand + Vector((0, 0.3, 0))), F(1.1), n=3, col=FUEGO, normal=(0, 1, 0))
    # plano 2: el árbitro saca la roja
    t2 = 2.3
    r.place(LEJOS, 0, 1)
    r.place(LEJOS, 0, F(t2) - 1)
    n9.place((0.35, 2.25, 0), math.pi, F(t2) - 1)
    n9.place(LEJOS, 0, F(t2))
    r.place((1.15, -0.8, 0), math.radians(-150), F(t2))
    r.reposo(F(t2))
    r.expresion(F(t2), "enfadado")
    silbato(r, F(t2 + 0.2))
    r.pose(F(t2 + 0.5), shoulders=((0.05, 0.12), (0.0, -3.0)), elbows=(-0.2, 0.0))
    key(card, F(t2 + 0.45), scale=(0.001,) * 3)
    key(card, F(t2 + 0.55), scale=(0.045, 0.006, 0.065))
    g.reposo(F(t2))
    g.place((0, -1.6, 0), math.pi, F(t2))
    g.expresion(F(t2), "sorpresa")
    g.mirar(F(t2), -0.4, 0.1)
    g.cabeza(F(t2 + 0.6), -0.35, 0, 0)
    brillo_ojos(g, [(F(t2), 0)])
    g.expresion(F(t2 + 1.4), "triste")
    encoger(g, F(t2 + 1.3))
    g.reposo(F(t2 + 2.2))
    vida(g, dur, 13, skip=[(0.3, 2.3)])
    vida(r, dur, 14)
    vida(n9, t2, 15)
    camera(sc, "c1", 0, t2, (3.2, 6.6, 2.0), (2.8, 6.0, 1.9), (0.1, -0.6, 1.3), (0.1, -0.6, 1.4), lens=26)
    camera(sc, "c2", t2, dur, (0.55, 2.9, 1.75), (0.55, 2.6, 1.75), (0.55, -1.3, 1.85), lens=28)


def s_cierre(sc, dur):
    a, g, t7, n9, n4 = A10(), AG(), A7(), N9(), N4()
    for p, s in ((a, 1), (g, 2), (t7, 3)):
        lagrimas(p, F(0.2), F(dur), seed=s)
    # el anime, de rodillas, llorando hacia el horizonte (espaldas a la portería)
    for p, loc, yaw, s in ((a, (0, 0, 0), 0.0, 16), (g, (-1.0, 0.5, 0), math.radians(10), 17),
                           (t7, (1.0, 0.45, 0), math.radians(-10), 18)):
        p.place(loc, yaw, 1)
        arrodillado(p, 1, lean=0.05)
        p.expresion(1, "triste")
        p.cabeza(1, 0, -0.35, 0)
        p.mirar(1, 0, 0.35)
        p.pose(F(1.2), hips=(-0.15, -0.15), knees=(1.6, 1.6), shoulders=((0.0, 2.5), (0.0, -2.5)),
               elbows=(-0.3, -0.3), lean=-0.05, pelvis_z=-0.31)
        p.expresion(F(1.2), "grito")
        p.expresion(F(2.2), "triste")
        arrodillado(p, F(2.6), lean=0.2)
        vida(p, dur, s)
    t2 = 2.9
    for p in (a, g, t7):
        p.place(p.root.location[:], p.root.rotation_euler[2], F(t2) - 1)
        p.place(LEJOS, 0, F(t2))
    # plano 2: los normales, tan tranquilos, saludan a cámara
    for p in (n9, n4):
        p.place(LEJOS, 0, 1)
        p.place(LEJOS, 0, F(t2) - 1)
    n9.place((-0.45, -6, 0), math.radians(6), F(t2))
    n4.place((0.5, -5.85, 0), math.radians(-12), F(t2))
    n9.reposo(F(t2))
    n4.reposo(F(t2))
    n9.expresion(F(t2), "feliz")
    n4.expresion(F(t2), "picaro")
    n4.mirar(F(t2), 0.45, 0)
    n4.cabeza(F(t2), 0.25, 0, 0)
    encoger(n4, F(t2 + 0.4))
    for i, f in enumerate(range(F(t2 + 0.3), F(dur) + 1, 5)):
        key(n9.sh["R"], f, rotation_euler=(0, -2.5, 0))
        key(n9.el["R"], f, rotation_euler=(0.5 * (1 if i % 2 else -1), 0, 0))
    vida(n9, dur, 19)
    vida(n4, dur, 20)
    camera(sc, "c1", 0, t2, (0.2, -3.1, 0.75), (0.15, -2.6, 0.8), (0, 0.2, 1.35), (0, 0.2, 1.4), lens=26)
    camera(sc, "c2", t2, dur, (0.05, -9.4, 1.5), (0.05, -8.9, 1.55), (0.05, -5.9, 1.4), (0.05, -5.9, 1.5), lens=34)


ESCENAS = {"gancho": s_gancho, "discurso": s_discurso, "gol": s_gol, "carga": s_carga, "robo": s_robo,
           "mano": s_mano, "cierre": s_cierre}


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
