// Emit dist/Elysium_Promo_AE.jsx from build/<id>.json (run engine/render.mjs
// --compile-only first). The script is plain ExtendScript: header + CONFIG +
// DATA + engine/ae-runtime.jsx.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { EASES, C } from './lib.js';
import { aeExpr, counterAE, counterValue } from './expr.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ids = ['pro', 'easy'];

function prep(L) {
  if (L.ex) {
    L.exAE = {};
    for (const [k, e] of Object.entries(L.ex)) L.exAE[k] = aeExpr(e);
    delete L.ex;
  }
  if (L.cnt) {
    L.cntAE = counterAE(L.cnt);
    L.cntFinal = counterValue(L.cnt, L.cnt.t1);
  }
  if (L.it) {
    for (const it of L.it) {
      if (it.ge) {
        it.geAE = {};
        for (const [k, e] of Object.entries(it.ge)) it.geAE[k] = aeExpr(e);
        delete it.ge;
      }
    }
  }
  if (L.mt) prep(L.mt);
  return L;
}

const videos = {};
let maxDur = 0;
for (const id of ids) {
  const v = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', id + '.json'), 'utf8'));
  delete v.warnings;
  v.layers.forEach(prep);
  for (const s of Object.values(v.scenes)) s.layers.forEach(prep);
  for (const s of Object.values(v.slots)) (s.layers || []).forEach(prep);
  videos[id] = v;
  maxDur = Math.max(maxDur, v.dur);
}

const CONFIG = {
  BUILD: ['pro', 'easy'],
  // 'sandoll' = 설치된 산돌구름 폰트를 아래 SANDOLL_PREFS 순서로 찾아 사용 (없으면 auto)
  // 'auto' = Pretendard → Apple SD 산돌고딕 Neo → Noto Sans KR → 본고딕 → 맑은 고딕 중 설치된 첫 번째
  KR_FONT: 'sandoll',
  SANDOLL_PREFS: {
    pro: ['그레타\\s*산스', 'Greta\\s*Sans', '고딕\\s*Neo\\s*3', 'Gothic\\s*Neo\\s*3', '고딕\\s*Neo\\s*1', 'Gothic\\s*Neo\\s*1'],
    easy: ['고딕\\s*Neo\\s*3', 'Gothic\\s*Neo\\s*3', '그레타\\s*산스', 'Greta\\s*Sans', '고딕\\s*Neo\\s*1', 'Gothic\\s*Neo\\s*1'],
  },
  // 산돌 폰트가 없을 때: 본고딕(Noto Sans KR / Source Han Sans K — 한글 디자인 산돌) 우선
  KR_AUTO_ORDER: ['noto', 'source', 'notocjk', 'apple', 'pretendard', 'malgun'],
  // 특정 폰트를 강제하려면 PostScript 이름을 넣으세요 (예: {400:'...',500:'...',600:'...',700:'...',800:'...'})
  KR_FONT_OVERRIDE: null,
  KR_PRESETS: {
    pretendard: { label: 'Pretendard', 400: 'Pretendard-Regular', 500: 'Pretendard-Medium', 600: 'Pretendard-SemiBold', 700: 'Pretendard-Bold', 800: 'Pretendard-ExtraBold', 900: 'Pretendard-Black' },
    apple: { label: 'Apple SD 산돌고딕 Neo', 400: 'AppleSDGothicNeo-Regular', 500: 'AppleSDGothicNeo-Medium', 600: 'AppleSDGothicNeo-SemiBold', 700: 'AppleSDGothicNeo-Bold', 800: 'AppleSDGothicNeo-ExtraBold', 900: 'AppleSDGothicNeo-Heavy' },
    noto: { label: 'Noto Sans KR (한글 디자인: 산돌커뮤니케이션)', 400: 'NotoSansKR-Regular', 500: 'NotoSansKR-Medium', 600: 'NotoSansKR-SemiBold', 700: 'NotoSansKR-Bold', 800: 'NotoSansKR-ExtraBold', 900: 'NotoSansKR-Black' },
    notocjk: { label: 'Noto Sans CJK KR (한글 디자인: 산돌커뮤니케이션)', 400: 'NotoSansCJKkr-Regular', 500: 'NotoSansCJKkr-Medium', 600: 'NotoSansCJKkr-Medium', 700: 'NotoSansCJKkr-Bold', 800: 'NotoSansCJKkr-Bold', 900: 'NotoSansCJKkr-Black' },
    source: { label: '본고딕 Source Han Sans K (한글 디자인: 산돌커뮤니케이션)', 400: 'SourceHanSansK-Regular', 500: 'SourceHanSansK-Medium', 600: 'SourceHanSansK-Medium', 700: 'SourceHanSansK-Bold', 800: 'SourceHanSansK-Bold', 900: 'SourceHanSansK-Heavy' },
    malgun: { label: '맑은 고딕 (대체)', 400: 'MalgunGothic', 500: 'MalgunGothic', 600: 'MalgunGothicBold', 700: 'MalgunGothicBold', 800: 'MalgunGothicBold', 900: 'MalgunGothicBold' },
  },
  EN_FONTS: { 400: 'DMSans-Regular', 500: 'DMSans-Medium', 600: 'DMSans-SemiBold', 700: 'DMSans-Bold' },
  MONO_FONTS: { 400: 'DMMono-Regular', 500: 'DMMono-Medium' },
  ROOT_FOLDER: 'Elysium Promo',
  SLOT_FOLDER: '03_SLOTS (로고·스톡 교체)',
  TXT_DONE: 'Elysium 프로모 컴포지션 생성 완료',
  TXT_KR_FONT: '한글 폰트:',
  TXT_MISSING: '설치가 필요한 폰트 (README의 무료 다운로드 링크 참고):',
  TXT_NEXT: '다음 단계: "03_SLOTS" 폴더의 LOGO_Elysium 컴프에 공식 로고를, STOCK_* 컴프에 스톡 영상을 넣으면 두 영상 전체에 자동 반영됩니다.',
  TXT_WARN: '경고',
  TXT_SEARCH: '추천 검색어:',
  TXT_SLOT_HOWTO: '이 컴프에 영상/로고 파일을 드래그해 넣고 화면에 맞게 스케일하세요.\n(이 안내 텍스트는 가이드 레이어라 렌더링되지 않습니다)',
};

