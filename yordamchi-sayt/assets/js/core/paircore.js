/* ---------- Juftlash yadrosi: o'xshash/adashtiriladigan so'zlarni topish ----------
   Bitta manba: vocab.js ham, home.js ham SHU yerdan foydalanadi (`window.PairCore`).
   Ilgari algoritm ikki faylda nusxalangan edi va ular bir-biridan uzoqlashib
   ketishi mumkin edi.

   UCH MANBA BOR, shu tartibda ishlatiladi:

   0) QO'LDA KO'RSATILGAN — `.md` faylda `> **Chalkashadi:** so'z1, so'z2`.
      Odam yozgani har doim taxmindan ustun, shuning uchun birinchi o'rinda.

   Qolgan ikkitasi avtomatik topiladi:

   A) O'ZAK OILASI — bir o'zakdan prefiks bilan yasalgan so'zlar:
        давать / отдавать / передавать / раздавать ...
        я открываю / я закрываю   (от+крываю, за+крываю)
      Bu eng qimmatli guruh: ma'no aynan PREFIKSDA farq qiladi.

   B) IMLO O'XSHASHLIGI — yozilishi deyarli bir xil, ma'nosi boshqa:
        предавать / придавать,  я храню / я храплю,  я рисую / я рискую

   NIMA UCHUN QAT'IY CHEKLOVLAR BOR
   --------------------------------
   Avvalgi versiya 150 so'zdan 166 ta "oila" yasagan edi: bitta so'z 12 ta
   oilaga tushib ketardi va "я пишу / я сижу" kabi umuman o'xshamagan
   juftlar chiqardi. Ikki sabab bor edi:

     1. "я " qo'shimchasi solishtirishga qo'shilib ketardi. "пишу"/"сижу"
        o'zaro 2 harf farq qiladi, uzunligi 4 — nisbat 0.5, rad etilishi
        kerak. Lekin "я пишу"/"я сижу" da uzunlik 6 bo'lib, nisbat 0.33 ga
        tushadi va chegaradan o'tib ketadi. Shuning uchun endi olmosh
        (я, ты, он...) solishtirishdan OLDIN olib tashlanadi.

     2. Bir so'z bir nechta oilada bo'la olardi. Endi har so'z FAQAT BITTA
        oilaga tegishli: avval o'zak oilalari yig'iladi (A), qolganlari
        ustida imlo o'xshashligi qidiriladi (B).

   Zaif juftni ko'rsatgandan ko'ra umuman ko'rsatmagan afzal: mashqning
   maqsadi — chalkashtiriladigan so'zlarni ajratish, tasodifan bir-biriga
   o'xshab qolgan so'zlarni emas. */
