"""PIXIE teaser v4 - 67.5 s tight cut.

BGM is re-edited on phrase boundaries (128 BPM, 16-beat phrases), so the output keeps one beat grid:
b(n) = 0.2504 + n * 0.46875.  Output phrases: 0 cold open | 16 build | 32 DROP trading | 48 lifestyle |
64 beauty (breakdown) | 80 travel (full) | 96 climax | 112 final hit -> silence -> 128 logo.
"""
from kit import *  # noqa: F401,F403  (sources, helpers, CLIPS/EVENTS/SFX)
from kit import b, W, H, FPS, CLIPS, EVENTS, SFX, SOURCES, LILAC, CHAMPAGNE, WHITE, VIOLET

# ---------------------------------------------------------------- BGM edit (src_start, src_end, out_start)
_P = lambda n: 0.2504 + 7.5 * n  # source phrase start
BGM_SEGMENTS = [
    (0.0, _P(1), 0.0),            # dark intro
    (_P(3), _P(6), _P(1)),        # build + riser -> drop -> groove
    (_P(8), _P(9), _P(4)),        # big hit + breakdown (beauty)
    (_P(11), _P(12), _P(5)),      # full energy (travel)
    (_P(13), _P(14) + 1.66, _P(6)),   # climax riser -> final hit (cut while the eye stares)
    (112.25, 120.0, None),           # 0.5 s of the original silence -> logo impact -> tail (placed below)
]
CUT_T = b(115.5)                     # music stops dead on the stare
LOGO_T0 = CUT_T + 2.1                # two heartbeats of silence, then the logo hit
BGM_SEGMENTS[-1] = (112.25, 120.0, LOGO_T0 - 0.5)
DUR_OUT = LOGO_T0 + (120.0 - 112.75)  # ~63.7 s

# ================================================================= A. COLD OPEN (beats 0-16)
vid("eye2", 0, 6, 0.4, speed=0.55, z0=1.0, z1=1.12, grade="noir", exp=-0.1, fade_in=0.5)
caption(2.5, 9.5, "감정은 차갑게. 차트는 정확하게.", en="Cold on emotion. Exact on the chart.", y=842, use_scrim=False, size=40)
SFX.append(dict(t=0.05, name="sub_drop", db=-12))
vid("eye4", 6, 9, 4.2, speed=0.5, z0=1.05, z1=1.14, grade="noir")
vid("eye3", 9, 10.5, 1.3, speed=0.5, z0=1.08, z1=1.14, grade="noir")
vid("eye2", 10.5, 14, 2.4, speed=0.4, z0=1.5, z1=1.8, grade="noir", focus=(0.36, 0.55), step=2.0 / FPS)
for bb in (6, 9, 10.5):
    EVENTS.append(dict(type="flash", t=b(bb), dur=0.08, amt=0.25))
    EVENTS.append(dict(type="shake", t=b(bb), dur=0.22, amp=6))
    SFX.append(dict(t=b(bb), name="click_soft", db=-14))
market_line(14, 16.2, amp=80)
EVENTS.append(dict(type="glitch", t0=b(15.6), t1=b(16), amt=0.8, seed=5))
SFX.append(dict(t=b(15.6), name="glitch", db=-13, kw=dict(dur=0.2, seed=8)))

# ================================================================= B. FIRST WORLD (beats 16-32)
hud(16, 32, tag="PIXIE  /  MARKET", inset=70)
cut(16, "flash", 0.7)
for i, (pid, foc) in enumerate([("P140", (0.42, 0.42)), ("P130", (0.3, 0.45)), ("P132", (0.5, 0.42)), ("P131", (0.4, 0.35))]):
    slam(pid, 16 + i, 17 + i, focus=foc, grade="trade", exp=-0.15, rot=(1.6 if i % 2 else -1.6))
    if i:
        cut(16 + i, "glitch" if i % 2 else "punch")
ph("P058", 20, 22, z0=1.08, z1=1.0, focus=(0.5, 0.5), grade="neutral", box=(656, 0, 608, H), layer=1,
   mask=lambda t, bw, bh: gfx.panel_mask(bw, bh, (t - b(20)) / 0.25, "up"))
SFX.append(dict(t=b(20), name="shutter", db=-13))
cut(22, "flash", 0.5)
slam("P129", 22, 24, focus=(0.42, 0.40), grade="trade", rot=-2.0)
burst(24, ["P139", "P128", "P141", "P126", "P142", "P138", "P130", "P129", "P131", "P140", "P132", "P142"],
      step=0.5, grade="trade", flash=0.35)
