"""Frame effects. Frames are float32 RGB arrays in [0,1], shape (H, W, 3)."""
import math

import cv2
import numpy as np

from .core import W, H, hash01

cv2.setNumThreads(1)

# ------------------------------------------------------------------ geometry


def affine(img, scale=1.0, rot=0.0, tx=0.0, ty=0.0, center=None, out=(W, H),
           border=cv2.BORDER_REFLECT101, interp=cv2.INTER_LINEAR):
    """Scale/rotate about `center` (source px) and place it at output centre + (tx,ty)."""
    h, w = img.shape[:2]
    cx, cy = center if center is not None else (w / 2.0, h / 2.0)
    ow, oh = out
    a = math.radians(rot)
    c, s = math.cos(a) * scale, math.sin(a) * scale
    m = np.array([[c, -s, 0.0], [s, c, 0.0]], np.float32)
    m[0, 2] = ow / 2.0 + tx - (c * cx - s * cy)
    m[1, 2] = oh / 2.0 + ty - (s * cx + c * cy)
    return cv2.warpAffine(img, m, (ow, oh), flags=interp, borderMode=border)


def cover_scale(w, h, ow=W, oh=H):
    return max(ow / w, oh / h)


def contain_scale(w, h, ow=W, oh=H):
    return min(ow / w, oh / h)


# ------------------------------------------------------------------ colour

GRADES = {
    # name: dict(exp, contrast, sat, temp(+warm), tint(+magenta), lift rgb, gain rgb, fade)
    "neutral": dict(exp=0.0, con=1.05, sat=1.0, lift=(0, 0, 0), gain=(1, 1, 1), fade=0.0),
    "noir": dict(exp=-0.10, con=1.18, sat=0.55, lift=(0.035, 0.02, 0.05), gain=(0.96, 0.97, 1.04), fade=0.02),
    "trade": dict(exp=-0.05, con=1.15, sat=0.85, lift=(0.03, 0.015, 0.05), gain=(1.0, 0.98, 1.05), fade=0.01),
    "warm": dict(exp=0.03, con=1.08, sat=1.06, lift=(0.03, 0.02, 0.03), gain=(1.05, 1.0, 0.93), fade=0.015),
    "champagne": dict(exp=0.05, con=1.03, sat=0.92, lift=(0.05, 0.035, 0.04), gain=(1.05, 1.0, 0.94), fade=0.03),
    "beauty": dict(exp=0.06, con=0.98, sat=0.9, lift=(0.06, 0.035, 0.07), gain=(1.04, 0.98, 1.02), fade=0.04),
    "night": dict(exp=0.0, con=1.14, sat=1.12, lift=(0.02, 0.01, 0.05), gain=(0.98, 0.98, 1.06), fade=0.0),
    "vivid": dict(exp=0.02, con=1.12, sat=1.15, lift=(0.015, 0.01, 0.03), gain=(1.02, 1.0, 1.0), fade=0.0),
    "stage": dict(exp=0.0, con=1.16, sat=1.18, lift=(0.03, 0.0, 0.06), gain=(1.0, 0.97, 1.08), fade=0.0),
}


def grade(img, name="neutral", amount=1.0, extra_exp=0.0):
    g = GRADES[name]
    out = img
    exp = g["exp"] + extra_exp
    if exp:
        out = out * (2.0 ** exp)
    con = 1 + (g["con"] - 1) * amount
    if con != 1:
        out = (out - 0.45) * con + 0.45
    sat = 1 + (g["sat"] - 1) * amount
    if sat != 1:
        lum = out[..., 0:1] * 0.2126 + out[..., 1:2] * 0.7152 + out[..., 2:3] * 0.0722
        out = lum + (out - lum) * sat
    lift = np.array(g["lift"], np.float32) * amount
    gain = 1 + (np.array(g["gain"], np.float32) - 1) * amount
    out = out * gain + lift * (1 - np.clip(out, 0, 1))
    fade = g["fade"] * amount
    if fade:
        out = out * (1 - fade) + fade
    return np.clip(out, 0, 1, out=out).astype(np.float32, copy=False)


_LUTS = {}
_LW = np.array([0.2126, 0.7152, 0.0722], np.float32)


