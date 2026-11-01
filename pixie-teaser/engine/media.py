"""Source media: conform video segments to JPEG sequences, load photos, random frame access."""
import json
import os
import subprocess
from collections import OrderedDict

import cv2
import numpy as np

from .core import W, H, WORK

CONF = os.path.join(WORK, "conf")


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def video_info(path):
    j = probe(path)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    if "rotate" in v.get("tags", {}):
        rot = int(v["tags"]["rotate"])
    if abs(rot) in (90, 270):
        w, h = h, w
    num, den = v.get("avg_frame_rate", "30/1").split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    dur = float(v.get("duration") or j["format"].get("duration") or 0)
    trc = v.get("color_transfer", "")
    has_audio = any(s["codec_type"] == "audio" for s in j["streams"])
    return dict(w=w, h=h, fps=fps, dur=dur, hdr=trc in ("smpte2084", "arib-std-b67"), transfer=trc,
                audio=has_audio, pix=v.get("pix_fmt", ""))


def conform(key, path, t_in, t_out, headroom=1.0, max_fps=60.0, fit="cover", force=False):
    """Extract [t_in, t_out] of `path` as JPEG frames scaled to cover W×H × headroom.

    Returns dict(dir, fps, start, n, w, h)."""
    info = video_info(path)
    fps = min(round(info["fps"]), max_fps) or 30
    pre = 0.0
    start = max(0.0, t_in - pre)
    dur = min(t_out, info["dur"]) - start
    tag = f"{key}_{start:.3f}_{dur:.3f}_{headroom}_{fit}_{fps}"
    d = os.path.join(CONF, tag)
    meta = os.path.join(d, "meta.json")
    if os.path.exists(meta) and not force:
        return json.load(open(meta))
    os.makedirs(d, exist_ok=True)
    sw, sh = info["w"], info["h"]
    if fit == "cover":
        s = max(W / sw, H / sh) * headroom
    elif fit == "width":
        s = W / sw * headroom
    else:  # contain
        s = min(W / sw, H / sh) * headroom
    s = min(s, 1.0) if headroom <= 1.0 and s > 1.0 and max(sw, sh) >= 3000 else s
    ow, oh = int(round(sw * s / 2) * 2), int(round(sh * s / 2) * 2)
    vf = []
    if info["hdr"]:
        vf.append("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
                  "tonemap=tonemap=mobius:desat=0.4:param=0.4,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    vf.append(f"scale={ow}:{oh}:flags=lanczos")
    vf.append(f"fps={fps}")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", path,
           "-vf", ",".join(vf), "-q:v", "2", os.path.join(d, "%05d.jpg")]
    subprocess.run(cmd, check=True)
    n = len([f for f in os.listdir(d) if f.endswith(".jpg")])
    m = dict(dir=d, fps=fps, start=start, n=n, w=ow, h=oh, src=path)
    json.dump(m, open(meta, "w"))
    return m


class Seq:
    def __init__(self, meta, cache=6):
        self.m = meta
        self.cache = OrderedDict()
        self.size = cache

    @property
    def fps(self):
        return self.m["fps"]

    def frame_at(self, ts):
        """Frame for source time ts (seconds, absolute source time)."""
        i = int(round((ts - self.m["start"]) * self.m["fps"]))
        i = max(0, min(self.m["n"] - 1, i))
        return self.frame(i)

    def frame(self, i):
        f = self.cache.get(i)
        if f is None:
            p = os.path.join(self.m["dir"], f"{i + 1:05d}.jpg")
            im = cv2.imread(p, cv2.IMREAD_COLOR)
            if im is None:
                raise FileNotFoundError(p)
            f = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
            self.cache[i] = f
            if len(self.cache) > self.size:
                self.cache.popitem(last=False)
        else:
            self.cache.move_to_end(i)
        return f


_photo_cache = OrderedDict()


def photo(path, headroom=1.3):
    key = (path, headroom)
    if key in _photo_cache:
        return _photo_cache[key]
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    s = max(W / w, H / h) * headroom
    if s < 1:
        im = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    f = np.ascontiguousarray(im)
    _photo_cache[key] = f
    if len(_photo_cache) > 8:
        _photo_cache.popitem(last=False)
    return f
