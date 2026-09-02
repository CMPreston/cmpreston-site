// The one hand-maintained content file. Edit this when adding poems.
// A folder entry: { type:'folder', name, icon, children:[...] }
// A document entry: { type:'doc', name, path } — path points at a compiled
// poem page copied into poems/ by tools/sync_poems.py (source of truth:
// ~/dev/cmpreston/dist/, never edited here).
// Special types: 'switcher' (skin toggle control), 'trash' (decorative).
//
// Content as of 2026-09-02: the published record. Sources are the frozen
// as-published snapshots in the vault (create/oslo/works/_published/), one
// per acceptance, compiled with the plain tool. "Photographs" holds the
// photo-poem pairings (the met_museum series); one pairing is live so far.
window.MANIFEST = {
  "site": {
    "title": "C.M. Preston",
    "contact": "cmpreston0@gmail.com",
    "about_lines": [
      "cmpreston.com",
      "poems for the browser",
      "Version 1.1",
      "(c) C.M. Preston. All rights reserved."
    ]
  },
  "desktop": [
    {
      "type": "folder",
      "name": "Poems",
      "icon": "folder",
      "children": [
        { "type": "doc", "name": "from the flood", "path": "poems/from-the-flood-meat-for-tea-2020.html" },
        { "type": "doc", "name": "stern promises", "path": "poems/stern-promises-meat-for-tea-2020.html" },
        { "type": "doc", "name": "My friends getting Botox", "path": "poems/my-friends-getting-botox-lucky-jefferson-2020.html" },
        { "type": "doc", "name": "Untitled", "path": "poems/untitled-better-than-starbucks-2020.html" }
      ]
    },
    {
      "type": "folder",
      "name": "Photographs",
      "icon": "folder",
      "children": [
        { "type": "doc", "name": "This causes seizures", "path": "poems/this-causes-seizures-ethel-2020.html" }
      ]
    },
    { "type": "trash", "icon": "trash" }
  ]
};
