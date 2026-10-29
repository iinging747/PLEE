// Version A — 고급자 (advanced). An expert walk-through of Elysium, built as
// a sequence of focused beats: every narration line gets one message, big,
// revealed word by word and cleared before the next. Chapters open on mint
// cards that continue the cut's wipe. The provided Hypurr character presents
// from the right, in glasses. Shot lengths follow the narration
// (dist/audio/narration_pro.json once the ElevenLabs voice exists, otherwise an
// estimate). Wording follows the brief: targets are "목표/사양", launch is
// "예정", every share names its denominator.
//
// `text` is the caption, `say` is what ElevenLabs reads (Korean pronunciation
// for tickers and English names).

import { C, W, assemble, logoSlot, mascot, timeline, rng, r2 } from '../engine/lib.js';

const X = 160; // content column; the presenter stands on the right
const X1 = 1440; // right edge of the content column
const CAT_X = 1700;
const GROUND = 900;

const SCRIPT = {
  intro: [
    { id: 'v01', text: 'Elysium을 조금 더 깊이 들여다보겠습니다.', say: '엘리시움을 조금 더 깊이 들여다보겠습니다.' },
    { id: 'v02', text: '구조, 성능 목표, 수익 흐름, 그리고 생태계 앱의 작동 방식까지 차례로 짚어 보겠습니다.' },
  ],
  arch: [
    { id: 'v03', text: 'Elysium은 Kinetiq이 만드는 Arbitrum Orbit 기반 L2로, Nitro와 ArbOS 위에서 동작합니다.', say: '엘리시움은 키네틱이 만드는 아비트럼 오빗 기반 레이어 투로, 나이트로와 에이알비 오에스 위에서 동작합니다.' },
    { id: 'v04', text: '실행 결과는 HyperEVM에 정산되고, 가스는 네이티브 HYPE로 지불합니다.', say: '실행 결과는 하이퍼 이브이엠에 정산되고, 가스는 네이티브 하이프로 지불합니다.' },
    { id: 'v05', text: 'HYPE는 래핑이나 스테이킹 단계 없이 1:1로 브리지되며, 브리징 자체로 스테이킹 수익이 생기지는 않습니다.', say: '하이프는 래핑이나 스테이킹 단계 없이 일 대 일로 브리지되며, 브리징 자체로 스테이킹 수익이 생기지는 않습니다.' },
  ],
  perf: [
    { id: 'v06', text: '기준부터 보겠습니다. HyperEVM fast block은 1초마다 최대 3M gas, slow block은 60초마다 30M gas로, 모두 블록당 한도입니다.', say: '기준부터 보겠습니다. 하이퍼 이브이엠 패스트 블록은 일 초마다 최대 삼백만 가스, 슬로 블록은 육십 초마다 삼천만 가스로, 모두 블록당 한도입니다.' },
    { id: 'v07', text: 'Elysium의 공식 사양은 canonical 블록 100~200ms, 체감 영수증 약 300ms, 실행 목표 300 Mgas/s입니다.', say: '엘리시움의 공식 사양은 캐노니컬 블록 백에서 이백 밀리초, 체감 영수증 약 삼백 밀리초, 실행 목표 초당 삼백 메가가스입니다.' },
    { id: 'v08', text: '이 수치는 메인넷 전 부하시험으로 검증될 목표치이며, 실측 성능이 아닙니다.' },
  ],
  value: [
    { id: 'v09', text: '시퀀서 수익은 빌더 25%, 트레저리 25%, KNTQ 공개시장 매수 50%로 배분될 계획입니다.', say: '시퀀서 수익은 빌더 이십오 퍼센트, 트레저리 이십오 퍼센트, 케이엔티큐 공개시장 매수 오십 퍼센트로 배분될 계획입니다.' },
    { id: 'v10', text: '매수한 KNTQ는 Assistance Fund로 보내 소각합니다. 분모는 전체 가스비가 아니라 시퀀서 수익입니다.', say: '매수한 케이엔티큐는 어시스턴스 펀드로 보내 소각합니다. 분모는 전체 가스비가 아니라 시퀀서 수익입니다.' },
  ],
  core: [
    { id: 'v11', text: '출시는 stock ArbOS로 시작하고, 약 4주 뒤 HyperCore read precompile과 keeper write 경로가 업그레이드로 추가될 계획입니다.', say: '출시는 스톡 에이알비 오에스로 시작하고, 약 사 주 뒤 하이퍼코어 리드 프리컴파일과 키퍼 라이트 경로가 업그레이드로 추가될 계획입니다.' },
    { id: 'v12', text: 'HyperCore 액션은 비동기로 처리되며, 두 체인 사이의 원자적 실행은 지원되지 않습니다.', say: '하이퍼코어 액션은 비동기로 처리되며, 두 체인 사이의 원자적 실행은 지원되지 않습니다.' },
  ],
  ascend: [
    { id: 'v13', text: 'Ascend는 토큰의 라이프사이클을 Launch, Ascended, HyperCore 현물, HIP-3 무기한 선물로 잇는 런치패드입니다.', say: '어센드는 토큰의 라이프사이클을 런치, 어센디드, 하이퍼코어 현물, 힙 쓰리 무기한 선물로 잇는 런치패드입니다.' },
    { id: 'v14', text: '거래 수수료는 1%, 그 절반은 배포자 몫입니다. 순 프로토콜 수익은 HYPE 20, KNTQ 80으로 나누고, 매수한 KNTQ는 소각 60, LP 20, 포인트 보상 20에 씁니다.', say: '거래 수수료는 일 퍼센트, 그 절반은 배포자 몫입니다. 순 프로토콜 수익은 하이프 이십, 케이엔티큐 팔십으로 나누고, 매수한 케이엔티큐는 소각 육십, 엘피 이십, 포인트 보상 이십에 씁니다.' },
    { id: 'v15', text: '단계 이동은 성장 경로일 뿐, 자동 상장을 보장하지 않습니다.' },
  ],
  montra: [
    { id: 'v16', text: 'Montra는 크리에이터 중심 런치패드입니다. 수수료는 1~10% 사이 다섯 단계, Montra 몫은 거래량의 0.40%로 고정입니다.', say: '몬트라는 크리에이터 중심 런치패드입니다. 수수료는 일에서 십 퍼센트 사이 다섯 단계, 몬트라 몫은 거래량의 영 점 사 퍼센트로 고정입니다.' },
    { id: 'v17', text: '그래서 출시 시점 크리에이터 몫은 수수료의 60~96%가 되고, Montra 수익의 70%는 MONTRA 매수와 소각에 쓰일 계획입니다.', say: '그래서 출시 시점 크리에이터 몫은 수수료의 육십에서 구십육 퍼센트가 되고, 몬트라 수익의 칠십 퍼센트는 몬트라 매수와 소각에 쓰일 계획입니다.' },
  ],
  nest: [
    { id: 'v18', text: 'Nest는 ve(3,3) AMM입니다. veNEST 보유자는 배출량에 투표하고, 투표한 풀의 수수료와 인센티브를 받습니다.', say: '네스트는 브이이 쓰리 쓰리 에이엠엠입니다. 브이이 네스트 보유자는 배출량에 투표하고, 투표한 풀의 수수료와 인센티브를 받습니다.' },
    { id: 'v19', text: 'Elysium에서는 fee-only 풀로 운영되며, 프로토콜 수수료 몫의 70%로 KNTQ를 매수해 자격을 갖춘 락업 참여자에게 배분합니다. 최대 락업은 6개월입니다.', say: '엘리시움에서는 피 온리 풀로 운영되며, 프로토콜 수수료 몫의 칠십 퍼센트로 케이엔티큐를 매수해 자격을 갖춘 락업 참여자에게 배분합니다. 최대 락업은 육 개월입니다.' },
  ],
  eloscape: [
    { id: 'v20', text: 'Eloscape는 5×5 그리드에서 60초마다 한 칸을 무작위로 고르는 게임화 채굴입니다. 당첨 칸 참여자가 예치 비중대로 HYPE를 나눕니다.', say: '엘로스케이프는 오 곱하기 오 그리드에서 육십 초마다 한 칸을 무작위로 고르는 게임화 채굴입니다. 당첨 칸 참여자가 예치 비중대로 하이프를 나눕니다.' },
    { id: 'v21', text: 'ELO는 분당 1개, 최대 300만 개까지 발행되며 아직 출시 전입니다. 낙첨 칸의 HYPE는 손실될 수 있습니다.', say: '엘로는 분당 한 개, 최대 삼백만 개까지 발행되며 아직 출시 전입니다. 낙첨 칸의 하이프는 손실될 수 있습니다.' },
  ],
  check: [
    { id: 'v22', text: '정리하면, 성능 수치는 목표이고, 수익 배분은 계획이며, 보상과 상장은 자격과 규칙에 따라 달라집니다.' },
    { id: 'v23', text: '참여 전에는 공식 도메인과 지원 네트워크, 그리고 최신 공지를 반드시 확인하세요.' },
  ],
  end: [{ id: 'v24', text: 'Elysium 메인넷은 2026년 11월 9일 출시 예정이며, 테스트넷은 지금 운영 중입니다.', say: '엘리시움 메인넷은 이천이십육 년 십일 월 구 일 출시 예정이며, 테스트넷은 지금 운영 중입니다.' }],
};

