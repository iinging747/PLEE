# PIXIE 유튜브 시작 티저 (v3)

2:00 · 1920×1080 · 30fps · H.264 + AAC 48kHz · -14 LUFS / -1.2 dBTP (유튜브 기준)

## 구성 (BGM 128BPM 그리드에 컷·자막·효과 정렬)

| 시간 | 파트 | 내용 |
|---|---|---|
| 0:00–0:15 | 콜드 오픈 | 눈 슬릿 리빌 → 크롬 *Cold. / Calm. / Calculated.* → 심박 라인 |
| 0:15–0:30 | 첫 번째 세계 | 컨퍼런스 트레이딩 세션·거래소 부스·마스크 셀피, 글리치 컷, 라이저 |
| 0:30 | 드롭 | **01 Trading** (Blender 크롬 타이틀) |
| 0:38 | **02 Lifestyle** | 집요리(단새우 타르타르·카르파초·랍스터) → Saint Pierre 파인다이닝 |
| 0:53 | 나이트 럭셔리 | 샴페인·칵테일 3분할 패널 |
| 1:00 | **03 Beauty** (브레이크다운) | 슬로모 눈, 블룸·라이트릭·파티클 |
| 1:08 | 밖으로 | 슈퍼트리 → 유리문 → 하늘 |
| 1:15 | **04 Travel** | ICN→SIN 항로 그래픽, 공항·라운지·기내 → 마리나베이 → TOKEN2049 |
| 1:30 | 나이트 & 파티 | 3분할 패널 |
| 1:38 | 클라이맥스 | 반박자 몽타주 + 챕터 단어 플래시 → *More than a trader* |
| 1:45 | 정적 | 눈이 카메라를 응시 → 음악 하드컷 → 암전 · 심장박동 |
| 1:53 | 로고 | 크롬 PIXIE 로고 → *Coming soon* (FIRST LIVE) |

## 빌드

```bash
python make.py titles   # Blender(bpy) 크롬 타이틀 스틸 → work/bl/
python make.py audio    # BGM + 효과음 + 현장음 믹스 → dist/PIXIE_teaser_mix.wav
python make.py video    # 합성·렌더·먹싱 → dist/PIXIE_teaser_1080p.mp4
```

- `timeline.py` — 편집 결정 목록(EDL): 컷, 자막, 트랜지션, 효과음 타이밍 전부
- `engine/` — 합성 엔진(이펙트·타이포·그래픽·오디오), `blender/titles.py` — 크롬 타이틀/로고
- 원본 소스 경로는 `PIXIE_MEDIA` 환경변수(manifest.tsv 포함 폴더)

## 교체 포인트

- **폰트(산돌구름)**: `assets/fonts/licensed/kr.otf`(자막), `kr_title.otf`, `label.otf`를 넣으면 자동 적용. 이 폴더는 git에 올리지 않음.
- **라이브 날짜**: `timeline.py`의 `LIVE_DATE = "2026. 12. 05"` 처럼 지정.
- **효과음(ElevenLabs)**: Actions → *PIXIE ElevenLabs SFX* 실행(API 키 입력) 또는 `sfx/<이름>.wav` 직접 추가 → `python make.py audio`. 프롬프트는 `tools/elevenlabs_sfx.json`.
- **대용량 원본 클립**(흠.mp4, 키보드 엔터, 새우다지기 등): Drive 커넥터 10MB 제한으로 이번 버전은 10MB 이하 클립 + 사진으로 구성. 원본이 들어오면 `media_extra/`에 두고 timeline에서 해당 구간을 교체.
