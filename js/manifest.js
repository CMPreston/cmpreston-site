// The one hand-maintained content file. Edit this when adding poems.
// A folder entry: { type:'folder', name, icon, children:[...] }
// A document entry: { type:'doc', name, path } — path points at a compiled
// poem page copied into poems/ by tools/sync_poems.py (source of truth:
// ~/dev/cmpreston/dist/, never edited here).
// Special types: 'switcher' (skin toggle control), 'trash' (decorative).
window.MANIFEST = {
  "site": {
    "title": "C.M. Preston",
    "contact": "cmpreston0@gmail.com",
    "about_lines": [
      "cmpreston.com",
      "poems for the browser",
      "Version 1.0",
      "(c) C.M. Preston. All rights reserved."
    ]
  },
  "desktop": [
    {
      "type": "folder",
      "name": "Poems",
      "icon": "folder",
      "children": [
        {
          "type": "folder",
          "name": "Demos",
          "icon": "folder",
          "children": [
            { "type": "doc", "name": "what the door does", "path": "poems/demo-clickshift.html" },
            { "type": "doc", "name": "the footnote descends", "path": "poems/demo-footnotes.html" },
            { "type": "doc", "name": "tracked changes", "path": "poems/demo-trackchanges.html" }
          ]
        }
      ]
    },
    { "type": "trash", "icon": "trash" }
  ]
};
