// cmpreston.com desktop shell — vanilla JS, no dependencies, no build step.
// Two skins: 'beos' (BeOS R4/R5 era) and 'os2' (OS/2 Warp 4, 1996).
// Structure lives here; every color/metric lives in css/<skin>.css.
(function () {
'use strict';

var SKIN = window.SKIN;
var M = window.MANIFEST;
var desktop = document.getElementById('desktop');
var zTop = 10;
var windows = [];
var openMenus = [];
var iconSeq = 0;

// ---------------------------------------------------------------- utilities

function el(tag, cls, parent) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (parent) parent.appendChild(n);
  return n;
}

// '&Open' -> O underlined (menu mnemonics, drawn everywhere in OS/2)
function mnemonic(node, label) {
  var i = label.indexOf('&');
  if (i === -1) { node.textContent = label; return; }
  node.appendChild(document.createTextNode(label.slice(0, i)));
  el('u', null, node).textContent = label[i + 1];
  node.appendChild(document.createTextNode(label.slice(i + 2)));
}

function iconPath(name) { return 'icons/' + SKIN + '/' + name + '.png'; }

// Touch devices get the linear list; narrow desktop windows stay desktop —
// 640x480 was a period-authentic desktop, after all.
function isMobile() {
  return matchMedia('(pointer: coarse)').matches &&
         matchMedia('(max-width: 1024px)').matches;
}

// ---------------------------------------------------------------- skin text

function switcherName() { return SKIN === 'beos' ? 'OS/2 Warp' : 'BeOS'; }
function trashName()    { return SKIN === 'beos' ? 'Trash' : 'Shredder'; }
function itemName(item) {
  if (item.type === 'switcher') return switcherName();
  if (item.type === 'trash') return trashName();
  return item.name;
}
function itemIcon(item) {
  if (item.type === 'doc') return 'doc';
  return item.icon || (item.type === 'folder' ? 'folder' : item.type);
}
function folderTitle(item) {
  return SKIN === 'os2' ? itemName(item) + ' - Icon View' : itemName(item);
}

// ---------------------------------------------------------------- menus

function closeMenus(fromLevel) {
  fromLevel = fromLevel || 0;
  while (openMenus.length > fromLevel) openMenus.pop().remove();
}

// items: [{label, action, sub, disabled, checked, def, sep, header, icon,
//          accel, hover}]
// def: default/bold item (OS/2 draws the default action bold)
// header: BeOS menu title row (icon + bold label + open-parent arrow)
// checked: leading checkmark; hover: render highlighted (fixture staging)
// accel 'ALT N' renders the BeOS ALT keycap; other accels render as text
function showMenu(items, x, y, level) {
  level = level || 0;
  closeMenus(level);
  var m = el('div', 'menu', desktop);
  m.style.zIndex = 30000 + level;
  items.forEach(function (it) {
    if (it.sep) { el('div', 'menu-sep', m); return; }
    var row = el('div', 'menu-item' + (it.disabled ? ' disabled' : '') +
                        (it.def ? ' default' : '') +
                        (it.header ? ' header' : '') +
                        (it.hover ? ' forced-hover' : ''), m);
    if (SKIN === 'beos') el('span', 'mi-check' + (it.checked ? ' checked' : ''), row);
    if (it.icon) {
      var mi = el('img', 'mi-icon', row);
      mi.src = iconPath(it.icon);
    }
    var lab = el('span', 'menu-label', row);
    mnemonic(lab, it.label);
    if (it.sub) el('span', 'menu-arrow', row);
    if (it.accel) {
      var acc = el('span', 'menu-accel', row);
      if (it.accel.indexOf('ALT ') === 0) {
        acc.className += ' accel-alt';
        el('img', 'altcap', acc).src = iconPath('menu-altkey');
        el('span', 'accel-letter', acc).textContent = it.accel.slice(4);
      } else {
        acc.textContent = it.accel;
      }
    }
    row.addEventListener('mouseenter', function () {
      if (it.sub) {
        var r = row.getBoundingClientRect();
        showMenu(it.sub, r.right - 2, r.top - 2, level + 1);
      } else {
        closeMenus(level + 1);
      }
    });
    if (!it.disabled && !it.sub) {
      row.addEventListener('mouseup', function (e) {
        e.stopPropagation();
        closeMenus(0);
        if (it.action) it.action();
      });
      row.addEventListener('click', function (e) { e.stopPropagation(); });
    }
  });
  // clamp into viewport
  m.style.left = '0px'; m.style.top = '0px';
  var mw = m.offsetWidth, mh = m.offsetHeight;
  if (x + mw > innerWidth) x = Math.max(0, innerWidth - mw - 1);
  if (y + mh > innerHeight) y = Math.max(0, innerHeight - mh - 1);
  m.style.left = x + 'px';
  m.style.top = y + 'px';
  openMenus.push(m);
  return m;
}

document.addEventListener('mousedown', function (e) {
  if (!e.target.closest('.menu')) closeMenus(0);
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') closeMenus(0);
});

// ---------------------------------------------------------------- windows

function focusWindow(win) {
  windows.forEach(function (w) { w.node.classList.remove('win-active'); });
  win.node.classList.add('win-active');
  win.node.style.zIndex = ++zTop;
}

function closeWindow(win) {
  var i = windows.indexOf(win);
  if (i !== -1) windows.splice(i, 1);
  win.node.remove();
  var last = windows[windows.length - 1];
  if (last) focusWindow(last);
}

function makeDraggable(win, handle) {
  handle.addEventListener('pointerdown', function (e) {
    if (e.button !== 0) return;
    if (e.target.closest('.tab-close,.tab-zoom,.tb-btn,.sysmenu')) return;
    var sx = e.clientX, sy = e.clientY;
    var ox = win.node.offsetLeft, oy = win.node.offsetTop;
    function move(ev) {
      win.node.style.left = Math.round(ox + ev.clientX - sx) + 'px';
      win.node.style.top = Math.max(0, Math.round(oy + ev.clientY - sy)) + 'px';
    }
    function up() {
      removeEventListener('pointermove', move);
      removeEventListener('pointerup', up);
    }
    addEventListener('pointermove', move);
    addEventListener('pointerup', up);
    e.preventDefault();
  });
}

var cascade = { n: 0 };
function nextPos(w, h) {
  var base = SKIN === 'beos' ? { x: 120, y: 60 } : { x: 140, y: 70 };
  var p = { x: base.x + cascade.n * 24, y: base.y + cascade.n * 22 };
  cascade.n = (cascade.n + 1) % 8;
  if (p.x + w > innerWidth) p.x = Math.max(8, innerWidth - w - 16);
  if (p.y + h > innerHeight) p.y = Math.max(8, innerHeight - h - 16);
  return p;
}

// opts: {kind, title, w, h, x, y, content(bodyEl, win), menubar:[..],
//        active (default true; false renders unfocused, used by fixtures)}
function createWindow(opts) {
  var win = { kind: opts.kind, title: opts.title, item: opts.item || null };
  var node = win.node = el('div', 'win win-' + opts.kind, desktop);
  var w = opts.w, h = opts.h;
  var pos = (opts.x != null) ? { x: opts.x, y: opts.y } : nextPos(w, h);
  node.style.left = pos.x + 'px';
  node.style.top = pos.y + 'px';
  node.style.width = w + 'px';

  var handle, inner;
  if (SKIN === 'beos') {
    // Yellow tab sits above the framed body; tab: close box | title | zoom box.
    var tab = el('div', 'tab', node);
    el('div', 'tab-close', tab).addEventListener('click', function () { closeWindow(win); });
    el('div', 'tab-title', tab).textContent = opts.title;
    el('div', 'tab-zoom', tab);
    inner = el('div', 'frame', node);
    handle = tab;
  } else {
    // OS/2 Warp 4: full-width dithered-blue title bar: sysmenu folder/doc icon |
    // title text | hide+maximize button cluster (a sprite). The fixtures pass
    // opts.titleImg to overlay the exact extracted title-bar rectangle (the
    // per-pixel dither and baked title text are un-CSS-able to the 2% bar);
    // production omits it and renders the CSS gradient below.
    var tb = el('div', 'titlebar', node);
    var sys = el('button', 'sysmenu', tb);
    el('img', null, sys).src = iconPath(opts.sysIcon || 'sysmenu-' + opts.kind);
    var tt = el('div', 'title', tb);
    tt.textContent = opts.title;
    var btns = el('span', 'tb-btns', tb);
    el('img', null, btns).src = iconPath('titlebtns');
    if (opts.titleImg) {
      var ti = el('img', 'title-img', tb);
      ti.src = iconPath(opts.titleImg);
      ti.draggable = false;
      if (opts.titleImgY != null) ti.style.top = opts.titleImgY + 'px';
    }
    sys.addEventListener('click', function (e) {
      e.stopPropagation();
      var r = sys.getBoundingClientRect();
      showMenu(sysMenuItems(win), r.left, r.bottom);
    });
    sys.addEventListener('dblclick', function () { closeMenus(0); closeWindow(win); });
    inner = node;
    handle = tb;
  }

  if (opts.menubar) buildMenubar(inner, opts.menubar, win);
  var body = el('div', 'win-body', inner);
  if (h != null) body.style.height = h + 'px';
  opts.content(body, win);
  if (SKIN === 'beos') el('div', 'resize-corner', inner);

  node.addEventListener('pointerdown', function () { focusWindow(win); }, true);
  makeDraggable(win, handle);
  windows.push(win);
  if (opts.active !== false) focusWindow(win);
  return win;
}

// BeOS Tracker-style furniture: right scrollbar (double arrows both ends)
// plus a bottom row holding the item-count box and horizontal scrollbar.
function beosFolderFurniture(body, win, statusText) {
  var vsb = el('div', 'sb sb-v', body);
  el('div', 'sb-btn sb-up', vsb);
  var tr = el('div', 'sb-track', vsb);
  el('div', 'sb-btn sb-down', vsb);
  var row = el('div', 'status-row', win.node.querySelector('.frame') || win.node);
  var sbox = el('div', 'status-box', row);
  sbox.textContent = statusText;
  var hsb = el('div', 'sb sb-h', row);
  el('div', 'sb-btn sb-left', hsb);
  el('div', 'sb-track sb-track-h', hsb);
  el('div', 'sb-btn sb-right', hsb);
  return { vsb: vsb, row: row };
}

function sysMenuItems(win) {
  return [
    { label: '&Close', accel: 'Alt+F4', def: true, action: function () { closeWindow(win); } },
    { sep: true },
    { label: 'Window &list', accel: 'Ctrl+Esc', disabled: true }
  ];
}

function buildMenubar(parent, menus, win) {
  var bar = el('div', 'menubar', parent);
  menus.forEach(function (mdef) {
    var item = el('div', 'menubar-item', bar);
    mnemonic(item, mdef.label);
    item.addEventListener('mousedown', function (e) {
      e.stopPropagation();
      var r = item.getBoundingClientRect();
      showMenu(mdef.items(win), r.left, r.bottom);
    });
  });
  return bar;
}

// ---------------------------------------------------------------- icons

// makeIcon renders one icon+label unit, used on desktop and in folder windows.
function makeIcon(item, parent, cls) {
  var d = el('div', 'icon ' + cls, parent);
  d.dataset.icon = itemIcon(item);
  var img = el('img', 'icon-img', d);
  img.src = iconPath(itemIcon(item));
  img.alt = '';
  img.draggable = false;
  var lab = el('div', 'icon-label', d);
  el('span', null, lab).textContent = itemName(item);
  d.tabIndex = 0;
  d.addEventListener('mousedown', function (e) {
    selectIcon(d);
    e.stopPropagation();
  });
  d.addEventListener('dblclick', function () { openItem(item); });
  d.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') openItem(item);
  });
  d.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    e.stopPropagation();
    selectIcon(d);
    showMenu(iconMenuItems(item), e.clientX, e.clientY);
  });
  return d;
}

