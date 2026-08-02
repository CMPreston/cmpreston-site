#!/usr/bin/env python3
"""Copy compiled poem pages from the cmpreston repo into poems/.

Source of truth is ~/dev/cmpreston/dist/ (read-only; built by that repo's
build.sh). Run this after rebuilding poems there, then add any new files to
js/manifest.js by hand. Python stdlib only.

Each copied page gets a robots "noarchive" directive injected (merged into an
existing robots meta if the compiler emitted one). Site policy: searchable,
never archived; the source pages in the compiler repo stay untouched.
"""
import pathlib
import re
import shutil
import sys

SRC = pathlib.Path.home() / 'dev' / 'cmpreston' / 'dist'
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
        if f.name == 'index.html':   # dist's own demo index, not a poem
            continue
        shutil.copy2(f, DST / f.name)
        ensure_noarchive(DST / f.name)
        copied.append(f.name)
    print(f'copied {len(copied)} poem page(s) from {SRC} (noarchive injected):')
    for name in copied:
        print(' ', name)

if __name__ == '__main__':
    main()
