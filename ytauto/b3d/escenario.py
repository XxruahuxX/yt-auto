"""Estadio: césped con franjas y textura, líneas reglamentarias, portería con red de malla, balón de pentágonos,
gradas con público animado (cientos de aficionados con colores al azar), vallas LED con texto propio, techo y cielo.

Coordenadas: punto de penalti en (0, 0), línea de gol en y = GY, el campo crece hacia +y."""
from __future__ import annotations

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

from .core import attach, mat, noise_anim, smooth, sphere, srgb

GY = -11.0          # línea de gol
GW, GH = 3.66, 2.44  # media anchura y altura de la portería
HALF_W = 34.0


def _nodes(m):
    return m.node_tree.nodes, m.node_tree.links


# ------------------------------------------------------------------ cielo y sol
def cielo(sol_elev=38, sol_rot=150, fuerza=0.9):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("cielo")
    sc.world = w
    w.use_nodes = True
    nt, ln = w.node_tree.nodes, w.node_tree.links
    bg = nt["Background"]
    ok = False
    try:
        sky = nt.new("ShaderNodeTexSky")
        for t in ("MULTIPLE_SCATTERING", "NISHITA", "SINGLE_SCATTERING"):
            try:
                sky.sky_type = t
                ok = True
                break
            except TypeError:
                continue
        if ok:
            sky.sun_elevation = math.radians(sol_elev)
            sky.sun_rotation = math.radians(sol_rot)
            if hasattr(sky, "sun_disc"):
                sky.sun_disc = False
            ln.new(sky.outputs[0], bg.inputs[0])
            bg.inputs[1].default_value = 0.22 * fuerza
    except Exception:
        ok = False
    if not ok:
        bg.inputs[0].default_value = (*srgb(110, 170, 240), 1)
        bg.inputs[1].default_value = 0.8 * fuerza
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 20))
    sun = bpy.context.active_object
    sun.name = "sol"
    sun.data.energy = 4.5
    sun.data.angle = math.radians(3)
    sun.data.color = (1.0, 0.95, 0.86)
    sun.rotation_euler = (math.radians(90 - sol_elev), 0, math.radians(sol_rot - 180))
    return sun


# ------------------------------------------------------------------ césped
def cesped():
    m = bpy.data.materials.new("cesped")
    m.use_nodes = True
    nt, ln = _nodes(m)
    bsdf = nt["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    geo = nt.new("ShaderNodeNewGeometry")   # posición en metros (las coords de objeto van de -1 a 1)
    sep = nt.new("ShaderNodeSeparateXYZ")
    ln.new(geo.outputs["Position"], sep.inputs[0])
    div = nt.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = 5.5
    ln.new(sep.outputs["Y"], div.inputs[0])
    fl = nt.new("ShaderNodeMath"); fl.operation = "FLOOR"
    ln.new(div.outputs[0], fl.inputs[0])
    md = nt.new("ShaderNodeMath"); md.operation = "MODULO"; md.inputs[1].default_value = 2.0
    ln.new(fl.outputs[0], md.inputs[0])
    stripes = nt.new("ShaderNodeMix"); stripes.data_type = "RGBA"
    stripes.inputs["A"].default_value = (*srgb(72, 150, 58), 1)
    stripes.inputs["B"].default_value = (*srgb(104, 186, 80), 1)
    ln.new(md.outputs[0], stripes.inputs["Factor"])
    nz = nt.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 6
    ln.new(geo.outputs["Position"], nz.inputs["Vector"])
    var = nt.new("ShaderNodeMix"); var.data_type = "RGBA"; var.blend_type = "MULTIPLY"
    var.inputs["Factor"].default_value = 0.2
    ln.new(stripes.outputs["Result"], var.inputs["A"])
    ramp = nt.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.85, 0.88, 0.8, 1)
    ramp.color_ramp.elements[1].color = (1.1, 1.05, 1.0, 1)
    ln.new(nz.outputs["Fac"], ramp.inputs[0])
    ln.new(ramp.outputs[0], var.inputs["B"])
    ln.new(var.outputs["Result"], bsdf.inputs["Base Color"])
    # grano de hierba
    nz2 = nt.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 90; nz2.inputs["Detail"].default_value = 2
    ln.new(geo.outputs["Position"], nz2.inputs["Vector"])
    bump = nt.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
    ln.new(nz2.outputs["Fac"], bump.inputs["Height"])
    ln.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bpy.ops.mesh.primitive_plane_add(location=(0, 30, 0))
    p = bpy.context.active_object
    p.name = "cesped"
    p.scale = (60, 60, 1)
    p.data.materials.append(m)
    return p


