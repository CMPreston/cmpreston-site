# cmpreston-site — a poetry site that is a 1990s desktop

The public shell for C.M. Preston's web poems. The reader lands on what
looks like a working desktop from one of two operating systems — BeOS
(R4/R5 "Blue" era) or OS/2 Warp 3 (1994) — opens folders, and finds
documents that are poems. A control on each desktop switches skins.

Written to pass the amnesia test: this file alone tells you how the repo
works.

## Hard rules

- **Vanilla HTML/CSS/JS. No node, no npm, no frameworks, no build step.**
  Open `index.html` and it works (a plain `python3 -m http.server` gives
  the full experience; `file://` degrades only the custom poem-scrollbars).
  The verification tooling under `verify/` is Python (Playwright +
  pixelmatch, both Python ports) — zero JavaScript tooling anywhere.
- **Identity firewall.** Nothing in this repo may reference the operator's
  real name, employer, cities, family, or personal accounts. The only
  contact address that may appear is `cmpreston0@gmail.com`. No analytics,
  no font CDNs, no third-party embeds.
- **Poems are read-only input.** Compiled poem pages come from
  `~/dev/cmpreston/dist/` (a separate, local-only repo). `tools/sync_poems.py`
  copies them into `poems/`; nothing here ever writes back.
- **Git/deploy identity.** This repo commits and (eventually) pushes as
  CMPreston (`cmpreston0@gmail.com`) — never a personal identity. Verify
  `git config user.email` and `gh auth status` before any push. First push,
  DNS changes, and shipping of extracted binary assets are gated actions
  requiring the human operator.

## Layout

```
index.html          boot page; picks skin (?skin= / localStorage / beos)
js/manifest.js      THE hand-edited content tree (folders/poems)
js/shell.js         window manager: desktop, windows, menus, dialogs
js/fixtures.js      staged verification states (?fixture=…); prod-inert
css/base.css        structure shared by skins
css/beos.css        BeOS skin (values measured from emulator captures)
css/os2.css         OS/2 Warp 3 skin (values measured from archive refs)
icons/<skin>/       sprites cut from reference captures by tools/make_icons.py
poems/              compiled poem pages copied from ~/dev/cmpreston/dist
fonts/              licensed webfonts + their license texts
tools/              stdlib-Python helpers (sync_poems, make_icons)
reference/<skin>/   ground-truth screenshots for the 6 checkpoint states
reference/raw/      unprocessed source captures incl. beos-emulator/
verify/             Playwright+pixelmatch harness (see VERIFICATION.md)
```

## Adding a poem

1. Build it in `~/dev/cmpreston` (`./build.sh path/to/poem.md`).
2. `python3 tools/sync_poems.py`
3. Add one entry in `js/manifest.js` under the folder you want.

## Verification

"Looks right" is not a completion criterion here. Twelve checkpoint states
(6 per skin) are pixel-diffed against reference screenshots — real BeOS
R5.0.1 emulator captures and curated OS/2 Warp 3 archive captures — with a
pass bar of <2% pixels different. See `VERIFICATION.md` for current status
and provenance, and `verify/` for the harness:

```
verify/.venv/bin/python3 verify/capture.py    # screenshot the 12 states
verify/.venv/bin/python3 verify/diff.py       # pixel-diff vs reference/
```

## Asset provenance

Icon sprites in `icons/` are pixel crops of the reference screenshots
(IBM's and Be's original artwork). They exist for local rendering and the
verification loop; whether they ship on the public site is an explicit
operator decision (asset licensing gate) recorded before deploy. Fonts in
`fonts/` are libre substitutes: Workplace Sans (SIL OFL 1.1) standing in
for OS/2's UI font, TeX Gyre Heros (GUST Font License) for BeOS's
Swis721 BT. License texts sit next to the binaries.
