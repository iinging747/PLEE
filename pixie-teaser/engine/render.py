"""Frame compositor + parallel renderer.

Usage:
  python -m engine.render stills 3.0 31.2 60.4      # PNG stills into work/stills
  python -m engine.render sheet 0 120 1.0           # contact sheet of frames every 1s
  python -m engine.render video [--jobs 4] [--from 0 --to 120]
"""
import math
import os
import subprocess
import sys
import time
from multiprocessing import Process

import cv2
import numpy as np

from .core import W, H, FPS, NF, DUR, WORK, DIST, clamp, prog, lerp, ease_out_cubic, ease_in_out, \
    ease_out_expo, smooth_noise
from . import fx, gfx, media


# ----------------------------------------------------------------------------- clip sampling

class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.clips = tl.CLIPS
        self.events = tl.EVENTS
        self.seqs = {}
        for c in self.clips:
            c.setdefault("layer", 0)
        self.clips.sort(key=lambda c: (c["layer"], c["t0"]))

    # -- source access --
    def source_frame(self, c, t):
        src = self.tl.SOURCES[c["src"]]
        local = t - c["t0"]
        sp = c.get("speed", 1.0)
        if callable(sp):
            st = sp(local)
        elif isinstance(sp, (list, tuple)):  # ramp: list of (local_t, speed) piecewise-linear, integrate
            st = integrate_ramp(sp, local)
        else:
            st = local * sp
        if c.get("reverse"):
            st = -st
        ts = c.get("in", 0.0) + st
        if src["kind"] == "photo":
            return media.photo(src["path"], src.get("headroom", 1.3))
        key = id(c)
        seq = self.seqs.get(key)
        if seq is None:
            seq = media.Seq(c["_conf"])
            self.seqs[key] = seq
        if c.get("freeze") is not None and local >= c["freeze"]:
            ts = c.get("in", 0.0) + (c["freeze"] * sp if not callable(sp) and not isinstance(sp, (list, tuple)) else st)
        return seq.frame_at(ts)

    def draw_clip(self, base, c, t):
        if c.get("step"):  # stepped / stutter motion (holds frames, e.g. 1/12 s)
            st = c["step"]
            t = c["t0"] + math.floor((t - c["t0"]) / st) * st
        local = t - c["t0"]
        dur = c["t1"] - c["t0"]
        k = clamp(local / dur) if dur > 0 else 1.0
        img = self.source_frame(c, t)
        sh, sw = img.shape[:2]
        box = c.get("box")
        bx, by, bw, bh = box if box else (0, 0, W, H)
        fit = c.get("fit", "cover")
        if fit == "cover":
            s0 = max(bw / sw, bh / sh)
        elif fit == "width":
            s0 = bw / sw
        elif fit == "height":
            s0 = bh / sh
        else:
            s0 = min(bw / sw, bh / sh)
        ez = {"lin": lambda x: x, "out": ease_out_cubic, "inout": ease_in_out, "expo": ease_out_expo}[c.get("ease", "lin")]
        kk = ez(k)
        z = lerp(c.get("z0", 1.0), c.get("z1", c.get("z0", 1.0)), kk)
        if "zfn" in c:
            z *= c["zfn"](local)
        s = s0 * z
        fxp, fyp = c.get("focus", (0.5, 0.5))
        if "focus1" in c:
            f1 = c["focus1"]
            fxp, fyp = lerp(fxp, f1[0], kk), lerp(fyp, f1[1], kk)
        cx, cy = fxp * sw, fyp * sh
        if fit == "cover":  # keep the view inside the image
            hw, hh = bw / (2 * s), bh / (2 * s)
            cx = clamp(cx, hw, sw - hw) if sw > 2 * hw else sw / 2
            cy = clamp(cy, hh, sh - hh) if sh > 2 * hh else sh / 2
        rot = lerp(c.get("r0", 0.0), c.get("r1", c.get("r0", 0.0)), kk)
        p0 = c.get("p0", (0, 0))
        p1 = c.get("p1", p0)
        tx, ty = lerp(p0[0], p1[0], kk), lerp(p0[1], p1[1], kk)
        if c.get("handheld"):
            a = c["handheld"]
            tx += smooth_noise(t, id(c) % 997, 0.8) * a
            ty += smooth_noise(t, id(c) % 991 + 5, 0.7) * a
            rot += smooth_noise(t, id(c) % 983 + 9, 0.5) * a * 0.02
        border = cv2.BORDER_CONSTANT if fit != "cover" else cv2.BORDER_REFLECT101
        frame = fx.affine(img, s, rot, tx, ty, (cx, cy), out=(bw, bh), border=border)
        if c.get("mirror"):
            frame = np.ascontiguousarray(frame[:, ::-1])
        frame = fx.to_f32(fx.grade_u8(frame, c.get("grade", "neutral"), c.get("gamt", 1.0), c.get("exp", 0.0)))
        # per-clip fx
        for e in c.get("fx", []):
            frame = apply_fx(frame, e, t, c)
        # opacity / fades
        op = c.get("opacity", 1.0)
        fi, fo = c.get("fade_in", 0.0), c.get("fade_out", 0.0)
        if fi > 0:
            op *= ease_in_out(local / fi)
        if fo > 0:
            op *= ease_in_out((c["t1"] - t) / fo)
        mask = None
        if "mask" in c:
            mask = c["mask"](t, bw, bh)
        if mask is None and op >= 0.999 and not box:
            base[:] = frame
            return base
        if mask is None:
            mask = np.ones((bh, bw), np.float32)
        return fx.over(base, frame, mask, bx, by, op)

    # -- frame --
    def frame(self, fi):
        t = fi / FPS
        base = np.zeros((H, W, 3), np.float32)
        for c in self.clips:
            if c["t0"] <= t < c["t1"]:
                base = self.draw_clip(base, c, t)
        # camera (punch/shake) on the composited picture
        scale, tx, ty, rot = 1.0, 0.0, 0.0, 0.0
        for e in self.events:
            typ = e["type"]
            if typ == "punch":
                d = t - e["t"]
                if 0 <= d < e.get("dur", 0.25):
                    scale *= 1 + e.get("amt", 0.06) * (1 - ease_out_cubic(d / e.get("dur", 0.25)))
            elif typ == "shake":
                d = t - e["t"]
                if 0 <= d < e.get("dur", 0.3):
                    a = e.get("amp", 14) * (1 - d / e.get("dur", 0.3)) ** 2
                    tx += smooth_noise(t, 11 + e["t"], 30) * a
                    ty += smooth_noise(t, 23 + e["t"], 33) * a
                    rot += smooth_noise(t, 37 + e["t"], 25) * a * 0.03
            elif typ == "drift":
                if e["t0"] <= t < e["t1"]:
                    scale *= 1 + e.get("amt", 0.04) * prog(t, e["t0"], e["t1"])
        if scale != 1.0 or tx or ty or rot:
            base = fx.affine(base, scale, rot, tx, ty)
        # base-level fx events
        for e in self.events:
            if e["type"] in ("whip", "zblur", "glitch", "rgb", "chroma", "sweep", "leak", "bloom", "particles", "tint", "blurev", "strobe", "black"):
                base = apply_fx(base, e, t, None)
        # letterbox (picture only - type sits on top and may use the bars)
        lb = self.letterbox(t)
        if lb > 0:
            base = fx.letterbox(base, lb)
        # graphics / text
        for e in self.events:
            if e["type"] == "draw" and e["t0"] <= t < e["t1"]:
                k = prog(t, e["t0"], e["t1"])
                r = e["fn"](base, t, k, fi)
                if r is not None:
                    base = r
        base = fx.vignette(base, self.tl.VIGNETTE)
        base = fx.grain(base, self.tl.GRAIN, fi)
        # final flashes / blackouts
        for e in self.events:
            if e["type"] in ("flash", "blackout", "fade"):
                base = apply_fx(base, e, t, None)
        return np.clip(base, 0, 1)

    def letterbox(self, t):
        kf = self.tl.LETTERBOX
        if not kf:
            return 0
        if t <= kf[0][0]:
            return kf[0][1]
        for (t0, v0, *_), (t1, v1, *rest) in zip(kf, kf[1:]):
            if t0 <= t < t1:
                mode = rest[0] if rest else "smooth"
                k = (t - t0) / (t1 - t0)
                k = ease_out_expo(k) if mode == "snap" else ease_in_out(k)
                return lerp(v0, v1, k)
        return kf[-1][1]


