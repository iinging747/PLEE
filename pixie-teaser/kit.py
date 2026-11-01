"""Shared edit kit (sources, clip/typography/transition helpers) for the PIXIE teaser timelines.

Everything is timed on the BGM grid: 128 BPM, beat b(n) = 0.2504 + n*0.46875 s.
Phrase hits (every 16 beats): 0.25 7.75 15.25 22.75 30.25 37.75 45.25 52.75 60.25 67.75 75.25 82.75 90.25 97.75 105.25 112.75
"""
import csv
import math
import unicodedata
import os

import numpy as np

from engine.core import beat as b, W, H, FPS, VIOLET, LILAC, CHAMPAGNE, SILVER, WHITE, PLUM, clamp, prog, \
    ease_out_expo, ease_out_cubic, ease_in_out, hash01
from engine import text as T, gfx, fx, layers

MEDIA = os.environ.get("PIXIE_MEDIA", "/tmp/claude-0/-home-user-PLEE/61b5d1dc-927d-5a82-bc2a-0ccef111c741/scratchpad/src")
EXTRA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media_extra")  # full-size clips dropped later

LIVE_DATE = None  # e.g. "2026. 12. 05" once the first live is confirmed

# ----------------------------------------------------------------------------- sources

SOURCES = {}
_rows = list(csv.DictReader(open(os.path.join(MEDIA, "manifest.tsv")), delimiter="\t"))
for r in _rows:
    if r["kind"] == "photo":
        SOURCES[r["index"]] = dict(kind="photo", path=r["local_path"], headroom=1.25)
    else:
        title = unicodedata.normalize("NFC", r["title"])
        key = {"눈2.mp4": "eye2", "눈3.mp4": "eye3", "눈4.mp4": "eye4", "눈.mp4": "eye1"}.get(title, r["index"])
        fit = "width" if key.startswith("eye") else "cover"
        SOURCES[key] = dict(kind="video", path=r["local_path"], fit=fit, has_audio=r["has_audio"] == "yes",
                            headroom=1.0, title=title)

for _k, _f, _crop in (("M1", "makeup_look.mp4", (1280, 340, 0, 190)), ("M2", "makeup_lip.mp4", (1920, 628, 0, 216)),
                      ("M3", "makeup_eye.mp4", (1280, 344, 0, 188))):
    _p = os.path.join(EXTRA, _f)
    if os.path.exists(_p):
        SOURCES[_k] = dict(kind="video", path=_p, fit="cover", crop=_crop, has_audio=_k != "M3", headroom=1.0)

CLIPS = []
EVENTS = []
SFX = []


def has(key):
    return key in SOURCES


# ----------------------------------------------------------------------------- clip helpers

def ph(pid, b0, b1, z0=1.03, z1=1.12, focus=(0.5, 0.5), focus1=None, grade="neutral", exp=0.0, **kw):
    c = dict(src=pid, t0=b(b0), t1=b(b1), z0=z0, z1=z1, focus=focus, grade=grade, exp=exp, ease="out")
    if focus1:
        c["focus1"] = focus1
    if pid in FACES:
        c["fx"] = [dict(type="beauty", amt=BEAUTY)]
    c.update(kw)
    CLIPS.append(c)
    return c


FACES = {"P129", "P142", "P057"}
BEAUTY = 0.6


def vid(key, b0, b1, t_in, speed=1.0, **kw):
    if not has(key):
        return None
    c = dict(src=key, t0=b(b0), t1=b(b1), speed=speed, fit=SOURCES[key].get("fit", "cover"), ease="out")
    c["in"] = t_in
    if key.startswith("eye") or key.startswith("M"):
        c["fx"] = [dict(type="beauty", amt=BEAUTY)]
    c.update(kw)
    CLIPS.append(c)
    return c


