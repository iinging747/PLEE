// Version C — "Elysium 런칭과 KNTQ 플라이휠" (under a minute). The wizard
// penguin explains the Elysium launch and the KNTQ buy pressure, following 코같투
// (@Edward__Park)'s post. Mechanisms are stated as planned designs; the 20%
// figure and the catalysts are the post author's own views and are labelled as
// such. Every point appears with a cast of the penguin's wand.
//
// `text` is the caption, `say` is what ElevenLabs reads.

import { C, W, H, assemble, logoSlot, timeline, rng, smooth, r2 } from '../engine/lib.js';

const X = 130; // content column
const X1 = 1180;
const PX = 1555; // penguin centre
const BOTTOM = 1095; // bust bottom sits just below the frame
const PH = 640; // penguin height
const STAR = '#F7A938'; // the hat's star orange
const NAVY = '#2C3592'; // the hat's navy

const SCRIPT = {
  hook: [
    { id: 'k01', text: '11월 최고 기대 이벤트, 바로 Elysium 런칭이에요.', say: '십일월 최고 기대 이벤트, 바로 엘리시움 런칭이에요.' },
    { id: 'k02', text: '하이퍼리퀴드 최대 LST 팀, Kinetiq의 L2죠.', say: '하이퍼리퀴드 최대 엘에스티 팀, 키네틱의 레이어 투죠.' },
  ],
  wheel: [
    { id: 'k03', text: '핵심은 바로 KNTQ 플라이휠.', say: '핵심은 바로 케이엔티큐 플라이휠.' },
    { id: 'k04', text: 'Elysium 시퀀서 수익의 절반으로 KNTQ를 사서, Assistance Fund로 보내 소각해요.', say: '엘리시움 시퀀서 수익의 절반으로 케이엔티큐를 사서, 어시스턴스 펀드로 보내 소각해요.' },
  ],
  scenario: [
    { id: 'k05', text: '가스비 상위권 L2가 되면 1년에 시총 약 20%를 사들일 수 있다는 계산도 있어요. 물론 낙관론이에요.', say: '가스비 상위권 레이어 투가 되면 일 년에 시총 약 이십 퍼센트를 사들일 수 있다는 계산도 있어요. 물론 낙관론이에요.' },
  ],
  ascend: [
    { id: 'k06', text: '런치패드 Ascend도 자체 토큰 없이 수익으로 KNTQ를 사요.', say: '런치패드 어센드도 자체 토큰 없이 수익으로 케이엔티큐를 사요.' },
    { id: 'k07', text: '생태계가 커질수록 KNTQ 매수도 커지는 구조죠.', say: '생태계가 커질수록 케이엔티큐 매수도 커지는 구조죠.' },
  ],
  watch: [{ id: 'k08', text: '큰손들의 언급, 추가 거래소 상장 가능성도 관전 포인트예요.' }],
  end: [{ id: 'k09', text: 'Elysium 메인넷은 11월 9일 예정! 투자 판단은 꼭 직접 하세요.', say: '엘리시움 메인넷은 십일월 구일 예정! 투자 판단은 꼭 직접 하세요.' }],
};

const at = (l, f = 0) => r2(l.t + l.dur * f);
const atw = (l, word, d = 0) => {
  const i = l.text.indexOf(word);
  return r2(l.t + (i < 0 ? 0 : (l.dur * i) / l.text.length) + d);
};
const until = (L, i) => (i + 1 < L.length ? r2(L[i + 1].t - 0.22) : undefined);
const keys = (arr) => {
  arr.sort((a, b) => a[0] - b[0]);
  for (const k of arr) k[0] = r2(k[0]);
  return arr.filter((k, i) => i === arr.length - 1 || arr[i + 1][0] > k[0]);
};

// 4-point star outline around the origin
const starPts = (r, k = 0.32) => {
  const v = [];
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4 - Math.PI / 2;
    const rr = i % 2 ? r * k : r;
    v.push([r2(rr * Math.cos(a)), r2(rr * Math.sin(a))]);
  }
  return v;
};

