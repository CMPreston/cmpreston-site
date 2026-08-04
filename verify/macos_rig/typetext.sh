#!/bin/bash
# Usage: ./typetext.sh "literal text"
# Types a literal string into the focused SheepShaver window via xdotool.
set -e
TEXT="$1"
docker exec sheepbox env DISPLAY=:99 bash -c '
  WID=$(xdotool search --onlyvisible --name "SheepShaver" | tail -1)
  xdotool windowfocus --sync "$WID"
  xdotool type --delay 60 -- "$1"
' _ "$TEXT"
