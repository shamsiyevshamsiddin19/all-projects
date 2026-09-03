/* ---------- "O'qib bo'ldim" belgilari ----------
 *
 * Boblar (papkalar) va mavzular uchun o'qilgan belgisi. Ikki narsa uchun
 * kerak: qayerda to'xtaganini eslash va KEYINGI qadamni ko'rsatish.
 *
 * NIMA UCHUN UZOQ BOSISH
 * ======================
 * Qator bosilganda odatda mavzu OCHILADI. Agar belgilash ham shu qatorda
 * bo'lsa, ikkisi bir-biriga xalaqit beradi. Uzoq bosish ularni ajratadi va
 * tasodifan "o'qidim" bo'lib qolishning oldini oladi — belgi orqaga
 * qaytariladigan bo'lsa ham, u KEYINGI mavzu qaysiligini o'zgartiradi,
 * ya'ni xato bosish o'quv yo'lini chalkashtiradi.
 *
 * Kutish vaqti qasddan uzun (7 soniya). Bosib turilgan vaqt ko'rinib
 * turadi (qatorda to'ladigan chiziq), aks holda odam nima bo'layotganini
 * bilmay qo'yib yuborardi.
 *
 * SAQLASH
 * =======
 * `localStorage` remote-storage.js orqali serverga sinxronlanadi, ya'ni
 * telefonda belgilangani kompyuterda ham ko'rinadi.
 *
 * Kalit: "<lang>::folder::<yo'l>" yoki "<lang>::topic::<id>".
 * Tilni ham qo'shamiz: bir xil nomli bob ikki kursda bo'lishi mumkin.
 */
(function (root) {
  'use strict';

  var KEY = 'grammar_read_v1';
  var HOLD_MS = 7000;

  function readAll() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '{}');
      return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
    } catch (e) { return {}; }
  }
  function writeAll(m) {
    try { localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) {}
    cache = null;
  }

  /* Ro'yxat har qator uchun so'raladi — har safar JSON o'qish sekin. */
  var cache = null;
  function all() { if (!cache) cache = readAll(); return cache; }

  function k(lang, kind, id) { return lang + '::' + kind + '::' + id; }

  function isRead(lang, kind, id) { return !!all()[k(lang, kind, id)]; }

  function setRead(lang, kind, id, on) {
    var m = readAll();
    if (on) m[k(lang, kind, id)] = Date.now(); else delete m[k(lang, kind, id)];
    writeAll(m);
  }

  /* Bob o'qilgan hisoblanadi: o'zi belgilangan BO'LSA yoki ichidagi
     mavzularning hammasi belgilangan bo'lsa. Ikkinchisi kerak — odam
     mavzularni birma-bir belgilab chiqsa, bob ham yopilgan bo'lishi
     kerak, aks holda u "tugallanmagan" bo'lib turaverardi. */
  function folderDone(lang, path, topicIds) {
    if (isRead(lang, 'folder', path)) return true;
    if (!topicIds || !topicIds.length) return false;
    for (var i = 0; i < topicIds.length; i++) {
      if (!isRead(lang, 'topic', topicIds[i])) return false;
    }
    return true;
  }

  /* KEYINGI qadam — ro'yxatdagi birinchi belgilanmagan element.
     `items` tartibi ekrandagi tartib bilan bir xil bo'lishi shart. */
  function nextIndex(items) {
    for (var i = 0; i < items.length; i++) if (!items[i]) return i;
    return -1;   // hammasi o'qilgan
  }

  root.ReadMark = {
    HOLD_MS: HOLD_MS,
    isRead: isRead,
    setRead: setRead,
    folderDone: folderDone,
    nextIndex: nextIndex,
    refresh: function () { cache = null; }
  };

  /* Boshqa qurilmadan kelgan belgilar ko'rinishi uchun. */
  try {
    root.addEventListener('remote-storage:refreshed', function () { cache = null; });
  } catch (e) {}
})(window);
