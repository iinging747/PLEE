"""Cut the wizard penguin (2D, flat pink background) out for the KNTQ explainer.

The backdrop is one flat pink, so a fill grown from the border through pixels
close to that pink removes it; the bold black outline stops the fill. The edge
gets a 1px soft alpha and any pink fringe is pulled to the outline colour.
The bust is cut off by the image's bottom edge, which stays the bottom edge.

    python3 engine/cut-penguin.py
"""
import os
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "characters", "source", "wizard_penguin_2d.jpg")
OUT = os.path.join(ROOT, "assets", "characters", "wizard_penguin.png")

im = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
h, w, _ = im.shape
BG = im[5, 5].copy()
near = np.abs(im - BG).max(axis=2) < 60

bg = np.zeros((h, w), bool)
q = deque()
for x in range(w):
    for y in (0, h - 1):
        if near[y, x]:
            bg[y, x] = True
            q.append((y, x))
for y in range(h):
    for x in (0, w - 1):
        if near[y, x] and not bg[y, x]:
            bg[y, x] = True
            q.append((y, x))
while q:
    y, x = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and near[ny, nx]:
            bg[ny, nx] = True
            q.append((ny, nx))

alpha = Image.fromarray(((~bg) * 255).astype(np.uint8))
alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
a = np.asarray(alpha).astype(np.float32) / 255

# fringe: blend semi-transparent edge pixels towards the dark outline colour
edge = (a > 0.01) & (a < 0.99)
ink = np.array([25, 25, 30], np.float32)
dist = np.abs(im - BG).max(axis=2)
pinkish = edge & (dist < 110)
rgb = im.copy()
rgb[pinkish] = rgb[pinkish] * 0.25 + ink * 0.75

out = np.dstack([rgb, a * 255]).astype(np.uint8)
img = Image.fromarray(out, "RGBA")
img = img.crop(img.getbbox())
img.save(OUT)
print("wrote", OUT, img.size, "bbox", Image.fromarray(out, "RGBA").getbbox())
