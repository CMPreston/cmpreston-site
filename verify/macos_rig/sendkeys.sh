#!/bin/bash
# Usage: ./sendkeys.sh KEY [KEY ...]
# Sends keys to the emulated guest via XTEST (keys go to the focused
# SheepShaver window). KEY syntax is xdotool keysym syntax: Return, F1,
# Escape, a, ctrl+alt+Delete, ... Modeled on verify/os2_rig/sendkeys.sh.
set -e
docker exec sheepbox sh -c "
  export DISPLAY=:99
  PID=\$(cat /tmp/sheepshaver.pid 2>/dev/null || echo NONE)
  WID=''
  for w in \$(xdotool search --onlyvisible --name 'SheepShaver'); do
    if xprop -id \$w _NET_WM_PID 2>/dev/null | grep -q \"= \$PID\$\"; then WID=\$w; fi
  done
  [ -z \"\$WID\" ] && WID=\$(xdotool search --onlyvisible --name 'SheepShaver' | tail -1)
  xdotool windowfocus --sync \$WID
  xdotool key --delay 120 $*
"
