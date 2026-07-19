#!/bin/bash
# Types a literal string into the guest, then Enter. Usage: ./typetext.sh "text"
docker exec w4box sh -c "
  export DISPLAY=:99
  WID=\$(xdotool search --onlyvisible --name '86Box' | tail -1)
  xdotool windowfocus --sync \$WID
  xdotool type --delay 40 -- \"\$1\"
  xdotool key Return
" -- "$1"
