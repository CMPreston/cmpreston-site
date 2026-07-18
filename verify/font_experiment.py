#!/usr/bin/env python3
"""Measure a state's diff under alternative font stacks.

Not part of the canonical suite (capture.py uses the production stack).
Usage: font_experiment.py [skin/state] — default beos/06-dialog.
"""
import json
import pathlib
import socket
import subprocess
import sys
import time

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / 'verify' / 'states.json').read_text())
VARIANTS = ['', 'tgh', 'swiss', 'swissaa']

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'beos/06-dialog'
    skin, state = target.split('/')
    ref_p = ROOT / 'reference' / skin / (state + '.png')
    ref = Image.open(ref_p).convert('RGB')
    w, h = ref.size

    s = socket.socket(); s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]; s.close()
    server = subprocess.Popen(
        [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.6)
    results = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                '--force-color-profile=srgb', '--disable-lcd-text',
                '--font-render-hinting=none', '--hide-scrollbars'])
            for var in VARIANTS:
                ctx = browser.new_context(viewport={'width': w, 'height': h},
                                          device_scale_factor=1)
                page = ctx.new_page()
                url = (f'http://127.0.0.1:{port}/index.html'
                       f'?skin={skin}&fixture={state}')
                if var:
                    url += f'&authfont={var}'
                page.goto(url)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(800)
                shot_p = ROOT / 'diffs' / f'fontexp-{state}-{var or "prod"}.png'
                shot_p.parent.mkdir(exist_ok=True)
                page.screenshot(path=str(shot_p))
                ctx.close()
                build = Image.open(shot_p).convert('RGB')
                diff = Image.new('RGBA', ref.size)
                n = pixelmatch(ref, build, diff,
                               threshold=CFG['pixel_threshold'], includeAA=True)
                pct = 100.0 * n / (w * h)
                diff.save(ROOT / 'diffs' / f'fontexp-{state}-{var or "prod"}-diff.png')
                results.append((var or 'prod(helvetica)', n, pct))
            browser.close()
    finally:
        server.terminate()
    print(f'{target}  (pass bar {CFG["pass_threshold_pct"]}%)')
    for var, n, pct in results:
        print(f'  {var:18s} {n:7d} px  {pct:6.3f}%')

if __name__ == '__main__':
    main()
