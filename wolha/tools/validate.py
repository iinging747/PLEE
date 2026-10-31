#!/usr/bin/env python3
"""스토리보드 JSON 검사기.

1) schema/storyboard.schema.json 구조 검사 (외부 패키지 불필요)
2) 제작 규칙 검사 — docs/storyboard_guide.md 의 '검수 규칙' 절과 1:1 대응
   - 씬 타임코드가 00:00부터 끊김 없이 이어지는지, 마지막이 runtime_sec 와 맞는지
   - 씬별 샷 길이 합이 씬 구간 길이와 맞는지 (±15% 또는 ±3초)
   - 회차 전체 길이가 runtime_sec ±5% 인지
   - 샷 id 가 씬 번호와 맞고 중복이 없는지
   - 인물·장소 id 가 설정집(bible)에 있는지
   - 대사가 대본 원문과 같은지 (shortform/epNN.md 와 대조)
   - 모티프 샷 규칙 (귀 클로즈업, 지붕 위 흑립은 와이드 등)
   - status 가 final 이면 모든 샷에 frame, image_prompt 가 있는지

사용법:
    python3 wolha/tools/validate.py                 # storyboards/*.json 전부
    python3 wolha/tools/validate.py wolha/storyboards/ep02.json
    python3 wolha/tools/validate.py --strict        # 경고도 실패로 처리

종료 코드: 오류가 있으면 1.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wolha_lib import (
    ROOT, SCHEMA_PATH, SHORTFORM_DIR, STORYBOARD_DIR, character_ids, dialogue_lines,
    load_json, location_ids, name_to_id, normalize_text, parse_shortform,
    tc_to_sec, validate_schema,
)

WIDE = {"ELS", "LS", "FS"}
CLOSE = {"CU", "ECU", "INSERT", "MCU"}


def check(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    data = load_json(path)
    schema = load_json(SCHEMA_PATH)
    errors += validate_schema(data, schema)
    if errors:
        return errors, warns  # 구조가 틀리면 의미 검사는 생략

    status = data.get("status", "draft")
    runtime = data["runtime_sec"]
    chars = character_ids()
    locs = location_ids()
    names = name_to_id()

    # 대본 원문
    md = SHORTFORM_DIR / f"ep{data['episode']:02d}.md"
    script = parse_shortform(md) if md.exists() else None
    if script is None:
        warns.append(f"대본 파일 {md.name} 없음 — 대사 대조 생략")
    script_scenes = {s["id"]: s for s in (script["scenes"] if script else [])}

    prev_out = "00:00"
    total = 0.0
    seen_ids: set[str] = set()
    for sc in data["scenes"]:
        sid = sc["id"]
        n = int(sid[2:])
        if sc["tc_in"] != prev_out:
            warns.append(f"{sid}: tc_in {sc['tc_in']} 이 앞 씬 tc_out {prev_out} 과 이어지지 않음")
        prev_out = sc["tc_out"]
        span = tc_to_sec(sc["tc_out"]) - tc_to_sec(sc["tc_in"])
        if span <= 0:
            errors.append(f"{sid}: 타임코드 구간이 0초 이하")
        if sc["location"] not in locs:
            errors.append(f"{sid}: 장소 id '{sc['location']}' 가 bible/locations.json 에 없음")
        for c in sc.get("characters", []):
            if c not in chars:
                errors.append(f"{sid}: 인물 id '{c}' 가 bible/characters.json 에 없음")

        shots = sc.get("shots", [])
        if not shots:
            (errors if status in ("review", "final") else warns).append(f"{sid}: 샷이 없음")
            continue

        scene_sum = 0.0
        last_no = 0
        src = script_scenes.get(sid)
        src_norm = normalize_text("\n".join(src["lines"])) if src else ""
        for sh in shots:
            shid = sh["id"]
            if shid in seen_ids:
                errors.append(f"{shid}: 샷 id 중복")
            seen_ids.add(shid)
            if int(shid[1:3]) != n:
                errors.append(f"{shid}: 씬 {sid} 안에 있는데 번호가 다름")
            no = int(shid[4:6])
            if shid[-1].isdigit() and no != last_no + 1:
                warns.append(f"{shid}: 샷 번호가 연속되지 않음 (앞 번호 {last_no:02d})")
            last_no = no
            scene_sum += sh["duration_sec"]
            for c in sh.get("characters", []):
                if c not in chars:
                    errors.append(f"{shid}: 인물 id '{c}' 없음")
            for d in sh.get("dialogue", []):
                if d["speaker"] not in chars:
                    errors.append(f"{shid}: 화자 id '{d['speaker']}' 없음")
                if src and normalize_text(d["line"]) not in src_norm:
                    warns.append(f"{shid}: 대사가 대본 원문과 다름 → {d['line'][:30]}")
            motifs = set(sh.get("motifs", []))
            if {"EAR_RED", "EAR_NOT_RED"} & motifs and sh["size"] not in CLOSE:
                warns.append(f"{shid}: 귀 모티프는 CU/ECU/INSERT 로 잡는 것이 규칙")
            if "ROOFTOP_HEUKRIP" in motifs and sh["size"] not in WIDE:
                warns.append(f"{shid}: 지붕 위 흑립은 ELS/LS 로 작게 잡는 것이 규칙")
            if "INSERT_TEXT" in motifs and not sh.get("insert_text"):
                warns.append(f"{shid}: INSERT_TEXT 샷에 insert_text 가 비어 있음")
            if status == "final":
                if not sh.get("frame"):
                    errors.append(f"{shid}: final 인데 frame 이 비어 있음")
                if not sh.get("image_prompt"):
                    errors.append(f"{shid}: final 인데 image_prompt 가 비어 있음")
            if sh.get("image") and not (ROOT / sh["image"]).exists():
                warns.append(f"{shid}: image 파일이 없음 → {sh['image']}")
            if sh["duration_sec"] > 12 and sh["move"] == "FIX":
                warns.append(f"{shid}: 12초 넘는 고정 샷 — 숏폼 템포 확인")

        # 대본 대사가 샷에 다 들어갔는지
        if src:
            used = normalize_text(" ".join(d["line"] for sh in shots for d in sh.get("dialogue", [])))
            for spk, line in dialogue_lines(src["lines"]):
                if normalize_text(line) and normalize_text(line) not in used:
                    warns.append(f"{sid}: 대본 대사 누락 → {spk}: {line[:30]}")

        tol = max(3.0, span * 0.15)
        if abs(scene_sum - span) > tol:
            warns.append(f"{sid}: 샷 길이 합 {scene_sum:.1f}초 ↔ 씬 구간 {span}초")
        total += scene_sum

    if prev_out != f"{runtime // 60:02d}:{runtime % 60:02d}":
        warns.append(f"마지막 씬 tc_out {prev_out} ≠ runtime {runtime}초")
    if total and abs(total - runtime) > runtime * 0.05:
        (errors if status == "final" else warns).append(
            f"샷 길이 총합 {total:.1f}초 ↔ runtime {runtime}초 (±5% 초과)")
    shot_count = len(seen_ids)
    if shot_count and not (25 <= shot_count <= 80):
        warns.append(f"샷 수 {shot_count}개 — 3분물 권장 범위 25~80")
    return errors, warns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    files = [Path(f) for f in args.files] or sorted(STORYBOARD_DIR.glob("ep*.json"))
    bad = False
    for f in files:
        errors, warns = check(f)
        mark = "OK " if not errors and not (args.strict and warns) else "ERR"
        print(f"[{mark}] {f.name}  오류 {len(errors)} · 경고 {len(warns)}")
        for e in errors:
            print(f"   ✗ {e}")
        for w in warns:
            print(f"   △ {w}")
        if errors or (args.strict and warns):
            bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