def tri(b0, b1, pids, stagger=0.5, grade="night", exp=0.0, focus=None):
    """Three vertical panels sliding in on the beat (portrait photos)."""
    gap = 8
    pw = (W - 2 * gap) // 3
    for i, pid in enumerate(pids):
        x = i * (pw + gap)
        t_in = b(b0 + i * stagger)
        mode = "up" if i % 2 == 0 else "down"

        def mask(t, bw, bh, t_in=t_in, mode=mode):
            return gfx.panel_mask(bw, bh, (t - t_in) / 0.35, mode)
        CLIPS.append(dict(src=pid, t0=t_in, t1=b(b1), box=(x, 0, pw, H), z0=1.12, z1=1.0, ease="out",
                          focus=(focus[i] if focus else (0.5, 0.5)), grade=grade, exp=exp, mask=mask, layer=1))
        SFX.append(dict(t=t_in, name="swish", db=-16, kw=dict(seed=60 + i)))
    # black underlay so gaps read clean
    EVENTS.append(dict(type="draw", t0=b(b0), t1=b(b1), fn=lambda f, t, k, fi: None))


# ----------------------------------------------------------------------------- transitions

def cut(bb, kind="punch", amt=1.0, sfx=True):
    t = b(bb)
    if kind == "punch":
        EVENTS.append(dict(type="punch", t=t, dur=0.32, amt=0.07 * amt))
        if sfx:
            SFX.append(dict(t=t, name="swish", db=-15, kw=dict(seed=int(bb * 7) % 97)))
    elif kind == "flash":
        EVENTS.append(dict(type="flash", t=t, dur=0.28, amt=0.85 * amt))
        EVENTS.append(dict(type="punch", t=t, dur=0.4, amt=0.09 * amt))
        EVENTS.append(dict(type="rgb", t=t, dur=0.22, px=14 * amt))
        if sfx:
            SFX.append(dict(t=t, name="impact", db=-9, duck=-4, duck_len=0.6))
    elif kind == "whip":
        ang = 0 if int(bb * 2) % 2 == 0 else 180
        EVENTS.append(dict(type="whip", t=t, pre=0.13, dur=0.13, px=220 * amt, angle=ang))
        if sfx:
            SFX.append(dict(t=t - 0.16, name="whoosh", db=-12, kw=dict(dur=0.45, seed=int(bb * 3) % 89)))
    elif kind == "zoom":
        EVENTS.append(dict(type="zblur", t=t, pre=0.16, dur=0.2, amt=0.22 * amt))
        EVENTS.append(dict(type="flash", t=t, dur=0.18, amt=0.35 * amt))
        if sfx:
            SFX.append(dict(t=t - 0.3, name="whoosh", db=-11, kw=dict(dur=0.55, f0=200, f1=5200, seed=int(bb) % 79)))
    elif kind == "glitch":
        EVENTS.append(dict(type="glitch", t0=t - 0.03, t1=t + 0.2, amt=0.75 * amt, seed=int(bb * 11)))
        if sfx:
            SFX.append(dict(t=t - 0.03, name="glitch", db=-14, kw=dict(dur=0.25, seed=int(bb * 5) % 71)))
    elif kind == "blink":  # two black frames right before the beat
        EVENTS.append(dict(type="blackout", t0=t - 2.0 / FPS, t1=t))
    elif kind == "soft":
        EVENTS.append(dict(type="flash", t=t, dur=0.6, amt=0.55 * amt, color=(1, 0.96, 0.92)))
        if sfx:
            SFX.append(dict(t=t, name="shimmer", db=-18))


# ----------------------------------------------------------------------------- typography helpers

KR = "kr_bold"       # caption face (swap: assets/fonts/licensed/kr.otf -> Sandoll)
KR_TRACK = -0.05
LBL = "unb"


def _font_override():
    lic = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "licensed")
    for role, key in (("kr", "kr_lic"), ("kr_title", "kr_title_lic"), ("label", "label_lic")):
        for ext in (".otf", ".ttf"):
            p = os.path.join(lic, role + ext)
            if os.path.exists(p):
                T.FONT_FILES[key] = os.path.relpath(p, T.FONTS)
                globals()["KR" if role == "kr" else ("LBL" if role == "label" else "KR_TITLE")] = key