// A burst of sparkles flying out from (x, y) at time t.
function sparkles(k, S, x, y, t, o = {}) {
  const R = rng(Math.round(t * 100) + (o.seed || 1));
  const n = o.n || 9;
  const it = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + R() * 0.6;
    const d = (o.d || 120) * (0.6 + R() * 0.6);
    const sz = (o.sz || 18) * (0.6 + R() * 0.7);
    const t0 = r2(t + R() * 0.08);
    const to = [r2(x + Math.cos(a) * d), r2(y + Math.sin(a) * d)];
    it.push({
      t: 'path', v: starPts(sz), cl: true, fl: { c: i % 3 ? STAR : C.mint, o: 100 }, st: { c: '#1B1B22', w: 2.5, o: 100 }, ga: [0, 0],
      gkf: {
        p: [[t0, [x, y], 'x'], [r2(t0 + 0.7), to, 'l']],
        s: [[t0, [0, 0], 'o'], [r2(t0 + 0.18), [120, 120], 'io'], [r2(t0 + 0.55), [80, 80], 'i'], [r2(t0 + 0.75), [0, 0], 'l']],
        r: [[t0, 0, 'l'], [r2(t0 + 0.75), R() > 0.5 ? 120 : -120, 'l']],
      },
    });
  }
  k.shape(S, it, { n: 'sparkles', anim: 'none' }).top = true;
  S.cues.push({ t: r2(t), type: 'sparkle' });
}

// The wizard penguin bust (assets/characters/wizard_penguin.png, cut by
// engine/cut-penguin.py), mirrored to face the content, with a talking beak,
// breathing, a floating wand that casts, hops and tilts.
const PENG = { src: 'assets/characters/wizard_penguin.png', size: [574, 618], mouth: [358, 351] };
function penguin(k, S, o = {}) {
  const kk = PH / PENG.size[1];
  const u = `${S.id}_peng`;
  const base = { in: 0, out: S.dur, top: true };
  const root = { k: 'null', n: 'Penguin ROOT', id: u + '_root', a: [0, 0], p: [PX, BOTTOM], kf: {}, ...base };
  const flip = { k: 'null', n: 'Penguin FLIP (mirror)', id: u + '_flip', par: root.id, a: [0, 0], p: [0, 0], s: [-100, 100], ...base };
  const img = { k: 'img', n: 'Wizard penguin', src: PENG.src, fit: [r2(PENG.size[0] * kk), PH], pv: [0.5, 1], par: flip.id, p: [0, 0], ex: { s: { fn: 'breath', a: 0.7, f: 2.1 } }, ...base };
  const m = [r2((PENG.mouth[0] - PENG.size[0] / 2) * kk), r2((PENG.mouth[1] - PENG.size[1]) * kk)];
  const mouth = { t: 'ell', sz: [r2(30 * kk), r2(18 * kk)], ps: m, fl: { c: '#7A2E1D', o: 100 }, st: { c: '#1B1B22', w: r2(3 * kk), o: 100 }, ga: m, ge: { s: { fn: 'talk', w: [], f: 16 } } };
  const face = { k: 'shape', n: 'Penguin beak (talk)', par: flip.id, p: [0, 0], it: [mouth], ...base };
  // floating wand on the content side, pivoting at its handle
  const hb = [-300, -150];
  const tip = [-430, -420];
  const wandIt = [
    { t: 'path', v: [hb, tip], cl: false, st: { c: '#1B1B22', w: 20, o: 100, cap: 'r' } },
    { t: 'path', v: [hb, tip], cl: false, st: { c: '#8A5A2B', w: 11, o: 100, cap: 'r' } },
    { t: 'path', v: [[hb[0] - 6, hb[1] - 12], [hb[0] - 26, hb[1] - 52]], cl: false, st: { c: '#C9934F', w: 4, o: 100, cap: 'r' } },
    { t: 'path', v: starPts(34, 0.42), cl: true, ps: tip, fl: { c: STAR, o: 100 }, st: { c: '#1B1B22', w: 4, o: 100 }, ga: [0, 0], gkf: { p: [[0, tip, 'l']] }, ge: { r: { fn: 'sway', a: 14, f: 2.4, ph: 0 } } },
  ];
  const wand = { k: 'shape', n: 'Wand', par: root.id, a: hb, p: hb, it: wandIt, kf: {}, ...base, ex: undefined };
  const glow = { k: 'shape', n: 'Wand glow', par: root.id, a: [0, 0], p: [0, 0], it: [{ t: 'ell', sz: [90, 90], ps: tip, fl: { c: '#FFE7A8', o: 100 }, ge: { o: { fn: 'twinkle', base: 70, amp: 0.8, f: 5, ph: 0 } } }], fx: { blur: 18 }, ...base };
  S.layers.push(root, flip, glow, img, face, wand);

  const K = { p: [], s: [], r: [[0, 0, 'l']], w: [[0, 0, 'l']] };
  const P = [PX, BOTTOM];
  let tilt = 0;
  const api = {
    // wand tip in comp space (at rest)
    tip: () => [PX + tip[0], BOTTOM + tip[1]],
    enter(t) {
      K.p.push([r2(t), [PX, BOTTOM + PH + 60], 'x'], [r2(t + 0.5), [PX, BOTTOM - 22], 'io'], [r2(t + 0.72), P, 'l']);
      K.s.push([r2(t + 0.45), [100, 100], 'io'], [r2(t + 0.55), [104, 95], 'io'], [r2(t + 0.75), [100, 100], 'l']);
      return api;
    },
    hop(t, h = 30) {
      K.p.push([r2(t), P, 'l'], [r2(t + 0.06), P, 'o'], [r2(t + 0.22), [PX, BOTTOM - h], 'io'], [r2(t + 0.42), P, 'l']);
      K.s.push([r2(t), [100, 100], 'o'], [r2(t + 0.06), [106, 93], 'io'], [r2(t + 0.2), [96, 105], 'io'], [r2(t + 0.42), [103, 97], 'io'], [r2(t + 0.56), [100, 100], 'l']);
      return api;
    },
    tilt(t, d, dur = 0.3) {
      K.r.push([r2(t), tilt, 'o'], [r2(t + dur), d, 'l']);
      tilt = d;
      return api;
    },
    // flick the wand and throw sparkles at the content
    cast(t, o2 = {}) {
      K.w.push([r2(t - 0.25), 0, 'o'], [r2(t - 0.05), 16, 'io'], [r2(t + 0.12), -22, 'io'], [r2(t + 0.4), 4, 'io'], [r2(t + 0.6), 0, 'l']);
      const [tx, ty] = api.tip();
      sparkles(k, S, tx - 40, ty + 10, t, o2);
      api.tilt(t - 0.05, -5, 0.2).tilt(t + 0.35, 0, 0.35);
      return api;
    },
    talk(windows) {
      mouth.ge.s.w = windows.map(([a, b]) => [r2(a), r2(b)]);
      return api;
    },
    done() {
      if (K.p.length) root.kf.p = keys(K.p);
      if (K.s.length) root.kf.s = keys(K.s);
      root.kf.r = keys(K.r);
      wand.kf.r = keys(K.w);
      return api;
    },
  };
  return api;
}

