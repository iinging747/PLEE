"""PIXIE channel teaser - edit decision list (EDL), graphics and sound design.

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
    if key.startswith("eye"):
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

KR = "kr_l"          # caption face (swap: assets/fonts/licensed/kr.otf -> Sandoll)
KR_TRACK = -0.045
LBL = "jost_l"


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


EN_FONT = "garamond_li"


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
            T.draw_text(frame, en, EN_FONT, int(size * 0.72), W / 2, yy + size * 1.12 + rise, color=(0.86, 0.86, 0.9),
                        opacity=a2 * 0.85, tracking=-0.015, shadow=0.5)
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
        T.draw_text(frame, place, "jost", 34, x, H - 160, align="left", opacity=a, tracking=-0.01, shadow=0.5)
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
            T.draw_text(frame, code, "didone", 64, xx, y0 + 70, opacity=a, tracking=-0.03, shadow=0.5)
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


def hud(b0, b1, tag="", color=WHITE):
    t0, t1 = b(b0), b(b1)

    def fn(frame, t, k, fi):
        a = min(clamp((t - t0) / 0.4), clamp((t1 - t) / 0.3))
        ov = gfx.Overlay()
        gfx.hud_corners(ov, (t - t0) / 0.6, inset=150 if t < b(64) else 64, arm=36, th=1)
        frame = ov.composite(frame, color, 0.55 * a)
        tc = t
        s = f"{int(tc // 60):02d}:{int(tc % 60):02d}:{int((tc * FPS) % FPS):02d}"
        T.draw_text(frame, "REC  " + s, "mono", 15, W - 160 if t < b(64) else W - 70, 150 + 26 if t < b(64) else 90,
                    align="right", opacity=0.6 * a, tracking=0.0, shadow=0.3)
        if int(t * 2) % 2 == 0:
            gfx.sparkle(frame, (W - 160 if t < b(64) else W - 70) - 172, (176 if t < b(64) else 90) - 1, 9, 0.8 * a,
                        color=(1, 0.25, 0.3), streak=False)
        if tag:
            T.draw_text(frame, tag, "mono", 15, 160 if t < b(64) else 70, 176 if t < b(64) else 90, align="left",
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


# ============================================================================= EDIT

# ---------------------------------------------------------------- A. COLD OPEN (beats 0-32)
# slit opens on the first eye; the eye clips are panoramic crops, so they live inside a letterbox slit
vid("eye2", 0, 16, 0.0, speed=0.48, z0=1.0, z1=1.14, grade="noir", exp=-0.15, fade_in=1.6, focus=(0.5, 0.5))
caption(8, 15, "시장은 늘, 감정을 시험한다", en="The market always tests your emotions.", y=846, use_scrim=False)
SFX.append(dict(t=b(0) + 0.05, name="sub_drop", db=-14))

vid("eye3", 16, 18, 0.95, speed=0.55, z0=1.05, z1=1.12, grade="noir", exp=-0.1)
chrome("cold", 18, 20, reveal="slam", exit="blur", exit_len=0.2, push=0.05)
vid("eye4", 20, 22, 4.15, speed=0.5, z0=1.04, z1=1.12, grade="noir", exp=-0.1)
chrome("calm", 22, 24, reveal="slam", exit="blur", exit_len=0.2, push=0.05)
vid("eye2", 24, 26, 2.3, speed=0.5, z0=1.1, z1=1.2, grade="noir", exp=-0.1)
chrome("calculated", 26, 28.5, reveal="slam", exit="blur", exit_len=0.25, push=0.05)
for bb in (18, 22, 26):
    SFX.append(dict(t=b(bb), name="impact", db=-13, kw=dict(size=0.7)))
    EVENTS.append(dict(type="flash", t=b(bb), dur=0.12, amt=0.3))
    EVENTS.append(dict(type="shake", t=b(bb), dur=0.3, amp=10))
    EVENTS.append(dict(type="rgb", t=b(bb), dur=0.18, px=8))
for bb in (16, 20, 24):
    SFX.append(dict(t=b(bb), name="click_soft", db=-18))
market_line(28.5, 33, amp=70)
caption(29, 32, "감정 대신, 원칙으로", en="Principles over emotions.", y=846, use_scrim=False)

# ---------------------------------------------------------------- B. FIRST WORLD (beats 32-64)
ph("P140", 32, 40, z0=1.18, z1=1.02, focus=(0.42, 0.42), grade="trade", exp=-0.35, fade_in=0.6)
EVENTS.append(dict(type="blurev", t0=b(32), t1=b(34), sigma=24, dir="in"))
hud(32, 64, tag="PIXIE / 01")
cut(40, "glitch")
ph("P130", 40, 42, z0=1.25, z1=1.15, focus=(0.30, 0.45), grade="trade", exp=-0.2)
cut(42, "glitch")
ph("P132", 42, 44, z0=1.0, z1=1.1, focus=(0.5, 0.42), grade="trade", exp=-0.2)
cut(44, "punch")
vid("eye4", 44, 46, 6.0, speed=0.45, z0=1.05, z1=1.1, grade="noir", fit="width")
cut(46, "glitch")
ph("P131", 46, 48, z0=1.12, z1=1.02, focus=(0.4, 0.35), grade="trade", exp=-0.15)
caption(41, 47.5, "매일, 같은 질문", en="Every day, the same question.")
bumps(40, 56, amt=0.018, shake=2.5)
cut(48, "punch")
ph("P128", 48, 49, z0=1.1, z1=1.16, focus=(0.5, 0.55), grade="trade")
ph("P138", 49, 50, z0=1.1, z1=1.16, focus=(0.5, 0.4), grade="trade")
cut(49, "punch", 0.6)
cut(50, "glitch")
ph("P058", 50, 52, z0=1.06, z1=1.0, focus=(0.5, 0.5), grade="neutral", box=(656, 0, 608, H), layer=1,
   mask=lambda t, bw, bh: gfx.panel_mask(bw, bh, (t - b(50)) / 0.3, "up"))  # the PIXIE avatar, vertical card
SFX.append(dict(t=b(50), name="shutter", db=-16))
cut(52, "flash", 0.5)
ph("P129", 52, 54, z0=1.15, z1=1.05, focus=(0.42, 0.40), grade="trade", exp=-0.05)  # Pixie, masked
cut(54, "punch")
ph("P139", 54, 55, z0=1.2, z1=1.25, focus=(0.5, 0.36), grade="trade")
ph("P132", 55, 56, z0=1.35, z1=1.4, focus=(0.55, 0.3), grade="trade")
cut(55, "punch", 0.6)
cut(56, "glitch")
# accelerate: photo burst on 8ths
acc = ["P130", "P129", "P141", "P131", "P126", "P139", "P128", "P142"]
burst(56, acc, step=0.5, grade="trade", flash=0.35)
bumps(56, 63, amt=0.03, shake=4)
EVENTS.append(dict(type="strobe", t0=b(60), t1=b(63), period=b(1) - b(0.5), amt=0.18))
SFX.append(dict(t=b(64), name="riser", align="end", db=-9, kw=dict(dur=3.6)))
EVENTS.append(dict(type="black", t0=b(63), t1=b(64)))
label(63, 64, "ENTER", y=H / 2, size=20, opacity=0.9)
SFX.append(dict(t=b(63.5), name="click_soft", db=-10))

# ---------------------------------------------------------------- C. 01 TRADING (beats 64-80)
cut(64, "flash", 1.2)
ph("P141", 64, 68, z0=1.08, z1=1.0, focus=(0.5, 0.4), grade="trade", exp=-0.6)
EVENTS.append(dict(type="blurev", t0=b(64), t1=b(68), sigma=14, dir="out"))
chapter("01", "ch_trading", 64, 68, "판단은 빠르게, 감정은 조용하게", darken=0.65)
seq = [("P139", (0.5, 0.36)), ("P131", (0.45, 0.35)), (None, None), ("P132", (0.52, 0.4)), ("P138", (0.5, 0.42)),
       ("P130", (0.62, 0.45))]
for i, (pid, foc) in enumerate(seq):
    bb = 68 + i * 2
    if pid is None:
        vid("eye3", bb, bb + 2, 2.2, speed=0.4, z0=1.0, z1=1.08, grade="noir", fit="width")
    else:
        slam(pid, bb, bb + 2, focus=foc, grade="trade", exp=-0.1, rot=(1.5 if i % 2 else -1.5))
    cut(bb, "punch" if i % 2 else "whip")
bumps(68, 80, amt=0.025, shake=3.5)
crt_off(80)

# ---------------------------------------------------------------- D. 02 LIFESTYLE (beats 80-112)
ph("P196", 80, 84, z0=1.12, z1=1.0, focus=(0.5, 0.5), grade="warm", exp=-0.45)
EVENTS.append(dict(type="blurev", t0=b(80), t1=b(84), sigma=16, dir="out"))
chapter("02", "ch_lifestyle", 80, 84, "같은 손, 다른 리듬", darken=0.55)
home = [("P198", (0.5, 0.52)), ("P195", (0.5, 0.5)), ("P193", (0.45, 0.45)), ("P197", (0.5, 0.48)),
        ("P196", (0.52, 0.47)), ("P194", (0.45, 0.38))]
for i, (pid, foc) in enumerate(home):
    bb = 84 + i * 2
    ph(pid, bb, bb + 2, z0=1.0 if i % 2 else 1.14, z1=1.14 if i % 2 else 1.02, focus=foc, grade="warm")
    cut(bb, "whip" if i % 2 == 0 else "punch", 0.8)
EVENTS.append(dict(type="leak", t0=b(84), t1=b(96), colors=[CHAMPAGNE, (0.9, 0.55, 0.45)], strength=0.22, seed=4))
# fine dining
cut(96, "zoom")
vid("V04", 96, 99, 0.6, speed=1.0, z0=1.05, z1=1.15, grade="champagne", audio=0.5, mask=strips(b(96)), layer=1)
CLIPS.append(dict(src="P194", t0=b(96), t1=b(96) + 0.4, z0=1.2, z1=1.24, focus=(0.45, 0.38), grade="warm", ease="out"))
loc_tag(96.5, 102, "Saint Pierre", "FINE DINING  ·  SINGAPORE")
vid("V02", 99, 101, 1.2, speed=1.0, z0=1.0, z1=1.1, grade="champagne")
cut(99, "punch", 0.7)
ph("P092", 101, 103, z0=1.15, z1=1.02, focus=(0.5, 0.55), grade="champagne")
cut(101, "whip", 0.8)
vid("V05", 103, 105, 1.5, speed=1.0, z0=1.0, z1=1.08, grade="champagne", audio=0.5)
cut(103, "punch", 0.7)
ph("P096", 105, 107, z0=1.1, z1=1.0, focus=(0.5, 0.5), grade="champagne")
cut(105, "whip", 0.8)
caption(103, 109.5, "좋은 것을, 알아보는 사람", en="An eye for the finer things.")
ph("P098", 107, 109, z0=1.0, z1=1.12, focus=(0.5, 0.5), grade="champagne")
cut(107, "punch", 0.7)
ph("P086", 109, 112, z0=1.12, z1=1.0, focus=(0.5, 0.45), grade="night")
cut(109, "zoom", 0.7)
EVENTS.append(dict(type="sweep", t0=b(97), t1=b(98.5), strength=0.35, width=0.25))
EVENTS.append(dict(type="sweep", t0=b(105), t1=b(106.5), strength=0.35, width=0.25))

bumps(84, 96, amt=0.012, shake=0, every=2.0)
bumps(96, 112, amt=0.014, shake=0, every=2.0)

# ---------------------------------------------------------------- D2. NIGHT LUXURY build (beats 112-128)
cut(112, "flash", 0.6)
tri(112, 116, ["P123", "P125", "P124"], stagger=0.5, grade="night")
tri(116, 120, ["P090", "P188", "P189"], stagger=0.5, grade="night")
cut(116, "punch", 0.6, sfx=False)
ph("P029", 120, 121, z0=1.15, z1=1.2, focus=(0.4, 0.4), grade="champagne")
ph("P121", 121, 122, z0=1.1, z1=1.16, focus=(0.5, 0.4), grade="night")
ph("P183", 122, 123, z0=1.1, z1=1.16, focus=(0.5, 0.45), grade="night")
ph("P030", 123, 124, z0=1.15, z1=1.2, focus=(0.5, 0.45), grade="night")
for bb in (120, 121, 122, 123):
    cut(bb, "punch", 0.7)
burst(124, ["P122", "P184", "P125", "P189", "P090", "P123", "P188", "P185"], step=0.5, grade="night", flash=0.4)
bumps(112, 127.5, amt=0.03, shake=4)
SFX.append(dict(t=b(128), name="riser", align="end", db=-11, kw=dict(dur=2.6, seed=21)))
cut(128, "blink")

# ---------------------------------------------------------------- E. 03 BEAUTY (beats 128-160)
cut(128, "soft", 1.2)
vid("eye3", 128, 136, 0.7, speed=0.32, z0=1.0, z1=1.18, grade="beauty", exp=0.05)
EVENTS.append(dict(type="bloom", t0=b(128), t1=b(144), strength=0.45, thr=0.68))
EVENTS.append(dict(type="particles", t0=b(128), t1=b(160), n=46, seed=8, color=(1, 0.92, 0.85), strength=0.55, speed=10))
EVENTS.append(dict(type="leak", t0=b(128), t1=b(144), colors=[LILAC, CHAMPAGNE], strength=0.25, seed=9, speed=0.6))
chapter("03", "ch_beauty", 132, 136, "차트 밖의 나는, 조금 더 부드럽다", darken=0.5)
beauty = [("P022", (0.42, 0.62)), ("P074", (0.5, 0.45)), ("P098", (0.5, 0.5)), (None, None)]
for i, (pid, foc) in enumerate(beauty):
    bb = 136 + i * 2
    if pid is None:
        vid("eye2", bb, bb + 2, 2.0, speed=0.35, z0=1.08, z1=1.16, grade="beauty", fit="width")
    else:
        ph(pid, bb, bb + 2, z0=1.04, z1=1.12, focus=foc, grade="beauty", fade_in=0.3)
SFX.append(dict(t=b(136), name="shimmer", db=-20, kw=dict(seed=44)))
# heading out
cut(144, "flash", 0.6)
ph("P170", 144, 148, z0=1.0, z1=1.14, focus=(0.5, 0.35), grade="night")
ph("P172", 148, 150, z0=1.12, z1=1.04, focus=(0.5, 0.4), grade="night")
cut(148, "whip", 0.7)
ph("P174", 150, 152, z0=1.0, z1=1.1, focus=(0.5, 0.35), grade="night")
cut(150, "punch", 0.6)
ph("P016", 152, 156, z0=1.0, z1=1.3, focus=(0.55, 0.62), grade="champagne", exp=0.05)
cut(152, "punch", 0.6)
caption(152.5, 159.5, "그리고, 더 넓은 세계로", en="And into a bigger world.")
cut(156, "zoom", 1.2)
ph("P192", 156, 160, z0=1.15, z1=1.0, focus=(0.5, 0.35), grade="vivid")

# ---------------------------------------------------------------- F. 04 TRAVEL (beats 160-192)
cut(160, "flash", 1.0)
ph("P192", 160, 164, z0=1.0, z1=1.06, focus=(0.5, 0.3), grade="vivid", exp=-0.4)
chapter("04", "ch_travel", 160, 164, None, darken=0.45)
route(164, 168)
ph("P001", 164, 168, z0=1.08, z1=1.0, focus=(0.5, 0.42), grade="vivid", exp=-0.1)
travel = [("P004", (0.5, 0.45)), ("P010", (0.5, 0.45)), ("P019", (0.45, 0.5)), ("P023", (0.5, 0.45))]
for i, (pid, foc) in enumerate(travel):
    bb = 168 + i * 1.5 if False else 168 + i * 2
    ph(pid, bb, bb + 2, z0=1.12 if i % 2 else 1.0, z1=1.0 if i % 2 else 1.12, focus=foc, grade="vivid")
    cut(bb, "whip" if i % 2 == 0 else "punch", 0.8)
caption(169, 175.5, "트레이딩만 하는 줄 알았지?", en="Thought I only traded?")
bumps(164, 176, amt=0.016, shake=0, every=2.0)
# Singapore
cut(176, "flash", 0.9)
ph("P099", 176, 180, z0=1.0, z1=1.1, focus=(0.5, 0.45), grade="night", mask=strips(b(176)), layer=1)
CLIPS.append(dict(src="P023", t0=b(176), t1=b(176) + 0.4, z0=1.16, z1=1.2, focus=(0.5, 0.45), grade="vivid", ease="out"))
loc_tag(176.5, 181, "Singapore", "MARINA BAY  ·  1.2834° N  103.8607° E")
chrome("world", 177, 180.5, darken=0.35, reveal="focus", exit="blur", cy=430)
SFX.append(dict(t=b(177), name="shimmer", db=-19))
slam("P119", 180, 182, focus=(0.5, 0.45), grade="night")
cut(180, "punch")
slam("P143", 182, 184, focus=(0.5, 0.45), grade="vivid")
cut(182, "whip")
slam("P127", 184, 186, focus=(0.42, 0.45), grade="stage")
loc_tag(184.3, 189.5, "TOKEN2049", "SINGAPORE  ·  2026")
cut(184, "zoom")
slam("P141", 186, 188, focus=(0.5, 0.42), grade="stage")
cut(186, "punch")
slam("P129", 188, 190, focus=(0.42, 0.42), grade="stage")
cut(188, "punch")
slam("P142", 190, 192, focus=(0.45, 0.45), grade="stage")
cut(190, "whip")

bumps(176, 192, amt=0.025, shake=3.5)

# ---------------------------------------------------------------- F2. NIGHT & PARTY (beats 192-208)
cut(192, "flash", 0.8)
ph("P147", 192, 194, z0=1.0, z1=1.08, focus=(0.5, 0.45), grade="stage", mask=strips(b(192)), layer=1)
CLIPS.append(dict(src="P142", t0=b(192), t1=b(192) + 0.4, z0=1.15, z1=1.2, focus=(0.45, 0.45), grade="stage", ease="out"))
tri(194, 198, ["P146", "P152", "P155"], stagger=0.5, grade="stage")
ph("P153", 198, 200, z0=1.08, z1=1.0, focus=(0.5, 0.5), grade="stage")
cut(198, "punch")
tri(200, 204, ["P169", "P171", "P173"], stagger=0.5, grade="night")
burst(204, ["P102", "P164", "P151", "P119", "P153", "P146", "P184", "P147"], step=0.5, grade="stage", flash=0.4)
bumps(192, 207.5, amt=0.03, shake=4)
SFX.append(dict(t=b(208), name="riser", align="end", db=-9, kw=dict(dur=3.6, seed=33)))

# ---------------------------------------------------------------- G. CLIMAX (beats 208-224)
pool = [("eye4", 4.6), "P196", "P147", "P099", "P141", ("eye3", 2.0), "P170", "P123", "P029", "P192",
        "P146", "P129", ("V02", 3.0), "P098", "P119", "P001", "P019", ("eye2", 2.6), "P195", "P127",
        "P147", "P188", "P142", "P174", "P090", "P139", ("V05", 3.5), "P143", "P153", "P196", "P058", "P016"]
words = {208: "ch_trading", 210: "ch_lifestyle", 212: "ch_beauty", 214: "ch_travel"}
pi = 0
bb = 208.0
while bb < 220.0 - 1e-6:
    step = 1.0 if bb < 212 else (0.5 if bb < 216 else 0.25)
    item = pool[pi % len(pool)]
    pi += 1
    if isinstance(item, tuple):
        vid(item[0], bb, bb + step, item[1], speed=0.6, z0=1.1, z1=1.18, grade="neutral",
            fit=SOURCES.get(item[0], {}).get("fit", "cover"))
    else:
        ph(item, bb, bb + step, z0=1.15, z1=1.22, focus=(0.5, 0.45), grade="vivid",
           r0=(1.0 if pi % 2 else -1.0), r1=0.0, step=(2.0 / FPS if step < 1 else None))
    cut(bb, "punch", 0.6, sfx=(step == 1.0))
    if step <= 0.25:
        EVENTS.append(dict(type="flash", t=b(bb), dur=0.07, amt=0.35, pow=1.5))
        SFX.append(dict(t=b(bb), name="shutter", db=-19))
    bb += step
for wb, shot in words.items():
    chrome(shot, wb, wb + 1.6, darken=0.55, reveal="slam", exit="fade", exit_len=0.15, push=0.06,
           sweep=(0.0, 1.0), sweep_strength=0.6)
    SFX.append(dict(t=b(wb), name="hit_metal", db=-15))
EVENTS.append(dict(type="strobe", t0=b(216), t1=b(220), period=b(1) - b(0.5), amt=0.16))
bumps(208, 220, amt=0.035, shake=5)
EVENTS.append(dict(type="black", t0=b(220), t1=b(224)))
chrome("more", 220, 224, reveal="focus", exit="cut", sweep=(0.1, 0.9))
SFX.append(dict(t=b(220), name="impact", db=-8, duck=-5, duck_len=1.0))
EVENTS.append(dict(type="particles", t0=b(220), t1=b(224), n=30, seed=12, color=(0.9, 0.85, 1.0), strength=0.5, speed=8))

# ---------------------------------------------------------------- H. EYE / SILENCE / LOGO (beats 224-)
vid("eye4", 224, 227.5, 3.2, speed=0.3, z0=1.0, z1=1.32, grade="noir", exp=-0.05, focus=(0.5, 0.48))
EVENTS.append(dict(type="flash", t=b(224), dur=0.35, amt=0.7))
EVENTS.append(dict(type="rgb", t=b(224), dur=0.3, px=10))
SFX.append(dict(t=b(224), name="impact", db=-7))
CUT_T = b(227.5)                          # music cut / hard black
EVENTS.append(dict(type="black", t0=CUT_T, t1=b(240)))
for hb, g in ((CUT_T + 1.45, -15), (CUT_T + 2.9, -13), (CUT_T + 4.05, -11), (CUT_T + 4.95, -9.5)):
    SFX.append(dict(t=hb, name="heartbeat", db=g))
SFX.append(dict(t=b(240), name="reverse_swell", align="end", db=-12))
SFX.append(dict(t=b(240), name="boom_low", db=-6))
LOGO_T0, LOGO_T1 = b(240), b(240) + 2.9
EVENTS.append(dict(type="draw", t0=LOGO_T0, t1=LOGO_T1,
                   fn=lambda f, t, k, fi: layers.chrome(f, "logo", t, LOGO_T0, LOGO_T1, reveal="cut", exit="fade",
                                                        exit_len=0.55, push=0.03, sweep=(0.12, 0.62),
                                                        sweep_strength=0.7, cy=500)))


def _logo_sub(frame, t, k, fi):
    a = min(clamp((t - LOGO_T0 - 0.35) / 0.5), clamp((LOGO_T1 - t) / 0.5))
    T.draw_text(frame, "More than a trader", "garamond_li", 40, W / 2, 742, opacity=a * 0.85, tracking=-0.02,
                color=(0.9, 0.9, 0.93), shadow=0.0)
    return frame


EVENTS.append(dict(type="draw", t0=LOGO_T0, t1=LOGO_T1, fn=_logo_sub))
LIVE_T0, LIVE_T1 = LOGO_T1 + 0.25, LOGO_T1 + 3.2
EVENTS.append(dict(type="draw", t0=LIVE_T0, t1=LIVE_T1,
                   fn=lambda f, t, k, fi: layers.chrome(f, "live", t, LIVE_T0, LIVE_T1, reveal="focus", exit="fade",
                                                        exit_len=0.6, push=0.03, sweep=(0.2, 0.8),
                                                        sweep_strength=0.6, cy=545)))


def _live_sub(frame, t, k, fi):
    a = min(clamp((t - LIVE_T0 - 0.2) / 0.5), clamp((LIVE_T1 - t) / 0.6))
    T.draw_text(frame, "FIRST LIVE", LBL, 22, W / 2, 452, opacity=a * 0.8, tracking=0.02)
    if LIVE_DATE:
        T.draw_text(frame, LIVE_DATE, "mono", 22, W / 2, 652, opacity=a * 0.8, tracking=0.0)
    else:
        T.draw_text(frame, "첫 라이브, 곧 공개됩니다", KR, 30, W / 2, 652, opacity=a * 0.75, tracking=KR_TRACK)
    return frame


EVENTS.append(dict(type="draw", t0=LIVE_T0, t1=LIVE_T1, fn=_live_sub))
SFX.append(dict(t=LIVE_T0, name="heartbeat", db=-11))
SFX.append(dict(t=LIVE_T1 + 0.25, name="heartbeat", db=-20))


# ----------------------------------------------------------------------------- voiceover (후시녹음)
# Drop recordings as vo/<id>.wav (48 kHz / 24-bit mono or stereo). Each is placed at `t`, high-passed,
# peak-normalised and the BGM dips under it. Lines double as the on-screen captions. See VO_SCRIPT.md.
VO = [
    dict(id="vo01", t=b(8.3), until=b(15), kr="시장은 늘, 감정을 시험한다", en="The market always tests your emotions."),
    dict(id="vo02", t=b(29.2), until=b(32), kr="감정 대신, 원칙으로", en="Principles over emotions."),
    dict(id="vo03", t=b(41.2), until=b(47.5), kr="매일, 같은 질문", en="Every day, the same question."),
    dict(id="vo04", t=b(64.6), until=b(70), kr="판단은 빠르게, 감정은 조용하게", en="Fast decisions. Quiet emotions."),
    dict(id="vo05", t=b(80.8), until=b(84.5), kr="같은 손, 다른 리듬", en="Same hands, a different rhythm."),
    dict(id="vo06", t=b(103.2), until=b(109.5), kr="좋은 것을, 알아보는 사람", en="An eye for the finer things."),
    dict(id="vo07", t=b(132.8), until=b(140), kr="차트 밖의 나는, 조금 더 부드럽다", en="Off the charts, I'm a little softer."),
    dict(id="vo08", t=b(152.7), until=b(159.5), kr="그리고, 더 넓은 세계로", en="And into a bigger world."),
    dict(id="vo09", t=b(169.2), until=b(175.5), kr="트레이딩만 하는 줄 알았지?", en="Thought I only traded?"),
    dict(id="vo10", t=b(220.4), until=b(224), kr="(영어) More than a trader.", en="More than a trader."),
    dict(id="vo11", t=LIVE_T0 + 0.5, until=LIVE_T1, kr="첫 라이브에서, 만나요", en="See you at the first live."),
]

# ----------------------------------------------------------------------------- global look / audio settings
LETTERBOX = [
    (0.0, 540), (b(0), 540), (b(0) + 2.2, 300), (b(32) - 0.05, 300, "smooth"), (b(32) + 0.6, 136, "snap"),
    (b(64) - 0.02, 136), (b(64) + 0.25, 0, "snap"), (b(128) - 0.02, 0), (b(128) + 1.0, 136), (b(160) - 0.02, 136),
    (b(160) + 0.25, 0, "snap"), (b(224) - 0.02, 0), (b(224) + 0.2, 300, "snap"), (CUT_T, 300), (CUT_T + 0.01, 0),
]
VIGNETTE = 0.3
GRAIN = 0.022

# BGM: keep everything until the final hit, then cut hard on the black (storyboard: music stops dead)
BGM_ENV = [(0, 1.0), (CUT_T - 0.03, 1.0), (CUT_T + 0.06, 0.0), (b(240) - 0.08, 0.0), (b(240) - 0.01, 1.0), (120, 1.0)]
BGM_GAIN_DB = -1.0
SFX_GAIN_DB = 0.0
NAT_GAIN_DB = -6.0
LUFS = -14.0

# nothing from before the hard cut may ring into the silence
for _e in SFX:
    if _e["t"] < CUT_T:
        _e["until"] = CUT_T
