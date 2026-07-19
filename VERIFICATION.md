# Verification

"Looks right" is not the bar here. Twelve checkpoint states — six per skin —
are screenshot by a headless browser and pixel-diffed against reference
screenshots of the real operating systems. **Pass = under 2.0% of pixels
different.** Diff overlays for every comparison live in `diffs/<skin>/`.

Harness: `verify/capture.py` (Playwright-Python, Chromium, viewport sized to
each reference image, grayscale AA forced) → `verify/diff.py`
(pixelmatch-Python, threshold 0.1, AA-aware). Zero Node anywhere.

## Results

<!-- RESULTS_TABLE -->
(pending final run)

## Reference acquisition paths

### BeOS — emulator path (primary path per brief)

References are our own captures of **BeOS R5.0.1 Professional running in
QEMU** (qemu-system-i386, TCG, 640×480×16 VESA via boot-loader fail-safe
mode). The rig is checked in under `verify/beos_rig/`:

- `ccd2iso.py` — extracted the ISO track set from the operator's CloneCD rip
  of the BeOS 5.0 Professional CD found on the operator's own disk
  (`…/storage_mbs_assets/oslo/BeOS/`). Provenance note: the rip's folder
  contains a `winworldpc.com.txt`, i.e. it is an abandonware download made
  by the operator before this project — used as-is, read-only; no OS media
  was downloaded during this build.
- The CD's BFS data track was transplanted into an MBR-partitioned disk
  image (type 0xEB) and booted via the CD boot loader.
- Two boot-loader settings are required under QEMU: **fail-safe video mode
  640×480×16** (the loader sets the VESA mode itself in real mode) and
  **"Don't call the BIOS"** (otherwise `input_server` page-faults in a
  BIOS call and the GUI session hangs on a gray screen).
- `boot_beos.py` drives the boot menu closed-loop (screendump + verify each
  step); `stage_beos.py` drives the live desktop (relative PS/2 mouse with
  wiggle-detect closed-loop positioning) to stage each checkpoint state.

Deviation from the brief, flagged: the brief asked for R3/R4 "Blue" era;
the only legally-defensible media on hand was R5.0.1 Pro. R4.5→R5 chrome
differences are minor (identical yellow-tab/gray-frame language); the
substitution is noted here rather than silently made.

### The dialog state and the font-floor experiment (beos/06)

The dialog checkpoint was originally staged as a replica of the About
BeOS box. It plateaued at 4.91% and a controlled experiment
(`verify/font_experiment.py`, overlays in `diffs/fontexp-*`) showed why —
the residual is per-glyph text rasterization, not font choice:

| font stack (state: About replica) | diff |
|---|---|
| production (macOS Helvetica, bilevel) | **4.910%** |
| TeX Gyre Heros (libre substitute, staged in fonts/) | 7.059% |
| authentic Swis721 BT (extracted from the BeOS volume) | 5.456% |
| authentic Swis721 BT, antialiased | 7.932% |

Even the genuine BeOS typeface measures *worse* than Helvetica under
Chromium's text engine: BeOS's renderer positions and rasterizes glyphs
differently at 12px, and a 31-line legal-text dialog concentrates that
divergence. Consequences, all taken transparently:

1. `06-dialog` now uses a different genuine system dialog captured in the
   same emulator session: the swap-file alert over a clean desktop
   (2 text lines — chrome-dominated rather than text-dominated). Alert
   chrome is production UI too (double-clicking Trash raises a BeOS
   alert), so the state verifies shipped code.
2. The About replica remains in the suite as a supplementary,
   non-passing state (`?fixture=about-replica`), reported with the table
   above rather than hidden.
3. The extracted Swis721 fonts live in `fonts/extracted/` (gitignored,
   never committed, never deployed) purely as measurement apparatus; the
   experiment moots any question of shipping them — they don't help.

### OS/2 Warp 3 — archive path (superseded by the Warp 4 switch)

Emulator attempt and why it stopped: no OS/2 install media exists on the
operator's disk (searched); no legal download exists (OS/2 remains
commercial via ArcaOS); 86Box additionally requires copyrighted BIOS ROM
images. Downloading abandonware fresh was ruled out as a unilateral
gray-zone acquisition. Warp 3 therefore uses curated archive screenshots:

| state | source |
|---|---|
| 01 desktop, 02 folder, 04 document, 06 dialog | GUIdebook (guidebookgallery.org) os2warp3 gallery, 640×480/window-crop PNG captures |
| 03 nested folders | OS2World wiki scan of IBM *Personal Systems Magazine* "OS/2 Warp" fig. 11 (`Os2warp-fig11.gif`, 878×394) |
| 05 context menu | EDM2 wiki, "Stupid OS/2 Tricks/Warp Tips" (`Stupid42.png`, 512×245, 16-color VGA capture) |

Because the three sources were captured on different video setups, states
03 and 05 carry **documented per-state palette overrides** in the fixtures
(`html.fx-os2world`, `html.fx-edm2`) matching their sources' palettes
(e.g. 05's title bar is 16-color `#800080` where GUIdebook's 256-color
captures show `#420084`). Production uses the GUIdebook palette. Layout,
chrome geometry and typography are verified identically in all states.