function selectIcon(node) {
  document.querySelectorAll('.icon.selected').forEach(function (n) {
    n.classList.remove('selected');
  });
  if (node) node.classList.add('selected');
}
document.addEventListener('mousedown', function (e) {
  if (!e.target.closest('.icon')) selectIcon(null);
});

function iconMenuItems(item) {
  var open = { label: '&Open', def: true, action: function () { openItem(item); } };
  if (SKIN === 'os2') {
    return [open, { sep: true },
      { label: '&Settings...', disabled: true },
      { label: '&Copy...', disabled: true },
      { label: 'Create s&hadow...', disabled: true }];
  }
  return [open, { sep: true },
    { label: 'Get &info', disabled: true },
    { label: '&Duplicate', disabled: true },
    { label: 'Move to &Trash', disabled: true }];
}

// ---------------------------------------------------------------- desktop

function renderDesktop() {
  var slots = deskSlots(M.desktop.length);
  M.desktop.forEach(function (item, i) {
    var d = makeIcon(item, desktop, 'desk-icon');
    d.style.left = slots[i].x + 'px';
    d.style.top = slots[i].y + 'px';
  });

  desktop.addEventListener('contextmenu', function (e) {
    if (e.target.closest('.win,.icon,.menu,#deskbar,#launchpad')) return;
    e.preventDefault();
    showMenu(desktopMenuItems(), e.clientX, e.clientY);
  });

  if (SKIN === 'beos') buildDeskbar(); else buildWarpCenter();
}

