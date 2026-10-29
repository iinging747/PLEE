"""Temporary soundtrack for the preview renders (replaced by the ElevenLabs mix).

Synthesises a quiet, beat-locked bed from build/<id>.json: pads, sub pulses,
hats, and an SFX hit on every storyboard cue, so the cuts can be judged in
time with music. Output: dist/audio/temp_music_<id>.wav (48 kHz stereo).

    python3 engine/temp_audio.py
"""
import json
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s
    A, D, R = int(a * SR), int(d * SR), int(r * SR)
    A = min(A, n)
    e[:A] = np.linspace(0, 1, A, endpoint=False)
    D = min(D, n - A)
    e[A:A + D] = np.linspace(1, s, D, endpoint=False)
    if R > 0:
        e[-R:] *= np.linspace(1, 0, R)
    return e


def pad_voice(freq, dur, bright=7.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.07, 0.0, 0.07):  # detuned unison, cents/100
        f = freq * 2 ** (det / 12)
        ph = rng.random() * 6.28
        for h in range(1, 9):
            out += np.sin(2 * np.pi * f * h * t + ph * h) * (1 / h) * np.exp(-h / bright)
    return out / 6.0


def lowpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def highpass(x, cutoff):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (cutoff / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


def reverb(x, secs=2.4, mix=0.25):
    n = int(secs * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir = lowpass(ir, 6000)
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[: len(x)]
    return x * (1 - mix) + y * mix * 0.6


def place(buf, sig, t, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def kick(f0=110, f1=42, dur=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9)


def hat(dur=0.035):
    n = int(dur * SR)
    return highpass(rng.standard_normal(n), 7000) * np.exp(-np.arange(n) / SR * 120)


def pluck(freq, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)) * np.exp(-t * 7)


def sfx(kind, dur=None):
    if kind in ("impact", "boom"):
        d = 2.2 if kind == "boom" else 1.4
        n = int(d * SR)
        t = np.arange(n) / SR
        f = 32 + 48 * np.exp(-t * 5)
        sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (1.6 if kind == "boom" else 2.6))
        nz = lowpass(rng.standard_normal(n), 1800) * np.exp(-t * 9) * 0.35
        return reverb(sub + nz, 2.8, 0.35) * (0.9 if kind == "boom" else 0.7)
    if kind == "hit":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        return (kick(160, 70, 0.35) * 0.5 + highpass(rng.standard_normal(n), 3000) * np.exp(-t * 60) * 0.25) * 0.7
    if kind == "whoosh":
        n = int(0.7 * SR)
        t = np.arange(n) / SR
        e = np.sin(np.pi * t / t[-1]) ** 2
        return lowpass(highpass(rng.standard_normal(n), 400), 5000) * e * 0.18
    if kind == "riser":
        d = dur or 3.0
        n = int(d * SR)
        t = np.arange(n) / SR
        e = (t / d) ** 2
        nz = highpass(rng.standard_normal(n), 1500) * e * 0.12
        tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * (t / d) ** 2) / SR) * e * 0.06
        return reverb(nz + tone, 1.5, 0.3)
    if kind == "ticks":
        d = dur or 1.3
        out = np.zeros(int(d * SR))
        for k in range(int(d / 0.0625)):
            place(out, hat(0.02) * (0.5 + 0.5 * (k % 2)), k * 0.0625, 0.35)
        return out
    return np.zeros(1)


def build(video_id, bpm, chords, style):
    v = json.load(open(os.path.join(ROOT, "build", video_id + ".json")))
    dur = v["dur"]
    n = int((dur + 3) * SR)
    pads = np.zeros(n)
    drums = np.zeros(n)
    beat = 60 / bpm
    bar = beat * 4
    # pads: one chord per two bars
    t = 0.0
    i = 0
    while t < dur:
        ch = chords[i % len(chords)]
        seg = bar * 2
        for note in ch:
            sig = pad_voice(midi(note), seg + 1.5, 5.0 if style == "pro" else 6.5) * env_adsr(int((seg + 1.5) * SR), 1.2, 0.5, 0.8, 1.4)
            place(pads, sig, t, 0.09)
        t += seg
        i += 1
    pads = reverb(lowpass(pads, 2600 if style == "pro" else 3400), 3.2, 0.35)
    # rhythm
    k = 0
    tt = 0.0
    while tt < dur - 1.5:
        if style == "pro":
            if tt >= 7.0:
                root = chords[int(tt / (bar * 2)) % len(chords)][0] - 24
                n_ = int(0.22 * SR)
                ts = np.arange(n_) / SR
                place(drums, np.sin(2 * np.pi * midi(root) * ts) * np.exp(-ts * 14), tt, 0.35)
            if 11.0 <= tt < dur - 6.0:
                place(drums, kick(), tt, 0.55)
                place(drums, hat(), tt + beat / 2, 0.12)
                place(drums, hat(0.02), tt + beat / 4, 0.05)
                place(drums, hat(0.02), tt + 3 * beat / 4, 0.05)
        else:
            if tt >= 1.0:
                if k % 2 == 0:
                    place(drums, kick(90, 45, 0.25), tt, 0.25)
                place(drums, hat(0.05), tt + beat / 2, 0.07)
                ch = chords[int(tt / (bar * 2)) % len(chords)]
                place(drums, pluck(midi(ch[(k * 2) % len(ch)] + 12)), tt, 0.07)
                place(drums, pluck(midi(ch[(k * 2 + 1) % len(ch)] + 12)), tt + beat / 2, 0.05)
        tt += beat
        k += 1
    fx = np.zeros(n)
    for c in v.get("cues", []):
        if style == "easy" and c["type"] == "whoosh" and c["t"] < 0.1:
            continue
        place(fx, sfx(c["type"], c.get("dur")), c["t"], 0.9 if style == "pro" else 0.6)
    mix = pads + drums + fx
    mix = mix[: int(dur * SR)]
    fade = int(1.2 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    mix = np.tanh(mix * 1.4) / 1.4
    peak = np.max(np.abs(mix)) or 1
    mix = mix / peak * (0.6 if style == "pro" else 0.42)
    # light stereo width: short delay on one side
    d = int(0.012 * SR)
    left = mix
    right = np.concatenate([np.zeros(d), mix[:-d]]) * 0.92 + mix * 0.08
    st = np.stack([left, right], axis=1)
    out = os.path.join(ROOT, "dist", "audio", f"temp_music_{video_id}.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    # keep a compact MP3 next to the WAV (the MP3 is what gets committed)
    mp3 = out[:-4] + ".mp3"
    os.system(f'ffmpeg -y -loglevel error -i "{out}" -b:a 192k "{mp3}"')
    print("wrote", mp3, f"{dur:.1f}s")


if __name__ == "__main__":
    # A minor: Am9 - Fmaj7 - Cmaj7 - G6 (pro) / C - G - Am - F (easy)
    build("pro", 120, [[57, 60, 64, 67, 71], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 64]], "pro")
    build("easy", 100, [[60, 64, 67, 72], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]], "easy")