KR_TITLE = "kr_m"
_font_override()


def scrim(frame, strength=0.55, top=False):
    """Soft dark gradient at the bottom (or top) third so captions always read."""
    key = ("scrim", top)
    m = _SCRIM.get(key)
    if m is None:
        y = np.linspace(0, 1, H, dtype=np.float32)
        g = np.clip((y - 0.55) / 0.45, 0, 1) ** 1.4 if not top else np.clip((0.4 - y) / 0.4, 0, 1) ** 1.4
        m = g[:, None, None]
        _SCRIM[key] = m
    frame *= 1 - m * strength
    return frame


_SCRIM = {}


EN_FONT = "unb_l"


def caption(b0, b1, text, en=None, y=None, size=44, use_scrim=True, color=(0.95, 0.95, 0.97), font=None):
    """Bilingual caption: Korean main line + English line beneath (Cormorant italic, tight)."""
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.3), clamp((t1 - t) / 0.25))
        if use_scrim:
            scrim(frame, 0.62 * a)
        yy = (H - (172 if en else 150)) if y is None else y
        rise = (1 - ease_out_cubic(a)) * 10
        T.draw_text(frame, text, font or KR, size, W / 2, yy + rise, color=color, opacity=a,
                    tracking=KR_TRACK, shadow=0.55)
        if en:
            a2 = min(clamp((t - t0 - 0.12) / 0.35), clamp((t1 - t) / 0.25))
            T.draw_text(frame, en.upper(), EN_FONT, int(size * 0.4), W / 2, yy + size * 1.05 + rise,
                        color=(0.82, 0.82, 0.88), opacity=a2 * 0.9, tracking=0.0, shadow=0.5)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))


# ---- energy helpers ("바바박")

def bumps(b0, b1, amt=0.022, shake=3.5, every=1.0):
    """Camera bump on every beat (kick): micro zoom punch + tiny shake."""
    x = b0
    while x < b1 - 1e-6:
        EVENTS.append(dict(type="punch", t=b(x), dur=0.2, amt=amt))
        if shake:
            EVENTS.append(dict(type="shake", t=b(x), dur=0.16, amp=shake))
        x += every


def burst(b0, pids, step=0.5, grade="vivid", flash=0.45, shutter=True, focus=(0.5, 0.45), kz=1.18):
    """Photo burst: stills fired on 8th notes, each with a white pop + shutter click."""
    for i, pid in enumerate(pids):
        bb = b0 + i * step
        ph(pid, bb, bb + step, z0=kz + 0.02 * (i % 3), z1=kz + 0.08 + 0.02 * (i % 3), focus=focus, grade=grade,
           r0=(1.2 if i % 2 else -1.2), r1=0.0)
        if flash:
            EVENTS.append(dict(type="flash", t=b(bb), dur=0.09, amt=flash, pow=1.5))
        if shutter:
            SFX.append(dict(t=b(bb), name="shutter", db=-17 - (i % 2) * 2))
    return b0 + len(pids) * step


def strips(t_start, n=4, dur=0.26, stagger=0.045):
    """Mask for a 4-strip slam wipe (alternating directions)."""
    def mask(t, bw, bh):
        m = np.zeros((bh, bw), np.float32)
        sw = bw // n + 1
        for i in range(n):
            k = ease_out_expo(clamp((t - t_start - i * stagger) / dur))
            hh = int(bh * k)
            if hh <= 0:
                continue
            x0 = i * sw
            if i % 2 == 0:
                m[:hh, x0:x0 + sw] = 1
            else:
                m[bh - hh:, x0:x0 + sw] = 1
        return m
    return mask