const at = (l, f = 0) => r2(l.t + l.dur * f);
// time at which a word of the caption is spoken (proportional to its position)
const atw = (l, word, d = 0) => {
  const i = l.text.indexOf(word);
  return r2(l.t + (i < 0 ? 0 : (l.dur * i) / l.text.length) + d);
};
// a beat lasts for one narration line; it leaves just before the next one
const until = (L, i) => (i + 1 < L.length ? r2(L[i + 1].t - 0.22) : undefined);

// shared shot setup: narration timing, presenter, captions, optional chapter card
function shot(k, key, id, name, T, o = {}) {
  const lead = o.card ? 1.9 : o.lead ?? 0.6;
  const tl = timeline(SCRIPT[key], T, { lead, gap: 0.35, tail: o.tail ?? 1.0 });
  const S = k.scene(id, name, tl.dur);
  const L = tl.lines;
  k.shape(S, [{ t: 'ell', sz: [460, 460], ps: [CAT_X, GROUND - 190], fl: { c: C.mint, o: 30 } }], { n: 'halo', anim: o.haloAt ? 'fade' : 'none', at: o.haloAt || 0, dIn: 0.8, fx: { blur: 50 } });
  const cat = mascot(k, S, CAT_X, GROUND, 360, { glasses: true });
  cat.talk(L.map((l) => [l.t, l.t + l.dur]));
  k.say(S, L, { y: 1012, sz: 30, maxChars: 46 });
  S.cues = [{ t: 0, type: 'whoosh' }];
  if (o.card) chapterCard(k, S, o.card[0], o.card[1], lead - 0.45);
  if (o.tag) k.label(S, o.tag, X, 150, { c: C.ink3, at: lead - 0.2 });
  return { S, L, cat, end: () => cat.pose(S.dur - 0.5, 'idle').done() };
}