bumps(16, 30, amt=0.02, shake=3)
caption(23.5, 30, "흔들리면, 지는 거야.", en="Flinch, and you lose.")
EVENTS.append(dict(type="strobe", t0=b(28), t1=b(30), period=b(1) - b(0.5), amt=0.15))
EVENTS.append(dict(type="black", t0=b(30), t1=b(32)))
label(30.2, 32, "ENTER", y=H / 2, size=22, opacity=0.95)
SFX.append(dict(t=b(31.5), name="click_soft", db=-8))

# ================================================================= C. 01 TRADING (beats 32-48) - DROP
tr = ph("P141", 32, 36, z0=1.12, z1=1.0, focus=(0.5, 0.4), grade="stage", exp=-0.1)
knockout("TRADER", tr, 32, 34.5, outline=True)
seq = [("P139", (0.5, 0.36)), ("P131", (0.45, 0.35)), ("eye3", 2.2), ("P132", (0.52, 0.4)), ("P138", (0.5, 0.42)),
       ("P130", (0.62, 0.45)), ("P140", (0.45, 0.42)), ("P129", (0.42, 0.4)), ("P142", (0.45, 0.45)),
       ("P128", (0.5, 0.5)), ("eye4", 6.0), ("P141", (0.5, 0.35))]
for i, item in enumerate(seq):
    bb = 36 + i
    if isinstance(item[1], float):
        vid(item[0], bb, bb + 1, item[1], speed=0.5, z0=1.0, z1=1.06, grade="noir", fit="width")
    else:
        slam(item[0], bb, bb + 1, focus=item[1], grade="trade", exp=-0.1, rot=(1.5 if i % 2 else -1.5))
    cut(bb, ["whip", "punch", "glitch", "punch"][i % 4], 0.8)
bumps(36, 48, amt=0.028, shake=4)
crt_off(48)

# ================================================================= D. 02 LIFESTYLE (beats 48-64)
slam("P196", 48, 50, focus=(0.5, 0.5), grade="warm", rot=-1.2)
slam("P198", 50, 52, focus=(0.5, 0.52), grade="warm", rot=1.2)
cut(50, "whip", 0.8)
caption(48.6, 55, "근데, 차트만 보고 살진 않아.", en="But I don't live on charts alone.")
dine = [("P194", (0.45, 0.38)), ("P195", (0.5, 0.5)), ("V04", 0.8), ("P193", (0.45, 0.45)), ("P197", (0.5, 0.48)),
        ("V02", 1.5), ("P092", (0.5, 0.55)), ("V05", 1.6)]
for i, item in enumerate(dine):
    bb = 52 + i
    if isinstance(item[1], float):
        vid(item[0], bb, bb + 1, item[1], speed=1.0, z0=1.18, z1=1.06, grade="champagne", ease="expo")
    else:
        slam(item[0], bb, bb + 1, focus=item[1], grade="warm", rot=(1.2 if i % 2 else -1.2))
    cut(bb, "whip" if i % 2 == 0 else "punch", 0.8)
EVENTS.append(dict(type="leak", t0=b(48), t1=b(60), colors=[CHAMPAGNE, (0.9, 0.55, 0.45)], strength=0.2, seed=4))
burst(60, ["P123", "P090", "P188", "P189", "P125", "P121", "P029", "P183"], step=0.5, grade="night", flash=0.4)
bumps(52, 63.5, amt=0.025, shake=3.5)
cut(64, "blink")

# ================================================================= E. 03 BEAUTY (beats 64-80) - breakdown
bt = vid("M2", 64, 68, 2.0, speed=0.5, z0=1.15, z1=1.05, grade="beauty", focus=(0.5, 0.45))
cut(64, "soft", 1.0, sfx=False)
bands(68, 76, [dict(src="M3", **{"in": 3.0}, speed=0.5, focus=(0.5, 0.5)),
               dict(src="M2", **{"in": 6.0}, speed=0.5, focus=(0.5, 0.42)),
               dict(src="M1", **{"in": 2.0}, speed=0.5, focus=(0.5, 0.45))], stagger=0.5)
vid("M3", 76, 80, 6.5, speed=[(0, 1.6), (0.5, 0.3), (1.9, 0.3)], z0=1.0, z1=1.12, grade="beauty",
    fit="width", mask=iris(b(76), 0.4))
caption(68.5, 76, "나를 가꾸는 것도, 투자니까.", en="Taking care of myself is an investment too.", size=46)
EVENTS.append(dict(type="bloom", t0=b(64), t1=b(80), strength=0.4, thr=0.7))
EVENTS.append(dict(type="particles", t0=b(64), t1=b(80), n=40, seed=8, color=(1, 0.92, 0.88), strength=0.5, speed=10))
EVENTS.append(dict(type="leak", t0=b(64), t1=b(80), colors=[LILAC, CHAMPAGNE], strength=0.22, seed=9, speed=0.6))
SFX.append(dict(t=b(68), name="shimmer", db=-18, kw=dict(seed=44)))
SFX.append(dict(t=b(80), name="riser", align="end", db=-12, kw=dict(dur=1.8, seed=27)))

