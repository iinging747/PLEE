// Canvas 2D player for compiled video documents (see engine/lib.js).
// Mirrors the After Effects runtime: same keyframes, same eases, same
// expressions, same layer order and track mattes.

import { EASES } from './lib.js';
import { evalExpr, counterValue } from './expr.js';

export const FAM = { kr: '"Pretendard"', krd: '"Jua"', en: '"DM Sans"', mono: '"DM Mono"' };

// cubic-bezier(x1, 0, x2, 1) solver
function bezier(x1, x2) {
  const cx = 3 * x1;
  const bx = 3 * (x2 - x1) - cx;
  const ax = 1 - cx - bx;
  const cy = 0;
  const by = 3 - cy;
  const ay = 1 - cy - by;
  const sx = (u) => ((ax * u + bx) * u + cx) * u;
  const sy = (u) => ((ay * u + by) * u + cy) * u;
  const dx = (u) => (3 * ax * u + 2 * bx) * u + cx;
  return (x) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let u = x;
    for (let i = 0; i < 8; i++) {
      const err = sx(u) - x;
      const d = dx(u);
      if (Math.abs(err) < 1e-6) return sy(u);
      if (Math.abs(d) < 1e-6) break;
      u -= err / d;
    }
    let lo = 0;
    let hi = 1;
    u = x;
    for (let i = 0; i < 40; i++) {
      const v = sx(u);
      if (Math.abs(v - x) < 1e-6) break;
      if (x > v) lo = u;
      else hi = u;
      u = (lo + hi) / 2;
    }
    return sy(u);
  };
}

const EASE_FN = {};
for (const [k, [o, i]] of Object.entries(EASES)) EASE_FN[k] = bezier(o, 1 - i);
EASE_FN.l = (x) => x;
EASE_FN.h = () => 0;

export function kfVal(kf, t, def) {
  if (!kf || !kf.length) return def;
  if (t <= kf[0][0]) return kf[0][1];
  const last = kf[kf.length - 1];
  if (t >= last[0]) return last[1];
  let i = 0;
  while (i < kf.length - 2 && t >= kf[i + 1][0]) i++;
  const [t0, v0, e] = kf[i];
  const [t1, v1] = kf[i + 1];
  const p = (EASE_FN[e] || EASE_FN.l)((t - t0) / (t1 - t0));
  if (Array.isArray(v0)) return v0.map((a, j) => a + (v1[j] - a) * p);
  return v0 + (v1 - v0) * p;
}

const BLEND = { screen: 'screen', add: 'lighter', multiply: 'multiply', overlay: 'overlay' };

