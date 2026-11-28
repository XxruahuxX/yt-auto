"""Hotel para «La Concentración»: habitación con una sola cama de matrimonio y pasillo con puertas.
Habitación: x de -2,5 a 2,5; y de -2,5 a 2,5 (cabecero en y≈2,2); colchón a MATT de altura.
Pasillo: x de -0,9 a 0,9; y de -1,5 a 11,5; la habitación 10 (puerta entreabierta) en la pared derecha, y = 10."""
from __future__ import annotations

import math

import bpy

from .core import cube, key, mat, pivot, sphere, srgb
from .vestuario import texto

MATT = 0.55          # altura de la cara de arriba del colchón
BED_Y = 1.0
HAB10_Y = 10.0
LUCES_H: list = []


def _mundo(nombre, col, fuerza):
    w = bpy.data.worlds.new(nombre)
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*srgb(*col), 1)
    bg.inputs[1].default_value = fuerza


def _area(loc, energy, size, col=(1.0, 0.95, 0.88), rot=(0, 0, 0)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    L = bpy.context.active_object
    L.data.energy, L.data.size, L.data.color = energy, size, col
    LUCES_H.append(L)
    return L


def reloj_tex(path, hora):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (400, 200), (8, 8, 10))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 130)
    w = d.textlength(hora, font=f)
    d.text(((400 - w) / 2, 22), hora, font=f, fill=(255, 40, 30))
    im.save(path)
    return path


def pantalla_reloj(nombre, path, loc):
    m = bpy.data.materials.new(nombre + "_m")
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    b = nt["Principled BSDF"]
    tx = nt.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path)
    ln.new(tx.outputs["Color"], b.inputs["Base Color"])
    ln.new(tx.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 3.0
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.pi / 2, 0, 0))
    o = bpy.context.active_object
    o.name, o.scale = nombre, (0.16, 0.08, 1)
    o.data.materials.append(m)
    return o


def habitacion(out, noche=False, sabana_y=BED_Y + 0.05, piernas=(-0.45, 0.45)):
    LUCES_H.clear()
    if noche:
        _mundo("noche", (20, 28, 60), 0.12)
    else:
        _mundo("hab", (70, 70, 80), 0.3)
    moqueta = mat("moqueta", srgb(120, 40, 50), 0.95)
    pared = mat("pared_hotel", srgb(226, 214, 190), 0.85)
    madera = mat("madera_hotel", srgb(110, 70, 42), 0.5, coat=0.2)
    blanco = mat("sabana", srgb(246, 246, 242), 0.8, sheen=0.3)
    cube("suelo_h", (0, 0, -0.01), (2.5, 2.5, 0.01), moqueta)
    cube("pared_h_fondo", (0, 2.55, 1.35), (2.5, 0.05, 1.35), pared)
    cube("pared_h_izq", (-2.55, 0, 1.35), (0.05, 2.5, 1.35), pared)
    cube("pared_h_der", (2.55, 0, 1.35), (0.05, 2.5, 1.35), pared)
    cube("pared_h_frente", (0, -2.55, 1.35), (2.5, 0.05, 1.35), pared)
    cube("techo_h", (0, 0, 2.75), (2.5, 2.5, 0.05), mat("techo_h", srgb(240, 238, 232), 0.9))
    # la cama (una sola)
    cube("cama_base", (0, BED_Y, 0.2), (0.96, 1.1, 0.2), madera, bevel=0.03)
    cube("colchon", (0, BED_Y, MATT - 0.08), (0.93, 1.07, 0.08), blanco, bevel=0.04)
    cube("cabecero", (0, BED_Y + 1.15, 0.85), (1.02, 0.05, 0.55), madera, bevel=0.03)
    for sx in (-1, 1):
        sphere(f"almohada{sx}", (sx * 0.45, BED_Y + 0.88, MATT + 0.06), (0.32, 0.15, 0.08), blanco)
        cube(f"mesita{sx}", (sx * 1.38, BED_Y + 0.9, 0.27), (0.25, 0.22, 0.27), madera, bevel=0.02)
    sabana(sabana_y, piernas)
    # reloj despertador en la mesita derecha (dos pantallas: 02:59 y 03:00)
    cube("reloj", (1.38, BED_Y + 0.85, 0.62), (0.18, 0.06, 0.09), mat("reloj_m", srgb(25, 25, 30), 0.4))
    r1 = pantalla_reloj("reloj_259", reloj_tex(f"{out}/reloj_259.png", "02:59"), (1.38, BED_Y + 0.785, 0.62))
    r2 = pantalla_reloj("reloj_300", reloj_tex(f"{out}/reloj_300.png", "03:00"), (1.38, BED_Y + 0.786, 0.62))
    # lámpara de la mesita izquierda
    cube("lampara_pie", (-1.38, BED_Y + 0.9, 0.7), (0.03, 0.03, 0.16), madera)
    sphere("lampara_pant", (-1.38, BED_Y + 0.9, 0.92), (0.15, 0.15, 0.12),
           mat("pantalla_lamp", srgb(250, 236, 200), 0.6, emit=0.0 if noche else 2.0))
    # ventana (pared derecha) con cortinas
    cielo = srgb(40, 60, 130) if noche else srgb(200, 225, 250)
    cube("ventana", (2.49, -0.4, 1.5), (0.01, 0.65, 0.6), mat("ventana_m", cielo, 0.3, emit=0.6 if noche else 3.0))
    cort = mat("cortina", srgb(150, 120, 80), 0.9, sheen=0.3)
    for sy in (-1, 1):
        cube(f"cortina{sy}", (2.44, -0.4 + sy * 0.8, 1.4), (0.03, 0.22, 0.95), cort)
    # puerta (pared izquierda)
    cube("puerta_h", (-2.49, -1.5, 1.05), (0.02, 0.5, 1.05), madera)
    cube("pomo_h", (-2.45, -1.15, 1.0), (0.03, 0.03, 0.03), mat("pomo", srgb(200, 170, 80), 0.3))
    # cuadro sobre el cabecero
    cube("cuadro", (0, 2.49, 1.85), (0.6, 0.01, 0.32), mat("cuadro_m", srgb(70, 120, 150), 0.6))
    if noche:
        _area((2.2, -0.4, 1.6), 130, 1.2, (0.55, 0.65, 1.0), rot=(0, math.radians(-90), 0))
        _area((0, -1.8, 2.4), 70, 2.0, (0.6, 0.7, 1.0), rot=(math.radians(35), 0, 0))
    else:
        _area((0, 0.4, 2.65), 260, 1.6)
        _area((0, -2.3, 1.8), 110, 3.0, rot=(math.radians(80), 0, 0))
    return r1, r2


