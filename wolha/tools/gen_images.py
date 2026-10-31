#!/usr/bin/env python3
"""샷별 콘티 이미지 생성 (선택 사항).

기본은 '드라이런'이다. 실제로 이미지를 만들지 않고, 보낼 프롬프트를
out/epNN_image_requests.jsonl 에 적어 둔다. 사람이 확인한 뒤 --run 으로 실행한다.

    python3 wolha/tools/gen_images.py 1                # 1화 프롬프트만 만들기
    python3 wolha/tools/gen_images.py 1 --run --limit 5 # 1화 앞 5컷만 실제 생성
    python3 wolha/tools/gen_images.py 1 --run --only S04-03

--run 은 OpenAI Images API 를 쓴다. 환경 변수:
    OPENAI_API_KEY        필수
    WOLHA_IMAGE_MODEL     기본 gpt-image-1
    WOLHA_IMAGE_QUALITY   기본 medium (low/medium/high)

생성된 PNG 는 assets/frames/epNN/<샷id>.png 에 저장하고, 스토리보드 JSON 의
image 필드를 그 경로로 바꾼다. 이미 image 가 있는 샷은 --force 없이 건너뛴다.
주의: 네트워크 호출 부분은 이 저장소를 만든 환경에서 실제 API 키로 시험하지 못했다.
처음 쓸 때는 --limit 1 로 한 컷만 돌려 응답 형식을 확인할 것.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

from wolha_lib import FRAMES_DIR, OUT_DIR, ROOT, STORYBOARD_DIR, characters, dump_json, load_json, locations

STYLE = ("Korean drama storyboard frame, loose ink line drawing with light watercolor wash, "
         "muted Joseon-era palette inspired by Shin Yun-bok genre paintings, coral red accents, "
         "cinematic composition, no text, no captions, no speech bubbles, no modern objects, "
         "historical setting: Hanyang (Seoul), Joseon dynasty, 1792")

SIZE_EN = {"ELS": "extreme wide shot", "LS": "wide shot", "FS": "full shot", "MLS": "medium long shot (knees up)",
           "MS": "medium shot (waist up)", "MCU": "medium close-up (chest up)", "CU": "close-up",
           "ECU": "extreme close-up", "INSERT": "insert close-up of an object", "2S": "two-shot", "GROUP": "group shot"}
ANGLE_EN = {"EYE": "eye level", "HIGH": "high angle", "LOW": "low angle", "BIRD": "bird's-eye view",
            "WORM": "worm's-eye view", "DUTCH": "dutch tilt", "OTS": "over-the-shoulder", "POV": "point-of-view",
            "TOP": "top-down", "PROFILE": "profile"}
TIME_EN = {"DAY": "daylight", "NIGHT": "night, lit only by oil lamps, lanterns or moonlight",
           "DAWN": "blue pre-dawn light", "DUSK": "warm sunset backlight", "MORNING": "soft morning light",
           "FLASHBACK": "desaturated memory tone"}


def build_prompt(data: dict, scene: dict, shot: dict, chars: dict, locs: dict) -> str:
    who = [chars[c]["prompt_en"] for c in shot.get("characters", []) if c in chars and chars[c].get("prompt_en")]
    loc = locs.get(scene["location"], {})
    parts = [STYLE,
             f'{SIZE_EN.get(shot["size"], shot["size"])}, {ANGLE_EN.get(shot["angle"], shot["angle"])}',
             TIME_EN.get(scene["time"], ""),
             f'location: {loc.get("prompt_en") or loc.get("name", scene["location"])}']
    if who:
        parts.append("characters: " + " | ".join(who))
    if shot.get("image_prompt"):
        parts.append("scene: " + shot["image_prompt"])
    return ". ".join(p for p in parts if p)


def call_api(prompt: str, size: str) -> bytes:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY 가 없습니다.")
    body = json.dumps({
        "model": os.environ.get("WOLHA_IMAGE_MODEL", "gpt-image-1"),
        "prompt": prompt,
        "size": size,
        "quality": os.environ.get("WOLHA_IMAGE_QUALITY", "medium"),
        "n": 1,
    }).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        res = json.load(r)
    item = res["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    if item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=120) as r:
            return r.read()
    raise RuntimeError(f"예상하지 못한 응답: {list(item)}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode", type=int)
    ap.add_argument("--run", action="store_true", help="실제로 API 호출")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    path = STORYBOARD_DIR / f"ep{args.episode:02d}.json"
    data = load_json(path)
    chars = {c["id"]: c for c in characters()}
    locs = {l["id"]: l for l in locations()}
    size = "1024x1536" if data.get("aspect") == "9:16" else "1536x1024"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    req_path = OUT_DIR / f"ep{args.episode:02d}_image_requests.jsonl"
    done = 0
    with open(req_path, "w", encoding="utf-8") as log:
        for sc in data["scenes"]:
            for sh in sc.get("shots", []):
                if args.only and sh["id"] not in args.only:
                    continue
                if sh.get("image") and not args.force:
                    continue
                prompt = build_prompt(data, sc, sh, chars, locs)
                log.write(json.dumps({"shot": sh["id"], "size": size, "prompt": prompt}, ensure_ascii=False) + "\n")
                if args.run:
                    out = FRAMES_DIR / f"ep{args.episode:02d}" / f"{sh['id']}.png"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        out.write_bytes(call_api(prompt, size))
                        sh["image"] = str(out.relative_to(ROOT))
                        print(f"[생성] {sh['image']}")
                    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as e:
                        print(f"[실패] {sh['id']}: {e}")
                    time.sleep(1)
                done += 1
                if args.limit and done >= args.limit:
                    break
            if args.limit and done >= args.limit:
                break
    if args.run:
        dump_json(data, path)
    print(f"{'생성' if args.run else '프롬프트 기록'} {done}건 → {req_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
