#!/bin/bash
# Usage: ./sendkeys.sh KEY [KEY ...]
# Sends keys to the emulated guest via XTEST (keys go to the focused 86Box window).
# KEY syntax is xdotool keysym syntax: Return, F1, Escape, a, ctrl+alt+Delete, ...
# Targets the window whose _NET_WM_PID matches /tmp/86box.pid (stale instances
# once stole keystrokes; keys must go to the LIVE instance). Fallback: highest id.
set -e
docker exec w4box sh -c "
  export DISPLAY=:99
  PID=\$(cat /tmp/86box.pid 2>/dev/null || echo NONE)
  WID=''
  for w in \$(xdotool search --onlyvisible --name '86Box'); do
    if xprop -id \$w _NET_WM_PID 2>/dev/null | grep -q \"= \$PID\$\"; then WID=\$w; fi
  done
  [ -z \"\$WID\" ] && WID=\$(xdotool search --onlyvisible --name '86Box' | tail -1)
  xdotool windowfocus --sync \$WID
  xdotool key --delay 120 $*
"
