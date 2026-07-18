#!/usr/bin/env python3
"""Stage desktop states on the live BeOS VM via the QEMU monitor.

One persistent HMP connection per invocation (rapid per-event reconnects
proved unreliable). PS/2 mouse is relative with acceleration, so moves pin
to the top-left corner then walk in small steps, with a screendump-based
closed-loop correction pass.

CLI:
  stage_beos.py <workdir> shot NAME.png
  stage_beos.py <workdir> moveto X Y
  stage_beos.py <workdir> clickat X Y   | rclickat X Y | dblat X Y
  stage_beos.py <workdir> drag X1 Y1 X2 Y2
  stage_beos.py <workdir> type 'text'   | key ret alt-o ...
"""
import os
import pathlib
import socket
import sys
import time

from PIL import Image

WORK = pathlib.Path(sys.argv[1]).resolve()
os.chdir(WORK)                      # sun_path length limit: relative socket
STEP = 3

class Mon:
    def __init__(self):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect('mon.sock')
        self.s.settimeout(0.05)     # drains must not block
        time.sleep(0.15)
        self.drain()

    def drain(self):
        try:
            while True:
                if not self.s.recv(65536):
                    break
        except socket.timeout:
            pass

    def cmd(self, c, delay=0.05):
        self.s.sendall((c + '\n').encode())
        time.sleep(delay)
        self.drain()

MON = None
def mon():
    global MON
    if MON is None:
        MON = Mon()
    return MON

def key(name, delay=0.12):
    mon().cmd('sendkey ' + name, delay)

def shot_im():
    p = WORK / '_stage.ppm'
    try: p.unlink()
    except FileNotFoundError: pass
    mon().cmd(f'screendump {p.name}', 0.5)
    for _ in range(24):
        try:
            return Image.open(p).convert('RGB')
        except Exception:
            time.sleep(0.2)
    raise RuntimeError('screendump failed')

def locate_cursor(im):
    px = im.load()
    w, h = im.size
    whites = []
    for y in range(0, h):
        for x in range(0, w):
            if px[x, y] == (255, 255, 255):
                whites.append((x, y))
    clusters = []
    for x, y in whites:
        placed = False
        for c in clusters:
            if c[0] - 20 <= x <= c[2] + 20 and c[1] - 20 <= y <= c[3] + 20:
                c[0] = min(c[0], x); c[1] = min(c[1], y)
                c[2] = max(c[2], x); c[3] = max(c[3], y)
                c[4] += 1
                placed = True
                break
        if not placed:
            clusters.append([x, y, x, y, 1])
    best = None
    for c in clusters:
        cw, ch = c[2] - c[0], c[3] - c[1]
        if 5 <= cw <= 16 and 8 <= ch <= 20 and 12 <= c[4] <= 120:
            score = abs(cw - 10) + abs(ch - 14)
            if best is None or score < best[0]:
                best = (score, c[0], c[1])
    return (best[1], best[2]) if best else None

def pin():
    for _ in range(16):
        mon().cmd('mouse_move -120 -120', 0.03)
    time.sleep(0.25)

def walk(dx, dy):
    while dx or dy:
        sx = max(-STEP, min(STEP, dx))
        sy = max(-STEP, min(STEP, dy))
        mon().cmd(f'mouse_move {sx} {sy}', 0.02)
        dx -= sx
        dy -= sy
    time.sleep(0.3)

def locate_by_wiggle():
    """Move +10,+10 between two dumps; the only thing that moves is the
    cursor. Returns the cursor tip position AFTER the wiggle, or None.
    The Deskbar region is masked out (its clock repaints)."""
    im1 = shot_im()
    walk(10, 10)
    im2 = shot_im()
    p1, p2 = im1.load(), im2.load()
    w, h = im1.size
    xs, ys = [], []
    for y in range(0, h):
        for x in range(0, w):
            if x > 512 and y < 76:
                continue                      # Deskbar mask
            if p1[x, y] != p2[x, y]:
                xs.append(x); ys.append(y)
    if not xs or len(xs) > 3000:
        return None
    return (min(xs) + 10, min(ys) + 10)

def move_to(x, y, verify=True):
    pin()
    walk(x - 10, y - 10)      # wiggle in locate_by_wiggle adds (10,10)
    if not verify:
        walk(10, 10)
        return
    for i in range(4):
        pos = locate_by_wiggle()
        if pos is None:
            print('  (cursor not detectable; dead reckoning only)')
            return
        dx, dy = x - pos[0], y - pos[1]
        print(f'  cursor at {pos}, target ({x},{y})')
        if abs(dx) <= 1 and abs(dy) <= 1:
            return
        if i == 3:
            walk(dx, dy)
            return
        walk(dx - 10, dy - 10)   # next wiggle re-adds (10,10)

def press(btn=1, hold=0.1):
    mon().cmd(f'mouse_button {btn}', hold)
    mon().cmd('mouse_button 0', 0.15)

def dbl():
    press(1, 0.06)
    time.sleep(0.12)
    press(1, 0.06)
    time.sleep(0.3)

CHARMAP = {c: c for c in 'abcdefghijklmnopqrstuvwxyz0123456789'}
CHARMAP.update({' ': 'spc', '.': 'dot', '/': 'slash', '-': 'minus', '=': 'equal',
                ',': 'comma', ';': 'semicolon', "'": 'apostrophe'})
SHIFT = {u: l for u, l in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                              'abcdefghijklmnopqrstuvwxyz')}
SHIFT.update({'!': '1', '?': 'slash', '(': '9', ')': '0', ':': 'semicolon',
              '"': 'apostrophe'})

def type_text(text):
    for ch in text:
        if ch in CHARMAP:
            key(CHARMAP[ch], 0.09)
        elif ch in SHIFT:
            key('shift-' + SHIFT[ch], 0.09)
        elif ch == '\n':
            key('ret', 0.09)

def walk1(dx, dy):
    # 1px steps: below any acceleration threshold -> exact 1:1 mapping
    while dx or dy:
        sx = max(-1, min(1, dx))
        sy = max(-1, min(1, dy))
        mon().cmd(f'mouse_move {sx} {sy}', 0.012)
        dx -= sx
        dy -= sy
    time.sleep(0.25)

def main():
    cmd, a = sys.argv[2], sys.argv[3:]
    if cmd == 'shot':
        shot_im().save(WORK / a[0])
    elif cmd == 'moveto':
        move_to(int(a[0]), int(a[1]))
    elif cmd == 'clickat':
        move_to(int(a[0]), int(a[1])); press(1)
    elif cmd == 'clickat1':
        pin(); walk1(int(a[0]), int(a[1])); press(1)
    elif cmd == 'moveto1':
        pin(); walk1(int(a[0]), int(a[1]))
    elif cmd == 'nudge':
        walk1(int(a[0]), int(a[1]))
    elif cmd == 'rclickat':
        move_to(int(a[0]), int(a[1])); press(2)
    elif cmd == 'dblat':
        move_to(int(a[0]), int(a[1])); dbl()
    elif cmd == 'drag':
        move_to(int(a[0]), int(a[1]))
        mon().cmd('mouse_button 1', 0.2)
        walk(int(a[2]) - int(a[0]), int(a[3]) - int(a[1]))
        time.sleep(0.2)
        mon().cmd('mouse_button 0', 0.25)
    elif cmd == 'type':
        type_text(' '.join(a))
    elif cmd == 'key':
        for k in a:
            key(k)
    else:
        sys.exit('unknown cmd ' + cmd)

if __name__ == '__main__':
    main()
