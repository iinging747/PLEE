#!/usr/bin/env python3
"""20부작 전체 콘티 보드(한 장짜리 HTML) 만들기.

storyboards/ep01~20.json 을 모두 읽어 tools/board_template.html 에 넣고 out/board.html 로 쓴다.
회차 레일, 3분 타임라인, 모티프 필터, 샷별 이미지 프롬프트 복사가 들어 있다.

    python3 tools/board.py            # out/board.html
"""
from __future__ import annotations

import json
import sys

from wolha_lib import OUT_DIR, ROOT, STORYBOARD_DIR, characters, load_json, tc_to_sec

KEEP = ["id", "size", "angle", "move", "lens_mm", "characters", "frame", "action", "dialogue", "sound",
        "insert_text", "transition", "duration_sec", "motifs", "continuity", "image_prompt", "notes", "image"]


def main() -> int:
    chars = {}
    for c in characters():
        chars[c["id"]] = c["names"][0] if c.get("names") else c["id"]
    chars["N:gangsu"] = "강수(N)"
    chars["extras"] = "단역"
    eps = []
    for path in sorted(STORYBOARD_DIR.glob("ep*.json")):
        d = load_json(path)
        scenes = []
        for s in d["scenes"]:
            scenes.append({
                "id": s["id"], "heading": s["heading"], "time": s["time"], "tc_in": s["tc_in"], "tc_out": s["tc_out"],
                "tc_in_sec": tc_to_sec(s["tc_in"]), "mood": s.get("mood", ""), "summary": s.get("summary", ""),
                "shots": [{k: sh[k] for k in KEEP if k in sh} for sh in s.get("shots", [])],
            })
        eps.append({
            "episode": d["episode"], "title": d["title"], "hook": d.get("hook", ""), "status": d.get("status", ""),
            "runtime": d.get("runtime_sec", 180), "shots": sum(len(s["shots"]) for s in scenes), "scenes": scenes,
        })
    data = json.dumps({"episodes": eps, "chars": chars, "imgBase": "../"}, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")
    tpl = (ROOT / "tools" / "board_template.html").read_text(encoding="utf-8")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "board.html"
    out.write_text(tpl.replace("/*__DATA__*/null", data), encoding="utf-8")
    n = sum(e["shots"] for e in eps)
    print(f"[보드] {out.relative_to(ROOT)}  회차 {len(eps)} · 샷 {n} · {out.stat().st_size // 1024}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
