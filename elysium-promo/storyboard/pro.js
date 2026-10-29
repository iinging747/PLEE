// Version A — 전문가 · 커머셜 (41s @ 120 BPM). One statement per shot, hard
// cuts on the beat. Wording follows the brief's publishing rules: targets are
// "목표/사양", launch is "예정", revenue shares name their denominator.

import { C, W, BEAT, assemble, logoSlot, estimateDur, r2 } from '../engine/lib.js';

// Several differently coloured runs on one line, each its own masked layer.
function rich(k, S, parts, x, y, o = {}) {
  const sz = o.sz || 150;
  const tr = o.tr ?? -40;
  const widths = parts.map(([t]) => k.measure(t, { f: 'kr', w: 600, sz, tr }));
  const total = widths.reduce((a, b) => a + b, 0);
  let cx = o.al === 'c' ? x - total / 2 : x;
  parts.forEach(([t, c, mark], i) => {
    k.text(S, t, cx, y, { f: 'kr', sz, w: 600, tr, c, anim: 'rise', at: (o.at ?? 0.1) + i * (o.stagger ?? 0.08), mark, markAt: 0.5 });
    cx += widths[i];
  });
}

function bigNumber(k, S, str, unit, o) {
  const numO = { f: 'en', w: 300, sz: o.sz || 300, tr: -45 };
  const nw = k.measure(str, numO);
  const x = o.x ?? 150;
  if (o.count) k.text(S, str, x + nw, o.y, { ...numO, al: 'r', at: o.at, s0: 104, counter: { t0: o.at, t1: o.at + 1.3, from: 0, to: o.count, dec: 0, suf: o.suf || '' }, c: o.c });
  else k.text(S, str, x, o.y, { ...numO, at: o.at, s0: 104, c: o.c });
  if (unit) k.text(S, unit, x + nw + 24, o.y + numO.sz * 0.36, { f: 'mono', w: 400, sz: 56, c: C.accent, baseline: true, anim: 'up', at: o.at + 0.35 });
  return nw;
}

function speedLines(k, S, o = {}) {
  const it = [];
  for (let i = 0; i < 6; i++) {
    const y = 250 + i * 110;
    it.push({ t: 'rect', sz: [220 + ((i * 97) % 260), 1.5], ps: [0, 0], fl: { c: i % 3 ? C.ink : C.accent, o: i % 3 ? 12 : 35 }, ge: { p: { fn: 'flowX', x0: (i * 613) % 2400, v: -(1500 + ((i * 211) % 900)), span: 2400, off: 240, y } } });
  }
  k.shape(S, it, { n: 'speed lines', anim: 'fade', at: o.at ?? 0.2, op: o.op ?? 100 });
}