def slam(pid, b0, b1, focus=(0.5, 0.45), grade="vivid", rot=1.5, **kw):
    """Kinetic photo: slams in from 1.28x with expo ease and a small rotation settle."""
    return ph(pid, b0, b1, z0=1.28, z1=1.04, focus=focus, grade=grade, ease="expo", r0=rot, r1=0.0, **kw)


def label(b0, b1, text, x=W / 2, y=380, size=22, align="center", opacity=0.78):
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.25), clamp((t1 - t) / 0.2))
        T.draw_text(frame, text, LBL, size, x, y, opacity=a * opacity, tracking=0.0, align=align, shadow=0.4)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))


def chrome(shot, b0, b1, darken=0.0, **kw):
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        return layers.chrome(frame, shot, t, t0, t1, darken=darken, **kw)
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))


def chapter(num, shot, b0, b1, kr_line=None, darken=0.6):
    """Chrome chapter title + index above + Korean line below, spaced from the real chrome bbox."""
    chrome(shot, b0, b1, darken=darken, reveal="focus", exit="blur", exit_len=0.3)
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        rgb, a_, x0, y0 = layers.rgba(shot)
        top, bot = y0 + 40, y0 + a_.shape[0] - 40
        a = min(clamp((t - t0 - 0.25) / 0.3), clamp((t1 - t - 0.15) / 0.2))
        T.draw_text(frame, num, LBL, 26, W / 2, top - 46, opacity=a * 0.8, tracking=0.0, shadow=0.4)
        ov = gfx.Overlay()
        ln = 40 * ease_out_expo((t - t0 - 0.2) / 0.5)
        ov.line((W / 2 - ln, top - 22), (W / 2 + ln, top - 22), 1)
        frame = ov.composite(frame, WHITE, 0.6 * a)
        if kr_line:
            a2 = min(clamp((t - t0 - 0.5) / 0.35), clamp((t1 - t - 0.15) / 0.2))
            T.draw_text(frame, kr_line, KR, 38, W / 2, bot + 58 + (1 - ease_out_cubic(a2)) * 8, opacity=a2,
                        tracking=KR_TRACK, shadow=0.5, color=(0.95, 0.95, 0.97))
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))
    SFX.append(dict(t=t0, name="hit_metal", db=-10, duck=-3, duck_len=0.5))
    SFX.append(dict(t=t0 + 0.35, name="shimmer", db=-20))


def loc_tag(b0, b1, place, coords):
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.3), clamp((t1 - t) / 0.25))
        x = 96
        ov = gfx.Overlay()
        ln = 70 * ease_out_expo((t - t0) / 0.5)
        ov.line((x, H - 196), (x + ln, H - 196), 1)
        frame = ov.composite(frame, WHITE, 0.8 * a)
        T.draw_text(frame, place.upper(), "anton", 54, x, H - 160, align="left", opacity=a, tracking=0.0, shadow=0.5)
        n = int(len(coords) * clamp((t - t0 - 0.25) / 0.6))
        T.draw_text(frame, coords[:n], "mono", 16, x, H - 122, align="left", opacity=a * 0.7, tracking=0.0, shadow=0.4)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))
    for i in range(8):
        SFX.append(dict(t=t0 + 0.25 + i * 0.075, name="tick", db=-26, kw=dict(freq=2600 + 120 * i)))


