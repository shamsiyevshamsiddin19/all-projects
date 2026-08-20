/* Profil sahifasi (avvalgi Bosh sahifa boshqaruvi + barcha "Yana" bo'limlari). */
(function () {
  'use strict';

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }

  /* Barcha "Yana" bo'limlari kartochkalari */
  var PROFILE_SECTIONS = [
    { v: 'goals', n: 'Maqsadlar', d: 'Kunlik vazifalar va odatlar', ic: 'check', c: '#10b981' },
    { v: 'stats', n: 'Statistika', d: 'Rivojlanish va o\'qish ko\'rsatkichlari', ic: 'chart', c: '#3b82f6' },
    { v: 'tarix', n: 'Tarix', d: 'Faollik va o\'rganishlar arxivi', ic: 'clock', c: '#8b5cf6' },
    { v: 'fanlar', n: 'Testlar', d: 'Bilimni sinash uchun testlar', ic: 'book', c: '#f59e0b' },
    { v: 'coding', n: 'Coding', d: 'Dasturlash darsliklari va amaliyot', ic: 'code', c: '#06b6d4' },
    { v: 'boost', n: 'Boostday', d: 'Intensiv rivojlanish rejasi', ic: 'message', c: '#ec4899' },
    { v: 'arxiv', n: 'Arxiv', d: 'Bajarilgan maqsadlar ombori', ic: 'archive', c: '#64748b' },
    { v: 'qoidalar', n: 'Qoidalar', d: 'Hayotiy qoidalar va tamoyillar', ic: 'file', c: '#14b8a6' },
    { v: 'settings', n: 'Sozlamalar', d: 'Ilova, mavzu va hisob sozlamalari', ic: 'settings', c: '#6366f1' }
  ];

  App.view('profile', {
    nav: 'profile',
    render: function (page) {
      page.innerHTML =
        /* Yuqori qator: salomlashuv + bildirishnoma qo'ng'irog'i */
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
        '<div id="h-widget"></div>' +
        
        /* Profil pastidagi "Barcha Bo'limlar" (Ilgari "Yana" menyusida bo'lgan bo'limlar) */
        '<div class="prof-more-wrap">' +
          '<div class="prof-more-head">' +
            '<h3>Barcha bo\'limlar va xizmatlar</h3>' +
            '<span>Tezkor o\'tish</span>' +
          '</div>' +
          '<div class="prof-grid">' +
            PROFILE_SECTIONS.map(function (sec) {
              return '<button class="prof-card" data-act="go" data-arg=\'' + App.arg({ v: sec.v }) + '\'>' +
                '<div class="prof-card-icon" style="background:color-mix(in srgb, ' + sec.c + ' 16%, transparent);color:' + sec.c + '">' +
                  '<span data-icon="' + sec.ic + '" data-icon-size="22"></span>' +
                '</div>' +
                '<div class="prof-card-info">' +
                  '<div class="prof-card-title">' + App.esc(sec.n) + '</div>' +
                  '<div class="prof-card-desc">' + App.esc(sec.d) + '</div>' +
                '</div>' +
                '<span class="prof-card-arrow" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span>' +
              '</button>';
            }).join('') +
          '</div>' +
        '</div>';

      App.icons(page);
      renderHello();
      renderLessons();
      if (window.LmsDay) LmsDay.ensureLoaded().then(renderLessons).catch(function () {});
      renderHeatmap();
      renderDailyWidget();
      bindResize();

      var g = (window.Goals && Goals.data && Goals.data.loaded) ? Goals.stats() : { done: 0, total: 0, pct: 0 };
      renderRings(g);
      if (window.Goals && !Goals.data.loaded) {
        Goals.load().then(function () { renderRings(Goals.stats()); }).catch(function () {});
      }
    },
    leave: function () { unbindResize(); stopHello(); }
  });

  /* Quyosh hisobi */
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

    var h0 = RAD * -0.833;
    var cosW = (Math.sin(h0) - Math.sin(phi) * Math.sin(dec)) / (Math.cos(phi) * Math.cos(dec));
    if (cosW > 1 || cosW < -1) return null;
    var w = Math.acos(cosW);
    var a = J0 + (w + lw) / (2 * Math.PI) + n;
    var Jset = J2000 + a + 0.0053 * Math.sin(M) - 0.0069 * Math.sin(2 * L);
    var Jrise = Jnoon - (Jset - Jnoon);
    return { rise: fromJulian(Jrise), set: fromJulian(Jset), noon: fromJulian(Jnoon) };
  }

  function geo() {
    var lat = parseFloat(ls('geo_lat', '')), lon = parseFloat(ls('geo_lon', ''));
    if (isFinite(lat) && isFinite(lon)) return { lat: lat, lon: lon };
    return { lat: 41.2995, lon: 69.2401 };
  }

  function hhmm(d) {
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }
  function dur(ms) {
    var m = Math.max(0, Math.round(ms / 60000));
    var h = Math.floor(m / 60); m = m % 60;
    if (h && m) return h + ' soat ' + m + ' daqiqa';
    if (h) return h + ' soat';
    return m + ' daqiqa';
  }

  var HELLO_T = null, HELLO_I = 0;

  function helloLines() {
    var now = new Date(), g = geo();
    var t = sunTimes(now, g.lat, g.lon);
    var lines = [];

    if (t) {
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
    var el = document.getElementById('h-hello');
    if (!el) return;
    var name = (window.Auth && Auth.user && Auth.user.name) ? Auth.user.name : (ls('user_name', '') || 'Do\'st');
    var w = greetWord();
    var lines = helloLines();
    HELLO_I = 0;

    function paint() {
      if (!el) return;
      var cur = lines[HELLO_I % lines.length];
      el.innerHTML =
        '<h2>' + w + ', <b>' + App.esc(name) + '</b>!</h2>' +
        '<div class="h-sun-line"><span class="h-sun-text">' + App.esc(cur) + '</span></div>';
    }
    paint();
    if (lines.length > 1) {
      HELLO_T = setInterval(function () {
        var sub = el.querySelector('.h-sun-text');
        if (!sub) return;
        sub.classList.add('fade-out');
        setTimeout(function () {
          HELLO_I++;
          sub.textContent = lines[HELLO_I % lines.length];
          sub.classList.remove('fade-out');
          sub.classList.add('fade-in');
          setTimeout(function () { sub.classList.remove('fade-in'); }, 300);
        }, 250);
      }, 4200);
    }
  }

  function stopHello() {
    if (HELLO_T) { clearInterval(HELLO_T); HELLO_T = null; }
  }

  function renderRings(g) {
    var el = document.getElementById('h-rings');
    if (!el) return;
    var gHtml = ringHtml({
      pct: g.pct,
      color: '#10b981',
      title: 'Maqsadlar',
      stat: g.done + '/' + g.total,
      act: 'go',
      arg: { v: 'goals' }
    });
    var hHtml = window.Habits ? Habits.ringHtml() : '';
    el.innerHTML = gHtml + (hHtml ? '<div class="ring-sep"></div>' + hHtml : '');
    App.icons(el);
  }

  function ringHtml(o) {
    var r = 32, c = 2 * Math.PI * r, off = c - (Math.max(0, Math.min(100, o.pct)) / 100) * c;
    return '<button class="ring-card" data-act="' + o.act + '" data-arg=\'' + App.arg(o.arg) + '\'>' +
      '<svg class="ring-svg" viewBox="0 0 80 80">' +
        '<circle class="ring-bg" cx="40" cy="40" r="' + r + '"/>' +
        '<circle class="ring-val" cx="40" cy="40" r="' + r + '" ' +
          'stroke="' + o.color + '" stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + off.toFixed(1) + '"/>' +
      '</svg>' +
      '<div class="ring-meta">' +
        '<div class="ring-title">' + App.esc(o.title) + '</div>' +
        '<div class="ring-stat">' + App.esc(o.stat) + '</div>' +
      '</div>' +
    '</button>';
  }

  function renderLessons() {
    var el = document.getElementById('h-lessons');
    if (!el || !window.LmsDay) return;
    el.innerHTML = LmsDay.cardHtml();
    App.icons(el);
  }

  /* Heatmap */
  var HM_OFF = 0, HM_WEEKS = 53;

  function calcWeeks() {
    var w = window.innerWidth;
    if (w < 420) return 16;
    if (w < 600) return 24;
    if (w < 900) return 36;
    return 53;
  }

  function bindResize() {
    window.addEventListener('resize', onResize);
  }
  function unbindResize() {
    window.removeEventListener('resize', onResize);
  }
  var RZ_T = null;
  function onResize() {
    clearTimeout(RZ_T);
    RZ_T = setTimeout(function () {
      var nw = calcWeeks();
      if (nw !== HM_WEEKS) {
        HM_WEEKS = nw;
        renderHeatmap();
      }
    }, 150);
  }

  function renderHeatmap() {
    var wrap = document.getElementById('hm-wrap');
    if (!wrap || !window.Activity) return;

    HM_WEEKS = calcWeeks();
    var acts = Activity.load();
    var actsMap = {};
    acts.forEach(function (a) { actsMap[a.date] = (actsMap[a.date] || 0) + (a.count || 1); });

    var now = new Date();
    var end = new Date(now.getFullYear(), now.getMonth(), now.getDate() - HM_OFF * 7);
    var start = new Date(end.getTime() - (HM_WEEKS * 7 - 1) * DAY_MS);

    var total = 0, activeDays = 0, maxStreak = 0, curStreak = 0;
    Object.keys(actsMap).sort().forEach(function (d) {
      if (actsMap[d] > 0) {
        curStreak++;
        if (curStreak > maxStreak) maxStreak = curStreak;
      } else {
        curStreak = 0;
      }
    });

    var daysHtml = [];
    var cur = new Date(start);
    while (cur <= end) {
      var ds = App.isoDate(cur);
      var cnt = actsMap[ds] || 0;
      if (cnt > 0) { total += cnt; activeDays++; }
      var lvl = cnt === 0 ? 0 : cnt < 3 ? 1 : cnt < 6 ? 2 : cnt < 10 ? 3 : 4;
      daysHtml.push(
        '<div class="hm-day hm-lvl-' + lvl + '" ' +
          'data-date="' + ds + '" data-cnt="' + cnt + '" ' +
          'title="' + ds + ': ' + cnt + ' faollik"></div>'
      );
      cur = new Date(cur.getTime() + DAY_MS);
    }

    wrap.innerHTML = daysHtml.join('');

    var elTot = document.getElementById('hm-total');
    if (elTot) elTot.textContent = total;
    var elDays = document.getElementById('hm-days');
    if (elDays) elDays.textContent = activeDays;
    var elStrk = document.getElementById('hm-streak');
    if (elStrk) elStrk.textContent = maxStreak;

    var elRange = document.getElementById('hm-range');
    if (elRange) {
      elRange.textContent = App.uzMonth(start) + ' ' + start.getFullYear() + ' — ' +
        App.uzMonth(end) + ' ' + end.getFullYear();
    }

    var fwd = document.getElementById('hm-fwd');
    if (fwd) fwd.disabled = (HM_OFF <= 0);
  }

  App.actions.hmBack = function () { HM_OFF += 4; renderHeatmap(); };
  App.actions.hmFwd = function () { if (HM_OFF > 0) { HM_OFF = Math.max(0, HM_OFF - 4); renderHeatmap(); } };

  function renderDailyWidget() {
    var host = document.getElementById('h-widget');
    if (!host) return;
    if (window.KunHisobi && KunHisobi.widgetHtml) {
      host.innerHTML = KunHisobi.widgetHtml();
      App.icons(host);
    } else {
      host.innerHTML = '';
    }
  }

})();
