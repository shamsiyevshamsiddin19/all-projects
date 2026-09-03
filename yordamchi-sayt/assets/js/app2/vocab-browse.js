/* ---------- Lug'at ko'rgichi: butun lug'at bitta ekranda ----------
 *
 * Lug'at bo'limidagi C (rus) / V (ingliz) tugmalari shu yerni ochadi.
 *
 * MAQSAD: mashq qilish emas, KO'RIB CHIQISH. Yuklangan hamma bo'lim
 * (8000, 229 va keyin qo'shilganlar) zich to'r ko'rinishida chiqadi,
 * shunda qaysi so'zni bilish/bilmaslikni bir qarashda belgilash mumkin.
 *
 * So'z bosilganda uchta amal ochiladi:
 *   1. O'rgandim  — so'z HAMMA joydan chiqadi (flashcard, svayp, reels,
 *                   test, bosh sahifa lentasi). `WordState.forPractice`.
 *   2. Saqlash    — "hozir o'rganyapman" ro'yxati.
 *   3. Rang       — o'zi uchun guruhlash; bir xil rangdagilar "Guruhlar"
 *                   bo'limida birga turadi.
 *
 * Kompyuterda sichqoncha so'z ustiga borsa tarjima darhol ko'rinadi
 * (`title` emas, o'z qalqib chiquvchi oynachasi — brauzerning `title`
 * kechikishi ro'yxatni ko'rib chiqishni sekinlashtiradi).
 */