// Default icon placement. BeOS lays the demo desktop as a row block top-left
// (matches R5 defaults); OS/2 as a column down the left edge (matches Warp 3).
function deskSlots(n) {
  var out = [];
  for (var i = 0; i < n; i++) {
    if (SKIN === 'beos') out.push({ x: 25 + (i % 3) * 100, y: 8 + Math.floor(i / 3) * 74 });
    else out.push({ x: 30, y: 12 + i * 64 });
  }
  return out;
}

function desktopMenuItems() {
  if (SKIN === 'os2') {
    return [
      { label: '&Open', sub: [
        { label: '&Icon view', action: null },
        { label: '&Tree view', disabled: true },
        { label: '&Details view', disabled: true }] },
      { sep: true },
      { label: '&Settings...', disabled: true },
      { label: 'System s&etup', disabled: true },
      { sep: true },
      { label: '&About this site...', action: showAbout },
      { label: 'Switch to &BeOS...', action: switchSkin },
      { sep: true },
      { label: '&Refresh', disabled: true },
      { label: 'Loc&kup now', disabled: true },
      { label: 'Sh&ut down...', disabled: true },
      { label: '&Window list', disabled: true }
    ];
  }
  // The R5 Tracker desktop menu, verbatim; our own entries live in Add-Ons.
  return [
    { label: '&Desktop', header: true, icon: 'menu-desktop', sub: [
      { label: 'Open', disabled: true }] },
    { sep: true },
    { label: '&New Folder', accel: 'ALT N', disabled: true },
    { sep: true },
    { label: '&Icon View', checked: true },
    { label: 'Mini &Icon View', disabled: true },
    { sep: true },
    { label: 'Clean &Up', accel: 'ALT K', disabled: true },
    { label: 'Select &All', accel: 'ALT A', disabled: true },
    { sep: true },
    { label: 'M&ount', sub: [{ label: 'boot', disabled: true }] },
    { sep: true },
    { label: 'Add-On&s', sub: [
      { label: 'About this site' + '…', action: showAbout },
      { label: 'Switch to OS/2 Warp' + '…', action: switchSkin }] }
  ];
}

