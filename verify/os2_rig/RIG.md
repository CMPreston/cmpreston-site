# w4rig — headless 86Box rig for the OS/2 Warp 4 install

86Box v6.0 (build 9001, arm64 NDR/interpreter AppImage) running under Xvfb `:99`
inside a Debian bookworm container. Driven entirely by `docker exec` + xdotool.
All rig files live in this directory, bind-mounted at `/work` in the container.

## Container

Build (context is this dir; `.dockerignore` keeps the ISO/disk images out):

```sh
docker build -t 86box-rig .
```

Run (ROMs mounted read-only from the real ROM dir — Docker cannot follow the
`roms-link` symlink, mount the target):

```sh
docker run -d --name w4box \
  -v "<abs path to w4rig>":/work \
  -v "/Users/cpreston/Library/Application Support/net.86box.86Box/roms":/roms:ro \
  86box-rig
```

- Entrypoint starts `Xvfb :99 -screen 0 1024x768x24`, then (unless `AUTOSTART=0`)
  launches 86Box via `start86.sh`, then stays alive with `tail -f`.
- Restart 86Box any time without touching the container:
  `docker exec w4box /usr/local/bin/start86.sh` (kills the old instance, log at
  `/work/86box.log`, pid at `/tmp/86box.pid`).
- 86Box command line used:
  `/opt/86box/AppRun --config /work/86box.cfg --vmpath /work --rompath /roms --noconfirm`
- The AppImage is extracted at image build time (`--appimage-extract`, no FUSE)
  to `/opt/86box/`; real binary at `/opt/86box/usr/local/bin/86Box`. It is a Qt5
  build and bundles its own glibc 2.31 compat, so base-image glibc is irrelevant.

## Emulated machine (all IDs verified against 86Box v6.0 source + ROM set)

| Item | Value |
|---|---|
| Machine | `p55t2p4` — ASUS P/I-P55T2P4, i430HX, Award 4.51PG (ROM `roms/machines/p55t2p4/0207_j2.bin`) |
| CPU | `pentium_p54c`, 133 MHz (`cpu_speed = 133333333`, `cpu_multi = 2`) |
| RAM | `mem_size = 65536` (64 MB — do not raise for Warp 4 GA) |
| Video | `s3_trio64vplus_pci` (S3 Trio64V+ PCI, 4 MB, ROM `roms/video/s3/S3T64VP.VBI` Cardex default; Phoenix `64V1506.ROM` also present) |
| HDD | `hdd_01_parameters = 63, 16, 4092, 0, ide` → 2,111,864,832 B (~1.97 GB) raw sparse image `/work/w4hd.img`, primary master; BIOS sees "LBA, Mode 4, 2112MB" |
| Floppy | `fdd_01_type = 35_2hd`, drive 2 disabled |
| CD-ROM | ATAPI secondary master (`cdrom_01_ide_channel = 1:0`), `/work/OS2WARP4.iso` |
| Mouse | `mouse_type = ps2` (2-button PS/2) |
| Sound/NIC | none |
| Renderer | Qt Software (`vid_renderer = qt_software`, written back by 86Box) |

86Box normalizes/rewrites `86box.cfg` in place on start (sorts keys, adds
`uuid`, relativizes paths against `/work`). Don't fight it; hand edits are fine
while 86Box is stopped.

## Control primitives (all verified working)

### Screenshot

```sh
docker exec w4box import -display :99 -window root /work/shot.png
# or: ./screenshot.sh [name.png]
```

The PNG lands in w4rig/ on the host. Captures the whole Xvfb root (86Box window
sits at 0,0; guest display area starts ~y=54 below menubar+toolbar).

### Keystrokes to the guest

```sh
./sendkeys.sh Return          # xdotool keysym syntax
./sendkeys.sh F1
./sendkeys.sh ctrl+alt+Delete
./typetext.sh "some string"   # literal text
```

Mechanism: `xdotool search --onlyvisible --name 86Box` → `windowfocus --sync` →
`xdotool key` (XTEST). 86Box forwards keys to the guest whenever its window has
X input focus (`kbd_req_capture = 0` default; mouse capture NOT required).
Verified: F1 advanced the BIOS "CMOS checksum error" pause; Enter advanced the
installer diskette prompts.

### Floppy swap (the load-bearing one)

```sh
./swap_floppy.sh /work/disk1.img    # container path!
```

Sequence (mouse-only for menus — see quirks): click **Media** (win origin
+127,+9) → click **Floppy 1** row (+270,+33) → click **Existing image…**
(+501,+59) → modal Qt file dialog opens (86Box auto-PAUSES emulation) → type
absolute path into the focused "File name" field (`ctrl+a` first) → `Return` →
dialog closes, emulation resumes → park pointer at (900,700), refocus window.

Verified end-to-end: menu title changed to `/work/disk1.img` after the swap and
the installer proceeded past the "Insert Diskette 1" prompt.

To verify a swap visually at any time (menu open/close leaves guest state
untouched):

```sh
docker exec w4box sh -c 'export DISPLAY=:99; xdotool mousemove 127 9 click 1; sleep 0.6; \
  import -window root /tmp/m.png; convert /tmp/m.png -crop 440x100+100+20 /work/menucrop.png; \
  xdotool mousemove 127 9 click 1; xdotool mousemove 900 700'
```

## Quirks the main workflow must know