// soft halo and a few ambient twinkles around the penguin
function stage(k, S) {
  k.shape(S, [{ t: 'ell', sz: [700, 700], ps: [PX, 760], fl: { c: C.mint, o: 34 } }], { n: 'halo', anim: 'none', fx: { blur: 60 } });
  const R = rng(5);
  const it = [];
  for (let i = 0; i < 7; i++) {
    const p = [r2(PX - 330 + R() * 660), r2(300 + R() * 380)];
    it.push({ t: 'path', v: starPts(8 + R() * 8), cl: true, fl: { c: i % 2 ? STAR : C.mint2, o: 100 }, ga: [0, 0], gkf: { p: [[0, p, 'l']] }, ge: { o: { fn: 'twinkle', base: 90, amp: 1.8, f: 2 + R() * 2, ph: R() * 6 } } });
  }
  k.shape(S, it, { n: 'ambient twinkles', anim: 'none' });
}

function shot(k, key, id, name, T, o = {}) {
  const tl = timeline(SCRIPT[key], T, { lead: o.lead ?? 0.55, gap: 0.3, tail: o.tail ?? 0.7 });
  const S = k.scene(id, name, tl.dur);
  const L = tl.lines;
  stage(k, S);
  const p = penguin(k, S);
  p.talk(L.map((l) => [l.t, l.t + l.dur]));
  k.say(S, L, { x: 655, y: 1012, sz: 30, maxChars: 30 });
  S.cues = [{ t: 0, type: 'whoosh' }];
  return { S, L, p };
}

const label = (k, S, str, y, t, ex, c) => k.label(S, str, X, y, { at: t, exit: ex, c: c || C.accent, sz: 22 });

