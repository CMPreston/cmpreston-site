#!/bin/bash
# Step 2 of the KERNEL-SAFE (mouse-only) floppy swap.
# Usage: ./floppy_dialog_pick.sh <rowY>
# Single-clicks the file row at (207, rowY) in the open dialog, then clicks the
# Open button (636,373). No keystrokes at all — safe while the OS/2 kernel runs.
# Verify afterwards with a screenshot (and/or the Media menu title).
set -e
ROWY="${1:?usage: floppy_dialog_pick.sh <rowY as seen in dialog.png>}"
docker exec w4box sh -c '
  export DISPLAY=:99
  ROWY="$1"
  PID=$(cat /tmp/86box.pid 2>/dev/null || echo NONE)
  WID=""
  for w in $(xdotool search --onlyvisible --name "86Box"); do
    if xprop -id $w _NET_WM_PID 2>/dev/null | grep -q "= $PID$"; then WID=$w; fi
  done
  [ -z "$WID" ] && WID=$(xdotool search --onlyvisible --name "86Box" | tail -1)
  xdotool mousemove 207 "$ROWY" click 1
  sleep 0.6
  xdotool mousemove 636 373 click 1                    # Open button
  sleep 1.2
  xdotool mousemove 900 700                            # park pointer
  xdotool windowfocus --sync "$WID"
' sh "$ROWY"
echo "picked row y=$ROWY and clicked Open"
