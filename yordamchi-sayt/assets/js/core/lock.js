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

  /* Har to'plam uchun BOSHLANG'ICH ochiq qism. Qolgani qulf. */
  var RULES = [
    { root: '1-8000',            open: ['1-8000/1-1000'] },
    { root: 'Тематический 9000', open: ['Тематический 9000/ОСНОВНЫЕ ПОНЯТИЯ'] }
  ];

  function readExtra() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(v) ? v.filter(function (x) { return typeof x === 'string' && x; }) : [];
    } catch (e) { return []; }
  }
  function writeExtra(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {}
    cache = null;
  }

  /* Ochiq prefikslar ro'yxati — qoidadagilar + qo'lda ochilganlar. */
  var cache = null;
  function openList() {
    if (!cache) {
      cache = [];
      RULES.forEach(function (r) { r.open.forEach(function (p) { cache.push(p); }); });
      readExtra().forEach(function (p) { if (cache.indexOf(p) < 0) cache.push(p); });
    }
    return cache;
  }

  function ruleFor(path) {
    for (var i = 0; i < RULES.length; i++) {
      var r = RULES[i].root;
      if (path === r || path.indexOf(r + '/') === 0) return RULES[i];
    }
    return null;   // qoida yo'q -> ochiq
  }

  /* `path` — kategoriya YO'LI yoki papka yo'li. Uchta holat bor:
       - ochiq prefiks ICHIDA        -> ochiq
       - ochiq prefiks SHU YO'L ichida -> "yarim ochiq", kirsa bo'ladi
         (masalan `1-8000` ning o'zi: ichida 1-1000 ochiq turibdi)
       - aks holda                    -> qulf */
  function isLocked(path) {
    path = String(path || '');
    if (!path || !ruleFor(path)) return false;
    var list = openList();
    for (var i = 0; i < list.length; i++) {
      var op = list[i];
      if (path === op || path.indexOf(op + '/') === 0) return false;  // ichida
      if (op.indexOf(path + '/') === 0) return false;                 // yarim ochiq
    }
    return true;
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
