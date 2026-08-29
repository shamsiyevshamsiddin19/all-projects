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

  var B = { lang: 'russian', tab: 'all', q: '', data: null, order: [] };

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

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' +
        App.arg({ v: 'vocab', p: { lang: B.lang } }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(LANGS[B.lang].name) + '</h1>' +
        '<button class="icon-btn ghost" id="vb-other" style="margin-left:auto" ' +
        'title="Boshqa tilga o\'tish">' + (B.lang === 'russian' ? 'V' : 'C') + '</button>' +
        '</div>' +
        '<div id="vb-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      var other = page.querySelector('#vb-other');
      if (other) other.onclick = function () {
        App.go('vocab_browse', { lang: B.lang === 'russian' ? 'english' : 'russian' });
      };

      load(B.lang).then(function (res) {
        B.data = res.data; B.order = res.order;
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
      var top = topSeg(cat);
      if (!byTop[top]) { byTop[top] = { name: top, secs: [], total: 0 }; groups.push(byTop[top]); }
      byTop[top].secs.push({ cat: cat, leaf: leafSeg(cat), words: words });
      byTop[top].total += words.length;
    });

    if (!groups.length) {
      host.innerHTML = App.empty({ icon: 'list', title: 'Topilmadi', text: 'Boshqa so\'z kiritib ko\'ring.' });
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