def integrate_ramp(ramp, local):
    """ramp: [(t, speed), ...] piecewise-linear speed; returns source seconds elapsed."""
    acc = 0.0
    for (ta, sa), (tb, sb) in zip(ramp, ramp[1:]):
        if local <= ta:
            break
        te = min(local, tb)
        if te > ta:
            sp_e = sa + (sb - sa) * (te - ta) / (tb - ta)
            acc += (sa + sp_e) / 2 * (te - ta)
    if local > ramp[-1][0]:
        acc += ramp[-1][1] * (local - ramp[-1][0])
    return acc


def apply_fx(img, e, t, clip):
    typ = e["type"]
    if typ == "beauty":
        return fx.beauty(img, e.get("amt", 0.6))
    if typ in ("leak", "bloom", "particles", "tint", "strobe") or "t0" in e:
        t0, t1 = e.get("t0", e.get("t", 0)), e.get("t1", e.get("t", 0) + e.get("dur", 0))
    else:
        t0, t1 = e["t"] - e.get("pre", 0.0), e["t"] + e.get("dur", 0.2)
    if not (t0 <= t < t1):
        return img
    if typ == "whip":
        pre, dur = e.get("pre", 0.12), e.get("dur", 0.12)
        d = t - e["t"]
        k = (1 + d / pre) if d < 0 else (1 - d / dur)
        k = clamp(k) ** 1.5
        return fx.dir_blur(img, e.get("px", 160) * k, e.get("angle", 0))
    if typ == "zblur":
        pre, dur = e.get("pre", 0.1), e.get("dur", 0.15)
        d = t - e["t"]
        k = (1 + d / pre) if d < 0 else (1 - d / dur)
        return fx.zoom_blur(img, e.get("amt", 0.18) * clamp(k) ** 1.4)
    if typ == "blurev":
        k = 1 - prog(t, t0, t1) if e.get("dir", "in") == "in" else prog(t, t0, t1)
        return fx.fast_blur(img, e.get("sigma", 20) * k)
    if typ == "glitch":
        d = t - t0
        k = e.get("amt", 0.7) * (1 - d / max(t1 - t0, 1e-6)) ** 0.5
        seed = int(t * 30) + int(e.get("seed", 0))
        return fx.glitch(fx.rgb_split(img, 10 * k), k, seed)
    if typ == "rgb":
        d = t - e["t"]
        k = (1 - d / e.get("dur", 0.2)) ** 2 if d >= 0 else clamp(1 + d / max(e.get("pre", 0.01), 1e-3)) ** 2
        return fx.chroma_radial(fx.rgb_split(img, e.get("px", 12) * k, e.get("angle", 0)), 0.006 * k)
    if typ == "chroma":
        k = 1 - prog(t, t0, t1)
        return fx.chroma_radial(img, e.get("amt", 0.01) * k)
    if typ == "sweep":
        return fx.light_sweep(img, prog(t, t0, t1), e.get("angle", -20), e.get("width", 0.2),
                              e.get("strength", 0.5), e.get("color", (1, 1, 1)))
    if typ == "leak":
        env = min(prog(t, t0, t0 + e.get("fin", 0.8)), 1 - prog(t, t1 - e.get("fout", 0.8), t1))
        layer = fx.light_leak(t, e["colors"], e.get("strength", 0.3) * env, e.get("seed", 0), e.get("speed", 1.0))
        if layer is None:
            return img
        lum = img.max(axis=2, keepdims=True)
        return fx.screen(img, layer * (0.12 + 0.88 * lum))  # keep blacks deep
    if typ == "bloom":
        return fx.bloom(img, e.get("thr", 0.7), e.get("strength", 0.45))
    if typ == "particles":
        env = min(prog(t, t0, t0 + 0.6), 1 - prog(t, t1 - 0.6, t1))
        return gfx.particles(img, t, e.get("n", 40), e.get("seed", 3), e.get("color", (1, 0.9, 0.8)),
                             e.get("size", (1.2, 3.5)), e.get("speed", 18), e.get("strength", 0.6) * env)
    if typ == "tint":
        env = min(prog(t, t0, t0 + e.get("fin", 0.3)), 1 - prog(t, t1 - e.get("fout", 0.3), t1))
        return fx.tint_mix(img, e["color"], e.get("amt", 0.2) * env)
    if typ == "strobe":
        period = e.get("period", 0.117)
        ph = ((t - t0) % period) / period
        return fx.flash(img, e.get("amt", 0.3) * (1 - ph) ** 3, e.get("color", (1, 1, 1)))
    if typ == "flash":
        d = t - e["t"]
        pre = e.get("pre", 0.0)
        if d < 0:
            k = clamp(1 + d / pre) ** 2 if pre > 0 else 0
        else:
            k = (1 - d / e.get("dur", 0.2)) ** e.get("pow", 2)
        return fx.flash(img, e.get("amt", 0.8) * k, e.get("color", (1, 1, 1)), e.get("mode", "screen"))
    if typ in ("black", "blackout"):
        return img * 0.0
    if typ == "fade":  # fade to/from black over [t0,t1]
        k = prog(t, t0, t1)
        k = k if e.get("dir", "out") == "out" else 1 - k
        return img * (1 - ease_in_out(k))
    if typ == "clipfx":  # per-clip callable
        return e["fn"](img, t, clip)
    return img


