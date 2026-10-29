// Version B — 초보자 (beginner). The provided Hypurr character explains one
// idea per shot, step by step. Shot lengths follow the narration: line
// durations come from dist/audio/narration_easy.json (written by
// engine/elevenlabs.mjs) when present, otherwise from a reading-speed estimate.
//
// `text` is the on-screen caption, `say` is what ElevenLabs reads (Korean
// pronunciation for tickers and English names).

import { C, W, assemble, logoSlot, mascot, timeline, r2 } from '../engine/lib.js';

const X = 760; // content column (the narrator stands on the left)
const GROUND = 885;
const CAT_X = 410;

const SCRIPT = {
  e01: [
    { id: 'n01', text: '안녕하세요! 오늘은 Elysium을 쉽게 알려드릴게요.', say: '안녕하세요! 오늘은 엘리시움을 쉽게 알려드릴게요.' },
    { id: 'n02', text: 'Elysium은 Hyperliquid 생태계에 새로 준비 중인 L2예요.', say: '엘리시움은 하이퍼리퀴드 생태계에 새로 준비 중인 레이어 투예요.' },
  ],
  e02: [
    { id: 'n03', text: 'L2는 쉽게 말해, 큰 도로 옆에 새로 낸 전용 고속 차선이에요.', say: '레이어 투는 쉽게 말해, 큰 도로 옆에 새로 낸 전용 고속 차선이에요.' },
    { id: 'n04', text: '속도가 특히 중요한 앱들이 이 차선을 달리게 돼요.' },
  ],
  e03: [
    { id: 'n05', text: '어떤 앱이냐면요, 사고팔 가격을 계속 내놓는 시장조성,' },
    { id: 'n06', text: '전문 전략으로 가격을 맞추는 PropAMM, 빠른 반응이 중요한 DeFi 앱이에요.', say: '전문 전략으로 가격을 맞추는 프랍 에이엠엠, 빠른 반응이 중요한 디파이 앱이에요.' },
  ],
  e04: [
    { id: 'n07', text: '목표 속도는 블록 하나에 0.1초에서 0.2초.', say: '목표 속도는 블록 하나에 영 점 일 초에서 영 점 이 초.' },
    { id: 'n08', text: '눈 한 번 깜빡이는 정도예요. 물론 아직은 목표치예요.' },
  ],
  e05: [
    { id: 'n09', text: '통행료인 가스는 HYPE로 내요. 새 토큰이 필요 없어요.', say: '통행료인 가스는 하이프로 내요. 새 토큰이 필요 없어요.' },
    { id: 'n10', text: '다만 HYPE를 옮기기만 한다고 스테이킹 수익이 생기진 않아요.', say: '다만 하이프를 옮기기만 한다고 스테이킹 수익이 생기진 않아요.' },
  ],
  e06: [{ id: 'n11', text: '그리고 Elysium에서 처리한 결과는 HyperEVM에 최종 기록돼요.', say: '그리고 엘리시움에서 처리한 결과는 하이퍼 이브이엠에 최종 기록돼요.' }],
  e07: [
    { id: 'n12', text: '이 길에서 생긴 시퀀서 수익은 이렇게 나눌 계획이에요.' },
    { id: 'n13', text: '25%는 앱을 만드는 빌더에게, 25%는 운영 금고에,', say: '이십오 퍼센트는 앱을 만드는 빌더에게, 이십오 퍼센트는 운영 금고에,' },
    { id: 'n14', text: '그리고 50%로는 KNTQ를 사서 소각해요.', say: '그리고 오십 퍼센트로는 케이엔티큐를 사서 소각해요.' },
  ],
  e08: [{ id: 'n15', text: 'Elysium 위에는 이런 앱 네 가지가 준비되고 있어요.', say: '엘리시움 위에는 이런 앱 네 가지가 준비되고 있어요.' }],
  e09: [
    { id: 'n16', text: 'Ascend는 토큰이 출시부터 성장까지 한 계단씩 올라가도록 돕는 런치패드예요.', say: '어센드는 토큰이 출시부터 성장까지 한 계단씩 올라가도록 돕는 런치패드예요.' },
    { id: 'n17', text: '다만 다음 단계로의 상장이 자동으로 보장되진 않아요.' },
  ],
  e10: [
    { id: 'n18', text: 'Montra는 크리에이터를 위한 토큰 발행소예요.', say: '몬트라는 크리에이터를 위한 토큰 발행소예요.' },
    { id: 'n19', text: '출시 시점엔 거래 수수료의 60에서 96%가 크리에이터 몫이에요.', say: '출시 시점엔 거래 수수료의 육십에서 구십육 퍼센트가 크리에이터 몫이에요.' },
  ],
  e11: [
    { id: 'n20', text: 'Nest는 토큰을 바꾸고, 유동성을 공급하고, 락업해서 투표하는 거래소예요.', say: '네스트는 토큰을 바꾸고, 유동성을 공급하고, 락업해서 투표하는 거래소예요.' },
    { id: 'n21', text: 'veNEST는 최대 6개월까지 묶일 수 있어요.', say: '브이이 네스트는 최대 육 개월까지 묶일 수 있어요.' },
  ],
  e12: [
    { id: 'n22', text: 'Eloscape는 게임처럼 하는 채굴이에요. 25칸 중 한 칸에 HYPE를 넣으면,', say: '엘로스케이프는 게임처럼 하는 채굴이에요. 이십오 칸 중 한 칸에 하이프를 넣으면,' },
    { id: 'n23', text: '60초마다 한 칸이 당첨돼요. 떨어진 칸의 HYPE는 잃을 수 있어요.', say: '육십 초마다 한 칸이 당첨돼요. 떨어진 칸의 하이프는 잃을 수 있어요.' },
  ],
  e13: [
    { id: 'n24', text: '마지막으로 꼭 기억하세요. 목표와 계획은 결과가 아니고,' },
    { id: 'n25', text: '보상과 수익은 보장되지 않아요. 참여는 공식 채널에서만 확인하세요.' },
  ],
  e14: [{ id: 'n26', text: 'Elysium 메인넷은 2026년 11월 9일 출시 예정이에요. 고마워요!', say: '엘리시움 메인넷은 이천이십육 년 십일 월 구 일 출시 예정이에요. 고마워요!' }],
};

