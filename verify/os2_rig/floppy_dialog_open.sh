#!/bin/bash
# Step 1 of the KERNEL-SAFE (mouse-only) floppy swap.
# Opens Media > Floppy 1 > "Existing image..." and screenshots the file dialog
# to /work/dialog.png (= w4rig/dialog.png). Emulation auto-pauses while open.
# Read the screenshot, find your image's row Y, then run floppy_dialog_pick.sh Y.
# NEVER type while this dialog is open if the OS/2 kernel is running (TRAP 000d).
set -e
docker exec w4box sh -c '
  export DISPLAY=:99
  PID=$(cat /tmp/86box.pid 2>/dev/null || echo NONE)
  WID=""
  for w in $(xdotool search --onlyvisible --name "86Box"); do
    if xprop -id $w _NET_WM_PID 2>/dev/null | grep -q "= $PID$"; then WID=$w; fi
  done
  [ -z "$WID" ] && WID=$(xdotool search --onlyvisible --name "86Box" | tail -1)
  xdotool windowfocus --sync "$WID"
  eval "$(xdotool getwindowgeometry --shell "$WID")"
  xdotool mousemove $((X + 127)) $((Y + 9)) click 1    # Media menu
  sleep 0.6
  xdotool mousemove $((X + 270)) $((Y + 33)) click 1   # Floppy 1 submenu
  sleep 0.8
  xdotool mousemove $((X + 460)) $((Y + 59)) click 1   # "Existing image..."
  sleep 2
  import -window root /work/dialog.png
'
echo "dialog open, screenshot at w4rig/dialog.png — now pick a row with floppy_dialog_pick.sh <Y>"
