"""Audio mix: BGM (with edit points) + natural sound from clips + sound design, loudness-normalised."""
import json
import os
import subprocess

import numpy as np
import soundfile as sf

from .core import ROOT, ASSETS, WORK, DUR
from . import sfx as S

SR = S.SR


def load_bgm():
    p = os.path.join(ASSETS, "audio", "bgm.wav")
    if not os.path.exists(p):
        p = os.path.join(ASSETS, "audio", "bgm.mp3")
    return decode(p, 0, None)


def decode(path, start, dur, speed=1.0):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}"]
    if dur is not None:
        cmd += ["-t", f"{dur * speed:.4f}"]
    cmd += ["-i", path, "-vn", "-ac", "2", "-ar", str(SR)]
    if abs(speed - 1.0) > 1e-3:
        chain, s = [], speed
        while s > 2.0:
            chain.append("atempo=2.0")
            s /= 2
        while s < 0.5:
            chain.append("atempo=0.5")
            s /= 0.5
        chain.append(f"atempo={s:.5f}")
        cmd += ["-af", ",".join(chain)]
    cmd += ["-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def place(bus, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(bus) - i)
    if n > 0:
        bus[i:i + n] += x[:n] * gain


def env_curve(points, n):
    """points [(t, gain_linear)] -> per-sample curve (linear interp)."""
    ts = np.array([p[0] for p in points]) * SR
    gs = np.array([p[1] for p in points])
    return np.interp(np.arange(n), ts, gs).astype(np.float32)


def db(x):
    return 10 ** (x / 20)


def limiter(x, ceiling=0.89, release=0.08, look=0.004):
    la = int(look * SR)
    peak = np.max(np.abs(x), axis=1)
    # look-ahead running max
    from scipy.ndimage import maximum_filter1d
    pk = maximum_filter1d(peak, size=2 * la + 1)
    g = np.minimum(1.0, ceiling / (pk + 1e-9))
    # smooth release (one-pole on gain, instant attack)
    a = np.exp(-1.0 / (release * SR))
    from scipy.signal import lfilter
    # approximate: release smoothing of 1-g, then take min with instantaneous g
    sm = 1 - lfilter([1 - a], [1, -a], 1 - g)
    out = np.minimum(g, np.clip(sm, 0, 1))
    return x * out[:, None]


def build(tl, out_wav):
    n = int(DUR * SR)
    bgm = load_bgm()[:n]
    if len(bgm) < n:
        bgm = np.pad(bgm, ((0, n - len(bgm)), (0, 0)))
    # BGM edit envelope
    bg_env = env_curve(tl.BGM_ENV, n) if getattr(tl, "BGM_ENV", None) else np.ones(n, np.float32)
    music = bgm * bg_env[:, None] * db(getattr(tl, "BGM_GAIN_DB", 0.0))

    nat = np.zeros((n, 2), np.float32)
    for c in tl.CLIPS:
        g = c.get("audio", 0.0)
        if g <= 0:
            continue
        src = tl.SOURCES[c["src"]]
        if src["kind"] != "video" or not src.get("has_audio", True):
            continue
        sp = c.get("speed", 1.0)
        sp = sp if isinstance(sp, (int, float)) else 1.0
        dur = c["t1"] - c["t0"]
        try:
            x = decode(src["path"], c.get("in", 0.0), dur, sp)
        except subprocess.CalledProcessError:
            continue
        L = len(x)
        if L == 0:
            continue
        fade = int(0.012 * SR)
        ramp = np.ones(L, np.float32)
        fi = int(c.get("afade_in", 0.012) * SR)
        fo = int(c.get("afade_out", 0.03) * SR)
        if fi:
            ramp[:fi] = np.linspace(0, 1, min(fi, L))[:min(fi, L)]
        if fo:
            ramp[-fo:] *= np.linspace(1, 0, min(fo, L))[-min(fo, L):]
        x = S.hp(x.T, c.get("hpf", 80)).T if c.get("hpf", 80) else x
        place(nat, x * ramp[:, None], c["t0"], db(g) if g > 1 else g)

    fxbus = np.zeros((n, 2), np.float32)
    duck = np.ones(n, np.float32)
    sfx_dir = os.path.join(ROOT, "sfx")
    cache = {}
    for e in tl.SFX:
        key = (e["name"], json.dumps(e.get("kw", {}), sort_keys=True))
        if key not in cache:
            cache[key] = S.get(e["name"], sfx_dir, **e.get("kw", {}))
        x = cache[key]
        t = e["t"]
        if e.get("align") == "end":
            t -= len(x) / SR
        elif e.get("align") == "peak":
            t -= e.get("peak", 0.0)
        t += e.get("offset", 0.0)
        if "until" in e:
            n_keep = int((e["until"] - t) * SR)
            if n_keep <= 0:
                continue
            if n_keep < len(x):
                x = x[:n_keep].copy()
                f = min(len(x), int(0.06 * SR))
                x[-f:] *= np.linspace(1, 0, f)[:, None]
        place(fxbus, x, t, db(e.get("db", -6.0)))
        if e.get("duck"):
            d0 = int(max(0, e["t"] - 0.02) * SR)
            d1 = int(min(DUR, e["t"] + e.get("duck_len", 0.5)) * SR)
            if d1 > d0:
                k = np.linspace(0, 1, d1 - d0)
                duck[d0:d1] = np.minimum(duck[d0:d1], 1 - (1 - db(e["duck"])) * (1 - k) ** 2)

    # voiceover (후시녹음): vo/<id>.wav if recorded
    vobus = np.zeros((n, 2), np.float32)
    vo_dir = os.path.join(ROOT, "vo")
    for v in getattr(tl, "VO", []):
        pth = os.path.join(vo_dir, v["id"] + ".wav")
        if not os.path.exists(pth):
            continue
        x = decode(pth, 0, None)
        x = S.hp(x.T, 90).T
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.7
        place(vobus, x, v["t"], db(v.get("db", -2.0)))
        d0 = int(max(0, v["t"] - 0.18) * SR)
        d1 = int(min(DUR, v["t"] + len(x) / SR + 0.25) * SR)
        r = int(0.12 * SR)
        g = np.full(d1 - d0, db(-7.0), np.float32)
        g[:r] = np.linspace(1, db(-7.0), r)
        g[-r:] = np.linspace(db(-7.0), 1, r)
        duck[d0:d1] = np.minimum(duck[d0:d1], g)

    mix = (music * duck[:, None] + nat * db(getattr(tl, "NAT_GAIN_DB", 0.0)) +
           fxbus * db(getattr(tl, "SFX_GAIN_DB", 0.0)) + vobus)
    mix = limiter(mix, 0.95)
    os.makedirs(os.path.dirname(out_wav), exist_ok=True)
    tmp = out_wav + ".pre.wav"
    sf.write(tmp, mix, SR, subtype="FLOAT")
    # two-pass loudnorm to YouTube-friendly level
    target = getattr(tl, "LUFS", -14.0)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af",
                        f"loudnorm=I={target}:TP=-1.2:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"): r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I={target}:TP=-1.2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af, "-ar", str(SR), "-c:a", "pcm_s24le", out_wav], check=True)
    os.remove(tmp)
    return out_wav


def stems_report(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    return tail
