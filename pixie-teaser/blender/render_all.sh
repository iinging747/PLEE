#!/bin/bash
# Render every chrome title still (Cycles CPU). Usage: bash blender/render_all.sh [samples]
cd "$(dirname "$0")/.."
S=${1:-48}
for shot in logo ch_trading ch_lifestyle ch_beauty ch_travel more cold calm calculated world live; do
  /opt/bpyenv/bin/python blender/titles.py -- $shot --still 1 --samples $S 2>&1 | grep -E "Saved|Error|Traceback"
done