def _strip(name, pts, width, m, z=0.004):
    """Línea pintada siguiendo una polilínea (x, y)."""
    verts, faces = [], []
    for i, (x, y) in enumerate(pts):
        a = Vector(pts[max(i - 1, 0)])
        b = Vector(pts[min(i + 1, len(pts) - 1)])
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x)) * width / 2
        verts += [(x + nrm.x, y + nrm.y, z), (x - nrm.x, y - nrm.y, z)]
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    return o


def lineas():
    m = mat("linea", srgb(245, 245, 240), 0.7)
    W = 0.12
    _strip("l_gol", [(-HALF_W, GY), (HALF_W, GY)], W, m)
    for sx in (-1, 1):
        _strip(f"l_banda{sx}", [(sx * HALF_W, GY), (sx * HALF_W, GY + 105)], W, m)
    a18, w18 = GY + 16.5, 20.16
    _strip("l_area", [(-w18, GY), (-w18, a18), (w18, a18), (w18, GY)], W, m)
    a6, w6 = GY + 5.5, 9.16
    _strip("l_area_peq", [(-w6, GY), (-w6, a6), (w6, a6), (w6, GY)], W, m)
    # media luna: arco de radio 9,15 alrededor del punto de penalti, fuera del área
    arc = []
    for i in range(41):
        a = math.radians(180) * i / 40
        x, y = 9.15 * math.cos(a), 9.15 * math.sin(a)
        if y >= a18 + 0.01:
            arc.append((x, y))
    if len(arc) > 1:
        _strip("l_medialuna", arc, W, m)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=0.002, location=(0, 0, 0.004))
    bpy.context.active_object.data.materials.append(m)
    # medio campo y círculo central
    hy = GY + 52.5
    _strip("l_medio", [(-HALF_W, hy), (HALF_W, hy)], W, m)
    _strip("l_circulo", [(9.15 * math.cos(a), hy + 9.15 * math.sin(a)) for a in
                         [2 * math.pi * i / 80 for i in range(81)]], W, m)


# ------------------------------------------------------------------ portería
def _net(name, corners, nu, nv, m):
    """Malla (cuadrícula) entre 4 esquinas, con modificador wireframe."""
    p00, p10, p11, p01 = [Vector(c) for c in corners]
    verts, faces = [], []
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            u = i / nu
            p = (p00 * (1 - u) + p10 * u) * (1 - v) + (p01 * (1 - u) + p11 * u) * v
            if j in (0, nv) or i in (0, nu):
                pass
            sag = math.sin(math.pi * u) * math.sin(math.pi * v) * 0.08
            verts.append((p.x, p.y + sag, p.z - sag * 0.5))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    wf = o.modifiers.new("hilos", "WIREFRAME")
    wf.thickness = 0.014
    wf.use_even_offset = True
    return o


def porteria():
    post = mat("poste", srgb(250, 250, 250), 0.25, coat=0.5)
    r = 0.06
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=GH, location=(sx * GW, GY, GH / 2), vertices=24)
        bpy.context.active_object.data.materials.append(post)
        smooth(bpy.context.active_object)
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=2 * GW + 2 * r, location=(0, GY, GH), vertices=24,
                                        rotation=(0, math.radians(90), 0))
    bpy.context.active_object.data.materials.append(post)
    smooth(bpy.context.active_object)
    # soportes traseros (finos, grises)
    sup = mat("soporte", srgb(170, 170, 175), 0.4)
    D, Dt = 2.0, 0.9   # fondo abajo y arriba
    for sx in (-1, 1):
        for a, b in (((sx * GW, GY - Dt, GH), (sx * GW, GY - D, 0)), ((sx * GW, GY, GH), (sx * GW, GY - Dt, GH))):
            a, b = Vector(a), Vector(b)
            d = b - a
            bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=d.length, location=(a + b) / 2, vertices=12)
            o = bpy.context.active_object
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = d.to_track_quat("Z", "Y")
            o.data.materials.append(sup)
    net = mat("red", srgb(245, 245, 245), 0.6)
    _net("red_fondo", [(-GW, GY - D, 0), (GW, GY - D, 0), (GW, GY - Dt, GH), (-GW, GY - Dt, GH)], 48, 18, net)
    _net("red_techo", [(-GW, GY - Dt, GH), (GW, GY - Dt, GH), (GW, GY, GH), (-GW, GY, GH)], 48, 6, net)
    for sx in (-1, 1):
        _net(f"red_lado{sx}", [(sx * GW, GY, 0), (sx * GW, GY - D, 0), (sx * GW, GY - Dt, GH), (sx * GW, GY, GH)],
             14, 18, net)


