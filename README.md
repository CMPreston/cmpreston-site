# cmpreston-site — a poetry site that is a 1990s desktop

The public shell for C.M. Preston's web poems. The reader lands on what
looks like a working desktop from one of three operating systems (BeOS
R4/R5 "Blue" era, OS/2 Warp 4 from 1996, or Mac OS 8.6 from 1999, the
Platinum appearance), opens folders, and finds documents that are poems.
Each desktop's system menus switch between the skins.

## Hard rules

- **Vanilla HTML/CSS/JS. No node, no npm, no frameworks, no build step.**
  Open `docs/index.html` and it works (a plain `python3 -m http.server`
  run in `docs/` gives the full experience; `file://` degrades only the
  custom poem-scrollbars).
  The verification tooling under `verify/` is Python (Playwright +
  pixelmatch, both Python ports) — zero JavaScript tooling anywhere.
- **Only `docs/` is published.** GitHub Pages serves `main:/docs` (legacy
  build, `docs/.nojekyll`, custom domain from `docs/CNAME`). Everything else
  here (verification harness, emulator rigs, reference captures, tools,
  this file) is development material and never served on the site.
- **Contact and embeds.** The only contact address on the site is
  `cmpreston0@gmail.com`. No analytics, no font CDNs, no third-party embeds.
- **Poems are read-only input.** Compiled poem pages come from the
  `cmpreston` poem compiler's `dist/` (a separate, local-only repo, checked
  out beside this one). `tools/sync_poems.py` copies them into
  `docs/poems/`; nothing here ever writes back.

## Layout

```
docs/               THE PUBLISHED SITE (GitHub Pages root)
  index.html        boot page; picks skin (?skin= / localStorage / beos)
  js/manifest.js    THE hand-edited content tree (folders/poems)
  js/shell.js       window manager: desktop, windows, menus, dialogs, 3 skins
  js/fixtures.js    staged verification states (?fixture=…); prod-inert
  css/base.css      structure shared by skins
  css/beos.css      BeOS skin (values measured from emulator captures)
  css/os2.css       OS/2 Warp 4 skin (values measured from emulator captures)
  css/macos.css     Mac OS 8.6 skin (values measured from emulator captures)
  icons/<skin>/     sprites cut from reference captures by tools/make_icons.py
  poems/            compiled poem pages copied from the compiler's dist/
  fonts/            licensed webfonts + their license texts
  CNAME, robots.txt, favicon.png, .nojekyll
tools/              stdlib-Python helpers (sync_poems, make_icons)
reference/<skin>/   ground-truth screenshots for the 6 checkpoint states
reference/raw/      unprocessed source captures incl. beos-emulator/
verify/             Playwright+pixelmatch harness + emulator rigs (beos_rig,
                    os2_rig, macos_rig; see VERIFICATION.md)
```

## Adding a poem

1. Build it in the `cmpreston` compiler repo (`./build.sh path/to/poem.md`).
2. `python3 tools/sync_poems.py`
3. Add one entry in `docs/js/manifest.js` under the folder you want.

## Verification

"Looks right" is not a completion criterion here. Eighteen checkpoint
states (6 per skin) are pixel-diffed against reference screenshots: real
BeOS R5.0.1, OS/2 Warp 4, and Mac OS 8.6, each running in an emulator and
captured by us, with a pass bar of <2% pixels different. See
`VERIFICATION.md` for current status and provenance, and `verify/` for the
harness:

```
verify/.venv/bin/python3 verify/capture.py    # screenshot the 18 states
verify/.venv/bin/python3 verify/diff.py       # pixel-diff vs reference/
```

## Asset provenance

Icon sprites in `docs/icons/` are pixel crops of the reference screenshots
(IBM's, Be's, and Apple's original artwork). They exist for local rendering
and the verification loop; shipping them on the public site is an explicit
operator decision (asset licensing gate), recorded before deploy for each
vendor's artwork. Fonts in `docs/fonts/` are libre substitutes: Workplace Sans
(SIL OFL 1.1) standing in for OS/2's UI font, TeX Gyre Heros (GUST Font
License) for BeOS's Swis721 BT; the Mac OS skin renders UI text in a
Geneva-first system stack (nothing Apple-owned is embedded as a webfont).
License texts sit next to the binaries.
