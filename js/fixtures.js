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
    content: opts.content
  });
  // R5 sizes the tab to its title; refs measure title width + 73. Local font
  // widths differ by a px or two, so fixtures pin the measured tab width.
  if (opts.tabW) {
    var tab = win.node.querySelector('.tab');
    if (tab) tab.style.width = opts.tabW + 'px';
  }
  return win;
}

function beosDeskbar(clock) {
  var db = el('div', null, desktop);
  db.id = 'deskbar';
  var logo = el('div', 'db-logo', db);
  el('img', null, logo).src = 'icons/beos/be-logo.png';
  var tray = el('div', 'db-tray', db);
  var mail = el('img', null, tray);   // tray mailbox, present in every ref
  mail.src = 'icons/beos/db-mail.png';
  mail.style.cssText = 'position:absolute;left:6px;top:26px';
  el('span', 'db-clock', tray).textContent = clock;
  var apps = el('div', 'db-apps', db);
  var t = el('div', 'db-app', apps);
  el('img', null, t).src = 'icons/beos/tracker.png';
  el('span', null, t).textContent = 'Tracker';
  return db;
}

function beosDesktopIcons() {
  icon({ icon: 'trash', label: 'Trash', x: 4, y: 20, w: 64 });
  icon({ icon: 'disk', label: 'BeOS 5 Pro Edition', x: 352, y: 14, w: 90 });
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

// ---- OS/2 content builders ----------------------------------------------

function os2LaunchpadAt(x, y) {
  var lp = el('div', null, desktop);
  lp.id = 'launchpad';
  lp.style.left = x + 'px';
  lp.style.top = y + 'px';
  lp.style.transform = 'none';
  lp.style.bottom = 'auto';
  var textcol = el('div', 'lp-textcols', lp);
  [['Lockup', 'Find'], ['Shut down', 'Window list']].forEach(function (col, ci) {
    var c = el('div', 'lp-col', textcol);
    col.forEach(function (t, ti) {
      var b = el('button', 'lp-textbtn', c);
      var u = [['&Lockup', '&Find'], ['Shut &down', 'Window &list']][ci][ti];
      var i = u.indexOf('&');
      b.appendChild(document.createTextNode(u.slice(0, i)));
      el('u', null, b).textContent = u[i + 1];
      b.appendChild(document.createTextNode(u.slice(i + 2)));
    });
  });
  var icons = el('div', 'lp-icons', lp);
  ['lp-printer', 'lp-floppy', 'lp-shell', 'lp-info', 'lp-shredder'].forEach(function (ic) {
    var cell = el('div', 'lp-cell', icons);
    el('button', 'lp-drawer', cell);
    var b = el('button', 'lp-iconbtn', cell);
    el('img', null, b).src = 'icons/os2/' + ic + '.png';
  });
  return lp;
}

function os2FolderContent(iconsList) {
  return function (body) {
    body.classList.add('folder-body');
    var view = el('div', 'folder-view', body);
    iconsList.forEach(function (sp) { gridIcon(view, sp); });
  };
}

function os2EditorContent(lines, caretLine) {
  return function (body) {
    body.classList.add('editor-body');
    var txt = el('div', 'editor-text', body);
    lines.forEach(function (ln, i) {
      var row = el('div', 'editor-line', txt);
      row.textContent = ln;
      if (i === caretLine) el('span', 'editor-caret', row);
    });
    var vsb = el('div', 'sb sb-v', body);
    el('div', 'sb-btn sb-up', vsb);
    el('div', 'sb-track', vsb);
    el('div', 'sb-btn sb-down', vsb);
    var hsb = el('div', 'sb sb-h', body);
    el('div', 'sb-btn sb-left', hsb);
    el('div', 'sb-track sb-track-h', hsb);
    el('div', 'sb-btn sb-right', hsb);
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

  '06-dialog': function () {
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

// OS/2 System Setup window contents (GUIdebook 02-folder ref), grid order.
var OS2_SS_ICONS = [
  ['System Clock', 20], ['Keyboard', 88], ['Selective Install', 150],
  ['Mouse', 246], ['Device Driver Install', 300], ['System', 420],
  ['Country', 20], ['Spooler', 88], ['Add Programs', 150],
  ['Create Utility Diskettes', 246], ['Selective Uninstall', 340], ['Sound', 430],
  ['Font Palette', 20], ['Mixed Color Palette', 100],
  ['Solid Color Palette', 210], ['Scheme Palette', 310], ['Power', 400]
];

FIXTURES.os2 = {
  '01-desktop': function () {
    clearDesktop();
    icon({ icon: 'printer', label: 'HP DeskJet Plus', x: 40, y: 17, w: 78 });
    icon({ icon: 'dos-programs', label: 'DOS Programs', x: 190, y: 20, w: 74 });
    icon({ icon: 'multimedia', label: 'Multimedia', x: 262, y: 20, w: 66 });
    icon({ icon: 'os2-system', label: 'OS/2 System', x: 46, y: 140, w: 70 });
    icon({ icon: 'information', label: 'Information', x: 46, y: 198, w: 66 });
    icon({ icon: 'templates', label: 'Templates', x: 48, y: 414, w: 64 });
    os2LaunchpadAt(119, 389);
    cursor(296, 270);
  },

  '02-folder': function () {
    clearDesktop();
    var row = 0;
    var iconsList = OS2_SS_ICONS.map(function (pair, i) {
      if (i === 6 || i === 12) row++;
      return { icon: 'ss-' + i, label: pair[0], x: pair[1], y: 6 + row * 62,
               selected: pair[0] === 'Power' };
    });
    fxWindow({
      kind: 'folder', title: 'System Setup - Icon View',
      sysIcon: 'sysmenu-folder',
      x: 0, y: 0, w: 512, h: 210,
      content: os2FolderContent(iconsList)
    });
  },

  '03-nested': function () {
    clearDesktop();
    document.documentElement.classList.add('fx-os2world');
    icon({ icon: 'p2p2', label: 'P2P/2', x: 822, y: 24, w: 56 });
    fxWindow({
      kind: 'folder', title: 'IBM Information Superhighway - Icon View',
      sysIcon: 'sysmenu-folder', active: false,
      x: 8, y: 8, w: 812, h: 140,
      content: os2FolderContent([
        { icon: 'compuserve', label: 'CompuServe', x: 30, y: 40, w: 84 },
        { icon: 'hyperaccess', label: 'HyperACCESS Lite', x: 140, y: 40, w: 90 },
        { icon: 'ibm-internet', label: 'IBM Internet Connection for OS/2',
          x: 290, y: 40, w: 124, selected: true }
      ])
    });
    fxWindow({
      kind: 'folder', title: 'IBM Internet Connection for OS/2 - Icon View',
      sysIcon: 'sysmenu-folder',
      x: 46, y: 160, w: 826, h: 234,
      content: os2FolderContent([
        { icon: 'app-templates', label: 'Application Templates', x: 80, y: 40, w: 92 },
        { icon: 'internet-utils', label: 'Internet Utilities', x: 230, y: 40, w: 80 },
        { icon: 'ultimedia', label: "Ultimedia Mail/2 'Lite'", x: 340, y: 40, w: 92 },
        { icon: 'newsreader', label: 'NewsReader/2', x: 480, y: 40, w: 84 },
        { icon: 'gopher', label: 'Gopher', x: 590, y: 40, w: 60 },
        { icon: 'retrieve', label: 'Retrieve Software Updates', x: 700, y: 40, w: 96 },
        { icon: 'intro-inet', label: 'Introduction to the IBM Internet Connection', x: 120, y: 130, w: 140 },
        { icon: 'readme', label: 'READ ME FIRST', x: 330, y: 130, w: 96 },
        { icon: 'dialer', label: 'IBM Internet Dialer', x: 460, y: 130, w: 80 },
        { icon: 'customer-svc', label: 'IBM Internet Customer Services', x: 620, y: 130, w: 110 }
      ])
    });
  },

  '04-document': function () {
    clearDesktop();
    fxWindow({
      kind: 'doc', title: 'OS/2 System Editor - Untitled',
      sysIcon: 'sysmenu-doc',
      x: 0, y: 0, w: 497, h: 294,
      menubar: [
        { label: '&File', items: function () { return []; } },
        { label: '&Edit', items: function () { return []; } },
        { label: '&Options', items: function () { return []; } },
        { label: '&Help', items: function () { return []; } }
      ],
      content: os2EditorContent(['This is a text editor test.'], 0)
    });
  },

  '05-context-menu': function () {
    clearDesktop();
    document.documentElement.classList.add('fx-edm2');
    fxWindow({
      kind: 'folder', title: 'TCP/IP - Icon View',
      sysIcon: 'sysmenu-folder',
      x: 0, y: 0, w: 512, h: 245,
      content: os2FolderContent([
        { icon: 'tcp-network', label: 'network dialer', x: 120, y: 8, w: 80 },
        { icon: 'tcp-webx', label: 'WebExplorer', x: 180, y: 8, w: 78 },
        { icon: 'tcp-news', label: 'NewsReader/2', x: 252, y: 8, w: 84 },
        { icon: 'tcp-gopher', label: 'Gopher', x: 340, y: 8, w: 56 },
        { icon: 'tcp-telnet5250', label: '5250 Telnet', x: 396, y: 8, w: 66 },
        { icon: 'tcp-tcpip', label: 'to TCP/IP', x: 120, y: 90, w: 64 },
        { icon: 'tcp-ultimedia', label: "Ultimedia Mail/2 'Lite'", x: 208, y: 90, w: 76 },
        { icon: 'tcp-rexx', label: 'REXX Sockets API', x: 288, y: 90, w: 90, selected: true },
        { icon: 'tcp-rexxftp', label: 'REXX FTP API', x: 380, y: 90, w: 80 },
        { icon: 'tcp-utils', label: 'TCP/IP Utilities', x: 452, y: 90, w: 60 },
        { icon: 'tcp-slip', label: 'S/Windows /IP Access', x: 120, y: 172, w: 76 },
        { icon: 'tcp-apptempl', label: 'Application Templates', x: 200, y: 172, w: 86 },
        { icon: 'tcp-vxftp', label: 'VxFTP v0.42', x: 300, y: 172, w: 70 },
        { icon: 'tcp-telnet', label: 'Telnet', x: 380, y: 172, w: 50 }
      ])
    });
    S.showMenu([
      { label: '&Open', sub: true, def: true },
      { label: '&Settings' },
      { label: 'Open pa&rent', hover: true },
      { label: 'Re&fresh now' },
      { label: '&Help', sub: true },
      { sep: true },
      { label: 'Create a&nother', sub: true },
      { label: '&Copy...' },
      { label: '&Move...' },
      { label: 'Create s&hadow...' },
      { label: 'Dele&te...' },
      { sep: true },
      { label: 'Pick&up' }
    ], 0, 17);
    cursor(112, 73);
  },

  '06-dialog': function () {
    clearDesktop();
    fxWindow({
      kind: 'about', title: 'System Editor - Product information',
      sysIcon: 'sysmenu-doc',
      x: 0, y: 0, w: 351, h: 164,
      content: function (body, win) {
        body.classList.add('about-os2');
        var row = el('div', 'about-row', body);
        el('img', 'about-icon', row).src = 'icons/os2/about.png';
        var lines = el('div', 'about-lines', row);
        ['Operating System/2', 'System Editor', 'Version 2.1',
         '(c) Copyright IBM Corp. 1981, 1992.',
         'All rights reserved.'].forEach(function (t) {
          el('div', null, lines).textContent = t;
        });
        var btnrow = el('div', 'about-btnrow', body);
        var ok = el('button', 'os2-button default-button', btnrow);
        ok.textContent = 'OK';
      }
    });
  }
};

var fn = FIXTURES[SKIN] && FIXTURES[SKIN][id];
if (fn) fn(); else console.warn('unknown fixture', SKIN, id);
})();
