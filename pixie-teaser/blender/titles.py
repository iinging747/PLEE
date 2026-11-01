"""Blender (bpy) title renderer for the PIXIE teaser: chrome type & logo on transparent film.

Run with the bpy venv:
  /opt/bpyenv/bin/python blender/titles.py -- <shot> [--frames a b] [--still f] [--samples n]
Output: work/bl/<shot>/####.png (RGBA, 1920x1080, 30 fps frame numbering from 1)
"""
import json
import math
import os
import sys

import bpy  # noqa: E402  (must precede addon_utils)
import addon_utils
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "assets", "fonts")
LICENSED = os.path.join(FONTS, "licensed")
OUT = os.path.join(ROOT, "assets", "titles")
FPS = 30


def font_path(role):
    """Roles map to files; a licensed (e.g. Sandoll) override in assets/fonts/licensed wins."""
    roles = {
        "display": ["BodoniModa-Regular.ttf"],
        "display_i": ["BodoniModa-Italic.ttf"],
        "label": ["Jost-Light.ttf"],
        "kr": ["Pretendard-Light.otf"],
    }
    over = os.path.join(LICENSED, role + ".otf")
    for ext in (".otf", ".ttf"):
        p = os.path.join(LICENSED, role + ext)
        if os.path.exists(p):
            return p
    return os.path.join(FONTS, roles[role][0])


# --------------------------------------------------------------------------- scene setup

def reset(samples=40):
    addon_utils.enable("cycles", default_set=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.glossy_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.fps = FPS
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.004, 0.003, 0.006, 1)
    bg.inputs[1].default_value = 1.0
    return sc


def chrome(name="chrome", color=(0.93, 0.94, 0.97), rough=0.13):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    return m


def emitter(name, loc, rot, size, strength, color=(1, 1, 1), camera_visible=False):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new(name + "_m")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*color, 1)
    em.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    o.data.materials.append(m)
    o.visible_camera = camera_visible
    o.visible_shadow = False
    return o, em


def studio(sweep=True):
    """Soft studio rig for chrome: top strip, violet left, champagne right, low fill + moving sweep bar."""
    emitter("top", (0, -1.5, 3.2), (math.radians(-25), 0, 0), (9, 1.2), 9, (1, 1, 1))
    emitter("left", (-4.5, -2.0, 0.6), (0, math.radians(-70), 0), (1.0, 5), 5, (0.62, 0.48, 0.95))
    emitter("right", (4.5, -2.0, 0.4), (0, math.radians(70), 0), (1.0, 5), 4, (1.0, 0.86, 0.7))
    emitter("floor", (0, -2.5, -2.6), (math.radians(30), 0, 0), (9, 1.0), 1.6, (0.8, 0.82, 0.9))
    sw = None
    if sweep:
        sw, em = emitter("sweep", (-8, -3.0, 0.3), (math.radians(90), math.radians(16), 0), (0.25, 6), 0, (1, 1, 1))
        sw.visible_camera = False
        sw["em"] = em.name
    return sw


def animate_sweep(sw, f0, f1, x0=-7.0, x1=7.0, strength=40):
    em = sw.active_material.node_tree.nodes["Emission"]
    for f, x, s in ((f0 - 1, x0, 0), (f0, x0, strength), (f1, x1, strength), (f1 + 1, x1, 0)):
        sw.location.x = x
        sw.keyframe_insert("location", index=0, frame=f)
        em.inputs[1].default_value = s
        em.inputs[1].keyframe_insert("default_value", frame=f)
    for fc in _fcurves(sw):
        for k in fc.keyframe_points:
            k.interpolation = "SINE"


