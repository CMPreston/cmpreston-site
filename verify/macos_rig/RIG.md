# macos_rig — headless SheepShaver rig for real Mac OS 8.6 reference captures

How `reference/macos/` and `reference/raw/macos-emulator/` were captured: real Mac
OS 8.6 running under SheepShaver, inside a Debian container with an Xvfb
display, driven entirely over `docker exec` — the same idiom as
`verify/os2_rig/` (Xvfb + xdotool + ImageMagick), modeled on it directly.
The QEMU rung was tried first per the house method (`verify/beos_rig/`) and
failed for an architectural reason documented below.

## Media and provenance

- `macos86.iso` (630,257,664 bytes) — operator-supplied Mac OS 8.6 install CD
  image. Gitignored, never committed. Structure verified before this rig was
  built: Apple Driver Map (blocksize 2048), Apple Partition Map, one bootable
  HFS partition named "Macintosh HD", start block 964 (512-byte units, byte
  offset 493568), length 1,228,800 blocks (629,145,600 bytes).
- No OS media, ROMs, or third-party emulators were downloaded. The Mac OS
  Toolbox ROM used by SheepShaver comes from the operator's own ISO (see
  "ROM extraction" below) — that provenance is the load-bearing legal fact
  for this rig, per the same logic as the BeOS/OS-2 rigs.

## Early check: full install CD, not update-only

The brief called for determining this before doing anything else, since a
Mac OS 8.6 *Update* CD requires a pre-existing Mac OS 8.5 system and cannot
fresh-install. Verified **full/OEM install CD, not update-only**, from the
CD's own contents (read via `hfsutils` and the `machfs` Python library,
before any emulator was involved):

- The volume (name "Mac OS 8.6") contains BOTH `Full Install Pieces/` and
  `Update Install Pieces/` top-level folders, each with their own
  `Software Installers/System Software`. The presence of a full-install
  piece set is the first signal.
- The CD carries its own top-level bootable `System Folder` (Apple Menu
  Items, Control Panels, Extensions, Fonts, Help, Preferences, Scripting
  Additions) — a minimal CD-boot System Folder used to start up from the CD
  and run the installer on a machine with no existing system at all.
- Decisive evidence: the CD's own `Installing Mac OS 8.6` read-me (SimpleText
  file, read directly off the HFS volume) says explicitly: *"4. Start up
  your computer using the Mac OS CD... 5. It's recommended that you do an
  easy installation to update your system software. If you plan to do a
  clean installation instead, write down your current Internet settings..."*
  — i.e. the CD itself documents both an update path and a from-scratch
  clean-install path, unconditional on any pre-existing system.

## ROM extraction and provenance

SheepShaver needs a New World "Mac OS ROM" file. Per `macemu/README.md`'s
installation notes (quoted there almost verbatim): *"SheepShaver can also
use the 'Mac OS ROM' file that comes with MacOS 8.5/8.6 (look in the System
Folder on your MacOS CD)."* Extraction method (no network fetch involved,
entirely from the operator's own ISO):

1. Carved the HFS partition out of the raw ISO with `dd` at the verified
   offsets (`bs=512 skip=964 count=1228800`) &rarr; `hfs_partition.raw`
   (gitignored).
2. Read it two ways, both installed here as open-source tools (see
   "Fetched tools" below): `hfsutils` (`hmount` + `hls`) and the `machfs`
   Python library. Both agree: `/System Folder/Mac OS ROM`, HFS type/creator
   `tbxi`/`chrp`, data fork 1,945,332 bytes, resource fork 3,438 bytes.
3. Extracted the **data fork only** (`machfs`, `item.data`) to
   `macos_rom.rom` (gitignored — never commit an Apple ROM dump). Its first
   bytes are a `<CHRP-BOOT>` text header:
   `<CHRP-BOOT><COMPATIBLE>iMac,1 PowerMac1,1 PowerBook1,1</COMPATIBLE>
   <DESCRIPTION>MacROM for NewWorld.</DESCRIPTION>...` — confirms it is a
   genuine New World ROM image compatible with the iMac/PowerMac1,1/
   PowerBook1,1 family SheepShaver emulates.

## Emulator ladder

### Rung 1 — QEMU on the host: empirically FAILED (architectural, not a flag/config problem)

