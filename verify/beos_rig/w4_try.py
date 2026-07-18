#!/usr/bin/env python3
"""One scripted OS/2 Warp 4 install-boot attempt under QEMU.

Boots the install floppy with the given extra QEMU args, performs the
three-diskette dance on fixed timings, then polls and classifies the
outcome: TRAP screen, still-loading, or installer-alive (blue Welcome).

Usage: w4_try.py <workdir> <tag> [extra qemu args...]
Writes <tag>-final.png and prints a verdict line.
"""
import os
import pathlib
import socket
import subprocess
import sys
import time

from PIL import Image

WORK = pathlib.Path(sys.argv[1]).resolve()
os.chdir(WORK)
TAG = sys.argv[2]
EXTRA = sys.argv[3:]
SOCK = f'mon-{TAG}.sock'
QEMU = '/opt/homebrew/bin/qemu-system-i386'

def hmp(cmd, delay=0.3):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.settimeout(0.6)
    time.sleep(0.1)
    try: s.recv(65536)
    except socket.timeout: pass
    s.sendall((cmd + '\n').encode())
    time.sleep(delay)
    try: s.recv(65536)
    except socket.timeout: pass
    s.close()

def dump(name):
    p = WORK / f'_w4_{TAG}.ppm'
    try: p.unlink()
    except FileNotFoundError: pass
    hmp(f'screendump {p.name}', 0.5)
    for _ in range(20):
        try:
            im = Image.open(p).convert('RGB')
            im.save(WORK / name)
            return im
        except Exception:
            time.sleep(0.2)
    raise RuntimeError('screendump failed')

def classify(im):
    px = im.load()
    w, h = im.size
    blue = black = white = 0
    n = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b = px[x, y]
            n += 1
            if b > 120 and r < 90 and g < 90: blue += 1
            elif r < 40 and g < 40 and b < 40: black += 1
            elif r > 200 and g > 200 and b > 200: white += 1
    blue /= n; black /= n; white /= n
    if black > 0.55 and white > 0.012:
        return 'TRAP/TEXT'
    if blue > 0.4:
        return 'BLUE'
    return f'OTHER(blue={blue:.2f},black={black:.2f})'

def main():
    # clear ANY prior warp4 instance — a stale one holds the disk write lock
    subprocess.run(['pkill', '-f', 'warp4-'], capture_output=True)
    time.sleep(1.2)
    pathlib.Path(SOCK).unlink(missing_ok=True)
    args = [QEMU, '-M', 'pc', '-m', '64',
            '-drive', 'file=w4_hd.raw,format=raw,if=ide,index=0',
            '-drive', 'file=w4/OS2WARP4.iso,format=raw,media=cdrom,if=ide,index=2',
            '-drive', 'file=w4/install.img,format=raw,if=floppy,index=0',
            '-boot', 'a', '-vga', 'std', '-display', 'none',
            '-monitor', f'unix:{SOCK},server,nowait',
            '-audiodev', 'none,id=noaud', '-rtc', 'base=localtime',
            '-name', f'warp4-{TAG}'] + EXTRA
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT)
    print('qemu pid', proc.pid, 'args:', ' '.join(EXTRA) or '(base)')
    time.sleep(3)
    if proc.poll() is not None:
        print('VERDICT: qemu died on launch')
        return 2

    # diskette dance on generous fixed timings, verifying prompts loosely
    time.sleep(17)                      # install disk boots to Disk 1 prompt
    dump(f'{TAG}-p1.png')
    hmp('change floppy0 w4/disk1.img raw', 0.5)
    hmp('sendkey ret')
    time.sleep(24)                      # disk 1 loads to Disk 2 prompt
    dump(f'{TAG}-p2.png')
    hmp('change floppy0 w4/disk2.img raw', 0.5)
    hmp('sendkey ret')

    verdict = '?'
    for i in range(16):                 # up to ~2.5 min of driver loading
        time.sleep(10)
        im = dump(f'{TAG}-final.png')
        verdict = classify(im)
        print(f'  t+{10*(i+1)}s {verdict}')
        if verdict == 'TRAP/TEXT':
            break
        if verdict == 'BLUE' and i >= 3:    # stable blue = installer alive
            break
    print('VERDICT:', verdict)
    if verdict != 'BLUE':
        proc.terminate()
    return 0 if verdict == 'BLUE' else 1

if __name__ == '__main__':
    sys.exit(main())