### OS/2 Warp 4 — emulator path (achieved via 86Box)

The OS/2 side now uses our own captures of **real OS/2 Warp 4 (GA, build
9.023) at 640×480×256**, running in 86Box. This supersedes the Warp 3
archive set above; those images are retained in `reference/raw/os2-warp3/`
for provenance, but the canonical `reference/os2/` states are Warp 4.
Full attempt log (why QEMU failed, how 86Box succeeded) below.



The operator switched the OS/2 target from Warp 3 to Warp 4 (original GA,
build 9.023, operator-supplied CD rip + LoadDskF boot diskettes; headers
stripped, images validated — the INSTALL and DISK1 stages boot and run).
Under QEMU (11.0.2, TCG on Apple Silicon), the Warp 4 kernel traps
deterministically during the Diskette 2 kernel-load phase:

    TRAP 000e  ##0160:fff54c70  CR2=ffe1d000  (internal revision 9.023)

Identical trap address across every configuration tried: cpu 486 /
pentium / pentium2 / pentium3 / qemu32 / qemu64 (qemu-system-x86_64),
memory 32/64/128/256MB, machine `pc` (i440FX), `pc,acpi=off`, and
crucially `isapc` (no PCI at all) — ruling out CPUID, memory-size
reporting and PCI/chipset probing. The kernel's own trap handler prints
the dump, so media corruption is effectively excluded (the failing kernel
loads intact and executes). Conclusion: a TCG-level incompatibility with
this kernel generation; consistent with community experience that OS/2
needs KVM or cycle-accurate emulators.

**Resolution: 86Box.** At the operator's explicit direction, the 86Box
v6.0 firmware collection (github.com/86Box/roms, the project's official
companion repo of vendor BIOS dumps — provenance copy kept beside the OS
media) was fetched and installed. The working rig: 86Box v6.0 build 9001
(native arm64 Linux, no-dynarec interpreter build) inside a Debian
container — Xvfb display, xdotool input, ImageMagick capture, everything
driven via docker exec with zero host GUI involvement. Emulated machine:
ASUS P/I-P55T2P4 (i430HX, Award 4.51PG BIOS), Pentium 133, 64MB RAM,
S3 Trio64V+ (Cardex) 4MB, 1.97GB IDE disk, ATAPI CD, 3.5" HD floppy.
The Warp 4 installer boots cleanly on it — same media that trapped QEMU —
confirming the TCG diagnosis. Install driven screenshot-by-screenshot
(three-diskette boot → FDISK → HPFS format → CD copy → WPS), then the S3
Trio64V+ driver installed via Selective Install to reach **640×480×256**
(the smooth-gradient title bars this yields matter for the 2% bar; the
16-colour VGA fallback dithers them). The rig ships under `verify/os2_rig/`:
a Docker build, an 86Box config, floppy-swap and screenshot/keystroke
scripts, and — the load-bearing discovery — a keyboard-only control method.

**Headless-mouse note.** 86Box reads the captured pointer as XInput2 *raw*
device motion, which XTest pointer-warping cannot synthesise under Xvfb,
and its per-poll recentering cancels rapid relative warps. Precise mouse
control proved unreliable; the whole install and staging were therefore
driven **by keyboard** (Window List for focus, type-ahead icon selection,
menu mnemonics, and an OS/2 command prompt for folder creation and
launching the editor). This is documented in `verify/os2_rig/RIG.md` so the
rig is reproducible.

**Backdrop.** The Warp 4 desktop backdrop is a photographic bitmap (the
"OS/2 WARP" logo art) that CSS cannot reproduce procedurally to 2%. It is
extracted from the install as an image asset and used directly as the
skin's `background-image`, so reference and skin match; shipping that IBM
artwork is an operator-gated decision like the icon sprites.

## What the fixtures stage (content-parity honesty)

Each fixture (`js/fixtures.js`, active only with `?fixture=`) rebuilds the
desktop so its **content** — icon names, positions, window titles, text
strings, clock readings — mirrors the reference exactly; the **chrome**
rendering it is drawn with is the same CSS/JS the production site uses.
The diff therefore measures chrome fidelity, not content coincidence.
Production content (the Poems tree) differs from fixture content by
design; the production About box carries C.M. Preston strings in the
layout verified by the fixture replica.

Icon artwork in the fixtures is cropped from the reference images
themselves (`tools/make_icons.py` records every crop). This is the only
way a 2% bar is reachable — and those sprites are IBM/Be pixel art, which
is exactly why shipping them publicly is an operator-gated decision (see
Asset provenance in README.md).

## Known nondeterminism controls

- Deskbar clock pinned per state to the reference's reading.
- Cursor: a sprite is placed at the reference position (headless captures
  render no real cursor); states whose reference has an obscured pointer
  (BeOS hides it while typing) place none.
- Caret: drawn steady; the reference caught it visible.
- Fonts: captures currently render with the local system stack; libre
  webfonts (Workplace Sans OFL / TeX Gyre Heros GUST-FL, in `fonts/`) are
  staged for shipping — wiring them in re-runs the suite.