def grade_u8(img, name="neutral", amount=1.0, extra_exp=0.0):
    """Fast grade for uint8 RGB: 3x3 saturation matrix + per-channel 1D LUT. Returns uint8."""
    key = (name, round(amount, 3), round(extra_exp, 3))
    if key not in _LUTS:
        g = GRADES[name]
        x = np.arange(256, dtype=np.float32)[:, None].repeat(3, 1) / 255.0
        x = x * (2.0 ** (g["exp"] + extra_exp))
        con = 1 + (g["con"] - 1) * amount
        x = (x - 0.45) * con + 0.45
        lift = np.array(g["lift"], np.float32) * amount
        gain = 1 + (np.array(g["gain"], np.float32) - 1) * amount
        x = x * gain + lift * (1 - np.clip(x, 0, 1))
        fade = g["fade"] * amount
        x = x * (1 - fade) + fade
        lut = np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8).reshape(1, 256, 3)
        sat = 1 + (g["sat"] - 1) * amount
        m = None
        if abs(sat - 1) > 1e-3:
            m = (np.eye(3, dtype=np.float32) * sat + (1 - sat) * np.repeat(_LW[None, :], 3, 0)).astype(np.float32)
        _LUTS[key] = (lut, m)
    lut, m = _LUTS[key]
    if m is not None:
        img = cv2.transform(img, m)
    return cv2.LUT(img, lut)


def to_f32(img_u8):
    return np.multiply(img_u8, np.float32(1 / 255.0), dtype=np.float32)


def _box(x, r):
    return cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1), borderType=cv2.BORDER_REFLECT101)


def guided(I, p, r, eps):
    """He et al. guided filter (grey guide), all float32."""
    mI, mp = _box(I, r), _box(p, r)
    cov = _box(I * p, r) - mI * mp
    var = _box(I * I, r) - mI * mI
    a = cov / (var + eps)
    bb = mp - a * mI
    return _box(a, r) * I + _box(bb, r)


def beauty(img, amount=0.6, brighten=0.025):
    """Natural skin retouch: edge-preserving smoothing on skin tones only, keeps fine texture,
    lashes, iris and hair; slight lift and warmth on skin. img float32 RGB."""
    if amount <= 0:
        return img
    h, w = img.shape[:2]
    f = 2 if w >= 1280 else 1
    small = cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA) if f > 1 else img
    u8 = np.clip(small * 255, 0, 255).astype(np.uint8)
    ycc = cv2.cvtColor(u8, cv2.COLOR_RGB2YCrCb).astype(np.float32)
    cr, cb, y = ycc[..., 1], ycc[..., 2], ycc[..., 0]
    # soft skin likelihood (Cr/Cb ellipse-ish window), excluding very dark pixels (lashes, pupils, hair)
    skin = np.clip(1 - np.abs(cr - 152) / 22, 0, 1) * np.clip(1 - np.abs(cb - 110) / 24, 0, 1)
    skin *= np.clip((y - 70) / 40, 0, 1)
    skin = cv2.GaussianBlur(skin, (0, 0), 3)
    sm = np.empty_like(small)
    for c in range(3):
        sm[..., c] = guided(small[..., c], small[..., c], 6 // f + 3, 0.0025)
    if f > 1:
        sm = cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR)
        skin = cv2.resize(skin, (w, h), interpolation=cv2.INTER_LINEAR)
    m = (skin * amount)[..., None]
    detail = img - cv2.GaussianBlur(img, (0, 0), 1.0)          # keep pore-level texture so it isn't plastic
    out = img + (sm - img) * m + detail * m * 0.35
    out = out + m * np.array([brighten * 1.1, brighten, brighten * 0.85], np.float32)
    return np.clip(out, 0, 1).astype(np.float32)


def tint_mix(img, color, amount):
    if amount <= 0:
        return img
    return img * (1 - amount) + np.array(color, np.float32) * amount * (0.25 + 0.75 * img)


# ------------------------------------------------------------------ blur family


