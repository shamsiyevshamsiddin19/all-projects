/* Аудирование / Listening (kutubxona bo'limi) — eshitib tushunish mashqi.
 *
 * DIQQAT — nomlar chalkashmasin: `listening.js` BOSHQA narsa. U "Mashqlar"
 * bo'limidagi raqam/harf/ism eshitib yozish drili (`listening_practice`).
 * Bu fayl esa kutubxonadagi «Аудирование» / «Listening» bo'limi uchun
 * (`ru_listening`, `en_listening`) — `.md` matnlar ustida ishlaydi.
 *
 * G'oya: Chtenie bilan AYNAN BIR XIL `.md` fayl ishlatiladi, faqat mashq
 * teskari. O'qishda matn ochiq turadi va ovoz yordamchi; bu yerda ovoz
 * asosiy, matndagi kalit so'zlar YASHIRIN — ularni quloq bilan tanib
 * to'ldirasiz.
 *
 * BO'SHLIQLAR QAYERDAN OLINADI:
 *   `{слово|tarjima}` deb belgilangan so'zlar. Bu tasodifiy emas: matnda
 *   aynan MUHIM so'zlar shunday belgilanadi, ya'ni tekshirishga arziydigan
 *   so'zlar allaqachon ajratilgan. Shuning uchun mavjud Chtenie
 *   fayllaringiz hech qanday o'zgarishsiz ishlaydi.
 *   Gapda belgilangan so'z bo'lmasa — zaxira sifatida eng uzun so'z
 *   (5+ harf, gap boshidagisi emas) bo'shliqqa aylanadi, shunda
 *   belgilanmagan matn ham mashqqa yaraydi.
 *
 * IKKI DARAJA (`listening_mode` localStorage'da):
 *   'choice' — yengil: 4 variantdan tanlanadi (chalg'ituvchilar shu
 *              matndagi boshqa kalit so'zlardan olinadi).
 *   'type'   — qiyin: so'z klaviaturada yoziladi, imlo ham tekshiriladi.
 *
 * Parser va intonatsiya reading.js dan olinadi (`window.RDCore`). */