// mint chapter card: continues the incoming wipe, shows the chapter, wipes away
function chapterCard(k, S, n, title, t1) {
  k.punch(S, 0, t1, { full: true });
  const ex = r2(t1 - 0.12);
  k.text(S, n, X - 10, 470, { f: 'en', w: 300, sz: 300, tr: -60, c: C.ink, anim: 'rise', at: 0.12, dIn: 0.8, exit: ex });
  k.words(S, title, X, 700, { f: 'en', w: 500, sz: 64, tr: 260, at: 0.3, stagger: 0.08, exit: ex });
  k.label(S, 'ELYSIUM — DEEP DIVE', X, 170, { c: C.ink, at: 0.2, exit: ex });
  S.cues.push({ t: 0.05, type: 'hit' });
}

// big number + mono unit + caption, all leaving together
function stat(k, S, x, y, num, unit, cap, t, ex, o = {}) {
  const nO = { f: 'en', w: 300, sz: o.sz || 220, tr: -50 };
  const nw = k.measure(num, nO);
  k.text(S, num, x, y, { ...nO, c: o.c || C.ink, at: t, s0: 112, b0: 30, exit: ex, counter: o.counter });
  if (unit) k.text(S, unit, x + nw + 18, y + nO.sz * 0.36, { f: 'mono', w: 400, sz: Math.round(nO.sz * 0.24), c: o.uc || C.accent, baseline: true, anim: 'up', at: t + 0.25, exit: ex });
  if (cap) k.text(S, cap, x + 6, y + nO.sz * 0.62, { sz: o.capSz || 30, w: 600, c: C.ink2, anim: 'up', at: t + 0.35, exit: ex });
  return nw;
}

const note = (k, S, str, y, t, ex, o = {}) => k.text(S, str, o.x ?? X, y, { sz: o.sz || 26, w: 600, c: o.c || C.ink2, anim: 'up', at: t, exit: ex, mark: o.mark, maxW: X1 - X });
const warnNote = (k, S, str, y, t, ex) => note(k, S, '주의 · ' + str, y, t, ex, { c: C.amber });

function intro(k, T) {
  const { S, L, cat, end } = shot(k, 'intro', 'a01', '01 Deep dive', T, { lead: 1.6, haloAt: 3.4 });
  const e0 = until(L, 0);
  k.horizon(S, 600, { at: 0.15, dur: 1.8, glow: 70, exit: e0 });
  k.text(S, 'A HYPERLIQUID L2 BY KINETIQ', W / 2, 655, { f: 'mono', w: 400, sz: 20, tr: 520, c: C.ink2, al: 'c', anim: 'chars', at: 1.0, exit: e0 });
  k.text(S, 'ELYSIUM', W / 2, 470, { f: 'en', w: 300, sz: 210, tr: 330, al: 'c', at: 0.45, trFrom: 900, s0: 106, b0: 40, exit: e0 });
  S.cues.push({ t: 0.1, type: 'riser', dur: 2.0 }, { t: 1.4, type: 'boom' });
  // kinetic chapter list, one word at a time, then the whole agenda
  const l1 = L[1];
  const words = [['구조', '01'], ['성능 목표', '02'], ['수익 흐름', '03'], ['생태계 앱', '04']];
  words.forEach(([w, n], i) => {
    const t = atw(l1, w, -0.1);
    const ex = i < words.length - 1 ? r2(atw(l1, words[i + 1][0], -0.25)) : r2(at(l1, 0.78));
    k.text(S, n, X, 330, { f: 'mono', sz: 22, c: C.accent, anim: 'fade', at: t, exit: ex });
    k.words(S, w, X - 8, 470, { sz: 190, at: t, stagger: 0.06, exit: ex });
  });
  const tA = at(l1, 0.8);
  ['ARCHITECTURE', 'PERFORMANCE', 'VALUE ACCRUAL', 'HYPERCORE', 'APPS × 4', 'CHECKLIST'].forEach((c, i) =>
    k.label(S, `0${i + 1}  ${c}`, X + (i % 3) * 400, 420 + Math.floor(i / 3) * 70, { c: C.ink, sz: 24, at: r2(tA + i * 0.07) }),
  );
  cat.enter(at(L[0], 0.5), at(L[0], 0.5) + 0.9, 2150).pose(at(l1, 0.1), 'present').sparkle(tA);
  end();
  return S;
}

