/* Tarix — barcha bo'limlarda (sport/lug'at/test/mavzu/listening/boostday) qilingan
   ishning kunlar bo'yicha lentasi. Manba: server activity_log (log_activity/get_activity_log). */
(function () {
  'use strict';

  var SEC = {
    sport:     { n: 'Sport',     ic: 'trophy',     c: 'var(--coral)' },
    vocab:     { n: 'Lug\'at',   ic: 'globe',      c: 'var(--teal)' },
    quiz:      { n: 'Test',      ic: 'book',       c: 'var(--accent)' },
    topic:     { n: 'Mavzu',     ic: 'file',       c: 'var(--purple)' },
    material:  { n: 'Materiallar', ic: 'book',     c: 'var(--teal)' },
    listening: { n: 'Listening', ic: 'headphones', c: 'var(--warn)' },
    reading:   { n: 'O\'qish',    ic: 'book',      c: 'var(--purple)' },
    boostday:  { n: 'Boostday',  ic: 'message',    c: 'var(--success)' }
  };
  // MUHIM: bu ro'yxat stats.js dagi SEC_BLOCKS va backend'dagi
  // ALLOWED_SECTIONS bilan bir xil bo'lishi kerak — uchalasi ham
  // activity_log dagi `section` qiymatlariga tayanadi.
  var SEC_ORDER = ['sport', 'vocab', 'quiz', 'topic', 'material', 'listening', 'reading', 'boostday'];
  var MON = ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'];
  // "Iyun"/"Iyul" kabi ba'zi oylar 3 harfga qisqartirilsa bir xil chiqib qolardi (Iyu/Iyu) —
  // shuning uchun qisqa nomlar alohida, kesib olinmaydi.
  var MON_SHORT = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek'];
  var WD = ['Yakshanba', 'Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba'];

  function secInfo(s) { return SEC[s] || { n: s, ic: 'file', c: 'var(--hint)' }; }

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function dkey(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function addDays(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }

  function dayLabel(key) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var yesterday = addDays(today, -1);
    if (key === dkey(today)) return 'Bugun';
    if (key === dkey(yesterday)) return 'Kecha';
    var parts = key.split('-').map(Number);
    var d = new Date(parts[0], parts[1] - 1, parts[2]);
    return d.getDate() + '-' + MON[d.getMonth()] + ', ' + WD[d.getDay()];
  }

  function itemText(it) {
    var amt = it.amount != null ? (it.amount % 1 === 0 ? it.amount.toFixed(0) : it.amount) : null;
    switch (it.section) {
      case 'sport': return it.object + (amt ? ' — ' + amt + ' ' + (it.unit || 'marta') : '');
      case 'quiz': return it.object + ' testi' + (amt ? ' — ' + amt + ' ' + (it.unit || 'savol') : '');
      case 'vocab': return it.object + (amt ? ' — ' + amt + ' ' + (it.unit || 'so\'z') : '');
      case 'topic': return it.object + ' mavzusi o\'qildi';
      case 'material': return it.object + ' o\'qildi';
      case 'listening': return it.object + (amt ? ' — ' + amt + ' ' + (it.unit || 'savol') : '');
      case 'boostday': return it.object + ' bajarildi';
      default: return it.object || secInfo(it.section).n;
    }
  }

  function itemTime(it) {
    var m = /\d{2}:\d{2}/.exec(it.at || '');
    return m ? m[0] : '';
  }

  function groupByDay(items) {
    var map = {}, order = [];
    items.forEach(function (it) {
      var key = (it.at || '').slice(0, 10);
      if (!key) return;
      if (!map[key]) { map[key] = []; order.push(key); }
      map[key].push(it);
    });
    order.sort().reverse();
    return order.map(function (key) { return { key: key, items: map[key] }; });
  }

  window.TarixGoTopic = function(lang, name) {
    if (!lang) lang = 'russian';
    var box = App.el('txd-body') || App.el('tx-feed');
    if (box) box.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
    
    window.Library.topics(lang).then(function(topics) {
      var found = topics.find(function(t) { return t.name === name; }) ||
                  topics.find(function(t) { return name.indexOf(t.name) !== -1 || t.name.indexOf(name) !== -1; });
      if (found) {
         App.go('grammar_topic', { lang: lang, id: found.id });
      } else {
         App.toast("Kechirasiz, '" + App.esc(name) + "' mavzusi topilmadi.");
         App.go('grammar', { lang: lang });
      }
    }).catch(function() {
      App.go('grammar', { lang: lang });
    });
  };

  function dayGroupHtml(group, filter, showHeader) {
    var items = filter && filter !== 'all' ? group.items.filter(function (i) { return i.section === filter; }) : group.items;
    if (!items.length) return '';
    var header = '';
    if (showHeader !== false) {
      var bySec = {};
      items.forEach(function (i) { bySec[i.section] = (bySec[i.section] || 0) + 1; });
      var chips = Object.keys(bySec).map(function (s) {
        var si = secInfo(s);
        return '<span style="color:' + si.c + '">' + si.n + ' ' + bySec[s] + '</span>';
      }).join(' · ');
      header = '<div class="list-label" style="margin-top:16px;display:flex;justify-content:space-between;align-items:baseline">' +
        '<span>' + dayLabel(group.key) + '</span>' +
        '<span style="display:flex;gap:8px;font-size:11px;font-weight:600;text-transform:none;letter-spacing:0">' + chips + '</span></div>';
    }

    return header +
      items.map(function (it) {
        var si = secInfo(it.section);
        
        var meta = {};
        try { meta = typeof it.meta === 'string' ? JSON.parse(it.meta) : (it.meta || {}); } catch(e){}
        var lang = meta.lang || '';
        
        var act = '';
        /* Bo'lim nomlari RO'YXATDAN O'TGAN view nomlari bo'lishi shart —
           `App.go` noma'lum nomda jimgina BOSH SAHIFAGA tashlaydi.
           Ilgari 'boostday' va 'listening' deb yozilgan edi, bunday
           ko'rinishlar yo'q (to'g'risi 'boost' va 'listening_practice'). */
        var secLang = lang === 'russian' ? 'russian' : 'english';
        if (it.section === 'sport') act = "App.go('sport')";
        else if (it.section === 'boostday') act = "App.go('boost')";
        else if (it.section === 'quiz') act = "App.go('quiz_dashboard')";
        else if (it.section === 'vocab') act = "App.go('vocab', { lang: '" + secLang + "' })";
        else if (it.section === 'topic') act = "window.TarixGoTopic('" + lang + "', '" + (it.object || '').replace(/'/g, "\\'") + "')";
        else if (it.section === 'material') act = "App.go('library', { sec: '" + (meta.sec || 'en_listening') + "' })";
        else if (it.section === 'listening') act = "App.go('listening_practice', { lang: '" + secLang + "' })";
        else if (it.section === 'reading') act = "App.go('library', { sec: '" + (meta.sec || 'en_reading') + "' })";

        var onclick = act ? ' onclick="' + act + '" style="cursor:pointer"' : ' style="cursor:default"';

        return '<div class="list-row"' + onclick + '>' +
          '<span class="li-ic" style="background:color-mix(in srgb,' + si.c + ' 16%, transparent);color:' + si.c + '">' +
          '<span data-icon="' + si.ic + '" data-icon-size="15"></span></span>' +
          '<div class="li-main"><div class="li-title">' + App.esc(itemText(it)) + '</div>' +
          '<div class="li-sub">' + si.n + (itemTime(it) ? ' · ' + itemTime(it) : '') + '</div></div></div>';
      }).join('');
  }

  /* ---------- Asosiy Tarix lentasi ---------- */
  var T = { items: [], currentDate: null, filter: 'all' };

  function fetchDay(date) {
    var d = dkey(date);
    return App.call('get_activity_log', null, { query: 'from=' + d + '&to=' + d }).then(function (j) {
      T.items = j.items || [];
      T.currentDate = date;
      return T.items;
    });
  }

  /* "D-MON" ko'rinishidagi qisqa sana (Tugmalarda ko'rsatish uchun) */
  function shortDate(key) {
    var p = key.split('-').map(Number);
    var d = new Date(p[0], p[1] - 1, p[2]);
    return d.getDate() + '-' + MON_SHORT[d.getMonth()];
  }

  function renderFeed(page) {
    var box = App.el('tx-feed'); if (!box) return;
    var rangeEl = App.el('tx-range');
    if (rangeEl) {
      rangeEl.textContent = 'Sana: ' + dayLabel(dkey(T.currentDate));
    }

    var group = { key: dkey(T.currentDate), items: T.items };
    var html = dayGroupHtml(group, T.filter, true);

    if (!html) {
      html = App.empty({ icon: 'clock', title: dayLabel(dkey(T.currentDate)) + ' tarixi bo\'sh', text: 'Bu kuni hech qanday mashq bajarilmagan.' });
    }

    var prev = addDays(T.currentDate, -1);
    var next = addDays(T.currentDate, 1);
    var isToday = dkey(T.currentDate) === dkey(new Date());

    var btnHtml = '<div style="display:flex;gap:12px;margin-top:24px">';
    btnHtml += '<button class="btn sec" id="tx-prev" style="flex:1">← ' + shortDate(dkey(prev)) + '</button>';
    if (!isToday) {
       btnHtml += '<button class="btn sec" id="tx-next" style="flex:1">' + shortDate(dkey(next)) + ' →</button>';
    }
    btnHtml += '</div>';

    box.innerHTML = html + btnHtml;
    App.icons(box);

    var prevBtn = App.el('tx-prev');
    if (prevBtn) prevBtn.onclick = function() {
      box.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
      fetchDay(prev).then(function() { renderFeed(page); });
    };
    
    var nextBtn = App.el('tx-next');
    if (nextBtn) nextBtn.onclick = function() {
      box.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
      fetchDay(next).then(function() { renderFeed(page); });
    };
  }

  App.view('tarix', {
    nav: 'tarix',
    render: function (page) {
      T.filter = 'all';
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<div style="display:flex;align-items:center;gap:9px;flex:1;min-width:0">' +
        '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:28px;height:28px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
        '<h1>Tarix</h1></div>' +
        '<button class="icon-btn ghost" style="margin-left:auto" data-act="tarixPickDate" aria-label="Sana bo\'yicha qidirish">' +
        '<span data-icon="calendar" data-icon-size="18"></span></button></div>' +
        '<div class="bo-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin:0 0 4px" id="tx-chips">' +
        '<button class="chip active" data-f="all">Hammasi</button>' +
        SEC_ORDER.map(function (s) { return '<button class="chip" data-f="' + s + '">' + secInfo(s).n + '</button>'; }).join('') +
        '</div>' +
        '<div class="muted" id="tx-range" style="font-size:11.5px;font-weight:600;margin:2px 1px 10px"></div>' +
        '<div id="tx-feed"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      page.querySelectorAll('#tx-chips .chip').forEach(function (c) {
        c.onclick = function () {
          T.filter = c.getAttribute('data-f');
          page.querySelectorAll('#tx-chips .chip').forEach(function (x) { x.classList.toggle('active', x === c); });
          renderFeed(page);
        };
      });

      fetchDay(new Date()).then(function () { renderFeed(page); }).catch(function (e) {
        var box = App.el('tx-feed');
        if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
      });
    }
  });

  App.actions.tarixPickDate = function () {
    var html = '<label class="field"><span>Sanani tanlang</span>' +
      '<input class="input" type="date" id="tx-date" value="' + dkey(new Date()) + '" max="' + dkey(new Date()) + '"></label>' +
      '<button class="btn" id="tx-date-go">Ko\'rish</button>';
    var sh = App.sheet(html, { title: 'Sana bo\'yicha qidiruv' });
    sh.querySelector('#tx-date-go').onclick = function () {
      var v = sh.querySelector('#tx-date').value;
      if (!v) return;
      App.closeSheet();
      App.go('tarix_day', { date: v });
    };
  };

  /* ---------- Bitta kun tafsiloti (Heatmap'dan bosilganda ham shu ishlatiladi) ---------- */
  App.view('tarix_day', {
    nav: 'tarix',
    render: function (page, params) {
      var date = /^\d{4}-\d{2}-\d{2}$/.test(params.date || '') ? params.date : dkey(new Date());
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'tarix' }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(dayLabel(date)) + '</h1></div>' +
        '<div id="txd-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      App.call('get_activity_log', null, { query: 'from=' + date + '&to=' + date }).then(function (j) {
        var box = App.el('txd-body'); if (!box) return;
        var items = j.items || [];
        if (!items.length) {
          box.innerHTML = App.empty({ icon: 'clock', title: 'Bu kuni hech narsa qilinmadi', text: '' });
          App.icons(box);
          return;
        }
        var group = { key: date, items: items };
        box.innerHTML = dayGroupHtml(group, 'all', false);
        App.icons(box);
      }).catch(function (e) {
        var box = App.el('txd-body');
        if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
      });
    }
  });

  window.Tarix = { dkey: dkey, dayLabel: dayLabel };
})();
