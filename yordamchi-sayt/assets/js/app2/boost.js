/* Boostday bot — saytdan boshqarish (Mini App xususiyatlari bilan).
   Barcha so'rovlar sayt backend'i orqali (/api?action=boost_*) ketadi. */
(function () {
  'use strict';

  var TYPES = {
    daily_todo:  { n: 'Har kungi reja', ic: 'refresh', c: 'var(--success)', d: 'Har kuni belgilangan vaqtda yuboriladi', e: '🔁' },
    todo:        { n: 'TO-DO',          ic: 'check',   c: 'var(--accent)',  d: 'Bitta sanaga vazifalar ro\'yxati',       e: '📋' },
    super_todo:  { n: 'Super TO-DO',    ic: 'clock',   c: 'var(--purple)',  d: 'Vaqt hisoblagichli vazifalar',           e: '⏱' },
    daily_plan:  { n: 'Oddiy reja',     ic: 'image',   c: 'var(--teal)',    d: 'Har kuni media/matn yuboriladi',         e: '📅' },
    reminder:    { n: 'Eslatma',        ic: 'alert',   c: 'var(--warn)',    d: 'Bir marta yuboriladi',                   e: '🎗' },
    challenge:   { n: 'Challenge',      ic: 'trophy',  c: 'var(--coral)',   d: 'Muddatli challenge posti',               e: '🔥' }
  };
  function tinfo(t) { return TYPES[t] || { n: t, ic: 'file', c: 'var(--hint)', d: '', e: '•' }; }

  var B = { data: null, channels: null, stats: null, filter: 'all', search: '' };

  /* ILOVAGA QAYTGANDA reja ma'lumoti eskirgan deb belgilanadi — vazifa
     Telegramda belgilangan bo'lishi mumkin (eng keng tarqalgan holat).
     Sport bo'limida ham xuddi shunday qilingan. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) return;
    B.data = null;
    var v = App.currentView && App.currentView();
    if (!v || ['boost', 'boost_plan', 'home', 'kun'].indexOf(v) < 0) return;
    if (document.querySelector('.sheet.show')) return;
    App.reload();
  });

  function call(action, payload) {
    return App.call('boost_' + action, payload || {});
  }

  function topbar(title, back, params, rightHtml) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      (back ? '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: back, p: params || {} }) +
        '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' : '') +
      '<h1>' + App.esc(title) + '</h1>' + (rightHtml || '') + '</div>';
  }

  function allPlans(j) {
    var d = j || B.data || {};
    return [].concat(d.daily_routines || [], d.todos || [], d.plans || [], d.reminders || []);
  }

  function planCount(p) {
    var groups = p.task_groups || (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []), n = 0;
    groups.forEach(function (g) { n += ((g && g.tasks) || []).length; });
    return n;
  }
  function planDone(p) {
    var groups = p.task_groups || (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []), n = 0;
    groups.forEach(function (g) {
      ((g && g.tasks) || []).forEach(function (t) { if (+t.status === 1) n++; });
    });
    return n;
  }
  function counts(d) {
    d = d || B.data || {};
    return {
      daily: (d.daily_routines || []).length,
      plans: (d.plans || []).length,
      rem:   (d.reminders || []).length,
      todo:  (d.todos || []).length
    };
  }

  /* ---------- PLAN ITEM HTML ---------- */
  function planItemHtml(p) {
    var ti = tinfo(p.plan_type);
    var total = planCount(p), done = planDone(p);
    var sub = [];
    if (p.time) sub.push('⏰ ' + p.time);
    if (p.date) sub.push(p.date);
    if (p.start_date) sub.push(p.start_date + '→' + (p.end_date || ''));
    if (total) sub.push(done + '/' + total + ' vazifa');
    if (p.channel_name) sub.push(p.channel_name);
    if (p.plan_type === 'daily_todo' && p.week_mode && p.week_mode !== 'everyday')
      sub.push(p.week_mode === 'odd' ? 'Toq kunlar' : 'Juft kunlar');
    return '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'boost_plan', p: { id: p.id } }) + '\'>' +
      '<span class="li-ic" style="background:color-mix(in srgb,' + ti.c + ' 16%, transparent);color:' + ti.c +
      '"><span data-icon="' + ti.ic + '" data-icon-size="15"></span></span>' +
      '<div class="li-main"><div class="li-title">' + App.esc(ti.e + ' ' + ti.n) +
      ' <span style="color:var(--hint);font-weight:500;font-size:12.5px">· ' + App.esc(p.channel_name || '') + '</span></div>' +
      '<div class="li-sub">' + App.esc(sub.join(' · ')) + '</div>' +
      (p.preview ? '<div class="li-sub" style="opacity:.6;font-size:11.5px;margin-top:2px">' + App.esc(p.preview.substring(0, 80)) + '</div>' : '') +
      '</div>' +
      '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
  }

  /* =========================================================
     VIEW: boost — Bosh sahifa + Rejalar + Filtr + Qidiruv
     ========================================================= */
  App.view('boost', {
    nav: 'boost',
    render: function (page) {
      page.innerHTML = topbar('Boostday', null, null,
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'boost_stats' }) + '\' style="margin-left:auto" aria-label="Statistika"><span data-icon="clock" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="boostChannels" aria-label="Kanallar"><span data-icon="settings" data-icon-size="18"></span></button>') +

        /* Bugungi barcha ishlar — Boostday vazifalari + Sport mashqlari BITTA
           ro'yxatda (band 5.1), lekin ro'yxat sahifa boshini bosib
           ketmasin deb TUGMA orqasida (sheet ichida) turadi. */
        '<button class="list-row" data-act="boostTodaySheet" style="margin-bottom:8px">' +
        '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)"><span data-icon="check" data-icon-size="15"></span></span>' +
        '<div class="li-main"><div class="li-title">Bugungi ishlar</div>' +
        '<div class="li-sub" id="bo-today-sub">Yuklanmoqda...</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +
        '<button class="list-row" data-act="boostAllSheet" style="margin-bottom:10px">' +
        '<span class="li-ic" style="background:var(--card-2);color:var(--hint)"><span data-icon="list" data-icon-size="15"></span></span>' +
        '<div class="li-main"><div class="li-title">Barcha vazifalar</div>' +
        '<div class="li-sub">Tizimdagi barcha reja va mashqlar</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        /* Stat kartochkalar */
        '<div id="bo-stats"></div>' +

        /* Filter chips */
        '<div class="bo-chips" id="bo-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px">' +
          '<button class="chip active" data-f="all">Hammasi</button>' +
          '<button class="chip" data-f="daily_todo">Har kungi</button>' +
          '<button class="chip" data-f="plans">Rejalar</button>' +
          '<button class="chip" data-f="reminder">Eslatma</button>' +
          '<button class="chip" data-f="todo">TO-DO</button>' +
        '</div>' +

        /* Qidiruv */
        '<div style="margin-bottom:12px"><input class="input" id="bo-search" placeholder="🔎 Qidirish..." style="padding-left:12px"></div>' +

        /* Rejalar ro'yxati */
        '<div id="bo-list"><div class="load-wrap"><div class="spinner"></div></div></div>' +

        /* Yangi reja tugmasi */
        '<button class="btn" style="margin-top:14px" data-act="boostNew"><span data-icon="plus" data-icon-size="16"></span>Yangi reja</button>';
      App.icons(page);

      // Chips logikasi
      page.querySelectorAll('#bo-chips .chip').forEach(function (c) {
        c.onclick = function () {
          B.filter = c.getAttribute('data-f');
          page.querySelectorAll('#bo-chips .chip').forEach(function (x) {
            x.classList.toggle('active', x === c);
          });
          renderList(page);
        };
      });

      // Qidiruv logikasi
      var searchEl = App.el('bo-search');
      searchEl.oninput = function () {
        B.search = searchEl.value;
        renderList(page);
      };

      // Ma'lumot yuklash
      call('stats').then(function (j) {
        var box = App.el('bo-stats'); if (!box) return;
        var s = j.summary || {};
        var c = counts();
        box.innerHTML = '<div class="stat-strip" style="margin:0 0 14px">' +
          '<div class="s"><div class="n" style="color:var(--success)">' + (c.daily || 0) + '</div><div class="l">Har kungi</div></div>' +
          '<div class="s"><div class="n">' + (c.plans + c.todo || 0) + '</div><div class="l">Rejalar</div></div>' +
          '<div class="s"><div class="n">' + (c.rem || 0) + '</div><div class="l">Eslatma</div></div>' +
          '<div class="s"><div class="n" style="color:var(--accent)">' + (s.percent || 0) + '%</div><div class="l">Bajarildi</div></div></div>';
      }).catch(function () {});

      call('list').then(function (j) {
        B.data = j;
        // Stat kartochkalarni yangilash
        var box = App.el('bo-stats');
        if (box) {
          var c = counts(j);
          box.innerHTML = '<div class="stat-strip" style="margin:0 0 14px">' +
            '<div class="s"><div class="n" style="color:var(--success)">' + c.daily + '</div><div class="l">Har kungi</div></div>' +
            '<div class="s"><div class="n">' + (c.plans + c.todo) + '</div><div class="l">Rejalar</div></div>' +
            '<div class="s"><div class="n">' + c.rem + '</div><div class="l">Eslatma</div></div>' +
            '<div class="s"><div class="n">' + (B.channels ? B.channels.length : '—') + '</div><div class="l">Kanal</div></div></div>';
        }
        renderList(page);
        renderTodayButton(page);
      }).catch(function (e) {
        var box = App.el('bo-list');
        if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Ulanmadi', text: e.message });
      });

      call('channels').then(function (j) {
        B.channels = j.channels || [];
      }).catch(function () {});
    }
  });

  /* =========================================================
     "Bugungi ishlar" — Boostday (har kungi + bugungi sanali TO-DO) va
     Sport mashqlari BITTA ro'yxatda. Bosilganda darhol belgilanadi:
       - Boostday: bot_py `toggle_task` (bitta vazifa, butun reja emas) —
         shu bilan bir vaqtda Telegramdagi xabar ham yangilanadi (5.3).
       - Sport: SportBridge.toggle — mavjud sport_log_v1'ga yozadi (5.4
         teskari yo'nalishi allaqachon ishlaydi: Telegramda belgilangan
         Boostday vazifasi shu ro'yxatni qayta yuklaganda ko'rinadi,
         chunki har safar serverdan `list` bilan olinadi — kesh yo'q). */
  function todayKeyStr() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  /* Boostday vazifalarni HOLATga ko'ra ajratadi. `wantDone` true bo'lsa —
     bajarilganlar, aks holda — bajarilmaganlar. Faqat "bugungi" doirada
     (har kungi rejalar + bugungi sanali TO-DO). */
  function boostItemsByStatus(wantDone) {
    var out = [];
    var today = todayKeyStr();
    function fromPlans(list) {
      (list || []).forEach(function (p) {
        var groups = p.task_groups && p.task_groups.length ? p.task_groups : (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []);
        var idx = 0;
        groups.forEach(function (g) {
          (g.tasks || []).forEach(function (t) {
            var done = +t.status === 1;
            if (done === !!wantDone && (t.text || '').trim()) {
              out.push({ kind: 'boost', planId: p.id, index: idx, text: t.text, superTodo: p.plan_type === 'super_todo', status: +t.status || 0 });
            }
            idx++;
          });
        });
      });
    }
    fromPlans(B.data && B.data.daily_routines);
    fromPlans((B.data && B.data.todos || []).filter(function (p) { return p.date === today; }));
    return out;
  }
  function boostTodayItems() { return boostItemsByStatus(false); }

  /* "Barcha vazifalar" — sana/holatdan qat'iy nazar TIZIMDAGI hamma
     bajarilishi mumkin bo'lgan ish: barcha checkable Boostday rejalari
     (har kungi + BARCHA TO-DO, sanasidan qat'iy nazar) + barcha sport
     mashqlari (barcha kategoriya, allaqachon bajarilgan-bajarilmaganidan
     qat'iy nazar — `done` bayrog'i bilan). */
  function boostAllItems() {
    var out = [];
    function fromPlans(list) {
      (list || []).forEach(function (p) {
        var groups = p.task_groups && p.task_groups.length ? p.task_groups : (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []);
        var idx = 0;
        groups.forEach(function (g) {
          (g.tasks || []).forEach(function (t) {
            if ((t.text || '').trim()) {
              out.push({
                kind: 'boost', planId: p.id, index: idx, text: t.text,
                superTodo: p.plan_type === 'super_todo', status: +t.status || 0,
                sub: (p.channel_name || '') + (p.date ? ' · ' + p.date : '')
              });
            }
            idx++;
          });
        });
      });
    }
    fromPlans(B.data && B.data.daily_routines);
    fromPlans(B.data && B.data.todos);
    return out;
  }

  /* Tugma ostidagi qisqa matn — nechta ish qolgani (sheet ochilmasdan ham ko'rinadi). */
  function renderTodayButton(page) {
    var sub = App.el('bo-today-sub'); if (!sub || !window.SportBridge) return;
    SportBridge.ensureLoaded().then(function () {
      var bIt = boostTodayItems();
      var total = bIt.length + dropSportDuplicates(SportBridge.todayPending()).length;
      sub = App.el('bo-today-sub'); if (!sub) return;
      sub.textContent = total ? total + ' ta ish qoldi' : 'Bugun hech narsa qolmadi 🎉';
    });
  }

  /* Qaysi sheet ochiq turibdi — toggle amallari to'g'ri joyni qayta
     chizishi uchun ('today' — Bugungi ishlar, 'all' — Barcha vazifalar). */
  var ACTIVE_SHEET = null;
  /* "Bugungi ishlar" ichidagi rejim: bajarilmagan / bajarilganlar / yashiringan. */
  var TODAY_MODE = 'pending';

  function boostRowHtml(it, done, extraBtn) {
    var icon = done ? 'check' : (it.superTodo && it.status === 2 ? 'clock' : 'plus');
    var bg = done ? 'var(--success-soft)' : 'var(--card-2)';
    var col = done ? 'var(--success)' : 'var(--hint)';
    return '<div class="list-row"><button class="li-ic" style="border:none;background:' + bg + ';color:' + col + '" ' +
      'data-act="todayToggleBoost" data-arg=\'' + App.arg({ id: it.planId, index: it.index }) + '\'>' +
      '<span data-icon="' + icon + '" data-icon-size="15"></span></button>' +
      '<div class="li-main"><div class="li-title">' + App.esc(it.text) + '</div>' +
      (it.sub ? '<div class="li-sub">' + App.esc(it.sub) + '</div>' : '') + '</div>' + (extraBtn || '') + '</div>';
  }
  function sportRowHtml(it, done, extraBtn) {
    var icon = done ? 'check' : 'plus';
    var bg = done ? 'var(--success-soft)' : 'var(--card-2)';
    var col = done ? 'var(--success)' : 'var(--hint)';
    return '<div class="list-row"><button class="li-ic" style="border:none;background:' + bg + ';color:' + col + '" ' +
      'data-act="todayToggleSport" data-arg=\'' + App.arg({ cat: it.cat, id: it.id }) + '\'>' +
      '<span data-icon="' + icon + '" data-icon-size="15"></span></button>' +
      '<div class="li-main"><div class="li-title">' + App.esc(it.name) + '</div>' +
      '<div class="li-sub">Sport · ' + App.esc(it.catName) + '</div></div>' + (extraBtn || '') + '</div>';
  }
  var PENDING_HIDE = { id: null, timer: null };
  function hideBtnHtml(it) {
    var confirming = PENDING_HIDE.id === String(it.id);
    return '<button class="icon-btn ghost" style="width:28px;height:28px' +
      (confirming ? ';background:var(--danger-soft);color:var(--danger)' : '') + '" ' +
      'aria-label="' + (confirming ? 'Tasdiqlash uchun yana bosing' : 'Bu mashqni bugun ko\'rsatma') + '" ' +
      'data-act="todayHideSport" data-arg=\'' + App.arg({ cat: it.cat, id: it.id, name: it.name }) + '\'>' +
      '<span data-icon="' + (confirming ? 'check' : 'x') + '" data-icon-size="13"></span></button>';
  }
  function unhideBtnHtml(it) {
    return '<button class="icon-btn ghost" style="width:28px;height:28px" aria-label="Qayta yoqish" ' +
      'data-act="todayUnhideSport" data-arg=\'' + App.arg({ cat: it.cat, id: it.id }) + '\'><span data-icon="refresh" data-icon-size="14"></span></button>';
  }

  /* Bitta ish IKKI marta ko'rinmasligi uchun: Boostday vazifasi bilan bir xil
     nomdagi sport mashqi ro'yxatdan olib tashlanadi. Boostday qatori qoldiriladi
     — chunki uni belgilash Telegramdagi xabarni ham yangilaydi (sport qatori
     esa faqat mahalliy). Ikkalasi baribir bir-biriga sinxronlanadi. */
  /* Bitta ish IKKI marta ko'rinmasligi uchun: Boostday vazifasi bilan bir xil
     nomdagi sport mashqi ro'yxatdan olib tashlanadi. Boostday qatori qoldiriladi
     — uni belgilash Telegramdagi xabarni ham yangilaydi.
     MUHIM: solishtirish BUGUNGI BARCHA Boostday vazifalari bilan qilinadi,
     ko'rsatilayotgan ro'yxat bilan emas. Aks holda bajarilgan vazifaning
     sport nusxasi "bajarilmagan" ro'yxatida qayta chiqib ketardi. */
  function boostTodayKeys() {
    var keys = {}, d = B.data || {}, today = todayKeyStr();
    function scan(list) {
      (list || []).forEach(function (p) {
        var groups = p.task_groups && p.task_groups.length
          ? p.task_groups : (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []);
        groups.forEach(function (g) {
          (g.tasks || []).forEach(function (t) {
            if ((t.text || '').trim()) keys[App.taskKey(t.text)] = true;
          });
        });
      });
    }
    scan(d.daily_routines);
    scan((d.todos || []).filter(function (p) { return p.date === today; }));
    return keys;
  }

  function dropSportDuplicates(sportItems) {
    if (!sportItems || !sportItems.length) return sportItems || [];
    var keys = boostTodayKeys();
    return sportItems.filter(function (s) { return !keys[App.taskKey(s.name)]; });
  }

  function todaySheetHtml() {
    var modes = [['pending', 'Bajarilmagan'], ['done', 'Bajarilganlar'], ['hidden', 'Yashiringan']];
    var chips = '<div class="bo-chips" style="display:flex;gap:6px;flex-wrap:wrap;margin:0 0 12px">' +
      modes.map(function (m) {
        return '<button class="chip' + (TODAY_MODE === m[0] ? ' active' : '') + '" data-act="todaySetMode" data-arg=\'' +
          App.arg({ m: m[0] }) + '\'>' + m[1] + '</button>';
      }).join('') + '</div>';

    var boostItems, sportItems, html;
    if (TODAY_MODE === 'done') {
      boostItems = boostItemsByStatus(true);
      sportItems = dropSportDuplicates(SportBridge.doneToday());
      html = boostItems.map(function (it) { return boostRowHtml(it, true); }).join('') +
        sportItems.map(function (it) { return sportRowHtml(it, true); }).join('');
      if (!boostItems.length && !sportItems.length) html = App.empty({ icon: 'check', title: 'Hali hech narsa bajarilmagan', text: '' });
    } else if (TODAY_MODE === 'hidden') {
      sportItems = SportBridge.hiddenPending();
      html = sportItems.map(function (it) { return sportRowHtml(it, false, unhideBtnHtml(it)); }).join('');
      if (!sportItems.length) html = App.empty({ icon: 'x', title: 'Yashiringan mashq yo\'q', text: '' });
    } else {
      boostItems = boostItemsByStatus(false);
      sportItems = dropSportDuplicates(SportBridge.todayPending());
      html = boostItems.map(function (it) { return boostRowHtml(it, false); }).join('') +
        sportItems.map(function (it) { return sportRowHtml(it, false, hideBtnHtml(it)); }).join('');
      if (!boostItems.length && !sportItems.length) html = App.empty({ icon: 'check', title: 'Bugun hech narsa yo\'q', text: 'Har kungi rejalar, bugungi TO-DO va sport mashqlari shu yerda chiqadi.' });
    }
    return chips + html;
  }

  function allSheetHtml() {
    var boostItems = boostAllItems();
    var sportItems = dropSportDuplicates(SportBridge.allExercises());
    if (!boostItems.length && !sportItems.length) {
      return App.empty({ icon: 'list', title: 'Hali hech narsa yo\'q', text: 'Reja yoki sport mashqi qo\'shing.' });
    }
    return boostItems.map(function (it) { return boostRowHtml(it, +it.status === 1); }).join('') +
      sportItems.map(function (it) { return sportRowHtml(it, !!it.done); }).join('');
  }

  function renderActiveSheet() {
    var body = App.el('bo-today-body'); if (!body) return;
    body.innerHTML = ACTIVE_SHEET === 'all' ? allSheetHtml() : todaySheetHtml();
    App.icons(body);
  }

  function resetPendingHide() {
    if (PENDING_HIDE.timer) clearTimeout(PENDING_HIDE.timer);
    PENDING_HIDE = { id: null, timer: null };
  }

  App.actions.boostTodaySheet = function () {
    ACTIVE_SHEET = 'today'; TODAY_MODE = 'pending'; resetPendingHide();
    var sh = App.sheet('<div id="bo-today-body"><div class="load-wrap"><div class="spinner"></div></div></div>', { title: 'Bugungi ishlar' });
    App.icons(sh);
    // Sheet ochilganda ro'yxatni serverdan qayta so'raymiz — shu bilan
    // reja tahrirlash oynasida yozuv/matn o'zgargan bo'lsa (yoki Telegramdan
    // belgilangan bo'lsa) ham eng yangi holat ko'rinadi.
    Promise.all([call('list'), SportBridge.ensureLoaded()]).then(function (r) {
      B.data = r[0];
      renderActiveSheet();
    }).catch(function (e) {
      var body = App.el('bo-today-body');
      if (body) body.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  };

  App.actions.boostAllSheet = function () {
    ACTIVE_SHEET = 'all'; resetPendingHide();
    var sh = App.sheet('<div id="bo-today-body"><div class="load-wrap"><div class="spinner"></div></div></div>', { title: 'Barcha vazifalar' });
    App.icons(sh);
    Promise.all([call('list'), SportBridge.ensureLoaded()]).then(function (r) {
      B.data = r[0];
      renderActiveSheet();
    }).catch(function (e) {
      var body = App.el('bo-today-body');
      if (body) body.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  };

  App.actions.todaySetMode = function (a) {
    TODAY_MODE = a.m || 'pending';
    resetPendingHide();
    renderActiveSheet();
  };

  App.actions.todayToggleBoost = function (a) {
    call('toggle_task', { id: a.id, index: a.index }).then(function () {
      return call('list');
    }).then(function (j) {
      B.data = j;
      /* Bu vazifa sport mashqi bo'lsa, Sport bo'limi ham darhol bir xil
         holatga keltiriladi. Server tomoni (bot) allaqachon jurnalga yozdi,
         shuning uchun `setDone` qayta yozmaydi (noBoostSync=true). */
      var task = window.BoostDay && BoostDay.findTaskByName
        ? findTaskTextById(a.id, a.index) : '';
      /* Sport ma'lumoti ham YUKLANGAN bo'lishi shart — `findByName`
         `S.data` bo'sh bo'lsa darrov `null` qaytaradi. Ilova Boostdayda
         ochilib, Sport bo'limi hech ochilmagan bo'lsa aynan shunday
         bo'lardi va galichka Sportga o'tmasdi. */
      if (task && window.SportBridge && SportBridge.findByName) {
        SportBridge.ensureLoaded().then(function () {
          var ex = SportBridge.findByName(task);
          if (ex) SportBridge.setDone(ex.cat, ex.id, isTaskDone(a.id, a.index));
        }).catch(function () {});
      }
      renderActiveSheet();
      renderTodayButton(App.el('page'));
      renderList(App.el('page'));
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* Rejadagi vazifaning matnini/holatini indeks bo'yicha topadi */
  function taskAt(planId, index) {
    var d = B.data || {}, res = null;
    ['daily_routines', 'todos', 'plans', 'reminders'].forEach(function (k) {
      (d[k] || []).forEach(function (p) {
        if (res || String(p.id) !== String(planId)) return;
        var groups = p.task_groups && p.task_groups.length
          ? p.task_groups : (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []);
        var i = 0;
        groups.forEach(function (g) {
          (g.tasks || []).forEach(function (t) {
            if (i === index) res = t;
            i++;
          });
        });
      });
    });
    return res;
  }
  function findTaskTextById(planId, index) { var t = taskAt(planId, index); return t ? t.text : ''; }
  function isTaskDone(planId, index) { var t = taskAt(planId, index); return !!t && +t.status === 1; }
  App.actions.todayToggleSport = function (a) {
    SportBridge.toggle(a.cat, a.id);
    renderActiveSheet();
    renderTodayButton(App.el('page'));
  };
  App.actions.todayHideSport = function (a) {
    // Tasodifiy bosilib ketishning oldini olish uchun ikki marta bosish talab
    // qilinadi (App.confirm() ISHLATILMAYDI — u sheet ochadi, bu esa joriy
    // "Bugungi ishlar" sheet'ini yopib qo'yardi). Birinchi bosish ✕ ni qizil
    // ✓ ga aylantiradi, 2.5 soniya ichida yana bosilsa — yashiriladi, aks
    // holda avtomatik asl holatiga qaytadi.
    if (PENDING_HIDE.id === String(a.id)) {
      if (PENDING_HIDE.timer) clearTimeout(PENDING_HIDE.timer);
      PENDING_HIDE = { id: null, timer: null };
      SportBridge.hideToday(a.id);
      renderActiveSheet();
      renderTodayButton(App.el('page'));
      return;
    }
    if (PENDING_HIDE.timer) clearTimeout(PENDING_HIDE.timer);
    PENDING_HIDE.id = String(a.id);
    PENDING_HIDE.timer = setTimeout(function () {
      PENDING_HIDE = { id: null, timer: null };
      renderActiveSheet();
    }, 2500);
    renderActiveSheet();
  };
  App.actions.todayUnhideSport = function (a) {
    SportBridge.unhideToday(a.id);
    renderActiveSheet();
    renderTodayButton(App.el('page'));
  };

  function renderList(page) {
    var box = App.el('bo-list'); if (!box) return;
    var list = allPlans().filter(function (p) { return p.status !== 'deleted'; });

    // Filtr
    if (B.filter !== 'all') {
      var d = B.data || {};
      switch (B.filter) {
        case 'daily_todo': list = d.daily_routines || []; break;
        case 'plans': list = (d.plans || []).concat(d.todos || []); break;
        case 'reminder': list = d.reminders || []; break;
        case 'todo': list = d.todos || []; break;
      }
    }

    // Qidiruv
    var q = (B.search || '').trim().toLowerCase();
    if (q) {
      list = list.filter(function (p) {
        var str = (p.channel_name || '') + ' ' + (p.preview || '') + ' ' + tinfo(p.plan_type).n;
        return str.toLowerCase().indexOf(q) >= 0;
      });
    }

    // Saralash (eng yangilari tepada)
    list.sort(function (a, b) { return b.id - a.id; });

    if (!list.length) {
      box.innerHTML = App.empty({ icon: 'refresh', title: 'Reja topilmadi', text: q ? 'Qidiruv natijasi bo\'sh.' : 'Pastdagi tugma bilan birinchi rejani qo\'shing.' });
      App.icons(box); return;
    }

    box.innerHTML = list.map(planItemHtml).join('');
    App.icons(box);
  }

  /* =========================================================
     VIEW: boost_stats — Statistika sahifasi
     ========================================================= */
  App.view('boost_stats', {
    nav: 'boost',
    render: function (page) {
      page.innerHTML = topbar('Statistika', 'boost') +
        '<div id="bst-cards"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<div id="bst-daily" style="margin-top:14px"></div>' +
        '<div id="bst-monthly" style="margin-top:14px"></div>' +
        '<div id="bst-types" style="margin-top:14px"></div>';
      App.icons(page);

      call('stats').then(function (j) {
        B.stats = j;
        var s = j.summary || {};
        var p = j.periods || {};
        var w = p.week || {}, m = p.month || {}, y = p.year || {};

        // Kartochkalar
        var cards = App.el('bst-cards');
        cards.innerHTML = '<div class="stat-strip" style="margin:0">' +
          '<div class="s"><div class="n" style="color:var(--accent)">' + (s.percent || 0) + '%</div><div class="l">Umumiy · ' + (s.completed_tasks || 0) + '/' + (s.total_tasks || 0) + '</div></div>' +
          '<div class="s"><div class="n">' + (w.percent || 0) + '%</div><div class="l">Hafta · ' + (w.completed_tasks || 0) + '/' + (w.total_tasks || 0) + '</div></div>' +
          '<div class="s"><div class="n">' + (m.percent || 0) + '%</div><div class="l">Oy · ' + (m.completed_tasks || 0) + '/' + (m.total_tasks || 0) + '</div></div>' +
          '<div class="s"><div class="n">' + (y.percent || 0) + '%</div><div class="l">Yil · ' + (y.completed_tasks || 0) + '/' + (y.total_tasks || 0) + '</div></div></div>';

        // 14 kunlik grafik
        var daily = j.daily_series || [];
        if (daily.length) {
          var maxD = Math.max.apply(null, daily.map(function (x) { return x.percent || 0; })) || 1;
          App.el('bst-daily').innerHTML = '<div class="card" style="padding:14px">' +
            '<div class="list-label" style="margin:-2px 0 8px">Oxirgi 14 kun</div>' +
            '<div style="display:flex;align-items:flex-end;gap:4px;height:100px">' +
            daily.map(function (x) {
              var h = Math.round(((x.percent || 0) / maxD) * 100);
              return '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;min-width:0">' +
                '<div style="width:100%;background:var(--border-soft);border-radius:4px 4px 2px 2px;height:100%;display:flex;align-items:flex-end">' +
                '<div style="width:100%;background:var(--accent);border-radius:4px 4px 0 0;height:' + h + '%;transition:height .4s"></div></div>' +
                '<div style="font-size:8px;color:var(--hint);white-space:nowrap;overflow:hidden">' + App.esc(x.label || '') + '</div></div>';
            }).join('') + '</div></div>';
        }

        // 12 oylik grafik
        var monthly = j.monthly_series || [];
        if (monthly.length) {
          var maxM = Math.max.apply(null, monthly.map(function (x) { return x.percent || 0; })) || 1;
          App.el('bst-monthly').innerHTML = '<div class="card" style="padding:14px">' +
            '<div class="list-label" style="margin:-2px 0 8px">Oxirgi 12 oy</div>' +
            '<div style="display:flex;align-items:flex-end;gap:4px;height:100px">' +
            monthly.map(function (x) {
              var h = Math.round(((x.percent || 0) / maxM) * 100);
              return '<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;min-width:0">' +
                '<div style="width:100%;background:var(--border-soft);border-radius:4px 4px 2px 2px;height:100%;display:flex;align-items:flex-end">' +
                '<div style="width:100%;background:var(--purple);border-radius:4px 4px 0 0;height:' + h + '%;transition:height .4s"></div></div>' +
                '<div style="font-size:8px;color:var(--hint);white-space:nowrap">' + App.esc(x.label || '') + '</div></div>';
            }).join('') + '</div></div>';
        }

        // Reja turlari taqsimoti
        var bd = j.plan_breakdown || {};
        var maxB = 1;
        Object.keys(bd).forEach(function (k) { if (bd[k] > maxB) maxB = bd[k]; });
        var typesHtml = Object.keys(TYPES).map(function (k) {
          var v = bd[k] || 0;
          var pct = Math.round((v / maxB) * 100);
          var ti = tinfo(k);
          return '<div style="display:flex;align-items:center;gap:10px;margin-bottom:9px">' +
            '<div style="font-size:13px;min-width:110px">' + ti.e + ' ' + ti.n + '</div>' +
            '<div style="flex:1;height:8px;background:var(--border-soft);border-radius:4px;overflow:hidden">' +
            '<div style="height:100%;background:' + ti.c + ';border-radius:4px;width:' + pct + '%;transition:width .4s"></div></div>' +
            '<div style="font-size:12px;color:var(--hint);min-width:24px;text-align:right;font-weight:600">' + v + '</div></div>';
        }).join('');
        App.el('bst-types').innerHTML = '<div class="card" style="padding:14px">' +
          '<div class="list-label" style="margin:-2px 0 10px">Reja turlari</div>' + typesHtml + '</div>';

      }).catch(function (e) {
        var cards = App.el('bst-cards');
        if (cards) cards.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
      });
    }
  });

  /* =========================================================
     VIEW: boost_plan — Bitta reja (tahrirlash)
     ========================================================= */
  App.view('boost_plan', {
    nav: 'boost',
    render: function (page, params) {
      var id = params.id;
      page.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
      Promise.all([
        call('get', { id: id }),
        B.channels ? Promise.resolve(B.channels) : call('channels').then(function (j) { return (B.channels = j.channels || []); })
      ]).then(function (r) {
        var p = r[0].item; if (!p) { App.go('boost'); return; }
        renderPlan(page, p);
      }).catch(function (e) { App.toast('⚠️ ' + e.message); App.go('boost'); });
    }
  });

  /* Kanalga tayinlangan mavzular (Sport/Ingliz/Rus/Dasturlash) uchun bo'lim nomi.
     `TOPICS` (Kanallar oynasidagi chip'lar) bilan bir xil bo'lishi shart. */
  var TOPIC_GROUP_NAME = { sport: '🏋 Sport', english: '🇬🇧 Ingliz tili', russian: '🇷🇺 Rus tili', dasturlash: '💻 Dasturlash' };

  /* Mavzu bo'limi BIRINCHI marta yaratilganda ichiga avtomatik yoziladigan
     standart vazifalar — Sport uchun barcha mashqlar nomi, Ingliz/Rus tili
     uchun lug'at kategoriyalari nomi. Nomlar tegishli bo'limdagi haqiqiy
     nomlar bilan AYNAN bir xil bo'lgani uchun (Sport -> sport.js mashq nomi,
     Lug'at -> vocab.js kategoriya nomi) bajarilganda statistikaga to'g'ri
     tushadi (masalan "1-100" lug'ati yodlansa — Lug'at grafigida ko'rinadi).
     Natija keshlanadi, har safar qayta so'ralmaydi. */
  var TOPIC_DEFAULTS_CACHE = {};
  function defaultItemsForTopic(topic) {
    // Foydalanuvchi iltimosiga ko'ra, endi mavzu qo'shilganda yuzlab
    // standart mashqlar avtomatik kiritilmaydi. Bo'lim faqat bo'sh holatda
    // yaratiladi, foydalanuvchi kerakli vazifalarni o'zi qo'shadi.
    return Promise.resolve([]);
  }

  /* Kanal mavzulariga mos bo'limlarni avtomatik tayyorlaydi — foydalanuvchi
     "+ Bo'lim" bosib har safar qo'lda nom kiritmasin. Faqat YETISHMAYOTGANLARI
     qo'shiladi (mavjudlariga tegilmaydi, ochirilgan/o'zgartirilganini qayta
     tiklamaydi — "xohlasam o'zgartiraman, bo'lmasa yo'q" shu tarzda ishlaydi:
     birinchi marta avtomatik qo'yiladi — ICHIDAGI standart vazifalar bilan
     birga — keyin foydalanuvchi ixtiyorida). Natija tayyor bo'lgach `cb()`
     chaqiriladi (defaultlar server/lokal manbadan async olinadi). */
  function syncGroupsWithChannelTopics(page, cb) {
    var p = page._plan;
    if (!p || ['todo', 'super_todo', 'daily_todo'].indexOf(p.plan_type) < 0) { if (cb) cb(); return; }
    var chan = (B.channels || []).find(function (c) { return c.channel_id === p.channel_id; });
    var topics = chan ? (chan.topics || '').split(',').filter(Boolean) : [];
    if (!topics.length) { if (cb) cb(); return; }
    var names = page._groups.map(function (g) { return (g.name || '').trim(); });
    var newTopics = topics.filter(function (t) { return TOPIC_GROUP_NAME[t] && names.indexOf(TOPIC_GROUP_NAME[t]) < 0; });
    if (!newTopics.length) { if (cb) cb(); return; }
    Promise.all(newTopics.map(defaultItemsForTopic)).then(function (lists) {
      newTopics.forEach(function (t, i) {
        var label = TOPIC_GROUP_NAME[t];
        if (page._groups.some(function (g) { return (g.name || '').trim() === label; })) return;
        var tasks = (lists[i] || []).map(function (name) { return { text: name, status: 0 }; });
        page._groups.push({ name: label, tasks: tasks });
      });
      // Agar faqat bitta, umuman bo'sh va nomsiz bo'lim qolgan bo'lsa (hech qachon
      // to'ldirilmagan boshlang'ich holat) — endi mavzu bo'limlari qo'shilgani
      // uchun ortiqcha, olib tashlaymiz.
      page._groups = page._groups.filter(function (g) { return (g.name || '').trim() || (g.tasks || []).length; });
      if (!page._groups.length) page._groups.push({ name: '', tasks: [] });
      if (cb) cb();
    });
  }

  function renderPlan(page, p) {
    var ti = tinfo(p.plan_type);
    var groups = (p.task_groups && p.task_groups.length) ? p.task_groups : (Array.isArray(p.tasks) ? [{name:'', tasks: p.tasks}] : [{name:'', tasks:[]}]);
    var total = planCount(p), done = planDone(p);
    var pct = total ? Math.round(done * 100 / total) : 0;

    var chansHtml = '<div class="bo-hero-t">' + App.esc(p.channel_name || '—') + '</div>';
    if (B.channels && B.channels.length) {
      chansHtml = '<select class="input bo-field" data-f="channel_id" style="background:rgba(255,255,255,0.1);color:inherit;border:none;font-weight:700;font-size:16px;padding:2px 8px;margin-bottom:4px;border-radius:6px">';
      B.channels.forEach(function(c) {
        chansHtml += '<option style="color:#000" value="' + App.esc(c.channel_id) + '"' + (c.channel_id === p.channel_id ? ' selected' : '') + '>' + App.esc(c.channel_name) + '</option>';
      });
      chansHtml += '</select>';
    }

    page.innerHTML = topbar(ti.e + ' ' + ti.n, 'boost') +
      '<div class="bo-hero" style="background:color-mix(in srgb,' + ti.c + ' 12%, transparent)">' +
      '<span class="bo-hero-ic" style="background:color-mix(in srgb,' + ti.c + ' 20%, transparent);color:' + ti.c + '">' +
      '<span data-icon="' + ti.ic + '" data-icon-size="22"></span></span>' +
      chansHtml +
      '<div class="bo-hero-s">' + App.esc(ti.d) + '</div></div>' +

      (total ? '<div class="stat-strip" style="margin:16px 0 8px">' +
        '<div class="s"><div class="n">' + total + '</div><div class="l">Vazifa</div></div>' +
        '<div class="s"><div class="n" style="color:var(--success)">' + done + '</div><div class="l">Bajarildi</div></div>' +
        '<div class="s"><div class="n">' + pct + '%</div><div class="l">Natija</div></div></div>' +
        '<div class="bar" style="margin:0 1px 14px"><i style="width:' + pct + '%"></i></div>' : '') +

      '<div class="list-row"><span class="li-ic" data-icon="clock" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Vaqt</div><div class="li-sub" style="display:flex;gap:6px;margin-top:4px">' +
      '<input type="time" class="input bo-field" data-f="time" value="' + App.esc(p.time || '') + '" style="padding:4px 8px;font-size:13px;width:110px">' +
      (p.plan_type === 'daily_todo' ? '<select class="input bo-field" data-f="week_mode" style="padding:4px 8px;font-size:13px;width:120px"><option value="everyday"'+(p.week_mode==='everyday'?' selected':'')+'>Har kuni</option><option value="odd"'+(p.week_mode==='odd'?' selected':'')+'>Toq kunlar</option><option value="even"'+(p.week_mode==='even'?' selected':'')+'>Juft kunlar</option></select>' : '') +
      '</div></div></div>' +
      (p.date !== undefined && (p.plan_type === 'todo' || p.plan_type === 'super_todo' || p.plan_type === 'reminder') ? '<div class="list-row"><span class="li-ic" data-icon="calendar" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Sana</div><div class="li-sub" style="margin-top:4px"><input type="date" class="input bo-field" data-f="date" value="' + App.esc(p.date) + '" style="padding:4px 8px;font-size:13px;width:150px"></div></div></div>' : '') +
      (p.start_date !== undefined && p.plan_type === 'challenge' ? '<div class="list-row"><span class="li-ic" data-icon="calendar" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Muddat</div><div class="li-sub" style="display:flex;gap:6px;margin-top:4px"><input type="date" class="input bo-field" data-f="start_date" value="' + App.esc(p.start_date) + '" style="padding:4px 8px;font-size:13px;flex:1"><input type="date" class="input bo-field" data-f="end_date" value="' + App.esc(p.end_date || '') + '" style="padding:4px 8px;font-size:13px;flex:1"></div></div></div>' : '') +

      '<div class="between list-label"><span>Vazifalar</span>' +
      '<span style="display:flex;gap:12px">' +
      '<button data-act="boostPickPlan" style="background:none;border:none;color:var(--accent);font-size:12px;font-weight:700;text-transform:none;letter-spacing:0">Bo\'limdan</button>' +
      '<button data-act="boostAddGroup" style="background:none;border:none;color:var(--accent);font-size:12px;font-weight:700;text-transform:none;letter-spacing:0">+ Bo\'lim</button></span></div>' +
      '<div id="bo-tasks"></div>' +

      /* Matn va Media (daily_plan, challenge, reminder uchun) */
      '<div id="bo-content"></div>' +

      '<div class="btn-row" style="margin-top:18px;flex-direction:column;gap:10px">' +
      '<button class="btn" id="bo-save">Saqlash</button>' +
      '<button class="btn ghost" id="bo-del" style="color:var(--danger);border-color:var(--danger-soft)">Rejani o\'chirish</button></div>';
    App.icons(page);

    page._plan = p;
    page._groups = groups.length ? JSON.parse(JSON.stringify(groups)) : [{ name: '', tasks: [] }];

    // Kontent (text/media) — faqat daily_plan, challenge, reminder uchun
    var isTasks = ['todo', 'super_todo', 'daily_todo'].indexOf(p.plan_type) >= 0;
    if (!isTasks && p.items && p.items.length) {
      var contentBox = App.el('bo-content');
      var textItems = p.items.filter(function (it) { return it.type === 'text'; });
      var mediaItems = p.items.filter(function (it) { return it.type !== 'text'; });
      var html = '';
      if (textItems.length) {
        html += '<div class="list-label">Matn</div>';
        textItems.forEach(function (it) {
          html += '<div class="card" style="padding:12px;white-space:pre-wrap;font-size:14px">' + App.esc(it.text || '') + '</div>';
        });
      }
      if (mediaItems.length) {
        html += '<div class="list-label">Media (' + mediaItems.length + ' ta)</div>';
        mediaItems.forEach(function (it) {
          var label = { photo: '🖼 Rasm', video: '🎬 Video', audio: '🎵 Audio', document: '📄 Fayl' }[it.type] || '📎 Fayl';
          html += '<div class="list-row"><span class="li-ic" style="background:var(--accent-soft);color:var(--accent)"><span data-icon="image" data-icon-size="14"></span></span>' +
            '<div class="li-main"><div class="li-title">' + label + '</div>' +
            (it.caption ? '<div class="li-sub">' + App.esc(it.caption) + '</div>' : '') +
            '</div></div>';
        });
      }
      contentBox.innerHTML = html;
      App.icons(contentBox);
    }

    drawTasks(page);
    syncGroupsWithChannelTopics(page, function () { drawTasks(page); });

    App.el('bo-save').onclick = function () { savePlan(page); };
    App.el('bo-del').onclick = function () {
      App.confirm('Bu reja o\'chiriladi. Bot endi uni yubormaydi.', function () {
        call('delete', { id: p.id }).then(function () { App.toast('O\'chirildi'); App.go('boost'); })
          .catch(function (e) { App.toast('⚠️ ' + e.message); });
      }, { danger: true, yes: 'O\'chirish' });
    };

    // Form inputs ni update qilish
    page.querySelectorAll('.bo-field').forEach(function(i) {
      i.onchange = function() {
        var k = i.getAttribute('data-f');
        if (k === 'channel_id') {
          var sel = i.options[i.selectedIndex];
          p.channel_id = i.value;
          p.channel_name = sel ? sel.text : p.channel_name;
          drawTasks(page);
          syncGroupsWithChannelTopics(page, function () { drawTasks(page); });
        } else {
          p[k] = i.value;
        }
      };
    });
  }

  function drawTasks(page) {
    var box = App.el('bo-tasks'); if (!box) return;
    var groups = page._groups;
    box.innerHTML = groups.map(function (g, gi) {
      /* Vaqt oralig'i BO'LIMGA tegishli (vazifaga emas): amalda bir
         bo'limdagi ishlar bitta oraliqda bajariladi, shuning uchun uni
         har bir vazifaga alohida yozish ortiqcha edi. */
      var gTime = (g.time || '').trim();
      return '<div class="bo-group" data-g="' + gi + '">' +
        '<div class="flex" style="gap:8px;margin-bottom:8px">' +
        '<input class="input bo-gname" data-g="' + gi + '" value="' + App.esc(g.name || '') +
        '" placeholder="Bo\'lim nomi (ixtiyoriy)" style="flex:1;font-weight:700">' +
        '<button class="icon-btn ghost bo-gtime" data-g="' + gi + '" title="Bo\'lim vaqti" ' +
        'style="width:34px;height:34px;color:' + (gTime ? 'var(--accent)' : 'var(--hint)') + '">' +
        '<span data-icon="clock" data-icon-size="15"></span></button>' +
        '<button class="icon-btn ghost bo-gdel" data-g="' + gi + '" style="width:34px;height:34px;color:var(--danger)">' +
        '<span data-icon="trash" data-icon-size="15"></span></button></div>' +
        (gTime ? '<div class="bo-gtime-lb" data-g="' + gi + '">' + App.esc(gTime) + '</div>' : '') +
        (g.tasks || []).map(function (t, ti2) {
          var doneCls = +t.status === 1 ? ' done' : '';
          return '<div class="bo-task' + doneCls + '" draggable="true" data-g="' + gi + '" data-t="' + ti2 + '">' +
            '<button class="icon-btn ghost bo-tdrag" style="width:24px;height:30px;color:var(--hint);cursor:grab;padding:0">' +
            '<span data-icon="menu" data-icon-size="14"></span></button>' +
            '<button class="bo-check' + doneCls + '" data-g="' + gi + '" data-t="' + ti2 + '">' +
            (+t.status === 1 ? '✓' : '') + '</button>' +
            '<input class="input bo-ttext" data-g="' + gi + '" data-t="' + ti2 + '" value="' + App.esc(t.text || '') + '">' +
            (t.duration ? '<span style="font-size:11px;color:var(--hint);white-space:nowrap;padding:0 4px">' + t.duration + ' daq</span>' : '') +
            '<button class="icon-btn ghost bo-tdel" data-g="' + gi + '" data-t="' + ti2 + '" style="width:30px;height:30px">' +
            '<span data-icon="x" data-icon-size="14"></span></button></div>';
        }).join('') +
        '<button class="btn sec sm bo-tadd" data-g="' + gi + '" style="width:100%;margin-top:4px">+ Vazifa</button></div>';
    }).join('');
    App.icons(box);

    box.querySelectorAll('.bo-gname').forEach(function (i) {
      i.oninput = function () { groups[+i.getAttribute('data-g')].name = i.value; };
    });
    box.querySelectorAll('.bo-ttext').forEach(function (i) {
      i.oninput = function () {
        groups[+i.getAttribute('data-g')].tasks[+i.getAttribute('data-t')].text = i.value;
      };
    });
    box.querySelectorAll('.bo-check').forEach(function (b) {
      b.onclick = function () {
        var t = groups[+b.getAttribute('data-g')].tasks[+b.getAttribute('data-t')];
        t.status = +t.status === 1 ? 0 : 1;
        drawTasks(page);
      };
    });
    box.querySelectorAll('.bo-tdel').forEach(function (b) {
      b.onclick = function () {
        groups[+b.getAttribute('data-g')].tasks.splice(+b.getAttribute('data-t'), 1);
        drawTasks(page);
      };
    });
    box.querySelectorAll('.bo-gtime').forEach(function (b) {
      b.onclick = function () {
        boGroupTime(groups, +b.getAttribute('data-g'), function () { drawTasks(page); });
      };
    });
    box.querySelectorAll('.bo-tadd').forEach(function (b) {
      b.onclick = function () {
        var gi = +b.getAttribute('data-g');
        groups[gi].tasks.push({ text: '', status: 0 });
        drawTasks(page);
      };
    });
    box.querySelectorAll('.bo-gdel').forEach(function (b) {
      b.onclick = function () {
        if (groups.length <= 1) { groups[0] = { name: '', tasks: [] }; drawTasks(page); return; }
        groups.splice(+b.getAttribute('data-g'), 1);
        drawTasks(page);
      };
    });

    // Drag and Drop implementation
    var dragged = null;
    box.ondragstart = function(e) {
      var t = e.target.closest('.bo-task');
      if (t) { dragged = t; e.dataTransfer.effectAllowed = 'move'; t.style.opacity = 0.5; }
    };
    box.ondragover = function(e) {
      e.preventDefault();
      var t = e.target.closest('.bo-task');
      if (t && t !== dragged) {
        var rect = t.getBoundingClientRect();
        var mid = rect.top + rect.height/2;
        if (e.clientY < mid) t.parentNode.insertBefore(dragged, t);
        else t.parentNode.insertBefore(dragged, t.nextSibling);
      }
    };
    box.ondragend = function(e) {
      if (dragged) {
        dragged.style.opacity = '';
        var newGroups = [];
        box.querySelectorAll('.bo-group').forEach(function(gEl) {
          var name = (gEl.querySelector('.bo-gname')||{}).value || '';
          var tasks = [];
          gEl.querySelectorAll('.bo-task').forEach(function(tEl) {
            var gi = +tEl.getAttribute('data-g');
            var ti = +tEl.getAttribute('data-t');
            if (groups[gi] && groups[gi].tasks[ti]) tasks.push(groups[gi].tasks[ti]);
          });
          newGroups.push({ name: name, tasks: tasks });
        });
        page._groups = newGroups;
        drawTasks(page);
      }
    };
  }

  /* Vaqt oralig'ini bir ko'rinishga keltiradi: "8:0-8.30" -> "08:00 - 08:30".
     Tushunarsiz bo'lsa bo'sh qaytaradi (vaqt ixtiyoriy — majburlamaymiz).
     AYNI qoida mini app'da ham bor (miniapp.html::normTimeRange). */
  function normTimeRange(raw) {
    var s = String(raw == null ? '' : raw).trim();
    if (!s) return '';
    var m = s.match(/^(\d{1,2})[:.\s]?(\d{2})\s*(?:[-–—]\s*(\d{1,2})[:.\s]?(\d{2}))?$/);
    if (!m) return '';
    /* Chegaradan chiqqan qiymat QISILMAYDI, rad etiladi: `25:99 - 30:00`
       ni qisib `23:59 - 23:00` qilish teskari oraliq yasardi. */
    function p(h, mi) {
      h = +h; mi = +mi;
      if (h > 23 || mi > 59) return null;
      return ('0' + h).slice(-2) + ':' + ('0' + mi).slice(-2);
    }
    var a = p(m[1], m[2]);
    if (!a) return '';
    if (!m[3]) return a;
    var b = p(m[3], m[4]);
    return b ? a + ' - ' + b : '';
  }

  /* BO'LIM vaqtini tahrirlash. Ilgari vaqt har bir vazifa MATNI ichida
     prefiks bo'lib turardi (`08:00 - 08:30 | Vazifa`); endi bo'limning
     o'z maydonida — bir bo'limdagi ishlar baribir bitta oraliqda
     bajariladi.
     Yangi bo'limga standart qiymat: oldingi bo'lim tugagan vaqtdan
     boshlab, o'sha uzunlikda (qo'lda yozishni kamaytiradi). */
  function boGroupTime(groups, gi, callback) {
    var def = (groups[gi].time || '').trim();

    if (!def) {
      var prevStart = null, prevEnd = null;
      for (var ig = gi - 1; ig >= 0; ig--) {
        var pm = (groups[ig].time || '').match(/^(\d{2}:\d{2})(?:\s*-\s*(\d{2}:\d{2}))?$/);
        if (pm) { prevStart = pm[1]; prevEnd = pm[2] || pm[1]; break; }
      }
      var dur = 30;
      if (prevStart && prevEnd && prevStart !== prevEnd) {
        var ps = prevStart.split(':'), pe = prevEnd.split(':');
        var d1 = new Date(); d1.setHours(+ps[0] || 0, +ps[1] || 0, 0, 0);
        var d2 = new Date(); d2.setHours(+pe[0] || 0, +pe[1] || 0, 0, 0);
        var diff = Math.round((d2 - d1) / 60000);
        if (diff > 0 && diff <= 600) dur = diff;
      }
      if (prevEnd) {
        var p2 = prevEnd.split(':');
        var d = new Date(); d.setHours(+p2[0] || 0, +p2[1] || 0, 0, 0);
        var nStart = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
        d.setMinutes(d.getMinutes() + dur);
        var nEnd = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
        def = nStart + ' - ' + nEnd;
      }
    }

    var title = (groups[gi].name || '').trim();
    App.prompt({
      title: title ? title + ' — vaqti' : 'Bo\'lim vaqti',
      label: 'Masalan: 08:00 - 08:30 (bo\'sh qoldirilsa o\'chiriladi)',
      value: def,
      /* `allowEmpty` SHART: usiz `App.prompt` bo'sh qiymatni rad etib
         "Bo'sh bo'lmasin" deydi, ya'ni vaqtni O'CHIRIB bo'lmasdi. */
      allowEmpty: true
    }, function (val) {
      groups[gi].time = normTimeRange(val);
      callback();
    });
  }

  App.actions.boostAddGroup = function () {
    var page = App.el('page');
    page._groups.push({ name: '', tasks: [] });
    drawTasks(page);
  };

  /* Tanlangan materiallarni MAVZU NOMIDAGI bo'limga qo'shadi (yo'q bo'lsa
     yaratadi) — shu tarzda bitta rejada Sport va tillar aralashib ketmaydi
     va Telegramda belgilanganda statistika to'g'ri bo'limga tushadi. */
  function addPickedToGroups(groups, picked) {
    var added = 0;
    picked.forEach(function (p) {
      var label = TOPIC_GROUP_NAME[p.topic] || '';
      var g = label
        ? groups.filter(function (x) { return (x.name || '').trim() === label; })[0]
        : groups[0];
      if (!g) {
        g = { name: label, tasks: [] };
        var empty = -1;
        groups.forEach(function (x, i) { if (empty < 0 && !(x.name || '').trim() && !(x.tasks || []).length) empty = i; });
        if (empty >= 0) groups[empty] = g; else groups.push(g);
      }
      g.tasks = g.tasks || [];
      var exists = g.tasks.some(function (t) { return (t.text || '') === p.name; });
      if (!exists) { g.tasks.push({ text: p.name, status: 0 }); added++; }
    });
    return added;
  }

  App.actions.boostPickPlan = function () {
    var page = App.el('page');
    if (!page || !page._groups) return;
    pkOpen(function (picked) {
      var n = addPickedToGroups(page._groups, picked);
      drawTasks(page);
      App.toast(n ? ('✅ ' + n + ' ta vazifa qo\'shildi — saqlashni unutmang') : 'Bularning hammasi allaqachon bor');
    });
  };

  /* Bo'lim nomiga qarab statistika bo'limini aniqlaydi — bot_py'dagi
     helpers.py::_section_for_group bilan bir xil mantiq (nomi bilan mos
     kelishi shart, aks holda saytda bajarilgan vazifa noto'g'ri statistikaga
     tushib qoladi). */
  function sectionForGroup(groupName, chanId) {
    var g = (groupName || '').toLowerCase();
    if (g.indexOf('sport') >= 0 || (groupName || '').indexOf('🏋') >= 0) return { section: 'sport', unit: 'marta' };
    if (g.indexOf('ingliz') >= 0 || g.indexOf('english') >= 0 || g.indexOf('rus') >= 0 ||
        (groupName || '').indexOf('🇬🇧') >= 0 || (groupName || '').indexOf('🇷🇺') >= 0) return { section: 'vocab', unit: 'so\'z' };
    var chan = (B.channels || []).find(function (c) { return c.channel_id === chanId; });
    var topics = chan ? topicsOf(chan) : [];
    if (topics.length === 1) {
      if (topics[0] === 'sport') return { section: 'sport', unit: 'marta' };
      if (topics[0] === 'english' || topics[0] === 'russian') return { section: 'vocab', unit: 'so\'z' };
    }
    return { section: 'boostday', unit: 'vazifa' };
  }

  function newlyDoneTasks(page) {
    // Saqlashdan oldingi (serverdagi) va joriy holatni solishtirib, endigina "bajarildi"
    // deb belgilangan vazifalarni topadi — Faoliyat jurnaliga shular yoziladi.
    var origGroups = (page._plan.task_groups && page._plan.task_groups.length)
      ? page._plan.task_groups
      : (Array.isArray(page._plan.tasks) ? [{ tasks: page._plan.tasks }] : []);
    var wasDone = {};
    origGroups.forEach(function (g) {
      (g.tasks || []).forEach(function (t) { if (+t.status === 1) wasDone[(t.text || '').trim()] = true; });
    });
    var out = [];
    page._groups.forEach(function (g) {
      (g.tasks || []).forEach(function (t) {
        var text = (t.text || '').trim();
        if (text && +t.status === 1 && !wasDone[text]) out.push({ text: text, group: g.name || '' });
      });
    });
    return out;
  }

  /* Vazifalarni YASSI ro'yxat sifatida yuborish mumkinmi?
     Faqat bitta bo'lim bo'lsa VA uning na nomi, na VAQTI bo'lsa —
     aks holda bo'lim vaqti saqlashda jimgina yo'qolib ketardi
     (bot ham aynan shu shartni ishlatadi: helpers.py::encode_task_groups). */
  function flatOk(groups) {
    if (groups.length !== 1) return false;
    var g = groups[0];
    return !(g.name || '').trim() && !(g.time || '').trim();
  }

  function savePlan(page) {
    var p = page._plan;
    var groups = page._groups.map(function (g) {
      return {
        /* `cat` — Kun hisobidagi rang turkumi. Tahrirlagichda ko'rinmaydi,
           lekin bu yerda ko'chirilmasa saqlashda YO'QOLARDI va bo'lim
           rangi "boshqa"ga tushib qolardi. */
        name: g.name || '', time: g.time || '', cat: g.cat || '',
        tasks: (g.tasks || []).filter(function (t) { return (t.text || '').trim(); })
      };
    }).filter(function (g) { return g.tasks.length || g.name; });

    var doneNow = newlyDoneTasks(page);
    var isSingleUnnamed = flatOk(groups);
    var tasksPayload = isSingleUnnamed ? JSON.stringify(groups[0].tasks) : JSON.stringify({ groups: groups });

    var btn = App.el('bo-save'); btn.disabled = true; btn.textContent = 'Saqlanmoqda...';
    call('save', {
      id: p.id, plan_type: p.plan_type, channel_id: p.channel_id, channel_name: p.channel_name,
      time: p.time || '', date: p.date || '', start_date: p.start_date || '', end_date: p.end_date || '',
      week_mode: p.week_mode || 'everyday',
      items: JSON.stringify(p.items || []),
      tasks: tasksPayload
    }).then(function () {
      App.toast('✅ Saqlandi'); btn.disabled = false; btn.textContent = 'Saqlash';
      if (window.Activity) Activity.mark();
      doneNow.forEach(function (it) {
        var s = sectionForGroup(it.group, p.channel_id);
        App.call('log_activity', { section: s.section, object: it.text, amount: 1, unit: s.unit, meta: { plan_type: p.plan_type, channel: p.channel_name } }).catch(function () {});
      });
    }).catch(function (e) {
      App.toast('⚠️ ' + e.message); btn.disabled = false; btn.textContent = 'Saqlash';
    });
  }

  /* ---------- Yangi reja (kengaytirilgan) ----------
     `NEW_STATE` — "Bo'limdan tanlash" uchun. App.sheet() har doim avvalgi
     sheet'ni yopadi (ustma-ust ochilmaydi), shuning uchun tanlagichni ochishdan
     oldin forma holati shu yerga olinadi va tanlash tugagach oyna AYNAN shu
     holatda qayta ochiladi — kiritilgan ma'lumot yo'qolmaydi. */
  var NEW_STATE = null;

  App.actions.boostNew = function () {
    call('channels').then(function (j) {
      var chans = j.channels || [];
      if (!chans.length) {
        App.toast('Avval kanal ulang'); App.actions.boostChannels(); return;
      }
      var html =
        '<label class="field"><span>Reja turi</span><select class="input" id="bn-type">' +
        Object.keys(TYPES).map(function (k) {
          return '<option value="' + k + '">' + TYPES[k].e + ' ' + TYPES[k].n + '</option>';
        }).join('') + '</select></label>' +
        '<p class="muted" id="bn-desc" style="font-size:12.5px;margin:-6px 1px 12px"></p>' +
        '<label class="field"><span>Kanal</span><select class="input" id="bn-ch">' +
        chans.map(function (c) {
          return '<option value="' + App.esc(c.channel_id) + '">' + App.esc(c.channel_name) + '</option>';
        }).join('') + '</select></label>' +
        '<label class="field"><span>Vaqt (soat:daqiqa)</span><input class="input" type="time" id="bn-time" value="07:00"></label>' +
        '<label class="field" id="bn-date-w"><span>Sana</span><input class="input" type="date" id="bn-date"></label>' +
        '<div class="flex" style="gap:8px" id="bn-range-w">' +
        '<label class="field" style="flex:1"><span>Boshlanish</span><input class="input" type="date" id="bn-start"></label>' +
        '<label class="field" style="flex:1"><span>Tugash</span><input class="input" type="date" id="bn-end"></label></div>' +
        '<label class="field" id="bn-week-w"><span>Qaysi kunlar</span><select class="input" id="bn-week">' +
        '<option value="everyday">Har kuni</option><option value="odd">Toq kunlar</option><option value="even">Juft kunlar</option></select></label>' +

        /* Matn va media (reja turlari uchun) */
        '<div id="bn-content-w">' +
        '<label class="field"><span>Asosiy matn</span><textarea class="input" id="bn-text" placeholder="Reja yoki eslatma matni..." rows="3"></textarea></label></div>' +

        /* Vazifalar (todo turlari uchun) */
        '<div id="bn-tasks-w" style="display:none">' +
        '<div id="bn-flat-w"><label class="field"><span>Vazifalar (har qatorda bitta)</span>' +
        '<textarea class="input" id="bn-tasks" placeholder="Kitob o\'qish\nSport mashqlari\nDars takrorlash" rows="5"></textarea></label>' +
        '<p class="muted" id="bn-super-hint" style="font-size:11.5px;margin:-6px 1px 8px;display:none">Super TO-DO formati: <b>Vazifa | daqiqa</b> (masalan: Kitob o\'qish | 25)</p></div>' +
        '<div id="bn-groups-w" style="display:none">' +
        '<div class="between list-label" style="margin:0 0 8px"><span>Vazifalar</span>' +
        '<span style="display:flex;gap:12px">' +
        '<button type="button" id="bn-pick" style="background:none;border:none;color:var(--accent);font-size:12px;font-weight:700;text-transform:none;letter-spacing:0">Bo\'limdan</button>' +
        '<button type="button" id="bn-addgroup" style="background:none;border:none;color:var(--accent);font-size:12px;font-weight:700;text-transform:none;letter-spacing:0">+ Bo\'lim</button></span></div>' +
        '<div id="bn-groups-box"></div>' +
        '<p class="muted" style="font-size:11.5px;margin:6px 1px 0">Kanalga mavzu (Sport/Ingliz/Rus tili/Dasturlash) tayinlangan bo\'lsa — tegishli bo\'lim avtomatik qo\'shiladi, xohlasangiz o\'zgartiring yoki o\'chiring.</p>' +
        '</div></div>' +

        '<button class="btn" id="bn-save">Yaratish</button>';
      var sh = App.sheet(html, { title: 'Yangi reja' });

      /* Bo'lim(lar)li vazifa muharriri — reja tahrirlash oynasidagi
         drawTasks()/syncGroupsWithChannelTopics() bilan bir xil mantiq,
         lekin hali saqlanmagan yangi reja uchun lokal massivda ishlaydi. */
      var NEW_GROUPS = (NEW_STATE && NEW_STATE.groups) ? NEW_STATE.groups : [{ name: '', tasks: [] }];
      function drawNewGroups() {
        var box = sh.querySelector('#bn-groups-box'); if (!box) return;
        box.innerHTML = NEW_GROUPS.map(function (g, gi) {
          var gTime = (g.time || '').trim();
          return '<div class="bo-group" data-g="' + gi + '">' +
            '<div class="flex" style="gap:8px;margin-bottom:8px">' +
            '<input class="input bn-gname" data-g="' + gi + '" value="' + App.esc(g.name || '') +
            '" placeholder="Bo\'lim nomi (ixtiyoriy)" style="flex:1;font-weight:700">' +
            '<button type="button" class="icon-btn ghost bn-gtime" data-g="' + gi + '" title="Bo\'lim vaqti" ' +
            'style="width:34px;height:34px;color:' + (gTime ? 'var(--accent)' : 'var(--hint)') + '">' +
            '<span data-icon="clock" data-icon-size="15"></span></button>' +
            '<button type="button" class="icon-btn ghost bn-gdel" data-g="' + gi + '" style="width:34px;height:34px;color:var(--danger)">' +
            '<span data-icon="trash" data-icon-size="15"></span></button></div>' +
            (gTime ? '<div class="bo-gtime-lb" data-g="' + gi + '">' + App.esc(gTime) + '</div>' : '') +
            (g.tasks || []).map(function (t, ti2) {
              return '<div class="bo-task" draggable="true" data-g="' + gi + '" data-t="' + ti2 + '">' +
                '<button type="button" class="icon-btn ghost bn-tdrag" style="width:24px;height:30px;color:var(--hint);cursor:grab;padding:0">' +
                '<span data-icon="menu" data-icon-size="14"></span></button>' +
                '<input class="input bn-ttext" data-g="' + gi + '" data-t="' + ti2 + '" value="' + App.esc(t.text || '') + '">' +
                '<button type="button" class="icon-btn ghost bn-tdel" data-g="' + gi + '" data-t="' + ti2 + '" style="width:30px;height:30px">' +
                '<span data-icon="x" data-icon-size="14"></span></button></div>';
            }).join('') +
            '<button type="button" class="btn sec sm bn-tadd" data-g="' + gi + '" style="width:100%;margin-top:4px">+ Vazifa</button></div>';
        }).join('');
        App.icons(box);
        box.querySelectorAll('.bn-gname').forEach(function (i) {
          i.oninput = function () { NEW_GROUPS[+i.getAttribute('data-g')].name = i.value; };
        });
        box.querySelectorAll('.bn-ttext').forEach(function (i) {
          i.oninput = function () { NEW_GROUPS[+i.getAttribute('data-g')].tasks[+i.getAttribute('data-t')].text = i.value; };
        });
        box.querySelectorAll('.bn-tdel').forEach(function (b) {
          b.onclick = function () {
            NEW_GROUPS[+b.getAttribute('data-g')].tasks.splice(+b.getAttribute('data-t'), 1);
            drawNewGroups();
          };
        });
        box.querySelectorAll('.bn-gtime').forEach(function (b) {
          b.onclick = function () {
            boGroupTime(NEW_GROUPS, +b.getAttribute('data-g'), function () { drawNewGroups(); });
          };
        });
        box.querySelectorAll('.bn-tadd').forEach(function (b) {
          b.onclick = function () {
            var gi = +b.getAttribute('data-g');
            NEW_GROUPS[gi].tasks.push({ text: '', status: 0 });
            drawNewGroups();
          };
        });
        box.querySelectorAll('.bn-gdel').forEach(function (b) {
          b.onclick = function () {
            if (NEW_GROUPS.length <= 1) { NEW_GROUPS[0] = { name: '', tasks: [] }; drawNewGroups(); return; }
            NEW_GROUPS.splice(+b.getAttribute('data-g'), 1);
            drawNewGroups();
          };
        });

        // Drag and Drop for new groups
        var dragged = null;
        box.ondragstart = function(e) {
          var t = e.target.closest('.bo-task');
          if (t) { dragged = t; e.dataTransfer.effectAllowed = 'move'; t.style.opacity = 0.5; }
        };
        box.ondragover = function(e) {
          e.preventDefault();
          var t = e.target.closest('.bo-task');
          if (t && t !== dragged) {
            var rect = t.getBoundingClientRect();
            var mid = rect.top + rect.height/2;
            if (e.clientY < mid) t.parentNode.insertBefore(dragged, t);
            else t.parentNode.insertBefore(dragged, t.nextSibling);
          }
        };
        box.ondragend = function(e) {
          if (dragged) {
            dragged.style.opacity = '';
            var newGroups = [];
            box.querySelectorAll('.bo-group').forEach(function(gEl) {
              var name = (gEl.querySelector('.bn-gname')||{}).value || '';
              var tasks = [];
              gEl.querySelectorAll('.bo-task').forEach(function(tEl) {
                var gi = +tEl.getAttribute('data-g');
                var ti = +tEl.getAttribute('data-t');
                if (NEW_GROUPS[gi] && NEW_GROUPS[gi].tasks[ti]) tasks.push(NEW_GROUPS[gi].tasks[ti]);
              });
              newGroups.push({ name: name, tasks: tasks });
            });
            NEW_GROUPS.length = 0;
            newGroups.forEach(function(g) { NEW_GROUPS.push(g); });
            drawNewGroups();
          }
        };
      }
      sh.querySelector('#bn-addgroup').onclick = function () { NEW_GROUPS.push({ name: '', tasks: [] }); drawNewGroups(); };

      /* Bo'limdan tanlash: forma holatini saqlab, tanlagichni ochamiz;
         tugagach shu oyna aynan o'sha holatda qayta ochiladi. */
      sh.querySelector('#bn-pick').onclick = function () {
        NEW_STATE = {
          type: sh.querySelector('#bn-type').value,
          ch: sh.querySelector('#bn-ch').value,
          time: sh.querySelector('#bn-time').value,
          date: sh.querySelector('#bn-date').value,
          start: sh.querySelector('#bn-start').value,
          end: sh.querySelector('#bn-end').value,
          week: sh.querySelector('#bn-week').value,
          groups: NEW_GROUPS
        };
        pkOpen(function (picked) {
          var n = addPickedToGroups(NEW_STATE.groups, picked);
          App.actions.boostNew();
          App.toast(n ? ('✅ ' + n + ' ta vazifa qo\'shildi') : 'Bularning hammasi allaqachon bor');
        });
      };

      function syncNewGroupsWithTopics() {
        var chId = sh.querySelector('#bn-ch').value;
        var chan = chans.find(function (c) { return c.channel_id === chId; });
        var topics = chan ? (chan.topics || '').split(',').filter(Boolean) : [];
        var names = NEW_GROUPS.map(function (g) { return (g.name || '').trim(); });
        var newTopics = topics.filter(function (t) { return TOPIC_GROUP_NAME[t] && names.indexOf(TOPIC_GROUP_NAME[t]) < 0; });
        if (!newTopics.length) { drawNewGroups(); return; }
        Promise.all(newTopics.map(defaultItemsForTopic)).then(function (lists) {
          newTopics.forEach(function (t, i) {
            var label = TOPIC_GROUP_NAME[t];
            if (NEW_GROUPS.some(function (g) { return (g.name || '').trim() === label; })) return;
            var tasks = (lists[i] || []).map(function (name) { return { text: name, status: 0 }; });
            NEW_GROUPS.push({ name: label, tasks: tasks });
          });
          NEW_GROUPS = NEW_GROUPS.filter(function (g) { return (g.name || '').trim() || (g.tasks || []).length; });
          if (!NEW_GROUPS.length) NEW_GROUPS.push({ name: '', tasks: [] });
          drawNewGroups();
        });
      }
      drawNewGroups();

      function sync() {
        var t = sh.querySelector('#bn-type').value;
        sh.querySelector('#bn-desc').textContent = tinfo(t).d;
        var isTasks = ['todo', 'super_todo', 'daily_todo'].indexOf(t) >= 0;
        var isGroupTasks = (t === 'todo' || t === 'daily_todo');
        sh.querySelector('#bn-date-w').style.display = (t === 'todo' || t === 'super_todo' || t === 'reminder') ? '' : 'none';
        sh.querySelector('#bn-range-w').style.display = (t === 'challenge') ? '' : 'none';
        sh.querySelector('#bn-week-w').style.display = (t === 'daily_todo') ? '' : 'none';
        sh.querySelector('#bn-content-w').style.display = isTasks ? 'none' : '';
        sh.querySelector('#bn-tasks-w').style.display = isTasks ? '' : 'none';
        sh.querySelector('#bn-flat-w').style.display = isGroupTasks ? 'none' : '';
        sh.querySelector('#bn-groups-w').style.display = isGroupTasks ? '' : 'none';
        sh.querySelector('#bn-super-hint').style.display = (t === 'super_todo') ? '' : 'none';
        if (isGroupTasks) syncNewGroupsWithTopics();
      }
      sh.querySelector('#bn-type').onchange = sync;
      sh.querySelector('#bn-ch').onchange = function () {
        if (['todo', 'daily_todo'].indexOf(sh.querySelector('#bn-type').value) >= 0) syncNewGroupsWithTopics();
      };
      // "Bo'limdan tanlash"dan qaytgan bo'lsak — kiritilganlarni tiklaymiz
      if (NEW_STATE) {
        var st = NEW_STATE; NEW_STATE = null;
        sh.querySelector('#bn-type').value = st.type;
        sh.querySelector('#bn-ch').value = st.ch;
        sh.querySelector('#bn-time').value = st.time;
        sh.querySelector('#bn-date').value = st.date;
        sh.querySelector('#bn-start').value = st.start;
        sh.querySelector('#bn-end').value = st.end;
        sh.querySelector('#bn-week').value = st.week;
      }
      sync();

      sh.querySelector('#bn-save').onclick = function () {
        var t = sh.querySelector('#bn-type').value;
        var chSel = sh.querySelector('#bn-ch');
        var isTasks = ['todo', 'super_todo', 'daily_todo'].indexOf(t) >= 0;
        var payload = {
          id: 0, plan_type: t,
          channel_id: chSel.value,
          channel_name: chSel.options[chSel.selectedIndex].text,
          time: sh.querySelector('#bn-time').value || '07:00',
          date: sh.querySelector('#bn-date').value || '',
          start_date: sh.querySelector('#bn-start').value || '',
          end_date: sh.querySelector('#bn-end').value || '',
          week_mode: sh.querySelector('#bn-week').value || 'everyday',
          items: '[]',
          tasks: JSON.stringify([{ name: '', tasks: [] }])
        };

        if (isTasks && t === 'super_todo') {
          var lines = sh.querySelector('#bn-tasks').value.split('\n').map(function (l) { return l.trim(); }).filter(Boolean);
          if (!lines.length) { App.toast('Kamida bitta vazifa yozing'); return; }
          var tasks = [];
          for (var i = 0; i < lines.length; i++) {
            var parts = lines[i].split('|');
            var text = (parts[0] || '').trim();
            var dur = parseInt((parts[1] || '').trim(), 10);
            if (!text || !dur || dur < 1) { App.toast('Format: Vazifa | daqiqa'); return; }
            tasks.push({ text: text, duration: dur, status: 0 });
          }
          payload.tasks = JSON.stringify([{ name: '', tasks: tasks }]);
        } else if (isTasks) {
          var grp = NEW_GROUPS.map(function (g) {
            return {
              name: g.name || '', time: g.time || '',
              tasks: (g.tasks || []).filter(function (tk) { return (tk.text || '').trim(); })
            };
          }).filter(function (g) { return g.tasks.length || g.name; });
          if (!grp.length) { App.toast('Kamida bitta vazifa yozing'); return; }
          var isSingleUnnamed = flatOk(grp);
          payload.tasks = isSingleUnnamed ? JSON.stringify(grp[0].tasks) : JSON.stringify({ groups: grp });
        } else {
          var txt = sh.querySelector('#bn-text').value.trim();
          if (!txt) { App.toast('Matn kiriting'); return; }
          payload.items = JSON.stringify([{ type: 'text', text: txt }]);
        }

        call('save', payload).then(function (res) {
          App.closeSheet(); App.toast('✅ Yaratildi');
          if (res.id) App.go('boost_plan', { id: res.id }); else App.reload();
        }).catch(function (e) { App.toast('⚠️ ' + e.message); });
      };
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* ---------- Kanallar ---------- */
  /* Mavzuli kanal — Sport/Ingliz/Rus bo'limidan "Yuborish" bosilganda shu
     mavzuga tayinlangan kanal avtomatik ishlatiladi (band 25). BITTA KANAL
     bir nechta mavzuga ega bo'lishi mumkin (checkbox), lekin har mavzu
     faqat BITTA kanalga tegishli bo'ladi — boshqa kanalda belgilansa,
     eskisidan avtomatik olib tashlanadi (bot tomonida). */
  /* ⚠️ Yangi mavzu qo'shilsa — bot tomonidagi `webapp.py::CHANNEL_TOPICS`
     ro'yxatiga ham QO'SHISH SHART. U qat'iy whitelist: ro'yxatda yo'q mavzu
     JIMGINA tashlab yuboriladi va kanalga tayinlanmaydi (bir marta shu
     tarzda "dasturlash" saqlanmay qolgan edi). */
  var TOPICS = [
    ['sport', '🏋 Sport'],
    ['english', '🇬🇧 Ingliz tili'],
    ['russian', '🇷🇺 Rus tili'],
    ['dasturlash', '💻 Dasturlash'],
    ['kun', '🗓 Kun rejasi']
  ];
  function topicLabel(t) {
    var f = TOPICS.find(function (x) { return x[0] === (t || ''); });
    return f ? f[1] : (t || '');
  }
  function topicsOf(c) { return (c.topics || '').split(',').filter(Boolean); }

  App.actions.boostChannels = function () {
    call('channels').then(function (j) {
      var chans = j.channels || [];
      var html =
        '<p class="muted" style="font-size:12.5px;margin:0 0 12px">Bot xabarlarni shu kanal/guruhlarga yuboradi. Bot kanalda admin bo\'lishi shart. Mavzu belgilansa — o\'sha mavzudagi bo\'limdan (masalan Sport) "Yuborish" bosilganda shu kanal avtomatik ishlatiladi. Bitta kanalga bir nechta mavzu belgilash mumkin.</p>' +
        (chans.length
          ? chans.map(function (c) {
              var topics = topicsOf(c);
              return '<div class="list-row" style="align-items:flex-start"><span class="li-ic" data-icon="message" data-icon-size="15"></span>' +
                '<div class="li-main"><div class="li-title">' + App.esc(c.channel_name) + '</div>' +
                '<div class="li-sub">' + App.esc(c.channel_id) + '</div>' +
                '<div class="flex" style="gap:5px;flex-wrap:wrap;margin-top:7px">' +
                TOPICS.map(function (t) {
                  var on = topics.indexOf(t[0]) >= 0;
                  return '<button class="chip-btn bo-chtopic' + (on ? ' active' : '') + '" data-id="' + c.id + '" data-t="' + t[0] + '">' + t[1] + '</button>';
                }).join('') + '</div></div>' +
                '<button class="icon-btn ghost bo-chdel" data-id="' + c.id + '" style="width:30px;height:30px">' +
                '<span data-icon="trash" data-icon-size="14"></span></button></div>';
            }).join('')
          : '<p class="muted" style="font-size:13px;margin:2px 1px 10px">Kanal ulanmagan.</p>') +
        '<label class="field" style="margin-top:12px"><span>Yangi kanal (@username yoki ID)</span>' +
        '<input class="input" id="bo-newch" placeholder="@mychannel"></label>' +
        '<button class="btn" id="bo-chadd">Ulash</button>';
      var sh = App.sheet(html, { title: 'Kanallar' });
      App.icons(sh);

      sh.querySelectorAll('.bo-chdel').forEach(function (b) {
        b.onclick = function () {
          call('delete_channel', { id: b.getAttribute('data-id') }).then(function () {
            App.closeSheet(); App.toast('O\'chirildi'); App.reload();
          }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        };
      });
      sh.querySelectorAll('.bo-chtopic').forEach(function (btn) {
        btn.onclick = function () {
          var chId = btn.getAttribute('data-id'), t = btn.getAttribute('data-t');
          var chan = chans.find(function (c) { return String(c.id) === String(chId); });
          if (!chan) return;
          var cur = topicsOf(chan);
          var i = cur.indexOf(t);
          if (i >= 0) cur.splice(i, 1); else cur.push(t);
          chan.topics = cur.join(',');
          btn.classList.toggle('active');
          // Boshqa kanaldagi shu mavzu chip'ini ham darhol yangilaymiz (bir mavzu — bitta kanal).
          if (i < 0) {
            sh.querySelectorAll('.bo-chtopic[data-t="' + t + '"]').forEach(function (other) {
              if (other !== btn) other.classList.remove('active');
            });
            chans.forEach(function (c) {
              if (c.id !== chan.id) c.topics = topicsOf(c).filter(function (x) { return x !== t; }).join(',');
            });
          }
          call('set_channel_topics', { id: chId, topics: chan.topics }).then(function () {
            App.toast('✅ Saqlandi');
          }).catch(function (e) { App.toast('⚠️ ' + e.message); App.reload(); });
        };
      });
      sh.querySelector('#bo-chadd').onclick = function () {
        var v = sh.querySelector('#bo-newch').value.trim();
        if (!v) return App.toast('Kanal nomini kiriting');
        call('add_channel', { channel: v }).then(function () {
          App.closeSheet(); App.toast('✅ Ulandi — endi mavzu(lar)ni belgilang'); App.reload();
        }).catch(function (e) { App.toast('⚠️ ' + e.message); });
      };
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* =========================================================
     VAZIFA TANLAGICH — "Ingliz bo'limi tanlanib ichiga kiriladi, ichma-ich
     papkalar bo'lsa ularga ham kirilib eng oxiridagi .md faylgacha boradi va
     tanlanadi, o'sha vazifa bo'ladi" (foydalanuvchi so'rovi).

     Daraxt:
       Ingliz tili / Rus tili → [Grammar, Lug'at, Reading, Listening, ...]
                                  → (ichma-ich papkalar) → .md fayllar ☑
       Sport                  → kategoriyalar → mashqlar ☑
     Tanlanganlar reja vazifasiga aylanadi. Nom AYNAN manbadagidek olinadi —
     shunda Telegramda belgilanganda statistika to'g'ri bo'limga tushadi.
     ========================================================= */
  var PK = null;   // {stack:[{title, load}], sel:{}, onDone}

  function pkOpen(onDone) {
    PK = { stack: [], sel: {}, onDone: onDone };
    App.sheet('<div id="pk-body"><div class="load-wrap"><div class="spinner"></div></div></div>', { title: 'Bo\'limdan tanlash' });
    pkPush({ title: 'Bo\'limlar', load: pkRoot });
  }
  function pkPush(level) { PK.stack.push(level); pkRender(); }
  App.actions.pkBack = function () {
    if (!PK) return;
    if (PK.stack.length <= 1) { App.closeSheet(); PK = null; return; }
    PK.stack.pop(); pkRender();
  };

  function pkRender() {
    var body = App.el('pk-body'); if (!PK || !body) return;
    var lvl = PK.stack[PK.stack.length - 1];
    body.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
    Promise.resolve(lvl.load()).then(function (rows) {
      var b = App.el('pk-body'); if (!b) return;
      var crumb = PK.stack.map(function (s) { return s.title; }).join(' / ');
      var html = '<div class="lib-crumb" style="margin-bottom:10px">' +
        (PK.stack.length > 1 ? '<button class="lib-cr" data-act="pkBack">← Ortga</button><span>/</span>' : '') +
        '<b>' + App.esc(crumb) + '</b></div>';

      if (!rows.length) {
        html += App.empty({ icon: 'list', title: 'Bo\'sh', text: 'Bu yerda hali material yo\'q.' });
      } else {
        html += rows.map(function (r) {
          if (r.type === 'branch') {
            return '<button class="pk-row" data-act="pkInto" data-arg=\'' + App.arg({ k: r.key }) + '\'>' +
              '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)">' +
              '<span data-icon="' + (r.ic || 'archive') + '" data-icon-size="14"></span></span>' +
              '<span class="pk-main"><b>' + App.esc(r.name) + '</b>' +
              (r.sub ? '<span>' + App.esc(r.sub) + '</span>' : '') + '</span>' +
              '<span class="li-chev" data-icon="arrowLeft" data-icon-size="15" style="transform:rotate(180deg)"></span></button>';
          }
          var on = !!PK.sel[r.name];
          return '<button class="pk-row' + (on ? ' on' : '') + '" data-act="pkPick" data-arg=\'' +
            App.arg({ n: r.name }) + '\'><span class="pk-box">' + (on ? '✓' : '') + '</span>' +
            '<span class="pk-main"><b>' + App.esc(r.name) + '</b>' +
            (r.sub ? '<span>' + App.esc(r.sub) + '</span>' : '') + '</span></button>';
        }).join('');
      }

      var n = Object.keys(PK.sel).length;
      html += '<div class="pk-bar"><button class="btn" data-act="pkDone"' + (n ? '' : ' disabled') + '>' +
        (n ? n + ' ta vazifa qo\'shish' : 'Vazifa tanlang') + '</button></div>';
      b.innerHTML = html;
      App.icons(b);
      // Keyingi darajaga o'tish uchun kalitlarni saqlaymiz
      PK.rows = {};
      rows.forEach(function (r) { if (r.type === 'branch') PK.rows[r.key] = r; });
    }).catch(function (e) {
      var b = App.el('pk-body');
      if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  App.actions.pkInto = function (a) {
    var r = PK && PK.rows && PK.rows[a.k];
    if (r) pkPush({ title: r.name, load: r.open, topic: r.topic || '' });
  };
  App.actions.pkPick = function (a) {
    if (!PK) return;
    if (PK.sel[a.n]) delete PK.sel[a.n];
    // Qaysi ILDIZ bo'limdan tanlangani eslab qolinadi — vazifa o'sha mavzu
    // nomidagi bo'limga tushadi (Sport → "🏋 Sport", Ingliz → "🇬🇧 Ingliz tili").
    else PK.sel[a.n] = (PK.stack[1] && PK.stack[1].topic) || '';
    pkRender();
  };
  App.actions.pkDone = function () {
    if (!PK) return;
    var picked = Object.keys(PK.sel).map(function (n) { return { name: n, topic: PK.sel[n] }; });
    var cb = PK.onDone;
    PK = null;
    App.closeSheet();
    if (picked.length && cb) cb(picked);
  };

  /* --- Daraxt darajalari --- */
  function pkRoot() {
    return [
      { type: 'branch', key: 'english', topic: 'english', name: '🇬🇧 Ingliz tili', ic: 'book', open: function () { return pkLang('english'); } },
      { type: 'branch', key: 'russian', topic: 'russian', name: '🇷🇺 Rus tili', ic: 'book', open: function () { return pkLang('russian'); } },
      { type: 'branch', key: 'sport', topic: 'sport', name: '🏋 Sport', ic: 'activity', open: pkSportCats }
    ];
  }

  /* Til ichidagi BARCHA bo'limlar — Grammar/Lug'at (mavjud modullar) va
     Materiallar bo'limlari (library.js reyestridan). */
  function pkLang(lang) {
    var out = [
      { type: 'branch', key: 'gram', name: lang === 'english' ? 'Grammar' : 'Grammatika', ic: 'edit',
        open: function () { return pkTopics(lang, ''); } },
      { type: 'branch', key: 'voc', name: lang === 'english' ? 'Vocabulary' : 'Lug\'at', ic: 'list',
        open: function () { return pkDict(lang); } }
    ];
    var S = (window.Library && Library.SECTIONS) || {};
    Object.keys(S).forEach(function (k) {
      if (S[k].parent !== lang) return;
      out.push({ type: 'branch', key: k, name: S[k].n, ic: S[k].ic, open: function () { return pkTopics(k, ''); } });
    });
    return out;
  }

  /* `language_topics` ustidagi umumiy papka brauzeri — Grammar ham,
     Materiallar bo'limlari ham shu jadvalda (Grammar'da papka bir daraja,
     Materiallarda ichma-ich — ikkalasi ham `folder` yo'li bilan ishlaydi). */
  function pkTopics(sec, path) {
    return App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(sec) }).then(function (j) {
      var mark = (window.Library && Library.FOLDER_MARK) || '__folder__';
      var topics = (j.topics || []);
      var v = (window.Library && Library.viewOf)
        ? Library.viewOf(topics, path)
        : { folders: [], files: topics.filter(function (t) { return (t.folder || '') === path && t.name !== mark; }) };
      var out = v.folders.map(function (f) {
        var sub = [];
        if (f.files) sub.push(f.files + ' ta fayl');
        if (f.subs) sub.push(f.subs + ' ta ichkarida');
        return {
          type: 'branch', key: 'f:' + f.n, name: f.n, ic: 'archive', sub: sub.join(' · '),
          open: function () { return pkTopics(sec, path ? path + '/' + f.n : f.n); }
        };
      });
      v.files.forEach(function (t) {
        if (t.name === mark) return;
        out.push({ type: 'leaf', name: t.name, sub: t.has_content === false ? 'matn yo\'q' : '' });
      });
      return out;
    });
  }

  /* Lug'at kategoriyalari (vocab.js bilan bir xil manba — nomlar aynan mos) */
  function pkDict(lang) {
    return App.call('get_dict_data', null, { query: 'lang=' + lang }).then(function (j) {
      var count = {};
      (j.items || []).forEach(function (it) { count[it.category] = (count[it.category] || 0) + 1; });
      return (j.order || []).map(function (c) {
        return { type: 'leaf', name: c, sub: (count[c] || 0) + ' ta so\'z' };
      });
    });
  }

  /* Sport: kategoriyalar → mashqlar (nomi Sport bo'limidagidek) —
     "Materiallardan tez qo'shish" daraxtida ishlatiladi (pkRoot → pkSportCats). */
  function pkSportCats() {
    if (!window.SportBridge) return [];
    return SportBridge.ensureLoaded().then(function () {
      var all = SportBridge.allExercises() || [];
      var order = [], byCat = {};
      all.forEach(function (e) {
        if (!byCat[e.cat]) { byCat[e.cat] = { name: e.catName, items: [] }; order.push(e.cat); }
        byCat[e.cat].items.push(e);
      });
      return order.map(function (c) {
        return {
          type: 'branch', key: 'c:' + c, name: byCat[c].name, ic: 'activity',
          sub: byCat[c].items.length + ' ta mashq',
          open: function () {
            return byCat[c].items.map(function (e) {
              var timePrefix = '';
              if (e.start_time && e.end_time) timePrefix = e.start_time + ' - ' + e.end_time + ' | ';
              else if (e.start_time) timePrefix = e.start_time + ' | ';
              return { type: 'leaf', name: timePrefix + e.name };
            });
          }
        };
      });
    });
  }

  /* =========================================================
     Kun hisobi ko'prigi — Boostday rejalari "butun kun vaqt chizig'i"da
     o'z vaqtida ko'rinishi uchun (kun.js chaqiradi). Reja qaysi kunga
     tegishli ekani bot mantig'i bilan bir xil aniqlanadi:
       - daily_todo / daily_plan — har kuni (week_mode: everyday/odd/even,
         odd = Du/Chor/Juma, even = Sesh/Pay/Shan, yakshanba hech qachon —
         scheduler.py::daily_mode_should_send bilan aynan bir xil)
       - todo / super_todo / reminder — faqat o'z sanasida
       - challenge — start_date..end_date oralig'ida
     ========================================================= */
  function weekModeMatches(mode, dow) {
    mode = (mode || 'everyday').toLowerCase();
    if (mode !== 'odd' && mode !== 'even') return true;
    var n = dow === 0 ? 7 : dow;          // 1=Dushanba ... 7=Yakshanba
    if (n === 7) return false;
    var isOdd = (n % 2) === 1;
    return mode === 'odd' ? isOdd : !isOdd;
  }

  function planTaskList(p) {
    var out = [];
    planGroupList(p).forEach(function (g) {
      g.tasks.forEach(function (t) { out.push(t); });
    });
    return out;
  }

  /* Rejani BO'LIMLAR ko'rinishida qaytaradi — har bo'lim o'z VAQTI bilan.
     Vaqt endi bo'lim darajasida (`task_groups[].time`), vazifa matnida emas:
     amalda bitta bo'limdagi ishlar bitta oraliqda bajariladi. Bo'limda vaqt
     bo'lmasa rejaning umumiy `time` i olinadi.
     Vazifa `index` lari BUTUN reja bo'yicha uzluksiz — `toggle_task` shu
     indeksni kutadi (bo'lim chegarasi indekslashga ta'sir qilmaydi). */
  function planGroupList(p) {
    var groups = (p.task_groups && p.task_groups.length)
      ? p.task_groups
      : (Array.isArray(p.tasks) ? [{ name: '', time: '', tasks: p.tasks }] : []);
    var out = [], idx = 0;
    groups.forEach(function (g) {
      var tasks = [];
      (g.tasks || []).forEach(function (t) {
        if ((t.text || '').trim()) {
          tasks.push({ index: idx, text: t.text, status: +t.status || 0, group: g.name || '' });
        }
        idx++;
      });
      if (tasks.length) {
        out.push({ name: g.name || '', time: (g.time || '').trim(), tasks: tasks });
      }
    });
    return out;
  }

  /* "08:00 - 09:30" yoki "08:00" -> {start,end}. Mos kelmasa null. */
  function splitTimeRange(s) {
    var m = String(s || '').trim().match(/^(\d{1,2}:\d{2})(?:\s*[-–—]\s*(\d{1,2}:\d{2}))?$/);
    if (!m) return null;
    return { start: m[1], end: m[2] || '' };
  }

  window.BoostDay = {
    /* B.data keshini ishlatadi; `force` bilan serverdan qayta so'raladi. */
    ensureLoaded: function (force) {
      if (!force && B.data) return Promise.resolve(B.data);
      return call('list').then(function (j) { B.data = j; return j; })
        .catch(function () { return (B.data = B.data || {}); });
    },
    /* `dateStr` — 'YYYY-MM-DD', `dow` — 0(Yak)..6(Shan). */
    dayItems: function (dateStr, dow) {
      var d = B.data || {}, out = [];
      function add(p) {
        var tasks = planTaskList(p);
        var done = tasks.filter(function (t) { return t.status === 1; }).length;
        out.push({
          kind: 'boost', planId: p.id, planType: p.plan_type,
          time: p.time || '', title: (p.preview || p.channel_name || tinfo(p.plan_type).n),
          channelName: p.channel_name || '', typeName: tinfo(p.plan_type).n, emoji: tinfo(p.plan_type).e, color: tinfo(p.plan_type).c,
          tasks: tasks, total: tasks.length, done: done,
          /* Bo'limlar o'z vaqti bilan — Kun hisobi vaqt chizig'i shulardan
             foydalanadi (har bo'lim alohida satr bo'lib chiqadi). */
          groups: planGroupList(p),
          preview: p.preview || ''
        });
      }
      (d.daily_routines || []).forEach(function (p) {
        if (weekModeMatches(p.week_mode, dow)) add(p);
      });
      (d.todos || []).forEach(function (p) { if (p.date === dateStr) add(p); });
      (d.plans || []).forEach(function (p) {
        if (p.plan_type === 'challenge') {
          if (p.start_date && dateStr >= p.start_date && (!p.end_date || dateStr <= p.end_date)) add(p);
        } else if (weekModeMatches(p.week_mode, dow)) add(p);
      });
      (d.reminders || []).forEach(function (p) { if (p.date === dateStr) add(p); });
      return out;
    },
    toggle: function (planId, index) {
      return call('toggle_task', { id: planId, index: index }).then(function () {
        return call('list').then(function (j) { B.data = j; return j; });
      });
    },

    /* Nomi bo'yicha BUGUNGI vazifani topadi (Sport bilan bog'lash uchun).
       Taqqoslash `App.taskKey` orqali — Boostday matnidagi vaqt prefiksi
       hisobga olinmaydi. */
    findTaskByName: function (text) {
      var key = App.taskKey(text);
      if (!key) return null;
      var d = B.data || {}, today = todayKeyStr(), found = null;
      function scan(list) {
        (list || []).forEach(function (p) {
          if (found) return;
          var groups = p.task_groups && p.task_groups.length
            ? p.task_groups : (Array.isArray(p.tasks) ? [{ tasks: p.tasks }] : []);
          var idx = 0;
          groups.forEach(function (g) {
            (g.tasks || []).forEach(function (t) {
              if (!found && App.taskKey(t.text) === key) {
                found = { planId: p.id, index: idx, status: +t.status || 0 };
              }
              idx++;
            });
          });
        });
      }
      scan(d.daily_routines);
      scan((d.todos || []).filter(function (p) { return p.date === today; }));
      return found;
    },

    /* Bugungi ishlarni GURUHLAR bo'yicha yig'adi (bosh sahifadagi vidjet uchun).
       Guruh — botda kiritilgan bo'lim nomi (`task_groups[].name`). Rejada
       bo'lim ochilmagan bo'lsa, rejaning o'zi bitta guruh sifatida olinadi
       (nomi: preview yoki kanal nomi yoki reja turi).
       Qaytaradi: [{ name, total, done, color }]. */
    dayGroups: function (dateStr, dow) {
      var d = B.data || {}, map = {}, order = [];
      /* `items` — kompyuterda bo'sh joyni to'ldirib, vazifa nomlarini
         ko'rsatish uchun (home.js kengaytirilgan vidjeti). */
      function add(gname, color, done, text) {
        if (!map[gname]) { map[gname] = { name: gname, total: 0, done: 0, color: color, items: [] }; order.push(gname); }
        map[gname].total++;
        if (done) map[gname].done++;
        map[gname].items.push({ text: text, done: done });
      }
      function scan(p) {
        var info = tinfo(p.plan_type);
        var fallback = (p.preview || p.channel_name || info.n || 'Reja').trim();
        var groups = (p.task_groups && p.task_groups.length)
          ? p.task_groups
          : (Array.isArray(p.tasks) ? [{ name: '', tasks: p.tasks }] : []);
        groups.forEach(function (g) {
          var gname = (g.name || '').trim() || fallback;
          (g.tasks || []).forEach(function (t) {
            var txt = (t.text || '').trim();
            if (!txt) return;
            add(gname, info.c, +t.status === 1, txt);
          });
        });
      }
      (d.daily_routines || []).forEach(function (p) { if (weekModeMatches(p.week_mode, dow)) scan(p); });
      (d.todos || []).forEach(function (p) { if (p.date === dateStr) scan(p); });
      return order.map(function (k) { return map[k]; });
    },

    /* Vazifani MA'LUM holatga keltiradi (Sport tomonidan chaqiriladi).
       Allaqachon shu holatda bo'lsa hech narsa qilmaydi — `toggle_task`
       almashtiruvchi bo'lgani uchun ikki tomon toggle qilsa holat buzilardi. */
    setTaskDone: function (text, want) {
      /* MUHIM: avval ma'lumot YUKLANGANIGA ishonch hosil qilamiz.
         `findTaskByName` `B.data` ga tayanadi; ilova to'g'ridan-to'g'ri
         Sport bo'limida ochilgan bo'lsa (router oxirgi manzilni tiklaydi)
         Boostday hech qachon yuklanmagan bo'ladi va qidiruv JIMGINA
         hech nima topmasdi — natijada Sportda belgilangan mashq
         Boostdayda belgilanmay qolardi. */
      return window.BoostDay.ensureLoaded().then(function () {
        var t = window.BoostDay.findTaskByName(text);
        if (!t) return false;
        if ((t.status === 1) === !!want) return false;
        return window.BoostDay.toggle(t.planId, t.index)
          .then(function () { return true; })
          .catch(function () { return false; });
      }).catch(function () { return false; });
    }
  };

  /* Sport (yoki kelajakda boshqa) bo'limdan mashq/matn yuborish uchun tashqi
     modullar chaqiradigan umumiy funksiya. `topic` bo'yicha tayinlangan kanalni
     topadi, mavjud faol shu nomdagi daily_todo rejaga qo'shadi yoki yangi
     yaratadi. `items` — [{text}] (allaqachon bajarilganlarini frontend o'zi
     filtrlaydi). Va'da (Promise) qaytaradi: {ok, message}. */
  window.BoostPush = {
    /* `opts.date` (YYYY-MM-DD) berilsa — BITTA MARTALIK "TO-DO" sifatida
       aynan o'sha kunga yuboriladi (plan_type='todo'). Berilmasa — avvalgidek
       har kuni takrorlanadigan "daily_todo" (Sport shu holatda ishlaydi). */
    pushTasks: function (topic, planTitle, items, opts) {
      opts = opts || {};
      var date = opts.date || '';
      var time = opts.time || '08:00';
      var planType = date ? 'todo' : 'daily_todo';
      return call('channels').then(function (j) {
        var chans = j.channels || [];
        var chan = chans.find(function (c) { return topicsOf(c).indexOf(topic) >= 0; });
        if (!chan) {
          return Promise.reject(new Error(topicLabel(topic) + ' uchun kanal tayinlanmagan. Avval Boostday > Kanallar\'da tayinlang.'));
        }
        return call('list').then(function (list) {
          var pool = date
            ? (list.todos || []).filter(function (p) { return p.plan_type === 'todo' && p.date === date; })
            : (list.daily_routines || []);
          var existing = pool.find(function (p) {
            return p.channel_id === chan.channel_id;
          });
          var groups, planId;
          if (existing) {
            groups = existing.task_groups && existing.task_groups.length ? existing.task_groups : [{ name: '', tasks: existing.tasks || [] }];
            planId = existing.id;
          } else {
            groups = [{ name: '', tasks: [] }];
            planId = 0;
          }
          // Kanal bir nechta mavzuga xizmat qilishi mumkin (masalan Sport+Rus
          // bitta rejada) — shuning uchun har doim MAVZU NOMIDAGI bo'limga
          // yoziladi, birinchi bo'limga emas (aks holda ikkalasi aralashib
          // ketardi). Bunday bo'lim hali yo'q bo'lsa — yaratiladi.
          var wantName = TOPIC_GROUP_NAME[topic] || '';
          var g = wantName ? groups.find(function (x) { return (x.name || '').trim() === wantName; }) : groups[0];
          if (!g) {
            g = { name: wantName, tasks: [] };
            // Bo'sh, nomsiz "boshlang'ich" bo'limni band qilib turmasin —
            // shu holatda o'sha bo'shini almashtiramiz, aks holda oxiriga qo'shamiz.
            var emptyDefault = groups.findIndex(function (x) { return !(x.name || '').trim() && !(x.tasks || []).length; });
            if (emptyDefault >= 0) groups[emptyDefault] = g; else groups.push(g);
          }
          g.name = g.name || '';
          var existingTexts = {};
          (g.tasks || []).forEach(function (t) { existingTexts[t.text] = true; });
          items.forEach(function (it) {
            if (!existingTexts[it.text]) { g.tasks.push({ text: it.text, status: 0 }); existingTexts[it.text] = true; }
          });
          var isSingleUnnamed = flatOk(groups);
          var tasksPayload = isSingleUnnamed ? JSON.stringify(groups[0].tasks) : JSON.stringify({ groups: groups });
          return call('save', {
            id: planId, plan_type: planType, channel_id: chan.channel_id, channel_name: chan.channel_name,
            time: (existing && existing.time) || time, date: date, start_date: '', end_date: '',
            week_mode: (existing && existing.week_mode) || 'everyday',
            items: (existing && existing.items) ? (typeof existing.items === 'string' ? existing.items : JSON.stringify(existing.items)) : JSON.stringify([{ type: 'text', text: planTitle }]),
            tasks: tasksPayload
          });
        });
      });
    },

    /* Bitta KUNNING to'liq rejasini (bo'limlar + har bo'lim vaqti bilan)
       o'sha sanaga `todo` reja qilib yozadi. Kun hisobidagi .md import shuni
       chaqiradi — haftalik reja 7 marta (har kun uchun) chaqiriladi.

       `mode`:
         'replace' — o'sha kundagi mavjud reja BUTUNLAY almashtiriladi
         'merge'   — mavjud bo'limlarga qo'shiladi (nomi bir xil bo'lim
                     topilsa uning ichiga, aks holda yangi bo'lim)
       Vazifa holati (`status`) merge'da SAQLANADI: allaqachon belgilangan
       ish qayta import qilinganda "bajarilmagan"ga qaytmasin. */
    pushDayPlan: function (topic, dateStr, planTitle, groups, opts) {
      opts = opts || {};
      var mode = opts.mode === 'merge' ? 'merge' : 'replace';
      return call('channels').then(function (j) {
        var chans = j.channels || [];
        var chan = chans.find(function (c) { return topicsOf(c).indexOf(topic) >= 0; });
        /* Mavzu hech qaysi kanalga tayinlanmagan bo'lsa-yu, kanal BITTA
           bo'lsa — o'shanga yozamiz. Tanlash noaniqligi yo'q, foydalanuvchini
           faqat mavzu tayinlash uchun to'xtatib qo'yish ortiqcha. */
        if (!chan && chans.length === 1) chan = chans[0];
        if (!chan) {
          return Promise.reject(new Error(topicLabel(topic) + ' uchun kanal tayinlanmagan. Avval Boostday > Kanallar\'da tayinlang.'));
        }
        return call('list').then(function (list) {
          var existing = (list.todos || []).find(function (p) {
            return p.plan_type === 'todo' && p.date === dateStr && p.channel_id === chan.channel_id;
          });

          var finalGroups;
          if (mode === 'merge' && existing) {
            finalGroups = (existing.task_groups && existing.task_groups.length)
              ? JSON.parse(JSON.stringify(existing.task_groups))
              : [{ name: '', time: '', cat: '', tasks: (existing.tasks || []).slice() }];
            groups.forEach(function (ng) {
              var name = (ng.name || '').trim();
              var g = finalGroups.find(function (x) { return (x.name || '').trim() === name; });
              if (!g) {
                g = { name: name, time: ng.time || '', cat: ng.cat || '', tasks: [] };
                var emptyIdx = finalGroups.findIndex(function (x) {
                  return !(x.name || '').trim() && !(x.time || '').trim() && !(x.tasks || []).length;
                });
                if (emptyIdx >= 0) finalGroups[emptyIdx] = g; else finalGroups.push(g);
              }
              if (ng.time) g.time = ng.time;
              if (ng.cat) g.cat = ng.cat;
              var have = {};
              (g.tasks || []).forEach(function (t) { have[App.taskKey(t.text)] = true; });
              (ng.tasks || []).forEach(function (t) {
                var k = App.taskKey(t.text);
                if (!k || have[k]) return;
                g.tasks.push({ text: t.text, status: 0 });
                have[k] = true;
              });
            });
          } else {
            /* Almashtirishda ham BUGUNGI belgilangan ishlar yo'qolmasin:
               eski rejadagi bir xil nomli vazifaning holati ko'chiriladi. */
            var prevStatus = {};
            if (existing) {
              var prev = (existing.task_groups && existing.task_groups.length)
                ? existing.task_groups
                : [{ tasks: existing.tasks || [] }];
              prev.forEach(function (g) {
                (g.tasks || []).forEach(function (t) {
                  if (+t.status === 1) prevStatus[App.taskKey(t.text)] = 1;
                });
              });
            }
            finalGroups = groups.map(function (g) {
              return {
                name: (g.name || '').trim(),
                time: (g.time || '').trim(),
                cat: (g.cat || '').trim(),      // turkum (rang) — Kun hisobi uchun
                tasks: (g.tasks || []).map(function (t) {
                  return { text: t.text, status: prevStatus[App.taskKey(t.text)] ? 1 : 0 };
                })
              };
            });
          }
          if (!finalGroups.length) finalGroups = [{ name: '', time: '', tasks: [] }];

          /* Reja vaqti — eng erta bo'lim vaqti (Boostday xabari shu vaqtda
             yuboriladi). Bo'lim vaqtlari bo'lmasa eskisi/standart qoladi. */
          var starts = finalGroups
            .map(function (g) { var r = splitTimeRange(g.time); return r ? r.start : ''; })
            .filter(Boolean).sort();
          var planTime = starts[0] || (existing && existing.time) || opts.time || '08:00';

          var isSingleUnnamed = flatOk(finalGroups);
          return call('save', {
            id: existing ? existing.id : 0,
            plan_type: 'todo', channel_id: chan.channel_id, channel_name: chan.channel_name,
            time: planTime, date: dateStr, start_date: '', end_date: '', week_mode: 'everyday',
            items: JSON.stringify([{ type: 'text', text: planTitle }]),
            tasks: isSingleUnnamed ? JSON.stringify(finalGroups[0].tasks) : JSON.stringify({ groups: finalGroups })
          });
        });
      });
    }
  };
})();
