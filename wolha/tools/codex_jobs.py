#!/usr/bin/env python3
"""Codex(또는 다른 이미지 생성기)로 콘티 패널 이미지를 만들 때 쓰는 작업 목록 도구.

1) 작업 목록 만들기
    python3 tools/codex_jobs.py                # assets/jobs/refs.jsonl + ep01~20.jsonl
    python3 tools/codex_jobs.py 5 6            # 5·6화만

   - refs.jsonl : 인물 레퍼런스 시트(assets/refs/chars/<id>.png)와
                  장소 레퍼런스(assets/refs/locs/<id>.png). 패널보다 먼저 만든다.
   - epNN.jsonl : 샷마다 한 줄. {"shot","out","size","prompt","refs"}
                  out 경로에 16:9 이미지를 저장하고, refs 의 그림을 참고 이미지로 붙여
                  얼굴·의상·세트를 회차 사이에서 똑같이 유지한다.

2) 만든 이미지를 스토리보드에 붙이기
    python3 tools/codex_jobs.py --attach 5     # assets/frames/ep05/*.png|jpg|webp → ep05.json image 필드

3) 진행 상황 보기
    python3 tools/codex_jobs.py --status
"""
from __future__ import annotations

import argparse
import json
import sys

from gen_images import STYLE, build_prompt, looks_for
from wolha_lib import FRAMES_DIR, ROOT, STORYBOARD_DIR, characters, dump_json, load_json, locations

JOBS_DIR = ROOT / "assets" / "jobs"
REFS_DIR = ROOT / "assets" / "refs"
EXTS = (".jpg", ".jpeg", ".webp", ".png")
# 레퍼런스 시트를 만들 인물(반복 등장하는 주·조연). 단역·내레이션은 제외
REF_CAST = ["dallae", "jeonggyeom", "yul", "gangsu", "yunhui", "heojin", "jeongjo", "heukrip",
            "meoksun", "ma_yeonggam", "an_naegwan", "lee_deokmu", "jongsagwan", "seoyeon"]
CONSISTENCY = ("Keep every character's face, hairstyle and costume identical to the attached reference sheets, "
               "and keep the set consistent with the attached location reference.")


def rel(p) -> str:
    return str(p.relative_to(ROOT))


def ref_path(kind: str, rid: str) -> str:
    """레퍼런스 그림 경로. 이미 만든(압축한) 파일이 있으면 그 확장자를 쓴다."""
    for ext in EXTS:
        p = REFS_DIR / kind / f"{rid}{ext}"
        if p.exists():
            return rel(p)
    return rel(REFS_DIR / kind / f"{rid}.png")


def ref_jobs(used_locs: set[str]) -> list[dict]:
    jobs = []
    chars = {c["id"]: c for c in characters()}
    for cid in REF_CAST:
        c = chars.get(cid)
        if not c or not c.get("prompt_en"):
            continue
        jobs.append({
            "ref": cid, "kind": "character", "out": rel(REFS_DIR / "chars" / f"{cid}.png"), "size": "1536x1024",
            "prompt": (f"{STYLE}. Character reference sheet on a plain warm-grey background: full-body front view, "
                       f"full-body three-quarter view, and a head-and-shoulders close-up of the same person, side by side. "
                       f"Even soft light, no props, no text. Character: {c['prompt_en']}"),
        })
        # 관복·변장처럼 차림이 다른 버전: 기본 시트를 참고 이미지로 붙여 같은 얼굴로 만든다
        for vname, vprompt in c.get("prompt_variants", {}).items():
            jobs.append({
                "ref": f"{cid}__{vname}", "kind": "character", "out": rel(REFS_DIR / "chars" / f"{cid}__{vname}.png"),
                "size": "1536x1024", "refs": [ref_path("chars", cid)],
                "prompt": (f"{STYLE}. Character reference sheet on a plain warm-grey background: full-body front view, "
                           f"full-body three-quarter view, and a head-and-shoulders close-up, side by side. Same person, same face "
                           f"as the attached reference sheet, only the clothing changes. Even soft light, no props, no text. "
                           f"Character: {vprompt}"),
            })
    for loc in locations():
        if loc["id"] in used_locs and loc.get("prompt_en"):
            jobs.append({
                "ref": loc["id"], "kind": "location", "out": rel(REFS_DIR / "locs" / f"{loc['id']}.png"), "size": "1536x1024",
                "prompt": f"{STYLE}. Empty establishing view of the set, no people, no text. Location: {loc['prompt_en']}",
            })
    return jobs


