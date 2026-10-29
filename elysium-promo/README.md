# Elysium 프로모 영상 (After Effects)

가로 1920×1080 · 30fps 두 가지 버전.

| 버전 | 컴포지션 | 길이 | 구성 |
|---|---|---|---|
| A. 전문가 · 커머셜 | `Elysium_Pro_Commercial` | 약 50초 (보이스오버 길이에 맞춰 자동 조정) | 120BPM 비트 컷, 한 화면 한 메시지, 전문가 톤 보이스오버 |
| B. 눈높이 | `Elysium_Easy_Explainer` | 약 2분 (내레이션 길이에 맞춰 자동 조정) | 고양이 캐릭터 내레이터, 자막, 단계별 설명 |

장면별 타임코드·화면 문구·내레이션 원고는 [`dist/SCRIPT.md`](dist/SCRIPT.md)에 있습니다.

## 폴더

```
dist/
  Elysium_Promo_AE.jsx      ← 에펙에서 실행하는 스크립트 (두 버전 모두 생성)
  preview/*.mp4             ← 미리보기 렌더
  audio/                    ← 임시 음악 / ElevenLabs 결과물 (mix, vo, music, sfx)
  SCRIPT.md                 ← 장면표 · 원고
assets/stickers/            ← 캐릭터 원본 스티커(PNG/WebP)를 넣는 곳
storyboard/pro.js, easy.js  ← 문구 · 타이밍 · 연출 (여기만 고치면 됨)
engine/                     ← 미리보기 렌더러 · AE 스크립트 생성기 · ElevenLabs 파이프라인
```

## After Effects에서 열기

1. 폰트: **산돌구름 폰트를 자동으로 찾아 씁니다.**
   - 커머셜: Sandoll 그레타산스 → 고딕Neo3 → 고딕Neo1 순
   - 눈높이: Sandoll 고딕Neo3 → 그레타산스 → 고딕Neo1 순
   - 산돌 폰트가 없으면 Pretendard(무료) → Apple SD 산돌고딕 Neo → Noto Sans KR 순으로 대체합니다. 영문·숫자는 Kinetiq 브랜드 서체인 **DM Sans / DM Mono**(무료)를 씁니다.
   - 순서를 바꾸거나 특정 폰트를 강제하려면 `dist/Elysium_Promo_AE.jsx` 맨 위 `CONFIG`의 `SANDOLL_PREFS`, `KR_FONT_OVERRIDE`를 수정하세요.
   - 미리보기 MP4는 이 서버에 산돌 폰트가 없어 Pretendard로 렌더링했습니다.
2. `File → Scripts → Run Script File…` → `dist/Elysium_Promo_AE.jsx` 실행.
   `dist/audio/`에 오디오가 있으면 자동으로 들어갑니다 (`*_mix.wav` 우선, 없으면 임시 음악).
3. 프로젝트 패널 `Elysium Promo`:
   - `01_MAIN`: 최종 컴포지션 두 개 (장면 시작점마다 마커)
   - `02_SCENES_*`: 장면별 프리컴프 — 문구·타이밍 수정은 여기서
   - `03_SLOTS`: `LOGO_Elysium`(공식 로고) · `STOCK_*`(스톡 영상) 교체용 컴프. 한 번 바꾸면 모든 장면에 반영
   - `05_CHARACTER`: 캐릭터 스티커 이미지

### 공식 로고
`kinetiq.xyz/brand` 또는 `elysium.kinetiq.xyz`에서 받은 SVG/PNG를 `LOGO_Elysium` 컴프에 넣고 기본 워드마크 레이어 2개를 끄세요.
Kinetiq 가이드에 따라 로고에는 재채색이나 효과를 넣지 않습니다. 스크립트는 로고에 크기·투명도·블러 인 애니메이션만 줍니다.

