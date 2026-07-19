#!/bin/bash
# Usage: ./swap_floppy.sh /work/disk1.img
# Swaps the image in Floppy drive 1 of the running 86Box via the Media menu.
# Path must be the CONTAINER path (w4rig/ is bind-mounted at /work).
#
# *** WARNING (hard-won): TYPED-PATH swap is ONLY safe while the guest is in
# *** BIOS/loader context (POST, boot prompts of install.img). Once the OS/2
# *** KERNEL is running (from "Insert Diskette 2" onward), the keystrokes
# *** typed into the dialog leak into the guest KBC and GPF the kernel
# *** (reproducible TRAP 000d). In kernel context use the mouse-only pair:
# *** floppy_dialog_open.sh + floppy_dialog_pick.sh <rowY>.
#
# Implementation notes:
# - 86Box's raw keyboard filter swallows ALL key events while a Qt MENU is open,
#   so menu navigation must be done entirely with mouse clicks.
# - The modal file dialog DOES receive keyboard (86Box pauses emulation there),
#   so the path is typed into the "File name" field and confirmed with Return.
# - Coordinates are relative to the 86Box window origin (no WM; window at 0,0).
#   Menubar: Media label at (+127,+9). Media popup: Floppy 1 row at (+270,+33).
#   Floppy submenu: "Existing image..." at (+501,+59).
# - Window is picked by _NET_WM_PID == /tmp/86box.pid (stale-instance guard).
set -e
IMG="${1:?usage: swap_floppy.sh /work/diskN.img}"

docker exec w4box sh -c '
  export DISPLAY=:99
  IMG="$1"
  PID=$(cat /tmp/86box.pid 2>/dev/null || echo NONE)
  WID=""
  for w in $(xdotool search --onlyvisible --name "86Box"); do
    if xprop -id $w _NET_WM_PID 2>/dev/null | grep -q "= $PID$"; then WID=$w; fi
  done
  [ -z "$WID" ] && WID=$(xdotool search --onlyvisible --name "86Box" | tail -1)
  xdotool windowfocus --sync "$WID"
  eval "$(xdotool getwindowgeometry --shell "$WID")"   # sets X, Y, WIDTH, HEIGHT

  xdotool mousemove $((X + 127)) $((Y + 9)) click 1    # open Media menu
  sleep 0.6
  xdotool mousemove $((X + 270)) $((Y + 33)) click 1   # open Floppy 1 submenu
  sleep 0.6
  xdotool mousemove $((X + 501)) $((Y + 59)) click 1   # "Existing image..."
  sleep 1.5                                            # file dialog opens (emu pauses)
  xdotool key ctrl+a                                   # clear any prefilled name
  xdotool type --delay 40 "$IMG"
  sleep 0.3
  xdotool key Return
  sleep 1.0
  xdotool mousemove 900 700                            # park pointer off the UI
  xdotool windowfocus --sync "$WID"                    # guest keys work again
' sh "$IMG"
echo "floppy swapped to: $IMG"