function hook(k, T) {
  const { S, L, p } = shot(k, 'hook', 'c01', '01 November', T, { lead: 0.9 });
  p.enter(0.05).cast(0.75, { n: 12, d: 160 });
  let ex = until(L, 0);
  label(k, S, 'WEB3 · 11월 최대 기대 이벤트', 300, 0.8, ex);
  k.words(S, 'Elysium 런칭', X - 6, 450, { sz: 170, at: 0.85, colors: [C.accent, C.ink], exit: ex });
  k.text(S, 'MAINNET 2026.11.09 · 예정', X, 600, { f: 'mono', sz: 24, tr: 260, c: C.ink2, anim: 'chars', at: 1.3, exit: ex });
  const t = at(L[1], 0.02);
  p.cast(t);
  k.text(S, 'by Kinetiq', X - 6, 380, { f: 'en', w: 300, sz: 150, tr: -20, at: t, s0: 108 });
  k.pill(S, '하이퍼리퀴드 최대 LST · kHYPE', X, 540, { at: atw(L[1], 'LST', -0.2), sz: 30 });
  k.words(S, 'kHYPE 팀의 L2', X, 690, { sz: 84, at: atw(L[1], 'L2', -0.4), marks: [false, false, true] });
  p.done();
  return S;
}

function wheel(k, T) {
  const { S, L, p } = shot(k, 'wheel', 'c02', '02 KNTQ flywheel', T, { lead: 0.7 });
  // k03: the title card
  const t1 = until(L, 0);
  k.punch(S, 0, t1, { full: true });
  k.text(S, 'KNTQ', X - 10, 470, { f: 'en', w: 300, sz: 280, tr: -40, anim: 'rise', at: 0.15, exit: r2(t1 - 0.1) });
  k.words(S, 'FLYWHEEL', X, 660, { f: 'en', w: 500, sz: 72, tr: 320, at: 0.35, exit: r2(t1 - 0.1) });
  p.cast(0.5, { n: 12 });
  // k04: the wheel, each node lit as it is named
  const l = L[1];
  const cx = 600;
  const cy = 560;
  const R0 = 250;
  const ring = smooth(Array.from({ length: 16 }, (_, i) => [r2(cx + R0 * Math.cos((i / 16) * 2 * Math.PI - Math.PI / 2)), r2(cy + R0 * Math.sin((i / 16) * 2 * Math.PI - Math.PI / 2))]), true);
  k.shape(S, [{ t: 'path', ...ring, st: { c: C.ink, w: 3, o: 22 }, tm: { e: [[l.t, 0, 'x'], [r2(l.t + 1.0), 100, 'l']] } }], { n: 'ring', anim: 'none', at: l.t });
  // two arrowheads chasing round the ring
  const head = (a) => {
    const x = cx + R0 * Math.cos(a);
    const y = cy + R0 * Math.sin(a);
    const d = a + Math.PI / 2;
    const pt = (r, ang) => [r2(x + r * Math.cos(ang)), r2(y + r * Math.sin(ang))];
    return { t: 'path', v: [pt(18, d), pt(14, d + 2.4), pt(14, d - 2.4)], cl: true, fl: { c: C.accent, o: 100 } };
  };
  const spin = { k: 'shape', n: 'ring arrows', p: [cx, cy], a: [cx, cy], it: [head(-Math.PI / 2 + 0.6), head(Math.PI / 2 + 0.6)], in: r2(l.t + 0.6), out: S.dur, kf: { r: [[r2(l.t + 0.6), 0, 'l'], [S.dur, r2(((S.dur - l.t) * 360) / 4.5), 'l']], o: [[r2(l.t + 0.6), 0, 'l'], [r2(l.t + 0.9), 100, 'l']] } };
  S.layers.push(spin);
  const nodes = [
    ['Elysium 사용', '활동 · 가스', [cx, cy - R0], 'c', -70, 'Elysium'],
    ['시퀀서 수익', '', [cx + R0, cy], 'l', 0, '시퀀서'],
    ['50% → KNTQ 매수', '공개시장', [cx, cy + R0], 'c', 70, 'KNTQ를'],
    ['소각', 'Assistance Fund', [cx - R0, cy], 'r', 0, 'Assistance'],
  ];
  nodes.forEach(([a, b, [nx, ny], al, dy, w], i) => {
    const t = atw(l, w, -0.15);
    k.shape(S, [{ t: 'ell', sz: [30, 30], ps: [nx, ny], fl: { c: i === 2 ? C.accent : C.ink, o: 100 }, st: { c: C.white, w: 4, o: 100 } }], { anim: 'pop', a: [nx, ny], p: [nx, ny], at: t });
    const tx = al === 'l' ? nx + 36 : al === 'r' ? nx - 36 : nx;
    const ty = ny + dy;
    k.text(S, a, tx, ty, { f: 'krd', sz: i === 2 ? 44 : 38, tr: -25, c: i === 2 ? C.accent : C.ink, al: al === 'c' ? 'c' : al, anim: 'up', at: t });
    if (b) k.text(S, b, tx, ty + 42, { sz: 22, w: 600, c: C.ink2, al: al === 'c' ? 'c' : al, anim: 'fade', at: t + 0.15 });
  });
  p.cast(atw(l, 'KNTQ를', -0.1)).hop(atw(l, '소각', 0));
  p.done();
  return S;
}

