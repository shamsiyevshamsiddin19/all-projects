/* =========================================================================
   Аудирование / Listening Darsligi (Video / Audio, Subtitrlar va Savollar)
   - 3 ta rejim:
     1. 🎬 Tinglash: YouTube video / Audio pleyer + Sinxron Subtitrlar
     2. ✍️ Diktant: Eshitib bo'shliqlarni to'ldirish (Yengil / Qiyin)
     3. ❓ Test (Quiz): Eshitib tushunish savol-javoblari
   - YouTube video ID va vaqt kodlari (`[00:01 - 00:05]`) qo'llab-quvvatlanadi
   - So'z ustiga bosganda tarjima
   ========================================================================= */
(function () {
  'use strict';

  var L = {
    sec: '', id: null, name: '', lang: 'ru-RU', dict: 'russian',
    rawContent: '',
    sentences: [], idx: 0,
    tab: 'listen', // 'listen' | 'dictate' | 'quiz'
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
    quizAnswered: false
  };

  function core() { return window.RDCore || null; }

  /* ================= Ovoz (TTS) ================= */

  function halt() {
    L.audioPlaying = false;
    if (L.partTimer) { clearTimeout(L.partTimer); L.partTimer = null; }
    if (window.TTS) TTS.cancel(); else { try { window.speechSynthesis.cancel(); } catch (e) {} }
  }

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

  /* ================= YouTube Pleyeri ================= */

  function stopYouTubeTracking() {
    if (L.ytInterval) { clearInterval(L.ytInterval); L.ytInterval = null; }
  }

  function startYouTubeTracking() {
    stopYouTubeTracking();
    L.ytInterval = setInterval(function () {
      if (!L.ytPlayer || typeof L.ytPlayer.getCurrentTime !== 'function') return;
      var cur = L.ytPlayer.getCurrentTime();
      var found = -1;
      for (var i = 0; i < L.sentences.length; i++) {
        var s = L.sentences[i];
        var st = s.startTime != null ? s.startTime : (i * 4);
        var et = s.endTime != null ? s.endTime : ((i + 1) * 4);
        if (cur >= st && cur < et) { found = i; break; }
      }
      if (found >= 0 && found !== L.activeSubIdx) {
        L.activeSubIdx = found;
        highlightSubRow(found);
      }
    }, 250);
  }

  function highlightSubRow(idx) {
    var box = App.el('au-body'); if (!box) return;
    box.querySelectorAll('.au-sub-row').forEach(function (el, i) {
      if (i === idx) {
        el.classList.add('active');
        el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        el.classList.remove('active');
      }
    });
  }

  function initYouTubePlayer(box, videoId) {
    stopYouTubeTracking();
    if (L.ytPlayer) {
      try { L.ytPlayer.destroy(); } catch (e) {}
      L.ytPlayer = null;
    }

    var holder = box.querySelector('#au-yt-wrap');
    if (!holder) return;

    holder.innerHTML = '<div id="au-yt-player"></div>';

    function setup() {
      try {
        L.ytPlayer = new window.YT.Player('au-yt-player', {
          videoId: videoId,
          playerVars: {
            playsinline: 1, rel: 0, modestbranding: 1, enablejsapi: 1
          },
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
      } catch (e) {
        holder.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(videoId) + '?playsinline=1&rel=0" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>';
      }
    }

    if (window.YT && window.YT.Player) {
      setup();
    } else {
      var old = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () {
        if (old) old();
        setup();
      };
      if (!document.querySelector('script[src*="youtube.com/iframe_api"]')) {
        var s = document.createElement('script');
        s.src = 'https://www.youtube.com/iframe_api';
        document.head.appendChild(s);
      }
    }
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
      L.tab = 'listen';
      L.activeSubIdx = -1;
      L.alive = true;
      try { L.rate = parseFloat(localStorage.getItem('reading_rate')) || 1; } catch (e) { L.rate = 1; }
      try { L.mode = localStorage.getItem('listening_mode') === 'type' ? 'type' : 'choice'; } catch (e) { L.mode = 'choice'; }

      var isReadOnly = window.Auth && Auth.isReadOnly && Auth.isReadOnly();

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="au-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 id="au-title"></h1>' +
        (isReadOnly ? '' :
          '<button class="icon-btn ghost" id="au-edit" style="margin-left:auto" aria-label="Tahrirlash" title="Matn va video havolasini tahrirlash">' +
          '<span data-icon="edit" data-icon-size="18"></span></button>') +
        '</div>' +

        /* 3 ta rejim: Tinglash, Diktant, Test */
        '<div class="au-tabbar" id="au-tabbar">' +
        '<button class="au-tabbar-btn active" data-tab="listen"><span data-icon="headphones" data-icon-size="15"></span> 🎬 Tinglash</button>' +
        '<button class="au-tabbar-btn" data-tab="dictate"><span data-icon="edit" data-icon-size="15"></span> ✍️ Diktant</button>' +
        '<button class="au-tabbar-btn" data-tab="quiz"><span data-icon="check" data-icon-size="15"></span> ❓ Test</button>' +
        '</div>' +

        '<div id="au-body"><div class="load-wrap"><div class="spinner"></div></div></div>';

      App.icons(page);
      bindTopbarTabs(page);
      loadDoc(page);
    }
  });

  function bindTopbarTabs(page) {
    page.querySelectorAll('#au-tabbar button').forEach(function (btn) {
      btn.onclick = function () {
        var t = btn.getAttribute('data-tab');
        if (t === L.tab) return;
        L.tab = t;
        page.querySelectorAll('#au-tabbar button').forEach(function (b) {
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
      L.name = t.name || 'Matn';
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
          text: 'Tepadagi qalamcha tugmasi orqali YouTube havolasi yoki dialog matnini kiriting.'
        });
        App.icons(box);
        return;
      }

      L.youtubeId = extractYouTubeId(t.content);

      var parsed = C.parse(t.content);
      var lines = String(t.content).split('\n');

      L.sentences = parsed.sentences.filter(function (s) {
        return s.k !== 'h' && (s.text || '').trim();
      });

      // Timestamplarni bog'lash
      L.sentences.forEach(function (s, i) {
        // Matndan qatorni topish
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
    if (L.tab === 'listen') {
      renderListenTab(page);
    } else if (L.tab === 'dictate') {
      renderSentence(page);
    } else if (L.tab === 'quiz') {
      renderQuizTab(page);
    }
  }

  /* ================= 1. 🎬 Tinglash va Subtitrlar ================= */

  function renderListenTab(page) {
    var box = App.el('au-body'); if (!box) return;

    var html = '';

    // YouTube video pleyeri (agar video mavjud bo'lsa)
    if (L.youtubeId) {
      html += '<div id="au-yt-wrap" class="au-video-wrap"></div>';
    } else {
      // Audio boshqaruv paneli
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

    // Subtitr qatorlari
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
      initYouTubePlayer(box, L.youtubeId);
    } else {
      bindAudioControls(box);
    }

    // Subtitr bosilganda sakrash
    box.querySelectorAll('.au-sub-row').forEach(function (row) {
      row.onclick = function (e) {
        // Agar so'z tarjimasi bosilgan bo'lsa — toast
        var rw = e.target.closest('.rd-w');
        if (rw && rw.getAttribute('title')) {
          App.toast(rw.textContent + ' — ' + rw.getAttribute('title'));
          return;
        }
        var si = parseInt(row.getAttribute('data-si'), 10);
        seekToSentence(si);
      };
    });
  }

  function seekToSentence(i) {
    var s = L.sentences[i];
    if (!s) return;
    L.activeSubIdx = i;
    highlightSubRow(i);

    if (L.youtubeId && L.ytPlayer && typeof L.ytPlayer.seekTo === 'function') {
      var seekSec = s.startTime != null ? s.startTime : (i * 4);
      L.ytPlayer.seekTo(seekSec, true);
      L.ytPlayer.playVideo();
    } else {
      halt();
      L.alive = true;
      say(s.text);
    }
  }

  function bindAudioControls(box) {
    var toggle = box.querySelector('#au-audio-toggle');
    if (toggle) {
      toggle.onclick = function () {
        if (L.audioPlaying) {
          halt();
          renderListenTab(App.page);
        } else {
          playAllSentences(0);
        }
      };
    }

    var slow = box.querySelector('#au-audio-slow');
    if (slow) {
      slow.onclick = function () {
        var cur = L.activeSubIdx >= 0 ? L.activeSubIdx : 0;
        var s = L.sentences[cur];
        if (!s) return;
        halt();
        L.alive = true;
        say(s.text, 0.7);
      };
    }

    var rep = box.querySelector('#au-audio-repeat');
    if (rep) {
      rep.onclick = function () {
        var cur = L.activeSubIdx >= 0 ? L.activeSubIdx : 0;
        seekToSentence(cur);
      };
    }
  }

  function playAllSentences(startIdx) {
    halt();
    L.audioPlaying = true;
    L.alive = true;
    var i = startIdx || 0;

    function playNext() {
      if (!L.audioPlaying || !L.alive || i >= L.sentences.length) {
        halt();
        highlightSubRow(-1);
        renderListenTab(App.page);
        return;
      }
      L.activeSubIdx = i;
      highlightSubRow(i);
      var s = L.sentences[i];
      say(s.text, L.rate, function () {
        i++;
        L.partTimer = setTimeout(playNext, 600);
      });
    }

    playNext();
    var toggle = document.querySelector('#au-audio-toggle');
    if (toggle) {
      toggle.innerHTML = '<span data-icon="pause" data-icon-size="16"></span> To\'xtatish';
      App.icons(toggle);
    }
  }

  /* ================= 2. ✍️ Diktant (Gap-fill) ================= */

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

    if (g.tries === 1) {
      App.toast('Yana bir bor tinglang — birinchi harfi «' + g.word.charAt(0) + '»');
      replay();
      return;
    }

    g.done = true;
    if (el) { el.classList.add('shown'); el.innerHTML = '<span class="au-gap-txt">' + App.esc(g.word) + '</span>'; }
    var ab2 = App.el('au-answer'); if (ab2) ab2.innerHTML = '';
    if (g.tr) {
      App.call('add_mistake', { lang: L.dict, category: L.name, ru: g.word, uz: g.tr }).catch(function () {});
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
      '<h2 style="margin:0 0 22px">Diktant tugadi</h2>' +
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

  /* ================= 3. ❓ Test (Quiz) ================= */

  function renderQuizTab(page) {
    var box = App.el('au-body'); if (!box) return;

    if (!L.questions || !L.questions.length) {
      box.innerHTML = App.empty({
        icon: 'check', title: 'Savollar topilmadi',
        text: 'Bu mavzuda savollar kiritilmagan. Tepadagi qalamcha orqali savollar qo\'shishingiz mumkin.'
      });
      App.icons(box);
      return;
    }

    if (L.quizIdx >= L.questions.length) {
      renderQuizResult(page);
      return;
    }

    var q = L.questions[L.quizIdx];
    var pct = Math.round((L.quizIdx / L.questions.length) * 100);

    var html =
      '<div class="au-head">' +
      '<div class="au-progress">Savol: ' + (L.quizIdx + 1) + ' / ' + L.questions.length + '</div>' +
      '<div style="font-size:12px;font-weight:700;color:var(--accent)">To\'g\'ri: ' + L.quizScore + '</div>' +
      '</div>' +
      '<div class="au-bar"><i style="width:' + pct + '%"></i></div>' +

      '<div class="au-quiz-box">' +
      '<div class="au-q-title">' + App.esc(q.q) + '</div>' +
      '<div class="au-q-opts">';

    q.options.forEach(function (opt, idx) {
      html += '<button class="au-q-btn" data-oi="' + idx + '">' +
        '<span>' + App.esc(opt) + '</span>' +
        '<span data-icon="check" data-icon-size="16" class="au-q-check" style="display:none"></span>' +
        '</button>';
    });

    html += '</div></div>' +
      '<div class="au-nav" id="au-q-nav" style="display:none">' +
      '<button class="btn" id="au-q-next">' +
        (L.quizIdx + 1 >= L.questions.length ? 'Natijani ko\'rish' : 'Keyingi savol ➔') +
      '</button>' +
      '</div>';

    box.innerHTML = html;
    App.icons(box);

    L.quizAnswered = false;

    box.querySelectorAll('.au-q-btn').forEach(function (btn) {
      btn.onclick = function () {
        if (L.quizAnswered) return;
        L.quizAnswered = true;
        var chosen = parseInt(btn.getAttribute('data-oi'), 10);
        var isOk = chosen === q.correct;

        if (isOk) {
          L.quizScore++;
          btn.classList.add('correct');
        } else {
          btn.classList.add('wrong');
          // To'g'ri variantni ko'rsatish
          var correctBtn = box.querySelector('.au-q-btn[data-oi="' + q.correct + '"]');
          if (correctBtn) correctBtn.classList.add('correct');
        }

        box.querySelectorAll('.au-q-btn').forEach(function (b) { b.classList.add('disabled'); });

        var nav = box.querySelector('#au-q-nav');
        if (nav) nav.style.display = 'flex';
      };
    });

    var nextBtn = box.querySelector('#au-q-next');
    if (nextBtn) {
      nextBtn.onclick = function () {
        L.quizIdx++;
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
        'YouTube video ulash: <code>youtube: https://youtu.be/ID</code><br>' +
        'Vaqtlar: <code>[00:01 - 00:05] Gap matni | Tarjima</code><br>' +
        'Savollar: <code>? Savol matni</code>, <code>+ To\'g\'ri javob</code>, <code>- Xato</code>' +
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
        // Builtin darslik uchun vaqtinchalik yangilash
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