# ================================================================= F. 04 TRAVEL (beats 80-96) - full energy
tv = ph("P192", 80, 83, z0=1.12, z1=1.0, focus=(0.5, 0.35), grade="vivid")
cut(80, "flash", 0.9)
ph("P001", 83, 85, z0=1.1, z1=1.0, focus=(0.5, 0.42), grade="vivid", exp=-0.15, mask=slash(b(83)))
route(83, 85)
world = [("P019", (0.45, 0.5), "vivid"), ("P023", (0.5, 0.45), "vivid"), ("P099", (0.5, 0.45), "night"),
         ("P119", (0.5, 0.45), "night"), ("P127", (0.42, 0.45), "stage"), ("P142", (0.45, 0.45), "stage"),
         ("P147", (0.5, 0.45), "stage")]
for i, (pid, foc, gr) in enumerate(world):
    bb = 85 + i
    slam(pid, bb, bb + 1, focus=foc, grade=gr, rot=(1.4 if i % 2 else -1.4))
    cut(bb, "whip" if i % 2 == 0 else "punch", 0.8)
loc_tag(87, 89.5, "Singapore", "MARINA BAY  ·  1.2834° N  103.8607° E")
tri(92, 94, ["P146", "P152", "P155"], stagger=0.33, grade="stage")
burst(94, ["P153", "P170", "P102", "P151"], step=0.5, grade="night", flash=0.4)
caption(87, 95, "트레이더? 그게 다가 아니야.", en="A trader? That's not all I am.", size=48)
bumps(85, 96, amt=0.03, shake=4)

# ================================================================= G. CLIMAX (beats 96-112)
pool = [("eye4", 4.6), "P196", "P147", "P099", "P141", ("M3", 4.0), "P170", "P123", "P029", "P192",
        "P146", "P129", ("V02", 3.0), "P098", "P119", "P001", "P019", ("M2", 8.0), "P195", "P127",
        "P188", "P142", "P174", "P090", "P139", ("V05", 3.5), "P143", "P153", ("M1", 5.0), "P016", "P130", "P197"]
pi = 0
bb = 96.0
while bb < 108.0 - 1e-6:
    step = 0.5 if bb < 104 else 0.25
    item = pool[pi % len(pool)]
    pi += 1
    if isinstance(item, tuple):
        vid(item[0], bb, bb + step, item[1], speed=0.7, z0=1.12, z1=1.2, grade="vivid",
            fit=SOURCES.get(item[0], {}).get("fit", "cover"))
    else:
        ph(item, bb, bb + step, z0=1.15, z1=1.24, focus=(0.5, 0.45), grade="vivid", r0=(1.0 if pi % 2 else -1.0),
           r1=0.0, step=2.0 / FPS)
    cut(bb, "punch", 0.6, sfx=False)
    if step <= 0.25:
        EVENTS.append(dict(type="flash", t=b(bb), dur=0.07, amt=0.35, pow=1.5))
        SFX.append(dict(t=b(bb), name="shutter", db=-19))
    bb += step


def _dim(f, t, k, fi):
    f *= 0.4
    return f


bumps(96, 108, amt=0.035, shake=5)
EVENTS.append(dict(type="black", t0=b(108), t1=b(112)))
chrome("a_more", 108, 112, reveal="slam", exit="cut", sweep=(0.15, 0.9), sweep_strength=0.7)
EVENTS.append(dict(type="particles", t0=b(108), t1=b(112), n=34, seed=12, color=(0.92, 0.88, 1.0), strength=0.5, speed=8))
SFX.append(dict(t=b(108), name="impact", db=-7, duck=-5, duck_len=0.8))
EVENTS.append(dict(type="shake", t=b(108), dur=0.35, amp=12))

# ================================================================= H. STARE / SILENCE / LOGO (beats 112-)
vid("eye4", 112, 115.5, 3.2, speed=0.3, z0=1.0, z1=1.32, grade="noir", exp=-0.05, focus=(0.5, 0.48))
EVENTS.append(dict(type="flash", t=b(112), dur=0.35, amt=0.7))
EVENTS.append(dict(type="rgb", t=b(112), dur=0.3, px=10))
SFX.append(dict(t=b(112), name="impact", db=-6))
EVENTS.append(dict(type="black", t0=CUT_T, t1=LOGO_T0))
for hb, g in ((CUT_T + 0.45, -13), (CUT_T + 1.35, -10.5)):
    SFX.append(dict(t=hb, name="heartbeat", db=g))
