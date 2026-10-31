#!/usr/bin/env python3
"""20부작 번호로 만든 패널 그림을 24부작 번호로 옮겨 붙인다.

24부작으로 늘리면서 8·13·18·22화가 새로 들어가 기존 회차 번호가 밀렸다.
20부작 시절에 만든 그림(assets/frames/ep01~20/<샷 id>.jpg)을 새 번호의
폴더로 복사하고, 스토리보드 image 필드를 연결한다.

    python3 tools/import_frames.py ../옛작업폴더/wolha          # 옛 wolha 폴더(또는 그 assets, frames 폴더)
    python3 tools/import_frames.py ../옛작업폴더/wolha --dry-run  # 복사하지 않고 무엇이 어디로 가는지만
    python3 tools/import_frames.py SRC --force                  # 이미 있는 그림도 덮어쓴다

번호 대응 (옛 → 새)
    1~7 → 1~7 · 8~11 → 9~12 · 12~15 → 14~17 · 16~18 → 19~21 · 19~20 → 23~24
    샷 id 는 그대로다. 단 옛 20화(새 24화) S#3 은 구경꾼 컷이 끼어들어
    S03-05~08 → S03-06~09 로 하나씩 밀린다.
    S00-* ('지난 대목')은 옮기지 않는다. codex_jobs --attach 가 원본 그림에서 다시 만든다.

레퍼런스 시트(assets/refs/chars, locs)는 이름이 같으므로 SRC 에 있으면 그대로 복사한다.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codex_jobs import EXTS, attach  # noqa: E402
from wolha_lib import FRAMES_DIR, ROOT, STORYBOARD_DIR, load_json  # noqa: E402

REFS_DIR = ROOT / "assets" / "refs"


def new_episode(n: int) -> int:
    if n <= 7:
        return n
    if n <= 11:
        return n + 1
    if n <= 15:
        return n + 2
    if n <= 18:
        return n + 3
    return n + 4


# 옛 번호 기준 샷 id 가 바뀐 곳: {옛 회차: {옛 id: 새 id}}
ID_SHIFT = {20: {"S03-05": "S03-06", "S03-06": "S03-07", "S03-07": "S03-08", "S03-08": "S03-09"}}


def find_dirs(src: Path) -> tuple[Path, Path | None]:
    """SRC 가 wolha 폴더든 assets 폴더든 frames 폴더든 frames·refs 위치를 찾는다."""
    for cand in (src / "assets", src / "wolha" / "assets", src):
        if (cand / "frames").is_dir():
            refs = cand / "refs"
            return cand / "frames", (refs if refs.is_dir() else None)
    if any(src.glob("ep[0-9][0-9]")):
        return src, None
    sys.exit(f"{src} 에서 frames 폴더(ep01~ 하위 폴더)를 찾지 못했습니다")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", type=Path, help="20부작 그림이 있는 옛 wolha 폴더 (또는 assets, frames 폴더)")
    ap.add_argument("--dry-run", action="store_true", help="복사하지 않고 대응표만 출력")
    ap.add_argument("--force", action="store_true", help="이미 있는 그림도 덮어쓴다")
    a = ap.parse_args()

    frames_src, refs_src = find_dirs(a.src.resolve())
    if frames_src.resolve() == FRAMES_DIR.resolve():
        sys.exit("SRC 가 이 저장소의 frames 폴더와 같습니다. 옛 작업 폴더를 가리켜 주세요")
    if any((frames_src / f"ep{n:02d}").is_dir() for n in range(21, 25)):
        sys.exit("SRC 에 ep21~24 폴더가 있습니다. 이미 24부작 번호라 옮길 필요가 없습니다")

    copied, skipped, touched = 0, 0, set()
    for n in range(1, 21):
        d = frames_src / f"ep{n:02d}"
        if not d.is_dir():
            continue
        m = new_episode(n)
        for f in sorted(d.iterdir()):
            if f.suffix.lower() not in EXTS or f.stem.startswith("S00-"):
                continue
            sid = ID_SHIFT.get(n, {}).get(f.stem, f.stem)
            dst = FRAMES_DIR / f"ep{m:02d}" / f"{sid}{f.suffix.lower()}"
            if dst.exists() and not a.force:
                skipped += 1
                continue
            if a.dry_run:
                print(f"ep{n:02d}/{f.name} → ep{m:02d}/{dst.name}")
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
            copied += 1
            touched.add(m)

    refs = 0
    if refs_src:
        for f in sorted(refs_src.rglob("*")):
            if f.is_file() and f.suffix.lower() in EXTS:
                dst = REFS_DIR / f.relative_to(refs_src)
                if dst.exists() and not a.force:
                    continue
                if not a.dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dst)
                refs += 1

    verb = "옮길" if a.dry_run else "옮긴"
    print(f"{verb} 패널 {copied}장 · 이미 있어 건너뜀 {skipped}장 · 레퍼런스 {refs}장")
    if a.dry_run:
        return 0

    # image 필드 연결. '지난 대목' 재사용 그림(image_from)도 여기서 만든다
    for p in sorted(STORYBOARD_DIR.glob("ep*.json")):
        attach(int(p.stem[2:]))

    # 회차별로 아직 그림이 없는 샷 수
    print("\n회차  그림/샷  남은 샷")
    for p in sorted(STORYBOARD_DIR.glob("ep*.json")):
        data = load_json(p)
        shots = [sh for sc in data["scenes"] for sh in sc["shots"]]
        have = sum(1 for sh in shots if sh.get("image"))
        print(f"ep{data['episode']:02d}  {have:>3}/{len(shots):<3}  {len(shots) - have}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
