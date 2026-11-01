"""Shared constants, music grid and easing helpers for the PIXIE teaser."""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
WORK = os.environ.get("PIXIE_WORK", os.path.join(ROOT, "work"))
DIST = os.path.join(ROOT, "dist")

W, H, FPS = 1920, 1080, 30
DUR = 120.0
NF = int(round(DUR * FPS))

# ---- music grid (PIXIE_ElevenLabs_BGM: 128 BPM, measured downbeat phase) ----
BPM = 128.0
BEAT = 60.0 / BPM            # 0.46875 s
T0 = 0.2504                  # first downbeat (phrase 0)
E8 = BEAT / 2


def beat(b):
    """Time of quarter-note beat b (fractions allowed)."""
    return T0 + b * BEAT


def bar(n):
    return beat(4 * n)


def phrase(n):
    """4-bar phrase starts: 0.25, 7.75, 15.25, ... 112.75 (big section hits)."""
    return beat(16 * n)


def fr(t):
    """Seconds -> nearest frame index."""
    return int(round(t * FPS))


# ---- palette (from the storyboard) ----
def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


PLUM = hexc("#21182d")
VIOLET = hexc("#7a5aa6")
LILAC = hexc("#c9b3ea")
CHAMPAGNE = hexc("#d8bf9e")
SILVER = hexc("#cfd3da")
BLACK = hexc("#0b0b0d")
WHITE = (1.0, 1.0, 1.0)


# ---- easing ----
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def prog(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def lerp(a, b, k):
    return a + (b - a) * k


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_cubic(x):
    x = clamp(x)
    return x ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def ease_out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_expo(x):
    x = clamp(x)
    return 0.0 if x <= 0 else 2 ** (10 * x - 10)


def ease_in_out_expo(x):
    x = clamp(x)
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2


def ease_out_back(x, s=1.70158):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def decay(t, t0, length):
    """1 at t0, exponential-ish fall to 0 after `length` seconds; 0 before t0."""
    if t < t0:
        return 0.0
    k = (t - t0) / max(length, 1e-6)
    return 0.0 if k >= 1 else (1 - k) ** 2


def pulse(t, t0, attack, release):
    if t < t0 - attack or t > t0 + release:
        return 0.0
    if t < t0:
        return ease_in_cubic((t - (t0 - attack)) / attack) if attack > 0 else 1.0
    return (1 - (t - t0) / release) ** 2


def hash01(*args):
    """Deterministic pseudo-random in [0,1)."""
    h = 2166136261
    for a in args:
        for ch in str(a):
            h = (h ^ ord(ch)) * 16777619 & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5bd1e995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


def smooth_noise(t, seed, freq=1.0):
    """Cheap smooth 1D noise in [-1,1]."""
    x = t * freq
    i = math.floor(x)
    f = x - i
    a = hash01(seed, i) * 2 - 1
    b = hash01(seed, i + 1) * 2 - 1
    f = f * f * (3 - 2 * f)
    return a + (b - a) * f