const scenes = {
  cold(k) {
    const S = k.scene('a01', '01 Cold open', DUR('a01'));
    k.horizon(S, 540, { at: 0.2, dur: 1.8 });
    k.text(S, 'A HYPERLIQUID L2 BY KINETIQ', 960, 488, { f: 'mono', w: 400, sz: 18, tr: 520, c: C.ink2, al: 'c', anim: 'chars', at: 1.1 });
    S.cues = [{ t: 0, type: 'riser', dur: 3.0 }];
    return S;
  },
  every(k) {
    const S = k.scene('a02', '02 Every millisecond', DUR('a02'));
    k.lines(S, ['모든 밀리초가'], 960, 540, { f: 'kr', w: 600, sz: 160, al: 'c', at: 0.08 });
    S.cues = [{ t: 0, type: 'impact' }];
    return S;
  },
  strategy(k) {
    const S = k.scene('a03', '03 Becomes strategy', DUR('a03'));
    rich(k, S, [['전략', C.ink, true], ['이 되는 곳.', C.ink]], 960, 540, { sz: 160, al: 'c', at: 0.08 });
    S.cues = [{ t: 0, type: 'hit' }];
    return S;
  },
  logo(k) {
    const S = k.scene('a04', '04 Logo', DUR('a04'));
    k.slot(S, 'PRO_LIGHT', { op: 30 });
    k.horizon(S, 640, { at: 0.05, dur: 1.0, x0: 360, x1: 1560 });
    k.logo(S, 960, 500, 100, { at: 0.15 });
    k.text(S, 'Hyperliquid 생태계를 위한 고성능 실행 L2', 960, 712, { sz: 32, w: 400, c: C.ink2, al: 'c', at: 1.0, s0: 103, b0: 16 });
    k.label(S, 'BY KINETIQ', 960, 770, { al: 'c', c: C.ink3, at: 1.5, tr: 400 });
    S.cues = [{ t: 0, type: 'boom' }];
    return S;
  },
  block(k) {
    const S = k.scene('a05', '05 Block time', DUR('a05'));
    k.label(S, 'BLOCK TIME — TARGET', 160, 300, { at: 0.05 });
    bigNumber(k, S, '100–200', 'ms', { y: 545, at: 0.1 });
    k.text(S, 'Canonical 블록 생성 목표 사양', 160, 770, { sz: 30, w: 400, c: C.ink2, anim: 'up', at: 0.45 });
    k.footnote(S, '참고 · HyperEVM fast block: 1초마다 최대 3M gas (블록당 한도) · 목표치는 메인넷 전 부하시험으로 검증 예정', { at: 0.7 });
    S.cues = [{ t: 0, type: 'hit' }];
    return S;
  },
  throughput(k) {
    const S = k.scene('a06', '06 Throughput', DUR('a06'));
    k.slot(S, 'PRO_SPEED', { op: 25 });
    speedLines(k, S, { at: 0.1 });
    k.label(S, 'EXECUTION THROUGHPUT — TARGET', 160, 300, { at: 0.05 });
    bigNumber(k, S, '300', 'Mgas/s', { y: 545, at: 0.1, count: 300 });
    k.text(S, '실행 처리량 목표', 160, 770, { sz: 30, w: 400, c: C.ink2, anim: 'up', at: 0.45 });
    k.footnote(S, '공식 사양상의 목표치이며 실측 성능이 아닙니다.', { at: 0.7 });
    S.cues = [{ t: 0, type: 'hit' }, { t: 0.1, type: 'ticks', dur: 1.3 }];
    return S;
  },
  gas(k) {
    const S = k.scene('a07', '07 Gas is HYPE', DUR('a07'));
    k.mintFrame(S);
    k.lines(S, ['가스는 HYPE.'], 160, 500, { f: 'kr', w: 600, sz: 180, c: C.ink, at: 0.06 });
    k.text(S, 'Native HYPE 1:1 브리지 · 가스용 신규 토큰 없음', 165, 690, { sz: 32, w: 500, c: C.ink, anim: 'up', at: 0.4 });
    S.cues = [{ t: 0, type: 'impact' }];
    return S;
  },
  settle(k) {
    const S = k.scene('a08', '08 Settles to HyperEVM', DUR('a08'));
    rich(k, S, [['정산은 ', C.ink], ['HyperEVM.', C.accent]], 160, 470, { sz: 150, at: 0.06 });
    k.label(S, 'ELYSIUM', 160, 730, { c: C.ink, at: 0.5, tr: 300 });
    k.line(S, [[420, 730], [1150, 730]], { c: C.ink, so: 40, at: 0.55, dur: 0.6 });
    k.shape(S, [{ t: 'ell', sz: [10, 10], ps: [0, 0], fl: { c: C.accent, o: 100 }, ge: { p: { fn: 'along', p0: [430, 730], p1: [1140, 730], v: 0.9, ph: 0 }, o: { fn: 'alongO', v: 0.9, ph: 0, base: 100 } } }], { n: 'settle pulse', at: 0.9 });
    k.label(S, 'HYPEREVM', 1185, 730, { at: 0.8, tr: 300 });
    k.text(S, 'L2 실행 결과를 HyperEVM에 최종 기록', 420, 790, { sz: 22, w: 400, c: C.ink2, anim: 'fade', at: 0.9 });
    S.cues = [{ t: 0, type: 'hit' }];
    return S;
  },
  value(k) {
    const S = k.scene('a09', '09 Value accrual', DUR('a09'));
    k.label(S, 'SEQUENCER REVENUE — PLANNED', 160, 290, { at: 0.05 });
    const nw = bigNumber(k, S, '50%', null, { y: 505, at: 0.1, count: 50, suf: '%', c: C.accent });
    k.text(S, '시퀀서 수익의 절반으로', 150 + nw + 70, 455, { sz: 36, w: 400, c: C.ink2, anim: 'up', at: 0.35 });
    k.text(S, 'KNTQ를 사서 소각합니다.', 150 + nw + 70, 532, { f: 'kr', sz: 64, w: 600, anim: 'rise', at: 0.45, mark: true });
    const segs = k.split(S, 160, 760, 1600, [
      { pct: 25, c: C.sky, label: '빌더 25%' },
      { pct: 25, c: C.kblue, label: '트레저리 25%' },
      { pct: 50, c: C.mint2, label: 'KNTQ 공개시장 매수 → 소각 50%' },
    ], { at: 0.8, stagger: 0.18 });
    for (const sg of segs) k.text(S, sg.label, sg.x, 805, { sz: 22, w: 500, c: sg.c === C.mint2 ? C.accent : sg.c, anim: 'fade', at: sg.t + 0.2 });
    k.footnote(S, '시퀀서 수익 기준의 예정 설계 (전체 가스비 기준 아님) · 시행 시점·실제 집행은 공식 공지를 확인하세요.', { at: 1.2 });
    S.cues = [{ t: 0, type: 'hit' }];
    return S;
  },
};

