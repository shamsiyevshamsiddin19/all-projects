/* =========================================================================
   Аудирование / Listening Darsligi (Ear Training & Fonetika Trenajyori)
   - 3 ta asosiy rejim:
     1. 🎓 Карточки: [ЩАС], [ЗДРАСЬТЕ] — qisqarishlar, tushuntirish va jonli audio
     2. 🎯 Тренажёр: Quloqni charxlash ovozli testi (tez/sekin TTS + variantlar)
     3. 📜 Все слова: Darsdagi barcha qisqarish va iboralar jamlanmasi
   - Zaxira va eski darslar uchun klassik Tinglash / Diktant / Test rejimi
   ========================================================================= */
(function () {
  'use strict';

  var L = {
    sec: '', id: null, name: '', lang: 'ru-RU', dict: 'russian',
    rawContent: '',
    sentences: [], idx: 0,
    tab: 'cards', // 'cards' | 'drill' | 'words' | 'listen' | 'dictate' | 'quiz'
    mode: 'choice', rate: 1,
    alive: false, partTimer: null,
    gaps: [],
    good: 0, bad: 0,
    wrongSents: [],
    startedAt: 0, logged: false,
    pool: [],
    youtubeId: null,
    ytPlayer: null,
    ytInterval: null,
    activeSubIdx: -1,
    audioPlaying: false,
    audioIdx: 0,
    questions: [],
    quizIdx: 0,
    quizScore: 0,
    quizAnswered: false,

    // Ear-Training Maxsus Holati
    isEar: false,
    cards: [],
    cardIdx: 0,
    drillQuestions: [],
    drillIdx: 0,
    drillScore: 0,
    drillPlaying: false
  };

  function core() { return window.RDCore || null; }

  /* ================= Ovoz (TTS) ================= */

  function halt() {
    L.audioPlaying = false;
    L.drillPlaying = false;
    if (L.partTimer) { clearTimeout(L.partTimer); L.partTimer = null; }
    if (window.TTS) TTS.cancel(); else { try { window.speechSynthesis.cancel(); } catch (e) {} }
  }

  function say(text, rate, done) {
    var C = core();
    var r = rate || L.rate || 1;
    if (!text) { if (done) done(); return; }

    // Agar maxsus qisqartma bo'lsa (masalan [ЩАС]), qavslarni olib tashlaymiz
    text = String(text).replace(/[\[\]]/g, '').trim();

    if (!window.TTS || !TTS.ok() || !C) {
      if (window.speechSynthesis) {
        try {
          var u = new SpeechSynthesisUtterance(text);
          u.lang = L.lang || 'ru-RU';
          u.rate = Math.max(0.5, Math.min(1.5, r));
          u.onend = function () { if (done) done(); };
          u.onerror = function () { if (done) done(); };
          window.speechSynthesis.speak(u);
          return;
        } catch (e) {}
      }
      if (done) done();
      return;
    }

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

  /* ================= Parser & Yordamchilar ================= */

  function extractYouTubeId(md) {
    if (!md) return null;
    var m = md.match(/(?:youtube:\s*|https?:\/\/(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/))([a-zA-Z0-9_-]{11})/i);
    return m ? m[1] : null;
  }

  function parseTimestamp(str) {
    if (!str) return null;
    var m = str.match(/(?:(\d{1,2}):)?(\d{1,2}):(\d{2})/);
    if (!m) return null;
    var h = m[1] ? parseInt(m[1], 10) : 0;
    var min = parseInt(m[2], 10);
    var sec = parseInt(m[3], 10);
    return h * 3600 + min * 60 + sec;
  }

  function formatTime(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    var m = Math.floor(sec / 60);
    var s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* Fonetik Ear-Training kartochkalarini o'qish */
  function parseCards(content) {
    var cards = [];
    var raw = String(content || '').replace(/\r/g, '');
    var chunks = raw.split(/\n---\n/);
    chunks.forEach(function (chk) {
      chk = chk.trim();
      if (!chk || chk.indexOf('card:') < 0) return;
      var lines = chk.split('\n');
      var card = {
        word: '',
        sound: '',
        spelling: '',
        mean: '',
        explain: '',
        example: '',
        example_audio: '',
        example_uz: ''
      };
      lines.forEach(function (l) {
        l = l.trim();
        var m = l.match(/^([a-zA-Z_]+):\s*(.+)$/);
        if (m) {
          var key = m[1].toLowerCase();
          var val = m[2].trim();
          if (key === 'card' || key === 'word') card.word = val;
          else if (key === 'sound') card.sound = val;
          else if (key === 'spelling') card.spelling = val;
          else if (key === 'mean') card.mean = val;
          else if (key === 'explain') card.explain = val;
          else if (key === 'example') card.example = val;
          else if (key === 'example_audio') card.example_audio = val;
          else if (key === 'example_uz') card.example_uz = val;
        }
      });
      if (card.word || card.sound) {
        cards.push(card);
      }
    });
    return cards;
  }

  function extractQuestions(md, sentences) {
    var qs = [];
    var lines = String(md || '').split('\n');
    var curQ = null;
    lines.forEach(function (line) {
      line = line.trim();
      var qm = line.match(/^\?\s*(.+)$/);
      if (qm) {
        if (curQ && curQ.options.length) qs.push(curQ);
        curQ = { q: qm[1].trim(), options: [], correct: 0 };
        return;
      }
      var opCorrect = line.match(/^\+\s*(.+)$/);
      if (opCorrect && curQ) {
        curQ.correct = curQ.options.length;
        curQ.options.push(opCorrect[1].trim());
        return;
      }
      var opWrong = line.match(/^-\s*(.+)$/);
      if (opWrong && curQ) {
        curQ.options.push(opWrong[1].trim());
        return;
      }
    });
    if (curQ && curQ.options.length) qs.push(curQ);

    // Agar matnda savollar bo'lmasa — kalit so'zlardan avtomatik generatsiya
    if (!qs.length && sentences && sentences.length >= 2) {
      var candidates = [];
      sentences.forEach(function (s) {
        (s.tokens || []).forEach(function (tk) {
          if (tk.k === 'w' && tk.t && tk.w && tk.w.length >= 3) {
            candidates.push({ ru: tk.w, uz: tk.t, sent: s.text });
          }
        });
      });
      if (candidates.length >= 2) {
        var c1 = candidates[0];
        var d1 = candidates[1] ? candidates[1].uz : 'Boshqa ma\'no';
        var d2 = candidates[2] ? candidates[2].uz : 'Noto\'g\'ri variant';
        var opts1 = [c1.uz, d1, d2];
        opts1.sort(function () { return Math.random() - 0.5; });
        qs.push({
          q: 'Dialogdagi «' + c1.ru + '» so\'zining to\'g\'ri tarjimasi nima?',
          options: opts1,
          correct: opts1.indexOf(c1.uz)
        });

        var c2 = candidates[Math.min(candidates.length - 1, 2)];
        var opts2 = [c2.uz, candidates[0].uz, 'Boshqa tushuncha'];
        opts2.sort(function () { return Math.random() - 0.5; });
        qs.push({
          q: '«' + c2.ru + '» so\'zi qanday tarjima qilinadi?',
          options: opts2,
          correct: opts2.indexOf(c2.uz)
        });
      }
    }
    return qs;
  }

  /* Subtitr sifatida ko'rsatiladigan qatormi?

     Savol bloki (`? savol`, `+ to'g'ri`, `- noto'g'ri`) SUBTITR EMAS.
     Ilgari ular ham gap sifatida chizilardi: Tinglash bo'limida savollar
     va TO'G'RI JAVOBLAR ochiq ko'rinib turardi, ustiga TTS ularni dialog
     kabi ovoz chiqarib o'qirdi — test butunlay ma'nosini yo'qotardi.
     Bu qatorlarni `extractQuestions()` allaqachon o'qigan.

     Dialog qatorlari UZUN TIRE (—, U+2014) bilan boshlanadi, javob
     variantlari esa oddiy defis (-, U+002D) bilan — chalkashmaydi. */
  function isSubtitleLine(s) {
    var txt = (s && s.text || '').trim();
    if (!txt || (s && s.k === 'h')) return false;
    if (/^\?\s*\S/.test(txt)) return false;      // savol
    if (/^\+\s*\S/.test(txt)) return false;      // to'g'ri variant
    if (/^-\s*\S/.test(txt)) return false;        // noto'g'ri variant
    if (/^youtube\s*:/i.test(txt)) return false;  // video havolasi (eski hujjatlar)
    return true;
  }

  /* Bo'shliqlar (gap-fill) uchun stop-words */
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

  function markedIdx(tokens) {
    var out = [];
    tokens.forEach(function (tk, i) { if (tk.k === 'w' && tk.t) out.push(i); });
    return out;
  }

  function fallbackIdx(tokens) {
    var cand = [], seen = 0;
    tokens.forEach(function (tk, i) {
      if (tk.k !== 'w') return;
      seen++;
      if (seen === 1) return;
      var w = tk.w || '';
      if (w.length < 5 || isStopword(w)) return;
      cand.push({ i: i, len: w.length });
    });
    if (!cand.length) return [];
    cand.sort(function (a, b) { return b.len - a.len; });
    var picked = [cand[0].i];
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

  function buildPool(sentences) {
    var set = {}, list = [];
    sentences.forEach(function (s) {
      (s.tokens || []).forEach(function (tk) {
        if (tk.k === 'w' && tk.w && tk.w.length >= 3 && !isStopword(tk.w)) {
          var k = tk.w.toLowerCase();
          if (!set[k]) { set[k] = true; list.push(tk.w); }
        }
      });
    });
    return list;
  }

  function formatSpelling(str) {
    str = String(str || '');
    // [harflar] ni yutiladigan harflar sifatida belgilaymiz
    return str.replace(/\[([^\]]+)\]/g, '<span class="au-swallow" title="Yutiladigan tovush">$1</span>');
  }

  function prepareDrillQuestions(rawQs, cards) {
    var list = [];
    if (rawQs && rawQs.length) {
      list = rawQs.map(function (q, qIdx) {
        var card = cards && cards[qIdx % cards.length] ? cards[qIdx % cards.length] : null;
        var cue = card ? (card.sound || card.word) : (q.options[q.correct] || '');
        var opts = q.options.map(function (opt, i) {
          return { text: opt, isCorrect: i === q.correct };
        });
        // Shuffllash (to'g'ri javob doim birinchi bo'lmasligi uchun)
        for (var i = opts.length - 1; i > 0; i--) {
          var j = Math.floor(Math.random() * (i + 1));
          var tmp = opts[i]; opts[i] = opts[j]; opts[j] = tmp;
        }
        return {
          q: q.q,
          cue: cue,
          explain: card ? card.explain : '',
          options: opts,
          answered: false,
          selected: -1,
          isCorrect: false
        };
      });
    } else if (cards && cards.length) {
      // Agar savollar bo'lmasa, kartochkalardan avtomatik tuzish
      list = cards.map(function (c, idx) {
        var opts = [
          { text: c.word, isCorrect: true }
        ];
        var other = cards.filter(function (_, i) { return i !== idx; });
        if (other[0]) opts.push({ text: other[0].word, isCorrect: false });
        if (other[1]) opts.push({ text: other[1].word, isCorrect: false });
        else opts.push({ text: 'Boshqa so\'z', isCorrect: false });
        opts.sort(function () { return Math.random() - 0.5; });
        return {
          q: 'Ovozda «' + c.sound + '» yangradi. Bu qaysi so\'zning qisqartmasi?',
          cue: c.sound,
          explain: c.explain,
          options: opts,
          answered: false,
          selected: -1,
          isCorrect: false
        };
      });
    }
    return list;
  }

  /* ================= Asosiy Ko'rinish ================= */

  App.view('listening_doc', {
    nav: 'languages',
    leave: function () {
      L.alive = false;
      halt();
      stopYouTubeTracking();
      if (L.ytPlayer) {
        try { L.ytPlayer.destroy(); } catch (e) {}
        L.ytPlayer = null;
      }
    },
    render: function (page, params) {
      var C = core();
      L.sec = params.sec || 'ru_listening';
      L.id = params.id;
      L.lang = C ? C.ttsLang(L.sec) : 'ru-RU';
      L.dict = C ? C.dictLang(L.sec) : 'russian';
      L.sentences = []; L.idx = 0; L.good = 0; L.bad = 0;
      L.wrongSents = []; L.logged = false; L.startedAt = Date.now();
      L.activeSubIdx = -1;
      L.alive = true;
      L.cards = [];
      L.cardIdx = 0;
      L.isEar = false;
      try { L.rate = parseFloat(localStorage.getItem('reading_rate')) || 1; } catch (e) { L.rate = 1; }
      try { L.mode = localStorage.getItem('listening_mode') === 'type' ? 'type' : 'choice'; } catch (e) { L.mode = 'choice'; }

      var isReadOnly = window.Auth && Auth.isReadOnly && Auth.isReadOnly();

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="au-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 id="au-title"></h1>' +
        (isReadOnly ? '' :
          '<button class="icon-btn ghost" id="au-edit" style="margin-left:auto" aria-label="Tahrirlash" title="Matnni tahrirlash">' +
          '<span data-icon="edit" data-icon-size="18"></span></button>') +
        '</div>' +

        '<div class="au-tabbar" id="au-tabbar"></div>' +

        '<div id="au-body"><div class="load-wrap"><div class="spinner"></div></div></div>';

      App.icons(page);
      loadDoc(page);
    }
  });

  function setupTabs(page) {
    var bar = page.querySelector('#au-tabbar');
    if (!bar) return;

    if (L.isEar) {
      // Ear Training rejimi
      L.tab = 'cards';
      bar.innerHTML =
        '<button class="au-tabbar-btn active" data-tab="cards"><span data-icon="book" data-icon-size="15"></span> 🎓 Карточки</button>' +
        '<button class="au-tabbar-btn" data-tab="drill"><span data-icon="headphones" data-icon-size="15"></span> 🎯 Тренажёр</button>' +
        '<button class="au-tabbar-btn" data-tab="words"><span data-icon="list" data-icon-size="15"></span> 📜 Все слова</button>';
    } else {
      // Standart dialog rejimi
      L.tab = 'listen';
      bar.innerHTML =
        '<button class="au-tabbar-btn active" data-tab="listen"><span data-icon="headphones" data-icon-size="15"></span> 🎬 Tinglash</button>' +
        '<button class="au-tabbar-btn" data-tab="dictate"><span data-icon="edit" data-icon-size="15"></span> ✍️ Diktant</button>' +
        '<button class="au-tabbar-btn" data-tab="quiz"><span data-icon="check" data-icon-size="15"></span> ❓ Test</button>';
    }

    App.icons(bar);

    bar.querySelectorAll('button').forEach(function (btn) {
      btn.onclick = function () {
        var t = btn.getAttribute('data-tab');
        if (t === L.tab) return;
        L.tab = t;
        bar.querySelectorAll('button').forEach(function (b) {
          b.classList.toggle('active', b.getAttribute('data-tab') === t);
        });
        halt();
        renderTab(page);
      };
    });

    var editBtn = page.querySelector('#au-edit');
    if (editBtn) {
      editBtn.onclick = function () { openEditor(page); };
    }
  }

  function loadDoc(page) {
    var C = core();
    if (!C) {
      var b0 = App.el('au-body');
      if (b0) b0.innerHTML = App.empty({ icon: 'alert', title: 'Modul yuklanmadi', text: 'reading.js topilmadi.' });
      return;
    }

    var builtin = window.ListeningBuiltin ? ListeningBuiltin.get(L.id) : null;

    function applyTopic(t) {
      var box = App.el('au-body'); if (!box) return;
      L.name = t.name || 'Аудирование';
      L.rawContent = t.content || '';
      var folder = (t.folder || '').trim();

      var back = page.querySelector('#au-back');
      if (back) {
        back.setAttribute('data-act', 'go');
        back.setAttribute('data-arg', App.arg({ v: 'listening_hub', p: { sec: L.sec, path: folder } }));
      }
      var h1 = page.querySelector('#au-title');
      if (h1) h1.textContent = L.name;

      if (!t.content) {
        box.innerHTML = App.empty({
          icon: 'headphones', title: 'Matn hali yo\'q',
          text: 'Tepadagi qalamcha orqali yangi mashq qo\'shishingiz mumkin.'
        });
        App.icons(box);
        return;
      }

      L.youtubeId = extractYouTubeId(t.content);

      // Kartochkalarni tekshirish
      L.cards = parseCards(t.content);
      L.isEar = L.cards.length > 0;
      L.cardIdx = 0;

      var parsed = C.parse(t.content);
      var lines = String(t.content).split('\n');
      L.sentences = parsed.sentences.filter(isSubtitleLine);

      // Timestamplar
      L.sentences.forEach(function (s, i) {
        var orig = lines.find(function (l) { return l.indexOf(s.text.slice(0, 15)) >= 0; }) || '';
        var tm = orig.match(/\[(\d{1,2}:\d{2})(?:\s*-\s*(\d{1,2}:\d{2}))?\]/);
        if (tm) {
          s.startTime = parseTimestamp(tm[1]);
          s.endTime = tm[2] ? parseTimestamp(tm[2]) : (s.startTime + 4);
        } else {
          s.startTime = i * 4;
          s.endTime = (i + 1) * 4;
        }
      });

      L.pool = buildPool(L.sentences);
      L.questions = extractQuestions(t.content, L.sentences);
      L.quizIdx = 0; L.quizScore = 0; L.quizAnswered = false;

      // Trenajyor savollari
      L.drillQuestions = prepareDrillQuestions(L.questions, L.cards);
      L.drillIdx = 0;
      L.drillScore = 0;

      setupTabs(page);
      renderTab(page);
    }

    if (builtin) {
      applyTopic(builtin);
      return;
    }

    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(L.id) }).then(function (t) {
      applyTopic(t);
    }).catch(function () {
      if (builtin) applyTopic(builtin);
      else {
        var box = App.el('au-body');
        if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: 'Mavzu topilmadi.' });
      }
    });
  }

  function renderTab(page) {
    if (L.isEar) {
      if (L.tab === 'cards') renderCardsTab(page);
      else if (L.tab === 'drill') renderDrillTab(page);
      else if (L.tab === 'words') renderWordsTab(page);
    } else {
      if (L.tab === 'listen') renderListenTab(page);
      else if (L.tab === 'dictate') renderSentence(page);
      else if (L.tab === 'quiz') renderQuizTab(page);
    }
  }

  /* =========================================================================
     A. 🎓 EAR-TRAINING 1: KARTOCHKALAR (Flashcards)
     ========================================================================= */

  function renderCardsTab(page) {
    var box = App.el('au-body'); if (!box) return;
    if (!L.cards.length) {
      box.innerHTML = App.empty({ icon: 'book', title: 'Kartochkalar yo\'q' });
      return;
    }

    var card = L.cards[L.cardIdx];
    var total = L.cards.length;

    var html =
      '<div class="au-ear-container">' +
      // Tepada navigatsiya va hisoblagich
      '<div class="au-ear-nav">' +
        '<button class="icon-btn ghost' + (L.cardIdx === 0 ? ' disabled' : '') + '" id="au-c-prev">' +
          '<span data-icon="arrowLeft" data-icon-size="18"></span></button>' +
        '<div class="au-c-counter">' +
          '<span class="au-c-counter-lbl">Kartochka</span> ' +
          '<strong>' + (L.cardIdx + 1) + '</strong> / ' + total +
        '</div>' +
        '<button class="icon-btn ghost' + (L.cardIdx === total - 1 ? ' disabled' : '') + '" id="au-c-next">' +
          '<span data-icon="arrowLeft" data-icon-size="18" style="transform:rotate(180deg)"></span></button>' +
      '</div>' +

      // Asosiy kartochka
      '<div class="au-ear-card">' +
        // Katta fonetik badge
        '<div class="au-sound-badge-wrap">' +
          '<div class="au-sound-badge">' +
            '<span class="au-sound-ic">👂</span>' +
            '<span class="au-sound-txt">' + App.esc(card.sound) + '</span>' +
          '</div>' +
          '<div class="au-sound-sub">Jonli nutqda eshitilishi (Редукция / Сжатие)</div>' +
        '</div>' +

        // Ovozli tinglash tugmalari (Tez vs Sekin)
        '<div class="au-play-row">' +
          '<button class="au-play-btn fast" id="au-play-fast" title="Jonli tezlikda eshitish">' +
            '<span class="au-play-ic">⚡</span>' +
            '<span class="au-play-txt">Jonli nutq (1.0x)</span>' +
          '</button>' +
          '<button class="au-play-btn slow" id="au-play-slow" title="Sekin va aniq talaffuz">' +
            '<span class="au-play-ic">🐢</span>' +
            '<span class="au-play-txt">Sekin (0.7x)</span>' +
          '</button>' +
        '</div>' +

        // Taqqoslash va ma'nosi
        '<div class="au-meta-box">' +
          '<div class="au-meta-row">' +
            '<span class="au-meta-lbl">✍️ Asl yozilishi:</span>' +
            '<span class="au-meta-val spelling">' + formatSpelling(card.spelling || card.word) + '</span>' +
          '</div>' +
          '<div class="au-meta-row">' +
            '<span class="au-meta-lbl">🇺🇿 Ma\'nosi:</span>' +
            '<span class="au-meta-val mean">' + App.esc(card.mean) + '</span>' +
          '</div>' +
        '</div>' +

        // Tushuntirish qoidasi
        '<div class="au-explain-box">' +
          '<div class="au-explain-title"><span data-icon="sparkles" data-icon-size="15"></span> Nega bunday eshitiladi?</div>' +
          '<div class="au-explain-text">' + App.esc(card.explain) + '</div>' +
        '</div>' +

        // Jonli gap ichida namunasi
        (card.example ?
          '<div class="au-example-box">' +
            '<div class="au-ex-top">' +
              '<span>💬 Jonli gap ichida:</span>' +
              '<button class="au-ex-speak" id="au-play-ex">' +
                '<span data-icon="volume" data-icon-size="14"></span> Eshitish' +
              '</button>' +
            '</div>' +
            '<div class="au-ex-ru">' + App.esc(card.example) + '</div>' +
            (card.example_uz ? '<div class="au-ex-uz">' + App.esc(card.example_uz) + '</div>' : '') +
          '</div>' : '') +
      '</div>' +

      // Pastki harakat tugmasi
      '<div style="margin-top:16px">' +
        (L.cardIdx < total - 1 ?
          '<button class="btn primary" id="au-card-next-btn" style="width:100%">Keyingi so\'zga o\'tish ➔</button>' :
          '<button class="btn primary" id="au-go-drill-btn" style="width:100%">🎯 Quloqni charxlash (Тренажёр) ➔</button>') +
      '</div>' +
      '</div>';

    box.innerHTML = html;
    App.icons(box);

    // Voqealarni bog'lash
    var btnFast = box.querySelector('#au-play-fast');
    if (btnFast) {
      btnFast.onclick = function () {
        halt();
        L.alive = true;
        say(card.sound.replace(/[\[\]]/g, ''), 1.05);
      };
    }

    var btnSlow = box.querySelector('#au-play-slow');
    if (btnSlow) {
      btnSlow.onclick = function () {
        halt();
        L.alive = true;
        say(card.word || card.sound, 0.7);
      };
    }

    var btnEx = box.querySelector('#au-play-ex');
    if (btnEx) {
      btnEx.onclick = function () {
        halt();
        L.alive = true;
        say(card.example_audio || card.example, 1.0);
      };
    }

    var prevBtn = box.querySelector('#au-c-prev');
    if (prevBtn && L.cardIdx > 0) {
      prevBtn.onclick = function () {
        halt();
        L.cardIdx--;
        renderCardsTab(page);
      };
    }

    var nextBtn = box.querySelector('#au-c-next');
    if (nextBtn && L.cardIdx < total - 1) {
      nextBtn.onclick = function () {
        halt();
        L.cardIdx++;
        renderCardsTab(page);
      };
    }

    var nextActionBtn = box.querySelector('#au-card-next-btn');
    if (nextActionBtn) {
      nextActionBtn.onclick = function () {
        halt();
        L.cardIdx++;
        renderCardsTab(page);
      };
    }

    var drillActionBtn = box.querySelector('#au-go-drill-btn');
    if (drillActionBtn) {
      drillActionBtn.onclick = function () {
        halt();
        // Trenajyorga o'tish
        var drillTabBtn = page.querySelector('#au-tabbar button[data-tab="drill"]');
        if (drillTabBtn) drillTabBtn.click();
      };
    }
  }

  /* =========================================================================
     B. 🎯 EAR-TRAINING 2: TRENAJYOR (Audio Drill & Quiz)
     ========================================================================= */

  function renderDrillTab(page) {
    var box = App.el('au-body'); if (!box) return;
    if (!L.drillQuestions.length) {
      box.innerHTML = App.empty({ icon: 'check', title: 'Savollar topilmadi' });
      return;
    }

    if (L.drillIdx >= L.drillQuestions.length) {
      renderDrillResult(page);
      return;
    }

    var q = L.drillQuestions[L.drillIdx];
    var total = L.drillQuestions.length;
    var pct = Math.round(((L.drillIdx) / total) * 100);

    var html =
      '<div class="au-drill-container">' +
      // Progress paneli
      '<div class="au-head">' +
        '<span class="au-progress">Savol ' + (L.drillIdx + 1) + ' / ' + total + '</span>' +
        '<span class="au-progress" style="color:var(--accent)">' + (L.drillScore) + ' to\'g\'ri</span>' +
      '</div>' +
      '<div class="au-bar"><i style="width:' + pct + '%"></i></div>' +

      // Katta ovoz bosqichi (Audio Stage)
      '<div class="au-drill-stage">' +
        '<button class="au-drill-speaker' + (L.drillPlaying ? ' playing' : '') + '" id="au-drill-play">' +
          '<span data-icon="volume" data-icon-size="34"></span>' +
          '<span class="au-drill-spk-lbl">' + (L.drillPlaying ? 'Yangramoqda...' : 'Ovozni tinglang') + '</span>' +
        '</button>' +
        '<div class="au-drill-speeds">' +
          '<button class="au-speed-chip" id="au-drill-speed-fast">⚡ 1.0x Tez</button>' +
          '<button class="au-speed-chip" id="au-speed-slow">🐢 0.7x Sekin</button>' +
        '</div>' +
      '</div>' +

      // Savol sarlavhasi
      '<div class="au-q-title" style="text-align:center;margin-top:14px">' + App.esc(q.q) + '</div>' +

      // Variantlar
      '<div class="au-q-opts">';

    q.options.forEach(function (opt, i) {
      var cls = '';
      if (q.answered) {
        if (opt.isCorrect) cls = ' correct';
        else if (q.selected === i) cls = ' wrong';
        else cls = ' disabled';
      }
      html +=
        '<button class="au-q-btn' + cls + '" data-oi="' + i + '">' +
        '<span>' + App.esc(opt.text) + '</span>' +
        (q.answered && opt.isCorrect ? '<span data-icon="check" data-icon-size="16"></span>' : '') +
        (q.answered && q.selected === i && !opt.isCorrect ? '<span data-icon="close" data-icon-size="16"></span>' : '') +
        '</button>';
    });

    html += '</div>';

    // Tushuntirish
    if (q.answered && q.explain) {
      html +=
        '<div class="au-explain-box" style="margin-top:14px;animation:fadein .2s ease">' +
          '<div class="au-explain-title">💡 Izoh:</div>' +
          '<div class="au-explain-text">' + App.esc(q.explain) + '</div>' +
        '</div>';
    }

    // Keyingi tugma
    if (q.answered) {
      html +=
        '<button class="btn primary" id="au-drill-next" style="width:100%;margin-top:16px">' +
        (L.drillIdx < total - 1 ? 'Keyingi savol ➔' : 'Natijani ko\'rish ➔') +
        '</button>';
    }

    html += '</div>';

    box.innerHTML = html;
    App.icons(box);

    // Avtomatik ovoz berish (savol ochilganda birinchi marta)
    if (!q.answered && !L.drillPlaying) {
      playDrillAudio(q.cue, 1.05);
    }

    // Ovoz tinglash tugmalari
    var spk = box.querySelector('#au-drill-play');
    if (spk) {
      spk.onclick = function () { playDrillAudio(q.cue, 1.05); };
    }
    var spFast = box.querySelector('#au-drill-speed-fast');
    if (spFast) {
      spFast.onclick = function () { playDrillAudio(q.cue, 1.05); };
    }
    var spSlow = box.querySelector('#au-speed-slow');
    if (spSlow) {
      spSlow.onclick = function () { playDrillAudio(q.cue, 0.7); };
    }

    // Variant tanlash
    if (!q.answered) {
      box.querySelectorAll('.au-q-btn').forEach(function (btn) {
        btn.onclick = function () {
          var oi = parseInt(btn.getAttribute('data-oi'), 10);
          q.answered = true;
          q.selected = oi;
          if (q.options[oi] && q.options[oi].isCorrect) {
            L.drillScore++;
            q.isCorrect = true;
          } else {
            q.isCorrect = false;
          }
          renderDrillTab(page);
        };
      });
    }

    // Keyingi savolga o'tish
    var nextBtn = box.querySelector('#au-drill-next');
    if (nextBtn) {
      nextBtn.onclick = function () {
        halt();
        L.drillIdx++;
        renderDrillTab(page);
      };
    }
  }

  function playDrillAudio(text, rate) {
    halt();
    L.alive = true;
    L.drillPlaying = true;
    var spk = document.querySelector('#au-drill-play');
    if (spk) spk.classList.add('playing');

    say(text, rate, function () {
      L.drillPlaying = false;
      if (spk) spk.classList.remove('playing');
    });
  }

  function renderDrillResult(page) {
    var box = App.el('au-body'); if (!box) return;
    var total = L.drillQuestions.length;
    var pct = total ? Math.round((L.drillScore / total) * 100) : 0;

    // Darsni tugatilgan deb belgilaymiz
    if (window.LearnMarks && LearnMarks.markTopicRead) {
      LearnMarks.markTopicRead(L.id);
    }
    if (window.ReadMark && ReadMark.markRead) {
      ReadMark.markRead(L.sec, 'topic', L.id);
    }

    box.innerHTML =
      '<div class="au-result-card">' +
      '<div class="au-res-badge">' + (pct >= 75 ? '🏆' : '🎯') + '</div>' +
      '<h2 style="margin:0 0 6px">' + (pct >= 80 ? 'Ajoyib natija!' : 'Mashq bajarildi!') + '</h2>' +
      '<p class="muted" style="margin:0 0 16px">' +
        (pct >= 80 ?
          'Qulog\'ingiz jonli rus nutqidagi qisqarish va tovushlarni a\'lo darajada ilg\'ay oldi!' :
          'Quloqni charxlashda davom eting! Kartochkalarni qayta tinglab ko\'ring.') +
      '</p>' +

      '<div class="stat-strip" style="max-width:240px;margin:0 auto 20px">' +
        '<div class="s"><div class="n" style="color:var(--success)">' + L.drillScore + '</div><div class="l">To\'g\'ri</div></div>' +
        '<div class="s"><div class="n" style="color:var(--danger)">' + (total - L.drillScore) + '</div><div class="l">Xato</div></div>' +
      '</div>' +

      '<div style="display:flex;flex-direction:column;gap:10px;margin-top:14px">' +
        '<button class="btn primary" id="au-drill-retry">🔄 Qayta topshirish</button>' +
        '<button class="btn secondary" id="au-drill-view-words">📜 Barcha so\'zlar ro\'yxati</button>' +
        '<button class="btn ghost" id="au-drill-back-hub">← Katalogga qaytish</button>' +
      '</div>' +
      '</div>';

    App.icons(box);

    var retry = box.querySelector('#au-drill-retry');
    if (retry) {
      retry.onclick = function () {
        L.drillIdx = 0;
        L.drillScore = 0;
        L.drillQuestions.forEach(function (q) {
          q.answered = false;
          q.selected = -1;
          q.isCorrect = false;
        });
        renderDrillTab(page);
      };
    }

    var viewWords = box.querySelector('#au-drill-view-words');
    if (viewWords) {
      viewWords.onclick = function () {
        var wordsTabBtn = page.querySelector('#au-tabbar button[data-tab="words"]');
        if (wordsTabBtn) wordsTabBtn.click();
      };
    }

    var backHub = box.querySelector('#au-drill-back-hub');
    if (backHub) {
      backHub.onclick = function () {
        App.go('listening_hub', { sec: L.sec });
      };
    }
  }

  /* =========================================================================
     C. 📜 EAR-TRAINING 3: BARCHA SO'ZLAR (Word list)
     ========================================================================= */

  function renderWordsTab(page) {
    var box = App.el('au-body'); if (!box) return;
    if (!L.cards.length) {
      box.innerHTML = App.empty({ icon: 'list', title: 'So\'zlar yo\'q' });
      return;
    }

    var html =
      '<div class="au-words-wrap">' +
      '<p class="muted" style="font-size:12.5px;margin:2px 2px 12px">' +
        '💡 So\'z ustiga bosing — batafsil kartochkasiga o\'tasiz. Karnaycha ustiga bossangiz — talaffuz yangraydi.' +
      '</p>' +
      '<div class="au-words-list">';

    L.cards.forEach(function (c, i) {
      html +=
        '<div class="au-word-row" data-ci="' + i + '">' +
          '<div class="au-w-num">' + (i + 1) + '</div>' +
          '<div class="au-w-main">' +
            '<div class="au-w-top">' +
              '<span class="au-w-sound">' + App.esc(c.sound) + '</span>' +
              '<span class="au-w-real">' + formatSpelling(c.spelling || c.word) + '</span>' +
            '</div>' +
            '<div class="au-w-mean">' + App.esc(c.mean) + '</div>' +
          '</div>' +
          '<button class="au-w-speak icon-btn ghost" data-ci="' + i + '" title="Tinglash">' +
            '<span data-icon="volume" data-icon-size="18"></span>' +
          '</button>' +
        '</div>';
    });

    html += '</div></div>';

    box.innerHTML = html;
    App.icons(box);

    // Voqealar: satr bosilganda kartaga o'tish
    box.querySelectorAll('.au-word-row').forEach(function (row) {
      row.onclick = function (e) {
        if (e.target.closest('.au-w-speak')) return;
        var ci = parseInt(row.getAttribute('data-ci'), 10);
        L.cardIdx = ci;
        var cardsTabBtn = page.querySelector('#au-tabbar button[data-tab="cards"]');
        if (cardsTabBtn) cardsTabBtn.click();
      };
    });

    // Karnaycha bosilganda ovoz chiqarish
    box.querySelectorAll('.au-w-speak').forEach(function (btn) {
      btn.onclick = function (e) {
        e.stopPropagation();
        var ci = parseInt(btn.getAttribute('data-ci'), 10);
        var c = L.cards[ci];
        if (c) {
          halt();
          L.alive = true;
          say(c.sound.replace(/[\[\]]/g, ''), 1.05);
        }
      };
    });
  }

  /* =========================================================================
     D. 🎬 ZAXIRA KLASSIK TINGLASH REJIMI (Subtitrlar & YouTube)
     ========================================================================= */

  function renderListenTab(page) {
    var box = App.el('au-body'); if (!box) return;

    var html = '';

    if (L.youtubeId) {
      html += '<div id="au-yt-wrap" class="au-video-wrap"></div>';
    } else {
      html +=
        '<div class="au-ctrl-bar">' +
        '<button class="au-ctrl-btn" id="au-audio-toggle">' +
          '<span data-icon="' + (L.audioPlaying ? 'pause' : 'play') + '" data-icon-size="16"></span> ' +
          (L.audioPlaying ? 'To\'xtatish' : 'Barchasini tinglash') +
        '</button>' +
        '<button class="au-ctrl-btn sec" id="au-audio-slow">0.7x sekin</button>' +
        '<button class="au-ctrl-btn sec" id="au-audio-repeat"><span data-icon="refresh" data-icon-size="14"></span> Qayta</button>' +
        '</div>';
    }

    html += '<p class="muted" style="font-size:12px;margin:4px 2px 10px">' +
      (L.youtubeId ? '💡 Gap ustiga bosing — video o\'sha sekundga sakraydi va qayta yangraydi.'
                   : '💡 Gap ustiga bosing — faqat o\'sha gap ovozli aytiladi.') +
      '</p>';

    html += '<div class="au-subs" id="au-subs">';
    L.sentences.forEach(function (s, i) {
      var timeStr = formatTime(s.startTime);
      var textHtml = (s.tokens || []).map(function (tk) {
        if (tk.k === 'x') return App.esc(tk.s);
        if (tk.t) return '<span class="rd-w" title="' + App.esc(tk.t) + '">' + App.esc(tk.w) + '</span>';
        return App.esc(tk.w);
      }).join('');

      html +=
        '<div class="au-sub-row" data-si="' + i + '">' +
        '<div class="au-sub-top">' +
          '<span class="au-sub-time">' + timeStr + '</span>' +
          '<span style="color:var(--hint)">#' + (i + 1) + '</span>' +
        '</div>' +
        '<div class="au-sub-text">' + textHtml + '</div>' +
        (s.tr ? '<div class="au-sub-tr">' + App.esc(s.tr) + '</div>' : '') +
        '</div>';
    });
    html += '</div>';

    box.innerHTML = html;
    App.icons(box);

    if (L.youtubeId) {
      initYouTubePlayer(L.youtubeId);
    } else {
      bindAudioControls(box);
    }

    bindSubClicks(box);
  }

  function bindAudioControls(box) {
    var toggleBtn = box.querySelector('#au-audio-toggle');
    if (toggleBtn) {
      toggleBtn.onclick = function () {
        if (L.audioPlaying) {
          halt();
          toggleBtn.innerHTML = '<span data-icon="play" data-icon-size="16"></span> Barchasini tinglash';
          App.icons(toggleBtn);
        } else {
          L.audioPlaying = true;
          L.audioIdx = 0;
          toggleBtn.innerHTML = '<span data-icon="pause" data-icon-size="16"></span> To\'xtatish';
          App.icons(toggleBtn);
          playSequential(box);
        }
      };
    }

    var slowBtn = box.querySelector('#au-audio-slow');
    if (slowBtn) {
      slowBtn.onclick = function () {
        var cur = L.sentences[L.activeSubIdx >= 0 ? L.activeSubIdx : 0];
        if (cur) {
          halt();
          L.alive = true;
          say(cur.text, 0.7);
        }
      };
    }

    var repBtn = box.querySelector('#au-audio-repeat');
    if (repBtn) {
      repBtn.onclick = function () {
        var cur = L.sentences[L.activeSubIdx >= 0 ? L.activeSubIdx : 0];
        if (cur) {
          halt();
          L.alive = true;
          say(cur.text, 1.0);
        }
      };
    }
  }

  function playSequential(box) {
    if (!L.audioPlaying || !L.alive) return;
    if (L.audioIdx >= L.sentences.length) {
      L.audioPlaying = false;
      var toggleBtn = box.querySelector('#au-audio-toggle');
      if (toggleBtn) {
        toggleBtn.innerHTML = '<span data-icon="play" data-icon-size="16"></span> Barchasini tinglash';
        App.icons(toggleBtn);
      }
      return;
    }

    var idx = L.audioIdx++;
    highlightSubRow(box, idx);
    var s = L.sentences[idx];
    say(s.text, L.rate || 1, function () {
      if (L.audioPlaying && L.alive) {
        setTimeout(function () { playSequential(box); }, 500);
      }
    });
  }

  function bindSubClicks(box) {
    box.querySelectorAll('.au-sub-row').forEach(function (row) {
      row.onclick = function () {
        var si = parseInt(row.getAttribute('data-si'), 10);
        var s = L.sentences[si];
        if (!s) return;

        highlightSubRow(box, si);

        if (L.youtubeId && L.ytPlayer && typeof L.ytPlayer.seekTo === 'function') {
          L.ytPlayer.seekTo(s.startTime, true);
          L.ytPlayer.playVideo();
        } else {
          halt();
          L.alive = true;
          say(s.text, L.rate || 1);
        }
      };
    });
  }

  function highlightSubRow(box, idx) {
    L.activeSubIdx = idx;
    box.querySelectorAll('.au-sub-row').forEach(function (r, i) {
      r.classList.toggle('active', i === idx);
      if (i === idx) {
        r.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  }

  /* YouTube API */
  function initYouTubePlayer(vid) {
    if (!window.YT || !window.YT.Player) {
      var tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      var first = document.getElementsByTagName('script')[0];
      first.parentNode.insertBefore(tag, first);

      var oldReady = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () {
        if (oldReady) oldReady();
        buildYT(vid);
      };
    } else {
      buildYT(vid);
    }
  }

  function buildYT(vid) {
    var wrap = document.getElementById('au-yt-wrap');
    if (!wrap) return;
    wrap.innerHTML = '<div id="au-yt-player"></div>';
    L.ytPlayer = new window.YT.Player('au-yt-player', {
      videoId: vid,
      playerVars: { playsinline: 1, rel: 0, modestbranding: 1 },
      events: {
        onStateChange: function (e) {
          if (e.data === window.YT.PlayerState.PLAYING) {
            startYouTubeTracking();
          } else {
            stopYouTubeTracking();
          }
        }
      }
    });
  }

  function startYouTubeTracking() {
    stopYouTubeTracking();
    L.ytInterval = setInterval(function () {
      if (!L.ytPlayer || typeof L.ytPlayer.getCurrentTime !== 'function') return;
      var cur = L.ytPlayer.getCurrentTime();
      for (var i = 0; i < L.sentences.length; i++) {
        var s = L.sentences[i];
        if (cur >= s.startTime && cur < s.endTime) {
          if (L.activeSubIdx !== i) {
            var box = App.el('au-body');
            if (box) highlightSubRow(box, i);
          }
          break;
        }
      }
    }, 300);
  }

  function stopYouTubeTracking() {
    if (L.ytInterval) { clearInterval(L.ytInterval); L.ytInterval = null; }
  }

  /* =========================================================================
     E. ✍️ ZAXIRA KLASSIK DIKTANT REJIMI
     ========================================================================= */

  function renderSentence(page) {
    var box = App.el('au-body'); if (!box) return;
    var s = L.sentences[L.idx];
    if (!s) { renderResult(page); return; }

    var gis = gapIndexes(s.tokens);
    var gmap = {};
    gis.forEach(function (i) { gmap[i] = true; });

    L.gaps = [];
    var sentHtml = (s.tokens || []).map(function (tk, i) {
      if (tk.k === 'x') return App.esc(tk.s);
      if (gmap[i]) {
        var gid = L.gaps.length;
        L.gaps.push({ tokenIdx: i, answer: tk.w, entered: '', ok: false, shown: false });
        return '<span class="au-gap" data-gid="' + gid + '">___</span>';
      }
      return App.esc(tk.w);
    }).join('');

    var total = L.sentences.length;
    var pct = Math.round((L.idx / total) * 100);

    var html =
      '<div class="au-head">' +
      '<span class="au-progress">Gap ' + (L.idx + 1) + ' / ' + total + '</span>' +
      '<div class="seg au-mode">' +
      '<button class="seg-btn' + (L.mode === 'choice' ? ' active' : '') + '" id="au-m-choice">Variantlar</button>' +
      '<button class="seg-btn' + (L.mode === 'type' ? ' active' : '') + '" id="au-m-type">Yozish</button>' +
      '</div>' +
      '</div>' +
      '<div class="au-bar"><i style="width:' + pct + '%"></i></div>' +

      '<div class="au-playrow">' +
      '<button class="icon-btn au-play" id="au-play" title="Tinglash"><span data-icon="volume" data-icon-size="24"></span></button>' +
      '<button class="icon-btn ghost au-slow" id="au-slow" title="Sekin tinglash">0.7x</button>' +
      '</div>' +
      '<div class="au-hint muted">Ovozni tinglang va bo\'sh o\'rinni to\'ldiring</div>' +

      '<div class="au-sent" id="au-sent">' + sentHtml + '</div>' +
      (s.tr ? '<div class="au-tr">' + App.esc(s.tr) + '</div>' : '') +

      '<div id="au-input-zone"></div>' +

      '<div class="au-nav">' +
      '<button class="btn secondary" id="au-skip">O\'tkazish</button>' +
      '<button class="btn primary" id="au-next" disabled>Keyingisi</button>' +
      '</div>';

    box.innerHTML = html;
    App.icons(box);

    bindEvents(page);
    renderInputZone(page);

    replay(1);
  }

  function bindEvents(page) {
    var pBtn = page.querySelector('#au-play');
    if (pBtn) pBtn.onclick = function () { replay(1); };
    var sBtn = page.querySelector('#au-slow');
    if (sBtn) sBtn.onclick = function () { replay(0.7); };

    var mChoice = page.querySelector('#au-m-choice');
    var mType = page.querySelector('#au-m-type');
    if (mChoice) mChoice.onclick = function () { setMode('choice', page); };
    if (mType) mType.onclick = function () { setMode('type', page); };

    var skip = page.querySelector('#au-skip');
    if (skip) {
      skip.onclick = function () {
        L.bad++;
        L.wrongSents.push(L.idx);
        L.gaps.forEach(function (g) {
          g.ok = false; g.shown = true;
          updateGapEl(g);
        });
        enableNext(page, true);
      };
    }

    var next = page.querySelector('#au-next');
    if (next) {
      next.onclick = function () {
        halt();
        L.idx++;
        renderSentence(page);
      };
    }
  }

  function setMode(m, page) {
    L.mode = m;
    try { localStorage.setItem('listening_mode', m); } catch (e) {}
    renderSentence(page);
  }

  function renderInputZone(page) {
    var zone = page.querySelector('#au-input-zone');
    if (!zone) return;
    var cur = currentGap();
    if (!cur) return;

    if (L.mode === 'choice') {
      var opts = makeOptions(cur.answer);
      zone.innerHTML = '<div class="au-opts">' +
        opts.map(function (w) {
          return '<button class="btn secondary au-opt" data-word="' + App.esc(w) + '">' + App.esc(w) + '</button>';
        }).join('') +
        '</div>';
      zone.querySelectorAll('.au-opt').forEach(function (btn) {
        btn.onclick = function () {
          pickOption(btn.getAttribute('data-word'), btn, page);
        };
      });
    } else {
      zone.innerHTML =
        '<form class="au-type" id="au-type-form">' +
        '<input type="text" class="input" id="au-input" placeholder="Eshitgan so\'zingiz..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">' +
        '<button type="submit" class="btn primary">Tekshirish</button>' +
        '</form>';
      var form = zone.querySelector('#au-type-form');
      var inp = zone.querySelector('#au-input');
      setTimeout(function () { if (inp) inp.focus(); }, 100);
      form.onsubmit = function (e) {
        e.preventDefault();
        var val = (inp.value || '').trim();
        if (!val) return;
        submitTyped(val, inp, page);
      };
    }
  }

  function currentGap() {
    for (var i = 0; i < L.gaps.length; i++) {
      if (!L.gaps[i].ok && !L.gaps[i].shown) return L.gaps[i];
    }
    return null;
  }

  function normalize(w) {
    return String(w || '').toLowerCase().replace(/ё/g, 'е').replace(/[^a-zа-я0-9]/g, '');
  }

  function pickOption(word, btn, page) {
    var g = currentGap();
    if (!g) return;
    if (normalize(word) === normalize(g.answer)) {
      g.ok = true;
      g.entered = g.answer;
      updateGapEl(g);
      checkDone(page);
    } else {
      btn.classList.add('bad');
      shakeGap(g);
      L.bad++;
      if (L.wrongSents.indexOf(L.idx) < 0) L.wrongSents.push(L.idx);
    }
  }

  function submitTyped(val, inp, page) {
    var g = currentGap();
    if (!g) return;
    if (normalize(val) === normalize(g.answer)) {
      g.ok = true;
      g.entered = g.answer;
      updateGapEl(g);
      checkDone(page);
    } else {
      inp.classList.add('bad');
      setTimeout(function () { inp.classList.remove('bad'); }, 400);
      shakeGap(g);
      L.bad++;
      if (L.wrongSents.indexOf(L.idx) < 0) L.wrongSents.push(L.idx);
    }
  }

  function updateGapEl(g) {
    var gid = L.gaps.indexOf(g);
    var el = document.querySelector('.au-gap[data-gid="' + gid + '"]');
    if (!el) return;
    el.textContent = g.answer;
    el.className = 'au-gap' + (g.ok ? ' ok' : (g.shown ? ' shown' : ''));
  }

  function shakeGap(g) {
    var gid = L.gaps.indexOf(g);
    var el = document.querySelector('.au-gap[data-gid="' + gid + '"]');
    if (!el) return;
    el.classList.add('shake');
    setTimeout(function () { el.classList.remove('shake'); }, 400);
  }

  function checkDone(page) {
    var cur = currentGap();
    if (cur) {
      renderInputZone(page);
    } else {
      L.good++;
      enableNext(page, true);
    }
  }

  function enableNext(page, auto) {
    var n = page.querySelector('#au-next');
    if (n) {
      n.disabled = false;
      n.classList.add('ready');
    }
    var zone = page.querySelector('#au-input-zone');
    if (zone) zone.innerHTML = '';
  }

  function makeOptions(target) {
    var list = [target];
    var normT = normalize(target);
    var shuffled = L.pool.slice().sort(function () { return Math.random() - 0.5; });
    for (var i = 0; i < shuffled.length && list.length < 4; i++) {
      var w = shuffled[i];
      if (normalize(w) !== normT && list.indexOf(w) < 0) list.push(w);
    }
    while (list.length < 4) list.push('so\'z ' + (list.length + 1));
    return list.sort(function () { return Math.random() - 0.5; });
  }

  function renderResult(page) {
    var box = App.el('au-body'); if (!box) return;
    var total = L.sentences.length;
    var ok = total - L.wrongSents.length;
    var pct = total ? Math.round((ok / total) * 100) : 100;

    box.innerHTML =
      '<div style="text-align:center;padding-top:12px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 16px">Diktant yakunlandi!</h2>' +
      '<div class="stat-strip" style="max-width:240px;margin:0 auto 24px">' +
      '<div class="s"><div class="n" style="color:var(--success)">' + ok + '</div><div class="l">To\'g\'ri</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)">' + L.wrongSents.length + '</div><div class="l">Xato</div></div>' +
      '</div>' +
      '<button class="btn" id="au-retry">Qayta ishlash</button>' +
      '</div>';
    App.icons(box);

    var retry = box.querySelector('#au-retry');
    if (retry) {
      retry.onclick = function () {
        L.idx = 0; L.good = 0; L.bad = 0; L.wrongSents = [];
        renderSentence(page);
      };
    }
  }

  /* =========================================================================
     F. ❓ ZAXIRA TEST REJIMI (Quiz)
     ========================================================================= */

  function renderQuizTab(page) {
    var box = App.el('au-body'); if (!box) return;
    if (!L.questions.length) {
      box.innerHTML = App.empty({ icon: 'check', title: 'Savollar yo\'q' });
      return;
    }

    if (L.quizIdx >= L.questions.length) {
      renderQuizResult(page);
      return;
    }

    var q = L.questions[L.quizIdx];
    var total = L.questions.length;
    var pct = Math.round((L.quizIdx / total) * 100);

    var html =
      '<div class="au-quiz-box">' +
      '<div class="au-q-head">' +
        '<span class="au-progress">Savol ' + (L.quizIdx + 1) + ' / ' + total + '</span>' +
        '<span class="au-progress" style="color:var(--accent)">' + L.quizScore + ' to\'g\'ri</span>' +
      '</div>' +
      '<div class="au-bar"><i style="width:' + pct + '%"></i></div>' +
      '<div class="au-q-title">' + App.esc(q.q) + '</div>' +
      '<div class="au-q-opts">';

    q.options.forEach(function (opt, i) {
      var cls = '';
      if (L.quizAnswered) {
        if (i === q.correct) cls = ' correct';
        else if (L.quizAnswered && i !== q.correct) cls = ' disabled';
      }
      html +=
        '<button class="au-q-btn' + cls + '" data-oi="' + i + '">' +
        '<span>' + App.esc(opt) + '</span>' +
        (L.quizAnswered && i === q.correct ? '<span data-icon="check" data-icon-size="16"></span>' : '') +
        '</button>';
    });

    html += '</div>';

    if (L.quizAnswered) {
      html += '<button class="btn primary" id="au-q-next" style="width:100%;margin-top:20px">' +
        (L.quizIdx < total - 1 ? 'Keyingi savol ➔' : 'Natijani ko\'rish ➔') +
        '</button>';
    }

    html += '</div>';

    box.innerHTML = html;
    App.icons(box);

    if (!L.quizAnswered) {
      box.querySelectorAll('.au-q-btn').forEach(function (btn) {
        btn.onclick = function () {
          var oi = parseInt(btn.getAttribute('data-oi'), 10);
          L.quizAnswered = true;
          if (oi === q.correct) {
            L.quizScore++;
            btn.classList.add('correct');
          } else {
            btn.classList.add('wrong');
          }
          renderQuizTab(page);
        };
      });
    }

    var nextBtn = box.querySelector('#au-q-next');
    if (nextBtn) {
      nextBtn.onclick = function () {
        L.quizIdx++;
        L.quizAnswered = false;
        renderQuizTab(page);
      };
    }
  }

  function renderQuizResult(page) {
    var box = App.el('au-body'); if (!box) return;
    var total = L.questions.length;
    var pct = total ? Math.round((L.quizScore / total) * 100) : 0;

    box.innerHTML =
      '<div style="text-align:center;padding-top:12px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 16px">Test yakunlandi!</h2>' +
      '<p class="muted" style="margin-bottom:20px">' +
        (pct >= 80 ? 'Ajoyib natija! Eshitib tushunish darajangiz yuqori! 🎯' : 'Yaxshi! Qayta tinglab, natijani yanada oshiring.') +
      '</p>' +
      '<div class="stat-strip" style="max-width:240px;margin:0 auto 24px">' +
      '<div class="s"><div class="n" style="color:var(--success)">' + L.quizScore + '</div><div class="l">To\'g\'ri</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)">' + (total - L.quizScore) + '</div><div class="l">Xato</div></div>' +
      '</div>' +
      '<button class="btn" id="au-q-retry">Qayta ishlash</button>' +
      '</div>';
    App.icons(box);

    var retry = box.querySelector('#au-q-retry');
    if (retry) {
      retry.onclick = function () {
        L.quizIdx = 0;
        L.quizScore = 0;
        L.quizAnswered = false;
        renderQuizTab(page);
      };
    }
  }

  /* ================= 4. Tahrirlash (Editor) ================= */

  function openEditor(page) {
    if (window.Auth && Auth.isReadOnly && Auth.isReadOnly()) return;
    var html =
      '<div class="rd-editor">' +
      '<p class="muted" style="font-size:12px;margin:0 0 8px">' +
        'Kartochka formati:<br>' +
        '<code>card: Здравствуйте</code><br>' +
        '<code>sound: [Здрасьте]</code><br>' +
        '<code>spelling: Здра[вствуй]те</code><br>' +
        '<code>mean: Salom</code><br>' +
        '<code>explain: Nega shunday...</code>' +
      '</p>' +
      '<textarea id="au-ta" class="input" style="height:320px;font-family:var(--mono);font-size:12.5px;line-height:1.5">' +
      App.esc(L.rawContent || '') + '</textarea>' +
      '<button class="btn" id="au-ta-save" style="margin-top:10px">Saqlash</button></div>';

    var sh = App.sheet(html, { title: 'Tahrirlash: ' + L.name, cls: 'editor-sheet' });
    sh.querySelector('#au-ta-save').onclick = function () {
      var val = sh.querySelector('#au-ta').value;
      if (typeof L.id === 'number') {
        App.call('upload_topic_content', { id: L.id, part: 'content', content: val })
          .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); loadDoc(page); })
          .catch(function (err) { App.toast('⚠️ ' + err.message); });
      } else {
        var b = window.ListeningBuiltin ? ListeningBuiltin.get(L.id) : null;
        if (b) b.content = val;
        L.rawContent = val;
        App.closeSheet();
        App.toast('✅ Saqlandi');
        loadDoc(page);
      }
    };
  }

})();
