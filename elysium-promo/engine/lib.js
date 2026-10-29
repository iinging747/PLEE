// Storyboard toolkit shared by the canvas preview and the After Effects generator.
// Scenes are described with a few high-level helpers that compile down to
// primitive layers with explicit keyframes:
//   text | shape | ramp | comp | slot | adjust
// Both back ends (engine/renderer.js and engine/ae-runtime.jsx) play exactly
// these primitives, so the preview MP4 and the AE project stay in sync.
//
// Visual language: bright warm paper, deep-teal type, mint highlighter accents,
// very large soft type (Pretendard), one message per shot, focus/mask reveals.

export const W = 1920;
export const H = 1080;
export const FPS = 30;
export const BEAT = 0.5; // 120 BPM: commercial shot lengths are multiples of a beat

// Palette: Hyperliquid mint + Kinetiq brand tokens (kinetiq.xyz/brand), light theme.
export const C = {
  paper: '#F7F6F2', // close to Kinetiq warm-50 #F8F7F4
  paper2: '#FFFFFF',
  paperEdge: '#E9E7E0',
  ink: '#0E2A30', // deep teal, close to Kinetiq brand-900 #04181C
  ink2: '#4E656A',
  ink3: '#859599',
  accent: '#0E9C84', // readable teal for coloured words on paper
  mint: '#97FCE4', // Hyperliquid mint: fills, highlighter, glow
  mint2: '#5FD9BF',
  sky: '#34B7DD', // Kinetiq brand-400
  kblue: '#2D7388', // Kinetiq brand-500
  amber: '#D9821F',
  white: '#FFFFFF',
  black: '#000000',
};

// Segment eases as [outInfluence, inInfluence] (0..1). A segment eases from
// speed 0 to speed 0 along cubic-bezier(o, 0, 1 - i, 1); this is exactly what
// AE draws for KeyframeEase(0, o*100) -> KeyframeEase(0, i*100).
export const EASES = {
  x: [0.04, 0.94], // snappy expo-like out (reveals)
  o: [0.1, 0.85], // decelerate
  so: [0.3, 0.7], // soft
  io: [0.55, 0.55], // in-out
  i: [0.6, 0.05], // accelerate (exits)
};

export const r2 = (n) => Math.round(n * 100) / 100;
export const hasHangul = (s) => /[ᄀ-ᇿ㄰-㆏가-힯]/.test(s);

export function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const sortKf = (kf) => {
  for (const k in kf) {
    kf[k].sort((a, b) => a[0] - b[0]);
    for (const key of kf[k]) key[0] = r2(key[0]);
    kf[k] = kf[k].filter((key, i, arr) => i === arr.length - 1 || arr[i + 1][0] > key[0]);
  }
};

// Smooth bezier path through points (Catmull-Rom). A point given as
// [x, y, 'c'] is a sharp corner. Returns { v, ti, to } for a 'path' item.
export function smooth(pts, closed = true, k = 1) {
  const n = pts.length;
  const v = pts.map((p) => [r2(p[0]), r2(p[1])]);
  const ti = [];
  const to = [];
  for (let i = 0; i < n; i++) {
    const corner = pts[i][2] === 'c' || (!closed && (i === 0 || i === n - 1));
    const prev = pts[(i - 1 + n) % n];
    const next = pts[(i + 1) % n];
    const tx = corner ? 0 : ((next[0] - prev[0]) / 6) * k;
    const ty = corner ? 0 : ((next[1] - prev[1]) / 6) * k;
    to.push([r2(tx), r2(ty)]);
    ti.push([r2(-tx), r2(-ty)]);
  }
  return { v, ti, to, cl: closed };
}

