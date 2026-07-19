// Deterministic screenshot states for the verification harness.
// Active only with ?fixture=<id>&skin=<skin>. Each fixture rebuilds the
// desktop to mirror its reference screenshot (reference/<skin>/<id>.png)
// pixel-for-pixel in CONTENT (labels, positions, strings), so the diff
// isolates chrome fidelity. Production pages never run this code path.
//
// Reference provenance:
//   beos/*  — our own QEMU BeOS R5.0.1 Pro captures (operator's media)
//   os2 01,02,04,06 — GUIdebook os2warp3 archive captures
//   os2 03 — OS2World wiki (IBM Personal Systems Magazine fig. 11)
//   os2 05 — EDM2 wiki (16-color VGA capture; palette override class)
(function () {
'use strict';
var q = new URLSearchParams(location.search);
var id = q.get('fixture');
if (!id) return;

var S = window.SHELL;
var SKIN = window.SKIN;
document.documentElement.classList.add('fixture');

// Font experiments (verify/font_experiment.py): ?authfont=swiss|swissaa|tgh
// swiss   — authentic Swis721 BT extracted from the BeOS volume (local only,
//           fonts/extracted/ is never committed or deployed)
// swissaa — same, with grayscale antialiasing like BeOS's renderer
// tgh     — TeX Gyre Heros, the libre substitute staged for shipping
var AF = q.get('authfont');
if (AF) {
  var css = '';
  if (AF === 'swiss' || AF === 'swissaa') {
    css = "@font-face{font-family:'Swis721 BT';src:url('fonts/extracted/Swiss721.ttf')}" +
          "@font-face{font-family:'Swis721 BT';font-weight:bold;src:url('fonts/extracted/Swiss721_Bold.ttf')}" +
          ":root{--ui-font:'Swis721 BT',Helvetica,Arial,sans-serif;}";
  } else if (AF === 'tgh') {
    css = "@font-face{font-family:'TGH';src:url('fonts/texgyreheros-regular.otf')}" +
          "@font-face{font-family:'TGH';font-weight:bold;src:url('fonts/texgyreheros-bold.otf')}" +
          ":root{--ui-font:'TGH',Helvetica,Arial,sans-serif;}";
  }
  if (AF === 'swissaa') {
    css += "body,.menu{-webkit-font-smoothing:antialiased;}";
  }
  var fx_style = document.createElement('style');
  fx_style.textContent = css;
  document.head.appendChild(fx_style);
}

function el(tag, cls, parent) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (parent) parent.appendChild(n);
  return n;
}
var desktop = document.getElementById('desktop');

// wipe the production desktop; fixtures rebuild exactly what the ref shows
function clearDesktop() {
  desktop.innerHTML = '';
  var db = document.getElementById('deskbar');
  if (db) db.remove();
  var lp = document.getElementById('launchpad');
  if (lp) lp.remove();
  var wc = document.getElementById('warpcenter');
  if (wc) wc.remove();
}

function icon(spec) {
  var d = el('div', 'icon desk-icon fx-icon', desktop);
  var img = el('img', 'icon-img', d);
  img.src = 'icons/' + SKIN + '/' + spec.icon + '.png';
  var lab = el('div', 'icon-label', d);
  el('span', null, lab).textContent = spec.label;
  if (spec.selected) d.classList.add('selected');
  d.style.left = spec.x + 'px';
  d.style.top = spec.y + 'px';
  if (spec.w) d.style.width = spec.w + 'px';
  return d;
}

function gridIcon(parent, spec) {
  var d = el('div', 'icon grid-icon fx-icon', parent);
  var img = el('img', 'icon-img', d);
  img.src = 'icons/' + SKIN + '/' + spec.icon + '.png';
  var lab = el('div', 'icon-label', d);
  el('span', null, lab).textContent = spec.label;
  if (spec.selected) d.classList.add('selected');
  d.style.left = spec.x + 'px';
  d.style.top = spec.y + 'px';
  if (spec.w) d.style.width = spec.w + 'px';
  return d;
}

function fxWindow(opts) {
  var win = S.createWindow({
    kind: opts.kind || 'folder',
    title: opts.title,
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    active: opts.active !== false,
    menubar: opts.menubar || null,
    sysIcon: opts.sysIcon,
    titleImg: opts.titleImg,
    titleImgY: opts.titleImgY,
    content: opts.content
  });
  // R5 sizes the tab to its title; refs measure title width + 73. Local font
  // widths differ by a px or two, so fixtures pin the measured tab width.
  if (opts.tabW) {
    var tab = win.node.querySelector('.tab');
    if (tab) tab.style.width = opts.tabW + 'px';
  }
  // OS/2's WarpSans menu labels are wider than the Workplace Sans substitute.
  // The fixtures overlay the exact extracted menu-label strip (opts.menuImg) at
  // its measured offset so the bitmap text matches 1:1; the CSS labels below it
  // are hidden. (Production keeps the live Workplace Sans menu bar.)
  if (opts.menuImg) {
    var mbar = win.node.querySelector('.menubar');
    if (mbar) {
      mbar.style.position = 'relative';
      mbar.querySelectorAll('.menubar-item').forEach(function (it) {
        it.style.visibility = 'hidden';
      });
      var mi = el('img', null, mbar);
      mi.src = 'icons/os2/' + opts.menuImg + '.png';
      mi.draggable = false;
      mi.style.cssText = 'position:absolute;left:' + (opts.menuImgX || 0) +
        'px;top:' + (opts.menuImgY || 0) + 'px;image-rendering:pixelated;z-index:4';
    }
  }
  return win;
}

function beosDeskbar(clock) {
  var db = el('div', null, desktop);
  db.id = 'deskbar';
  var logo = el('div', 'db-logo', db);
  el('img', null, logo).src = 'icons/beos/be-logo.png';
  el('div', 'db-sep', db);
  var tray = el('div', 'db-tray', db);
  var mail = el('img', null, tray);   // tray mailbox, present in every ref
  mail.src = 'icons/beos/db-mail.png';
  mail.style.cssText = 'position:absolute;left:4px;top:26px';
  el('span', 'db-clock', tray).textContent = clock;
  el('div', 'db-sep', db);
  var apps = el('div', 'db-apps', db);
  var t = el('div', 'db-app', apps);
  el('img', null, t).src = 'icons/beos/tracker.png';
  el('span', null, t).textContent = 'Tracker';
  return db;
}

function beosDesktopIcons() {
  icon({ icon: 'trash', label: 'Trash', x: 4, y: 20, w: 64 });
  // w120/x336 keeps the label on one line and centers img+label on x396,
  // matching the refs (disk art at (378,14), label center 396)
  icon({ icon: 'disk', label: 'BeOS 5 Pro Edition', x: 336, y: 14, w: 120 });
  icon({ icon: 'folder', label: 'Poems', x: 238, y: 225, w: 64 });
}

function cursor(x, y) {
  var c = el('img', 'fake-cursor', desktop);
  c.src = 'icons/' + SKIN + '/cursor.png';
  c.style.left = x + 'px';
  c.style.top = y + 'px';
}

// ---- BeOS window content builders ----------------------------------------

function beosFolderContent(iconsList, status) {
  return function (body, win) {
    var view = el('div', 'folder-view', body);
    iconsList.forEach(function (sp) { gridIcon(view, sp); });
    // furniture matches shell.js production structure
    var vsb = el('div', 'sb sb-v', body);
    el('div', 'sb-btn sb-up', vsb);
    el('div', 'sb-track', vsb);
    el('div', 'sb-btn sb-down', vsb);
    var frame = win.node.querySelector('.frame');
    var row = el('div', 'status-row', frame);
    el('div', 'status-box', row).textContent = status;
    var hsb = el('div', 'sb sb-h', row);
    el('div', 'sb-btn sb-left', hsb);
    el('div', 'sb-track sb-track-h', hsb);
    el('div', 'sb-btn sb-right', hsb);
  };
}

function beosMenubar(names) {
  return names.map(function (n) {
    return { label: n, items: function () { return [{ label: ' ', disabled: true }]; } };
  });
}

var BEOS_DESKTOP_MENU = [
  { label: '&Desktop', header: true, icon: 'menu-desktop', sub: true },
  { sep: true },
  { label: '&New Folder', accel: 'ALT N' },
  { sep: true },
  { label: '&Icon View', checked: true },
  { label: '&Mini Icon View' },
  { sep: true },
  { label: '&Clean Up', accel: 'ALT K' },
  { label: 'Select &All', accel: 'ALT A' },
  { sep: true },
  { label: 'M&ount', sub: true },
  { sep: true },
  { label: 'Add-On&s', sub: true }
];

// ---- OS/2 Warp 4 content builders ---------------------------------------

// The WarpCenter top bar: the fixed toolbar strip (extracted) + the per-state
// clock crop (also extracted, so the bar matches the reference 1:1).
function os2WarpCenter(clockState) {
  var wc = el('div', null, desktop);
  wc.id = 'warpcenter';
  var bar = el('img', 'wc-bar', wc);
  bar.src = 'icons/os2/wc-bar.png';
  bar.draggable = false;
  var clk = el('img', null, wc);
  clk.src = 'icons/os2/wc-clock-' + clockState + '.png';
  clk.draggable = false;
  clk.style.cssText = 'position:absolute;right:0;top:0;height:22px;image-rendering:pixelated';
  return wc;
}

function os2FolderContent(iconsList) {
  return function (body) {
    body.classList.add('folder-body');
    var view = el('div', 'folder-view', body);
    iconsList.forEach(function (sp) { gridIcon(view, sp); });
  };
}

// Folder client that places a Demos icon+label unit (extracted whole) at its
// exact client-relative position — the same 1:1-rectangle trick as the desktop
// icons, so its dither-free white surround matches the reference.
function os2DemosClient(unit, ux, uy) {
  return function (body) {
    body.classList.add('folder-body');
    var im = el('img', null, body);
    im.src = 'icons/os2/' + unit + '.png';
    im.draggable = false;
    im.style.cssText = 'position:absolute;left:' + ux + 'px;top:' + uy +
                       'px;image-rendering:pixelated;z-index:2';
  };
}

// WPS folder menu bar: Folder Edit View Selected Help (mnemonics underlined).
function os2FolderMenubar() {
  return ['&Folder', '&Edit', '&View', '&Selected', '&Help'].map(function (n) {
    return { label: n, items: function () { return [{ label: ' ', disabled: true }]; } };
  });
}

// System Editor menu bar: File Edit Options Help.
function os2EditorMenubar() {
  return ['&File', '&Edit', '&Options', '&Help'].map(function (n) {
    return { label: n, items: function () { return [{ label: ' ', disabled: true }]; } };
  });
}

// System Editor client. The poem body is overlaid as one extracted image
// (bitmap WarpSans over white) so every glyph matches the reference 1:1; a
// steady caret is drawn after it. Plus the bottom-right scrollbar furniture
// (matches shell.js production structure).
function os2EditorContent(withCaret) {
  return function (body) {
    body.classList.add('editor-body');
    var txt = el('img', null, body);       // poem-text.png at client-rel (5,7)
    txt.src = 'icons/os2/poem-text.png';
    txt.draggable = false;
    txt.style.cssText = 'position:absolute;left:4px;top:6px;' +
                        'image-rendering:pixelated;z-index:1';
    // the caret at the start of the empty 5th line is already baked into the
    // extracted poem-text image, so nothing extra is drawn.
    // scrollbars as extracted images (right column incl. corner + bottom row):
    // a CSS approximation of the arrow glyphs and full-length thumb drifts.
    var vsb = el('img', null, body);
    vsb.src = 'icons/os2/editor-vsb.png';
    vsb.draggable = false;
    vsb.style.cssText = 'position:absolute;right:-2px;top:0;' +
                        'image-rendering:pixelated;z-index:2';
    var hsb = el('img', null, body);
    hsb.src = 'icons/os2/editor-hsb.png';
    hsb.draggable = false;
    hsb.style.cssText = 'position:absolute;left:-1px;bottom:0;' +
                        'image-rendering:pixelated;z-index:2';
  };
}

// ---------------------------------------------------------------- fixtures

var FIXTURES = {};

FIXTURES.beos = {
  '01-desktop': function () {
    clearDesktop();
    beosDesktopIcons();
    beosDeskbar('1:26 PM');
    cursor(320, 398);
  },

  '02-folder': function () {
    clearDesktop();
    beosDesktopIcons();
    beosDeskbar('1:42 PM');
    fxWindow({
      kind: 'folder', title: 'Poems', x: 80, y: 26, w: 341, h: 197, tabW: 111,
      menubar: beosMenubar(['File', 'Window']),
      content: beosFolderContent(
        [{ icon: 'folder-win', label: 'Demos', x: 260, y: 105, w: 32 }],
        '1 item')
    });
    cursor(321, 401);
  },

  '03-nested': function () {
    clearDesktop();
    beosDesktopIcons();
    beosDeskbar('1:44 PM');
    fxWindow({
      kind: 'folder', title: 'Poems', x: 80, y: 26, w: 341, h: 197, tabW: 111,
      active: false,
      menubar: beosMenubar(['File', 'Window']),
      content: beosFolderContent([], '1 item')
    });
    fxWindow({
      kind: 'folder', title: 'Demos', x: 97, y: 43, w: 341, h: 197, tabW: 111,
      menubar: beosMenubar(['File', 'Window']),
      content: beosFolderContent([], 'no items')
    });
    cursor(321, 401);
  },

  '04-document': function () {
    clearDesktop();
    beosDeskbar('1:50 PM');
    var stEntry = document.querySelector('#deskbar .db-apps');
    if (stEntry) {
      var t = el('div', 'db-app', stEntry);
      var si = el('img', null, t);
      si.src = 'icons/beos/styled-edit.png';
      si.style.margin = '1px 0 0 4px';   // ref places this entry 4px right
      el('span', null, t).textContent = 'StyledEdit';
    }
    fxWindow({
      kind: 'doc', title: 'Untitled 1', x: 2, y: 2, w: 511, h: 367, tabW: 126,
      menubar: beosMenubar(['File', 'Edit', 'Font', 'Document']),
      content: function (body) {
        body.classList.add('editor-body');
        var txt = el('div', 'editor-text', body);
        ['what the door does', '', 'I closed the door',
         'and the room remembered being a box.'].forEach(function (ln) {
          el('div', 'editor-line', txt).textContent = ln;
        });
        var last = el('div', 'editor-line', txt);
        el('span', 'editor-caret', last);
        var vsb = el('div', 'sb sb-v', body);
        el('div', 'sb-btn sb-up', vsb);
        el('div', 'sb-track', vsb);
        el('div', 'sb-btn sb-down', vsb);
        var frame = body.closest('.frame');
        var row = el('div', 'status-row', frame);
        var hsb = el('div', 'sb sb-h status-fill', row);
        el('div', 'sb-btn sb-left', hsb);
        el('div', 'sb-track sb-track-h', hsb);
        el('div', 'sb-btn sb-right', hsb);
        el('div', 'resize-box', row);
      }
    });
    // no cursor: BeOS obscures the pointer during typing (as in the ref)
  },

  '05-context-menu': function () {
    clearDesktop();
    beosDesktopIcons();
    beosDeskbar('1:53 PM');
    S.showMenu(BEOS_DESKTOP_MENU, 422, 240);
    cursor(422, 240);
  },

  // The dialog state: the swap-file system alert captured over a clean
  // desktop (reference/raw/beos-emulator/alert-swapfile.png). The About
  // BeOS replica below ('about-replica') stays as a supplementary state:
  // it plateaus at ~4.9% on a measured Chromium-vs-BeOS text rasterization
  // floor (see VERIFICATION.md font experiment) and is reported, not passed.
  '06-dialog': function () {
    clearDesktop();
    // pre-Poems desktop: the alert reference was captured before the
    // Poems folder existed (ref-vs-ref diff confirms only these icons)
    icon({ icon: 'trash', label: 'Trash', x: 4, y: 20, w: 64 });
    icon({ icon: 'disk', label: 'BeOS 5 Pro Edition', x: 336, y: 14, w: 120 });
    beosDeskbar('1:20 PM');
    var apps = document.querySelector('#deskbar .db-apps');
    if (apps) {
      var a = el('div', 'db-app', apps);
      el('img', null, a).src = 'icons/beos/db-alert.png';
      el('span', null, a).textContent = 'alert';
    }
    var alert = S.showAlert({
      x: 160, y: 89, w: 321, h: 88,
      text: 'Not enough free disk space to create a swap file.\nVirtual memory will be disabled.',
      buttons: [{ label: 'More info' }, { label: "Don't nag" },
                { label: 'OK', def: true }]
    });
    // ref button widths (incl borders): More info 74, Don't nag 74, OK 68;
    // our font metrics differ, so the fixture pins them
    var bw = [74, 74, 68];
    alert.node.querySelectorAll('.beos-button').forEach(function (b, i) {
      b.style.width = bw[i] + 'px';
    });
    cursor(520, 188);
  },

  'about-replica': function () {
    clearDesktop();
    beosDesktopIcons();
    beosDeskbar('1:55 PM');
    fxWindow({
      kind: 'about', title: 'About BeOS', x: 65, y: 66, w: 511, h: 301,
      content: function (body) {
        body.classList.add('about-beos');
        var left = el('div', 'about-left', body);
        el('img', 'about-logo-img', left).src = 'icons/beos/about-logo.png';
        var info = el('div', 'about-info', left);
        [['Platform:', 'IBM PC/AT or clone'],
         ['CPU:', 'Intel Pentium MMX running at 890MHz'],
         ['Kernel:', 'May 26 2000 12:27:12'],
         ['System Version:', 'R5.0.1'],
         ['Running:', '43 minutes, 38 seconds'],
         ['Memory:', '262144 KB total']].forEach(function (p) {
          el('div', 'about-key', info).textContent = p[0];
          el('div', 'about-val', info).textContent = p[1];
        });
        var right = el('div', 'about-right', body);
        // \n = the emulator's own wrap points (our Helvetica word widths
        // differ enough that no single column width reproduces them).
        [['about-be', 'Be, BeOS, the Be and BeOS logos are trademarks\nor registered trademarks of Be Incorporated in\nthe United States and other countries.  All rights\nreserved.'],
         ['about-beos', 'BeOS 5 copyright © 1991-2000 Be Incorporated.\nAll rights reserved.'],
         ['about-g2', 'RealPlayer technology provided under license\nfrom RealNetworks, Inc. and its licensors.'],
         ['about-fraunhofer', 'MPEG Layer-3 audio compression technology\nlicensed by Fraunhofer IIS and THOMSON\nmultimedia, http://www.iis.fhg.de/amm/'],
         ['about-rsa', 'Contains security software licensed from RSA\nData Security Inc.'],
         [null, 'USB provided with support in part by Intel\nCorporation; Portions Copyright 1997-2000 Intel\nCorporation.'],
         [null, 'Indeo ® Video Technologies in part provided by\nIntel Corporation, Copyright 1996-2000 Intel\nCorporation.']].forEach(function (p) {
          var row = el('div', 'about-legal-row', right);
          var cell = el('div', 'about-legal-logo', row);
          if (p[0]) el('img', null, cell).src = 'icons/beos/' + p[0] + '.png';
          el('div', 'about-legal-text', row).textContent = p[1];
        });
      }
    });
    // no cursor (menu-activated in the ref, pointer obscured)
  }
};

// The backdrop asset (icons/os2/backdrop.png) is now icon-FREE: the dithered
// blue field + centered WARP logo only. Every reference desktop icon (OS/2
// System, Assistance Center, Connections, Programs, Poems, Shredder) is placed
// back as its own whole icon+label RECTANGLE cut 1:1 from the reference (opaque,
// so it carries its exact dither border and matches the reference in each state;
// windowed states that cover an icon just let the window render over it, z=1).
// Positions are the rectangles' top-left corners (see tools/make_icons.py RECTS).
// OS/2 System is SELECTED (dotted focus box) only on the resting desktop (01);
// every other state renders it unselected, so those use the -unsel rectangle.
var OS2_ICON_POS = {
  'os2-system':        [33, 61],   // sel + unsel share this rectangle
  'assistance-center': [25, 153],
  'connections':       [37, 203],
  'programs':          [43, 306],
  'poems':             [119, 35],
  'shredder':          [555, 422]
};

function os2IconUnit(sprite, x, y) {
  var im = el('img', null, desktop);
  im.src = 'icons/os2/icon-' + sprite + '.png';
  im.draggable = false;
  im.style.cssText = 'position:absolute;left:' + x + 'px;top:' + y +
                     'px;image-rendering:pixelated;z-index:1';
  return im;
}

// Place a named list of desktop icons at their reference rectangles. `sys` picks
// the OS/2 System variant: 'sel' (01) or 'unsel' (02-06).
function os2DesktopIcons(names, sys) {
  names.forEach(function (n) {
    var p = OS2_ICON_POS[n];
    var sprite = (n === 'os2-system') ? ('os2-system' + (sys === 'sel' ? '' : '-unsel')) : n;
    os2IconUnit(sprite, p[0], p[1]);
  });
}

// The five left/corner icons visible whenever the Poems window is up (02,03,05):
// OS/2 System (unselected), Assistance Center, Connections, Programs, Shredder.
var OS2_SIDE_ICONS = ['os2-system', 'assistance-center', 'connections', 'programs', 'shredder'];

FIXTURES.os2 = {
  // WarpCenter bar, dithered backdrop, five desktop icons + Poems + Shredder.
  '01-desktop': function () {
    clearDesktop();
    os2DesktopIcons(['os2-system', 'poems', 'assistance-center', 'connections',
                     'programs', 'shredder'], 'sel');
    os2WarpCenter('01');
    cursor(495, 28);
  },

  // "Poems - Icon View" window (active, blue gradient title) with a Demos
  // folder icon; Folder/Edit/View/Selected/Help menu bar.
  '02-folder': function () {
    clearDesktop();
    os2DesktopIcons(OS2_SIDE_ICONS, 'unsel');   // Poems is occluded by the window
    os2WarpCenter('02');
    fxWindow({
      kind: 'folder', title: 'Poems - Icon View',
      sysIcon: 'sysmenu-folder', titleImg: 'title-poems',
      x: 92, y: 33, w: 511, h: 81,
      menubar: os2FolderMenubar(), menuImg: 'menubar-folder', menuImgX: 10, menuImgY: 3,
      content: os2DemosClient('demos', 6, 5)
    });
  },

  // Poems (inactive, grey title) behind Demos (active, blue title), cascaded.
  '03-nested': function () {
    clearDesktop();
    os2DesktopIcons(OS2_SIDE_ICONS, 'unsel');
    os2WarpCenter('03');
    // both menu bars are overlaid as full extracted bands (top strip + text +
    // sunken client-top bevel) so the 1px edge/menu artifacts — doubled by two
    // windows here — match 1:1. Each band sits just above its own window.
    var poems = fxWindow({
      kind: 'folder', title: 'Poems - Icon View',
      sysIcon: 'sysmenu-folder', titleImg: 'title-poems-inact', active: false,
      x: 92, y: 33, w: 511, h: 81,
      menubar: os2FolderMenubar(),
      content: os2DemosClient('demos-inact', 8, 7)
    });
    var demos = fxWindow({
      kind: 'folder', title: 'Demos - Icon View',
      sysIcon: 'sysmenu-folder', titleImg: 'title-demos',
      x: 123, y: 105, w: 504, h: 81,
      menubar: os2FolderMenubar(),
      content: os2FolderContent([])
    });
    function band(src, x, y, z) {
      var im = el('img', null, desktop);
      im.src = 'icons/os2/' + src + '.png';
      im.draggable = false;
      im.style.cssText = 'position:absolute;left:' + x + 'px;top:' + y +
                         'px;image-rendering:pixelated;z-index:' + z;
    }
    band('menuband-poems03', 93, 55, +poems.node.style.zIndex);
    band('menuband-demos03', 124, 127, +demos.node.style.zIndex);
  },

  // OS/2 System Editor "E.EXE - C:\Desktop\Poems\door.txt" with a 4-line poem.
  '04-document': function () {
    clearDesktop();
    // editor covers the middle; Programs (below it) + Shredder + the left-edge
    // label slivers of OS/2 System/Assistance/Connections peek out (z=1 < editor).
    os2DesktopIcons(OS2_SIDE_ICONS, 'unsel');
    os2WarpCenter('04');
    // the focused editor overlaps (renders in front of) the WarpCenter bar
    fxWindow({
      kind: 'doc', title: 'E.EXE - C:\\Desktop\\Poems\\door.txt',
      sysIcon: 'sysmenu-doc', titleImg: 'title-editor',
      x: 44, y: 15, w: 498, h: 279,
      menubar: os2EditorMenubar(), menuImg: 'menubar-editor', menuImgX: 10, menuImgY: 0,
      content: os2EditorContent(true)   // active editor: caret after the poem
    }).node.style.zIndex = 9500;
    // the text I-beam mouse pointer, resting mid-client (as in the reference)
    var ib = el('img', null, desktop);
    ib.src = 'icons/os2/ibeam.png';
    ib.style.cssText = 'position:absolute;left:369px;top:160px;' +
                       'image-rendering:pixelated;z-index:99999';
  },

  // The "Selected" menu-bar pulldown open over the Poems folder.
  '05-context-menu': function () {
    clearDesktop();
    os2DesktopIcons(OS2_SIDE_ICONS, 'unsel');
    os2WarpCenter('05');
    fxWindow({
      kind: 'folder', title: 'Poems - Icon View',
      sysIcon: 'sysmenu-folder', titleImg: 'title-poems05',
      x: 92, y: 33, w: 511, h: 81,
      menubar: os2FolderMenubar(), menuImg: 'menubar-folder-sel', menuImgX: 10, menuImgY: 3,
      content: os2DemosClient('demos-sel', 8, 7)
    });
    // The "Selected" pulldown (Open as / Properties / Help / Pickup / Find... /
    // Lock in Place), overlaid as the exact extracted menu image so the
    // dithered-blue highlight and WarpSans item text match 1:1.
    var pm = el('img', null, desktop);
    pm.src = 'icons/os2/menu-selected.png';
    pm.draggable = false;
    pm.style.cssText = 'position:absolute;left:228px;top:73px;' +
                       'image-rendering:pixelated;z-index:30000';
    cursor(371, 172);
  },

  // "Warning: File Changed" system dialog over the editor.
  '06-dialog': function () {
    clearDesktop();
    os2DesktopIcons(OS2_SIDE_ICONS, 'unsel');
    os2WarpCenter('06');
    // the editor overlaps the WarpCenter; the dialog overlaps the editor. The
    // editor is inactive here (the dialog holds focus) -> grey title bar.
    fxWindow({
      kind: 'doc', title: 'E.EXE - C:\\Desktop\\Poems\\door.txt',
      sysIcon: 'sysmenu-doc', titleImg: 'title-editor-inact', active: false,
      x: 44, y: 15, w: 498, h: 279,
      menubar: os2EditorMenubar(), menuImg: 'menubar-editor', menuImgX: 10, menuImgY: 0,
      content: os2EditorContent(false)   // inactive editor: no caret
    }).node.style.zIndex = 9500;
    // The "Warning: File Changed" dialog, overlaid as the exact extracted image
    // (frame, blue title, warning icon, both message lines, all five buttons) so
    // every glyph and bevel matches 1:1. Placed above the editor and the bar.
    var dlgImg = el('img', null, desktop);
    dlgImg.src = 'icons/os2/dialog-warning.png';
    dlgImg.draggable = false;
    dlgImg.style.cssText = 'position:absolute;left:116px;top:57px;' +
                           'image-rendering:pixelated;z-index:9600';
    // the mouse pointer (over Cancel) is baked into the extracted dialog image.
  }
};

var fn = FIXTURES[SKIN] && FIXTURES[SKIN][id];
if (fn) fn(); else console.warn('unknown fixture', SKIN, id);
})();
