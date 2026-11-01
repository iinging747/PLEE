"""Build the PIXIE teaser.

  python make.py titles      # Blender chrome stills (needs /opt/bpyenv with bpy)
  python make.py audio       # mix -> dist/PIXIE_teaser_mix.wav
  python make.py video       # frames -> dist/PIXIE_teaser_1080p.mp4 (muxed with the mix)
  python make.py all
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine.core import DIST, WORK  # noqa: E402
from engine import audio, render  # noqa: E402

MIX = os.path.join(DIST, "PIXIE_teaser_mix.wav")
OUT = os.path.join(DIST, "PIXIE_teaser_1080p.mp4")


def titles():
    subprocess.run(["bash", os.path.join(ROOT, "blender", "render_all.sh"), "48"], check=True)


def build_audio():
    tl = render.load_timeline()
    audio.build(tl, MIX)
    print(audio.stems_report(MIX))


def build_video(jobs=4):
    silent = render.video(jobs)
    if not os.path.exists(MIX):
        build_audio()
    os.makedirs(DIST, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", MIX, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart",
                    "-shortest", OUT], check=True)
    print(OUT)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("titles", "all"):
        if cmd == "titles":
            titles()
    if cmd in ("audio", "all"):
        build_audio()
    if cmd in ("video", "all"):
        build_video()