// shared shot setup: timing, ground line, narrator, captions
function shot(k, id, name, timing, o = {}) {
  const tl = timeline(SCRIPT[id], timing, { lead: o.lead ?? 0.5, tail: o.tail ?? 0.8, min: o.min });
  const S = k.scene(id, name, tl.dur);
  const L = tl.lines;
  // soft mint halo behind the narrator
  k.shape(S, [{ t: 'ell', sz: [560, 560], ps: [CAT_X, 640], fl: { c: C.mint, o: 30 } }], { n: 'halo', anim: o.drawGround ? 'scale' : 'none', a: [CAT_X, 640], p: [CAT_X, 640], at: 0.05, fx: { blur: 40 } });
  const fig = mascot(k, S, CAT_X, GROUND, 470, { flip: true });
  fig.talk(L.map((l) => [l.t, l.t + l.dur]));
  k.say(S, L);
  S.cues = [{ t: 0, type: 'whoosh' }];
  return { S, L, fig, end: () => fig.pose(S.dur - 0.45, 'idle', 0.3).done() };
}
const at = (l, f = 0) => r2(l.t + l.dur * f);

function e01(k, T) {
  const { S, L, fig, end } = shot(k, 'e01', '01 Hello', T, { drawGround: true, lead: 1.6 });
  fig.enter(0.1, 1.3, -180);
  fig.wave(at(L[0], 0.05), 3);
  fig.pose(at(L[1], 0.1), 'present');
  k.logo(S, 1260, 450, 62, { at: at(L[0], 0.3) });
  k.label(S, 'A HYPERLIQUID L2 BY KINETIQ', 1260, 560, { al: 'c', c: C.ink2, at: at(L[1], 0.1), tr: 360 });
  end();
  return S;
}