// ---------------------------------------------------------------- folders

function openFolder(item) {
  var existing = windows.find(function (w) { return w.item === item; });
  if (existing) { focusWindow(existing); return existing; }
  var dims = SKIN === 'beos' ? { w: 340, h: 220 } : { w: 400, h: 230 };
  var n = (item.children || []).length;
  return createWindow({
    kind: 'folder',
    item: item,
    title: folderTitle(item),
    sysIcon: 'sysmenu-folder',
    w: dims.w, h: dims.h,
    menubar: SKIN === 'beos' ? beosFolderMenubar() : null,
    content: function (body, win) {
      var view = el('div', 'folder-view', body);
      (item.children || []).forEach(function (child) {
        makeIcon(child, view, 'grid-icon');
      });
      if (SKIN === 'beos') {
        beosFolderFurniture(body, win,
          n === 1 ? '1 item' : n + ' items');
      }
    }
  });
}

function beosFolderMenubar() {
  return [
    { label: 'File', items: function (win) {
      return [
        { label: 'Open', accel: 'Alt+O', disabled: true },
        { label: 'Get info', accel: 'Alt+I', disabled: true },
        { sep: true },
        { label: 'Close', accel: 'Alt+W', action: function () { closeWindow(win); } }
      ]; } },
    { label: 'Window', items: function (win) {
      return [
        { label: 'Resize to fit', accel: 'Alt+Y', disabled: true },
        { label: 'Select all', accel: 'Alt+A', disabled: true },
        { sep: true },
        { label: 'Close', accel: 'Alt+W', action: function () { closeWindow(win); } }
      ]; } }
  ];
}