# ------------------------------------------------------------------ balón
def balon(loc=(0, 0, 0.11), r=0.11):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    ico = bpy.context.active_object
    dirs = [v.co.normalized() for v in ico.data.vertices]
    bpy.data.objects.remove(ico)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=loc)
    b = bpy.context.active_object
    b.name = "balon"
    b.data.materials.append(mat("balon_blanco", srgb(248, 248, 248), 0.35, coat=0.6))
    b.data.materials.append(mat("balon_negro", srgb(18, 18, 22), 0.35, coat=0.6))
    lim = math.cos(math.radians(19))
    for p in b.data.polygons:
        c = p.center.normalized()
        if max(c.dot(d) for d in dirs) > lim:
            p.material_index = 1
        p.use_smooth = True
    return b


# ------------------------------------------------------------------ vallas LED
def _led_image(path, txt, bg, fg, w=1024, h=96):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    font = None
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f):
            font = ImageFont.truetype(f, 64)
            break
    font = font or ImageFont.load_default()
    tw = d.textlength(txt, font=font)
    x = 20
    while x < w:
        d.text((x, 12), txt, fill=fg, font=font)
        x += tw + 80
    im.save(path)
    return path


def vallas(tmpdir="/tmp"):
    textos = [("DATOCRACK", (10, 20, 60), (255, 210, 40)), ("¡SUSCRÍBETE!", (200, 20, 40), (255, 255, 255)),
              ("DATOCRACK", (20, 120, 60), (255, 255, 255))]
    imgs = []
    for i, (t, bg, fg) in enumerate(textos):
        pth = _led_image(os.path.join(tmpdir, f"led_{i}.png"), t, bg, fg)
        m = bpy.data.materials.new(f"led{i}")
        m.use_nodes = True
        nt, ln = _nodes(m)
        bsdf = nt["Principled BSDF"]
        tex = nt.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(pth)
        ln.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        ln.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.6
        imgs.append(m)
    frame_m = mat("led_marco", srgb(25, 25, 30), 0.5)

    def board(name, center, length, rot, m):
        bpy.ops.mesh.primitive_cube_add(location=center)
        o = bpy.context.active_object
        o.name = name
        o.scale = (length / 2, 0.08, 0.45)
        o.rotation_euler = (0, 0, rot)
        o.data.materials.append(frame_m)
        from mathutils import Euler
        rz = Euler((0, 0, rot)).to_matrix()
        bpy.ops.mesh.primitive_plane_add(location=Vector(center) + rz @ Vector((0, 0.085, 0)))
        s = bpy.context.active_object
        s.name = name + "_pantalla"
        s.scale = (length / 2 - 0.03, 0.42, 1)
        s.rotation_euler = (math.radians(90), 0, rot + math.pi)
        s.data.materials.append(m)
        # UV a lo largo: el texto se repite sin estirarse
        uv = s.data.uv_layers.active.data
        for li, lp in enumerate(s.data.loops):
            co = s.data.vertices[lp.vertex_index].co
            uv[li].uv = ((co.x + 1) / 2 * length / 10.0, (co.y + 1) / 2)
        return o

    k = 0
    for x0 in range(-30, 30, 10):
        board(f"valla_fondo{k}", (x0 + 5, GY - 4.0, 0.47), 9.9, 0, imgs[k % 3])
        k += 1
    for sx in (-1, 1):
        for y0 in range(-8, 40, 10):
            board(f"valla_lado{sx}_{y0}", (sx * (HALF_W + 4), y0 + 5, 0.47), 9.9, sx * math.radians(90), imgs[k % 3])
            k += 1


