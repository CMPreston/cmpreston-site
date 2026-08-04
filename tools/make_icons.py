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
REF = ROOT / 'reference'          # 640x480 Warp-4 crops live here (reference/os2/*)
OUT = ROOT / 'icons'

# (source-relative, crop box (l,t,r,b), output-relative, make transparent bg?)
# BeOS crops still read from reference/raw/ (RAW); the OS/2 Warp-4 sprites are
# cut separately in cut_os2() below, straight from reference/os2/*.png.
CROPS = [
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
    # BeOS alert-state sprites (alert-swapfile.png = swap-file alert capture)
    ('beos-emulator/alert-swapfile.png', (163, 92, 208, 140), 'beos/alert-icon.png', False),
    ('beos-emulator/alert-swapfile.png', (524, 71, 540, 87), 'beos/db-alert.png', False),
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

# ---------------------------------------------------------------- OS/2 Warp 4
# All Warp-4 sprites are cut from the freshly-captured 640x480 references in
# reference/os2/ (and one extra source, reference/raw/os2-warp4/). The desktop
# backdrop is a heavily ordered-dithered bitmap and the active title bars are
# per-pixel dithered gradients; neither is reproducible by CSS solids to the 2%
# bar, so per the project brief they ship as extracted image assets:
#   backdrop.png     -- icon-free desktop field (logo kept), body background
#   wc-bar.png       -- the WarpCenter top bar, fixed content x0..556
#   wc-clock-*.png   -- per-state clock readout (right of the bar)
#   title-*.png      -- each fixture window's exact title-bar rectangle (the
#                       blue dither + baked white title text), placed 1:1
# Small solid/edged widgets (folder sysmenu, min/max buttons, warning icon,
# icons) are ordinary crops; icons over the blue field get a blue knockout.

def _knockout_blue(rgba):
    """Make the pure-blue dithered desktop field transparent (backdrop is
    (0,0,~161) with dither down to ~120 and up to ~254; all have r,g < ~40)."""
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            p = px[x, y]
            if p[0] < 40 and p[1] < 40 and p[2] > 90:
                px[x, y] = (0, 0, 0, 0)

def _declutter(rgba, minsize=25):
    """Drop isolated speckle: keep only connected opaque components >= minsize."""
    from collections import deque
    px = rgba.load(); W, H = rgba.size
    seen = [[False] * H for _ in range(W)]
    keep = [[False] * H for _ in range(W)]
    for sx in range(W):
        for sy in range(H):
            if seen[sx][sy] or px[sx, sy][3] == 0:
                continue
            q = deque([(sx, sy)]); comp = []; seen[sx][sy] = True
            while q:
                x, y = q.popleft(); comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                               (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[nx][ny] and px[nx, ny][3] > 0:
                        seen[nx][ny] = True; q.append((nx, ny))
            if len(comp) >= minsize:
                for x, y in comp:
                    keep[x][y] = True
    for x in range(W):
        for y in range(H):
            if not keep[x][y]:
                px[x, y] = (0, 0, 0, 0)

def crop_clean(src_rel, box, dst):
    """A production desktop icon: knock out the blue field (B notably > R), drop
    speckle, tight-crop, and pad to a centred square so CSS 32x32 doesn't
    distort it. Used for the manifest-driven folder/shredder desktop icons."""
    im = Image.open(REF / src_rel).convert('RGB').crop(box).convert('RGBA')
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if r < 62 and g < 66 and b > r + 20:
                px[x, y] = (0, 0, 0, 0)
    _declutter(im)
    im = im.crop(im.getbbox())
    s = max(im.size)
    sq = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    sq.alpha_composite(im, ((s - im.width) // 2, (s - im.height) // 2))
    (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
    sq.save(OUT / dst)
    print(f'{dst:28s} {sq.size[0]}x{sq.size[1]}  <- {src_rel} {box} (clean)')

def cut_os2(only=None):
    def want(dst):
        return not only or any(f in dst for f in only)

    def crop(src_rel, box, dst, mode=None):
        # src under reference/ (e.g. 'os2/01-desktop.png' or
        # 'raw/os2-warp4/extra-systemfolder.png')
        im = Image.open(REF / src_rel).convert('RGB')
        c = im.crop(box)
        if mode == 'blue':
            c = c.convert('RGBA'); _knockout_blue(c)
        out = OUT / dst
        out.parent.mkdir(parents=True, exist_ok=True)
        c.save(out)
        print(f'{dst:28s} {c.size[0]}x{c.size[1]}  <- {src_rel} {box}')

    D = 'os2/01-desktop.png'
    # ---- desktop icon rectangles (whole icon+label units, placed 1:1) ----
    # The backdrop is now icon-FREE (dithered field + WARP logo only), so every
    # resting desktop icon is cut as its own opaque rectangle and placed back by
    # the fixtures at its reference position (js/fixtures.js OS2_ICON_POS). Opaque
    # rectangles carry each icon's exact dither border, so they match the
    # reference 1:1 in every state; a window that covers an icon simply renders
    # over it. Each box fully contains the icon art + label (nonblue content) with
    # ~2px pad and stays left of the WARP logo (max x 117). These ARE the same
    # rectangles the backdrop inpaint erases below, so the fixture sprite exactly
    # covers the inpainted patch (fixtures stay pixel-identical to the old baked
    # backdrop; production no longer double-draws icons).
    OS2_RECTS = {
        'os2-system':        (33, 61, 100, 120),   # 01: selected (focus dashes)
        'assistance-center': (25, 153, 118, 215),
        'connections':       (37, 203, 118, 282),
        'programs':          (43, 306, 91, 359),
        'poems':             (119, 35, 158, 88),
        'shredder':          (555, 422, 601, 473),
    }
    for nm, box in OS2_RECTS.items():
        if want('os2/icon-' + nm):
            crop(D, box, 'os2/icon-%s.png' % nm)
    # OS/2 System is selected only on the resting desktop (01); 02-06 show it
    # unselected. Cut the unselected variant from 02 at the same rectangle.
    if want('os2/icon-os2-system-unsel'):
        crop('os2/02-folder.png', OS2_RECTS['os2-system'], 'os2/icon-os2-system-unsel.png')
    # ---- backdrop: the desktop field (real pixels), WARP logo, NO icons ----
    # The OS renders the backdrop bitmap deterministically (byte-identical across
    # all six captures). We keep the real dithered field + WARP logo but INPAINT
    # OUT the six resting desktop icons (they belong to the reference/fixtures,
    # not the poetry site's production desktop, which draws its own Poems/BeOS/
    # Shredder icons over this field). The field is a pure blue-channel dither
    # (R=G=0, a smooth diagonal gradient of two blues + occasional dark pixels),
    # so each masked pixel is refilled from a RANDOM clean field pixel in a small
    # local neighbourhood -- this matches the local gradient AND reproduces the
    # stochastic dither texture seamlessly. The original icon-baked field is kept
    # as backdrop-withicons.png. (Deterministic: fixed RNG seed.)
    if want('os2/backdrop'):
        import random as _random
        # Reconstruct the old icon-baked backdrop first (kept as -withicons.png):
        # raw 01 with the OS/2 System icon composited UNSELECTED (from 02) over
        # its selected copy and the stray cursor arrow cleaned with a donor tile.
        baked = Image.open(REF / D).convert('RGB')       # raw 01 desktop
        bpx = baked.load()
        unsel = Image.open(REF / 'os2/02-folder.png').convert('RGB')
        baked.paste(unsel.crop((30, 60, 100, 122)), (30, 60))
        CDX, CDY, CDS = 270, 60, 120
        for y in range(24, 44):
            for x in range(486, 512):
                bpx[x, y] = bpx[CDX + (x % CDS), CDY + (y % CDS)]
        (OUT / 'os2' / 'backdrop.png').parent.mkdir(parents=True, exist_ok=True)
        baked.save(OUT / 'os2' / 'backdrop-withicons.png')  # the old baked backdrop
        # The clean backdrop is inpainted from RAW 01 (not the baked copy): raw 01
        # keeps every icon's content neatly inside OS2_RECTS, so no stray icon
        # pixels survive at the mask boundary. R=G=0 for the whole field.
        im = Image.open(REF / D).convert('RGB')
        px = im.load()
        W, H = im.size
        mask = [[False] * W for _ in range(H)]
        for (x0, y0, x1, y1) in OS2_RECTS.values():
            for y in range(y0, y1):
                for x in range(x0, x1):
                    mask[y][x] = True
        def _isfield(x, y):
            r, g, b = px[x, y]
            return r < 90 and g < 90 and b > 55
        def _clean(x, y):
            return y >= 23 and not mask[y][x] and _isfield(x, y)
        def _sample(x, y):
            for rad in (10, 16, 24, 36, 52, 80, 120, 220):
                vals = []
                for yy in range(max(23, y - rad), min(H, y + rad + 1)):
                    for xx in range(max(0, x - rad), min(W, x + rad + 1)):
                        if _clean(xx, yy):
                            vals.append(px[xx, yy][2])
                if len(vals) >= 40:
                    return vals
            return vals
        rng = _random.Random(1996)
        todo = [(x, y) for y in range(H) for x in range(W) if mask[y][x]]
        fills = [(x, y, (rng.choice(v) if (v := _sample(x, y)) else 128)) for x, y in todo]
        for x, y, b in fills:
            px[x, y] = (0, 0, b)
        im.save(OUT / 'os2' / 'backdrop.png')
        print(f'{"os2/backdrop.png":28s} {im.size[0]}x{im.size[1]}  <- {D} '
              f'(field + WARP logo; {len(fills)} icon px inpainted)')
    # ---- desktop icons (32x32-ish art, blue field knocked out) ----
    # OS/2 System: use extra-systemfolder (unselected; 01 has the focus dashes)
    if want('os2/os2-system'):
        crop('raw/os2-warp4/extra-systemfolder.png', (48, 66, 90, 100),
             'os2/os2-system.png', 'blue')
    if want('os2/assistance-center'):
        crop(D, (48, 156, 90, 192), 'os2/assistance-center.png', 'blue')
    if want('os2/connections'):
        crop(D, (48, 232, 88, 262), 'os2/connections.png', 'blue')
    if want('os2/programs'):
        crop(D, (48, 306, 88, 340), 'os2/programs.png', 'blue')
    if want('os2/poems'):
        crop(D, (122, 33, 158, 67), 'os2/poems.png', 'blue')
    if want('os2/shredder'):
        crop(D, (552, 430, 604, 467), 'os2/shredder.png', 'blue')
    # in-folder Demos icon (over white client), used 1:1 by the fixtures
    if want('os2/folder-win'):
        crop('os2/02-folder.png', (103, 90, 141, 125), 'os2/folder-win.png')
    # production desktop folder + shredder: clean transparent, decluttered, square
    if want('os2/folder.png'):
        crop_clean('os2/01-desktop.png', (123, 35, 159, 67), 'os2/folder.png')
    if want('os2/trash.png'):
        crop_clean('os2/01-desktop.png', (553, 420, 601, 457), 'os2/trash.png')
    # whole Demos icon+label units, placed 1:1 in the folder client (02 shows it
    # unselected, 05 selected with a blue label box)
    if want('os2/demos'):
        crop('os2/02-folder.png', (100, 79, 140, 132), 'os2/demos.png')
    if want('os2/demos-sel'):
        crop('os2/05-context-menu.png', (102, 81, 138, 134), 'os2/demos-sel.png')
    # 03: the Demos icon in the inactive Poems window behind — only its left
    # strip (x102..122) shows; the rest is covered by the front Demos window.
    if want('os2/demos-inact'):
        crop('os2/03-nested.png', (102, 81, 123, 115), 'os2/demos-inact.png')
    # ---- window chrome ----
    # title-bar sysmenu (yellow folder) and the min/max button cluster
    if want('os2/sysmenu-folder'):
        crop('os2/02-folder.png', (102, 40, 116, 56), 'os2/sysmenu-folder.png')
    if want('os2/sysmenu-doc'):
        # editor sysmenu is occluded by WarpCenter in 04; the folder sysmenu is
        # the same WPS system-menu glyph, reused
        crop('os2/02-folder.png', (102, 40, 116, 56), 'os2/sysmenu-doc.png')
    if want('os2/titlebtns'):
        crop('os2/02-folder.png', (544, 40, 602, 54), 'os2/titlebtns.png')
    # ---- dialog warning icon (teal triangle) ----
    if want('os2/warning'):
        crop('os2/06-dialog.png', (140, 106, 164, 130), 'os2/warning.png')
    # ---- desktop pointer + editor text I-beam ----
    if want('os2/cursor'):
        crop('os2/02-folder.png', (492, 27, 506, 44), 'os2/cursor.png', 'blue')
    if want('os2/ibeam'):
        crop('os2/04-document.png', (369, 160, 376, 175), 'os2/ibeam.png')
    # the editor's poem text block, extracted whole (bitmap WarpSans over white)
    # and overlaid 1:1 in 04/06 so every glyph matches (04 and 06 share it).
    if want('os2/poem-text'):
        crop('os2/04-document.png', (50, 56, 294, 130), 'os2/poem-text.png')
    # the editor scrollbars (arrows + full-length thumb), extracted whole and
    # placed 1:1 — a CSS approximation of the arrow glyphs/thumb bevel drifts.
    # vsb = right column incl. the bottom-right corner; hsb = bottom row.
    if want('os2/editor-vsb'):
        crop('os2/04-document.png', (523, 49, 541, 327), 'os2/editor-vsb.png')
    if want('os2/editor-hsb'):
        crop('os2/04-document.png', (44, 310, 523, 327), 'os2/editor-hsb.png')

    # ---- menu-bar label strips (extracted so the bitmap WarpSans text matches
    # 1:1; the Workplace Sans substitute is close but not per-glyph exact) ----
    # 02/03 folder menu: Folder Edit View Selected Help.
    if want('os2/menubar-folder'):
        crop('os2/02-folder.png', (104, 58, 324, 73), 'os2/menubar-folder.png')
    # 05 folder menu with "Selected" pulled down (highlighted blue box).
    if want('os2/menubar-folder-sel'):
        crop('os2/05-context-menu.png', (104, 58, 339, 74), 'os2/menubar-folder-sel.png')
    # 04/06 editor menu: File Edit Options Help.
    if want('os2/menubar-editor'):
        crop('os2/04-document.png', (56, 34, 210, 49), 'os2/menubar-editor.png')
    # 05 "Selected" pulldown menu, extracted whole (raised grey box, dithered-
    # blue "Open as" highlight, all item text + arrows). Placed 1:1 — a CSS menu
    # can't reproduce the dithered highlight or the WarpSans item metrics to 2%.
    if want('os2/menu-selected'):
        crop('os2/05-context-menu.png', (228, 73, 339, 199), 'os2/menu-selected.png')
    # 03 has two folder menu bars (inactive Poems + active Demos). Extract each
    # full band incl. the top strip, text, and the sunken client-top bevel, so
    # the 1px bevel/menu-edge artifacts (doubled by the two windows) match 1:1.
    if want('os2/menuband-poems03'):
        crop('os2/03-nested.png', (93, 55, 602, 75), 'os2/menuband-poems03.png')
    if want('os2/menuband-demos03'):
        crop('os2/03-nested.png', (124, 127, 626, 147), 'os2/menuband-demos03.png')

    # ---- WarpCenter bar: fixed content strip (x0..556), clock excluded ----
    if want('os2/wc-bar'):
        crop(D, (0, 0, 556, 22), 'os2/wc-bar.png')
    # per-state clock readouts (right end of the bar)
    CLOCKS = {'01-desktop': 'wc-clock-01', '02-folder': 'wc-clock-02',
              '03-nested': 'wc-clock-03', '04-document': 'wc-clock-04',
              '05-context-menu': 'wc-clock-05', '06-dialog': 'wc-clock-06'}
    for st, name in CLOCKS.items():
        if want('os2/' + name):
            crop('os2/%s.png' % st, (556, 0, 640, 22), 'os2/%s.png' % name)

    # ---- window title bars: exact blue-dither rectangle per fixture window ----
    # Each is placed 1:1 in its fixture (fixed-width windows). The band carries
    # the ordered dither + baked white title text (both un-CSS-able to 2%).
    # 02-folder: Poems window at x92,y33, title bar rows 33..55.
    if want('os2/title-poems'):
        crop('os2/02-folder.png', (92, 33, 603, 56), 'os2/title-poems.png')
    # 05-context-menu: same Poems window, active (identical geometry).
    if want('os2/title-poems05'):
        crop('os2/05-context-menu.png', (92, 33, 603, 56), 'os2/title-poems05.png')
    # 03-nested: Poems (inactive, grey) behind + Demos (active) in front.
    if want('os2/title-poems-inact'):
        crop('os2/03-nested.png', (92, 33, 603, 56), 'os2/title-poems-inact.png')
    if want('os2/title-demos'):
        crop('os2/03-nested.png', (123, 105, 627, 128), 'os2/title-demos.png')
    # 04-document / 06-dialog: editor window (x44..540). The editor is focused
    # and sits IN FRONT of the WarpCenter, so its full 16px title bar (y15..31)
    # is visible (it covers the WarpCenter's lower rows y15..21). We extract the
    # whole band and render the editor above the WarpCenter.
    if want('os2/title-editor'):
        crop('os2/04-document.png', (44, 15, 541, 32), 'os2/title-editor.png')
    # in 06 the editor is inactive (the dialog holds focus): a solid-grey title
    # bar. Extracted from 06 so its greys/sysmenu/buttons match 1:1.
    if want('os2/title-editor-inact'):
        crop('os2/06-dialog.png', (44, 15, 541, 32), 'os2/title-editor-inact.png')
    # 06 dialog inner title bar ("Warning: File Changed", blue). Extracted as
    # the full band incl. the dialog's top edge/bevel (y58..75) so it covers the
    # dialog frame top 1:1; placed flush to the dialog's top-left corner.
    if want('os2/title-warning'):
        crop('os2/06-dialog.png', (116, 58, 470, 75), 'os2/title-warning.png')
    # the entire "Warning: File Changed" dialog (frame, blue title, warning icon,
    # both message lines, all five buttons) extracted whole and placed 1:1 — the
    # WarpSans message/button text and the button bevels can't be reproduced to
    # 2% by CSS + the Workplace Sans substitute.
    if want('os2/dialog-warning'):
        crop('os2/06-dialog.png', (116, 57, 471, 195), 'os2/dialog-warning.png')

def main(only=None):
    for src, box, dst, transparent in CROPS:
        if only and not any(f in dst for f in only):
            continue
        size = cut(src, box, dst, transparent)
        print(f'{dst:28s} {size[0]}x{size[1]}  <- {src} {box}')
    if not only or any('tab-' in f or '-i' in f for f in only):
        cut_inactive_tab_widgets()
    if not only or any('os2/' in f or f.startswith('os2') for f in only):
        cut_os2(only)
    if not only or any('macos/' in f or f.startswith('macos') for f in only):
        cut_macos(only)

# ------------------------------------------------------------- Mac OS 8.6
# Wave 2 (measurement + fixtures + assets): every crop below is cut from our
# own SheepShaver captures of real Mac OS 8.6 (British localization) at
# reference/macos/*.png, 640x480, Millions of colors (see verify/macos_rig/
# RIG.md for the capture rig). Boxes were measured with PIL pixel sampling /
# connected-component analysis, never eyeballed (per the project's house
# method). Wave 3 owns chrome-fidelity CSS tuning against the diff% these
# fixtures start at; this pass only has to get CONTENT right.
#
# Desktop background knockout note: the wallpaper is a soft-embossed pattern
# (solid field RGB(99,99,156) plus a repeating "sad Mac" watermark), not a
# hard 2-color dither like OS/2's field. Its watermark blends toward the SAME
# hue family the Poems folder icon's own fill uses (e.g. (199,199,252)), so a
# flat color-range knockout would eat holes in the folder icon itself. Instead
# MACOS_TILE_BOX below records one verified-clean 140x140 period of the
# pattern (self-tiling mean abs diff ~1.4/channel, i.e. exact); knockout
# predicts the true background color at each pixel's OWN absolute screen
# position by tiling that period, and only clears pixels matching the
# prediction. Icons whose art never overlaps the purple family (doc, trash,
# macintosh-hd, cursor) use a cheaper flat purple-range test instead.
MACOS_TILE_BOX = (0, 100, 140, 240)   # region of 01-desktop.png = one clean tile
# Anchor fact for wave 3: this box's top-left corner sits at screen (0,100),
# i.e. tile(0,0) == screen(0, 100 mod 140). Equivalent minimal CSS offset:
# background-position: 0 -40px (or 0 100px) with background-repeat: repeat.

def _macos_tile_image():
    return Image.open(REF / 'macos' / '01-desktop.png').convert('RGB').crop(MACOS_TILE_BOX)

def _macos_bg_at(tile, x, y):
    tw, th = tile.size
    return tile.getpixel(((x - MACOS_TILE_BOX[0]) % tw, (y - MACOS_TILE_BOX[1]) % th))

def knockout_macos_pattern(rgba, x0, y0, tol=30):
    """Clear pixels matching the predicted desktop-pattern color at their true
    screen position (x0+dx, y0+dy plus the crop's own origin); keeps icon art
    that happens to share the wallpaper's hue family (the Poems folder icon)."""
    tile = _macos_tile_image()
    px = rgba.load()
    for dy in range(rgba.height):
        for dx in range(rgba.width):
            bg = _macos_bg_at(tile, x0 + dx, y0 + dy)
            p = px[dx, dy]
            if all(abs(p[i] - bg[i]) <= tol for i in range(3)):
                px[dx, dy] = (0, 0, 0, 0)

def knockout_macos_purple(rgba, tol=25):
    """Flat color-range knockout for icon art that never overlaps the
    wallpaper's purple family (r~=g, b notably higher): doc, trash,
    macintosh-hd, cursor."""
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if abs(r - g) < 16 and b > r + tol:
                px[x, y] = (0, 0, 0, 0)

def knockout_macos_menubar(rgba, tol=10):
    """Flat knockout of the (221,221,221) menu-bar grey, for apple.png/finder.png."""
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if abs(r - 221) <= tol and abs(g - 221) <= tol and abs(b - 221) <= tol:
                px[x, y] = (0, 0, 0, 0)

def crop_macos_clean(src_rel, box, dst, method='purple'):
    """A production desktop/menu-bar icon: crop, knock out its background by
    the given method ('pattern' = tile-diff for the Poems folder icon,
    'purple' = flat wallpaper range, 'menubar' = flat menu-bar grey), drop
    speckle, tight-crop, and pad to a centred square so CSS 32x32 doesn't
    distort it. Mirrors cut_os2()'s crop_clean()."""
    im = Image.open(REF / src_rel).convert('RGB').crop(box).convert('RGBA')
    if method == 'pattern':
        knockout_macos_pattern(im, box[0], box[1])
    elif method == 'menubar':
        knockout_macos_menubar(im)
    else:
        knockout_macos_purple(im)
    _declutter(im)
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    s = max(im.size)
    sq = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    sq.alpha_composite(im, ((s - im.width) // 2, (s - im.height) // 2))
    (OUT / dst).parent.mkdir(parents=True, exist_ok=True)
    sq.save(OUT / dst)
    print(f'{dst:28s} {sq.size[0]}x{sq.size[1]}  <- {src_rel} {box} (clean, {method})')

def cut_macos(only=None):
    def want(dst):
        return not only or any(f in dst for f in only)

    def crop(src_rel, box, dst):
        im = Image.open(REF / src_rel).convert('RGB').crop(box)
        out = OUT / dst
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out)
        print(f'{dst:28s} {im.size[0]}x{im.size[1]}  <- {src_rel} {box}')

    # ---- desktop background pattern tile (140x140, see MACOS_TILE_BOX) ----
    if want('macos/pattern'):
        crop('macos/01-desktop.png', MACOS_TILE_BOX, 'macos/pattern.png')

    # ---- desktop icon+label whole-rectangle units (opaque, 1:1 placement) --
    # Per the extraction policy: these carry the patterned background, so
    # fixture placement must be exact (same idiom as OS/2's OS2_RECTS). All
    # nine are the real Mac OS 8.6 Easy-Install default desktop content;
    # 'unix' is flagged separately below as a non-authentic rig artifact.
    # Italic labels (measured by pixel slant, not assumed from "is it an
    # alias"): register, browsenet, mail. quicktime measured NOT italic.
    DESKTOP_RECTS = {
        'desktop-register':     ('macos/01-desktop.png', (411, 25, 517, 76)),
        'desktop-macintoshhd':  ('macos/01-desktop.png', (554, 44, 630, 82)),
        'desktop-doorpoem':     ('macos/01-desktop.png', (415, 89, 513, 140)),
        # 'Unix': a SheepShaver host-mount artifact frozen into the ground
        # truth captures, NOT authentic Mac OS 8.6 content. Fixtures must
        # replicate it for content parity (it's really there in the
        # reference); it must never be added to the production icon set.
        'desktop-unix':         ('macos/01-desktop.png', (573, 108, 611, 140)),
        'desktop-poems':        ('macos/01-desktop.png', (571, 153, 612, 212)),
        'desktop-browsenet':    ('macos/01-desktop.png', (538, 218, 640, 268)),
        'desktop-quicktime':    ('macos/01-desktop.png', (542, 281, 640, 341)),
        'desktop-mail':         ('macos/01-desktop.png', (573, 345, 611, 396)),
        'desktop-wastebasket':  ('macos/01-desktop.png', (557, 409, 627, 460)),
    }
    for name, (src, box) in DESKTOP_RECTS.items():
        if want(f'macos/{name}'):
            crop(src, box, f'macos/{name}.png')

    # ---- in-window Demos icon+label (opaque, sits on white, no knockout) ---
    # 02-folder: normal state. 03-nested: darkened "opened" state, visible
    # only as the slice not covered by the (dragged) Demos window in front.
    if want('macos/demos-normal'):
        crop('macos/02-folder.png', (32, 70, 67, 115), 'macos/demos-normal.png')
    if want('macos/demos-opened'):
        crop('macos/03-nested.png', (30, 70, 58, 118), 'macos/demos-opened.png')

    # ---- cursors ----
    if want('macos/cursor'):
        im = Image.open(REF / 'macos/01-desktop.png').convert('RGB').crop((305, 253, 320, 273)).convert('RGBA')
        knockout_macos_purple(im)
        (OUT / 'macos/cursor.png').parent.mkdir(parents=True, exist_ok=True)
        im.save(OUT / 'macos/cursor.png')
        print(f'{"macos/cursor.png":28s} {im.size[0]}x{im.size[1]}  <- macos/01-desktop.png (305, 253, 320, 273) (purple knockout)')
    if want('macos/ibeam'):
        crop('macos/04-document.png', (433, 232, 443, 251), 'macos/ibeam.png')

    # ---- screen-top menu bar bands (0,0)-(640,19); clock split out per-state
    # like OS/2's wc-bar+wc-clock-NN so the live parts don't force six full
    # copies of the static parts. 'left' = Apple logo + menu titles (two
    # content variants: Finder's File/Edit/View/Special/Help, enabled and the
    # dimmed-during-modal-alert state seen only in 06; SimpleText's own
    # File/Edit/Font/Size/Style/Sound/Help in 04). 'app' = grip + app icon +
    # app name + the screen's top-right corner cut (Finder variant measured
    # byte-identical across 01/02/03/05/06, including 06 -- only the menu
    # TITLES dim during the modal alert, not the application-menu segment).
    if want('macos/menubar-left-finder'):
        crop('macos/01-desktop.png', (0, 0, 245, 19), 'macos/menubar-left-finder.png')
    if want('macos/menubar-left-finder-dim'):
        crop('macos/06-dialog.png', (0, 0, 245, 19), 'macos/menubar-left-finder-dim.png')
    if want('macos/menubar-left-simpletext'):
        crop('macos/04-document.png', (0, 0, 317, 19), 'macos/menubar-left-simpletext.png')
    CLOCK_SRC = {
        '01-desktop': (488, 0, 547, 19), '02-folder': (488, 0, 547, 19),
        '03-nested': (488, 0, 547, 19), '05-context-menu': (488, 0, 547, 19),
        '06-dialog': (488, 0, 547, 19),
    }
    for state, box in CLOCK_SRC.items():
        dst = f'macos/menubar-clock-{state[:2]}.png'
        if want(f'macos/menubar-clock-{state[:2]}'):
            crop(f'macos/{state}.png', box, dst)
    if want('macos/menubar-clock-04'):
        crop('macos/04-document.png', (458, 0, 518, 19), 'macos/menubar-clock-04.png')
    if want('macos/menubar-app-finder'):
        crop('macos/01-desktop.png', (547, 0, 640, 19), 'macos/menubar-app-finder.png')
    if want('macos/menubar-app-simpletext'):
        crop('macos/04-document.png', (518, 0, 640, 19), 'macos/menubar-app-simpletext.png')

    # ---- context menu (05) and dialog (06), whole rectangles -- both carry
    # bitmap text + bevels a CSS menu/dialog can't hit the 2% bar with yet ----
    if want('macos/menu-desktop-context'):
        crop('macos/05-context-menu.png', (306, 204, 532, 339), 'macos/menu-desktop-context.png')
    if want('macos/dialog-wastebasket'):
        crop('macos/06-dialog.png', (131, 85, 509, 192), 'macos/dialog-wastebasket.png')

    # ---- Control Strip (bottom-left docked bar). The strip content itself
    # never changes, but wave-3 pixel-measurement found the 01-desktop crop is
    # NOT byte-identical to 04's own capture: the SimpleText document window
    # in 04-document.png is genuinely tall enough (see win-doc geometry below)
    # that its bottom-left corner bevel overlaps the strip's top ~10-14 rows
    # (measured: 370x14 differing region, not the "8x8 corner" an earlier pass
    # assumed -- corrected here from direct pixel comparison, not carried
    # forward). One extraction serves states 01/02/03/05/06 (no window reaches
    # that low there); 04 gets its own per-state crop below so the composited
    # window-over-strip pixels match 1:1 without having to model the overlap. ----
    if want('macos/controlstrip'):
        crop('macos/01-desktop.png', (0, 454, 370, 480), 'macos/controlstrip.png')
    if want('macos/controlstrip-04'):
        crop('macos/04-document.png', (0, 454, 370, 480), 'macos/controlstrip-04.png')

    # ---- wave-3 chrome-state crops -----------------------------------------
    # Title-bar widget glyphs (close/collapse/zoom): measured 12x12px each,
    # starting at the pinstripe zone's own top (see wave-3 report). Per-pixel
    # bevelled glyph art (not a flat bevel CSS can redraw), so extracted like
    # OS/2's sysmenu/titlebtns. Active-state only: real Mac OS hides the whole
    # box row on an inactive window (measured, see css/macos.css), so no
    # inactive variant is needed. Source: 02-folder.png (Poems, active).
    if want('macos/mtb-close'):
        crop('macos/02-folder.png', (11, 29, 23, 41), 'macos/mtb-close.png')
    if want('macos/mtb-collapse'):
        crop('macos/02-folder.png', (390, 29, 402, 41), 'macos/mtb-collapse.png')
    if want('macos/mtb-zoom'):
        crop('macos/02-folder.png', (406, 29, 418, 41), 'macos/mtb-zoom.png')
    # Desktop Poems icon, "opened" (darkened) variant: real Finder darkens a
    # folder's desktop icon while its window is open. Correction (direct
    # pixel check, not carried forward from the "measured byte-identical"
    # assumption this comment used to make): 02 and 03 are NOT identical here
    # -- 02 additionally shows the icon SELECTED (black label; Poems was just
    # double-clicked open and stays the current selection), while 03 shows it
    # open-but-unselected (light label; focus moved to Demos, opened
    # afterward, which deselects the Poems desktop icon). Two crops, one per
    # state. 'folder' (normal, unopened) stays the 01-sourced crop above.
    if want('macos/desktop-poems-opened'):
        crop('macos/02-folder.png', (571, 153, 612, 212), 'macos/desktop-poems-opened.png')
    if want('macos/desktop-poems-opened-unsel'):
        crop('macos/03-nested.png', (571, 153, 612, 212), 'macos/desktop-poems-opened-unsel.png')
    # Grow box (resize corner): measured art is a small DIAMOND checkerboard
    # glyph centered in the 16x16 tile, not a uniform diagonal hatch (a CSS
    # repeating-gradient approximation was tried first and measured further
    # from the reference than this direct extraction).
    if want('macos/growbox'):
        crop('macos/02-folder.png', (407, 248, 423, 264), 'macos/growbox.png')

    # ---- production icons: clean, transparent, cut from the SAME genuine
    # Mac OS 8.6 art (Poems is a real folder, "what the door does" a real
    # document, Wastebasket the real trash, Macintosh HD the real boot disk)
    # -- never from the 'Unix' rig artifact. ----
    # Bottom edges are held exact to the measured label-top (no pad): the pale
    # (207,207,225) label-backing box sits just 1-2px below and its color is
    # too close to the wallpaper purple for the flat knockout to clear (that
    # showed up as a thin retained sliver until this was tightened).
    if want('macos/folder.png'):
        crop_macos_clean('macos/01-desktop.png', (571, 153, 609, 188), 'macos/folder.png', 'pattern')
    if want('macos/doc.png'):
        crop_macos_clean('macos/01-desktop.png', (415, 89, 510, 124), 'macos/doc.png', 'purple')
    if want('macos/trash.png'):
        crop_macos_clean('macos/01-desktop.png', (557, 409, 624, 444), 'macos/trash.png', 'purple')
    if want('macos/macintosh-hd.png'):
        crop_macos_clean('macos/01-desktop.png', (554, 44, 627, 60), 'macos/macintosh-hd.png', 'purple')
    if want('macos/apple.png'):
        crop_macos_clean('macos/01-desktop.png', (15, 0, 30, 18), 'macos/apple.png', 'menubar')
    if want('macos/finder.png'):
        crop_macos_clean('macos/01-desktop.png', (559, 0, 579, 20), 'macos/finder.png', 'menubar')

if __name__ == '__main__':
    import sys
    main(sys.argv[1:] or None)