// ---------------------------------------------------------------- documents

function openDoc(item) {
  var existing = windows.find(function (w) { return w.item === item; });
  if (existing) { focusWindow(existing); return existing; }
  var dims = SKIN === 'beos' ? { w: 460, h: 340 } : { w: 470, h: 330 };
  return createWindow({
    kind: 'doc',
    item: item,
    title: item.name,
    sysIcon: 'sysmenu-doc',
    w: dims.w, h: dims.h,
    menubar: docMenubar(),
    content: function (body, win) {
      body.classList.add('doc-view');
      var clip = el('div', 'iframe-clip', body);
      var fr = el('iframe', 'poem-frame', clip);
      fr.src = item.path;
      fr.title = item.name;
      buildDocScrollbars(body, fr, win);
    }
  });
}

function docMenubar() {
  if (SKIN === 'os2') {
    return [
      { label: '&File', items: function (win) {
        return [
          { label: '&New', disabled: true },
          { label: '&Save', disabled: true },
          { sep: true },
          { label: '&Close', def: true, action: function () { closeWindow(win); } }
        ]; } },
      { label: '&Edit', items: function () {
        return [
          { label: '&Copy', accel: 'Ctrl+Ins', disabled: true },
          { label: 'Select &all', disabled: true }
        ]; } },
      { label: '&Options', items: function () {
        return [{ label: '&Word wrap', checked: true, disabled: true }]; } },
      { label: '&Help', items: function () {
        return [{ label: '&About this site...', action: showAbout }]; } }
    ];
  }
  return [
    { label: 'File', items: function (win) {
      return [
        { label: 'Save', accel: 'Alt+S', disabled: true },
        { label: 'Page setup' + '…', disabled: true },
        { sep: true },
        { label: 'Close', accel: 'Alt+W', action: function () { closeWindow(win); } }
      ]; } },
    { label: 'Edit', items: function () {
      return [
        { label: 'Copy', accel: 'Alt+C', disabled: true },
        { label: 'Select all', accel: 'Alt+A', disabled: true }
      ]; } },
    { label: 'Font', items: function () {
      return [{ label: 'As compiled', checked: true, disabled: true }]; } }
  ];
}