(function (root) {
  'use strict';

  /* Tuslangan shakllardagi olmosh — solishtirishga qo'shilmasin */
  var PRONOUNS = ['я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они', 'i', 'you', 'we', 'they', 'he', 'she'];

  /* Rus fe'l prefikslari — uzunidan qisqasiga, "pere" "pe" dan oldin topilsin */
  var PREFIXES = [
    'недо', 'подо', 'обо', 'ото', 'через', 'черес', 'сверх',
    'пере', 'пред', 'пре', 'при', 'про', 'раз', 'рас', 'воз', 'вос',
    'вз', 'вс', 'вы', 'во', 'до', 'за', 'из', 'ис', 'на', 'над',
    'об', 'от', 'по', 'под', 'со', 'у', 'о', 'с'
  ].sort(function (a, b) { return b.length - a.length; });

  /* Solishtiriladigan "asl" so'z: kichik harf, ё->е, olmoshsiz */
  function coreWord(raw) {
    var w = String(raw || '').toLowerCase().replace(/ё/g, 'е').trim();
    var sp = w.indexOf(' ');
    if (sp > 0) {
      var first = w.slice(0, sp);
      if (PRONOUNS.indexOf(first) >= 0) w = w.slice(sp + 1).trim();
    }
    return w;
  }

  /* So'zdan prefiksni olib tashlab, mumkin bo'lgan o'zaklarni qaytaradi.
     Bittadan ko'p bo'lishi mumkin ("подавать" -> "давать" va "одавать"),
     shuning uchun hammasi sinab ko'riladi. */
  function stems(w) {
    var out = [];
    for (var i = 0; i < PREFIXES.length; i++) {
      var p = PREFIXES[i];
      if (w.indexOf(p) === 0 && w.length - p.length >= 4) out.push(w.slice(p.length));
    }
    return out;
  }

  function levenshtein(a, b) {
    var m = a.length, n = b.length;
    if (!m) return n;
    if (!n) return m;
    var prev = new Array(n + 1), cur = new Array(n + 1), i, j;
    for (j = 0; j <= n; j++) prev[j] = j;
    for (i = 1; i <= m; i++) {
      cur[0] = i;
      for (j = 1; j <= n; j++) {
        var cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      }
      var t = prev; prev = cur; cur = t;
    }
    return prev[n];
  }

  function sharedPrefix(a, b) {
    var n = Math.min(a.length, b.length), i = 0;
    while (i < n && a.charAt(i) === b.charAt(i)) i++;
    return i;
  }

  /* (B) Ikki so'z ROSTDAN adashtiriladigan darajada o'xshashmi?
     Faqat qisqa masofa YETARLI EMAS — ular ko'zga ham o'xshab ko'rinishi,
     ya'ni boshi bir xil bo'lishi kerak. "храню/храплю" (umumiy bosh "хра")
     o'xshaydi; "пишу/сижу" esa yo'q, garchi masofa ikkalasida ham 2 bo'lsa. */
  function looksAlike(a, b) {
    if (a === b) return false;
    var maxLen = Math.max(a.length, b.length);
    if (maxLen < 5) return false;
    if (Math.abs(a.length - b.length) > 2) return false;

    var d = levenshtein(a, b);
    if (d < 1 || d > 2) return false;

    /* Asosiy filtr — UMUMIY BOSH. Masofaning o'zi yetarli emas: "пишу" va
       "сижу" ham 2 harf farq qiladi, lekin ular bir-biriga o'xshamaydi.
       "храню"/"храплю" esa (umumiy bosh "хра") aynan chalkashtiriladigan
       juft — shuning uchun chegara masofada emas, boshning uzunligida. */
    return sharedPrefix(a, b) >= 3;
  }

  var MAX_FAMILY = 8;

  /* words: [{ru, uz, ...}] -> [[w, w, ...], ...]
     Har so'z ENG KO'PI BILAN BITTA oilada bo'ladi. */
  function build(words, lang) {
    var list = words || [];
    if (list.length < 2) return [];

    var cores = list.map(function (w) { return coreWord(w.ru); });
    var used = new Array(list.length);
    var groups = [];

    function take(idxs) {
      /* Lug'atda bir so'z ikki marta yozilgan bo'lishi mumkin — bir xil
         so'zdan iborat "juftlik" mashq emas, shuning uchun matni bo'yicha
         takrorlar tashlanadi. */
      var seenText = {};
      idxs = idxs.filter(function (i) {
        var c = cores[i];
        if (seenText[c]) return false;
        seenText[c] = true;
        return true;
      });
      if (idxs.length < 2) return;
      var g = idxs.slice(0, MAX_FAMILY);
      g.forEach(function (i) { used[i] = true; });
      groups.push(g.map(function (i) { return list[i]; }));
    }

    /* --- 0) QO'LDA KO'RSATILGAN juftliklar (.md dagi "Chalkashadi:") ---
       Bu eng ishonchli manba: so'zni AI emas, odam (yoki tekshirilgan AI
       matni) bog'lagan. Shuning uchun avtomatik topilganidan OLDIN olinadi
       va bu so'zlar keyingi shoxobchalarga umuman qo'shilmaydi. */
    var byCore = {};
    cores.forEach(function (c, i) { if (byCore[c] === undefined) byCore[c] = i; });

    list.forEach(function (w, i) {
      if (used[i]) return;
      var linked = w.pairWith;
      if (!linked || !linked.length) return;
      var idxs = [i];
      linked.forEach(function (other) {
        var j = byCore[coreWord(other)];
        if (j !== undefined && j !== i && !used[j] && idxs.indexOf(j) < 0) idxs.push(j);
      });
      take(idxs);
    });

    /* --- A) O'zak oilalari --- */
    if (lang === 'russian') {
      var byStem = {};
      list.forEach(function (w, i) {
        var c = cores[i];
        if (c.length < 5) return;
        stems(c).forEach(function (st) {
          if (st.length < 4) return;
          (byStem[st] = byStem[st] || []).push(i);
        });
      });
      /* So'zning O'ZI boshqalarning ochiq o'zagi bo'lishi mumkin:
         "давать" — "отдавать"/"передавать" oilasining o'zagi.
         Bu ATAYLAB IKKINCHI o'tishda qilinadi. Birinchi tsikl ichida
         qilinganda tartibga bog'liq bo'lib qolardi: "давать" ro'yxatda
         birinchi kelsa, o'sha paytda `byStem['давать']` hali yaratilmagan
         bo'lardi va bosh so'z o'z oilasiga TUSHMAY qolardi. */
      list.forEach(function (w, i) {
        var c = cores[i];
        if (c.length >= 5 && byStem[c] && byStem[c].indexOf(i) < 0) byStem[c].push(i);
      });
      /* Katta oiladan boshlaymiz — so'z eng mazmunli guruhga tushsin */
      Object.keys(byStem)
        .sort(function (a, b) { return byStem[b].length - byStem[a].length; })
        .forEach(function (st) {
          var free = byStem[st].filter(function (i, pos, arr) {
            return !used[i] && arr.indexOf(i) === pos;
          });
          take(free);
        });
    }

    /* --- B) Imlo o'xshashligi (qolganlar ustida) ---
       Har so'zni har so'z bilan solishtirish 8000 so'zli lug'atda 64 million
       taqqoslash bo'lardi — ilova qotib qolardi. Lekin `looksAlike` baribir
       UMUMIY BOSH (3 harf) talab qiladi, ya'ni birinchi 3 harfi boshqacha
       so'zlar hech qachon juft bo'lolmaydi. Shuning uchun so'zlar birinchi
       3 harfi bo'yicha savatlarga bo'linadi va solishtirish faqat savat
       ICHIDA ketadi. Natija aynan bir xil, tezligi esa lug'at hajmidan
       deyarli mustaqil. */
    var buckets = {};
    for (var i2 = 0; i2 < list.length; i2++) {
      if (used[i2]) continue;
      var c2 = cores[i2];
      if (c2.length < 5) continue;
      var key = c2.slice(0, 3);
      (buckets[key] = buckets[key] || []).push(i2);
    }
    Object.keys(buckets).forEach(function (key) {
      var idxs = buckets[key];
      for (var x = 0; x < idxs.length; x++) {
        var a = idxs[x];
        if (used[a]) continue;
        var ca = cores[a];
        var bucket = [a];
        for (var y = x + 1; y < idxs.length; y++) {
          var b = idxs[y];
          if (used[b]) continue;
          if (looksAlike(ca, cores[b])) bucket.push(b);
        }
        take(bucket);
      }
    });

    return groups;
  }

  root.PairCore = {
    build: build,
    coreWord: coreWord,
    levenshtein: levenshtein,
    looksAlike: looksAlike
  };
})(typeof window !== 'undefined' ? window : this);