def fast_blur(img, sigma):
    if sigma <= 0.3:
        return img
    if sigma > 6:
        f = 4 if sigma > 18 else 2
        small = cv2.resize(img, (img.shape[1] // f, img.shape[0] // f), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sigma / f)
        return cv2.resize(small, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(img, (0, 0), sigma)


def dir_blur(img, length, angle=0.0):
    """Directional (whip) motion blur. length in px."""
    if length < 1.5:
        return img
    f = 2 if length > 24 else 1
    src = cv2.resize(img, (img.shape[1] // f, img.shape[0] // f), interpolation=cv2.INTER_AREA) if f > 1 else img
    L = max(3, int(length / f) | 1)
    k = np.zeros((L, L), np.float32)
    k[L // 2, :] = 1.0
    rot = cv2.getRotationMatrix2D((L / 2 - 0.5, L / 2 - 0.5), angle, 1.0)
    k = cv2.warpAffine(k, rot, (L, L))
    k /= max(k.sum(), 1e-6)
    out = cv2.filter2D(src, -1, k, borderType=cv2.BORDER_REFLECT101)
    if f > 1:
        out = cv2.resize(out, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return out


def zoom_blur(img, amount, samples=7, center=None):
    """Radial zoom blur. amount ~0..0.25 (fractional scale spread)."""
    if amount < 0.004:
        return img
    h, w = img.shape[:2]
    f = 2
    small = cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    cx, cy = (sw / 2, sh / 2) if center is None else (center[0] / f, center[1] / f)
    acc = np.zeros_like(small)
    for i in range(samples):
        s = 1 + amount * i / (samples - 1)
        m = np.array([[s, 0, cx - s * cx], [0, s, cy - s * cy]], np.float32)
        acc += cv2.warpAffine(small, m, (sw, sh), borderMode=cv2.BORDER_REFLECT101)
    acc /= samples
    blurred = cv2.resize(acc, (w, h), interpolation=cv2.INTER_LINEAR)
    # keep the centre a bit sharper
    return blurred


# ------------------------------------------------------------------ glitch / chroma


def rgb_split(img, px, angle=0.0):
    if abs(px) < 0.5:
        return img
    dx = px * math.cos(math.radians(angle))
    dy = px * math.sin(math.radians(angle))
    h, w = img.shape[:2]
    out = img.copy()
    m1 = np.array([[1, 0, dx], [0, 1, dy]], np.float32)
    m2 = np.array([[1, 0, -dx], [0, 1, -dy]], np.float32)
    out[..., 0] = cv2.warpAffine(img[..., 0], m1, (w, h), borderMode=cv2.BORDER_REFLECT101)
    out[..., 2] = cv2.warpAffine(img[..., 2], m2, (w, h), borderMode=cv2.BORDER_REFLECT101)
    return out


def chroma_radial(img, amount):
    """Lens-style chromatic aberration (R scaled out, B scaled in). amount ~0..0.02"""
    if amount < 0.0008:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    for ch, s in ((0, 1 + amount), (2, 1 - amount)):
        m = np.array([[s, 0, w / 2 * (1 - s)], [0, s, h / 2 * (1 - s)]], np.float32)
        out[..., ch] = cv2.warpAffine(img[..., ch], m, (w, h), borderMode=cv2.BORDER_REFLECT101)
    return out


def glitch(img, intensity, seed):
    """Horizontal slice displacement + per-slice chroma offset + a few block repeats."""
    if intensity <= 0.01:
        return img
    h, w = img.shape[:2]
    out = img.copy()
    n = int(4 + 14 * intensity)
    for i in range(n):
        r = hash01(seed, i, "y")
        y0 = int(r * h)
        bh = int(6 + hash01(seed, i, "h") * 90 * intensity)
        y1 = min(h, y0 + bh)
        if y1 <= y0:
            continue
        sh = int((hash01(seed, i, "x") * 2 - 1) * 220 * intensity)
        band = np.roll(img[y0:y1], sh, axis=1)
        if hash01(seed, i, "c") > 0.5:
            band = band.copy()
            band[..., 0] = np.roll(band[..., 0], int(18 * intensity), axis=1)
            band[..., 2] = np.roll(band[..., 2], -int(18 * intensity), axis=1)
        out[y0:y1] = band
    # quantised colour flicker on a few rows
    if intensity > 0.5:
        y0 = int(hash01(seed, "q") * (h - 40))
        out[y0:y0 + 30] = np.round(out[y0:y0 + 30] * 4) / 4
    return out


# ------------------------------------------------------------------ light


def screen(a, b):
    return a + b - a * b


def add_glow(img, layer, strength=1.0):
    return np.clip(img + layer * strength, 0, 1)


def bloom(img, threshold=0.72, strength=0.5, sigma=28):
    if strength <= 0:
        return img
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA)
    lum = small.max(axis=2, keepdims=True)
    hi = small * np.clip((lum - threshold) / (1 - threshold + 1e-6), 0, 1)
    hi = cv2.GaussianBlur(hi, (0, 0), sigma / 4)
    hi = cv2.resize(hi, (w, h), interpolation=cv2.INTER_LINEAR)
    return screen(img, np.clip(hi * strength, 0, 1))


_VIG = {}


def vignette(img, strength=0.35, roundness=1.0):
    if strength <= 0:
        return img
    key = (img.shape[1], img.shape[0], round(roundness, 2), round(strength, 3))
    if key not in _VIG:
        h, w = img.shape[:2]
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        nx = (x - w / 2) / (w / 2)
        ny = (y - h / 2) / (h / 2) * roundness
        d = np.sqrt(nx * nx * 0.75 + ny * ny)
        v = np.clip(1 - np.clip(d - 0.45, 0, None) ** 1.6, 0, 1)
        _VIG[key] = np.repeat((1 - strength + strength * v)[..., None], 3, 2).astype(np.float32)
    img *= _VIG[key]
    return img


_GRAIN = []


def grain(img, amount, frame):
    if amount <= 0:
        return img
    if not _GRAIN:
        rng = np.random.default_rng(7)
        for _ in range(8):
            n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            n = cv2.GaussianBlur(n, (0, 0), 0.6)
            n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
            _GRAIN.append(np.repeat(n[..., None], 3, 2))
    n = _GRAIN[frame % len(_GRAIN)]
    cv2.scaleAdd(n, float(amount), img, dst=img)
    return img


def light_leak(t, colors, strength, seed=0, scale=1.0):
    """Procedural drifting light leak, returns additive RGB layer (H,W,3)."""
    if strength <= 0:
        return None
    sw, sh = 192, 108
    y, x = np.mgrid[0:sh, 0:sw].astype(np.float32)
    acc = np.zeros((sh, sw, 3), np.float32)
    for i, col in enumerate(colors):
        ph = hash01(seed, i) * 6.28
        cx = sw * (0.5 + 0.55 * math.sin(t * 0.23 * scale + ph))
        cy = sh * (0.5 + 0.45 * math.cos(t * 0.17 * scale + ph * 1.7))
        rad = sw * (0.28 + 0.12 * math.sin(t * 0.31 + i))
        g = np.exp(-(((x - cx) ** 2) + ((y - cy) ** 2)) / (2 * rad * rad))
        acc += g[..., None] * np.array(col, np.float32)
    acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    return np.clip(acc * strength, 0, 1)


def light_sweep(img, k, angle=-20.0, width=0.18, strength=0.55, color=(1, 1, 1)):
    """Diagonal bright band sweeping across the frame. k in [0,1] = position."""
    if k <= 0 or k >= 1 or strength <= 0:
        return img
    h, w = img.shape[:2]
    a = math.radians(angle)
    y, x = np.ogrid[0:h, 0:w]
    u = (x / w) * math.cos(a) + (y / h) * math.sin(a)
    u0 = -0.4 + k * 1.9
    band = np.exp(-((u - u0) ** 2) / (2 * (width / 2.5) ** 2)).astype(np.float32)
    return screen(img, band[..., None] * np.array(color, np.float32) * strength)


def letterbox(img, bar_px, color=(0, 0, 0)):
    b = int(round(bar_px))
    if b <= 0:
        return img
    img[:b] = color
    img[-b:] = color
    return img


def flash(img, amount, color=(1, 1, 1), mode="screen"):
    if amount <= 0:
        return img
    c = np.array(color, np.float32) * amount
    if mode == "add":
        return np.clip(img + c, 0, 1)
    return screen(img, c)


def over(dst, rgb, alpha, x=0, y=0, opacity=1.0):
    """Alpha-composite rgb(h,w,3)/alpha(h,w) onto dst at (x,y); clipped to frame."""
    if opacity <= 0:
        return dst
    h, w = alpha.shape[:2]
    H_, W_ = dst.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W_, x0 + w), min(H_, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return dst
    sx1, sy1 = sx0 + (dx1 - dx0), sy0 + (dy1 - dy0)
    a = alpha[sy0:sy1, sx0:sx1, None] * opacity
    src = rgb[sy0:sy1, sx0:sx1] if rgb.ndim == 3 else rgb
    region = dst[dy0:dy1, dx0:dx1]
    region *= (1 - a)
    region += src * a
    return dst


def add_at(dst, rgb, x=0, y=0, amount=1.0):
    """Additive blend (for glows) at (x,y)."""
    h, w = rgb.shape[:2]
    H_, W_ = dst.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    dx1, dy1 = min(W_, x0 + w), min(H_, y0 + h)
    if dx1 <= dx0 or dy1 <= dy0:
        return dst
    sx1, sy1 = sx0 + (dx1 - dx0), sy0 + (dy1 - dy0)
    region = dst[dy0:dy1, dx0:dx1]
    region += rgb[sy0:sy1, sx0:sx1] * amount
    np.clip(region, 0, 1, out=region)
    return dst
