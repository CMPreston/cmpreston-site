#!/usr/bin/env python3
"""Closed-loop mouse control for the OS/2 Warp 4 guest in headless 86Box.

86Box only feeds mouse to the guest while the window has CAPTURED the
pointer, and it recenters the host pointer every poll — so rapid relative
warps cancel out. This driver captures once, then issues ONE settled
relative move at a time, screenshotting to locate the guest arrow cursor
and iterating until it reaches the target guest-pixel. Runs on the host;
shells into the container for xdotool + screendump.

Guest arrow cursor: a black-bordered white pointer ~12x18. We find it by
template-ish detection (a compact cluster of near-white pixels with black
neighbours) in the guest render area.

CLI (from w4rig/):
  mouse.py cap                 capture the pointer (idempotent)
  mouse.py rel                 release (Ctrl+End)
  mouse.py to GX GY            move guest cursor to (GX,GY) guest pixels
  mouse.py click [GX GY]       (move then) left click
  mouse.py dblclick GX GY
  mouse.py rclick GX GY        right button (context menu)
"""
import subprocess
import sys
import time

from PIL import Image

WORK = '/private/tmp/claude-501/-Users-cpreston-dev-cmpreston-site/7b4872a1-8fa3-46b7-95db-e8ce2c881a50/scratchpad/w4rig'
# guest render offset inside the 86Box window. With HiDPI scaling DISABLED the
# render is crisp 1:1 and the 640x480 guest starts at frame (0,52) and spans to
# (640,532). (Menu ~22 + toolbar ~30 = 52; status bar below y=532.) Full-frame
# Xvfb screendump is 1024x768 with the window at (0,0).
GUEST_X0, GUEST_Y0 = 0, 52
GUEST_Y1 = 532
# frame rows that animate and must be masked in diffs: the 86Box internal
# window titlebar band sits right at the top of the guest area.
MASK_TOP = 70    # ignore diffs above this frame-y (titlebar/toolbar churn)
MASK_RIGHT = 638  # ignore the far-right edge column artifacts

def dexec(script):
    return subprocess.run(['docker', 'exec', 'w4box', 'sh', '-c', script],
                          capture_output=True, text=True)

def xdo(cmd):
    dexec(f'export DISPLAY=:99; WID=$(xdotool search --onlyvisible --name "86Box"|tail -1); {cmd}')

def shot():
    dexec('export DISPLAY=:99; import -window root /work/_m.png')
    for _ in range(15):
        try:
            return Image.open(f'{WORK}/_m.png').convert('RGB')
        except Exception:
            time.sleep(0.15)
    raise RuntimeError('screendump failed')

def _diff_cluster(a, b):
    """Top-left of the region that changed between two shots, ignoring the
    86Box toolbar (y<52) and bottom status bar (y>556) which animate."""
    pa, pb = a.load(), b.load()
    W, H = a.size
    xs, ys = [], []
    for y in range(52, min(H, 556)):
        for x in range(0, min(W, 645)):
            if pa[x, y] != pb[x, y]:
                xs.append(x); ys.append(y)
    if not xs or len(xs) > 4000:
        return None
    return (min(xs), min(ys), max(xs), max(ys))

def _is_white(p):
    return p[0] > 200 and p[1] > 200 and p[2] > 200

def _is_black(p):
    return p[0] < 70 and p[1] < 70 and p[2] < 70

# Black-outline silhouette of the OS/2 arrow cursor, as (dx,dy) offsets from the
# TIP (hotspot, top-left). Extracted from a clean capture on a white field.
# Background-independent: the outline is always dark whatever is behind it.
ARROW_OUTLINE = [
    (0,0),
    (0,1),(1,1),
    (0,2),(1,2),(2,2),
    (0,3),(1,3),(2,3),(3,3),
    (0,4),(1,4),(2,4),(3,4),(4,4),
    (0,5),(1,5),(2,5),(3,5),(4,5),(5,5),
    (0,6),(1,6),(2,6),(3,6),(4,6),(5,6),(6,6),
    (0,7),(1,7),(2,7),(3,7),
    (0,8),(1,8),(3,8),(4,8),
    (0,9),(3,9),(4,9),
    (4,10),(5,10),
    (4,11),(5,11),
    (5,12),(6,12),
    (5,13),(6,13),
]
ARROW_N = len(ARROW_OUTLINE)

