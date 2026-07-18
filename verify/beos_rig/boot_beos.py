#!/usr/bin/env python3
"""Closed-loop driver for the BeOS R5 boot loader menu under headless QEMU.

Reads the framebuffer (HMP screendump) after every keypress and verifies
menu state before proceeding — the loader's row layout is fixed 16px rows
starting at y=80. End state: booting with
  * boot volume: first BFS volume ("BeOS 5 Pro Edition")
  * fail-safe video mode: 640x480x16 (loader-set, no runtime video BIOS)
  * [X] Use fail-safe video mode
  * [X] Don't call the BIOS   <- avoids the input_server INT15 crash
Then polls until the desktop paints (many colors) or the kernel debugger
appears (few colors + text signature), and reports which.

Usage: boot_beos.py <mon.sock dir> ; needs Pillow (verify/.venv).
"""
import socket
import subprocess
import sys
import time
import pathlib

from PIL import Image

WORK = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
import os
os.chdir(WORK)          # macOS sun_path is 104 bytes; use relative socket path
SOCK = pathlib.Path('mon.sock')
ROW0_Y = 80
ROW_H = 16

def hmp(cmd, delay=0.25):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(str(SOCK))
    s.settimeout(2.0)
    time.sleep(0.1)
    try: s.recv(65536)
    except socket.timeout: pass
    s.sendall((cmd + '\n').encode())
    time.sleep(delay)
    try: s.recv(65536)
    except socket.timeout: pass
    s.close()

def key(name, delay=0.3):
    hmp('sendkey ' + name, delay)

_dump_n = 0
def dump():
    global _dump_n
    _dump_n += 1
    p = WORK / f'_drv{_dump_n % 4}.ppm'
    hmp(f'screendump {p}', 0.45)
    for _ in range(20):
        try:
            return Image.open(p).convert('RGB')
        except Exception:
            time.sleep(0.2)
    raise RuntimeError('screendump unreadable')

def row_brightness(im, y):
    box = im.crop((100, y + 2, 520, y + 13))
    px = list(box.getdata())
    return sum(sum(p) for p in px) / (3 * len(px))

def highlight_y(im):
    best, besty = 0, None
    y = ROW0_Y
    while y < 340:
        b = row_brightness(im, y)
        if b > 90 and b > best:
            best, besty = b, y
        y += ROW_H
    return besty

def in_menu(im):
    return highlight_y(im) is not None and im.size[0] == 720

def goto_row(target_y, tries=26):
    im = dump()
    for _ in range(tries):
        hy = highlight_y(im)
        if hy == target_y:
            return True
        key('down' if (hy is None or hy < target_y) else 'up')
        im = dump()
    return False

def checkbox_dark(im, y):
    # dark glyph pixels inside the '[ ]' area; an X adds noticeably more
    box = im.crop((86, y + 1, 118, y + 14))
    return sum(1 for p in box.getdata() if sum(p) < 250)

def main():
    print('resetting...')
    hmp('system_reset', 0.3)
    menu = None
    for i in range(40):
        key('spc', 0.25)
        if i % 4 == 3:
            im = dump()
            if in_menu(im):
                menu = im
                break
    if menu is None:
        print('FAIL: never reached boot menu'); return 1
    print('main menu reached')

    # 1. boot volume -> first entry
    goto_row(ROW0_Y); key('ret', 0.7)
    im = dump()
    if highlight_y(im) != ROW0_Y:
        print('volume menu unexpected'); return 1
    key('ret', 0.7)                     # select first volume, back to main
    print('boot volume selected')

    # 2. fail-safe video mode -> 640x480x16 (index 12)
    goto_row(ROW0_Y + 2 * ROW_H); key('ret', 0.7)
    if not goto_row(ROW0_Y + 12 * ROW_H):
        print('FAIL: could not reach 640x480x16 row'); return 1
    key('ret', 0.7)
    print('fail-safe mode 640x480x16 selected')

    # 3. safe mode menu: toggle rows 1 (use fail-safe video) and 2 (no BIOS)
    goto_row(ROW0_Y + 1 * ROW_H); key('ret', 0.7)
    for row in (1, 2):
        y = ROW0_Y + row * ROW_H
        goto_row(y)
        before = checkbox_dark(dump(), y)
        key('ret', 0.5)
        time.sleep(0.4)
        after = checkbox_dark(dump(), y)
        state = 'ON' if after > before else 'UNCONFIRMED'
        print(f'  safe-mode row {row}: dark px {before} -> {after}  [{state}]')
        if after <= before:
            print('  (leaving as-is; verify visually if boot fails)')
    goto_row(ROW0_Y + 10 * ROW_H)       # Return to main menu (y=240)
    key('ret', 0.7)

    # 4. Continue booting (y=144)
    goto_row(ROW0_Y + 4 * ROW_H)
    key('ret', 0.5)
    print('continuing boot...')

    # 5. poll for outcome
    for i in range(40):
        time.sleep(8)
        im = dump()
        if im.size[0] != 640:
            continue
        colors = im.getcolors(200000)
        n = len(colors) if colors else 999999
        top = im.crop((0, 0, 300, 12))
        darktext = sum(1 for p in top.getdata() if sum(p) > 600)
        print(f'  t+{8*(i+1)}s colors={n}')
        if n <= 8 and darktext > 40:
            im.save(WORK / 'beos_crash.png')
            print('FAIL: kernel debugger on screen (beos_crash.png)')
            return 1
        if n > 400:
            time.sleep(10)
            dump().save(WORK / 'beos_desktop.png')
            print('SUCCESS: desktop painted -> beos_desktop.png')
            return 0
    print('TIMEOUT: no desktop, no debugger detected')
    dump().save(WORK / 'beos_last.png')
    return 1

if __name__ == '__main__':
    sys.exit(main())