def _fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def backdrop(cam, width, text_h, strength=1.15):
    """Large gradient softbox behind the camera: gives chrome faces a silver gradient + horizon line."""
    y = cam.location.y - 4.0
    bpy.ops.mesh.primitive_plane_add(size=1, location=(cam.location.x, y, cam.location.z),
                                     rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.scale = (width * 3, text_h * 2.7, 1)
    m = bpy.data.materials.new("backdrop")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    stops = [(0.0, (0.30, 0.29, 0.34)), (0.28, (0.10, 0.09, 0.13)), (0.47, (0.03, 0.028, 0.04)),
             (0.50, (1.0, 1.0, 1.0)), (0.535, (0.52, 0.52, 0.56)), (0.80, (0.80, 0.81, 0.85)), (1.0, (0.98, 0.98, 1.0))]
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = (*col, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Y"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
    o.data.materials.append(m)
    o.visible_camera = False
    o.visible_shadow = False
    return o


def camera(lens=85, dist=9.0, fstop=None, focus=9.0):
    bpy.ops.object.camera_add(location=(0, -dist, 0), rotation=(math.radians(90), 0, 0))
    cam = bpy.context.object
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus
    return cam


def text_obj(body, role="display", size=1.0, extrude=0.035, bevel=0.006, spacing=0.92, mat=None, loc=(0, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    t = bpy.context.object
    t.data.body = body
    t.data.font = bpy.data.fonts.load(font_path(role), check_existing=True)
    t.data.size = size
    t.data.extrude = extrude
    t.data.bevel_depth = bevel
    t.data.bevel_resolution = 3
    t.data.space_character = spacing
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.resolution_u = 24
    if mat:
        t.data.materials.append(mat)
    return t


def logo_obj(mat, width=4.6, extrude=0.07, bevel=0.010, star_mat=None):
    """Import the traced logo SVGs (word + star share one canvas), scale to `width`, stand it up."""
    addon_utils.enable("io_curve_svg", default_set=True)
    objs = []
    for key_, m in (("pixie_word", mat), ("pixie_star", star_mat or mat)):
        before = set(bpy.data.objects)
        bpy.ops.import_curve.svg(filepath=os.path.join(ROOT, "assets", "logo", key_ + ".svg"))
        new = [o for o in bpy.data.objects if o not in before]
        objs.extend((o, m) for o in new)
    # common bounds (both SVGs share the 3000x1017 canvas)
    xs, ys = [], []
    for o, _ in objs:
        for sp in o.data.splines:
            for bp_ in sp.bezier_points:
                v = o.matrix_world @ bp_.co
                xs.append(v.x)
                ys.append(v.y)
    word_w = max(xs) - min(xs)
    k = width / word_w
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    for o, m in objs:
        o.data.dimensions = "2D"
        o.data.fill_mode = "BOTH"
        o.data.resolution_u = 24
        o.data.extrude = extrude / k
        o.data.bevel_depth = bevel / k
        o.data.bevel_resolution = 3
        o.data.materials.clear()
        o.data.materials.append(m)
        o.location = (-cx * k, 0, -cy * k)
        o.scale = (k, k, k)
        o.rotation_euler = (math.radians(90), 0, 0)
        # location after rotation: x stays, y(curve) -> z(world)
        o.location = (-cx * k, 0, -cy * k)
    bpy.context.view_layer.update()
    return [o for o, _ in objs]


def bbox_world(objs):
    xs, zs = [], []
    for o in objs:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c)
            xs.append(v.x)
            zs.append(v.z)
    return min(xs), max(xs), min(zs), max(zs)


def fit_camera(cam, objs, frac=0.5, lens=85):
    """Place the camera on -Y so the objects span `frac` of the frame width; centre them."""
    bpy.context.view_layer.update()
    x0, x1, z0, z1 = bbox_world(objs)
    w = x1 - x0
    frame_w = w / frac
    d = frame_w * lens / 36.0
    cam.location = ((x0 + x1) / 2, -d, (z0 + z1) / 2)
    return d


def key(obj, path, frame, value, index=-1, interp="BEZIER"):
    if index >= 0:
        getattr(obj, path)[index] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(path, index=index, frame=frame)
    for fc in _fcurves(obj):
        for k in fc.keyframe_points:
            if int(round(k.co[0])) == frame:
                k.interpolation = interp


# --------------------------------------------------------------------------- shots

def shot_logo(sc):
    m = chrome()
    objs = logo_obj(m, width=4.6, star_mat=chrome("star", rough=0.07))
    studio(sweep=False)
    cam = camera(lens=85)
    d = fit_camera(cam, objs, 0.56)
    x0, x1, z0, z1 = bbox_world(objs[:1])
    backdrop(cam, d * 36 / 85, z1 - z0)


def shot_word(sc, body, role="display", size=1.0, spacing=0.9, frac=0.42):
    t = text_obj(body, role, size=size, spacing=spacing, mat=chrome())
    studio(sweep=False)
    cam = camera(lens=85)
    d = fit_camera(cam, [t], frac)
    x0, x1, z0, z1 = bbox_world([t])
    backdrop(cam, d * 36 / 85, (z1 - z0) * 0.8)


SHOTS = {
    "logo": lambda sc: shot_logo(sc),
    "ch_trading": lambda sc: shot_word(sc, "Trading"),
    "ch_lifestyle": lambda sc: shot_word(sc, "Lifestyle"),
    "ch_beauty": lambda sc: shot_word(sc, "Beauty"),
    "ch_travel": lambda sc: shot_word(sc, "Travel"),
    "more": lambda sc: shot_word(sc, "More than a trader", role="display_i", spacing=0.93, frac=0.62),
    "cold": lambda sc: shot_word(sc, "Cold.", frac=0.30),
    "calm": lambda sc: shot_word(sc, "Calm.", frac=0.30),
    "calculated": lambda sc: shot_word(sc, "Calculated.", role="display_i", frac=0.48),
    "world": lambda sc: shot_word(sc, "A bigger world", role="display_i", spacing=0.93, frac=0.55),
    "live": lambda sc: shot_word(sc, "Coming soon", role="display_i", spacing=0.93, frac=0.40),
}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    shot = argv[0]
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 40
    sc = reset(samples)
    SHOTS[shot](sc)
    d = os.path.join(OUT, shot)
    os.makedirs(d, exist_ok=True)
    if "--still" in argv:
        f = int(argv[argv.index("--still") + 1])
        sc.frame_set(f)
        sc.render.filepath = os.path.join(d, f"still_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        return
    if "--frames" in argv:
        i = argv.index("--frames")
        sc.frame_start, sc.frame_end = int(argv[i + 1]), int(argv[i + 2])
    sc.render.filepath = os.path.join(d, "")
    sc.render.use_overwrite = False
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