1. **Keyboard is DEAD while a Qt menu is open.** 86Box's raw-input filter
   swallows every key event during menu popups (mnemonics, arrows, Escape —
   nothing works). Navigate menus with mouse clicks only. Close a stray menu by
   clicking the menubar label again. The modal file dialog is the exception:
   it receives keyboard normally.
2. **Never click inside the guest display area** — that captures the mouse into
   the guest and the pointer disappears from X's control. All scripts park the
   pointer at (900,700), outside the 86Box window. If capture ever happens,
   easiest recovery is `docker exec w4box /usr/local/bin/start86.sh` (restarts
   the emulator; state loss = reboot of guest).
3. **First cold boot pauses in POST**: "CMOS checksum error — Press F1 to
   continue" (fresh NVR). `./sendkeys.sh F1` clears it. Recurs only if
   `/work/nvr/` is wiped.
4. **Timing**: BIOS POST→floppy boot ~15 s; install.img→blue IBM installer
   screen ~60 s total from 86Box start. Interpreter build; be patient, poll
   screenshots rather than assuming failure. Screen-change detection that works:
   compare md5 of `import png:-` output, or average-color of a center crop
   (blue screen = B>>R).
5. **Window geometry moves with guest video mode** (e.g. 640x400→720x480 text
   modes). Window stays at (0,0); menubar offsets are stable. The swap script
   re-reads geometry each run via `xdotool getwindowgeometry --shell`.
6. **`--config /work/86box.cfg` appears split in `ps` output** (AppRun `$@`
   re-tokenization) but the config IS loaded correctly (verified: 86Box
   rewrote the file, correct machine booted).
7. Harmless log noise: ALSA "cannot open device" + OpenAL warnings (no sound
   HW in container), `gamemodeauto` dlopen failure.
8. Do NOT mount a second floppy drive or extra devices without need — the Media
   menu row coordinates in `swap_floppy.sh` assume exactly: Floppy 1 row,
   CD-ROM 1 row, "Clear image history".

## Proof screenshots

- `proof-installer.png` — blue IBM "OS/2 Warp version 4 Installation" first
  screen (with Diskette 1 insert prompt), rendered by 86Box in the container.
- `proof-disk2prompt.png` — "Insert Diskette 2" prompt reached after
  `swap_floppy.sh /work/disk1.img` + Enter, validating the swap primitive.

## Current boot state

Guest is sitting at the "Insert the OS/2 Diskette 2 into drive A. Then, press
Enter." prompt with disk1.img still in the drive. Next steps for the main
workflow: `./swap_floppy.sh /work/disk2.img` then `./sendkeys.sh Return`.
Install deliberately NOT continued past this point. `/work/w4hd.img` is still
blank/unpartitioned. 86Box has been running continuously since first boot
(container `w4box`, emulator pid in `/tmp/86box.pid`).

## MOUSE WORKS (correction to earlier "mouse unusable" note)
The earlier conclusion that the guest mouse is unusable was WRONG. Root cause
of the confusion: 86Box only feeds mouse to the guest while the window has
CAPTURED the pointer, AND it recenters the host pointer every poll — so RAPID
relative warps (xdotool mousemove_relative in a tight loop) cancel to zero net
motion. The guest cursor never moved, which read as "dead."

Fix (proven): capture once, then issue ONE settled relative move at a time with
a ~0.35s pause between moves. The guest cursor then tracks precisely.
- Capture: move host pointer into the render area and click once (bar flips to
  "Press Ctrl+End or middle button to release mouse").
- Move: single `xdotool mousemove_relative --sync -- DX DY`, pause, repeat.
- Release: Ctrl+End (or middle button).
Driver: mouse.py (cap / rel / to GX GY / click / dblclick / rclick), closed-loop
via wiggle-diff cursor detection. Guest (0,0) ≈ window (0,55); guest crop box
(0,55,640,535) for a 640×480 mode.
This unblocks Selective Install (sidesteps the twin-window keyboard-focus bug)
and all WPS staging.

## KEYBOARD-ONLY CONTROL (proven reliable — PREFER THIS OVER THE MOUSE)
The guest mouse is unreliable headless (detection false-matches on the
dithered backdrop; 86Box recentering corrupts relative moves). Do NOT fight
it — drive everything by keyboard. Proven vocabulary:
- ./sendkeys.sh <keysyms>   e.g. Return, Escape, Down, Up, Tab, alt+f, ctrl+Escape, shift+F10, alt+F4
- ./typetext.sh "literal"   types a literal string + Enter (for command line / editor text)
- ./screenshot.sh -> shot.png (=w4rig/shot.png). Read it. Guest crop box (0,52,640,532)=640x480.
Focus the DESKTOP reliably: Ctrl+Esc (Window List) -> "Desktop - Icon View" is
preselected -> Return. Then type-ahead selects desktop icons by first letter
(e.g. 'o' selects "OS/2 System"), Return opens.
Open a folder's contents: select icon (type-ahead/arrows) -> Return.
Menus: alt+<mnemonic> opens a menu bar menu; arrows + Return pick items; Escape closes.
Object popup (context menu): select the object, then shift+F10.
Command line: OS/2 System -> Command Prompts -> "OS/2 Window". mkdir under
C:\Desktop makes desktop folder objects. `E <path>` opens the System Editor.
Already created on disk: C:\Desktop\Poems and C:\Desktop\Poems\Demos.