def _dark(p):
    # slightly looser than _is_black: outline pixels can be antialiased over
    # bright backgrounds. Require clearly darker than a mid-grey.
    return p[0] < 110 and p[1] < 110 and p[2] < 110

def find_cursor_tpl(im=None, region=None):
    """Single-shot template match of the arrow's dark outline. Slides the
    ARROW_OUTLINE silhouette over the guest area; the tip is where the most
    template pixels are dark (with a high threshold so text/edges don't match).
    Returns tip (frame x,y) or None. No wiggle, no motion, background-agnostic."""
    im = im or shot()
    px = im.load()
    W, H = im.size
    x0, y0, x1, y1 = region or (0, max(GUEST_Y0, 54), min(W, 636), min(H, GUEST_Y1) - 14)
    best = None
    best_hits = 0
    thr = int(ARROW_N * 0.80)   # need >=80% of the 47 outline pixels dark
    for y in range(y0, y1):
        row = im.im  # unused; keep px access
        for x in range(x0, x1):
            # quick reject: tip pixel and the first few must be dark
            if not _dark(px[x, y]):
                continue
            if not (_dark(px[x, y + 1]) and _dark(px[x + 1, y + 2])):
                continue
            hits = 0
            for dx, dy in ARROW_OUTLINE:
                if _dark(px[x + dx, y + dy]):
                    hits += 1
                    # early exit if already best-beating handled below
            if hits > best_hits:
                best_hits = hits
                best = (x, y)
    if best_hits >= thr:
        return best
    return None

def find_cursor_shape(im=None, region=None):
    """Single-shot shape detector for the OS/2 white arrow (black outline,
    tip at top-left, ~12 wide x 19 tall). Returns the tip (x,y) or None.

    Scans for candidate tip pixels: a black outline pixel whose down/right
    neighbourhood is white (the arrow body), then scores the ~13x20 footprint
    by arrow-likeness (enough white body + black outline, mostly on the upper
    diagonal). Independent of background, so it works on busy screens."""
    im = im or shot()
    px = im.load()
    W, H = im.size
    x0, y0, x1, y1 = region or (0, 52, min(W, 646), min(H, 556))
    best = None
    best_score = 0
    for y in range(y0, y1 - 20):
        for x in range(x0, x1 - 13):
            p = px[x, y]
            # tip: black-ish outline pixel, with the pixel just below-right whitish
            if not _is_black(p):
                continue
            if not (_is_white(px[x + 1, y + 1]) or _is_white(px[x + 2, y + 2])):
                continue
            # require background above/left of tip to NOT be arrow (tip is top-left)
            # score footprint
            white = black = 0
            body_ok = True
            for dy in range(0, 19):
                for dx in range(0, 13):
                    q = px[x + dx, y + dy]
                    # arrow body lives roughly under the diagonal (dx <= dy+3)
                    if dx <= dy + 4:
                        if _is_white(q):
                            white += 1
                        elif _is_black(q):
                            black += 1
            # arrow has a solid white body (~90-140 px) framed by black outline
            if white < 45 or black < 12:
                continue
            score = white + black * 2
            if score > best_score:
                best_score = score
                best = (x, y)
    return best

def _changed_points(a, b):
    pa, pb = a.load(), b.load()
    W, H = a.size
    pts = []
    y0 = max(MASK_TOP, GUEST_Y0)
    for y in range(y0, min(H, GUEST_Y1)):
        for x in range(0, min(W, MASK_RIGHT)):
            if pa[x, y] != pb[x, y]:
                pts.append((x, y))
    return pts