def route(b0, b1, a_code="ICN", b_code="SIN", a_city="Seoul", b_city="Singapore"):
    """Flight path graphic: arc draws between two airports with a travelling dot."""
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.3), clamp((t1 - t) / 0.3))
        p = ease_in_out(clamp((t - t0 - 0.2) / (t1 - t0 - 0.6)))
        x0, x1, y0 = W * 0.5 - 330, W * 0.5 + 330, H * 0.5 + 40
        pts = []
        n = 80
        for i in range(n + 1):
            u = i / n
            if u > p:
                break
            pts.append((x0 + (x1 - x0) * u, y0 - math.sin(u * math.pi) * 150))
        frame = scrim(frame, 0.35 * a)
        frame *= 1 - 0.35 * a
        ov = gfx.Overlay()
        if len(pts) > 1:
            ov.poly(pts, 2)
        ov.circle((x0, y0), 5, -1)
        if p > 0.98:
            ov.circle((x1, y0), 5, -1)
        frame = ov.composite(frame, WHITE, 0.9 * a, glow=0.6)
        if pts:
            gfx.sparkle(frame, pts[-1][0], pts[-1][1], 26, a * 0.9, streak=False)
        for (xx, code, city) in ((x0, a_code, a_city), (x1, b_code, b_city)):
            T.draw_text(frame, code, "anton", 88, xx, y0 + 76, opacity=a, tracking=0.0, shadow=0.5)
            T.draw_text(frame, city, LBL, 20, xx, y0 + 120, opacity=a * 0.75, tracking=0.0)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))
    SFX.append(dict(t=t0 + 0.2, name="whoosh", db=-14, kw=dict(dur=1.4, f0=150, f1=2600, seed=5, peak=0.8)))


def market_line(b0, b1, y=H / 2, amp=90, color=LILAC):
    """Heartbeat line that doubles as a market pulse (no numbers, no fake data)."""
    t0, t1 = b(b0), b(b1)
    beats = [b(i) for i in range(int(b0) - 8, int(b1) + 8)]

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.5), clamp((t1 - t) / 0.4))
        ov = gfx.Overlay()
        gfx.ecg(ov, t, y, amp, beats, th=2)
        return ov.composite(frame, color, a, glow=0.9)
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))


def hud(b0, b1, tag="", color=WHITE, inset=64):
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.4), clamp((t1 - t) / 0.3))
        ov = gfx.Overlay()
        gfx.hud_corners(ov, (t - t0) / 0.6, inset=inset, arm=36, th=1)
        frame = ov.composite(frame, color, 0.55 * a)
        tc = t
        s = f"{int(tc // 60):02d}:{int(tc % 60):02d}:{int((tc * FPS) % FPS):02d}"
        T.draw_text(frame, "REC  " + s, "mono", 15, W - inset - 6, inset + 26,
                    align="right", opacity=0.6 * a, tracking=0.0, shadow=0.3)
        if int(t * 2) % 2 == 0:
            gfx.sparkle(frame, (W - inset - 6) - 172, (176 if t < b(64) else 90) - 1, 9, 0.8 * a,
                        color=(1, 0.25, 0.3), streak=False)
        if tag:
            T.draw_text(frame, tag, "mono", 15, inset + 6, inset + 26, align="left",
                        opacity=0.6 * a, tracking=0.0, shadow=0.3)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))


def crt_off(bb, dur=0.24):
    """Picture collapses to a line then a dot (screen switching off)."""
    import cv2
    t1 = b(bb)
    t0 = t1 - dur

    def fn(frame, t, k, fi):
        q = ease_in_out(k)
        sy = max(0.004, 1 - q * 1.1)
        sx = 1 - max(0, (q - 0.7) / 0.3) * 0.98
        m = np.array([[sx, 0, W / 2 * (1 - sx)], [0, sy, H / 2 * (1 - sy)]], np.float32)
        out = cv2.warpAffine(frame, m, (W, H), borderMode=cv2.BORDER_CONSTANT)
        return fx.flash(out, 0.35 * q)
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))
    SFX.append(dict(t=t0, name="glitch", db=-16, kw=dict(dur=0.2, seed=91)))




# ============================================================================= v4 motion-graphics kit
TITLE = "anton"


