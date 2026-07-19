# Warp 4 install drive plan (main workflow owns this; rig agent owns RIG.md)

Principle: never key blind. Screenshot → read → respond, every screen.
OS/2's installer is fully keyboard-driven; the WPS afterwards is too
(arrows/Enter, Shift+F10 context menus, Alt+F for menus).

## Phase A — text-mode (floppy boot)
1. INSTALL boots → "Insert Diskette 1" → swap disk1.img → Enter.
2. Diskette 1 loads → "Insert Diskette 2" → swap disk2.img → Enter.
3. Welcome (blue) → Enter. Choose **Advanced installation** if offered a
   choice we need (blank disk requires FDISK anyway).
4. FDISK: create primary partition from all free space, set installable
   (menu-driven; F3 saves). Expect a mandatory reboot → repeat the
   three-diskette dance (swap back to install.img before reset).
5. Format: **HPFS**. Then phase-1 file copy (floppies + CD present).
6. "Remove diskette and press Enter" → EJECT floppy (or swap a blank),
   Enter → system boots from HD into the GUI installer.

## Phase B — GUI phase (keyboard: Tab/arrows/Enter, Alt+letter)
7. System Configuration screens: accept defaults (US keyboard, PS/2
   mouse, locale). Display: leave VGA for now (S3 driver post-install).
8. Component selection: defaults EXCEPT deselect networking/TCP-IP if it
   asks about adapters (no NIC in the machine — choose "No adapter" /
   skip). No printer.
9. Long CD copy → automatic reboot(s). Keep floppy ejected.
10. First WPS boot: close the tutorial/WarpCenter first-run windows as
    they appear.

## Phase C — display + staging prep
11. Selective Install → Display: S3 Trio64V+ → **640×480×256** (matches
    the BeOS side's 640×480; 256 colors renders the Warp 4 desktop art
    correctly). Reboot.
12. Verify desktop = WarpCenter top bar + default Warp 4 backdrop.

## Phase D — stage the six site states (mirrors the BeOS session)
- Desktop: create folder "Poems" (Shift+F10 on desktop → Create another →
  Folder; or Templates tear-off). Keep WarpCenter as-is.
- 01-desktop: clean desktop + Poems folder, pointer parked.
- 02-folder: open Poems (Icon view).
- 03-nested: create+open Demos inside Poems, overlapping windows.
- 04-document: OS/2 System Editor (E.EXE) with the poem fragment typed.
- 05-context-menu: Shift+F10 desktop pop-up menu visible.
- 06-dialog: a real system dialog — candidates: E.EXE product-information
  box (Help → Product information) or the shutdown confirmation. Prefer
  Product information (matches the site's About box pattern).
- Capture everything at 640×480×256; ALSO harvest sprite crops (folder
  icons, WarpCenter pieces, pointer, min/max buttons, etc.).

## Known 86Box handling
- Swaps via the rig's swap_floppy.sh; verify every swap with a screenshot
  before pressing Enter.
- The NDR build ≈ real Pentium speed: file-copy phases take tens of
  minutes. Poll with screenshots every 60–90s; do not spam keys while
  the guest is busy (keystroke buffer survives and fires later).
- If the installer hangs >10 min with no disk/screen change, screenshot,
  check docker logs, and only then consider a reset.