function scenario(k, T) {
  const { S, L, p } = shot(k, 'scenario', 'c03', '03 Optimistic scenario', T, { tail: 0.8 });
  const l = L[0];
  label(k, S, 'SCENARIO · 원문 작성자 추산', 250, l.t);
  k.text(S, 'KNTQ 시총 약 $122M 기준 (작성 시점)', X, 330, { sz: 30, w: 600, c: C.ink2, anim: 'up', at: l.t + 0.1 });
  const t = atw(l, '1년에', -0.2);
  const big = { f: 'en', w: 300, sz: 260, tr: -50 };
  k.text(S, '~20%', X - 8, 520, { ...big, c: C.accent, at: t, s0: 110, b0: 34, counter: { t0: t, t1: t + 1.2, from: 0, to: 20, dec: 0, pre: '~', suf: '%' } });
  const sx = X + k.measure('~20%', big) + 40;
  k.text(S, '1년간 공개시장', sx, 455, { f: 'krd', sz: 48, tr: -25, anim: 'rise', at: t + 0.3 });
  k.text(S, '매수 가능 물량', sx, 520, { f: 'krd', sz: 48, tr: -25, anim: 'rise', at: t + 0.4 });
  k.text(S, '가정: Elysium이 월간 L2 가스비 Top 3', sx + 2, 590, { sz: 24, w: 600, c: C.ink2, anim: 'up', at: t + 0.55 });
  // supply bar with the 20% slice
  k.split(S, X, 720, 1000, [{ pct: 100, c: '#E3E6E1' }], { at: t, h: 22 });
  k.split(S, X, 720, 200, [{ pct: 100, c: C.mint2 }], { at: r2(t + 0.5), h: 22 });
  k.text(S, 'KNTQ 공급', X + 1000, 760, { sz: 20, w: 600, c: C.ink3, al: 'r', anim: 'fade', at: t + 0.2 });
  k.pill(S, '낙관 시나리오 · 확정 아님', X, 850, { at: atw(l, '물론', -0.1), sz: 26, fill: '#FFE3BF' });
  p.cast(t).tilt(atw(l, '물론'), 6).tilt(atw(l, '물론', 1.2), 0);
  p.done();
  return S;
}

function ascend(k, T) {
  const { S, L, p } = shot(k, 'ascend', 'c04', '04 Ascend', T);
  let ex = until(L, 0);
  const l = L[0];
  const t = atw(l, 'Ascend', -0.2);
  k.text(S, 'ASCEND', X - 8, 330, { f: 'en', w: 300, sz: 150, tr: 120, at: t, trFrom: 380, s0: 104, exit: ex });
  k.text(S, 'Elysium 위 큐레이팅 런치패드', X, 440, { f: 'krd', sz: 40, tr: -20, anim: 'up', at: t + 0.3, exit: ex, mark: true });
  [['자체 토큰 없음', '자체 토큰'], ['수익 → KNTQ 매수', '수익으로'], ['HyperCore Spot · Perp 성장 경로', 'KNTQ를 사요']].forEach(([s, w], i) => k.pill(S, s, X, 560 + i * 90, { at: atw(l, w, -0.1), sz: 28, fill: i === 1 ? C.mint : '#ECEFEA', exit: ex }));
  p.cast(t).cast(atw(l, '수익으로', 0));
  // k07: the loop in one line
  const l2 = L[1];
  k.words(S, '생태계가 커질수록', X, 400, { sz: 104, at: l2.t });
  k.words(S, 'KNTQ 매수도 커진다', X, 560, { sz: 104, at: atw(l2, 'KNTQ', -0.1), colors: [C.accent, C.ink, C.ink] });
  k.text(S, '= FLYWHEEL', X + 4, 700, { f: 'en', w: 500, sz: 44, tr: 260, c: C.ink2, anim: 'up', at: atw(l2, '구조', -0.2) });
  p.hop(atw(l2, 'KNTQ', 0)).cast(atw(l2, '구조', -0.1));
  p.done();
  return S;
}

