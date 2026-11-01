#!/usr/bin/env python3
"""스토리보드 JSON → 콘티 시트(HTML), 샷 리스트(CSV), 이미지 프롬프트(JSONL).

    python3 wolha/tools/render.py            # storyboards/*.json 전부
    python3 wolha/tools/render.py 1 2 3      # 회차 지정

결과물: wolha/out/epNN.html, epNN_shotlist.csv, epNN_prompts.jsonl, index.html
HTML 은 외부 리소스 없이 혼자 열리고, A4 가로로 인쇄된다.
이미지가 있으면(assets/frames/epNN/<샷id>.png) 패널에 넣고, 없으면 구도 가이드를 그린다.
"""
from __future__ import annotations

import csv
import html
import json
import os
import sys
from pathlib import Path

from wolha_lib import (
    OUT_DIR, ROOT, STORYBOARD_DIR, characters, load_json, sec_to_tc, tc_to_sec,
)

SIZE_KO = {
    "ELS": "익스트림 롱", "LS": "롱", "FS": "풀", "MLS": "니", "MS": "웨이스트",
    "MCU": "바스트", "CU": "클로즈업", "ECU": "익스트림 클로즈업", "INSERT": "인서트",
    "2S": "투숏", "GROUP": "그룹",
}
ANGLE_KO = {
    "EYE": "아이레벨", "HIGH": "하이", "LOW": "로우", "BIRD": "부감", "WORM": "앙각",
    "DUTCH": "더치", "OTS": "어깨 너머", "POV": "시점", "TOP": "탑", "PROFILE": "측면",
}
MOVE_ARROW = {
    "FIX": "", "PAN_L": "←", "PAN_R": "→", "TILT_U": "↑", "TILT_D": "↓",
    "DOLLY_IN": "⇢◎", "DOLLY_OUT": "◎⇠", "TRACK_L": "⇐", "TRACK_R": "⇒", "TRACK_IN": "⇡",
    "CRANE_UP": "⤴", "CRANE_DOWN": "⤵", "HANDHELD": "≈", "ZOOM_IN": "⊕", "ZOOM_OUT": "⊖",
    "CRASH_ZOOM": "⊕!", "RACK_FOCUS": "◐", "STEADICAM": "∿", "ORBIT": "↻", "SLOWMO": "⏱",
}
# 샷 크기별로 가이드 실루엣의 머리 높이 비율(프레임 높이 대비)
SIZE_SCALE = {"ELS": 0.06, "LS": 0.12, "FS": 0.16, "MLS": 0.22, "MS": 0.3, "MCU": 0.42,
              "CU": 0.6, "ECU": 0.95, "2S": 0.28, "GROUP": 0.18}


def esc(s) -> str:
    return html.escape(str(s or ""))


def char_names() -> dict[str, str]:
    out = {}
    for c in characters():
        out[c["id"]] = (c.get("names") or [c["id"]])[0]
    out["N:gangsu"] = "N·강수"
    return out


def placeholder_svg(shot: dict) -> str:
    """이미지가 없을 때 쓰는 구도 가이드: 3분할선 + 샷 크기에 맞춘 머리 원 + 표기."""
    w, h = 320, 180
    size = shot["size"]
    parts = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">',
             f'<rect width="{w}" height="{h}" class="ph-bg"/>']
    for x in (w / 3, 2 * w / 3):
        parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" class="ph-grid"/>')
    for y in (h / 3, 2 * h / 3):
        parts.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" class="ph-grid"/>')
    if size == "INSERT":
        parts.append(f'<rect x="{w*0.2}" y="{h*0.2}" width="{w*0.6}" height="{h*0.6}" class="ph-fig"/>')
    else:
        r = h * SIZE_SCALE.get(size, 0.3) / 2
        n = max(1, min(4, len(shot.get("characters", [])) or 1))
        for i in range(n):
            cx = w * (i + 1) / (n + 1)
            cy = h / 3
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="ph-fig"/>')
            bottom = min(h, cy + r * 4.5)
            parts.append(f'<path d="M{cx - r*1.7:.1f},{bottom:.1f} Q{cx:.1f},{cy + r*0.9:.1f} {cx + r*1.7:.1f},{bottom:.1f}" class="ph-fig"/>')
    parts.append(f'<text x="10" y="22" class="ph-size">{esc(size)}</text>')
    label = f'{ANGLE_KO.get(shot["angle"], shot["angle"])} · {shot["move"]} {MOVE_ARROW.get(shot["move"], "")}'
    if shot.get("lens_mm"):
        label += f' · {shot["lens_mm"]}mm'
    parts.append(f'<text x="10" y="{h-10}" class="ph-meta">{esc(label)}</text>')
    parts.append("</svg>")
    return "".join(parts)


