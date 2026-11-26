"""«La Concentración», capítulo 2: El autobús. Parodia animada con caricaturas.
Uso: python -m ytauto.b3d.cap02 SALIDA_DIR ESCENA DURACION [ancho alto] [fotogramas,sueltos]"""
from __future__ import annotations

import math
import sys

import bpy
from mathutils import Vector

from . import cap01 as C1
from .autobus import FILAS, FONDO_Y, autobus, frenazo
from .cap01 import LEJOS, ORDEN, POS, fuera, linea, ojos_cerrados, reparto, sentado_banco
from .core import all_fcurves, cube, key, mat, setup_render, sphere, srgb, world
from .vestuario import LUCES, PUERTA, abrir_puerta, vestuario
from .video_anime import hablar
from .video_penalti import FPS, F, camera, encoger, vida


# ------------------------------------------------------------------ atrezo
def nota_tex(lineas, firma="— M"):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 700, 1000
    im = Image.new("RGB", (W, H), (246, 238, 214))
    d = ImageDraw.Draw(im)
    fb = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    f1, f2 = ImageFont.truetype(fb, 84), ImageFont.truetype(fb, 150)
    y = 120
    for line in lineas:
        if line:
            w = d.textlength(line, font=f1)
            d.text(((W - w) / 2, y), line, font=f1, fill=(30, 26, 24))
        y += 100
    d.text((W - 260, H - 230), firma, font=f2, fill=(160, 18, 28))
    path = f"{C1.OUT}/nota2.png"
    im.save(path)
    return path


