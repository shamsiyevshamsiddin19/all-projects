/* Sport — mashqlar (kategoriya bo'yicha), og'irlik/set/takror, media (rasm/video/YouTube link) */
(function () {
  'use strict';

  /* ⚠️ `backend_py/app/handlers/sport.py::CATEGORIES` bilan BIR XIL bo'lishi
     shart — u yerda yo'q kategoriyadagi mashqlar saytga yetib kelmaydi. */
  var CATS = [
    { id: 'turnik', n: 'Turnik', c: 'var(--accent)', ic: 'spTurnik' },
    { id: 'brus', n: 'Brus', c: 'var(--purple)', ic: 'spBrus' },
    { id: 'ajimaniya', n: 'Ajimaniya', c: 'var(--teal)', ic: 'spPush' },
    { id: 'full', n: 'Full Body', c: 'var(--coral)', ic: 'spBody' },
    { id: 'grud', n: 'Ko\'krak', c: 'var(--warn)', ic: 'spChest' },
    { id: 'bitseps', n: 'Bitseps', c: 'var(--success)', ic: 'spBiceps' },
    { id: 'triseps', n: 'Triseps', c: 'var(--danger)', ic: 'spTriceps' },
    { id: 'orqa', n: 'Orqa', c: 'var(--accent)', ic: 'spBack' },
    { id: 'yelka', n: 'Yelka', c: 'var(--purple)', ic: 'spShoulder' },
    { id: 'oyoq', n: 'Oyoq', c: 'var(--teal)', ic: 'spLegs' },
    { id: 'press', n: 'Press / Qorin', c: 'var(--purple)', ic: 'spPress' },
    { id: 'kardio', n: 'Kardio', c: 'var(--coral)', ic: 'spCardio' },
    { id: 'armwresling', n: 'Armrestling', c: 'var(--warn)', ic: 'spArm' },
    { id: 'futbol', n: 'Futbol', c: 'var(--success)', ic: 'spFutbol' },
    { id: 'voleybol', n: 'Voleybol', c: 'var(--accent)', ic: 'spVoleybol' },
    { id: 'badminton', n: 'Badminton', c: 'var(--teal)', ic: 'spBadminton' },
    { id: 'basketbol', n: 'Basketbol', c: 'var(--coral)', ic: 'spBasketbol' }
  ];
  /* Jamoaviy/o'yin sportlari — bu yerda "og'irlik" tushunchasi yo'q,
     standart o'lchov vaqt yoki masofa bo'ladi. */
  var TEAM_CATS = ['futbol', 'voleybol', 'badminton', 'basketbol'];
  function isTeamCat(id) { return TEAM_CATS.indexOf(id) >= 0; }

  function catInfo(id) {
    return CATS.find(function (c) { return c.id === id; }) || { id: id, n: id, c: 'var(--hint)', ic: 'trophy' };
  }

  /* Kategoriya rasmi bor-yo'qligi. Rasm qo'shilgani sari shu ro'yxatga
     id qo'shiladi — bo'lmaganlari eski rangli belgi bilan ko'rinaveradi. */
  var CAT_IMG = ['turnik', 'brus', 'ajimaniya', 'full', 'grud', 'bitseps',
    'triseps', 'orqa', 'yelka', 'oyoq', 'press', 'kardio', 'armwresling',
    'futbol', 'voleybol', 'badminton', 'basketbol'];
  /* Versiya — rasm almashtirilganda brauzer keshi eskisini ushlab qolmasin.
     Rasmlarni yangilaganda shu qiymatni ham oshirish kerak.
     20260806: `press` qo'shildi; jamoaviy sport rasmlari (futbol/voleybol/
     badminton/basketbol) 1024px va 190-423 KB edi — boshqalari kabi 440px
     ga keltirildi, bo'lim rasmlari jami 1186 KB dan 256 KB ga tushdi. */
  var IMG_V = '20260806a';
  function catImg(id) {
    return CAT_IMG.indexOf(id) === -1 ? '' : 'assets/img/sport/' + id + '.webp?v=' + IMG_V;
  }

  /* Mashq belgisi: rasmi bo'lsa — o'sha rasm, bo'lmasa kategoriya belgisi */
  function exerciseThumb(e, info) {
    var img = (e.media || []).find(function (m) { return /\.(jpg|jpeg|png|gif|webp|avif)$/i.test(m); });
    if (img) {
      var src = /^https?:\/\//i.test(img) ? img : '/' + String(img).replace(/^\/+/, '');
      return '<img class="ex-thumb" src="' + App.esc(src) + '" alt="" loading="lazy">';
    }
    return '<span class="li-ic" style="background:color-mix(in srgb,' + info.c + ' 16%, transparent);color:' + info.c +
      '"><span data-icon="' + info.ic + '" data-icon-size="16"></span></span>';
  }

  var S = { data: null, boostDone: [] };
  /* ILOVAGA QAYTGANDA ma'lumot eskirgan deb belgilanadi.
     Odatiy holat: foydalanuvchi mashqni TELEGRAMDA belgilaydi va ilovaga
     qaytadi. Kesh butun sessiya davomida saqlangani uchun "bajarildi"
     belgisi ko'rinmay qolardi — endi qaytishda qaytadan olinadi. */
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) return;
    S.data = null;
    var v = App.currentView && App.currentView();
    if (!v || ['sport', 'sport_cat', 'sport_exercise', 'sport_mine'].indexOf(v) < 0) return;
    if (document.querySelector('.sheet.show')) return;   // oyna ochiq — bezovta qilmaymiz
    App.reload();
  });

  function loadAll(force) {
    if (S.data && !force) return Promise.resolve(S.data);
    return App.call('sport_get_all').then(function (j) {
      S.data = j.data || {};
      S.boostDone = j.today_boost_done || [];   // Telegram/Boostday orqali bugun bajarilgan nomlar (band 25)
      return S.data;
    });
  }
  function topbar(title, backView, backParams, rightHtml) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: backView, p: backParams || {} }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(title) + '</h1>' + (rightHtml || '') + '</div>';
  }

  /* =========================================================
     VIEW: sport — kategoriyalar
     ========================================================= */
  App.view('sport', {
    nav: 'sport',
    render: function (page) {
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<div style="display:flex;align-items:center;gap:9px;flex:1;min-width:0">' +
        '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:28px;height:28px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
        '<h1>Sport</h1></div></div>' +
        '<div id="sport-mine-entry"></div>' +
        '<div id="sport-cats"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      loadAll().then(function (data) {
        /* "Mening mashqlarim" — eng tepada, kundalik ishlatiladigan qisqa ro'yxat */
        var me = App.el('sport-mine-entry');
        if (me) {
          var mine = mineList();
          var doneN = mine.filter(function (x) { return loggedToday(x.id); }).length;
          me.innerHTML = '<button class="list-row" data-act="go" data-arg=\'' +
            App.arg({ v: 'sport_mine' }) + '\' style="margin-bottom:14px">' +
            '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="check" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">Mening mashqlarim</div>' +
            '<div class="li-sub">' + (mine.length
              ? doneN + ' / ' + mine.length + ' bugun bajarildi'
              : 'O\'zingiz bajaradigan mashqlarni tanlang') + '</div></div>' +
            '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
          App.icons(me);
        }

        var box = App.el('sport-cats'); if (!box) return;
        box.className = 'sp-grid';
        /* FAOL kategoriyalar tepada, to'xtatilganlari eng pastda.
           O'zaro tartib o'zgarmaydi (barqaror saralash) — ya'ni faollar
           ham, to'xtatilganlar ham `CATS` dagi asl ketma-ketligini
           saqlaydi, faqat ikki guruhga ajraladi. */
        var ordered = CATS.map(function (c, i) { return { c: c, i: i }; })
          .sort(function (a, b) {
            var da = isCatDisabled(a.c.id) ? 1 : 0, db = isCatDisabled(b.c.id) ? 1 : 0;
            return da !== db ? da - db : a.i - b.i;
          })
          .map(function (x) { return x.c; });

        /* WORKOUT — turnik mahorati yo'l xaritasi (workout.js). Bu oddiy
           kategoriya emas (bazada mashqlari yo'q), shuning uchun ro'yxatga
           qo'lda, eng birinchi plitka sifatida qo'shiladi. */
        var wp = (window.Workout && Workout.progress) ? Workout.progress() : null;
        var wkTile = '<button class="sp-tile" data-act="go" data-arg=\'' +
          App.arg({ v: 'workout' }) + '\'>' +
          '<img src="assets/img/sport/workout.webp?v=' + IMG_V + '" alt="" loading="lazy">' +
          '<span class="sp-bar" style="background:var(--accent)"></span>' +
          '<span class="sp-ov"><span class="sp-n">Workout</span>' +
          '<span class="sp-c">' + (wp ? wp.done + ' / ' + wp.total + ' ko\'nikma' : 'Bosqichma-bosqich') +
          '</span></span></button>';

        box.innerHTML = wkTile + ordered.map(function (c) {
          var n = (data[c.id] || []).length;
          var img = catImg(c.id);
          var disabled = isCatDisabled(c.id);
          var inner = img
            ? '<img src="' + img + '" alt="" loading="lazy"' + (disabled ? ' style="filter:grayscale(1) opacity(0.5)"' : '') + '>'
            : '<span class="sp-fb" style="background:color-mix(in srgb,' + c.c + ' ' + (disabled ? '5' : '14') + '%, transparent);color:' + (disabled ? 'var(--hint)' : c.c) +
              '"><span data-icon="' + c.ic + '" data-icon-size="30"></span></span>';
          return '<button class="sp-tile" data-act="go" data-arg=\'' + App.arg({ v: 'sport_cat', p: { cat: c.id } }) + '\'>' +
            inner +
            '<span class="sp-bar" style="background:' + (disabled ? 'var(--border)' : c.c) + '"></span>' +
            '<span class="sp-ov"><span class="sp-n"' + (disabled ? ' style="color:var(--hint)"' : '') + '>' + c.n + '</span>' +
            '<span class="sp-c">' + (disabled ? 'To\'xtatilgan' : (n ? n + ' ta mashq' : 'Mashq yo\'q')) + '</span></span></button>';
        }).join('');
        App.icons(box);
      });
    }
  });

  /* =========================================================
     VIEW: sport_cat — kategoriya ichidagi mashqlar
     ========================================================= */
  /* Boostdayga yuborish uchun tanlash rejimi. Sahifa qayta chizilganda ham
     saqlanib qolishi shart emas — yangi kategoriyaga o'tilsa tozalanadi. */
  var SEND = { active: false, cat: '', ids: {} };

  function renderExList(page, cat, info) {
    var box = App.el('ex-list'); if (!box) return;
    var list = S.data[cat] || [];
    if (!list.length) { box.innerHTML = App.empty({ icon: 'trophy', title: 'Mashq yo\'q', text: 'Pastdagi tugma bilan qo\'shing.' }); return; }
    box.innerHTML = list.map(function (e) {
      var sub = exerciseSub(e) + (e.media && e.media.length ? ' · ' + e.media.length + ' media' : '');
      var done = loggedToday(e.id);
      if (SEND.active) {
        var checked = !!SEND.ids[e.id];
        return '<button class="list-row" data-act="sendToggleEx" data-arg=\'' + App.arg({ id: e.id }) + '\'>' +
          '<span class="li-ic" style="border:1px solid var(--border);background:' + (checked ? 'var(--accent)' : 'none') + ';color:#fff">' +
          (checked ? '<span data-icon="check" data-icon-size="15"></span>' : '') + '</span>' +
          '<div class="li-main"><div class="li-title">' + App.esc(e.name) + '</div>' +
          (sub.trim() ? '<div class="li-sub">' + App.esc(sub) + '</div>' : '') + '</div></button>';
      }
      return '<div class="list-row">' +
        exerciseThumb(e, info) +
        '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" data-act="go" data-arg=\'' +
        App.arg({ v: 'sport_exercise', p: { cat: cat, id: e.id } }) + '\'>' +
        '<div class="li-title">' + App.esc(e.name) + '</div>' + 
        (e.start_time && e.end_time ? '<div class="li-sub" style="color:var(--accent);font-weight:600;margin-bottom:2px">🕒 ' + App.esc(e.start_time) + ' - ' + App.esc(e.end_time) + '</div>' : '') +
        (sub.trim() ? '<div class="li-sub">' + App.esc(sub) + '</div>' : '') + '</button>' +
        '<button class="icon-btn ghost sp-log' + (done ? ' done' : '') + '" data-act="sportLog" data-arg=\'' +
        App.arg({ cat: cat, id: e.id }) + '\' title="Bugun bajardim"><span data-icon="check" data-icon-size="17"></span></button>' +
        '</div>';
    }).join('');
    App.icons(box);
  }

  function renderSportCatPage(page, cat, info) {
    var n = Object.keys(SEND.ids).length;
    var disabled = isCatDisabled(cat);
    var rightHtml = SEND.active ? '' : 
      '<div style="display:flex;gap:12px;margin-left:auto;align-items:center">' +
      '<label class="ui-switch" title="' + (disabled ? 'Turkumni yoqish' : 'Turkumni to\'xtatib turish') + '"><input type="checkbox" onchange="App.actions.catToggle()" ' + (!disabled ? 'checked' : '') + '><span class="ui-slider"></span></label>' +
      '<button class="icon-btn ghost" data-act="sendModeOn" title="Boostdayga yuborish" style="margin:0"><span data-icon="send" data-icon-size="18"></span></button>' +
      '</div>';
    page.innerHTML = topbar(info.n, 'sport', null, rightHtml) +
      (SEND.active
        ? '<div class="flex" style="gap:8px;margin-bottom:14px">' +
          '<button class="btn sec" style="flex:1" data-act="sendModeOff">Bekor qilish</button>' +
          '<button class="btn" style="flex:1" data-act="sendPush">Yuborish (' + n + ')</button></div>'
        : '<button class="btn sec" data-act="restTimer" style="margin-bottom:14px"><span data-icon="clock" data-icon-size="16"></span>Dam olish taymeri</button>') +
      '<div id="ex-list"><div class="load-wrap"><div class="spinner"></div></div></div>' +
      (SEND.active ? '' : '<button class="btn" style="margin-top:14px" data-act="exerciseAdd" data-arg=\'' + App.arg({ cat: cat }) + '\'><span data-icon="plus" data-icon-size="16"></span>Mashq qo\'shish</button>');
    App.icons(page);
    loadAll().then(function () { renderExList(page, cat, info); });
  }

  // Tugma yasaydigan alohida yordamchi endi shart emas, chunki tepadagi div ichida yasadik.
  // function finishBtnHtml(action, icon, label) { ... }

  App.view('sport_cat', {
    nav: 'sport',
    render: function (page, params) {
      var cat = params.cat || '';
      var info = catInfo(cat);
      SEND = { active: false, cat: cat, ids: {} };
      renderSportCatPage(page, cat, info);
    }
  });

  var CAT_DISABLED_KEY = 'sport_cat_disabled_v1';
  function disabledCats() {
    try { var v = JSON.parse(localStorage.getItem(CAT_DISABLED_KEY) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function saveDisabledCats(arr) { try { localStorage.setItem(CAT_DISABLED_KEY, JSON.stringify(arr)); } catch (e) {} }
  function isCatDisabled(catId) {
    return disabledCats().indexOf(catId) >= 0;
  }

  App.actions.catToggle = function () {
    var cat = SEND.cat;
    var d = disabledCats();
    var idx = d.indexOf(cat);
    if (idx >= 0) {
      d.splice(idx, 1);
      App.toast('Turkum yana yoqildi');
    } else {
      d.push(cat);
      App.toast('Turkum vaqtincha to\'xtatildi');
    }
    saveDisabledCats(d);
    renderSportCatPage(App.el('page'), cat, catInfo(cat));
  };

  App.actions.sendModeOn = function () {
    var page = App.el('page');
    SEND.active = true; SEND.ids = {};
    renderSportCatPage(page, SEND.cat, catInfo(SEND.cat));
  };
  App.actions.sendModeOff = function () {
    var page = App.el('page');
    SEND.active = false; SEND.ids = {};
    renderSportCatPage(page, SEND.cat, catInfo(SEND.cat));
  };
  App.actions.sendToggleEx = function (a) {
    if (SEND.ids[a.id]) delete SEND.ids[a.id]; else SEND.ids[a.id] = true;
    renderSportCatPage(App.el('page'), SEND.cat, catInfo(SEND.cat));
  };
  App.actions.sendPush = function () {
    var ids = Object.keys(SEND.ids);
    if (!ids.length) return App.toast('Kamida bitta mashq tanlang');
    var list = S.data[SEND.cat] || [];
    var items = list.filter(function (e) { return SEND.ids[e.id]; }).map(function (e) {
      var timePrefix = '';
      if (e.start_time && e.end_time) timePrefix = e.start_time + ' - ' + e.end_time + ' | ';
      else if (e.start_time) timePrefix = e.start_time + ' | ';
      return { text: timePrefix + e.name };
    });
    if (!window.BoostPush) return App.toast('Boostday moduli yuklanmagan');
    App.toast('Yuborilmoqda...');
    BoostPush.pushTasks('sport', '🏋 Sport mashqlari', items).then(function () {
      App.toast('✅ ' + items.length + ' ta mashq Boostdayga yuborildi');
      App.actions.sendModeOff();
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* =========================================================
     VIEW: sport_exercise — bitta mashqning to'liq sahifasi
     ========================================================= */
  App.view('sport_exercise', {
    nav: 'sport',
    render: function (page, params) {
      var cat = params.cat || '', id = params.id;
      page.innerHTML = '<div id="ex-view"><div class="load-wrap"><div class="spinner"></div></div></div>';
      loadAll().then(function (data) {
        var e = (data[cat] || []).find(function (x) { return String(x.id) === String(id); });
        if (!e) { App.toast('Mashq topilmadi'); App.go('sport_cat', { cat: cat }); return; }
        renderExerciseView(page, cat, e, params.from || '');
      });
    }
  });

  function renderExerciseView(page, cat, e, from) {
    var t = PTYPE[effType(e)] || PTYPE.weight;
    var tgt = todayTarget(e);
    var steps = progressSteps(e);
    var base = t.field === 'weight' ? (e.weight || 0) : (e.reps || 0);
    var done = loggedToday(e.id);
    var auto = e.progress_mode !== 'manual' && e.increase;

    // Media galereyasi
    var media = (e.media || []).map(function (m) {
      var src = '/' + String(m).replace(/^\/+/, '');
      if (/^https?:\/\//i.test(m)) src = m;
      if (/\.(jpg|jpeg|png|gif|webp|avif)$/i.test(m)) {
        return '<img class="ex-media" src="' + App.esc(src) + '" alt="" loading="lazy">';
      }
      if (/youtube\.com|youtu\.be/i.test(m)) {
        return '<a class="ex-media ex-link" href="' + App.esc(m) + '" target="_blank" rel="noopener">' +
          '<span data-icon="play" data-icon-size="22"></span><span>Video</span></a>';
      }
      return '<video class="ex-media" src="' + App.esc(src) + '" controls preload="metadata"></video>';
    }).join('');

    page.innerHTML =
      '<div class="topbar" style="margin:-16px -15px 12px">' +
      /* "Mening mashqlarim" dan kelingan bo'lsa o'sha ro'yxatga qaytadi,
         aks holda kategoriya sahifasiga. */
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' +
      App.arg(from === 'mine' ? { v: 'sport_mine' } : { v: 'sport_cat', p: { cat: cat } }) +
      '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(e.name) + '</h1>' +
      '<button class="icon-btn ghost" id="exv-edit" aria-label="Tahrirlash"><span data-icon="edit" data-icon-size="18"></span></button></div>' +

      // Bugungi maqsad — asosiy blok
      '<div class="ex-hero">' +
      '<span class="ex-hero-ic" style="background:color-mix(in srgb,' + catInfo(cat).c + ' 18%, transparent);color:' + catInfo(cat).c + '">' +
      '<span data-icon="' + catInfo(cat).ic + '" data-icon-size="24"></span></span>' +
      '<div class="ex-hero-lbl">Bugungi maqsad</div>' +
      '<div class="ex-hero-val">' + tgt.value + '<span>' + tgt.unit + '</span></div>' +
      (e.sets ? '<div class="ex-hero-sub">' + e.sets + ' set' + (t.field === 'weight' && e.reps ? ' × ' + e.reps + ' takror' : '') + '</div>' : '') +
      (e.start_time && e.end_time ? '<div class="ex-hero-sub" style="margin-top:8px;color:var(--accent);font-weight:600;font-size:14px">🕒 ' + App.esc(e.start_time) + ' - ' + App.esc(e.end_time) + '</div>' : '') +
      '</div>' +

      // O'sish ma'lumoti
      '<div class="stat-strip" style="margin:16px 0">' +
      '<div class="s"><div class="n">' + base + '<span style="font-size:13px">' + tgt.unit + '</span></div><div class="l">Boshlang\'ich</div></div>' +
      '<div class="s"><div class="n" style="color:var(--success)">' + (e.increase ? '+' + e.increase : '—') + '</div><div class="l">Ortirish</div></div>' +
      '<div class="s"><div class="n">' + steps + '</div><div class="l">Marta oshgan</div></div>' +
      '</div>' +

      '<div class="list-row"><span class="li-ic" data-icon="refresh" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">' + App.esc(t.n.split(' (')[0]) + ' oshadi</div>' +
      '<div class="li-sub">' + App.esc(PMODE[e.progress_mode] || '—') + (auto ? '' : ' · avtomatik emas') + '</div></div></div>' +
      (e.start_date
        ? '<div class="list-row"><span class="li-ic" data-icon="calendar" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">Boshlangan</div><div class="li-sub">' + App.esc(e.start_date) + '</div></div></div>'
        : '') +

      // Tavsif Markdown sifatida render qilinadi (App.md — arxiv/grammar
      // bilan bir xil): sarlavha, ro'yxat, qalin matn, jadval va h.k.
      (e.desc ? '<div class="list-label">Tavsif</div><div class="md-content">' + App.md(e.desc) + '</div>' : '') +
      (media ? '<div class="list-label">Media</div><div class="ex-media-grid">' + media + '</div>' : '') +

      '<button class="btn" id="exv-done" style="margin-top:20px;background:' + (done ? 'var(--card)' : 'var(--success)') +
      ';color:' + (done ? 'var(--text)' : '#fff') + (done ? ';border:1px solid var(--border)' : '') + '">' +
      '<span data-icon="check" data-icon-size="17"></span>' + (done ? 'Bugun bajarilgan — bekor qilish' : 'Bugun bajardim') + '</button>' +
      '<button class="btn sec" id="exv-rest" style="margin-top:10px"><span data-icon="clock" data-icon-size="16"></span>Dam olish taymeri</button>';

    App.icons(page);
    // Tahrirlash mantig'i bitta joyda — App.actions.exerciseEdit (ilgari shu
    // yerda AYNAN o'sha kod takrorlangan, action esa hech qayerdan
    // chaqirilmay o'lik qolgan edi).
    App.el('exv-edit').onclick = function () { App.actions.exerciseEdit({ cat: cat, id: e.id }); };
    App.el('exv-done').onclick = function () { App.actions.sportLog({ cat: cat, id: e.id }); };
    App.el('exv-rest').onclick = function () { App.actions.restTimer(); };
  }

  /* =========================================================
     O'sish tizimi: nima oshadi (og'irlik/takror/vaqt) va qachon oshadi
     ========================================================= */
  var PTYPE = {
    weight: { n: 'Og\'irlik (kg)', unit: 'kg',  field: 'weight', step: '0.5' },
    reps:   { n: 'Takror (soni)',  unit: 'ta',  field: 'reps',   step: '1' },
    time:   { n: 'Vaqt (soniya)',  unit: 's',   field: 'reps',   step: '1' },
    // O'yin sportlari uchun: mashg'ulot daqiqada, yugurish esa metrda o'lchanadi
    min:    { n: 'Vaqt (daqiqa)',  unit: 'daq', field: 'reps',   step: '1' },
    dist:   { n: 'Masofa (metr)',  unit: 'm',   field: 'reps',   step: '10' }
  };
  var PMODE = {
    daily:     'Har kuni',
    even:      'Juft kunlari',
    odd:       'Toq kunlari',
    alternate: 'Kun ora',
    manual:    'Qo\'lda (avtomatik emas)'
  };

  function dstr(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  /* Eski (tur belgilanmagan) mashqlar uchun turni aqlli topish:
     og'irligi 0 bo'lib takrori bor bo'lsa — bu tana og'irligi bilan bajariladigan
     mashq (turnik/brus), ya'ni takror oshadi. Ma'lumot o'zgartirilmaydi, faqat ko'rsatish. */
  function effType(e) {
    var pt = e.progress_type || 'weight';
    if (pt === 'weight' && !(e.weight > 0) && (e.reps > 0)) return 'reps';
    return pt;
  }

  /* Berilgan sana o'sish kunimi? */
  function isProgressDay(mode, date, startDate) {
    if (mode === 'manual') return false;
    if (mode === 'daily') return true;
    var day = date.getDate();
    if (mode === 'even') return day % 2 === 0;
    if (mode === 'odd') return day % 2 === 1;
    if (mode === 'alternate') {
      if (!startDate) return true;
      var s = new Date(startDate + 'T00:00:00');
      var diff = Math.floor((date - s) / 86400000);
      return diff >= 0 && diff % 2 === 0;
    }
    return true;
  }

  /* Boshlanish sanasidan bugungacha nechta o'sish kuni bo'lgan */
  function progressSteps(e) {
    if (!e.start_date || e.progress_mode === 'manual') return 0;
    var s = new Date(e.start_date + 'T00:00:00');
    var today = new Date(); today.setHours(0, 0, 0, 0);
    if (isNaN(s.getTime()) || s > today) return 0;
    var n = 0, cur = new Date(s);
    // Birinchi kun boshlang'ich qiymat — o'sish keyingi o'sish kunlaridan boshlanadi
    cur.setDate(cur.getDate() + 1);
    var guard = 0;
    while (cur <= today && guard < 3650) {
      if (isProgressDay(e.progress_mode, cur, e.start_date)) n++;
      cur.setDate(cur.getDate() + 1);
      guard++;
    }
    return n;
  }

  /* Bugungi maqsad qiymati */
  function todayTarget(e) {
    var t = PTYPE[effType(e)] || PTYPE.weight;
    var base = t.field === 'weight' ? (e.weight || 0) : (e.reps || 0);
    var inc = e.increase || 0;
    var val = base + inc * progressSteps(e);
    return { value: Math.round(val * 100) / 100, unit: t.unit, label: t.n };
  }

  /* Qisqa tavsif: "20kg · 4x10 · har kuni +2.5kg" */
  function exerciseSub(e) {
    var t = PTYPE[effType(e)] || PTYPE.weight;
    var tgt = todayTarget(e);
    var parts = [];
    parts.push(tgt.value + tgt.unit + (t.field === 'reps' ? '' : ''));
    if (e.sets) parts.push(e.sets + ' ' + (isTeamCat(e.category) ? 'seriya' : 'set'));
    if (e.increase) parts.push('+' + e.increase + tgt.unit + ' ' + (PMODE[e.progress_mode] || '').toLowerCase());
    return parts.join(' · ');
  }

  /* ---------- Mashq qo'shish/tahrirlash sheet ---------- */
  function exerciseFormHtml(e) {
    e = e || {};
    var mediaPreview = '';
    if (e.media && e.media.length) {
      mediaPreview = '<div class="list-label" style="margin-top:18px">Mavjud media (' + e.media.length + ')</div>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px">' +
        e.media.map(function (m) {
          if (/\.(jpg|jpeg|png|gif|webp|avif)$/i.test(m)) {
            return '<img src="/' + m.replace(/^\/+/, '') + '" style="width:56px;height:56px;border-radius:10px;object-fit:cover;border:1px solid var(--border)">';
          }
          return '<span style="width:56px;height:56px;border-radius:10px;border:1px solid var(--border);display:flex;align-items:center;justify-content:center;color:var(--hint)"><span data-icon="video" data-icon-size="20"></span></span>';
        }).join('') + '</div>' +
        '<label class="field" style="display:flex;align-items:center;gap:8px;flex-direction:row"><input type="checkbox" id="ex-replace" style="width:auto"><span style="margin:0">Yangi media eskilarini almashtirsin</span></label>';
    }
    var ptype = effType(e);
    var pmode = e.progress_mode || 'daily';
    var sdate = e.start_date || dstr(new Date());

    return '<label class="field"><span>Nomi</span><input class="input" id="ex-name" value="' + App.esc(e.name || '') + '" placeholder="Masalan: Tortilish"></label>' +
      '<label class="field"><span>Tavsif (ixtiyoriy — Markdown)</span><textarea class="textarea" id="ex-desc" rows="8">' + App.esc(e.desc || '') + '</textarea></label>' +
      '<p class="muted" style="font-size:11.5px;margin:-6px 1px 12px">Markdown ishlaydi: ' +
      '<code>## Sarlavha</code>, <code>**qalin**</code>, <code>- ro\'yxat</code>, <code>1. raqamli</code>, jadval.</p>' +

      '<label class="field"><span>Nima oshadi?</span><select class="input" id="ex-ptype">' +
      Object.keys(PTYPE).map(function (k) {
        return '<option value="' + k + '"' + (k === ptype ? ' selected' : '') + '>' + PTYPE[k].n + '</option>';
      }).join('') + '</select></label>' +

      '<div style="display:flex;gap:10px">' +
      '<label class="field" style="flex:1"><span id="ex-base-lbl">Boshlang\'ich</span><input class="input" type="number" step="0.5" id="ex-base" value="' +
      (ptype === 'weight' ? (e.weight || '') : (e.reps || '')) + '"></label>' +
      '<label class="field" style="flex:1"><span id="ex-inc-lbl">Ortirish</span><input class="input" type="number" step="0.5" id="ex-increase" value="' + (e.increase || '') + '"></label>' +
      '</div>' +

      '<label class="field"><span>Qachon oshadi?</span><select class="input" id="ex-pmode">' +
      Object.keys(PMODE).map(function (k) {
        return '<option value="' + k + '"' + (k === pmode ? ' selected' : '') + '>' + PMODE[k] + '</option>';
      }).join('') + '</select></label>' +

      '<label class="field"><span>Boshlangan sana</span><input class="input" type="date" id="ex-sdate" value="' + sdate + '"></label>' +
      '<div style="display:flex;gap:10px">' +
      '<label class="field" style="flex:1"><span>Boshlanish vaqti</span><input class="input" type="time" id="ex-stime" value="' + (e.start_time || '') + '"></label>' +
      '<label class="field" style="flex:1"><span>Tugash vaqti</span><input class="input" type="time" id="ex-etime" value="' + (e.end_time || '') + '"></label>' +
      '</div>' +
      '<p class="muted" id="ex-preview" style="font-size:12.5px;margin:-6px 1px 12px"></p>' +

      '<div style="display:flex;gap:10px">' +
      '<label class="field" style="flex:1"><span>Setlar</span><input class="input" type="number" id="ex-sets" value="' + (e.sets || '') + '"></label>' +
      '<label class="field" style="flex:1" id="ex-reps-wrap"><span>Takrorlar</span><input class="input" type="number" id="ex-reps" value="' + (e.reps || '') + '"></label>' +
      '</div>' +
      '<label class="field"><span>Rasm/video qo\'shish (ixtiyoriy)</span><input type="file" class="input" id="ex-media" multiple accept="image/*,video/*"></label>' +
      '<label class="field"><span>YouTube/video link (ixtiyoriy)</span><input class="input" id="ex-link" placeholder="https://youtube.com/..."></label>' +
      mediaPreview +
      '<button class="btn" id="ex-save" style="margin-top:6px">Saqlash</button>' +
      (e.id ? '<button class="btn ghost" style="margin-top:10px;color:var(--danger);border-color:var(--danger-soft)" id="ex-del">O\'chirish</button>' : '');
  }

  function bindExerciseForm(sh, cat, existing) {
    // Tur o'zgarganda yorliqlar va ko'rinish moslashadi
    function syncLabels() {
      var t = PTYPE[sh.querySelector('#ex-ptype').value] || PTYPE.weight;
      sh.querySelector('#ex-base-lbl').textContent = 'Boshlang\'ich (' + t.unit + ')';
      sh.querySelector('#ex-inc-lbl').textContent = 'Ortirish (' + t.unit + ')';
      sh.querySelector('#ex-base').step = t.step;
      sh.querySelector('#ex-increase').step = t.step;
      // Takror/vaqt turida "Takrorlar" maydoni boshlang'ich bilan bir xil bo'ladi
      sh.querySelector('#ex-reps-wrap').style.display = (t.field === 'reps') ? 'none' : '';
      preview();
    }
    function preview() {
      var e = {
        progress_type: sh.querySelector('#ex-ptype').value,
        progress_mode: sh.querySelector('#ex-pmode').value,
        start_date: sh.querySelector('#ex-sdate').value,
        increase: parseFloat(sh.querySelector('#ex-increase').value) || 0
      };
      var base = parseFloat(sh.querySelector('#ex-base').value) || 0;
      if (e.progress_type === 'weight') e.weight = base; else e.reps = base;
      var t = todayTarget(e);
      var steps = progressSteps(e);
      var el = sh.querySelector('#ex-preview');
      if (e.progress_mode === 'manual' || !e.increase) {
        el.textContent = 'Avtomatik oshmaydi — qiymat o\'zgarmaydi.';
      } else {
        el.innerHTML = 'Bugungi maqsad: <b style="color:var(--text)">' + t.value + t.unit + '</b>' +
          ' (' + steps + ' marta oshgan · ' + (PMODE[e.progress_mode] || '').toLowerCase() + ')';
      }
    }
    ['#ex-ptype'].forEach(function (s) { sh.querySelector(s).onchange = syncLabels; });
    ['#ex-pmode', '#ex-sdate', '#ex-base', '#ex-increase'].forEach(function (s) {
      sh.querySelector(s).oninput = preview;
      sh.querySelector(s).onchange = preview;
    });
    syncLabels();

    sh.querySelector('#ex-save').onclick = function () {
      var name = sh.querySelector('#ex-name').value.trim();
      if (!name) return App.toast('Nomini kiriting');
      var ptype = sh.querySelector('#ex-ptype').value;
      var base = sh.querySelector('#ex-base').value || 0;
      var fd = new FormData();
      fd.append('id', existing && existing.id ? existing.id : 0);
      fd.append('category', cat);
      fd.append('name', name);
      fd.append('desc', sh.querySelector('#ex-desc').value.trim());
      fd.append('progress_type', ptype);
      fd.append('progress_mode', sh.querySelector('#ex-pmode').value);
      fd.append('start_date', sh.querySelector('#ex-sdate').value || '');
      // Og'irlik turida `weight`, takror/vaqt turida `reps` boshlang'ich qiymat bo'ladi
      fd.append('weight', ptype === 'weight' ? base : 0);
      fd.append('reps', ptype === 'weight' ? (sh.querySelector('#ex-reps').value || 0) : base);
      fd.append('increase', sh.querySelector('#ex-increase').value || 0);
      fd.append('sets', sh.querySelector('#ex-sets').value || 0);
      fd.append('start_time', sh.querySelector('#ex-stime').value || '');
      fd.append('end_time', sh.querySelector('#ex-etime').value || '');
      var replaceEl = sh.querySelector('#ex-replace');
      if (replaceEl && replaceEl.checked) fd.append('replace_media', '1');
      var files = sh.querySelector('#ex-media').files;
      for (var i = 0; i < files.length; i++) fd.append('media', files[i]);
      var link = sh.querySelector('#ex-link').value.trim();
      if (link) fd.append('media_links', link);

      var btn = sh.querySelector('#ex-save'); btn.textContent = 'Saqlanmoqda...'; btn.disabled = true;
      App.callForm('sport_save_exercise', fd).then(function (res) {
        App.closeSheet(); App.toast('✅ Saqlandi');
        S.data = res.data || null;
        App.reload();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); btn.textContent = 'Saqlash'; btn.disabled = false; });
    };
    var delBtn = sh.querySelector('#ex-del');
    if (delBtn) {
      delBtn.onclick = function () {
        App.confirm('"' + existing.name + '" mashqi o\'chiriladi.', function () {
          App.call('sport_delete_exercise', { id: existing.id }).then(function () {
            App.closeSheet(); App.toast('O\'chirildi'); loadAll(true).then(App.reload);
          }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        }, { danger: true, yes: 'O\'chirish' });
      };
    }
  }

  App.actions.exerciseAdd = function (a) {
    var sh = App.sheet(exerciseFormHtml(), { title: 'Yangi mashq' });
    bindExerciseForm(sh, a.cat, null);
  };
  App.actions.exerciseEdit = function (a) {
    var e = (S.data[a.cat] || []).find(function (x) { return x.id === a.id; });
    if (!e) return;
    var sh = App.sheet(exerciseFormHtml(e), { title: e.name });
    bindExerciseForm(sh, a.cat, e);
  };

  /* =========================================================
     Mashg'ulot tarixi — localStorage'da (server bilan sinxron)
     ========================================================= */
  var LOG_KEY = 'sport_log_v1';

  function sportLog() {
    try { var v = JSON.parse(localStorage.getItem(LOG_KEY) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function saveLog(list) { try { localStorage.setItem(LOG_KEY, JSON.stringify(list.slice(-1000))); } catch (e) {} }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function exerciseName(id) {
    if (!S.data) return null;
    for (var cat in S.data) {
      var found = (S.data[cat] || []).find(function (x) { return String(x.id) === String(id); });
      if (found) return found.name;
    }
    return null;
  }
  function loggedToday(id) {
    var t = today();
    if (sportLog().some(function (x) { return x.d === t && String(x.id) === String(id); })) return true;
    // Telegram/Boostday orqali bajarilgan bo'lsa ham hisobga olinadi — vazifa
    // matni mashq nomi bilan aynan bir xil bo'lib yuborilgani uchun (band 25).
    if (S.boostDone && S.boostDone.length) {
      var name = exerciseName(id);
      if (name && S.boostDone.indexOf(name) >= 0) return true;
    }
    return false;
  }

  /* Bitta mashqni bugun bajarilgan/bajarilmagan deb belgilaydi. `silent` bo'lsa
     App.reload() chaqirmaydi (masalan Boostday "Bugungi ishlar" ro'yxatidan
     turib belgilanganda — o'sha ro'yxat o'zi qayta chiziladi, butun Sport
     sahifasi emas). Qaytaradi: endi bajarilganmi (true/false) yoki topilmasa null. */
  /* `noBoostSync` — Boostday tomonidan chaqirilganda true bo'ladi, shunda
     ortga qarab yana Boostday belgilanmaydi (cheksiz aylanishning oldi olinadi). */
  function toggleExercise(cat, id, silent, noBoostSync) {
    var e = ((S.data && S.data[cat]) || []).find(function (x) { return String(x.id) === String(id); });
    if (!e) return null;
    var list = sportLog(), t = today();
    var idx = list.findIndex(function (x) { return x.d === t && String(x.id) === String(id); });

    /* Yo'nalish `loggedToday` bo'yicha aniqlanadi, mahalliy ro'yxat bo'yicha
       EMAS. Sabab: mashq Telegramdan (yoki boshqa qurilmadan) belgilangan
       bo'lsa u faqat SERVERDA turadi — mahalliy ro'yxat bo'sh bo'ladi.
       Ilgari shu yerda `idx >= 0` tekshirilgani uchun bunday mashqni bosganda
       u bekor qilinmay, QAYTA belgilanardi — foydalanuvchi uni hech qachon
       olib tashlay olmasdi. */
    var nowDone;
    if (loggedToday(id)) {
      if (idx >= 0) { list.splice(idx, 1); saveLog(list); }
      /* MUHIM: mahalliy ro'yxatdan o'chirishning O'ZI yetmaydi.
         `loggedToday` serverdagi `activity_log` yozuvlarini ham hisobga
         oladi (Telegramdan belgilangani ko'rinsin deb), shuning uchun
         server yozuvi qolsa mashq "bajarilgan" bo'lib turaverardi va uni
         qaytarib olib bo'lmasdi. Endi server yozuvi ham o'chiriladi. */
      if (S.boostDone) {
        S.boostDone = S.boostDone.filter(function (n) { return App.taskKey(n) !== App.taskKey(e.name); });
      }
      App.call('unlog_activity', { section: 'sport', object: e.name }).catch(function () {});
      if (!silent) App.toast('Bekor qilindi');
      nowDone = false;
    } else {
      list.push({ d: t, cat: cat, id: e.id, name: e.name, weight: e.weight || 0, sets: e.sets || 0, reps: e.reps || 0 });
      saveLog(list);
      if (!silent) App.toast('✅ Bajarildi: ' + e.name);
      if (window.Activity) Activity.mark();
      /* Jurnalga faqat SHU YERDAN belgilanganda yozamiz. Boostday tomonidan
         chaqirilgan bo'lsa, bot o'zi allaqachon `section='sport'` yozgan —
         ikki marta yozilsa statistika ikki barobar ko'rsatardi. */
      if (!noBoostSync) {
        App.call('log_activity', { section: 'sport', object: e.name, amount: 1, unit: 'marta', meta: { cat: cat, via: 'sport' } }).catch(function () {});
      }
      nowDone = true;
    }

    /* Ikki tomonlama sinxron: shu mashqqa mos Boostday vazifasi bo'lsa uni ham
       belgilaymiz — shunda Telegramdagi xabar ham yangilanadi. */
    if (!noBoostSync && window.BoostDay && BoostDay.setTaskDone) {
      BoostDay.setTaskDone(e.name, nowDone);
    }

    if (!silent) App.reload();
    return nowDone;
  }

  App.actions.sportLog = function (a) { toggleExercise(a.cat, a.id, false); };

  /* Foydalanuvchi "bu mashqni Bugungi ishlarda ko'rsatma" desa, uning ID'si
     shu ro'yxatga tushadi — mashq o'zi Sport bo'limida qoladi, faqat
     birlashtirilgan "Bugungi ishlar" ro'yxatidan chiqib ketadi. */
  var HIDDEN_KEY = 'sport_today_hidden_v1';
  function hiddenIds() {
    try { var v = JSON.parse(localStorage.getItem(HIDDEN_KEY) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function saveHidden(arr) { try { localStorage.setItem(HIDDEN_KEY, JSON.stringify(arr)); } catch (e) {} }

  /* Hali BUGUN bajarilmagan (yoki — allExercises=true bo'lsa — mutlaqo BARCHA)
     mashqlar ro'yxati. `wantHidden` true bo'lsa — teskarisi: faqat
     YASHIRILGANLARI qaytariladi ("yashiringan mashqlarni qayta yoqish" uchun).
     MUHIM: bu yerda `isProgressDay` ATAYLAB ishlatilmaydi — u "bugun OG'IRLIK/
     qiymat oshadimi" degan boshqa savolga javob beradi (mashqning o'zi bugun
     kerak-kerak emasligiga emas). Avval shu bilan aralashtirilib, progress_mode
     'manual' bo'lgan mashqlar (masalan futbol/voleybol/badminton — hammasi
     'manual') "Bugungi ishlar"da HECH QACHON ko'rinmay qolgan edi. Endi
     ortiqcha mashqni ko'rsatmaslik foydalanuvchining o'zi ✕ bilan yashirishiga
     qoldirilgan (hideToday/unhideToday). */
  /* =========================================================
     MENING MASHQLARIM — shaxsiy ro'yxat

     Barcha kategoriyalarda 90+ mashq bor; kundalik ishlatiladigani esa
     bir nechtasi. Bu bo'lim foydalanuvchi TANLAGAN mashqlarni bitta qisqa
     ro'yxatda ko'rsatadi, shu yerdan belgilash qulay bo'ladi.
     Saqlash: `sport_mine_v1` (id lar massivi) — remote-storage sinxronlaydi.
     ========================================================= */
  var MINE_KEY = 'sport_mine_v1';

  function mineIds() {
    try {
      var v = JSON.parse(localStorage.getItem(MINE_KEY) || '[]');
      return Array.isArray(v) ? v.map(String) : [];
    } catch (e) { return []; }
  }
  function setMine(ids) {
    try { localStorage.setItem(MINE_KEY, JSON.stringify(ids.map(String))); } catch (e) {}
  }

  /* Tanlangan mashqlar — TO'LIQ mashq obyekti bilan (o'chirilganlari tushadi).
     `ex` — bazadagi asl yozuv: rasm, og'irlik/set/takror, vaqt va h.k.
     Shu tufayli bu yerda kategoriya sahifasidagi AYNAN o'sha kartochkani
     chizish mumkin. */
  function mineList() {
    if (!S.data) return [];
    var ids = mineIds(), out = [];
    CATS.forEach(function (c) {
      (S.data[c.id] || []).forEach(function (e) {
        if (ids.indexOf(String(e.id)) >= 0) {
          out.push({ cat: c.id, info: c, id: e.id, name: e.name, ex: e });
        }
      });
    });
    return out;
  }

  App.view('sport_mine', {
    nav: 'sport',
    render: function (page) {
      page.innerHTML = topbar('Mening mashqlarim', 'sport', {},
        '<button class="icon-btn ghost" data-act="mineDownload" style="margin-left:auto" aria-label=".md yuklab olish">' +
        '<span data-icon="download" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="mineEdit" aria-label="Tanlash">' +
        '<span data-icon="edit" data-icon-size="18"></span></button>') +
        '<div id="mine-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      loadAll().then(function () { paintMine(); });
    }
  });

  /* .md fayl qilib yuklab olish. Har mashq uchun HOZIRGI holat to'liq
     yoziladi: bugungi maqsad (necha kg/ta/soniya/daqiqa/metrda turgani),
     set soni, boshlang'ich qiymat va undan necha marta oshgani, oshish
     qadami/rejimi, vaqt oynasi, bugun bajarilgan-bajarilmagani, tavsifi. */
  function mineToMd() {
    var list = mineList();
    var byCat = {};
    list.forEach(function (x) { (byCat[x.cat] = byCat[x.cat] || []).push(x); });

    var done = list.filter(function (x) { return loggedToday(x.id); }).length;
    var lines = [
      '# Mening mashqlarim',
      '',
      '_' + dstr(new Date()) + ' · ' + list.length + ' ta mashq · bugun bajarildi: ' +
        done + '/' + list.length + '_',
      ''
    ];

    CATS.forEach(function (c) {
      var items = byCat[c.id];
      if (!items || !items.length) return;
      lines.push('## ' + c.n, '');
      items.forEach(function (x) {
        var e = x.ex;
        var t = PTYPE[effType(e)] || PTYPE.weight;
        var tgt = todayTarget(e);
        var steps = progressSteps(e);
        var base = t.field === 'weight' ? (e.weight || 0) : (e.reps || 0);
        var setWord = isTeamCat(e.category) ? 'seriya' : 'set';

        lines.push('### ' + e.name + (loggedToday(e.id) ? ' ✅' : ''));
        lines.push('- **Hozir:** ' + tgt.value + ' ' + tgt.unit +
          (e.sets ? ' × ' + e.sets + ' ' + setWord : '') + ' — ' + t.n);
        /* Oshish bo'lmasa boshlang'ich = hozirgi qiymat — takrorlamaymiz. */
        if (steps && tgt.value !== base) {
          lines.push('- **Boshlang\'ich:** ' + base + ' ' + tgt.unit +
            ' → ' + steps + ' marta oshgan');
        }
        lines.push('- **Ortirish:** ' + (e.increase
          ? '+' + e.increase + ' ' + tgt.unit + ' · ' + (PMODE[e.progress_mode] || '')
          : 'yo\'q'));
        if (e.start_date) lines.push('- **Boshlangan sana:** ' + e.start_date);
        if (e.start_time && e.end_time) {
          lines.push('- **Vaqt:** ' + e.start_time + ' - ' + e.end_time);
        }
        if (e.desc && e.desc.trim()) lines.push('', e.desc.trim());
        lines.push('');
      });
    });
    return lines.join('\n');
  }
  App.actions.mineDownload = function () {
    loadAll().then(function () {
      if (!mineList().length) { App.toast('⚠️ Hali mashq tanlanmagan'); return; }
      App.download('Mening mashqlarim.md', mineToMd());
    });
  };

  function paintMine() {
    var box = App.el('mine-body'); if (!box) return;
    var list = mineList();

    if (!list.length) {
      box.innerHTML = App.empty({
        icon: 'activity', title: 'Hali mashq tanlanmagan',
        text: 'Barcha bo\'limlardagi mashqlardan o\'zingiz bajaradiganlarini tanlang — shu yerda qisqa ro\'yxat bo\'lib turadi.'
      }) + '<button class="btn" data-act="mineEdit" style="margin-top:12px">' +
        '<span data-icon="plus" data-icon-size="16"></span>Mashq tanlash</button>';
      App.icons(box);
      return;
    }

    var done = list.filter(function (x) { return loggedToday(x.id); }).length;

    /* Kartochka kategoriya sahifasidagi bilan AYNAN bir xil: rasm, nom,
       vaqt, og'irlik/set ma'lumoti, o'ngda "bugun bajardim" tugmasi.
       Bosilganda mashqning to'liq sahifasi (bajarish tartibi, media)
       ochiladi — ya'ni hamma narsa shu yerning o'zida. */
    box.innerHTML =
      '<div class="mine-head"><b>' + done + ' / ' + list.length + '</b>' +
      '<span>bugun bajarildi</span></div>' +
      '<div class="mine-bar"><i style="width:' + Math.round((done / list.length) * 100) + '%"></i></div>' +
      '<button class="btn sec" data-act="restTimer" style="margin-bottom:14px">' +
      '<span data-icon="clock" data-icon-size="16"></span>Dam olish taymeri</button>' +
      list.map(function (x) {
        var e = x.ex, info = x.info;
        var sub = exerciseSub(e) + (e.media && e.media.length ? ' · ' + e.media.length + ' media' : '');
        var on = loggedToday(e.id);
        return '<div class="list-row">' +
          exerciseThumb(e, info) +
          '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" data-act="go" data-arg=\'' +
          App.arg({ v: 'sport_exercise', p: { cat: x.cat, id: e.id, from: 'mine' } }) + '\'>' +
          '<div class="li-title">' + App.esc(e.name) + '</div>' +
          (e.start_time && e.end_time
            ? '<div class="li-sub" style="color:var(--accent);font-weight:600;margin-bottom:2px">🕒 ' +
              App.esc(e.start_time) + ' - ' + App.esc(e.end_time) + '</div>' : '') +
          '<div class="li-sub">' + App.esc(info.n) + (sub.trim() ? ' · ' + App.esc(sub) : '') + '</div></button>' +
          '<button class="icon-btn ghost sp-log' + (on ? ' done' : '') + '" data-act="sportLog" data-arg=\'' +
          App.arg({ cat: x.cat, id: e.id }) + '\' title="Bugun bajardim">' +
          '<span data-icon="check" data-icon-size="17"></span></button>' +
          '</div>';
      }).join('') +
      '<button class="btn sec" data-act="mineEdit" style="margin-top:16px">' +
      '<span data-icon="edit" data-icon-size="16"></span>Ro\'yxatni o\'zgartirish</button>';
    App.icons(box);
  }

  /* Tanlash oynasi — barcha kategoriyalardagi mashqlar, belgilash bilan */
  App.actions.mineEdit = function () {
    var sel = {};
    mineIds().forEach(function (id) { sel[id] = 1; });

    /* MUHIM: element JORIY oyna ichidan izlanadi, `App.el(id)` bilan EMAS.
       Oyna yopilganda DOM'dan ~280ms keyin o'chadi; shu orada qayta ochilsa
       hujjatda bir xil id'li IKKI element bo'ladi va `App.el` o'layotganini
       qaytarib, chizilgan ro'yxat ko'rinmay qolardi. */
    var SHEET = null;
    function draw() {
      var body = SHEET && SHEET.querySelector('#mine-pick'); if (!body) return;
      var html = '';
      CATS.forEach(function (c) {
        var items = (S.data && S.data[c.id]) || [];
        if (!items.length) return;
        html += '<div class="list-label">' + App.esc(c.n) + '</div>' +
          items.map(function (e) {
            var on = !!sel[String(e.id)];
            return '<button class="pk-row' + (on ? ' on' : '') + '" data-mine="' + e.id + '">' +
              '<span class="pk-box">' + (on ? '✓' : '') + '</span>' +
              '<span class="pk-main"><b>' + App.esc(e.name) + '</b></span></button>';
          }).join('');
      });
      if (!html) html = App.empty({ icon: 'activity', title: 'Mashq yo\'q', text: 'Avval kategoriyalarga mashq qo\'shing.' });
      var n = Object.keys(sel).length;
      html += '<div class="pk-bar"><button class="btn" id="mine-save">' +
        (n ? n + ' ta mashq saqlash' : 'Bo\'sh ro\'yxatni saqlash') + '</button></div>';
      body.innerHTML = html;
      App.icons(body);
      body.querySelectorAll('[data-mine]').forEach(function (b) {
        b.onclick = function () {
          var id = b.getAttribute('data-mine');
          if (sel[id]) delete sel[id]; else sel[id] = 1;
          draw();
        };
      });
      body.querySelector('#mine-save').onclick = function () {
        setMine(Object.keys(sel));
        App.closeSheet();
        App.toast('✅ Ro\'yxat saqlandi');
        paintMine();
      };
    }

    SHEET = App.sheet('<div id="mine-pick"><div class="load-wrap"><div class="spinner"></div></div></div>',
                      { title: 'Mashq tanlash' });
    loadAll().then(draw);
  };

  function scheduledPending(wantHidden, allExercises) {
    if (!S.data) return [];
    var out = [];
    var hidden = hiddenIds();
    var disabledC = disabledCats();
    CATS.forEach(function (c) {
      if (disabledC.indexOf(c.id) >= 0) return;
      (S.data[c.id] || []).forEach(function (e) {
        if (!allExercises && loggedToday(e.id)) return;
        var isHidden = hidden.indexOf(String(e.id)) >= 0;
        if (!allExercises && isHidden !== !!wantHidden) return;
        out.push({ cat: c.id, catName: c.n, id: e.id, name: e.name });
      });
    });
    return out;
  }

  /* Bugun BAJARILGAN mashqlar (Bajarilganlar panelida qayta bosib bekor
     qilish uchun) — sportLog() dan bugungi sanali yozuvlar. */
  function doneTodayList() {
    var t = today();
    return sportLog().filter(function (x) { return x.d === t; }).map(function (x) {
      var info = catInfo(x.cat);
      return { cat: x.cat, catName: info.n, id: x.id, name: x.name };
    });
  }

  /* Boostday "Bugungi ishlar" ro'yxati uchun ko'prik — sport mashqlari va
     Boostday vazifalari BITTA ro'yxatda ko'rinishi shart (band 5.1). */
  /* Nom bo'yicha mashqni topadi (Boostday vazifasi bilan bog'lash uchun).
     Taqqoslash `App.taskKey` orqali — vaqt prefiksi olib tashlanadi. */
  function findByName(text) {
    if (!S.data) return null;
    var key = App.taskKey(text);
    if (!key) return null;
    for (var cat in S.data) {
      var hit = (S.data[cat] || []).find(function (x) { return App.taskKey(x.name) === key; });
      if (hit) return { cat: cat, id: hit.id, name: hit.name };
    }
    return null;
  }

  window.SportBridge = {
    ensureLoaded: function () { return loadAll(); },
    todayPending: function () { return scheduledPending(false); },
    hiddenPending: function () { return scheduledPending(true); },
    doneToday: function () { return doneTodayList(); },
    allExercises: function () { return scheduledPending(false, true); },
    findByName: findByName,
    isDone: function (id) { return loggedToday(id); },
    /* Boostday tomonidan chaqiriladi: mashqni MA'LUM holatga keltiradi.
       `toggle` emas — chunki chaqiruvchi allaqachon yangi holatni biladi va
       ikki tomon "toggle" qilsa holat teskari bo'lib ketardi. */
    setDone: function (cat, id, want) {
      var isNow = loggedToday(id);
      if (!!want === !!isNow) return isNow;
      return toggleExercise(cat, id, true, true);   // silent + boostga qaytarma sinxron yo'q
    },
    /* Nomlar ro'yxatidan mos mashqlarni "Mening mashqlarim"ga qo'shadi.
       Kun rejasi .md importi shuni chaqiradi: rejadagi vazifa nomi haqiqiy
       mashq nomi bilan mos kelsa, mashq avtomatik shaxsiy ro'yxatga tushadi
       (Boostdayda belgilangani Sportda ham ✓ bo'lib ko'rinishi shu orqali).
       Qaytaradi: YANGI qo'shilganlar soni. */
    addToMineByName: function (names) {
      if (!S.data || !names || !names.length) return 0;
      var byKey = {};
      CATS.forEach(function (c) {
        (S.data[c.id] || []).forEach(function (e) { byKey[App.taskKey(e.name)] = e; });
      });
      var ids = mineIds(), have = {}, added = 0;
      ids.forEach(function (id) { have[String(id)] = 1; });
      names.forEach(function (n) {
        var e = byKey[App.taskKey(n)];
        if (!e || have[String(e.id)]) return;
        ids.push(String(e.id)); have[String(e.id)] = 1; added++;
      });
      if (added) setMine(ids);
      return added;
    },
    hideToday: function (id) {
      var h = hiddenIds();
      if (h.indexOf(String(id)) < 0) { h.push(String(id)); saveHidden(h); }
    },
    unhideToday: function (id) {
      saveHidden(hiddenIds().filter(function (x) { return x !== String(id); }));
    },
    toggle: function (cat, id) { return toggleExercise(cat, id, true); }
  };

  /* ---------- Dam olish taymeri (setlar orasida) ---------- */
  var REST = { t: null, left: 0 };
  App.actions.restTimer = function () {
    var last = parseInt(localStorage.getItem('sport_rest_sec') || '90', 10);
    var html =
      '<div style="text-align:center;position:relative;width:160px;height:160px;margin:10px auto">' +
      '<svg viewBox="0 0 100 100" style="width:100%;height:100%;transform:rotate(-90deg)">' +
      '<circle cx="50" cy="50" r="45" fill="none" stroke="var(--border)" stroke-width="6"/>' +
      '<circle id="rt-svg" cx="50" cy="50" r="45" fill="none" stroke="var(--accent)" stroke-width="6" stroke-dasharray="283" stroke-dashoffset="0" style="transition: stroke-dashoffset 1s linear"/>' +
      '</svg>' +
      '<div style="position:absolute;top:0;left:0;right:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center">' +
      '<div id="rt-view" style="font-size:32px;font-weight:800;font-family:var(--mono);line-height:1">' + fmt(last) + '</div>' +
      '</div></div>' +
      '<p class="muted" id="rt-hint" style="text-align:center;font-size:12.5px;margin:0 0 16px">Vaqtni tanlang va boshlang</p>' +
      '<div class="flex" id="rt-presets" style="gap:7px;flex-wrap:wrap;justify-content:center;margin-bottom:16px">' +
      [30, 60, 90, 120, 180].map(function (s) {
        return '<button class="chip-btn' + (s === last ? ' active' : '') + '" data-s="' + s + '">' + fmt(s) + '</button>';
      }).join('') + '</div>' +
      '<div class="btn-row"><button class="btn sec" id="rt-stop">To\'xtatish</button>' +
      '<button class="btn" id="rt-start">Boshlash</button></div>';
    var sh = App.sheet(html, { title: 'Dam olish taymeri' });
    var sec = last;

    function updateSvg(left) {
      var svg = sh.querySelector('#rt-svg');
      if (svg) svg.style.strokeDashoffset = (283 - (left / sec) * 283) || 0;
    }

    function fmtNow() { 
      var left = Math.max(0, REST.left > 0 ? REST.left : sec);
      sh.querySelector('#rt-view').textContent = fmt(left);
      updateSvg(left);
    }
    sh.querySelectorAll('#rt-presets .chip-btn').forEach(function (b) {
      b.onclick = function () {
        sh.querySelectorAll('#rt-presets .chip-btn').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active');
        sec = +b.getAttribute('data-s');
        localStorage.setItem('sport_rest_sec', sec);
        stop(); fmtNow();
      };
    });
    function stop() { if (REST.t) { clearInterval(REST.t); REST.t = null; } REST.left = 0; }
    sh.querySelector('#rt-stop').onclick = function () { stop(); fmtNow(); sh.querySelector('#rt-hint').textContent = 'To\'xtatildi'; };
    sh.querySelector('#rt-start').onclick = function () {
      stop(); REST.left = sec;
      updateSvg(sec);
      sh.querySelector('#rt-hint').textContent = 'Ketmoqda...';
      REST.t = setInterval(function () {
        REST.left--;
        var v = sh.querySelector('#rt-view');
        if (!v) { stop(); return; }               // oyna yopilgan
        v.textContent = fmt(Math.max(0, REST.left));
        updateSvg(REST.left);
        if (REST.left <= 0) {
          stop(); v.textContent = '00:00'; updateSvg(0);
          sh.querySelector('#rt-hint').textContent = '✅ Dam tugadi!';
          App.toast('⏱ Dam olish tugadi');
          try { navigator.vibrate && navigator.vibrate([200, 100, 200]); } catch (e) {}
        }
      }, 1000);
    };
  };
  function fmt(s) { return ('0' + Math.floor(s / 60)).slice(-2) + ':' + ('0' + (s % 60)).slice(-2); }
})();
