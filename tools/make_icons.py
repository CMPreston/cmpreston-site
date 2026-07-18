#!/usr/bin/env python3
"""Cut icon/chrome sprites for both skins out of the reference screenshots.

Provenance: every sprite is a crop of a reference image in reference/raw/
(GUIdebook archive captures and our own emulator captures). These are
recreations-by-extraction of IBM's and Be's original pixel art; whether they
may ship on the public site is an operator decision gated in the project
brief (asset licensing gate). Until that decision, they exist for local
rendering and pixel-diff verification.

Needs Pillow: run with verify/.venv/bin/python3.
"""
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / 'reference' / 'raw'
OUT = ROOT / 'icons'

# (source-relative, crop box (l,t,r,b), output-relative, make transparent bg?)
CROPS = [
    # ---------------- OS/2 (from GUIdebook os2warp3 captures) ----------------
    ('os2/desktop-empty.png', (52, 140, 84, 168), 'os2/os2-system.png', True),
    ('os2/desktop-empty.png', (51, 198, 82, 230), 'os2/information.png', True),
    ('os2/desktop-empty.png', (53, 414, 84, 441), 'os2/templates.png', True),
    ('os2/desktop-empty.png', (196, 20, 227, 47), 'os2/dos-programs.png', True),
    ('os2/desktop-empty.png', (267, 20, 299, 48), 'os2/multimedia.png', True),
    ('os2/desktop-empty.png', (44, 17, 77, 47), 'os2/printer.png', True),
    ('os2/desktop-empty.png', (296, 270, 313, 292), 'os2/cursor.png', True),
    # folder icon: 'Games' folder in the OS/2 System window of desktop-full
    ('os2/desktop-full.png', (556, 300, 588, 330), 'os2/folder.png', False),
    # sysmenu mini-icons: title bar left of System Setup window (folder-ish)
    ('os2/settings-menu.png', (4, 3, 24, 19), 'os2/sysmenu-folder.png', False),
    ('os2/app-texteditor.png', (4, 3, 24, 19), 'os2/sysmenu-doc.png', False),
    # about dialog icon (System Editor pencil/page)
    ('os2/dialog-about.png', (38, 58, 80, 102), 'os2/about.png', False),
    # LaunchPad icon buttons (from desktop-empty LaunchPad, 640x480)
    ('os2/desktop-empty.png', (293, 411, 325, 446), 'os2/lp-printer.png', False),
    ('os2/desktop-empty.png', (338, 411, 370, 446), 'os2/lp-floppy.png', False),
    ('os2/desktop-empty.png', (383, 411, 415, 446), 'os2/lp-shell.png', False),
    ('os2/desktop-empty.png', (428, 411, 460, 446), 'os2/lp-info.png', False),
    ('os2/desktop-empty.png', (473, 411, 505, 446), 'os2/lp-shredder.png', False),
    # ---------------- BeOS (from GUIdebook beos5 captures; to be replaced ----
    # ---------------- by our own emulator captures where they differ) --------
    ('beos/desktop-empty.png', (139, 20, 172, 52), 'beos/folder.png', True),
    # trash: recropped from our own R5 capture (replaces GUIdebook crop);
    # art spans exactly 32 rows incl. the floor shadow (ref rows 20..51)
    ('beos-emulator/beos-01-desktop.png', (20, 20, 52, 52), 'beos/trash.png', True),
    ('beos/desktop-empty.png', (521, 1, 639, 19), 'beos/be-logo.png', False),
    ('beos/desktop-empty.png', (524, 47, 540, 63), 'beos/tracker.png', False),
    ('beos/desktop-empty.png', (38, 86, 73, 117), 'beos/webglobe.png', True),
    # ---------------- BeOS window chrome (our emulator captures) -------------
    # Coordinates measured against reference/beos/02..04 (raw twins verified
    # byte-identical). Scrollbar caps carry both arrow buttons of one end.
    ('beos-emulator/beos-04-document.png', (495, 46, 508, 76), 'beos/sb-v-top.png', False),
    ('beos-emulator/beos-04-document.png', (495, 383, 508, 413), 'beos/sb-v-bottom.png', False),
    ('beos-emulator/beos-04-document.png', (7, 414, 37, 427), 'beos/sb-h-left.png', False),
    ('beos-emulator/beos-04-document.png', (464, 414, 494, 427), 'beos/sb-h-right.png', False),
    ('beos-emulator/beos-02-folder.png', (402, 267, 421, 286), 'beos/corner-tracker.png', False),
    ('beos-emulator/beos-04-document.png', (494, 413, 513, 432), 'beos/corner-doc.png', False),
    ('beos-emulator/beos-02-folder.png', (84, 30, 98, 44), 'beos/tab-close.png', False),
    ('beos-emulator/beos-02-folder.png', (173, 30, 190, 44), 'beos/tab-zoom.png', False),
    # folder icon over white (Tracker window interior), for in-window use
    ('beos-emulator/beos-02-folder.png', (345, 175, 377, 207), 'beos/folder-win.png', False),
    # StyledEdit mini app icon from the 04 deskbar entry
    ('beos-emulator/beos-04-document.png', (529, 71, 545, 87), 'beos/styled-edit.png', False),
    # Deskbar tray mailbox (over the tray face, no transparency needed)
    ('beos-emulator/beos-01-desktop.png', (525, 26, 542, 42), 'beos/db-mail.png', False),
]

