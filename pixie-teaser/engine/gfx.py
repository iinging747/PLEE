"""Motion-graphics elements: star sparkles, HUD lines, particles, ECG line, panels."""
import math

import cv2
import numpy as np

from .core import W, H, hash01, clamp, ease_out_expo
from . import fx

_STAR = {}
_DOT = {}


def star_alpha(size):
    """Curved four-point star (matches the PIXIE logo star)."""
    size = max(4, int(size)) | 1
    if size not in _STAR:
        r = size // 2
        y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32) / max(r, 1)
        p = 0.52
        d = np.abs(x) ** p + np.abs(y) ** p
        a = np.clip((1.0 - d) * r * 0.35 + 0.5, 0, 1)
        _STAR[size] = a.astype(np.float32)
    return _STAR[size]


def dot(sigma):
    key = round(sigma, 1)
    if key not in _DOT:
        r = int(sigma * 3) + 1
        y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
        _DOT[key] = np.exp(-(x * x + y * y) / (2 * sigma * sigma)).astype(np.float32)
    return _DOT[key]


def sparkle(frame, x, y, size, k, color=(1, 1, 1), streak=True, rot=0.0):
    """Star glint. k: 0..1 intensity."""
    if k <= 0.01:
        return frame
    s = star_alpha(size * (0.6 + 0.4 * k))
    if rot:
        m = cv2.getRotationMatrix2D((s.shape[1] / 2, s.shape[0] / 2), rot, 1.0)
        s = cv2.warpAffine(s, m, (s.shape[1], s.shape[0]))
    c = np.array(color, np.float32)
    h, w = s.shape
    gs = max(2, size * 0.18)
    pd = int(gs * 3) + 2
    glow = cv2.GaussianBlur(np.pad(s, pd), (0, 0), gs)
    fx.add_at(frame, glow[..., None] * c, x - w / 2 - pd, y - h / 2 - pd, 0.9 * k)
    fx.over(frame, c, s, x - w / 2, y - h / 2, k)
    if streak:
        L = int(size * 7)
        line = np.zeros((9, L), np.float32)
        xs = np.linspace(-1, 1, L, dtype=np.float32)
        line[4] = (1 - np.abs(xs)) ** 3
        line = cv2.GaussianBlur(line, (0, 0), 1.5)
        fx.add_at(frame, line[..., None] * c, x - L / 2, y - 4, 0.8 * k)
    return frame


def particles(frame, t, n, seed, color=(1, 0.9, 0.8), size=(1.2, 3.5), speed=18, strength=0.6, region=(0, 0, W, H)):
    if strength <= 0:
        return frame
    x0, y0, rw, rh = region
    c = np.array(color, np.float32)
    for i in range(n):
        sx = hash01(seed, i, "x")
        sy = hash01(seed, i, "y")
        sp = 0.4 + hash01(seed, i, "s")
        sig = size[0] + (size[1] - size[0]) * hash01(seed, i, "z")
        px = x0 + ((sx * rw + math.sin(t * 0.5 + i) * 30) % rw)
        py = y0 + ((sy * rh - t * speed * sp) % rh)
        tw = 0.5 + 0.5 * math.sin(t * (1.5 + sp * 2) + i * 2.1)
        d = dot(sig)
        fx.add_at(frame, d[..., None] * c, px - d.shape[1] / 2, py - d.shape[0] / 2, strength * tw)
    return frame


class Overlay:
    """8-bit AA line canvas composited once per frame (cv2 AA needs uint8)."""

    def __init__(self):
        self.a = np.zeros((H, W), np.uint8)
        self.used = False

    def line(self, p0, p1, th=2, v=255):
        cv2.line(self.a, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), int(v), th, cv2.LINE_AA)
        self.used = True

    def poly(self, pts, th=2, v=255, closed=False):
        p = np.array(pts, np.int32).reshape(-1, 1, 2)
        cv2.polylines(self.a, [p], closed, int(v), th, cv2.LINE_AA)
        self.used = True

    def rect(self, x0, y0, x1, y1, th=2, v=255):
        cv2.rectangle(self.a, (int(x0), int(y0)), (int(x1), int(y1)), int(v), th, cv2.LINE_AA)
        self.used = True

    def circle(self, c, r, th=2, v=255):
        cv2.circle(self.a, (int(c[0]), int(c[1])), int(r), int(v), th, cv2.LINE_AA)
        self.used = True

    def composite(self, frame, color=(1, 1, 1), opacity=1.0, glow=0.0):
        if not self.used or opacity <= 0:
            return frame
        x, y, w, h = cv2.boundingRect(self.a)
        if w == 0 or h == 0:
            return frame
        pd = 24
        x0, y0 = max(0, x - pd), max(0, y - pd)
        x1, y1 = min(W, x + w + pd), min(H, y + h + pd)
        a = self.a[y0:y1, x0:x1].astype(np.float32) / 255.0
        c = np.array(color, np.float32)
        if glow > 0:
            g = fx.fast_blur(a, 6)
            fx.add_at(frame, g[..., None] * c, x0, y0, glow * opacity)
        return fx.over(frame, c, a, x0, y0, opacity)


def hud_corners(ov, k, inset=70, arm=60, th=2):
    """Corner brackets that slide in (k 0..1)."""
    if k <= 0:
        return
    e = ease_out_expo(k)
    a = arm * e
    pts = [(inset, inset, 1, 1), (W - inset, inset, -1, 1), (inset, H - inset, 1, -1), (W - inset, H - inset, -1, -1)]
    for x, y, sx, sy in pts:
        ov.line((x, y), (x + sx * a, y), th)
        ov.line((x, y), (x, y + sy * a), th)


def ecg(ov, t, y, amp, beats, x0=0, x1=W, th=3, travel=0.0):
    """Heartbeat line: flat with spikes centred on given beat times, drawn up to progress."""
    xs = np.arange(x0, x1, 4, dtype=np.float32)
    ys = np.zeros_like(xs)
    span = 2.2  # seconds across screen
    tt = t - span + (xs - x0) / (x1 - x0) * span  # time each x represents (scrolling)
    for b in beats:
        d = tt - b
        ys += -np.exp(-(d / 0.018) ** 2) * 1.0 + np.exp(-((d - 0.035) / 0.02) ** 2) * 0.45
        ys += -np.exp(-((d - 0.2) / 0.016) ** 2) * 0.5
    pts = np.stack([xs, y + ys * amp], axis=1)
    ov.poly(pts, th)


def panel_mask(w, h, k, mode="up"):
    """Animated reveal mask for split-screen panels."""
    m = np.zeros((h, w), np.float32)
    e = ease_out_expo(k)
    if mode == "up":
        hh = int(h * e)
        if hh > 0:
            m[h - hh:] = 1
    elif mode == "down":
        hh = int(h * e)
        if hh > 0:
            m[:hh] = 1
    elif mode == "rl":
        ww = int(w * e)
        if ww > 0:
            m[:, w - ww:] = 1
    else:
        ww = int(w * e)
        if ww > 0:
            m[:, :ww] = 1
    return m
