"""Procedural sound design (48 kHz stereo float32). Swap any of these with ElevenLabs renders
by dropping a WAV with the same name into sfx/ (see sfx/ELEVENLABS_PROMPTS.md)."""
import os

import numpy as np
from scipy import signal

SR = 48000
_rng = np.random.default_rng(2049)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def noise(n, seed=None):
    r = np.random.default_rng(seed) if seed is not None else _rng
    return r.standard_normal(n).astype(np.float32)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def lp(x, f, order=2):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def stereo(x, width=0.0, pan=0.0):
    l = x * np.sqrt(0.5 * (1 - pan))
    r = x * np.sqrt(0.5 * (1 + pan))
    s = np.stack([l, r], 1)
    if width > 0:
        d = int(0.011 * SR)
        s[d:, 1] = s[d:, 1] * (1 - width) + x[:-d] * width * np.sqrt(0.5)
    return s.astype(np.float32)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return (x / m * peak).astype(np.float32)


def reverb(x, seconds=2.2, damp=4500, mix=0.35, seed=1, pre=0.012):
    """Convolution reverb with a synthetic decorrelated stereo IR. x: mono or stereo."""
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 6.9 / seconds)
    irs = []
    for ch in range(2):
        ir = noise(n, seed + ch) * env
        ir = lp(ir, damp)
        ir[: int(pre * SR)] = 0
        irs.append(ir / np.sqrt(np.sum(ir ** 2) + 1e-9))
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    wet = np.stack([signal.fftconvolve(x[:, c], irs[c])[: len(x) + n] for c in range(2)], 1)
    dry = np.zeros_like(wet)
    dry[: len(x)] = x
    return (dry * (1 - mix) + wet * mix).astype(np.float32)


# ------------------------------------------------------------------ sounds


def impact(size=1.0, seed=3):
    dur = 4.0
    t = t_axis(dur)
    f = 58 * np.exp(-t * 2.2) + 28
    ph = 2 * np.pi * np.cumsum(f) / SR
    sub = np.sin(ph) * np.exp(-t * 2.4) * 1.0
    body = lp(noise(len(t), seed), 220) * np.exp(-t * 9) * 2.5
    crack = bp(noise(len(t), seed + 1), 900, 7000) * np.exp(-t * 55) * 1.4
    thump = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 28) * 0.6
    x = sub + body + crack + thump
    x = np.tanh(x * 1.6 * size)
    st = reverb(x, 3.2, 3200, 0.45, seed)
    return norm(st[: int(dur * SR)], 0.95)


def hit_metal(seed=5):
    """Short cinematic metallic hit (for chapter slams)."""
    dur = 2.5
    t = t_axis(dur)
    parts = [(183, 1.0), (411, 0.6), (657, 0.45), (1023, 0.3), (1596, 0.2)]
    x = sum(a * np.sin(2 * np.pi * f * t + i) * np.exp(-t * (3 + i * 1.3)) for i, (f, a) in enumerate(parts))
    x += bp(noise(len(t), seed), 2000, 9000) * np.exp(-t * 40) * 0.8
    x += np.sin(2 * np.pi * 48 * t) * np.exp(-t * 6) * 0.9
    st = reverb(np.tanh(x * 1.2), 2.4, 5000, 0.4, seed)
    return norm(st[: len(t)], 0.9)


def whoosh(dur=0.7, f0=250, f1=4200, seed=7, pan_from=-0.7, pan_to=0.7, peak=0.62):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur
    env = np.where(k < peak, (k / peak) ** 2.2, ((1 - k) / (1 - peak)) ** 1.6)
    x = noise(n, seed)
    # time-varying band-pass via short overlapping blocks
    out = np.zeros(n, np.float32)
    blk = 1024
    win = np.hanning(blk * 2).astype(np.float32)
    for s in range(0, n, blk):
        kk = min(1, s / n)
        fc = f0 * (f1 / f0) ** (np.sin(kk * np.pi) if f1 > f0 else kk)
        seg = x[max(0, s - blk): s + blk]
        if len(seg) < 64:
            continue
        y = bp(seg, max(60, fc * 0.5), min(SR / 2 - 100, fc * 1.8))
        w = win[: len(y)]
        a = max(0, s - blk)
        out[a: a + len(y)] += y * w
    out *= env
    pans = np.linspace(pan_from, pan_to, n)
    st = np.stack([out * np.sqrt(0.5 * (1 - pans)), out * np.sqrt(0.5 * (1 + pans))], 1)
    st = reverb(st, 0.9, 6000, 0.2, seed)
    return norm(st[:n], 0.8)


def swish(seed=11):
    return whoosh(0.28, 600, 7000, seed, -0.3, 0.3, 0.5)


def riser(dur=3.0, seed=13):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = t / dur
    f = 110 * (2400 / 110) ** (k ** 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25 + np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * 0.12
    nz = hp(noise(n, seed), 800) * (0.1 + 0.9 * k ** 2)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * (4 + 18 * k ** 2) * t)
    x = (tone + nz * 0.6) * (k ** 1.8) * trem
    st = reverb(x, 1.6, 7000, 0.3, seed)[:n]
    return norm(st, 0.8)