CSS = """
:root{--bg:#f7f3ea;--paper:#fffdf8;--ink:#1d1b18;--muted:#6d665c;--line:#d8cfbf;--accent:#b03a2e;--chip:#efe6d4}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#191714;--paper:#22201c;--ink:#efe9de;--muted:#a59d90;--line:#3a352e;--accent:#e2735f;--chip:#2e2a24}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
header{padding:20px 24px;border-bottom:1px solid var(--line);background:var(--paper)}
h1{margin:0 0 4px;font-size:22px}h2{margin:28px 24px 8px;font-size:16px}
.meta{color:var(--muted);font-size:13px}.hook{margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:0 24px 8px}
@media (max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.grid{grid-template-columns:1fr;padding:0 16px}h2{margin:24px 16px 8px}header{padding:16px}}
.panel{background:var(--paper);border:1px solid var(--line);border-radius:6px;overflow:hidden;break-inside:avoid}
.frame{aspect-ratio:16/9;background:#e9e2d3;display:block;width:100%}.frame img,.frame svg{width:100%;height:100%;display:block;object-fit:cover}
.ph-bg{fill:#ece5d6}.ph-grid{stroke:#c9bfac;stroke-width:1;stroke-dasharray:3 4}.ph-fig{fill:none;stroke:#8a7f6c;stroke-width:2}
.ph-size{font:700 18px sans-serif;fill:#5a5143}.ph-meta{font:12px sans-serif;fill:#5a5143}
.cap{padding:8px 10px 10px}.row1{display:flex;justify-content:space-between;gap:8px;font-weight:700}
.tc{color:var(--muted);font-weight:400;font-variant-numeric:tabular-nums}
.act{margin:4px 0}.dlg{margin:2px 0;padding-left:8px;border-left:3px solid var(--accent)}
.snd,.frm{color:var(--muted);font-size:12px;margin-top:2px}
.chips{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}.chip{background:var(--chip);border-radius:10px;padding:0 7px;font-size:11px}
.ins{font-family:serif;background:var(--chip);padding:2px 6px;border-radius:4px;display:inline-block;margin-top:4px}
table{border-collapse:collapse;margin:0 24px;font-size:13px}td,th{border:1px solid var(--line);padding:4px 8px;text-align:left}
@media print{@page{size:A4 landscape;margin:10mm}body{background:#fff}header{border:0}.grid{grid-template-columns:repeat(3,1fr);gap:8px}}
"""


def render_episode(data: dict, names: dict[str, str]) -> str:
    ep = data["episode"]
    shots_all = [sh for sc in data["scenes"] for sh in sc.get("shots", [])]
    total = sum(sh["duration_sec"] for sh in shots_all)
    head = (f'<header><h1>{ep}화 「{esc(data["title"])}」</h1>'
            f'<div class="meta">{esc(data["series"])} · 목표 {data["runtime_sec"]}초 · '
            f'샷 {len(shots_all)}개 · 샷 합계 {total:.0f}초 ({sec_to_tc(total)}) · 상태 {esc(data.get("status",""))}</div>')
    if data.get("hook"):
        head += f'<div class="hook">훅: {esc(data["hook"])}</div>'
    head += "</header>"
    body = []
    for sc in data["scenes"]:
        body.append(f'<h2>[{sc["tc_in"]}–{sc["tc_out"]}] {esc(sc["id"])}. {esc(sc["heading"])}</h2>')
        if not sc.get("shots"):
            body.append('<p class="meta" style="padding:0 24px">샷 미작성</p>')
            continue
        body.append('<div class="grid">')
        t = tc_to_sec(sc["tc_in"])
        for sh in sc["shots"]:
            img = sh.get("image")
            if img and (ROOT / img).exists():
                rel = os.path.relpath(ROOT / img, OUT_DIR)
                frame = f'<img src="{esc(rel)}" alt="{esc(sh["id"])}">'
            else:
                frame = placeholder_svg(sh)
            cap = [f'<div class="row1"><span>{esc(sh["id"])} · {SIZE_KO.get(sh["size"], sh["size"])}</span>'
                   f'<span class="tc">{sec_to_tc(t)} · {sh["duration_sec"]:g}s</span></div>',
                   f'<div class="act">{esc(sh["action"])}</div>']
            if sh.get("insert_text"):
                cap.append(f'<div class="ins">{esc(sh["insert_text"])}</div>')
            for d in sh.get("dialogue", []):
                mode = f' ({d["mode"]})' if d.get("mode") and d["mode"] != "ON" else ""
                cap.append(f'<div class="dlg"><b>{esc(names.get(d["speaker"], d["speaker"]))}</b>{esc(mode)} {esc(d["line"])}</div>')
            if sh.get("frame"):
                cap.append(f'<div class="frm">구도: {esc(sh["frame"])}</div>')
            if sh.get("sound"):
                cap.append(f'<div class="snd">소리: {esc(sh["sound"])}</div>')
            chips = [sh.get("transition", "CUT")] + sh.get("motifs", [])
            cap.append('<div class="chips">' + "".join(f'<span class="chip">{esc(c)}</span>' for c in chips) + "</div>")
            body.append(f'<article class="panel"><div class="frame">{frame}</div><div class="cap">{"".join(cap)}</div></article>')
            t += sh["duration_sec"]
        body.append("</div>")
    title = f'{ep}화 콘티'
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body>{head}{"".join(body)}</body></html>')


