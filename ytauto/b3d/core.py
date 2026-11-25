"""Utilidades comunes: materiales, primitivas, articulaciones, calcomanías sobre esferas y keyframes."""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector


def srgb(r, g, b):
    f = lambda v: (v / 255) ** 2.2
    return (f(r), f(g), f(b))


_MATS: dict[str, bpy.types.Material] = {}


def mat(name, col, rough=0.55, emit=0.0, sheen=0.0, coat=0.0):
    """Material Principled. col en lineal (usa srgb())."""
    if name in _MATS and _MATS[name].name in bpy.data.materials:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    _MATS[name] = m
    return m


def skin_mat(name, col):
    """Piel con un poco de subsurface para que no parezca plástico."""
    m = mat(name, col, 0.5)
    b = m.node_tree.nodes["Principled BSDF"]
    try:
        b.inputs["Subsurface Weight"].default_value = 0.15
        b.inputs["Subsurface Radius"].default_value = (0.6, 0.25, 0.15)
        b.inputs["Subsurface Scale"].default_value = 0.05
    except KeyError:
        pass
    return m


def attach(o, parent):
    """Emparenta conservando la posición en el mundo."""
    if parent is None:
        return o
    o.parent = parent
    o.matrix_parent_inverse = world(parent).inverted()
    return o


def world(o):
    """Matriz de mundo calculada a mano (sin view_layer.update, que es lento con miles de objetos)."""
    if o.parent is None:
        return o.matrix_basis.copy()
    return world(o.parent) @ o.matrix_parent_inverse @ o.matrix_basis


def smooth(o):
    if hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True


def sphere(name, loc, scale, m, parent=None, seg=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, segments=seg, ring_count=rings)
    o = bpy.context.active_object
    o.name, o.scale = name, scale
    if m:
        o.data.materials.append(m)
    attach(o, parent)
    smooth(o)
    return o


def cube(name, loc, scale, m, parent=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name, o.scale = name, scale
    if m:
        o.data.materials.append(m)
    attach(o, parent)
    if bevel:
        md = o.modifiers.new("bisel", "BEVEL")
        md.width, md.segments = bevel, 3
    return o


def pivot(name, loc, parent=None):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.active_object
    e.name = name
    e.empty_display_size = 0.1
    attach(e, parent)
    return e


def limb(name, a, b, r, m, parent, r2=None, verts=20, caps=True):
    """Tubo de a a b (coordenadas del padre) con extremos redondeados (si caps)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2 if r2 is not None else r, depth=d.length,
                                    location=(a + b) / 2, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    attach(o, parent)
    smooth(o)
    if caps:
        sphere(name + "_a", a, (r,) * 3, m, parent, 20, 10)
        sphere(name + "_b", b, ((r2 if r2 is not None else r),) * 3, m, parent, 20, 10)
    return o


def cone_to(name, base, tip, r, m, parent, bend=None):
    """Cono (mechón). bend: vector que curva la punta (añade un segundo tramo)."""
    a, b = Vector(base), Vector(tip)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.004, depth=d.length, location=(a + b) / 2, vertices=14)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(m)
    attach(o, parent)
    smooth(o)
    return o


def dome(name, loc, scale, m, parent=None, keep="top", seg=32, rings=16):
    """Media esfera (keep='top' deja z>=0, 'bottom' z<=0). Útil para párpados y pantalón."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    kill = [v for v in bm.verts if (v.co.z < -1e-4 if keep == "top" else v.co.z > 1e-4)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location, o.scale = loc, scale
    o.data.materials.append(m)
    attach(o, parent)
    smooth(o)
    sol = o.modifiers.new("grosor", "SOLIDIFY")
    sol.thickness = 0.04
    return o


def decal(name, shapes: dict[str, list[tuple[float, float]]], center, radius, lift, m, parent, base=None):
    """Calcomanía con forma de polígono sobre la superficie frontal (-Y) de una esfera.
    shapes: {nombre: [(x, z), ...]} todas con el mismo nº de puntos (perímetro, en coordenadas de cara relativas
    al centro de la esfera). La primera es la forma base; el resto se convierten en shape keys."""
    names = list(shapes)
    base = base or names[0]
    cx, cy, cz = center
    R = radius + lift

    def proj(x, z):
        h = max(R * R - x * x - z * z, 1e-6)
        return Vector((cx + x, cy - math.sqrt(h), cz + z))

    K = 5

    def ring(pts):
        mx = sum(p[0] for p in pts) / len(pts)
        mz = sum(p[1] for p in pts) / len(pts)
        out = [proj(mx, mz)]
        for r in range(1, K + 1):
            u = r / K
            out += [proj(mx + (x - mx) * u, mz + (z - mz) * u) for x, z in pts]
        return out

    pts0 = ring(shapes[base])
    n = len(shapes[base])
    me = bpy.data.meshes.new(name)
    faces = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    for r in range(1, K):
        a0, a1 = 1 + (r - 1) * n, 1 + r * n
        faces += [(a0 + i, a1 + i, a1 + (i + 1) % n, a0 + (i + 1) % n) for i in range(n)]
    me.from_pydata([tuple(p) for p in pts0], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    smooth(o)
    o.shape_key_add(name="Basis")
    for nm in names:
        if nm == base:
            continue
        sk = o.shape_key_add(name=nm)
        for i, p in enumerate(ring(shapes[nm])):
            sk.data[i].co = p
    attach(o, parent)
    return o


def key(o, f, **props):
    for k, v in props.items():
        setattr(o, k, v)
        o.keyframe_insert(data_path=k, frame=f)


def key_shape(o, f, weights: dict[str, float]):
    kb = o.data.shape_keys.key_blocks
    for kname in kb.keys()[1:]:
        kb[kname].value = weights.get(kname, 0.0)
        kb[kname].keyframe_insert("value", frame=f)


def noise_anim(o, path, index, strength, scale, phase, base=None):
    """Movimiento continuo con un modificador de ruido en la F-curve (barato para cientos de objetos)."""
    if base is not None:
        v = getattr(o, path)
        v[index] = base
    o.keyframe_insert(data_path=path, index=index, frame=1)
    fc = o.animation_data.action.fcurves.find(path, index=index) if hasattr(o.animation_data.action, "fcurves") else None
    if fc is None:
        fc = _find_fcurve(o, path, index)
    md = fc.modifiers.new("NOISE")
    md.strength, md.scale, md.phase = strength, scale, phase
    return fc


def _find_fcurve(o, path, index):
    """Blender 5: las acciones tienen capas/canales; buscamos la F-curve en el slot del objeto."""
    act = o.animation_data.action
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            bag = strip.channelbag(o.animation_data.action_slot)
            for fc in bag.fcurves:
                if fc.data_path == path and fc.array_index == index:
                    return fc
    raise RuntimeError(f"sin fcurve {path}[{index}] en {o.name}")


def all_fcurves(o):
    ad = o.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            try:
                out += list(strip.channelbag(ad.action_slot).fcurves)
            except Exception:
                pass
    return out


def setup_render(sc, w, h, fps, frames, samples=20):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.use_freestyle = False
    sc.render.use_persistent_data = True
    c = sc.cycles
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces = 4, 2, 2
    c.transmission_bounces, c.volume_bounces, c.transparent_max_bounces = 2, 0, 8
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.04
    c.caustics_reflective = c.caustics_refractive = False
    sc.render.threads_mode = "AUTO"
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.render.image_settings.file_format = "PNG"