SFX.append(dict(t=LOGO_T0, name="reverse_swell", align="end", db=-13))
SFX.append(dict(t=LOGO_T0, name="boom_low", db=-6))
LOGO_T1 = LOGO_T0 + 2.8
EVENTS.append(dict(type="draw", t0=LOGO_T0, t1=LOGO_T1,
                   fn=lambda f, t, k, fi: layers.chrome(f, "logo", t, LOGO_T0, LOGO_T1, reveal="cut", exit="fade",
                                                        exit_len=0.5, push=0.03, sweep=(0.12, 0.62),
                                                        sweep_strength=0.7, cy=520)))


def _logo_sub(frame, t, k, fi):
    a = min(clamp((t - LOGO_T0 - 0.35) / 0.4), clamp((LOGO_T1 - t) / 0.5))
    T.draw_text(frame, "MORE THAN A TRADER", "unb_l", 20, W / 2, 742, opacity=a * 0.85, tracking=0.02)
    T.draw_text(frame, "TRADING  ·  LIFESTYLE  ·  BEAUTY  ·  TRAVEL", "unb_l", 14, W / 2, 782, opacity=a * 0.55,
                tracking=0.02)
    return frame


EVENTS.append(dict(type="draw", t0=LOGO_T0, t1=LOGO_T1, fn=_logo_sub))
LIVE_T0, LIVE_T1 = LOGO_T1 + 0.15, DUR_OUT - 0.5
EVENTS.append(dict(type="draw", t0=LIVE_T0, t1=LIVE_T1,
                   fn=lambda f, t, k, fi: layers.chrome(f, "a_soon", t, LIVE_T0, LIVE_T1, reveal="slam", exit="fade",
                                                        exit_len=0.6, push=0.03, sweep=(0.2, 0.8),
                                                        sweep_strength=0.6, cy=540)))


def _live_sub(frame, t, k, fi):
    a = min(clamp((t - LIVE_T0 - 0.2) / 0.4), clamp((LIVE_T1 - t) / 0.6))
    T.draw_text(frame, "FIRST LIVE", "unb", 22, W / 2, 420, opacity=a * 0.85, tracking=0.02)
    line = LIVE_DATE if LIVE_DATE else "나는 픽시. 첫 라이브에서 보자."
    T.draw_text(frame, line, KR, 34, W / 2, 672, opacity=a * 0.85, tracking=KR_TRACK)
    return frame


EVENTS.append(dict(type="draw", t0=LIVE_T0, t1=LIVE_T1, fn=_live_sub))
SFX.append(dict(t=LIVE_T0, name="heartbeat", db=-11))
SFX.append(dict(t=LIVE_T0, name="hit_metal", db=-16))

# ---------------------------------------------------------------- voiceover slots (VO_SCRIPT.md)
VO = [
    dict(id="vo01", t=b(2.7), until=b(9.5), kr="감정은 차갑게. 차트는 정확하게.", en="Cold on emotion. Exact on the chart."),
    dict(id="vo02", t=b(23.8), until=b(30), kr="흔들리면, 지는 거야.", en="Flinch, and you lose."),
    dict(id="vo03", t=b(48.8), until=b(55), kr="근데, 차트만 보고 살진 않아.", en="But I don't live on charts alone."),
    dict(id="vo04", t=b(68.8), until=b(76), kr="나를 가꾸는 것도, 투자니까.", en="Taking care of myself is an investment too."),
    dict(id="vo05", t=b(87.2), until=b(95), kr="트레이더? 그게 다가 아니야.", en="A trader? That's not all I am."),
    dict(id="vo06", t=LIVE_T0 + 0.3, until=LIVE_T1, kr="나는 픽시. 첫 라이브에서 보자.", en="I'm Pixie. See you at the first live."),
]

# ---------------------------------------------------------------- look / audio
LETTERBOX = [
    (0.0, 540), (0.2, 540), (1.1, 300), (b(16) - 0.02, 300), (b(16) + 0.18, 0, "snap"),
    (b(112) - 0.02, 0), (b(112) + 0.18, 300, "snap"), (CUT_T, 300), (CUT_T + 0.01, 0),
]
VIGNETTE = 0.28
GRAIN = 0.02
BGM_ENV = [(0, 1.0), (CUT_T - 0.03, 1.0), (CUT_T + 0.04, 0.0), (LOGO_T0 - 0.52, 0.0), (LOGO_T0 - 0.5, 1.0), (DUR_OUT, 1.0)]
BGM_GAIN_DB = -1.0
SFX_GAIN_DB = 0.0
NAT_GAIN_DB = -6.0
LUFS = -14.0
for _e in SFX:
    if _e["t"] < CUT_T:
        _e["until"] = CUT_T
