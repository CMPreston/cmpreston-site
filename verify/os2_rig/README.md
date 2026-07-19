# OS/2 Warp 4 reference rig (86Box, headless, containerised)

How the `reference/os2/` screenshots were captured: real OS/2 Warp 4 (GA,
build 9.023) running at 640×480×256 in 86Box v6.0, inside a Debian
container with an Xvfb display, driven entirely over `docker exec`. This
is the reproducible half of the rig — the large binaries it needs are NOT
committed (they are the operator's OS media and IBM/vendor firmware):

- `OS2WARP4.iso` + the boot diskette images — operator-supplied Warp 4 CD
  rip (the canonical boot diskettes are inside the ISO under `/DISKIMGS`).
- 86Box v6.0 ROM set (`github.com/86Box/roms`, vendor BIOS dumps) mounted
  read-only at `/roms`.
- The 86Box arm64 Linux AppImage, extracted into the image at build.
- `w4hd.img` — the installed 1.97 GB HPFS system disk.

Place those beside these files and `docker build -t 86box-rig .`, then run
with `/work` bound to this dir and the ROM set bound at `/roms` (see the
`docker run` invocation echoed by `start86.sh`).

## Files

| file | role |
|---|---|
| `Dockerfile`, `entrypoint.sh`, `.dockerignore` | container: Xvfb + xdotool + ImageMagick + 86Box |
| `86box.cfg` | machine: ASUS P/I-P55T2P4 (i430HX), Pentium 133, 64 MB, S3 Trio64V+, HPFS IDE disk, ATAPI CD |
| `start86.sh` | (re)launch 86Box on `:99`, recording the real PID |
| `screenshot.sh` | `import`-capture the framebuffer to `shot.png` |
| `sendkeys.sh` | xdotool keysyms to the guest (Return, alt+f, ctrl+Escape, …) |
| `typetext.sh` | type a literal string + Enter (command line / editor) |
| `swap_floppy.sh`, `floppy_dialog_*.sh` | change floppy image via the 86Box Media menu (install-time) |
| `mouse.py` | closed-loop guest mouse driver — see the caveat below |
| `RIG.md` | full field notes: quirks, the mouse caveat, and the keyboard-only method |
| `INSTALL-PLAN.md` | the install runbook that was followed |

## The load-bearing lesson: drive it by keyboard

86Box reads the captured pointer as XInput2 **raw** device motion, which
XTest pointer-warping cannot synthesise under Xvfb, and it recenters the
host pointer every poll (so rapid relative warps cancel). `mouse.py`
exists and *can* nudge the guest cursor with settled single-step moves,
but precise positioning is unreliable on a busy backdrop. Everything real
here — the install and all six state captures — was done **by keyboard**:
Window List (`ctrl+Escape`) for focus, type-ahead icon selection, menu
mnemonics (`alt+<letter>`), object popups (`shift+F10`), and an OS/2
command prompt for `mkdir C:\Desktop\...` and launching `E`. See RIG.md.
