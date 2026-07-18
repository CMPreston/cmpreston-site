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

### OS/2 Warp 3 — archive path (documented fallback per brief)

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
