#!/usr/bin/env python3
"""Copy compiled poem pages from the cmpreston repo into poems/.

Source of truth is ~/dev/cmpreston/dist/ (read-only; built by that repo's
build.sh). Run this after rebuilding poems there, then add any new files to
js/manifest.js by hand. Python stdlib only.

Skipped: dist's own index.html and the demo-*.html tool demos (scaffolding,
not C.M. Preston works; removed from the site 2026-09-02). Also carried
across: dist/images/ (photographs for plain poems) into poems/images/ and
dist/fonts/ (embedded typefaces and their license notes) into poems/fonts/,
so a compiled page's relative src and its @font-face url keep working.

Each copied page gets a robots "noarchive" directive injected (merged into an
existing robots meta if the compiler emitted one). Site policy: searchable,
never archived; the source pages in the compiler repo stay untouched.
"""
import os
import pathlib
import re
import shutil
import sys

SRC = pathlib.Path(os.environ.get('CMP_DIST') or
                   pathlib.Path.home() / 'dev' / 'cmpreston' / 'dist')
DST = pathlib.Path(__file__).resolve().parent.parent / 'poems'

ROBOTS_META = re.compile(r'(<meta\s+name="robots"\s+content=")([^"]*)(")', re.I)

def ensure_noarchive(page: pathlib.Path) -> None:
    html = page.read_text(encoding='utf-8')
    m = ROBOTS_META.search(html)
    if m:
        if 'noarchive' in m.group(2).lower():
            return
        html = ROBOTS_META.sub(
            lambda mm: mm.group(1) + mm.group(2) + ', noarchive' + mm.group(3),
            html, count=1)
    else:
        html = html.replace(
            '<head>', '<head>\n<meta name="robots" content="noarchive">', 1)
    page.write_text(html, encoding='utf-8')

def main():
    if not SRC.is_dir():
        sys.exit(f'source not found: {SRC}')
    DST.mkdir(exist_ok=True)
    copied = []
    for f in sorted(SRC.glob('*.html')):
        if f.name == 'index.html' or f.name.startswith('demo-'):
            continue                 # dist's demo index and tool demos
        shutil.copy2(f, DST / f.name)
        ensure_noarchive(DST / f.name)
        copied.append(f.name)
    images = SRC / 'images'
    if images.is_dir():
        (DST / 'images').mkdir(exist_ok=True)
        for f in sorted(images.iterdir()):
            if f.is_file():
                shutil.copy2(f, DST / 'images' / f.name)
                copied.append('images/' + f.name)
    fonts = SRC / 'fonts'
    if fonts.is_dir():
        (DST / 'fonts').mkdir(exist_ok=True)
        for f in sorted(fonts.iterdir()):
            if f.is_file():
                shutil.copy2(f, DST / 'fonts' / f.name)
                copied.append('fonts/' + f.name)
    print(f'copied {len(copied)} poem page(s) from {SRC} (noarchive injected):')
    for name in copied:
        print(' ', name)

if __name__ == '__main__':
    main()