const header = `﻿/*
  Elysium 프로모 영상 — After Effects 자동 생성 스크립트
  ---------------------------------------------------------------
  사용법
    1) 폰트 설치 (무료): DM Sans, DM Mono (Google Fonts)
       한글: 산돌구름 폰트를 자동으로 찾아 사용 — 고급자: Sandoll 그레타산스 → 고딕Neo3 → 고딕Neo1
                                                   초보자: Sandoll 고딕Neo3 → 그레타산스 → 고딕Neo1
             제목은 같은 산돌 패밀리의 ExtraBold/Heavy 웨이트를 씁니다
             산돌 폰트가 없으면 본고딕 Noto Sans KR(무료, 한글 디자인 산돌) → Apple SD 산돌고딕 Neo 순으로 대체
    2) After Effects > File > Scripts > Run Script File… 에서 이 파일 실행
       (같은 폴더의 audio/temp_music_*.wav 가 있으면 임시 음악도 자동으로 들어갑니다)
    3) 프로젝트 패널 "Elysium Promo"
         01_MAIN       Elysium_Advanced (고급자) · Elysium_Beginner (초보자)
         02_SCENES_*   장면별 프리컴프 — 문구·타이밍 수정은 여기서
         03_SLOTS      LOGO_Elysium(공식 로고) · STOCK_*(스톡 영상) 교체용 컴프
    4) 공식 로고: kinetiq.xyz/brand 또는 elysium.kinetiq.xyz 에서 SVG/PNG를 받아
       LOGO_Elysium 컴프에 넣고 기본 워드마크 레이어 2개를 끄세요. (로고 재채색·효과 금지 규정 준수)
  이 파일은 engine/build-jsx.mjs 가 생성합니다. 직접 수정하지 말고 storyboard/*.js 를 고친 뒤 다시 빌드하세요.
*/
`;

const escape = (s) => s.replace(/[\u007f-￿]/g, (ch) => '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0'));
const runtime = fs.readFileSync(path.join(ROOT, 'engine', 'ae-runtime.jsx'), 'utf8');
const body = `(function () {
var CONFIG = ${JSON.stringify(CONFIG, null, 1)};
var DATA = { videos: ${JSON.stringify(videos)} };
var DATA_EASES = ${JSON.stringify(EASES)};
var DATA_FPS = 30;
var DATA_BG = ${JSON.stringify(C.paper)};
var DATA_MAX_DUR = ${maxDur};
var SCRIPT_DIR = (function () { try { return File($.fileName).parent.fsName; } catch (e) { return Folder.desktop.fsName; } })();
${runtime}
})();
`;
const out = path.join(ROOT, 'dist', 'Elysium_Promo_AE.jsx');
fs.writeFileSync(out, header + escape(body), 'utf8');
console.log('wrote', out, (fs.statSync(out).size / 1024).toFixed(0) + ' KB');
