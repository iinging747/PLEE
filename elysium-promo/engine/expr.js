// Procedural motion used by background/fx layers. Each spec has one formula
// written twice: evalExpr() for the canvas preview, aeExpr() emitting the same
// math as an After Effects expression (works in the Legacy and JS engines).

const fmt = (n) => {
  const v = Math.round(n * 1000) / 1000;
  return v < 0 ? `(${v})` : String(v); // parenthesise so "a-" + "-5" never becomes "a--5"
};

export function evalExpr(e, t) {
  const S = Math.sin;
  const Cs = Math.cos;
  const wrap = (x, m) => ((x % m) + m) % m;
  switch (e.fn) {
    case 'drift':
      return [e.base[0] + e.a[0] * S(t * e.f[0] + e.ph[0]), e.base[1] + e.a[1] * Cs(t * e.f[1] + e.ph[1])];
    case 'flowX':
      return [wrap(e.x0 + e.v * t, e.span) - e.off, e.y];
    case 'riseY':
      return [e.x0 + e.amp * S(t * e.f + e.ph), wrap(e.y0 - e.v * t, e.Hh) - 20];
    case 'twinkle':
      return e.base * (1 - e.amp / 2 + (e.amp / 2) * S(t * e.f + e.ph));
    case 'progress':
      return [Math.min(Math.max(t / e.dur, 0), 1) * 100, 100];
    case 'along': {
      const fr = wrap(t * e.v + e.ph, 1);
      return [e.p0[0] + (e.p1[0] - e.p0[0]) * fr, e.p0[1] + (e.p1[1] - e.p0[1]) * fr];
    }
    case 'alongO': {
      const fr = wrap(t * e.v + e.ph, 1);
      return e.base * S(Math.PI * fr);
    }
    case 'oscS':
      return [e.b + e.a * S(t * e.f + e.ph), 100];
    case 'pulse':
      return e.base * (0.55 + 0.45 * S(t * e.f));
    case 'bob':
      return [e.base[0], e.base[1] + e.a * S(t * e.f + e.ph)];
    case 'blink':
      return [100, wrap(t + e.ph, e.per) < 0.12 ? 10 : 100];
    case 'talk': {
      let on = 0;
      for (const [a, b] of e.w) if (t >= a && t < b) on = 1;
      return [100, on * (35 + 75 * Math.abs(S(t * e.f)))];
    }
    case 'sway':
      return e.a * S(t * e.f + e.ph);
    default:
      throw new Error('unknown expr ' + e.fn);
  }
}

export function aeExpr(e) {
  const W = (x, m) => `((${x})%${m}+${m})%${m}`;
  switch (e.fn) {
    case 'drift':
      return `[${fmt(e.base[0])}+${fmt(e.a[0])}*Math.sin(time*${fmt(e.f[0])}+${fmt(e.ph[0])}), ${fmt(e.base[1])}+${fmt(e.a[1])}*Math.cos(time*${fmt(e.f[1])}+${fmt(e.ph[1])})]`;
    case 'flowX':
      return `[${W(`${fmt(e.x0)}+${fmt(e.v)}*time`, fmt(e.span))}-${fmt(e.off)}, ${fmt(e.y)}]`;
    case 'riseY':
      return `[${fmt(e.x0)}+${fmt(e.amp)}*Math.sin(time*${fmt(e.f)}+${fmt(e.ph)}), ${W(`${fmt(e.y0)}-${fmt(e.v)}*time`, fmt(e.Hh))}-20]`;
    case 'twinkle':
      return `${fmt(e.base)}*(1-${fmt(e.amp / 2)}+${fmt(e.amp / 2)}*Math.sin(time*${fmt(e.f)}+${fmt(e.ph)}))`;
    case 'progress':
      return `[Math.min(Math.max(time/${fmt(e.dur)},0),1)*100, 100]`;
    case 'along':
      return `var fr=${W(`time*${fmt(e.v)}+${fmt(e.ph)}`, 1)}; [${fmt(e.p0[0])}+${fmt(e.p1[0] - e.p0[0])}*fr, ${fmt(e.p0[1])}+${fmt(e.p1[1] - e.p0[1])}*fr]`;
    case 'alongO':
      return `var fr=${W(`time*${fmt(e.v)}+${fmt(e.ph)}`, 1)}; ${fmt(e.base)}*Math.sin(Math.PI*fr)`;
    case 'oscS':
      return `[${fmt(e.b)}+${fmt(e.a)}*Math.sin(time*${fmt(e.f)}+${fmt(e.ph)}), 100]`;
    case 'pulse':
      return `${fmt(e.base)}*(0.55+0.45*Math.sin(time*${fmt(e.f)}))`;
    case 'bob':
      return `[${fmt(e.base[0])}, ${fmt(e.base[1])}+${fmt(e.a)}*Math.sin(time*${fmt(e.f)}+${fmt(e.ph)})]`;
    case 'blink':
      return `[100, ${W(`time+${fmt(e.ph)}`, fmt(e.per))}<0.12?10:100]`;
    case 'talk':
      return `var w=${JSON.stringify(e.w)}; var on=0; for (var i=0;i<w.length;i++){ if (time>=w[i][0] && time<w[i][1]) on=1; } [100, on*(35+75*Math.abs(Math.sin(time*${fmt(e.f)})))]`;
    case 'sway':
      return `${fmt(e.a)}*Math.sin(time*${fmt(e.f)}+${fmt(e.ph)})`;
    default:
      throw new Error('unknown expr ' + e.fn);
  }
}

// Counter text (shared by both back ends): ease-out-quart from `from` to `to`.
export function counterValue(c, t) {
  let x = (t - c.t0) / (c.t1 - c.t0);
  x = x < 0 ? 0 : x > 1 ? 1 : x;
  const v = c.from + (c.to - c.from) * (c.lin ? x : 1 - Math.pow(1 - x, 4));
  return (c.pre || '') + v.toFixed(c.dec || 0) + (c.suf || '');
}

export function counterAE(c) {
  const q = (s) => JSON.stringify(s || '');
  return `var x=(time-${fmt(c.t0)})/${fmt(c.t1 - c.t0)}; x=x<0?0:(x>1?1:x); var v=${fmt(c.from)}+${fmt(c.to - c.from)}*${c.lin ? 'x' : '(1-Math.pow(1-x,4))'}; ${q(c.pre)}+v.toFixed(${c.dec || 0})+${q(c.suf)}`;
}