`qemu-system-ppc` 11.0.2 (`/opt/homebrew/bin`, already installed) was tried
on both candidate machines, per the brief. Work directory
`verify/macos_rig/qemu_work/` (gitignored scratch; not committed).

Base command (both machines), HMP monitor on a unix socket for closed-loop
screendump control, modeled on `verify/beos_rig/qemu_ctl.py` (copied
locally as `verify/macos_rig/qemu_ctl.py`, stdlib-only, unmodified logic):

```sh
qemu-system-ppc -M mac99,via=pmu -m 256 \
  -cdrom macos86.iso -hda macos.img -boot d -display none \
  -monitor unix:mon.sock,server=on,wait=off \
  -prom-env 'boot-device=cd:,\:tbxi'
```

(and the same with `-M g3beige`, dropping `via=pmu` which is mac99-only).

Result, identical on **both** `mac99,via=pmu` and `g3beige`: OpenBIOS 1.1
(built Sep 24 2024, the version bundled with this QEMU) boots to its Forth
prompt and reports:

```
Welcome to OpenBIOS v1.1 built on Sep 24 2024 19:56
Trying cd:,\:tbxi...
No valid state has been set by load or init-program
0 >
```

Diagnosis, established interactively at the Forth prompt (screendumps
`qemu_work/shot1.png` .. `shot8.png`, not committed — scratch):

