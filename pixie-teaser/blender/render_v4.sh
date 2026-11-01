#!/bin/bash
cd "$(dirname "$0")/.."
for shot in a_cold a_calm a_calc a_more a_soon; do
  /opt/bpyenv/bin/python blender/titles.py -- $shot --still 1 --samples ${1:-48} 2>&1 | grep -E "Saved|Error|Traceback"
done