(function () {
  'use strict';

  var LANGS = {
    russian: { name: 'Rus tili', key: 'C' },
    english: { name: 'Ingliz tili', key: 'V' }
  };

  /* `mode` — TEZ REJIM. Bo'sh bo'lsa so'z bosilganda oynacha ochiladi.
     'master' | 'save' | '#rrggbb' bo'lsa esa oynacha OCHILMAYDI, bosilgan
     so'zga o'sha amal darrov qo'llanadi. Yuzlab so'zni tartiblashda har
     safar oynacha ochib yopish juda sekin edi. */
  var B = { lang: 'russian', tab: 'all', q: '', data: null, order: [], mode: '', folder: '' };

  /* Kategoriya SHU papka ichidami. Bo'sh papka = ildiz = hammasi. */
  function inScope(cat) {
    if (!B.folder) return true;
    return cat === B.folder || String(cat).indexOf(B.folder + '/') === 0;
  }

  /* Guruh sarlavhasi uchun nom: papka ostidagi BIRINCHI bo'lak.
     Ildizda bu odatdagi `topSeg`, papka ichida esa bir pog'ona pastdagi
     nom — aks holda "1-1000" ichida ham guruh "1-8000" deb yozilardi. */
  function groupSeg(cat) {
    if (!B.folder) return topSeg(cat);
    var rest = String(cat).slice(B.folder.length + 1);
    var i = rest.indexOf('/');
    return i < 0 ? (rest || leafSeg(cat)) : rest.slice(0, i);
  }

  function WS() { return window.WordState; }

  /* ---------- Ma'lumot ---------- */
  function load(lang) {
    return App.call('get_dict_data', null, { query: 'lang=' + lang }).then(function (j) {
      var data = {}, order = j.order || [];
      (j.items || []).forEach(function (it) {
        (data[it.category] = data[it.category] || []).push({
          ru: it.word_ru, uz: it.word_uz, note: it.note || ''
        });
      });
      order.forEach(function (c) { if (!data[c]) data[c] = []; });
      Object.keys(data).forEach(function (c) { if (order.indexOf(c) < 0) order.push(c); });
      return { data: data, order: order };
    });
  }

  /* ---------- Ko'rinish ---------- */
  App.view('vocab_browse', {
    nav: 'languages',
    render: function (page, params) {
      B.lang = params.lang === 'english' ? 'english' : 'russian';
      B.tab = params.tab || 'all';
      B.q = '';
      B.folder = params.folder || '';

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' +
        App.arg({ v: 'vocab', p: { lang: B.lang, folder: B.folder } }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        /* Sarlavha QAYERDAN kelinganini aytadi. Ilgari doim til nomi
           turardi, endi esa "1-1000" ichidan kirilsa shu yoziladi —
           aks holda ekrandagi so'zlar qaysi to'plamdanligi bilinmasdi. */
        '<h1>' + App.esc(B.folder ? leafSeg(B.folder) : LANGS[B.lang].name) + '</h1>' +
        '<button class="icon-btn ghost vb-mode-btn" id="vb-mode" style="margin-left:auto" ' +
        'title="Tez rejim"><span data-icon="edit" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" id="vb-other" ' +
        'title="Boshqa tilga o\'tish">' + (B.lang === 'russian' ? 'V' : 'C') + '</button>' +
        '</div>' +
        '<div id="vb-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      var modeBtn = page.querySelector('#vb-mode');
      if (modeBtn) modeBtn.onclick = function () { openModePicker(page); };
      syncModeBtn(page);

      var other = page.querySelector('#vb-other');
      if (other) other.onclick = function () {
        /* Papka tashlanadi: yo'llar ikki tilda bir xil bo'lsa ham
           (`1-8000/...`), "Тематический 9000" faqat rus tilida bor —
           papka saqlansa ingliz tilida bo'sh ekran chiqardi. */
        App.go('vocab_browse', { lang: B.lang === 'russian' ? 'english' : 'russian' });
      };

      load(B.lang).then(function (res) {
        B.data = res.data;
        /* IKKI filtr, bir joyda:
             1) papka — "C" qaysi sahifada bosilgan bo'lsa, o'shanisi;
             2) qulf — qulflangan bo'lim bu yerda ham ko'rinmasligi kerak.
           Ikkinchisi ilgari YO'Q edi: bu ekran to'g'ridan-to'g'ri serverdan
           o'qigani uchun qulflangan 22 ming so'z shu yerda ochiq chiqardi. */
        B.order = (res.order || []).filter(function (c) {
          if (!inScope(c)) return false;
          return !(window.WordLock && WordLock.isLocked(c));
        });
        paint(page);
      }).catch(function (e) {
        var b = App.el('vb-body');
        if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
      });
    }
  });

  function paint(page) {
    var box = App.el('vb-body'); if (!box) return;
    box.innerHTML =
      '<div class="vb-tabs">' +
        tabBtn('all', 'Lug\'at') +
        tabBtn('saved', 'Saqlanganlar') +
        tabBtn('groups', 'Guruhlar') +
        tabBtn('learned', 'O\'rganilganlar') +
      '</div>' +
      '<div class="vb-search">' +
        '<span data-icon="search" data-icon-size="15"></span>' +
        '<input class="vb-inp" id="vb-q" placeholder="So\'z qidirish..." value="' + App.esc(B.q) + '">' +
      '</div>' +
      '<div id="vb-content"></div>' +
      '<div class="vb-pop" id="vb-pop" hidden></div>';
    App.icons(box);

    box.querySelectorAll('.vb-tab').forEach(function (t) {
      t.onclick = function () { B.tab = t.getAttribute('data-t'); paint(page); };
    });

    var inp = box.querySelector('#vb-q');
    if (inp) {
      var timer = null;
      inp.oninput = function () {
        clearTimeout(timer);
        timer = setTimeout(function () { B.q = inp.value; paintContent(page); }, 180);
      };
    }
    paintContent(page);
  }

  function tabBtn(id, label) {
    return '<button class="vb-tab' + (B.tab === id ? ' active' : '') + '" data-t="' + id + '">' +
      App.esc(label) + '</button>';
  }

  function matches(w) {
    if (!B.q) return true;
    var q = B.q.toLowerCase();
    return (w.ru || '').toLowerCase().indexOf(q) >= 0 ||
           (w.uz || '').toLowerCase().indexOf(q) >= 0;
  }

  function paintContent(page) {
    var host = App.el('vb-content'); if (!host) return;
    if (B.tab === 'saved') return paintSaved(host, page);
    if (B.tab === 'groups') return paintGroups(host, page);
    if (B.tab === 'learned') return paintLearned(host, page);
    paintAll(host, page);
  }

  /* Bir so'z katakchasi. `data-ru` — amallar shu orqali topadi. */
  function chip(w) {
    var ws = WS();
    var mastered = ws && ws.isMastered(w.ru);
    var saved = ws && ws.isSaved(w.ru);
    var color = ws ? ws.colorOf(w.ru) : '';
    /* Uzun so'zga kichikroq o'lcham. O'lchash bilan qilinmadi: 8000+
       katakni o'lchash sahifani qotirardi. Harf soni yetarli aniq
       ko'rsatkich — ustun eni barcha kataklarda bir xil. */
    var n = (w.ru || '').length;
    var sizeCls = n >= 16 ? ' len-l' : (n >= 11 ? ' len-m' : '');
    var cls = 'vb-w' + sizeCls + (mastered ? ' done' : '') + (saved ? ' saved' : '');
    var style = color ? ' style="--wcolor:' + color + '"' : '';
    return '<button class="' + cls + (color ? ' tinted' : '') + '" data-ru="' + App.esc(w.ru) + '"' +
      style + '>' + App.esc(w.ru) + '</button>';
  }

  /* "1-8000/1-1000/1-100" -> guruh "1-8000", bo'lim "1-100".
     To'liq yo'lni sarlavha qilib yozish o'qishga qiyin va takroriy edi. */
  function topSeg(cat) {
    var i = String(cat || '').indexOf('/');
    return i < 0 ? cat : cat.slice(0, i);
  }
  function leafSeg(cat) {
    var i = String(cat || '').lastIndexOf('/');
    return i < 0 ? cat : cat.slice(i + 1);
  }

  function paintAll(host, page) {
    /* Har lug'at ALOHIDA guruh bo'ladi: ilgari 8000 ning bo'limlari va
       229 lik ro'yxat ketma-ket oqib ketardi va qaysi lug'at qayerda
       tugaganini bilib bo'lmasdi. */
    var groups = [], byTop = {};
    B.order.forEach(function (cat) {
      var words = (B.data[cat] || []).filter(matches);
      if (!words.length) return;
      var top = groupSeg(cat);
      if (!byTop[top]) { byTop[top] = { name: top, secs: [], total: 0 }; groups.push(byTop[top]); }
      byTop[top].secs.push({ cat: cat, leaf: leafSeg(cat), words: words });
      byTop[top].total += words.length;
    });

    if (!groups.length) {
      /* Ikki xil bo'shlik bor va ularni ajratish kerak: qidiruv natija
         bermadimi, yoki bu papkada umuman so'z yo'qmi (qulflangan yoki
         hali to'ldirilmagan). Bitta "Topilmadi" ikkalasiga ham yaramasdi. */
      host.innerHTML = B.q
        ? App.empty({ icon: 'search', title: 'Topilmadi',
                      text: '"' + B.q + '" bo\'yicha so\'z yo\'q. Boshqa so\'z kiritib ko\'ring.' })
        : App.empty({ icon: 'list', title: 'Bo\'sh',
                      text: 'Bu bo\'limda ko\'rsatiladigan so\'z yo\'q — qulflangan yoki hali to\'ldirilmagan.' });
      App.icons(host);
      return;
    }

    host.innerHTML = groups.map(function (g) {
      /* Bitta bo'limli lug'at (masalan 229 lik) — ortiqcha ichki sarlavha
         berilmaydi, guruh sarlavhasining o'zi yetarli. */
      var single = g.secs.length === 1 && g.secs[0].leaf === g.name;
      return '<div class="vb-group">' +
        '<div class="vb-group-h"><span>' + App.esc(g.name) + '</span>' +
        '<i>' + g.total + ' so\'z</i></div>' +
        g.secs.map(function (sec) {
          return '<div class="vb-sec">' +
            (single ? '' :
              '<div class="vb-sec-h"><span>' + App.esc(sec.leaf) + '</span>' +
              '<i>' + sec.words.length + '</i></div>') +
            '<div class="vb-grid">' + sec.words.map(chip).join('') + '</div></div>';
        }).join('') +
        '</div>';
    }).join('');
    App.icons(host);
    bindWords(host, page);
  }

  function allWords() {
    var out = [];
    B.order.forEach(function (c) { (B.data[c] || []).forEach(function (w) { out.push(w); }); });
    return out;
  }

  function paintSaved(host, page) {
    var ws = WS();
    var words = allWords().filter(function (w) { return ws && ws.isSaved(w.ru) && matches(w); });
    if (!words.length) {
      host.innerHTML = App.empty({
        icon: 'bookmark', title: 'Saqlangan so\'z yo\'q',
        text: 'Lug\'atdan so\'z tanlab "Saqlash" tugmasini bosing — hozir o\'rganayotganlaringiz shu yerda to\'planadi.'
      });
      App.icons(host); return;
    }
    host.innerHTML = '<div class="vb-sec"><div class="vb-sec-h"><span>Hozir o\'rganyapman</span>' +
      '<i>' + words.length + '</i></div><div class="vb-grid">' + words.map(chip).join('') + '</div></div>';
    bindWords(host, page);
  }

  function paintGroups(host, page) {
    var ws = WS(); if (!ws) return;
    var byColor = ws.byColor();
    var keys = Object.keys(byColor);
    if (!keys.length) {
      host.innerHTML = App.empty({
        icon: 'star', title: 'Guruh yo\'q',
        text: 'So\'zni tanlab rang bering — bir xil rangli so\'zlar shu yerda birga turadi.'
      });
      App.icons(host); return;
    }
    var index = {};
    allWords().forEach(function (w) { index[w.ru] = w; });

    var html = '';
    ws.COLORS.forEach(function (c) {
      var list = (byColor[c.hex] || [])
        .map(function (ru) { return index[ru] || { ru: ru, uz: '' }; })
        .filter(matches);
      if (!list.length) return;
      html += '<div class="vb-sec">' +
        '<div class="vb-sec-h"><span class="vb-dot" style="background:' + c.hex + '"></span>' +
        '<span>' + App.esc(c.name) + '</span><i>' + list.length + '</i></div>' +
        '<div class="vb-grid">' + list.map(chip).join('') + '</div></div>';
    });
    host.innerHTML = html;
    bindWords(host, page);
  }

  /* ---------- So'z bilan ishlash ---------- */
  function bindWords(host, page) {
    var index = {};
    allWords().forEach(function (w) { index[w.ru] = w; });

    host.querySelectorAll('.vb-w').forEach(function (el) {
      var ru = el.getAttribute('data-ru');
      var w = index[ru] || { ru: ru, uz: '' };

      /* Kompyuterda: sichqoncha ustiga kelsa tarjima darhol chiqadi */
      el.onmouseenter = function () { showTip(el, w); };
      el.onmouseleave = hideTip;

      el.onclick = function (e) {
        e.stopPropagation();
        hideTip();
        /* Tez rejim yoqilgan bo'lsa oynacha ochilmaydi — amal darrov
           qo'llanadi va ro'yxat joyida yangilanadi. */
        if (B.mode) { applyMode(w.ru, el); return; }
        openActions(el, w, page);
      };
    });
  }

  var tipEl = null;
  function showTip(el, w) {
    if (!w.uz) return;
    tipEl = App.el('vb-pop'); if (!tipEl) return;
    tipEl.innerHTML = '<b>' + App.esc(w.ru) + '</b><span>' + App.esc(w.uz) + '</span>';
    tipEl.hidden = false;
    place(tipEl, el);
  }
  function hideTip() { if (tipEl) tipEl.hidden = true; }

  function place(pop, el) {
    var r = el.getBoundingClientRect();
    pop.style.left = '0px'; pop.style.top = '0px';
    var pr = pop.getBoundingClientRect();
    var left = Math.min(Math.max(8, r.left + r.width / 2 - pr.width / 2), window.innerWidth - pr.width - 8);
    var top = r.top - pr.height - 8;
    if (top < 8) top = r.bottom + 8;           // tepada joy bo'lmasa pastga
    pop.style.left = Math.round(left) + 'px';
    pop.style.top = Math.round(top + window.scrollY) + 'px';
  }

  /* ---------- Tez rejim ---------- */

  function modeLabel(m) {
    if (m === 'master') return 'O\'rgandim';
    if (m === 'save') return 'Saqlash';
    if (m) {
      var ws = WS();
      var hit = ws && ws.COLORS.filter(function (c) { return c.hex === m; })[0];
      return hit ? hit.name : 'Rang';
    }
    return '';
  }

  /* Tugma yoqilganda "chiroq kabi" yonib turadi va joriy rejim rangini oladi */
  function syncModeBtn(page) {
    var btn = (page || document).querySelector('#vb-mode');
    if (!btn) return;
    var on = !!B.mode;
    btn.classList.toggle('on', on);
    btn.style.color = (B.mode && B.mode.charAt(0) === '#') ? B.mode : '';
    btn.setAttribute('title', on ? 'Tez rejim: ' + modeLabel(B.mode) : 'Tez rejim');
  }

  /* Bosilgan so'zga joriy rejimni qo'llaydi. Butun ro'yxat qayta
     chizilmaydi — 8000 katakni qayta yasash sezilarli sekinlik berardi;
     faqat shu katakning ko'rinishi yangilanadi. */
  function applyMode(ru, el) {
    var ws = WS(); if (!ws) return;
    if (B.mode === 'master') ws.toggleMastered(ru);
    else if (B.mode === 'save') ws.toggleSaved(ru);
    else ws.setColor(ru, ws.colorOf(ru) === B.mode ? '' : B.mode);

    var mastered = ws.isMastered(ru), saved = ws.isSaved(ru), color = ws.colorOf(ru);
    el.classList.toggle('done', mastered);
    el.classList.toggle('saved', saved);
    el.classList.toggle('tinted', !!color);
    if (color) el.style.setProperty('--wcolor', color); else el.style.removeProperty('--wcolor');
  }

  function openModePicker(page) {
    var ws = WS(); if (!ws) return;
    var html =
      '<p class="muted" style="font-size:12.5px;margin:0 0 12px">' +
      'Rejimni tanlang — shundan keyin bosilgan HAR SO\'Z shu belgini oladi. ' +
      'Ko\'p so\'zni tez tartiblash uchun.</p>' +
      '<div class="vb-act-row">' +
        '<button class="vb-act' + (B.mode === 'master' ? ' on' : '') + '" data-m="master">' +
          '<span data-icon="check" data-icon-size="17"></span><b>O\'rgandim</b>' +
          '<i>Hech qayerda chiqmaydi</i></button>' +
        '<button class="vb-act' + (B.mode === 'save' ? ' on' : '') + '" data-m="save">' +
          '<span data-icon="bookmark" data-icon-size="17"></span><b>Saqlash</b>' +
          '<i>Hozir o\'rganaman</i></button>' +
      '</div>' +
      '<div class="vb-act-lbl">Rang bilan guruhlash</div>' +
      '<div class="vb-colors">' +
        ws.COLORS.map(function (c) {
          return '<button class="vb-color' + (B.mode === c.hex ? ' on' : '') + '" data-m="' + c.hex +
            '" title="' + App.esc(c.name) + '" style="background:' + c.hex + '"></button>';
        }).join('') +
        '<button class="vb-color none' + (B.mode ? '' : ' on') + '" data-m="" title="Rejimni o\'chirish">✕</button>' +
      '</div>';
    var sh = App.sheet(html, { title: 'Tez rejim' });
    App.icons(sh);
    sh.querySelectorAll('[data-m]').forEach(function (b) {
      b.onclick = function () {
        var m = b.getAttribute('data-m');
        B.mode = (B.mode === m) ? '' : m;      // qayta bosilsa o'chadi
        App.closeSheet();
        syncModeBtn(page);
        App.toast(B.mode ? 'Tez rejim: ' + modeLabel(B.mode) : 'Tez rejim o\'chirildi');
      };
    });
  }

  /* ---------- O'rganilganlar ---------- */

  /* O'rgangan so'zlar O'Z BO'LIMIDA turadi (1-100, 101-200 ...), ya'ni
     qaysi qismni qanchalik o'zlashtirganingiz ko'rinadi. Oddiy tekis
     ro'yxat buni ko'rsatmasdi. */
  function paintLearned(host, page) {
    var ws = WS(); if (!ws) return;
    var groups = [], byTop = {}, total = 0;

    B.order.forEach(function (cat) {
      var words = (B.data[cat] || []).filter(function (w) {
        return ws.isMastered(w.ru) && matches(w);
      });
      if (!words.length) return;
      total += words.length;
      var top = groupSeg(cat);
      if (!byTop[top]) { byTop[top] = { name: top, secs: [], total: 0 }; groups.push(byTop[top]); }
      byTop[top].secs.push({ leaf: leafSeg(cat), words: words, all: (B.data[cat] || []).length });
      byTop[top].total += words.length;
    });

    if (!total) {
      host.innerHTML = App.empty({
        icon: 'check', title: 'Hali o\'rganilgan so\'z yo\'q',
        text: 'So\'zni bosib "O\'rgandim" ni tanlang — u shu yerga tushadi va mashqlarda chiqmaydi.'
      });
      App.icons(host);
      return;
    }

    host.innerHTML = groups.map(function (g) {
      return '<div class="vb-group">' +
        '<div class="vb-group-h"><span>' + App.esc(g.name) + '</span>' +
        '<i>' + g.total + ' o\'rganilgan</i></div>' +
        g.secs.map(function (sec) {
          return '<div class="vb-sec">' +
            '<div class="vb-sec-h"><span>' + App.esc(sec.leaf) + '</span>' +
            '<i>' + sec.words.length + '/' + sec.all + '</i></div>' +
            '<div class="vb-grid">' + sec.words.map(chip).join('') + '</div></div>';
        }).join('') +
        '</div>';
    }).join('');
    App.icons(host);
    bindWords(host, page);
  }

  /* Uchta amal + rang tanlash */
  function openActions(el, w, page) {
    var ws = WS(); if (!ws) return;
    var mastered = ws.isMastered(w.ru);
    var saved = ws.isSaved(w.ru);
    var color = ws.colorOf(w.ru);

    var html =
      '<div class="vb-act-head"><b>' + App.esc(w.ru) + '</b>' +
      (w.uz ? '<span>' + App.esc(w.uz) + '</span>' : '') + '</div>' +
      '<div class="vb-act-row">' +
        '<button class="vb-act' + (mastered ? ' on' : '') + '" data-a="master">' +
          '<span data-icon="check" data-icon-size="17"></span>' +
          '<b>' + (mastered ? 'O\'rgandim ✓' : 'O\'rgandim') + '</b>' +
          '<i>Hech qayerda chiqmaydi</i>' +
        '</button>' +
        '<button class="vb-act' + (saved ? ' on' : '') + '" data-a="save">' +
          '<span data-icon="bookmark" data-icon-size="17"></span>' +
          '<b>' + (saved ? 'Saqlangan' : 'Saqlash') + '</b>' +
          '<i>Hozir o\'rganaman</i>' +
        '</button>' +
      '</div>' +
      '<div class="vb-act-lbl">Rang bilan guruhlash</div>' +
      '<div class="vb-colors">' +
        ws.COLORS.map(function (c) {
          return '<button class="vb-color' + (color === c.hex ? ' on' : '') + '" ' +
            'data-hex="' + c.hex + '" title="' + App.esc(c.name) + '" ' +
            'style="background:' + c.hex + '"></button>';
        }).join('') +
        '<button class="vb-color none' + (color ? '' : ' on') + '" data-hex="" title="Rangsiz">✕</button>' +
      '</div>';

    var sh = App.sheet(html, { title: 'So\'z' });
    App.icons(sh);

    /* ENTER — eng ko'p ishlatiladigan amal, ya'ni "O'rgandim".
       Ro'yxatni ko'rib chiqishda qo'lni sichqonchadan uzmasdan tez
       belgilash mumkin bo'lsin. Oynacha yopilganda tinglagich ham
       olib tashlanadi (aks holda ular yig'ilib qolardi). */
    function onKey(e) {
      if (e.key !== 'Enter') return;
      e.preventDefault();
      var on = ws.toggleMastered(w.ru);
      App.toast(on ? '✓ O\'rgandim — endi mashqlarda chiqmaydi' : 'Belgi olib tashlandi');
      document.removeEventListener('keydown', onKey, true);
      App.closeSheet();
      paintContent(page);
    }
    document.addEventListener('keydown', onKey, true);
    var mo = new MutationObserver(function () {
      if (!document.body.contains(sh)) {
        document.removeEventListener('keydown', onKey, true);
        mo.disconnect();
      }
    });
    mo.observe(document.body, { childList: true, subtree: true });

    sh.querySelectorAll('.vb-act').forEach(function (b) {
      b.onclick = function () {
        var a = b.getAttribute('data-a');
        if (a === 'master') {
          var on = ws.toggleMastered(w.ru);
          App.toast(on ? '✓ O\'rgandim — endi mashqlarda chiqmaydi' : 'Belgi olib tashlandi');
        } else {
          var s = ws.toggleSaved(w.ru);
          App.toast(s ? '🔖 Saqlandi' : 'Saqlanganlardan olib tashlandi');
        }
        App.closeSheet();
        paintContent(page);
      };
    });

    sh.querySelectorAll('.vb-color').forEach(function (b) {
      b.onclick = function () {
        ws.setColor(w.ru, b.getAttribute('data-hex'));
        App.closeSheet();
        paintContent(page);
      };
    });
  }
})();