function hexA(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

// images: { src -> HTMLImageElement | null }, preloaded by the page
export function createRenderer(canvas, video, images = {}) {
  const W = video.w;
  const H = video.h;
  const ctx = canvas.getContext('2d');
  const pool = [];
  let used = 0;
  function acquire() {
    if (used >= pool.length) {
      const c = document.createElement('canvas');
      c.width = W;
      c.height = H;
      pool.push({ c, ctx: c.getContext('2d') });
    }
    const o = pool[used++];
    o.ctx.setTransform(1, 0, 0, 1, 0, 0);
    o.ctx.globalAlpha = 1;
    o.ctx.globalCompositeOperation = 'source-over';
    o.ctx.filter = 'none';
    o.ctx.clearRect(0, 0, W, H);
    return o;
  }
  const release = () => used--;

  // film grain tile
  const grain = document.createElement('canvas');
  grain.width = grain.height = 256;
  {
    const g = grain.getContext('2d');
    const img = g.createImageData(256, 256);
    let s = 1234567;
    for (let i = 0; i < img.data.length; i += 4) {
      s = (s * 1103515245 + 12345) & 0x7fffffff;
      const v = s & 255;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
  }
  const grainPat = ctx.createPattern(grain, 'repeat');

  function transform(c, L, t) {
    const p = L.ex && L.ex.p ? evalExpr(L.ex.p, t) : kfVal(L.kf && L.kf.p, t, L.p || [0, 0]);
    const a = L.a || [0, 0];
    const s = L.ex && L.ex.s ? evalExpr(L.ex.s, t) : kfVal(L.kf && L.kf.s, t, L.s || [100, 100]);
    const r = L.ex && L.ex.r ? evalExpr(L.ex.r, t) : kfVal(L.kf && L.kf.r, t, L.r || 0);
    c.translate(p[0], p[1]);
    if (r) c.rotate((r * Math.PI) / 180);
    c.scale(s[0] / 100, s[1] / 100);
    c.translate(-a[0], -a[1]);
  }

  function drawText(c, L, t) {
    c.font = `${L.w} ${L.sz}px ${FAM[L.f]}`;
    c.letterSpacing = `${((L.tr + kfVal(L.trk, t, 0)) / 1000) * L.sz}px`;
    c.fillStyle = L.c;
    c.textBaseline = 'alphabetic';
    const txt = L.cnt ? counterValue(L.cnt, t) : L.tx;
    const lines = txt.split('\n');
    if (!L.rv) {
      c.textAlign = L.al === 'c' ? 'center' : L.al === 'r' ? 'right' : 'left';
      lines.forEach((li, i) => c.fillText(li, 0, i * L.ld));
      return;
    }
    // per-character reveal (AE: text animator opacity 0, range Start 0 -> 100)
    const total = lines.reduce((n, li) => n + [...li].length, 0);
    const prog = Math.min(Math.max((t - L.rv.t0) / (L.rv.t1 - L.rv.t0), 0), 1) * total;
    c.textAlign = 'left';
    let k = 0;
    const base = c.globalAlpha;
    lines.forEach((li, i) => {
      const lw = c.measureText(li).width;
      const x0 = L.al === 'c' ? -lw / 2 : L.al === 'r' ? -lw : 0;
      const chars = [...li];
      let acc = '';
      for (const ch of chars) {
        const a = Math.min(Math.max(prog - k, 0), 1);
        if (a > 0) {
          c.globalAlpha = base * a;
          c.fillText(ch, x0 + c.measureText(acc).width, i * L.ld);
        }
        acc += ch;
        k++;
      }
    });
    c.globalAlpha = base;
  }

  function pathOf(it, t) {
    const P = new Path2D();
    if (it.t === 'rect') {
      const [w, h] = it.sz;
      const r = Math.min(it.rd || 0, w / 2, h / 2);
      P.roundRect(it.ps[0] - w / 2, it.ps[1] - h / 2, w, h, r);
      return P;
    }
    if (it.t === 'ell') {
      P.ellipse(it.ps[0], it.ps[1], it.sz[0] / 2, it.sz[1] / 2, 0, 0, Math.PI * 2);
      return P;
    }
    if (it.ti) {
      // bezier path (no trim support)
      const v = it.v;
      P.moveTo(v[0][0], v[0][1]);
      const n = v.length;
      for (let i = 1; i <= (it.cl ? n : n - 1); i++) {
        const a = v[i - 1];
        const b = v[i % n];
        const oa = it.to[i - 1];
        const ib = it.ti[i % n];
        P.bezierCurveTo(a[0] + oa[0], a[1] + oa[1], b[0] + ib[0], b[1] + ib[1], b[0], b[1]);
      }
      if (it.cl) P.closePath();
      return P;
    }
    // polyline with optional trim
    let v = it.v;
    if (it.cl) v = [...v, v[0]];
    let s = 0;
    let e = 100;
    if (it.tm) {
      s = typeof it.tm.s === 'number' ? it.tm.s : kfVal(it.tm.s, t, 0);
      e = typeof it.tm.e === 'number' ? it.tm.e : kfVal(it.tm.e, t, 100);
    }
    if (e <= s) return null;
    if (s === 0 && e === 100) {
      P.moveTo(v[0][0], v[0][1]);
      for (let i = 1; i < v.length; i++) P.lineTo(v[i][0], v[i][1]);
      if (it.cl) P.closePath();
      return P;
    }
    const seg = [];
    let len = 0;
    for (let i = 1; i < v.length; i++) {
      const d = Math.hypot(v[i][0] - v[i - 1][0], v[i][1] - v[i - 1][1]);
      seg.push(d);
      len += d;
    }
    const a = (len * s) / 100;
    const b = (len * e) / 100;
    let acc = 0;
    let started = false;
    for (let i = 1; i < v.length; i++) {
      const d = seg[i - 1];
      const s0 = acc;
      const s1 = acc + d;
      acc = s1;
      if (s1 < a || s0 > b || d === 0) continue;
      const u0 = Math.max(0, (a - s0) / d);
      const u1 = Math.min(1, (b - s0) / d);
      const x0 = v[i - 1][0] + (v[i][0] - v[i - 1][0]) * u0;
      const y0 = v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u0;
      const x1 = v[i - 1][0] + (v[i][0] - v[i - 1][0]) * u1;
      const y1 = v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u1;
      if (!started) {
        P.moveTo(x0, y0);
        started = true;
      }
      P.lineTo(x1, y1);
    }
    return P;
  }

  function drawShape(c, L, t) {
    for (const it of L.it) {
      const A = it.ga || (it.t === 'path' ? [0, 0] : it.ps);
      const gp = it.ge && it.ge.p ? evalExpr(it.ge.p, t) : kfVal(it.gkf && it.gkf.p, t, A);
      const gs = it.ge && it.ge.s ? evalExpr(it.ge.s, t) : kfVal(it.gkf && it.gkf.s, t, [100, 100]);
      const go = it.ge && it.ge.o ? evalExpr(it.ge.o, t) : kfVal(it.gkf && it.gkf.o, t, it.go ?? 100);
      const gr = it.ge && it.ge.r ? evalExpr(it.ge.r, t) : kfVal(it.gkf && it.gkf.r, t, 0);
      if (go <= 0 || gs[0] === 0 || gs[1] === 0) continue;
      const P = pathOf(it, t);
      if (!P) continue;
      c.save();
      c.globalAlpha *= go / 100;
      c.translate(gp[0], gp[1]);
      if (gr) c.rotate((gr * Math.PI) / 180);
      c.scale(gs[0] / 100, gs[1] / 100);
      c.translate(-A[0], -A[1]);
      if (it.fl) {
        c.fillStyle = hexA(it.fl.c, it.fl.o / 100);
        c.fill(P);
      }
      if (it.st) {
        c.strokeStyle = hexA(it.st.c, (it.st.o ?? 100) / 100);
        c.lineWidth = it.st.w;
        c.lineCap = it.st.cap === 'b' ? 'butt' : 'round';
        c.lineJoin = 'round';
        c.stroke(P);
      }
      c.restore();
    }
  }

  function drawRamp(c, L) {
    const [w, h] = L.sz;
    const r = L.rp;
    let g;
    if (r.t === 'rad') g = c.createRadialGradient(r.p1[0], r.p1[1], 0, r.p1[0], r.p1[1], Math.hypot(r.p2[0] - r.p1[0], r.p2[1] - r.p1[1]));
    else g = c.createLinearGradient(r.p1[0], r.p1[1], r.p2[0], r.p2[1]);
    g.addColorStop(0, r.c1);
    g.addColorStop(1, r.c2);
    c.fillStyle = g;
    c.fillRect(0, 0, w, h);
  }

  function drawComp(c, layers, t) {
    for (const L of layers) {
      if (t < L.in || t >= L.out) continue;
      drawLayer(c, L, t);
    }
  }

  function drawLayer(c, L, t) {
    let op = L.ex && L.ex.o ? evalExpr(L.ex.o, t) : kfVal(L.kf && L.kf.o, t, L.o ?? 100);
    if (op <= 0.01) return;
    op /= 100;
    if (L.k === 'adjust') {
      if (L.fx && L.fx.noise) {
        c.save();
        c.globalCompositeOperation = 'overlay';
        c.globalAlpha = Math.min(1, L.fx.noise * 0.04);
        const ox = Math.floor(Math.random() * 256);
        const oy = Math.floor(Math.random() * 256);
        c.translate(-ox, -oy);
        c.fillStyle = grainPat;
        c.fillRect(0, 0, W + 256, H + 256);
        c.restore();
      }
      return;
    }
    const nested = L.k === 'comp' || L.k === 'slot';
    const blur = L.fx ? (L.fx.blurKf ? kfVal(L.fx.blurKf, t, 0) : L.fx.blur || 0) : 0;
    const needsOff = nested || L.mt || blur > 0.3;
    if (!needsOff) {
      c.save();
      c.globalAlpha *= op;
      if (L.bl) c.globalCompositeOperation = BLEND[L.bl];
      transform(c, L, t);
      drawContent(c, L, t);
      c.restore();
      return;
    }
    let A = acquire();
    if (nested) {
      const src = L.k === 'comp' ? video.scenes[L.ref] : video.slots[L.ref];
      if (src && src.layers && src.layers.length) {
        const B = acquire();
        drawComp(B.ctx, src.layers, t - L.in);
        A.ctx.save();
        transform(A.ctx, L, t);
        const sw = src.w || W;
        const sh = src.h || H;
        A.ctx.drawImage(B.c, 0, 0, sw, sh, 0, 0, sw, sh);
        A.ctx.restore();
        release();
      }
    } else {
      A.ctx.save();
      transform(A.ctx, L, t);
      drawContent(A.ctx, L, t);
      A.ctx.restore();
    }
    if (blur > 0.3) {
      const B = acquire();
      B.ctx.filter = `blur(${blur / 2}px)`;
      B.ctx.drawImage(A.c, 0, 0);
      B.ctx.filter = 'none';
      A.ctx.clearRect(0, 0, W, H);
      A.ctx.drawImage(B.c, 0, 0);
      release();
    }
    if (L.mt) {
      const M = acquire();
      if (t >= (L.mt.in ?? 0) && t < (L.mt.out ?? 1e9)) drawLayer(M.ctx, L.mt, t);
      A.ctx.globalCompositeOperation = 'destination-in';
      A.ctx.drawImage(M.c, 0, 0);
      A.ctx.globalCompositeOperation = 'source-over';
      release();
    }
    c.save();
    c.globalAlpha *= op;
    if (L.bl) c.globalCompositeOperation = BLEND[L.bl];
    c.drawImage(A.c, 0, 0);
    c.restore();
    release();
  }

  // image layers fit inside L.fit (w, h) and are drawn centred on the anchor,
  // matching an AE footage layer whose scale is multiplied by the same factor
  function drawImageLayer(c, L) {
    const img = images[L.src];
    if (!img) return;
    const k = Math.min(L.fit[0] / img.naturalWidth, L.fit[1] / img.naturalHeight);
    const w = img.naturalWidth * k;
    const h = img.naturalHeight * k;
    c.drawImage(img, -w / 2, -h / 2, w, h);
  }

  function drawContent(c, L, t) {
    if (L.k === 'text') drawText(c, L, t);
    else if (L.k === 'shape') drawShape(c, L, t);
    else if (L.k === 'ramp') drawRamp(c, L);
    else if (L.k === 'img') drawImageLayer(c, L);
  }

  return {
    frame(t) {
      used = 0;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, W, H);
      drawComp(ctx, video.layers, t);
    },
  };
}