// Custom period scrollbars driving the poem iframe. If the iframe document is
// unreachable (file:// cross-document rules), fall back to its native
// scrollbar: body gets 'native-scroll' and our chrome is not built.
function buildDocScrollbars(body, fr, win) {
  var vsb = el('div', 'sb sb-v', body);
  var up = el('div', 'sb-btn sb-up', vsb);
  var track = el('div', 'sb-track', vsb);
  var thumb = el('div', 'sb-thumb', track);
  var dn = el('div', 'sb-btn sb-down', vsb);
  if (SKIN === 'os2') el('div', 'sb sb-h', body);

  function doc() {
    try { return fr.contentDocument || null; } catch (e) { return null; }
  }
  function metrics() {
    var d = doc();
    if (!d || !d.documentElement) return null;
    var de = d.documentElement;
    return { max: Math.max(0, de.scrollHeight - de.clientHeight),
             page: de.clientHeight, full: de.scrollHeight, top: de.scrollTop || d.body.scrollTop || 0 };
  }
  function layout() {
    var m = metrics();
    if (!m) { body.classList.add('native-scroll'); return; }
    var th = m.full ? Math.max(18, Math.round(track.clientHeight * m.page / m.full)) : track.clientHeight;
    thumb.style.height = th + 'px';
    var range = track.clientHeight - th;
    thumb.style.top = (m.max ? Math.round(range * m.top / m.max) : 0) + 'px';
  }
  function scrollBy(dy) {
    var d = doc();
    if (!d) return;
    d.documentElement.scrollTop += dy;
    if (d.body) d.body.scrollTop += dy;
    layout();
  }
  fr.addEventListener('load', function () {
    var d = doc();
    if (!d) { body.classList.add('native-scroll'); return; }
    body.classList.remove('native-scroll');
    layout();
    d.addEventListener('scroll', layout, { passive: true });
  });
  up.addEventListener('mousedown', function () { scrollBy(-40); });
  dn.addEventListener('mousedown', function () { scrollBy(40); });
  thumb.addEventListener('pointerdown', function (e) {
    var m0 = metrics();
    if (!m0) return;
    var sy = e.clientY, t0 = thumb.offsetTop;
    var range = track.clientHeight - thumb.offsetHeight;
    function move(ev) {
      var t = Math.max(0, Math.min(range, t0 + ev.clientY - sy));
      var d = doc();
      if (d && range) {
        d.documentElement.scrollTop = m0.max * t / range;
        if (d.body) d.body.scrollTop = m0.max * t / range;
      }
      layout();
    }
    function upfn() {
      removeEventListener('pointermove', move);
      removeEventListener('pointerup', upfn);
    }
    addEventListener('pointermove', move);
    addEventListener('pointerup', upfn);
    e.preventDefault();
  });
}

// ---------------------------------------------------------------- dialogs

var aboutWin = null;
function showAbout() {
  if (aboutWin && windows.indexOf(aboutWin) !== -1) { focusWindow(aboutWin); return aboutWin; }
  var site = M.site;
  if (SKIN === 'os2') {
    aboutWin = createWindow({
      kind: 'about',
      title: site.title + ' - Product information',
      sysIcon: 'sysmenu-doc',
      w: 351, h: null,
      content: function (body, win) {
        body.classList.add('about-os2');
        var row = el('div', 'about-row', body);
        el('img', 'about-icon', row).src = iconPath('about');
        var lines = el('div', 'about-lines', row);
        site.about_lines.forEach(function (t) { el('div', null, lines).textContent = t; });
        var btnrow = el('div', 'about-btnrow', body);
        var ok = el('button', 'os2-button default-button', btnrow);
        ok.textContent = 'OK';
        ok.addEventListener('click', function () { closeWindow(win); });
      }
    });
  } else {
    aboutWin = createWindow({
      kind: 'about',
      title: 'About this site',
      w: 511, h: null,
      content: function (body) {
        body.classList.add('about-beos');
        var left = el('div', 'about-left', body);
        var logo = el('div', 'about-logo', left);
        el('span', 'logo-a', logo).textContent = 'CM';
        el('span', 'logo-b', logo).textContent = 'P';
        var info = el('div', 'about-info', left);
        [['Site:', 'cmpreston.com'],
         ['Form:', 'poems for the browser'],
         ['Version:', '1.0'],
         ['Contact:', site.contact]].forEach(function (pair) {
          el('div', 'about-key', info).textContent = pair[0];
          el('div', 'about-val', info).textContent = pair[1];
        });
        var right = el('div', 'about-right', body);
        el('p', null, right).textContent =
          'Poems written for the screen, presented in the manner of the ' +
          'operating systems that first made the screen feel like a desk.';
        el('p', null, right).textContent =
          'Everything here is plain HTML, CSS and JavaScript. No trackers, ' +
          'no analytics, no fonts phoned home.';
        el('p', null, right).textContent = 'Mail: ' + site.contact;
      }
    });
  }
  return aboutWin;
}