function e02(k, T) {
  const { S, L, fig, end } = shot(k, 'e02', '02 Express lane', T);
  fig.pose(at(L[0], 0.3), 'point');
  k.label(S, 'L2 = 전용 고속 차선', X, 250, { at: 0.2, c: C.accent, sz: 24 });
  k.lines(S, ['큰 도로 옆,', '새로 낸 고속 차선'], X, 360, { f: 'krd', sz: 80, at: at(L[0], 0.35), marks: [false, true] });
  const lanes = [500, 580, 680];
  lanes.forEach((y, i) => k.line(S, [[X, y], [1760, y]], { c: i === 2 ? C.accent : C.ink, so: i === 2 ? 60 : 18, at: 0.3 + i * 0.1, dur: 0.8 }));
  k.label(S, 'HYPEREVM', X, 466, { c: C.ink3, at: 0.6 });
  k.label(S, 'ELYSIUM L2', X, 646, { c: C.accent, at: at(L[0], 0.6) });
  const slow = [];
  const span = 1760 - X;
  for (const y of [500, 580]) for (let i = 0; i < 6; i++) slow.push({ t: 'ell', sz: [14, 14], ps: [0, 0], fl: { c: C.ink3, o: 60 }, ge: { p: { fn: 'flowX', x0: r2(i * (span / 6) + (y === 580 ? 80 : 0)), v: 90, span, off: -X, y } } });
  k.shape(S, slow, { n: 'slow traffic', at: 0.6 });
  const fast = [];
  for (let i = 0; i < 3; i++) {
    const ge = { p: { fn: 'flowX', x0: i * ((span - 160) / 3), v: 900, span: span - 160, off: -X - 160, y: 680 } };
    fast.push({ t: 'rect', sz: [150, 4], ps: [-80, 0], ga: [0, 0], rd: 2, fl: { c: C.mint2, o: 70 }, ge }, { t: 'ell', sz: [18, 18], ps: [0, 0], fl: { c: C.accent, o: 100 }, ge });
  }
  k.shape(S, fast, { n: 'express glow', at: at(L[0], 0.6), fx: { blur: 14 }, op: 60 });
  k.shape(S, fast, { n: 'express traffic', at: at(L[0], 0.6) });
  fig.pose(at(L[1], 0.2), 'present');
  end();
  return S;
}

function e03(k, T) {
  const { S, L, fig, end } = shot(k, 'e03', '03 Which apps', T);
  const items = [
    ['시장조성', '사고팔 가격을 계속 제시하는 역할', at(L[0], 0.5)],
    ['PropAMM', '전문 전략으로 가격을 맞추는 AMM', at(L[1], 0.05)],
    ['DeFi 앱', '빠른 반응이 중요한 금융 서비스', at(L[1], 0.6)],
  ];
  items.forEach(([w, d, t], i) => {
    const y = 300 + i * 175;
    k.text(S, w, X, y, { f: 'krd', sz: 92, c: C.ink, anim: 'rise', at: t, mark: i === 1 });
    k.text(S, d, X + 4, y + 70, { sz: 24, c: C.ink2, anim: 'fade', at: t + 0.2 });
  });
  fig.pose(at(L[0], 0.4), 'point').pose(at(L[1], 0.5), 'pointUp');
  end();
  return S;
}