def knockout(word, src_clip, b0, b_zoom, zoom_beats=0.75, index=None, kr=None, en=None, size=None, outline=True):
    """Huge condensed word with the next shot playing INSIDE the letters, then a zoom-through
    into one letter that reveals the full shot. `src_clip` is a clip dict already in CLIPS."""
    t0, tz = b(b0), b(b_zoom)
    tz1 = b(b_zoom + zoom_beats)
    size = size or T.fit_size(word, TITLE, 1720, 640)
    cy = H / 2 + 10
    state = {}

    def geom():
        if "ax" not in state:
            m = T.text_mask(word, TITLE, size, W / 2, cy)
            state["m"] = m
            state["ax"], state["ay"] = T.anchor_in(m, W / 2, H / 2)
        return state["m"], state["ax"], state["ay"]

    def mask(t, bw, bh):
        if t >= tz1:
            return None
        m, ax, ay = geom()
        lt = t - t0
        if t < tz:
            s = 1.0 + 0.16 * (1 - ease_out_expo(lt / 0.3)) + 0.035 * prog(t, t0, tz)
        else:
            k = (t - tz) / (tz1 - tz)
            s = 1.035 * math.exp(math.log(60.0) * k ** 2.2)
        mm = T.zoom_mask(m, s, ax, ay)
        state["cur"] = mm
        return mm
    src_clip["mask"] = mask
    src_clip["t0"] = min(src_clip["t0"], t0)

    def deco(frame, t, k, fi):
        if t >= tz1:
            return frame
        m, ax, ay = geom()
        a = clamp((t - t0) / 0.12) * (1 - clamp((t - tz) / 0.18))
        cur = state.get("cur")
        if cur is not None:
            # crisp white edge around the letters + a little lift inside so dark footage still reads
            import cv2
            edge = np.clip(cv2.dilate(cur, np.ones((5, 5), np.uint8)) - cur, 0, 1)
            fx.add_at(frame, edge[..., None] * np.float32(0.85), 0, 0, 1.0)
            fx.add_at(frame, cur[..., None] * np.float32(0.07), 0, 0, 1.0)
        if outline and a > 0:
            # stroke echo of the word above and below, drifting apart
            d = 0.62 * size + 30 * prog(t, t0, tz)
            for sgn in (-1, 1):
                T.draw_text(frame, word, TITLE, size, W / 2, cy + sgn * d, outline=2, opacity=0.22 * a,
                            shadow=0.0, color=(1, 1, 1))
        if index and a > 0:
            T.draw_text(frame, index, LBL, 20, 120, 112, align="left", opacity=0.85 * a, tracking=0.0, shadow=0.3)
            ov = gfx.Overlay()
            ov.line((120, 136), (120 + 160 * ease_out_expo((t - t0) / 0.5), 136), 1)
            frame = ov.composite(frame, WHITE, 0.6 * a)
        if kr and a > 0:
            a2 = a * clamp((t - t0 - 0.15) / 0.25)
            T.draw_text(frame, kr, KR, 40, W - 120, H - 150, align="right", opacity=a2, tracking=KR_TRACK, shadow=0.6)
            if en:
                T.draw_text(frame, en.upper(), EN_FONT, 17, W - 120, H - 108, align="right", opacity=a2 * 0.8,
                            tracking=0.0, shadow=0.5)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=tz1, fn=deco))
    SFX.append(dict(t=t0, name="impact", db=-8, duck=-4, duck_len=0.5))
    SFX.append(dict(t=t0, name="hit_metal", db=-12))
    SFX.append(dict(t=tz - 0.05, name="whoosh", db=-9, kw=dict(dur=0.5, f0=180, f1=6000, seed=int(b0) % 50)))
    EVENTS.append(dict(type="shake", t=t0, dur=0.3, amp=12))
    EVENTS.append(dict(type="flash", t=t0, dur=0.14, amt=0.5))
    EVENTS.append(dict(type="zblur", t=tz1, pre=(tz1 - tz) * 0.6, dur=0.12, amt=0.16))


