/* Maqsadlar (deadline bilan) va Statistika bo'limlari.

   Statistika butun ilovadan ma'lumot yig'adi:
     - Maqsadlar        -> Goals.stats()
     - Testlar          -> get_structure + quiz natijalari (localStorage keshi)
     - Lug'at           -> get_dict_data (har ikki til) + SRS holati
     - Sport            -> sport_get_all + sport_log_v1
     - Grammatika       -> get_topics (english/russian/coding)
     - Faollik          -> activity_days_v1
   Har blok MUSTAQIL yuklanadi: bittasi yiqilsa qolgani baribir chiqadi. */
(function () {
  'use strict';

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function jls(k, d) { try { return JSON.parse(ls(k, '')) || d; } catch (e) { return d; } }

  /* Sport tarixi — sport.js MASSIV sifatida yozadi: [{d, cat, id, name, ...}].
     (Ilgari bu yerda kun-kalitli obyekt deb o'qilardi va grafikda mashq nomi
     o'rniga maydon nomlari — d/cat/id — chiqib qolardi.) */
  function sportLog() {
    var v = jls('sport_log_v1', []);
    return Array.isArray(v) ? v : [];
  }

  function topbar(title, right) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'>' +
      '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:26px;height:26px;border-radius:7px;object-fit:cover;flex-shrink:0;margin-right:6px">' +
      '<h1>' + App.esc(title) + '</h1>' + (right || '') + '</div>';
  }

  /* =========================================================
     MAQSADLAR — maqsadlar ro'yxati + deadlinelar
     ========================================================= */
  function dls() { return jls('home_deadlines_v1', []); }

  function upcoming() {
    var now = new Date(); now.setHours(0, 0, 0, 0);
    return dls().filter(function (d) { return d.end && d.status !== 'done'; })
      .map(function (d) {
        return { id: d.id, name: d.name, start: d.start, end: d.end,
                 days: Math.ceil((new Date(d.end) - now) / 86400000) };
      })
      .sort(function (a, b) { return a.days - b.days; });
  }

  function renderDeadlines() {
    var box = App.el('g-dl'); if (!box) return;
    var list = upcoming();
    if (!list.length) {
      box.innerHTML = '<p class="muted" style="font-size:13px;margin:2px 1px 10px">Deadline yo\'q</p>';
      return;
    }
    var now = new Date(); now.setHours(0, 0, 0, 0);
    box.innerHTML = list.map(function (d) {
      var end = new Date(d.end), start = d.start ? new Date(d.start) : null;
      var pct = 0;
      if (start && end > start) {
        pct = Math.max(0, Math.min(100, Math.round(((now - start) / (end - start)) * 100)));
      }
      var otdi = d.days < 0;
      var soon = d.days >= 0 && d.days <= 7;
      var badge = otdi ? 'muddati o\'tdi' : d.days + ' kun';
      return '<div class="dl2">' +
        '<div class="dl2-top"><div class="dl2-n">' + App.esc(d.name) + '</div>' +
        '<div class="dl2-d' + (soon || otdi ? ' soon' : '') + '">' + badge + '</div></div>' +
        '<div class="dl2-track"><div class="dl2-fill' + (soon || otdi ? ' soon' : '') +
        '" style="width:' + (otdi ? 100 : pct) + '%"></div></div>' +
        '<div class="dl2-sub"><span>' + App.esc(App.uzDate(d.start) || '—') + '</span>' +
        '<span>' + (otdi ? '100' : pct) + '%</span>' +
        '<span>' + App.esc(App.uzDate(d.end)) + '</span></div>' +
        // O'chirish/tahrirlash FAQAT Sozlamalarda — bu yerda ko'rsatilmaydi
        '</div>';
    }).join('');
  }

  App.view('goals', {
    nav: 'goals',
    render: function (page) {
      page.innerHTML =
        topbar('Maqsadlar',
          '<button class="icon-btn ghost" data-act="goalAdd" aria-label="Maqsad qo\'shish">' +
          '<span data-icon="plus" data-icon-size="20"></span></button>') +

        '<div class="rings" id="g-rings"></div>' +

        '<div class="hsec"><h2>Deadlinelar</h2>' +
        '<button class="lnk" data-act="addDeadline">+ Qo\'shish</button></div>' +
        '<div id="g-dl"></div>' +

        '<div class="hsec"><h2>Maqsadlar</h2></div>' +
        '<div id="g-list"><div class="load-wrap"><div class="spinner"></div></div></div>';

      App.icons(page);
      renderDeadlines();
      renderGoalRings();

      var box = App.el('g-list');
      if (!window.Goals) { box.innerHTML = ''; return; }
      if (Goals.data.loaded) { Goals.renderInto(box); renderGoalRings(); }
      else {
        Goals.load().then(function () {
          if (App.el('g-list')) Goals.renderInto(App.el('g-list'));
          renderGoalRings();
        }).catch(function (e) {
          if (App.el('g-list')) App.el('g-list').innerHTML =
            App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
        });
      }
    }
  });

  function ring(pct, color, mid) {
    var r = 22, c = 2 * Math.PI * r;
    var on = Math.max(0, Math.min(100, pct)) / 100 * c;
    return '<div class="ring"><svg viewBox="0 0 52 52">' +
      '<circle class="bgc" cx="26" cy="26" r="' + r + '" fill="none" stroke-width="5"></circle>' +
      '<circle class="fgc" cx="26" cy="26" r="' + r + '" fill="none" stroke-width="5" ' +
      'style="stroke:' + color + '" stroke-dasharray="' + on.toFixed(1) + ' ' + c.toFixed(1) + '"></circle>' +
      '</svg><div class="ring-mid">' + mid + '</div></div>';
  }

  function renderGoalRings() {
    var box = App.el('g-rings'); if (!box) return;
    var loaded = window.Goals && Goals.data && Goals.data.loaded;
    var d = upcoming();
    var yaqin = d.filter(function (x) { return x.days >= 0 && x.days <= 7; }).length;

    /* Maqsadlar halqasi hajm (Katta/O'rta/Kichik) bo'yicha 3 rangga bo'linadi,
       yonida taqsimot. Deadline halqasi avvalgidek. */
    var goalsPanel = (loaded && window.GoalSizes)
      ? GoalSizes.panel().replace('margin:2px 1px 16px', 'flex:1;margin:0;padding:14px;background:var(--card);border:1px solid var(--border-soft);border-radius:var(--radius);')
      : '<div class="ring-card" style="flex:1">' + ring(0, 'var(--accent)', '0%') +
        '<div class="ring-lb"><b>—</b><span>Maqsad</span></div></div>';

    box.innerHTML = goalsPanel +
      '<div class="ring-card" style="flex:1">' + ring(d.length ? 100 : 0, 'var(--warn)', String(d.length)) +
        '<div class="ring-lb"><b>' + (yaqin ? yaqin + ' ta yaqin' : 'Muddat bor') + '</b><span>Deadline</span></div></div>';
  }


  /* =========================================================
     CHIZIQLI GRAFIK (SVG, kutubxonasiz — oflaynda ham ishlaydi)
     series: [{ nom, rang, nuqtalar: {'YYYY-MM-DD': son} }]
     ========================================================= */
  var UZ_MON = ['yan','fev','mar','apr','may','iyn','iyl','avg','sen','okt','noy','dek'];

  /* Grafik chapga tortilganda ORQAGA qancha kun ko'rish mumkin.
     MA'LUMOT so'rovlari ham AYNI shu oynani so'rashi shart — aks holda
     chetdan tashqarisi ma'lumotsiz qolib, grafikda soxta 0 chiziladi
     (`activityLog()` ga qarang). */
  var CHART_HISTORY_DAYS = 400;

  function dayKey(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
           String(d.getDate()).padStart(2, '0');
  }

  /* markers: [{ sana, rang, matn }] — chiziqdan mustaqil, X o'qi ustida
     ko'rinadigan nuqtalar (deadline muddati, bajarilgan maqsad va h.k.) */
  /* Grafik endi CHAPGA TORTIB (sichqoncha yoki barmoq bilan) orqaga —
     eski kunlarga — surilishi mumkin. Buning uchun `days` (14/30/90
     tugmasi) bilan bir xil ZICHLIKDA, lekin ANCHA UZUNROQ jadval chiziladi
     (HIST_DAYS), so'ng u gorizontal skrollanadigan konteynerga joylanadi va
     boshlang'ich holatda "Bugun" o'ng chetda ko'rinadigan qilib oxiriga
     suriladi (paintChart funksiyasi). SVG endi butun (100%) emas, ANIQ
     piksel kengligida chiziladi — aks holda skroll qilishning ma'nosi
     qolmasdi (butun jadval konteynerga siqib joylashtirilgan bo'lardi). */
  function lineChart(series, days, markers, opts) {
    opts = opts || { type: localStorage.getItem('chart_type') || 'line' };
    var H = 250, L = 8, R = 46, T = 14, B = 26;   // chekka bo'shliqlar
    var today = new Date(); today.setHours(0, 0, 0, 0);

    var HIST_DAYS = Math.max(days, CHART_HISTORY_DAYS);
    var perDay = (700 - L - R) / Math.max(1, days - 1);   // avvalgi zichlik saqlanadi
    /* Bugundan KEYIN ham kunlar chiziladi — shuning uchun "Bugun"ni
       ko'rinadigan oyna MARKAZIGA surish mumkin bo'ladi (`paintChart`).
       Standart holatda `opts.futureDays` chaqiruvchidan keladi: u haqiqiy
       konteyner kengligidan hisoblanadi (`fitFutureDays`), shu sabab har
       qanday ekran o'lchamida markazlash aniq chiqadi. Berilmasa — kichik
       standart qiymat (masalan konteyner hali o'lchanmagan bo'lsa). */
    var FUTURE_DAYS = opts.futureDays || 3;
    var TOTAL = HIST_DAYS + FUTURE_DAYS;
    var innerW = perDay * (TOTAL - 1);
    var W = L + R + innerW;

    /* Sanalar o'qi: o'tmish -> BUGUN -> bir necha kun kelajak.
       `todayIdx` — bugungi kunning ro'yxatdagi o'rni (oxirgisi EMAS). */
    var dates = [];
    for (var i = HIST_DAYS - 1; i >= -FUTURE_DAYS; i--) {
      var d = new Date(today); d.setDate(today.getDate() - i);
      dates.push(d);
    }
    var todayIdx = HIST_DAYS - 1;

    // Eng katta qiymat -> Y masshtabi (0 bo'lsa ham grafik ko'rinsin)
    var max = 0;
    series.forEach(function (s) {
      dates.forEach(function (d) { var v = s.nuqtalar[dayKey(d)] || 0; if (v > max) max = v; });
    });
    if (max <= 0) max = 1;
    var LINES = 4;
    var raw = max / LINES;
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var mult = [1, 2, 2.5, 5, 10].filter(function (m) { return mag * m >= raw; })[0] || 10;
    var niceStep = mag * mult;
    var top = niceStep * LINES;

    var innerH = H - T - B;
    var x = function (i) { return L + i * perDay; };
    var y = function (v) { return T + innerH - (v / top) * innerH; };

    // To'r chiziqlari + Y yozuvlari
    var grid = '';
    for (var g = 0; g <= LINES; g++) {
      var val = top * g / LINES, gy = y(val);
      grid += '<line x1="' + L + '" y1="' + gy.toFixed(1) + '" x2="' + (W - R) + '" y2="' + gy.toFixed(1) +
              '" class="ch-grid"/>' +
              '<text x="' + (W - R + 8) + '" y="' + (gy + 3.5).toFixed(1) + '" class="ch-ylb">' +
              (val >= 1000 ? (val / 1000) + 'k' : Math.round(val)) + '</text>';
    }

    /* X yozuvlari.
       Ilgari butun oyna uchun atigi ~4 ta yozuv chiqardi — surilganda
       qayerdaligini bilish qiyin edi. Endi joy yetgancha ZICH: qadam
       yozuvlar bir-biriga tegmaydigan eng kichik qiymatdan olinadi.

       Qadam BUGUNDAN sanaladi, shuning uchun bugungi kun HAR DOIM
       yozuvli bo'ladi va uning atrofi "Kecha / Bugun / Ertaga" deb
       o'qiladi — sana raqamini qidirib o'tirmaysiz. */
    var xlb = '';
    var GAP = 30;                                   // yozuvlar orasidagi eng kichik masofa (px)
    var stepX = Math.max(1, Math.ceil(GAP / perDay));
    // So'z-yozuvlar ("Kecha"/"Ertaga") raqamdan kengroq — joy tor bo'lsa ishlatilmaydi
    var wordsFit = perDay * stepX >= 38 && perDay >= 18;

    /* Avval "Bugun" atrofi: qadam bir necha kunlik bo'lsa ham, Kecha/
       Bugun/Ertaga UCHALASI ham alohida ko'rsatiladi — muntazam qadam
       ularni chetlab o'tishi mumkin edi. */
    var used = {};
    function put(xi, txt, extraCls) {
      if (xi < 0 || xi >= dates.length || used[xi]) return;
      used[xi] = true;
      xlb += '<text x="' + x(xi).toFixed(1) + '" y="' + (H - 8) + '" class="ch-xlb' +
             (extraCls || '') + '">' + App.esc(txt) + '</text>';
    }
    put(todayIdx, 'Bugun', ' ch-xlb-today');
    if (wordsFit) { put(todayIdx - 1, 'Kecha'); put(todayIdx + 1, 'Ertaga'); }

    /* Qolgan o'q — muntazam qadam, "Bugun" atrofidagilar bilan
       to'qnashmasligi uchun band qilingan o'rinlar o'tkazib yuboriladi. */
    for (var xi = todayIdx % stepX; xi < dates.length; xi += stepX) {
      if (used[xi]) continue;
      var dd = dates[xi];
      var txt = (dd.getDate() === 1) ? UZ_MON[dd.getMonth()] : String(dd.getDate());
      put(xi, txt);
    }

    // Chiziqlar yoxud ustunlar (Bar)
    var paths = '';
    series.forEach(function (s, si) {
      var barW = Math.max(2, perDay * 0.4);
      var pts = [];
      dates.forEach(function (d, i) {
        var v = s.nuqtalar[dayKey(d)] || 0;
        var cx = x(i);
        var cy = y(v);
        pts.push(cx.toFixed(1) + ',' + cy.toFixed(1));

        // Agar BAR bo'lsa
        if (opts.type === 'bar') {
          var ox = cx - (series.length * barW) / 2 + (si * barW);
          var h = y(0) - cy;
          if (h > 0) {
            paths += '<rect x="' + ox.toFixed(1) + '" y="' + cy.toFixed(1) + '" width="' + barW.toFixed(1) + '" height="' + h.toFixed(1) + '" fill="' + s.rang + '" rx="2" ry="2"><title>' + dayKey(d) + ' — ' + s.nom + ': ' + v + '</title></rect>';
          }
        }
      });

      if (opts.type !== 'bar') {
        var pStr = pts.join(' ');
        var areaPts = L + ',' + y(0).toFixed(1) + ' ' + pStr + ' ' + x(dates.length - 1).toFixed(1) + ',' + y(0).toFixed(1);
        paths += '<polygon points="' + areaPts + '" fill="' + s.rang + '1a" />' +
                 '<polyline points="' + pStr + '" fill="none" stroke="' + s.rang +
                 '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>';
        // Nuqtalar
        dates.forEach(function (d, i) {
          var v = s.nuqtalar[dayKey(d)] || 0;
          if (v) {
            paths += '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="3" fill="' + s.rang +
                     '"><title>' + dayKey(d) + ' — ' + s.nom + ': ' + v + '</title></circle>';
          }
        });
      }
    });

    var legend = series.map(function (s) {
      return '<span class="ch-lg"><i style="background:' + s.rang + '"></i>' + App.esc(s.nom) + '</span>';
    }).join('');

    // Belgilar — X o'qi ustida (pastda), chiziqlarga aralashmaydi
    var mk = '', mkLegend = '';
    if (markers && markers.length) {
      var idx = {};
      dates.forEach(function (d, i) { idx[dayKey(d)] = i; });
      markers.forEach(function (m) {
        var i = idx[m.sana];
        if (i === undefined) return;
        var cy = T + innerH + 7;
        mk += '<circle cx="' + x(i).toFixed(1) + '" cy="' + cy + '" r="3.4" fill="' + m.rang +
              '" stroke="var(--card)" stroke-width="1"><title>' + App.esc(m.matn) + '</title></circle>';
      });
      var turlar = {};
      markers.forEach(function (m) { turlar[m.tur] = m.rang; });
      mkLegend = Object.keys(turlar).map(function (t) {
        return '<span class="ch-lg"><i style="background:' + turlar[t] + ';border-radius:50%"></i>' + App.esc(t) + '</span>';
      }).join('');
    }

    /* QO'ZG'ALMAS KO'RSATKICH (cursor). Foydalanuvchi so'ragan aynan shu:
       vertikal uzuq-uzuq chiziq EKRANDA (ko'rinadigan oyna markazida)
       QOTIB TURADI — grafik chapga/o'ngga surilganda sanalar uning
       OSTIDAN o'tib ketadi, chiziqning o'zi joyidan qo'zg'almaydi. Shu
       sabab endi SVG ICHIGA chizilmaydi (u bilan birga scroll qilib
       ketardi) — buning o'rniga `paintChart` HTML/CSS bilan alohida
       qatlam sifatida qo'yadi va scroll paytida qaysi kun ustida
       turganini o'zi hisoblab, o'sha kunning barcha qiymatlarini
       yozuvda ko'rsatadi. Kerakli hisob-kitob uchun (`x`, `perDay`,
       `dates`, `todayIdx`, `series`) natija bilan birga qaytariladi. */
    return {
      html: '<div class="ch-legend">' + legend + mkLegend + '</div>' +
        '<div class="ch-wrap">' +
        '<div class="ch-scroll">' +
        '<svg class="ch-svg" width="' + W.toFixed(1) + '" height="' + H + '" viewBox="0 0 ' + W.toFixed(1) + ' ' + H + '">' +
        grid + paths + mk + xlb + '</svg>' +
        '</div>' +
        '<div class="ch-cursor"></div>' +
        '<div class="ch-cursor-lb"></div>' +
        '</div>',
      meta: { L: L, perDay: perDay, dates: dates, todayIdx: todayIdx, series: series }
    };
  }

  /* `lineChart()` natijasini joylashtiradi va QO'ZG'ALMAS ko'rsatkichni
     ulaydi: boshlang'ich holatda "Bugun" ko'rinadigan oyna MARKAZIDA
     turadi (shuning uchun uning o'ng tomonida "Ertaga" va yana bir necha
     kun ko'rinib turadi), so'ng har scroll'da qaysi kun ko'rsatkich
     ustida turganini hisoblab, sanasi va shu kungi qiymatlarni yozuvda
     ko'rsatadi. Barcha so'rovlar `box` ICHIDA qidiriladi (global id emas)
     — sahifada bir nechta grafik bir vaqtda turishi mumkin (asosiy
     Dinamika + har bo'lim ichidagi alohida grafik). */
  /* Ko'rsatkichni ANIQ markazlash uchun "bugundan keyin" nechta kun
     zaxira kerakligini KONTEYNERNING HAQIQIY kengligidan hisoblaydi.
     Standart 3 kun kichik ekranlarda yetarli edi, lekin kengroq
     ekranda (yoki 90-kunlik zichlikda) yarim oyna kengligi zaxiradan
     katta bo'lib, brauzer chetga tirmashib qolar, "Bugun" markazdan
     bir necha kun CHAPDA ko'rinardi. Endi zaxira shunga yetarli:
     `viewportPx/2` px'ni qamrab olguncha kun qo'shiladi (+2 kun
     ehtiyot uchun — brauzer qirralari, scrollbar va h.k.). */
  function fitFutureDays(viewportPx, perDay) {
    var need = Math.ceil((viewportPx / 2) / Math.max(1, perDay)) + 2;
    return Math.max(3, Math.min(200, need));
  }

  function paintChart(box, series, days, markers) {
    if (!box) return;
    var perDayPreview = (700 - 8 - 46) / Math.max(1, days - 1);
    var futureDays = fitFutureDays(box.clientWidth || 700, perDayPreview);
    var result = lineChart(series, days, markers, {
      type: localStorage.getItem('chart_type') || 'line',
      futureDays: futureDays
    });

    box.innerHTML = result.html;
    var sc = box.querySelector('.ch-scroll');
    var lb = box.querySelector('.ch-cursor-lb');
    if (!sc || !lb) return;

    var m = result.meta;
    function repaint() {
      var centerX = sc.scrollLeft + sc.clientWidth / 2;
      var idx = Math.round((centerX - m.L) / m.perDay);
      idx = Math.max(0, Math.min(m.dates.length - 1, idx));
      var d = m.dates[idx];
      var key = dayKey(d);
      var dateTxt = idx === m.todayIdx ? 'Bugun' : (d.getDate() + '-' + UZ_MON[d.getMonth()]);
      var vals = m.series.map(function (s) {
        var v = s.nuqtalar[key] || 0;
        return v ? ('<i style="background:' + s.rang + '"></i>' + App.esc(s.nom) + ' ' + v) : '';
      }).filter(Boolean).join('');
      lb.innerHTML = '<b>' + App.esc(dateTxt) + '</b>' + (vals || '<span class="ch-cursor-empty">Bo\'sh kun</span>');
    }

    /* Boshlang'ich holat: "Bugun" ko'rsatkich ustida — ANIQ markazda
       (endi `futureDays` konteyner kengligiga mos hisoblangani uchun
       chetga tirmashib qolmaydi). */
    var todayX = m.L + m.todayIdx * m.perDay;
    sc.scrollLeft = Math.max(0, Math.min(sc.scrollWidth - sc.clientWidth, todayX - sc.clientWidth / 2));

    /* `setTimeout` bilan cheklaymiz, `requestAnimationFrame` BILAN EMAS:
       rAF sahifa/pane ko'rinmay qolganda (fonga o'tganda) ushlanib
       qolishi mumkin, ya'ni yorliq scroll paytida yangilanmay qolardi.
       `repaint()` juda arzon (bir necha o'nlab qiymatni solishtirish),
       shuning uchun 16ms chegarasi (~60fps) yetarlicha silliq. */
    var pending = false;
    sc.addEventListener('scroll', function () {
      if (pending) return;
      pending = true;
      setTimeout(function () { pending = false; repaint(); }, 16);
    }, { passive: true });
    repaint();
  }

  /* Grafikni sichqoncha bilan bosib-tortib skroll qilish (desktop uchun —
     telefonda barmoq bilan tabiiy ishlaydi, `overflow-x:auto` yetarli).
     Delegatsiya orqali BIR MARTA ulanadi, har safar qayta chizilganda
     qayta bog'lash shart emas. */
  var chDrag = null;
  document.addEventListener('mousedown', function (e) {
    var el = e.target.closest && e.target.closest('.ch-scroll');
    if (!el) return;
    chDrag = { el: el, x: e.clientX, left: el.scrollLeft };
    el.classList.add('dragging');
    e.preventDefault();
  });
  document.addEventListener('mousemove', function (e) {
    if (!chDrag) return;
    /* "Bugun" chizig'ini tortayotgandek — chapga tortilsa eski kunlar
       ko'rinadi (scrollbar dastagini chapga surish bilan bir xil mantiq),
       oddiy "yuzani ushlab tortish" (kontent kursorga ergashadi) EMAS. */
    chDrag.el.scrollLeft = chDrag.left + (e.clientX - chDrag.x);
  });
  function chDragEnd() {
    if (!chDrag) return;
    chDrag.el.classList.remove('dragging');
    chDrag = null;
  }
  document.addEventListener('mouseup', chDragEnd);
  document.addEventListener('mouseleave', chDragEnd);

  /* =========================================================
     STATISTIKA — butun ilova bo'yicha
     ========================================================= */
  App.view('stats', {
    nav: 'stats',
    render: function (page) {
      var ct = localStorage.getItem('chart_type') || 'line';
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>Statistika</h1>' +
        '<div style="flex:1"></div>' +
        '<div class="seg" style="margin:0;width:auto;min-height:30px;font-size:12px">' +
        '<button class="' + (ct !== 'bar' ? 'active' : '') + '" data-act="statsChartType" data-arg=\'{"type":"line"}\' style="padding:0 12px">Chiziqli</button>' +
        '<button class="' + (ct === 'bar' ? 'active' : '') + '" data-act="statsChartType" data-arg=\'{"type":"bar"}\' style="padding:0 12px">Ustunli</button></div></div>' +
        '<div class="st-grid" id="st-top"></div>' +
        '<div class="hsec"><h2>Dinamika</h2>' +
        '<div class="seg seg-sm" id="st-range">' +
        [14, 30, 90].map(function (n) {
          return '<button class="' + (n === RANGE ? 'active' : '') + '" data-act="statsRange" data-arg=\'' +
            App.arg({ n: n }) + '\'>' + n + ' kun</button>';
        }).join('') + '</div></div>' +
        '<div class="ch-card" id="st-chart"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<div class="hsec"><h2>Faollik</h2>' +
        '<span class="muted" style="font-size:11.5px;font-weight:600" id="st-act-sum"></span></div>' +
        '<div class="st-bars" id="st-act"></div>' +
        SEC_BLOCKS.map(sectionBlockHtml).join('') +
        '';

      App.icons(page);
      renderTop();
      renderChart();
      renderActivity();
      renderQuiz();
      renderVocab();
      renderTopics();
      renderSport();
      renderAllBreakdowns();
    }
  });


  /* Tanlangan davr (kun). Sozlama saqlanadi. */
  var RANGE = parseInt(ls('stats_range_v1', '30'), 10) || 30;
  App.actions.statsRange = function (a) {
    RANGE = parseInt(a.n, 10) || 30;
    try { localStorage.setItem('stats_range_v1', String(RANGE)); } catch (e) {}
    App.reload();
  };

  App.actions.statsChartType = function(a) {
    try { localStorage.setItem('chart_type', a.type); } catch (e) {}
    App.reload();
  };

  /* Dinamika grafigi — HAQIQIY ma'lumot:
       Testlar   -> quiz_results (created_at bo'yicha kunlik son)
       Sport     -> sport_log_v1 (mashg'ulot kunlari)
       Boostday  -> boost_stats.daily_series (bajarilgan vazifalar)
       Faollik   -> activity_days_v1
     Server bloklari yiqilsa ham qolganlari chiziladi. */
  function renderChart() {
    var box = App.el('st-chart'); if (!box) return;

    var faollik = {}, sport = {};
    jls('activity_days_v1', []).forEach(function (d) { faollik[d] = 1; });
    // sport_log_v1 — MASSIV: [{d: 'YYYY-MM-DD', name, cat, ...}] (sport.js shunday yozadi)
    sportLog().forEach(function (e) { if (e && e.d) sport[e.d] = (sport[e.d] || 0) + 1; });

    Promise.all([
      App.call('get_quiz_results').catch(function () { return { results: [] }; }),
      App.call('boost_stats').catch(function () { return {}; })
    ]).then(function (r) {
      var testlar = {};
      (r[0].results || []).forEach(function (row) {
        var k = String(row.created_at || '').slice(0, 10);
        if (k) testlar[k] = (testlar[k] || 0) + 1;
      });

      var boost = {};
      ((r[1] && r[1].daily_series) || []).forEach(function (d) {
        if (d && d.date) boost[d.date] = +d.completed_tasks || 0;
      });

      var series = [
        { nom: 'Faollik', rang: '#2cbb5d', nuqtalar: faollik },
        { nom: 'Testlar', rang: '#4fb8e8', nuqtalar: testlar },
        { nom: 'Sport',   rang: '#ef8b6b', nuqtalar: sport },
        { nom: 'Boostday', rang: '#a78bfa', nuqtalar: boost }
      ].filter(function (x) { return Object.keys(x.nuqtalar).length; });

      /* Belgilar: deadline muddati — QIZIL, bajarilgan maqsad — YASHIL.
         Ular chiziqlardan mustaqil, X o'qi ustida ko'rinadi. */
      var markers = [];
      dls().forEach(function (d) {
        if (!d.end) return;
        markers.push({ sana: String(d.end).slice(0, 10), rang: '#f0564b',
                       tur: 'Deadline', matn: 'Deadline: ' + d.name });
      });
      var G = (window.Goals && Goals.data && Goals.data.goals) || [];
      G.forEach(function (g) {
        if (!g.completed || !g.completed_at) return;
        markers.push({ sana: String(g.completed_at).slice(0, 10), rang: '#2cbb5d',
                       tur: 'Maqsad bajarildi', matn: 'Bajarildi: ' + g.text });
      });

      if (!series.length && !markers.length) {
        box.innerHTML = '<p class="muted" style="font-size:13px;margin:6px 2px">' +
          'Hali ma\'lumot yo\'q — test yeching yoki mashq belgilang.</p>';
        return;
      }
      paintChart(box, series, RANGE, markers);
    }).catch(function (e) { fail('st-chart', e); });
  }


  /* =========================================================
     KENGAYTIRILGAN GRAFIKLAR — har bo'lim uchun alohida
     Har bir obyekt (test bazasi, mashq, lug'at kategoriyasi) O'Z chizig'iga
     ega. Chiziq/nuqta ustiga borilsa nomi va qiymati chiqadi (<title>).
     ========================================================= */
  var PALETTE = ['#4fb8e8','#2cbb5d','#ef8b6b','#a78bfa','#ffa116','#f0564b',
                 '#34c2a8','#e5a13a','#8b7be8','#5ac8fa','#ff8fab','#9ee493'];

  /* Har bir "nom" uchun alohida chiziq yasaydi */
  function toSeries(map) {
    return Object.keys(map).sort().map(function (nom, i) {
      return { nom: nom, rang: PALETTE[i % PALETTE.length], nuqtalar: map[nom] };
    });
  }

  /* =========================================================
     HAR BO'LIM O'Z GRAFIGI BILAN — tanlagich EMAS, hammasi bir-birining
     ostida ketma-ket ko'rinadi (Lug'at grafigi, Grammatika grafigi, Sport
     grafigi va h.k.). Manba: activity_log (barcha bo'limlar uchun yagona
     jurnal). Bo'lim ichida "obyekt" (fan bazasi, mashq, kategoriya) bo'yicha
     alohida chiziq/ustun chiziladi. */
  /* Bo'lim kalitlari activity_log dagi `section` qiymatlari bilan AYNAN
     mos bo'lishi shart. Ilgari bu yerda `lang_ru`/`lang_en` turardi —
     bunday `section` hech qachon yozilmaydi, ya'ni ikkala blok DOIM bo'sh
     edi. Ayni paytda eng ko'p yoziladigan `topic` (mavzular) va `vocab`
     (lug'at) bo'limlari statistikada umuman ko'rinmasdi.
     Ro'yxat: backend ALLOWED_SECTIONS va tarix.js SEC bilan bir xil. */
  var SEC_BLOCKS = [
    { k: 'quiz',      n: 'Testlar',     empty: 'Hali test yechilmagan',    summaryId: 'st-quiz' },
    { k: 'topic',     n: 'Mavzular',    empty: 'Hali mavzu o\'rganilmagan' },
    { k: 'vocab',     n: 'Lug\'at',     empty: 'Hali so\'z yodlanmagan' },
    { k: 'reading',   n: 'O\'qish',     empty: 'Hali matn o\'qilmagan' },
    { k: 'listening', n: 'Listening',   empty: 'Hali mashq bajarilmagan' },
    { k: 'material',  n: 'Materiallar', empty: 'Hali material o\'qilmagan' },
    { k: 'sport',     n: 'Sport',       empty: 'Hali mashq belgilanmagan',  summaryId: 'st-sport' },
    { k: 'boostday',  n: 'Boostday',    empty: 'Hali vazifa bajarilmagan' }
  ];

  function sectionBlockHtml(s) {
    return '<div class="hsec"><h2>' + App.esc(s.n) + '</h2></div>' +
      (s.summaryId ? '<div id="' + s.summaryId + '"><div class="load-wrap"><div class="spinner"></div></div></div>' : '') +
      '<div class="between" style="margin:14px 0 4px"><span class="muted" style="font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px">Taqsimot</span>' +
      '<span class="muted" style="font-size:11px">ustunga bosing — tafsiloti</span></div>' +
      '<div id="st-brk-' + s.k + '"><div class="load-wrap"><div class="spinner"></div></div></div>' +
      '<div class="ch-card" id="st-brk-chart-' + s.k + '"></div>';
  }

  /* Jurnal keshi — barcha bo'lim bloklari BITTA so'rovdan foydalanadi */
  var LOG_CACHE = { key: null, items: null };
  function activityLog() {
    /* RANGE (14/30/90) EMAS — bo'lim grafiklari ham chapga tortilib
       orqaga suriladi, shuning uchun jurnal ham shuncha kunni qamrashi
       kerak. Ilgari faqat RANGE so'ralardi va tortib orqaga o'tilganda
       Mavzular/Lug'at/Sport chiziqlari soxta 0 ko'rsatardi. */
    var from = new Date();
    from.setDate(from.getDate() - (Math.max(RANGE, CHART_HISTORY_DAYS) - 1));
    var key = dayKey(from);
    if (LOG_CACHE.key === key && LOG_CACHE.items) return Promise.resolve(LOG_CACHE.items);
    return App.call('get_activity_log', null, { query: 'from=' + key }).then(function (j) {
      LOG_CACHE = { key: key, items: j.items || [] };
      return LOG_CACHE.items;
    });
  }

  function fmtDur(sec) {
    if (!sec) return '';
    if (sec < 60) return sec + ' soniya';
    var m = Math.round(sec / 60);
    if (m < 60) return m + ' daqiqa';
    var h = Math.floor(m / 60);
    return h + ' soat ' + (m % 60) + ' daq';
  }

  /* nomi qanday tuziladi: testda "Fan__Baza" -> faqat Baza, qolganida obyekt nomi */
  function bucketName(sectionKey, it) {
    if (sectionKey === 'quiz') return String(it.object || 'Baza').split('__').pop();
    if (sectionKey === 'boostday') {
      var meta = {};
      try { meta = typeof it.meta === 'string' ? JSON.parse(it.meta) : (it.meta || {}); } catch(e){}
      return (meta && meta.group) ? meta.group : 'Vazifalar';
    }
    return it.object || '—';
  }

  /* Har bo'lim bo'yicha guruh — sectionKey bilan namespace qilingan
     (turli bo'limlarda bir xil nom kelib qolsa aralashmasin, masalan
     ikkalasida ham "Boshqa" bo'lishi mumkin). */
  var BREAK_GROUPS = {};

  function renderOneBreakdown(s, items) {
    var box = App.el('st-brk-' + s.k);
    var chartBox = App.el('st-brk-chart-' + s.k);
    if (!box) return;

    var groups = {}, unit = '';
    items.forEach(function (it) {
      if (it.section !== s.k) return;
      var nom = bucketName(s.k, it);
      var g = groups[nom] || (groups[nom] = { n: 0, amount: 0, dur: 0, kunlar: {} });
      g.n++;
      g.amount += (it.amount || 0);
      g.dur += (it.duration || 0);
      var kun = String(it.at || '').slice(0, 10);
      if (kun) g.kunlar[kun] = (g.kunlar[kun] || 0) + 1;
      if (!unit && it.unit) unit = it.unit;
    });
    BREAK_GROUPS[s.k] = groups;

    var nomlar = Object.keys(groups).sort(function (a, b) { return groups[b].n - groups[a].n; });
    if (!nomlar.length) {
      box.innerHTML = '<p class="muted" style="font-size:13px;margin:6px 2px">' + App.esc(s.empty) + '</p>';
      if (chartBox) chartBox.innerHTML = '';
      return;
    }

    var max = groups[nomlar[0]].n;
    box.innerHTML = nomlar.map(function (nom, i) {
      var g = groups[nom];
      var pct = Math.round((g.n / max) * 100);
      var rang = PALETTE[i % PALETTE.length];
      var sub = g.n + ' marta';
      if (g.amount) sub += ' · ' + Math.round(g.amount) + (unit ? ' ' + unit : '');
      if (g.dur) sub += ' · ' + fmtDur(g.dur);
      return '<button class="st-brk" data-act="statsBreakDetail" data-arg=\'' +
        App.arg({ sec: s.k, nom: nom }) + '\' style="display:flex;align-items:center;gap:10px;width:100%;' +
        'background:none;border:none;padding:7px 2px;text-align:left;cursor:pointer">' +
        '<span style="font-size:13px;min-width:96px;color:var(--text)">' + App.esc(nom) + '</span>' +
        '<span style="flex:1;height:8px;background:var(--border-soft);border-radius:4px;overflow:hidden">' +
        '<i style="display:block;height:100%;background:' + rang + ';border-radius:4px;width:' + pct + '%"></i></span>' +
        '<span style="font-size:11.5px;color:var(--hint);min-width:120px;text-align:right">' + App.esc(sub) + '</span>' +
        '</button>';
    }).join('');
    App.icons(box);

    if (chartBox) {
      var map = {};
      nomlar.slice(0, 8).forEach(function (nom) { map[nom] = groups[nom].kunlar; });
      paintChart(chartBox, toSeries(map), RANGE);
    }
  }

  function renderAllBreakdowns() {
    activityLog().then(function (baseItems) {
      // Rus tili va Ingliz tili uchun virtual ma'lumotlar yaratish
      var items = [];
      baseItems.forEach(function (it) {
        items.push(it);
        
        var isRu = false, isEn = false;
        var meta = {};
        try { meta = typeof it.meta === 'string' ? JSON.parse(it.meta) : (it.meta || {}); } catch(e){}
        
        var mGrp = (meta.group || '').toLowerCase();
        var mLang = (meta.lang || '').toLowerCase();
        var oName = (it.object || '').toLowerCase();
        
        if (mLang === 'russian' || mLang === 'ru' || mLang.indexOf('ru_') === 0) isRu = true;
        if (mGrp.indexOf('rus') !== -1 || mGrp.indexOf('🇷🇺') !== -1) isRu = true;
        if (it.section === 'quiz' && oName.indexOf('russian__') === 0) isRu = true;
        
        if (mLang === 'english' || mLang === 'en' || mLang.indexOf('en_') === 0) isEn = true;
        if (mGrp.indexOf('ingliz') !== -1 || mGrp.indexOf('english') !== -1 || mGrp.indexOf('🇬🇧') !== -1) isEn = true;
        if (it.section === 'quiz' && oName.indexOf('english__') === 0) isEn = true;

        var vName = bucketName(it.section, it);
        if (isRu) {
          var cloneRu = Object.assign({}, it);
          cloneRu.section = 'lang_ru';
          cloneRu.object = vName;
          items.push(cloneRu);
        }
        if (isEn) {
          var cloneEn = Object.assign({}, it);
          cloneEn.section = 'lang_en';
          cloneEn.object = vName;
          items.push(cloneEn);
        }
      });

      SEC_BLOCKS.forEach(function (s) {
        if (!App.el('st-brk-' + s.k)) return;
        renderOneBreakdown(s, items);
      });
    }).catch(function (e) { console.error('breakdown error', e); });
  }

  /* Ustunga bosilganda — nomi va tafsiloti */
  App.actions.statsBreakDetail = function (a) {
    var g = (BREAK_GROUPS[a.sec] || {})[a.nom];
    if (!g) return;
    var kunlar = Object.keys(g.kunlar).sort().reverse();
    var html =
      '<div class="stat-strip" style="margin:0 0 14px">' +
      '<div class="s"><div class="n">' + g.n + '</div><div class="l">Marta</div></div>' +
      (g.amount ? '<div class="s"><div class="n">' + Math.round(g.amount) + '</div><div class="l">Miqdor</div></div>' : '') +
      '<div class="s"><div class="n">' + kunlar.length + '</div><div class="l">Kun</div></div>' +
      (g.dur ? '<div class="s"><div class="n">' + Math.round(g.dur / 60) + '</div><div class="l">Daqiqa</div></div>' : '') +
      '</div>' +
      '<div class="list-label">Kunlar bo\'yicha</div>' +
      kunlar.slice(0, 20).map(function (k) {
        return '<div class="list-row" style="cursor:default"><div class="li-main">' +
          '<div class="li-title">' + App.esc(window.Tarix ? Tarix.dayLabel(k) : k) + '</div></div>' +
          '<span style="font-size:12.5px;color:var(--hint)">' + g.kunlar[k] + ' marta</span></div>';
      }).join('');
    App.sheet(html, { title: a.nom });
  };

  function card(n, l, c) {
    return '<div class="st-c"><div class="st-n" style="color:' + (c || 'var(--text)') + '">' +
      App.esc(String(n)) + '</div><div class="st-l">' + App.esc(l) + '</div></div>';
  }
  function fail(id, e) {
    var b = App.el(id);
    if (b) b.innerHTML = '<p class="muted" style="font-size:12.5px;margin:2px 1px">Yuklanmadi: ' +
      App.esc(e && e.message ? e.message : 'xato') + '</p>';
  }

  /* --- Yuqoridagi umumiy kartalar --- */
  function renderTop() {
    var box = App.el('st-top'); if (!box) return;
    var days = jls('activity_days_v1', []);
    var streak = (window.Activity && Activity.streak) ? Activity.streak() : 0;
    var g = (window.Goals && Goals.data && Goals.data.loaded) ? Goals.stats() : null;

    box.innerHTML =
      card(days.length, 'Faol kun', 'var(--success)') +
      card(streak, 'Ketma-ket', 'var(--warn)') +
      card(g ? g.done + '/' + g.total : '—', 'Maqsad') +
      card(upcoming().length, 'Deadline');

    if (!g && window.Goals) {
      Goals.load().then(function () {
        if (App.el('st-top')) renderTop();
      }).catch(function () {});
    }
  }

  /* --- Faollik: oxirgi 14 kun ustunli grafik --- */
  function renderActivity() {
    var box = App.el('st-act'); if (!box) return;
    var set = {};
    jls('activity_days_v1', []).forEach(function (d) { set[d] = true; });
    function key(d) {
      return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
             String(d.getDate()).padStart(2, '0');
    }
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var html = '', n = 0;
    for (var i = 13; i >= 0; i--) {
      var d = new Date(today); d.setDate(today.getDate() - i);
      var on = !!set[key(d)];
      if (on) n++;
      html += '<div class="st-bar' + (on ? ' on' : '') + '" title="' + key(d) + '">' +
              '<i></i><span>' + d.getDate() + '</span></div>';
    }
    box.innerHTML = html;
    var s = App.el('st-act-sum');
    if (s) s.textContent = n + ' / 14 kun';
  }

  /* --- Testlar --- */
  function renderQuiz() {
    App.call('get_structure').then(function (j) {
      var box = App.el('st-quiz'); if (!box) return;
      var st = j.structure || [];
      var fan = st.length, baza = 0;
      st.forEach(function (f) { baza += (f.dbs || f.bases || []).length; });
      box.innerHTML = '<div class="st-grid">' +
        card(fan, 'Fan') + card(baza, 'Baza') + '</div>';
    }).catch(function (e) { fail('st-quiz', e); });
  }

  /* --- Lug'at: ikkala til + SRS holati --- */
  function renderVocab() {
    var box = App.el('st-vocab'); if (!box) return;
    Promise.all([
      App.call('get_dict_data', null, { query: 'lang=english' }).catch(function () { return { items: [] }; }),
      App.call('get_dict_data', null, { query: 'lang=russian' }).catch(function () { return { items: [] }; })
    ]).then(function (r) {
      var en = (r[0].items || []).length, ru = (r[1].items || []).length;
      var srs = jls('vocab_srs_v1', {});
      var keys = Object.keys(srs);
      var ozlash = keys.filter(function (k) { return (srs[k].n || 0) >= 3; }).length;
      var bugun = keys.filter(function (k) {
        return srs[k].due && new Date(srs[k].due) <= new Date();
      }).length;
      box.innerHTML = '<div class="st-grid">' +
        card(en + ru, 'Jami so\'z') +
        card(ozlash, 'O\'zlashtirilgan', 'var(--success)') +
        card(bugun, 'Bugun takror', 'var(--warn)') +
        '</div>' +
        '<div class="st-split"><span>Ingliz: <b>' + en + '</b></span>' +
        '<span>Rus: <b>' + ru + '</b></span></div>';
    }).catch(function (e) { fail('st-vocab', e); });
  }

  /* --- Grammatika mavzulari --- */
  function renderTopics() {
    var box = App.el('st-topics'); if (!box) return;
    var langs = [['english', 'Ingliz'], ['russian', 'Rus'], ['coding', 'Coding']];
    Promise.all(langs.map(function (l) {
      return App.call('get_topics', null, { query: 'lang=' + l[0] })
        .catch(function () { return { topics: [] }; });
    })).then(function (rs) {
      var jami = 0, satr = '';
      rs.forEach(function (r, i) {
        var n = (r.topics || []).length;
        jami += n;
        satr += '<span>' + langs[i][1] + ': <b>' + n + '</b></span>';
      });
      box.innerHTML = '<div class="st-grid">' + card(jami, 'Jami mavzu') + '</div>' +
                      '<div class="st-split">' + satr + '</div>';
    }).catch(function (e) { fail('st-topics', e); });
  }

  /* --- Sport --- */
  function renderSport() {
    App.call('sport_get_all').then(function (j) {
      var box = App.el('st-sport'); if (!box) return;
      var data = j.data || {};
      var mashq = 0, kat = 0;
      Object.keys(data).forEach(function (k) {
        var n = (data[k] || []).length;
        if (n) { kat++; mashq += n; }
      });
      var kunSet = {};
      sportLog().forEach(function (e) { if (e && e.d) kunSet[e.d] = true; });
      box.innerHTML = '<div class="st-grid">' +
        card(mashq, 'Mashq') + card(kat, 'Kategoriya') +
        card(Object.keys(kunSet).length, 'Mashg\'ulot kuni', 'var(--success)') + '</div>';
    }).catch(function (e) { fail('st-sport', e); });
  }
})();