def reverse_swell(dur=1.6, seed=17):
    src = impact(1.0, seed)
    tail = src[: int(dur * SR)][::-1].copy()
    k = np.linspace(0, 1, len(tail))[:, None]
    tail *= k ** 1.5
    return norm(hp(tail.T, 120).T if False else tail, 0.75)


def sub_drop(dur=1.6):
    t = t_axis(dur)
    f = 90 * np.exp(-t * 2.5) + 26
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)
    return stereo(norm(np.tanh(x * 1.4), 0.9))


def heartbeat(strength=1.0, seed=19):
    dur = 1.2
    t = t_axis(dur)

    def thump(t0, a, f):
        tt = np.clip(t - t0, 0, None)
        on = (t >= t0).astype(np.float32)
        return on * a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 22) * (1 - np.exp(-tt * 400))

    x = thump(0.0, 1.0, 52) + thump(0.27, 0.7, 47)
    x += lp(noise(len(t), seed), 120) * (np.exp(-t * 18) + 0.6 * np.exp(-np.clip(t - 0.27, 0, None) * 18) * (t > 0.27)) * 0.6
    x = np.tanh(x * 1.8) * strength
    return stereo(norm(x, 0.95 * strength))


def tick(freq=3200, seed=23):
    t = t_axis(0.06)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 160) * 0.6
    x += hp(noise(len(t), seed), 3000) * np.exp(-t * 600) * 0.8
    return stereo(norm(x, 0.6))


def click_soft(seed=29):
    t = t_axis(0.05)
    x = bp(noise(len(t), seed), 1500, 6000) * np.exp(-t * 400)
    return stereo(norm(x, 0.5))


def glitch_burst(dur=0.35, seed=31):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    r = np.random.default_rng(seed)
    pos = 0
    while pos < n:
        ln = int(r.uniform(0.008, 0.035) * SR)
        f = r.choice([180, 330, 660, 1200, 2400, 3900])
        tt = np.arange(min(ln, n - pos)) / SR
        sq = np.sign(np.sin(2 * np.pi * f * tt)) * r.uniform(0.2, 0.7)
        if r.random() < 0.35:
            sq = np.round(noise(len(tt), int(r.integers(1e6))) * 3) / 3 * 0.5
        out[pos: pos + len(tt)] = sq
        pos += ln + int(r.uniform(0, 0.012) * SR)
    out = lp(out, 9000)
    return stereo(norm(out, 0.55), width=0.6)


def shutter(seed=37):
    t = t_axis(0.18)
    a = bp(noise(len(t), seed), 1200, 8000)
    env = np.exp(-t * 300) + 0.8 * np.exp(-np.clip(t - 0.07, 0, None) * 260) * (t > 0.07)
    return stereo(norm(a * env, 0.6))


def shimmer(dur=1.8, seed=41):
    t = t_axis(dur)
    r = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for i in range(9):
        f = r.uniform(2400, 7200)
        d = r.uniform(0, 0.25)
        tt = np.clip(t - d, 0, None)
        x += np.sin(2 * np.pi * f * tt) * np.exp(-tt * r.uniform(2.5, 6)) * (t > d) * r.uniform(0.3, 1)
    st = reverb(x * 0.3, 2.0, 9000, 0.5, seed)[: len(t)]
    return norm(st, 0.5)


def boom_low(seed=43):
    """Deep cinematic 'bwong' for the logo slam."""
    dur = 5.0
    t = t_axis(dur)
    f = 44 + 6 * np.exp(-t * 3)
    x = sum(np.sin(2 * np.pi * np.cumsum(f * m) / SR + i) * a for i, (m, a) in enumerate([(1, 1), (2.01, 0.45), (3.0, 0.25), (4.02, 0.12)]))
    x *= np.exp(-t * 1.1) * (1 - np.exp(-t * 80))
    x = lp(np.tanh(x * 1.5), 900)
    x += bp(noise(len(t), seed), 2500, 9000) * np.exp(-t * 35) * 0.5
    st = reverb(x, 4.0, 2500, 0.4, seed)[: len(t)]
    return norm(st, 0.95)


LIB = {
    "impact": impact, "hit_metal": hit_metal, "whoosh": whoosh, "swish": swish, "riser": riser,
    "reverse_swell": reverse_swell, "sub_drop": sub_drop, "heartbeat": heartbeat, "tick": tick,
    "click_soft": click_soft, "glitch": glitch_burst, "shutter": shutter, "shimmer": shimmer,
    "boom_low": boom_low,
}


def get(name, sfx_dir=None, **kw):
    """Use sfx/<name>.wav if present (e.g. an ElevenLabs render), else synthesize."""
    if sfx_dir:
        p = os.path.join(sfx_dir, name + ".wav")
        if os.path.exists(p):
            import soundfile as sf
            x, sr = sf.read(p, dtype="float32", always_2d=True)
            if sr != SR:
                x = signal.resample_poly(x, SR, sr, axis=0).astype(np.float32)
            if x.shape[1] == 1:
                x = np.repeat(x, 2, 1)
            return x
    base = name.split("@")[0]
    return LIB[base](**kw)