function arch(k, T) {
  const { S, L, cat, end } = shot(k, 'arch', 'a02', '02 Architecture', T, { card: ['01', 'ARCHITECTURE'], tag: '01 — ARCHITECTURE' });
  // v03: what it is built on
  let ex = until(L, 0);
  k.words(S, 'Arbitrum Orbit', X - 6, 330, { f: 'en', w: 300, sz: 150, tr: -30, at: at(L[0], 0.1), exit: ex });
  k.words(S, '기반의 L2', X, 500, { sz: 130, at: at(L[0], 0.25), marks: [false, true], exit: ex });
  [['ORBIT', 'L2 체인'], ['NITRO', '실행 스택'], ['ARBOS', 'L2 운영체제']].forEach(([a, b], i) => {
    const t = atw(L[0], i === 0 ? 'Orbit' : i === 1 ? 'Nitro' : 'ArbOS', 0.05);
    const y = 690 + i * 78;
    k.shape(S, [{ t: 'rect', sz: [560, 62], ps: [X + 280, y], rd: 14, fl: { c: i === 0 ? C.mint : C.white, o: 100 }, st: { c: C.ink, w: 1.5, o: 25 } }], { n: 'stack ' + a, anim: 'growX', p: [X, y], a: [X, y], at: t, dIn: 0.6, exit: ex });
    k.label(S, a, X + 28, y, { c: C.ink, at: t + 0.15, exit: ex });
    k.text(S, b, X + 532, y, { sz: 22, w: 600, c: C.ink2, al: 'r', anim: 'fade', at: t + 0.25, exit: ex });
  });
  // v04: settlement and gas
  ex = until(L, 1);
  const t4 = at(L[1], 0.02);
  k.label(S, 'SETTLEMENT', X, 300, { at: t4, exit: ex });
  k.text(S, 'HyperEVM', X - 4, 420, { f: 'en', w: 300, sz: 150, tr: -30, at: t4 + 0.1, exit: ex });
  k.line(S, [[X + 700, 260], [X + 700, 560]], { c: C.ink, so: 18, at: t4 + 0.2, dur: 0.6, exit: ex });
  const tg = atw(L[1], '가스');
  k.label(S, 'GAS', X + 780, 300, { at: tg, exit: ex });
  k.text(S, 'HYPE', X + 776, 420, { f: 'en', w: 300, sz: 150, tr: -30, c: C.accent, at: tg + 0.1, exit: ex });
  note(k, S, '실행 결과는 HyperEVM에 최종 정산', 530, t4 + 0.4, ex);
  note(k, S, '네이티브 HYPE · 가스용 신규 토큰 없음', 530, tg + 0.3, ex, { x: X + 780 });
  // v05: the bridge
  const t5 = at(L[2], 0.02);
  stat(k, S, X, 430, '1:1', null, null, t5, undefined, { sz: 300 });
  k.words(S, 'HYPE 브리지', X + 560, 380, { sz: 80, at: t5 + 0.2 });
  k.text(S, 'NO WRAPPER · NO STAKING HOP', X + 566, 480, { f: 'mono', sz: 22, tr: 200, c: C.accent, anim: 'chars', at: t5 + 0.45 });
  warnNote(k, S, '브리징만으로 스테이킹 수익이 생기지는 않습니다', 680, atw(L[2], '브리징 자체'), undefined);
  cat.pose(at(L[0], 0.2), 'point').pose(t4, 'present').pose(atw(L[2], '브리징 자체'), 'stop');
  end();
  return S;
}

function perf(k, T) {
  const { S, L, cat, end } = shot(k, 'perf', 'a03', '03 Performance', T, { card: ['02', 'PERFORMANCE'], tag: '02 — PERFORMANCE' });
  const track = (y, t, ex, label) => {
    k.line(S, [[X, y], [X1, y]], { c: C.ink, so: 25, at: t, dur: 0.8, exit: ex });
    k.text(S, '0s', X, y + 40, { f: 'mono', sz: 18, c: C.ink3, al: 'c', anim: 'fade', at: t, exit: ex });
    k.text(S, '1s', X1, y + 40, { f: 'mono', sz: 18, c: C.ink3, al: 'c', anim: 'fade', at: t, exit: ex });
    if (label) k.label(S, label, X, y - 44, { c: C.ink3, at: t, exit: ex });
  };
  const dot = (x, y, t, ex, c, sz = 18) => k.shape(S, [{ t: 'ell', sz: [sz, sz], ps: [x, y], fl: { c, o: 100 } }], { anim: 'pop', a: [x, y], p: [x, y], at: t, exit: ex });
  // v06: HyperEVM reference
  let ex = until(L, 0);
  const t6 = at(L[0], 0.12);
  k.label(S, 'REFERENCE · HYPEREVM DUAL BLOCKS', X, 250, { c: C.ink2, at: t6, exit: ex });
  stat(k, S, X, 400, '1s', '3M GAS', 'fast block · 블록당 한도', atw(L[0], 'fast'), ex, { sz: 160, c: C.ink2, uc: C.ink2 });
  stat(k, S, X + 620, 400, '60s', '30M GAS', 'slow block · 블록당 한도', atw(L[0], 'slow'), ex, { sz: 160, c: C.ink2, uc: C.ink2 });
  track(760, t6, ex, 'ONE SECOND');
  dot(X1, 760, atw(L[0], 'fast', 0.4), ex, C.ink2, 22);
  // v07: Elysium spec — the same second, ten blocks
  ex = until(L, 1);
  const t7 = at(L[1], 0.02);
  track(760, t7, ex, 'ONE SECOND · ELYSIUM TARGET');
  for (let i = 1; i <= 7; i++) dot(r2(X + ((X1 - X) * i) / 7), 760, r2(t7 + 0.35 + i * 0.15), ex, C.accent);
  k.label(S, 'ELYSIUM · OFFICIAL SPEC (TARGET)', X, 250, { at: t7, exit: ex });
  const tA = atw(L[1], 'canonical');
  const tB = atw(L[1], '체감', -0.1);
  const tC = atw(L[1], '실행 목표', -0.1);
  stat(k, S, X, 430, '100–200', 'ms', 'canonical 블록 생성', tA, r2(tB - 0.2));
  stat(k, S, X, 430, '~300', 'ms', '체감 영수증', tB, r2(tC - 0.2));
  stat(k, S, X, 430, '300', 'Mgas/s', '실행 처리량 목표', tC, ex, { c: C.accent, counter: { t0: tC, t1: tC + 1.2, from: 0, to: 300, dec: 0 } });
  S.cues.push({ t: r2(t7 + 0.4), type: 'ticks', dur: 1.2 });
  // v08: these are targets
  const t8 = at(L[2], 0);
  k.punch(S, r2(t8 - 0.1), S.dur);
  k.words(S, '목표 사양입니다.', X, 450, { sz: 150, at: t8 + 0.2 });
  k.text(S, '메인넷 전 부하시험으로 검증될 예정 · 실측 성능이 아닙니다', X + 4, 600, { sz: 34, w: 600, c: C.ink, anim: 'up', at: t8 + 0.5 });
  cat.pose(t6, 'point').pose(t7, 'pointUp').pose(tC, 'present').done();
  return S;
}

