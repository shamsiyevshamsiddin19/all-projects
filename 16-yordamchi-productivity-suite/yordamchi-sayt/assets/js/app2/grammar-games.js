/* Grammar o'yinlari — 4 tur: to'ldirish, saralash, juftlash, gap tuzish.
   Matn formatlari eski saytdan aynan ko'chirilgan (foydalanuvchi bazalari mos kelsin). */
(function () {
  'use strict';

  var GUIDE = {
    fill: {
      label: 'Bo\'shliqni to\'ldirish',
      intro: 'Har bir qator — bitta savol. Maydonlar nuqtali vergul (;) bilan ajratiladi:',
      fields: 'gap (bo\'sh joy = ___) ; to\'g\'ri javob ; noto\'g\'ri javoblar (vergul bilan) ; tarjima (ixtiyoriy)',
      example: 'Я ___ книгу. ; читаю ; читаешь, читают ; Men kitob o\'qiyman\nОна ___ в школе. ; работает ; работаю, работаешь ; U maktabda ishlaydi'
    },
    sort: {
      label: 'Saralash',
      intro: 'Guruh nomini # bilan boshlang, keyingi qatorda shu guruh so\'zlarini vergul bilan yozing:',
      fields: '# Guruh nomi  ⟶  keyingi qator: so\'z1, so\'z2, so\'z3',
      example: '# Мужской (он)\nстол, музей, словарь\n# Женский (она)\nкнига, семья\n# Средний (оно)\nокно, море'
    },
    match: {
      label: 'Juftlash',
      intro: 'Har bir qator — bitta juft. Chap va o\'ng tomon = belgisi bilan ajratiladi:',
      fields: 'chap tomon = o\'ng tomon',
      example: 'стол = столы\nкнига = книги\nокно = окна'
    },
    order: {
      label: 'Gap tuzish',
      intro: 'Har bir qator — bitta to\'g\'ri gap. So\'zlar bo\'sh joy bilan ajratiladi. Tarjimani | dan keyin yozing (ixtiyoriy):',
      fields: 'To\'g\'ri gap | tarjima (ixtiyoriy)',
      example: 'Это город, который я люблю | Bu men sevadigan shahar\nКнига, которую я читаю | Men o\'qiyotgan kitob'
    }
  };

  /* ---------- Parserlar ---------- */
  function parseFill(text) {
    var rounds = [];
    String(text || '').split('\n').forEach(function (line) {
      var l = line.trim(); if (!l) return;
      var parts = l.split(';').map(function (s) { return s.trim(); });
      if (parts.length < 3) return;
      var sentence = parts[0], answer = parts[1];
      var wrongs = parts[2].split(',').map(function (s) { return s.trim(); }).filter(Boolean);
      if (sentence.indexOf('___') < 0 || !answer || !wrongs.length) return;
      rounds.push({ text: sentence, answer: answer, options: [answer].concat(wrongs), uz: parts[3] || '' });
    });
    return rounds.length ? { rounds: rounds } : null;
  }

  function parseSort(text) {
    var buckets = [], items = [], curKey = null;
    String(text || '').split('\n').forEach(function (line) {
      var l = line.trim(); if (!l) return;
      var m = l.match(/^#\s*(.+)$/);
      if (m) { curKey = 'b' + buckets.length; buckets.push({ key: curKey, label: m[1].trim() }); return; }
      if (curKey == null) return;
      l.split(',').forEach(function (part) {
        var t = part.trim(); if (t) items.push({ text: t, key: curKey });
      });
    });
    return (buckets.length >= 2 && items.length >= 2) ? { buckets: buckets, items: items } : null;
  }

  function parseMatch(text) {
    var pairs = [];
    String(text || '').split('\n').forEach(function (line) {
      var l = line.trim(); if (!l) return;
      var m = l.match(/^(.+?)\s*[=|]\s*(.+)$/);
      if (m && m[1].trim() && m[2].trim()) pairs.push({ a: m[1].trim(), b: m[2].trim() });
    });
    return pairs.length >= 2 ? { pairs: pairs } : null;
  }

  function parseOrder(text) {
    var rounds = [];
    String(text || '').split('\n').forEach(function (line) {
      var l = line.trim(); if (!l) return;
      var sentence = l, uz = '';
      var pipe = l.indexOf('|');
      if (pipe >= 0) { sentence = l.slice(0, pipe).trim(); uz = l.slice(pipe + 1).trim(); }
      var tokens = sentence.split(/\s+/).filter(Boolean);
      if (tokens.length >= 2) rounds.push({ tokens: tokens, uz: uz });
    });
    return rounds.length ? { rounds: rounds } : null;
  }

  function parseGame(type, raw) {
    if (!String(raw || '').trim()) return null;
    var data = type === 'sort' ? parseSort(raw)
      : type === 'match' ? parseMatch(raw)
      : type === 'order' ? parseOrder(raw)
      : parseFill(raw);
    if (!data) return null;
    data.type = type;
    return data;
  }

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* ---------- O'yin holati ---------- */
  var G = null;

  function hud() {
    return '<div class="stat-strip" style="margin:0 0 14px">' +
      '<div class="s"><div class="n" id="gg-step">' + (G.step + 1) + '/' + G.total + '</div><div class="l">Bosqich</div></div>' +
      '<div class="s"><div class="n" style="color:var(--success)" id="gg-good">' + G.good + '</div><div class="l">To\'g\'ri</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)" id="gg-bad">' + G.bad + '</div><div class="l">Xato</div></div>' +
      '</div>';
  }
  function syncHud() {
    var a = App.el('gg-step'), b = App.el('gg-good'), c = App.el('gg-bad');
    if (a) a.textContent = Math.min(G.step + 1, G.total) + '/' + G.total;
    if (b) b.textContent = G.good;
    if (c) c.textContent = G.bad;
  }
  function score(ok) { if (ok) G.good++; else G.bad++; syncHud(); }

  function stage(html) {
    var el = App.el('gg-stage');
    if (el) { el.innerHTML = html; App.icons(el); }
  }

  function finish() {
    var total = G.good + G.bad;
    var pct = total ? Math.round(G.good * 100 / total) : 0;
    var msg = pct >= 90 ? 'Ajoyib!' : pct >= 70 ? 'Yaxshi!' : pct >= 50 ? 'Yomon emas' : 'Yana mashq qiling';
    stage('<div style="text-align:center;padding-top:6px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 18px">' + msg + '</h2>' +
      '<button class="btn" id="gg-again">Yana o\'ynash</button></div>');
    var again = App.el('gg-again');
    if (again) again.onclick = function () { start(G.page, G.def, G.onExit); };
    if (window.Activity) Activity.mark();
  }

  function next() {
    G.step++;
    if (G.step >= G.total) { finish(); return; }
    renderStep();
  }

  /* ---------- Bosqich turlari ---------- */
  function renderStep() {
    syncHud(); // yangi bosqichda hisoblagich ham yangilansin
    if (G.type === 'fill') return renderFill();
    if (G.type === 'sort') return renderSort();
    if (G.type === 'order') return renderOrder();
    return renderMatch();
  }

  function renderFill() {
    var r = G.data.rounds[G.step];
    var opts = shuffle(r.options);
    stage('<div class="gg-q">' + App.esc(r.text).replace('___', '<u class="gg-blank">___</u>') + '</div>' +
      (r.uz ? '<p class="muted" style="font-size:12.5px;margin:-6px 0 14px">' + App.esc(r.uz) + '</p>' : '') +
      '<div id="gg-opts">' + opts.map(function (o, i) {
        return '<button class="qopt" data-i="' + i + '">' + App.esc(o) + '</button>';
      }).join('') + '</div>');
    var box = App.el('gg-opts');
    box.querySelectorAll('.qopt').forEach(function (b, i) {
      b.onclick = function () {
        if (box._done) return; box._done = true;
        var ok = opts[i] === r.answer;
        b.classList.add(ok ? 'correct' : 'wrong');
        if (!ok) {
          box.querySelectorAll('.qopt').forEach(function (x, xi) {
            if (opts[xi] === r.answer) x.classList.add('correct');
          });
        }
        box.querySelectorAll('.qopt').forEach(function (x) { x.classList.add('disabled'); });
        score(ok);
        setTimeout(next, ok ? 700 : 1400);
      };
    });
  }

  function renderSort() {
    var it = G.items[G.step];
    stage('<div class="gg-q" style="text-align:center">' + App.esc(it.text) + '</div>' +
      '<p class="muted" style="font-size:12.5px;text-align:center;margin:-6px 0 14px">Qaysi guruhga tegishli?</p>' +
      '<div id="gg-opts">' + G.data.buckets.map(function (b) {
        return '<button class="qopt" data-k="' + b.key + '">' + App.esc(b.label) + '</button>';
      }).join('') + '</div>');
    var box = App.el('gg-opts');
    box.querySelectorAll('.qopt').forEach(function (b) {
      b.onclick = function () {
        if (box._done) return; box._done = true;
        var ok = b.getAttribute('data-k') === it.key;
        b.classList.add(ok ? 'correct' : 'wrong');
        if (!ok) {
          box.querySelectorAll('.qopt').forEach(function (x) {
            if (x.getAttribute('data-k') === it.key) x.classList.add('correct');
          });
        }
        box.querySelectorAll('.qopt').forEach(function (x) { x.classList.add('disabled'); });
        score(ok);
        setTimeout(next, ok ? 650 : 1300);
      };
    });
  }

  function renderOrder() {
    var r = G.data.rounds[G.step];
    var pool = shuffle(r.tokens);
    var picked = [];
    stage((r.uz ? '<p class="muted" style="font-size:12.5px;margin:0 0 10px">' + App.esc(r.uz) + '</p>' : '') +
      '<div class="gg-built" id="gg-built"></div>' +
      '<div class="gg-pool" id="gg-pool"></div>' +
      '<div class="btn-row"><button class="btn sec" id="gg-undo">Orqaga</button>' +
      '<button class="btn" id="gg-check">Tekshirish</button></div>');

    function draw() {
      var built = App.el('gg-built'), poolEl = App.el('gg-pool');
      built.innerHTML = picked.length
        ? picked.map(function (t, i) { return '<button class="gg-tok picked" data-i="' + i + '">' + App.esc(t) + '</button>'; }).join('')
        : '<span class="muted" style="font-size:12.5px">So\'zlarni tartib bilan bosing...</span>';
      poolEl.innerHTML = pool.map(function (t, i) {
        return t === null ? '' : '<button class="gg-tok" data-i="' + i + '">' + App.esc(t) + '</button>';
      }).join('');
      poolEl.querySelectorAll('.gg-tok').forEach(function (b) {
        b.onclick = function () {
          var i = +b.getAttribute('data-i');
          picked.push(pool[i]); pool[i] = null; draw();
        };
      });
      built.querySelectorAll('.gg-tok').forEach(function (b) {
        b.onclick = function () {
          var i = +b.getAttribute('data-i');
          var t = picked.splice(i, 1)[0];
          for (var k = 0; k < pool.length; k++) { if (pool[k] === null) { pool[k] = t; break; } }
          draw();
        };
      });
    }
    draw();

    App.el('gg-undo').onclick = function () {
      if (!picked.length) return;
      var t = picked.pop();
      for (var k = 0; k < pool.length; k++) { if (pool[k] === null) { pool[k] = t; break; } }
      draw();
    };
    App.el('gg-check').onclick = function () {
      var ok = picked.join(' ') === r.tokens.join(' ');
      score(ok);
      stage('<div class="qfeed ' + (ok ? 'correct' : 'wrong') + '">' +
        (ok ? '✓ To\'g\'ri!' : '✗ To\'g\'ri javob: ' + App.esc(r.tokens.join(' '))) + '</div>');
      setTimeout(next, ok ? 900 : 1900);
    };
  }

  function renderMatch() {
    // Juftlash bir bosqichda: barcha juftlarni ulash kerak
    var pairs = G.data.pairs;
    var left = shuffle(pairs.map(function (p, i) { return { t: p.a, i: i }; }));
    var right = shuffle(pairs.map(function (p, i) { return { t: p.b, i: i }; }));
    var selL = null, doneCount = 0;

    stage('<p class="muted" style="font-size:12.5px;margin:0 0 12px">Chapdagi so\'zni tanlab, o\'ngdan mosini bosing.</p>' +
      '<div class="gg-match"><div class="gg-col" id="gg-l"></div><div class="gg-col" id="gg-r"></div></div>');

    function draw() {
      App.el('gg-l').innerHTML = left.map(function (x, i) {
        return '<button class="gg-mtok' + (x.done ? ' done' : '') + (selL === i ? ' sel' : '') + '" data-i="' + i + '">' + App.esc(x.t) + '</button>';
      }).join('');
      App.el('gg-r').innerHTML = right.map(function (x, i) {
        return '<button class="gg-mtok' + (x.done ? ' done' : '') + '" data-i="' + i + '">' + App.esc(x.t) + '</button>';
      }).join('');
      App.el('gg-l').querySelectorAll('.gg-mtok').forEach(function (b, i) {
        b.onclick = function () { if (left[i].done) return; selL = i; draw(); };
      });
      App.el('gg-r').querySelectorAll('.gg-mtok').forEach(function (b, i) {
        b.onclick = function () {
          if (right[i].done || selL === null) return;
          var ok = left[selL].i === right[i].i;
          score(ok);
          if (ok) {
            left[selL].done = true; right[i].done = true; doneCount++;
            selL = null; draw();
            if (doneCount === pairs.length) setTimeout(finish, 600);
          } else {
            b.classList.add('bad');
            setTimeout(function () { selL = null; draw(); }, 550);
          }
        };
      });
    }
    draw();
  }

  /* ---------- Boshlash ---------- */
  function start(page, def, onExit) {
    G = {
      page: page, def: def, onExit: onExit, type: def.type, data: def,
      step: 0, good: 0, bad: 0
    };
    if (def.type === 'sort') { G.items = shuffle(def.items); G.total = G.items.length; }
    else if (def.type === 'match') { G.total = 1; }
    else { G.total = def.rounds.length; }

    page.innerHTML = '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" id="gg-exit"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(GUIDE[def.type].label) + '</h1></div>' +
      hud() + '<div id="gg-stage"></div>';
    App.icons(page);
    App.el('gg-exit').onclick = onExit;
    renderStep();
  }

  window.GrammarGames = { parse: parseGame, guide: GUIDE, start: start };
})();
