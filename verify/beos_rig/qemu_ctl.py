#!/usr/bin/env python3
"""Talk to a QEMU HMP monitor over a unix socket. stdlib only.

Usage:
  qemu_ctl.py <sock> cmd 'screendump /path/shot.ppm'
  qemu_ctl.py <sock> keys 'ret'            # comma/space separated sendkey names, one sendkey per token
  qemu_ctl.py <sock> type 'hello world'    # types a string via sendkey
  qemu_ctl.py <sock> mouse <dx> <dy>       # relative move
  qemu_ctl.py <sock> click [1|2|4]         # press+release button mask (1=left)
"""
import socket, sys, time

CHARMAP = {}
for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
    CHARMAP[c] = c
CHARMAP.update({' ': 'spc', '.': 'dot', '/': 'slash', '-': 'minus', '=': 'equal',
                ',': 'comma', ';': 'semicolon', "'": 'apostrophe', '\\': 'backslash',
                '[': 'bracket_left', ']': 'bracket_right', '`': 'grave_accent'})
SHIFTED = {}
for lo, hi in zip('abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    SHIFTED[hi] = lo
SHIFTED.update({'!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6',
                '&': '7', '*': '8', '(': '9', ')': '0', '_': 'minus', '+': 'equal',
                ':': 'semicolon', '"': 'apostrophe', '<': 'comma', '>': 'dot',
                '?': 'slash', '~': 'grave_accent', '{': 'bracket_left', '}': 'bracket_right',
                '|': 'backslash'})

def hmp(sock_path, commands, delay=0.08):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(sock_path)
    s.settimeout(2.0)
    time.sleep(0.15)
    try:
        s.recv(65536)  # banner
    except socket.timeout:
        pass
    out = []
    for cmd in commands:
        s.sendall((cmd + '\n').encode())
        time.sleep(delay)
        try:
            out.append(s.recv(65536).decode('utf-8', 'replace'))
        except socket.timeout:
            out.append('')
    s.close()
    return out

def main():
    sock_path, mode, args = sys.argv[1], sys.argv[2], sys.argv[3:]
    if mode == 'cmd':
        print('\n'.join(hmp(sock_path, [' '.join(args)], delay=0.4)))
    elif mode == 'keys':
        keys = ' '.join(args).replace(',', ' ').split()
        hmp(sock_path, ['sendkey ' + k for k in keys], delay=0.15)
    elif mode == 'type':
        text = ' '.join(args)
        cmds = []
        for ch in text:
            if ch in CHARMAP:
                cmds.append('sendkey ' + CHARMAP[ch])
            elif ch in SHIFTED:
                cmds.append('sendkey shift-' + SHIFTED[ch])
        hmp(sock_path, cmds, delay=0.12)
    elif mode == 'mouse':
        dx, dy = args
        hmp(sock_path, [f'mouse_move {dx} {dy}'], delay=0.15)
    elif mode == 'click':
        btn = args[0] if args else '1'
        hmp(sock_path, [f'mouse_button {btn}', 'mouse_button 0'], delay=0.15)
    else:
        sys.exit('unknown mode ' + mode)

if __name__ == '__main__':
    main()
