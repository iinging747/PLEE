"""Cut the base character (assets/stickers/hypurr_sit.png) into rig parts.

Writes assets/stickers/rig/hypurr_{head,body,tail}.png (same canvas size, so
they share one pivot) and assets/stickers/rig/rig.json with the joint and face
positions the storyboard rig uses. Run with: python3 -I engine/cut-rig.py
"""
import json
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "stickers", "hypurr_sit.png")
OUT = os.path.join(ROOT, "assets", "stickers", "rig")

# head = everything above the chin line (ears and whiskers included)
CHIN = [(0, 400), (60, 415), (120, 437), (170, 447), (250, 450), (300, 437), (350, 425), (400, 405), (430, 380), (450, 365)]
# tail = right of the body edge, behind the hoodie
TAIL = [(447, 365), (579, 365), (579, 705), (466, 705), (461, 680), (453, 640), (444, 600), (441, 540), (438, 440)]

im = Image.open(SRC).convert("RGBA")
W, H = im.size


def masked(poly):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    part = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    part.paste(im, (0, 0), m)
    return part, m


head_poly = [(0, 0), (W, 0), (W, 365)] + list(reversed(CHIN))
head, head_m = masked(head_poly)
tail, tail_m = masked(TAIL)
rest = Image.new("L", (W, H), 255)
rest.paste(0, (0, 0), head_m)
rest.paste(0, (0, 0), tail_m)
body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
body.paste(im, (0, 0), rest)

os.makedirs(OUT, exist_ok=True)
head.save(os.path.join(OUT, "hypurr_head.png"))
body.save(os.path.join(OUT, "hypurr_body.png"))
tail.save(os.path.join(OUT, "hypurr_tail.png"))

rig = {
    "size": [W, H],
    "origin": [290, 800],  # rig space origin: between the feet, on the ground
    "neck": [245, 445],
    "tailBase": [455, 672],
    "chin": CHIN,
    "eyes": [{"c": [111.5, 325.5], "sz": [43, 63]}, {"c": [309.5, 298.5], "sz": [49, 69]}],
    "mouth": [196, 352],
    "nose": [190, 336],
    "cheeks": [[70, 372], [345, 345]],
    "faceTop": [210, 140],
}
with open(os.path.join(OUT, "rig.json"), "w") as f:
    json.dump(rig, f, indent=1)
print("rig parts written to", OUT)
