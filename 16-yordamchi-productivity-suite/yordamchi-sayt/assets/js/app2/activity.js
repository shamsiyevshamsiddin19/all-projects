/* Faollik: qaysi kunlar ishlagansiz — seriya (streak) va haftalik ko'rinish.
   localStorage'da saqlanadi, remote-storage ko'prigi orqali serverga sinxronlanadi. */
(function () {
  'use strict';

  var KEY = 'activity_days_v1';
  var MAX_DAYS = 400; // taxminan bir yil — ro'yxat cheksiz o'smasin

  function todayKey(d) {
    d = d || new Date();
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function write(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(-MAX_DAYS))); } catch (e) {}
  }

  /* Bugungi kunni faol deb belgilaydi (test yakunlansa, lug'at mashqi bo'lsa va h.k.) */
  function mark() {
    var t = todayKey();
    var list = read();
    if (list.indexOf(t) === -1) { list.push(t); list.sort(); write(list); }
  }

  /* Ketma-ket necha kun ishlangani. Bugun ishlanmagan bo'lsa ham, kecha ishlangan
     bo'lsa seriya uzilmagan hisoblanadi (kun tugamagan). */
  function streak() {
    var set = {};
    read().forEach(function (d) { set[d] = true; });
    var d = new Date();
    if (!set[todayKey(d)]) {
      d.setDate(d.getDate() - 1);
      if (!set[todayKey(d)]) return 0;
    }
    var n = 0;
    while (set[todayKey(d)]) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }

  /* Oxirgi 7 kun: [{label, active, today}] — bosh sahifadagi mayda ko'rsatkich uchun */
  function lastWeek() {
    var names = ['Ya', 'Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh'];
    var set = {};
    read().forEach(function (d) { set[d] = true; });
    var out = [], now = new Date();
    for (var i = 6; i >= 0; i--) {
      var d = new Date(now);
      d.setDate(now.getDate() - i);
      var k = todayKey(d);
      out.push({ label: names[d.getDay()], active: !!set[k], today: i === 0 });
    }
    return out;
  }

  function totalDays() { return read().length; }

  /* ---------- Boostday intensivligi (GitHub uslubidagi kunlar) ----------
     Boostday `stats` javobidagi `daily_series` (14 kun: date, total_tasks,
     completed_tasks) asosida har kun uchun 0-4 daraja hisoblaymiz.
     Daraja MUTLAQ son emas, oynadagi ENG KATTA qiymatga nisbatan beriladi —
     shunda kam vazifa qiladigan kunlarda ham farq ko'rinadi (GitHub ham
     foydalanuvchi taqsimotiga moslashadi). */

  var boostCache = null; // {at: ms, map: {date: {total, completed, percent}}}
  var BOOST_TTL = 60000;

  function boostSeries() {
    if (boostCache && (Date.now() - boostCache.at) < BOOST_TTL) {
      return Promise.resolve(boostCache.map);
    }
    if (!window.App || !App.call) return Promise.resolve(null);
    return App.call('boost_stats', {}).then(function (j) {
      var map = {};
      (j && j.daily_series || []).forEach(function (d) {
        if (!d || !d.date) return;
        var total = +d.total_tasks || 0, completed = +d.completed_tasks || 0;
        map[d.date] = { total: total, completed: completed,
          percent: total ? Math.round(completed * 100 / total) : 0 };
      });
      boostCache = { at: Date.now(), map: map };
      return map;
    }).catch(function () {
      // Boostday ulanmagan/ruxsat yo'q — mavjud lokal ko'rsatkich bilan davom etamiz
      return null;
    });
  }

  function levelOf(count, max) {
    if (!count) return 0;
    if (max <= 0) return 0;
    var q = count / max;
    if (q > 0.75) return 4;
    if (q > 0.5) return 3;
    if (q > 0.25) return 2;
    return 1;
  }

  /* lastWeek() ning Boostday bilan boyitilgan varianti:
     [{label, active, today, count, level}] — level 0..4 */
  function lastWeekBoost() {
    var base = lastWeek();
    return boostSeries().then(function (map) {
      if (!map) return base; // fallback: eski on/off ko'rinish
      var now = new Date(), counts = [];
      for (var i = 6; i >= 0; i--) {
        var d = new Date(now);
        d.setDate(now.getDate() - i);
        counts.push((map[todayKey(d)] || {}).completed || 0);
      }
      // Darajani oxirgi 14 kunning eng kattasiga nisbatan beramiz — bir hafta
      // sust bo'lsa ham masshtab sakrab ketmasin.
      var max = 0;
      Object.keys(map).forEach(function (k) { if (map[k].completed > max) max = map[k].completed; });
      return base.map(function (d, i) {
        d.count = counts[i];
        d.level = levelOf(counts[i], max);
        if (d.count > 0) d.active = true;
        return d;
      });
    });
  }

  window.Activity = {
    mark: mark, streak: streak, lastWeek: lastWeek, totalDays: totalDays,
    lastWeekBoost: lastWeekBoost,
    /* Kun bo'yicha Boostday vazifa foizi: {date: {total, completed, percent}}.
       Bosh sahifadagi faollik heatmap kataklarining rangi shundan olinadi. */
    dailyStats: boostSeries
  };
})();
