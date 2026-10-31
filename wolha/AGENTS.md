# AGENTS.md — 「월하노인을 잡아라」 스토리보드 작업 지침 (Codex용)

이 폴더(`wolha/`)는 숏폼 사극 로코 「월하노인을 잡아라」(20부작, 회당 3분)의 스토리보드 에셋을 만드는 작업장이다. 저장소의 다른 폴더(`index.html`, `.github/` 등)는 별개 프로젝트이니 건드리지 않는다.

## 목표

`storyboards/ep02.json` ~ `ep20.json`의 빈 `shots`를 채운다. 기준은 다음 세 가지다.
1. 대본: `shortform/epNN.md`
2. 기법 규칙: `docs/storyboard_guide.md`
3. 견본: `storyboards/ep01.json`. 밀도, 문장 톤, 필드 쓰는 법을 이 파일에 맞춘다.

## 먼저 읽을 것 (순서대로)

1. `docs/storyboard_guide.md`: 샷 크기·앵글·무빙 코드, 180도 법칙, 모티프 규칙, 검수 규칙
2. `storyboards/ep01.json`: 완성된 견본
3. `bible/characters.json`, `bible/locations.json`: 인물·장소 id, 외형, 화면 방향(axis)
4. `shortform/epNN.md`: 작업할 회차 대본
5. 필요하면 `source/`: 원작 16부작(회당 60분) 대본과 기획안. 디테일 참고용이며 숏폼 대본과 다르면 **숏폼 대본이 우선**한다.

## 회차 하나를 작업하는 순서

```bash
cd wolha
python3 tools/skeleton.py 5                  # 뼈대가 없거나 대본이 바뀌었을 때만
# storyboards/ep05.json 의 각 scene.shots 를 채운다 (status 를 "draft" 로)
python3 tools/validate.py storyboards/ep05.json
python3 tools/check_hangul.py storyboards/ep05.json   # 깨진 한글 음절 확인
python3 tools/render.py 5                    # out/ep05.html 콘티 시트 확인
python3 tools/board.py                       # out/board.html 전체 보드 갱신
python3 tools/gen_images.py 5                # (선택) 이미지 프롬프트만 기록, 드라이런
```

검사에서 오류가 0이고 경고를 다 정리했으면 `status`를 `"review"`로 바꾼다. `"final"`은 사람이 승인한 뒤에만 쓴다.

## 반드시 지킬 규칙

