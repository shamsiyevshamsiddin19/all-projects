/* Kun hisobi — BUTUN KUNNING aniq vaqtli rejasi (faqat darslar emas).
   Bitta vaqt chizig'ida birlashtiriladi:
     1) haftalik takrorlanuvchi mashg'ulotlar  — `kun_schedule_v1` (0..6 kun bo'yicha)
     2) aniq sanaga bog'langan bir martalik voqealar — `kun_events_v1` ("YYYY-MM-DD")
     3) Boostday rejalari o'z vaqtida (window.BoostDay ko'prigi orqali)
     4) vaqti yo'q ishlar — sport mashqlari (window.SportBridge)
   Ikkala saqlash kaliti ham localStorage'da (remote-storage orqali server bilan
   avtomatik sinxron — alohida ro'yxatga qo'shish shart emas). */
(function () {
  'use strict';

  var STORE_KEY = 'kun_schedule_v1';
  var EVENT_KEY = 'kun_events_v1';

  var DEFAULT_SCHEDULE = {
    1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 0: []
  };
  var DAY_SHORT = ["Yak", "Dush", "Sesh", "Chor", "Pay", "Jum", "Shan"];
  var DAY_FULL = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];
  var MON_SHORT = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
  var REF_WEEK_START = new Date('2026-03-17T00:00:00');

  /* ---------- TURKUMLAR (rang guruhlari) ----------
     Bir turkumdagi hamma ish BIR XIL rangda ko'rinadi — jadvalga qaraganda
     "bu nima ish" darhol bilinadi. Rang mashg'ulotning O'ZIDA emas,
     turkumida saqlanadi, shuning uchun butun guruhning rangini bir joydan
     o'zgartirish mumkin. */
  var CATS = [
    { id: 'kurs',       n: 'Dars / kurs',       e: '📚', c: '#3b82f6' },
    { id: 'rus',        n: 'Rus tili',          e: '🇷🇺', c: '#a855f7' },
    { id: 'dasturlash', n: 'Dasturlash',        e: '💻', c: '#22c55e' },
    { id: 'sport',      n: 'Sport',             e: '🏋', c: '#f97316' },
    { id: 'hayot',      n: 'Kundalik hayot',    e: '🌿', c: '#14b8a6' },
    { id: 'boshqa',     n: 'Boshqa',            e: '📌', c: '#64748b' }
  ];
  function catInfo(id) {
    for (var i = 0; i < CATS.length; i++) if (CATS[i].id === id) return CATS[i];
    return CATS[CATS.length - 1];        // 'boshqa'
  }
  function catColor(id) { return catInfo(id).c; }

  /* Nomidan turkumni taxmin qilish — .md da turkum yozilmagan bo'lsa
     ishlatiladi (eski fayllar va qo'lda kiritilganlar ham rangli chiqsin).
     TARTIB MUHIM: aniqrog'i oldin tekshiriladi, aks holda "Rus tili darsi"
     "dars" deb topilib, rus tili rangini yo'qotardi. */
  /* ⚠️ TARTIB va ANIQLIK muhim. Ilgari `sport` birinchi turgan va uning
     ichida umumiy `mashq` so'zi bor edi — natijada "Rus tili MASHQlari" va
     "Dasturlash MASHQlari" ham sport deb topilib, hammasi bir xil to'q
     sariq rangda chiqardi. Endi: aniq mavzular (rus/dasturlash) OLDIN,
     umumiy so'zlar esa umuman ishlatilmaydi.
     So'z chegaralari (`\b`) ham qo'yildi — `tish` "o'rgaTISH" ichidan,
     `o'qish` esa "yOQISH" ichidan topilib ketardi. */
  var CAT_HINTS = [
    ['rus',        /rus\s*til|russian|русск|падеж|глагол/i],
    ['dasturlash', /dasturlash|coding|\bkod\b|html|css|javascript|typescript|python|\bjava\b|react|backend|frontend|algoritm|leetcode|\bpdp\b|\bsql\b|\bgit\b/i],
    ['sport',      /\bsport|zal(ga|da)?\b|turnik|brus|\bpress\b|ajimaniya|yugur|fitnes|futbol|basketbol|voleybol|badminton|suzish|velosiped/i],
    ['hayot',      /ovqat|nonushta|tushlik|kechki|uyg['’]?on|uyqu|uxla|dam olish|yuvin|\bdush\b|cho['’]?mil|\btish|shaxsiy|namoz|tozalash|kiyin|xarid/i],
    ['kurs',       /\bdars|\bkurs|universitet|ma['’]?ruza|amaliyot|seminar|imtihon|\blms\b|tatu|\bo['’]?qish|\blab\b|kollokvium/i]
  ];
  function guessCat(text) {
    var s = String(text || '');
    for (var i = 0; i < CAT_HINTS.length; i++) {
      if (CAT_HINTS[i][1].test(s)) return CAT_HINTS[i][0];
    }
    return 'boshqa';
  }

  /* Mashg'ulot TURLARI (qo'lda qo'shish oynasida tanlanadi). Har turi
     o'z TURKUMIGA tegishli — rangni turkum beradi. */
  var KINDS = [
    { k: 'dars',       n: 'Dars',              e: '📚', cat: 'kurs' },
    { k: 'kurs',       n: 'Kurs (majburiy)',   e: '🎓', cat: 'kurs' },
    { k: 'mustaqil',   n: "Mustaqil o'qish",   e: '📖', cat: 'kurs' },
    { k: 'rus',        n: 'Rus tili',          e: '🇷🇺', cat: 'rus' },
    { k: 'dasturlash', n: 'Dasturlash',        e: '💻', cat: 'dasturlash' },
    { k: 'sport',      n: 'Sport',             e: '🏋', cat: 'sport' },
    { k: 'ovqat',      n: 'Ovqatlanish',       e: '🍽', cat: 'hayot' },
    { k: 'uyqu',       n: 'Uyqu / uyg\'onish', e: '😴', cat: 'hayot' },
    { k: 'shaxsiy',    n: 'Shaxsiy',           e: '🌿', cat: 'hayot' },
    { k: 'yol',        n: "Yo'l / safar",      e: '🚌', cat: 'hayot' },
    { k: 'ish',        n: 'Ish / loyiha',      e: '💼', cat: 'boshqa' },
    { k: 'boshqa',     n: 'Boshqa',            e: '📌', cat: 'boshqa' }
  ];
  function kindInfo(k) {
    for (var i = 0; i < KINDS.length; i++) if (KINDS[i].k === k) return KINDS[i];
    return KINDS[0];
  }
  /* Turi bo'yicha rang. Eski yozuvlarda `kind` yo'q yoki olib tashlangan
     tur bo'lishi mumkin — unda nomidan taxmin qilamiz. */
  function kindColor(kind, title) {
    var ki = null;
    for (var i = 0; i < KINDS.length; i++) if (KINDS[i].k === kind) ki = KINDS[i];
    return catColor(ki ? ki.cat : guessCat(title || kind));
  }

  /* --- Sana yordamchilari (hammasi mahalliy vaqt bo'yicha) --- */
  function dkey(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function parseKey(s) {
    var p = String(s || '').split('-');
    if (p.length !== 3) return null;
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    return isNaN(d.getTime()) ? null : d;
  }
  function addDays(d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; }
  function todayKey() { return dkey(new Date()); }
  function shortDate(d) { return d.getDate() + ' ' + MON_SHORT[d.getMonth()]; }

  /* --- Jadval saqlash/o'qish --- */
  var SCHEDULE = null, EVENTS = null;
  function loadSchedule() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      if (raw) {
        /* ⚠️ BU YERDA MA'LUMOT YO'QOTADIGAN TEKSHIRUV BOR EDI:
           `raw.indexOf('Differensial') !== -1` bo'lsa BUTUN jadval
           o'chirilardi. U eski hardcoded demo jadvalni tozalash uchun
           yozilgan, lekin HAR yuklashda ishlardi — natijada matnida shu
           so'z bo'lgan HAQIQIY jadval ham yo'q qilinardi. Foydalanuvchining
           darsi aynan "Differensial tenglamalar" deb ataladi, ya'ni u o'z
           jadvalini kiritsa har safar yo'qotardi.
           Demo jadval allaqachon hammada tozalangan (bu kod uzoq vaqtdan
           beri jonli), shuning uchun tekshiruv butunlay olib tashlandi. */
        var v = JSON.parse(raw);
        if (v && typeof v === 'object') return v;
      }
    } catch (e) {}
    return JSON.parse(JSON.stringify(DEFAULT_SCHEDULE));
  }
  function saveSchedule() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(SCHEDULE)); } catch (e) {}
  }
  function loadEvents() {
    try {
      var raw = localStorage.getItem(EVENT_KEY);
      if (raw) {
        var v = JSON.parse(raw);
        if (v && typeof v === 'object' && !Array.isArray(v)) return v;
      }
    } catch (e) {}
    return {};
  }
  function saveEvents() {
    try { localStorage.setItem(EVENT_KEY, JSON.stringify(EVENTS)); } catch (e) {}
  }
  function ensureLoaded() {
    if (!SCHEDULE) SCHEDULE = loadSchedule();
    if (!EVENTS) EVENTS = loadEvents();
  }
  /* Bo'limga har kirganda saqlangan holatni QAYTA o'qiymiz: remote-storage
     server bilan sinxronlashni sahifa yuklangandan keyin tugatadi, shuning
     uchun bir marta keshlab qo'yilsa boshqa qurilmada kiritilgan mashg'ulot
     ko'rinmay qolardi. */
  function refreshStores() { SCHEDULE = loadSchedule(); EVENTS = loadEvents(); }

  function isLeftWeekActive() {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var ref = new Date(REF_WEEK_START); ref.setHours(0, 0, 0, 0);
    var diffWeeks = Math.floor((today - ref) / (1000 * 60 * 60 * 24 * 7));
    return diffWeeks % 2 === 0;
  }
  function isLessonActive(lesson) {
    if (!lesson.weekType) return true;
    var leftActive = isLeftWeekActive();
    return lesson.weekType === 'left' ? leftActive : !leftActive;
  }
  function toMins(t) { var p = String(t || '').split(':'); return (+p[0] || 0) * 60 + (+p[1] || 0); }
  function nowMins() { var d = new Date(); return d.getHours() * 60 + d.getMinutes(); }
  function durLabel(mins) {
    if (mins <= 0) return '';
    var h = Math.floor(mins / 60), m = mins % 60;
    return (h ? h + ' soat' : '') + (h && m ? ' ' : '') + (m ? m + ' min' : '');
  }
  /* Xulosa kartochkasi tor — u yerda "5s 30d" ko'rinishi ishlatiladi. */
  function durShort(mins) {
    if (mins <= 0) return '—';
    var h = Math.floor(mins / 60), m = mins % 60;
    return (h ? h + 's' : '') + (h && m ? ' ' : '') + (m ? m + 'd' : '');
  }
  /* Kesishuvchi oraliqlarni birlashtirib, jami BAND vaqtni hisoblaydi
     (bir vaqtda ikki ish bo'lsa ikki marta sanalmasin). */
  function busyMins(items) {
    var iv = items.filter(function (x) { return x.start; })
      .map(function (x) { return [toMins(x.start), Math.max(toMins(x.start), toMins(x.end || x.start))]; })
      .sort(function (a, b) { return a[0] - b[0]; });
    if (!iv.length) return 0;
    var merged = [iv[0].slice()];
    for (var i = 1; i < iv.length; i++) {
      var last = merged[merged.length - 1];
      if (iv[i][0] <= last[1]) last[1] = Math.max(last[1], iv[i][1]);
      else merged.push(iv[i].slice());
    }
    return merged.reduce(function (s, x) { return s + (x[1] - x[0]); }, 0);
  }

  /* =========================================================
     KUN YIG'UVCHI — barcha manbalarni bitta ro'yxatga keltiradi.
     Har element: {src, start, end, title, sub, color, emoji, ...}
     `src`: 'plan' (haftalik jadval) | 'event' (bir martalik) | 'boost'
     ========================================================= */
  /* Shu kun uchun to'silgan (LMS bilan takrorlanadigan) qo'lda kiritilgan
     darslar soni — foydalanuvchiga eslatma ko'rsatish uchun. */
  var HIDDEN_DUP = 0;

  /* `includeInactive` — JADVAL (grid) ko'rinishi uchun: 1/2-hafta almashinib
     turadigan darsning HOZIR faol BO'LMAGAN varianti ham qaytariladi
     (`inactiveWeek:true` bilan belgilanib) — eski saytdagi kabi ikkalasi
     ham bir vaqt katagida, xira rangda ko'rinadi. Ro'yxat (list) rejimi
     buni ATAYLAB ishlatmaydi — u yerda faqat HAQIQIY bugungi kun kerak. */
  function localItems(dateStr, includeInactive) {
    ensureLoaded();
    var d = parseKey(dateStr); if (!d) return [];
    var dow = d.getDay(), out = [];

    /* TAKRORLANISHNI TO'SISH — `lmsDup` bayrog'i bo'yicha (markLmsDuplicates
       izohiga qarang). Bayroq DOIMIY, shuning uchun kanikulda LMS bo'sh
       bo'lsa ham qo'lda kiritilgan nusxalar chiqib qolmaydi. LMS uzilgan
       bo'lsa bayroq e'tiborga olinmaydi — jadval to'liq qaytadi. */
    var lmsOn = lmsConnected();

    (SCHEDULE[dow] || []).forEach(function (l, i) {
      var active = isLessonActive(l);
      if (!active && !includeInactive) return;     // 1/2-hafta almashinuvi
      var ki = kindInfo(l.kind), c = lessonCat(l);
      if (lmsOn && l.lmsDup) { HIDDEN_DUP++; return; }
      out.push({
        src: 'plan', day: dow, idx: i,
        start: l.start, end: l.end, title: l.subject, room: l.room || '',
        cat: c, color: catColor(c), emoji: ki.e, kindName: ki.n,
        repeatNote: l.weekType ? (l.weekType === 'left' ? '1-hafta' : '2-hafta') : '',
        inactiveWeek: !active
      });
    });
    (EVENTS[dateStr] || []).forEach(function (l, i) {
      var ki = kindInfo(l.kind), c = lessonCat(l);
      out.push({
        src: 'event', date: dateStr, idx: i,
        start: l.start, end: l.end, title: l.subject, room: l.room || '',
        cat: c, color: catColor(c), emoji: ki.e, kindName: ki.n, done: !!l.done,
        repeatNote: 'bir martalik'
      });
    });
    return out;
  }

  /* Yozuvning turkumi: aniq berilgan `cat` -> turi orqali -> nomidan taxmin.
     Rang ATAYLAB yozuvda saqlanmaydi (eski `l.color` endi ishlatilmaydi):
     bir turkumdagi hamma narsa bir xil rangda bo'lishi kerak, alohida
     saqlangan rang esa buni buzardi. */
  function lessonCat(l) {
    if (l.cat) return l.cat;
    for (var i = 0; i < KINDS.length; i++) if (KINDS[i].k === l.kind) return KINDS[i].cat;
    return guessCat(l.subject || '');
  }

  /* =========================================================
     LMS (lms.tuit.uz) darslari — Sozlamalar > Sessiya orqali ulanadi.
     Server jadvalni saqlab turadi, bu yerda faqat KESHLAB o'qiladi.
     Qo'lda kiritilgan mashg'ulotlar bilan bir xil ko'rinishda chiqadi.
     ========================================================= */
  var LMS_CACHE_KEY = 'lms_schedule_cache_v1';
  var LMS_CONN_KEY = 'lms_connected_v1';
  var LMS = { loaded: false, byDate: {}, promise: null };

  function lmsConnected() {
    try { return localStorage.getItem(LMS_CONN_KEY) === '1'; } catch (e) { return false; }
  }

  /* Serverdan kelgan jadvalni localStorage'ga ham yozamiz: shu bilan sahifa
     BIRINCHI chizilishidayoq darslar joyida bo'ladi (aks holda avval qo'lda
     kiritilganlar, keyin LMS kelib ro'yxat sakrab ketardi) va oflaynda ham
     ko'rinadi. */
  function lmsFromCache() {
    try {
      var v = JSON.parse(localStorage.getItem(LMS_CACHE_KEY) || 'null');
      if (v && typeof v === 'object' && !Array.isArray(v)) return v;
    } catch (e) {}
    return null;
  }
  (function () { var c = lmsFromCache(); if (c) LMS.byDate = c; })();

  window.LmsDay = {
    clear: function () {
      LMS = { loaded: false, byDate: {}, promise: null };
      try { localStorage.removeItem(LMS_CACHE_KEY); } catch (e) {}
    },
    ensureLoaded: function () {
      if (LMS.loaded) return Promise.resolve(LMS.byDate);
      if (LMS.promise) return LMS.promise;
      LMS.promise = App.call('lms_schedule').then(function (j) {
        var by = {};
        (j.lessons || []).forEach(function (l) { (by[l.date] = by[l.date] || []).push(l); });
        LMS.byDate = by; LMS.loaded = true; LMS.promise = null;
        try { localStorage.setItem(LMS_CACHE_KEY, JSON.stringify(by)); } catch (e) {}
        return by;
      }).catch(function () {
        LMS.loaded = true; LMS.promise = null;
        return LMS.byDate;                       // keshdagisi qoladi (oflayn)
      });
      return LMS.promise;
    },
    day: function (dateStr) { return LMS.byDate[dateStr] || []; },
    /* Shu kunda LMS darsi boshlanadigan vaqtlar — takrorlanishni to'sish uchun. */
    startsOn: function (dateStr) {
      var set = {};
      (LMS.byDate[dateStr] || []).forEach(function (l) { set[l.start] = true; });
      return set;
    },
    has: function () {
      for (var k in LMS.byDate) if (LMS.byDate[k] && LMS.byDate[k].length) return true;
      return false;
    },
    connected: lmsConnected,
    setConnected: function (v) {
      try { localStorage.setItem(LMS_CONN_KEY, v ? '1' : '0'); } catch (e) {}
    }
  };

  /* LMS ulanganmi — kuniga bir marta emas, bo'limga har kirganda tekshiriladi
     (arzon so'rov, oflaynda keshdan keladi). */
  function refreshLmsStatus() {
    return App.call('lms_status').then(function (st) {
      LmsDay.setConnected(!!st.connected);
      return st;
    }).catch(function () { return null; });
  }

  /* ==========================================================
     TAKRORIY DARSLARNI DOIMIY BELGILASH.

     Muammo: qo'lda kiritilgan haftalik jadval HAR HAFTA takrorlanadi, LMS esa
     ANIQ SANALI darslar beradi. Ilgari takrorlanish "shu kunda LMS'da shu
     vaqtda dars bormi" degan tekshiruv bilan to'silardi — bu KANIKULDA
     buzilardi: LMS bo'sh qaytadi, tekshiruv ishlamaydi va qo'lda kiritilgan
     darslar ta'til kunlarida ham chiqib turardi (dars yo'q bo'lsa ham).

     Yechim: LMS ma'lumoti BOR paytda mos kelgan yozuvga `lmsDup` bayrog'i
     qo'yiladi va SAQLANADI. Keyin LMS bo'sh bo'lsa ham (kanikul) o'sha
     yozuvlar ko'rsatilmaydi — chunki ular LMS beradigan darsning nusxasi
     ekani allaqachon aniqlangan. LMS uzilsa — bayroq e'tiborga olinmaydi va
     jadval avvalgidek to'liq qaytadi. */
  /* Fan nomini solishtirish uchun soddalashtirish: qavs ichidagi kod olib
     tashlanadi va apostrof turlari birxillashtiriladi.
       "Ehtimollar va statistika (MTH009-1)" -> "ehtimollar va statistika"
       "Sun’iy intellekt asoslari (M)"       -> "sun'iy intellekt asoslari"
     Shu bilan qo'lda kiritilgan yozuv LMS'dagi bilan mos kelishi aniqlanadi. */
  function normSubject(s) {
    return String(s || '')
      .replace(/\([^)]*\)/g, ' ')
      .replace(/[’‘`´]/g, "'")
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .trim();
  }

  function markLmsDuplicates() {
    if (!LmsDay.has()) return false;
    ensureLoaded();
    var changed = false;

    // LMS beradigan fan NOMLARI (butun jadval bo'yicha) — hafta kunidan
    // qat'iy nazar. Bu muhim: LMS bir haftalik oyna beradi, qo'lda kiritilgan
    // jadval esa 6 kunga yoyilgan; faqat vaqt bo'yicha solishtirsak, LMS
    // qamramagan kundagi nusxa belgilanmay qolardi.
    var lmsNames = {};
    Object.keys(LMS.byDate).forEach(function (dt) {
      (LMS.byDate[dt] || []).forEach(function (l) {
        var n = normSubject(l.subject);
        if (n) lmsNames[n] = true;
      });
    });

    Object.keys(SCHEDULE).forEach(function (dow) {
      (SCHEDULE[dow] || []).forEach(function (l) {
        if ((l.kind || 'dars') !== 'dars' || l.lmsDup) return;
        if (lmsNames[normSubject(l.subject)]) { l.lmsDup = true; changed = true; }
      });
    });

    // Nomi boshqacha yozilgan bo'lsa ham — o'sha kun va o'sha vaqtda LMS darsi
    // bo'lsa, bu aniq nusxa.
    Object.keys(LMS.byDate).forEach(function (dt) {
      var d = parseKey(dt); if (!d) return;
      var starts = LmsDay.startsOn(dt);
      (SCHEDULE[d.getDay()] || []).forEach(function (l) {
        if ((l.kind || 'dars') !== 'dars' || l.lmsDup) return;
        if (starts[l.start]) { l.lmsDup = true; changed = true; }
      });
    });

    if (changed) saveSchedule();
    return changed;
  }

  /* Avto-yangilash: kuniga bir marta (sozlamada yoqilgan bo'lsa). Server
     tomon `auto_sync` bayrog'ini saqlaydi, bu yerda kun kaliti bilan
     takrorlanmasligi ta'minlanadi. */
  var AUTO_KEY = 'lms_last_auto_sync';
  function maybeAutoSync() {
    var today = todayKey();
    try { if (localStorage.getItem(AUTO_KEY) === today) return; } catch (e) { return; }
    App.call('lms_status').then(function (st) {
      if (!st.connected || !st.auto_sync) return;
      try { localStorage.setItem(AUTO_KEY, today); } catch (e) {}
      return App.call('lms_sync', {}).then(function () {
        LmsDay.clear();
        return LmsDay.ensureLoaded().then(renderDay);
      });
    }).catch(function () {});
  }

  function lmsItems(dateStr) {
    var d = parseKey(dateStr);
    // LMS yozgi ta'tilda (Iyul - 6, Avgust - 7) ham adashib dars qaytarsa, ularni to'sib qolamiz.
    if (d && (d.getMonth() === 6 || d.getMonth() === 7)) return [];

    /* LMS darslari — hammasi "Dars / kurs" turkumida. Ilgari dars TURIGA
       (ma'ruza/amaliyot/laboratoriya) qarab turli rang berilardi; endi
       majburiy darslar bitta rangda, turi matnda ko'rsatiladi. */
    return LmsDay.day(dateStr).map(function (l) {
      return {
        src: 'lms', start: l.start, end: l.end,
        title: l.subject, room: [l.room, l.stream].filter(Boolean).join(' · '),
        cat: 'kurs', color: catColor('kurs'), emoji: '📚',
        kindName: l.type_name || 'Dars', repeatNote: l.type_name || ''
      };
    });
  }

  /* Boostday rejalarini vaqt chizig'iga aylantiradi.

     VAQT BO'LIM DARAJASIDA (`task_groups[].time`) — vazifa matnida emas.
     Shuning uchun har BO'LIM alohida satr bo'lib chiqadi, ichida o'z
     vazifalari bilan. Vaqti yo'q bo'limlar rejaning umumiy vaqtiga
     yig'iladi (bitta "reja" satri) — aks holda ular vaqt chizig'idan
     butunlay tushib qolardi. */
  function boostItems(dateStr) {
    if (!window.BoostDay) return [];
    var d = parseKey(dateStr); if (!d) return [];
    var out = [];
    BoostDay.dayItems(dateStr, d.getDay()).forEach(function (b) {
      if (b.planType === 'challenge') return;
      var groups = b.groups || [];
      var untimed = [];

      groups.forEach(function (g) {
        var r = splitRange(g.time);
        if (!r) { untimed.push(g); return; }
        var done = g.tasks.filter(function (t) { return t.status === 1; }).length;
        /* Turkum: .md dan kelgan aniq `cat`, bo'lmasa bo'lim nomidan
           (va ichidagi vazifalardan) taxmin qilinadi. */
        var c = g.cat || guessCat(g.name + ' ' + g.tasks.map(function (t) { return t.text; }).join(' '));
        out.push({
          src: 'boost_group', planId: b.planId, groupName: g.name,
          start: r.start, end: r.end,
          /* `room` ATAYLAB bo'sh: ilgari bu yerga kanal nomi yozilardi va
             jadvalda har blokda "My daily life" takrorlanib, vaqt satrini
             siqib chiqarardi. Kanal nomi bo'lim haqida hech nima aytmaydi. */
          title: g.name || b.title, room: '',
          cat: c, color: catColor(c), emoji: catInfo(c).e, kindName: 'Reja bo\'limi',
          tasks: g.tasks, total: g.tasks.length, doneCount: done,
          done: done === g.tasks.length && g.tasks.length > 0
        });
      });

      /* Vaqtsiz bo'limlar — rejaning o'z vaqti bilan bitta satr */
      if (untimed.length) {
        var tasks = [];
        untimed.forEach(function (g) { tasks = tasks.concat(g.tasks); });
        var pr = splitRange(b.time);
        var doneN = tasks.filter(function (t) { return t.status === 1; }).length;
        out.push({
          src: 'boost', planId: b.planId,
          start: pr ? pr.start : '', end: pr ? pr.end : '',
          title: b.title, channelName: b.channelName, color: b.color,
          emoji: b.emoji || '⚡', kindName: b.typeName,
          tasks: tasks, total: tasks.length, doneCount: doneN
        });
      }
    });
    return out;
  }

  /* "08:00 - 09:30" | "08:00-09:30" | "08:00" -> {start,end}; aks holda null */
  function splitRange(s) {
    var m = String(s || '').trim().match(/^(\d{1,2}:\d{2})(?:\s*[-–—]\s*(\d{1,2}:\d{2}))?$/);
    if (!m) return null;
    var pad = function (x) { return x.length === 4 ? '0' + x : x; };
    return { start: pad(m[1]), end: m[2] ? pad(m[2]) : '' };
  }

  function sortItems(list) {
    return list.slice().sort(function (a, b) {
      var av = a.start ? toMins(a.start) : 99999, bv = b.start ? toMins(b.start) : 99999;
      if (av !== bv) return av - bv;
      return String(a.title).localeCompare(String(b.title));
    });
  }

  /* --- Joriy holat: 'past' (tugagan) | 'live' (hozir) | 'next' (kelasi) --- */
  function statusOf(it, isToday) {
    if (!isToday || !it.start) return '';
    var n = nowMins(), s = toMins(it.start), e = it.end ? toMins(it.end) : s + 60;
    if (n >= e) return 'past';
    if (n >= s) return 'live';
    return '';
  }

  /* =========================================================
     VIEW: kun
     ========================================================= */
  var SEL_DATE = null;          // 'YYYY-MM-DD'
  var OPEN_PLAN = null;         // vaqt chizig'ida ochiq turgan Boostday reja id
  /* Bosh sahifadagi "Kunlik statistika" halqasidan kelinganda ochilishi
     kerak bo'lgan BO'LIM NOMI (`?open=...`). Nom bo'yicha ishlaymiz, chunki
     `BoostDay.dayGroups()` guruhlarni nom bo'yicha yig'adi va planId bermaydi. */
  var WANT_OPEN = '';

  /* Ko'rinish rejimi: 'list' — kunlik vaqt chizig'i, 'grid' — haftalik jadval.
     Tanlov localStorage'da (remote-storage server bilan sinxronlaydi). */
  var VIEW_KEY = 'kun_view_v1';
  function kunView() {
    try { return localStorage.getItem(VIEW_KEY) === 'grid' ? 'grid' : 'list'; } catch (e) { return 'list'; }
  }
  function setKunView(v) {
    try { localStorage.setItem(VIEW_KEY, v === 'grid' ? 'grid' : 'list'); } catch (e) {}
  }

  /* Joriy rejimga qarab kerakli chizuvchini chaqiradi — barcha
     "yuklangach qayta chiz" nuqtalari shuni ishlatadi. */
  function renderBody() {
    if (kunView() === 'grid') renderGrid(); else renderDay();
  }

  App.view('kun', {
    nav: 'kun',
    render: function (page, params) {
      refreshStores();
      // Sana: ?date=YYYY-MM-DD. Eski ?d=<hafta kuni> havolalari ham ishlaydi —
      // shu hafta kunining joriy haftadagi sanasiga aylantiriladi.
      var sel = params.date && parseKey(params.date) ? params.date : null;
      if (!sel && params.d !== undefined && params.d !== '') {
        var want = parseInt(params.d, 10), t = new Date();
        sel = dkey(addDays(t, (want - t.getDay() + 7) % 7));
      }
      SEL_DATE = sel || todayKey();
      OPEN_PLAN = null;
      WANT_OPEN = String(params.open || '').trim();
      var mode = kunView();

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 style="display:flex;align-items:center;gap:6px">Kun hisobi <label style="cursor:pointer;color:var(--accent);display:flex"><span data-icon="calendar" data-icon-size="18"></span><input type="date" style="position:absolute;opacity:0;width:1px;height:1px;overflow:hidden;padding:0;border:0" onchange="App.go(\'kun\', {date: this.value})"></label></h1>' +
        '<div style="flex:1"></div>' +
        '<button class="icon-btn ghost" data-act="kunImport" aria-label="Fayldan yuklash" title="Fayldan yuklash"><span data-icon="upload" data-icon-size="19"></span></button>' +
        '<button class="icon-btn ghost" data-act="kunAdd" aria-label="Qo\'shish"><span data-icon="plus" data-icon-size="20"></span></button></div>' +
        /* Bitta ixcham qator: chapda hafta o'qlari, o'ngda rejim tanlagichi */
        '<div class="kun-bar">' +
        '<div id="kun-nav"></div>' +
        '<div class="seg seg-sm" id="kun-modes">' +
        '<button class="' + (mode === 'list' ? 'active' : '') + '" data-act="kunMode" data-arg=\'{"m":"list"}\'>Kun</button>' +
        '<button class="' + (mode === 'grid' ? 'active' : '') + '" data-act="kunMode" data-arg=\'{"m":"grid"}\'>Jadval</button>' +
        '</div></div>' +
        '<div id="kun-week"></div>' +
        '<div id="kun-sum"></div>' +
        '<div id="kun-list"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      renderWeek();
      renderBody();
      // Serverdan kelgan manbalar (LMS darslari, Boostday rejalari, sport)
      // yuklangach vaqt chizig'i qayta chiziladi.
      Promise.all([LmsDay.ensureLoaded(), refreshLmsStatus()]).then(function () {
        markLmsDuplicates();
        renderWeek(); renderBody();
        maybeAutoSync();
      });
      if (window.BoostDay) BoostDay.ensureLoaded().then(renderBody).catch(function () {});
      if (window.SportBridge) SportBridge.ensureLoaded().then(renderBody).catch(function () {});
      bindGridResize();
    },
    leave: function () { unbindGridResize(); }
  });

  App.actions.kunMode = function (a) {
    if (kunView() === a.m) return;
    setKunView(a.m);
    App.reload();
  };

  /* ---------- Hafta chizig'i (haqiqiy sanalar bilan) ----------
     JADVAL rejimida kun chiplari CHIZILMAYDI: jadvalning o'z ustun
     sarlavhalari (`.kg-dh`) aynan shu vazifani bajaradi — ikkalasi
     birga turganda bir xil sana ikki qator bo'lib takrorlanardi va
     ortiqcha joy egallardi. Hafta almashtirish o'qlari ikkala rejimda
     ham kerak, shuning uchun ular qoladi. */
  function renderWeek() {
    var box = App.el('kun-week'); if (!box) return;
    var navBox = App.el('kun-nav');
    var sel = parseKey(SEL_DATE), tKey = todayKey();
    // Hafta dushanbadan boshlanadi
    var start = addDays(sel, -(((sel.getDay() + 6) % 7)));
    var days = [];
    for (var i = 0; i < 7; i++) days.push(addDays(start, i));
    var isGrid = kunView() === 'grid';

    var chips = isGrid ? '' :
      '<div class="kun-days">' +
      days.map(function (d) {
        var k = dkey(d), n = localItems(k).length + lmsItems(k).length + boostItems(k).length;
        return '<button class="chip-btn' + (k === SEL_DATE ? ' active' : '') + (k === tKey ? ' is-today' : '') +
          '" data-act="kunGo" data-arg=\'' + App.arg({ date: k }) + '\'>' +
          '<b>' + DAY_SHORT[d.getDay()] + '</b><i>' + d.getDate() + '</i>' +
          (n ? '<u></u>' : '') + '</button>';
      }).join('') + '</div>';

    /* Jadvalda "bugun" shu haftada bo'lsa yetarli — kun tanlash muhim emas.
       Ro'yxatda esa aniq SANA tanlangani uchun bugundan chetlashsa ko'rsatamiz. */
    var offToday = isGrid
      ? !days.some(function (d) { return dkey(d) === tKey; })
      : SEL_DATE !== tKey;

    /* Hafta o'qlari + "bugunga qaytish" — hammasi yuqoridagi ixcham
       qatorda (rejim tanlagichi yonida). Qaytish tugmasi faqat bugundan
       (jadvalda — bugungi haftadan) chetlashganda paydo bo'ladi. */
    if (navBox) {
      navBox.innerHTML =
        '<div class="kun-wknav">' +
        '<button class="hm-arrow" data-act="kunWeek" data-arg=\'' + App.arg({ n: -7 }) + '\' aria-label="Oldingi hafta">' +
        '<span data-icon="arrowLeft" data-icon-size="13"></span></button>' +
        '<span class="kun-wklabel">' + shortDate(days[0]) + ' — ' + shortDate(days[6]) + '</span>' +
        '<button class="hm-arrow" data-act="kunWeek" data-arg=\'' + App.arg({ n: 7 }) + '\' aria-label="Keyingi hafta">' +
        '<span data-icon="arrowLeft" data-icon-size="13" style="transform:rotate(180deg)"></span></button>' +
        (offToday
          ? '<button class="kun-todaybtn" data-act="kunGo" data-arg=\'' + App.arg({ date: tKey }) + '\' ' +
            'title="' + (isGrid ? 'Bugungi haftaga qaytish' : 'Bugunga qaytish') + '">↺ Bugun</button>'
          : '') +
        '</div>';
      App.icons(navBox);
    }

    box.innerHTML = chips;
    App.icons(box);
  }

  App.actions.kunGo = function (a) { App.go('kun', { date: a.date }); };
  App.actions.kunWeek = function (a) {
    var d = parseKey(SEL_DATE) || new Date();
    App.go('kun', { date: dkey(addDays(d, parseInt(a.n, 10))) });
  };
  /* ---------- Kun xulosasi ---------- */
  function renderSummary(items, isToday) {
    var box = App.el('kun-sum'); if (!box) return;
    var timed = items.filter(function (x) { return x.start; });
    if (!timed.length) { box.innerHTML = ''; return; }

    var first = Math.min.apply(null, timed.map(function (x) { return toMins(x.start); }));
    var last = Math.max.apply(null, timed.map(function (x) { return toMins(x.end || x.start); }));
    var span = Math.max(0, last - first);

    // Kun qay darajada o'tgani (faqat bugun uchun)
    var passed = isToday ? Math.max(0, Math.min(100, Math.round((nowMins() - first) * 100 / (span || 1)))) : 0;

    // Eng yaqin bo'sh vaqtni hisoblash
    var nextFreeHtml = '';
    if (isToday) {
      var n = nowMins();
      var evs = [];
      timed.forEach(function (x) {
        var s = toMins(x.start), e = toMins(x.end || x.start);
        if (e > s) { evs.push({ t: s, v: 1 }); evs.push({ t: e, v: -1 }); }
        else { evs.push({ t: s, v: 1 }); evs.push({ t: s + 30, v: -1 }); }
      });
      evs.sort(function (a, b) { return a.t - b.t || b.v - a.v; });
      var bc = 0, lt = 0, gaps = [];
      evs.forEach(function (ev) {
        if (bc === 0 && ev.t > lt) gaps.push({ s: lt, e: ev.t });
        bc += ev.v;
        lt = ev.t;
      });
      if (bc === 0 && lt < 24 * 60) gaps.push({ s: lt, e: 24 * 60 });

      var nf = null;
      for (var i = 0; i < gaps.length; i++) {
        if (gaps[i].e > n) {
          nf = { s: Math.max(n, gaps[i].s), e: gaps[i].e };
          break;
        }
      }
      if (nf && (nf.e - nf.s >= 5)) {
        var dText = durShort(nf.e - nf.s);
        var tText = '';
        if (nf.e >= 24 * 60) {
          if (nf.s === n) tText = 'Hozir kun oxirigacha bo\'shsiz';
          else tText = 'Eng yaqin bo\'sh vaqt: ' + fmtHM(nf.s) + ' dan kun oxirigacha';
        } else {
          if (nf.s === n) tText = 'Hozir ' + fmtHM(nf.e) + ' gacha bo\'shsiz (' + dText + ')';
          else tText = 'Eng yaqin bo\'sh vaqt: ' + fmtHM(nf.s) + ' - ' + fmtHM(nf.e) + ' (' + dText + ')';
        }
        nextFreeHtml = '<div style="font-size:12.5px;text-align:center;color:var(--success);font-weight:600;margin:-8px 0 12px;letter-spacing:0.2px;opacity:0.9">✨ ' + tText + '</div>';
      }
    }

    box.innerHTML =
      nextFreeHtml +
      '<div class="kun-band"><span>' + fmtHM(first) + '</span>' +
      '<div class="kun-track">' + (isToday ? '<i style="width:' + passed + '%"></i>' : '') + '</div>' +
      '<span>' + fmtHM(last) + '</span></div>';
  }
  function fmtHM(m) { return ('0' + Math.floor(m / 60)).slice(-2) + ':' + ('0' + (m % 60)).slice(-2); }

  /* ---------- Kun vaqt chizig'i ---------- */
  function renderDay() {
    var box = App.el('kun-list'); if (!box) return;
    var isToday = SEL_DATE === todayKey();
    var d = parseKey(SEL_DATE);
    HIDDEN_DUP = 0;
    var items = sortItems(localItems(SEL_DATE).concat(lmsItems(SEL_DATE), boostItems(SEL_DATE)));

    /* Bosh sahifadan `?open=<bo'lim nomi>` bilan kelingan bo'lsa — o'sha
       bo'limni DARHOL ochiq holda chizamiz (foydalanuvchi qidirib
       o'tirmasin). Faqat BIR MARTA: keyin oddiy bosish bilan
       ochib-yopish ishlayveradi. */
    if (WANT_OPEN) {
      var wanted = null;
      items.forEach(function (x) {
        if (!wanted && x.src === 'boost_group' && String(x.groupName || '') === WANT_OPEN) wanted = x;
      });
      if (wanted) OPEN_PLAN = wanted.planId + '|' + wanted.groupName;
      WANT_OPEN = '';
    }
    var dupNote = HIDDEN_DUP
      ? '<div class="kun-note">' + HIDDEN_DUP + ' ta qo\'lda kiritilgan dars LMS bilan takrorlangani uchun ' +
        'ko\'rsatilmadi. <button class="lib-cr" data-act="kunCleanDup">Butunlay tozalash</button></div>'
      : '';

    var head = '<div class="between" style="margin:2px 0 10px">' +
      '<h2 style="font-size:16px;font-weight:700;margin:0">' + DAY_FULL[d.getDay()] +
      '<span class="muted" style="font-weight:600;font-size:12.5px"> · ' + shortDate(d) + '</span></h2>' +
      (isToday ? '<span class="kun-nowchip">hozir ' + fmtHM(nowMins()) + '</span>' : '') + '</div>';

    renderSummary(items, isToday);

    var timed = items.filter(function (x) { return x.start; });
    var untimed = items.filter(function (x) { return !x.start; });

    var html = head + dupNote;
    if (!timed.length && !untimed.length) {
      box.innerHTML = html + App.empty({
        icon: 'calendar', title: 'Bu kun bo\'sh',
        text: 'Yuqoridagi + tugmasi bilan mashg\'ulot qo\'shing yoki ⬆ orqali .md jadval yuklang.'
      });
      App.icons(box);
      return;
    }

    // Vaqt chizig'i: "hozir" markeri va oraliqdagi bo'sh vaqt qatorlari bilan
    var nowShown = !isToday, n = nowMins(), prevEnd = null;
    timed.forEach(function (it) {
      var s = toMins(it.start);
      if (!nowShown && n < s) { html += nowRowHtml(n); nowShown = true; }
      if (prevEnd !== null && s - prevEnd >= 30) html += gapRowHtml(prevEnd, s);
      html += rowHtml(it, statusOf(it, isToday));
      prevEnd = Math.max(prevEnd === null ? 0 : prevEnd, toMins(it.end || it.start));
    });
    if (!nowShown) html += nowRowHtml(n);

    /* Vaqti yo'q ishlar (sport mashqlari va vaqtsiz reja bo'limlari).
       Ilgari `untimed` hisoblanardi-yu, HECH QAYERGA chizilmasdi — ular
       kun ro'yxatidan butunlay tushib qolardi. */
    if (untimed.length) {
      html += '<div class="list-label" style="margin-top:16px">Vaqti belgilanmagan</div>' +
        untimed.map(function (it) { return rowHtml(it, ''); }).join('');
    }

    box.innerHTML = html;
    App.icons(box);

    /* Ochiq bo'lim ekrandan tashqarida qolishi mumkin (kun uzun bo'lsa) —
       uni yumshoq surib ko'rsatamiz. */
    if (OPEN_PLAN) {
      var openEl = box.querySelector('.kun-tasks');
      if (openEl && openEl.previousElementSibling) {
        try { openEl.previousElementSibling.scrollIntoView({ block: 'center', behavior: 'smooth' }); } catch (e) {}
      }
    }
  }

  /* =========================================================
     HAFTALIK JADVAL ko'rinishi (klassik dars jadvali kabi)

     7 ustun (Dush..Yak) × vaqt o'qi. Har mashg'ulot o'z boshlanish/tugash
     vaqtiga qarab ustun ichida joylashadi (mutlaq joylashuv), shuning uchun
     bir vaqtga to'g'ri kelganlar yonma-yon ko'rinadi.
     ========================================================= */
  var GRID_SLOT = 30;           // vaqt o'qidagi belgi qadami (daqiqa)

  function weekStartOf(dateStr) {
    var d = parseKey(dateStr) || new Date();
    return addDays(d, -(((d.getDay() + 6) % 7)));   // dushanbadan
  }

  /* ---------- Vaqt o'qi: CHIZIQLI EMAS, NISBIY ----------
     Muammo: 7 soatlik "Kurs" kabi uzun blok ekranning yarmini band qilib,
     30 daqiqalik "Tushlik" kabi qisqa ishlarni deyarli ko'rinmas qilib
     qo'yardi (chiziqli shkalada balandlik = daqiqa soni × doimiy son).

     Yechim: haftadagi barcha mashg'ulotlarning boshlanish/tugash
     nuqtalari yig'ib olinadi, ular orasidagi HAR BIR oraliq alohida
     KVADRAT ILDIZ bilan siqiladi, so'ng ketma-ket qo'shib chiqiladi.
     Ildiz olish qisqa oraliqni deyarli o'zgartirmaydi, uzunini esa
     sezilarli qisqartiradi: 30 daqiqa -> √30≈5.5, 450 daqiqa (7.5 soat)
     -> √450≈21.2 — xom holda 15 marta farq bo'lsa, ekranda atigi ~4 marta
     farq qoladi. Natija: uzun blok siqiladi, qisqa ishlar o'qib bo'ladigan
     bo'ladi, umumiy balandlik ham qisqarib scroll kamayadi.

     Bitta umumiy o'q BUTUN HAFTAGA (barcha 7 ustunga) tegishli, shuning
     uchun nuqtalar barcha kunlar bo'yicha birlashtiriladi. */
  /* 1/2 — KVADRAT ILDIZ. Foydalanuvchi so'roviga ko'ra kub ildizdan (1/3)
     qaytarildi. O'lchangan natija (30 daq "Tushlik" / 7.5 soat "Kurs"
     nisbati, GRID_SCALE=1.5 bilan birga):
       chiziqli (eski)         — 15x   (xom vaqt bilan bir xil)
       kub ildiz (1/3, o'tgan) — 2.6x
       kvadrat ildiz (hozirgi, 1/2) — 4.1x
     Kvadrat ildiz kub ildizdan KAMROQ siqadi (daraja kattaroq bo'lgani
     uchun) — uzun ish (Kurs) qisqasiga nisbatan yana bir oz kattaroq
     ko'rinadi, lekin hamon chiziqlidan ancha yumshoq. */
  var GRID_POWER = 1 / 2;       // 1 = chiziqli, kichikroq = kuchliroq siqish
  /* GRID_SCALE — foydalanuvchi so'roviga ko'ra qo'shildi: nisbatlarni
     BUZMASDAN hammasini bab-baravar kattalashtiradi ("chiqqan qiymatni
     hammasiga ko'paytirsang nisbat saqlanadi"). Matematik jihatdan bu
     to'g'ri — GRID_PX_PER_UNIT chiziqli koeffitsiyent bo'lgani uchun uni
     ko'paytirish har bir segmentni BIR XIL nisbatda kattalashtiradi,
     ikkita segment orasidagi nisbat (masalan 2.6x) o'zgarmaydi.
     1.5 tanlandi (2 emas): 30 daq blok 27px->40px (bosish uchun qulayroq),
     umumiy balandlik esa (sinov ma'lumotida) 368px->552px — hali ham eski
     chiziqli holatdan (918px) sezilarli qisqaroq. 2x qilinsa 736px chiqib,
     "juda uzun sahifa" muammosiga qaytardi. */
  var GRID_SCALE = 1.5;
  /* Kalibrlash: 30 daqiqalik (GRID_SLOT) oraliq AVVALGI chiziqli o'lcham
     bilan BIR XIL (27px) qolsin — faqat undan UZUNROQ narsalar siqiladi.
     Shunda "qisqa ish avvalgidek, uzun ish kichikroq" so'zma-so'z bajariladi
     (kalibrlash bo'lmasa — masalan doim 15px/birlik desak — natija AKSINCHA
     avvalgidan ancha KATTA chiqib qolishi mumkin, sinovda shunday bo'lgan).
     GRID_SCALE shu 27px'ning o'ziga qo'llanadi — shuning uchun kattalashtirish
     ANCHOR nuqtasidan boshlab BUTUN egri chiziqqa proporsional tarqaladi. */
  var GRID_PX_PER_UNIT = (27 * GRID_SCALE) / Math.pow(GRID_SLOT, GRID_POWER);
  var GRID_MIN_H = Math.round(22 * GRID_SCALE);   // BITTA mashg'ulot uchun eng kam balandlik
  /* BUTUN jadval uchun eng kam balandlik. Siqish kuchli bo'lgani uchun
     kunda 1-2 ta qisqa ish bo'lsa (masalan hafta oxiri bo'sh bo'lsa),
     hisoblangan balandlik juda kichik (~60-100px) chiqib, jadval singan/
     "buzilgan" ko'rinishga kelishi mumkin edi — bu shunga qarshi pol. */
  var GRID_MIN_TOTAL_H = 300;

  function buildTimeScale(days, minM, maxM) {
    var bounds = {}; bounds[minM] = 1; bounds[maxM] = 1;
    days.forEach(function (day) {
      day.timed.forEach(function (it) {
        var s = toMins(it.start), e = endMins(it);
        if (s >= minM && s <= maxM) bounds[s] = 1;
        if (e >= minM && e <= maxM) bounds[e] = 1;
      });
    });
    var pts = Object.keys(bounds).map(Number).sort(function (a, b) { return a - b; });
    var y = [0];
    for (var i = 1; i < pts.length; i++) {
      y.push(y[i - 1] + Math.pow(pts[i] - pts[i - 1], GRID_POWER) * GRID_PX_PER_UNIT);
    }
    function topOf(m) {
      if (m <= pts[0]) return Math.round(y[0]);
      if (m >= pts[pts.length - 1]) return Math.round(y[y.length - 1]);
      var lo = 0, hi = pts.length - 1;             // ikkilik qidiruv
      while (hi - lo > 1) {
        var mid = (lo + hi) >> 1;
        if (pts[mid] <= m) lo = mid; else hi = mid;
      }
      var frac = (m - pts[lo]) / (pts[hi] - pts[lo]);
      return Math.round(y[lo] + frac * (y[hi] - y[lo]));
    }
    return { topOf: topOf, height: Math.round(y[y.length - 1]) };
  }

  /* Bir vaqtga to'g'ri kelgan mashg'ulotlarni YONMA-YON joylashtirish.

     Avval o'zaro kesishadigan ishlar bitta "to'da"ga yig'iladi, keyin
     to'da ichida har biri bo'sh "yo'lak"ka tushadi. Natijada ustun
     kengligi yo'laklar soniga bo'linadi — hech biri ikkinchisini
     bekitmaydi (jadvalda bir vaqtda ikki dars bo'lishi odatiy hol). */
  function layoutLanes(items) {
    var sorted = items.slice().sort(function (a, b) {
      var d = toMins(a.start) - toMins(b.start);
      return d || (endMins(a) - endMins(b));
    });
    var out = [], cluster = [], clusterEnd = -1;

    function flush() {
      if (!cluster.length) return;
      var lanes = [];                      // lanes[i] = shu yo'lakning tugash vaqti
      cluster.forEach(function (it) {
        var s = toMins(it.start), e = endMins(it), placed = -1;
        for (var i = 0; i < lanes.length; i++) {
          if (lanes[i] <= s) { lanes[i] = e; placed = i; break; }
        }
        if (placed < 0) { lanes.push(e); placed = lanes.length - 1; }
        it._lane = placed;
      });
      cluster.forEach(function (it) { it._lanes = lanes.length; out.push(it); });
      cluster = []; clusterEnd = -1;
    }

    sorted.forEach(function (it) {
      var s = toMins(it.start);
      if (cluster.length && s >= clusterEnd) flush();
      cluster.push(it);
      clusterEnd = Math.max(clusterEnd, endMins(it));
    });
    flush();
    return out;
  }
  function endMins(it) { return it.end ? toMins(it.end) : toMins(it.start) + 60; }

  /* "7 soat 30 min" — kun sarlavhasidagi umumiy band vaqt */
  function busyLabel(items) {
    var m = busyMins(items);
    if (!m) return '';
    var h = Math.floor(m / 60), r = m % 60;
    return (h ? h + ' soat' : '') + (r ? (h ? ' ' : '') + r + ' min' : '');
  }

  /* Mobilda BITTA kun ustuni to'liq kenglikda, keyingisi chekkadan bir
     siltim ko'rinib turadi (eski saytdagi kabi) — 7 tasini siqib
     o'qib bo'lmaydigan qilib qo'yish o'rniga chapga/o'ngga surib
     ko'riladi. Desktopda (>=920px) hammasi baribir sig'gani uchun
     eski teng-ustunli (`1fr`) tartib saqlanadi — `null` shuni bildiradi. */
  function gridColMetrics(box) {
    if ((window.innerWidth || 1024) >= 920) return null;
    var w = (box && box.clientWidth) || document.documentElement.clientWidth || 360;
    var axis = w < 380 ? 34 : 40;
    var peek = 26;                              // keyingi kun shu qadar ko'rinib tursin
    var day = Math.max(200, Math.round(w - axis - peek));
    return { axis: axis, day: day };
  }

  var GRID_RESIZE_T = null;
  function onGridResize() {
    clearTimeout(GRID_RESIZE_T);
    GRID_RESIZE_T = setTimeout(function () { if (kunView() === 'grid') renderGrid(); }, 200);
  }
  function bindGridResize() { window.addEventListener('resize', onGridResize); }
  function unbindGridResize() { window.removeEventListener('resize', onGridResize); clearTimeout(GRID_RESIZE_T); }

  function renderGrid() {
    var box = App.el('kun-list'); if (!box) return;
    var start = weekStartOf(SEL_DATE), tKey = todayKey();
    var cm = gridColMetrics(box);

    // Haftaning 7 kuni uchun ishlarni yig'amiz. `true` — 1/2-hafta
    // almashinuvining HOZIR FAOL BO'LMAGAN varianti ham qaytariladi
    // (xira ko'rinishda, ma'lumot uchun — eski saytdagi kabi).
    var days = [];
    for (var i = 0; i < 7; i++) {
      var d = addDays(start, i), k = dkey(d);
      HIDDEN_DUP = 0;
      var all = sortItems(localItems(k, true).concat(lmsItems(k), boostItems(k)));
      days.push({
        date: k, d: d,
        timed: all.filter(function (x) { return x.start; }),
        untimed: all.filter(function (x) { return !x.start; })
      });
    }

    var total = days.reduce(function (n, x) { return n + x.timed.length + x.untimed.length; }, 0);
    if (!total) {
      box.innerHTML = App.empty({
        icon: 'calendar', title: 'Bu hafta bo\'sh',
        text: 'Yuqoridagi + tugmasi bilan mashg\'ulot qo\'shing yoki ⬆ orqali .md reja yuklang.'
      });
      App.icons(box);
      return;
    }

    // Vaqt oralig'i — eng erta boshlanish va eng kech tugashga qarab
    var minM = 24 * 60, maxM = 0;
    days.forEach(function (day) {
      day.timed.forEach(function (it) {
        var s = toMins(it.start), e = endMins(it);
        if (s < minM) minM = s;
        if (e > maxM) maxM = e;
      });
    });
    if (minM > maxM) { minM = 8 * 60; maxM = 18 * 60; }
    minM = Math.floor(minM / GRID_SLOT) * GRID_SLOT;
    maxM = Math.ceil(maxM / GRID_SLOT) * GRID_SLOT;
    if (maxM - minM < 4 * GRID_SLOT) maxM = minM + 4 * GRID_SLOT;

    var scale = buildTimeScale(days, minM, maxM);
    var height = Math.max(scale.height, GRID_MIN_TOTAL_H);
    var topOf = scale.topOf;

    /* Chap ustun: har 30 daqiqada belgi. Yonidagi chiziq to'liq soatda
       to'q, yarim soatda punktir — jadval o'qilishi osonlashadi. */
    var marks = '', lines = '';
    for (var t = minM; t <= maxM; t += GRID_SLOT) {
      var full = (t % 60) === 0;
      marks += '<div class="kgt' + (full ? ' full' : '') + '" style="top:' + topOf(t) + 'px">' +
        fmtHM(t) + '</div>';
      lines += '<div class="kgl' + (full ? ' full' : '') + '" style="top:' + topOf(t) + 'px"></div>';
    }

    var isThisWeek = days.some(function (x) { return x.date === tKey; });
    var nowLine = '';
    if (isThisWeek) {
      var nm = nowMins();
      if (nm >= minM && nm <= maxM) nowLine = '<div class="kg-now" style="top:' + topOf(nm) + 'px"></div>';
    }

    var cols = days.map(function (day) {
      var items = layoutLanes(day.timed).map(function (it) {
        var s = toMins(it.start), e = endMins(it);
        var hgt = Math.max(GRID_MIN_H, (topOf(e) - topOf(s)) - 2);
        var w = 100 / (it._lanes || 1);
        var st = statusOf(it, day.date === tKey);
        var meta = it.start + (it.end ? ' - ' + it.end : '') + (it.room ? ' · ' + it.room : '');
        var col = it.color || 'var(--accent)';
        var style = 'top:' + topOf(s) + 'px;height:' + hgt + 'px;' +
          'left:' + (it._lane * w) + '%;width:calc(' + w + '% - 2px);background:' + col;
        var body = '<i>' + App.esc(meta) + '</i>' +
          '<b>' + App.esc((it.emoji ? it.emoji + ' ' : '') + it.title) + '</b>' +
          (it.inactiveWeek ? '<em>Keyingi hafta</em>' : '');

        /* Almashinuvning HOZIR FAOL BO'LMAGAN varianti — faqat ma'lumot
           uchun (xira), bosilmaydi: bosilsa o'sha kunning ro'yxatida
           umuman ko'rinmaydi (list rejimi ularni chiqarmaydi), shuning
           uchun tugma emas — oddiy <div>. */
        if (it.inactiveWeek) {
          return '<div class="kgi otherweek" style="' + style + '" title="' +
            App.esc(meta + ' · ' + it.title + ' · keyingi hafta') + '">' + body + '</div>';
        }
        return '<button class="kgi' + (st === 'past' ? ' past' : '') + (st === 'live' ? ' live' : '') +
          (it.done ? ' done' : '') + '" style="' + style + '" ' +
          'data-act="kunGridOpen" data-arg=\'' + App.arg({ date: day.date }) + '\' ' +
          'title="' + App.esc(meta + ' · ' + it.title) + '">' + body + '</button>';
      }).join('');

      return '<div class="kgc' + (day.date === tKey ? ' is-today' : '') + '">' + items + '</div>';
    }).join('');

    var heads = days.map(function (day) {
      // Xulosa faqat HOZIR FAOL darslar bo'yicha — "keyingi hafta"gi
      // variant vaqtni ikki marta hisoblamasin.
      var lbl = busyLabel(day.timed.filter(function (x) { return !x.inactiveWeek; }));
      /* SANA ham ko'rsatiladi: ilgari band vaqt yozuvi sanani butunlay
         siqib chiqarardi va qaysi ustun qaysi kun ekanini bilib bo'lmasdi
         (yuqoridagi "10 avg — 16 avg" faqat oraliqni aytadi). */
      return '<button class="kgh' + (day.date === tKey ? ' is-today' : '') +
        (day.date === SEL_DATE ? ' is-sel' : '') + '" data-act="kunGo" data-arg=\'' +
        App.arg({ date: day.date }) + '\'>' +
        '<b>' + DAY_SHORT[day.d.getDay()].toUpperCase() + ' ' + day.d.getDate() + '</b>' +
        '<i>' + (lbl || '—') + '</i></button>';
    }).join('');

    /* Vaqti yo'q ishlar jadval ostida — vaqt o'qiga joylasha olmaydi,
       lekin yo'qolib ham ketmasligi kerak. */
    var extra = '';
    days.forEach(function (day) {
      if (!day.untimed.length) return;
      extra += '<div class="kg-extra"><b>' + DAY_SHORT[day.d.getDay()] + ' ' + day.d.getDate() + '</b>' +
        day.untimed.map(function (it) {
          return '<span class="kg-chip" style="border-left-color:' + (it.color || 'var(--hint)') + '">' +
            App.esc((it.emoji ? it.emoji + ' ' : '') + it.title) + '</span>';
        }).join('') + '</div>';
    });

    /* Mobilda ustun kengligi JS'da hisoblangan (`cm`) — konteynerlarga
       to'g'ridan-to'g'ri `grid-template-columns` beriladi (bolalarga
       alohida `width` emas: grid o'z yo'lagi kengligini o'zi belgilaydi).
       `width:max-content` FAQAT mobilda kerak — grid haqiqiy (7×kenglik)
       o'lchamini olishi uchun, aks holda `.kg2` konteyner enига siqilib,
       gorizontal scroll ishlamay qolardi. Desktopda (`cm===null`) bu
       qo'shilmaydi — CSS'dagi teng-ustunli (`1fr`, konteyner eniga cho'zilgan)
       qoida ishlayveradi. */
    var mobileW = cm ? 'width:max-content;min-width:100%;' : '';
    var headCols = cm ? ' style="' + mobileW + 'grid-template-columns:' + cm.axis + 'px repeat(7,' + cm.day + 'px)"' : '';
    var bodyStyle = mobileW + 'height:' + height + 'px' + (cm ? ';grid-template-columns:' + cm.axis + 'px max-content' : '');
    var colsStyle = cm ? ' style="grid-template-columns:repeat(7,' + cm.day + 'px)"' : '';

    box.innerHTML =
      '<div class="kg2" id="kg2-wrap">' +
      '<div class="kg2-head"' + headCols + '><div class="kgh-corner">VAQT</div>' + heads + '</div>' +
      '<div class="kg2-body" style="' + bodyStyle + '">' +
      '<div class="kg2-times">' + marks + '</div>' +
      '<div class="kg2-cols"' + colsStyle + '>' + lines + nowLine + cols + '</div>' +
      '</div></div>' + extra;
    App.icons(box);

    /* Tanlangan kun (SEL_DATE) darhol ko'rinsin — har doim haftaning
       1-kunidan boshlab ochilmasin. */
    if (cm) {
      var wrap = box.querySelector('#kg2-wrap');
      var idx = -1;
      for (var di = 0; di < days.length; di++) if (days[di].date === SEL_DATE) { idx = di; break; }
      if (wrap && idx > 0) wrap.scrollLeft = idx * cm.day;
    }
  }

  /* Jadvaldagi mashg'ulotga bosilsa — o'sha kunning to'liq ro'yxatiga o'tadi */
  App.actions.kunGridOpen = function (a) {
    setKunView('list');
    App.go('kun', { date: a.date });
  };

  function nowRowHtml(n) {
    return '<div class="kun-now"><span>' + fmtHM(n) + '</span><i></i></div>';
  }
  function gapRowHtml(from, to) {
    return '<div class="kun-gap"><span>' + durLabel(to - from) + ' bo\'sh</span></div>';
  }

  function rowHtml(it, st) {
    var timeCol = it.start
      ? App.esc(it.start) + '<br><span style="opacity:.65">' + App.esc(it.end || '') + '</span>'
      : '<span style="opacity:.55">—</span>';

    var isBoost = it.src === 'boost' || it.src === 'boost_group';

    var sub = [];
    if (isBoost && (it.channelName || it.room)) sub.push(it.channelName || it.room);
    else if (it.room) sub.push(it.room);
    if (isBoost && it.total) sub.push(it.doneCount + '/' + it.total + ' vazifa');
    if (it.repeatNote) sub.push(it.repeatNote);
    if (st === 'live') sub.push('hozir');

    /* Bo'lim satrining o'ziga xos kaliti — bitta rejada bir nechta bo'lim
       bo'lishi mumkin, shuning uchun faqat planId yetmaydi. */
    var openKey = it.src === 'boost_group' ? (it.planId + '|' + it.groupName) : String(it.planId);

    var act, arg;
    if (isBoost) { act = 'kunOpenPlan'; arg = App.arg({ key: openKey }); }
    else if (it.src === 'event') { act = 'kunEditEvent'; arg = App.arg({ date: it.date, i: it.idx }); }
    else { act = 'kunEdit'; arg = App.arg({ d: it.day, i: it.idx }); }

    var tickBtn = '';
    if (it.src === 'event') {
      tickBtn = '<button class="kun-tick' + (it.done ? ' on' : '') + '" data-act="kunToggleEvent" data-arg=\'' +
        App.arg({ date: it.date, i: it.idx }) + '\' aria-label="Bajarildi">✓</button>';
    }

    var body =
      '<div class="les' + (st === 'live' ? ' now' : '') + (st === 'past' ? ' past' : '') +
      (it.done ? ' done' : '') + '" data-act="' + act + '" data-arg=\'' + arg + '\' role="button" tabindex="0">' +
      '<div class="les-t">' + timeCol + '</div>' +
      '<div class="les-bar" style="background:' + (it.color || 'var(--accent)') + '"></div>' +
      '<div class="les-m"><b>' + App.esc((it.emoji ? it.emoji + ' ' : '') + it.title) + '</b>' +
      '<span>' + App.esc(sub.join(' · ')) + '</span></div>' +
      tickBtn +
      '</div>';

    // Boostday bo'limi/rejasi ochilgan bo'lsa — vazifalari shu yerda belgilanadi
    if (isBoost && OPEN_PLAN === openKey && (it.tasks || []).length) {
      body += '<div class="kun-tasks">' + it.tasks.map(function (t) {
        return '<button class="kun-task' + (t.status === 1 ? ' on' : '') + '" data-act="kunToggleTask" data-arg=\'' +
          App.arg({ id: it.planId, index: t.index }) + '\'>' +
          '<i>' + (t.status === 1 ? '✓' : '') + '</i><span>' + App.esc(t.text) + '</span></button>';
      }).join('') +
      '<button class="lnk" style="margin:6px 0 2px" data-act="go" data-arg=\'' +
      App.arg({ v: 'boost_plan', p: { id: it.planId } }) + '\'>Rejani tahrirlash →</button></div>';
    }
    return body;
  }

  /* ---------- Vaqt chizig'idagi amallar ---------- */
  App.actions.kunOpenPlan = function (a) {
    var key = String(a.key);
    OPEN_PLAN = (OPEN_PLAN === key) ? null : key;
    renderDay();
  };
  App.actions.kunToggleTask = function (a) {
    if (!window.BoostDay) return;
    BoostDay.toggle(parseInt(a.id, 10), parseInt(a.index, 10))
      .then(function () { renderDay(); if (window.Activity) Activity.mark(); })
      .catch(function (e) { App.toast('⚠️ ' + e.message); });
  };
  App.actions.kunToggleEvent = function (a) {
    ensureLoaded();
    var list = EVENTS[a.date] || [], it = list[parseInt(a.i, 10)];
    if (!it) return;
    it.done = !it.done;
    saveEvents();
    renderDay();
    if (it.done && window.Activity) Activity.mark();
  };
  /* LMS bilan takrorlanadigan QO'LDA kiritilgan darslarni butunlay o'chiradi.
     Faqat "dars" turidagilar va faqat LMS'da mos vaqt topilganlari o'chadi —
     sport/ish/uyqu kabi yozuvlarga tegilmaydi. */
  App.actions.kunCleanDup = function () {
    refreshStores();
    markLmsDuplicates();
    var victims = [];
    Object.keys(SCHEDULE).forEach(function (dow) {
      (SCHEDULE[dow] || []).forEach(function (l) {
        if (l.lmsDup) victims.push({ dow: +dow, l: l });
      });
    });
    if (!victims.length) { App.toast('Takroriy dars topilmadi'); return; }

    App.confirm(victims.length + ' ta qo\'lda kiritilgan dars o\'chiriladi (LMS ularni o\'zi beradi). ' +
      'Sport, ish va boshqa yozuvlaringizga tegilmaydi.', function () {
      victims.forEach(function (v) {
        var arr = SCHEDULE[v.dow] || [];
        var i = arr.indexOf(v.l);
        if (i >= 0) arr.splice(i, 1);
      });
      saveSchedule();
      App.toast('✅ ' + victims.length + ' ta takroriy dars o\'chirildi');
      App.go('kun', { date: SEL_DATE });
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Mashg'ulot qo'shish / tahrirlash ----------
     Bitta oyna ikkala manbani boshqaradi:
       src='plan'  — haftalik takrorlanuvchi (SCHEDULE[hafta kuni])
       src='event' — aniq sanadagi bir martalik (EVENTS['YYYY-MM-DD'])
     "Takrorlanishi" tanlagichi orqali ular BIR-BIRIGA O'TKAZILADI — masalan
     har haftalik darsni "faqat shu kun"ga aylantirsa, yozuv jadvaldan
     chiqarilib o'sha sanaga ko'chiriladi. */
  function itemSheet(src, where, idx) {
    ensureLoaded();
    var isNew = idx === undefined || idx === null || idx < 0;
    var l;
    if (isNew) {
      l = { start: '08:30', end: '10:00', room: '', subject: '', color: '', kind: 'dars', weekType: '' };
    } else {
      l = (src === 'event' ? (EVENTS[where] || []) : (SCHEDULE[where] || []))[idx];
      if (!l) return;
    }
    // Takrorlanish qiymati: '' har hafta | left 1-hafta | right 2-hafta | once bir martalik
    var repeat = src === 'event' ? 'once' : (l.weekType || '');
    var baseDate = src === 'event' ? where : SEL_DATE;
    var baseDow = src === 'event' ? (parseKey(where) || new Date()).getDay() : where;

    var html =
      '<label class="field"><span>Nomi</span><input class="input" id="k-sub" placeholder="Masalan: Matematika, Zalga chiqish, Tushlik" value="' + App.esc(l.subject) + '"></label>' +
      '<label class="field"><span>Turi</span><select class="input" id="k-kind">' +
      KINDS.map(function (k) {
        return '<option value="' + k.k + '"' + ((l.kind || 'dars') === k.k ? ' selected' : '') + '>' + k.e + ' ' + k.n + '</option>';
      }).join('') + '</select></label>' +
      '<div class="flex" style="gap:8px">' +
      '<label class="field" style="flex:1"><span>Boshlanish</span><input class="input" type="time" id="k-start" value="' + l.start + '"></label>' +
      '<label class="field" style="flex:1"><span>Tugash</span><input class="input" type="time" id="k-end" value="' + l.end + '"></label>' +
      '</div>' +
      '<label class="field"><span>Joy (ixtiyoriy)</span><input class="input" id="k-room" placeholder="Xona, manzil yoki izoh" value="' + App.esc(l.room || '') + '"></label>' +
      '<label class="field"><span>Takrorlanishi</span><select class="input" id="k-rep">' +
      [['', 'Har hafta'], ['left', 'Faqat 1-hafta'], ['right', 'Faqat 2-hafta'], ['once', 'Faqat shu kun (bir martalik)']]
        .map(function (o) {
          return '<option value="' + o[0] + '"' + (repeat === o[0] ? ' selected' : '') + '>' + o[1] + '</option>';
        }).join('') + '</select></label>' +
      '<label class="field" id="k-dayw"><span>Hafta kuni</span><select class="input" id="k-day">' +
      [1, 2, 3, 4, 5, 6, 0].map(function (d) {
        return '<option value="' + d + '"' + (d === baseDow ? ' selected' : '') + '>' + DAY_FULL[d] + '</option>';
      }).join('') + '</select></label>' +
      '<label class="field" id="k-datew"><span>Sana</span><input class="input" type="date" id="k-date" value="' + App.esc(baseDate) + '"></label>' +
      /* Rang endi ERKIN tanlanmaydi — u TURKUMdan keladi, shunda bir
         toifadagi hamma ish jadvalda bir xil rangda ko'rinadi. */
      '<label class="field"><span>Turkum (rangni shu belgilaydi)</span><select class="input" id="k-cat">' +
      CATS.map(function (c) {
        return '<option value="' + c.id + '"' + (lessonCat(l) === c.id ? ' selected' : '') + '>' +
          c.e + ' ' + c.n + '</option>';
      }).join('') + '</select></label>' +
      '<div class="flex" id="k-catprev" style="gap:8px;align-items:center;margin:-6px 0 14px">' +
      '<span style="width:22px;height:12px;border-radius:4px;background:' + catColor(lessonCat(l)) + '"></span>' +
      '<span class="muted" style="font-size:12px">Shu turkumdagi hamma ish shu rangda</span></div>' +
      (isNew ? '<button class="btn" id="k-save">Qo\'shish</button>'
        : '<div class="btn-row"><button class="btn danger" id="k-del">O\'chirish</button><button class="btn" id="k-save">Saqlash</button></div>');

    var sh = App.sheet(html, { title: isNew ? 'Yangi mashg\'ulot' : 'Tahrirlash' });

    function syncRepeat() {
      var once = sh.querySelector('#k-rep').value === 'once';
      sh.querySelector('#k-dayw').style.display = once ? 'none' : '';
      sh.querySelector('#k-datew').style.display = once ? '' : 'none';
    }
    sh.querySelector('#k-rep').onchange = syncRepeat; syncRepeat();

    /* Rang namunasini jonli yangilab turamiz */
    function syncCatPreview() {
      var sw = sh.querySelector('#k-catprev span');
      if (sw) sw.style.background = catColor(sh.querySelector('#k-cat').value);
    }
    sh.querySelector('#k-cat').onchange = syncCatPreview;
    /* Tur o'zgarganda turkum ham o'sha turning turkumiga o'tadi
       (foydalanuvchi keyin xohlasa qo'lda boshqasini tanlaydi). */
    sh.querySelector('#k-kind').onchange = function () {
      sh.querySelector('#k-cat').value = kindInfo(this.value).cat;
      syncCatPreview();
    };

    function removeOld() {
      if (isNew) return;
      if (src === 'event') { (EVENTS[where] || []).splice(idx, 1); if (!EVENTS[where].length) delete EVENTS[where]; }
      else (SCHEDULE[where] || []).splice(idx, 1);
    }

    sh.querySelector('#k-save').onclick = function () {
      var subject = sh.querySelector('#k-sub').value.trim();
      if (!subject) return App.toast('Nomini kiriting');
      var kind = sh.querySelector('#k-kind').value;
      var rep = sh.querySelector('#k-rep').value;
      var item = {
        start: sh.querySelector('#k-start').value || '08:30',
        end: sh.querySelector('#k-end').value || '10:00',
        room: sh.querySelector('#k-room').value.trim(),
        subject: subject,
        kind: kind,
        cat: sh.querySelector('#k-cat').value
      };
      if (item.start > item.end) return App.toast('Tugash vaqti boshlanishdan keyin bo\'lsin');

      removeOld();
      var goDate;
      if (rep === 'once') {
        var dstr = sh.querySelector('#k-date').value || todayKey();
        if (!parseKey(dstr)) return App.toast('Sanani tanlang');
        if (!EVENTS[dstr]) EVENTS[dstr] = [];
        if (!isNew && src === 'event' && l.done) item.done = true;
        EVENTS[dstr].push(item);
        goDate = dstr;
      } else {
        var nd = parseInt(sh.querySelector('#k-day').value, 10);
        if (rep) item.weekType = rep;
        if (!SCHEDULE[nd]) SCHEDULE[nd] = [];
        SCHEDULE[nd].push(item);
        // Tanlangan haftadagi shu kunga o'tamiz (sanani yo'qotmasdan)
        var cur = parseKey(SEL_DATE) || new Date();
        goDate = dkey(addDays(cur, (nd - cur.getDay() + 7) % 7));
      }
      saveSchedule(); saveEvents();
      App.closeSheet();
      App.go('kun', { date: goDate });
    };

    if (!isNew) {
      sh.querySelector('#k-del').onclick = function () {
        App.confirm('"' + l.subject + '" o\'chirilsinmi?', function () {
          removeOld(); saveSchedule(); saveEvents();
          App.closeSheet(); App.go('kun', { date: SEL_DATE });
        }, { danger: true, yes: 'O\'chirish' });
      };
    }
  }

  App.actions.kunAdd = function () { itemSheet('plan', (parseKey(SEL_DATE) || new Date()).getDay(), -1); };
  App.actions.kunEdit = function (a) { itemSheet('plan', parseInt(a.d, 10), parseInt(a.i, 10)); };
  App.actions.kunEditEvent = function (a) { itemSheet('event', a.date, parseInt(a.i, 10)); };

  /* =========================================================
     .md (yoki .txt) fayldan jadvalni AVTOMATIK o'qish

     Faylda nechta kun bo'lsa — hammasi o'qiladi. Kun sarlavhasi
     quyidagi ko'rinishlarda bo'lishi mumkin:
        ## Dushanba        # Dush        **Seshanba**       Juma:
        ## Dushanba (1-hafta)            ## 2026-09-01      ## 01.09.2026
     Sana yozilsa — o'sha sananing hafta kuniga joylanadi.

     Dars qatori (oldida -, *, + yoki "1." bo'lishi mumkin):
        08:30-10:00 | A-408 | Fan nomi
        08:30-10:00 | Fan nomi
        08:30-10:00 Fan nomi (A-408)
        08:30 Fan nomi                  <- oxiri yozilmasa +90 daqiqa
     Markdown jadval qatorlari (| ... | ... |) ham qo'llab-quvvatlanadi.
     ========================================================= */

  var DAY_WORDS = {
    yakshanba: 0, yak: 0, voskresene: 0, sunday: 0, sun: 0,
    dushanba: 1, dush: 1, ponedelnik: 1, monday: 1, mon: 1,
    seshanba: 2, sesh: 2, vtornik: 2, tuesday: 2, tue: 2,
    chorshanba: 3, chor: 3, sreda: 3, wednesday: 3, wed: 3,
    payshanba: 4, pay: 4, chetverg: 4, thursday: 4, thu: 4,
    juma: 5, jum: 5, pyatnitsa: 5, friday: 5, fri: 5,
    shanba: 6, shan: 6, subbota: 6, saturday: 6, sat: 6
  };
  var MONTHS_UZ = ['yanvar', 'fevral', 'mart', 'aprel', 'may', 'iyun',
    'iyul', 'avgust', 'sentabr', 'oktabr', 'noyabr', 'dekabr'];

  function addMinutes(hhmm, mins) {
    var p = hhmm.split(':');
    var t = parseInt(p[0], 10) * 60 + parseInt(p[1], 10) + mins;
    t = ((t % 1440) + 1440) % 1440;
    return ('0' + Math.floor(t / 60)).slice(-2) + ':' + ('0' + (t % 60)).slice(-2);
  }
  function normTime(s) {
    var m = String(s).match(/^(\d{1,2})[:.](\d{2})$/);
    if (!m) return null;
    var h = parseInt(m[1], 10), mi = parseInt(m[2], 10);
    if (h > 23 || mi > 59) return null;
    return ('0' + h).slice(-2) + ':' + ('0' + mi).slice(-2);
  }

  /* Sarlavhadan hafta kunini aniqlash. Topilmasa null. */
  function parseDayHeader(line) {
    var s = String(line).trim()
      .replace(/^#{1,6}\s*/, '')          // ## sarlavha
      .replace(/^\*\*(.*)\*\*$/, '$1')    // **qalin**
      .replace(/^[-*+]\s*/, '')
      .replace(/:\s*$/, '')
      .trim();
    if (!s) return null;

    var weekType = '';
    var wt = s.match(/\(?\s*([12])\s*[- ]?\s*hafta\s*\)?/i);
    if (wt) { weekType = wt[1] === '1' ? 'left' : 'right'; s = s.replace(wt[0], '').trim(); }
    else if (/toq\s*hafta/i.test(s)) { weekType = 'left'; s = s.replace(/toq\s*hafta/i, '').trim(); }
    else if (/juft\s*hafta/i.test(s)) { weekType = 'right'; s = s.replace(/juft\s*hafta/i, '').trim(); }

    s = s.replace(/[()\[\]]/g, ' ').replace(/\s+/g, ' ').trim();

    // 2026-09-01  yoki  01.09.2026 / 01/09/2026
    var d = null;
    var iso = s.match(/(\d{4})[-.\/](\d{1,2})[-.\/](\d{1,2})/);
    var dmy = s.match(/(\d{1,2})[-.\/](\d{1,2})[-.\/](\d{4})/);
    if (iso) d = new Date(+iso[1], +iso[2] - 1, +iso[3]);
    else if (dmy) d = new Date(+dmy[3], +dmy[2] - 1, +dmy[1]);
    else {
      // "1-sentabr" / "1 sentabr"
      var uz = s.match(/(\d{1,2})\s*[-\s]\s*([a-z']+)/i);
      if (uz) {
        var mi = MONTHS_UZ.indexOf(uz[2].toLowerCase());
        if (mi >= 0) { var y = new Date().getFullYear(); d = new Date(y, mi, +uz[1]); }
      }
    }
    // Sana faqat SOF sarlavha qatorida qabul qilinadi: dars qatorida ham
    // sanaga o'xshash bo'lak uchrashi mumkin, shuning uchun "|" bo'lsa yoki
    // qator uzun bo'lsa — bu sarlavha emas.
    if (d && !isNaN(d.getTime()) && String(line).indexOf('|') < 0 && s.length <= 40) {
      /* `date` — haftalik jadval uchun kerak emas (u faqat `day` ni oladi),
         lekin haftalik REJA importi aynan sanaga yozadi. */
      return { day: d.getDay(), weekType: weekType, dated: true, date: d };
    }

    // Kun nomi (birinchi so'z yetarli)
    var words = s.toLowerCase().replace(/[^a-zа-яё'\s]/gi, ' ').split(/\s+/);
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if (w && DAY_WORDS[w] !== undefined) return { day: DAY_WORDS[w], weekType: weekType, dated: false };
    }
    return null;
  }

  /* Bitta dars qatorini o'qish. Vaqt topilmasa null. */
  function parseLessonLine(line, defWeekType) {
    var s = String(line).trim();
    if (!s) return null;
    if (/^\|?\s*:?-{3,}/.test(s)) return null;               // jadval ajratgichi
    s = s.replace(/^[-*+]\s+/, '').replace(/^\d+[.)]\s+/, '').trim();

    var weekType = defWeekType || '';
    var wt = s.match(/\(?\s*([12])\s*[- ]?\s*hafta\s*\)?/i);
    if (wt) { weekType = wt[1] === '1' ? 'left' : 'right'; s = s.replace(wt[0], '').trim(); }

    var parts;
    if (s.indexOf('|') >= 0) {
      parts = s.split('|').map(function (x) { return x.trim(); }).filter(function (x) { return x !== ''; });
    } else {
      parts = [s];
    }
    if (!parts.length) return null;

    // Vaqt qaysi bo'lakda?
    var timeIdx = -1, start = null, end = null;
    for (var i = 0; i < parts.length; i++) {
      var r = parts[i].match(/(\d{1,2}[:.]\d{2})\s*(?:[-–—]|gacha|dan)\s*(\d{1,2}[:.]\d{2})/);
      if (r) { start = normTime(r[1]); end = normTime(r[2]); timeIdx = i; break; }
    }
    if (timeIdx < 0) {
      for (var j = 0; j < parts.length; j++) {
        var r2 = parts[j].match(/(\d{1,2}[:.]\d{2})/);
        if (r2) { start = normTime(r2[1]); timeIdx = j; break; }
      }
    }
    if (!start) return null;
    if (!end) end = addMinutes(start, 90);

    var rest = [];
    for (var k = 0; k < parts.length; k++) {
      if (k === timeIdx) {
        // vaqt bo'lagida matn ham bo'lishi mumkin: "08:30-10:00 Fan nomi"
        var leftover = parts[k].replace(/\d{1,2}[:.]\d{2}\s*(?:[-–—]|gacha|dan)?\s*(\d{1,2}[:.]\d{2})?/g, ' ').trim();
        if (leftover) rest.push(leftover);
      } else if (parts[k]) rest.push(parts[k]);
    }
    if (!rest.length) return null;

    var room = '', subject = '';
    if (rest.length >= 2) { room = rest[0]; subject = rest.slice(1).join(' — '); }
    else {
      subject = rest[0];
      var pr = subject.match(/\(([^()]{1,16})\)\s*$/);   // "Fan nomi (A-408)"
      if (pr) { room = pr[1].trim(); subject = subject.replace(pr[0], '').trim(); }
    }
    subject = subject.replace(/^[-–—:\s]+|[-–—:\s]+$/g, '').trim();
    if (!subject) return null;

    return { start: start, end: end, room: room, subject: subject, weekType: weekType };
  }

  /* Butun faylni o'qish -> { 0..6: [dars,...] } + statistika */
  function parseScheduleMd(text) {
    var lines = String(text || '').replace(/\r/g, '').split('\n');
    var out = {}, cur = null, curWT = '', stats = { days: {}, total: 0, dated: 0, skipped: 0 };

    /* `###` dan boshlanadigan bo'lak — REJA bo'limi (parsePlanMd o'qiydi),
       dars emas. Uni o'tkazib yubormasak, "### 07:00 - 07:40 | Ertalabki
       rejim" xonasi "###" bo'lgan dars bo'lib jadvalga tushib qolardi. */
    var inPlanGroup = false;

    lines.forEach(function (raw) {
      var line = raw.trim();
      if (!line) return;
      if (/^```/.test(line)) return;

      var lvl = (line.match(/^(#{1,6})\s/) || [, ''])[1].length;
      if (lvl >= 3) { inPlanGroup = true; return; }
      if (lvl && lvl <= 2) inPlanGroup = false;
      if (inPlanGroup) return;

      var hdr = parseDayHeader(line);
      // Sarlavha faqat vaqt YO'Q qatorlarda (aks holda dars qatorini yeb qo'yadi).
      // Sanali sarlavha bundan mustasno: "01.09.2026" vaqt naqshiga o'xshaydi,
      // lekin parseDayHeader uni allaqachon qat'iy tekshirgan.
      if (hdr && (hdr.dated || !/\d{1,2}[:.]\d{2}/.test(line))) {
        cur = hdr.day; curWT = hdr.weekType;
        if (hdr.dated) stats.dated++;
        if (!out[cur]) out[cur] = [];
        return;
      }
      if (cur === null) return;                 // kun sarlavhasidan oldingi matn

      var les = parseLessonLine(line, curWT);
      if (!les) { if (/\d{1,2}[:.]\d{2}/.test(line)) stats.skipped++; return; }

      // Jadval sarlavhasini ("Vaqt | Xona | Fan") o'tkazib yuboramiz
      if (/^(vaqt|time|soat)$/i.test(les.room) || /^(fan|dars|subject|mavzu)$/i.test(les.subject)) return;

      /* Ilgari har fanga navbatdagi rang berilardi (COLORS aylanasi) —
         natijada bir xil toifadagi ishlar turli rangda chiqardi. Endi
         rang TURKUMdan keladi, jadvalga esa turkum yoziladi. */
      les.cat = guessCat(les.subject + ' ' + (les.room || ''));
      if (!les.weekType) delete les.weekType;

      out[cur].push(les);
      stats.total++;
      stats.days[cur] = (stats.days[cur] || 0) + 1;
    });

    return { schedule: out, stats: stats };
  }
  App.parseScheduleMd = parseScheduleMd;   // sinov/boshqa modullar uchun

  /* =========================================================
     HAFTALIK REJA (.md) — BO'LIMLI format

     Boostday'da vaqt endi BO'LIMGA qo'yiladi (vazifaga emas), shuning uchun
     .md ham shu tuzilishda:

       ## Dushanba                 <- kun (hafta kuni yoki 12.08.2026)
       ### 08:00-09:00 | Ertalab   <- bo'lim: vaqt | nom  (tartibi ixtiyoriy)
       - Yuzni yuvish              <- vazifa
       - Nonushta

     Bitta faylda butun hafta bo'lishi mumkin. Hafta kuni bilan yozilgan
     sarlavha JORIY hafta (dushanbadan boshlanadigan) sanasiga bog'lanadi.
     ========================================================= */

  /* "08:00-09:00 | Nom" | "Nom | 08:00-09:00" | "08:00 Nom" -> {time, name} */
  /* Turkum nomining turli yozilishlari -> ichki id. AI yoki foydalanuvchi
     qaysi shaklda yozsa ham tushunilsin. */
  var CAT_ALIAS = {
    kurs: 'kurs', dars: 'kurs', lesson: 'kurs', universitet: 'kurs', majburiy: 'kurs',
    rus: 'rus', 'rus tili': 'rus', russian: 'rus',
    dasturlash: 'dasturlash', coding: 'dasturlash', code: 'dasturlash', programming: 'dasturlash', it: 'dasturlash',
    sport: 'sport', fitness: 'sport', jismoniy: 'sport',
    hayot: 'hayot', kundalik: 'hayot', shaxsiy: 'hayot', life: 'hayot', ovqat: 'hayot', uyqu: 'hayot',
    boshqa: 'boshqa', other: 'boshqa'
  };
  function normCat(raw) {
    var k = String(raw || '').trim().toLowerCase();
    return CAT_ALIAS[k] || '';
  }

  function parseGroupHeader(line) {
    var s = String(line).replace(/^#{1,6}\s*/, '').replace(/^\*\*(.*)\*\*$/, '$1').trim();
    if (!s) return null;
    var time = '', name = s, cat = '';

    /* Turkum belgisi: "### 18:00 - 19:30 | Sport [sport]".
       Qavs ichidagi so'z nomdan olib tashlanadi — sarlavhada ko'rinmaydi. */
    var tag = s.match(/\[([^\]]+)\]/);
    if (tag) {
      var c = normCat(tag[1]);
      if (c) { cat = c; s = s.replace(tag[0], ' '); name = s; }
    }

    var rng = s.match(/(\d{1,2}[:.]\d{2})\s*[-–—]\s*(\d{1,2}[:.]\d{2})/);
    if (rng) {
      time = normTime(rng[1]) + ' - ' + normTime(rng[2]);
      name = s.replace(rng[0], '');
    } else {
      var one = s.match(/(\d{1,2}[:.]\d{2})/);
      if (one) { time = normTime(one[1]); name = s.replace(one[0], ''); }
    }
    name = name.replace(/\|/g, ' ').replace(/\s+/g, ' ').replace(/^[-–—·:]+|[-–—·:]+$/g, '').trim();
    if (!time && !name) return null;
    return { time: time, name: name, cat: cat };
  }

  function parsePlanMd(text) {
    var lines = String(text || '').replace(/\r/g, '').split('\n');
    var days = [], cur = null, curGroup = null;
    var stats = { days: 0, groups: 0, tasks: 0 };

    /* Joriy haftaning dushanbasi — hafta kuni nomi shu haftaga bog'lanadi */
    var t = new Date(); t.setHours(0, 0, 0, 0);
    var monday = addDays(t, -(((t.getDay() + 6) % 7)));

    /* Bitta sana faylda IKKI xil sarlavha bilan uchrashi mumkin
       ("## Chorshanba" va "## 12.08.2026" — bir kun). Bunda yangi kun
       ochmasdan mavjudiga davom etamiz, aks holda o'sha sanaga ikki marta
       yozilib, "almashtirish" rejimida birinchisi yo'qolib ketardi. */
    function pushDay(dow, dateObj, label) {
      var d = dateObj || addDays(monday, (dow + 6) % 7);
      var key = dkey(d);
      var same = days.filter(function (x) { return x.date === key; })[0];
      if (same) { cur = same; curGroup = null; return; }
      cur = { dow: dow, date: key, label: label, groups: [] };
      days.push(cur);
      curGroup = null;
    }

    lines.forEach(function (raw) {
      var line = raw.trim();
      if (!line || /^```/.test(line)) return;

      var hLevel = (line.match(/^(#{1,6})\s/) || [, ''])[1].length;

      /* ### (yoki undan chuqurroq) — BO'LIM sarlavhasi */
      if (hLevel >= 3 && cur) {
        var g = parseGroupHeader(line);
        if (g) {
          /* Turkum yozilmagan bo'lsa nomidan taxmin qilamiz — eski
             fayllar ham rangli chiqsin. */
          curGroup = { name: g.name, time: g.time, cat: g.cat || guessCat(g.name), tasks: [] };
          cur.groups.push(curGroup); stats.groups++;
        }
        return;
      }

      /* ## yoki # — KUN sarlavhasi */
      if (hLevel && hLevel <= 2) {
        var hdr = parseDayHeader(line);
        if (hdr) { pushDay(hdr.day, hdr.date || null, line.replace(/^#{1,6}\s*/, '').trim()); return; }
        return;
      }

      /* Sarlavhasiz kun nomi ham qabul qilinadi ("Dushanba:") */
      if (!/^[-*+]\s/.test(line) && !cur) {
        var h2 = parseDayHeader(line);
        if (h2) { pushDay(h2.day, h2.date || null, line.trim()); return; }
      }

      if (!cur) return;

      /* DARS qatori bo'lsa — bu reja emas, jadval (parseScheduleMd o'qiydi).
         Belgisi: bo'lim ochilmagan va qatorda vaqt oralig'i + "|" bor
         (`- 08:30-10:00 | A-408 | Matematika`). Aks holda reja vazifasi
         dars bo'lib, dars esa vazifa bo'lib ikki joyga tushib ketardi. */
      if (!curGroup && /\d{1,2}[:.]\d{2}/.test(line) && line.indexOf('|') >= 0) return;

      /* Vazifa qatori */
      var task = line.replace(/^[-*+]\s+/, '').replace(/^\d+[.)]\s+/, '').trim();
      task = task.replace(/^\[[ xX]\]\s*/, '');           // - [ ] belgisi
      if (!task) return;
      if (!curGroup) {
        /* Bo'limsiz vazifa — nomsiz, vaqtsiz bo'limga tushadi */
        curGroup = { name: '', time: '', cat: '', tasks: [] };
        cur.groups.push(curGroup); stats.groups++;
      }
      curGroup.tasks.push({ text: task });
      stats.tasks++;
    });

    /* Bo'sh bo'limlarni tashlaymiz (sarlavha yozilib, vazifa yozilmagan) */
    days.forEach(function (d) {
      d.groups = d.groups.filter(function (g) { return g.tasks.length; });
    });
    days = days.filter(function (d) { return d.groups.length; });
    stats.days = days.length;
    stats.groups = days.reduce(function (n, d) { return n + d.groups.length; }, 0);

    return { days: days, stats: stats };
  }
  App.parsePlanMd = parsePlanMd;   // sinov uchun

  /* ---------- Import oynasi ----------
     Ikki xil .md qabul qilinadi va TUR AVTOMATIK aniqlanadi:
       · REJA   — `### 08:00-09:00 | Bo'lim` + vazifalar (Boostdayga yoziladi)
       · JADVAL — `- 08:30-10:00 | Xona | Fan` (haftalik takrorlanuvchi dars)
     Ikkalasi bitta faylda aralash bo'lsa, ikkalasi ham qo'llanadi. */
  App.actions.kunImport = function () {
    var html =
      '<input type="file" id="k-file" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">' +
      '<button class="btn sec" id="k-pick" style="margin-bottom:4px">' +
      '<span data-icon="upload" data-icon-size="16"></span>.md fayl tanlash</button>' +
      '<p id="k-finfo" style="font-size:12.5px;color:var(--hint);margin:0 0 10px">Yoki matnni pastga qo\'ying</p>' +
      '<label class="field" style="margin-bottom:12px"><span>Reja / jadval matni (Markdown)</span>' +
      '<textarea class="textarea" id="k-text" rows="14" style="font-family:monospace;font-size:13px;line-height:1.5"' +
      ' placeholder="## Dushanba&#10;### 07:00 - 07:30 | Ertalabki rejim&#10;- Yuzni yuvish&#10;- Nonushta&#10;&#10;### 18:00 - 19:30 | Sport&#10;- Tortilish&#10;- Press"></textarea></label>' +

      '<p style="font-size:12.5px;color:var(--hint);line-height:1.55;margin:0 0 16px">' +
      '<b>Kun rejasi:</b> <code>## Dushanba</code> yoki <code>## 12.08.2026</code>, ' +
      'bo\'lim <code>### 08:00 - 09:00 | Nom</code>, ostida <code>- vazifa</code>. ' +
      'Vaqt BO\'LIMGA qo\'yiladi.<br>' +
      '<b>Dars jadvali:</b> <code>- 08:30-10:00 | Xona | Fan</code>.<br>' +
      '<i style="display:inline-block;margin-top:6px;color:var(--accent)">Rejani AI ga yozdirib olsangiz ham bo\'ladi — ' +
      '<a href="Jadval_AI_Qollanma.md" download style="color:var(--accent);text-decoration:underline;font-weight:600">qo\'llanmani yuklab oling</a></i>' +
      '</p>' +

      '<label class="field"><span>Reja qanday yozilsin?</span>' +
      '<select class="select" id="k-pmode">' +
      '<option value="replace">O\'sha kunlardagi rejani almashtirish</option>' +
      '<option value="merge">Mavjud rejaga qo\'shish</option>' +
      '</select></label>' +
      '<label class="field" style="display:flex;align-items:center;gap:8px;flex-direction:row;margin-bottom:6px">' +
      '<input type="checkbox" id="k-sport" checked style="width:auto">' +
      '<span style="margin:0">Sport mashqlarini "Mening mashqlarim"ga ulash</span></label>' +
      '<label class="field"><span>Dars jadvali qanday qo\'shilsin?</span>' +
      '<select class="select" id="k-mode">' +
      '<option value="merge">Mavjud jadvalga qo\'shish</option>' +
      '<option value="replace">Faylda bor kunlarni almashtirish</option>' +
      '<option value="wipe">Butun jadvalni almashtirish</option>' +
      '</select></label>' +
      '<button class="btn" id="k-import">Tekshirish va qo\'shish</button>';

    var sh = App.sheet(html, { title: 'Fayldan yuklash', cls: 'wide-sheet' });
    App.icons(sh);

    var fileEl = sh.querySelector('#k-file');
    var info = sh.querySelector('#k-finfo');
    sh.querySelector('#k-pick').onclick = function () { fileEl.click(); };

    function describe(text, prefix) {
      var p = parsePlanMd(text), s = parseScheduleMd(text);
      var bits = [];
      if (p.stats.tasks) bits.push('<b>' + p.stats.tasks + '</b> ta vazifa (' + p.stats.groups + ' bo\'lim, ' + p.stats.days + ' kun)');
      if (s.stats.total) bits.push('<b>' + s.stats.total + '</b> ta dars');
      info.innerHTML = bits.length ? '✅ ' + prefix + bits.join(' · ') : '⚠️ ' + prefix + 'hech narsa topilmadi — formatni tekshiring';
      info.style.color = bits.length ? 'var(--success)' : 'var(--danger)';
      return { plan: p, sched: s };
    }

    fileEl.onchange = function () {
      var f = fileEl.files && fileEl.files[0];
      if (!f) return;
      info.textContent = 'O\'qilmoqda...';
      var fr = new FileReader();
      fr.onload = function () {
        sh.querySelector('#k-text').value = String(fr.result || '');
        describe(fr.result, App.esc(f.name) + ' — ');
      };
      fr.onerror = function () { info.textContent = 'Faylni o\'qib bo\'lmadi'; };
      fr.readAsText(f);
    };
    sh.querySelector('#k-text').oninput = function () { describe(this.value, ''); };

    sh.querySelector('#k-import').onclick = function () {
      var text = sh.querySelector('#k-text').value;
      var plan = parsePlanMd(text), sched = parseScheduleMd(text);
      if (!plan.stats.tasks && !sched.stats.total) {
        return App.toast('Hech narsa topilmadi — formatni tekshiring');
      }
      var planMode = sh.querySelector('#k-pmode').value;
      var schedMode = sh.querySelector('#k-mode').value;
      var linkSport = sh.querySelector('#k-sport').checked;

      var msg = [];
      if (plan.stats.tasks) {
        msg.push(plan.stats.tasks + ' ta vazifa Boostdayga yoziladi:');
        plan.days.forEach(function (d) {
          var n = d.groups.reduce(function (a, g) { return a + g.tasks.length; }, 0);
          msg.push('  ' + DAY_FULL[d.dow] + ' (' + d.date + '): ' + n + ' ta');
        });
      }
      if (sched.stats.total) {
        if (msg.length) msg.push('');
        msg.push(sched.stats.total + ' ta dars haftalik jadvalga qo\'shiladi');
      }

      App.confirm(msg.join('\n'), function () {
        App.closeSheet();
        runImport(plan, sched, planMode, schedMode, linkSport);
      }, { yes: 'Qo\'shish', title: 'Tasdiqlang' });
    };
  };

  /* Importni bajaradi: jadval (mahalliy) + reja (Boostday) + sport ulash */
  function runImport(plan, sched, planMode, schedMode, linkSport) {
    /* 1) Dars jadvali — mahalliy, darhol */
    if (sched.stats.total) {
      ensureLoaded();
      if (schedMode === 'wipe') SCHEDULE = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [] };
      Object.keys(sched.schedule).forEach(function (d) {
        if (!SCHEDULE[d] || schedMode === 'replace' || schedMode === 'wipe') SCHEDULE[d] = [];
        SCHEDULE[d] = SCHEDULE[d].concat(sched.schedule[d]);
      });
      saveSchedule();
    }

    if (!plan.stats.tasks) {
      App.toast('✅ ' + sched.stats.total + ' ta dars qo\'shildi');
      App.reload();
      return;
    }
    if (!window.BoostPush || !BoostPush.pushDayPlan) {
      App.toast('⚠️ Boostday moduli yuklanmagan');
      return;
    }

    /* 2) Sport mashqlarini "Mening mashqlarim"ga ulash (nom bo'yicha) */
    var linked = 0;
    if (linkSport && window.SportBridge && SportBridge.addToMineByName) {
      var names = [];
      plan.days.forEach(function (d) {
        d.groups.forEach(function (g) { g.tasks.forEach(function (t) { names.push(t.text); }); });
      });
      linked = SportBridge.addToMineByName(names);
    }

    /* 3) Har kun uchun Boostdayga yozamiz — KETMA-KET (parallel emas):
       hammasi bitta `todo` bazasiga yozadi, bir vaqtda yuborilsa oxirgisi
       oldingilarini bosib ketishi mumkin. */
    App.toast('Boostdayga yozilmoqda...');
    var okDays = 0, failed = null;
    var chain = Promise.resolve();
    plan.days.forEach(function (d) {
      chain = chain.then(function () {
        if (failed) return;
        return BoostPush.pushDayPlan('kun', d.date, DAY_FULL[d.dow] + ' — kun rejasi', d.groups, { mode: planMode })
          .then(function () { okDays++; })
          .catch(function (e) { failed = e; });
      });
    });

    chain.then(function () {
      if (failed) { App.toast('⚠️ ' + failed.message); return; }
      var parts = [okDays + ' kunlik reja Boostdayga yozildi'];
      if (sched.stats.total) parts.push(sched.stats.total + ' ta dars jadvalga');
      if (linked) parts.push(linked + ' ta sport mashqi ulandi');
      App.toast('✅ ' + parts.join(' · '));
      var boot = window.BoostDay ? BoostDay.ensureLoaded(true) : Promise.resolve();
      boot.then(function () { App.go('kun', { date: plan.days[0].date }); });
    });
  }

  /* Tashqi modullar uchun (bosh sahifa "Bugungi reja" bloki).
     Jadval kun.js ichida yopiq bo'lgani uchun kichik API ochamiz — home.js
     localStorage'ni o'zi o'qib, standart jadvalni bilmay qolmasin.
     `dayLessons` endi haftalik jadval + o'sha sanadagi bir martalik
     voqealarni birga qaytaradi (bosh sahifada ham butun kun ko'rinsin). */
  /* ---------- Qo'lda kiritish (Kun hisobi UI) ---------- */
  App.actions.kunAdd = function () {
    var d = parseKey(SEL_DATE) || new Date();
    
    var html =
      '<label class="field"><span>Sarlavha (Nomi)</span><input type="text" id="k-add-title" class="input" placeholder="Masalan: Ingliz tili kursi yoki Ish"></label>' +
      '<div style="display:flex;gap:10px">' +
        '<label class="field" style="flex:1"><span>Boshlanish</span><input type="time" id="k-add-start" class="input"></label>' +
        '<label class="field" style="flex:1"><span>Tugash</span><input type="time" id="k-add-end" class="input"></label>' +
      '</div>' +
      '<label class="field"><span>Turi</span><select id="k-add-kind" class="input">' +
        KINDS.map(function(k) { return '<option value="' + k.k + '">' + k.e + ' ' + k.n + '</option>'; }).join('') +
      '</select></label>' +
      '<label class="field"><span>Turkum (rangni shu belgilaydi)</span><select id="k-add-cat" class="input">' +
        CATS.map(function(c) { return '<option value="' + c.id + '">' + c.e + ' ' + c.n + '</option>'; }).join('') +
      '</select></label>' +
      '<label class="field"><span>Xona yoki Manzil (ixtiyoriy)</span><input type="text" id="k-add-room" class="input"></label>' +
      '<label class="field"><span>Takrorlanish</span><select id="k-add-rep" class="input">' +
        '<option value="plan">Haftalik (' + DAY_FULL[d.getDay()] + ' kunlari takrorlanadi)</option>' +
        '<option value="event">Bir martalik (faqat shu sana uchun)</option>' +
      '</select></label>' +
      '<button class="btn" id="k-add-save" style="margin-top:10px">Saqlash</button>';
      
    var sh = App.sheet(html, { title: 'Mashg\'ulot qo\'shish' });

    // Tur tanlanganda turkum ham o'sha turnikiga o'tadi
    sh.querySelector('#k-add-kind').onchange = function () {
      sh.querySelector('#k-add-cat').value = kindInfo(this.value).cat;
    };

    sh.querySelector('#k-add-save').onclick = function () {
      var t = sh.querySelector('#k-add-title').value.trim();
      var st = sh.querySelector('#k-add-start').value;
      var en = sh.querySelector('#k-add-end').value;
      var ki = sh.querySelector('#k-add-kind').value;
      var rm = sh.querySelector('#k-add-room').value.trim();
      var rep = sh.querySelector('#k-add-rep').value;

      if (!t) return App.toast('Sarlavha yozish majburiy');
      if (!st) return App.toast('Boshlanish vaqtini kiriting');

      var obj = { subject: t, kind: ki, cat: sh.querySelector('#k-add-cat').value, room: rm };
      if (st) obj.start = st;
      if (en) obj.end = en;
      
      if (rep === 'plan') {
        var dow = d.getDay();
        if (!SCHEDULE[dow]) SCHEDULE[dow] = [];
        SCHEDULE[dow].push(obj);
        saveSchedule();
      } else {
        var k = dkey(d);
        if (!EVENTS[k]) EVENTS[k] = [];
        EVENTS[k].push(obj);
        saveEvents();
      }
      
      App.closeSheet();
      App.toast('✅ Muvaffaqiyatli qo\'shildi');
      App.reload();
    };
  };

  window.Kun = {
    dayLessons: function (dayIdx) {
      refreshStores();
      var d = new Date();
      if (dayIdx !== undefined) d = addDays(d, (dayIdx - d.getDay() + 7) % 7);
      return sortItems(localItems(dkey(d)).concat(lmsItems(dkey(d)))).map(function (x) {
        return { start: x.start, end: x.end, subject: (x.emoji ? x.emoji + ' ' : '') + x.title, room: x.room, color: x.color, done: !!x.done };
      });
    },
    /* Bugungi to'liq reja (Boostday rejalari bilan) — chaqiruvchi kutib oladi. */
    dayFull: function (dateStr) {
      refreshStores();
      var k = dateStr || todayKey();
      var boot = window.BoostDay ? BoostDay.ensureLoaded() : Promise.resolve();
      return boot.then(function () { return sortItems(localItems(k).concat(lmsItems(k), boostItems(k))); });
    },
    dayLabel: function (dayIdx) {
      return DAY_FULL[dayIdx === undefined ? new Date().getDay() : dayIdx];
    },
    dateKey: dkey
  };
})();
