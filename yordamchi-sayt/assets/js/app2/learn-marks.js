/* Learn — belgilash (highlight), "Reels" ko'rigi va keyingi mavzuga o'tish.

   Uchta mustaqil imkoniyat bitta modulda, chunki uchalasi ham AYNAN bir xil
   joyda — darslik matni ochilgan sahifada — ishlaydi va bir xil ma'lumotga
   (joriy hujjat + uning ro'yxatdagi qo'shnilari) tayanadi.

   1) BELGILASH.  O'ng chekkadagi tortma ochiladi, undagi belgi tugmasi
      bosiladi va matn ustida to'rtburchak chiziladi (kompyuterdagi kabi
      bosib-tortib). Qo'yib yuborilganda ichidagi matn sariq bilan
      belgilanadi va "Saqlash" tugmasi chiqadi.

      Belgi DOM ni O'ZGARTIRMAYDI: `range.getClientRects()` dan olingan
      to'rtburchaklar alohida qatlamga chiziladi. Sababi — matnni <mark>
      bilan o'rash matn tugunlarini bo'lib yuboradi va keyingi belgilarning
      saqlangan indekslari siljib qoladi. Qatlam esa istalgancha belgi
      bilan ham matnga tegmaydi; o'lcham o'zgarganda qayta chiziladi.

      Saqlash: matn tugunining tartib raqami + siljish (si/so/ei/eo) hamda
      matnning O'ZI. Ochilganda avval indeks bo'yicha tiklanadi; matn mos
      kelmasa (.md tahrirlangan bo'lsa) matn bo'yicha qidirib topiladi.

   2) REELS.  Har bir Learn sahifasining o'ng pastida dumaloq tugma. Bosilsa
      belgilangan joylar birma-bir, to'liq ekranda chiqadi — yuqoriga surib
      keyingisiga o'tiladi.

   3) KEYINGI MAVZU.  Matn oxiriga yetganda barmoqni yuqoriga tortib turilsa
      (Telegram'dagi kabi) keyingi mavzu ochiladi. Qo'shni mavzular
      `get_topics` dan olinadi — joriy mavzu bilan BIR PAPKADAGILAR, nom
      bo'yicha tabiiy (raqamli) tartibda.

   Saqlash joyi — localStorage `learn_marks_v1`. remote-storage.js uni
   avtomatik serverga sinxronlaydi, shuning uchun alohida API kerak emas. */