(function () {
  'use strict';

  var L = {
    sec: '', id: null, name: '', lang: 'ru-RU', dict: 'russian',
    sentences: [], idx: 0,
    mode: 'choice', rate: 1,
    alive: false, partTimer: null,
    gaps: [],
    good: 0, bad: 0,
    wrongSents: [],
    startedAt: 0, logged: false,
    pool: []
  };

  function core() { return window.RDCore || null; }

  /* ================= Ovoz (intonatsiya bilan) ================= */

  function halt() {
    if (L.partTimer) { clearTimeout(L.partTimer); L.partTimer = null; }
    if (window.TTS) TTS.cancel(); else { try { window.speechSynthesis.cancel(); } catch (e) {} }
  }

  /* `rate` ATAYLAB argument sifatida olinadi, `L.rate` dan emas: "sekin"
     tugmasi bosilganda tezlik faqat SHU o'qish uchun pasayishi kerak.
     Global holatga yozib keyin tiklashga urinilsa ishlamaydi — bo'laklar
     asinxron o'qiladi, tiklash birinchi bo'lakdan oldin ishlab ulguradi. */
  function say(text, rate, done) {
    var C = core();
    var r = rate || L.rate || 1;
    if (!text || !window.TTS || !TTS.ok() || !C) { if (done) done(); return; }
    var parts = C.prosodyParts(text);
    if (!parts.length) { if (done) done(); return; }
    var i = 0;
    (function next() {
      if (!L.alive) return;
      var p = parts[i++];
      TTS.speak(p.text, { lang: L.lang, rate: r * p.rate, pitch: p.pitch }, function () {
        if (!L.alive) return;
        if (i >= parts.length) { if (done) done(); return; }
        L.partTimer = setTimeout(next, Math.round(p.pause / r));
      });
    })();
  }

  function replay(rate) {
    var s = L.sentences[L.idx];
    if (!s) return;
    halt();
    L.alive = true;
    say(s.text, rate);
  }

  /* ================= Bo'shliqlarni aniqlash ================= */

  function markedIdx(tokens) {
    var out = [];
    tokens.forEach(function (tk, i) { if (tk.k === 'w' && tk.t) out.push(i); });
    return out;
  }

  /* Zaxira: belgilangan so'z bo'lmasa — eng uzun so'z (gap boshidagisi emas) */
  /* Yordamchi so'zlar — bulardan bo'shliq yasash mashq bermaydi: ularni
     kontekstdan taxmin qilib qo'yish oson, eshitish esa tekshirilmaydi. */
  var STOPWORDS = {
    ru: ['и','в','на','с','по','к','у','за','из','от','до','для','о','об','а','но','же',
         'ли','бы','не','ни','то','что','как','так','вот','это','этот','эта','эти','все',
         'всё','был','была','было','были','есть','мы','вы','они','она','оно','он','я','ты'],
    en: ['the','a','an','and','or','but','in','on','at','to','of','for','with','is','are',
         'was','were','be','been','this','that','it','as','by','from','they','you','we','he','she']
  };

  function isStopword(w) {
    var x = String(w || '').toLowerCase();
    return STOPWORDS.ru.indexOf(x) >= 0 || STOPWORDS.en.indexOf(x) >= 0;
  }

  /* Belgilangan so'z bo'lmaganda: eng mazmunli 1-2 so'z tanlanadi.
     Ilgari faqat ENG UZUN bitta so'z olinardi — uzun gapda bu juda oson
     bo'lib qolardi, qolgan hamma narsa ochiq turardi. */
  function fallbackIdx(tokens) {
    var cand = [], seen = 0;
    tokens.forEach(function (tk, i) {
      if (tk.k !== 'w') return;
      seen++;
      if (seen === 1) return;                 // gap boshidagi so'z olinmaydi
      var w = tk.w || '';
      if (w.length < 5 || isStopword(w)) return;
      cand.push({ i: i, len: w.length });
    });
    if (!cand.length) return [];

    cand.sort(function (a, b) { return b.len - a.len; });
    var picked = [cand[0].i];
    /* Ikkinchi bo'shliq faqat gap yetarlicha uzun bo'lsa va birinchisidan
       uzoqda tursa qo'shiladi — yonma-yon ikki bo'shliq gapni o'qib
       bo'lmaydigan qilib qo'yadi. */
    if (cand.length > 1 && seen >= 7) {
      for (var k = 1; k < cand.length; k++) {
        if (Math.abs(cand[k].i - picked[0]) >= 4) { picked.push(cand[k].i); break; }
      }
    }
    return picked.sort(function (a, b) { return a - b; });
  }

  function gapIndexes(tokens) {
    var m = markedIdx(tokens);
    return m.length ? m : fallbackIdx(tokens);
  }

  /* Butun hujjatdagi kalit so'zlar — variantlar shu yerdan olinadi */
  function buildPool(sentences) {
    var seen = {}, out = [];
    sentences.forEach(function (s) {
      (s.tokens || []).forEach(function (tk) {
        if (tk.k === 'w' && tk.t && tk.w) {
          var k = tk.w.toLowerCase();
          if (!seen[k]) { seen[k] = 1; out.push(tk.w); }
        }
      });
    });
    return out;
  }

  function norm(s) {
    return String(s || '').toLowerCase().replace(/ё/g, 'е')
      .replace(/[^0-9a-zà-ÿа-я]/gi, '').trim();
  }

  /* Bitta bo'shliq uchun 4 ta variant: to'g'risi + 3 chalg'ituvchi.
     Uzunligi yaqin so'zlar tanlanadi — ular qiyinroq va foydaliroq. */
  function optionsFor(word) {
    var opts = [word];
    var cand = L.pool.filter(function (w) { return norm(w) !== norm(word); });
    cand.sort(function (a, b) {
      return Math.abs(a.length - word.length) - Math.abs(b.length - word.length);
    });
    var near = cand.slice(0, 12);
    while (opts.length < 4 && near.length) {
      opts.push(near.splice(Math.floor(Math.random() * near.length), 1)[0]);
    }
    for (var i = opts.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = opts[i]; opts[i] = opts[j]; opts[j] = t;
    }
    return opts;
  }

  /* ================= Ko'rinish ================= */

  App.view('listening_doc', {
    nav: 'languages',
    leave: function () { L.alive = false; halt(); },
    render: function (page, params) {
      var C = core();
      L.sec = params.sec || 'ru_listening';
      L.id = params.id;
      L.lang = C ? C.ttsLang(L.sec) : 'ru-RU';
      L.dict = C ? C.dictLang(L.sec) : 'russian';
      L.sentences = []; L.idx = 0; L.good = 0; L.bad = 0;
      L.wrongSents = []; L.logged = false; L.startedAt = Date.now();
      L.alive = true;
      try { L.rate = parseFloat(localStorage.getItem('reading_rate')) || 1; } catch (e) { L.rate = 1; }
      try { L.mode = localStorage.getItem('listening_mode') === 'type' ? 'type' : 'choice'; } catch (e) { L.mode = 'choice'; }

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="au-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 id="au-title"></h1></div>' +
        '<div id="au-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      loadDoc(page);
    }
  });

  function loadDoc(page) {
    var C = core();
    if (!C) {
      var b0 = App.el('au-body');
      if (b0) b0.innerHTML = App.empty({ icon: 'alert', title: 'Modul yuklanmadi', text: 'reading.js topilmadi.' });
      return;
    }
    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(L.id) }).then(function (t) {
      var box = App.el('au-body'); if (!box) return;
      L.name = t.name || 'Matn';
      var folder = (t.folder || '').trim();

      var back = page.querySelector('#au-back');
      if (back) {
        back.setAttribute('data-act', 'go');
        back.setAttribute('data-arg', App.arg({ v: 'library', p: { sec: L.sec, path: folder } }));
      }
      var h1 = page.querySelector('#au-title');
      if (h1) h1.textContent = L.name;

      if (!t.content) {
        box.innerHTML = App.empty({
          icon: 'headphones', title: 'Matn hali yo\'q',
          text: 'Bu bo\'limga Chtenie uchun yozilgan .md faylni yuklasangiz bo\'ladi — format bir xil.'
        });
        App.icons(box);
        return;
      }

      var parsed = C.parse(t.content);
      /* Sarlavhalar reading.js da OVOZ uchun `sentences` ga qo'shiladi, lekin
         ular mashq bandi emas — "Mavzu 1" dan bo'shliq yasash mantiqsiz. */
      L.sentences = parsed.sentences.filter(function (s) {
        return s.k !== 'h' && (s.text || '').trim();
      });
      L.pool = buildPool(L.sentences);

      if (!L.sentences.length) {
        box.innerHTML = App.empty({ icon: 'headphones', title: 'Gap topilmadi', text: 'Faylda o\'qiladigan gap yo\'q.' });
        App.icons(box);
        return;
      }
      renderSentence(page);
    }).catch(function (e) {
      var box = App.el('au-body');
      if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  function renderSentence(page) {
    var box = App.el('au-body'); if (!box) return;
    if (L.idx >= L.sentences.length) { renderResult(page); return; }

    var s = L.sentences[L.idx];
    var tokens = s.tokens || [];
    var gi = gapIndexes(tokens);

    L.gaps = gi.map(function (ti) {
      return { ti: ti, word: tokens[ti].w, tr: tokens[ti].t || '', tries: 0, done: false };
    });

    var htmlParts = [];
    tokens.forEach(function (tk, i) {
      if (tk.k === 'x') { htmlParts.push(App.esc(tk.s)); return; }
      var gpos = gi.indexOf(i);
      if (gpos < 0) { htmlParts.push(App.esc(tk.w)); return; }
      var w = tk.w || '';
      htmlParts.push(
        '<button class="au-gap" data-g="' + gpos + '" style="min-width:' + Math.max(52, w.length * 14) + 'px">' +
        '<span class="au-gap-txt">' + new Array(w.length + 1).join('·') + '</span></button>'
      );
    });

    box.innerHTML =
      '<div class="au-head">' +
      '<div class="au-progress">' + (L.idx + 1) + ' / ' + L.sentences.length + '</div>' +
      '<div class="seg au-mode" id="au-mode">' +
      '<button class="' + (L.mode === 'choice' ? 'active' : '') + '" data-m="choice">Yengil</button>' +
      '<button class="' + (L.mode === 'type' ? 'active' : '') + '" data-m="type">Qiyin</button>' +
      '</div></div>' +
      '<div class="au-bar"><i style="width:' + Math.round((L.idx / L.sentences.length) * 100) + '%"></i></div>' +

      '<div class="au-playrow">' +
      '<button class="au-play" id="au-play" aria-label="Tinglash"><span data-icon="volume" data-icon-size="26"></span></button>' +
      '<button class="au-slow" id="au-slow">0.7x sekin</button>' +
      '</div>' +

      '<p class="muted au-hint">Tinglang va tushib qolgan so\'zlarni to\'ldiring. Nuqtalarga bosing.</p>' +
      '<div class="au-sent" id="au-sent">' + htmlParts.join('') + '</div>' +
      '<div class="au-tr" id="au-tr"' + (s.tr ? '' : ' hidden') + ' style="display:none">' + App.esc(s.tr || '') + '</div>' +
      '<div id="au-answer"></div>' +
      '<div class="au-nav">' +
      '<button class="btn sec" id="au-prev"' + (L.idx === 0 ? ' disabled' : '') + '>Ortga</button>' +
      '<button class="btn" id="au-next">' + (L.gaps.length ? 'Tashlab ketish' : 'Keyingi') + '</button>' +
      '</div>';
    App.icons(box);
    bindSentence(page);

    halt();
    L.alive = true;
    say(s.text);
  }

  function bindSentence(page) {
    var box = App.el('au-body'); if (!box) return;

    box.querySelectorAll('#au-mode button').forEach(function (b) {
      b.onclick = function () {
        L.mode = b.getAttribute('data-m');
        try { localStorage.setItem('listening_mode', L.mode); } catch (e) {}
        renderSentence(page);
      };
    });

    var play = box.querySelector('#au-play');
    if (play) play.onclick = function () { replay(); };

    var slow = box.querySelector('#au-slow');
    if (slow) slow.onclick = function () { replay(0.7); };

    box.querySelectorAll('.au-gap').forEach(function (el) {
      el.onclick = function () { openAnswer(page, +el.getAttribute('data-g')); };
    });

    var prev = box.querySelector('#au-prev');
    if (prev) prev.onclick = function () { if (L.idx > 0) { L.idx--; renderSentence(page); } };

    var next = box.querySelector('#au-next');
    if (next) next.onclick = function () { L.idx++; renderSentence(page); };
  }

  function openAnswer(page, gpos) {
    var g = L.gaps[gpos];
    if (!g || g.done) return;
    var box = App.el('au-answer'); if (!box) return;

    if (L.mode === 'choice') {
      box.innerHTML = '<div class="au-opts">' + optionsFor(g.word).map(function (o) {
        return '<button class="au-opt" data-w="' + App.esc(o) + '">' + App.esc(o) + '</button>';
      }).join('') + '</div>';
      box.querySelectorAll('.au-opt').forEach(function (b) {
        b.onclick = function () { check(page, gpos, b.getAttribute('data-w'), b); };
      });
    } else {
      box.innerHTML =
        '<div class="au-type">' +
        '<input class="input" id="au-inp" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Eshitgan so\'zingizni yozing">' +
        '<button class="btn" id="au-ok">Tekshirish</button>' +
        '</div>';
      var inp = box.querySelector('#au-inp');
      var ok = box.querySelector('#au-ok');
      if (inp) { inp.focus(); inp.onkeydown = function (e) { if (e.key === 'Enter') ok.click(); }; }
      if (ok) ok.onclick = function () { check(page, gpos, inp ? inp.value : '', null); };
    }
  }

  function check(page, gpos, answer, btn) {
    var g = L.gaps[gpos];
    if (!g || g.done) return;
    var el = document.querySelector('.au-gap[data-g="' + gpos + '"]');

    if (norm(answer) === norm(g.word)) {
      g.done = true;
      L.good++;
      if (el) { el.classList.add('ok'); el.innerHTML = '<span class="au-gap-txt">' + App.esc(g.word) + '</span>'; }
      var ab = App.el('au-answer'); if (ab) ab.innerHTML = '';
      afterGap(page);
      return;
    }

    g.tries++;
    L.bad++;
    if (btn) { btn.classList.add('bad'); btn.disabled = true; }
    if (el) { el.classList.add('shake'); setTimeout(function () { el.classList.remove('shake'); }, 400); }

    /* Birinchi xatoda javob ochilmaydi — yana bir bor tinglab ko'rish
       imkoni beriladi, faqat birinchi harf aytiladi. */
    if (g.tries === 1) {
      App.toast('Yana bir bor tinglang — birinchi harfi «' + g.word.charAt(0) + '»');
      replay();
      return;
    }

    g.done = true;
    if (el) { el.classList.add('shown'); el.innerHTML = '<span class="au-gap-txt">' + App.esc(g.word) + '</span>'; }
    var ab2 = App.el('au-answer'); if (ab2) ab2.innerHTML = '';
    /* Faqat tarjimasi bor so'z xatolarga tushadi — zaxira bo'shliqda
       (belgilanmagan so'z) tarjima yo'q, uni lug'atga qo'shib bo'lmaydi. */
    if (g.tr) {
      App.call('add_mistake', { lang: L.dict, category: L.name, ru: g.word, uz: g.tr })
        .catch(function () {});
    }
    if (L.wrongSents.indexOf(L.idx) < 0) L.wrongSents.push(L.idx);
    afterGap(page);
  }

  function afterGap(page) {
    var left = L.gaps.filter(function (g) { return !g.done; }).length;
    if (left) return;

    var tr = App.el('au-tr');
    if (tr && tr.textContent.trim()) { tr.hidden = false; tr.style.display = ''; }

    var next = App.el('au-next');
    if (next) {
      next.textContent = L.idx + 1 >= L.sentences.length ? 'Natijani ko\'rish' : 'Keyingi gap';
      next.classList.add('ready');
    }
  }

  function renderResult(page) {
    var box = App.el('au-body'); if (!box) return;
    halt();
    var total = L.good + L.bad;
    var pct = total ? Math.round((L.good / total) * 100) : 0;

    box.innerHTML =
      '<div style="text-align:center;padding-top:8px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 22px">Tinglash tugadi</h2>' +
      '<div class="stat-strip" style="max-width:280px;margin:0 auto 26px">' +
      '<div class="s"><div class="n" style="color:var(--success)">' + L.good + '</div><div class="l">To\'g\'ri</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)">' + L.bad + '</div><div class="l">Xato</div></div>' +
      '<div class="s"><div class="n">' + L.sentences.length + '</div><div class="l">Gap</div></div>' +
      '</div>' +
      (L.wrongSents.length
        ? '<button class="btn" id="au-retry">⚠ Xato bo\'lgan ' + L.wrongSents.length + ' gapni qaytarish</button>'
        : '<p class="muted">Hammasini to\'g\'ri eshitdingiz! 🎉</p>') +
      '<button class="btn ' + (L.wrongSents.length ? 'ghost' : '') + '" style="margin-top:10px" id="au-again">Boshidan</button>' +
      '</div>';
    App.icons(box);

    if (total > 0 && !L.logged) {
      if (window.Activity) Activity.mark();
      App.call('log_activity', {
        section: 'listening', object: L.name, amount: total, unit: 'so\'z',
        duration: L.startedAt ? Math.round((Date.now() - L.startedAt) / 1000) : null,
        meta: { sec: L.sec, good: L.good, bad: L.bad, mode: L.mode }
      }).catch(function () {});
      L.logged = true;
    }

    var retry = App.el('au-retry');
    if (retry) retry.onclick = function () {
      L.sentences = L.wrongSents.map(function (i) { return L.sentences[i]; });
      L.idx = 0; L.good = 0; L.bad = 0; L.wrongSents = []; L.logged = false;
      L.alive = true;
      renderSentence(page);
    };
    var again = App.el('au-again');
    if (again) again.onclick = function () {
      L.idx = 0; L.good = 0; L.bad = 0; L.wrongSents = []; L.logged = false;
      L.alive = true;
      renderSentence(page);
    };
  }

})();
