#!/usr/bin/env python3
"""숏폼 대본(shortform/epNN.md)에서 스토리보드 뼈대(storyboards/epNN.json)를 만든다.

씬 제목, 타임코드, 장소 id, 시간대, 등장인물, 대본 원문(source_text)을 채우고
shots 는 빈 배열로 둔다. 샷은 사람이나 Codex 가 docs/storyboard_guide.md 를 보고 채운다.

사용법:
    python3 wolha/tools/skeleton.py 2            # 2화 뼈대 생성
    python3 wolha/tools/skeleton.py 2-20         # 2~20화
    python3 wolha/tools/skeleton.py all --force  # 이미 있는 파일도 덮어씀(주의)

이미 shots 가 채워진 파일은 --force 없이 덮어쓰지 않는다.
"""
from __future__ import annotations

import argparse
import sys

from wolha_lib import (
    SHORTFORM_DIR, STORYBOARD_DIR, dump_json, load_json, match_location,
    name_to_id, parse_shortform, time_code,
)

SERIES = "월하노인을 잡아라 (숏폼 20부작)"


def episodes_from_arg(arg: str) -> list[int]:
    if arg == "all":
        return list(range(1, 21))
    if "-" in arg:
        a, b = arg.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in arg.split(",")]


def guess_characters(lines: list[str], names: dict[str, str]) -> list[str]:
    text = "\n".join(lines)
    found: list[str] = []
    for name in sorted(names, key=len, reverse=True):
        cid = names[name]
        if cid in ("extras",) or cid.startswith("N:"):
            continue
        if name in text and cid not in found:
            found.append(cid)
    return found


def build(ep_no: int) -> dict:
    md = SHORTFORM_DIR / f"ep{ep_no:02d}.md"
    if not md.exists():
        raise FileNotFoundError(f"{md} 가 없습니다. 먼저 tools/split_episodes.py 로 대본을 나누세요.")
    ep = parse_shortform(md)
    names = name_to_id()
    scenes = []
    prev_loc = "flashback_misc"
    for sc in ep["scenes"]:
        if sc["heading"].startswith("같은 장소"):
            loc = prev_loc  # '같은 장소'는 앞 씬 장소를 이어받는다
        else:
            loc = match_location(sc["heading"]) or "flashback_misc"
        prev_loc = loc
        scenes.append({
            "id": sc["id"],
            "heading": sc["heading"],
            "location": loc,
            "time": time_code(sc["heading"]),
            "tc_in": sc["tc_in"],
            "tc_out": sc["tc_out"],
            "characters": guess_characters(sc["lines"], names),
            "summary": "",
            "source_text": "\n".join(sc["lines"]),
            "shots": [],
        })
    return {
        "series": SERIES,
        "episode": ep_no,
        "title": ep["title"],
        "hook": ep["hook"],
        "runtime_sec": 180,
        "aspect": "16:9",
        "status": "skeleton",
        "scenes": scenes,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episodes", help="예: 2 / 2-20 / 3,5,7 / all")
    ap.add_argument("--force", action="store_true", help="샷이 채워진 기존 파일도 덮어쓰기")
    args = ap.parse_args(argv)

    for n in episodes_from_arg(args.episodes):
        out = STORYBOARD_DIR / f"ep{n:02d}.json"
        if out.exists() and not args.force:
            existing = load_json(out)
            if any(s.get("shots") for s in existing.get("scenes", [])):
                print(f"[건너뜀] {out.name}: 이미 샷이 있습니다 (--force 로 덮어쓰기)")
                continue
        data = build(n)
        dump_json(data, out)
        print(f"[생성] {out.relative_to(STORYBOARD_DIR.parent)}  씬 {len(data['scenes'])}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
