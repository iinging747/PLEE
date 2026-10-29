// Writes dist/SCRIPT.md from the compiled videos: shot list with timecodes,
// on-screen copy, narration lines (caption + what ElevenLabs reads), SFX cues
// and stock slots. Handy for review before opening After Effects.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const tc = (t) => {
  const m = Math.floor(t / 60);
  const s = (t - m * 60).toFixed(1).padStart(4, '0');
  return `${m}:${s}`;
};
const esc = (s) => String(s).replace(/\|/g, '\\|').replace(/\n/g, ' / ');

const out = ['# Elysium 프로모 — 장면표 · 스크립트', '', '`engine/script-doc.mjs`가 빌드 결과(build/*.json)에서 자동 생성합니다. 문구 수정은 `storyboard/*.js`에서 하세요.', ''];
const titles = { pro: 'A. 고급자 버전 (전문가 해설)', easy: 'B. 초보자 버전 (Hypurr가 하나씩 설명)' };
for (const id of ['pro', 'easy']) {
  const v = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', id + '.json'), 'utf8'));
  out.push(`## ${titles[id]} — ${v.name} (${v.dur}s, 1920×1080, 30fps)`, '');
  out.push(`내레이션 길이 기준: ${v.timingSource === 'elevenlabs' ? 'ElevenLabs 실제 음성 길이' : '읽기 속도 추정치 (ElevenLabs 생성 후 자동 재조정)'}`, '');
  out.push('| # | 시작 | 길이 | 장면 | 화면 문구 |', '|---|---|---|---|---|');
  v.order.forEach((o, i) => {
    const sc = v.scenes[o.id];
    // captions may be split into chunks: skip any text that is part of a narration line
    const caps = v.narration.filter((n) => n.scene === o.id).map((n) => n.text);
    const copy = sc.layers.filter((L) => L.k === 'text' && !caps.some((c) => c.includes(L.tx)) && L.sz >= 30).map((L) => L.tx);
    out.push(`| ${i + 1} | ${tc(o.start)} | ${o.dur}s | ${esc(o.name)} | ${esc([...new Set(copy)].join(' · '))} |`);
  });
  out.push('');
  if (v.narration.length) {
    out.push('### 내레이션 (ElevenLabs TTS)', '', '| ID | 시작 | 자막 | 읽는 문장 (발음용) |', '|---|---|---|---|');
    for (const n of v.narration) out.push(`| ${n.id} | ${tc(n.start)} | ${esc(n.text)} | ${n.say !== n.text ? esc(n.say) : '〃'} |`);
    out.push('');
  }
  if (v.cues.length) {
    const byType = {};
    for (const c of v.cues) (byType[c.type] = byType[c.type] || []).push(tc(c.t));
    out.push('### 효과음 큐', '', ...Object.entries(byType).map(([t, ts]) => `- **${t}**: ${ts.join(', ')}`), '');
  }
  const stock = Object.entries(v.slots).filter(([, s]) => s.kind === 'stock');
  if (stock.length) {
    out.push('### 스톡 영상 슬롯 (AE `03_SLOTS` 폴더)', '');
    for (const [sid, s] of stock) out.push(`- **${s.name}** — ${s.desc}. 추천 검색어: ${s.search.map((q) => `[${q}](https://www.pexels.com/search/videos/${encodeURIComponent(q)}/)`).join(', ')}`);
    out.push('');
  }
}
fs.writeFileSync(path.join(ROOT, 'dist', 'SCRIPT.md'), out.join('\n'));
console.log('wrote dist/SCRIPT.md');