def _tela():
    """Tela de sábana: rayas finas azul claro sobre blanco roto, con arrugas en relieve."""
    m = bpy.data.materials.new("sabana_tela")
    m.use_nodes = True
    nt, ln = m.node_tree.nodes, m.node_tree.links
    b = nt["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Sheen Weight"].default_value = 0.5
    tc = nt.new("ShaderNodeTexCoord")
    wv = nt.new("ShaderNodeTexWave")
    wv.wave_type, wv.bands_direction = "BANDS", "X"
    wv.inputs["Scale"].default_value = 9.0
    wv.inputs["Distortion"].default_value = 0.6
    ramp = nt.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (*srgb(238, 236, 228), 1)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (*srgb(120, 160, 205), 1)
    ln.new(tc.outputs["Object"], wv.inputs["Vector"])
    ln.new(wv.outputs["Fac"], ramp.inputs["Fac"])
    ln.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nz = nt.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 4.0
    bump = nt.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    ln.new(tc.outputs["Object"], nz.inputs["Vector"])
    ln.new(nz.outputs["Fac"], bump.inputs["Height"])
    ln.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def sabana(y_fin, piernas=(-0.45, 0.45), alto=0.2):
    """Sábana como malla: tapa el colchón desde los pies hasta y_fin, abombada sobre las piernas de cada uno
    (sin atravesarse: su parte alta queda por encima del muslo) y cae por los lados y por los pies."""
    import bmesh
    nx, ny = 64, 48
    x0, x1 = -1.02, 1.02
    y0 = BED_Y - 1.14
    pies_y = y_fin - 0.68                                        # las botas apuntan hacia arriba: más bulto
    bm = bmesh.new()
    grid = []
    for j in range(ny + 1):
        fila = []
        y = y0 + (y_fin - y0) * j / ny
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            z = MATT + 0.035
            for px in piernas:                                   # bulto de las piernas
                z += alto * math.exp(-((x - px) / 0.22) ** 4) * (1 + 0.9 * math.exp(-((y - pies_y) / 0.16) ** 2))
            z += 0.012 * math.sin(x * 23 + y * 7) * math.sin(y * 13)   # arrugas suaves
            if abs(x) > 0.94:                                    # cae por los lados
                z -= (abs(x) - 0.94) * 4.5
            if y < BED_Y - 1.07:                                 # cae por los pies
                z -= (BED_Y - 1.07 - y) * 4.5
            if j == ny:                                          # borde doblado
                z += 0.01
            fila.append(bm.verts.new((x, y, max(z, 0.12))))
        grid.append(fila)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    me = bpy.data.meshes.new("sabana")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("sabana", me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(_tela())
    for poly in me.polygons:
        poly.use_smooth = True
    sol = o.modifiers.new("grosor", "SOLIDIFY")
    sol.thickness = 0.012
    return o


def bota(nombre, loc, col, yaw=0.0):
    o = cube(nombre, loc, (0.045, 0.12, 0.045), mat(f"bota_{col}", srgb(*col), 0.4))
    o.rotation_euler = (0, 0, yaw)
    s = cube(nombre + "_suela", (loc[0], loc[1], 0.006), (0.047, 0.122, 0.006), mat("suela", srgb(240, 240, 240), 0.5))
    s.rotation_euler = (0, 0, yaw)
    return o


def pasillo():
    LUCES_H.clear()
    _mundo("pasillo", (15, 15, 25), 0.05)
    moq = mat("moqueta_p", srgb(90, 30, 40), 0.95)
    pared = mat("pared_p", srgb(200, 190, 168), 0.85)
    madera = mat("madera_hotel", srgb(110, 70, 42), 0.5, coat=0.2)
    cube("suelo_p", (0, 5, -0.01), (0.9, 6.5, 0.01), moq)
    cube("techo_p", (0, 5, 2.65), (0.9, 6.5, 0.05), mat("techo_h", srgb(240, 238, 232), 0.9))
    cube("fondo_p", (0, 11.55, 1.3), (0.9, 0.05, 1.3), pared)
    for sx in (-1, 1):
        if sx == -1:
            cube("pared_p-1", (-0.95, 5, 1.3), (0.05, 6.5, 1.3), pared)
        else:
            cube("pared_p1a", (0.95, (HAB10_Y - 0.5 - 1.5) / 2, 1.3), (0.05, (HAB10_Y - 0.5 + 1.5) / 2, 1.3), pared)
            cube("pared_p1b", (0.95, (HAB10_Y + 0.5 + 11.5) / 2, 1.3), (0.05, (11.5 - HAB10_Y - 0.5) / 2, 1.3), pared)
        for k, y in enumerate((1.0, 3.6, 6.2, 8.8)):
            if sx == 1 and y == 8.8:
                continue
            cube(f"puerta_p{sx}_{k}", (sx * 0.9, y, 1.05), (0.01, 0.45, 1.05), madera)
    # habitación 10: hueco con puerta entreabierta y luz de fiesta detrás
    y10 = HAB10_Y
    cube("pared_p1_tapa", (0.95, y10, 2.4), (0.05, 0.5, 0.25), pared)
    hinge = pivot("hinge10", (0.92, y10 - 0.45, 0))
    cube("puerta10", (0.92, y10, 1.05), (0.02, 0.45, 1.05), madera, hinge)
    hinge.rotation_euler = (0, 0, math.radians(-35))
    cube("placa10", (0.89, y10 - 0.75, 1.6), (0.01, 0.12, 0.08), mat("placa_dorada", srgb(200, 170, 80), 0.3))
    t = texto("num10", "10", (0.875, y10 - 0.75, 1.6), 0.12, mat("num_negro", srgb(20, 20, 20), 0.5),
              rot=(math.pi / 2, 0, -math.pi / 2))
    fiesta = mat("fiesta", srgb(255, 0, 200), 0.5, emit=6.0)
    cube("fiesta_fondo", (2.2, y10, 1.2), (0.02, 1.2, 1.4), fiesta)
    cube("fiesta_suelo", (1.6, y10, -0.005), (0.7, 0.6, 0.005), mat("moqueta_p", srgb(90, 30, 40), 0.95))
    for sz in (-1, 1):
        cube(f"hab10_lado{sz}", (1.6, y10 + sz * 0.55, 1.3), (0.6, 0.02, 1.3), pared)
    bpy.ops.object.light_add(type="POINT", location=(1.5, y10, 1.2))
    luz10 = bpy.context.active_object
    luz10.data.energy, luz10.data.shadow_soft_size = 120, 0.3
    # luces del pasillo: tenues; salida verde al fondo
    for y in (1.5, 5.0, 8.5):
        _area((0, y, 2.58), 14, 0.5, (1.0, 0.85, 0.65))
    cube("salida_p", (0, 11.48, 2.3), (0.22, 0.02, 0.08), mat("salida", srgb(30, 200, 90), 0.4, emit=4.0))
    return fiesta, luz10, t


def fiesta_anim(fiesta, luz, dur_f, cada=6):
    cols = [(1.0, 0.0, 0.8), (0.0, 0.8, 1.0), (1.0, 0.85, 0.0), (0.4, 1.0, 0.2)]
    s = fiesta.node_tree.nodes["Principled BSDF"].inputs["Emission Color"]
    for i, f in enumerate(range(1, dur_f + 1, cada)):
        c = cols[i % len(cols)]
        s.default_value = (*c, 1)
        s.keyframe_insert("default_value", frame=f)
        luz.data.color = c
        luz.data.keyframe_insert("color", frame=f)
    for fc in (fiesta.node_tree.animation_data.action.fcurves if hasattr(fiesta.node_tree.animation_data.action,
                                                                         "fcurves") else []):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def sombra(loc):
    """Silueta encapuchada con un saco al hombro."""
    negro = mat("sombra_m", srgb(8, 8, 10), 0.95)
    r = pivot("sombra", loc)
    sphere("sombra_cuerpo", (loc[0], loc[1], loc[2] + 0.85), (0.27, 0.2, 0.6), negro, r)
    sphere("sombra_cabeza", (loc[0], loc[1], loc[2] + 1.55), (0.15, 0.15, 0.17), negro, r)
    sphere("sombra_saco", (loc[0] + 0.25, loc[1] + 0.12, loc[2] + 1.45), (0.28, 0.24, 0.3),
           mat("saco", srgb(60, 45, 30), 0.95), r)
    for sx in (-1, 1):
        cube(f"sombra_pierna{sx}", (loc[0] + sx * 0.1, loc[1], loc[2] + 0.2), (0.06, 0.06, 0.22), negro, r)
    return r