// ---------------------------------------------------------------- chrome bars

var clockEl = null;
function buildDeskbar() {
  var db = el('div', null, desktop);
  db.id = 'deskbar';
  var logo = el('div', 'db-logo', db);
  el('img', null, logo).src = iconPath('be-logo');
  el('div', 'db-sep', db);
  var tray = el('div', 'db-tray', db);
  clockEl = el('span', 'db-clock', tray);
  tickClock();
  el('div', 'db-sep', db);
  var apps = el('div', 'db-apps', db);
  var t = el('div', 'db-app', apps);
  el('img', null, t).src = iconPath('tracker');
  el('span', null, t).textContent = 'Tracker';
  db.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  logo.addEventListener('click', function (e) {
    var r = logo.getBoundingClientRect();
    showMenu([
      { label: 'About this site' + '…', action: showAbout },
      { sep: true },
      { label: 'Switch to OS/2 Warp' + '…', action: switchSkin },
      { sep: true },
      { label: 'Restart', disabled: true },
      { label: 'Shut down', disabled: true }
    ], r.left - 60, r.bottom);
    e.stopPropagation();
  });
}

var clockPinned = false;
function tickClock() {
  if (!clockEl || clockPinned) return;
  var d = new Date();
  var h = d.getHours() % 12 || 12;
  var mm = String(d.getMinutes()).padStart(2, '0');
  var ap = d.getHours() < 12 ? 'AM' : 'PM';
  if (SKIN === 'os2') {
    // WarpCenter shows H:MM:SS AM (seconds visible in the reference)
    var ss = String(d.getSeconds()).padStart(2, '0');
    clockEl.textContent = h + ':' + mm + ':' + ss + ' ' + ap;
    setTimeout(tickClock, 1000);
  } else {
    clockEl.textContent = h + ':' + mm + ' ' + ap;
    setTimeout(tickClock, 5000);
  }
}

// OS/2 Warp 4 WarpCenter: the ~22px bar pinned to the top edge. Left/middle is
// the fixed toolbar (OS/2 logo tile, launch buttons, the C:(HPFS) drive/resource
// indicator, more icon buttons) rendered from the extracted strip sprite; the
// clock lives at the right and ticks live. The dark bottom edge is drawn in CSS.
function buildWarpCenter() {
  var wc = el('div', null, desktop);
  wc.id = 'warpcenter';
  var bar = el('img', 'wc-bar', wc);          // fixed content, x0..556
  bar.src = iconPath('wc-bar');
  bar.draggable = false;
  clockEl = el('span', 'wc-clock', wc);       // right-aligned live readout
  tickClock();
  wc.addEventListener('contextmenu', function (e) { e.preventDefault(); });
  return wc;
}

// ---------------------------------------------------------------- actions

function openItem(item) {
  if (isMobile()) return openMobile(item);
  if (item.type === 'folder') return openFolder(item);
  if (item.type === 'doc') return openDoc(item);
  if (item.type === 'switcher') return switchSkin();
  if (item.type === 'trash' && SKIN === 'beos') {
    return showAlert({
      text: 'The Trash is empty.',
      buttons: [{ label: 'OK', def: true }]
    });
  }
  return null;
}