def write_csv(data: dict, path: Path, names: dict[str, str]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["shot", "scene", "tc_in", "sec", "size", "angle", "move", "lens", "characters",
                    "action", "dialogue", "sound", "insert", "transition", "motifs", "image"])
        for sc in data["scenes"]:
            t = tc_to_sec(sc["tc_in"])
            for sh in sc.get("shots", []):
                dl = " / ".join(f'{names.get(d["speaker"], d["speaker"])}: {d["line"]}' for d in sh.get("dialogue", []))
                w.writerow([sh["id"], sc["id"], sec_to_tc(t), sh["duration_sec"], sh["size"], sh["angle"],
                            sh["move"], sh.get("lens_mm", ""), ",".join(sh.get("characters", [])), sh["action"],
                            dl, sh.get("sound", ""), sh.get("insert_text", ""), sh.get("transition", "CUT"),
                            ",".join(sh.get("motifs", [])), sh.get("image") or ""])
                t += sh["duration_sec"]


def write_prompts(data: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for sc in data["scenes"]:
            for sh in sc.get("shots", []):
                f.write(json.dumps({"episode": data["episode"], "shot": sh["id"], "location": sh.get("location") or sc["location"],
                                    "time": sc["time"], "size": sh["size"], "angle": sh["angle"],
                                    "characters": sh.get("characters", []),
                                    "prompt": sh.get("image_prompt", "")}, ensure_ascii=False) + "\n")


def write_index(rows: list[tuple]) -> None:
    trs = "".join(
        f'<tr><td><a href="ep{ep:02d}.html">{ep}화</a></td><td>{esc(title)}</td><td>{esc(status)}</td>'
        f'<td>{n}</td><td>{sec_to_tc(total)}</td></tr>' for ep, title, status, n, total in rows)
    page = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>콘티 목록</title><style>{CSS}</style></head><body>'
            f'<header><h1>월하노인을 잡아라 — 숏폼 콘티</h1><div class="meta">회차별 콘티 시트</div></header>'
            f'<h2>회차</h2><table><tr><th>회차</th><th>제목</th><th>상태</th><th>샷</th><th>길이</th></tr>{trs}</table></body></html>')
    (OUT_DIR / "index.html").write_text(page, encoding="utf-8")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    files = ([STORYBOARD_DIR / f"ep{int(a):02d}.json" for a in argv] if argv
             else sorted(STORYBOARD_DIR.glob("ep*.json")))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = char_names()
    rows = []
    for f in files:
        data = load_json(f)
        stem = f.stem
        (OUT_DIR / f"{stem}.html").write_text(render_episode(data, names), encoding="utf-8")
        write_csv(data, OUT_DIR / f"{stem}_shotlist.csv", names)
        write_prompts(data, OUT_DIR / f"{stem}_prompts.jsonl")
        shots = [sh for sc in data["scenes"] for sh in sc.get("shots", [])]
        rows.append((data["episode"], data["title"], data.get("status", ""), len(shots),
                     sum(s["duration_sec"] for s in shots)))
        print(f"[렌더] out/{stem}.html  샷 {len(shots)}개")
    all_rows = {}
    for f in sorted(STORYBOARD_DIR.glob("ep*.json")):
        d = load_json(f)
        shots = [sh for sc in d["scenes"] for sh in sc.get("shots", [])]
        all_rows[d["episode"]] = (d["episode"], d["title"], d.get("status", ""), len(shots),
                                  sum(s["duration_sec"] for s in shots))
    write_index([all_rows[k] for k in sorted(all_rows)])
    return 0


if __name__ == "__main__":
    sys.exit(main())
