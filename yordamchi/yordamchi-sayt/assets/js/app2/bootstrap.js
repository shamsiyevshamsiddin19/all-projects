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
  var BOTTOM = ['home', 'kun', 'languages', 'sport', 'settings'];

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
  /* Sozlamalar bo'limiga kira oladimi. Standart `ruxsatlar`
     (`["home","languages","fanlar","stats"]`) ichida `settings` YO'Q —
     ya'ni oddiy foydalanuvchi Sozlamalarni umuman ocholmaydi. Chiqish
     tugmasi esa FAQAT o'sha sahifada edi, natijada ular tizimdan
     chiqa olmasdi. Shuning uchun chiqishni menyuga ham qo'shamiz. */
  function canOpenSettings() {
    if (!window.Auth || typeof Auth.isAllowed !== 'function') return true;
    return Auth.isAllowed('settings');
  }

  function logoutRowHtml() {
    return '<button class="list-row" data-act="logout" style="color:var(--danger);margin-top:8px">' +
      '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" ' +
      'data-icon="lock" data-icon-size="20"></span>' +
      '<div class="li-main"><div class="li-title" style="color:var(--danger)">' +
      'Tizimdan chiqish</div></div></button>';
  }

  function isAdminUser() {
    return !window.Auth || typeof Auth.isAdmin !== 'function' || Auth.isAdmin();
  }

  /* Oddiy foydalanuvchida menyu tartibini `ruxsatlar` belgilaydi — admin
     bergan ketma-ketlik (Bosh, Testlar, Learn, Statistika, Profil) yon
     menyuda ham bir xil ko'rinsin. Adminda NAV tartibi o'zgarmaydi. */
  function orderForUser(list) {
    if (isAdminUser()) return list;
    var r = (window.Auth && Auth.user && Auth.user.ruxsatlar) || null;
    if (!Array.isArray(r) || r.indexOf('*') >= 0) return list;
    return list.slice().sort(function (a, b) {
      var ia = r.indexOf(a.v), ib = r.indexOf(b.v);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
  }

  function visibleNav() {
    var h = hiddenSet();
    return orderForUser(NAV.filter(function (i) {
      if (h.indexOf(i.v) >= 0) return false;
      if (window.Auth && typeof Auth.isAllowed === 'function') {
        return Auth.isAllowed(i.v);
      }
      return true;
    }));
  }
  window.NavConfig = { all: NAV, hidden: hiddenSet };
  // Sozlamalardan bo'lim yashirilganda menyuni darhol qayta quradi
  window.NavRebuild = function () { buildSidebar(); buildBottom(); };

  var SIDE_ICONS = {
    home: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M3 4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4zm10 0a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-6a1 1 0 0 1-1-1V4zM3 14a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6zm10-2a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1h-6a1 1 0 0 1-1-1v-8z"/></svg>',
    languages: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 4.5C9.5 2.8 6 2.5 3 3v14c3-.5 6.5-.2 9 1.5 2.5-1.7 6-2 9-1.5V3c-3-.5-6.5-.2-9 1.5zm-1 12c-2.3-1.1-5.2-1.3-7.5-.8V4.8c2.2-.4 5-.2 7.5.9v10.8zm9.5-.8c-2.3-.5-5.2-.3-7.5.8V5.7c2.5-1.1 5.3-1.3 7.5-.9v10.9z"/></svg>',
    kun: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 4h-1V2h-2v2H8V2H6v2H5a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3h14a3 3 0 0 0 3-3V7a3 3 0 0 0-3-3zm1 15a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-9h16v9zm0-11H4V7a1 1 0 0 1 1-1h1v1h2V6h8v1h2V6h1a1 1 0 0 1 1 1v1z"/><circle cx="8" cy="13" r="1.2"/><circle cx="12" cy="13" r="1.2"/><circle cx="16" cy="13" r="1.2"/><circle cx="8" cy="17" r="1.2"/><circle cx="12" cy="17" r="1.2"/><circle cx="16" cy="17" r="1.2"/></svg>',
    sport: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M20.5 7h-1.8a4.9 4.9 0 0 0-1.4-2.5l1.3-1.3a1 1 0 0 0-1.4-1.4L15.9 3.1A4.9 4.9 0 0 0 13.4 1.7V.5a1 1 0 0 0-2 0v1.2a4.9 4.9 0 0 0-2.5 1.4L7.6 1.8a1 1 0 0 0-1.4 1.4l1.3 1.3A4.9 4.9 0 0 0 6.1 7H4.3A2.3 2.3 0 0 0 2 9.3v5.4A2.3 2.3 0 0 0 4.3 17h1.8a4.9 4.9 0 0 0 1.4 2.5l-1.3 1.3a1 1 0 0 0 1.4 1.4l1.3-1.3a4.9 4.9 0 0 0 2.5 1.4v1.2a1 1 0 0 0 2 0v-1.2a4.9 4.9 0 0 0 2.5-1.4l1.3 1.3a1 1 0 0 0 1.4-1.4l-1.3-1.3a4.9 4.9 0 0 0 1.4-2.5h1.8a2.3 2.3 0 0 0 2.3-2.3V9.3A2.3 2.3 0 0 0 20.5 7zM6 13.5v-3c0-.3.2-.5.5-.5h1.1a4.9 4.9 0 0 0 0 4H6.5a.5.5 0 0 1-.5-.5zm12 0c0 .3-.2.5-.5.5h-1.1a4.9 4.9 0 0 0 0-4h1.1c.3 0 .5.2.5.5v3z"/></svg>',
    profile: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8V21a.6.6 0 0 0 .6.6h18a.6.6 0 0 0 .6-.6v-1.8c0-3.2-6.4-4.8-9.6-4.8z"/></svg>',
    goals: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm0-13a5 5 0 1 0 5 5 5 5 0 0 0-5-5zm0 8a3 3 0 1 1 3-3 3 3 0 0 1-3 3zm0-4a1 1 0 1 0 1 1 1 1 0 0 0-1-1z"/></svg>',
    stats: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M4 19h16a1 1 0 0 0 0-2H4a1 1 0 0 0 0 2zm1-5h3a1 1 0 0 0 1-1V9a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v4a1 1 0 0 0 1 1zm6 0h3a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1h-3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1zm6 0h3a1 1 0 0 0 1-1v-6a1 1 0 0 0-1-1h-3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1z"/></svg>',
    tarix: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8zm.8-13H11v6.2l4.8 2.8.8-1.3-4.1-2.4V7z"/></svg>',
    fanlar: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-3 2v6l-2.5-1.5L11 11V5h5zm-9 4h2v2H7V9zm0 4h7v2H7v-2zm10 4H7v-2h10v2z"/></svg>',
    coding: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M8.7 15.3L4.4 11l4.3-4.3a1 1 0 0 0-1.4-1.4l-5 5a1 1 0 0 0 0 1.4l5 5a1 1 0 0 0 1.4-1.4zm6.6-8.6l4.3 4.3-4.3 4.3a1 1 0 0 0 1.4 1.4l5-5a1 1 0 0 0 0-1.4l-5-5a1 1 0 0 0-1.4 1.4zm-4.7 12a1 1 0 0 0 1.2-.7l3-12a1 1 0 0 0-1.9-.5l-3 12a1 1 0 0 0 .7 1.2z"/></svg>',
    boost: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M13 2L4 13.5h6L9 22l11-12.5h-7L13 2z"/></svg>',
    arxiv: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M20 4H4a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-9a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zM4 6h16v2H4V6zm14 13H6v-9h12v9zm-3-6H9a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2z"/></svg>',
    qoidalar: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 12h8v2H8v-2zm0 4h8v2H8v-2z"/></svg>',
    settings: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm8.6 3.2l-1.8-.3a6.7 6.7 0 0 0-.6-1.5l1.1-1.5a1 1 0 0 0-.1-1.3l-1.9-1.9a1 1 0 0 0-1.3-.1l-1.5 1.1a6.7 6.7 0 0 0-1.5-.6l-.3-1.8a1 1 0 0 0-1-.8h-2.6a1 1 0 0 0-1 .8l-.3 1.8a6.7 6.7 0 0 0-1.5.6L7.3 4.8a1 1 0 0 0-1.3.1L4.1 6.8a1 1 0 0 0-.1 1.3l1.1 1.5a6.7 6.7 0 0 0-.6 1.5l-1.8.3a1 1 0 0 0-.8 1v2.6a1 1 0 0 0 .8 1l1.8.3a6.7 6.7 0 0 0 .6 1.5l-1.1 1.5a1 1 0 0 0 .1 1.3l1.9 1.9a1 1 0 0 0 1.3.1l1.5-1.1a6.7 6.7 0 0 0 1.5.6l.3 1.8a1 1 0 0 0 1 .8h2.6a1 1 0 0 0 1-.8l.3-1.8a6.7 6.7 0 0 0 1.5-.6l1.5 1.1a1 1 0 0 0 1.3-.1l1.9-1.9a1 1 0 0 0 .1-1.3l-1.1-1.5a6.7 6.7 0 0 0 .6-1.5l1.8-.3a1 1 0 0 0 .8-1v-2.6a1 1 0 0 0-.8-1z"/></svg>'
  };

  function buildSidebar() {
    var el = document.getElementById('side-nav');
    if (!el) return;
    el.innerHTML = visibleNav().map(function (i) {
      var ic = SIDE_ICONS[i.v] || ('<span data-icon="' + (i.ic || 'circle') + '" data-icon-size="20"></span>');
      return '<button class="side-link" data-nav="' + i.v + '" data-act="go" data-arg=\'' + App.arg({ v: i.v }) + '\'>' +
        '<span class="side-rail-slot">' + ic + '</span>' +
        '<span class="side-link-txt">' + i.n + '</span></button>';
    }).join('');
    
    var oldPomo = document.getElementById('global-pomo-btn');
    if (oldPomo) oldPomo.remove();

    App.icons(el);
  }

  var BOT_ICONS = {
    home: '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2.1L2.8 9.5a1.2 1.2 0 0 0-.4.9v10a1.6 1.6 0 0 0 1.6 1.6h4.5a1 1 0 0 0 1-1v-5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v5a1 1 0 0 0 1 1h4.5a1.6 1.6 0 0 0 1.6-1.6v-10a1.2 1.2 0 0 0-.4-.9L12 2.1z"/></svg>',
    kun: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2.5"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    languages: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    sport: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5v14M18 5v14M2 8v8M22 8v8M6 12h12"/></svg>',
    settings: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    profile: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    stats: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>',
    fanlar: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>'
  };

  function buildBottom() {
    var el = document.getElementById('botnav');
    if (!el) return;
    
    // Foydalanuvchi tanlagan qat'iy tartib:
    // 1: Bosh sahifa, 2: Kun hisobi
    // 3: Learn (Markaziy ko'tarilgan + FAB tugmasi)
    // 4: Sport, 5: Sozlamalar
    var leftItems = ['home', 'kun'];
    var rightItems = ['sport', 'settings'];

    /* Oddiy foydalanuvchida `kun`, `sport`, `settings` ga ruxsat YO'Q —
       ular filtrdan tushib, pastda faqat "Bosh + Learn" qolardi.
       Ularga o'z to'plami:
       1 Bosh · 2 Testlar · 3 Learn (markazdagi FAB) · 4 Statistika · 5 Profil */
    if (!isAdminUser()) {
      leftItems = ['home', 'fanlar'];
      rightItems = ['stats', 'profile'];
    }

    if (window.Auth && typeof Auth.isAllowed === 'function') {
      leftItems = leftItems.filter(function (v) { return Auth.isAllowed(v); });
      rightItems = rightItems.filter(function (v) { return Auth.isAllowed(v); });
    }

    function itemHtml(v) {
      var i = NAV.find(function (x) { return x.v === v; }) || { n: v, ic: 'user' };
      var ic = BOT_ICONS[v] || ('<span data-icon="' + (i.ic || 'circle') + '" data-icon-size="20"></span>');
      return '<a class="botnav-item" data-nav="' + v + '" data-act="go" data-arg=\'' + App.arg({ v: v }) + '\' title="' + App.esc(i.n) + '" aria-label="' + App.esc(i.n) + '">' +
        '<span class="botnav-ic">' + ic + '</span>' +
        '<span class="botnav-dot"></span>' +
      '</a>';
    }

    var fabHtml = '<div class="botnav-fab-slot">' +
      '<a class="botnav-fab" data-nav="languages" data-act="go" data-arg=\'' + App.arg({ v: 'languages' }) + '\' aria-label="Learn" title="Learn">' +
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round">' +
          '<line x1="12" y1="5" x2="12" y2="19"/>' +
          '<line x1="5" y1="12" x2="19" y2="12"/>' +
        '</svg>' +
      '</a>' +
    '</div>';

    el.innerHTML = leftItems.map(itemHtml).join('') + fabHtml + rightItems.map(itemHtml).join('');
    App.icons(el);
  }

  App.actions.moreMenu = function () {
    var h = hiddenSet();
    // Pastki panelga sig'magan + yashirilmagan barcha bo'limlar
    var items = NAV.map(function (i) { return i.v; })
      .filter(function (v) {
        if (BOTTOM.indexOf(v) >= 0 || h.indexOf(v) >= 0) return false;
        if (window.Auth && typeof Auth.isAllowed === 'function') return Auth.isAllowed(v);
        return true;
      });
    if (!window.Auth || typeof Auth.isAdmin !== 'function' || Auth.isAdmin()) {
      if (items.indexOf('settings') < 0) items.push('settings');
    }
    items = items.filter(function (v, i) { return items.indexOf(v) === i; });
    var html = '<div class="more-menu-grid">' + items.map(function (v) {
      var i = NAV.find(function (x) { return x.v === v; });
      var ic = SIDE_ICONS[v] || ('<span data-icon="' + (i.ic || 'circle') + '" data-icon-size="20"></span>');
      return '<button class="more-menu-item" data-act="goClose" data-arg=\'' + App.arg({ v: v }) + '\'>' +
        '<span class="more-menu-ic">' + ic + '</span>' +
        '<span class="more-menu-txt">' + i.n + '</span></button>';
    }).join('') + '</div>' + logoutRowHtml();
    App.sheet(html, { title: 'Barcha bo\'limlar' });
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
          surish umuman ishlaydi — o'sha bo'limlarning o'z gorizontal
          elementlari bor va tasodifiy o'tib ketish bezovta qilardi.
       2) Aylanma EMAS: `Statistika` dan o'ngga yoki `Kun hisobi` dan
          chapga surilsa hech qayerga o'tmaydi.

     Ro'yxat `navList()` dan MUSTAQIL: bu ataylab qisqa, tez-tez ochiladigan
     bo'limlar yo'li. Learn va uning ichki sahifalarida surish xalaqit
     bermasligi uchun 'languages' va barcha o'rganish bo'limlarida surish o'chirilgan. */
  var SWIPE_PATH = ['home', 'kun', 'sport', 'settings'];

  var LEARN_VIEWS = [
    'languages', 'english', 'russian', 'grammar', 'grammar_topic',
    'vocab', 'vocab_browse', 'vocab_practice', 'library', 'library_doc',
    'reading_doc', 'listening_doc', 'coding', 'qoidalar', 'test_results'
  ];

  function isLearnView(v) {
    if (!v) return false;
    return LEARN_VIEWS.indexOf(v) >= 0 || v.indexOf('lang_') === 0 || v.indexOf('ru_') === 0 || v.indexOf('en_') === 0;
  }

  /* Joriy bo'lim shu yo'lning qaysi o'rnida (-1 = yo'lda yo'q). */
  function swipeIndex() {
    var cur = App.currentView && App.currentView();
    if (isLearnView(cur)) return -1;
    var active = document.querySelector('.botnav a.active, .side-link.active');
    var v = active ? active.getAttribute('data-nav') : null;
    if (!v || v === '__more__') v = cur;
    if (isLearnView(v)) return -1;
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
    nav.addEventListener('touchstart', function (e) {
      if (e.touches.length !== 1) return;
      var cur = App.currentView && App.currentView();
      if (isLearnView(cur)) return;
      var t = e.touches[0];
      var list = dialList();
      var active = document.querySelector('.botnav a.active, .side-link.active');
      var v = active ? active.getAttribute('data-nav') : null;
      if (!v || v === '__more__') v = cur;
      var idx = list.indexOf(v);
      if (idx < 0) idx = 0;
      DIAL = {
        list: list,
        startX: t.clientX,
        idx: idx,
        startIdx: idx,
        el: dialOverlay(),
        moved: false,
        suppressClickUntil: 0,
      };
      DIAL.el.classList.add('show');
      paintDial();
    }, { passive: true });

    nav.addEventListener('touchmove', function (e) {
      if (!DIAL || e.touches.length !== 1) return;
      var dx = e.touches[0].clientX - DIAL.startX;
      if (Math.abs(dx) > 10) DIAL.moved = true;
      var steps = Math.round(dx / STEP);
      var next = Math.max(0, Math.min(DIAL.list.length - 1, DIAL.startIdx + steps));
      if (next !== DIAL.idx) {
        DIAL.idx = next;
        paintDial();
      }
    }, { passive: true });

    nav.addEventListener('touchend', function () {
      if (DIAL && DIAL.moved) DIAL.suppressClickUntil = Date.now() + 350;
      dialEnd(true);
    }, { passive: true });

    nav.addEventListener('touchcancel', function () { dialEnd(false); }, { passive: true });

    nav.addEventListener('click', function (e) {
      if (DIAL && DIAL.suppressClickUntil && Date.now() < DIAL.suppressClickUntil) {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);
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
      var cur = App.currentView && App.currentView();
      if (isLearnView(cur)) return true;
      if (document.querySelector('.page-languages, .page-grammar, .page-vocab, .page-library, .page-reading, .page-coding')) return true;
      if (!t || !t.closest) return true;
      if (t.closest('input,textarea,select,.sheet,.rd-pop,.rd-player,.vocab-screen,.reading-screen,.grammar-view,.page-languages')) return true;
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
  /* ---------------- Versiya qo'riqchisi ----------------
     MUAMMO: navigatsiya "avval tarmoq" tartibida ishlaydi, lekin tarmoq
     UZILSA service worker keshdagi ESKI index.html ni beradi. Eski
     index.html esa eski `?v=` manzillarini chaqiradi va ular ham keshda
     bor — natijada internet sekin/uzuq bo'lgan bir lahzada butun ilova
     ESKI holatda ochilib qolardi va shundayligicha qolib ketardi.

     YECHIM: sahifa ochilgach serverdan `version.json` so'raladi (kesh
     butunlay chetlab o'tiladi). Serverdagi build sahifadagidan farq qilsa
     — hamma kesh tozalanadi, service worker ro'yxatdan chiqariladi va
     sahifa BIR MARTA qayta yuklanadi.

     Tarmoq yo'q bo'lsa hech narsa qilinmaydi: oflaynda eski nusxa bilan
     ishlash — bu xato emas, ataylab shunday. */
  function currentBuild() {
    var m = document.querySelector('meta[name="app-build"]');
    return m ? (m.getAttribute('content') || '') : '';
  }

  function guardVersion() {
    var mine = currentBuild();
    if (!mine || mine === 'dev') return;          // mahalliy ishlash — tekshirilmaydi

    fetch('version.json?t=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        if (!j || !j.build || j.build === mine) return;

        /* Qayta yuklash HALQASIGA tushmaslik uchun: shu build uchun bir
           marta urinamiz. Agar tozalashdan keyin ham eski nusxa kelsa
           (masalan server orqada), cheksiz yangilanib turmaydi. */
        var mark = 'app_build_reload_' + j.build;
        try {
          if (sessionStorage.getItem(mark)) return;
          sessionStorage.setItem(mark, '1');
        } catch (e) {}

        var jobs = [];
        if (window.caches) {
          jobs.push(caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (k) { return caches.delete(k); }));
          }));
        }
        if (navigator.serviceWorker) {
          jobs.push(navigator.serviceWorker.getRegistrations().then(function (rs) {
            return Promise.all(rs.map(function (r) { return r.unregister(); }));
          }));
        }
        Promise.all(jobs).catch(function () {}).then(function () {
          location.reload();
        });
      })
      .catch(function () {});                     // oflayn — tegmaymiz
  }

  window.addEventListener('load', guardVersion);
  /* Ulanish qaytganda ham tekshiramiz: ilova oflayn ochilgan bo'lsa,
     internet kelishi bilan o'zi eng so'nggisiga o'tadi. */
  window.addEventListener('online', guardVersion);
  window.addEventListener('hashchange', guardVersion);
  setInterval(guardVersion, 30000);

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
