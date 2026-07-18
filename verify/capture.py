#!/usr/bin/env python3
"""Screenshot the site's 12 fixture states with headless Chromium.

Each build screenshot is taken at exactly the pixel dimensions of its
reference image (reference/<skin>/<state>.png), so the diff is 1:1.
Run with verify/.venv/bin/python3. Serves the repo over a local
http.server (fetch-free shell also works from file://, but http keeps
iframe scripting same-origin for the custom scrollbars).
"""
import json
import pathlib
import socket
import subprocess
import sys
import time

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / 'verify' / 'states.json').read_text())
OUT = ROOT / 'build_screenshots'

def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def main(only=None):
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.6)
    taken, missing = [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                '--force-color-profile=srgb',
                '--disable-lcd-text',
                '--font-render-hinting=none',
                '--hide-scrollbars',
            ])
            for skin in CFG['skins']:
                for state in CFG['states']:
                    if only and (skin, state) not in only and state not in only:
                        continue
                    ref = ROOT / 'reference' / skin / (state + '.png')
                    if not ref.exists():
                        missing.append(f'{skin}/{state}')
                        continue
                    w, h = Image.open(ref).size
                    ctx = browser.new_context(
                        viewport={'width': w, 'height': h},
                        device_scale_factor=1)
                    page = ctx.new_page()
                    page.goto(f'http://127.0.0.1:{port}/index.html'
                              f'?skin={skin}&fixture={state}')
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(700)   # settle fonts/iframes
                    dst = OUT / skin / (state + '.png')
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(dst))
                    ctx.close()
                    taken.append(f'{skin}/{state} ({w}x{h})')
            browser.close()
    finally:
        server.terminate()
    for t in taken:
        print('captured', t)
    for m in missing:
        print('NO REFERENCE for', m, '- state not captured', file=sys.stderr)
    return 0

if __name__ == '__main__':
    only = set(a for a in sys.argv[1:]) or None
    sys.exit(main(only))