(function () {
  'use strict';

  var KEY = 'learn_marks_v1';

  /* Belgilash faqat `.md-content` bo'lgan sahifalarda ishlaydi.
     `reading_doc` bundan tashqarida: u yerda har so'z bosiladigan
     (tarjima/tinglash) element — to'rtburchak tortish ular bilan
     to'qnashadi. U sahifada faqat Reels va keyingi mavzu qoladi. */
  var DOC_VIEWS = { grammar_topic: 1, library_doc: 1, reading_doc: 1 };

  /* Pastdagi dumaloq "Reels" tugmasi Learn bo'limining BOSH sahifasida
     va har bir bo'limning O'ZIDA turadi:

       Learn (languages)      -> hamma belgilar
       Ingliz tili / Русский  -> o'sha tilnikilar (grammatika + materiallar)
       Python, Django, ...    -> o'sha bo'limnikilar
       Coding                 -> coding bo'liminikilar

     Papka ICHIDA ko'rsatilmaydi — o'sha yerda diqqat mavzularga qaratilgan
     bo'lishi kerak. Darslik matni ochilganda Reels yo'qolmaydi: o'ng
     chekkadagi tortmadagi ▶ tugmasi orqali ochiladi.

     Belgi qaysi bo'limga tegishli ekani uning saqlangan parametrlaridan
     bilinadi: `p.lang` (grammatika mavzulari) yoki `p.sec` (materiallar —
     `en_reading`, `ru_writing` kabi). */
  function docLang(d) {
    var p = (d && d.p) || {};
    return String(p.lang || p.sec || '');
  }
  function byLang(L) {
    return function (k, d) { return docLang(d) === L; };
  }

  /* Qaytadi: `null` — hammasi, funksiya — filtr, `undefined` — tugma yo'q. */
  function fabScope() {
    var v = S.view, p = S.params || {};
    if (v === 'languages') return null;
    if (v === 'english') return function (k, d) {
      var l = docLang(d); return l === 'english' || l.indexOf('en_') === 0;
    };
    if (v === 'russian') return function (k, d) {
      var l = docLang(d); return l === 'russian' || l.indexOf('ru_') === 0;
    };
    if (v === 'coding') return byLang('coding');
    /* Papka ichida emas, faqat bo'lim ildizida */
    if (v === 'grammar' && p.lang && !p.folder) return byLang(p.lang);
    if (v === 'library' && p.sec && !p.path) return byLang(p.sec);
    return undefined;
  }

  var S = {
    view: '', params: {}, docKey: '', title: '',
    md: null, layer: null, marks: [],
    marking: false, pending: null,
    dock: null, fab: null, nextInfo: null, nextBar: null,
    selA: null, selB: null, gen: 0, sig: ''
  };

  /* ---------------- saqlash ---------------- */

  function loadAll() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; }
    catch (e) { return {}; }
  }
  function saveAll(o) {
    try { localStorage.setItem(KEY, JSON.stringify(o)); }
    catch (e) { App.toast('⚠️ Saqlanmadi — joy yetmadi'); }
  }
  function docEntry(all, key) {
    return all[key] || (all[key] = { t: '', v: '', p: {}, m: [] });
  }
  function marksOf(key) {
    var d = loadAll()[key];
    return (d && d.m) || [];
  }

  /* ---------------- matn o'rni ---------------- */

  function textNodes(root) {
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), a = [], n;
    while ((n = w.nextNode())) a.push(n);
    return a;
  }

  /* Belgilangan bo'lakning HTML ko'rinishi. Reels'da matn AYNAN darslikdagi
     kabi chiqishi kerak (qalin so'zlar, ro'yxat, jadval, sarlavha) — shu
     sabab oddiy matndan tashqari HTML ham saqlanadi.

     `cloneContents()` bo'lak o'rtasidan boshlansa ham to'g'ri ishlaydi:
     brauzer ochilmagan teglarni o'zi yopadi. O'zimizning belgi qatlamlari
     nusxaga tushib qolmasligi uchun ular olib tashlanadi. */
  var HTML_LIMIT = 20000;
  function rangeHtml(range) {
    try {
      var d = document.createElement('div');
      d.appendChild(range.cloneContents());
      var junk = d.querySelectorAll('.lm-layer, .lm-capture, .lm-rect');
      for (var i = 0; i < junk.length; i++) junk[i].parentNode.removeChild(junk[i]);
      var h = d.innerHTML;
      return h.length > HTML_LIMIT ? '' : h;
    } catch (e) { return ''; }
  }

  function serialize(root, range) {
    var nodes = textNodes(root);
    var si = nodes.indexOf(range.startContainer), ei = nodes.indexOf(range.endContainer);
    if (si < 0 || ei < 0) return null;
    var text = range.toString().trim();
    if (!text) return null;
    return { id: 'm' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
             si: si, so: range.startOffset, ei: ei, eo: range.endOffset,
             text: text, h: rangeHtml(range), at: Date.now() };
  }

  /* Saqlangan belgini qayta Range ga aylantiradi. */
  function deserialize(root, m) {
    var nodes = textNodes(root);
    if (m.si < nodes.length && m.ei < nodes.length) {
      try {
        var r = document.createRange();
        r.setStart(nodes[m.si], Math.min(m.so, nodes[m.si].length));
        r.setEnd(nodes[m.ei], Math.min(m.eo, nodes[m.ei].length));
        if (!r.collapsed && r.toString().trim() === m.text) return r;
      } catch (e) { /* indekslar siljigan — pastda matn bo'yicha qidiramiz */ }
    }
    return byText(root, m.text);
  }

  /* Zaxira yo'l: butun matnni birlashtirib, belgilangan parchani qidiradi. */
  function byText(root, text) {
    if (!text) return null;
    var nodes = textNodes(root), full = '', map = [];
    nodes.forEach(function (n, i) { map.push({ i: i, at: full.length, len: n.length }); full += n.data; });
    var pos = full.indexOf(text);
    if (pos < 0) {
      // bo'shliqlar farq qilishi mumkin — siqib qidiramiz
      var norm = text.replace(/\s+/g, ' ').trim();
      pos = full.replace(/\s+/g, ' ').indexOf(norm);
      if (pos < 0) return null;
    }
    var end = pos + text.length;
    var a = locate(map, pos), b = locate(map, end);
    if (!a || !b) return null;
    try {
      var r = document.createRange();
      r.setStart(nodes[a.i], a.off);
      r.setEnd(nodes[b.i], b.off);
      return r.collapsed ? null : r;
    } catch (e) { return null; }
  }
  function locate(map, pos) {
    for (var k = 0; k < map.length; k++) {
      var e = map[k];
      if (pos >= e.at && pos <= e.at + e.len) return { i: e.i, off: pos - e.at };
    }
    return null;
  }

  /* ---------------- chizish ---------------- */

  function ensureLayer() {
    if (!S.md) return null;
    if (S.layer && S.layer.parentNode === S.md) return S.layer;
    var l = document.createElement('div');
    l.className = 'lm-layer';
    S.md.insertBefore(l, S.md.firstChild);
    S.layer = l;
    return l;
  }

  /* Range ni qatlamdagi to'rtburchaklarga aylantiradi. */
  function paint(range, cls, id) {
    var layer = ensureLayer(); if (!layer || !range) return;
    var base = S.md.getBoundingClientRect();
    var rects = range.getClientRects();
    for (var i = 0; i < rects.length; i++) {
      var r = rects[i];
      if (r.width < 1 || r.height < 1) continue;
      var d = document.createElement('div');
      d.className = cls;
      if (id) d.setAttribute('data-mark', id);
      d.style.left = (r.left - base.left) + 'px';
      d.style.top = (r.top - base.top) + 'px';
      d.style.width = r.width + 'px';
      d.style.height = r.height + 'px';
      layer.appendChild(d);
    }
  }

  function redraw() {
    var layer = ensureLayer(); if (!layer) return;
    layer.innerHTML = '';
    S.marks = marksOf(S.docKey);
    S.marks.forEach(function (m) {
      var r = deserialize(S.md, m);
      if (r) paint(r, 'lm-rect', m.id);
    });
    refreshDockCount();
  }

  var redrawT = null;
  function redrawSoon() { clearTimeout(redrawT); redrawT = setTimeout(redraw, 120); }

  /* ---------------- to'rtburchak bilan tanlash ---------------- */

  function caretAt(x, y) {
    if (document.caretRangeFromPoint) return document.caretRangeFromPoint(x, y);
    if (document.caretPositionFromPoint) {
      var p = document.caretPositionFromPoint(x, y);
      if (!p) return null;
      var r = document.createRange();
      r.setStart(p.offsetNode, p.offset); r.collapse(true);
      return r;
    }
    return null;
  }

  /* Ikki nuqta orasidagi matnni Range qilib beradi. Nuqta matndan tashqarida
     (chekka bo'shliqda) bo'lsa — X ni matn maydoniga qisib qidiradi, aks holda
     brauzer null qaytarib, tanlash umuman ishlamay qolardi. */
  function rangeBetween(x1, y1, x2, y2) {
    var b = S.md.getBoundingClientRect();
    var cx = function (x) { return Math.min(Math.max(x, b.left + 2), b.right - 2); };
    var a = caretAt(cx(x1), y1), c = caretAt(cx(x2), y2);
    if (!a || !c) return null;
    if (!S.md.contains(a.startContainer) || !S.md.contains(c.startContainer)) return null;
    var r = document.createRange();
    try {
      if (a.compareBoundaryPoints(Range.START_TO_START, c) <= 0) {
        r.setStart(a.startContainer, a.startOffset);
        r.setEnd(c.startContainer, c.startOffset);
      } else {
        r.setStart(c.startContainer, c.startOffset);
        r.setEnd(a.startContainer, a.startOffset);
      }
    } catch (e) { return null; }
    if (r.collapsed) return null;
    return snapWords(r);
  }

  /* Chetlarini so'z chegarasiga suradi — yarim so'z belgilanib qolmasin. */
  function snapWords(r) {
    try {
      var sc = r.startContainer, ec = r.endContainer;
      if (sc.nodeType === 3) {
        var so = r.startOffset;
        while (so > 0 && /\S/.test(sc.data.charAt(so - 1))) so--;
        r.setStart(sc, so);
      }
      if (ec.nodeType === 3) {
        var eo = r.endOffset;
        while (eo < ec.data.length && /\S/.test(ec.data.charAt(eo))) eo++;
        r.setEnd(ec, eo);
      }
    } catch (e) { /* chegarada — qanday bo'lsa shunday qoladi */ }
    return r;
  }

  /* ---- To'rtburchak bilan tanlash ----

     Kompyuterdagi "ekran kesish" oynasi kabi ishlaydi: belgilash tugmasi
     bosilganda tayyor to'rtburchak CHIQADI, tashqarisi qoraytiriladi.
     To'rt burchagidagi oq doiralardan tortib kattalashtirasiz/kichraytirasiz,
     ichidan tortib butun to'rtburchakni surasiz. Shundan keyin "Saqlash".

     Nega erkin tortib chizish emas: barmoq bilan bir urinishda kerakli
     joyni ANIQ o'rab olish qiyin — sal xato bo'lsa boshidan boshlash
     kerak bo'lardi. Chiqib turgan to'rtburchakni esa xohlagancha
     to'g'rilash mumkin. */

  var MIN_W = 60, MIN_H = 28;

  /* Nuqtadagi matn o'rni. Nuqta ekrandan tashqarida bo'lsa brauzer null
     qaytaradi — bunday holda ESKI chekka saqlanib qoladi (to'rtburchak
     ekrandan uzunroq bo'lsa ham tanlov buzilmasin). */
  function caretIn(x, y) {
    if (y < 2 || y > window.innerHeight - 2) return null;
    var b = S.md.getBoundingClientRect();
    var cx = Math.min(Math.max(x, b.left + 2), b.right - 2);

    /* `caretRangeFromPoint` oddiy hit-test qiladi — tanlash qatlami matn
       USTIDA turgani uchun u matn o'rniga qatlamning o'zini qaytaradi
       (natijada tanlov doim bo'sh chiqardi). Qatlamni bir zumga
       "bosilmaydigan" qilib qo'yamiz: hit-test `pointer-events:none` ni
       hisobga oladi, harakat esa `setPointerCapture` tufayli uzilmaydi. */
    var cap = S._cap, prev = null;
    if (cap) { prev = cap.style.pointerEvents; cap.style.pointerEvents = 'none'; }
    var r = caretAt(cx, y);
    if (cap) cap.style.pointerEvents = prev || '';

    if (!r || !S.md.contains(r.startContainer)) return null;
    if (cap && cap.contains(r.startContainer)) return null;
    return { n: r.startContainer, o: r.startOffset };
  }

  function rangeOfSel() {
    if (!S.selA || !S.selB) return null;
    var a = document.createRange(), b = document.createRange();
    try {
      a.setStart(S.selA.n, S.selA.o); a.collapse(true);
      b.setStart(S.selB.n, S.selB.o); b.collapse(true);
    } catch (e) { return null; }
    var r = document.createRange();
    try {
      if (a.compareBoundaryPoints(Range.START_TO_START, b) <= 0) {
        r.setStart(S.selA.n, S.selA.o); r.setEnd(S.selB.n, S.selB.o);
      } else {
        r.setStart(S.selB.n, S.selB.o); r.setEnd(S.selA.n, S.selA.o);
      }
    } catch (e) { return null; }
    if (r.collapsed) return null;
    return snapWords(r);
  }

  function startMarking() {
    if (!S.md || S.marking) return;
    S.marking = true;
    document.body.classList.add('lm-on');
    S.selA = S.selB = null;

    var cap = document.createElement('div');
    cap.className = 'lm-capture';
    S.md.appendChild(cap);
    /* DARHOL tayinlanadi: `caretIn()` shu havoladan foydalanadi, birinchi
       hisoblash esa quyida — pastda tayinlansa birinchi marta bo'sh chiqadi. */
    S._cap = cap;

    var sel = document.createElement('div');
    sel.className = 'lm-sel';
    sel.innerHTML = ['tl', 'tr', 'bl', 'br'].map(function (c) {
      return '<i class="lm-h lm-h-' + c + '" data-c="' + c + '"></i>';
    }).join('') + '<span class="lm-sel-hint">burchaklardan tortib moslang</span>';
    cap.appendChild(sel);

    /* Boshlang'ich o'lcham — hozir KO'RINIB turgan matnning o'rtasidan.
       Butun matn balandligi bo'yicha o'rtasini olsak, uzun darslikda
       to'rtburchak ekrandan tashqarida paydo bo'lardi. */
    var b = S.md.getBoundingClientRect();
    var visTop = Math.max(0, -b.top);
    var visBot = Math.min(b.height, window.innerHeight - b.top);
    var vh = Math.max(60, visBot - visTop);
    var h = Math.max(MIN_H, Math.min(190, vh * 0.42));
    var box = {
      x: 0,
      y: Math.max(0, visTop + (vh - h) / 2),
      w: Math.max(MIN_W, b.width),
      h: h
    };

    var barEl = bar('', [
      { t: 'Bekor', k: 'sec', f: stopMarking },
      { t: 'Saqlash', k: '', f: function () { commit(); } }
    ]);
    var barTxt = barEl.querySelector('.lm-bar-t');
    var saveBtn = barEl.querySelectorAll('.lm-bar-b .btn')[1];

    function apply(recalc) {
      sel.style.left = box.x + 'px';
      sel.style.top = box.y + 'px';
      sel.style.width = box.w + 'px';
      sel.style.height = box.h + 'px';
      if (recalc === false) return;
      var bb = S.md.getBoundingClientRect();
      var pad = 4;
      var a = caretIn(bb.left + box.x + pad, bb.top + box.y + pad);
      var c = caretIn(bb.left + box.x + box.w - pad, bb.top + box.y + box.h - pad);
      if (a) S.selA = a;
      if (c) S.selB = c;
      var r = rangeOfSel();
      S.pending = r ? { range: r } : null;
      var t = r ? r.toString().replace(/\s+/g, ' ').trim() : '';
      barTxt.textContent = t ? short(t) : 'To\'rtburchakni matn ustiga qo\'ying';
      saveBtn.disabled = !t;
      saveBtn.classList.toggle('off', !t);
    }
    apply();

    /* --- surish va o'lcham o'zgartirish --- */
    var drag = null;

    function onDown(e) {
      var h = e.target.closest ? e.target.closest('.lm-h') : null;
      drag = {
        corner: h ? h.getAttribute('data-c') : '',
        px: e.clientX, py: e.clientY,
        b0: { x: box.x, y: box.y, w: box.w, h: box.h }
      };
      sel.classList.add('grab');
      try { sel.setPointerCapture(e.pointerId); } catch (err) {}
      e.preventDefault(); e.stopPropagation();
    }

    function onMove(e) {
      if (!drag) return;
      var dx = e.clientX - drag.px, dy = e.clientY - drag.py, o = drag.b0;
      var maxW = S.md.getBoundingClientRect().width;
      var maxH = S.md.scrollHeight || S.md.getBoundingClientRect().height;

      if (!drag.corner) {                       // butun to'rtburchakni surish
        box.x = Math.min(Math.max(0, o.x + dx), maxW - o.w);
        box.y = Math.min(Math.max(0, o.y + dy), maxH - o.h);
      } else {
        var l = o.x, t = o.y, r = o.x + o.w, bt = o.y + o.h;
        if (drag.corner.charAt(0) === 't') t = Math.min(o.y + dy, bt - MIN_H);
        else bt = Math.max(o.y + o.h + dy, t + MIN_H);
        if (drag.corner.charAt(1) === 'l') l = Math.min(o.x + dx, r - MIN_W);
        else r = Math.max(o.x + o.w + dx, l + MIN_W);
        box.x = Math.max(0, l);
        box.y = Math.max(0, t);
        box.w = Math.min(r, maxW) - box.x;
        box.h = Math.min(bt, maxH) - box.y;
      }
      apply();
      edgeScroll(e.clientY);
      e.preventDefault();
    }

    function onUp(e) {
      if (!drag) return;
      drag = null;
      sel.classList.remove('grab');
      stopEdgeScroll();
      try { sel.releasePointerCapture(e.pointerId); } catch (err) {}
      apply();
    }

    sel.addEventListener('pointerdown', onDown);
    sel.addEventListener('pointermove', onMove);
    sel.addEventListener('pointerup', onUp);
    sel.addEventListener('pointercancel', onUp);

    /* Barmoq ekran chetiga yetganda sahifa o'zi suriladi — aks holda
       ekranga sig'maydigan bo'lakni belgilab bo'lmasdi. */
    var esT = null, esV = 0;
    function edgeScroll(y) {
      var top = 90, bot = window.innerHeight - 110;
      esV = y < top ? -Math.min(18, (top - y) / 3)
          : y > bot ? Math.min(18, (y - bot) / 3) : 0;
      if (esV && !esT) esT = setInterval(function () {
        window.scrollBy(0, esV);
        if (drag) {
          if (drag.corner) { box.h += esV > 0 ? esV : 0; }
          drag.py -= esV;
        }
        apply();
      }, 16);
      if (!esV) stopEdgeScroll();
    }
    function stopEdgeScroll() { if (esT) { clearInterval(esT); esT = null; } esV = 0; }

    /* Sahifa surilganda to'rtburchak matn bilan birga qoladi (u
       `.md-content` ichida joylashgan), lekin chekka nuqtalar qayta
       hisoblanishi kerak — shuning uchun scroll'da ham yangilaymiz. */
    var sc = function () { if (!drag) apply(); };
    window.addEventListener('scroll', sc, { passive: true });

    S._killHint = function () {
      window.removeEventListener('scroll', sc);
      stopEdgeScroll();
      if (barEl) { barEl.remove(); barEl = null; }
    };
  }

  function stopMarking() {
    S.marking = false;
    document.body.classList.remove('lm-on');
    if (S._cap) { S._cap.remove(); S._cap = null; }
    if (S._killHint) { S._killHint(); S._killHint = null; }
    S.pending = null; S.selA = S.selB = null;
    redraw();
  }

  function commit() {
    if (!S.pending || !S.pending.range) { App.toast('⚠️ To\'rtburchak ichida matn yo\'q'); return; }
    var m = serialize(S.md, S.pending.range);
    if (!m) { App.toast('⚠️ Bu joyni saqlab bo\'lmadi'); stopMarking(); return; }
    var all = loadAll(), d = docEntry(all, S.docKey);
    d.t = S.title; d.v = S.view; d.p = S.params;
    d.m.push(m);
    saveAll(all);
    S.pending = null;
    stopMarking();
    App.toast('⭐ Saqlandi');
    redraw();
  }

  function short(s) {
    s = String(s).replace(/\s+/g, ' ').trim();
    return s.length > 60 ? s.slice(0, 60) + '…' : s;
  }

  /* Pastdagi suzuvchi panel (maslahat + tugmalar) */
  function bar(text, btns) {
    var el = document.createElement('div');
    el.className = 'lm-bar';
    el.innerHTML = '<div class="lm-bar-t"></div><div class="lm-bar-b"></div>';
    el.querySelector('.lm-bar-t').textContent = text;
    var box = el.querySelector('.lm-bar-b');
    (btns || []).forEach(function (b) {
      var x = document.createElement('button');
      x.className = 'btn ' + (b.k || '');
      x.textContent = b.t;
      x.onclick = b.f;
      box.appendChild(x);
    });
    document.body.appendChild(el);
    return el;
  }

  /* ---------------- o'ng chekkadagi tortma ---------------- */

  function buildDock() {
    killDock();
    if (!DOC_VIEWS[S.view]) return;
    var canMark = !!S.md;

    var d = document.createElement('div');
    d.className = 'lm-dock';
    d.innerHTML =
      '<button class="lm-handle" aria-label="Belgilash paneli"><i></i></button>' +
      '<div class="lm-dock-body">' +
      (canMark ? '<button class="lm-b" data-a="mark" title="Belgilash" aria-label="Belgilash">' +
        '<span data-icon="edit" data-icon-size="19"></span></button>' : '') +
      '<button class="lm-b" data-a="list" title="Belgilarim" aria-label="Belgilarim">' +
        '<span data-icon="star" data-icon-size="19"></span><b class="lm-cnt"></b></button>' +
      '<button class="lm-b" data-a="reels" title="Reels" aria-label="Reels">' +
        '<span data-icon="play" data-icon-size="19"></span></button>' +
      '</div>';
    document.body.appendChild(d);
    App.icons(d);
    S.dock = d;

    var handle = d.querySelector('.lm-handle');
    handle.onclick = function () { d.classList.toggle('open'); };

    /* Barmoq bilan chapga tortib ochish — "tortma" hissi shundan. */
    var sx = 0, on = false;
    handle.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; on = true; }, { passive: true });
    handle.addEventListener('touchmove', function (e) {
      if (!on) return;
      var dx = e.touches[0].clientX - sx;
      if (dx < -22) { d.classList.add('open'); on = false; }
      else if (dx > 22) { d.classList.remove('open'); on = false; }
    }, { passive: true });
    handle.addEventListener('touchend', function () { on = false; }, { passive: true });

    d.querySelectorAll('.lm-b').forEach(function (b) {
      b.onclick = function () {
        var a = b.getAttribute('data-a');
        d.classList.remove('open');
        if (a === 'mark') startMarking();
        else if (a === 'list') openList();
        else openReels(sameDoc(S.docKey));
      };
    });
    refreshDockCount();
  }

  function refreshDockCount() {
    var n = marksOf(S.docKey).length;
    if (S.dock) {
      var c = S.dock.querySelector('.lm-cnt');
      if (c) { c.textContent = n || ''; c.style.display = n ? '' : 'none'; }
    }
    /* Pastdagi dumaloq tugmadagi son ham darrov yangilansin — belgi
       saqlangandan keyin u eskicha turib qolardi. */
    if (S.fab) {
      var b = S.fab.querySelector('b'), k = countMarks(fabScope());
      if (b) { b.textContent = k || ''; b.style.display = k ? '' : 'none'; }
    }
  }

  function killDock() { if (S.dock) { S.dock.remove(); S.dock = null; } }

  function openList() {
    var list = marksOf(S.docKey);
    if (!list.length) {
      App.sheet('<div class="lm-empty">Bu mavzuda hali belgi yo\'q.<br>' +
        'Tortmadagi ✏ tugmani bosib matnni to\'rtburchak bilan o\'rab oling.</div>',
        { title: 'Belgilarim' });
      return;
    }
    var html = list.map(function (m, i) {
      return '<div class="lm-row"><span class="lm-row-n">' + (i + 1) + '</span>' +
        '<div class="lm-row-t" data-go="' + m.id + '">' + App.esc(short(m.e || m.text)) +
        (m.e ? ' <span class="lm-row-tag">tahrirlangan</span>' : '') + '</div>' +
        '<button class="icon-btn ghost lm-row-x" data-ed="' + m.id + '" aria-label="Tahrirlash">' +
        '<span data-icon="edit" data-icon-size="16"></span></button>' +
        '<button class="icon-btn ghost lm-row-x" data-del="' + m.id + '" aria-label="O\'chirish">' +
        '<span data-icon="trash" data-icon-size="16"></span></button></div>';
    }).join('');
    var sh = App.sheet(html + '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Yopish</button>' +
      '<button class="btn" id="lm-reels">Reels</button></div>', { title: 'Belgilarim (' + list.length + ')' });
    App.icons(sh);
    sh.querySelector('#lm-reels').onclick = function () { App.closeSheet(); openReels(sameDoc(S.docKey)); };
    sh.querySelectorAll('[data-del]').forEach(function (b) {
      b.onclick = function () {
        App.confirm('Bu belgi o\'chirilsinmi?', function () {
          removeMark(b.getAttribute('data-del'));
          App.closeSheet(); openList();
        }, { danger: true, yes: 'O\'chirish' });
      };
    });
    sh.querySelectorAll('[data-ed]').forEach(function (b) {
      b.onclick = function () {
        var id = b.getAttribute('data-ed');
        App.closeSheet();
        editMark(S.docKey, id, function () { openList(); });
      };
    });
    sh.querySelectorAll('[data-go]').forEach(function (b) {
      b.onclick = function () { App.closeSheet(); scrollToMark(b.getAttribute('data-go')); };
    });
  }

  function scrollToMark(id) {
    var m = marksOf(S.docKey).find(function (x) { return x.id === id; });
    if (!m || !S.md) return;
    var r = deserialize(S.md, m);
    if (!r) { App.toast('⚠️ Bu joy topilmadi — matn o\'zgargan'); return; }
    var rect = r.getBoundingClientRect();
    window.scrollTo({ top: window.scrollY + rect.top - window.innerHeight / 3, behavior: 'smooth' });
    var el = S.layer && S.layer.querySelector('[data-mark="' + id + '"]');
    if (el) { el.classList.add('flash'); setTimeout(function () { el.classList.remove('flash'); }, 1400); }
  }

  /* ---------------- Reels ---------------- */

  /* match: `null` — hamma belgilar; funksiya `(key, doc) -> bool` — filtr. */
  function collect(match) {
    var all = loadAll(), out = [];
    Object.keys(all).forEach(function (k) {
      var d = all[k] || {};
      if (match && !match(k, d)) return;
      (d.m || []).forEach(function (m) {
        out.push({ key: k, title: d.t || 'Mavzu', v: d.v, p: d.p, m: m });
      });
    });
    out.sort(function (a, b) { return (b.m.at || 0) - (a.m.at || 0); });
    return out;
  }
  function countMarks(match) { return collect(match).length; }
  function sameDoc(key) { return function (k) { return k === key; }; }

  /* Belgi mazmuni — o'zgartirilgan matn > asl HTML > oddiy matn */
  function fillBody(el, m) {
    if (m.e) {                       // foydalanuvchi tahrirlagan (markdown)
      el.className = 'lm-r-txt md-content';
      el.innerHTML = App.md ? App.md(m.e) : App.esc(m.e);
    } else if (m.h) {                // darslikdagi ASL ko'rinish
      el.className = 'lm-r-txt md-content';
      el.innerHTML = m.h;
    } else {                         // eski belgilar
      el.className = 'lm-r-txt';
      el.textContent = m.text;
      var n = m.text.length;
      el.style.fontSize = (n < 90 ? 26 : n < 220 ? 21 : n < 500 ? 17.5 : 15) + 'px';
    }
    if (App.typeset) { try { App.typeset(el); } catch (e) {} }
  }

  /* Belgini tahrirlash — matn markdown sifatida saqlanadi, shuning uchun
     qalin/ro'yxat kabi belgilashlar tahrirdan keyin ham ishlaydi. */
  function editMark(key, id, done) {
    var all = loadAll(), d = all[key];
    if (!d) return;
    var m = (d.m || []).find(function (x) { return x.id === id; });
    if (!m) return;
    /* Tahrirlash oynasiga o'qishli matn qo'yiladi.

       `m.text` — `range.toString()` natijasi: jadval va ro'yxatlarda
       hamma katak bir-biriga yopishib ketadi ("вы-етеработаете...").
       Saqlangan HTML dan `innerText` olsak, brauzer qator va katak
       chegaralarini hisobga oladi — matn odam o'qiydigan holatda chiqadi. */
    var cur = m.e;
    if (!cur && m.h) {
      var tmp = document.createElement('div');
      tmp.style.cssText = 'position:absolute;left:-9999px;top:0;width:600px';
      tmp.innerHTML = m.h;
      document.body.appendChild(tmp);
      cur = (tmp.innerText || '').replace(/\n{3,}/g, '\n\n').trim();
      tmp.remove();
    }
    if (!cur) cur = m.text;
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">Markdown ishlaydi: ' +
      '<code>**qalin**</code>, <code>- ro\'yxat</code>, <code>&gt; iqtibos</code></p>' +
      '<label class="field"><span>Belgilangan matn</span>' +
      '<textarea class="textarea" id="lm-ed" spellcheck="false">' + App.esc(cur) + '</textarea></label>' +
      (m.e ? '<button class="btn sec" id="lm-reset" style="width:100%;margin-bottom:10px">Aslini qaytarish</button>' : '') +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="lm-ok">Saqlash</button></div>';
    var sh = App.sheet(html, { title: 'Belgini tahrirlash', cls: 'editor-sheet' });
    sh.querySelector('#lm-ok').onclick = function () {
      var v = sh.querySelector('#lm-ed').value.trim();
      if (!v) { App.toast('⚠️ Matn bo\'sh'); return; }
      m.e = v;
      saveAll(all);
      App.closeSheet();
      App.toast('✅ Saqlandi');
      if (done) done();
    };
    var rs = sh.querySelector('#lm-reset');
    if (rs) rs.onclick = function () {
      delete m.e; saveAll(all); App.closeSheet(); App.toast('↩️ Asliga qaytdi');
      if (done) done();
    };
  }

  function deleteMark(key, id, done) {
    var all = loadAll(), d = all[key];
    if (!d) return;
    d.m = (d.m || []).filter(function (x) { return x.id !== id; });
    if (!d.m.length) delete all[key];
    saveAll(all);
    if (S.md && key === S.docKey) redraw();
    refreshDockCount();
    if (done) done();
  }

  /* Joriy hujjatdagi belgini o'chirish (belgi ustiga bosilganda ishlatiladi).
     DIQQAT: bu funksiya avvalgi tahrirda tasodifan yo'qolgan edi va
     `removeMark is not defined` xatosi berardi — o'chirish umuman
     ishlamasdi. Shuning uchun endi `deleteMark` ustidagi yupqa qobiq. */
  function removeMark(id) { deleteMark(S.docKey, id); }

  /* ---- Reels ----

     Instagram/TikTok kabi TIK LENTA: har bir belgi butun ekranni egallaydi,
     barmoq bilan surilganda kartochka barmoqqa ergashadi va qo'yib
     yuborilganda o'ziga "yopishadi".

     Buni qo'lda animatsiya bilan emas, brauzerning O'Z scroll'i +
     `scroll-snap` bilan qildik: harakat 60 kadrda silliq bo'ladi,
     inersiya va "rezina" effekti tizimникidek tabiiy chiqadi. Ilgari
     kartochka har safar qaytadan chizilardi — shuning uchun o'tish
     to'xtab-to'xtab, sun'iy tuyulardi. */
  function openReels(match) {
    var items = collect(match);
    /* Bu bo'limda belgi bo'lmasa BO'SH ko'rsatamiz — ilgari jimgina
       hamma belgi chiqarilardi va foydalanuvchi boshqa bo'limnikini
       ko'rib chalg'irdi. */
    if (!items.length) {
      var bor = collect(null).length;
      App.sheet('<div class="lm-empty">' +
        (bor ? 'Bu bo\'limda hali belgi yo\'q.<br>Boshqa bo\'limlarda ' + bor + ' ta bor — ' +
               'hammasini Learn bosh sahifasidagi tugmadan ko\'rasiz.'
             : 'Hali bironta belgi yo\'q.<br>Darslik matnini ochib, o\'ng chekkadagi ' +
               'tortmadan ✏ ni bosing.') +
        '</div>', { title: 'Reels' });
      return;
    }

    var i = 0;
    var w = document.createElement('div');
    w.className = 'lm-reels';
    /* Chapdagi holat chizig'i va pastdagi "1 / 4" hisobi ATAYLAB yo'q —
       foydalanuvchi so'rovi: lenta toza ko'rinsin. */
    w.innerHTML =
      '<button class="lm-r-x" aria-label="Yopish"><span data-icon="close" data-icon-size="20"></span></button>' +
      '<div class="lm-r-scroll"></div>' +
      '<div class="lm-r-rail">' +
      '<button class="lm-r-a" data-a="open" aria-label="Mavzuni ochish"><span data-icon="book" data-icon-size="19"></span><b>Mavzu</b></button>' +
      '<button class="lm-r-a" data-a="edit" aria-label="Tahrirlash"><span data-icon="edit" data-icon-size="19"></span><b>Tahrir</b></button>' +
      '<button class="lm-r-a danger" data-a="del" aria-label="O\'chirish"><span data-icon="trash" data-icon-size="19"></span><b>O\'chir</b></button>' +
      '</div>';
    document.body.appendChild(w);
    document.body.classList.add('lm-noscroll');
    App.icons(w);

    var scroll = w.querySelector('.lm-r-scroll');

    function build() {
      scroll.innerHTML = '';
      items.forEach(function (it, k) {
        var sl = document.createElement('div');
        sl.className = 'lm-r-slide';
        sl.innerHTML =
          '<div class="lm-r-card">' +
          '<div class="lm-r-src"></div>' +
          '<div class="lm-r-body"><div class="lm-r-txt"></div></div>' +
          '</div>';
        sl.querySelector('.lm-r-src').textContent = it.title;
        fillBody(sl.querySelector('.lm-r-txt'), it.m);
        scroll.appendChild(sl);
      });
      markActive();
    }

    /* Faol kartochka to'liq ko'rinadi, qo'shnilari xiralashadi — surish
       paytida "keyingisi kelyapti" hissi shundan.

       Bu ilgari `IntersectionObserver` bilan qilingan edi, lekin u ba'zan
       birinchi kartochkani ham faol deb belgilamasdan qolardi (hammasi
       xira turardi). Endi joriy raqam scroll'dan aniq hisoblanadi —
       xatosiz va bir xil ishlaydi. */
    function markActive() {
      [].forEach.call(scroll.children, function (c, k) {
        c.classList.toggle('on', k === i);
      });
    }

    function syncUI() { /* ko'rsatkich ham, hisob ham yo'q — qiladigan ish qolmadi */ }

    var tick = null;
    scroll.addEventListener('scroll', function () {
      if (tick) return;
      tick = requestAnimationFrame(function () {
        tick = null;
        var h = scroll.clientHeight || 1;
        var k = Math.round(scroll.scrollTop / h);
        if (k !== i && k >= 0 && k < items.length) { i = k; syncUI(); markActive(); }
      });
    }, { passive: true });

    function goTo(k, smooth) {
      k = Math.max(0, Math.min(items.length - 1, k));
      i = k; syncUI(); markActive();
      scroll.scrollTo({ top: k * scroll.clientHeight, behavior: smooth ? 'smooth' : 'auto' });
    }

    build();
    syncUI();

    w.querySelector('.lm-r-x').onclick = close;

    w.querySelectorAll('.lm-r-a').forEach(function (btn) {
      btn.onclick = function () {
        var it = items[i];
        var a = btn.getAttribute('data-a');
        if (a === 'open') {
          close();
          if (it.v && it.p) {
            App.go(it.v, it.p);
            setTimeout(function () { scrollToMark(it.m.id); }, 700);
          }
          return;
        }
        if (a === 'edit') {
          editMark(it.key, it.m.id, function () {
            var fresh = marksOf(it.key).find(function (x) { return x.id === it.m.id; });
            if (fresh) {
              it.m = fresh;
              var sl = scroll.children[i];
              if (sl) fillBody(sl.querySelector('.lm-r-txt'), fresh);
            }
          });
          return;
        }
        App.confirm('Bu belgi o\'chirilsinmi?', function () {
          deleteMark(it.key, it.m.id, function () {
            items.splice(i, 1);
            if (!items.length) { close(); return; }
            if (i >= items.length) i = items.length - 1;
            build();
            goTo(i, false);
            App.toast('🗑 O\'chirildi');
          });
        }, { danger: true, yes: 'O\'chirish' });
      };
    });

    function onKey(e) {
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowDown' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); goTo(i + 1, true); }
      else if (e.key === 'ArrowUp' || e.key === 'PageUp') { e.preventDefault(); goTo(i - 1, true); }
    }
    document.addEventListener('keydown', onKey);

    /* Ekran o'lchami o'zgarsa (telefonni burish) joriy kartochkada qolamiz.

       DIQQAT: bu yerda to'g'ridan-to'g'ri `goTo()` chaqirish MUMKIN EMAS.
       Telefonda sahifa surilganda brauzerning manzil paneli yig'ilib-ochiladi
       va har safar `resize` beradi — lenta o'qish paytida sakrab ketardi.
       Bundan tashqari scroll→resize→scroll aylanmasi hosil bo'lib, sahifa
       umuman qayta chizilmay qolardi (skrinshot 30 soniyada ham
       olinmadi — aynan shu sabab topilgan).

       Shuning uchun: faqat balandlik SEZILARLI o'zgarganda va kechikish
       bilan qayta tekislaymiz. */
    var lastH = window.innerHeight, resT = null;
    var onRes = function () {
      if (Math.abs(window.innerHeight - lastH) < 60) return;   // panel yig'ilishi — e'tiborsiz
      clearTimeout(resT);
      resT = setTimeout(function () {
        lastH = window.innerHeight;
        goTo(i, false);
      }, 250);
    };
    window.addEventListener('resize', onRes);

    function close() {
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', onRes);
      clearTimeout(resT);
      if (tick) cancelAnimationFrame(tick);
      document.body.classList.remove('lm-noscroll');
      w.classList.add('out');
      setTimeout(function () { w.remove(); }, 160);
    }
  }

  /* ---------------- Reels tugmasi (o'ng past) ---------------- */

  function buildFab() {
    killFab();
    var scope = fabScope();
    if (scope === undefined) return;
    var b = document.createElement('button');
    b.className = 'lm-fab';
    b.setAttribute('aria-label', 'Belgilangan joylar (Reels)');
    b.innerHTML = '<span data-icon="play" data-icon-size="21"></span><b></b>';
    document.body.appendChild(b);
    App.icons(b);
    var n = countMarks(scope);
    var cnt = b.querySelector('b');
    cnt.textContent = n || '';
    cnt.style.display = n ? '' : 'none';
    b.onclick = function () { openReels(fabScope()); };
    S.fab = b;
  }
  function killFab() { if (S.fab) { S.fab.remove(); S.fab = null; } }

  /* ---------------- keyingi mavzu ---------------- */

  var SEC_PARAM = { grammar_topic: 'lang', library_doc: 'sec', reading_doc: 'sec' };

  /* Joriy mavzuning ro'yxatdagi qo'shnisini topadi. */
  function findNext() {
    var key = SEC_PARAM[S.view];
    if (!key) return Promise.resolve(null);
    var sec = S.params[key];
    var id = String(S.params.id || '');
    if (!sec || !id) return Promise.resolve(null);

    return App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(sec) })
      .then(function (j) {
        var list = (j && (j.topics || j.items || j.list)) || (Array.isArray(j) ? j : []);
        if (!list.length) return null;
        var cur = list.find(function (t) { return String(t.id) === id; });
        if (!cur) return null;
        var folder = (cur.folder || '').trim();
        /* Tartib SERVERdan kelgani bo'yicha qoladi (`sort_order, id`) —
           ro'yxatda ham aynan shu tartib ko'rinadi, shuning uchun "keyingisi"
           foydalanuvchi ko'rgan keyingi qator bilan bir xil bo'ladi. */
        var sibs = list.filter(function (t) {
          return (t.folder || '').trim() === folder && t.name !== '__folder__';
        });
        var k = sibs.findIndex(function (t) { return String(t.id) === id; });
        if (k < 0 || k + 1 >= sibs.length) return null;
        var nx = sibs[k + 1];
        return { id: nx.id, name: nx.name, params: assign({}, S.params, { id: nx.id }) };
      })
      .catch(function () { return null; });
  }

  function assign(t) {
    for (var i = 1; i < arguments.length; i++) {
      var s = arguments[i] || {};
      Object.keys(s).forEach(function (k) { t[k] = s[k]; });
    }
    return t;
  }

  /* `findNext()` tarmoqqa boradi. Javob kelguncha foydalanuvchi boshqa
     mavzuga o'tib ketishi mumkin — o'shanda ESKI mavzuning "keyingisi"
     yangi sahifaga qo'shilib qolardi. `S.gen` har bir `attach()` da
     oshadi; javob qaytganda raqam o'zgargan bo'lsa — tashlab yuboriladi. */
  function setupNext() {
    killNext();
    if (!SEC_PARAM[S.view]) return;
    var gen = S.gen;
    findNext().then(function (nx) {
      if (!nx || gen !== S.gen) return;
      S.nextInfo = nx;
      armPull(nx);
    });
  }

  /* Matn oxirida "Keyingi mavzu — <nom>" tugmasi bor edi — OLIB TASHLANDI
     (foydalanuvchi so'rovi: keyingisiga surib o'tiladi, nomini oldindan
     yozib qo'yish shart emas). Yagona yo'l — pastda tortish jesti. */

  /* Telegram uslubidagi tortish: sahifa oxirida barmoqni yuqoriga tortib
     turilsa halqa to'ladi va qo'yib yuborilganda keyingi mavzu ochiladi. */
  function armPull(nx) {
    var el = document.createElement('div');
    el.className = 'lm-pull';
    /* Faqat halqa va strelka — mavzu nomi ATAYLAB yozilmaydi. */
    el.innerHTML =
      '<svg viewBox="0 0 44 44"><circle class="bg" cx="22" cy="22" r="19"></circle>' +
      '<circle class="fg" cx="22" cy="22" r="19"></circle></svg>' +
      '<span class="lm-pull-ic" data-icon="arrowLeft" data-icon-size="16"></span>';
    document.body.appendChild(el);
    App.icons(el);
    var ic = el.querySelector('.app-icon');
    if (ic) ic.style.transform = 'rotate(-90deg)';
    var fg = el.querySelector('.fg');
    var LEN = 2 * Math.PI * 19;
    fg.style.strokeDasharray = LEN;
    S.nextBar = el;

    /* TORTISH MASOFASI. Avval 110px edi va bu juda kam bo'lgan:
       mavzu o'qib bo'lingach sahifa oxirida oddiy surish ham keyingisiga
       "chizillab" o'tkazib yuborardi. Endi ataylab uzunroq — o'tish
       tasodifan emas, QASDDAN bo'lishi kerak. */
    var NEED = 200;              // telefonda shuncha piksel tortilsa — o'tadi

    /* Eng qisqa davomiylik: masofa yig'ilib qolsa ham, jest shundan
       tez tugasa o'tkazilmaydi. Trackpad'ning bitta silkitishi bir
       lahzada yuzlab birlik beradi — vaqt chegarasi aynan shuni to'xtatadi. */
    var MIN_MS = 420;

    var acc = 0, sy = 0, on = false, fired = false, t0 = 0;

    function atEnd() {
      var doc = document.documentElement;
      return window.innerHeight + window.scrollY >= (doc.scrollHeight - 6);
    }
    function show(p) {
      p = Math.max(0, Math.min(1, p));
      el.classList.toggle('on', p > 0.02);
      el.classList.toggle('ready', p >= 1);
      fg.style.strokeDashoffset = LEN * (1 - p);
    }
    function reset() { acc = 0; show(0); }

    function ts(e) {
      if (e.touches.length !== 1) { on = false; return; }
      sy = e.touches[0].clientY; on = atEnd(); acc = 0; fired = false;
      t0 = Date.now();
    }
    function tm(e) {
      if (!on || fired) return;
      if (!atEnd()) { reset(); on = false; return; }
      var dy = sy - e.touches[0].clientY;     // yuqoriga tortish -> musbat
      acc = Math.max(0, dy);
      show(acc / NEED);
      if (acc >= NEED && Date.now() - t0 >= MIN_MS) {
        fired = true;
        go();
      }
    }
    function te() { on = false; if (!fired) reset(); }

    function go() {
      show(1);
      if (navigator.vibrate) { try { navigator.vibrate(12); } catch (e) {} }
      setTimeout(function () { App.go(S.view, nx.params); }, 130);
    }

    document.addEventListener('touchstart', ts, { passive: true });
    document.addEventListener('touchmove', tm, { passive: true });
    document.addEventListener('touchend', te, { passive: true });

    /* Kompyuterda: oxirida g'ildirakni pastga aylantirish.

       IKKI HIMOYA BOR, ikkalasi ham kerak:
         1. Har hodisadan olinadigan ulush CHEKLANGAN (STEP_CAP). Trackpad
            va "silliq surish" bitta hodisada 300+ birlik yuborishi mumkin —
            usiz halqa bir silkitishda to'lib, mavzu o'tib ketardi.
         2. Eng qisqa davomiylik (MIN_MS): tez-tez kelgan hodisalar
            yig'ilib qolsa ham, jest juda qisqa bo'lsa o'tkazilmaydi. */
    /* Sichqoncha g'ildiragi bir "tiq"da ~100 birlik yuboradi, trackpad esa
       o'nlab mayda hodisa. Ulush 45 ga cheklangani uchun g'ildirak bilan
       ~16 marta aylantirish kerak bo'ladi — qasddan qilinadigan, lekin
       zeriktirmaydigan miqdor. */
    var WHEEL_NEED = Math.round(NEED * 3.5);
    var STEP_CAP = 45;
    var wacc = 0, wt = null, wt0 = 0;
    function onWheel(e) {
      if (!atEnd() || e.deltaY <= 0 || fired) return;
      if (wacc === 0) wt0 = Date.now();
      wacc += Math.min(e.deltaY, STEP_CAP);
      show(wacc / WHEEL_NEED);
      clearTimeout(wt);
      /* Qo'yib yuborilsa halqa asta bo'shaydi — 420ms juda tez edi,
         foydalanuvchi to'xtab o'ylab olsa yig'ilgani yo'qolardi. */
      wt = setTimeout(function () { wacc = 0; show(0); }, 900);
      if (wacc >= WHEEL_NEED && Date.now() - wt0 >= MIN_MS) { fired = true; go(); }
    }
    window.addEventListener('wheel', onWheel, { passive: true });

    S._pullOff = function () {
      document.removeEventListener('touchstart', ts);
      document.removeEventListener('touchmove', tm);
      document.removeEventListener('touchend', te);
      window.removeEventListener('wheel', onWheel);
      clearTimeout(wt);
    };
  }

  function killNext() {
    if (S._pullOff) { S._pullOff(); S._pullOff = null; }
    if (S.nextBar) { S.nextBar.remove(); S.nextBar = null; }
    S.nextInfo = null;
  }

  /* ---------------- sahifa almashuvi ---------------- */

  var ro = null;

  function teardown() {
    stopMarking();
    killDock(); killFab(); killNext();
    if (ro) { ro.disconnect(); ro = null; }
    S.md = null; S.layer = null; S.marks = [];
  }

  function docKeyOf(view, params) {
    return DOC_VIEWS[view] && params.id ? 't' + params.id : '';
  }

  function attach() {
    var view = App.currentView ? App.currentView() : '';
    var params = (App.state && App.state._lastParams) || {};
    var md = document.querySelector('#page .md-content');

    /* Qayta qurish kerakmi — YO'L (ko'rinish + parametrlar) bo'yicha
       hal qilinadi. Ilgari faqat ko'rinish nomi va hujjat kaliti
       solishtirilardi; `grammar?lang=russian` dan `grammar?lang=django` ga
       o'tilganda ikkalasi ham o'zgarmasdi (hujjat kaliti bo'sh) va funksiya
       erta qaytib ketardi — Reels tugmasi ESKI bo'limning belgilarini
       ko'rsatib turardi. */
    var sig = view + '|' + (App._serializeParams ? App._serializeParams(params) : '');
    var mdChanged = md !== S.md;
    if (sig === S.sig && !mdChanged) return;

    teardown();
    S.gen++;
    S.sig = sig;
    S.view = view;
    S.params = params;
    S.docKey = docKeyOf(view, params);
    S.md = md;

    var h1 = document.querySelector('#page .topbar h1');
    S.title = (h1 && h1.textContent.trim()) || 'Mavzu';

    if (S.md) {
      S.md.classList.add('lm-host');
      redraw();
      if (window.ResizeObserver) {
        ro = new ResizeObserver(redrawSoon);
        ro.observe(S.md);
      }
    }
    buildDock();
    buildFab();
    setupNext();
  }

  var t = null;
  function schedule() { clearTimeout(t); t = setTimeout(attach, 90); }

  function init() {
    var page = App.el('page'); if (!page) return;
    new MutationObserver(schedule).observe(page, { childList: true, subtree: true });
    window.addEventListener('resize', redrawSoon);
    window.addEventListener('remote-storage:refreshed', function () {
      if (S.md) redrawSoon();
      refreshDockCount();
    });
    /* Belgi ustiga bosilganda — o'chirish taklifi */
    document.addEventListener('click', function (e) {
      var r = e.target.closest && e.target.closest('.lm-rect[data-mark]');
      if (!r || S.marking) return;
      var id = r.getAttribute('data-mark');
      App.confirm('Bu belgi o\'chirilsinmi?', function () { removeMark(id); },
        { danger: true, yes: 'O\'chirish' });
    });
    schedule();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.LearnMarks = { open: openReels, refresh: schedule };
})();
