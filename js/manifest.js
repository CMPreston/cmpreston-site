// The one hand-maintained content file. Edit this when adding poems.
// A folder entry: { type:'folder', name, icon, children:[...] }
// A document entry: { type:'doc', name, path } — path points at a compiled
// poem page copied into poems/ by tools/sync_poems.py (source of truth:
// ~/dev/cmpreston/dist/, never edited here).
// Special types: 'switcher' (skin toggle control), 'trash' (decorative).
//
// Content as of 2026-09-06: the published record, one Poems folder.
// Sources are the frozen as-published snapshots in the vault
// (create/oslo/works/_published/), one per acceptance. The four tracked-changes
// pieces are the HTML re-renders (trackchanges tool, balloon markup), approved
// by P 2026-09-06 over the journal page images; the image snapshots stay in
// the vault as the record.
window.MANIFEST = {
  "site": {
    "title": "C.M. Preston",
    "contact": "cmpreston0@gmail.com",
    "about_lines": [
      "cmpreston.com",
      "poems for the browser",
      "Version 1.4",
      "(c) C.M. Preston. All rights reserved."
    ]
  },
  "desktop": [
    {
      "type": "folder",
      "name": "Poems",
      "icon": "folder",
      "children": [
        { "type": "doc", "name": "This causes seizures", "path": "poems/this-causes-seizures-ethel-2020.html" },
        { "type": "doc", "name": "from the flood", "path": "poems/from-the-flood-meat-for-tea-2020.html" },
        { "type": "doc", "name": "stern promises", "path": "poems/stern-promises-meat-for-tea-2020.html" },
        { "type": "doc", "name": "My friends getting Botox", "path": "poems/my-friends-getting-botox-lucky-jefferson-2020.html" },
        { "type": "doc", "name": "Untitled", "path": "poems/untitled-better-than-starbucks-2020.html" },
        { "type": "doc", "name": "Our Love was a Hazardous Spill", "path": "poems/our-love-was-a-hazardous-spill-html-punt-volat-2020.html" },
        { "type": "doc", "name": "Track Changes #5", "path": "poems/track-changes-5-just-html-dream-pop-press-2020.html" },
        { "type": "doc", "name": "Track Changes #6", "path": "poems/track-changes-6-i-have-felt-this-way-for-a-while-html-dream-pop-press-2020.html" },
        { "type": "doc", "name": "Track Changes #6 (reprise)", "path": "poems/track-changes-6-reprise-i-have-felt-this-way-for-a-while-html-dream-pop-press-2020.html" }
      ]
    },
    { "type": "trash", "icon": "trash" }
  ]
};