# ----------------------------------------------------------------------------- orchestration

def load_timeline():
    import importlib
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    tl = importlib.import_module(os.environ.get("PIXIE_TIMELINE", "timeline"))
    return tl


def prepare(tl):
    """Conform every clip's source range (cached)."""
    for c in tl.CLIPS:
        src = tl.SOURCES[c["src"]]
        if src["kind"] != "video":
            continue
        sp = c.get("speed", 1.0)
        dur = c["t1"] - c["t0"]
        if callable(sp):
            span = max(abs(sp(dur)), abs(sp(0))) + 0.2
        elif isinstance(sp, (list, tuple)):
            span = integrate_ramp(sp, dur) + 0.2
        else:
            span = dur * abs(sp) + 0.2
        t_in = c.get("in", 0.0)
        a, b = (t_in - span, t_in + 0.1) if c.get("reverse") else (t_in - 0.05, t_in + span)
        c["_conf"] = media.conform(c["src"], src["path"], max(0.0, a), b, src.get("headroom", 1.0),
                                   src.get("max_fps", 60), src.get("fit", "cover"), crop=src.get("crop"))


def render_range(f0, f1, out_path, crf=18):
    tl = load_timeline()
    prepare(tl)
    r = Renderer(tl)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-x264-params", "keyint=60:min-keyint=30", "-colorspace", "bt709", "-color_primaries", "bt709",
           "-color_trc", "bt709", "-color_range", "tv", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for fi in range(f0, f1):
        fr_ = r.frame(fi)
        p.stdin.write((fr_ * 255 + 0.5).astype(np.uint8).tobytes())
        if (fi - f0) % 150 == 0:
            el = time.time() - t0
            print(f"[{os.getpid()}] frame {fi} ({fi - f0}/{f1 - f0}) {el:.0f}s", flush=True)
    p.stdin.close()
    p.wait()


