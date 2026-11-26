"""«La Concentración», capítulo 1: La carta. Parodia animada con caricaturas.
Uso: python -m ytauto.b3d.cap01 SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import random
import sys

import bpy
from mathutils import Vector

from .core import all_fcurves, cube, key, mat, setup_render, sphere, srgb
from .famosos import FAMOSOS
from .personaje import PELVIS_Z
from .vestuario import PUERTA, abrir_puerta, apagar, cerrar_puerta, vestuario
from .video_anime import aura_anim, hablar
from .video_penalti import FPS, F, camera, encoger, jarras, vida

LEJOS = (40, 60, 0)
ORDEN = ["cr7", "messi", "neymar", "lamine", "mbappe", "haaland", "kane"]
OUT = "/tmp"


def reparto(keys=ORDEN):
    return {k: FAMOSOS[k]() for k in keys}


def fuera(ps, f=1):
    for p in ps:
        p.place(LEJOS, 0, f)


def sentado_banco(p, f, lean=0.05):
    p.pose(f, hips=(-1.5, -1.5), knees=(1.5, 1.5), shoulders=((0.05, 0.15), (0.05, -0.15)), elbows=(-0.6, -0.6),
           lean=lean, pelvis_z=-0.15)


def ojos_cerrados(p, f, cerrados=True):
    for up in p.lids_up:
        key(up, f, rotation_euler=(math.radians(92 if cerrados else -55), 0, 0))


# ------------------------------------------------------------------ atrezo
def sobre(nombre, loc, rot_z=0.0):
    papel = mat("sobre_m", srgb(240, 230, 205), 0.6)
    s = cube(nombre, loc, (0.15, 0.1, 0.004), papel)
    s.rotation_euler = (0, 0, rot_z)
    sphere(nombre + "_sello", (loc[0], loc[1], loc[2] + 0.004), (0.025, 0.025, 0.006),
           mat("lacre", srgb(170, 20, 30), 0.4), s)
    return s


def carta_tex():
    from PIL import Image, ImageDraw, ImageFont
    W, H = 700, 1000
    im = Image.new("RGB", (W, H), (246, 238, 214))
    d = ImageDraw.Draw(im)
    fb = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    f1, f2 = ImageFont.truetype(fb, 86), ImageFont.truetype(fb, 150)
    y = 110
    for line in ("PARTIDO", "SECRETO", "", "SÁBADO", "", "SIN", "ENTRENADOR"):
        if line:
            w = d.textlength(line, font=f1)
            d.text(((W - w) / 2, y), line, font=f1, fill=(30, 26, 24))
        y += 100
    d.text((W - 260, H - 230), "— M", font=f2, fill=(160, 18, 28))
    path = f"{OUT}/carta.png"
    im.save(path)
    return path


def carta(loc, rot=(0, 0, 0)):
    m = bpy.data.materials.new("carta_m")
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    b = nt["Principled BSDF"]
    tx = nt.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(carta_tex())
    ln.new(tx.outputs["Color"], b.inputs["Base Color"])
    ln.new(tx.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.25
    b.inputs["Roughness"].default_value = 0.7
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = "carta"
    o.scale = (0.21, 0.3, 1)
    o.data.materials.append(m)
    return o


def mate(p):
    """Mate con bombilla en la mano derecha (construir antes de colocar)."""
    hand = bpy.data.objects[f"{p.n}_manoR"]
    from .core import world
    pos = world(hand).translation
    calabaza = sphere(p.n + "_mate", tuple(pos + Vector((0, -0.07, 0.02))), (0.055, 0.055, 0.065),
                      mat("mate_m", srgb(120, 72, 40), 0.5, coat=0.4), p.el["R"])
    cube(p.n + "_bombilla", tuple(pos + Vector((0.0, -0.07, 0.11))), (0.006, 0.006, 0.07),
         mat("bombilla_m", srgb(200, 200, 205), 0.15, coat=1.0), p.el["R"])
    return calabaza


# ------------------------------------------------------------------ escenas
def s_carta(sc, dur):
    ps = reparto(["messi"])
    m = ps["messi"]
    hinge = vestuario()
    rng = random.Random(3)
    sobres = []
    for i in range(7):                                 # siete sobres entran por debajo de la puerta
        s = sobre(f"sobre{i}", (PUERTA[0] - 0.4, PUERTA[1] + 0.5, 0.005))
        f0 = F(0.15 + i * 0.22)
        dst = (PUERTA[0] + 0.5 + rng.uniform(0, 0.9), PUERTA[1] + 0.1 + rng.uniform(0, 0.8), 0.005)
        key(s, 1, location=Vector((PUERTA[0] - 0.4, PUERTA[1] + 0.5, 0.005)))
        key(s, f0, location=Vector((PUERTA[0] - 0.4, PUERTA[1] + 0.5, 0.005)))
        key(s, f0 + 7, location=Vector(dst), rotation_euler=(0, 0, rng.uniform(-0.8, 0.8)))
        sobres.append((s, dst))
    # Messi lo ve, se agacha y coge uno
    m.place((-1.6, 1.4, 0), math.radians(-60), 1)
    m.reposo(1)
    m.expresion(1, "neutral")
    m.mirar(F(0.6), 0.2, -0.35)
    m.expresion(F(1.0), "sorpresa")
    m.correr(F(1.8), F(2.6), (-1.6, 1.4, 0), (-2.9, 1.35, 0), yaw=math.radians(-80), pasos_s=1.6, amp=0.45)
    m.place((-2.9, 1.35, 0), math.radians(-80), F(2.6))
    m.pose(F(2.9), knees=(0.6, 0.6), shoulders=((-1.0, 0.2), (-1.3, -0.2)), elbows=(-0.2, -0.2), lean=0.6,
           pelvis_z=-0.12)
    m.reposo(F(3.5))
    s, dst = sobres[0]
    key(s, F(2.95), location=Vector(dst))
    key(s, F(3.5), location=Vector((-3.15, 1.05, 1.05)), rotation_euler=(math.radians(70), 0, math.radians(-80)))
    m.pose(F(3.5), shoulders=((-0.9, 0.2), (-0.9, -0.2)), elbows=(-0.9, -0.9))
    m.cabeza(F(3.5), 0, 0.3, 0)
    vida(m, dur, 1)
    camera(sc, "c1", 0, 1.8, (-3.3, 0.5, 0.3), (-3.4, 0.6, 0.28), (PUERTA[0] + 0.6, PUERTA[1] + 0.6, 0.0), lens=24)
    camera(sc, "c2", 1.8, dur, (-4.2, -0.9, 1.55), (-4.15, -0.8, 1.5), (-2.4, 1.4, 1.0), (-2.9, 1.35, 0.95), lens=24)


def s_lee(sc, dur):
    ps = reparto(["messi"])
    m = ps["messi"]
    vestuario()
    m.place((0, 1.0, 0), 0, 1)
    m.pose(1, shoulders=((-0.9, 0.2), (-0.9, -0.2)), elbows=(-0.9, -0.9))
    m.expresion(1, "neutral")
    m.mirar(1, 0, -0.45)
    m.cabeza(1, 0, 0.25, 0)
    m.expresion(F(1.2), "sorpresa")
    m.expresion(F(2.4), "picaro")
    m.mirar(F(2.4), 0, 0)
    m.cabeza(F(2.4), 0, 0.05, 0)
    c = carta((0, 0.52, 1.28), rot=(math.radians(72), 0, 0))
    vida(m, dur, 2)
    camera(sc, "c1", 0, dur, (0.05, -0.75, 1.6), (0.03, -0.5, 1.58), (0, 0.6, 1.45), (0, 0.65, 1.5), lens=32)


POS = {"cr7": (-1.45, 3.0), "haaland": (-0.48, 3.05), "kane": (0.48, 3.05), "mbappe": (1.45, 3.0),
       "messi": (-0.95, 2.0), "lamine": (0.0, 1.95), "neymar": (0.95, 2.0)}


def linea(ps, y=None, f=1):
    for k, (x, yy) in POS.items():
        if k in ps:
            ps[k].place((x, yy, 0), 0, f)


def s_llegan(sc, dur):
    ps = reparto()
    hinge = vestuario()
    abrir_puerta(hinge, 1, F(0.4))
    # cinco dentro, dos entrando por la puerta
    linea(ps)
    for k in ORDEN:
        ps[k].reposo(1)
        ps[k].expresion(1, "neutral")
    for k, t0 in (("neymar", 0.0), ("kane", 0.4)):
        dst = (*POS[k], 0)
        ps[k].place((PUERTA[0] + 0.3, PUERTA[1] + 0.5, 0), math.radians(-90), 1)
        ps[k].correr(F(t0 + 0.1), F(t0 + 1.6), (PUERTA[0] + 0.3, PUERTA[1] + 0.5, 0), dst, yaw=math.radians(-60),
                     pasos_s=1.8, amp=0.5)
        ps[k].place(dst, 0, F(t0 + 1.7))
        ps[k].reposo(F(t0 + 1.7))
    # se miran raro: cabezas y ojos a un lado y a otro
    rng = random.Random(5)
    for j, k in enumerate(ORDEN):
        p = ps[k]
        for n, t in enumerate((1.0, 1.9, 2.8)):
            s = rng.choice((-1, 1))
            p.cabeza(F(t + j * 0.05), 0.35 * s, 0, 0.05 * s)
            p.mirar(F(t + j * 0.05), 0.45 * s, 0)
        p.expresion(F(1.0 + j * 0.05), rng.choice(("picaro", "neutral", "enfadado")))
        vida(p, dur, 10 + j)
    camera(sc, "c1", 0, 2.2, (0.0, -2.6, 1.6), (0.0, -2.2, 1.55), (0, 2.5, 1.3), lens=24)
    camera(sc, "c2", 2.2, dur, (-0.5, -0.3, 1.75), (-0.48, -0.1, 1.75), (-0.5, 2.0, 1.75), lens=30)


def s_manias(sc, dur):
    ps = reparto(["cr7", "haaland", "messi"])
    cr, ha, me = ps["cr7"], ps["haaland"], ps["messi"]
    mate(me)
    vestuario()
    t1, t2 = 1.65, 3.25
    # Cristiano: sentadillas
    cr.place((0, 2.4, 0), 0, 1)
    cr.expresion(1, "enfadado")
    for i, f in enumerate(range(1, F(t1) + 1, 7)):
        abajo = i % 2 == 1
        cr.pose(f, hips=(-1.1, -1.1) if abajo else (0, 0), knees=(1.6, 1.6) if abajo else (0.05, 0.05),
                shoulders=((-1.4, 0.15), (-1.4, -0.15)), elbows=(-0.1, -0.1), lean=0.35 if abajo else 0.0,
                pelvis_z=-0.3 if abajo else 0.0)
    cr.place((0, 2.4, 0), 0, F(t1) - 1)
    cr.place(LEJOS, 0, F(t1))
    # Haaland: meditando en el suelo, con un aura dorada muy zen
    fuera([ha], 1)
    ha.place(LEJOS, 0, F(t1) - 1)
    ha.place((0, 2.2, 0), 0, F(t1))
    ha.pose(F(t1), hips=(-1.5, -1.5), knees=(2.0, 2.0), shoulders=((-0.3, 0.45), (-0.3, -0.45)), elbows=(-0.4, -0.4),
            pelvis_z=-(PELVIS_Z - 0.18))
    ha.expresion(F(t1), "feliz")
    ojos_cerrados(ha, F(t1))
    ha.place((0, 2.2, 0), 0, F(t2) - 1)
    ha.place(LEJOS, 0, F(t2))
    aura_anim((0, 2.2, 0), F(t1 + 0.2), F(t1 + 0.8), F(t2 - 0.05), F(t2), cam_dir=(0, -1), seed=21,
              col=(1.0, 0.5, 0.0), height=1.4)
    # Messi: en el banco con el mate
    fuera([me], 1)
    me.place(LEJOS, 0, F(t2) - 1)
    me.place((0.4, 3.8, 0), 0, F(t2))
    sentado_banco(me, F(t2))
    me.expresion(F(t2), "neutral")
    me.pose(F(t2 + 0.5), hips=(-1.5, -1.5), knees=(1.5, 1.5), shoulders=((0.05, 0.15), (-1.15, -0.25)),
            elbows=(-0.6, -2.3), lean=0.05, pelvis_z=-0.15)
    me.expresion(F(t2 + 0.5), "picaro")
    ojos_cerrados(me, F(t2 + 0.9))
    me.expresion(F(t2 + 1.2), "feliz")
    vida(cr, t1, 20)
    camera(sc, "c1", 0, t1, (0.9, -0.6, 1.3), (0.8, -0.4, 1.25), (0, 2.4, 1.1), lens=28)
    camera(sc, "c2", t1, t2, (0.2, -0.4, 0.9), (0.15, -0.2, 0.95), (0, 2.2, 0.85), lens=30)
    camera(sc, "c3", t2, dur, (0.85, 1.6, 1.45), (0.8, 1.75, 1.45), (0.4, 3.8, 1.35), lens=32)


def s_quien(sc, dur):
    ps = reparto()
    vestuario()
    linea(ps)
    for k in ORDEN:
        ps[k].reposo(1)
        ps[k].expresion(1, "neutral")
    la = ps["lamine"]
    la.pose(F(0.2), shoulders=((0.05, 0.12), (0.0, -2.7)), elbows=(-0.2, -0.3))
    hablar(la, F(0.2), F(1.3), "sorpresa", "grito", cada=4)
    la.reposo(F(1.6))
    xm, xb = POS["messi"][0], POS["mbappe"][0]
    for j, k in enumerate(ORDEN):
        p = ps[k]
        x = POS[k][0]
        for t, tx in ((1.6, xm), (2.5, xb)):
            if k in ("messi", "mbappe"):
                continue
            s = 1 if tx < x else -1
            p.cabeza(F(t + 0.04 * j), 0.45 * s, 0, 0)
            p.mirar(F(t + 0.04 * j), 0.45 * s, 0)
        if k not in ("messi", "mbappe"):
            p.expresion(F(1.7), "picaro")
        vida(p, dur, 30 + j)
    me, mb = ps["messi"], ps["mbappe"]
    me.expresion(F(1.8), "sorpresa")
    mb.expresion(F(2.6), "sorpresa")
    me.cabeza(F(2.7), -0.5, 0, 0)
    me.mirar(F(2.7), -0.45, 0)
    mb.cabeza(F(2.8), 0.5, 0, 0)
    mb.mirar(F(2.8), 0.45, 0)
    encoger(me, F(3.1))
    encoger(mb, F(3.15))
    camera(sc, "c1", 0, 1.5, (0.1, -0.3, 1.75), (0.1, -0.1, 1.75), (0.0, 1.95, 1.8), lens=32)
    camera(sc, "c2", 1.5, dur, (0.0, -2.6, 1.6), (0.0, -2.3, 1.6), (0, 2.5, 1.35), lens=24)


def s_apagon(sc, dur):
    ps = reparto()
    hinge = vestuario()
    linea(ps)
    for j, k in enumerate(ORDEN):
        p = ps[k]
        p.reposo(1)
        p.expresion(1, "neutral")
        p.mirar(F(0.9), 0, 0.4)
        p.cabeza(F(0.9), 0, -0.15, 0)
        p.expresion(F(1.0), "sorpresa")
        p.mirar(F(2.2), 0.5, 0)
        p.cabeza(F(2.2), 0.45, 0, 0)
        vida(p, dur, 40 + j)
    apagar(F(0.85), F(0.95), 0.015)
    abrir_puerta(hinge, 1, 2)
    cerrar_puerta(hinge, F(2.1), F(2.35))
    camera(sc, "c1", 0, dur, (0.0, -2.8, 1.6), (0.0, -2.2, 1.6), (-0.3, 2.5, 1.35), (-0.5, 2.4, 1.4), lens=24)


ESCENAS = {"carta": s_carta, "lee": s_lee, "llegan": s_llegan, "manias": s_manias, "quien": s_quien,
           "apagon": s_apagon}


def main():
    global OUT
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    OUT = out
    rw, rh = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (576, 1024)
    only = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    ESCENAS[name](sc, dur)
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
    setup_render(sc, rw, rh, FPS, F(dur), 16)
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