# ------------------------------------------------------------------ gradas y público
def _fan_meshes():
    """Dos aficionados base (brazos abajo / brazos arriba), cada uno una sola malla con 2 materiales."""
    shirt = bpy.data.materials.new("afic_camiseta")
    shirt.use_nodes = True
    nt, ln = _nodes(shirt)
    info = nt.new("ShaderNodeObjectInfo")
    ramp = nt.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    cols = [(220, 30, 40), (255, 255, 255), (30, 80, 200), (255, 200, 30), (20, 20, 25), (40, 150, 70),
            (240, 120, 30), (120, 40, 160)]
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*srgb(*cols[0]), 1)
    els[1].position, els[1].color = 1 / len(cols), (*srgb(*cols[1]), 1)
    for i, c in enumerate(cols[2:], 2):
        e = els.new(i / len(cols))
        e.color = (*srgb(*c), 1)
    ln.new(info.outputs["Random"], ramp.inputs[0])
    ln.new(ramp.outputs[0], nt["Principled BSDF"].inputs["Base Color"])
    nt["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    skin = bpy.data.materials.new("afic_piel")
    skin.use_nodes = True
    nt, ln = _nodes(skin)
    info = nt.new("ShaderNodeObjectInfo")
    ramp = nt.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*srgb(110, 70, 45), 1)
    ramp.color_ramp.elements[1].color = (*srgb(250, 210, 180), 1)
    mth = nt.new("ShaderNodeMath"); mth.operation = "FRACT"
    mul = nt.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 7.31
    ln.new(info.outputs["Random"], mul.inputs[0])
    ln.new(mul.outputs[0], mth.inputs[0])
    ln.new(mth.outputs[0], ramp.inputs[0])
    ln.new(ramp.outputs[0], nt["Principled BSDF"].inputs["Base Color"])

    meshes = []
    for arms_up in (False, True):
        bm = bmesh.new()

        def blob(c, s, mi):
            ret = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
            for v in ret["verts"]:
                v.co = Vector((v.co.x * s[0] + c[0], v.co.y * s[1] + c[1], v.co.z * s[2] + c[2]))
            for f in {f for v in ret["verts"] for f in v.link_faces}:
                f.material_index = mi
                f.smooth = True

        blob((0, 0, 0.55), (0.2, 0.15, 0.32), 0)
        blob((0, 0, 1.0), (0.14, 0.14, 0.15), 1)
        for sx in (-1, 1):
            if arms_up:
                blob((sx * 0.2, 0, 1.15), (0.05, 0.05, 0.25), 0)
                blob((sx * 0.22, 0, 1.42), (0.06, 0.06, 0.06), 1)
            else:
                blob((sx * 0.21, 0, 0.55), (0.055, 0.055, 0.22), 0)
        me = bpy.data.meshes.new("aficionado_" + ("arriba" if arms_up else "abajo"))
        bm.to_mesh(me)
        bm.free()
        me.materials.append(shirt)
        me.materials.append(skin)
        meshes.append(me)
    return meshes


