# AGENTS.md

이 저장소에는 서로 무관한 프로젝트가 함께 들어 있다.

| 경로 | 내용 |
|---|---|
| `wolha/` | 숏폼 사극 로코 「월하노인을 잡아라」(20부작, 회당 3분) 대본과 스토리보드 에셋 |
| `index.html`, `.github/` | 별개 프로젝트. `wolha` 작업 중에는 건드리지 않는다 |

스토리보드 작업 지침은 **`wolha/AGENTS.md`** 에 있다. `wolha/` 아래 파일을 다룰 때는 그 문서를 먼저 읽는다.

빠른 시작:

```bash
cd wolha
python3 tools/validate.py          # 전체 스토리보드 검사
python3 tools/render.py            # out/*.html 콘티 시트 생성
```