function e04(k, T) {
  const { S, L, fig, end } = shot(k, 'e04', '04 Speed', T);
  k.label(S, 'BLOCK TIME — TARGET', X, 230, { at: 0.2 });
  k.text(S, '0.1~0.2초', X - 8, 380, { f: 'krd', sz: 190, at: at(L[0], 0.55), s0: 104 });
  const y = 620;
  k.line(S, [[X, y], [1760, y]], { c: C.ink, so: 25, at: 0.3, dur: 0.9 });
  k.text(S, 'Elysium 목표 · 0.1~0.2초마다', X, y - 38, { sz: 22, w: 600, c: C.accent, anim: 'fade', at: at(L[0], 0.6) });
  k.text(S, 'HyperEVM 빠른 블록 · 1초마다', 1760, y - 38, { sz: 22, c: C.ink2, al: 'r', anim: 'fade', at: at(L[0], 0.6) });
  for (let i = 1; i <= 6; i++) {
    const x = X + 150 * i;
    k.shape(S, [{ t: 'ell', sz: [16, 16], ps: [x, y], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [x, y], p: [x, y], at: r2(at(L[0], 0.6) + i * 0.12) });
  }
  k.shape(S, [{ t: 'ell', sz: [16, 16], ps: [1760, y], fl: { c: C.ink3, o: 80 } }], { anim: 'pop', a: [1760, y], p: [1760, y], at: r2(at(L[0], 0.6) + 1.2) });
  k.text(S, '0s', X, y + 34, { f: 'mono', sz: 16, c: C.ink3, al: 'c', anim: 'fade', at: 0.6 });
  k.text(S, '1s', 1760, y + 34, { f: 'mono', sz: 16, c: C.ink3, al: 'c', anim: 'fade', at: 0.6 });
  k.text(S, '목표 사양이에요 · 메인넷 전 부하시험으로 검증될 예정', X, 760, { sz: 22, c: C.ink3, anim: 'fade', at: at(L[1], 0.5) });
  fig.pose(at(L[0], 0.4), 'pointUp').pose(at(L[1], 0.55), 'shrug');
  end();
  return S;
}

function e05(k, T) {
  const { S, L, fig, end } = shot(k, 'e05', '05 Gas is HYPE', T);
  fig.pose(at(L[0], 0.15), 'hold');
  const [hx, hy] = fig.hand();
  const cx = hx + 40;
  const cy = hy - 40;
  k.shape(S, [{ t: 'ell', sz: [92, 92], ps: [cx, cy], fl: { c: C.mint, o: 100 }, st: { c: '#1B3A40', w: 5, o: 100 } }], { anim: 'pop', a: [cx, cy], p: [cx, cy], at: at(L[0], 0.3) });
  k.text(S, 'HYPE', cx, cy, { f: 'en', w: 700, sz: 22, tr: 40, c: '#1B3A40', al: 'c', anim: 'fade', at: at(L[0], 0.4) });
  k.label(S, '통행료 = 가스', X, 250, { at: 0.2, sz: 24 });
  const wGas = k.measure('가스는 ', { f: 'krd', w: 400, sz: 150 });
  k.text(S, '가스는 ', X, 400, { f: 'krd', sz: 150, anim: 'rise', at: at(L[0], 0.1) });
  k.text(S, 'HYPE', X + wGas, 400, { f: 'krd', sz: 150, anim: 'rise', at: at(L[0], 0.18), mark: true });
  k.text(S, '새 가스 토큰 없이 · HYPE를 1:1로 브리지', X, 540, { sz: 32, c: C.ink2, anim: 'up', at: at(L[0], 0.6) });
  k.text(S, '주의 · 브리지만으로 스테이킹 수익이 생기지는 않아요', X, 680, { sz: 28, w: 500, c: C.amber, anim: 'up', at: at(L[1], 0.3) });
  fig.pose(at(L[1], 0.2), 'stop');
  end();
  return S;
}

function e06(k, T) {
  const { S, L, fig, end } = shot(k, 'e06', '06 Settlement', T, { tail: 1.2 });
  k.label(S, '정산 = 최종 장부에 기록', X, 250, { at: 0.2, sz: 24 });
  k.lines(S, ['최종 기록은', 'HyperEVM에'], X, 380, { f: 'krd', sz: 96, at: at(L[0], 0.2), marks: [false, true] });
  const y = 600;
  k.label(S, 'ELYSIUM', X, y, { c: C.ink, at: at(L[0], 0.3), tr: 300 });
  k.line(S, [[X + 240, y], [1450, y]], { c: C.ink, so: 40, at: at(L[0], 0.35), dur: 0.7 });
  k.shape(S, [0, 0.33, 0.66].map((ph) => ({ t: 'ell', sz: [10, 10], ps: [0, 0], fl: { c: C.accent, o: 100 }, ge: { p: { fn: 'along', p0: [X + 250, y], p1: [1440, y], v: 0.6, ph }, o: { fn: 'alongO', v: 0.6, ph, base: 100 } } })), { n: 'settle pulses', at: at(L[0], 0.5) });
  k.label(S, 'HYPEREVM', 1480, y, { at: at(L[0], 0.5), tr: 300 });
  fig.pose(at(L[0], 0.25), 'point');
  end();
  return S;
}

function e07(k, T) {
  const { S, L, fig, end } = shot(k, 'e07', '07 Where fees go', T, { tail: 1.2 });
  k.label(S, 'SEQUENCER REVENUE — PLANNED', X, 240, { at: 0.2 });
  k.text(S, '시퀀서 수익, 이렇게 나눌 계획', X, 320, { f: 'krd', sz: 64, anim: 'rise', at: at(L[0], 0.2) });
  const cols = [
    { x: X, pct: 25, c: C.sky, t: '빌더', d: '앱을 만드는 개발자', when: at(L[1], 0.02) },
    { x: X + 340, pct: 25, c: C.kblue, t: '운영 금고', d: 'Kinetiq 트레저리', when: at(L[1], 0.55) },
    { x: X + 680, pct: 50, c: C.accent, t: 'KNTQ 매수·소각', d: '시장에서 사서 없애요', when: at(L[2], 0.2) },
  ];
  for (const c of cols) {
    k.text(S, c.pct + '%', c.x, 470, { f: 'en', w: 500, sz: 120, tr: -30, c: c.c, at: c.when, s0: 104, counter: { t0: c.when, t1: c.when + 0.9, from: 0, to: c.pct, dec: 0, suf: '%' } });
    k.text(S, c.t, c.x, 572, { sz: 28, w: 700, anim: 'up', at: c.when + 0.2 });
    k.text(S, c.d, c.x, 612, { sz: 22, c: C.ink2, anim: 'fade', at: c.when + 0.3 });
  }
  // one bar per share, each grows when the narration names it
  cols.forEach((c, i) => k.split(S, X + [0, 250, 500][i], 690, ([240, 240, 500][i] * 100) / c.pct, [{ pct: c.pct, c: c.c === '#8EBFCC' ? C.kblue : c.c === C.accent ? C.mint2 : c.c }], { at: c.when }));
  k.text(S, '시퀀서 수익 기준 예정 설계 · 전체 가스비 기준 아님 · 시행 시점은 공식 공지 확인', X, 760, { sz: 20, c: C.ink3, anim: 'fade', at: at(L[2], 0.5) });
  fig.pose(at(L[0], 0.1), 'present').pose(at(L[1], 0.05), 'point').pose(at(L[2], 0.3), 'open');
  end();
  return S;
}

function e08(k, T) {
  const { S, L, fig, end } = shot(k, 'e08', '08 Four apps', T, { tail: 1.2 });
  k.label(S, 'ELYSIUM ECOSYSTEM', X, 220, { at: 0.2 });
  ['ASCEND', 'MONTRA', 'NEST', 'ELOSCAPE'].forEach((n, i) => {
    const y = 330 + i * 120;
    k.text(S, `0${i + 1}`, X, y, { f: 'mono', sz: 20, c: C.accent, anim: 'fade', at: at(L[0], 0.3) + i * 0.22 });
    k.text(S, n, X + 70, y, { f: 'en', w: 500, sz: 96, tr: 100, anim: 'rise', at: at(L[0], 0.3) + i * 0.22 });
  });
  fig.pose(at(L[0], 0.2), 'present');
  end();
  return S;
}

function appHead(k, S, name, tag, t) {
  k.text(S, name, X - 6, 270, { f: 'en', w: 600, sz: 120, tr: 80, at: t, trFrom: 280, s0: 103 });
  k.text(S, tag, X, 372, { f: 'krd', sz: 44, c: C.ink, anim: 'up', at: t + 0.3, mark: true, markAt: 0.3 });
}
const warnLine = (k, S, str, t) => k.text(S, '주의 · ' + str, X, 790, { sz: 24, w: 500, c: C.amber, anim: 'up', at: t, maxW: 1000 });

function e09(k, T) {
  const { S, L, fig, end } = shot(k, 'e09', '09 Ascend', T);
  appHead(k, S, 'ASCEND', '토큰의 성장 사다리', 0.3);
  const steps = [['LAUNCH', 760, 700], ['ASCENDED', 1000, 610], ['HYPERCORE SPOT', 1240, 520], ['HIP-3 PERPS', 1480, 430]];
  const pts = [];
  steps.forEach(([, x, y], i) => {
    pts.push([x, y], [x + 220, y]);
    if (i < steps.length - 1) pts.push([x + 240, steps[i + 1][2]]);
  });
  k.line(S, pts, { c: C.accent, sw: 4, at: at(L[0], 0.35), dur: 2.0 });
  steps.forEach(([n, x, y], i) => {
    const t = at(L[0], 0.35) + i * 0.45;
    k.label(S, n, x, y - 28, { c: i === 3 ? C.accent : C.ink, at: t, tr: 200 });
    if (i) fig.hop(t, 22 + i * 6); // a little hop per step, like climbing
  });
  warnLine(k, S, '단계는 방향일 뿐, 자동 졸업·상장을 보장하지 않아요', at(L[1], 0.2));
  fig.pose(at(L[0], 0.25), 'pointUp', 0.25).sparkle(at(L[0], 0.35) + 1.5).pose(at(L[1], 0.15), 'stop');
  end();
  return S;
}

function e10(k, T) {
  const { S, L, fig, end } = shot(k, 'e10', '10 Montra', T);
  appHead(k, S, 'MONTRA', '크리에이터의 토큰 발행소', 0.3);
  k.text(S, '60–96%', X - 6, 545, { f: 'en', w: 600, sz: 170, tr: -40, c: C.accent, at: at(L[1], 0.45), s0: 104 });
  k.text(S, '출시 시점 · 거래 수수료 중 크리에이터 몫', X, 660, { sz: 26, c: C.ink2, anim: 'up', at: at(L[1], 0.6) });
  k.text(S, 'Montra 몫은 거래량의 0.40% 고정 · MONTRA 커뮤니티 에어드롭 25% 계획', X, 712, { sz: 21, c: C.ink3, anim: 'fade', at: at(L[1], 0.75), maxW: 1000 });
  warnLine(k, S, '에어드롭은 활동만으로 보장되지 않아요', at(L[1], 0.85));
  fig.pose(at(L[0], 0.2), 'present').pose(at(L[1], 0.4), 'point');
  end();
  return S;
}

function e11(k, T) {
  const { S, L, fig, end } = shot(k, 'e11', '11 Nest', T);
  appHead(k, S, 'NEST', '유동성이 모이는 둥지', 0.3);
  [['스왑', X, 0.18], ['유동성 공급', X + 250, 0.42], ['락업·투표', X + 700, 0.7]].forEach(([w, x, f], i) => {
    k.text(S, `0${i + 1}`, x, 480, { f: 'mono', sz: 18, c: C.accent, anim: 'fade', at: at(L[0], f) });
    k.text(S, w, x, 545, { f: 'krd', sz: 64, anim: 'rise', at: at(L[0], f) });
  });
  k.text(S, 'veNEST · 최대 6개월 락업', X, 670, { sz: 38, w: 700, anim: 'up', at: at(L[1], 0.15), mark: true });
  warnLine(k, S, '신규 토큰 LP는 가격 변동·비영구적 손실 위험이 있어요', at(L[1], 0.6));
  fig.pose(at(L[0], 0.15), 'point').pose(at(L[1], 0.15), 'stop');
  end();
  return S;
}

function e12(k, T) {
  const { S, L, fig, end } = shot(k, 'e12', '12 Eloscape', T, { tail: 1.0 });
  appHead(k, S, 'ELOSCAPE', '게임처럼 하는 온체인 채굴', 0.3);
  const facts = [['25칸 중 한 칸에 HYPE를 넣고', at(L[0], 0.6)], ['60초마다 1칸 당첨', at(L[1], 0.05)], ['당첨 칸 참여자끼리 비중대로 HYPE 분배', at(L[1], 0.3)], ['ELO 최대 300만 개 · 아직 미출시', at(L[1], 0.5)]];
  facts.forEach(([f, t], i) => k.text(S, f, X, 470 + i * 52, { sz: 26, c: i === 3 ? C.ink3 : C.ink2, anim: 'up', at: t, maxW: 540 }));
  const cell = 62;
  const gap = 10;
  const gx = 1500 - (5 * cell + 4 * gap) / 2;
  const gy = 560 - (5 * cell + 4 * gap) / 2;
  const pos = (r, c) => [gx + cell / 2 + c * (cell + gap), gy + cell / 2 + r * (cell + gap)];
  const cells = [];
  for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) cells.push({ t: 'rect', sz: [cell, cell], ps: pos(r, c), rd: 9, fl: { c: C.white, o: 100 }, st: { c: C.ink, w: 2, o: 30 }, gkf: { o: [[r2(0.4 + (r + c) * 0.04), 0, 'so'], [r2(0.7 + (r + c) * 0.04), 100, 'l']] } });
  k.shape(S, cells, { n: 'grid', anim: 'none' });
  const mine = pos(1, 1);
  const tIn = at(L[0], 0.75);
  const tLose = at(L[1], 0.55);
  k.shape(S, [{ t: 'rect', sz: [cell, cell], ps: mine, rd: 9, fl: { c: C.mint, o: 70 }, st: { c: C.accent, w: 2.5, o: 100 }, gkf: { o: [[tIn, 0, 'x'], [r2(tIn + 0.3), 100, 'l'], [tLose, 100, 'io'], [r2(tLose + 0.5), 25, 'l']] } }], { n: 'my deposit', anim: 'none' });
  const win = pos(3, 3);
  const tWin = at(L[1], 0.08);
  const hi = [{ t: 'rect', sz: [cell, cell], ps: win, rd: 9, fl: { c: C.accent, o: 100 }, gkf: { s: [[tWin, [40, 40], 'x'], [r2(tWin + 0.45), [100, 100], 'l']], o: [[tWin, 0, 'so'], [r2(tWin + 0.2), 100, 'l']] } }];
  k.shape(S, hi, { n: 'winner glow', anim: 'none', fx: { blur: 24 }, op: 60 });
  k.shape(S, hi, { n: 'winner', anim: 'none' });
  k.text(S, 'WIN', win[0], win[1], { f: 'mono', w: 500, sz: 16, c: C.white, al: 'c', anim: 'fade', at: r2(tWin + 0.3) });
  k.text(S, '낙첨', mine[0], mine[1], { sz: 18, w: 700, c: C.amber, al: 'c', anim: 'fade', at: r2(tLose + 0.3) });
  warnLine(k, S, '낙첨 칸의 HYPE는 잃을 수 있어요 · 수익 보장 없음', at(L[1], 0.7));
  fig.pose(at(L[0], 0.3), 'point').pose(at(L[1], 0.6), 'shrug');
  end();
  return S;
}