# Inactive-tab widgets: cropped from n1.png whose back window sits at the same
# coordinates, but its bottom row is occluded by the front window there; that
# row is resynthesized from the active sprites through the measured
# active->inactive palette map (verified pairs from 02 vs 03 references).
INACTIVE_MAP = {
    (255, 203, 0): (239, 235, 239), (214, 158, 0): (198, 190, 198),
    (173, 121, 0): (156, 154, 156), (181, 130, 0): (165, 162, 165),
    (255, 255, 57): (255, 255, 255), (255, 239, 33): (255, 255, 255),
    (239, 182, 0): (222, 215, 222), (255, 255, 82): (255, 255, 255),
}

def cut_inactive_tab_widgets():
    n1 = Image.open(RAW / 'beos-emulator' / 'n1.png').convert('RGB')
    act = Image.open(RAW / 'beos-emulator' / 'beos-02-folder.png').convert('RGB')
    for box, dst in [((84, 30, 98, 44), 'beos/tab-close-i.png'),
                     ((173, 30, 190, 44), 'beos/tab-zoom-i.png')]:
        crop = n1.crop(box)
        ref = act.crop(box)
        pc, pr = crop.load(), ref.load()
        y = crop.height - 1
        for x in range(crop.width):
            pc[x, y] = INACTIVE_MAP.get(pr[x, y], pr[x, y])
        (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
        crop.save(OUT / dst)
        print(f'{dst:28s} {crop.width}x{crop.height}  <- n1.png {box} (+synth row)')

def cut(src, box, dst, transparent):
    im = Image.open(RAW / src).convert('RGB')
    crop = im.crop(box)
    if transparent:
        # knock out the desktop background color (probe the crop's corners)
        rgba = crop.convert('RGBA')
        corners = [rgba.getpixel(p) for p in
                   [(0, 0), (crop.width - 1, 0), (0, crop.height - 1)]]
        bg = max(set((c[0], c[1], c[2]) for c in corners),
                 key=lambda c: sum(1 for k in corners if (k[0], k[1], k[2]) == c))
        px = rgba.load()
        for y in range(rgba.height):
            for x in range(rgba.width):
                p = px[x, y]
                if all(abs(p[i] - bg[i]) <= 12 for i in range(3)):
                    px[x, y] = (0, 0, 0, 0)
        crop = rgba
    out = OUT / dst
    out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out)
    return crop.size

def main(only=None):
    for src, box, dst, transparent in CROPS:
        if only and not any(f in dst for f in only):
            continue
        size = cut(src, box, dst, transparent)
        print(f'{dst:28s} {size[0]}x{size[1]}  <- {src} {box}')
    if not only or any('tab-' in f or '-i' in f for f in only):
        cut_inactive_tab_widgets()

if __name__ == '__main__':
    import sys
    main(sys.argv[1:] or None)