def _cluster(pts, gap=10):
    clusters = []
    for p in pts:
        best = None
        for c in clusters:
            cx, cy = c['cx'], c['cy']
            if abs(p[0] - cx) < gap and abs(p[1] - cy) < gap:
                best = c
                break
        if best is None:
            best = {'pts': [], 'cx': p[0], 'cy': p[1]}
            clusters.append(best)
        best['pts'].append(p)
        xs = [q[0] for q in best['pts']]
        ys = [q[1] for q in best['pts']]
        best['cx'] = sum(xs) // len(xs)
        best['cy'] = sum(ys) // len(ys)
        best['box'] = (min(xs), min(ys), max(xs), max(ys))
    return clusters

def find_cursor(im=None, wig=(0, 22)):
    """Locate the guest arrow TIP (frame coords). Primary method: single-shot
    dark-outline template match (fast, no drift, background-agnostic, never
    returns a wrong point). Fallback: wiggle-diff when the outline is on a
    background too light/busy to match. None if truly not found."""
    a = im or shot()
    hit = find_cursor_tpl(a)
    if hit is not None:
        return hit
    return _find_cursor_wiggle(a, wig)

def _find_cursor_wiggle(a, wig=(0, 22)):
    """Wiggle-diff fallback: move by `wig`, diff two shots, the arrow-sized
    cluster is the cursor; return the POST-move tip. Titlebar (y<MASK_TOP) and
    right edge masked."""
    dx, dy = wig
    move_rel(dx, dy)
    b = shot()
    # the move may have carried the arrow onto plainer ground — try template
    hit = find_cursor_tpl(b)
    if hit is not None:
        return hit
    pts = _changed_points(a, b)
    if not pts or len(pts) > 3000:
        return None
    cl = _cluster(pts, gap=12)
    # arrow silhouette is roughly 10-18 wide, 12-22 tall
    def arrowish(c):
        x0, y0, x1, y1 = c['box']
        w, h = x1 - x0 + 1, y1 - y0 + 1
        return 6 <= w <= 26 and 8 <= h <= 30 and len(c['pts']) >= 20
    cands = [c for c in cl if arrowish(c)]
    if not cands:
        return None
    # the post-move cluster is offset by ~wig from the pre-move one. If two
    # candidates differ by ~wig, pick the one further along +wig. Else pick the
    # single/largest candidate's leading (post-move) tip.
    if len(cands) >= 2:
        # try to find a pair separated by ~wig
        for c1 in cands:
            for c2 in cands:
                if c1 is c2:
                    continue
                if abs((c2['box'][0] - c1['box'][0]) - dx) <= 6 and \
                   abs((c2['box'][1] - c1['box'][1]) - dy) <= 6:
                    return (c2['box'][0], c2['box'][1])  # c2 is post-move
    # single merged cluster (small wiggle): post-move tip = min corner shifted
    # toward +wig within the union box.
    c = max(cands, key=lambda c: len(c['pts']))
    bx = c['box']
    # tip of the arrow = its top-left; the union's top-left is the pre-move tip,
    # so post-move tip ~ union top-left + wig (clamped inside union).
    tx = min(bx[2], bx[0] + max(0, dx))
    ty = min(bx[3], bx[1] + max(0, dy))
    return (tx, ty)

def home():
    """Slam the guest cursor to the top-left corner (deterministic anchor).
    Returns the resulting tip in frame coords ~ (GUEST_X0, GUEST_Y0)."""
    for _ in range(6):
        xdo('xdotool mousemove_relative --sync -- -500 -500')
    time.sleep(0.4)
    return (GUEST_X0 + 1, GUEST_Y0)

def capture():
    xdo('xdotool windowfocus --sync $WID; xdotool mousemove --window $WID 320 300; xdotool click 1')
    time.sleep(0.8)

def is_captured(im=None):
    im = im or shot()
    # status bar text region differs; simplest: check we can read the bar text
    # via a crude heuristic — the toolbar row y36..48. We trust capture() ran.
    return True

def move_rel(dx, dy):
    # 86Box recenters the host pointer each mouse poll; issue ONE settled move
    # (no --sync, which lets the recenter race the move) then wait for the poll
    # to consume it. OS/2 applies its own pointer accel, so guest displacement
    # != host delta — callers must MEASURE, not dead-reckon.
    xdo(f'xdotool mousemove_relative -- {dx} {dy}')
    time.sleep(0.45)

