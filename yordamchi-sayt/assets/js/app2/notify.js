/* Bildirishnomalar markazi.

   Nima uchun kerak: foydalanuvchi kelajakdagi ishni OLDINDAN rejalashtirib
   qo'yishi kerak — masalan "keyingi hafta futbolda bu mashqni almashtirish".
   O'sha kun kelganda eslatma qo'ng'iroqda paydo bo'ladi.

   Saqlash: `notify_v1` localStorage. Remote-storage ko'prigi uni avtomatik
   serverga sinxronlaydi, shuning uchun yangi jadval/endpoint kerak emas
   (loyihadagi mavjud naqsh).

   Yozuv tuzilishi:
     { id, text, note, date:'YYYY-MM-DD', sec, read:0|1, created }
   `date` — eslatma FAOLLASHADIGAN kun. Kelmagan eslatmalar "Rejalashtirilgan"
   bo'limida turadi va o'qilmagan deb sanalmaydi. */
(function () {
  'use strict';

  var KEY = 'notify_v1';

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  function load() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      if (!Array.isArray(v) || !v.length) {
        v = [
          {
            id: 'n_welcome_1',
            text: "Yangi 229 ta rus tili fe'llari to'liq yuklandi! Bosh sahifadagi story va reels orqali o'rganing.",
            note: "229 ta hozirgi zamon fe'li",
            date: todayStr(),
            sec: 'languages',
            read: 0,
            created: todayStr()
          },
          {
            id: 'n_welcome_2',
            text: "Kunlik rejalar va odatlarni bajarishni unutmang.",
            note: "Kunlik maqsadlar",
            date: todayStr(),
            sec: 'goals',
            read: 0,
            created: todayStr()
          },
          {
            id: 'n_welcome_3',
            text: "Barcha qo'shimcha bo'limlar uchun o'ng tomondagi yangi tortmadan foydalaning.",
            note: "Yordamchi menyusi",
            date: todayStr(),
            sec: 'boost',
            read: 0,
            created: todayStr()
          }
        ];
        try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (x) {}
      }
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(-300))); } catch (e) {}
  }

  /* Sanasi kelgan (yoki o'tgan) eslatmalar — ular "kelgan xabar" hisoblanadi */
  function due(list) {
    var t = todayStr();
    return (list || load()).filter(function (n) { return !n.date || n.date <= t; });
  }
  function upcoming(list) {
    var t = todayStr();
    return (list || load()).filter(function (n) { return n.date && n.date > t; });
  }
  function unreadCount() {
    return due().filter(function (n) { return !n.read; }).length;
  }

  /* Bo'limlar — eslatmani qaysi sohaga tegishli qilish (ixtiyoriy) */
  var SECS = [
    { k: '', n: 'Umumiy', ic: 'bell' },
    { k: 'sport', n: 'Sport', ic: 'trophy' },
    { k: 'boost', n: 'Boostday', ic: 'message' },
    { k: 'languages', n: 'Til', ic: 'globe' },
    { k: 'fanlar', n: 'Testlar', ic: 'book' },
    { k: 'goals', n: 'Maqsadlar', ic: 'check' }
  ];
  function secInfo(k) {
    return SECS.find(function (s) { return s.k === (k || ''); }) || SECS[0];
  }

  /* ---------- Bosh sahifadagi qo'ng'iroq ---------- */
  function bellHtml() {
    var n = unreadCount();
    return '<button class="nt-bell" data-act="ntOpen" aria-label="Bildirishnomalar">' +
      '<span data-icon="bell" data-icon-size="20"></span>' +
      (n ? '<span class="nt-badge">' + (n > 9 ? '9+' : n) + '</span>' : '') +
      '</button>';
  }

  /* ---------- Ro'yxat ---------- */
  function rowHtml(n) {
    var si = secInfo(n.sec);
    var when = n.date ? App.uzDate(n.date) : '';
    return '<div class="list-row nt-row' + (n.read ? ' read' : '') + '">' +
      '<button class="li-ic" style="border:none;background:' + (n.read ? 'var(--card-2)' : 'var(--accent-soft)') +
        ';color:' + (n.read ? 'var(--hint)' : 'var(--accent)') + '" ' +
        'data-act="ntToggleRead" data-arg=\'' + App.arg({ id: n.id }) + '\' ' +
        'aria-label="' + (n.read ? 'O\'qilmagan qilish' : 'O\'qildi') + '">' +
      '<span data-icon="' + si.ic + '" data-icon-size="15"></span></button>' +
      '<div class="li-main"' + (n.sec ? ' style="cursor:pointer" data-act="ntGoSec" data-arg=\'' + App.arg({ id: n.id, sec: n.sec }) + '\'' : '') + '>' +
      '<div class="li-title">' + App.esc(n.text) + '</div>' +
      '<div class="li-sub">' + App.esc(si.n) + (when ? ' · ' + App.esc(when) : '') +
      (n.note ? ' · ' + App.esc(n.note) : '') + (n.sec ? ' · <b style="color:var(--accent)">Ochish &rarr;</b>' : '') + '</div></div>' +
      '<button class="icon-btn ghost" style="width:28px;height:28px" aria-label="O\'chirish" ' +
      'data-act="ntDelete" data-arg=\'' + App.arg({ id: n.id }) + '\'>' +
      '<span data-icon="trash" data-icon-size="13"></span></button></div>';
  }

  function sheetHtml() {
    var list = load();
    var d = due(list).sort(function (a, b) { return (b.date || '') < (a.date || '') ? -1 : 1; });
    var u = upcoming(list).sort(function (a, b) { return (a.date || '') < (b.date || '') ? -1 : 1; });

    var html =
      '<button class="btn" data-act="ntAdd" style="margin-bottom:14px">' +
      '<span data-icon="plus" data-icon-size="16"></span>Yangi eslatma</button>';

    if (!d.length && !u.length) {
      return html + App.empty({
        icon: 'bell', title: 'Bildirishnoma yo\'q',
        text: 'Kelajakdagi ishni oldindan yozib qo\'ying — masalan "keyingi hafta futbolda yangi mashq qo\'shish". O\'sha kun kelganda shu yerda chiqadi.'
      });
    }

    if (d.length) {
      html += '<div class="list-label">Kelgan' + (unreadCount() ? ' · ' + unreadCount() + ' ta yangi' : '') + '</div>' +
        d.map(rowHtml).join('');
    }
    if (u.length) {
      html += '<div class="list-label">Rejalashtirilgan</div>' + u.map(rowHtml).join('');
    }
    if (d.length) {
      html += '<button class="btn sec" data-act="ntReadAll" style="margin-top:14px">Hammasini o\'qilgan qilish</button>';
    }
    return html;
  }

  function repaint() {
    var body = App.el('nt-body');
    if (body) { body.innerHTML = sheetHtml(); App.icons(body); }
    // Bosh sahifadagi qo'ng'iroq belgisini ham yangilaymiz
    var host = App.el('nt-bell-host');
    if (host) { host.innerHTML = bellHtml(); App.icons(host); }
  }

  App.actions.ntOpen = function () {
    var sh = App.sheet('<div id="nt-body">' + sheetHtml() + '</div>', { title: 'Bildirishnomalar' });
    App.icons(sh);
  };

  App.actions.ntGoSec = function (a) {
    if (!a) return;
    var list = load();
    var it = list.find(function (x) { return String(x.id) === String(a.id); });
    if (it) { it.read = 1; save(list); }
    App.closeSheet();
    if (a.sec) App.go(a.sec);
  };

  App.actions.ntToggleRead = function (a) {
    var list = load();
    var it = list.find(function (x) { return String(x.id) === String(a.id); });
    if (it) { it.read = it.read ? 0 : 1; save(list); repaint(); }
  };
  App.actions.ntReadAll = function () {
    var t = todayStr();
    var list = load();
    list.forEach(function (n) { if (!n.date || n.date <= t) n.read = 1; });
    save(list); repaint();
  };
  App.actions.ntDelete = function (a) {
    save(load().filter(function (x) { return String(x.id) !== String(a.id); }));
    repaint();
  };

  /* ---------- Yangi eslatma ---------- */
  App.actions.ntAdd = function () {
    var t = todayStr();
    var html =
      '<label class="field"><span>Nima eslatilsin?</span>' +
      '<input class="input" id="nt-text" placeholder="Masalan: futbolda dribbling mashqini almashtirish"></label>' +
      '<label class="field"><span>Qachon</span>' +
      '<input class="input" type="date" id="nt-date" value="' + t + '"></label>' +
      '<div class="list-label">Tez tanlash</div>' +
      '<div class="flex" style="gap:6px;flex-wrap:wrap;margin-bottom:12px">' +
      [['Bugun', 0], ['Ertaga', 1], ['3 kun', 3], ['1 hafta', 7], ['2 hafta', 14], ['1 oy', 30]]
        .map(function (p) {
          return '<button class="chip-btn nt-quick" data-d="' + p[1] + '">' + p[0] + '</button>';
        }).join('') + '</div>' +
      '<label class="field"><span>Bo\'lim</span><select class="input" id="nt-sec">' +
      SECS.map(function (s) { return '<option value="' + s.k + '">' + s.n + '</option>'; }).join('') +
      '</select></label>' +
      '<label class="field"><span>Qo\'shimcha izoh (ixtiyoriy)</span>' +
      '<input class="input" id="nt-note" placeholder="Qisqa izoh"></label>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="nt-save">Saqlash</button></div>';

    var sh = App.sheet(html, { title: 'Yangi eslatma' });
    App.icons(sh);

    // Tez tanlash tugmalari sanani to'ldiradi
    sh.querySelectorAll('.nt-quick').forEach(function (b) {
      b.onclick = function () {
        var d = new Date();
        d.setDate(d.getDate() + (+b.getAttribute('data-d') || 0));
        sh.querySelector('#nt-date').value =
          d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
        sh.querySelectorAll('.nt-quick').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
      };
    });

    sh.querySelector('#nt-save').onclick = function () {
      var text = (sh.querySelector('#nt-text').value || '').trim();
      if (!text) { App.toast('Matnni kiriting'); return; }
      var list = load();
      list.push({
        id: 'n' + Date.now() + Math.floor(Math.random() * 1000),
        text: text,
        note: (sh.querySelector('#nt-note').value || '').trim(),
        date: sh.querySelector('#nt-date').value || todayStr(),
        sec: sh.querySelector('#nt-sec').value || '',
        read: 0,
        created: todayStr()
      });
      save(list);
      App.closeSheet();
      App.toast('✅ Eslatma qo\'shildi');
      // Bosh sahifadagi belgi darhol yangilansin
      var host = App.el('nt-bell-host');
      if (host) { host.innerHTML = bellHtml(); App.icons(host); }
    };
  };

  /* Boshqa modullar uchun (bosh sahifa qo'ng'iroqni shundan oladi) */
  window.Notify = {
    bellHtml: bellHtml,
    unreadCount: unreadCount,
    /* Kod ichidan eslatma qo'shish (kelajakda avtomatik eslatmalar uchun) */
    add: function (text, date, sec, note) {
      if (!String(text || '').trim()) return;
      var list = load();
      list.push({
        id: 'n' + Date.now() + Math.floor(Math.random() * 1000),
        text: String(text).trim(), note: note || '',
        date: date || todayStr(), sec: sec || '', read: 0, created: todayStr()
      });
      save(list);
    }
  };
})();