def video(jobs=4, t_from=0.0, t_to=None, out=None):
    tl = load_timeline()
    if t_to is None:
        t_to = getattr(tl, "DUR_OUT", DUR)
    prepare(tl)  # conform once in the parent
    f0, f1 = int(round(t_from * FPS)), int(round(t_to * FPS))
    os.makedirs(os.path.join(WORK, "chunks"), exist_ok=True)
    bounds = np.linspace(f0, f1, jobs + 1).astype(int)
    procs, parts = [], []
    for j in range(jobs):
        pth = os.path.join(WORK, "chunks", f"part{j:02d}.mp4")
        parts.append(pth)
        p = Process(target=render_range, args=(int(bounds[j]), int(bounds[j + 1]), pth))
        p.start()
        procs.append(p)
    for p in procs:
        p.join()
        if p.exitcode != 0:
            raise SystemExit(f"render worker failed: {p.exitcode}")
    lst = os.path.join(WORK, "chunks", "list.txt")
    with open(lst, "w") as f:
        for pth in parts:
            f.write(f"file '{pth}'\n")
    silent = os.path.join(WORK, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    return silent


def stills(times, scale=1.0, tag="s"):
    tl = load_timeline()
    prepare(tl)
    r = Renderer(tl)
    d = os.path.join(WORK, "stills")
    os.makedirs(d, exist_ok=True)
    paths = []
    for t in times:
        fi = int(round(float(t) * FPS))
        img = (r.frame(fi) * 255 + 0.5).astype(np.uint8)
        if scale != 1.0:
            img = cv2.resize(img, (int(W * scale), int(H * scale)), interpolation=cv2.INTER_AREA)
        p = os.path.join(d, f"{tag}_{fi:05d}.jpg")
        cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        paths.append(p)
    return paths


def sheet(t0, t1, step, cols=6, scale=0.2, name="sheet"):
    tl = load_timeline()
    prepare(tl)
    r = Renderer(tl)
    ts = np.arange(t0, t1, step)
    tw, th = int(W * scale), int(H * scale)
    rows = int(math.ceil(len(ts) / cols))
    out = np.zeros((rows * (th + 18), cols * tw, 3), np.uint8)
    for i, t in enumerate(ts):
        img = (r.frame(int(round(t * FPS))) * 255 + 0.5).astype(np.uint8)
        img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        y, x = (i // cols) * (th + 18), (i % cols) * tw
        out[y:y + th, x:x + tw] = img
        cv2.putText(out, f"{t:6.2f}", (x + 4, y + th + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1, cv2.LINE_AA)
    d = os.path.join(WORK, "stills")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{name}_{t0:06.2f}.jpg")
    cv2.imwrite(p, cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return p


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cmd = sys.argv[1]
    if cmd == "stills":
        for p in stills(sys.argv[2:]):
            print(p)
    elif cmd == "sheet":
        a, b, s = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
        print(sheet(a, b, s, name=sys.argv[5] if len(sys.argv) > 5 else "sheet"))
    elif cmd == "video":
        args = sys.argv[2:]
        jobs = int(args[args.index("--jobs") + 1]) if "--jobs" in args else 4
        a = float(args[args.index("--from") + 1]) if "--from" in args else 0.0
        b = float(args[args.index("--to") + 1]) if "--to" in args else None
        print(video(jobs, a, b))
