#!/usr/bin/env python3
"""Pixel-diff build screenshots against references; write diff overlays.

Pass bar: under 2.0% of pixels different (states.json pass_threshold_pct).
Outputs diffs/<skin>/<state>.png and diffs/results.json.
Run with verify/.venv/bin/python3.
"""
import json
import pathlib
import sys

from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / 'verify' / 'states.json').read_text())

def main():
    results = []
    for skin in CFG['skins']:
        for state in CFG['states']:
            ref_p = ROOT / 'reference' / skin / (state + '.png')
            build_p = ROOT / 'build_screenshots' / skin / (state + '.png')
            row = {'skin': skin, 'state': state}
            if not ref_p.exists():
                row['status'] = 'NO-REFERENCE'
                results.append(row)
                continue
            if not build_p.exists():
                row['status'] = 'NO-BUILD-SHOT'
                results.append(row)
                continue
            ref = Image.open(ref_p).convert('RGB')
            build = Image.open(build_p).convert('RGB')
            if ref.size != build.size:
                row['status'] = f'SIZE-MISMATCH ref={ref.size} build={build.size}'
                results.append(row)
                continue
            diff = Image.new('RGB', ref.size)
            n = pixelmatch(ref, build, diff,
                           threshold=CFG['pixel_threshold'],
                           includeAA=True)
            pct = 100.0 * n / (ref.size[0] * ref.size[1])
            out = ROOT / 'diffs' / skin / (state + '.png')
            out.parent.mkdir(parents=True, exist_ok=True)
            diff.save(out)
            row.update(status='ok', pixels=n, pct=round(pct, 3),
                       passed=pct < CFG['pass_threshold_pct'],
                       size=list(ref.size))
            results.append(row)
    (ROOT / 'diffs' / 'results.json').write_text(json.dumps(results, indent=1))
    print(f"{'skin':6s} {'state':16s} {'diff%':>8s}  pass?")
    failures = 0
    for r in results:
        if r['status'] != 'ok':
            print(f"{r['skin']:6s} {r['state']:16s} {'—':>8s}  {r['status']}")
            failures += 1
        else:
            mark = 'PASS' if r['passed'] else 'FAIL'
            if not r['passed']:
                failures += 1
            print(f"{r['skin']:6s} {r['state']:16s} {r['pct']:8.3f}  {mark}")
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
