#!/usr/bin/env python3
"""스토리보드 JSON 의 한글 오타(깨진 음절) 찾기.

대본·원작·가이드·바이블에 한 번도 안 나오는 음절을 쓴 단어를 문맥과 함께 보여 준다.
'뚼', '픩', '궐짝' 같은 잘못된 음절을 잡는 용도다. 나온다고 다 오타는 아니니 눈으로 확인한다.

    python3 tools/check_hangul.py                 # storyboards/ 전체
    python3 tools/check_hangul.py storyboards/ep05.json
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_GLOBS = ["source/*.md", "shortform/*.md", "docs/*.md", "bible/*.json", "AGENTS.md", "TASKS.md", "README.md"]
HANGUL = re.compile(r"[가-힣]")
WORD = re.compile(r"[가-힣]+")

# 코퍼스에 없어도 흔히 쓰는 음절(오탐 줄이기)
COMMON = set("캔갈같걀걔겁곰괜굉궤귤깃깍깔깡꺾꼼꽁꾹꿀끈낌낱넉넌넙놈뇌뉘늬닳댁덫덮뎌돋됨둑뒹듬딧땀땅떠뗀똑뚝뛸뜰띈띤랑랬렀렵롭룩륨릅맏맙맡맴멎멸몹묶묵뭇뭣믐밉밟뱃벨볕볶봅봤뵙붐빛빵빻뺨뻔뼘뽑뾰뿔삐삿샅샘섯셈셋솜쇄숱쉼슭싹쌈썩쎄쏜쑥쓴씌앎앳얀얽엊엎엮옅옛옳옷왠욱웁윗읊잎잦잼쟁젓젖젤졸좁죽줌쥔즙짊짐짚쪼쫓찢찧챙첩첼촘촛촨춥췄츠칙칠칭캐컥켠콧쾅쿵퀭큼킁탁탄턱텅톡툭퉁튄틈팎팔펑폭푹퓨픈핏핥햅헐혀홑홱훅훑훨휙휩흉흘흙흠흩힐힘")


def corpus_counter() -> Counter:
    c: Counter = Counter()
    for g in CORPUS_GLOBS:
        for p in ROOT.glob(g):
            c.update(HANGUL.findall(p.read_text(encoding="utf-8")))
    return c


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted((ROOT / "storyboards").glob("ep*.json"))
    seen = corpus_counter()
    total = 0
    for f in files:
        text = Path(f).read_text(encoding="utf-8")
        hits = []
        for m in WORD.finditer(text):
            w = m.group(0)
            odd = [ch for ch in w if seen[ch] == 0 and ch not in COMMON]
            if odd:
                s = max(0, m.start() - 15)
                hits.append((w, "".join(odd), text[s:m.end() + 15].replace("\n", " ")))
        if hits:
            print(f"■ {Path(f).name}: 의심 {len(hits)}건")
            for w, odd, ctx in hits:
                print(f"   {w}  [{odd}]  …{ctx}…")
        total += len(hits)
    print(f"합계 의심 {total}건")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
