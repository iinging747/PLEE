"""Render the teaser's sound effects with the ElevenLabs Sound Effects API.

  ELEVENLABS_API_KEY=... python tools/elevenlabs_sfx.py [name ...]

Writes sfx/<name>.wav (48 kHz stereo). engine/sfx.py picks these up automatically on the next
`python make.py audio`. Without names, every entry in tools/elevenlabs_sfx.json is rendered.
"""
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192"


def render(name, spec, key):
    body = json.dumps({"text": spec["text"], "duration_seconds": spec["duration"],
                       "prompt_influence": spec.get("influence", 0.5)}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json",
                                          "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=180) as r:
        mp3 = r.read()
    out = os.path.join(ROOT, "sfx", name + ".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "mp3", "-i", "-", "-ar", "48000", "-ac", "2", out],
                   input=mp3, check=True)
    print("wrote", out)


def main():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("set ELEVENLABS_API_KEY")
    specs = json.load(open(os.path.join(ROOT, "tools", "elevenlabs_sfx.json")))
    specs.pop("_note", None)
    names = sys.argv[1:] or list(specs)
    os.makedirs(os.path.join(ROOT, "sfx"), exist_ok=True)
    for n in names:
        render(n, specs[n], key)


if __name__ == "__main__":
    main()