// four app shots share one layout; each gets its own line motif
const APPS = [
  { id: 'a10', name: 'ASCEND', desc: '토큰 출시부터 성장까지, 단계형 런치패드', tag: 'Launch → Ascended → HyperCore Spot → HIP-3 Perps · 자동 상장 보장 아님', motif: 'steps' },
  { id: 'a11', name: 'MONTRA', desc: '크리에이터 중심 토큰 런치패드', tag: '거래 수수료 설정 1–10% · 출시 시점 크리에이터 몫 60–96%', motif: 'rays' },
  { id: 'a12', name: 'NEST', desc: 've(3,3) AMM · 유동성 · 투표 시장', tag: 'veNEST로 배출량 투표 · 최대 6개월 락업', motif: 'rings' },
  { id: 'a13', name: 'ELOSCAPE', desc: '60초 라운드의 게임화 온체인 채굴', tag: 'ELO 최대 300만 개 · 미출시 · 낙첨 시 원금 손실 가능', motif: 'grid' },
];

function motif(k, S, kind) {
  const cx = 1560;
  const cy = 540;
  if (kind === 'steps') {
    const pts = [[1360, 720], [1460, 720], [1460, 620], [1560, 620], [1560, 520], [1660, 520], [1660, 420], [1760, 420]];
    k.line(S, pts, { c: C.accent, sw: 3, at: 0.25, dur: 1.2 });
    [[1460, 720], [1560, 620], [1660, 520], [1760, 420]].forEach((q, i) => k.shape(S, [{ t: 'ell', sz: [14, 14], ps: q, fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: q, p: q, at: 0.45 + i * 0.22 }));
  } else if (kind === 'rays') {
    const it = [];
    for (let i = 0; i < 18; i++) {
      const a = (i * 20 * Math.PI) / 180;
      const r1 = i % 2 ? 150 : 210;
      it.push({ t: 'path', v: [[r2(cx + 46 * Math.cos(a)), r2(cy + 46 * Math.sin(a))], [r2(cx + r1 * Math.cos(a)), r2(cy + r1 * Math.sin(a))]], cl: false, st: { c: i % 3 ? C.ink : C.accent, w: 2.5, o: i % 3 ? 35 : 100, cap: 'r' }, tm: { e: [[r2(0.25 + i * 0.03), 0, 'x'], [r2(0.95 + i * 0.03), 100, 'l']] } });
    }
    k.shape(S, it, { n: 'rays', anim: 'none' });
    k.shape(S, [{ t: 'ell', sz: [20, 20], ps: [cx, cy], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [cx, cy], p: [cx, cy], at: 0.2 });
  } else if (kind === 'rings') {
    const it = [60, 110, 160, 210].map((r, i) => ({ t: 'ell', sz: [r * 2, r * 2], ps: [cx, cy], st: { c: i === 0 ? C.accent : C.ink, w: 2.5, o: 90 - i * 22 }, gkf: { s: [[r2(0.2 + i * 0.12), [0, 0], 'x'], [r2(1.0 + i * 0.12), [100, 100], 'l']] } }));
    k.shape(S, it, { n: 'rings', anim: 'none' });
    k.shape(S, [{ t: 'ell', sz: [16, 16], ps: [cx, cy], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [cx, cy], p: [cx, cy], at: 0.15 });
  } else {
    const dots = [];
    const hi = [];
    const wins = [[1, 3, 0.45], [3, 1, 1.0], [2, 4, 1.5]];
    for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) dots.push({ t: 'ell', sz: [10, 10], ps: [cx - 140 + c * 70, cy - 140 + r * 70], fl: { c: C.ink, o: 30 }, gkf: { o: [[r2(0.15 + (r + c) * 0.03), 0, 'so'], [r2(0.4 + (r + c) * 0.03), 100, 'l']] } });
    for (const [r, c, t] of wins) hi.push({ t: 'ell', sz: [30, 30], ps: [cx - 140 + c * 70, cy - 140 + r * 70], fl: { c: C.accent, o: 100 }, gkf: { s: [[t, [0, 0], 'x'], [r2(t + 0.3), [100, 100], 'io'], [r2(t + 0.42), [100, 100], 'i'], [r2(t + 0.55), [35, 35], 'l']] } });
    k.shape(S, dots, { n: 'dot grid', anim: 'none' });
    k.shape(S, hi, { n: 'winner glow', anim: 'none', fx: { blur: 18 }, op: 50 });
    k.shape(S, hi, { n: 'winners', anim: 'none' });
  }
}

function app(k, a, i) {
  const S = k.scene(a.id, `${10 + i} ${a.name}`, DUR(a.id));
  k.label(S, `0${i + 1} / 04 — ECOSYSTEM`, 160, 300, { at: 0.03 });
  k.text(S, a.name, 150, 520, { f: 'en', w: 300, sz: 190, tr: 140, at: 0.05, trFrom: 420, s0: 103, maxW: 1180 });
  k.text(S, a.desc, 160, 690, { sz: 40, w: 500, anim: 'up', at: 0.3 });
  k.text(S, a.tag, 160, 752, { sz: 22, w: 400, c: C.ink2, anim: 'fade', at: 0.5, maxW: 1150 });
  motif(k, S, a.motif);
  if (i === 3) k.footnote(S, '앱별 내용은 제공 브리프 기준 · 네트워크 지원·가동 여부와 보상 조건은 각 공식 채널에서 확인', { at: 0.6 });
  S.cues = [{ t: 0, type: i === 0 ? 'impact' : 'hit' }];
  return S;
}

function core(k) {
  const S = k.scene('a14', '14 HyperCore', DUR('a14'));
  k.label(S, 'NEXT — HYPERCORE CONNECTION', 160, 290, { at: 0.05 });
  k.lines(S, ['HyperCore로 이어지는', '다음 단계.'], 160, 470, { f: 'kr', w: 600, sz: 120, at: 0.08, colors: [C.ink, C.accent] });
  const y = 760;
  k.label(S, 'ELYSIUM', 160, y, { c: C.ink, at: 0.6, tr: 300 });
  k.line(S, [[420, y], [1150, y]], { c: C.ink, so: 40, at: 0.6, dur: 0.6 });
  const pulse = (p0, p1, c, ph) => ({ t: 'ell', sz: [10, 10], ps: [0, 0], fl: { c, o: 100 }, ge: { p: { fn: 'along', p0, p1, v: 0.8, ph }, o: { fn: 'alongO', v: 0.8, ph, base: 100 } } });
  k.shape(S, [pulse([1140, y], [430, y], C.sky, 0), pulse([430, y], [1140, y], C.accent, 0.5)], { n: 'read/write pulses', at: 1.0 });
  k.label(S, 'HYPERCORE', 1185, y, { at: 0.8, tr: 300 });
  k.text(S, '← READ  시장 데이터 조회', 420, y - 42, { sz: 22, w: 600, c: C.kblue, anim: 'fade', at: 1.0 });
  k.text(S, 'WRITE  keeper 거래 전달 →', 1150, y + 44, { sz: 22, w: 600, c: C.accent, al: 'r', anim: 'fade', at: 1.1 });
  k.footnote(S, '메인넷 약 4주 뒤 read precompile · keeper write 업그레이드 계획 · 비동기 처리, 양 체인 원자성 없음', { at: 1.2 });
  S.cues = [{ t: 0, type: 'hit' }];
  return S;
}

function end(k) {
  const S = k.scene('a15', '15 End card', DUR('a15'));
  k.slot(S, 'PRO_LIGHT', { op: 30 });
  k.logo(S, 960, 420, 80, { at: 0.15 });
  k.horizon(S, 560, { at: 0.4, dur: 1.4, x0: 560, x1: 1360, glow: 55 });
  k.label(S, 'MAINNET — SCHEDULED', 960, 640, { al: 'c', at: 0.9, tr: 400 });
  k.text(S, '2026.11.09', 960, 735, { f: 'en', w: 300, sz: 130, tr: 30, al: 'c', at: 1.05, trFrom: 260, s0: 104 });
  k.label(S, 'TESTNET LIVE · CHAIN ID 99801', 960, 830, { al: 'c', c: C.ink2, at: 1.6, tr: 300 });
  k.footnote(S, '본 영상은 정보 제공 목적이며 투자 권유가 아닙니다 · 수치는 공개 자료 기준의 목표·계획으로 변경될 수 있습니다', { x: W / 2, al: 'c', at: 1.8 });
  S.cues = [{ t: 0, type: 'boom' }];
  return S;
}

export const STOCK = {
  PRO_LIGHT: { desc: '추상 라이트 · 렌즈 플레어 (로고/엔딩 배경)', search: ['dark abstract light leak', 'anamorphic lens flare black background', 'light rays dark'], dur: 8 },
  PRO_SPEED: { desc: '라이트 트레일 · 고속 모션 (처리량 장면)', search: ['light trails highway night', 'fast tunnel lights', 'speed lines abstract'], dur: 4 },
};

// Expert voice-over (ElevenLabs). Each line starts `at` seconds into its shot;
// if the real (or estimated) line is longer than the shots it spans, the last
// shot of the span is extended by whole beats so cuts stay on the grid.
const BASE = { a01: 3, a02: 2, a03: 2, a04: 4, a05: 2.5, a06: 2.5, a07: 2, a08: 2.5, a09: 3.5, a10: 2, a11: 2, a12: 2, a13: 2, a14: 3, a15: 6 };
export const VO = [
  { id: 'p01', scene: 'a02', span: ['a02', 'a03'], at: 0.25, text: '시장에서는, 밀리초가 곧 전략입니다.' },
  { id: 'p02', scene: 'a04', at: 0.3, text: 'Elysium. Hyperliquid를 위한 고성능 실행 레이어입니다.', say: '엘리시움. 하이퍼리퀴드를 위한 고성능 실행 레이어입니다.' },
  { id: 'p03', scene: 'a05', span: ['a05', 'a06'], at: 0.2, text: '블록 생성 목표는 100에서 200밀리초, 처리량 목표는 초당 300메가가스입니다.', say: '블록 생성 목표는 백에서 이백 밀리초, 처리량 목표는 초당 삼백 메가가스입니다.' },
  { id: 'p04', scene: 'a07', span: ['a07', 'a08'], at: 0.15, text: '가스는 HYPE로, 정산은 HyperEVM에서 이뤄집니다.', say: '가스는 하이프로, 정산은 하이퍼 이브이엠에서 이뤄집니다.' },
  { id: 'p05', scene: 'a09', at: 0.2, text: '시퀀서 수익의 절반은 KNTQ 매수와 소각에 쓰일 계획입니다.', say: '시퀀서 수익의 절반은 케이엔티큐 매수와 소각에 쓰일 계획입니다.' },
  { id: 'p06', scene: 'a10', at: 0.15, text: '토큰 성장의 사다리, Ascend.', say: '토큰 성장의 사다리, 어센드.' },
  { id: 'p07', scene: 'a11', at: 0.15, text: '크리에이터 런치패드, Montra.', say: '크리에이터 런치패드, 몬트라.' },
  { id: 'p08', scene: 'a12', at: 0.15, text: '유동성과 투표의 허브, Nest.', say: '유동성과 투표의 허브, 네스트.' },
  { id: 'p09', scene: 'a13', at: 0.15, text: '게임화된 채굴, Eloscape.', say: '게임화된 채굴, 엘로스케이프.' },
  { id: 'p10', scene: 'a14', at: 0.2, text: 'HyperCore와의 연결은 메인넷 이후 단계적으로 확장될 계획입니다.', say: '하이퍼코어와의 연결은 메인넷 이후 단계적으로 확장될 계획입니다.' },
  { id: 'p11', scene: 'a15', at: 0.6, text: 'Elysium 메인넷, 2026년 11월 9일 출시 예정입니다.', say: '엘리시움 메인넷, 이천이십육 년 십일 월 구 일 출시 예정입니다.' },
];
let DUR = (id) => BASE[id];

function timeVO(timing) {
  const extra = {};
  const lines = VO.map((l) => {
    const dur = (timing && timing[l.id]) || estimateDur(l.say || l.text, 6.6);
    const span = l.span || [l.scene];
    const room = span.reduce((a, s) => a + BASE[s], 0);
    const need = l.at + dur + 0.3 - room;
    const last = span[span.length - 1];
    if (need > 0) extra[last] = Math.max(extra[last] || 0, Math.ceil(need / BEAT) * BEAT);
    return { ...l, dur: r2(dur), t: l.at };
  });
  DUR = (id) => BASE[id] + (extra[id] || 0);
  return lines;
}

export function build(k, timing) {
  const lines = timeVO(timing && timing.lines);
  const list = [scenes.cold(k), scenes.every(k), scenes.strategy(k), scenes.logo(k), scenes.block(k), scenes.throughput(k), scenes.gas(k), scenes.settle(k), scenes.value(k), ...APPS.map((a, i) => app(k, a, i)), core(k), end(k)];
  for (const S of list) k.vo(S, lines.filter((l) => l.scene === S.id));
  const dur = list.reduce((a, s) => a + s.dur, 0);
  const slots = { LOGO: logoSlot(k, dur) };
  for (const [id, m] of Object.entries(STOCK)) slots[id] = { name: 'STOCK_' + id, kind: 'stock', w: 1920, h: 1080, ...m, layers: [] };
  return assemble({ id: 'pro', name: 'Elysium_Pro_Commercial' }, list, slots, k, { push: 3 });
}