def bands(b0, b1, specs, gap=8, stagger=0.5, lines=True):
    """Stack of horizontal cinematic bands, each playing its own clip, sliding in from alternating sides.
    specs: list of dict(src=..., in=..., speed=..., focus=...)."""
    n = len(specs)
    bh = (H - gap * (n - 1)) // n
    for i, sp in enumerate(specs):
        y = i * (bh + gap)
        ti = b(b0 + i * stagger)
        mode = "lr" if i % 2 == 0 else "rl"

        def mk(t, bw, bh_, ti=ti, mode=mode):
            return gfx.panel_mask(bw, bh_, (t - ti) / 0.4, mode)
        c = dict(src=sp["src"], t0=ti, t1=b(b1), box=(0, y, W, bh), mask=mk, layer=2, ease="out",
                 z0=sp.get("z0", 1.08), z1=sp.get("z1", 1.0), focus=sp.get("focus", (0.5, 0.5)),
                 grade=sp.get("grade", "beauty"), speed=sp.get("speed", 1.0), fit="cover")
        c["in"] = sp.get("in", 0.0)
        if SOURCES.get(sp["src"], {}).get("kind") == "video":
            c["fx"] = [dict(type="beauty", amt=BEAUTY)]
        CLIPS.append(c)
        SFX.append(dict(t=ti, name="whoosh", db=-15, kw=dict(dur=0.4, seed=70 + i)))
    if lines:
        def ln(frame, t, k, fi):
            ov = gfx.Overlay()
            for i in range(1, n):
                yy = i * (bh + gap) - gap / 2
                e = ease_out_expo((t - b(b0 + i * stagger)) / 0.5)
                if e > 0:
                    ov.line((W / 2 - W / 2 * e, yy), (W / 2 + W / 2 * e, yy), 1)
            return ov.composite(frame, WHITE, 0.55)
        EVENTS.append(dict(type="draw", t0=b(b0), t1=b(b1), fn=ln))


def iris(t_start, dur=0.35, cx=W / 2, cy=H / 2):
    """Circular reveal mask (grows from a point) for a clip."""
    R = math.hypot(W, H)

    def mask(t, bw, bh):
        k = ease_out_expo(clamp((t - t_start) / dur))
        if k >= 1:
            return None
        yy, xx = np.ogrid[0:bh, 0:bw]
        r = R * k
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        return np.clip((r - d) / 3.0, 0, 1).astype(np.float32)
    return mask


def slash(t_start, dur=0.3, angle=-18):
    """Diagonal wipe mask."""
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def mask(t, bw, bh):
        k = ease_out_expo(clamp((t - t_start) / dur))
        if k >= 1:
            return None
        yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
        u = (xx / bw - 0.5) * ca + (yy / bh - 0.5) * sa
        edge = -0.9 + 1.8 * k
        return np.clip((edge - u) * 400, 0, 1).astype(np.float32)
    return mask


def word_slam(b0, b1, text, size=200, y=H / 2, color=(1, 1, 1), font=None, echo=True, exit_blur=True):
    """Per-letter slam of a big word + outline echoes."""
    t0, t1 = b(b0), b(b1)
    font = font or TITLE

    def fn(frame, t, k, fi):
        lt = t - t0
        a = clamp((t1 - t) / 0.12)
        T.draw_text(frame, text, font, size, W / 2, y, anim=T.a_slam(clamp(lt / 0.45)), opacity=a, color=color,
                    tracking=0.0, shadow=0.5, mblur=max(0, 30 * (1 - lt / 0.2)))
        if echo:
            for sgn in (-1, 1):
                T.draw_text(frame, text, font, size, W / 2, y + sgn * (size * 0.9 + 20 * lt), outline=2,
                            opacity=0.18 * a * clamp(lt / 0.2), shadow=0.0)
        return frame
    EVENTS.append(dict(type="draw", t0=t0, t1=t1, fn=fn))
    EVENTS.append(dict(type="shake", t=t0, dur=0.25, amp=9))
    SFX.append(dict(t=t0, name="impact", db=-11, kw=dict(size=0.8)))
