/* ---------- Lug'at qulfi: diqqatni bir joyga yig'ish ----------
 *
 * Muammo: lug'atda 25 000 dan ortiq so'z bor. Hammasi bir vaqtda ochiq
 * turganda lenta ham, qidiruv ham, mashqlar ham butun to'plamdan tortadi —
 * ya'ni 1-1000 ni o'rganayotgan odamga 7000-chi so'z ham chiqaveradi.
 *
 * Qulf ikki ishni qiladi:
 *   1) qulflangan bo'limga KIRIB bo'lmaydi (qator qulf belgisi bilan
 *      ko'rinadi — nima kutayotgani bilinib tursin);
 *   2) qulflangan so'zlar BOSHQA JOYLARDAN ham yo'qoladi: lenta, qidiruv,
 *      filtrlar, juftlash, Reels — hammasi bitta havzadan oladi.
 *
 * ICHIDA QOLGANI EMAS, RO'YXATDAGISI QULFLANADI
 * ---------------------------------------------
 * Qoida "ro'yxatda yo'q hamma narsa qulf" EMAS. Har to'plam (`root`) uchun
 * alohida yoziladi, ro'yxatda yo'q to'plam esa butunlay ochiq. Aks holda
 * yangi lug'at qo'shilganda u o'zi-o'zidan qulflanib qolardi va buni
 * tushunish qiyin bo'lardi.
 *
 * Ochiq bo'limlar `localStorage` da (server bilan sinxron), ya'ni telefonda
 * ochilgani kompyuterda ham ochiq bo'ladi.
 */
(function (root) {
  'use strict';

  var KEY = 'vocab_unlocked_v1';   // qo'shimcha ochilgan yo'llar

  /* Foydalanuvchi talabi: barcha lug'atlardan bloklar olib tashlangan, barcha to'plamlar to'liq ochiq. */
  var RULES = [];

  function readExtra() {
    return [];
  }
  function writeExtra(list) {
    cache = null;
  }

  var cache = null;
  function openList() {
    return [];
  }

  function ruleFor(path) {
    return null;   // qoida yo'q -> to'liq ochiq
  }

  function isLocked(path) {
    return false;  // barcha bloklar olib tashlangan
  }

  /* Havzadan qulflanganlarini olib tashlaydi. Lenta, qidiruv, filtrlar va
     juftlash shu bitta havzadan oladi, shuning uchun filtr ham bitta. */
  function filterWords(list) {
    return (list || []).filter(function (w) { return !isLocked(w && w.cat); });
  }

  /* --- Sozlamalar uchun: qulflanadigan BO'LIMLAR ro'yxati ---
     Ro'yxat qo'lda yozilmaydi — ma'lumotdan o'rganiladi. `note()` har
     kategoriya yo'lini ko'rsatadi, modul esa to'plam ostidagi BIRINCHI
     bo'lakni bo'lim deb oladi. Shunda kitobga yangi bo'lim qo'shilsa u
     sozlamalarda o'zi paydo bo'ladi. */
  var units = {};
  function note(cat) {
    cat = String(cat || '');
    var r = ruleFor(cat);
    if (!r) return;
    var rest = cat.slice(r.root.length + 1);
    if (!rest) return;
    var seg = rest.split('/')[0];
    var path = r.root + '/' + seg;
    if (!units[path]) units[path] = { path: path, root: r.root, name: seg, count: 0 };
    units[path].count++;
  }
  function unitList() {
    return Object.keys(units).map(function (p) {
      var u = units[p];
      return { path: u.path, root: u.root, name: u.name, words: u.count, locked: isLocked(u.path) };
    });
  }

  function setOpen(path, on) {
    var list = readExtra();
    var i = list.indexOf(path);
    if (on && i < 0) list.push(path);
    if (!on && i >= 0) list.splice(i, 1);
    /* Qoidada yozilgan boshlang'ich ochiq bo'limni yopib bo'lmaydi —
       aks holda foydalanuvchi o'zini butunlay tashqarida qoldirardi. */
    writeExtra(list);
  }
  function isFixedOpen(path) {
    var out = false;
    RULES.forEach(function (r) { if (r.open.indexOf(path) >= 0) out = true; });
    return out;
  }

  root.WordLock = {
    isLocked: isLocked,
    filterWords: filterWords,
    note: note,
    units: unitList,
    setOpen: setOpen,
    isFixedOpen: isFixedOpen,
    refresh: function () { cache = null; }
  };

  /* Boshqa qurilmada ochilgan bo'lim shu yerda ham ochilsin. */
  try {
    root.addEventListener('remote-storage:refreshed', function () { cache = null; });
  } catch (e) {}
})(window);