function e13(k, T) {
  const { S, L, fig, end } = shot(k, 'e13', '13 Before you join', T, { tail: 1.2 });
  k.lines(S, ['참여 전에, 꼭.'], X, 270, { f: 'krd', sz: 100, at: at(L[0], 0.05) });
  [['목표·계획은 결과가 아니에요', at(L[0], 0.6)], ['보상·상장·수익은 보장되지 않아요', at(L[1], 0.05)], ['공식 도메인·채널에서만 확인하세요', at(L[1], 0.55)]].forEach(([s, t], i) => {
    const y = 440 + i * 105;
    k.text(S, `0${i + 1}`, X, y, { f: 'mono', sz: 22, c: C.amber, anim: 'fade', at: t });
    k.text(S, s, X + 70, y, { sz: 44, w: 700, tr: -25, anim: 'rise', at: t });
  });
  fig.pose(at(L[0], 0.1), 'stop').pose(at(L[1], 0.3), 'present');
  end();
  return S;
}

function e14(k, T) {
  const { S, L, fig } = shot(k, 'e14', '14 End card', T, { tail: 2.2 });
  k.logo(S, 1260, 400, 62, { at: 0.2 });
  k.label(S, 'MAINNET — SCHEDULED', 1260, 520, { al: 'c', at: 0.7, tr: 400 });
  k.text(S, '2026.11.09', 1260, 610, { f: 'en', w: 600, sz: 110, tr: 40, al: 'c', at: 0.85, trFrom: 240, s0: 104 });
  k.label(S, 'TESTNET LIVE · CHAIN ID 99801', 1260, 705, { al: 'c', c: C.ink2, at: 1.3, tr: 300 });
  k.text(S, '정보 제공 목적이며 투자 권유가 아닙니다 · 수치는 목표·계획으로 변경될 수 있습니다', 1260, 790, { sz: 19, c: C.ink3, al: 'c', anim: 'fade', at: 1.5 });
  fig.pose(at(L[0], 0.2), 'present').wave(at(L[0], 0.8), 3).happy(at(L[0], 0.8), S.dur).done();
  return S;
}

export const STOCK = {};

export function build(k, timing) {
  const T = timing && timing.lines;
  const list = [e01, e02, e03, e04, e05, e06, e07, e08, e09, e10, e11, e12, e13, e14].map((f) => f(k, T));
  const dur = list.reduce((a, s) => a + s.dur, 0);
  const slots = { LOGO: logoSlot(k, dur) };
  return assemble({ id: 'easy', name: 'Elysium_Beginner' }, list, slots, k, { push: 2, wipe: true });
}

export { SCRIPT, W };
