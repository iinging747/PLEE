"""공용 유틸: 경로, JSON 로더, 타임코드, 의존성 없는 미니 JSON Schema 검사기.

외부 패키지 없이 파이썬 3.9+ 표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # wolha/
SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"
CHARACTERS_PATH = ROOT / "bible" / "characters.json"
LOCATIONS_PATH = ROOT / "bible" / "locations.json"
SHORTFORM_DIR = ROOT / "shortform"
STORYBOARD_DIR = ROOT / "storyboards"
OUT_DIR = ROOT / "out"
FRAMES_DIR = ROOT / "assets" / "frames"


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump_json(data, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def tc_to_sec(tc: str) -> int:
    m, s = tc.split(":")
    return int(m) * 60 + int(s)


def sec_to_tc(sec: float) -> str:
    sec = int(round(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def characters():
    data = load_json(CHARACTERS_PATH)
    return data["characters"]


def character_ids() -> set[str]:
    return {c["id"] for c in characters()}


def name_to_id() -> dict[str, str]:
    """대본 표기 이름 -> 캐릭터 id. 긴 이름 우선 매칭을 위해 정렬은 호출 측에서."""
    table = {}
    for c in characters():
        for n in c.get("names", []):
            table[n] = c["id"]
    return table


def locations():
    return load_json(LOCATIONS_PATH)["locations"]


def location_ids() -> set[str]:
    return {l["id"] for l in locations()}


def match_location(heading: str) -> str | None:
    best = None
    best_len = 0
    for loc in locations():
        for kw in loc.get("match", []):
            if kw in heading and len(kw) > best_len:
                best, best_len = loc["id"], len(kw)
    return best


def normalize_text(s: str) -> str:
    """대사 원문 대조용 정규화: 공백·문장부호 차이를 무시한다."""
    s = s.replace("\\", "")
    s = re.sub(r"\([^()]*\)", "", s)  # (O.S.), (사이), (혼잣말) 같은 지문 제거
    s = re.sub(r"[\s….…,!?'\"“”‘’—\-()]", "", s)
    return s


# ---------------------------------------------------------------- mini schema

class SchemaError(Exception):
    pass


def _type_ok(value, t: str) -> bool:
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate_schema(value, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """JSON Schema 중 이 프로젝트가 쓰는 부분집합만 검사한다.

    지원: type, const, enum, pattern, minLength, minimum, maximum, required,
    properties, additionalProperties(false), items, minItems, $ref(#/$defs/...)
    """
    root = root or schema
    errors: list[str] = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            raise SchemaError(f"지원하지 않는 $ref: {ref}")
        return validate_schema(value, root["$defs"][ref.split("/")[-1]], root, path)

    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(value, x) for x in types):
            return [f"{path}: 타입이 {types} 이어야 함 (값: {type(value).__name__})"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: 값은 {schema['const']!r} 이어야 함")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} 는 허용값이 아님 {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} 가 패턴 {schema['pattern']} 과 맞지 않음")
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: 너무 짧음")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} < 최소 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} > 최대 {schema['maximum']}")
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: 필수 필드 '{req}' 없음")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                errors += validate_schema(v, props[k], root, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: 정의되지 않은 필드 '{k}'")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: 항목이 {schema['minItems']}개 이상이어야 함")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate_schema(item, schema["items"], root, f"{path}[{i}]")
    return errors


# ---------------------------------------------------------------- script parse

SCENE_RE = re.compile(
    r"^#{2,4}\s*\[(\d{2}:\d{2})\s*[–\-~]\s*(\d{2}:\d{2})\]\s*S#(\d+)\.\s*(.+?)\s*$"
)
EP_RE = re.compile(r"^#\s*(\d+)화\s*[「“\"]?(.+?)[」”\"]?\s*$")
SPEAKER_RE = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$")


def time_code(heading: str) -> str:
    m = re.search(r"\(([^()]*)\)\s*$", heading)
    t = m.group(1) if m else ""
    if "회상" in t:
        return "FLASHBACK"
    if "새벽" in t:
        return "DAWN"
    if "해 질" in t or "해질" in t or "저녁" in t:
        return "DUSK"
    if "밤" in t or "삼경" in t or "사경" in t:
        return "NIGHT"
    if "아침" in t:
        return "MORNING"
    return "DAY"


def parse_shortform(md_path: Path) -> dict:
    """shortform/epNN.md -> {episode, title, hook, scenes:[{id, heading, tc_in, tc_out, lines}]}"""
    text = md_path.read_text(encoding="utf-8").replace("\\", "")
    ep = {"episode": None, "title": "", "hook": "", "scenes": []}
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = EP_RE.match(line)
        if m and ep["episode"] is None:
            ep["episode"] = int(m.group(1))
            ep["title"] = m.group(2).strip()
            continue
        if line.startswith("훅:") and not ep["hook"]:
            ep["hook"] = line[3:].strip()
            continue
        m = SCENE_RE.match(line)
        if m:
            cur = {
                "id": f"S#{int(m.group(3))}",
                "heading": m.group(4).strip(),
                "tc_in": m.group(1),
                "tc_out": m.group(2),
                "lines": [],
            }
            ep["scenes"].append(cur)
            continue
        if cur is not None and line.strip():
            cur["lines"].append(line.strip())
    return ep


def dialogue_lines(lines: list[str]) -> list[tuple[str, str]]:
    out = []
    for l in lines:
        m = SPEAKER_RE.match(l)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out
