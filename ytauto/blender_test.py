"""Prueba 3D con Blender (bpy): nuestro personaje (cabeza redonda blanca, cuerpo ovalado con dorsal, brazos y
piernas finos) tira un penalti y el portero se tira. Luz de sol con sombras, cámara que se mueve.
Uso: python -m ytauto.blender_test salida_dir [ancho alto fps segundos]"""
from __future__ import annotations

import math
import sys

import bpy
from mathutils import Vector

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/bt"
RW, RH = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (540, 960)
FPS = int(sys.argv[4]) if len(sys.argv) > 4 else 30
SECS = float(sys.argv[5]) if len(sys.argv) > 5 else 8.0
N = int(FPS * SECS)


def mat(name, col, rough=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def srgb(r, g, b):
    f = lambda v: (v / 255) ** 2.2
    return (f(r), f(g), f(b))


def obj(op, name, loc, scale=(1, 1, 1), m=None, parent=None, **kw):
    op(location=loc, **kw)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    if m:
        o.data.materials.append(m)
    if parent:
        o.parent = parent
    bpy.ops.object.shade_smooth() if hasattr(o.data, "polygons") else None
    return o


def limb(name, a, b, r, m, parent):
    """Cilindro fino de a a b (coordenadas locales del padre)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=(a + b) / 2, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    o.parent = parent
    return o


def pivot(name, loc, parent=None):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.active_object
    e.name = name
    if parent:
        e.parent = parent
    return e


def cone_to(name, base, tip, r, m, parent):
    """Cono (mechón) con la base en `base` y la punta en `tip`."""
    a, b = Vector(base), Vector(tip)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.005, depth=d.length, location=(a + b) / 2, vertices=12)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    o.parent = parent
    bpy.ops.object.shade_smooth()
    return o


def player(name, kit, num, loc, gloves=False, hair_col=(24, 18, 14), skin_col=(255, 226, 204)):
    root = pivot(name, loc)
    skin, ink = mat(name + "_piel", srgb(*skin_col), 0.45), mat(name + "_tinta", srgb(14, 12, 20), 0.3)
    hairm = mat(name + "_pelo", srgb(*hair_col), 0.5)
    shirt, legs = mat(name + "_cam", srgb(*kit), 0.6), mat(name + "_pant", srgb(36, 44, 92), 0.6)
    whitem, mouthm = mat(name + "_bl", (1, 1, 1), 0.25), mat(name + "_boca", srgb(120, 20, 30), 0.4)
    obj(bpy.ops.mesh.primitive_uv_sphere_add, name + "_cuerpo", (0, 0, 1.05), (0.33, 0.28, 0.55), shirt, root,
        segments=32, ring_count=16)
    hz, hr = 1.92, 0.34
    obj(bpy.ops.mesh.primitive_uv_sphere_add, name + "_cabeza", (0, 0, hz), (hr,) * 3, skin, root, segments=32, ring_count=16)
    # pelo: casquete echado hacia atrás (se ve la frente) + mechones de punta
    obj(bpy.ops.mesh.primitive_uv_sphere_add, name + "_casco", (0, 0.05, hz + 0.06), (0.35, 0.34, 0.3), hairm, root,
        segments=32, ring_count=16)
    for i in range(13):
        az = i / 13 * 2 * math.pi
        el = math.radians(35 + 25 * (i % 2))
        dvec = Vector((math.cos(az) * math.cos(el), 0.08 + math.sin(az) * math.cos(el) * 0.9, math.sin(el)))
        if dvec.y < -0.45:      # nada de mechones tapando la cara
            dvec.y = -0.45
            dvec.z += 0.25
        dvec.normalize()
        base = Vector((0, 0.05, hz + 0.06)) + dvec * 0.27
        cone_to(f"{name}_mechon{i}", base, base + dvec * 0.2 + Vector((0, 0.04, 0.05)), 0.1, hairm, root)
    cone_to(f"{name}_tupe", (0, -0.15, hz + 0.3), (0, -0.33, hz + 0.42), 0.12, hairm, root)
    # cara: ojos grandes (blanco + pupila), cejas, nariz y boca
    for sx in (-1, 1):
        obj(bpy.ops.mesh.primitive_uv_sphere_add, name + f"_ojo{sx}", (sx * 0.12, -0.285, hz + 0.05), (0.08, 0.05, 0.095),
            whitem, root)
        obj(bpy.ops.mesh.primitive_uv_sphere_add, name + f"_pupila{sx}", (sx * 0.115, -0.33, hz + 0.04), (0.042, 0.02, 0.05),
            ink, root)
        cj = obj(bpy.ops.mesh.primitive_cube_add, name + f"_ceja{sx}", (sx * 0.13, -0.3, hz + 0.17), (0.075, 0.02, 0.022),
                 hairm, root)
        cj.rotation_euler = (0, sx * math.radians(-12), 0)
    obj(bpy.ops.mesh.primitive_uv_sphere_add, name + "_nariz", (0, -0.345, hz - 0.04), (0.05, 0.04, 0.045), skin, root)
    obj(bpy.ops.mesh.primitive_uv_sphere_add, name + "_boca", (0, -0.31, hz - 0.15), (0.11, 0.035, 0.035), mouthm, root)
    for sx in (-1, 1):   # orejas
        obj(bpy.ops.mesh.primitive_uv_sphere_add, name + f"_oreja{sx}", (sx * 0.34, 0.02, hz - 0.01), (0.04, 0.07, 0.09), skin, root)
    # dorsal en la espalda y en el pecho
    for side, y in (("d", 0.29), ("p", -0.29)):
        bpy.ops.object.text_add(location=(0, y, 1.08))
        tx = bpy.context.active_object
        tx.name = name + "_num" + side
        tx.data.body = num
        tx.data.align_x = "CENTER"
        tx.data.align_y = "CENTER"
        tx.data.size = 0.36
        tx.data.extrude = 0.01
        tx.rotation_euler = (math.radians(90), 0, math.radians(180) if side == "d" else 0)
        tx.data.materials.append(whitem)
        tx.parent = root
    joints = {}
    hand = mat(name + "_guante", srgb(170, 230, 60), 0.5) if gloves else skin
    for sx, nm in ((-1, "L"), (1, "R")):
        hip = pivot(f"{name}_cadera{nm}", (sx * 0.14, 0, 0.62), root)
        limb(f"{name}_pierna{nm}", (0, 0, 0), (0, 0, -0.56), 0.06, legs, hip)
        obj(bpy.ops.mesh.primitive_uv_sphere_add, f"{name}_bota{nm}", (0, -0.08, -0.6), (0.11, 0.18, 0.08), ink, hip)
        sh = pivot(f"{name}_hombro{nm}", (sx * 0.31, 0, 1.36), root)
        obj(bpy.ops.mesh.primitive_uv_sphere_add, f"{name}_hombrera{nm}", (0, 0, 0), (0.1,) * 3, shirt, sh)
        limb(f"{name}_manga{nm}", (0, 0, 0), (sx * 0.07, 0, -0.27), 0.085, shirt, sh)
        limb(f"{name}_antebrazo{nm}", (sx * 0.07, 0, -0.25), (sx * 0.12, 0, -0.55), 0.06, skin, sh)
        obj(bpy.ops.mesh.primitive_uv_sphere_add, f"{name}_mano{nm}", (sx * 0.12, 0, -0.6), ((0.1 if not gloves else 0.13),) * 3,
            hand, sh)
        joints[nm] = (hip, sh)
    return root, joints


def key(o, f, **props):
    for k, v in props.items():
        setattr(o, k, v)
        o.keyframe_insert(data_path=k, frame=f)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, N

    # cielo
    w = bpy.data.worlds.new("cielo")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*srgb(80, 155, 240), 1)
    bg.inputs[1].default_value = 0.8

    # césped con franjas
    for i in range(-8, 9):
        col = srgb(70, 160, 70) if i % 2 else srgb(84, 178, 82)
        obj(bpy.ops.mesh.primitive_plane_add, f"franja{i}", (0, i * 2.0, 0), (30, 1.0, 1), mat(f"cesped{i}", col, 0.9))
    white = mat("linea", (1, 1, 1), 0.6)
    obj(bpy.ops.mesh.primitive_plane_add, "linea_area", (0, -5.5, 0.005), (8, 0.05, 1), white)
    obj(bpy.ops.mesh.primitive_cylinder_add, "punto", (0, 0, 0.006), (0.12, 0.12, 0.002), white)
    # portería
    gx, gy, gh = 3.66, -11.0, 2.44
    post = mat("poste", (1, 1, 1), 0.3)
    for sx in (-1, 1):
        obj(bpy.ops.mesh.primitive_cylinder_add, f"poste{sx}", (sx * gx, gy, gh / 2), (0.06, 0.06, gh / 2), post)
    lb = obj(bpy.ops.mesh.primitive_cylinder_add, "larguero", (0, gy, gh), (0.06, 0.06, gx), post)
    lb.rotation_euler = (0, math.radians(90), 0)
    net = mat("red", (1, 1, 1), 0.8)
    net.blend_method = "BLEND" if hasattr(net, "blend_method") else None
    nb = net.node_tree.nodes["Principled BSDF"]
    nb.inputs["Alpha"].default_value = 0.35
    obj(bpy.ops.mesh.primitive_plane_add, "red_fondo", (0, gy - 1.5, gh / 2), (gx, 1, gh / 2), net).rotation_euler = (math.radians(90), 0, 0)
    # grada de fondo
    for i in range(6):
        obj(bpy.ops.mesh.primitive_cube_add, f"grada{i}", (0, -24 - i * 1.2, 1 + i * 1.3), (30, 0.6, 0.65),
            mat(f"grada{i}", srgb(60 + i * 8, 64 + i * 6, 90 + i * 8), 0.9))

    # balón
    ball = obj(bpy.ops.mesh.primitive_ico_sphere_add, "balon", (0, 0, 0.11), (0.11, 0.11, 0.11), mat("balon", (1, 1, 1), 0.4),
               subdivisions=3)
    # jugadores
    yo, jy = player("yo", (46, 120, 210), "9", (0.4, 2.6, 0))
    gk, jg = player("portero", (255, 140, 30), "1", (0, gy + 0.4, 0), gloves=True)
    gk.rotation_euler = (0, 0, math.radians(180))

    # --- animación
    f = lambda s: int(1 + s * FPS)
    # carrera: del 0,6 s al 2,0 s, braceo y zancada alternos
    t_kick = 2.0
    for i in range(0, f(t_kick) + 1, 2):
        s = i / FPS
        k = min(1.0, max(0.0, (s - 0.6) / (t_kick - 0.6)))
        key(yo, i or 1, location=Vector((0.4 - 0.4 * k, 2.6 - 2.2 * k, 0.04 * abs(math.sin(s * 12)) * (0 < k < 1))))
        sw = math.sin(s * 12) * 0.7 * (0 < k < 1)
        for nm, sg in (("L", 1), ("R", -1)):
            hip, sh = jy[nm]
            key(hip, i or 1, rotation_euler=(sg * sw, 0, 0))
            key(sh, i or 1, rotation_euler=(-sg * sw, 0, 0))
    # chute con la derecha
    hipR = jy["R"][0]
    key(hipR, f(t_kick - 0.15), rotation_euler=(1.1, 0, 0))
    key(hipR, f(t_kick + 0.05), rotation_euler=(-1.3, 0, 0))
    key(hipR, f(t_kick + 0.5), rotation_euler=(0, 0, 0))
    for sh, a in ((jy["L"][1], (0, 0.9, 0)), (jy["R"][1], (0, -0.9, 0))):
        key(sh, f(t_kick), rotation_euler=a)
    # balón a la escuadra derecha
    key(ball, f(t_kick), location=Vector((0, 0, 0.11)))
    tgt = Vector((2.9, gy + 0.2, 2.1))
    for j in range(1, 9):
        u = j / 8
        p = Vector((0, 0, 0.11)).lerp(tgt, u)
        p.z += math.sin(u * math.pi) * 0.6
        key(ball, f(t_kick + 0.9 * u), location=p)
    key(ball, f(t_kick + 0.9), rotation_euler=(0, 0, 0))
    ball.rotation_euler = (12, 3, 0)
    ball.keyframe_insert("rotation_euler", frame=f(t_kick + 0.9))
    key(ball, f(t_kick + 1.4), location=Vector((2.7, gy - 1.2, 0.8)))
    key(ball, f(t_kick + 2.0), location=Vector((2.4, gy - 1.3, 0.11)))
    # portero: balanceo y estirada tardía hacia el otro lado... luego al bueno
    for i in range(1, f(t_kick) + 1, 3):
        s = i / FPS
        key(gk, i, location=Vector((0.25 * math.sin(s * 3), gy + 0.4, 0)))
        for nm in ("L", "R"):
            key(jg[nm][1], i, rotation_euler=(0, (-0.9 if nm == "R" else 0.9) + 0.1 * math.sin(s * 6), 0))
    key(gk, f(t_kick + 0.25), location=Vector((0.2, gy + 0.4, 0.0)), rotation_euler=(0, 0, math.radians(180)))
    key(gk, f(t_kick + 0.75), location=Vector((2.0, gy + 0.4, 1.0)), rotation_euler=(0, math.radians(-75), math.radians(180)))
    key(gk, f(t_kick + 1.3), location=Vector((2.6, gy + 0.4, 0.3)), rotation_euler=(0, math.radians(-90), math.radians(180)))
    # celebración
    for nm in ("L", "R"):
        key(jy[nm][1], f(t_kick + 1.3), rotation_euler=(0, 0, 0))
        key(jy[nm][1], f(t_kick + 1.7), rotation_euler=(0, (2.6 if nm == "L" else -2.6), 0))
    # celebración: corre hacia la cámara, saltando y con los brazos arriba
    key(yo, f(t_kick + 1.3), location=Vector((0, 0.3, 0)), rotation_euler=(0, 0, 0))
    for i in range(f(t_kick + 1.4), N + 1, 3):
        s = i / FPS
        u = (s - t_kick - 1.4) / (SECS - t_kick - 1.4)
        key(yo, i, location=Vector((0.3 * u, 0.3 - 2.0 * u, 0.22 * abs(math.sin(s * 8)))))
        sw = math.sin(s * 16) * 0.6
        for nm, sg in (("L", 1), ("R", -1)):
            key(jy[nm][0], i, rotation_euler=(sg * sw, 0, 0))
            key(jy[nm][1], i, rotation_euler=(0, (2.5 if nm == "L" else -2.5) + sg * 0.35 * math.sin(s * 10), 0))

    # luces
    bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 5.5
    sun.data.color = (1.0, 0.95, 0.88)
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

    # cámaras: 4 planos con corte seco (marcadores), cada uno con un leve travelling
    def camera(nm, t0, t1, p0, p1, tgt0, tgt1=None, lens=30, follow=None):
        bpy.ops.object.camera_add()
        cm = bpy.context.active_object
        cm.name = nm
        cm.data.lens = lens
        c = cm.constraints.new("TRACK_TO")
        c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        if follow:
            c.target = follow
        else:
            tr = pivot(nm + "_mira", tgt0)
            c.target = tr
            key(tr, f(t0), location=Vector(tgt0))
            key(tr, f(t1), location=Vector(tgt1 or tgt0))
        key(cm, f(t0), location=Vector(p0))
        key(cm, f(t1), location=Vector(p1))
        mk = sc.timeline_markers.new(nm, frame=f(t0))
        mk.camera = cm
        if t0 == 0:
            sc.camera = cm
        return cm

    camera("cara", 0, 1.0, (0.2, 0.7, 2.0), (0.3, 1.1, 1.95), (0.4, 2.6, 1.8), lens=32)
    camera("detras", 1.0, t_kick + 0.4, (2.2, 7.5, 2.4), (0.9, 4.0, 1.6), (0, -3, 1.0), (0, -6, 1.2), lens=28)
    camera("porteria", t_kick + 0.4, t_kick + 2.2, (6.0, -5.5, 1.5), (5.0, -6.5, 1.7), (2.0, gy, 1.3), (2.4, gy, 1.2), lens=30)
    head = bpy.data.objects["yo_cabeza"]
    camera("celebra", t_kick + 2.2, SECS, (0.4, -2.6, 1.8), (0.6, -3.8, 1.9), None, lens=30, follow=head)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            for fc in getattr(o.animation_data.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"

    # render
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 20
    sc.cycles.use_denoising = True
    sc.render.use_freestyle = False
    sc.render.line_thickness_mode = "ABSOLUTE"
    sc.render.line_thickness = 1.6
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = OUT + "/f_"
    if len(sys.argv) > 6:   # solo algunos fotogramas, para revisar
        for fr in map(int, sys.argv[6].split(",")):
            sc.frame_set(fr)
            sc.render.filepath = f"{OUT}/s_{fr:04d}.png"
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
