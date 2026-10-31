# 「월하노인을 잡아라」 숏폼 스토리보드 에셋

1792년 한양을 배경으로 한 사극 로맨틱 코미디 미스터리다. 20부작이고 회당 3분이다. 이 폴더는 대본을 콘티로 바꾸는 작업장이다. Codex 같은 코딩 에이전트가 이어서 작업할 수 있도록 규칙, 데이터 형식, 도구를 함께 담았다.

## 구성

```
wolha/
├── AGENTS.md                  Codex 작업 지침 (여기부터 읽기)
├── TASKS.md                   회차별 진행표와 Codex에 줄 프롬프트
├── docs/storyboard_guide.md   스토리보드 기법 가이드 (샷 크기·앵글·무빙·모티프·검수 규칙)
├── shortform/ep01~20.md       숏폼 대본 (회당 3분, 씬별 타임코드)
├── source/                    원작 자료: 16부작 대본(회당 60분), 기획안, 1화 원작 스토리보드
├── bible/characters.json      인물 설정 (id, 외형, 의상, 이미지 프롬프트 토큰)
├── bible/locations.json       장소 설정 (id, 세트, 조명 동기, 화면 방향)
├── schema/storyboard.schema.json  스토리보드 JSON 형식
├── storyboards/ep01.json      ★ 견본 (완성, 샷 60개)
├── storyboards/ep02~20.json   뼈대 (씬·타임코드·장소·인물만 채움, shots 비어 있음)
├── tools/                     파이썬 도구 (표준 라이브러리만 사용)
│   ├── split_episodes.py      통합 대본 → 회차별 파일
│   ├── skeleton.py            대본 → 스토리보드 뼈대
│   ├── validate.py            형식·제작 규칙 검사
│   ├── render.py              콘티 시트 HTML / 샷 리스트 CSV / 프롬프트 JSONL
│   └── gen_images.py          (선택) 패널 이미지 생성, 기본은 드라이런
├── assets/frames/             생성된 패널 이미지 (epNN/샷id.png)
└── out/                       렌더 결과 (커밋 안 함)
```

## 빠른 사용법

```bash
cd wolha
python3 tools/validate.py                 # 전체 검사
python3 tools/render.py 1                 # out/ep01.html 생성 → 브라우저로 열기
python3 tools/gen_images.py 1             # 1화 이미지 프롬프트를 out/ep01_image_requests.jsonl 에 기록
OPENAI_API_KEY=... python3 tools/gen_images.py 1 --run --limit 1   # 한 컷만 실제 생성해 보기
```

## Codex에서 이어 가기

1. 이 저장소를 Codex에 연결하고, 작업 디렉터리를 `wolha/`로 둔다.
2. `TASKS.md`의 "Codex에 줄 프롬프트"를 그대로 붙여 넣는다. 한 번에 2~3회차씩 맡기는 것을 권장한다.
3. 회차마다 `validate.py` 오류 0, `out/epNN.html` 확인, 커밋이 끝나면 다음 회차로 넘어간다.

## 출처

- 숏폼 대본과 원작 대본은 Claude Docs 문서 「월하노인을 잡아라」에서 내보냈다.
- 대본을 고칠 때는 문서 쪽을 고치고, 그다음 `source/shortform_20부작.md`를 다시 내보내 `tools/split_episodes.py source/shortform_20부작.md shortform`을 실행한다.
