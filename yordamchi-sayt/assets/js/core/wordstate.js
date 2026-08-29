/* ---------- So'z holati: o'rgandim / saqlangan / rang guruhi ----------
 *
 * Bitta manba (`window.WordState`). Ilgari bu holat home.js ichida
 * yashiringan edi va FAQAT filtr sifatida ishlatilardi — ya'ni "o'rgandim"
 * deb belgilangan so'z baribir flashcard, reels va svayp mashqlarida
 * chiqaverardi. Endi u chinakam holat: mashqlar shu modul orqali so'z
 * so'raydi va o'rganilganlar butunlay chiqib ketadi.
 *
 * SAQLASH KALITLARI ATAYLAB ESKISICHA QOLDIRILDI
 * ----------------------------------------------
 * `vocab_mastered_v1` / `vocab_bookmarks_v1` — home.js allaqachon shu
 * kalitlarni o'qiydi va foydalanuvchida bu ma'lumot bor. Kalit formatini
 * o'zgartirish mavjud belgilarni yo'qotardi, shuning uchun format bir xil:
 * oddiy `w.ru` satrlari massivi.
 *
 * `localStorage` remote-storage.js tomonidan yamalgan, ya'ni har yozuv
 * serverga sinxronlanadi va boshqa qurilmada ham ko'rinadi.
 */
(function (root) {
  'use strict';

  var K_MASTERED = 'vocab_mastered_v1';   // butunlay o'rganilgan — hech qayerda chiqmaydi
  var K_SAVED    = 'vocab_bookmarks_v1';  // hozir o'rganilayotgan
  var K_GROUPS   = 'vocab_groups_v1';     // { "слово": "#ef4444" }

  /* Bir-biridan OSON farqlanadigan ranglar. Ko'p rang emas: 8 tadan ortiq
     bo'lsa ular o'zaro chalkashib ketadi va guruhlash ma'nosini yo'qotadi. */
  var COLORS = [
    { id: 'qizil',   hex: '#ef4444', name: 'Qizil' },
    { id: 'zangori', hex: '#3b82f6', name: 'Zangori' },
    { id: 'yashil',  hex: '#22c55e', name: 'Yashil' },
    { id: 'sariq',   hex: '#eab308', name: 'Sariq' },
    { id: 'binafsha',hex: '#a855f7', name: 'Binafsha' },
    { id: 'pushti',  hex: '#ec4899', name: 'Pushti' },
    { id: 'moviy',   hex: '#06b6d4', name: 'Moviy' },
    { id: 'sabzi',   hex: '#f97316', name: 'Sabzi' }
  ];

  function readList(key) {
    try {
      var v = JSON.parse(localStorage.getItem(key) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function writeList(key, list) {
    try { localStorage.setItem(key, JSON.stringify(list)); } catch (e) {}
  }
  function readMap(key) {
    try {
      var v = JSON.parse(localStorage.getItem(key) || '{}');
      return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
    } catch (e) { return {}; }
  }
  function writeMap(key, obj) {
    try { localStorage.setItem(key, JSON.stringify(obj)); } catch (e) {}
  }

  /* Ro'yxatlar tez tekshiriladigan bo'lishi kerak: mashq har so'z uchun
     chaqiradi, 8000 so'zli lug'atda `indexOf` sekinlik qilardi. */
  var cache = { mastered: null, saved: null, groups: null };
  function masteredSet() {
    if (!cache.mastered) {
      cache.mastered = {};
      readList(K_MASTERED).forEach(function (w) { cache.mastered[w] = 1; });
    }
    return cache.mastered;
  }
  function savedSet() {
    if (!cache.saved) {
      cache.saved = {};
      readList(K_SAVED).forEach(function (w) { cache.saved[w] = 1; });
    }
    return cache.saved;
  }
  function groupsMap() {
    if (!cache.groups) cache.groups = readMap(K_GROUPS);
    return cache.groups;
  }
  function invalidate() { cache.mastered = cache.saved = cache.groups = null; }

  function toggleInList(key, cacheName, word) {
    var list = readList(key);
    var i = list.indexOf(word);
    if (i >= 0) list.splice(i, 1); else list.push(word);
    writeList(key, list);
    cache[cacheName] = null;
    return i < 0;   // true = qo'shildi
  }

  root.WordState = {
    COLORS: COLORS,

    /* --- O'rgandim (butunlay) --- */
    isMastered: function (ru) { return !!masteredSet()[ru]; },
    toggleMastered: function (ru) {
      var on = toggleInList(K_MASTERED, 'mastered', ru);
      /* O'rganib bo'lingan so'z "hozir o'rganyapman" ro'yxatida turishi
         mantiqsiz — ikkisi bir vaqtda yoqilmaydi. */
      if (on && this.isSaved(ru)) toggleInList(K_SAVED, 'saved', ru);
      return on;
    },
    masteredList: function () { return readList(K_MASTERED); },

    /* --- Saqlangan (hozir o'rganilayotgan) --- */
    isSaved: function (ru) { return !!savedSet()[ru]; },
    toggleSaved: function (ru) {
      var on = toggleInList(K_SAVED, 'saved', ru);
      if (on && this.isMastered(ru)) toggleInList(K_MASTERED, 'mastered', ru);
      return on;
    },
    savedList: function () { return readList(K_SAVED); },

    /* --- Rang guruhlari --- */
    colorOf: function (ru) { return groupsMap()[ru] || ''; },
    setColor: function (ru, hex) {
      var m = groupsMap();
      if (!hex) delete m[ru]; else m[ru] = hex;
      writeMap(K_GROUPS, m);
      cache.groups = null;
    },
    /* { hex: [ru, ru, ...] } — "Guruhlar" bo'limi shundan chiziladi */
    byColor: function () {
      var m = groupsMap(), out = {};
      Object.keys(m).forEach(function (ru) {
        (out[m[ru]] = out[m[ru]] || []).push(ru);
      });
      return out;
    },

    /* --- Mashqlar uchun asosiy filtr ---
       O'rganib bo'lingan so'zlar mashqqa TUSHMAYDI. Aynan shu narsa
       "galichka" ning ma'nosi: bu so'zni har qanday holatda bilaman. */
    forPractice: function (words) {
      var m = masteredSet();
      return (words || []).filter(function (w) { return !m[w && w.ru]; });
    },

    /* Boshqa qurilmadan sinxron kelganda keshni yangilash uchun */
    refresh: invalidate
  };
})(window);