- **대본을 고치지 않는다.** `shortform/`, `source/`는 읽기 전용이다. 대본 오류를 발견하면 고치지 말고 PR 설명이나 `notes`에 적는다.
- **대사는 원문 그대로.** `dialogue.line`은 대본 대사를 글자 그대로 옮긴다. 괄호 지문은 빼고 `mode`(ON/OS/VO/N/WHISPER)로 표시한다. 대본의 모든 대사가 어느 샷엔가 들어가야 한다(검사기가 누락을 경고한다).
- **이야기를 지어내지 않는다.** 대본에 없는 사건, 대사, 인물을 추가하지 않는다. 인서트, 리액션, 공간 소개 같은 **촬영상의 컷**은 자유롭게 넣어도 된다.
- **타임코드를 지킨다.** 씬 샷 길이의 합은 그 씬의 `tc_in`~`tc_out` 구간과 같게 맞춘다. 회차 합계는 180초다.
- **밀도.** 회차당 샷 30~60개, 평균 3~5초. 숏폼이라 마스터 샷은 짧게, 리액션은 꼭 넣는다.
- **id 규칙.** 샷 id는 `S씬2자리-번호2자리`(예: `S03-04`)이고 씬마다 01부터 센다. 인물·장소는 `bible`에 있는 id만 쓴다. 새 단역이 필요하면 `extras`를 쓰고, 반복해서 나오면 `bible/characters.json`에 추가한다(그때는 `prompt_en`도 쓴다).
- **모티프.** 귀 빨개짐(EAR_RED), 지붕 위 흑립(ROOFTOP_HEUKRIP), 문틈(DOOR_GAP), 우산(UMBRELLA), 엽전 비(COIN_RAIN) 같은 반복 모티프는 가이드 8장의 구도 약속을 따르고 `motifs`에 태그한다. 흑립은 1~2화에서 얼굴과 왼손을 보이지 않는다. 왼손 흉터는 3화 S#5에서 처음 보인다.
- **연속성.** 의상·부상 상태를 회차 사이에 이어 간다. 예:
  - 강수: 왼쪽 팔뚝 붕대 11~18화(15화 "성한 손", 16화 "붕대 감은 팔"), 오른쪽 목덜미 무명 16~18화. 19화부터 둘 다 없음
  - 율: 왼쪽 옆구리 상처 11화~, 가슴 상처 17화~ (붕대는 옷 안에)
  - 정겸: 17화 S#6에서 갓을 잃고 18화 S#3까지 맨상투, 18화 S#4부터 다시 갓
  - **차림이 평소와 다르면 씬이나 샷에 `looks`를 단다.** 이미지 프롬프트가 bible 의 `prompt_variants`로 바뀐다.
    - 정겸 `palace`(단령·사모): 궐 안 장면 전부(1화 S#2, 7화 S#3, 10화 S#3, 12화 S#1, 14화 S#5, 16화 S#5), 8화 세검정 혼담, 2화 회상 컷
    - 정겸 `bareheaded`(맨상투): 17화 S06-06~18화 S#3
    - 정조 `disguise`(삿갓 선비)와 안 내관 `disguise`(무명옷): 11화 S#3 / 정조 `procession`(융복·전립): 19화 S#5, 20화 S#1~S#2
  - 달래: 19~20화 격쟁 장면은 흰 소복
- **고증.** 1792~1793년 한양이 무대다. 전기 조명, 근대 소품, 마고자 같은 후대 복식은 쓰지 않는다. 확실하지 않으면 `notes`에 `고증확인:`으로 적는다.
- **image_prompt는 영어로, 장면 내용만** 적는다. 그림에 글자를 넣으라고 쓰지 않는다.
- **네트워크 호출 금지(기본).** `gen_images.py --run`은 사용자가 명시적으로 요청하고 `OPENAI_API_KEY`가 있을 때만 실행한다. Codex 내장 이미지 생성으로 패널을 만드는 일은 아래 "이미지 에셋" 절을 따른다.

## 이미지 에셋 (패널 그림)

콘티 패널마다 실제 그림을 만들어 `assets/frames/epNN/<샷id>.jpg`로 채운다. 작업 목록은 `assets/jobs/`에 미리 만들어 두었다(`python3 tools/codex_jobs.py`로 다시 만든다).

1. **레퍼런스 먼저.** `assets/jobs/refs.jsonl`의 기본 인물 시트(14명, `ref`에 `__`가 없는 줄) → 차림 변형 시트(5장, `refs`의 기본 시트를 참고 이미지로 붙여 같은 얼굴로) → 장소 그림 순서로 만든다. 각 줄의 `prompt`로, `size` 크기, 글자 없이 생성해 `out` 경로에 저장한다. 인물 시트는 사람이 승인한 뒤 장소로 넘어간다.
   끝나면 `python3 tools/compress_frames.py --refs` → `python3 tools/codex_jobs.py`(작업 목록이 새 레퍼런스 경로를 가리키게 다시 만든다).
2. **패널.** `assets/jobs/epNN.jsonl`의 한 줄이 샷 하나다. `refs`에 적힌 그림을 참고 이미지로 붙이고 `prompt`로 생성해 `out` 경로에 저장한다. 얼굴·의상·세트는 레퍼런스와 같아야 한다. 그림에 글자·말풍선을 넣지 않는다(INSERT 샷의 글씨는 빈 종이나 흐린 붓자국으로).
3. **회차가 끝나면** 순서대로:
   ```bash
   python3 tools/compress_frames.py 5        # 16:9로 잘라 1280x720 JPEG, 원본 PNG 삭제
   python3 tools/codex_jobs.py --attach 5    # ep05.json 의 image 필드 채우기
   python3 tools/validate.py storyboards/ep05.json
   python3 tools/render.py 5 && python3 tools/board.py
   ```
   `out/ep05.html`을 열어 패널이 `frame`/`action` 설명, 샷 크기, 화면 방향(axis)과 맞는지 보고, 크게 어긋난 컷은 다시 생성한다.
4. **진행 확인:** `python3 tools/codex_jobs.py --status`

## 완료 기준 (회차별)

- [ ] `python3 tools/validate.py storyboards/epNN.json`: 오류 0, 경고 0(남는 경고는 `notes`에 이유를 적는다)
- [ ] 모든 씬에 샷이 있고, 샷 합계가 180초 ±5%
- [ ] 대본의 대사가 모두 들어감
- [ ] 각 씬 첫 샷 `continuity`에 화면 축이 적혀 있음
- [ ] 엔딩 샷이 다음 회 훅으로 끝남(FREEZE, CRANE_UP 또는 대사)
- [ ] `out/epNN.html`을 열어 패널 순서와 흐름을 눈으로 확인
- [ ] `status: "review"`

## 커밋

- 회차 하나에 커밋 하나. 메시지 예: `storyboard: ep05 「연애 자료조사」 샷 41개`
- `out/`은 생성물이라 커밋하지 않는다(.gitignore).
- 이미지는 `compress_frames.py`로 줄인 JPEG만 커밋한다(PNG 원본 커밋 금지). 메시지 예: `assets: ep05 패널 41장`, `assets: 레퍼런스 시트`
