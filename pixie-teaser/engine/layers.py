"""Pre-rendered layers (Blender chrome stills) animated in 2D: reveal, focus pull, push, light sweep."""
import math
import os

import cv2
import numpy as np

from .core import ROOT, W, H, clamp, ease_out_cubic, ease_out_expo, ease_in_out
from . import fx

BL = os.path.join(ROOT, "assets", "titles")
_cache = {}


def rgba(shot):
    """Cropped premultiplied RGB + alpha of work/bl/<shot>/still_0001.png and its frame offset."""
    if shot in _cache:
        return _cache[shot]
    p = os.path.join(BL, shot, "still_0001.png")
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(p)
    a = im[..., 3].astype(np.float32) / 255.0
    ys, xs = np.where(a > 0.004)
    pad = 40
    y0, y1 = max(0, ys.min() - pad), min(im.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(im.shape[1], xs.max() + pad)
    rgb = cv2.cvtColor(im[y0:y1, x0:x1, :3], cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    a = a[y0:y1, x0:x1]
    res = (rgb, a, x0, y0)
    _cache[shot] = res
    return res


def chrome(frame, shot, t, t_in, t_out, cx=None, cy=None, scale=1.0, push=0.035, focus=0.35,
           sweep=(0.15, 0.85), sweep_strength=0.85, reveal="focus", exit="fade", exit_len=0.25,
           opacity=1.0, shadow=0.55, darken=0.0, tint=None):
    """Draw a chrome still between t_in and t_out.

    reveal: 'focus' (blur->sharp + scale settle), 'rise' (slides up behind a baseline mask), 'cut' (hard).
    sweep: (start,end) as fractions of the shot's life for the specular band crossing the letters.
    darken: dims the picture behind (radial) so the title reads over footage.
    """
    if t < t_in or t >= t_out:
        return frame
    rgb, a, x0, y0 = rgba(shot)
    life = t_out - t_in
    k = (t - t_in) / life
    lt = t - t_in
    h, w = a.shape
    # entry
    s = scale * (1 + push * (1 - k))
    blur = 0.0
    op = opacity
    rise_mask = None
    if reveal == "focus":
        e = ease_out_cubic(clamp(lt / max(focus, 1e-3)))
        blur = (1 - e) * 18
        op *= clamp(lt / (focus * 0.6))
        s *= 1 + 0.06 * (1 - e)
    elif reveal == "slam":
        e = ease_out_expo(clamp(lt / 0.22))
        s *= 1 + 0.28 * (1 - e)
        blur = (1 - e) * 8
    elif reveal == "rise":
        e = ease_out_expo(clamp(lt / 0.55))
        rise_mask = e
    # exit
    to = t_out - t
    if exit == "fade" and to < exit_len:
        op *= ease_in_out(to / exit_len)
        blur = max(blur, (1 - to / exit_len) * 10)
    elif exit == "blur" and to < exit_len:
        q = 1 - to / exit_len
        blur = max(blur, q * 26)
        op *= 1 - q * q
        s *= 1 + 0.05 * q
    if op <= 0.002:
        return frame
    # light sweep (specular band across the letters, only on the chrome)
    img = rgb
    if sweep and sweep_strength > 0:
        ks = (k - sweep[0]) / (sweep[1] - sweep[0])
        if 0 < ks < 1:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            u = xx / w + (yy / h) * 0.35
            c = -0.3 + ks * 1.65
            band = np.exp(-((u - c) ** 2) / (2 * 0.045 ** 2)) + 0.35 * np.exp(-((u - c + 0.09) ** 2) / (2 * 0.02 ** 2))
            img = np.clip(rgb + (band * sweep_strength)[..., None] * a[..., None], 0, 1.0)
    if tint is not None:
        img = img * np.array(tint, np.float32)
    al = a
    if rise_mask is not None:
        off = int((1 - rise_mask) * h * 0.6)
        if off > 0:
            img = np.roll(img, off, axis=0)
            al = np.roll(al, off, axis=0)
            img[:off] = 0
            al = al.copy()
            al[:off] = 0
    if s != 1.0:
        nw, nh = int(w * s), int(h * s)
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        al = cv2.resize(al, (nw, nh), interpolation=cv2.INTER_LINEAR)
    if blur > 0.4:
        img = fx.fast_blur(img, blur)
        al = fx.fast_blur(al, blur)
    hh, ww = al.shape
    ccx = (x0 + w / 2) if cx is None else cx
    ccy = (y0 + h / 2) if cy is None else cy
    px, py = ccx - ww / 2, ccy - hh / 2
    if darken > 0:
        frame *= 1 - darken * _radial_dim(op)
    if shadow > 0:
        sh = fx.fast_blur(al, 18)
        fx.over(frame, np.zeros(3, np.float32), sh * shadow, px, py + 6, op)
    # rgb from Blender is already premultiplied against transparent film; treat as straight colour
    return fx.over(frame, img, al, px, py, op)


_RD = {}


def _radial_dim(amount):
    key = 0
    if key not in _RD:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * 0.55)) ** 2 + ((y - H / 2) / (H * 0.5)) ** 2)
        _RD[key] = np.clip(1.15 - d * 0.6, 0.35, 1.0)[..., None].astype(np.float32)
    return _RD[key] * amount