def gradas(semilla=7, filas=11, ocupacion=0.88, animar=True, fps=24):
    """Grada detrás de la portería y en los dos laterales cercanos, con público."""
    rng = random.Random(semilla)
    seat_m = mat("grada", srgb(60, 70, 95), 0.8)
    step_m = mat("grada_hormigon", srgb(150, 150, 158), 0.9)
    roof_m = mat("techo", srgb(120, 126, 138), 0.6)
    wall_m = mat("pared", srgb(170, 172, 180), 0.8)
    light_m = mat("foco", srgb(255, 250, 235), 0.2, emit=25.0)
    fans = _fan_meshes()
    crowd = bpy.data.collections.new("publico")
    bpy.context.scene.collection.children.link(crowd)
    RD, RH = 0.8, 0.42    # fondo y alto de cada fila

    def tribuna(name, origin, along, back, length):
        """origin: esquina delantera izquierda a ras de suelo; along/back: vectores unitarios (x, y)."""
        o = Vector((*origin, 0))
        a, b = Vector((*along, 0)), Vector((*back, 0))
        base_h = 1.2
        # muro frontal
        mid = o + a * (length / 2)
        bpy.ops.mesh.primitive_cube_add(location=mid + Vector((0, 0, base_h / 2)) - b * 0.1)
        w = bpy.context.active_object
        w.scale = (length / 2 if abs(a.x) > 0.5 else 0.1, length / 2 if abs(a.y) > 0.5 else 0.1, base_h / 2)
        w.data.materials.append(step_m)
        top = 0
        for r in range(filas):
            z = base_h + r * RH
            c = mid + b * (RD * (r + 0.5)) + Vector((0, 0, z / 2))
            bpy.ops.mesh.primitive_cube_add(location=c)
            st = bpy.context.active_object
            st.name = f"{name}_fila{r}"
            sx_, sy_ = (length / 2, RD / 2) if abs(a.x) > 0.5 else (RD / 2, length / 2)
            st.scale = (sx_, sy_, z / 2)
            st.data.materials.append(step_m if r % 2 else seat_m)
            n = int(length / 0.62)
            for i in range(n):
                if rng.random() > ocupacion:
                    continue
                p = o + a * ((i + 0.5) * length / n + rng.uniform(-0.08, 0.08)) + b * (RD * (r + 0.45)) + \
                    Vector((0, 0, z - 0.15))
                fan = bpy.data.objects.new(f"{name}_af{r}_{i}", fans[1 if rng.random() < 0.22 else 0])
                crowd.objects.link(fan)
                fan.location = p
                yaw = math.atan2(-b.y, -b.x) - math.pi / 2
                fan.rotation_euler = (0, 0, yaw + rng.uniform(-0.25, 0.25))
                s = rng.uniform(0.82, 1.0)
                fan.scale = (s, s, s * rng.uniform(0.95, 1.08))
                if animar:
                    noise_anim(fan, "location", 2, strength=rng.uniform(0.08, 0.2), scale=rng.uniform(4, 9),
                               phase=rng.uniform(0, 100), base=p.z)
            top = z
        # techo con focos
        depth = RD * filas
        rc = mid + b * (depth / 2 + 0.5) + Vector((0, 0, base_h + filas * RH + 2.2))
        bpy.ops.mesh.primitive_cube_add(location=rc)
        rf = bpy.context.active_object
        rf.scale = ((length / 2 + 1, depth / 2 + 1.5, 0.15) if abs(a.x) > 0.5 else (depth / 2 + 1.5, length / 2 + 1, 0.15))
        rf.data.materials.append(roof_m)
        for i in range(int(length / 6)):
            lc = o + a * (3 + i * 6) - b * 0.5 + Vector((0, 0, rc.z - 0.2))
            bpy.ops.mesh.primitive_cube_add(location=lc)
            lt = bpy.context.active_object
            lt.scale = (0.9, 0.25, 0.08) if abs(a.x) > 0.5 else (0.25, 0.9, 0.08)
            lt.data.materials.append(light_m)
        # relleno de luz para que la grada no quede negra bajo el techo
        lc = mid + b * (depth / 2) - b * 6 + Vector((0, 0, base_h + filas * RH * 0.6))
        bpy.ops.object.light_add(type="AREA", location=lc)
        L = bpy.context.active_object
        L.data.shape = "RECTANGLE"
        L.data.size, L.data.size_y = length, 4
        L.data.energy = 60 * length
        L.data.color = (1, 0.97, 0.92)
        L.rotation_euler = (b + Vector((0, 0, -0.25))).to_track_quat("-Z", "Y").to_euler()
        if abs(a.x) < 0.5:
            L.data.size, L.data.size_y = 4, length
        # pared trasera
        bc = mid + b * (depth + 0.2) + Vector((0, 0, (base_h + filas * RH + 2.2) / 2))
        bpy.ops.mesh.primitive_cube_add(location=bc)
        bw = bpy.context.active_object
        bw.scale = ((length / 2, 0.2, bc.z) if abs(a.x) > 0.5 else (0.2, length / 2, bc.z))
        bw.data.materials.append(wall_m)

    # fondo (detrás de la portería) y laterales cercanos
    tribuna("fondo", (-HALF_W - 6, GY - 6), (1, 0), (0, -1), 2 * HALF_W + 12)
    tribuna("lat_izq", (-HALF_W - 6, GY - 6), (0, 1), (-1, 0), 50)
    tribuna("lat_der", (HALF_W + 6, GY - 6 + 50), (0, -1), (1, 0), 50)
    return crowd


def estadio(publico=True, tmpdir="/tmp"):
    cielo()
    cesped()
    lineas()
    porteria()
    vallas(tmpdir)
    if publico:
        gradas()