function value(k, T) {
  const { S, L, cat, end } = shot(k, 'value', 'a04', '04 Value accrual', T, { card: ['03', 'VALUE ACCRUAL'], tag: '03 — VALUE ACCRUAL' });
  let ex = until(L, 0);
  k.words(S, '시퀀서 수익은', X, 280, { sz: 96, at: at(L[0], 0.02), exit: ex });
  const segs = [
    { pct: 25, c: C.sky, t: '빌더', d: 'Elysium 위 앱 개발자', w: '빌더' },
    { pct: 25, c: C.kblue, t: '트레저리', d: 'Kinetiq 트레저리', w: '트레저리' },
    { pct: 50, c: C.mint2, t: 'KNTQ 공개시장 매수', d: '→ 소각', w: 'KNTQ' },
  ];
  let x = X;
  for (const sg of segs) {
    const when = atw(L[0], sg.w, -0.1);
    const w = ((X1 - X - 20) * sg.pct) / 100;
    k.split(S, x, 640, w, [{ pct: 100, c: sg.c }], { at: when, h: 14, exit: ex });
    k.text(S, sg.pct + '%', x - 4, 520, { f: 'en', w: 300, sz: 150, tr: -40, c: sg.c === C.mint2 ? C.accent : sg.c, at: when, s0: 108, exit: ex, counter: { t0: when, t1: when + 0.9, from: 0, to: sg.pct, dec: 0, suf: '%' } });
    k.text(S, sg.t, x, 710, { sz: 32, w: 700, anim: 'up', at: when + 0.15, exit: ex });
    k.text(S, sg.d, x, 756, { sz: 22, w: 500, c: C.ink2, anim: 'fade', at: when + 0.25, exit: ex });
    x += w + 10;
  }
  // v10: where the bought KNTQ goes
  const t = at(L[1], 0.02);
  let nx = X;
  ['KNTQ 매수', 'Assistance Fund', '소각'].forEach((n, i) => {
    const fo = i === 1 ? { f: 'en', w: 400, sz: 58, tr: -10 } : { f: 'krd', w: 800, sz: 70, tr: -30 };
    const tn = r2(t + i * 0.45);
    if (i) {
      k.line(S, [[nx, 380], [nx + 80, 380]], { c: C.accent, sw: 3, at: r2(tn - 0.25), dur: 0.3 });
      nx += 120;
    }
    k.text(S, n, nx, 380, { ...fo, c: i === 2 ? C.accent : C.ink, anim: 'rise', at: tn });
    nx += k.measure(n, fo) + 40;
  });
  k.text(S, '분모 = 시퀀서 수익 (전체 가스비 아님)', X, 600, { f: 'krd', sz: 64, tr: -30, anim: 'rise', at: atw(L[1], '분모'), mark: true });
  note(k, S, '예정 설계 · 비용 처리 · 시행 시점 · 실제 집행은 공식 공지를 확인하세요', 720, atw(L[1], '분모', 0.6), undefined, { c: C.ink3, sz: 24 });
  cat.pose(at(L[0], 0.1), 'present').pose(t, 'point').pose(atw(L[1], '분모'), 'stop');
  end();
  return S;
}