### 스톡 영상
`STOCK_*` 컴프에 영상을 드래그하면 됩니다. 추천 검색어는 각 컴프 안의 가이드 텍스트와 `dist/SCRIPT.md`에 있습니다.
배경 위에 Multiply 모드로 얹히고 Tint가 걸려 있어, 어떤 영상을 넣어도 톤이 맞춰집니다.

## 캐릭터 (눈높이 버전)
HariShimSing 스티커 원본을 `assets/stickers/`에 넣으면 그 캐릭터를 그대로 장면별로 배치해 애니메이션합니다.
텔레그램 봇 토큰(@BotFather에서 무료 발급)이 있으면 팩 전체를 자동으로 받을 수 있습니다.
```bash
TELEGRAM_BOT_TOKEN=... node engine/fetch-stickers.mjs HariShimSing
```
정지 스티커는 PNG, 영상 스티커는 PNG와 알파 채널이 있는 ProRes 4444 `.mov`로 변환됩니다. 목록은 `manifest.json`에 저장됩니다.
지금 미리보기의 고양이는 그 스티커를 참고해 그린 임시 캐릭터입니다.

## ElevenLabs (내레이션 · 음악 · 효과음)
```bash
export ELEVENLABS_API_KEY=...          # 키는 커밋하지 마세요
export ELEVENLABS_VOICE_ID=...         # 선택: Voice Library의 한국어 보이스
node engine/elevenlabs.mjs all
npm run build
```
- `voice`: 커머셜 11줄(전문가 톤 보이스오버) + 눈높이 26줄 내레이션 생성 → 실제 음성 길이로 모든 장면 타이밍 자동 재조정
  - 목소리는 Voice Library에서 신뢰감 있는 한국어 남성 내레이터(중년, 정보 전달형)를 자동으로 골라 계정에 추가하고 `build/voice.json`에 기록합니다. 직접 고르려면 `ELEVENLABS_VOICE_ID`를 지정하세요.
- `music`: 두 버전 각각 영상 길이에 딱 맞춘 배경음악 (프롬프트는 `engine/elevenlabs.mjs`의 `MUSIC`)
- `sfx`: 장면 전환 효과음 (whoosh · impact · boom · hit · riser · ticks)
- `mix`: 음악은 내레이션 아래로 자동 덕킹, 효과음은 컷 타이밍에 배치 → `dist/audio/<id>_mix.wav`
- 클라우드 세션에서 돌리려면 환경 설정에 `ELEVENLABS_API_KEY`를 환경 변수로 넣고 `api.elevenlabs.io`를 허용 도메인에 추가하세요.

## 수정 · 다시 빌드
```bash
npm install
npm run build          # 컴파일 → AE 스크립트 → 미리보기 MP4
```
- `npm run compile`: 스토리보드만 컴파일 (`build/*.json`)
- `npm run jsx`: AE 스크립트만 다시 생성
- `node engine/render.mjs --only pro --stills 3,8.5`: 특정 시점 스틸 확인
- `node engine/test-ae-mock.mjs`: AE 스크립트를 모의 AE 환경에서 실행해 오류 검사
- `node engine/test-expr.mjs`: AE 익스프레션과 미리보기 계산이 같은지 검사
- `python3 engine/temp_audio.py`: 임시 음악 다시 생성

## 표현 원칙 (원문 브리프의 게시 전 확인사항 반영)
- 100–200ms, 300 Mgas/s는 **목표 · 사양**으로만 표기, 메인넷은 **2026.11.09 예정**
- 25 / 25 / 50은 **시퀀서 수익** 기준 (전체 가스비 아님), 시행 시점은 공식 공지 확인
- HyperCore read/write는 **메인넷 약 4주 뒤 업그레이드 계획**, 비동기 · 원자성 없음
- 상장 · 에어드롭 · 보상 · 수익은 보장하지 않음, ELO는 미출시, Eloscape 낙첨 시 원금 손실 가능
- 마지막 장면에 "정보 제공 목적이며 투자 권유가 아님" 고지