# Measured host->guest motion gains for THIS rig (OS/2 accel + 86Box recenter):
#   X: ~2.7 guest px per host px (fast horizontal accel).
#   Y: ~1.0 guest px per host px for large moves, ~0.55 for small.
# Callers convert a desired guest delta to a host delta by dividing by gain.
GAIN_X = 2.7
GAIN_Y = 1.0

def _host_for_guest(ex, ey):
    """Host (dx,dy) to achieve guest error (ex,ey), with per-axis gains and
    smaller, damped steps as the error shrinks (avoids the 2.7x X overshoot)."""
    # X: high gain -> divide; damp to ~70% to converge without ringing.
    hdx = ex / GAIN_X
    hdy = ey / GAIN_Y
    hdx *= 0.7
    hdy *= 0.8
    # near target, force tiny host steps for precision
    if abs(ex) < 30:
        hdx = max(-8, min(8, ex / GAIN_X))
    if abs(ey) < 15:
        hdy = max(-10, min(10, ey / GAIN_Y))
    hdx = int(max(-140, min(140, hdx)))
    hdy = int(max(-140, min(140, hdy)))
    # ensure a nonzero nudge if there is meaningful error
    if hdx == 0 and abs(ex) > 3:
        hdx = 2 if ex > 0 else -2
    if hdy == 0 and abs(ey) > 3:
        hdy = 2 if ey > 0 else -2
    return hdx, hdy

def move_to(gx, gy, tol=5, tries=45, verbose=False):
    """Closed-loop move the guest arrow TIP to guest-pixel (gx,gy) using the
    single-shot template detector each step and the measured per-axis gains.
    Returns the final frame-pos, or the best pos if detection is lost on the
    target's background (the caller should confirm the landing by screenshot).

    Keeps the arrow off the very top edge (y<GUEST_Y0+6) during travel because
    86Box clamps/glitches there."""
    tx, ty = gx + GUEST_X0, gy + GUEST_Y0
    pos = find_cursor()
    misses = 0
    best = pos
    stalls = 0
    prev = None
    for _ in range(tries):
        if pos is None:
            misses += 1
            if misses > 8:
                return best
            # nudge to plainer ground: move a bit toward mid-screen and down off
            # the top edge, then re-detect
            move_rel(20 if tx > 320 else -20, 25)
            pos = find_cursor()
            continue
        misses = 0
        best = pos
        ex, ey = tx - pos[0], ty - pos[1]
        if verbose:
            print('pos', pos, 'err', (ex, ey))
        if abs(ex) <= tol and abs(ey) <= tol:
            return pos
        # detect oscillation (position repeating) -> shrink X step
        if prev is not None and abs(pos[0] - prev[0]) <= 3 and abs(pos[1] - prev[1]) <= 3:
            stalls += 1
        else:
            stalls = 0
        prev = pos
        hdx, hdy = _host_for_guest(ex, ey)
        if stalls >= 2:                      # damp harder to break ringing
            hdx = int(hdx * 0.4)
            hdy = int(hdy * 0.4)
        move_rel(hdx, hdy)
        pos = find_cursor()
    return best if best else pos

def click(btn=1):
    xdo(f'xdotool click {btn}')
    time.sleep(0.5)

def main():
    cmd = sys.argv[1]
    a = sys.argv[2:]
    if cmd == 'cap':
        capture()
    elif cmd == 'rel':
        xdo('xdotool key ctrl+End')
    elif cmd == 'to':
        print(move_to(int(a[0]), int(a[1])))
    elif cmd == 'click':
        if len(a) == 2:
            move_to(int(a[0]), int(a[1]))
        click(1)
    elif cmd == 'dblclick':
        move_to(int(a[0]), int(a[1]))
        click(1); time.sleep(0.08); click(1)
    elif cmd == 'rclick':
        move_to(int(a[0]), int(a[1]))
        click(2)
    elif cmd == 'find':
        print(find_cursor(shot()))
    else:
        sys.exit('unknown ' + cmd)

if __name__ == '__main__':
    main()
