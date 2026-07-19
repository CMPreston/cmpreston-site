#!/bin/bash
# Usage: ./screenshot.sh [outfile.png]   (default: shot.png in w4rig/, host-visible)
# Captures the full Xvfb root window (includes 86Box menubar + emulated display).
OUT="${1:-shot.png}"
docker exec w4box import -display :99 -window root "/work/$OUT"
echo "saved: $OUT"
