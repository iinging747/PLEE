"""Kinetic typography: glyph-level layout, per-letter animation, glow, wipe, scramble."""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .core import FONTS, hash01
from . import fx

FONT_FILES = {
    # refined display serif (high contrast, fashion-editorial)
    "didone": "BodoniModa-Regular.ttf",
    "didone_m": "BodoniModa-Medium.ttf",
    "didone_i": "BodoniModa-Italic.ttf",
    "garamond_l": "Cormorant-Light.ttf",
    "garamond": "Cormorant-Regular.ttf",
    "garamond_li": "Cormorant-LightItalic.ttf",
    "garamond_i": "Cormorant-Italic.ttf",
    "garamond_mi": "Cormorant-MediumItalic.ttf",
    "italiana": "Italiana.ttf",
    "cinzel": "Cinzel-Medium.ttf",
    "playfair_i": "Playfair-Italic.ttf",
    # thin geometric sans for labels
    "jost_xl": "Jost-ExtraLight.ttf",
    "jost_l": "Jost-Light.ttf",
    "jost": "Jost-Regular.ttf",
    "jost_m": "Jost-Medium.ttf",
    "tenor": "TenorSans.ttf",
    "mont_l": "Montserrat-Light.ttf",
    "mono": "JetBrainsMono-Regular.ttf",
    # Korean
    "kr_t": "Pretendard-Thin.otf",
    "kr_xl": "Pretendard-ExtraLight.otf",
    "kr_l": "Pretendard-Light.otf",
    "kr": "Pretendard-Regular.otf",
    "kr_m": "Pretendard-Medium.otf",
    "kr_sb": "Pretendard-SemiBold.otf",
}

_fonts = {}
_glyphs = {}
_layouts = {}


def font(name, size):
    key = (name, int(size))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.join(FONTS, FONT_FILES[name]), int(size))
    return _fonts[key]


