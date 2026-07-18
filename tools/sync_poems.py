#!/usr/bin/env python3
"""Copy compiled poem pages from the cmpreston repo into poems/.

Source of truth is ~/dev/cmpreston/dist/ (read-only; built by that repo's
build.sh). Run this after rebuilding poems there, then add any new files to
js/manifest.js by hand. Python stdlib only.
"""
import pathlib
import shutil
import sys

SRC = pathlib.Path.home() / 'dev' / 'cmpreston' / 'dist'
DST = pathlib.Path(__file__).resolve().parent.parent / 'poems'

def main():
    if not SRC.is_dir():
        sys.exit(f'source not found: {SRC}')
    DST.mkdir(exist_ok=True)
    copied = []
    for f in sorted(SRC.glob('*.html')):
        if f.name == 'index.html':   # dist's own demo index, not a poem
            continue
        shutil.copy2(f, DST / f.name)
        copied.append(f.name)
    print(f'copied {len(copied)} poem page(s) from {SRC}:')
    for name in copied:
        print(' ', name)

if __name__ == '__main__':
    main()
