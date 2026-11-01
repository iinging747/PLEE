# PIXIE 티저 인수인계 (클라우드 세션 → 로컬 세션)

이 문서는 사용자의 로컬 컴퓨터(윈도우, 애프터이펙트·산돌구름 폰트·엔바토 템플릿 보유)에서 이어서 작업할 Claude 세션을 위한 메모다.

## 기획 의도 (사용자가 처음 준 콘티)
- 처음엔 **냉철한 트레이더**처럼 등장
- 중반엔 **완전히 다른 여성스러운 모습**: 요리, 뷰티, 자기관리
- 후반엔 **더 큰 세계를 사는 사람**이라는 인상: 여행, 싱가포르, TOKEN2049
- 마지막에 **채널 이름(PIXIE)과 첫 라이브** 공개 → 다음 영상을 보게 만들기
- 배너 태그라인: "More than a trader" / TRADING · LIFESTYLE · BEAUTY · TRAVEL
- 팔레트: Deep Plum, Violet, Champagne, Silver, Black
- 레퍼런스: 2026 챔피언스 주제곡 티저, T1 vs WBG "THE GLORY" Worlds 2023 Finals Tease

## 현재 상태 (v4, 1:04)
- `timeline.py` 가 편집 전체. `kit.py` 는 공용 헬퍼, `engine/` 은 파이썬 합성 엔진, `blender/` 는 크롬 타이틀.
- BGM(`assets/audio/bgm.mp3`, 원본 wav는 별도)을 128BPM 프레이즈 단위로 잘라 1:04로 편집 (`BGM_SEGMENTS`).
- 대사(자막 한/영 + 후시녹음 슬롯 vo01~vo06): `VO_SCRIPT.md`
  1. 감정은 차갑게. 차트는 정확하게.
  2. 흔들리면, 지는 거야.
  3. 근데, 차트만 보고 살진 않아.
  4. 나를 가꾸는 것도, 투자니까.
  5. 트레이더? 그게 다가 아니야.
  6. 나는 픽시. 첫 라이브에서 보자.
- 결과물: `dist/PIXIE_teaser_preview.mp4` (압축본)

## 사용자 피드백 (중요)
- 싫어함: AI 같은 슬로건 문구("같은 손, 다른 리듬" 류), 챕터 카드 공식(01/04 TRADING…), 얇은 세리프 폰트, 늘어지는 구성, 텍스트가 안 보이는 배치, 엉성한 모션그래픽
- 원함: 애프터이펙트/엔바토 수준의 세련되고 집중되는 모션그래픽, 빠른 컷, 자간 좁게, 한/영 혼용 자막, 산돌 폰트, 얼굴 보정, 화장 영상 사용
- BGM은 나중에 일레븐랩스로 새로 만들 예정 (사용자 컴퓨터에서)
- 답변은 짧고 자연스러운 한국어로. 표·과한 서식 지양.

## 이 컴퓨터에서 할 일
1. 애프터이펙트로 재제작: 엔바토 템플릿을 `aerender.exe` + ExtendScript(JSX)로 채워 렌더 (텍스트·푸티지 교체 자동화).
   후보: [스타일리시 패션 프로모](https://elements.envato.com/stylish-fashion-promo-UYJR6AC), [깔끔한 패션 오프너](https://elements.envato.com/fashion-promo-opener-H43NSFN), [패션 프로모](https://elements.envato.com/fashion-promo-VSGC53U), [패션 오프너](https://elements.envato.com/fashion-opener-3H9ZUYU), [글리치 트레일러](https://elements.envato.com/glitch-trailer-VBDV5YK), [필름 번 팩](https://elements.envato.com/film-burns-pack-5URFCTZ), [라이트릭·번 팩](https://elements.envato.com/light-transitions-burns-ae-project-footages-VG34KQU)
2. 산돌 폰트: 산돌 정체(히어로 문장), 산돌명조 Neo1(자막), 산돌고딕 Neo1(라벨). 파이썬 엔진을 쓸 경우 `assets/fonts/licensed/kr.otf` 등에 두면 자동 적용(git 제외).
3. 원본 영상: 구글 드라이브 폴더 `13fKEs-p6YEVltB5JbhSt23w9FDT6J-mm` (소유 pixiescrypto). 클라우드에선 10MB 제한으로 못 썼던 핵심 클립을 이제 쓸 수 있음:
   흠.mp4(차트 노트북 닫기), 키보드 엔터.mp4, 새우다지기, 래디시컷, 단새우타르타르, 연어모양, IMG_6656(완성 식탁), 나트랑 바닷가, IMG_6164/6166(TOKEN2049 입장), 20261007_140349(무대), IMG_5973(마리나베이), IMG_6366, 20261003_203245(야간 수영장), 파티 클립들.
   파일별 설명은 사용자가 준 "PIXIE 영상 파일별 정리" 문서와 `media_manifest.tsv`(사진 P001~P198 인덱스 매핑) 참고.
4. 화장 영상 3개(사용자 업로드, 레터박스된 와이드 밴드): `media_extra/makeup_look.mp4`(crop 1280:340:0:190), `makeup_lip.mp4`(1920:628:0:216), `makeup_eye.mp4`(1280:344:0:188). git에 없으니 사용자에게 받아서 넣을 것.
5. 라이브 날짜가 정해지면 `LIVE_DATE` 반영.

## 파이썬 엔진을 로컬에서 돌릴 때
- 필요: Python 3.11+, ffmpeg, `pip install numpy opencv-python-headless pillow scipy soundfile librosa`
- 사진은 HEIC가 많아 `pillow-heif`로 JPEG 변환 후 manifest 재생성 필요 (`PIXIE_MEDIA` 환경변수로 폴더 지정)
- `python make.py audio` → `python make.py video`
