/* Bosh sahifa.
   Tuzilishi: halqali ko'rsatkichlar -> bugungi darslar -> faollik heatmap'i
   (oxirgi bir yil) -> kunlik statistika.
   Maqsadlarning to'liq boshqaruvi alohida "goals" bo'limida. */
(function () {
  'use strict';

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }

  App.view('home', {
    nav: 'home',
    render: function (page) {
      page.innerHTML =
        /* Yuqori qator: salomlashuv + o'ng burchakda bildirishnoma qo'ng'irog'i */
        '<div class="h-top">' +
          '<div class="h-hello" id="h-hello"></div>' +
          '<div id="nt-bell-host">' + (window.Notify ? Notify.bellHtml() : '') + '</div>' +
        '</div>' +
        '<div class="rings" id="h-rings"></div>' +
        '<div id="h-lessons"></div>' +
        '<div class="hm-card">' +
          '<div class="hm-head">' +
            '<div class="hm-title"><b id="hm-total">0</b> <span id="hm-period">faollik</span></div>' +
            '<div class="hm-stats"><span>Faol kunlar: <b id="hm-days">0</b></span>' +
            '<span>Eng uzun seriya: <b id="hm-streak">0</b></span></div>' +
          '</div>' +
          '<div class="hm-nav">' +
            '<button class="hm-arrow" data-act="hmBack" aria-label="Oldingi">' +
            '<span data-icon="arrowLeft" data-icon-size="15"></span></button>' +
            '<span class="hm-range" id="hm-range"></span>' +
            '<button class="hm-arrow" data-act="hmFwd" aria-label="Keyingi" id="hm-fwd">' +
            '<span data-icon="arrowLeft" data-icon-size="15" style="transform:rotate(180deg)"></span></button>' +
          '</div>' +
          '<div class="hm-wrap" id="hm-wrap"></div>' +
        '</div>' +
        '<div id="h-widget"></div>';

      App.icons(page);
      renderHello();
      renderLessons();
      if (window.LmsDay) LmsDay.ensureLoaded().then(renderLessons).catch(function () {});
      renderHeatmap();
      renderDailyWidget();
      bindResize();
      mountDrawer();

      var g = (window.Goals && Goals.data && Goals.data.loaded) ? Goals.stats() : { done: 0, total: 0, pct: 0 };
      renderRings(g);
      if (window.Goals && !Goals.data.loaded) {
        Goals.load().then(function () { renderRings(Goals.stats()); }).catch(function () {});
      }
    },
    leave: function () { unbindResize(); stopHello(); unmountDrawer(); }
  });

  /* =========================================================
     O'NG TOMONDAGI TEZKOR TORTMA

     Yozuvlar BO'LIM TILIDA: rus bo'limi — ruscha, ingliz — inglizcha,
     o'zbekcha bo'limlar — o'zbekcha. Shu sabab qaysi bo'limga
     borishi tugmani o'qiganda darrov ayon bo'ladi.
     ========================================================= */
  var SHORTCUTS = [
    { t: 'Грамматика', s: 'Русская грамматика', ic: 'book', c: 'var(--purple)',
      go: { v: 'grammar', p: { lang: 'russian', folder: 'Grammatika' } } },
    { t: 'Словарь', s: 'Русские слова', ic: 'globe', c: 'var(--teal)',
      go: { v: 'vocab', p: { lang: 'russian' } } },
    { t: 'Mening mashqlarim', s: 'Sport', ic: 'check', c: 'var(--accent)',
      go: { v: 'sport_mine' } }
  ];

  var DW = null;

  function unmountDrawer() {
    if (!DW) return;
    document.removeEventListener('click', DW.onDocClick, true);
    DW.el.remove();
    DW = null;
  }

  function mountDrawer() {
    unmountDrawer();
    var el = document.createElement('div');
    el.className = 'hdw';
    el.innerHTML =
      '<button class="hdw-handle" id="hdw-handle" aria-label="Tezkor havolalar"><i></i></button>' +
      '<div class="hdw-panel">' +
        '<div class="hdw-title">Tezkor</div>' +
        SHORTCUTS.map(function (x) {
          return '<button class="hdw-row" data-act="go" data-arg=\'' + App.arg(x.go) + '\'>' +
            '<span class="hdw-ic" style="background:color-mix(in srgb,' + x.c + ' 16%, transparent);color:' + x.c + '">' +
            '<span data-icon="' + x.ic + '" data-icon-size="15"></span></span>' +
            '<span class="hdw-m"><b>' + App.esc(x.t) + '</b><span>' + App.esc(x.s) + '</span></span>' +
            '</button>';
        }).join('') +
      '</div>';
    document.body.appendChild(el);
    App.icons(el);

    var handle = el.querySelector('#hdw-handle');
    var W = function () { return parseFloat(getComputedStyle(el).getPropertyValue('--hdw-w')) || 236; };

    function setOpen(on) { el.classList.toggle('open', !!on); }
    function isOpen() { return el.classList.contains('open'); }

    /* Bosib-tortish: chapga surish ochadi, o'ngga — yopadi. Barmoq/sichqon
       deyarli qimirlamasa oddiy bosish deb hisoblanadi va shunchaki
       almashtiriladi (tortmani ochish uchun aniq tortish shart emas). */
    var drag = null;
    handle.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, base: isOpen() ? 0 : W(), moved: 0 };
      el.classList.add('drag');
      try { handle.setPointerCapture(e.pointerId); } catch (err) {}
    });
    handle.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x;
      drag.moved = Math.max(drag.moved, Math.abs(dx));
      var off = Math.max(0, Math.min(W(), drag.base + dx));
      el.style.transform = 'translateY(-50%) translateX(' + off + 'px)';
    });
    function endDrag(e) {
      if (!drag) return;
      var dx = (e.clientX || 0) - drag.x;
      var off = Math.max(0, Math.min(W(), drag.base + dx));
      el.classList.remove('drag');
      el.style.transform = '';
      setOpen(drag.moved < 6 ? !isOpen() : off < W() / 2);
      drag = null;
    }
    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);

    /* Tashqariga bosilsa yopiladi. `capture` — ichkaridagi `data-act="go"`
       delegatsiyasi hujjat darajasida ishlaydi, undan OLDIN ushlaymiz. */
    function onDocClick(e) {
      if (!DW || !isOpen()) return;
      if (el.contains(e.target)) return;
      setOpen(false);
    }
    document.addEventListener('click', onDocClick, true);

    DW = { el: el, onDocClick: onDocClick };
  }

  /* =========================================================
     QUYOSH HISOBI — chiqish/botish vaqti
     Serverdan yoki API'dan olinmaydi, o'rnida hisoblanadi: internetsiz
     ham ishlaydi va hech qanday joylashuv so'rovi chiqmaydi.
     Algoritm — standart quyosh pozitsiyasi formulasi (SunCalc bilan bir xil).
     Joylashuv: sozlanmagan bo'lsa Toshkent.
     ========================================================= */
  var RAD = Math.PI / 180, DAY_MS = 86400000, J1970 = 2440588, J2000 = 2451545;
  var OBLIQ = RAD * 23.4397;

  function toDays(d) { return d.valueOf() / DAY_MS - 0.5 + J1970 - J2000; }
  function fromJulian(j) { return new Date((j + 0.5 - J1970) * DAY_MS); }

  function sunTimes(date, lat, lng) {
    var lw = RAD * -lng, phi = RAD * lat, d = toDays(date);
    var J0 = 0.0009;
    var n = Math.round(d - J0 - lw / (2 * Math.PI));
    var ds = J0 + (0 + lw) / (2 * Math.PI) + n;
    var M = RAD * (357.5291 + 0.98560028 * ds);
    var C = RAD * (1.9148 * Math.sin(M) + 0.02 * Math.sin(2 * M) + 0.0003 * Math.sin(3 * M));
    var L = M + C + RAD * 102.9372 + Math.PI;
    var dec = Math.asin(Math.sin(OBLIQ) * Math.sin(L));
    var Jnoon = J2000 + ds + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);

    // -0.833° — atmosfera sinishi va quyosh diskining kattaligi hisobga olingan
    var h0 = RAD * -0.833;
    var cosW = (Math.sin(h0) - Math.sin(phi) * Math.sin(dec)) / (Math.cos(phi) * Math.cos(dec));
    if (cosW > 1 || cosW < -1) return null;      // qutb kuni/tuni
    var w = Math.acos(cosW);
    var a = J0 + (w + lw) / (2 * Math.PI) + n;
    var Jset = J2000 + a + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
    var Jrise = Jnoon - (Jset - Jnoon);
    return { rise: fromJulian(Jrise), set: fromJulian(Jset), noon: fromJulian(Jnoon) };
  }

  function geo() {
    var lat = parseFloat(ls('geo_lat', '')), lon = parseFloat(ls('geo_lon', ''));
    if (isFinite(lat) && isFinite(lon)) return { lat: lat, lon: lon };
    return { lat: 41.2995, lon: 69.2401 };       // Toshkent
  }

  function hhmm(d) {
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }
  /* "2 soat 15 daqiqa" / "40 daqiqa" */
  function dur(ms) {
    var m = Math.max(0, Math.round(ms / 60000));
    var h = Math.floor(m / 60); m = m % 60;
    if (h && m) return h + ' soat ' + m + ' daqiqa';
    if (h) return h + ' soat';
    return m + ' daqiqa';
  }

  /* =========================================================
     Salomlashuv + ALMASHIB TURADIGAN quyosh ma'lumoti
     ========================================================= */
  var HELLO_T = null, HELLO_I = 0;

  function helloLines() {
    var now = new Date(), g = geo();
    var t = sunTimes(now, g.lat, g.lon);
    var lines = [];

    if (t) {
      // Ertangi chiqish — bugungisi allaqachon o'tgan bo'lsa kerak bo'ladi
      var tomorrow = new Date(now.getTime() + DAY_MS);
      var t2 = sunTimes(tomorrow, g.lat, g.lon);

      if (now < t.rise) {
        lines.push('Quyosh chiqishiga ' + dur(t.rise - now) + ' bor');
      } else if (now < t.set) {
        lines.push('Quyosh botishiga ' + dur(t.set - now) + ' bor');
        lines.push('Quyosh ' + hhmm(t.rise) + ' da chiqqan');
      } else {
        lines.push('Quyosh ' + hhmm(t.set) + ' da botdi');
        if (t2) lines.push('Quyosh chiqishiga ' + dur(t2.rise - now) + ' bor');
      }
      lines.push('Bugun kunduz ' + dur(t.set - t.rise));
      lines.push('Chiqishi ' + hhmm(t.rise) + ' · botishi ' + hhmm(t.set));
    }

    lines.push(App.uzDate(now));
    return lines;
  }

  /* Salomlashuv ham SOATGA emas, QUYOSHGA qarab tanlanadi — yozda va
     qishda kun uzunligi ancha farq qiladi, qat'iy soat bilan "Xayrli
     kech" quyosh hali tikka turganda ham chiqib qolardi. */
  function greetWord() {
    var now = new Date(), g = geo();
    var t = sunTimes(now, g.lat, g.lon);
    if (!t) {
      var h = now.getHours();
      return h < 5 ? 'Xayrli tun' : h < 12 ? 'Xayrli tong' : h < 18 ? 'Xayrli kun' : 'Xayrli kech';
    }
    var HOUR = 3600000;
    if (now < t.rise - HOUR) return 'Xayrli tun';
    if (now < t.rise + 5 * HOUR) return 'Xayrli tong';
    if (now < t.set - 3 * HOUR) return 'Xayrli kun';
    if (now < t.set + HOUR) return 'Xayrli kech';
    return 'Xayrli tun';
  }

  function renderHello() {
    stopHello();
    var box = App.el('h-hello'); if (!box) return;
    var name = (ls('user_name', '') || '').trim();

    box.innerHTML = '<b id="h-greet"></b><span class="h-sun" id="h-sun"></span>';

    function paint() {
      var g = App.el('h-greet'), s = App.el('h-sun');
      if (!g || !s) { stopHello(); return; }      // sahifa almashgan
      g.textContent = greetWord() + (name ? ', ' + name : '');
      var lines = helloLines();
      HELLO_I = HELLO_I % lines.length;
      s.textContent = lines[HELLO_I];
      s.classList.remove('in');
      void s.offsetWidth;                          // animatsiyani qayta boshlash
      s.classList.add('in');
    }

    paint();
    /* Har 6 soniyada keyingi xabar. Bo'limdan chiqilganda `leave` ilagi
       to'xtatadi — aks holda taymer fonda ishlab yuraverardi. */
    HELLO_T = setInterval(function () { HELLO_I++; paint(); }, 6000);
  }

  function stopHello() {
    if (HELLO_T) { clearInterval(HELLO_T); HELLO_T = null; }
  }

  /* ---------- Halqali ko'rsatkichlar ---------- */
  function ringSvg(pct, color) {
    var r = 22, c = 2 * Math.PI * r;
    var on = Math.max(0, Math.min(100, pct)) / 100 * c;
    return '<svg viewBox="0 0 52 52">' +
      '<circle class="bgc" cx="26" cy="26" r="' + r + '" fill="none" stroke-width="5"></circle>' +
      '<circle class="fgc" cx="26" cy="26" r="' + r + '" fill="none" stroke-width="5" ' +
      'style="stroke:' + color + '" stroke-dasharray="' + on.toFixed(1) + ' ' + c.toFixed(1) + '"></circle>' +
      '</svg>';
  }
  function renderRings(g) {
    var box = App.el('h-rings'); if (!box) return;
    var streak = (window.Activity && Activity.streak) ? Activity.streak() : 0;
    // Seriya halqasi 30 kunlik maqsadga nisbatan to'ladi
    var sPct = Math.min(100, Math.round((streak / 30) * 100));
    box.innerHTML =
      '<div class="ring-card">' +
        '<div class="ring">' + ringSvg(g.pct, 'var(--accent)') +
          '<div class="ring-mid">' + g.pct + '%</div></div>' +
        '<div class="ring-lb"><b>' + g.done + '/' + g.total + '</b><span>Maqsad</span></div>' +
      '</div>' +
      '<div class="ring-card">' +
        '<div class="ring">' + ringSvg(sPct, 'var(--warn)') +
          '<div class="ring-mid">' + (streak || '·') + '</div></div>' +
        '<div class="ring-lb"><b>' + (streak ? streak + ' kun' : 'Boshlang') + '</b><span>Ketma-ket</span></div>' +
      '</div>';
  }

  /* ---------- Bugungi darslar ---------- */
  function nowMins() { var d = new Date(); return d.getHours() * 60 + d.getMinutes(); }
  function toMins(t) { var p = String(t || '').split(':'); return (+p[0] || 0) * 60 + (+p[1] || 0); }

  function renderLessons() {
    var box = App.el('h-lessons'); if (!box) return;
    if (!window.Kun || !Kun.dayLessons) { box.innerHTML = ''; return; }
    var list = [];
    try { list = Kun.dayLessons(); } catch (e) { list = []; }
    if (!list.length) { box.innerHTML = ''; return; }

    var n = nowMins();
    box.innerHTML =
      '<div class="hsec"><h2>Bugungi reja</h2>' +
      '<button class="lnk" data-act="go" data-arg=\'{"v":"kun"}\'>Kun hisobi</button></div>' +
      list.map(function (l) {
        var live = n >= toMins(l.start) && n < toMins(l.end);
        var past = n >= toMins(l.end);
        return '<div class="les' + (live ? ' now' : '') + (past ? ' past' : '') + (l.done ? ' done' : '') + '">' +
          '<div class="les-t">' + App.esc(l.start) + '<br>' + App.esc(l.end) + '</div>' +
          '<div class="les-bar" style="background:' + (l.color || 'var(--accent)') + '"></div>' +
          '<div class="les-m"><b>' + App.esc(l.subject) + '</b>' +
          '<span>' + App.esc(l.room || '') + (live ? ' · hozir' : '') + '</span></div>' +
          '</div>';
      }).join('');
  }

  /* Nechta oy ORQAGA surilgan (0 = joriy oygacha) — eski tarixni ko'rish uchun. */
  var HM_OFFSET = 0;
  // Qadam — ko'rinayotgan oyna kengligiga teng (telefonda 6, desktopda 12)
  App.actions.hmBack = function () { HM_OFFSET += monthsToShow(); renderHeatmap(); };
  App.actions.hmFwd = function () {
    HM_OFFSET = Math.max(0, HM_OFFSET - monthsToShow());
    renderHeatmap();
  };

  /* Ekran o'lchami o'zgarganda qator soni ham o'zgaradi — qayta chizamiz. */
  var RESIZE_T = null;
  function onResize() {
    clearTimeout(RESIZE_T);
    RESIZE_T = setTimeout(function () { if (App.el('hm-wrap')) renderHeatmap(); }, 200);
  }
  function bindResize() { window.addEventListener('resize', onResize); }
  function unbindResize() { window.removeEventListener('resize', onResize); clearTimeout(RESIZE_T); }

  /* Bo'shliqlar tor ekranda kichikroq — shu hisobga kataklar kattaroq chiqadi.
     (`.hm-row` gap'i CSS'da ham shu qiymatlarga mos bo'lishi kerak.) */
  function gaps() {
    var narrow = (window.innerWidth || 1024) < 700;
    return { cell: narrow ? 2 : 3, month: narrow ? 4 : 6 };
  }

  /* Nechta oy ko'rsatiladi.
     Telefonda 6 oy — bu ekranga TO'LIQ sig'adi, ya'ni na siljitish, na
     karusel kerak (foydalanuvchi so'rovi). Kengroq ekranda 12 oy.
     Eski oylarni ko'rish uchun tepadagi ← → strelkalari bor — ular
     ko'rinayotgan oyna qadamiga teng suradi. */
  function monthsToShow() {
    var w = window.innerWidth || 1024;
    return w < 700 ? 6 : 12;
  }

  /* ---------- Faollik heatmap: bitta qator (LeetCode uslubi) ----------
     Oylar ALOHIDA bloklar — oralarida bo'shliq, oy nomi blok ostida.
     Katak o'lchami JS'da hisoblanadi (CSS `1fr` emas): ko'rsatilayotgan
     oylar soni mavjud enga qarab tanlangani uchun hammasi doim sig'adi.

     Katak RANGI Boostday kunlik vazifalar foizidan (`Activity.dailyStats`)
     keladi — "faol kunmi" (streak/umumiy son) esa hamon eski
     `activity_days_v1`dan (istalgan bo'limdagi ish, Boostday'ga bog'liq
     emas). Ikkalasi ATAYLAB alohida: rang darajasi FAQAT foydalanuvchi
     so'ragan "vazifalar necha % bajarildi" ma'nosini bersin. */
  function renderHeatmap() {
    var wrap = App.el('hm-wrap'); if (!wrap) return;
    Activity.dailyStats().then(function (statsMap) {
      if (App.el('hm-wrap')) paintHeatmap(statsMap || {});
    });
  }

  /* 0-70% orasi rang bermaydi (yopiq/neytral), 50% dan boshlab 4 daraja:
       50-69%  — miltillovchi ko'k (e'tibor tortish uchun)
       70-79%  — ko'kimtir (och ko'k)
       80-99%  — ko'k
       100%    — ko'm-ko'k (eng to'q) */
  function heatLevel(pct) {
    if (pct >= 100) return 4;
    if (pct >= 80) return 3;
    if (pct >= 70) return 2;
    if (pct >= 50) return 1;
    return 0;
  }

  function paintHeatmap(statsMap) {
    var wrap = App.el('hm-wrap'); if (!wrap) return;
    var set = {};
    try {
      (JSON.parse(ls('activity_days_v1', '[]')) || []).forEach(function (d) { set[d] = true; });
    } catch (e) {}

    function key(d) {
      return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
             String(d.getDate()).padStart(2, '0');
    }

    var MON = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyn', 'Iyl', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek'];
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var todayKey = key(today);

    // Ko'rsatiladigan oylar: joriy oy oxirgi bo'ladi
    var SHOW = monthsToShow();
    var months = [];
    for (var m = SHOW - 1; m >= 0; m--) {
      var d = new Date(today.getFullYear(), today.getMonth() - m - HM_OFFSET, 1);
      months.push({ y: d.getFullYear(), m: d.getMonth() });
    }

    /* Oy necha ustunga (haftaga) bo'linadi */
    function colsOf(mo) {
      var first = new Date(mo.y, mo.m, 1);
      var last = new Date(mo.y, mo.m + 1, 0);
      return Math.ceil((first.getDay() + last.getDate()) / 7);
    }

    /* Katak o'lchami — mavjud enni ANIQ formula bilan bo'lamiz. Umumiy en:
         cell*totalCols + cellGap*(totalCols - oylarSoni) + monthGap*(oylar-1)
       (har oy ichida `cols-1` ta katak oralig'i bor). Taxminiy bo'lish
       o'nlab piksel behuda ketkazardi — katak allaqachon kichkina bo'lgani
       uchun har piksel muhim. Oylar soni ekranga qarab tanlangani uchun
       natija DOIM sig'adi: siljitish/karusel yo'q. */
    var G = gaps();
    var CELL_GAP = G.cell, MONTH_GAP = G.month;
    var n = months.length;
    var totalCols = months.reduce(function (a, mo) { return a + colsOf(mo); }, 0);
    var w = wrap.clientWidth;
    var cell = Math.floor((w - CELL_GAP * (totalCols - n) - MONTH_GAP * (n - 1)) / totalCols);
    if (!isFinite(cell) || cell < 6) cell = 6;   // o'qib bo'ladigan eng kichik
    if (cell > 26) cell = 26;                    // keng ekranda cho'zilmasin

    /* Birinchi chizishda sahifa hali joylashmagan bo'lishi mumkin — o'shanda
       `clientWidth` haqiqiy kenglikni bermaydi va katak keraksiz kichik
       chiqadi. Shubhali bo'lsa keyingi kadrda qayta chizamiz. */
    if (w < 80) { setTimeout(renderHeatmap, 60); }

    function monthHtml(mo) {
      var first = new Date(mo.y, mo.m, 1);
      var last = new Date(mo.y, mo.m + 1, 0);
      var cols = colsOf(mo);

      // Ustun × qator kataklari; oyga tegishli bo'lmagan katak bo'sh
      var cells = [];
      for (var c = 0; c < cols; c++) {
        for (var r = 0; r < 7; r++) {
          var dayNum = c * 7 + r - first.getDay() + 1;
          if (dayNum < 1 || dayNum > last.getDate()) { cells.push(null); continue; }
          cells.push(new Date(mo.y, mo.m, dayNum));
        }
      }

      var inner = cells.map(function (d) {
        if (!d) return '<i class="pad"></i>';
        var k = key(d);
        if (d > today) return '<i class="fut"></i>';
        var st = statsMap[k];
        var pct = st ? st.percent : 0;
        var lvl = heatLevel(pct);
        var cls = [];
        if (k === todayKey) cls.push('now');
        if (lvl === 1) cls.push('blink');
        var title = st && st.total
          ? k + ' — ' + pct + '% (' + st.completed + '/' + st.total + ')'
          : k;
        return '<i data-l="' + lvl + '"' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') +
               ' title="' + App.esc(title) + '" style="cursor:pointer" data-act="go" data-arg=\'' + App.arg({ v: 'tarix_day', p: { date: k } }) + '\'></i>';
      }).join('');

      return '<div class="hm-mo">' +
             '<div class="hm-mo-grid" style="gap:' + CELL_GAP + 'px;' +
             'grid-template-columns:repeat(' + cols + ',' + cell + 'px);' +
             'grid-template-rows:repeat(7,' + cell + 'px)">' +
             inner + '</div>' +
             '<div class="hm-mo-lb">' + MON[mo.m] + '</div></div>';
    }

    // Bitta qator, to'liq sig'adi — siljitish yo'q
    wrap.innerHTML = '<div class="hm-row" id="hm-row" style="gap:' + MONTH_GAP + 'px">' +
                     months.map(monthHtml).join('') + '</div>';

    // Statistika — KO'RSATILAYOTGAN oylar oralig'i bo'yicha
    var active = 0, streak = 0, best = 0;
    var from = new Date(months[0].y, months[0].m, 1);
    for (var d2 = new Date(from); d2 <= today; d2.setDate(d2.getDate() + 1)) {
      if (set[key(d2)]) { active++; streak++; if (streak > best) best = streak; }
      else { streak = 0; }
    }

    App.el('hm-total').textContent = active;
    App.el('hm-days').textContent = active;
    App.el('hm-streak').textContent = best;
    // Sarlavha ko'rsatilayotgan davrga mos bo'lsin ("oxirgi bir yilda" emas)
    var lbl = App.el('hm-period');
    if (lbl) lbl.textContent = 'faollik — oxirgi ' + SHOW + ' oyda';
    App.el('hm-range').textContent = MON[months[0].m] + ' ' + months[0].y + ' — ' +
      MON[months[months.length - 1].m] + ' ' + months[months.length - 1].y;
    var fw = App.el('hm-fwd');
    if (fw) {
      fw.style.opacity = HM_OFFSET === 0 ? '0.3' : '1';
      fw.style.pointerEvents = HM_OFFSET === 0 ? 'none' : 'auto';
    }
  }

  /* ---------- Kunlik statistika ----------
     MUHIM: raqamlar boshqa modullarning OMMAVIY API'sidan olinadi
     (BoostDay.dayGroups) — localStorage'ni to'g'ridan-to'g'ri o'qish
     EMAS. Ilgari shu yerda `boost_tasks_v1`/`kun_log_v1`/`sport_data_v1`
     kabi MAVJUD BO'LMAGAN kalitlar o'qilgani uchun hamma ko'rsatkich doim
     0 bo'lib turardi. */
  function renderDailyWidget() {
    var box = App.el('h-widget'); if (!box) return;

    box.innerHTML = '<div class="hsec" style="margin-top:24px"><h2>Kunlik statistika</h2></div>' +
      '<div class="load-wrap"><div class="spinner"></div></div>';

    var d = new Date();
    var ymd = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    var dayOfWeek = d.getDay();

    var boot = [];
    // Faqat Boostday kerak — vidjet endi sport ma'lumotini ishlatmaydi
    if (window.BoostDay) boot.push(window.BoostDay.ensureLoaded());

    /* Bitta halqa. Tuzilishi ATAYLAB bir xil — telefonda ham, kompyuterda
       ham AYNI markup ishlatiladi, farqni faqat CSS qiladi:
         telefon  — halqa tepada, nomi ostida (markazlangan)
         kompyuter — halqa nom bilan BIR QATORDA (chapda), ostida vazifalar
       Ilgari halqa matn ustida "yolg'iz" suzib turardi va ustunlar turli
       balandlikda tugab, o'ng tomon tarqoq ko'rinardi. */
    /* O'lcham ATAYLAB berilmaydi — SVG normallashtirilgan 100 birlikli
       viewBox'da chiziladi va HAQIQIY o'lchamni CSS beradi. Shu sabab bir
       xil markup telefonda katta (54px), kompyuterda ixcham (44px) halqa
       bo'lib chiqadi va nom uchun joy qoladi (ilgari o'lcham inline
       yozilgani uchun kompyuterda nom qisqarib ketardi). */
    function mkRing(pct, color, label, valLabel, arg, items) {
      var STROKE = 9;                        // 100 birlikdan
      var r = (100 - STROKE) / 2;
      var c = 2 * Math.PI * r;
      var on = Math.max(0, Math.min(100, pct)) / 100 * c;

      var detail = '';
      if (items && items.length) {
        var MAX = 6;
        detail = '<div class="wd-detail">' +
          items.slice(0, MAX).map(function (t) {
            var txt = App.normTaskName(t.text);
            return '<div class="wd-ditem' + (t.done ? ' done' : '') + '" title="' + App.esc(txt) + '">' +
              (t.done ? '<span class="wd-tick" data-icon="check" data-icon-size="11"></span>'
                      : '<i class="wd-dot" style="border-color:' + color + '"></i>') +
              '<span class="wd-dtxt">' + App.esc(txt) + '</span></div>';
          }).join('') +
          (items.length > MAX ? '<div class="wd-ditem more">+' + (items.length - MAX) + ' ko\'proq</div>' : '') +
          '</div>';
      }

      /* `--wd-c` — bo'lim rangi. Kompyuterda ustunning chap chekkasidagi
         nozik belgi shu rangda bo'ladi (halqa bilan bir xil), shu sabab
         ustunlar orasiga alohida ajratgich chiziq kerak emas — guruhlar
         ko'p bo'lib ikkinchi qatorga o'ralganda ham chalkashmaydi. */
      return '<div class="wd-ring" style="--wd-c:' + color +
        (arg ? ';cursor:pointer"' + ' data-act="go" data-arg=\'' + App.arg(arg) + '\'' : '"') + '>' +
        '<div class="wd-head">' +
          '<div class="wd-ring-svg">' +
          '<svg viewBox="0 0 100 100">' +
          '<circle cx="50" cy="50" r="' + r + '" fill="none" stroke="var(--border)" stroke-width="' + STROKE + '"></circle>' +
          '<circle cx="50" cy="50" r="' + r + '" fill="none" stroke="' + color +
          '" stroke-width="' + STROKE + '" stroke-linecap="round" stroke-dasharray="' + on.toFixed(1) + ' ' + c.toFixed(1) + '"></circle>' +
          '</svg>' +
          '<div class="wd-ring-mid">' + pct + '%</div>' +
          '</div>' +
          '<div class="wd-meta">' +
            '<div class="wd-lbl">' + App.esc(label) + '</div>' +
            '<div class="wd-val">' + App.esc(valLabel) + '</div>' +
          '</div>' +
        '</div>' +
        detail +
        '</div>';
    }

    /* Halqalar: chapda bitta katta UMUMIY, o'ngda har bir bo'lim uchun
       kichkinasi. Bo'limlar — botda kiritilgan GURUHLAR + Sport.
       ("Jadval" va yagona "Boostday" halqalari olib tashlandi: ular bir
       xil ishni ikki marta ko'rsatardi.) */
    /* Har bo'limga O'Z rangi. Ilgari `p.color` (reja TURI rangi) ustun edi —
       bitta rejadagi hamma guruh bir xil rang olardi, natijada uchala halqa
       ham bir xil yashil chiqib, bo'limlarni bir-biridan ajratib bo'lmasdi. */
    var RING_COLORS = ['var(--purple)', 'var(--success)', 'var(--coral)', 'var(--warn)', 'var(--accent)'];

    function paint(parts) {
      var totalTasks = 0, doneTasks = 0;
      parts.forEach(function (p) { totalTasks += p.total; doneTasks += p.done; });
      var pct = function (a, b) { return b ? Math.round((a / b) * 100) : 0; };

      var subs = parts.length
        ? parts.map(function (p, i) {
            return mkRing(pct(p.done, p.total), RING_COLORS[i % RING_COLORS.length],
                          p.name, p.done + '/' + p.total, p.go, p.items);
          }).join('')
        : '<p class="wd-empty">Botda reja kiritilmagan</p>';

      /* UMUMIY ko'rsatkich ikki ko'rinishda chiziladi, ikkalasi ham
         markupda turadi va kerakligini CSS tanlaydi:
           telefon   — katta halqa (`.wd-ring`), avvalgidek
           kompyuter — tepada butun kenglikdagi CHIZIQ (`.wd-line`);
                       shunda ustunlarga butun kenglik qoladi. */
      var allPct = pct(doneTasks, totalTasks);
      box.innerHTML =
        '<div class="hsec" style="margin-top:24px"><h2>Kunlik statistika</h2></div>' +
        '<div class="wd-card">' +
          '<div class="wd-main">' +
            /* KUNLIK ODATLAR halqasi (habits.js) — `wd-main` NING ICHIDA
               turadi, shuning uchun kompyuterda "Umumiy kun" qatori bilan
               yonma-yon joylashadi va ustma-ust tushmaydi. Odat bo'lmasa
               bo'sh qoladi va CSS uni butunlay yashiradi (`:empty`). */
            '<div id="hb-slot" class="hb-slot"></div>' +
            mkRing(allPct, 'var(--accent)', 'Umumiy kun', doneTasks + ' / ' + totalTasks + ' vazifa') +
            '<div class="wd-line">' +
              '<div class="wd-line-top">' +
                '<b>Umumiy kun</b>' +
                '<span>' + doneTasks + ' / ' + totalTasks + ' vazifa</span>' +
                '<em>' + allPct + '%</em>' +
              '</div>' +
              '<div class="wd-bar"><i style="width:' + allPct + '%"></i></div>' +
            '</div>' +
          '</div>' +
          '<div class="wd-sub">' + subs + '</div>' +
        '</div>';
      App.icons(box);
      paintHabitRing();
    }

    /* Odatlar halqasi MUSTAQIL yuklanadi — bot javobi kechiksa ham
       kunlik statistika kutib turmaydi. Yuklanmasa halqa umuman
       ko'rinmaydi (bo'sh joy qolmaydi). */
    function paintHabitRing() {
      var slot = App.el('hb-slot');
      if (!slot || !window.Habits) return;
      Habits.ensureLoaded().then(function (list) {
        var s = App.el('hb-slot'); if (!s) return;
        var st = Habits.stat(list);
        s.innerHTML = st.total ? Habits.ringHtml(st) : '';
        App.icons(s);
      }).catch(function () {});
    }
    window.Home = window.Home || {};
    window.Home.refreshHabits = paintHabitRing;

    Promise.all(boot).then(function () {
      var parts = [];

      /* FAQAT botda kiritilgan guruhlar. Alohida "Sport" halqasi ATAYLAB
         yo'q: foydalanuvchi mashqlarni doim bot orqali qo'shadi, shuning
         uchun ular allaqachon o'z guruhida sanaladi — ikkinchi halqa
         qo'shilsa bitta ish ikki joyda ko'rinardi. */
      if (window.BoostDay && BoostDay.dayGroups) {
        try {
          BoostDay.dayGroups(ymd, dayOfWeek).forEach(function (g) {
            if (g.total) parts.push({ name: g.name, total: g.total, done: g.done, color: g.color, go: { v: 'boost' }, items: g.items });
          });
        } catch (e) {}
      }

      paint(parts);
    }).catch(function () { paint([]); });
  }

})();
