#!/usr/bin/env python3
"""Split a short-form script Markdown file into one file per episode.

Usage:
    python3 split_episodes.py INPUT.md OUTPUT_DIR

Every `## N화 「제목」` section becomes OUTPUT_DIR/epNN.md (N zero-padded to
two digits), with its heading promoted to `# N화 「제목」`. The rest of the
section is copied unchanged. Text before the first episode heading goes to
OUTPUT_DIR/README.md.
"""
import argparse
import os
import re
import sys

EPISODE_RE = re.compile(r"^## (\d+)화(?=\s|$)(.*)$")


def split(text):
    """Return (preamble_lines, [(episode_number, section_lines), ...])."""
    preamble = []
    episodes = []
    current = None
    for line in text.splitlines():
        m = EPISODE_RE.match(line)
        if m:
            current = [line[1:]]  # "## N화 …" -> "# N화 …"
            episodes.append((int(m.group(1)), current))
        elif current is None:
            preamble.append(line)
        else:
            current.append(line)
    return preamble, episodes


def as_file_text(lines):
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    while lines and not lines[0].strip():
        lines = lines[1:]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", help="Markdown file with `## N화 …` episode headings")
    ap.add_argument("outdir", help="directory to write epNN.md and README.md into")
    args = ap.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        text = f.read()

    preamble, episodes = split(text)
    if not episodes:
        sys.exit("error: no `## N화` headings found in %s" % args.input)

    numbers = [n for n, _ in episodes]
    dupes = sorted({n for n in numbers if numbers.count(n) > 1})
    if dupes:
        sys.exit("error: duplicate episode numbers: %s" % dupes)
    expected = list(range(1, len(numbers) + 1))
    if sorted(numbers) != expected:
        print("warning: episode numbers are not 1..%d: %s" % (len(numbers), numbers),
              file=sys.stderr)

    os.makedirs(args.outdir, exist_ok=True)
    written = []
    if any(line.strip() for line in preamble):
        path = os.path.join(args.outdir, "README.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(as_file_text(preamble))
        written.append(path)
    for n, lines in episodes:
        path = os.path.join(args.outdir, "ep%02d.md" % n)
        with open(path, "w", encoding="utf-8") as f:
            f.write(as_file_text(lines))
        written.append(path)

    for path in written:
        print(path)
    print("%d episodes written to %s" % (len(episodes), args.outdir), file=sys.stderr)


if __name__ == "__main__":
    main()
