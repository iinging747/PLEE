#!/usr/bin/env python3
"""생성된 패널 이미지를 16:9 JPEG 로 줄인다(저장소 용량 관리).

이미지 생성기는 보통 1536x1024(3:2) PNG 를 준다. 콘티는 16:9 이므로 가운데를 16:9 로 잘라
1280x720 JPEG(품질 82)로 저장하고 원본 PNG 는 지운다. 한 장 200KB 안팎이 된다.

    python3 tools/compress_frames.py 5            # assets/frames/ep05/*.png
    python3 tools/compress_frames.py 5 --keep     # 원본 PNG 남기기
    python3 tools/compress_frames.py --refs       # assets/refs/ 도 같은 방식(레퍼런스는 자르지 않음)

Pillow 가 있으면 Pillow 를, 없으면 ffmpeg 를 쓴다. 둘 다 없으면 `pip install pillow`.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from wolha_lib import FRAMES_DIR, ROOT

W, H, Q = 1280, 720, 82


def convert(src: Path, dst: Path, crop: bool) -> None:
    try:
        from PIL import Image  # type: ignore
        im = Image.open(src).convert("RGB")
        if crop:
            w, h = im.size
            th = round(w * 9 / 16)
            if th <= h:
                top = (h - th) // 2
                im = im.crop((0, top, w, top + th))
            else:
                tw = round(h * 16 / 9)
                left = (w - tw) // 2
                im = im.crop((left, 0, left + tw, h))
            im = im.resize((W, H), Image.LANCZOS)
        else:
            im.thumbnail((1600, 1600))
        im.save(dst, "JPEG", quality=Q, optimize=True, progressive=True)
        return
    except ImportError:
        pass
    if not shutil.which("ffmpeg"):
        raise SystemExit("Pillow 도 ffmpeg 도 없습니다. `pip install pillow` 후 다시 실행하세요.")
    vf = f"crop='min(iw,ih*16/9)':'min(ih,iw*9/16)',scale={W}:{H}" if crop else "scale='min(1600,iw)':-2"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-vf", vf, "-q:v", "3", str(dst)], check=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episodes", nargs="*", type=int)
    ap.add_argument("--keep", action="store_true", help="원본 PNG 를 지우지 않는다")
    ap.add_argument("--refs", action="store_true", help="assets/refs/ 를 처리")
    a = ap.parse_args(argv)
    targets: list[tuple[Path, bool]] = []
    if a.refs:
        targets += [(p, False) for p in sorted((ROOT / "assets" / "refs").rglob("*.png"))]
    for n in a.episodes:
        targets += [(p, True) for p in sorted((FRAMES_DIR / f"ep{n:02d}").glob("*.png"))]
    if not targets:
        print("처리할 PNG 가 없습니다.")
        return 0
    before = after = 0
    for src, crop in targets:
        dst = src.with_suffix(".jpg")
        before += src.stat().st_size
        convert(src, dst, crop)
        after += dst.stat().st_size
        if not a.keep:
            src.unlink()
    print(f"[압축] {len(targets)}장  {before / 1e6:.1f}MB → {after / 1e6:.1f}MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