function watch(k, T) {
  const { S, L, p } = shot(k, 'watch', 'c05', '05 What to watch', T, { tail: 0.8 });
  const l = L[0];
  label(k, S, '관전 포인트 · 원문 작성자의 기대 (확정 아님)', 230, l.t, undefined, C.amber);
  const cards = [['smartestmoney.hl', '등판할까?', '큰손들'], ['Ansem', '팔로업할까?', '언급'], ['추가 거래소', '상장될까?', '추가 거래소']];
  cards.forEach(([a, b, w], i) => {
    const t = atw(l, w, -0.1);
    const y = 360 + i * 175;
    k.shape(S, [{ t: 'rect', sz: [980, 140], ps: [X + 490, y], rd: 26, fl: { c: C.white, o: 100 }, st: { c: C.ink, w: 2, o: 14 } }], { anim: 'pop', a: [X + 490, y], p: [X + 490, y], at: t });
    k.text(S, '?', X + 70, y, { f: 'en', w: 400, sz: 90, c: STAR, al: 'c', anim: 'pop', at: t + 0.1 });
    k.text(S, a, X + 150, y - 14, { f: 'en', w: 500, sz: 48, tr: -10, anim: 'up', at: t + 0.12 });
    k.text(S, b, X + 150, y + 38, { sz: 26, w: 600, c: C.ink2, anim: 'up', at: t + 0.2 });
    p.cast(t + 0.05, { n: 7, d: 100 });
  });
  p.done();
  return S;
}

function end(k, T) {
  const { S, L, p } = shot(k, 'end', 'c06', '06 End card', T, { tail: 2.4 });
  const cx = 655;
  k.logo(S, cx, 330, 64, { at: 0.2 });
  k.horizon(S, 445, { at: 0.45, dur: 1.2, x0: cx - 420, x1: cx + 420, glow: 60 });
  k.label(S, 'MAINNET — SCHEDULED', cx, 520, { al: 'c', at: 0.8, tr: 400, sz: 20 });
  k.text(S, '2026.11.09', cx, 620, { f: 'en', w: 300, sz: 140, tr: 30, al: 'c', at: 0.95, trFrom: 280, s0: 106 });
  k.pill(S, 'KNTQ 플라이휠', cx, 745, { at: 1.3, sz: 28, al: 'c' });
  k.text(S, '참고: 코같투 (@Edward__Park) 님의 글', cx, 830, { sz: 22, w: 600, c: C.ink2, al: 'c', anim: 'fade', at: 1.5 });
  k.text(S, '정보 제공 목적이며 투자 권유가 아닙니다 · 수치는 작성 시점 기준의 추정·계획으로 변경될 수 있습니다', cx, 900, { sz: 18, w: 500, c: C.ink3, al: 'c', anim: 'fade', at: 1.7 });
  p.cast(0.25, { n: 14, d: 170 }).hop(atw(L[0], '예정', 0)).tilt(atw(L[0], '투자'), 7).tilt(atw(L[0], '투자', 1.0), 0);
  S.cues.push({ t: 0.15, type: 'boom' });
  p.done();
  return S;
}

export const STOCK = {};

export function build(k, timing) {
  const T = timing && timing.lines;
  const list = [hook, wheel, scenario, ascend, watch, end].map((f) => f(k, T));
  const dur = list.reduce((a, s) => a + s.dur, 0);
  const slots = { LOGO: logoSlot(k, dur) };
  return assemble({ id: 'kntq', name: 'Elysium_KNTQ_Flywheel_Penguin' }, list, slots, k, { push: 2, wipe: true });
}

export { SCRIPT, W, H };