def episode_jobs(n: int) -> list[dict]:
    data = load_json(STORYBOARD_DIR / f"ep{n:02d}.json")
    chars = {c["id"]: c for c in characters()}
    locs = {l["id"]: l for l in locations()}
    size = "1024x1536" if data.get("aspect") == "9:16" else "1536x1024"
    jobs = []
    for sc in data["scenes"]:
        for sh in sc.get("shots", []):
            lk = looks_for(sc, sh)
            refs = [ref_path("chars", f"{c}__{lk[c]}" if lk.get(c) in chars[c].get("prompt_variants", {}) else c)
                    for c in sh.get("characters", []) if c in REF_CAST][:3]
            if sc["location"] in locs and sc["location"] != "flashback_misc":
                refs.append(ref_path("locs", sc["location"]))
            prompt = build_prompt(data, sc, sh, chars, locs)
            if refs:
                prompt += ". " + CONSISTENCY
            jobs.append({"shot": sh["id"], "out": rel(FRAMES_DIR / f"ep{n:02d}" / f"{sh['id']}.png"),
                         "size": size, "prompt": prompt, "refs": refs})
    return jobs


def write_jsonl(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def find_image(n: int, shot_id: str):
    for ext in EXTS:
        p = FRAMES_DIR / f"ep{n:02d}" / f"{shot_id}{ext}"
        if p.exists():
            return p
    return None


def attach(n: int) -> int:
    path = STORYBOARD_DIR / f"ep{n:02d}.json"
    data = load_json(path)
    got = miss = 0
    for sc in data["scenes"]:
        for sh in sc.get("shots", []):
            p = find_image(n, sh["id"])
            if p:
                sh["image"] = rel(p)
                got += 1
            else:
                miss += 1
    dump_json(data, path)
    print(f"[붙임] ep{n:02d}: 이미지 {got}장 연결, 없는 샷 {miss}개")
    return 0


def status() -> int:
    refs = [json.loads(l) for l in open(JOBS_DIR / "refs.jsonl", encoding="utf-8")] if (JOBS_DIR / "refs.jsonl").exists() else []
    have = sum((ROOT / r["out"]).exists() for r in refs)
    print(f"레퍼런스 {have}/{len(refs)}")
    for path in sorted(STORYBOARD_DIR.glob("ep*.json")):
        n = int(path.stem[2:])
        shots = [sh["id"] for sc in load_json(path)["scenes"] for sh in sc.get("shots", [])]
        made = sum(find_image(n, s) is not None for s in shots)
        print(f"ep{n:02d}  패널 {made:>3}/{len(shots):<3}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episodes", nargs="*", type=int)
    ap.add_argument("--attach", type=int, metavar="N", help="N화 이미지 파일을 스토리보드에 연결")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args(argv)
    if a.attach:
        return attach(a.attach)
    if a.status:
        return status()
    eps = a.episodes or [int(p.stem[2:]) for p in sorted(STORYBOARD_DIR.glob("ep*.json"))]
    used_locs = set()
    for p in sorted(STORYBOARD_DIR.glob("ep*.json")):
        used_locs |= {sc["location"] for sc in load_json(p)["scenes"]}
    write_jsonl(JOBS_DIR / "refs.jsonl", ref_jobs(used_locs))
    total = 0
    for n in eps:
        jobs = episode_jobs(n)
        write_jsonl(JOBS_DIR / f"ep{n:02d}.jsonl", jobs)
        total += len(jobs)
        print(f"[작업] assets/jobs/ep{n:02d}.jsonl  샷 {len(jobs)}개")
    print(f"[작업] assets/jobs/refs.jsonl  레퍼런스 · 합계 패널 {total}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