function core(k, T) {
  const { S, L, cat, end } = shot(k, 'core', 'a05', '05 HyperCore link', T, { card: ['04', 'HYPERCORE'], tag: '04 — HYPERCORE CONNECTION' });
  const ex = until(L, 0);
  const y = 330;
  const t = at(L[0], 0.02);
  k.line(S, [[X, y], [X1, y]], { c: C.ink, so: 25, at: t, dur: 1.0, exit: ex });
  [[X, 'MAINNET', 'stock ArbOS로 시작', '출시'], [X + 640, '+ 약 4주 · 계획', 'read precompile · keeper write', '4주']].forEach(([x, a, b, w]) => {
    const tt = atw(L[0], w, -0.1);
    k.shape(S, [{ t: 'ell', sz: [22, 22], ps: [x + 11, y], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [x + 11, y], p: [x + 11, y], at: tt, exit: ex });
    k.label(S, a, x, y - 50, { c: C.ink, sz: 22, at: tt, exit: ex });
    k.text(S, b, x, y + 60, { sz: 30, w: 600, c: C.ink2, anim: 'up', at: tt + 0.1, exit: ex });
  });
  const dy = 640;
  const td = atw(L[0], 'HyperCore');
  k.text(S, 'ELYSIUM', X, dy, { f: 'en', w: 500, sz: 44, tr: 200, anim: 'up', at: td, exit: ex });
  k.line(S, [[X + 300, dy], [1070, dy]], { c: C.ink, so: 35, at: td, dur: 0.6, exit: ex });
  k.text(S, 'HYPERCORE', 1100, dy, { f: 'en', w: 500, sz: 44, tr: 200, anim: 'up', at: td + 0.1, exit: ex });
  const pulse = (p0, p1, c, ph) => ({ t: 'ell', sz: [14, 14], ps: [0, 0], fl: { c, o: 100 }, ge: { p: { fn: 'along', p0, p1, v: 0.8, ph }, o: { fn: 'alongO', v: 0.8, ph, base: 100 } } });
  k.shape(S, [pulse([1060, dy], [X + 310, dy], C.kblue, 0), pulse([X + 310, dy], [1060, dy], C.accent, 0.5)], { n: 'read/write pulses', at: td + 0.4, exit: ex });
  k.text(S, '← READ  시장 데이터 접근', X + 310, dy - 46, { sz: 24, w: 600, c: C.kblue, anim: 'fade', at: atw(L[0], 'read'), exit: ex });
  k.text(S, 'WRITE  keeper trade-only agent →', 1060, dy + 50, { sz: 24, w: 600, c: C.accent, al: 'r', anim: 'fade', at: atw(L[0], 'keeper'), exit: ex });
  // v12: asynchronous, no atomicity
  const t2 = at(L[1], 0.02);
  k.text(S, 'ASYNC', X - 10, 430, { f: 'en', w: 300, sz: 260, tr: 120, at: t2, trFrom: 500, s0: 106, b0: 36 });
  k.words(S, '두 체인 사이 원자적 실행은 없습니다', X, 640, { sz: 64, at: atw(L[1], '두 체인'), marks: [false, false, true, true, false] });
  cat.pose(t, 'point').pose(t2, 'stop');
  end();
  return S;
}

// app scenes share a header
function appHead(k, S, name, sub, t, ex) {
  k.text(S, name, X - 8, 250, { f: 'en', w: 300, sz: 150, tr: 110, at: t, trFrom: 380, s0: 104, b0: 30, exit: ex, maxW: 1240 });
  k.text(S, sub, X, 360, { f: 'krd', sz: 40, tr: -20, anim: 'up', at: t + 0.3, exit: ex, mark: true, markAt: 0.3 });
}

function ascend(k, T) {
  const { S, L, cat, end } = shot(k, 'ascend', 'a06', '06 Ascend', T, { card: ['05', 'ECOSYSTEM APPS'], tag: '05 — APPS · ASCEND' });
  let ex = until(L, 0);
  appHead(k, S, 'ASCEND', '토큰의 라이프사이클 런치패드', at(L[0], 0.02), ex);
  const steps = [['LAUNCH', 'Launch'], ['ASCENDED', 'Ascended'], ['HYPERCORE SPOT', 'HyperCore'], ['HIP-3 PERPS', 'HIP-3']];
  const pts = [];
  steps.forEach((_, i) => {
    const x = X + i * 300;
    const y = 840 - i * 100;
    pts.push([x, y], [x + 260, y]);
    if (i < 3) pts.push([x + 290, y - 100]);
  });
  k.line(S, pts, { c: C.accent, sw: 4, at: atw(L[0], 'Launch', -0.2), dur: atw(L[0], 'HIP-3') - atw(L[0], 'Launch') + 0.4, ease: 'l', exit: ex });
  steps.forEach(([n, w], i) => {
    const tt = atw(L[0], w, -0.05);
    k.label(S, n, X + i * 300, 840 - i * 100 - 34, { c: i === 3 ? C.accent : C.ink, sz: 21, at: tt, exit: ex });
    if (i) cat.hop(tt, 18 + i * 6);
  });
  // v14: the three splits, one at a time
  ex = until(L, 1);
  const l = L[1];
  const tA = at(l, 0.0);
  const tB = atw(l, '순 프로토콜', -0.15);
  const tC = atw(l, '매수한', -0.15);
  stat(k, S, X, 420, '1%', null, '거래 수수료 · 그중 50%는 배포자 몫', tA, r2(tB - 0.2));
  stat(k, S, X, 420, '20 : 80', null, '순 프로토콜 수익 · HYPE 20% : KNTQ 80%', tB, r2(tC - 0.2));
  stat(k, S, X, 420, '60·20·20', null, '매수한 KNTQ · 소각 60 · kHYPE/KNTQ LP 20 · 포인트 20', tC, ex, { c: C.accent });
  k.text(S, '서로 다른 단계의 배분입니다 · 분모를 섞지 마세요', X, 720, { sz: 24, w: 500, c: C.ink3, anim: 'fade', at: tC + 0.6, exit: ex });
  // v15: caution
  const t3 = at(L[2], 0.02);
  k.words(S, '성장 경로일 뿐,', X, 400, { sz: 110, at: t3 });
  k.words(S, '자동 상장 보장은 없습니다', X, 560, { sz: 110, c: C.amber, at: atw(L[2], '자동') });
  cat.pose(at(L[0], 0.1), 'pointUp').pose(tA, 'point').pose(t3, 'stop');
  end();
  return S;
}

function montra(k, T) {
  const { S, L, cat, end } = shot(k, 'montra', 'a07', '07 Montra', T, { tag: '05 — APPS · MONTRA', lead: 0.9 });
  let ex = until(L, 0);
  appHead(k, S, 'MONTRA', '크리에이터 중심 런치패드', 0.3, ex);
  // fee setting scale: five settings between 1% and 10%
  const y = 620;
  const t1 = atw(L[0], '수수료');
  k.line(S, [[X, y], [X + 1000, y]], { c: C.ink, so: 25, at: t1, dur: 0.7, exit: ex });
  for (let i = 0; i < 5; i++) {
    const x = r2(X + (1000 * i) / 4);
    k.shape(S, [{ t: 'ell', sz: [20, 20], ps: [x, y], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [x, y], p: [x, y], at: r2(t1 + 0.25 + i * 0.12), exit: ex });
  }
  k.text(S, '1%', X, y + 46, { f: 'mono', sz: 22, c: C.ink2, al: 'c', anim: 'fade', at: t1 + 0.3, exit: ex });
  k.text(S, '10%', X + 1000, y + 46, { f: 'mono', sz: 22, c: C.ink2, al: 'c', anim: 'fade', at: t1 + 0.8, exit: ex });
  k.label(S, 'FEE SETTINGS · 5단계', X, y - 50, { c: C.ink2, at: t1 + 0.1, exit: ex });
  k.pill(S, 'Montra 몫 = 거래량의 0.40% 고정', X, 800, { at: atw(L[0], 'Montra 몫'), sz: 28, exit: ex });
  // v17: the creator share
  const t2 = at(L[1], 0.02);
  stat(k, S, X, 430, '60–96%', null, '출시 시점 · 거래 수수료 중 크리에이터 몫', t2, undefined, { sz: 240, c: C.accent });
  k.text(S, 'Montra 수익의 70% → MONTRA 매수 · 소각', X, 720, { f: 'krd', sz: 52, tr: -25, anim: 'rise', at: atw(L[1], 'Montra 수익') });
  k.text(S, '나머지 30%는 생태계 · 수수료 내부 배분과 거래량 대비 요율은 다른 분모입니다', X, 800, { sz: 24, w: 500, c: C.ink3, anim: 'fade', at: atw(L[1], 'Montra 수익', 0.8) });
  cat.pose(0.4, 'present').pose(t1, 'point').pose(t2, 'open');
  end();
  return S;
}

function nest(k, T) {
  const { S, L, cat, end } = shot(k, 'nest', 'a08', '08 Nest', T, { tag: '05 — APPS · NEST', lead: 0.9 });
  let ex = until(L, 0);
  appHead(k, S, 'NEST', 've(3,3) AMM', 0.3, ex);
  // the ve(3,3) loop: lock -> vote -> earn
  const nodes = [['LOCK', 'NEST → veNEST', X, 560], ['VOTE', '배출량 투표', X + 420, 560], ['EARN', '수수료 + 인센티브', X + 840, 560]];
  nodes.forEach(([a, b, x, y], i) => {
    const tt = atw(L[0], i === 0 ? 'veNEST' : i === 1 ? '투표하고' : '수수료', -0.1);
    k.text(S, a, x, y, { f: 'en', w: 300, sz: 96, tr: 40, at: tt, s0: 108, exit: ex });
    k.text(S, b, x + 4, y + 80, { sz: 28, w: 600, c: C.ink2, anim: 'up', at: tt + 0.2, exit: ex });
    if (i) k.line(S, [[x - 130, y - 14], [x - 40, y - 14]], { c: C.accent, sw: 3, at: tt - 0.1, dur: 0.3, exit: ex });
  });
  k.line(S, [[X + 1120, 600], [X + 1180, 600], [X + 1180, 760], [X + 40, 760], [X + 40, 700]], { c: C.accent, so: 50, sw: 2, at: atw(L[0], '수수료', 0.5), dur: 0.8, exit: ex });
  // v19: on Elysium
  const t2 = at(L[1], 0.02);
  k.text(S, 'fee-only', X - 6, 330, { f: 'en', w: 300, sz: 170, tr: -20, c: C.accent, at: t2, s0: 106 });
  k.text(S, 'Elysium의 Nest 풀은 스왑 수수료만 제공합니다', X, 470, { sz: 30, w: 600, c: C.ink2, anim: 'up', at: t2 + 0.4 });
  k.text(S, '프로토콜 수수료 몫의 70% → KNTQ 매수 → 자격 갖춘 락업 참여자', X, 600, { f: 'krd', sz: 44, tr: -25, anim: 'rise', at: atw(L[1], '70%', -0.2), maxW: X1 - X });
  k.pill(S, 'MAX LOCK 6개월 · vault에서 나가면 6개월 락', X, 760, { at: atw(L[1], '최대'), sz: 28 });
  cat.pose(0.4, 'point').pose(t2, 'present').pose(atw(L[1], '최대'), 'stop');
  end();
  return S;
}

function eloscape(k, T) {
  const { S, L, cat, end } = shot(k, 'eloscape', 'a09', '09 Eloscape', T, { tag: '05 — APPS · ELOSCAPE', lead: 0.9 });
  let ex = until(L, 0);
  appHead(k, S, 'ELOSCAPE', '게임화된 온체인 채굴', 0.3, ex);
  const cell = 66;
  const gap = 12;
  const gx = 900;
  const gy = 430;
  const pos = (r, c) => [gx + cell / 2 + c * (cell + gap), gy + cell / 2 + r * (cell + gap)];
  const cells = [];
  for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) cells.push({ t: 'rect', sz: [cell, cell], ps: pos(r, c), rd: 10, fl: { c: C.white, o: 100 }, st: { c: C.ink, w: 1.5, o: 30 }, gkf: { o: [[r2(0.5 + (r + c) * 0.03), 0, 'so'], [r2(0.75 + (r + c) * 0.03), 100, 'l']] } });
  k.shape(S, cells, { n: 'grid', anim: 'none', exit: ex });
  // rounds: a scan runs over the grid, then one random cell wins
  const R = rng(11);
  const t0 = atw(L[0], '60초');
  const wins = [];
  for (let n = 0; n < 4; n++) {
    const t = r2(t0 + n * 1.3);
    const r = Math.floor(R() * 5);
    const c = Math.floor(R() * 5);
    wins.push({ t: 'rect', sz: [cell, cell], ps: pos(r, c), rd: 10, fl: { c: C.accent, o: 100 }, gkf: { o: [[t, 0, 'x'], [r2(t + 0.15), 100, 'l'], [r2(t + 0.9), 100, 'i'], [r2(t + 1.1), 0, 'l']], s: [[t, [70, 70], 'x'], [r2(t + 0.35), [100, 100], 'l']] }, ga: pos(r, c) });
  }
  k.shape(S, wins, { n: 'winning cells', anim: 'none', exit: ex });
  k.label(S, '5×5 · 60s ROUND', gx, gy - 50, { c: C.ink, at: t0, exit: ex });
  k.text(S, '60초마다 1칸', X, 520, { f: 'krd', sz: 64, tr: -30, anim: 'rise', at: t0, exit: ex });
  k.text(S, '무작위 당첨', X, 610, { f: 'krd', sz: 64, tr: -30, anim: 'rise', at: t0 + 0.12, exit: ex });
  k.text(S, '당첨 칸 참여자가 예치 비중대로 HYPE 분배', X, 720, { sz: 26, w: 600, c: C.ink2, anim: 'up', at: atw(L[0], '당첨 칸'), exit: ex, maxW: 700 });
  // v21: ELO supply and the risk
  const t2 = at(L[1], 0.02);
  stat(k, S, X, 430, '3,000,000', 'ELO MAX', '분당 1개 발행 · 아직 미출시', t2, undefined, { sz: 190, counter: { t0: t2, t1: t2 + 1.6, from: 0, to: 3000000, dec: 0, sep: true } });
  k.words(S, '낙첨 칸의 HYPE는 손실될 수 있습니다', X, 700, { sz: 56, c: C.amber, at: atw(L[1], '낙첨') });
  k.text(S, '청구 수수료 · 가스비 별도 · 수익 보장 없음', X, 780, { sz: 24, w: 500, c: C.ink3, anim: 'fade', at: atw(L[1], '낙첨', 0.6) });
  cat.pose(0.4, 'point').pose(t2, 'pointUp').pose(atw(L[1], '낙첨'), 'shrug');
  end();
  return S;
}

function check(k, T) {
  const { S, L, cat, end } = shot(k, 'check', 'a10', '10 Checklist', T, { card: ['06', 'CHECKLIST'], tag: '06 — CHECKLIST', tail: 1.2 });
  const ex = until(L, 0);
  [['성능 수치', '목표', '성능'], ['수익 배분', '계획', '수익'], ['보상 · 상장', '조건부', '보상']].forEach(([a, b, w], i) => {
    const t = atw(L[0], w, -0.1);
    const y = 330 + i * 160;
    k.text(S, `0${i + 1}`, X, y - 10, { f: 'mono', sz: 22, c: C.amber, anim: 'fade', at: t, exit: ex });
    k.words(S, a, X + 80, y, { sz: 92, at: t, exit: ex });
    k.text(S, '= ' + b, X + 640, y, { f: 'krd', sz: 92, tr: -40, c: C.accent, anim: 'rise', at: t + 0.25, exit: ex });
  });
  const t2 = at(L[1], 0.02);
  k.words(S, '참여 전, 반드시 확인', X, 330, { sz: 110, at: t2, marks: [false, false, true] });
  ['공식 도메인', '지원 네트워크', '최신 공지'].forEach((w, i) => {
    const t = atw(L[1], w, -0.1);
    const y = 520 + i * 90;
    k.shape(S, [{ t: 'ell', sz: [16, 16], ps: [X + 8, y], fl: { c: C.accent, o: 100 } }], { anim: 'pop', a: [X + 8, y], p: [X + 8, y], at: t });
    k.text(S, w, X + 44, y, { f: 'krd', sz: 56, tr: -25, anim: 'rise', at: t });
  });
  cat.pose(at(L[0], 0.05), 'stop').pose(t2, 'present');
  end();
  return S;
}

function finale(k, T) {
  const { S, L, cat } = shot(k, 'end', 'a11', '11 End card', T, { tail: 2.8 });
  const cx = 800;
  k.logo(S, cx, 360, 72, { at: 0.2 });
  k.horizon(S, 480, { at: 0.5, dur: 1.3, x0: cx - 460, x1: cx + 460, glow: 60 });
  k.label(S, 'MAINNET — SCHEDULED', cx, 560, { al: 'c', at: 0.9, tr: 400, sz: 20 });
  k.text(S, '2026.11.09', cx, 670, { f: 'en', w: 300, sz: 150, tr: 30, al: 'c', at: 1.05, trFrom: 300, s0: 106, b0: 34 });
  k.label(S, 'TESTNET LIVE · CHAIN ID 99801', cx, 780, { al: 'c', c: C.ink2, at: 1.5, tr: 300 });
  k.text(S, '본 영상은 정보 제공 목적이며 투자 권유가 아닙니다 · 수치는 공개 자료 기준의 목표·계획으로 변경될 수 있습니다', cx, 900, { sz: 19, w: 500, c: C.ink3, al: 'c', anim: 'fade', at: 1.7 });
  cat.pose(at(L[0], 0.1), 'present').wave(r2(at(L[0], 1) + 0.3), 3).done();
  S.cues.push({ t: 0.15, type: 'boom' });
  return S;
}

export const STOCK = {};

export function build(k, timing) {
  const T = timing && timing.lines;
  const list = [intro, arch, perf, value, core, ascend, montra, nest, eloscape, check, finale].map((f) => f(k, T));
  const dur = list.reduce((a, s) => a + s.dur, 0);
  const slots = { LOGO: logoSlot(k, dur) };
  return assemble({ id: 'pro', name: 'Elysium_Advanced' }, list, slots, k, { push: 2, wipe: true });
}

export { SCRIPT, W };