- `show-devs` confirms the device tree is sane: `/packages/hfs-files` and
  `/packages/mac-parts` are loaded (HFS + Apple Partition Map support
  exists in this OpenBIOS build), and `cd`/`hd` aliases correctly resolve
  to the ATA cdrom/disk nodes (`.properties` on `/aliases` matched
  `show-devs`' own tree exactly).
- `dir cd:,\` **works** and lists the CD's real top-level HFS contents
  exactly as `machfs` reported them independently (About Mac OS 8.5, Full
  Install Pieces, System Folder, etc.) — OpenBIOS's HFS reader is not the
  problem.
- `boot cd:,\System Folder\Mac OS ROM` (explicit path, bypassing whatever
  `\:tbxi` type-search does) no longer prints "Trying..." — i.e. the file
  *was* located — but still ends in the same "No valid state has been set
  by load or init-program".
- Tried feeding the extracted ROM straight to QEMU's `mac99` `firmware=`
  machine property (`-M mac99,via=pmu,firmware=macos_rom.rom`): hard
  rejection, `qemu-system-ppc: ../macos_rom.bin exceeds maximum image size
  (1 MiB)` — that property expects an OpenBIOS-sized firmware replacement,
  not a 1.9 MB Toolbox ROM.

Conclusion: OpenBIOS's HFS/CD boot path can **read** the volume and **find**
the `tbxi` file, but has no code path to **execute** it. The `<CHRP-BOOT>`
header on this ROM is a compatibility/description/icon badge (used by a
real New World Mac's onboard boot ROM to load this file into RAM as a
Toolbox supplement) — it is not a CHRP ELF/FCode kernel image of the kind
OpenBIOS's loader knows how to hand off to (that's the Linux/BSD path,
e.g. yaboot). This matches the brief's own steer ("classic Mac OS 8.6 is
doubtful" on mac99) but is now an empirically confirmed, reproducible
verdict rather than an assumption, and it is a vanilla-QEMU/OpenBIOS
limitation independent of boot-device flags, RAM size, or machine choice.
Time spent on this rung: well inside the ~60-90 minute box.

### Rung 2 — SheepShaver, containerized: environment blocker, then resolved without Docker Desktop

Docker Desktop's CLI was present but its daemon was down. `open -a Docker`
was tried per the brief; the daemon never came up because Docker Desktop's
first-run bring-up on this host stalls on a **modal, interactive macOS
admin-password prompt** (`osascript ... "Docker Desktop requires privileged
access to configure privileged port mapping" ... with administrator
privileges`) — confirmed by inspecting the actual running processes, not
assumed. Separately confirmed the host's own display was not capturable at
all (`screencapture` failed: "could not create image from display"),
consistent with a locked/asleep session. Both facts together rule out
*any* GUI-dependent path tonight, including a native (non-Docker)
SheepShaver fallback — that fallback needs a capturable display and
synthetic input into a real window, neither of which is available right
now. No attempt was made to dismiss or work around the admin prompt: that
would mean guessing/bypassing an authentication control, which is out of
scope regardless of task urgency.

**Resolution: `colima`** (github.com/colima-io/colima, MIT license, via
Homebrew — an allowed open-source fetch), a Lima-based container runtime
that talks to macOS's native `Virtualization.framework` (`vz`) directly and
needs no Docker Desktop GUI and no interactive privileged-helper step:

```sh
brew install colima          # pulled lima 2.2.0 as a dependency
colima start --cpu 2 --memory 4 --disk 20
```

This came up entirely headlessly (log excerpt): `"[hostagent] Starting VZ"`
&rarr; `"[hostagent] [VZ] - vm state change: running"` &rarr; forwards
`/var/run/docker.sock` to a host socket and registers a `colima` Docker CLI
context. `docker ps` / `docker info` (`Architecture: aarch64`, `OSType:
linux`) worked immediately after, with zero GUI interaction of any kind.
This is a swap of *which* Linux VM backs the `docker` CLI, not a departure
from "run SheepShaver in a Docker container" — the rest of the rig is
identical to the OS/2 rig's Docker/Xvfb/xdotool/ImageMagick idiom.

## Container build

`verify/macos_rig/Dockerfile`: `debian:bookworm-slim` + the same headless
stack as `verify/os2_rig/Dockerfile` (`xvfb xauth x11-utils xdotool
imagemagick procps fonts-dejavu-core`) plus a build toolchain, since
SheepShaver ships no binary release and must be compiled from source:
`build-essential autoconf automake libtool pkg-config git libsdl2-dev
libgtk-3-dev libreadline-dev zlib1g-dev`.

Source: `github.com/kanjitalk755/macemu` (the actively maintained
SheepShaver/BasiliskII fork), GPLv2, fetched at image-build time via
`git clone --depth 1` (recorded here for provenance; never vendored into
the repo). Build, straight from `macemu/README.md`'s documented Linux
recipe:

```sh
cd SheepShaver/src/Unix
./autogen.sh --enable-sdl-video --disable-sdl-audio --without-esd \
             --with-gtk=gtk3 --disable-xf86-dga --disable-xf86-vidmode \
             --disable-fbdev-dga --disable-vosf --with-mon=no
make -j"$(nproc)"
```

DGA/VidMode/fbdev direct-framebuffer extensions are disabled because we run
**windowed** under Xvfb (no direct hardware framebuffer to hand out) — same
"windowed, not exclusive" posture as the 86Box rig. The container's guest
architecture is `aarch64` (colima's VM matches the Apple Silicon host), and
`macemu/README.md` documents that the PPC JIT is x86_64-only — arm64 Linux
builds auto-select the portable interpreter core (`kpx_cpu`). This is the
same "no JIT on arm64, interpreter is fine" precedent the 86Box rig set for
OS/2 Warp 4. Source pinned at commit `ba0bf07013d4d1c38beef8c8f697bef495a36c81`
(2026-08-02) for reproducibility.

## Two SheepShaver crashes and their fixes

Both were real, reproducible crashes (not config typos), diagnosed from the
source rather than guessed at, since this is the exact "correctness over
completeness, report honestly" territory the brief asked for.

### 1. `Cannot map Low Memory Globals: Operation not permitted` (start-up)

SheepShaver's `real`-addressing mode (the configure default) needs to
`mmap(MAP_FIXED)` the guest's low-memory globals at literal **host virtual
address 0** (`main_unix.cpp`, `vm_mac_acquire_fixed(0, 0x3000)`). Modern
Linux refuses this via `vm.mmap_min_addr` (a NULL-deref exploit mitigation).
Fixed at the colima-VM kernel level (this sysctl is global, not per-container-
namespace, and colima's VM is ours alone to tune):

```sh
colima ssh -- sudo sysctl -w vm.mmap_min_addr=0
```

### 2. SIGSEGV deeper in emulation, after the above fix

With `mmap_min_addr=0`, start-up got past the low-memory mapping but then
SIGSEGV'd with a live PPC register dump (real, non-zero register contents —
this was mid-emulation, not start-up). `real`-addressing (host address ==
guest address, literally) is fragile on a 64-bit host beyond just the
zero-page case. Fix: rebuilt with `--enable-addressing=direct` (base-offset
host&harr;guest translation — the documented, more portable alternative).
This fully resolved it; every subsequent boot, install, restart-via-relaunch,
and staging action ran crash-free.

## Install

Booted the freshly-built container, `Install Mac OS 8.6 (UK)` ran from the
CD (the CD's own bootable System Folder), targeting a blank 2 GB sparse
raw disk image (`macos_hd.img`, `truncate -s 2G`, gitignored). Steps, all
verified screenshot-by-screenshot (never blind input):

1. First boot: Finder auto-offers to initialise the blank disk (`This disk
   is unreadable... Do you want to initialise the disk?`) &rarr; Mac OS
   Standard, named "untitled" at this point.
2. Launched `Install Mac OS 8.6`, walked Welcome &rarr; Select Destination
   ("untitled", "None Installed", 2045 MB available, 224 MB required for a
   basic installation) &rarr; Important Information &rarr; Software Licence
   Agreement (British) &rarr; Agree &rarr; Start. Easy Install, default
   component set, no customisation.
3. Install ran for real (guest-reported ETA ~4 minutes; actual wall clock
   was comparable — the arm64 interpreter is not noticeably slow for this
   workload). Finished cleanly: "The installation process has finished."
4. Quit the installer, **Special > Restart** to boot from the HDD instead
   of the CD — **this crashed the emulator** (see "in-guest Restart" below).
   Recovered by relaunching the SheepShaver process fresh from the host
   (`start_sheep.sh`) rather than trusting the guest's own restart routine;
   the now-blessed HDD booted directly into the installed system (its own
   default purple desktop pattern, distinct from the CD's grey "CD" pattern
   used during install — a useful visual tell that boot device switched
   correctly).
5. First-boot **Mac OS Setup Assistant** dismissed via its close box &rarr;
   "Are you sure you want to quit? ... Quit" (answers not needed for a
   default-appearance rig).
6. Renamed the boot volume from "untitled" to **"Macintosh HD"** (single
   click to select, second click on the name to enter rename mode, type,
   Return) to match the state spec's required desktop icon name — this is
   the one cosmetic change made, because the brief's canonical-state spec
   explicitly names it.
7. Ejected the install CD (select icon, File > Put Away) so it wouldn't
   appear as an extra desktop icon in the reference captures.

### The in-guest Restart bug (real, reproducible, worth flagging)

`Special > Restart` from the CD-booted Finder reliably SIGSEGV'd the
emulator (live PPC register dump, non-zero — a real fault in whatever code
path the guest's restart/reset routine exercises under this interpreter
build), even after the addressing-mode fix above. **Workaround, not a
root-cause fix**: never use the guest's Restart menu item; instead kill and
relaunch the host-side SheepShaver process (`start_sheep.sh`, which is
idempotent — kill-if-running then start fresh). Because the HDD was already
"blessed" (valid System Folder), a fresh process launch boots straight from
it exactly as a real Restart would have. **Flag for whoever touches this rig
next**: avoid triggering a guest-side Restart/Shut-Down-then-restart cycle;
if a future session needs one, expect to work around it the same way, and
budget time to actually root-cause it (likely somewhere in the ADB/reset
emulation given the crash is deep in emulated execution, not start-up).

## Input control (verified empirically, closed-loop, exactly like BeOS/OS-2)

**Mouse works normally** — the load-bearing difference from both prior rigs.
SheepShaver's SDL2 video backend takes ordinary X11 pointer events, so
plain `xdotool mousemove X Y click 1` behaves exactly as on a normal X
window (verified: the guest cursor sprite is drawn at the literal clicked
position every time, confirmed over dozens of clicks/drags). No wiggle-
detection, no capture/release dance, no raw-input workaround needed —
unlike 86Box (XInput2 raw-motion capture) or BeOS (relative PS/2
acceleration). Drag-and-drop (window title bars, icon-to-Wastebasket) works
with plain `mousedown` / `mousemove` / `mouseup`.

**Guest window offset**: the SDL window is borderless under Xvfb and its
(0,0) sits at Xvfb-root (192,144) for the `win/640/480` mode used here —
computed once from a full-black-background bounding box, reused via
`crop_guest.py`. Re-derive it if the window manager or SDL version changes.

**Keyboard mostly works, with two real gotchas worth recording:**

1. **`xdotool type`'s embedded `\n` is silently dropped**, not sent as
   Return. First poem-typing attempt produced all four lines run together
   on one line. Fix: type each line as a separate `xdotool type` call and
   send `Return` as its own explicit `xdotool key` between them (see
   `typetext.sh` / `sendkeys.sh` usage in the staging log below).
2. **No reliable Command-key mapping was found.** `ctrl+a` in a text field
   did **not** act as Select-All (classic Mac text widgets don't bind
   Ctrl-A that way, and the SDL layer's Mac-Command emulation was not
   discoverable in the time available) — it inserted a literal control
   character instead, corrupting a filename mid-edit. Worked around
   entirely without Command-key chords: Select All was reached via the
   **Edit menu** click path instead of `⌘A`; clearing a text field was done
   with repeated literal `BackSpace` keysyms. **Also observed:** a text
   field can silently drop further keystrokes after a burst of rapid
   `docker exec` round-trips (a `BackSpace` batch stopped taking effect
   partway through); the fix was always to click back into the field to
   re-confirm focus before continuing to type/delete. Any follow-on agent
   scripting text entry here should click-to-refocus before each burst
   rather than assuming focus persists across many rapid separate
   `docker exec` calls.

## Staging (per the brief's spec, all verified by screenshot after each step)

- **Poems/Demos**: clicked bare desktop (to target the Finder/Desktop, not
  whatever was frontmost) &rarr; File > New Folder &rarr; typed "Poems" &rarr;
  Return. Opened it, File > New Folder &rarr; "Demos" &rarr; Return, left empty.
- **Nested/cascade (state 03)**: opening a child folder from a parent
  reused the exact same window frame/position as the parent (fully
  overlapping it, not offset) — this is the real Finder's own default
  window-placement behaviour here, not a bug. Dragged the Demos title bar
  to a new position by hand to produce the cascade the state spec wants.
- **SimpleText document**: found `SimpleText` in `Macintosh HD/Applications/`
  (not aliased in the Apple Menu Items list). Typed the four lines with
  explicit `Return`s per the gotcha above; verified the exact text and
  caret position by screenshot before saving. Saved to the **Desktop**
  (File > Save, "Desktop" button in the Save dialog, typed filename,
  Save) — the brief didn't mandate a save location, and Desktop keeps
  state 04's "clean desktop, no Finder windows" easy to arrange (just
  close the one document window).
- **Context menu (state 05)**: `xdotool keydown ctrl` &rarr; click &rarr;
  `keyup ctrl` on bare desktop. Worked first try; standard Mac OS 8
  Control-click contextual menus are enabled by default.
- **Empty-Wastebasket dialog (state 06)**: made a disposable "throwaway"
  folder on the desktop, dragged it onto the Wastebasket icon (verified the
  "full trash" icon glyph appeared), Special > Empty Wastebasket (this UK
  build's Finder says "Wastebasket", not "Trash" — a real localisation
  detail, not a typo), captured the confirmation alert, then clicked OK for
  real so the rig ends in a clean, empty-trash state.
- **Colour depth**: checked (didn't need to change) via Apple menu >
  Control Panels > Monitors & Sound &rarr; already at **Millions** of
  colours, 640&times;480 at 75 Hz — exceeds the brief's "thousands if
  attainable" bar.

## Results: the six canonical states

All captured at the guest's native 640&times;480, cropped losslessly from
the Xvfb root capture (no scaling), saved to `reference/macos/`. Clock
readings and any content notes below are transcribed directly from the
final saved PNGs (re-read after saving, not from memory of the capture
session).

| state | file | clock | notes |
|---|---|---|---|
| 01 | `01-desktop.png` | 3:29 am | Bare desktop, Finder active. Also carries the install's default extra desktop icons (Register with Apple, Browse the Internet, Get QuickTime Pro, Mail) and the staged "what the door does" document icon, alongside the required Macintosh HD / Wastebasket / Poems — none of this was cleaned up, since removing default-install icons would itself be a cosmetic customisation the brief asked us not to make. |
| 02 | `02-folder.png` | 3:18 am | Poems window, icon view, Demos visible, active. |
| 03 | `03-nested.png` | 3:19 am | Demos active (striped title bar) cascaded over Poems inactive (grey/flat title bar) — the inactive-Platinum-chrome capture the brief called out as critical. |
| 04 | `04-document.png` | 3:25 am | SimpleText, title "what the door does", exact staging-spec text, caret on the trailing blank line, clean desktop behind. |
| 05 | `05-context-menu.png` | 3:27 am | Control-click contextual menu on bare desktop, pointer visible at the invocation point. |
| 06 | `06-dialog.png` | 3:28 am | Real "Wastebasket contains 1 item... remove it permanently?" alert. Note the pinstriped alert-title bar renders pink/red rather than the grey one might expect from memory of classic Mac OS — this is SheepShaver executing the genuine Mac OS 8.6 Toolbox drawing code at Millions-of-colours depth, not a rendering bug in the rig, so it was kept as-is rather than "corrected." |

No deviations from the staging spec's required content in any of the six
states; the only deliberate cosmetic change from stock is the disk rename
to "Macintosh HD" (required by the spec itself) and ejecting the install CD
(not asked for explicitly, done so the CD icon wouldn't clutter state 01).

Colour depth achieved: **Millions of colours**, 640&times;480 @ 75 Hz.

## Raw extras (`reference/raw/macos-emulator/`)

`about-this-computer.png`, `apple-menu-open.png`, `file-menu-open.png`,
`special-menu-open.png`, `monitors-control-panel.png` (shows the Millions/
640x480 setting directly), `desktop-pattern-tile.png` (140x140 icon-free
tile for pattern extraction), `pointer-at-100-100.png` (cursor at a known,
documented guest coordinate on bare desktop), `wastebasket-full.png` (the
"contains items" Trash icon glyph, for contrast with the empty one visible
in state 01). State 03 already supplies the required "inactive window"
capture, so no separate one was made.

`about-this-computer.png` is also worth a factual flag rather than a
guess: its version line reads literally **"Mac OS B1-8.6"** (verified by
pixel-zooming the saved crop, not transcribed from a thumbnail) — the "B1"
prefix does not match anything in the brief or in what was independently
confirmed elsewhere (volume name, Installer, both About-the-OS read-mes all
just say "Mac OS 8.6" / "8.6"). Reported as observed; no explanation
invented for it.

## Fetched tools (all open-source, per the brief's allowance)

| tool | version | source |
|---|---|---|
| hfsutils | 3.2.6 | Homebrew (`brew install hfsutils`) |
| machfs | 1.3 | PyPI (`pip install machfs`), pulled `macresources` 1.2 |
| colima | 0.10.3 (commit `00f6c297`) | Homebrew; upstream github.com/abiosoft/colima |
| lima | 2.2.0 | Homebrew, colima's dependency |
| kanjitalk755/macemu | commit `ba0bf07013d4d1c38beef8c8f697bef495a36c81` (2026-08-02) | `git clone` at Docker build time, github.com/kanjitalk755/macemu |
| qemu-system-ppc | 11.0.2 | already installed (`/opt/homebrew/bin`), used for the (failed) rung 1 only |

## Reproducing this rig

```sh
# one-time host prep
brew install hfsutils colima
verify/.venv/bin/pip install machfs
colima start --cpu 2 --memory 4 --disk 20
colima ssh -- sudo sysctl -w vm.mmap_min_addr=0   # after every colima restart

# extraction (from the operator-supplied ISO; see "ROM extraction" above)
# produces (gitignored): hfs_partition.raw, macos_rom.rom

cd verify/macos_rig
docker build -t macos-rig .
docker run -d --name sheepbox -v "$(pwd)":/work macos-rig
# entrypoint auto-starts SheepShaver if /work/sheepshaver_prefs exists
./screenshot.sh shot.png        # capture
./sendkeys.sh Return             # keyboard
./typetext.sh "literal text"     # literal text (one line at a time; see gotcha above)
docker exec sheepbox sh -c "export DISPLAY=:99; xdotool mousemove X Y click 1"
```

`macos_hd.img` (the installed 2 GB system disk) is gitignored, same as the
OS/2 rig's `w4hd.img` — not reproducible without redoing the install, which
is why this file documents every step.