def nota(loc, rot, lineas):
    m = bpy.data.materials.new("nota_m")
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    b = nt["Principled BSDF"]
    tx = nt.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(nota_tex(lineas))
    ln.new(tx.outputs["Color"], b.inputs["Base Color"])
    ln.new(tx.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = "nota"
    o.scale = (0.21, 0.3, 1)
    o.data.materials.append(m)
    return o


def encender(f0, f1, desde=0.015):
    for L in LUCES:
        e = L.data.energy
        L.data.energy = e * desde
        L.data.keyframe_insert("energy", frame=1)
        L.data.keyframe_insert("energy", frame=f0)
        L.data.energy = e
        L.data.keyframe_insert("energy", frame=f1)
    pm = bpy.data.materials.get("pantalla")
    if pm:
        s = pm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        v = s.default_value
        s.default_value = 0.0
        s.keyframe_insert("default_value", frame=f0)
        s.default_value = v
        s.keyframe_insert("default_value", frame=f1)


def sentado_bus(p, f, lean=0.0):
    sentado_banco(p, f, lean)


def manos_nuca(p, f):
    p.pose(f, hips=(-1.5, -1.5), knees=(1.5, 1.5), shoulders=((0.3, 2.6), (0.3, -2.6)), elbows=(-2.2, -2.2),
           lean=-0.25, pelvis_z=-0.15)


# ------------------------------------------------------------------ escenas
def s_luz(sc, dur):
    ps = reparto()
    hinge = vestuario()
    linea(ps)
    abrir_puerta(hinge, 1, 2, ang=-70)
    for j, k in enumerate(ORDEN):
        p = ps[k]
        p.reposo(1)
        p.expresion(1, "sorpresa")
        p.mirar(1, 0, 0.3)
        p.mirar(F(1.6), 0, -0.5)
        p.cabeza(F(1.6), 0, 0.35, 0)
        p.expresion(F(1.8), "neutral")
        vida(p, dur, 50 + j)
    encender(F(0.3), F(0.45))
    nota((0.0, 0.9, 0.003), (0, 0, 0.3), ["EL AUTOBÚS", "SALE A", "LAS 7", "", "NO LLEGUÉIS", "TARDE"])
    camera(sc, "c1", 0, 1.5, (0.0, -2.6, 1.6), (0.0, -2.3, 1.6), (0, 2.5, 1.35), lens=24)
    camera(sc, "c2", 1.5, dur, (0.15, 0.2, 0.95), (0.12, 0.3, 0.85), (0.0, 0.9, 0.0), lens=30)


def s_nota(sc, dur):
    ps = reparto(["kane"])
    k = ps["kane"]
    vestuario()
    k.place((0, 1.0, 0), 0, 1)
    k.pose(1, shoulders=((-0.9, 0.2), (-0.9, -0.2)), elbows=(-0.9, -0.9))
    k.expresion(1, "neutral")
    k.mirar(1, 0, -0.45)
    k.cabeza(1, 0, 0.25, 0)
    k.expresion(F(1.6), "sorpresa")
    nota((0, 0.5, 1.4), (math.radians(72), 0, 0), ["EL AUTOBÚS", "SALE A", "LAS 7", "", "NO LLEGUÉIS", "TARDE"])
    vida(k, dur, 60)
    camera(sc, "c1", 0, dur, (0.05, -0.8, 1.75), (0.03, -0.55, 1.73), (0, 0.6, 1.55), (0, 0.65, 1.6), lens=32)


def s_asientos(sc, dur):
    ps = reparto(["neymar", "cr7", "mbappe"])
    ne, cr, mb = ps["neymar"], ps["cr7"], ps["mbappe"]
    autobus(dur)
    # Neymar, repanchingado en el centro del asiento del fondo, manos en la nuca
    ne.place((0.0, FONDO_Y + 0.05, 0), 0, 1)
    ne.pose(1, hips=(-1.4, -1.4), knees=(0.35, 0.35), shoulders=((0.3, 2.6), (0.3, -2.6)), elbows=(-2.2, -2.2),
            lean=-0.55, pelvis_z=-0.12)
    ne.expresion(1, "feliz")
    ojos_cerrados(ne, 1)
    ojos_cerrados(ne, F(2.6), True)
    ne.expresion(F(3.0), "picaro")
    for up in ne.lids_up:
        key(up, F(3.0), rotation_euler=(math.radians(-30), 0, 0))
    # Cristiano y Mbappé, de pie en el pasillo, mosqueados
    cr.place((-0.6, FONDO_Y - 0.65, 0), 0.45, 1)
    mb.place((0.64, FONDO_Y - 0.62, 0), -0.45, 1)
    for p in (cr, mb):
        p.reposo(1)
        p.expresion(1, "enfadado")
    cr.pose(F(0.6), shoulders=((0.25, 0.75), (0.25, -0.75)), elbows=(-1.5, -1.5))
    mb.pose(F(0.9), shoulders=((0.25, 0.75), (0.25, -0.75)), elbows=(-1.5, -1.5))
    hablar(cr, F(0.6), F(2.2), "enfadado", "grito", cada=4)
    cr.cabeza(F(3.2), 0.4, 0, 0)
    mb.expresion(F(3.3), "triste")
    vida(cr, dur, 61)
    vida(mb, dur, 62)
    camera(sc, "c1", 0, dur, (0.0, FONDO_Y - 2.9, 1.7), (0.0, FONDO_Y - 2.6, 1.65), (0.0, FONDO_Y - 0.3, 1.05),
           lens=22)


def s_deberes(sc, dur):
    ps = reparto(["lamine", "haaland"])
    la, ha = ps["lamine"], ps["haaland"]
    # cuaderno y lápiz en las manos de Lamine; bocatas en el regazo de Haaland
    hand = world(bpy.data.objects["lamine_manoL"]).translation
    autobus(dur)
    y = FILAS[2]
    la.place((-0.72, y, 0), 0, 1)
    ha.place((0.72, y, 0), 0, 1)
    sentado_bus(la, 1)
    sentado_bus(ha, 1)
    la.pose(1, hips=(-1.5, -1.5), knees=(1.5, 1.5), shoulders=((-0.75, 0.25), (-0.85, -0.1)), elbows=(-1.3, -1.6),
            lean=0.25, pelvis_z=-0.15)
    cuaderno = cube("cuaderno", (-0.72, y - 0.38, 0.86), (0.13, 0.1, 0.006), mat("cuaderno_m", srgb(245, 245, 240),
                                                                                  0.6))
    cuaderno.rotation_euler = (math.radians(30), 0, 0)
    la.expresion(1, "enfadado")
    la.mirar(1, 0, -0.5)
    la.cabeza(1, 0, 0.35, 0)
    for i, f in enumerate(range(F(0.3), F(dur), 8)):          # escribe
        key(la.el["R"], f, rotation_euler=(-1.6 - 0.12 * (i % 2), 0, 0))
    la.cabeza(F(2.6), 0.35, 0.2, 0)
    la.mirar(F(2.6), 0.5, -0.1)
    la.expresion(F(2.7), "sorpresa")
    # Haaland y los bocatas
    pan = mat("pan", srgb(222, 170, 100), 0.6)
    for i in range(6):
        cube(f"bocata{i}", (0.72 + (i % 3 - 1) * 0.12, y - 0.42 + (i // 3) * 0.02, 0.62 + (i // 3) * 0.06),
             (0.05, 0.12, 0.035), pan)
    ha.expresion(1, "feliz")
    for i, f in enumerate(range(F(0.2), F(dur), 9)):           # mano a la boca, una y otra vez
        arriba = i % 2 == 0
        ha.pose(f, hips=(-1.5, -1.5), knees=(1.5, 1.5),
                shoulders=((0.05, 0.15), (-1.25, -0.25) if arriba else (-0.4, -0.2)),
                elbows=(-0.6, -2.3 if arriba else -0.8), lean=0.05, pelvis_z=-0.15)
        ha.expresion(f, "grito" if arriba else "feliz")
    vida(la, dur, 63)
    vida(ha, dur, 64)
    for nm in [o.name for o in bpy.data.objects if o.name.startswith(("as_L1", "as_R1"))]:
        bpy.data.objects.remove(bpy.data.objects[nm])         # fila de delante fuera: si no, tapa
    camera(sc, "c1", 0, dur, (0.0, y - 2.3, 1.75), (0.0, y - 2.1, 1.72), (0, y, 1.15), lens=22)


def s_kane(sc, dur):
    ps = reparto(["kane", "messi", "lamine", "neymar"])
    ka = ps["kane"]
    autobus(dur)
    ka.place((0.0, FILAS[1] - 0.1, 0), math.pi, 1)
    ka.reposo(1)
    ka.pose(F(0.2), shoulders=((-0.4, 0.6), (-0.4, -0.6)), elbows=(-1.4, -1.4))
    hablar(ka, F(0.1), F(1.3), "sorpresa", "grito", cada=4)
    for p, (x, y), s in ((ps["messi"], (-0.72, FILAS[2]), 65), (ps["lamine"], (0.72, FILAS[2]), 66),
                         (ps["neymar"], (-0.72, FILAS[3]), 67)):
        p.place((x, y, 0), 0, 1)
        sentado_bus(p, 1)
        p.expresion(1, "neutral")
        for n, t in enumerate((1.3, 1.6, 1.9, 2.2)):          # niegan con la cabeza
            p.cabeza(F(t + 0.05 * s % 3), 0.3 * (1 if n % 2 else -1), 0, 0)
        p.cabeza(F(2.5), 0, 0, 0)
        p.expresion(F(1.4), "triste")
        vida(p, dur, s)
    ka.expresion(F(1.9), "triste")
    vida(ka, dur, 68)
    camera(sc, "c1", 0, dur, (0.2, FILAS[3] + 0.3, 1.8), (0.15, FILAS[3] + 0.1, 1.78), (0, FILAS[1], 1.45), lens=24)


def s_frena(sc, dur):
    ps = reparto(["messi", "lamine", "cr7", "mbappe"])
    tf = 1.1
    pais = autobus(dur)
    frenazo(pais, F(tf), dur)
    sit = ((ps["messi"], (-0.72, FILAS[1])), (ps["lamine"], (0.72, FILAS[1])), (ps["cr7"], (-0.72, FILAS[2])),
           (ps["mbappe"], (0.72, FILAS[2])))
    for j, (p, (x, y)) in enumerate(sit):
        p.place((x, y, 0), 0, 1)
        sentado_bus(p, 1)
        p.expresion(1, "neutral")
        sentado_bus(p, F(tf))
        sentado_bus(p, F(tf + 0.15), lean=0.7)                  # latigazo hacia delante
        sentado_bus(p, F(tf + 0.5), lean=-0.05)
        p.expresion(F(tf + 0.1), "sorpresa")
        p.cabeza(F(tf + 0.7), 0.0, -0.1, 0)
        p.mirar(F(tf + 0.7), 0, 0)
        vida(p, dur, 70 + j)
    t2 = 2.6
    for p, _ in sit:
        p.expresion(F(t2 + 0.8), "grito")
    # plano 1: pasajeros; plano 2: el asiento del conductor, vacío, con la gorra
    cam1 = camera(sc, "c1", 0, t2, (0.3, 0.3, 1.9), (0.3, 0.35, 1.9), (0, FILAS[2] - 0.3, 1.0), lens=24)
    key(cam1, F(tf), location=Vector((0.3, 0.33, 1.9)))
    key(cam1, F(tf + 0.08), location=Vector((0.38, 0.45, 1.82)))
    key(cam1, F(tf + 0.18), location=Vector((0.27, 0.32, 1.92)))
    camera(sc, "c2", t2, dur, (0.3, -1.33, 1.25), (0.25, -1.3, 1.2), (-0.72, -0.9, 0.55), lens=22)


ESCENAS = {"luz": s_luz, "nota": s_nota, "asientos": s_asientos, "deberes": s_deberes, "kane": s_kane,
           "frena": s_frena}


def main():
    out, name, dur = sys.argv[1], sys.argv[2], float(sys.argv[3])
    C1.OUT = out
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
                kp.interpolation = "LINEAR" if o.name == "paisaje" else "BEZIER"
                if i + 1 < len(kps):
                    nf = kps[i + 1].co.x
                    if any(kp.co.x < c and c <= nf <= c + 1 for c in cuts):
                        kp.interpolation = "CONSTANT"
    setup_render(sc, rw, rh, FPS, F(dur), 12)
    sc.cycles.light_sampling_threshold = 0.05
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