def glyph(name, size, ch, stroke=0):
    """Alpha mask for one glyph, plus its offset from the pen position on the baseline."""
    key = (name, int(size), ch, stroke)
    g = _glyphs.get(key)
    if g is None:
        f = font(name, size)
        if ch.strip() == "":
            g = (np.zeros((1, 1), np.float32), 0, 0)
        else:
            l, t, r, b = f.getbbox(ch, anchor="ls", stroke_width=stroke)
            pad = 2 + stroke
            w, h = int(r - l) + 2 * pad, int(b - t) + 2 * pad
            im = Image.new("L", (max(w, 1), max(h, 1)), 0)
            d = ImageDraw.Draw(im)
            d.text((pad - l, pad - t), ch, font=f, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
            a = np.asarray(im, np.float32) / 255.0
            if stroke:
                im2 = Image.new("L", im.size, 0)
                ImageDraw.Draw(im2).text((pad - l, pad - t), ch, font=f, fill=255, anchor="ls")
                a = np.clip(a - np.asarray(im2, np.float32) / 255.0, 0, 1)
            g = (a, int(l) - pad, int(t) - pad)
        _glyphs[key] = g
    return g


def layout(text, name, size, tracking=0.0):
    """Returns list of (char, pen_x), total width, cap height, ascent, descent."""
    key = (text, name, int(size), round(tracking, 4))
    hit = _layouts.get(key)
    if hit is not None:
        return hit
    f = font(name, size)
    out = []
    # prefix lengths keep the font's own kerning pairs, then tracking is added per glyph
    for i, ch in enumerate(text):
        out.append((ch, f.getlength(text[:i]) + tracking * size * i))
    width = f.getlength(text) + tracking * size * max(len(text) - 1, 0)
    ref = "가" if any("가" <= c <= "힣" for c in text) else "H"
    l, t, r, b = f.getbbox(ref, anchor="ls")
    cap = -t
    asc, desc = f.getmetrics()
    res = (out, width, cap, asc, desc)
    _layouts[key] = res
    return res


def text_width(text, name, size, tracking=0.0):
    return layout(text, name, size, tracking)[1]


SCRAMBLE_SET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$%&@/<>+=*"


def draw_text(frame, text, name, size, cx, cy, color=(1, 1, 1), opacity=1.0, tracking=0.0,
              anim=None, scale=1.0, blur=0.0, mblur=0.0, glow=0.0, glow_color=None, glow_sigma=14,
              shadow=0.45, outline=0, wipe=None, align="center", gradient=None, scramble=None,
              chroma=0.0, frame_no=0):
    """Draw `text` centred (or left/right aligned) at (cx, cy = optical centre of caps).

    anim(i, n) -> (dx, dy, alpha) per glyph.
    wipe = (k, softness_px, direction) reveal mask, direction 'lr' | 'rl' | 'c' (from centre).
    scramble = (k, seed): glyphs not yet locked show random characters.
    gradient = callable(h, w) -> (h,w,3) fill image (e.g. silver).
    """
    if opacity <= 0.001 or not text:
        return frame
    items, width, cap, asc, desc = layout(text, name, size, tracking)
    n = len(items)
    margin = int(size * 0.6 + glow_sigma * 2 + 40)
    cw = int(width + 2 * margin)
    ch_ = int(asc + desc + 2 * margin)
    canvas = np.zeros((ch_, cw), np.float32)
    base_y = margin + asc
    for i, (c, px) in enumerate(items):
        if c == " ":
            continue
        dx = dy = 0.0
        a = 1.0
        if anim is not None:
            dx, dy, a = anim(i, n)
            if a <= 0.002:
                continue
        cc = c
        if scramble is not None:
            k, seed = scramble
            lock = (i / max(n - 1, 1)) * 0.75
            if k < lock + 0.25:
                if k < lock:
                    cc = SCRAMBLE_SET[int(hash01(seed, i, frame_no // 2) * len(SCRAMBLE_SET))]
        ga, ox, oy = glyph(name, size, cc, outline)
        gx = int(round(margin + px + ox + dx))
        gy = int(round(base_y + oy + dy))
        h, w = ga.shape
        x0, y0 = max(gx, 0), max(gy, 0)
        x1, y1 = min(gx + w, cw), min(gy + h, ch_)
        if x1 > x0 and y1 > y0:
            region = canvas[y0:y1, x0:x1]
            np.maximum(region, ga[y0 - gy:y1 - gy, x0 - gx:x1 - gx] * a, out=region)

    if wipe is not None:
        k, soft, direction = wipe
        xs = np.arange(cw, dtype=np.float32)
        x_l, x_r = margin, margin + width
        if direction == "lr":
            edge = x_l - soft + (x_r - x_l + 2 * soft) * k
            m = np.clip((edge - xs) / soft, 0, 1)
        elif direction == "rl":
            edge = x_r + soft - (x_r - x_l + 2 * soft) * k
            m = np.clip((xs - edge) / soft, 0, 1)
        else:  # centre out
            half = (width / 2 + soft) * k
            m = np.clip((half - np.abs(xs - (x_l + width / 2))) / soft, 0, 1)
        canvas *= m[None, :]

    if scale != 1.0:
        nw, nh = max(1, int(cw * scale)), max(1, int(ch_ * scale))
        canvas = cv2.resize(canvas, (nw, nh), interpolation=cv2.INTER_LINEAR if scale > 1 else cv2.INTER_AREA)
    if mblur > 1:
        canvas = fx.dir_blur(canvas[..., None].repeat(3, 2), mblur, 0)[..., 0]
    if blur > 0.3:
        canvas = cv2.GaussianBlur(canvas, (0, 0), blur)

    hh, ww = canvas.shape
    s = scale
    if align == "center":
        ox_ = cx - (margin + width / 2) * s
    elif align == "left":
        ox_ = cx - margin * s
    else:
        ox_ = cx - (margin + width) * s
    oy_ = cy - (base_y - cap / 2) * s

    if shadow > 0:
        sh = fx.fast_blur(canvas, max(4, size * 0.08))
        fx.over(frame, np.zeros(3, np.float32), sh * shadow, ox_ + 3, oy_ + 5, opacity)
    if glow > 0:
        gl = fx.fast_blur(canvas, glow_sigma)
        gc = np.array(glow_color if glow_color is not None else color, np.float32)
        fx.add_at(frame, gl[..., None] * gc, ox_, oy_, glow * opacity)
    fill = gradient(hh, ww) if gradient is not None else np.array(color, np.float32)
    if chroma > 0.5:
        cr = int(chroma)
        fx.add_at(frame, canvas[..., None] * np.array([0.9, 0.0, 0.25], np.float32), ox_ - cr, oy_, 0.55 * opacity)
        fx.add_at(frame, canvas[..., None] * np.array([0.0, 0.35, 0.95], np.float32), ox_ + cr, oy_, 0.55 * opacity)
    fx.over(frame, fill, canvas, ox_, oy_, opacity)
    return frame


def silver_gradient(h, w):
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    base = 0.62 + 0.36 * np.cos((y - 0.32) * 5.2) ** 2
    base = np.clip(base - 0.18 * (y > 0.55) * (y - 0.55) * 2, 0.35, 1)
    g = np.repeat(base, w, axis=1)
    return np.stack([g * 0.96, g * 0.97, g * 1.0], axis=-1).astype(np.float32)


# ---------------------------------------------------------------- animation presets


def a_rise(k, dist=60, stagger=0.06, fade=True):
    """Letters rise into place with stagger. k = global progress 0..1."""
    from .core import ease_out_expo

    def f(i, n):
        local = (k * (1 + stagger * n) - stagger * i)
        e = ease_out_expo(local)
        return 0.0, (1 - e) * dist, (e if fade else 1.0)
    return f


def a_type(k):
    def f(i, n):
        return 0.0, 0.0, 1.0 if i < k * n else 0.0
    return f


def a_spread(k, spread=0.6):
    """Letters fly in from the centre spread."""
    from .core import ease_out_expo

    def f(i, n):
        e = ease_out_expo(k)
        off = (i - (n - 1) / 2) * spread * 40 * (1 - e)
        return off, 0.0, e
    return f


def a_flicker(k, seed):
    def f(i, n):
        r = hash01(seed, i)
        on = k > r * 0.6 and (k > r * 0.6 + 0.12 or hash01(seed, i, int(k * 40)) > 0.4)
        return 0.0, 0.0, 1.0 if on else 0.0
    return f
