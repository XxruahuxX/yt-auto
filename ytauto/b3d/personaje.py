"""Personaje del canal en 3D: cabeza redonda, cara con expresiones (boca con shape keys, ojos que miran,
párpados, cejas), cuerpo con rodillas y codos, equipación completa y varios peinados.

Uso:
    p = Personaje("yo", kit=(46, 120, 210), num="9", pelo="pinchos").build()
    p.place((0, 2, 0), yaw=0)
    p.expresion(frame, "feliz"); p.parpadeo(frame); p.mirar(frame, yaw, pitch)
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from .core import (attach, cone_to, cube, decal, dome, key, key_shape, limb, mat, pivot, skin_mat, smooth,
                   sphere, srgb)

# --- alturas (el personaje se construye en el origen, pies en z=0) -----------------------------------
PELVIS_Z = 0.62
NECK_Z = 1.55
HEAD_C = Vector((0, 0, 1.92))
HEAD_R = 0.34

# --- boca: polígonos paramétricos (todas con el mismo nº de puntos) ----------------------------------
NM = 16  # puntos por labio


def _mouth(w, corner, up, open_, p=1.0, skew=0.0, cz=-0.15):
    def upper(t):
        return cz + corner * t * t + up * (1 - t * t) ** p + skew * t

    def lower(t):
        return cz + corner * t * t - open_ * (1 - t * t) ** p + skew * t

    ts = [-1 + 2 * i / (NM - 1) for i in range(NM)]
    pts = [(w * t, upper(t)) for t in ts]
    pts += [(w * t, lower(t)) for t in reversed(ts[1:-1])]
    return pts, upper, lower


def _teeth(w, upper, lower, depth):
    ts = [-0.86 + 1.72 * i / (NM - 1) for i in range(NM)]
    top = [(w * t, upper(t) - 0.002) for t in ts]
    bot = [(w * t, max(upper(t) - 0.002 - depth * (1 - t * t) ** 0.3, lower(t) + 0.003)) for t in reversed(ts[1:-1])]
    return top + bot


def _tongue(w, lower, open_):
    n = 2 * NM - 2
    k = max(0.0, open_ - 0.04) / max(open_, 1e-6)    # boca cerrada: sin lengua
    cz = lower(0) + open_ * 0.32
    rx, rz = w * 0.5 * k + 1e-4, open_ * 0.34 * k + 1e-4
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = rx * math.cos(a), cz + rz * math.sin(a)
        t = max(-1.0, min(1.0, x / w))
        pts.append((x, max(z, lower(t) + 0.004) if z < cz else z))
    return pts


# nombre: (ancho, esquinas, labio sup, apertura, exponente, sesgo, dientes)
BOCAS = {
    "neutral": (0.095, 0.014, 0.006, 0.007, 1.0, 0.0, 0.0),
    "feliz": (0.125, 0.04, -0.004, 0.085, 0.75, 0.0, 0.028),
    "enfadado": (0.11, -0.012, 0.022, 0.03, 0.6, 0.0, 0.03),
    "sorpresa": (0.055, 0.0, 0.045, 0.06, 0.5, 0.0, 0.0),
    "triste": (0.09, -0.03, 0.006, 0.007, 1.0, 0.0, 0.0),
    "picaro": (0.1, 0.018, 0.006, 0.008, 1.0, 0.022, 0.0),
    "grito": (0.115, -0.006, 0.035, 0.11, 0.6, 0.0, 0.03),
}

# nombre: (boca, cejas_dz, cejas_giro, párpado_sup, giro_párpado, párpado_inf, cejas_asim)
EXPRESIONES = {
    "neutral": ("neutral", 0.0, 0.0, -55, 0.0, 60, 0.0),
    "feliz": ("feliz", 0.02, -0.05, -50, 0.0, 22, 0.0),
    "enfadado": ("enfadado", -0.03, 0.5, -18, 0.3, 50, 0.0),
    "sorpresa": ("sorpresa", 0.05, -0.12, -78, 0.0, 70, 0.0),
    "triste": ("triste", 0.0, -0.45, -22, -0.3, 58, 0.0),
    "picaro": ("picaro", 0.0, 0.1, -25, 0.0, 40, 0.06),
    "grito": ("grito", -0.025, 0.5, -40, 0.25, 40, 0.0),
}


def _font():
    import os
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f):
            return bpy.data.fonts.load(f, check_existing=True)
    return None


class Personaje:
    def __init__(self, nombre, kit=(46, 120, 210), num="9", pelo="pinchos", pelo_col=(48, 32, 22),
                 piel=(250, 203, 170), ojos=(110, 70, 40), pantalon=(32, 40, 86), medias=None,
                 guantes=False, ribete=(255, 255, 255)):
        self.n = nombre
        self.kit, self.num, self.pelo, self.pelo_col = kit, num, pelo, pelo_col
        self.piel, self.ojos_col, self.pantalon_col = piel, ojos, pantalon
        self.medias_col = medias or kit
        self.guantes, self.ribete = guantes, ribete
        self.j: dict = {}

    # ------------------------------------------------------------------ construcción
    def build(self):
        n = self.n
        self.m_skin = skin_mat(n + "_piel", srgb(*self.piel))
        self.m_hair = mat(n + "_pelo", srgb(*self.pelo_col), 0.5)
        self.m_shirt = mat(n + "_cam", srgb(*self.kit), 0.6, sheen=0.3)
        self.m_trim = mat(n + "_ribete", srgb(*self.ribete), 0.6)
        self.m_shorts = mat(n + "_pant", srgb(*self.pantalon_col), 0.6, sheen=0.3)
        self.m_socks = mat(n + "_medias", srgb(*self.medias_col), 0.7)
        self.m_boot = mat(n + "_bota", srgb(20, 20, 26), 0.25, coat=0.6)
        self.m_sole = mat(n + "_suela", srgb(235, 235, 235), 0.5)
        self.m_ink = mat(n + "_tinta", srgb(10, 8, 14), 0.15, coat=1.0)
        self.m_white = mat(n + "_blanco", srgb(250, 250, 250), 0.2, coat=0.6)
        self.m_iris = mat(n + "_iris", srgb(*self.ojos_col), 0.2, coat=1.0)
        self.m_mouth = mat(n + "_boca", srgb(70, 12, 20), 0.6)
        self.m_teeth = mat(n + "_dientes", srgb(250, 248, 240), 0.3)
        self.m_tongue = mat(n + "_lengua", srgb(225, 95, 105), 0.5)
        self.m_blush = mat(n + "_colorete", srgb(255, 160, 150), 0.6)
        self.m_glove = mat(n + "_guante", srgb(170, 230, 60), 0.55)

        root = self.root = pivot(n, (0, 0, 0))
        pel = self.pelvis = pivot(n + "_pelvis", (0, 0, PELVIS_Z), root)
        torso = self.torso = pivot(n + "_torso", (0, 0, PELVIS_Z + 0.05), pel)
        neck = self.neck = pivot(n + "_cuello", (0, 0, NECK_Z), torso)
        self._body(torso)
        self._head(neck)
        self._hair(neck)
        self._arms(torso)
        self._legs(pel)
        return self

    def _body(self, torso):
        n = self.n
        body = sphere(n + "_cuerpo", (0, 0, 1.06), (0.33, 0.28, 0.52), self.m_shirt, torso, 48, 32)
        body.data.materials.append(self.m_shorts)
        hem = 0.74                       # por debajo, pantalón; la camiseta cae por encima
        for pg in body.data.polygons:
            if 1.06 + pg.center.z * 0.52 < hem:
                pg.material_index = 1
        k = math.sqrt(1 - ((hem - 1.06) / 0.52) ** 2)
        bpy.ops.mesh.primitive_torus_add(location=(0, 0, hem + 0.01), major_radius=1.0, minor_radius=0.03)
        hm = bpy.context.active_object
        hm.name = n + "_bajo"
        hm.scale = (0.33 * k + 0.005, 0.28 * k + 0.005, 1)
        hm.data.materials.append(self.m_shirt)
        smooth(hm)
        attach(hm, torso)
        # cuello de la camiseta (pico)
        bpy.ops.mesh.primitive_torus_add(location=(0, 0, 1.54), major_radius=0.14, minor_radius=0.03)
        col = bpy.context.active_object
        col.name, col.scale = n + "_cuellocam", (1, 0.9, 0.6)
        col.data.materials.append(self.m_trim)
        smooth(col)
        attach(col, torso)
        # cuello (piel) que une con la cabeza
        limb(n + "_cuellopiel", (0, 0, 1.5), (0, 0, 1.68), 0.1, self.m_skin, self.neck, caps=False)
        # dorsal delante y detrás
        for side, y in (("d", 0.282), ("p", -0.282)):
            bpy.ops.object.text_add(location=(0, y, 1.08))
            tx = bpy.context.active_object
            tx.name = n + "_num" + side
            tx.data.body = self.num
            fnt = _font()
            if fnt:
                tx.data.font = fnt
            tx.data.align_x, tx.data.align_y = "CENTER", "CENTER"
            tx.data.size = 0.34 if side == "d" else 0.2
            tx.data.extrude = 0.012
            tx.data.bevel_depth = 0.004
            if side == "p":
                tx.location = (0.13, -0.27, 1.25)
            tx.rotation_euler = (math.radians(90), 0, math.radians(180) if side == "d" else math.radians(-14))
            tx.data.materials.append(self.m_trim)
            attach(tx, torso)

    def _head(self, neck):
        n, c, R = self.n, HEAD_C, HEAD_R
        self.head = sphere(n + "_cabeza", tuple(c), (R,) * 3, self.m_skin, neck, 48, 24)
        # orejas y nariz
        for sx in (-1, 1):
            sphere(n + f"_oreja{sx}", (sx * (R - 0.01), 0.03, c.z - 0.02), (0.045, 0.075, 0.095), self.m_skin, neck)
        sphere(n + "_nariz", (0, -R - 0.005, c.z - 0.045), (0.048, 0.04, 0.042), self.m_skin, neck)
        # colorete
        for sx in (-1, 1):
            pts = [(sx * 0.19 + 0.055 * math.cos(a), -0.075 + 0.03 * math.sin(a))
                   for a in [2 * math.pi * i / 20 for i in range(20)]]
            decal(n + f"_colorete{sx}", {"b": pts}, tuple(c), R, 0.002, self.m_blush, neck)
        # ojos: raíz con escala de elipsoide; dentro, esfera unidad + pivote de mirada con iris/pupila/brillo
        self.eyes, self.lids_up, self.lids_lo, self.look = [], [], [], []
        for sx in (-1, 1):
            er = pivot(n + f"_ojo{sx}", (sx * 0.125, c.y - 0.268, c.z + 0.045), neck)
            er.scale = (0.088, 0.062, 0.105)
            sphere(n + f"_esclera{sx}", (0, 0, 0), (1, 1, 1), self.m_white, None)
            sc_ = bpy.context.active_object
            sc_.parent = er
            lk = pivot(n + f"_mira{sx}", (0, 0, 0), None)
            lk.parent = er
            for nm, scl, y, m in (("iris", (0.56, 0.2, 0.52), -0.93, self.m_iris),
                                  ("pupila", (0.3, 0.12, 0.3), -1.0, self.m_ink)):
                o = sphere(n + f"_{nm}{sx}", (0, y, 0), scl, m, None)
                o.parent = lk
            hl = sphere(n + f"_brillo{sx}", (0.22, -1.04, 0.28), (0.12, 0.05, 0.12),
                        mat(n + "_brillo", (1, 1, 1), 0.1, emit=3.0), None)
            hl.parent = lk
            lid_m = mat(n + "_parpado_m", srgb(*self.piel), 0.5)    # sin subsurface: si no, se transparenta el iris
            up = dome(n + f"_parpado{sx}", (0, 0, 0), (1.2, 1.2, 1.2), lid_m, None, "top")
            up.parent = er
            up.modifiers["grosor"].thickness = 0.08
            lo = dome(n + f"_parpadoinf{sx}", (0, 0, 0), (1.17, 1.17, 1.17), lid_m, None, "bottom")
            lo.parent = er
            lo.modifiers["grosor"].thickness = 0.08
            for o in (up, lo):
                o.rotation_mode = "XYZ"
            up.rotation_euler = (math.radians(-55), 0, 0)
            lo.rotation_euler = (math.radians(60), 0, 0)
            self.eyes.append(er)
            self.look.append(lk)
            self.lids_up.append(up)
            self.lids_lo.append(lo)
        # cejas: curva con grosor sobre la frente
        self.brows = []
        for sx in (-1, 1):
            bc = Vector((sx * 0.135, 0, c.z + 0.17))
            pv = pivot(n + f"_cejapiv{sx}", (bc.x, c.y - 0.31, bc.z), neck)
            cu = bpy.data.curves.new(n + f"_ceja{sx}", "CURVE")
            cu.dimensions = "3D"
            cu.bevel_depth = 0.027
            cu.bevel_resolution = 4
            cu.use_fill_caps = True
            sp = cu.splines.new("POLY")
            k = 7
            sp.points.add(k - 1)
            for i in range(k):
                t = -1 + 2 * i / (k - 1)
                x = bc.x + t * 0.08
                z = bc.z + 0.022 * (1 - t * t) - 0.008 * t * sx
                y = c.y - math.sqrt(max((R + 0.022) ** 2 - x * x - (z - c.z) ** 2, 1e-6))
                sp.points[i].co = (x - bc.x, y - (c.y - 0.31), z - bc.z, 1)
                sp.points[i].radius = 1.0 - 0.45 * abs(t) ** 2 + (0.15 if t * sx < 0 else 0)
            co = bpy.data.objects.new(cu.name, cu)
            bpy.context.collection.objects.link(co)
            co.data.materials.append(self.m_hair)
            co.parent = pv
            pv.rotation_mode = "XYZ"
            self.brows.append(pv)
        self.brow_rest = [b.location.copy() for b in self.brows]
        # boca: interior + dientes + lengua, con una shape key por expresión
        shapes_m, shapes_t, shapes_l = {}, {}, {}
        for nm, (w, cor, up_, op, p, sk, td) in BOCAS.items():
            pts, upper, lower = _mouth(w, cor, up_, op, p, sk)
            shapes_m[nm] = pts
            shapes_t[nm] = _teeth(w, upper, lower, td)
            shapes_l[nm] = _tongue(w, lower, op)
        self.mouth = [decal(n + "_boca", shapes_m, tuple(c), R, 0.003, self.m_mouth, neck),
                      decal(n + "_lengua", shapes_l, tuple(c), R, 0.0045, self.m_tongue, neck),
                      decal(n + "_dientes", shapes_t, tuple(c), R, 0.0055, self.m_teeth, neck)]

    def _hair(self, neck):
        n, c, R, m = self.n, HEAD_C, HEAD_R, self.m_hair
        rng = random.Random(hash(n) & 0xFFFF)
        estilo = self.pelo
        if estilo == "rapado":
            dome(n + "_casco", (0, 0.02, c.z + 0.02), (R + 0.012, R + 0.012, R + 0.02), m, neck, "top").rotation_euler = (
                math.radians(-28), 0, 0)
            return
        # casquete: cubre la parte de arriba y de atrás, deja la frente libre
        cap = dome(n + "_casco", (0, 0.015, c.z + 0.01), (R + 0.022, R + 0.022, R + 0.03), m, neck, "top")
        cap.rotation_euler = (math.radians(-40), 0, 0)
        cap.modifiers["grosor"].thickness = 0.06
        # patillas
        for sx in (-1, 1):
            sphere(n + f"_patilla{sx}", (sx * (R - 0.02), -0.04, c.z + 0.02), (0.035, 0.07, 0.1), m, neck)
        if estilo == "pinchos":
            k = 0
            for ring_el, cnt, ln, rad in ((78, 5, 0.2, 0.1), (55, 9, 0.22, 0.1), (30, 11, 0.16, 0.085)):
                for i in range(cnt):
                    az = 2 * math.pi * (i + 0.5 * (ring_el == 55)) / cnt + math.pi / 2
                    el = math.radians(ring_el + rng.uniform(-6, 6))
                    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
                    if d.y < -0.35 and ring_el < 60:      # nada encima de los ojos
                        continue
                    base = c + d * (R - 0.02)
                    tip = base + (d + Vector((0, 0.35, 0.25))).normalized() * ln * rng.uniform(0.85, 1.15)
                    cone_to(f"{n}_mechon{k}", base, tip, rad, m, neck)
                    k += 1
            # tupé hacia delante
            cone_to(n + "_tupe", c + Vector((0.03, -0.12, R - 0.04)), c + Vector((0.06, -0.36, R + 0.1)), 0.13, m, neck)
            cone_to(n + "_tupe2", c + Vector((-0.08, -0.1, R - 0.05)), c + Vector((-0.12, -0.33, R + 0.04)), 0.1, m, neck)
        elif estilo == "rizos":
            for i in range(46):
                az = rng.uniform(0, 2 * math.pi)
                el = math.radians(rng.uniform(5, 90))
                d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
                if d.y < -0.5 and el < math.radians(55):
                    continue
                rr = rng.uniform(0.075, 0.1)
                sphere(f"{n}_rizo{i}", tuple(c + d * (R + 0.02)), (rr,) * 3, m, neck, 16, 8)
        elif estilo == "raya":
            # flequillo peinado de lado: un elipsoide grande inclinado sobre la frente
            fl = sphere(n + "_flequillo", tuple(c + Vector((0.06, -0.14, R - 0.05))), (0.3, 0.2, 0.11), m, neck)
            fl.rotation_euler = (math.radians(-25), math.radians(-14), math.radians(-8))
            fl2 = sphere(n + "_flequillo2", tuple(c + Vector((-0.17, -0.05, R - 0.1))), (0.14, 0.2, 0.1), m, neck)
            fl2.rotation_euler = (math.radians(-10), math.radians(40), 0)
        elif estilo == "coleta":
            sphere(n + "_mono", tuple(c + Vector((0, 0.3, 0.12))), (0.13, 0.13, 0.13), m, neck)
            cone_to(n + "_coleta", c + Vector((0, 0.36, 0.08)), c + Vector((0, 0.5, -0.3)), 0.1, m, neck)

    def _arms(self, torso):
        n = self.n
        self.sh, self.el = {}, {}
        hand_m = self.m_glove if self.guantes else self.m_skin
        for sx, nm in ((-1, "L"), (1, "R")):
            s0 = Vector((sx * 0.3, 0, 1.36))
            sh = pivot(f"{n}_hombro{nm}", tuple(s0), torso)
            sh.rotation_mode = "XYZ"
            sphere(f"{n}_hombrera{nm}", tuple(s0), (0.11,) * 3, self.m_shirt, sh)
            e0 = s0 + Vector((sx * 0.06, 0, -0.27))
            limb(f"{n}_manga{nm}", s0, s0 + Vector((sx * 0.04, 0, -0.18)), 0.095, self.m_shirt, sh, r2=0.085, caps=False)
            bpy.ops.mesh.primitive_torus_add(location=tuple(s0 + Vector((sx * 0.042, 0, -0.185))), major_radius=0.083,
                                             minor_radius=0.016)
            cf = bpy.context.active_object
            cf.name = f"{n}_puno{nm}"
            cf.data.materials.append(self.m_trim)
            smooth(cf)
            attach(cf, sh)
            limb(f"{n}_brazo{nm}", s0 + Vector((sx * 0.04, 0, -0.17)), e0, 0.062, self.m_skin, sh, caps=False)
            el = pivot(f"{n}_codo{nm}", tuple(e0), sh)
            el.rotation_mode = "XYZ"
            sphere(f"{n}_codoesf{nm}", tuple(e0), (0.062,) * 3, self.m_skin, el)
            w0 = e0 + Vector((sx * 0.03, 0, -0.26))
            limb(f"{n}_antebrazo{nm}", e0, w0, 0.06, self.m_skin, el, r2=0.052)
            hr = 0.13 if self.guantes else 0.09
            sphere(f"{n}_mano{nm}", tuple(w0 + Vector((0, 0, -0.05))), (hr, hr * 0.8, hr * 1.05), hand_m, el)
            sphere(f"{n}_pulgar{nm}", tuple(w0 + Vector((-sx * 0.02, -0.07, -0.02))), (hr * 0.38,) * 3, hand_m, el)
            sh.rotation_euler = (0, -sx * 0.12, 0)     # brazos algo separados en reposo
            el.rotation_euler = (0.15, 0, 0)
            self.sh[nm], self.el[nm] = sh, el

    def _legs(self, pel):
        n = self.n
        self.hip, self.knee = {}, {}
        for sx, nm in ((-1, "L"), (1, "R")):
            h0 = Vector((sx * 0.15, 0, PELVIS_Z))
            hip = pivot(f"{n}_cadera{nm}", tuple(h0), pel)
            hip.rotation_mode = "XYZ"
            limb(f"{n}_perneraa{nm}", h0 + Vector((0, 0, 0.12)), h0 + Vector((0, 0, -0.12)), 0.12, self.m_shorts, hip,
                 r2=0.115, caps=False)
            k0 = h0 + Vector((0, 0, -0.3))
            limb(f"{n}_muslo{nm}", h0 + Vector((0, 0, -0.08)), k0, 0.076, self.m_skin, hip, caps=False)
            kn = pivot(f"{n}_rodilla{nm}", tuple(k0), hip)
            kn.rotation_mode = "XYZ"
            sphere(f"{n}_rodillaesf{nm}", tuple(k0), (0.074,) * 3, self.m_skin, kn)
            a0 = k0 + Vector((0, 0, -0.24))
            limb(f"{n}_media{nm}", k0 + Vector((0, 0, -0.04)), a0, 0.072, self.m_socks, kn, r2=0.06)
            bpy.ops.mesh.primitive_torus_add(location=tuple(k0 + Vector((0, 0, -0.06))), major_radius=0.073,
                                             minor_radius=0.014)
            bd = bpy.context.active_object
            bd.name = f"{n}_banda{nm}"
            bd.data.materials.append(self.m_trim)
            smooth(bd)
            attach(bd, kn)
            sphere(f"{n}_bota{nm}", tuple(a0 + Vector((0, -0.07, -0.03))), (0.095, 0.17, 0.075), self.m_boot, kn)
            sphere(f"{n}_suela{nm}", tuple(a0 + Vector((0, -0.07, -0.075))), (0.1, 0.175, 0.025), self.m_sole, kn)
            self.hip[nm], self.knee[nm] = hip, kn

    # ------------------------------------------------------------------ colocación y animación
    def place(self, loc, yaw=0.0, f=None):
        self.root.location = loc
        self.root.rotation_euler = (0, 0, yaw)
        if f is not None:
            key(self.root, f, location=Vector(loc), rotation_euler=(0, 0, yaw))

    def expresion(self, f, nombre, peso=1.0):
        boca, bdz, btilt, lu, lt, ll, basim = EXPRESIONES[nombre]
        for o in self.mouth:
            key_shape(o, f, {boca: peso} if boca != "neutral" else {})
        for i, (pv, sx) in enumerate(zip(self.brows, (-1, 1))):
            rest = self.brow_rest[i]
            dz = bdz + basim * sx
            key(pv, f, location=Vector((rest.x, rest.y, rest.z + dz)), rotation_euler=(0, -sx * btilt, 0))
        for up, lo, sx in zip(self.lids_up, self.lids_lo, (-1, 1)):
            key(up, f, rotation_euler=(math.radians(lu), -sx * lt, 0))
            key(lo, f, rotation_euler=(math.radians(ll), 0, 0))
        self._last = (lu, lt, ll)
        self._lidtl = sorted(getattr(self, "_lidtl", []) + [(f, (lu, lt, ll))])

    def parpadeo(self, f, dur=4):
        tl = [v for fe, v in getattr(self, "_lidtl", []) if fe <= f]
        lu, lt, ll = tl[-1] if tl else (-55, 0.0, 60)
        for up, sx in zip(self.lids_up, (-1, 1)):
            key(up, f, rotation_euler=(math.radians(lu), -sx * lt, 0))
            key(up, f + dur // 2, rotation_euler=(math.radians(92), 0, 0))
            key(up, f + dur, rotation_euler=(math.radians(lu), -sx * lt, 0))

    def mirar(self, f, yaw=0.0, pitch=0.0):
        """yaw>0 mira a su izquierda (−x del mundo si mira a −y), pitch>0 arriba. Radianes (≈ ±0,5)."""
        for lk in self.look:
            lk.rotation_mode = "XYZ"
            key(lk, f, rotation_euler=(pitch, 0, yaw))

    def cabeza(self, f, yaw=0.0, pitch=0.0, roll=0.0):
        self.neck.rotation_mode = "XYZ"
        key(self.neck, f, rotation_euler=(pitch, roll, yaw))

    # ------------------------------------------------------------------ poses
    def pose(self, f, hips=(0, 0), knees=(0.05, 0.05), shoulders=((0, 0), (0, 0)), elbows=(0.15, 0.15),
             lean=0.0, pelvis_z=0.0, twist=0.0):
        """hips/knees: (L, R) en rad (cadera +: pierna atrás; rodilla +: dobla).
        shoulders: ((xL, yL), (xR, yR)); x −: brazo adelante; y: abre (L +, R −). elbows: − dobla hacia delante."""
        for i, nm in enumerate(("L", "R")):
            key(self.hip[nm], f, rotation_euler=(hips[i], 0, 0))
            key(self.knee[nm], f, rotation_euler=(knees[i], 0, 0))
            key(self.sh[nm], f, rotation_euler=(shoulders[i][0], shoulders[i][1], 0))
            key(self.el[nm], f, rotation_euler=(elbows[i], 0, 0))
        self.torso.rotation_mode = "XYZ"
        key(self.torso, f, rotation_euler=(lean, 0, twist))
        key(self.pelvis, f, location=Vector((0, 0, PELVIS_Z + pelvis_z)))

    def reposo(self, f):
        self.pose(f, shoulders=((0.05, 0.12), (0.05, -0.12)), elbows=(-0.2, -0.2))

    def zancada(self, f, fase, amp=1.0):
        """Un fotograma del ciclo de carrera (fase en radianes)."""
        sL, sR = math.sin(fase), math.sin(fase + math.pi)
        kL = 0.25 + 1.1 * max(0.0, math.sin(fase + 0.7))
        kR = 0.25 + 1.1 * max(0.0, math.sin(fase + math.pi + 0.7))
        self.pose(f, hips=(0.65 * sL * amp, 0.65 * sR * amp), knees=(kL * amp, kR * amp),
                  shoulders=((-0.7 * sR * amp, 0.15), (-0.7 * sL * amp, -0.15)), elbows=(-1.3, -1.3),
                  lean=0.15 * amp, pelvis_z=0.05 * abs(math.cos(fase)) * amp - 0.03, twist=0.12 * sL * amp)

    def correr(self, f0, f1, p0, p1, yaw=0.0, pasos_s=2.6, fps=24, amp=1.0):
        """Corre de p0 a p1 entre los fotogramas f0 y f1 (ciclo + desplazamiento)."""
        p0, p1 = Vector(p0), Vector(p1)
        for f in range(f0, f1 + 1, 2):
            u = (f - f0) / max(1, f1 - f0)
            self.place(tuple(p0.lerp(p1, u)), yaw, f)
            self.zancada(f, 2 * math.pi * pasos_s * (f - f0) / fps, amp)

    def respirar(self, f0, f1, fps=24):
        for f in range(f0, f1 + 1, 8):
            s = f / fps
            key(self.torso, f, scale=(1 + 0.012 * math.sin(s * 3.2), 1 + 0.012 * math.sin(s * 3.2), 1))