// BeOS-style system alert: gray panel, darker icon stripe at the left,
// right-aligned buttons, no title tab. opts: {text (\n = line break),
// buttons: [{label, action, def}], x/y/w/h (fixtures pin these)}
function showAlert(opts) {
  var win = { kind: 'alert', title: '' };
  var node = win.node = el('div', 'win win-alert win-active', desktop);
  if (opts.w) node.style.width = opts.w + 'px';
  var aw = opts.w || 317, ah = opts.h || 84;
  node.style.left = (opts.x != null ? opts.x
      : Math.round((innerWidth - aw) / 2)) + 'px';
  node.style.top = (opts.y != null ? opts.y
      : Math.round(innerHeight * 0.22)) + 'px';
  if (opts.h) node.style.height = opts.h + 'px';
  var body = el('div', 'alert-body', node);
  var stripe = el('div', 'alert-stripe', body);
  el('img', 'alert-icon', stripe).src = iconPath('alert-icon');
  var content = el('div', 'alert-content', body);
  var text = el('div', 'alert-text', content);
  String(opts.text).split('\n').forEach(function (ln) {
    el('div', null, text).textContent = ln;
  });
  var btns = el('div', 'alert-buttons', content);
  (opts.buttons || [{ label: 'OK', def: true }]).forEach(function (b) {
    var btn = el('button', 'beos-button' + (b.def ? ' default-button' : ''), btns);
    btn.textContent = b.label;
    btn.addEventListener('click', function () {
      node.remove();
      var i = windows.indexOf(win);
      if (i !== -1) windows.splice(i, 1);
      if (b.action) b.action();
    });
  });
  node.addEventListener('pointerdown', function () { focusWindow(win); }, true);
  windows.push(win);
  focusWindow(win);
  return win;
}

function switchSkin() {
  var next = SKIN === 'beos' ? 'os2' : 'beos';
  try { localStorage.setItem('skin', next); } catch (e) {}
  location.href = location.pathname; // drop ?skin/?fixture overrides
}

// ---------------------------------------------------------------- mobile

function renderMobile() {
  document.body.classList.add('mobile');
  var list = el('div', 'm-list', desktop);
  var head = el('div', 'm-head', list);
  head.textContent = M.site.title;
  var sw = el('button', 'm-switch', head);
  sw.textContent = 'Skin: ' + (SKIN === 'beos' ? 'BeOS' : 'OS/2 Warp');
  sw.addEventListener('click', switchSkin);
  function walk(items, depth, parent) {
    items.forEach(function (item) {
      if (item.type === 'switcher' || item.type === 'trash') return;
      var row = el('div', 'm-row', parent);
      row.style.paddingLeft = (12 + depth * 22) + 'px';
      el('img', 'm-icon', row).src = iconPath(itemIcon(item));
      el('span', null, row).textContent = itemName(item);
      if (item.type === 'doc') {
        row.addEventListener('click', function () { openMobile(item); });
      } else {
        row.classList.add('m-folder');
        var box = el('div', 'm-children', parent);
        box.style.display = 'none';
        walk(item.children || [], depth + 1, box);
        row.addEventListener('click', function () {
          box.style.display = box.style.display === 'none' ? '' : 'none';
        });
      }
    });
  }
  walk(M.desktop, 0, list);
  var foot = el('div', 'm-foot', list);
  foot.textContent = M.site.contact;
}

function openMobile(item) {
  if (item.type !== 'doc') return null;
  var ov = el('div', 'm-overlay', document.body);
  var bar = el('div', 'm-bar', ov);
  var back = el('button', 'm-back', bar);
  back.textContent = '◀ Back';
  el('span', 'm-title', bar).textContent = item.name;
  var fr = el('iframe', 'm-frame', ov);
  fr.src = item.path;
  back.addEventListener('click', function () { ov.remove(); });
  return ov;
}

// ---------------------------------------------------------------- fixture API

window.SHELL = {
  windows: windows,
  openItem: openItem,
  openFolder: openFolder,
  openDoc: openDoc,
  showAbout: showAbout,
  showAlert: showAlert,
  showMenu: showMenu,
  desktopMenuItems: desktopMenuItems,
  iconMenuItems: iconMenuItems,
  switchSkin: switchSkin,
  createWindow: createWindow,
  makeIcon: makeIcon,
  selectIcon: selectIcon,
  closeMenus: closeMenus,
  pinClock: function (text) {
    clockPinned = true;
    if (clockEl) clockEl.textContent = text;
  },
  fakeCursor: function (x, y) {
    var c = el('img', 'fake-cursor', desktop);
    c.src = iconPath('cursor');
    c.style.left = x + 'px';
    c.style.top = y + 'px';
    return c;
  }
};

// ---------------------------------------------------------------- boot

if (isMobile() && !new URLSearchParams(location.search).get('fixture')) {
  renderMobile();
} else {
  renderDesktop();
}

})();
