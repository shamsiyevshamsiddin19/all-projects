/* Navigatsiya konfiguratsiyasi + ishga tushirish */
(function () {
  'use strict';

  var NAV = [
    { v: 'home', n: 'Bosh', ic: 'home' },
    { v: 'languages', n: 'Learn', ic: 'globe' },
    { v: 'kun', n: 'Kun hisobi', bn: 'Kun', ic: 'calendar' },
    { v: 'sport', n: 'Sport', ic: 'trophy' },
    { v: 'profile', n: 'Profil', ic: 'user' },
    { v: 'goals', n: 'Maqsadlar', ic: 'check' },
    { v: 'stats', n: 'Statistika', ic: 'chart' },
    { v: 'tarix', n: 'Tarix', ic: 'clock' },
    { v: 'fanlar', n: 'Testlar', ic: 'book' },
    { v: 'coding', n: 'Coding', ic: 'code' },
    { v: 'boost', n: 'Boostday', ic: 'message' },
    { v: 'arxiv', n: 'Arxiv', ic: 'archive' },
    { v: 'qoidalar', n: 'Qoidalar', ic: 'file' },
    { v: 'settings', n: 'Sozlamalar', ic: 'settings' }
  ];
  var BOTTOM = ['home', 'languages', 'kun', 'sport', 'settings'];

  var NAV_IMG = {
    home: 1, profile: 1, goals: 1, stats: 1, tarix: 1, fanlar: 1, languages: 1, coding: 1,
    sport: 1, boost: 1, kun: 1, arxiv: 1, qoidalar: 1, settings: 1, pomodoro: 1
  };
  var NAV_IMG_V = '?v=20260820v10';       // rasm almashtirilsa shu raqam oshiriladi

  function navIcon(v, ic, size) {
    if (NAV_IMG[v]) {
      return '<img class="nav-img" src="assets/img/nav/' + v + '.svg' + NAV_IMG_V +
        '" alt="" width="' + size + '" height="' + size + '" style="width:' + size + 'px;height:' + size + 'px">';
    }
    return '<span data-icon="' + ic + '" data-icon-size="' + size + '"></span>';
  }

  /* Foydalanuvchi yashirgan bo'limlar (Sozlamalardan boshqariladi).
     'home', 'profile' va 'settings' hech qachon yashirilmaydi — aks holda qaytib bo'lmaydi. */
  function hiddenSet() {
    try {
      var v = JSON.parse(localStorage.getItem('nav_hidden_v1') || '[]');
      return Array.isArray(v) ? v.filter(function (x) { return x !== 'home' && x !== 'profile' && x !== 'settings'; }) : [];
    } catch (e) { return []; }
  }
  function visibleNav() {
    var h = hiddenSet();
    return NAV.filter(function (i) { return h.indexOf(i.v) < 0; });
  }
  window.NavConfig = { all: NAV, hidden: hiddenSet };
  // Sozlamalardan bo'lim yashirilganda menyuni darhol qayta quradi
  window.NavRebuild = function () { buildSidebar(); buildBottom(); };

  function buildSidebar() {
    var el = document.getElementById('side-nav');
    el.innerHTML = visibleNav().map(function (i) {
      return '<button class="side-link" data-nav="' + i.v + '" data-act="go" data-arg=\'' + App.arg({ v: i.v }) + '\'>' +
        navIcon(i.v, i.ic, 22) + i.n + '</button>';
    }).join('');
    
    // Global harakat tugmalari
    var pbtn = document.getElementById('global-pomo-btn');
    if (!pbtn) {
      pbtn = document.createElement('button');
      pbtn.id = 'global-pomo-btn';
      pbtn.className = 'side-link';
      pbtn.style.marginTop = 'auto';
      pbtn.style.background = 'var(--accent-soft)';
      pbtn.style.color = 'var(--accent)';
      pbtn.innerHTML = navIcon('pomodoro', 'clock', 22) + 'Pomodoro';
      pbtn.setAttribute('data-act', 'pomoToggle');
      el.appendChild(pbtn);
    }
    
    App.icons(el);
  }

  var TG_ICONS = {
    home: {
      out: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9.5L12 3l9 6.5V20a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
      fill: '<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2.5L2 9.8V20a2 2 0 0 0 2 2h5a1 1 0 0 0 1-1v-6h4v6a1 1 0 0 0 1 1h5a2 2 0 0 0 2-2V9.8L12 2.5z"/></svg>'
    },
    languages: {
      out: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
      fill: '<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M6.5 2H19a1 1 0 0 1 1 1v17.5a1 1 0 0 1-1 1H6.5A2.5 2.5 0 0 1 4 19V4.5A2.5 2.5 0 0 1 6.5 2zM6.5 17a2.5 2.5 0 0 0-2.5 2.5c0 .28.22.5.5.5H19v-3H6.5z"/></svg>'
    },
    kun: {
      out: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="3"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
      fill: '<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 4h-2V2.5a1 1 0 0 0-2 0V4H9V2.5a1 1 0 0 0-2 0V4H5a3 3 0 0 0-3 3v13a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zm1 16a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V10h16v10z"/></svg>'
    },
    sport: {
      out: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5v14M18 5v14M2 8v8M22 8v8M6 12h12"/></svg>',
      fill: '<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M6 4a1 1 0 0 0-1 1v6H3a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1h2v2a1 1 0 0 0 2 0v-6h10v6a1 1 0 0 0 2 0v-2h2a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1h-2V5a1 1 0 0 0-2 0v6H7V5a1 1 0 0 0-1-1z"/></svg>'
    },
    settings: {
      out: '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83 2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
      fill: '<svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm8 3.16-1.54-.26a6.97 6.97 0 0 0-.58-1.4l.9-1.28a1 1 0 0 0-.12-1.32l-1.92-1.92a1 1 0 0 0-1.32-.12l-1.28.9c-.45-.24-.92-.44-1.4-.58L12.5 3.6a1 1 0 0 0-1-.6h-2.72a1 1 0 0 0-1 .6l-.26 1.54c-.48.14-.95.34-1.4.58l-1.28-.9a1 1 0 0 0-1.32.12L1.6 6.86a1 1 0 0 0-.12 1.32l.9 1.28c-.24.45-.44.92-.58 1.4L.26 11.16a1 1 0 0 0-.6 1v2.72c0 .48.34.88.8.98l1.54.26c.14.48.34.95.58 1.4l-.9 1.28a1 1 0 0 0 .12 1.32l1.92 1.92a1 1 0 0 0 1.32.12l1.28-.9c.45.24.92.44 1.4.58l.26 1.54a1 1 0 0 0 1 .6h2.72a1 1 0 0 0 1-.6l.26-1.54c.48-.14.95-.34 1.4-.58l1.28.9a1 1 0 0 0 1.32-.12l1.92-1.92a1 1 0 0 0 .12-1.32l-.9-1.28c.24-.45.44-.92.58-1.4l1.54-.26a1 1 0 0 0 .6-1v-2.72a1 1 0 0 0-.6-.98z"/></svg>'
    }
  };

  function buildBottom() {
    var el = document.getElementById('botnav');
    var h = hiddenSet();
    el.innerHTML = BOTTOM.filter(function (v) { return v === '__more__' || h.indexOf(v) < 0; }).map(function (v) {
      if (v === '__more__') {
        return '<a data-nav="__more__" data-act="moreMenu"><span class="tg-tab-ic"><span data-icon="menu" data-icon-size="22"></span></span><span>Yana</span></a>';
      }
      var i = NAV.find(function (x) { return x.v === v; }) || { n: v, ic: 'user' };
      var tg = TG_ICONS[v];
      var iconHtml = tg
        ? '<span class="tg-tab-ic"><span class="tg-ic-out">' + tg.out + '</span><span class="tg-ic-fill">' + tg.fill + '</span></span>'
        : '<span class="tg-tab-ic">' + navIcon(v, i.ic || 'user', 24) + '</span>';
      return '<a data-nav="' + v + '" data-act="go" data-arg=\'' + App.arg({ v: v }) + '\'>' +
        iconHtml + '<span>' + (i.bn || i.n) + '</span></a>';
    }).join('');
    App.icons(el);
  }

  App.actions.moreMenu = function () {
    var h = hiddenSet();
    // Pastki panelga sig'magan + yashirilmagan barcha bo'limlar
    var items = NAV.map(function (i) { return i.v; })
      .filter(function (v) { return BOTTOM.indexOf(v) < 0 && h.indexOf(v) < 0; })
      .concat(['settings']);
    items = items.filter(function (v, i) { return items.indexOf(v) === i; });
    var html = items.map(function (v) {
      var i = NAV.find(function (x) { return x.v === v; });
      return '<button class="list-row" data-act="goClose" data-arg=\'' + App.arg({ v: v }) + '\'>' +
        '<span class="li-ic nav-ic-img">' + navIcon(v, i.ic, 20) + '</span>' +
        '<div class="li-main"><div class="li-title">' + i.n + '</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
    }).join('');
    App.sheet(html, { title: 'Menyu' });
  };
  App.actions.goClose = function (a) { App.closeSheet(); App.go(a.v); };

  /* Belgini serverga BIR MARTA ko'chirish (o'zini o'zi tuzatish).
     Muammo: `save_app_icon` chaqiruvi kodga keyinroq qo'shilgan, shuning uchun
     undan OLDIN belgi qo'ygan foydalanuvchida rasm faqat localStorage'da qoladi —
     serverdagi PNG va manifest esa eski holicha turadi (telefon bosh ekranidagi
     yorliqda va yangi qurilmada eski belgi ko'rinadi). `app_icon_version` yo'qligi
     aynan shu holatni bildiradi: bir marta yuboramiz va versiyani saqlaymiz. */
  function syncIconToServer() {
    try {
      if (localStorage.getItem('app_icon_version')) return;         // allaqachon yuborilgan
      var full = localStorage.getItem('app_custom_icon');
      if (!full || full.indexOf('data:image/') !== 0) return;        // yuborishga narsa yo'q
      App.call('save_app_icon', { icon: full })
        .then(function (r) {
          if (r && r.version) localStorage.setItem('app_icon_version', String(r.version));
          App.applyAppIcon();
        })
        .catch(function () {});   // jimgina: bu fon vazifasi, foydalanuvchini bezovta qilmaydi
    } catch (e) {}
  }

  function boot() {
    // Serverdan sinxronlangan belgini hamma joyga qo'llaymiz (yangi qurilmada ham to'g'ri chiqsin)
    App.applyAppIcon();
    syncIconToServer();
    buildSidebar();
    buildBottom();
    bindDial();
    bindSwipe();
    App.boot();
    var sp = document.getElementById('splash');
    if (sp) { sp.classList.add('gone'); setTimeout(function () { sp.remove(); }, 350); }
  }

  // Storage bridge tayyor bo'lgach ishga tushiramiz (localStorage server bilan sinxron)
  function afterAuth() {
    if (window.RemoteStorageBridge && window.RemoteStorageBridge.whenReady) {
      var done = false, safetyFired = false;
      var go = function () { if (done) return; done = true; boot(); };
      window.RemoteStorageBridge.whenReady().then(function () {
        go();
        /* Xavfsizlik chegarasi (pastda, 4000ms) ALLAQACHON ishga tushirgan
           bo'lsa — bootstrap SEKIN javob berdi, ya'ni ilova localStorage
           hali TO'LIQ sinxronlanmagan holda chizilgan. Masalan foydalanuvchi
           qo'shgan maxsus tillar (custom_langs) ko'rinmay qolardi va hech
           qachon o'zi tuzalmasdi — yangi sahifaga o'tilgunga qadar. Endi
           bootstrap oxiri kelganda joriy bo'lim QAYTA chiziladi. */
        if (safetyFired) { try { App.reload(); } catch (e) {} }
      }).catch(go);
      setTimeout(function () { safetyFired = true; go(); }, 4000);
    } else {
      boot();
    }
  }

  /* Ko'prik endi mahalliy SURATdan darhol tayyor bo'ladi (remote-storage.js),
     ya'ni yuqoridagi `whenReady()` tarmoqni kutmaydi. Serverdagi holat orqa
     fonda kelib SURATDAN FARQ qilsa — menyu va joriy bo'lim qayta chiziladi.
     Odatda farq bo'lmaydi va foydalanuvchi hech narsa sezmaydi; boshqa
     qurilmada o'zgarish bo'lgan bo'lsa, u bir lahzada o'zi paydo bo'ladi. */
  window.addEventListener('remote-storage:refreshed', function () {
    try {
      buildSidebar();
      buildBottom();
      App.reload();
    } catch (e) {}
  });

  /* ============================================================
     BO'LIMLAR ORASIDA JEST BILAN O'TISH
     Ikki yo'l, bitta ro'yxat ustida ishlaydi (`visibleNav()` tartibi):
       1) Pastki paneldagi tugmani BOSIB TURIB barmoqni o'ngga/chapga surish
          — iPhone kamerasidagi rejim g'ildiragi kabi (g'ildirak ko'rinadi,
          qo'yib yuborilganda tanlangan bo'limga o'tadi);
       2) Sahifani o'ngga/chapga SURISH — Telegram jildlari kabi.
     ============================================================ */

  function navList() { return visibleNav().map(function (i) { return i.v; }); }

  /* Joriy bo'lim ro'yxatdagi qaysi o'rinda. Ko'rinish o'z `nav` nomiga ega
     bo'lishi mumkin (masalan `reading_doc` -> `languages`), shuning uchun
     avval faol tugmadan o'qiymiz. */
  function currentIndex(list) {
    var active = document.querySelector('.botnav a.active, .side-link.active');
    var v = active ? active.getAttribute('data-nav') : null;
    if (!v || v === '__more__') v = App.currentView && App.currentView();
    var i = list.indexOf(v);
    return i < 0 ? 0 : i;
  }

  function goIndex(list, i) {
    i = Math.max(0, Math.min(list.length - 1, i));
    if (list[i]) App.go(list[i]);
  }

  /* ---------- Surib almashtirish: QAT'IY BESH BO'LIMLI YO'L ----------
     Faqat shu yo'lda ishlaydi va chetidan CHIQMAYDI:

         Kun hisobi <- Arxiv <- [BOSH SAHIFA] -> Maqsad -> Statistika

     Ikki qoida:
       1) Ro'yxatdan TASHQARIDAGI bo'limda (Sport, Boostday, Learn...)
          surish umuman ishlamaydi — o'sha bo'limlarning o'z gorizontal
          elementlari bor va tasodifiy o'tib ketish bezovta qilardi.
       2) Aylanma EMAS: `Statistika` dan o'ngga yoki `Kun hisobi` dan
          chapga surilsa hech qayerga o'tmaydi.

     Ro'yxat `navList()` dan MUSTAQIL: bu ataylab qisqa, tez-tez ochiladigan
     bo'limlar yo'li — yon paneldagi to'liq tartib bilan aralashtirilmaydi. */
  var SWIPE_PATH = ['home', 'languages', 'kun', 'sport', 'settings'];

  /* Joriy bo'lim shu yo'lning qaysi o'rnida (-1 = yo'lda yo'q). */
  function swipeIndex() {
    var active = document.querySelector('.botnav a.active, .side-link.active');
    var v = active ? active.getAttribute('data-nav') : null;
    if (!v || v === '__more__') v = App.currentView && App.currentView();
    return SWIPE_PATH.indexOf(v);
  }

  /* ---------- 1) Pastki paneldagi g'ildirak ---------- */
  var DIAL = null;   // { list, start, idx, startIdx, el, moved }
  var STEP = 44;     // necha px surilganda bitta bo'lim almashadi

  function dialOverlay() {
    var el = document.getElementById('nav-dial');
    if (!el) {
      el = document.createElement('div');
      el.id = 'nav-dial';
      el.className = 'nav-dial';
      document.body.appendChild(el);
    }
    return el;
  }

  function paintDial() {
    if (!DIAL) return;
    var el = DIAL.el, list = DIAL.list;
    el.innerHTML = '<div class="nd-strip">' + list.map(function (v, i) {
      var item = NAV.find(function (x) { return x.v === v; }) || { n: v, ic: 'home' };
      return '<div class="nd-item' + (i === DIAL.idx ? ' on' : '') + '">' +
        '<span class="nd-ic">' + navIcon(item.v || v, item.ic, 24) + '</span>' +
        '<span class="nd-n">' + App.esc(item.n) + '</span></div>';
    }).join('') + '</div>';
    App.icons(el);
    // Tanlangan element markazga keladi
    var strip = el.querySelector('.nd-strip');
    var cur = el.querySelectorAll('.nd-item')[DIAL.idx];
    if (strip && cur) {
      strip.style.transform = 'translateX(' + (el.offsetWidth / 2 - cur.offsetLeft - cur.offsetWidth / 2) + 'px)';
    }
  }

  function dialEnd(commit) {
    if (!DIAL) return;
    var d = DIAL; DIAL = null;
    d.el.classList.remove('show');
    setTimeout(function () { if (!DIAL && d.el.parentNode) d.el.remove(); }, 200);
    if (commit && d.moved && d.idx !== d.startIdx) goIndex(d.list, d.idx);
  }

  function bindDial() {
    var nav = document.getElementById('botnav');
    if (!nav || nav._dialBound) return;
    nav._dialBound = true;

    /* Uzoq bosilganda chiqadigan "nusxa olish / tanlash" menyusi barmoq
       harakatini o'g'irlab, g'ildirakni aylantirishga xalaqit berardi. */
    nav.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    nav.addEventListener('selectstart', function (e) { e.preventDefault(); });
    nav.addEventListener('dragstart', function (e) { e.preventDefault(); });

    nav.addEventListener('touchstart', function (e) {
      if (e.touches.length !== 1) return;
      var list = navList();
      if (list.length < 2) return;
      DIAL = {
        list: list, startX: e.touches[0].clientX,
        startIdx: currentIndex(list), idx: currentIndex(list),
        el: dialOverlay(), moved: false
      };
      // Tanlash boshlanib qolgan bo'lsa bekor qilamiz
      try { var sel = window.getSelection && window.getSelection(); if (sel && sel.removeAllRanges) sel.removeAllRanges(); } catch (x) {}
    }, { passive: true });

    nav.addEventListener('touchmove', function (e) {
      if (!DIAL || e.touches.length !== 1) return;
      var dx = e.touches[0].clientX - DIAL.startX;
      if (!DIAL.moved) {
        if (Math.abs(dx) < 12) return;      // oddiy bosishni buzmaymiz
        DIAL.moved = true;
        DIAL.el.classList.add('show');
      }
      // Surish YO'NALISHI: o'ngga -> ro'yxat bo'ylab oldinga
      var next = DIAL.startIdx + Math.round(dx / STEP);
      next = Math.max(0, Math.min(DIAL.list.length - 1, next));
      if (next !== DIAL.idx) {
        DIAL.idx = next;
        if (navigator.vibrate) { try { navigator.vibrate(8); } catch (x) {} }
      }
      paintDial();
      e.preventDefault();                    // sahifa siljimasin
    }, { passive: false });

    nav.addEventListener('touchend', function () { dialEnd(true); }, { passive: true });
    nav.addEventListener('touchcancel', function () { dialEnd(false); }, { passive: true });
  }

  /* ---------- 2) Sahifani surish (Telegram jildlari kabi) ---------- */
  function bindSwipe() {
    var page = document.getElementById('page');
    if (!page || page._swipeBound) return;
    page._swipeBound = true;

    var sx = 0, sy = 0, on = false;

    /* Gorizontal siljiydigan yoki matn tanlanadigan joylarda ishlamasin —
       aks holda heatmap lentasi, chiplar va inputlar buzilardi. */
    function blocked(t) {
      if (!t || !t.closest) return true;
      if (t.closest('input,textarea,select,.sheet,.rd-pop,.rd-player')) return true;
      var el = t;
      while (el && el !== page) {
        if (el.scrollWidth > el.clientWidth + 4) {
          var ox = getComputedStyle(el).overflowX;
          if (ox === 'auto' || ox === 'scroll') return true;
        }
        el = el.parentElement;
      }
      return false;
    }

    page.addEventListener('touchstart', function (e) {
      if (e.touches.length !== 1 || blocked(e.target)) { on = false; return; }
      // Yo'ldan tashqaridagi bo'limda umuman kuzatmaymiz
      if (swipeIndex() < 0) { on = false; return; }
      sx = e.touches[0].clientX; sy = e.touches[0].clientY;
      on = true;
    }, { passive: true });

    page.addEventListener('touchend', function (e) {
      if (!on) return;
      on = false;
      var t = e.changedTouches[0];
      var dx = t.clientX - sx, dy = t.clientY - sy;
      // Aniq gorizontal harakat bo'lsagina: uzunligi yetarli va burchagi tor
      if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.6) return;

      var i = swipeIndex();
      if (i < 0) return;
      // Barmoq chapga -> o'ngdagi bo'lim (Maqsad, Statistika)
      // Barmoq o'ngga -> chapdagi bo'lim (Arxiv, Kun hisobi)
      var j = dx < 0 ? i + 1 : i - 1;
      if (j < 0 || j >= SWIPE_PATH.length) return;   // chetdan chiqmaydi
      App.go(SWIPE_PATH[j]);
    }, { passive: true });
  }

  // Avval kirish tekshiriladi — kirilmagan bo'lsa ilova umuman ochilmaydi.
  function start() {
    // 1) Darhol: localStorage'da belgi bo'lsa qo'llaymiz (sidebar inline skriptdan keyin turadi).
    App.applyTheme();
    App.applyAppIcon();
    // 2) Serverdan sinxronlash tugagach yana qo'llaymiz — yangi qurilmada localStorage
    //    dastlab bo'sh bo'ladi, belgi faqat shundan keyin paydo bo'ladi. Bu kirish
    //    ekranida ham to'g'ri chiqishi uchun auth'dan mustaqil ishlaydi.
    if (window.RemoteStorageBridge && window.RemoteStorageBridge.whenReady) {
      window.RemoteStorageBridge.whenReady()
        .then(function () { App.applyTheme(); App.applyAppIcon(); })
        .catch(function () {});
    }
    if (window.Auth && window.Auth.gate) window.Auth.gate(afterAuth);
    else afterAuth();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();

  // Service worker
  if ('serviceWorker' in navigator) {
    /* SW o'qish javoblarini keshdan DARHOL beradi, yangisini esa orqa fonda
       oladi. Yangisi eskisidan farq qilsa shu xabar keladi — joriy bo'lim
       o'zi jimgina yangilanadi (foydalanuvchi hech narsa bosmaydi). */
    navigator.serviceWorker.addEventListener('message', function (e) {
      if (e.data && e.data.type === 'data-updated') App._onDataUpdated();
    });

    window.addEventListener('load', function () {
      navigator.serviceWorker.register('service-worker.js').then(function (reg) {
        /* Kesh yetarlimi? Brauzer joy bo'shatish uchun uni tozalab yuborishi
           mumkin — bunda ilova internetsiz ochilmay qoladi. Kam bo'lsa SW dan
           qayta to'ldirishni so'raymiz (yetarli bo'lsa hech narsa qilmaymiz —
           har yuklanishda fayllarni bekorga qayta yuklamaslik uchun). */
        if (!window.caches) return;
        caches.keys().then(function (keys) {
          var shell = keys.filter(function (k) { return k.indexOf('yordamchi-shell') === 0; })[0];
          function ask() {
            var sw = reg.active || navigator.serviceWorker.controller;
            if (sw) sw.postMessage('precache');
          }
          if (!shell) { ask(); return; }
          caches.open(shell).then(function (c) { return c.keys(); })
            .then(function (list) { if (list.length < 10) ask(); });
        }).catch(function () {});
      }).catch(function () {});
    });
  }

  /* ---------------- Oflayn rejim ----------------
     Ilova internetsiz ham ishlaydi: app shell va oxirgi o'qilgan ma'lumot
     service worker keshida, mahalliy o'zgarishlar esa localStorage'da
     (remote-storage ko'prigi ularni navbatga qo'yib, ulanish tiklanganda
     serverga yuboradi). Bu yerda faqat ikki narsa:
       1) foydalanuvchiga holatni ko'rsatish,
       2) ulanish qaytganda navbatni DARHOL bo'shatish. */

  function offlineBar() {
    var el = document.getElementById('offline-bar');
    if (!el) {
      el = document.createElement('div');
      el.id = 'offline-bar';
      el.innerHTML = '<span class="ob-dot"></span><span class="ob-t"></span>';
      document.body.appendChild(el);
    }
    return el;
  }

  function showOffline() {
    var el = offlineBar();
    el.querySelector('.ob-t').textContent = 'Internet yo\'q — oflayn rejim';
    el.classList.remove('back');
    el.classList.add('show');
  }

  function showBack() {
    var el = offlineBar();
    el.querySelector('.ob-t').textContent = 'Internet tiklandi — sinxronlanmoqda';
    el.classList.add('show', 'back');
    // Navbatdagi o'zgarishlarni darhol yuboramiz (ilgari faqat sahifa
    // yashirilganda/yopilganda yuborilardi — ulanish qaytgani sezilmasdi).
    try {
      if (window.RemoteStorageBridge && window.RemoteStorageBridge.flush) {
        window.RemoteStorageBridge.flush();
      }
    } catch (e) {}
    setTimeout(function () { el.classList.remove('show'); }, 2600);
  }

  window.addEventListener('offline', showOffline);
  window.addEventListener('online', showBack);
  if (!navigator.onLine) showOffline();
})();
