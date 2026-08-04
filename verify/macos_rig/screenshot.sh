#!/bin/bash
# Usage: ./screenshot.sh [outfile.png]   (default: shot.png in macos_rig/, host-visible)
# Captures the full Xvfb root window (SheepShaver's window sits on it).
# Modeled on verify/os2_rig/screenshot.sh.
OUT="${1:-shot.png}"
docker exec sheepbox import -display :99 -window root "/work/$OUT"
echo "saved: $OUT"