// Narration timing: line durations come from build/narration_<id>.json once
// ElevenLabs audio exists, otherwise from a reading-speed estimate.
export function estimateDur(text, rate = 7.2) {
  const n = text.replace(/[\s.,!?·'"‘’“”~:()\-–—]/g, '').length;
  return r2(n / rate + 0.3);
}
// Split a caption at clause boundaries into chunks of at most maxChars,
// falling back to the space nearest the middle for an overlong clause.
export function captionChunks(text, maxChars) {
  if (text.length <= maxChars) return [text];
  const clauses = text.split(/(?<=[,.?!])\s+/);
  const out = [];
  for (const c of clauses) {
    const prev = out[out.length - 1];
    if (prev !== undefined && prev.length + 1 + c.length <= maxChars) out[out.length - 1] = prev + ' ' + c;
    else out.push(c);
  }
  return out.flatMap((c) => {
    if (c.length <= maxChars) return [c];
    const mid = c.length / 2;
    let best = -1;
    for (let i = 0; i < c.length; i++) if (c[i] === ' ' && (best < 0 || Math.abs(i - mid) < Math.abs(best - mid))) best = i;
    return best < 0 ? [c] : captionChunks(c.slice(0, best), maxChars).concat(captionChunks(c.slice(best + 1), maxChars));
  });
}

export function timeline(lines, timing, o = {}) {
  const lead = o.lead ?? 0.6;
  const gap = o.gap ?? 0.35;
  const tail = o.tail ?? 0.9;
  let t = lead;
  const out = lines.map((l) => {
    const d = (timing && timing[l.id]) || estimateDur(l.say || l.text);
    const r = { ...l, t: r2(t), dur: r2(d) };
    t += d + gap;
    return r;
  });
  let dur = t - gap + tail;
  dur = Math.max(o.min ?? 0, Math.ceil(dur / BEAT) * BEAT);
  return { lines: out, dur: r2(dur) };
}

// ---------------------------------------------------------------------------
// Kit: builder API bound to a text measuring function.
//   measure(str, font, weight, size, tracking) -> width in px (single line)
// Fonts (preview): kr / krd = Noto Sans KR (본고딕, Hangul designed by Sandoll),
// en = DM Sans, mono = DM Mono. krd is the heavy display cut. In After Effects
// kr / krd resolve to the installed Sandoll family (그레타산스, 고딕Neo3, ...).

export function makeKit(measure) {
  const warnings = [];
  const textWidth = (str, f, w, sz, tr) => Math.max(...String(str).split('\n').map((li) => measure(li, f, w, sz, tr)));

  // Entrance keyframes. Shots end on cuts, so layers stay until the scene ends
  // unless `o.exit` is given.
  function motion(L, o, S) {
    const at = o.at ?? 0;
    const top = o.op ?? 100;
    const type = o.anim ?? 'focus';
    const p = L.p;
    const kf = (L.kf = L.kf || {});
    const d = o.dIn ?? 1.0;
    if (top !== 100) L.o = top;
    switch (type) {
      case 'focus': {
        kf.o = [[at, 0, 'so'], [at + 0.45, top, 'l']];
        const s0 = o.s0 ?? 107;
        kf.s = [[at, [s0, s0], 'x'], [at + d * 1.2, [100, 100], 'l']];
        L.fx = { ...(L.fx || {}), blurKf: [[at, o.b0 ?? 24, 'o'], [at + d * 0.8, 0, 'l']] };
        break;
      }
      case 'up':
        kf.p = [[at, [p[0], p[1] + (o.dy ?? 30)], 'x'], [at + d, [p[0], p[1]], 'l']];
        kf.o = [[at, 0, 'so'], [at + 0.4, top, 'l']];
        break;
      case 'rise':
        kf.p = [[at, [p[0], p[1] + o.mdy], 'x'], [at + (o.dIn ?? 0.8), [p[0], p[1]], 'l']];
        break;
      case 'fade':
        kf.o = [[at, 0, 'io'], [at + (o.dIn ?? 0.5), top, 'l']];
        break;
      case 'pop': {
        // overshooting scale for friendly elements
        kf.s = [[at, [0, 0], 'o'], [at + 0.28, [112, 112], 'io'], [at + 0.5, [100, 100], 'l']];
        kf.o = [[at, 0, 'l'], [at + 0.08, top, 'l']];
        break;
      }
      case 'scale': {
        const s0 = o.s0 ?? 0;
        kf.s = [[at, [s0, s0], 'x'], [at + d, [100, 100], 'l']];
        if (o.fadeIn !== false) kf.o = [[at, 0, 'so'], [at + 0.25, top, 'l']];
        break;
      }
      case 'growX':
        kf.s = [[at, [0, 100], 'x'], [at + d, [100, 100], 'l']];
        break;
      case 'chars':
        kf.o = [[at, 0, 'l'], [at + 0.05, top, 'l']];
        break;
      case 'none':
        break;
      default:
        throw new Error('unknown anim ' + type);
    }
    L.in = r2(Math.max(0, at));
    L.out = S.dur;
    if (o.exit !== undefined && o.exit !== false && o.exit < S.dur) {
      // exits accelerate away: masked lines slide back out of their matte,
      // everything else drifts up, blurs and fades
      const ex = o.exit;
      if (kf.p) {
        const last = kf.p[kf.p.length - 1][1];
        const dy = type === 'rise' ? -o.mdy : -(o.exitDy ?? 40);
        kf.p.push([ex, last, 'i'], [ex + 0.32, [last[0], r2(last[1] + dy)], 'l']);
      } else if (type !== 'none' && type !== 'growX' && L.k === 'text') {
        L.fx = { ...(L.fx || {}) };
        L.fx.blurKf = (L.fx.blurKf || [[at, 0, 'l']]).concat([[ex, 0, 'i'], [ex + 0.3, 18, 'l']]);
      }
      if (type !== 'rise') {
        kf.o = kf.o || [[Math.max(at, ex - 0.01), top, 'l']];
        kf.o.push([ex, top, 'i'], [ex + 0.28, 0, 'l']);
      }
      L.out = r2(Math.min(S.dur, ex + 0.34));
    }
    if (kf.p || ['pop', 'scale', 'focus', 'growX'].includes(type)) L.mb = true;
    sortKf(kf);
    if (L.fx && L.fx.blurKf) {
      const b = { b: L.fx.blurKf };
      sortKf(b);
      L.fx.blurKf = b.b;
    }
    return L;
  }

  const kit = {
    C,
    warnings,
    motion,
    measure: (str, o = {}) => textWidth(str, o.f || 'kr', o.w || 500, o.sz || 40, o.tr ?? 0),

    scene(id, name, dur) {
      return { id, name, dur: r2(dur), layers: [], slots: [], narration: [], cues: [] };
    },

    // Text. y is the visual centre of the block unless o.baseline is set.
    // o.mark draws a mint highlighter stroke behind the text.
    text(S, str, x, y, o = {}) {
      let f = o.f || 'kr';
      if ((f === 'en' || f === 'mono') && hasHangul(str)) f = 'kr';
      const sz = o.sz || 40;
      let w = o.w || (f === 'krd' ? 800 : 500);
      const tr = o.tr ?? (f === 'kr' ? (sz >= 90 ? -35 : -15) : 0);
      const ld = o.ld || Math.round(sz * 1.32);
      const al = o.al || 'l';
      const lines = String(str).split('\n');
      const base = o.baseline ? y : y + sz * 0.36 - ((lines.length - 1) * ld) / 2;
      const tw = textWidth(str, f, w, sz, tr);
      const left = al === 'c' ? x - tw / 2 : al === 'r' ? x - tw : x;
      if (o.mark) {
        const mh = sz * 0.42;
        const my = base - sz * 0.12 + (lines.length - 1) * ld;
        const mark = { k: 'shape', n: 'highlighter', p: [r2(left - 10), r2(my)], a: [r2(left - 10), r2(my)], it: [{ t: 'rect', sz: [r2(tw + 20), r2(mh)], ps: [r2(left - 10 + (tw + 20) / 2), r2(my)], rd: r2(mh * 0.3), fl: { c: o.markC || C.mint, o: o.markO ?? 85 } }] };
        motion(mark, { at: (o.at ?? 0) + (o.markAt ?? 0.35), anim: 'growX', dIn: 0.6, exit: o.exit }, S);
        S.layers.push(mark);
      }
      const L = { k: 'text', n: o.n || str.replace(/\n/g, ' ').slice(0, 28), tx: str, f, w, sz, c: o.c || C.ink, al, tr, ld, p: [r2(x), r2(base)] };
      if (o.maxW && tw > o.maxW) warnings.push(`[${S.id}] text too wide (${Math.round(tw)} > ${o.maxW}): ${str}`);
      if (o.counter) L.cnt = o.counter;
      if (o.bl) L.bl = o.bl;
      const anim = o.anim ?? 'focus';
      if (anim === 'focus' || anim === 'pop') {
        // pivot on the visual centre so the scale settles in place
        const ax = al === 'c' ? 0 : al === 'r' ? -tw / 2 : tw / 2;
        const ay = -sz * 0.36 + ((lines.length - 1) * ld) / 2;
        L.a = [r2(ax), r2(ay)];
        L.p = [r2(x + ax), r2(base + ay)];
        if (o.trFrom !== undefined) L.trk = [[o.at ?? 0, o.trFrom - tr, 'x'], [(o.at ?? 0) + 1.6, 0, 'l']];
      }
      if (anim === 'rise') {
        o.mdy = o.mdy ?? sz * 1.25;
        const top = base - sz * 1.05;
        const bottom = base + (lines.length - 1) * ld + sz * 0.38;
        const pad = 60;
        L.mt = { k: 'shape', n: L.n + ' (matte)', p: [0, 0], it: [{ t: 'rect', sz: [r2(tw + pad * 2), r2(bottom - top)], ps: [r2(left + tw / 2), r2((top + bottom) / 2)], fl: { c: C.white, o: 100 } }] };
      }
      if (anim === 'chars') {
        const at = o.at ?? 0;
        L.rv = { t0: r2(at), t1: r2(at + (o.cdur ?? Math.min(0.75, 0.022 * str.length + 0.25))), e: 'l' };
      }
      motion(L, { ...o, anim }, S);
      if (L.mt) {
        L.mt.in = L.in;
        L.mt.out = L.out;
      }
      L._w = tw;
      S.layers.push(L);
      return L;
    },

    // Big statement, one masked layer per line.
    lines(S, lines, x, y, o = {}) {
      const sz = o.sz || 120;
      const lh = o.lh || Math.round(sz * 1.2);
      const at = o.at ?? 0.15;
      return lines.map((li, i) =>
        kit.text(S, li, x, y + (i - (lines.length - 1) / 2) * lh, {
          sz,
          f: o.f,
          w: o.w || (o.f === 'en' ? 600 : 700),
          tr: o.tr,
          c: (o.colors && o.colors[i]) || o.c || C.ink,
          al: o.al || 'l',
          anim: o.anim || 'rise',
          at: at + i * (o.stagger ?? 0.12),
          maxW: o.maxW,
          exit: o.exit,
          trFrom: o.trFrom,
          mark: o.marks && o.marks[i],
          markAt: 0.45,
        }),
      );
    },

    // Kinetic headline: every word rises out of its own mask, one after another.
    // Words are laid out on one line (left/centre aligned); returns the width.
    words(S, str, x, y, o = {}) {
      const sz = o.sz || 140;
      const f = o.f || 'krd';
      const w = o.w || (f === 'en' ? 600 : 800);
      const tr = o.tr ?? (f === 'en' ? -20 : -40);
      const parts = String(str).split(' ');
      const space = kit.measure(' ', { f, w, sz, tr }) * (o.space ?? 0.9);
      const widths = parts.map((q) => kit.measure(q, { f, w, sz, tr }));
      const total = widths.reduce((a, b) => a + b, 0) + space * (parts.length - 1);
      let cx = o.al === 'c' ? x - total / 2 : x;
      const at = o.at ?? 0;
      parts.forEach((q, i) => {
        const c = (o.colors && o.colors[i]) || o.c || C.ink;
        kit.text(S, q, cx, y, { f, w, sz, tr, c, anim: 'rise', at: r2(at + i * (o.stagger ?? 0.07)), dIn: o.dIn ?? 0.7, exit: o.exit, mark: o.marks && o.marks[i], markAt: 0.3 });
        cx += widths[i] + space;
      });
      if (o.maxW && total > o.maxW) warnings.push(`[${S.id}] words too wide (${Math.round(total)} > ${o.maxW}): ${str}`);
      return total;
    },

    // Full-frame colour card wiping in from the left (punctuation beats),
    // wiping out to the right at t1.
    punch(S, t0, t1, o = {}) {
      const L = { k: 'shape', n: 'punch card', p: [0, H / 2], a: [0, H / 2], it: [{ t: 'rect', sz: [W, H], ps: [W / 2, H / 2], fl: { c: o.c || C.mint, o: 100 } }] };
      // o.full: already covering the frame at t0 (continues a wipe)
      L.kf = { s: o.full ? [[t0, [100, 100], 'l']] : [[t0, [0, 100], 'x'], [r2(t0 + 0.45), [100, 100], 'l']] };
      L.in = r2(t0);
      L.out = r2(Math.min(S.dur, t1 + 0.4));
      if (t1 < S.dur) {
        L.kf.p = [[t1, [0, H / 2], 'i'], [r2(t1 + 0.4), [W, H / 2], 'l']];
        L.kf.s.push([t1, [100, 100], 'i'], [r2(t1 + 0.4), [0, 100], 'l']);
      }
      L.mb = true;
      sortKf(L.kf);
      S.layers.push(L);
      return L;
    },

    // Small mono label (uppercase Latin) or small Korean caption.
    label(S, str, x, y, o = {}) {
      const kr = hasHangul(str);
      return kit.text(S, str, x, y, { f: kr ? 'kr' : 'mono', w: kr ? 600 : 500, sz: o.sz || (kr ? 24 : 19), tr: o.tr ?? (kr ? 0 : 240), c: o.c || C.accent, al: o.al || 'l', anim: o.anim || (kr ? 'fade' : 'chars'), at: o.at ?? 0.1, exit: o.exit, maxW: o.maxW });
    },

    footnote(S, str, o = {}) {
      return kit.text(S, str, o.x ?? 160, o.y ?? 1000, { sz: o.sz || 19, w: 500, c: o.c || C.ink3, al: o.al || 'l', anim: 'fade', at: o.at ?? 0.6, maxW: 1600 });
    },

    // Plain line that draws on with Trim Paths.
    line(S, pts, o = {}) {
      const at = o.at ?? 0;
      const it = { t: 'path', v: pts.map((q) => [r2(q[0]), r2(q[1])]), cl: !!o.closed, st: { c: o.c || C.ink, w: o.sw ?? 1.5, o: o.so ?? 100, cap: o.cap || 'r' } };
      if (o.draw !== false) it.tm = { e: [[at, 0, o.ease || 'x'], [at + (o.dur ?? 0.9), 100, 'l']] };
      const L = { k: 'shape', n: o.n || 'line', p: [0, 0], it: [it] };
      if (o.fx) L.fx = o.fx;
      if (o.bl) L.bl = o.bl;
      motion(L, { ...o, anim: o.anim || 'none' }, S);
      S.layers.push(L);
      return L;
    },

    shape(S, it, o = {}) {
      const L = { k: 'shape', n: o.n || 'shape', p: o.p || [0, 0], it };
      if (o.a) L.a = o.a;
      if (o.fx) L.fx = { ...o.fx };
      if (o.bl) L.bl = o.bl;
      if (o.ex) L.ex = o.ex;
      motion(L, { anim: 'fade', ...o }, S);
      S.layers.push(L);
      return L;
    },

    // Rounded tag with text (friendly accents, used sparingly).
    pill(S, str, x, y, o = {}) {
      const sz = o.sz || 24;
      const tw = textWidth(str, 'kr', 600, sz, -10);
      const w = tw + sz * 1.6;
      const h = sz * 2;
      const cx = o.al === 'c' ? x : x + w / 2;
      kit.shape(S, [{ t: 'rect', sz: [r2(w), r2(h)], ps: [r2(cx), y], rd: h / 2, fl: { c: o.fill || C.mint, o: o.fillO ?? 100 } }], { n: 'pill', p: [r2(cx), y], a: [r2(cx), y], anim: 'pop', at: o.at, exit: o.exit });
      kit.text(S, str, cx, y, { sz, w: 600, tr: -10, c: o.c || C.ink, al: 'c', anim: 'fade', dIn: 0.3, at: (o.at ?? 0) + 0.12, exit: o.exit });
      return w;
    },

    // Full-frame mint background for punctuation shots.
    mintFrame(S) {
      S.layers.push({ k: 'ramp', n: 'Mint frame', in: 0, out: S.dur, p: [W / 2, H / 2], a: [W / 2, H / 2], sz: [W, H], rp: { t: 'lin', p1: [0, 0], c1: '#B4FFEC', p2: [W, H], c2: '#7FEBD1' } });
    },

    // The "horizon": a hairline with a soft mint glow and a travelling highlight.
    horizon(S, y, o = {}) {
      const at = o.at ?? 0;
      const x0 = o.x0 ?? 0;
      const x1 = o.x1 ?? W;
      const cx = o.cx ?? (x0 + x1) / 2;
      const dur = o.dur ?? 1.4;
      const half = (pts, extra) => ({ t: 'path', v: pts, cl: false, st: { c: extra.c, w: extra.w, o: extra.o, cap: 'r' }, tm: { e: [[at, 0, 'x'], [at + dur, 100, 'l']] } });
      const mk = (extra) => [half([[cx, y], [x0, y]], extra), half([[cx, y], [x1, y]], extra)];
      kit.shape(S, mk({ c: o.c || C.mint2, w: 14, o: 70 }), { n: 'horizon glow', anim: 'none', at, fx: { blur: 30 }, op: o.glow ?? 90, exit: o.exit });
      kit.shape(S, mk({ c: o.core || C.ink, w: 1.5, o: o.coreO ?? 45 }), { n: 'horizon', anim: 'none', at, exit: o.exit });
      if (o.travel !== false) {
        const sp = x1 - x0 + 600;
        kit.shape(
          S,
          [{ t: 'ell', sz: [340, 4], ps: [0, 0], fl: { c: C.accent, o: 90 }, ge: { p: { fn: 'flowX', x0: r2(x0 + (o.phase ?? 0.3) * sp), v: o.v ?? 520, span: r2(sp), off: r2(300 - x0), y } } }],
          { n: 'horizon highlight', anim: 'fade', at: at + dur * 0.6, fx: { blur: 6 }, exit: o.exit },
        );
      }
    },

    // Thin bar split into segments that grow one after another.
    split(S, x, y, w, segs, o = {}) {
      const at = o.at ?? 0;
      const gap = o.gap ?? 10;
      const h = o.h ?? 6;
      let cx = x;
      return segs.map((sg, i) => {
        const sw = (w * sg.pct) / 100 - (i < segs.length - 1 ? gap : 0);
        const t0 = at + i * (o.stagger ?? 0.25);
        const L = { k: 'shape', n: 'split ' + i, p: [cx, y], a: [cx, y], it: [{ t: 'rect', sz: [r2(sw), h], ps: [r2(cx + sw / 2), y], rd: h / 2, fl: { c: sg.c, o: 100 } }] };
        motion(L, { at: t0, anim: 'growX', dIn: 0.9, exit: o.exit }, S);
        S.layers.push(L);
        const r = { ...sg, x: cx, t: t0, w: sw };
        cx += (w * sg.pct) / 100;
        return r;
      });
    },

    // Elysium logo slot (official logo goes into the LOGO comp in AE).
    logo(S, x, y, scale, o = {}) {
      const L = { k: 'slot', n: 'LOGO Elysium', ref: 'LOGO', p: [x, y], a: [600, 150], s: [scale, scale] };
      motion(L, { anim: 'none', ...o }, S);
      const at = o.at ?? 0;
      L.kf.o = [[at, 0, 'so'], [at + 0.6, 100, 'l']];
      L.kf.s = [[at, [scale * 1.08, scale * 1.08], 'x'], [at + 2.2, [scale, scale], 'l']];
      L.fx = { blurKf: [[at, 30, 'o'], [at + 1.0, 0, 'l']] };
      S.layers.push(L);
      return L;
    },

    // Character sticker image (assets/stickers/<file>), fitted into a box of
    // height h and centred on (x, y). Pops in; optional idle wiggle.
    sticker(S, file, x, y, h, o = {}) {
      const L = { k: 'img', n: 'sticker ' + file, src: 'assets/stickers/' + file, fit: [r2(h * (o.aspect ?? 1.3)), h], p: [r2(x), r2(y)] };
      motion(L, { anim: 'pop', ...o }, S);
      if (o.wiggle !== false) L.ex = { r: { fn: 'sway', a: o.wiggle ?? 2.5, f: 2.2, ph: 0 } };
      S.layers.push(L);
      return L;
    },

    // Stock footage placeholder (AE: replaceable precomp; preview: empty).
    slot(S, id, o = {}) {
      const L = { k: 'slot', n: 'STOCK ' + id, ref: id, p: [W / 2, H / 2], a: [W / 2, H / 2], bl: 'multiply', fx: { tint: [C.ink, C.paper2] } };
      motion(L, { anim: 'fade', op: o.op ?? 25, at: o.at ?? 0, dIn: 0.8 }, S);
      S.layers.push(L);
      S.slots.push(id);
      return L;
    },

    // Voice-over without subtitles (commercial): manifest entries only.
    vo(S, lines) {
      for (const l of lines) S.narration.push({ id: l.id, t: l.t, dur: l.dur, text: l.text, say: l.say || l.text });
    },

    // Narrated subtitles + manifest entries for the ElevenLabs script. Long
    // lines are shown in clause-sized chunks (o.maxChars), timed by length.
    say(S, lines, o = {}) {
      for (const l of lines) {
        S.narration.push({ id: l.id, t: l.t, dur: l.dur, text: l.text, say: l.say || l.text });
        const chunks = captionChunks(l.text, o.maxChars || 999);
        const len = (s) => s.replace(/\s/g, '').length;
        const total = chunks.reduce((a, c) => a + len(c), 0);
        let t = l.t;
        chunks.forEach((c, i) => {
          const d = (l.dur * len(c)) / total;
          const L = kit.text(S, c, o.x ?? W / 2, o.y ?? 1000, { sz: o.sz || 32, w: 600, tr: -15, c: o.c || C.ink, al: 'c', anim: 'fade', dIn: i ? 0.08 : 0.15, at: r2(t), maxW: 1700 });
          L.top = true; // captions stay above full-frame cards
          const last = i === chunks.length - 1;
          const end = r2(last ? l.t + l.dur + 0.15 : t + d - 0.08);
          if (end < S.dur) {
            L.kf.o.push([end, 100, 'io'], [r2(end + (last ? 0.15 : 0.06)), 0, 'l']);
            L.out = r2(Math.min(S.dur, end + (last ? 0.2 : 0.08)));
          }
          t += d;
        });
      }
    },
  };
  return kit;
}

// ---------------------------------------------------------------------------
// Hypurr: the provided base character (assets/stickers/hypurr_sit.png) cut
// into head / body / tail (engine/cut-rig.py) and rigged with parented nulls:
//   ROOT (placement, hops, lean) > BODY (breathing) > TAIL (sway)
//                                               > HEAD idle > HEAD (tilts)
// Face overlays on the head add blinks, a talking mouth, happy eyes, glasses,
// sparkles, a sweat drop and a "!" mark, drawn in the character's own line
// style. Hops squash and stretch about the feet, like the sticker pack.
// o.flip mirrors the character (it then faces right).

const RIG = {
  size: [579, 813],
  origin: [290, 800],
  neck: [245, 445],
  tailBase: [455, 672],
  chin: [[0, 400], [60, 415], [120, 437], [170, 447], [250, 450], [300, 437], [350, 425], [400, 405], [430, 380], [450, 365]],
  eyes: [{ c: [111.5, 325.5], sz: [43, 63] }, { c: [309.5, 298.5], sz: [49, 69] }],
  mouth: [196, 352],
  line: '#0B1F1E',
  fur: '#FFFFFF',
};
const MOODS = {
  idle: { head: 0, lean: 0 },
  point: { head: 7, lean: 3 },
  pointUp: { head: -8, lean: 2, hop: 1 },
  present: { head: 4, hop: 1, sparkle: 1 },
  open: { head: 0, hop: 1, happy: 0.9 },
  cheer: { head: 0, hop: 2, happy: 1.4 },
  hold: { head: 5, lean: 1 },
  shrug: { head: -9, lean: 0, sweat: 1 },
  stop: { head: -5, lean: -3, alert: 1 },
};
let rigSeq = 0;

export function mascot(kit, S, x, ground, height, o = {}) {
  const k = height / RIG.size[1];
  const rp = (p) => [r2((p[0] - RIG.origin[0]) * k), r2((p[1] - RIG.origin[1]) * k)];
  const neg = (p) => [-p[0], -p[1]];
  const pv = [r2(RIG.origin[0] / RIG.size[0]), r2(RIG.origin[1] / RIG.size[1])];
  const fit = [r2(RIG.size[0] * k), r2(RIG.size[1] * k)];
  const u = `${S.id}_hyp${++rigSeq}`;
  const id = (n) => `${u}_${n}`;
  const lw = (w) => r2(w * k);
  const base = { in: 0, out: S.dur };
  const neck = rp(RIG.neck);
  const tailB = rp(RIG.tailBase);
  const nul = (n, extra) => ({ k: 'null', n: `Hypurr ${n}`, id: id(n), a: [0, 0], ...base, ...extra });
  const img = (n, file, par, p) => ({ k: 'img', n: `Hypurr ${n}`, src: `assets/stickers/rig/${file}`, fit, pv, par: id(par), p, ...base });

  const sx = o.flip ? -1 : 1;
  const root = nul('ROOT', { p: [r2(x), r2(ground)], s: [sx * 100, 100], kf: {} });
  const body = nul('BODY', { par: id('ROOT'), p: [0, 0], ex: { s: { fn: 'breath', a: 1.1, f: 2.3 } } });
  const tail = nul('TAIL', { par: id('BODY'), p: tailB, ex: { r: { fn: 'sway', a: 5, f: 1.7, ph: 0 } } });
  const headIdle = nul('HEAD idle', { par: id('BODY'), p: neck, ex: { r: { fn: 'sway', a: 1.6, f: 1.15, ph: 0.8 } } });
  const head = nul('HEAD', { par: id('HEAD idle'), p: [0, 0], kf: {} });
  // white neck patch under the chin so tilting the head never opens a gap
  const chin = RIG.chin.map(rp);
  const neckFill = { k: 'shape', n: 'Hypurr neck fill', par: id('BODY'), p: [0, 0], ...base, it: [{ t: 'path', v: [...chin, ...chin.slice().reverse().map(([a, b]) => [a, r2(b - 46 * k)])], cl: true, fl: { c: RIG.fur, o: 100 } }] };

  // face rig (head space): blink covers, happy eyes, talking mouth, extras
  const fp = (p) => {
    const q = rp(p);
    return [r2(q[0] - neck[0]), r2(q[1] - neck[1])];
  };
  const face = [];
  const happyItems = [];
  for (const e of RIG.eyes) {
    const c = fp(e.c);
    const cover = [r2((e.sz[0] + 14) * k), r2((e.sz[1] + 14) * k)];
    const blink = { fn: 'blinkO', ph: 0.5, per: 3.8 };
    face.push({ t: 'ell', sz: cover, ps: c, fl: { c: RIG.fur, o: 100 }, ge: { o: blink } });
    face.push({ t: 'path', ...smooth([[c[0] - cover[0] * 0.42, c[1] + 4 * k], [c[0], c[1] + 12 * k], [c[0] + cover[0] * 0.42, c[1] + 4 * k]], false), st: { c: RIG.line, w: lw(6), o: 100, cap: 'r' }, ge: { o: blink } });
    const hc = { t: 'ell', sz: cover, ps: c, fl: { c: RIG.fur, o: 100 }, go: 0 };
    const ha = { t: 'path', ...smooth([[c[0] - cover[0] * 0.4, c[1] + 8 * k], [c[0], c[1] - 14 * k], [c[0] + cover[0] * 0.4, c[1] + 8 * k]], false), st: { c: RIG.line, w: lw(7), o: 100, cap: 'r' }, go: 0 };
    face.push(hc, ha);
    happyItems.push(hc, ha);
  }
  const mc = fp(RIG.mouth);
  const mouth = { t: 'ell', sz: [lw(30), lw(26)], ps: [mc[0], r2(mc[1] + 11 * k)], fl: { c: '#E46F8A', o: 100 }, st: { c: RIG.line, w: lw(4.5), o: 100 }, ga: mc, ge: { s: { fn: 'talk', w: [], f: 15 } } };
  face.push(mouth);
  if (o.glasses) {
    for (const e of RIG.eyes) {
      const c = fp(e.c);
      face.push({ t: 'ell', sz: [lw(e.sz[0] + 58), lw(e.sz[1] + 30)], ps: c, st: { c: '#E5352E', w: lw(9), o: 100 } });
    }
    const [l, r] = RIG.eyes.map((e) => fp(e.c));
    face.push({ t: 'path', ...smooth([[r2(l[0] + lw(50)), r2(l[1] - lw(4))], [r2((l[0] + r[0]) / 2), r2((l[1] + r[1]) / 2 - lw(14))], [r2(r[0] - lw(52)), r2(r[1] - lw(2))]], false), st: { c: '#E5352E', w: lw(8), o: 100, cap: 'r' } });
  }
  const top = fp([60, 120]);
  const sparkle = { t: 'path', v: [[top[0], r2(top[1] - 30 * k)], [r2(top[0] + 9 * k), r2(top[1] - 9 * k)], [r2(top[0] + 30 * k), top[1]], [r2(top[0] + 9 * k), r2(top[1] + 9 * k)], [top[0], r2(top[1] + 30 * k)], [r2(top[0] - 9 * k), r2(top[1] + 9 * k)], [r2(top[0] - 30 * k), top[1]], [r2(top[0] - 9 * k), r2(top[1] - 9 * k)]], cl: true, fl: { c: '#FFE36E', o: 100 }, st: { c: RIG.line, w: lw(5), o: 100 }, ga: top, gkf: { s: [[0, [0, 0], 'h']] } };
  const sw = fp([420, 200]);
  const sweat = { t: 'path', ...smooth([[sw[0], r2(sw[1] - 26 * k), 'c'], [r2(sw[0] + 13 * k), r2(sw[1] + 4 * k)], [sw[0], r2(sw[1] + 16 * k)], [r2(sw[0] - 13 * k), r2(sw[1] + 4 * k)]], true, 0.9), fl: { c: '#8FD6F5', o: 100 }, st: { c: RIG.line, w: lw(4), o: 100 }, ga: sw, gkf: { s: [[0, [0, 0], 'h']] } };
  const am = fp([470, 95]);
  // "!" mark: two items scaling about the same point
  const alert = [
    { t: 'rect', sz: [lw(20), lw(62)], ps: [am[0], r2(am[1] - 18 * k)], rd: lw(10), fl: { c: '#FFB547', o: 100 }, st: { c: RIG.line, w: lw(5), o: 100 }, ga: am },
    { t: 'ell', sz: [lw(22), lw(22)], ps: [am[0], r2(am[1] + 34 * k)], fl: { c: '#FFB547', o: 100 }, st: { c: RIG.line, w: lw(5), o: 100 }, ga: am },
  ];
  face.push(sparkle, sweat, ...alert);

  const L = [
    root, body, tail,
    img('tail', 'hypurr_tail.png', 'TAIL', neg(tailB)),
    neckFill,
    img('body', 'hypurr_body.png', 'BODY', [0, 0]),
    headIdle, head,
    img('head', 'hypurr_head.png', 'HEAD', neg(neck)),
    { k: 'shape', n: 'Hypurr face rig', par: id('HEAD'), p: [0, 0], it: face, ...base },
  ];
  if (o.at) for (const l of L) if (l.k !== 'null') l.kf = { ...(l.kf || {}), o: [[o.at, 0, 'so'], [o.at + 0.35, 100, 'l']] };
  for (const l of L) l.top = true; // the presenter stays above full-frame cards
  S.layers.push(...L);

  // keyframe builders
  const keys = { head: [[0, 0, 'l']], lean: [[0, 0, 'l']], pos: [], sq: [], happy: [[0, 0, 'h']], sparkle: [[0, [0, 0], 'h']], sweat: [[0, [0, 0], 'h']], alert: [[0, [0, 0], 'h']] };
  let cur = { head: 0, lean: 0 };
  const P = [r2(x), r2(ground)];
  const popKeys = (arr, t, hold = 0.9) => arr.push([r2(t), [0, 0], 'o'], [r2(t + 0.22), [115, 115], 'io'], [r2(t + 0.36), [100, 100], 'l'], [r2(t + 0.36 + hold), [100, 100], 'i'], [r2(t + 0.56 + hold), [0, 0], 'h']);
  const api = {
    layers: L,
    pose(t, name, d = 0.32) {
      const m = MOODS[name] || MOODS.idle;
      keys.head.push([r2(t), cur.head, 'o'], [r2(t + d), m.head, 'l']);
      keys.lean.push([r2(t), cur.lean * sx, 'o'], [r2(t + d), (m.lean || 0) * sx, 'l']);
      cur = { head: m.head, lean: m.lean || 0 };
      for (let i = 0; i < (m.hop || 0); i++) api.hop(t + i * 0.42);
      if (m.happy) api.happy(t, t + m.happy);
      if (m.sparkle) popKeys(keys.sparkle, t + 0.1);
      if (m.sweat) popKeys(keys.sweat, t + 0.15, 1.2);
      if (m.alert) popKeys(keys.alert, t + 0.05, 1.1);
      return api;
    },
    wave(t, n = 3) {
      keys.lean.push([r2(t), cur.lean * sx, 'io']);
      for (let i = 0; i < n * 2; i++) keys.lean.push([r2(t + 0.17 * (i + 1)), (cur.lean + (i % 2 ? -5 : 5)) * sx, 'io']);
      keys.lean.push([r2(t + 0.17 * (n * 2 + 1)), cur.lean * sx, 'l']);
      api.happy(t, t + 0.17 * (n * 2 + 1));
      return api;
    },
    happy(t0, t1) {
      keys.happy.push([r2(t0), 100, 'h'], [r2(t1), 0, 'h']);
      return api;
    },
    sparkle(t) {
      popKeys(keys.sparkle, t);
      return api;
    },
    hop(t, h = 34) {
      // anticipation squash, stretch in the air, a small squash on landing
      keys.pos.push([r2(t), P, 'l'], [r2(t + 0.07), P, 'o'], [r2(t + 0.24), [P[0], r2(P[1] - h * k * 1.6)], 'io'], [r2(t + 0.44), P, 'l']);
      const S2 = (a, b) => [sx * a, b];
      keys.sq.push([r2(t), S2(100, 100), 'o'], [r2(t + 0.07), S2(108, 91), 'io'], [r2(t + 0.2), S2(95, 106), 'io'], [r2(t + 0.44), S2(105, 95), 'io'], [r2(t + 0.6), S2(100, 100), 'l']);
      return api;
    },
    alert(t) {
      popKeys(keys.alert, t, 1.1);
      return api;
    },
    enter(t0, t1, fromX) {
      const n = Math.max(2, Math.round((t1 - t0) / 0.3));
      for (let i = 0; i <= n; i++) {
        const uu = i / n;
        keys.pos.push([r2(t0 + (t1 - t0) * uu), [r2(fromX + (P[0] - fromX) * (1 - (1 - uu) ** 2)), r2(P[1] - (i % 2 ? 26 * k * 1.6 : 0))], 'io']);
      }
      return api;
    },
    talk(windows) {
      mouth.ge.s.w = windows.map(([a, b]) => [r2(a), r2(b)]);
      return api;
    },
    // a spot in front of the character for props (comp space)
    hand() {
      return [r2(x - sx * 300 * k), r2(ground - 300 * k)];
    },
    done() {
      const kf = { r: keys.head };
      sortKf(kf);
      head.kf.r = kf.r;
      const lk = { r: keys.lean, p: keys.pos, s: keys.sq };
      if (!lk.p.length) delete lk.p;
      if (!lk.s.length) delete lk.s;
      sortKf(lk);
      root.kf = { ...root.kf, ...lk };
      const hk = { o: keys.happy };
      sortKf(hk);
      if (hk.o.length > 1) for (const it of happyItems) it.gkf = { o: hk.o };
      for (const [item, arr] of [[sparkle, keys.sparkle], [sweat, keys.sweat], [alert[0], keys.alert], [alert[1], keys.alert]]) {
        const g = { s: arr };
        sortKf(g);
        item.gkf = { s: g.s };
      }
      return api;
    },
  };
  return api;
}

// ---------------------------------------------------------------------------
// Main comp: warm paper with a mint dawn rising from the horizon and a fine
// architectural grid under the scenes; grain, transitions and fades above.

export function mainLayers(video) {
  const { dur } = video;
  const grid = [];
  for (let x = 120; x < W; x += 120) grid.push({ t: 'path', v: [[x, 0], [x, H]], cl: false, st: { c: C.ink, w: 1, o: 100 } });
  for (let y = 120; y < H; y += 120) grid.push({ t: 'path', v: [[0, y], [W, y]], cl: false, st: { c: C.ink, w: 1, o: 100 } });
  const full = { in: 0, out: dur, p: [W / 2, H / 2], a: [W / 2, H / 2], sz: [W, H] };
  return [
    { k: 'ramp', n: 'BG paper', ...full, rp: { t: 'lin', p1: [W / 2, 0], c1: '#FCFBF8', p2: [W / 2, H], c2: '#F1F6F2' } },
    { k: 'ramp', n: 'BG horizon light', ...full, bl: 'multiply', rp: { t: 'rad', p1: [W * 0.5, H + 330], c1: '#B5F1DE', p2: [W * 0.5 + 1350, H + 330], c2: C.white } },
    { k: 'ramp', n: 'BG top light', ...full, bl: 'multiply', o: 60, rp: { t: 'rad', p1: [W * 0.12, -260], c1: '#DCEFF6', p2: [W * 0.12 + 1100, -260], c2: C.white } },
    { k: 'shape', n: 'BG grid', in: 0, out: dur, p: [0, 0], o: 4.5, it: grid },
    { k: 'ramp', n: 'Vignette', ...full, bl: 'multiply', o: 55, rp: { t: 'rad', p1: [W / 2, H * 0.45], c1: C.white, p2: [W / 2 + 1400, H * 0.45], c2: C.paperEdge } },
  ];
}

// Two-panel wipe across a cut at time t: a mint panel covers the frame and
// slides off to the right, trailed by a thin ink panel.
function wipeLayers(t, dur, i) {
  const rect = (c) => [{ t: 'rect', sz: [W, H], ps: [W / 2, H / 2], fl: { c, o: 100 } }];
  const t0 = r2(Math.max(0, t - 0.3));
  const mk = (n, c, lag) => ({
    k: 'shape', n, in: t0, out: r2(Math.min(dur, t + 0.5 + lag)), p: [-W, 0], it: rect(c), mb: true,
    kf: { p: [[r2(t0 + lag), [-W, 0], 'i'], [r2(t + lag * 0.5), [0, 0], 'o'], [r2(t + 0.36 + lag), [W, 0], 'l']] },
  });
  return [mk(`Wipe ${i} ink`, C.ink, 0.07), mk(`Wipe ${i} mint`, C.mint, 0)];
}

export function finishLayers(video) {
  const { dur } = video;
  return [
    { k: 'adjust', n: 'Film grain', in: 0, out: dur, fx: { noise: 2.5 } },
    { k: 'ramp', n: 'Fade in/out', in: 0, out: dur, p: [W / 2, H / 2], a: [W / 2, H / 2], sz: [W, H], rp: { t: 'lin', p1: [0, 0], c1: C.paper, p2: [W, H], c2: C.paper }, kf: { o: [[0, 100, 'so'], [0.5, 0, 'l'], [dur - 1.0, 0, 'io'], [dur, 100, 'l']] } },
  ];
}

export function assemble(meta, scenes, slotsMeta, kit, opts = {}) {
  let t = 0;
  const video = { id: meta.id, name: meta.name, w: W, h: H, fps: FPS, dur: 0, scenes: {}, slots: {}, layers: [], order: [], narration: [], cues: [] };
  const placed = [];
  for (const S of scenes) {
    placed.push({ S, start: r2(t) });
    t += S.dur;
  }
  video.dur = r2(t);
  const layers = mainLayers(video);
  const push = opts.push ?? 3; // slow camera push-in per shot (%)
  const wipes = [];
  placed.forEach(({ S, start }, i) => {
    // layers flagged `top` (captions, presenter) draw above everything else
    const ordered = [...S.layers.filter((l) => !l.top), ...S.layers.filter((l) => l.top)];
    video.scenes[S.id] = { name: S.name, dur: S.dur, layers: ordered.map(clean) };
    video.order.push({ id: S.id, start, dur: S.dur, name: S.name });
    for (const n of S.narration) video.narration.push({ ...n, scene: S.id, start: r2(start + n.t) });
    // a whoosh on a cut leads the wipe so its swell lands on the cut
    for (const c of S.cues || []) video.cues.push({ ...c, t: r2(Math.max(0, start + c.t - (opts.wipe && i && c.type === 'whoosh' && c.t === 0 ? 0.3 : 0))) });
    // camera: each shot lands slightly pushed in, settles, then drifts in slowly
    const end = r2(start + S.dur);
    const s = i && opts.wipe ? [[start, [104, 104], 'x'], [r2(start + 1.1), [100, 100], 'l'], [end, [100 + push, 100 + push], 'l']] : [[start, [100, 100], 'l'], [end, [100 + push, 100 + push], 'l']];
    layers.push({ k: 'comp', n: S.name, ref: S.id, in: start, out: end, p: [W / 2, H / 2], a: [W / 2, H / 2], kf: { s } });
    if (i && opts.wipe) wipes.push(...wipeLayers(start, video.dur, i));
  });
  layers.push(...wipes, ...finishLayers(video));
  video.layers = layers.map(clean);
  for (const [id, m] of Object.entries(slotsMeta)) video.slots[id] = { ...m, layers: (m.layers || []).map(clean) };
  video.warnings = kit.warnings;
  return video;
}

function clean(L) {
  const out = {};
  for (const [k, v] of Object.entries(L)) {
    if (k.startsWith('_') || k === 'top') continue;
    out[k] = k === 'mt' && v ? clean(v) : v;
  }
  return out;
}

// Default (replaceable) content of the LOGO slot: a typographic wordmark.
export function logoSlot(kit, dur) {
  const S = kit.scene('LOGO', 'LOGO', dur);
  const T = (o) => kit.text(S, 'ELYSIUM', 600, 150, { f: 'en', w: 300, sz: 150, tr: 440, al: 'c', anim: 'none', ...o });
  T({ n: 'Wordmark (placeholder)' });
  const sweep = T({ n: 'Wordmark sweep', c: C.mint2 });
  sweep.mt = { k: 'shape', n: 'sweep matte', p: [0, 150], in: 0, out: dur, fx: { blur: 50 }, r: 16, it: [{ t: 'rect', sz: [180, 460], ps: [0, 0], fl: { c: C.white, o: 100 } }], kf: { p: [[0.9, [-300, 150], 'io'], [2.6, [1500, 150], 'l']] } };
  return { name: 'LOGO_Elysium', kind: 'logo', w: 1200, h: 300, dur, desc: '공식 Elysium 로고 자리 — kinetiq.xyz/brand 또는 elysium.kinetiq.xyz 에서 받은 SVG/PNG를 이 컴프에 넣고 기본 워드마크 레이어 2개를 끄세요.', layers: S.layers };
}
