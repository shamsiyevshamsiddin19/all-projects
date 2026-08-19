/* Testlar (Quiz) — fanlar/bazalar boshqaruvi, test yechish, ro'yxat rejimi, natija. */
(function () {
  'use strict';

  var Q = {
    structure: null,           // [{subject, name, full, count}]
    data: null,                // {questions, solved, flags} — joriy baza
    db: '',
    quiz: null,                // {active, index, score}
    list: null,                // {active, rendered, chunkSize, title}
    session: { correct: 0, wrong: 0, total: 0 }
  };

  /* ---------- Yordamchi: sarlavha qatori ---------- */
  function topbar(title, backView, backParams, rightHtml) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: backView, p: backParams || {} }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(title) + '</h1>' + (rightHtml || '') + '</div>';
  }

  /* ---------- Matn/LaTeX render (MathJax mavjud bo'lsa) ---------- */
  function mathHtml(text) {
    var t = App.esc(String(text == null ? '' : text));
    t = t.replace(/\[tex\]([\s\S]*?)\[\/tex\]/g, function (_, e) { return '\\(' + e + '\\)'; });
    return t.replace(/\n/g, '<br>');
  }
  /* MathJax faqat matnda LaTeX bo'lsa yuklanadi (bir marta) — har sahifada CDN'ga
     so'rov ketmasin. `\(...\)`, `$...$` yoki `[tex]` uchrasa ishga tushadi. */
  var mjState = 0; // 0=yuklanmagan, 1=yuklanmoqda, 2=tayyor
  function needsMath(el) {
    var t = el ? (el.textContent || '') : '';
    return t.indexOf('\\(') >= 0 || t.indexOf('\\[') >= 0 || /\$[^$]+\$/.test(t);
  }
  function loadMathJax(cb) {
    if (mjState === 2) return cb();
    if (mjState === 1) { setTimeout(function () { loadMathJax(cb); }, 300); return; }
    mjState = 1;
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js';
    s.async = true;
    s.onload = function () { mjState = 2; cb(); };
    s.onerror = function () { mjState = 0; };
    document.head.appendChild(s);
  }
  function typeset(el) {
    if (!el || !needsMath(el)) return;
    loadMathJax(function () {
      if (window.MathJax && MathJax.typesetPromise) {
        try { MathJax.typesetPromise([el]); } catch (e) {}
      }
    });
  }
  // Grammar mavzu testlari ham shu render/LaTeX yordamchilaridan foydalanadi
  App.mathHtml = mathHtml;
  App.typeset = typeset;

  /* ---------- Savol izohi (IXTIYORIY) ----------
     Savolda izoh bo'lsa — javob berilgandan keyin yuqorida lampa belgisi
     paydo bo'ladi; bosilganda izoh pastki oynada ochiladi. Izohi yo'q
     savollarda lampa umuman ko'rinmaydi (eski xatti-harakat saqlanadi). */
  function hasExpl(q) { return String((q && q.explanation) || '').trim() !== ''; }

  function lampHtml(qid) {
    return '<button class="qlamp hidden" data-act="showExpl" data-arg=\'' + App.arg({ id: qid }) +
      '\' title="Izoh" aria-label="Izoh"><span data-icon="bulb" data-icon-size="17"></span></button>';
  }

  /* Javob berilgach chaqiriladi — izohi bor savolda lampani ko'rsatadi */
  function revealLamp(scope, q) {
    if (!scope || !hasExpl(q)) return;
    var b = scope.querySelector('.qlamp');
    if (b) b.classList.remove('hidden');
  }

  App.actions.showExpl = function (a) {
    var list = (Q.data && Q.data.questions) || [];
    var q = list.find(function (x) { return String(x.id) === String(a.id); });
    var t = String((q && q.explanation) || '').trim();
    if (!t) return App.toast('Bu savolda izoh yo\'q');
    var sh = App.sheet('<div class="qexpl-t">' + mathHtml(t) + '</div>', { title: 'Izoh' });
    typeset(sh);
  };

  /* ---------- Test matnini parslash (raqamli/#/A)-B)/+- formatlar) ---------- */
  function parseTests(text) {
    var lines = String(text || '').replace(/\r/g, '').split('\n');
    var questions = [], cur = null, lastOption = null, inExpl = false;

    function startQuestion(t) {
      finishQuestion();
      cur = { text: String(t || '').trim(), options: {}, correct: '', idx: 0, explanation: '' };
      lastOption = null; inExpl = false;
    }
    function finishQuestion() {
      if (!cur) return;
      var cleaned = {};
      Object.keys(cur.options).forEach(function (k) { var v = String(cur.options[k] || '').trim(); if (v) cleaned[k] = v; });
      var keys = Object.keys(cleaned);
      var correct = String(cur.correct || '').trim().toUpperCase();
      if (cur.text.trim() && keys.length) {
        questions.push({
          text: cur.text.trim(),
          options: cleaned,
          correct: cleaned[correct] ? correct : keys[0],
          explanation: String(cur.explanation || '').trim()
        });
      }
      cur = null; lastOption = null; inExpl = false;
    }

    lines.forEach(function (raw) {
      var line = raw.trim(); var m;
      // Bo'sh qator izohni to'xtatmaydi — izoh bir necha xatboshi bo'lishi mumkin
      if (!line) { if (!inExpl) lastOption = null; return; }
      if ((m = line.match(/^(?:savol|question|q)\s*[:.)-]\s*(.*)$/i))) { startQuestion(m[1]); return; }
      if ((m = line.match(/^#\s*(.*)$/))) { startQuestion(m[1]); return; }
      if ((m = line.match(/^\d+[.)]\s*(.*)$/))) { startQuestion(m[1]); return; }
      if (!cur) { startQuestion(line); return; }
      // IXTIYORIY izoh — "Izoh: ...", "Tushuntirish: ...", "Explanation: ..."
      // Javobdan keyin ko'rsatiladi. Bir necha qator bo'lishi mumkin.
      if ((m = line.match(/^(?:izoh|izox|tushuntirish|explanation|expl|note)\s*[:.-]\s*(.*)$/i))) {
        cur.explanation = m[1].trim(); lastOption = null; inExpl = true; return;
      }
      if ((m = line.match(/^(?:javob|answer|correct)\s*[:-]\s*([A-H])/i))) {
        cur.correct = m[1].toUpperCase(); lastOption = null; inExpl = false; return;
      }
      if ((m = line.match(/^([A-H])[).:-]\s*(.*)$/i))) {
        var key = m[1].toUpperCase(); cur.options[key] = m[2].trim();
        cur.idx = Math.max(cur.idx, key.charCodeAt(0) - 64); lastOption = key; inExpl = false; return;
      }
      if (/^[+-]\s*/.test(line)) {
        var k2 = String.fromCharCode(65 + cur.idx++); cur.options[k2] = line.substring(1).trim();
        if (line.charAt(0) === '+') cur.correct = k2; lastOption = k2; inExpl = false; return;
      }
      // Izoh boshlangan bo'lsa — keyingi oddiy qatorlar ham izohga qo'shiladi
      if (inExpl) { cur.explanation = [cur.explanation, line].filter(Boolean).join('\n'); return; }
      if (lastOption) { cur.options[lastOption] = [cur.options[lastOption], line].filter(Boolean).join('\n'); return; }
      cur.text = [cur.text, line].filter(Boolean).join('\n');
    });
    finishQuestion();
    return questions;
  }
  // Grammar moduli ham xuddi shu formatdan foydalanadi
  App.parseTests = parseTests;

  function shuffleOptions(q) {
    var keys = Object.keys(q.options);
    var vals = keys.map(function (k) { return q.options[k]; });
    var correctVal = q.options[q.correct];
    for (var i = vals.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = vals[i]; vals[i] = vals[j]; vals[j] = t; }
    var newOptions = {}, newCorrect = '';
    keys.forEach(function (k, i) { newOptions[k] = vals[i]; if (vals[i] === correctVal) newCorrect = k; });
    return Object.assign({}, q, { options: newOptions, correct: newCorrect });
  }

  /* ---------- Ma'lumot yuklash ---------- */
  function loadStructure(force) {
    if (Q.structure && !force) return Promise.resolve(Q.structure);
    return App.call('get_structure').then(function (j) { Q.structure = j.structure || []; return Q.structure; });
  }
  function loadDB(full) {
    return App.call('get_data', null, { query: 'db=' + encodeURIComponent(full) }).then(function (j) {
      Q.db = full;
      Q.data = {
        questions: j.questions || [], solved: j.solved || [],
        flags: j.flags || {}, wrong: j.wrong || {}
      };
      return Q.data;
    });
  }
  function subjectOf(full) { return full.split('__')[0] || ''; }

  /* ---------- Fan/baza ikonkasi ----------
     Avval maktab/universitet fanlari uchun emoji jadvali, so'ng texnologiya
     logolari (Learn'dagi 138 talik baza, `TechIcon` orqali — jadval bitta
     nusxada, languages.js'da). Hech biri topilmasa — rangli harf plitkasi. */
  var FAN_EMOJI = [
    [/matem|algebra|geometr|matan|hisob/,        '🧮', '#3B82F6'],
    [/fizik/,                                    '⚛️', '#8B5CF6'],
    [/kimyo|ximiy/,                              '🧪', '#10B981'],
    [/biolog|anatom|botanik|zoolog/,             '🧬', '#22C55E'],
    [/tarix|history/,                            '🏛', '#F59E0B'],
    [/geograf/,                                  '🌍', '#06B6D4'],
    [/ingliz|english/,                           '🇬🇧', '#EF4444'],
    [/rus\b|russk|русск/,                        '🇷🇺', '#6366F1'],
    [/ona tili|adabiyot|o'zbek|ozbek/,           '📖', '#EC4899'],
    [/huquq|konstitu|qonun/,                     '⚖️', '#64748B'],
    [/iqtisod|moliya|buxgalt|menejment|marketing/, '💰', '#F97316'],
    [/tibbiy|meditsin|salomatlik/,               '🩺', '#F43F5E'],
    [/falsafa|mantiq|psixolog|sotsiolog/,        '🧠', '#A855F7'],
    [/sport|jismoniy/,                           '🏅', '#14B8A6'],
    [/harbiy|mudofa|fuqaro muhofaza/,            '🛡', '#78716C'],
    [/din|islom|hadis/,                          '🕌', '#0EA5E9'],
    [/ekolog|atrof muhit/,                       '🌱', '#84CC16']
  ];

  function subjectIcon(name, parent) {
    var s = 28;
    var low = (name || '').replace(/_/g, ' ').toLowerCase();
    for (var i = 0; i < FAN_EMOJI.length; i++) {
      if (FAN_EMOJI[i][0].test(low)) {
        return '<span style="width:' + s + 'px;height:' + s + 'px;border-radius:8px;background:' +
          FAN_EMOJI[i][2] + '22;font-size:16px;display:inline-flex;align-items:center;justify-content:center">' +
          FAN_EMOJI[i][1] + '</span>';
      }
    }
    // Texnologiya logosi — baza nomida topilmasa, fan nomidan ham qidiramiz
    if (window.TechIcon) {
      if (TechIcon.find(low)) return TechIcon.html(low, s);
      if (parent && TechIcon.find(parent.replace(/_/g, ' ').toLowerCase())) {
        return TechIcon.html(parent.replace(/_/g, ' ').toLowerCase(), s);
      }
      return TechIcon.html(name || '?', s);   // rangli harf plitkasi
    }
    return '<span style="width:' + s + 'px;height:' + s + 'px;border-radius:8px;background:var(--accent);' +
      'color:#fff;font-weight:700;font-size:14px;display:inline-flex;align-items:center;justify-content:center">' +
      App.esc((name || '?').charAt(0).toUpperCase()) + '</span>';
  }

  /* ---------- Ro'yxat sozlamasi (oraliq / bo'lak) — bazaga bog'liq, localStorage'da saqlanadi ---------- */
  function listCfgAll() { try { return JSON.parse(localStorage.getItem('quiz_list_cfg_v1') || '{}') || {}; } catch (e) { return {}; } }
  function loadListCfg(db) { return listCfgAll()[db] || null; }
  function saveListCfg(db, cfg) { var all = listCfgAll(); all[db] = cfg; localStorage.setItem('quiz_list_cfg_v1', JSON.stringify(all)); }
  function clampNum(v, min, max, fallback) {
    var n = parseInt(v, 10);
    if (isNaN(n)) return fallback;
    return Math.max(min, Math.min(max, n));
  }
  function startRangeQuiz(from, to) {
    Q.session = { correct: 0, wrong: 0, total: 0, startedAt: Date.now() };
    var set = Q.data.questions.slice(from - 1, to);
    if (!set.length) return App.toast('Bu oraliqda savol yo\'q');
    Q.list = { active: set.map(shuffleOptions), rendered: 0, chunkSize: set.length, title: 'Ro\'yxat (' + from + '-' + to + ')' };
    Q.session.total = set.length;
    App.go('quiz_list', { db: Q.db });
  }
  function defaultListCfg(total) { return { mode: 'range', from: 1, to: Math.min(20, total), chunk: Math.min(25, total) }; }

  function openListConfig() {
    if (!Q.data) return App.toast('Baza yuklanmoqda, biroz kuting');
    var total = Q.data.questions.length;
    var chunkMin = Math.min(10, total || 1);
    var cfg = loadListCfg(Q.db) || defaultListCfg(total);
    if (cfg.to > total) cfg.to = total;
    if (cfg.chunk > total) cfg.chunk = total || 1;
    if (cfg.chunk < chunkMin) cfg.chunk = chunkMin;

    var html =
      '<div class="seg" style="margin-bottom:14px">' +
      '<button class="' + (cfg.mode === 'range' ? 'active' : '') + '" data-act="qlSetMode" data-arg=\'{"mode":"range"}\'>Oraliq</button>' +
      '<button class="' + (cfg.mode === 'chunk' ? 'active' : '') + '" data-act="qlSetMode" data-arg=\'{"mode":"chunk"}\'>Bo\'laklarga bo\'lib</button>' +
      '</div>' +
      (cfg.mode === 'range'
        ? '<div class="flex" style="gap:8px;margin-bottom:10px">' +
          '<label class="field" style="flex:1;margin:0"><span>Dan (1-' + total + ')</span><input class="input" type="number" id="ql-from" min="1" max="' + total + '" value="' + cfg.from + '"></label>' +
          '<label class="field" style="flex:1;margin:0"><span>Gacha</span><input class="input" type="number" id="ql-to" min="1" max="' + total + '" value="' + cfg.to + '"></label>' +
          '</div>' +
          '<button class="btn" id="ql-range-start" style="width:100%">Boshlash</button>'
        : '<label class="field"><span>Necha tadan bo\'lak (kamida ' + chunkMin + ', jami ' + total + ' savol)</span><input class="input" type="number" id="ql-chunk" min="' + chunkMin + '" max="' + total + '" value="' + cfg.chunk + '"></label>' +
          '<div id="ql-chunks" class="flex" style="flex-wrap:wrap;gap:8px;margin-top:4px"></div>');

    var sh = App.sheet(html, { title: 'Tanlab ishlash' });

    if (cfg.mode === 'range') {
      sh.querySelector('#ql-from').oninput = function () { cfg.from = clampNum(this.value, 1, total, cfg.from); saveListCfg(Q.db, cfg); };
      sh.querySelector('#ql-to').oninput = function () { cfg.to = clampNum(this.value, 1, total, cfg.to); saveListCfg(Q.db, cfg); };
      sh.querySelector('#ql-range-start').onclick = function () {
        var from = clampNum(sh.querySelector('#ql-from').value, 1, total, cfg.from);
        var to = clampNum(sh.querySelector('#ql-to').value, 1, total, cfg.to);
        if (from > to) { var t = from; from = to; to = t; }
        cfg.from = from; cfg.to = to; saveListCfg(Q.db, cfg);
        App.closeSheet();
        startRangeQuiz(from, to);
      };
    } else {
      var renderBlocks = function (size) {
        var cbox = sh.querySelector('#ql-chunks'); if (!cbox) return;
        var blocksHtml = '';
        for (var i = 0; i < total; i += size) {
          var from = i + 1, to = Math.min(total, i + size);
          blocksHtml += '<button class="chip-btn" data-from="' + from + '" data-to="' + to + '">' + from + '-' + to + '</button>';
        }
        cbox.innerHTML = blocksHtml || '<p class="muted" style="font-size:13px;margin:2px">Savol yo\'q</p>';
        cbox.querySelectorAll('button').forEach(function (b) {
          b.onclick = function () {
            var from = +this.getAttribute('data-from'), to = +this.getAttribute('data-to');
            App.closeSheet();
            startRangeQuiz(from, to);
          };
        });
      };
      sh.querySelector('#ql-chunk').oninput = function () {
        var n = parseInt(this.value, 10);
        renderBlocks(isNaN(n) || n < 1 ? chunkMin : Math.min(n, total));
      };
      sh.querySelector('#ql-chunk').onchange = function () {
        var size = clampNum(this.value, chunkMin, total, cfg.chunk);
        this.value = size; cfg.chunk = size; saveListCfg(Q.db, cfg);
        renderBlocks(size);
      };
      renderBlocks(cfg.chunk);
    }
  }
  App.actions.qlOpen = function () { openListConfig(); };
  App.actions.qlSetMode = function (a) {
    var cfg = loadListCfg(Q.db) || defaultListCfg(Q.data.questions.length);
    cfg.mode = a.mode;
    saveListCfg(Q.db, cfg);
    openListConfig();
  };

  /* =========================================================
     VIEW: fanlar — fanlar ro'yxati (hub)
     ========================================================= */
  App.view('fanlar', {
    nav: 'fanlar',
    render: function (page) {
      page.innerHTML = '<div class="topbar" style="margin:-16px -15px 12px"><h1>Testlar</h1>' +
        '<button class="icon-btn ghost" data-act="fanAdd" aria-label="Fan qo\'shish"><span data-icon="plus" data-icon-size="20"></span></button></div>' +
        '<div id="fan-list"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      loadStructure().then(function (structure) {
        var box = App.el('fan-list'); if (!box) return;
        var bySubject = {};
        structure.forEach(function (r) {
          bySubject[r.subject] = bySubject[r.subject] || { name: r.subject, count: 0, dbs: 0 };
          bySubject[r.subject].count += r.count; bySubject[r.subject].dbs += 1;
        });
        var subjects = Object.keys(bySubject).sort();
        if (!subjects.length) { box.innerHTML = App.empty({ icon: 'book', title: 'Fan yo\'q', text: '"+" tugmasi bilan birinchi fan qo\'shing.' }); return; }
        box.innerHTML = subjects.map(function (s) {
          var d = bySubject[s];
          return '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'fanlar_subject', p: { subject: s } }) + '\'>' +
            '<span class="li-ic" style="background:none;padding:0">' + subjectIcon(s) + '</span>' +
            '<div class="li-main"><div class="li-title">' + App.esc(s) + '</div><div class="li-sub">' + d.dbs + ' baza · ' + d.count + ' savol</div></div>' +
            '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
        }).join('');
        App.icons(box);
      });
    }
  });
  App.actions.fanAdd = function () {
    App.prompt({ title: 'Yangi fan', label: 'Fan nomi (masalan: Matematika)' }, function (name) {
      App.go('fanlar_subject', { subject: name.replace(/\s+/g, '_') });
    });
  };

  /* =========================================================
     VIEW: fanlar_subject — bitta fan ichidagi bazalar
     ========================================================= */
  App.view('fanlar_subject', {
    nav: 'fanlar',
    render: function (page, params) {
      var subject = params.subject || '';
      page.innerHTML = topbar(subject, 'fanlar') +
        '<div id="db-list"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<button class="btn sec" data-act="dbAdd" data-arg=\'' + App.arg({ subject: subject }) + '\' style="margin-top:14px"><span data-icon="plus" data-icon-size="16"></span>Yangi baza</button> ' +
        '<button class="btn ghost" data-act="fanManage" data-arg=\'' + App.arg({ subject: subject }) + '\' style="margin-top:10px">Fanni boshqarish</button>';
      App.icons(page);
      loadStructure().then(function (structure) {
        var box = App.el('db-list'); if (!box) return;
        var dbs = structure.filter(function (r) { return r.subject === subject; });
        if (!dbs.length) { box.innerHTML = App.empty({ icon: 'file', title: 'Baza yo\'q', text: 'Pastdagi tugma bilan birinchi bazani qo\'shing.' }); return; }
        box.innerHTML = dbs.map(function (d) {
          return '<div class="list-row">' +
            '<span class="li-ic" style="background:none;padding:0">' + subjectIcon(d.name, subject) + '</span>' +
            '<button class="li-main li-btn" data-act="go" data-arg=\'' + App.arg({ v: 'quiz_dashboard', p: { db: d.full } }) + '\'>' +
            '<div class="li-title">' + App.esc(d.name) + '</div><div class="li-sub">' + d.count + ' savol</div></button>' +
            '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="dbManage" data-arg=\'' + App.arg({ full: d.full, name: d.name }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
        }).join('');
        App.icons(box);
      });
    }
  });

  /* Matnli fayldan (.txt) savollarni o'qib, textarea'ga qo'yadi va sonini ko'rsatadi. */
  function attachTxtPicker(sh, fileId, textId, infoId, nameId) {
    var fileEl = sh.querySelector('#' + fileId);
    if (!fileEl) return;
    fileEl.onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
      var info = sh.querySelector('#' + infoId);
      if (info) { info.textContent = 'O\'qilmoqda...'; info.style.color = 'var(--hint)'; }
      var reader = new FileReader();
      reader.onload = function () {
        var text = String(reader.result || '');
        sh.querySelector('#' + textId).value = text;
        var found = parseTests(text).length;
        if (info) {
          info.textContent = found
            ? '✅ ' + f.name + ' — ' + found + ' ta savol topildi'
            : '⚠️ ' + f.name + ' — savol topilmadi, formatni tekshiring';
          info.style.color = found ? 'var(--success)' : 'var(--danger)';
        }
        // Baza nomi bo'sh bo'lsa, fayl nomidan taklif qilamiz
        if (nameId) {
          var nameEl = sh.querySelector('#' + nameId);
          if (nameEl && !nameEl.value.trim()) nameEl.value = f.name.replace(/\.[^.]+$/, '');
        }
      };
      reader.onerror = function () {
        if (info) { info.textContent = '⚠️ Faylni o\'qib bo\'lmadi'; info.style.color = 'var(--danger)'; }
      };
      reader.readAsText(f, 'UTF-8');
    };
  }

  function txtPickerHtml(fileId, infoId) {
    return '<button class="btn sec" type="button" onclick="document.getElementById(\'' + fileId + '\').click()" style="margin-bottom:10px">' +
      '<span data-icon="upload" data-icon-size="16"></span>Fayldan yuklash (.txt)</button>' +
      '<input type="file" id="' + fileId + '" hidden accept=".txt,text/plain">' +
      '<p class="muted" id="' + infoId + '" style="font-size:12px;margin:-4px 1px 12px"></p>';
  }

  App.actions.dbAdd = function (a) {
    var html =
      '<label class="field"><span>Baza nomi</span><input class="input" id="db-name" placeholder="Masalan: 1-variant"></label>' +
      txtPickerHtml('db-file', 'db-file-info') +
      '<label class="field"><span>Savollar matni</span><textarea class="textarea" id="db-text" rows="9" placeholder="1. Savol matni&#10;A) Variant&#10;B) Variant&#10;Javob: A&#10;&#10;yoki&#10;&#10;#Savol&#10;- Noto\'g\'ri&#10;+ To\'g\'ri"></textarea></label>' +
      '<p class="muted" style="font-size:11.5px;margin:-6px 1px 12px">' +
      'Izoh (ixtiyoriy): javob qatoridan keyin <code>Izoh: ...</code> yozing — ' +
      'javob berilgach ko\'rsatiladi. Yozmasangiz ham bo\'ladi.<br>' +
      'LaTeX: <code>[tex]...[/tex]</code> yoki <code>\\(...\\)</code></p>' +
      '<button class="btn" id="db-save">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Yangi baza — ' + a.subject });
    attachTxtPicker(sh, 'db-file', 'db-text', 'db-file-info', 'db-name');
    sh.querySelector('#db-save').onclick = function () {
      var name = sh.querySelector('#db-name').value.trim();
      var text = sh.querySelector('#db-text').value;
      if (!name) return App.toast('Baza nomini kiriting');
      var qs = parseTests(text);
      if (!qs.length) return App.toast('Savol topilmadi — formatni tekshiring');
      var full = a.subject + '__' + name.replace(/\s+/g, '_');
      App.call('create_db', { name: full }).then(function () {
        return App.call('upload_base', { questions: qs }, { query: 'db=' + encodeURIComponent(full) });
      }).then(function (res) {
        App.closeSheet(); App.toast('✅ ' + res.count + ' ta savol saqlandi');
        loadStructure(true).then(App.reload);
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
  };

  App.actions.dbManage = function (a) {
    var html =
      '<button class="list-row" data-act="dbRename" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="dbReplace" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="upload" data-icon-size="15"></span><div class="li-main"><div class="li-title">Savollarni yangilash</div></div></button>' +
      '<button class="list-row" data-act="dbDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)"><span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span><div class="li-main"><div class="li-title" style="color:var(--danger)">Bazani o\'chirish</div></div></button>';
    App.sheet(html, { title: a.name });
  };
  App.actions.dbRename = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Nomini o\'zgartirish', label: 'Yangi nom', value: a.name }, function (name) {
      var subject = subjectOf(a.full);
      App.call('rename_db', { old: a.full, new: subject + '__' + name.replace(/\s+/g, '_') })
        .then(function () { loadStructure(true).then(App.reload); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };
  App.actions.dbReplace = function (a) {
    App.closeSheet();
    var html = txtPickerHtml('db-file2', 'db-file2-info') +
      '<label class="field"><span>Yangi savollar matni (eskisi almashadi)</span><textarea class="textarea" id="db-text2" rows="9"></textarea></label>' +
      '<p class="muted" style="font-size:11.5px;margin:-6px 1px 12px">' +
      'Izoh (ixtiyoriy): javob qatoridan keyin <code>Izoh: ...</code> yozing.</p>' +
      '<button class="btn" id="db-save2">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Savollarni yangilash' });
    attachTxtPicker(sh, 'db-file2', 'db-text2', 'db-file2-info', null);
    sh.querySelector('#db-save2').onclick = function () {
      var qs = parseTests(sh.querySelector('#db-text2').value);
      if (!qs.length) return App.toast('Savol topilmadi');
      App.call('upload_base', { questions: qs }, { query: 'db=' + encodeURIComponent(a.full) })
        .then(function (res) { App.closeSheet(); App.toast('✅ ' + res.count + ' ta savol saqlandi'); loadStructure(true).then(App.reload); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
  };
  App.actions.dbDelete = function (a) {
    App.confirm('"' + a.name + '" bazasi butunlay o\'chiriladi.', function () {
      App.call('delete_db', { name: a.full }).then(function () { loadStructure(true).then(App.reload); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  App.actions.fanManage = function (a) {
    var html =
      '<button class="list-row" data-act="fanRename" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="fanDelete" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span><div class="li-main"><div class="li-title" style="color:var(--danger)">Fanni (barcha bazalari bilan) o\'chirish</div></div></button>';
    App.sheet(html, { title: a.subject });
  };
  App.actions.fanRename = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Fan nomini o\'zgartirish', label: 'Yangi nom', value: a.subject }, function (name) {
      App.call('rename_fan', { old: a.subject, new: name.replace(/\s+/g, '_') })
        .then(function () { loadStructure(true); App.go('fanlar'); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };
  App.actions.fanDelete = function (a) {
    App.confirm('"' + a.subject + '" fani va undagi BARCHA bazalar o\'chiriladi.', function () {
      App.call('delete_fan', { fan: a.subject }).then(function () { loadStructure(true); App.go('fanlar'); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* =========================================================
     VIEW: quiz_dashboard — test paneli
     ========================================================= */
  App.view('quiz_dashboard', {
    nav: 'fanlar',
    render: function (page, params) {
      var full = params.db || '';
      var rightHtml =
        '<button class="icon-btn ghost" data-act="qwVersions" data-arg=\'' + App.arg({ db: full }) + '\' ' +
        'aria-label="Xatolar versiyalari" title="Xatolar versiyalari"><span data-icon="clock" data-icon-size="18"></span></button>';
      page.innerHTML = topbar(full.split('__')[1] || full, 'fanlar_subject', { subject: subjectOf(full) }, rightHtml) +
        '<div class="stat-strip" id="qd-stats"></div>' +
        '<div class="btn-row" style="flex-direction:column;gap:10px">' +
        '<button class="btn" data-act="playQuiz" data-arg=\'{"mode":"all"}\'>Bittalab ishlash</button>' +
        '<div id="qd-wrong-btn"></div>' +
        '<button class="btn sec" data-act="playList" data-arg=\'{"mode":"all"}\'>Ro\'yxat (barchasi)</button>' +
        '<button class="btn sec" data-act="playList" data-arg=\'{"mode":"random"}\'>Tasodifiy 25 ta</button>' +
        '<button class="btn sec" data-act="qlOpen">Tanlab ishlash (oraliq / bo\'lak)</button>' +
        '<button class="btn sec" data-act="playQuiz" data-arg=\'{"mode":"saved"}\'>Saqlanganlar</button>' +
        '</div>' +
        '<button class="btn ghost" style="margin-top:14px" data-act="go" data-arg=\'' +
        App.arg({ v: 'quiz_manage', p: { db: full } }) + '\'><span data-icon="edit" data-icon-size="16"></span>Savollarni boshqarish</button>' +
        '<div class="list-label" style="margin-top:24px">Natijalar tarixi</div>' +
        '<div id="qd-history"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<button class="btn ghost" style="margin-top:22px;color:var(--danger);border-color:var(--danger-soft)" data-act="resetHistory">Tarixni tozalash</button>';
      App.icons(page);
      loadDB(full).then(function (d) {
        var box = App.el('qd-stats');
        var wrongCount = Object.keys(d.wrong || {}).length;
        if (box) {
          box.innerHTML =
            '<div class="s"><div class="n">' + d.questions.length + '</div><div class="l">Jami savol</div></div>' +
            '<div class="s"><div class="n">' + d.solved.length + '</div><div class="l">Yechilgan</div></div>' +
            '<div class="s"><div class="n" style="color:' + (wrongCount ? 'var(--danger)' : 'var(--text)') + '">' + wrongCount + '</div><div class="l">Xato</div></div>' +
            '<div class="s"><div class="n">' + Object.keys(d.flags).length + '</div><div class="l">Saqlangan</div></div>';
        }
        var wb = App.el('qd-wrong-btn');
        if (wb && wrongCount) {
          wb.innerHTML = '<div style="display:flex;gap:8px">' +
            '<button class="btn" style="background:var(--danger);flex:1" data-act="playQuiz" data-arg=\'{"mode":"wrong"}\'>' +
            '<span data-icon="alert" data-icon-size="16"></span>Xatolar ustida ishlash (' + wrongCount + ')</button>' +
            '<button class="btn sec" style="flex:0 0 auto;padding:0 14px" data-act="qwDownload" data-arg=\'' +
            App.arg({ db: full }) + '\' title=".md yuklab olish va versiya saqlash">' +
            '<span data-icon="download" data-icon-size="16"></span></button></div>';
          App.icons(wb);
        }
      });
      renderQuizHistory(full);
    }
  });

  /* Natijalar tarixi — oxirgi sessiyalar va o'sish ko'rsatkichi */
  function renderQuizHistory(full) {
    App.call('get_quiz_results', null, { query: 'db=' + encodeURIComponent(full) }).then(function (j) {
      var box = App.el('qd-history'); if (!box) return;
      var rows = j.results || [];
      if (!rows.length) {
        box.innerHTML = '<p class="muted" style="font-size:13px;margin:2px 1px">Hali test yakunlanmagan. Birinchi natijadan keyin shu yerda o\'sish ko\'rinadi.</p>';
        return;
      }
      var best = 0, sum = 0;
      rows.forEach(function (r) { if (r.percent > best) best = r.percent; sum += r.percent; });
      var avg = Math.round(sum / rows.length);

      box.innerHTML =
        '<div class="stat-strip" style="margin:0 0 12px">' +
        '<div class="s"><div class="n">' + rows.length + '</div><div class="l">Sessiya</div></div>' +
        '<div class="s"><div class="n">' + avg + '%</div><div class="l">O\'rtacha</div></div>' +
        '<div class="s"><div class="n" style="color:var(--success)">' + best + '%</div><div class="l">Eng yaxshi</div></div>' +
        '</div>' +
        '<div class="qh-bars">' + rows.slice(0, 12).reverse().map(function (r) {
          var col = r.percent >= 80 ? 'var(--success)' : (r.percent >= 50 ? 'var(--warn)' : 'var(--danger)');
          return '<div class="qh-bar" title="' + App.esc(r.at + ' — ' + r.percent + '%') + '">' +
            '<i style="height:' + Math.max(4, r.percent) + '%;background:' + col + '"></i></div>';
        }).join('') + '</div>' +
        rows.slice(0, 5).map(function (r) {
          var col = r.percent >= 80 ? 'var(--success)' : (r.percent >= 50 ? 'var(--warn)' : 'var(--danger)');
          return '<div class="list-row"><div class="li-main"><div class="li-title" style="font-size:13.5px">' +
            r.correct + '/' + r.total + ' to\'g\'ri</div><div class="li-sub">' + App.esc(r.at) + '</div></div>' +
            '<span class="li-val" style="color:' + col + ';font-weight:800">' + r.percent + '%</span></div>';
        }).join('');
    }).catch(function () {
      var box = App.el('qd-history');
      if (box) box.innerHTML = '<p class="muted" style="font-size:13px;margin:2px 1px">Tarixni yuklab bo\'lmadi.</p>';
    });
  }

  /* =========================================================
     VIEW: quiz_manage — savollarni qidirish va yakka tahrirlash
     ========================================================= */
  App.view('quiz_manage', {
    nav: 'fanlar',
    render: function (page, params) {
      var full = params.db || '';
      page.innerHTML = topbar('Savollar', 'quiz_dashboard', { db: full }) +
        '<div class="flex" style="gap:8px;margin-bottom:12px">' +
        '<input class="input" id="qm-q" placeholder="Savol yoki variant bo\'yicha qidirish..." style="flex:1">' +
        '<button class="icon-btn" id="qm-add" title="Savol qo\'shish"><span data-icon="plus" data-icon-size="18"></span></button></div>' +
        '<p class="muted" id="qm-count" style="font-size:12.5px;margin:0 0 8px"></p>' +
        '<div id="qm-list"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      var render = function () {
        var box = App.el('qm-list'); if (!box) return;
        var all = (Q.data && Q.data.questions) || [];
        var q = (App.el('qm-q').value || '').trim().toLowerCase();
        var shown = q ? all.filter(function (x) {
          var hay = (x.text + ' ' + Object.keys(x.options).map(function (k) { return x.options[k]; }).join(' ')).toLowerCase();
          return hay.indexOf(q) >= 0;
        }) : all;

        App.el('qm-count').textContent = q ? shown.length + ' ta topildi (jami ' + all.length + ')' : all.length + ' ta savol';
        if (!shown.length) {
          box.innerHTML = App.empty({ icon: 'book', title: q ? 'Topilmadi' : 'Savol yo\'q', text: q ? 'Boshqa so\'z bilan qidiring.' : '+ tugmasi bilan qo\'shing.' });
          App.icons(box); return;
        }
        // Ro'yxat uzun bo'lishi mumkin — birinchi 100 tasi ko'rsatiladi
        box.innerHTML = shown.slice(0, 100).map(function (x) {
          var n = all.indexOf(x) + 1;
          return '<button class="list-row" data-qid="' + x.id + '">' +
            '<span class="li-val" style="align-self:flex-start;min-width:26px">' + n + '</span>' +
            '<div class="li-main"><div class="li-title" style="white-space:normal">' + App.esc(x.text.slice(0, 90)) + '</div>' +
            '<div class="li-sub">To\'g\'ri: ' + App.esc(x.correct) + ' · ' + Object.keys(x.options).length + ' variant</div></div>' +
            '<span class="li-chev" data-icon="edit" data-icon-size="15"></span></button>';
        }).join('') +
          (shown.length > 100 ? '<p class="muted" style="font-size:12px;text-align:center;margin:12px 0">Yana ' + (shown.length - 100) + ' ta — qidiruv bilan toraytiring</p>' : '');
        App.icons(box);
        box.querySelectorAll('.list-row').forEach(function (b) {
          b.onclick = function () { questionSheet(page, full, b.getAttribute('data-qid'), render); };
        });
      };

      App.el('qm-q').oninput = render;
      App.el('qm-add').onclick = function () { questionSheet(page, full, null, render); };
      if (Q.db === full && Q.data) render(); else loadDB(full).then(render);
    }
  });

  function questionSheet(page, full, qid, onDone) {
    var isNew = !qid;
    var qq = isNew ? { text: '', options: { A: '', B: '', C: '', D: '' }, correct: 'A', explanation: '' }
      : Q.data.questions.find(function (x) { return String(x.id) === String(qid); });
    if (!qq) return;
    var keys = isNew ? ['A', 'B', 'C', 'D'] : Object.keys(qq.options);

    var html =
      '<label class="field"><span>Savol matni</span><textarea class="textarea" id="qs-text" rows="3">' + App.esc(qq.text) + '</textarea></label>' +
      '<div class="list-label" style="margin-top:2px">Variantlar (to\'g\'risini belgilang)</div>' +
      keys.map(function (k) {
        return '<div class="flex" style="gap:8px;margin-bottom:8px">' +
          '<button type="button" class="qs-pick' + (k === qq.correct ? ' sel' : '') + '" data-k="' + k + '">' + k + '</button>' +
          '<input class="input qs-opt" data-k="' + k + '" value="' + App.esc(qq.options[k] || '') + '" style="flex:1"></div>';
      }).join('') +
      '<label class="field"><span>Izoh (ixtiyoriy)</span>' +
      '<textarea class="textarea" id="qs-expl" rows="3" placeholder="Javob berilgandan keyin ko\'rsatiladi. Bo\'sh qoldirsangiz ham bo\'ladi.">' +
      App.esc(qq.explanation || '') + '</textarea></label>' +
      (isNew ? '<button class="btn" id="qs-save" style="margin-top:8px">Qo\'shish</button>'
        : '<div class="btn-row"><button class="btn danger" id="qs-del">O\'chirish</button><button class="btn" id="qs-save">Saqlash</button></div>');
    var sh = App.sheet(html, { title: isNew ? 'Yangi savol' : 'Savolni tahrirlash' });

    var correct = qq.correct;
    sh.querySelectorAll('.qs-pick').forEach(function (b) {
      b.onclick = function () {
        sh.querySelectorAll('.qs-pick').forEach(function (x) { x.classList.remove('sel'); });
        b.classList.add('sel'); correct = b.getAttribute('data-k');
      };
    });

    sh.querySelector('#qs-save').onclick = function () {
      var text = sh.querySelector('#qs-text').value.trim();
      if (!text) return App.toast('Savol matnini kiriting');
      var options = {};
      sh.querySelectorAll('.qs-opt').forEach(function (i) {
        var v = i.value.trim();
        if (v) options[i.getAttribute('data-k')] = v;
      });
      if (Object.keys(options).length < 2) return App.toast('Kamida 2 ta variant kerak');
      if (!options[correct]) return App.toast('To\'g\'ri javob bo\'sh variantga belgilangan');

      var explEl = sh.querySelector('#qs-expl');
      var action = isNew ? 'add_question' : 'edit_question';
      var payload = {
        text: text, options: options, correct: correct,
        explanation: explEl ? explEl.value.trim() : ''
      };
      if (!isNew) payload.id = qq.id;
      App.call(action, payload, { query: 'db=' + encodeURIComponent(full) }).then(function () {
        App.closeSheet(); App.toast('✅ Saqlandi');
        loadDB(full).then(onDone);
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };

    if (!isNew) {
      sh.querySelector('#qs-del').onclick = function () {
        App.confirm('Bu savol o\'chirilsinmi?', function () {
          App.call('delete_question', { id: qq.id }, { query: 'db=' + encodeURIComponent(full) }).then(function () {
            App.closeSheet(); App.toast('O\'chirildi');
            loadDB(full).then(onDone);
          }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        }, { danger: true, yes: 'O\'chirish' });
      };
    }
  }

  App.actions.resetHistory = function () {
    App.confirm('Bu bazadagi barcha yechilgan/saqlangan belgilar o\'chadi. Bu amalni ortga qaytarib bo\'lmaydi.', function () {
      App.confirm('Rostdan ham ishonchingiz komilmi? Progress butunlay yo\'qoladi.', function () {
        App.call('reset_history', null, { query: 'db=' + encodeURIComponent(Q.db) }).then(function () {
          App.toast('✅ Tozalandi'); App.reload();
        });
      }, { danger: true, yes: 'Ha, albatta o\'chirilsin', title: 'So\'nggi tasdiq' });
    }, { danger: true, yes: 'Davom etish' });
  };

  /* =========================================================
     Bitta-bitta o'ynash (quiz_play)
     ========================================================= */
  App.actions.playQuiz = function (a) {
    Q.session = { correct: 0, wrong: 0, total: 0, startedAt: Date.now() };
    var all = Q.data.questions, solvedIds = Q.data.solved || [], flags = Q.data.flags || {};
    var wrong = Q.data.wrong || {};
    var set;
    if (a.mode === 'saved') {
      set = all.filter(function (q) { return flags[q.id] === 'saved'; });
      if (!set.length) return App.toast('Saqlangan savollar yo\'q');
    } else if (a.mode === 'wrong') {
      // Ko'p xato qilingan savol oldinroq chiqadi
      set = all.filter(function (q) { return wrong[q.id] > 0; })
        .sort(function (x, y) { return (wrong[y.id] || 0) - (wrong[x.id] || 0); });
      if (!set.length) return App.toast('Xato qilingan savollar yo\'q');
    } else {
      var avail = all.filter(function (q) { return solvedIds.indexOf(q.id) === -1; });
      if (!avail.length) return App.toast('Barcha savollar yechilgan!');
      set = avail;
    }
    set = set.map(shuffleOptions);
    Q.session.total = set.length;
    Q.session.mode = a.mode || '';
    Q.quiz = { active: set, index: 0, score: 0, answered: false, src: a.mode === 'wrong' ? 'wrong' : '' };
    App.go('quiz_play', { db: Q.db });
  };

  /* `Q.quiz`/`Q.list` — faqat XOTIRADAGI sessiya, sahifa yangilanganda yo'qoladi.
     Router esa oxirgi hashni tiklaydi (`#quiz_play?db=...`), shuning uchun
     sahifa yangilangach yoki telefon ilovani fondan o'chirib qaytganda
     bu view'lar bo'sh holatga urilib QIZIL XATO kartasini chiqarardi.
     Endi jimgina panelga qaytariladi. */
  function sessionGate(state, page) {
    if (state && state.active && state.active.length) return true;
    App.toast('Sessiya tugagan — qaytadan boshlang');
    setTimeout(function () { App.go('quiz_dashboard', Q.db ? { db: Q.db } : {}); }, 0);
    if (page) page.innerHTML = '';
    return false;
  }

  App.view('quiz_play', {
    render: function (page) {
      if (!sessionGate(Q.quiz, page)) return;
      renderQuestion(page);
    }
  });

  function renderQuestion(page) {
    var quiz = Q.quiz, q = quiz.active[quiz.index];
    if (!q) return finishSession();
    quiz.answered = false;
    var pct = Math.round(((quiz.index + 1) / quiz.active.length) * 100);
    page.innerHTML =
      '<div class="topbar" style="margin:-16px -15px 12px"><button class="icon-btn ghost" data-act="finishQuiz"><span data-icon="x" data-icon-size="18"></span></button>' +
      '<h1>' + (quiz.index + 1) + ' / ' + quiz.active.length + '</h1>' +
      lampHtml(q.id) +
      '<span class="sub" style="font-weight:700;color:var(--success)">' + quiz.score + '</span></div>' +
      '<div class="qprog"><div class="bar"><i style="width:' + pct + '%"></i></div></div>' +
      '<div class="qtext" id="q-text"></div>' +
      '<div id="q-opts"></div>' +
      '<div id="q-feed"></div>' +
      '<button class="btn hidden" id="q-next" data-act="nextQuestion">Keyingi savol</button>' +
      '<button class="btn ghost" id="q-skip" data-act="skipQuestion">O\'tkazib yuborish</button>';
    var textEl = App.el('q-text'); textEl.innerHTML = mathHtml(q.text); typeset(textEl);
    var opts = App.el('q-opts');
    opts.innerHTML = Object.keys(q.options).map(function (k) {
      return '<button class="qopt" data-key="' + k + '"><b>' + k + ')</b><span class="qopt-t"></span></button>';
    }).join('');
    Object.keys(q.options).forEach(function (k) {
      opts.querySelector('[data-key="' + k + '"] .qopt-t').innerHTML = mathHtml(q.options[k]);
    });
    typeset(opts);
    opts.querySelectorAll('.qopt').forEach(function (btn) {
      btn.onclick = function () { checkAnswer(page, btn.getAttribute('data-key'), q); };
    });
    bindQuizKeys(page, q);
  }

  /* Klaviatura (desktop): 1-4 yoki A-D javob, Enter/bo'shliq keyingisi */
  function bindQuizKeys(page, q) {
    if (window._quizKeyHandler) document.removeEventListener('keydown', window._quizKeyHandler);
    window._quizKeyHandler = function (e) {
      if (!document.getElementById('q-opts')) {   // test ekranidan chiqilgan
        document.removeEventListener('keydown', window._quizKeyHandler);
        window._quizKeyHandler = null;
        return;
      }
      if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
      var keys = Object.keys(q.options);
      var idx = -1;
      if (/^[1-9]$/.test(e.key)) idx = parseInt(e.key, 10) - 1;
      else {
        var up = e.key.toUpperCase();
        if (keys.indexOf(up) >= 0) idx = keys.indexOf(up);
      }
      if (idx >= 0 && idx < keys.length) {
        e.preventDefault();
        var b = document.querySelector('#q-opts [data-key="' + keys[idx] + '"]');
        if (b && !b.classList.contains('disabled')) b.click();
        return;
      }
      if (e.key === 'Enter' || e.key === ' ') {
        var next = document.getElementById('q-next');
        if (next && !next.classList.contains('hidden')) { e.preventDefault(); next.click(); }
      }
    };
    document.addEventListener('keydown', window._quizKeyHandler);
  }

  function checkAnswer(page, choice, q) {
    var quiz = Q.quiz; if (quiz.answered) return;
    quiz.answered = true;
    var opts = App.el('q-opts');
    opts.querySelectorAll('.qopt').forEach(function (b) { b.classList.add('disabled'); });
    var chosenBtn = opts.querySelector('[data-key="' + choice + '"]');
    var feed = App.el('q-feed');
    if (choice === q.correct) {
      chosenBtn.classList.add('correct'); quiz.score++; Q.session.correct++;
      if (Q.data.solved.indexOf(q.id) === -1) Q.data.solved.push(q.id);
      App.call('mark_solved', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      // Xatolar rejimida to'g'ri javob berilsa — savol xatolar ro'yxatidan chiqadi
      if (Q.quiz && Q.quiz.src === 'wrong' && Q.data.wrong[q.id]) {
        delete Q.data.wrong[q.id];
        App.call('clear_wrong', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      }
      feed.innerHTML = '<div class="qfeed correct">✓ To\'g\'ri javob</div>';
    } else {
      chosenBtn.classList.add('wrong'); Q.session.wrong++;
      Q.data.wrong[q.id] = (Q.data.wrong[q.id] || 0) + 1;
      App.call('mark_wrong', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      var correctBtn = opts.querySelector('[data-key="' + q.correct + '"]'); if (correctBtn) correctBtn.classList.add('correct');
      feed.innerHTML = '<div class="qfeed wrong">✗ Xato. To\'g\'ri javob: ' + q.correct + '</div>';
    }
    // Izohi bor savolda — yuqoridagi lampa belgisi paydo bo'ladi
    revealLamp(page, q);
    App.el('q-skip').classList.add('hidden');
    var nextBtn = App.el('q-next'); nextBtn.classList.remove('hidden');
    nextBtn.textContent = quiz.index + 1 >= quiz.active.length ? 'Natijani ko\'rish' : 'Keyingi savol';
  }

  App.actions.nextQuestion = function () { Q.quiz.index++; App.go('quiz_play', { db: Q.db }, { silent: true }); };
  App.actions.skipQuestion = function () {
    App.confirm('Bu savol o\'tkazib yuborilsinmi?', function () { Q.quiz.index++; App.go('quiz_play', { db: Q.db }, { silent: true }); }, { yes: 'Ha' });
  };
  App.actions.finishQuiz = function () { finishSession(); };

  function finishSession() {
    // Tarixga faqat haqiqatan javob berilgan savollar hisoblanadi (yarim tashlab
    // ketilgan sessiyada 100 ta savol emas, javob berilgani yoziladi).
    var answered = Q.session.correct + Q.session.wrong;
    var total = answered > 0 ? answered : Q.session.total;
    var pct = total === 0 ? 0 : Math.round((Q.session.correct / total) * 100);
    App.state._result = { pct: pct, correct: Q.session.correct, wrong: Q.session.wrong, total: total };

    if (answered > 0) {
      App.call('save_quiz_result', {
        db: Q.db, mode: Q.session.mode || '', total: total,
        correct: Q.session.correct, wrong: Q.session.wrong,
        duration: Q.session.startedAt ? Math.round((Date.now() - Q.session.startedAt) / 1000) : null
      }).catch(function () {});
      if (window.Activity) window.Activity.mark();
    }
    App.go('quiz_result', { db: Q.db });
  }

  App.view('quiz_result', {
    render: function (page) {
      /* Natija ham xotirada — yangilangandan keyin "0%" degan yolg'on
         natija ko'rsatgandan ko'ra panelga qaytgan ma'qul. */
      var r = App.state._result;
      if (!r || !r.total) {
        setTimeout(function () { App.go('quiz_dashboard', Q.db ? { db: Q.db } : {}); }, 0);
        page.innerHTML = ''; return;
      }
      var msg = r.pct >= 90 ? 'Ajoyib natija!' : r.pct >= 70 ? 'Yaxshi!' : r.pct >= 50 ? 'Yomon emas' : 'Ko\'proq mashq qiling';
      page.innerHTML =
        '<div style="text-align:center;padding-top:8px">' +
        '<div class="res-circle"><span>' + r.pct + '%</span></div>' +
        '<h2 style="margin:0 0 22px">' + msg + '</h2>' +
        '<div class="stat-strip" style="max-width:280px;margin:0 auto 26px">' +
        '<div class="s"><div class="n" style="color:var(--success)">' + r.correct + '</div><div class="l">To\'g\'ri</div></div>' +
        '<div class="s"><div class="n" style="color:var(--danger)">' + r.wrong + '</div><div class="l">Xato</div></div>' +
        '<div class="s"><div class="n">' + r.total + '</div><div class="l">Jami</div></div>' +
        '</div>' +
        '<button class="btn" data-act="go" data-arg=\'' + App.arg({ v: 'quiz_dashboard', p: { db: Q.db } }) + '\'>Panelga qaytish</button>' +
        '<button class="btn ghost" style="margin-top:10px" data-act="go" data-arg=\'{"v":"home"}\'>Bosh sahifa</button>' +
        '</div>';
    }
  });

  /* =========================================================
     Ro'yxat rejimi (quiz_list)
     ========================================================= */
  App.actions.playList = function (a) {
    Q.session = { correct: 0, wrong: 0, total: 0, startedAt: Date.now() };
    var all = Q.data.questions, solvedIds = Q.data.solved || [];
    var avail = all.filter(function (q) { return solvedIds.indexOf(q.id) === -1; });
    if (!avail.length) return App.toast('Barcha savollar yechilgan!');
    var set, chunk = 50, title = 'Ro\'yxat (Barchasi)';
    if (a.mode === 'random') { set = avail.slice().sort(function () { return .5 - Math.random(); }).slice(0, 25); chunk = 25; title = 'Tasodifiy 25 ta'; }
    else { set = avail; }
    Q.list = { active: set.map(shuffleOptions), rendered: 0, chunkSize: chunk, title: title };
    Q.session.total = set.length;
    Q.session.mode = a.mode || 'list';
    App.go('quiz_list', { db: Q.db });
  };

  App.view('quiz_list', {
    render: function (page) {
      if (!sessionGate(Q.list, page)) return;
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'quiz_dashboard', p: { db: Q.db } }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(Q.list.title) + '</h1>' +
        '<button class="btn sm sec" style="width:auto" data-act="finishQuiz">Yakunlash</button>' +
        '</div>' +
        '<div id="ql-items"></div>' +
        '<button class="btn sec hidden" id="ql-more" data-act="listMore">Yana yuklash...</button>' +
        '<button class="btn" style="margin-top:14px" data-act="finishQuiz">Yakunlash — natijani ko\'rish</button>';
      renderListChunk();
    }
  });

  function renderListChunk() {
    var l = Q.list, box = App.el('ql-items'); if (!box) return;
    var start = l.rendered, end = Math.min(l.active.length, start + l.chunkSize);
    var html = '';
    for (var i = start; i < end; i++) {
      var q = l.active[i];
      var saved = (Q.data.flags || {})[q.id] === 'saved';
      html += '<div class="qcard" data-idx="' + i + '">' +
        '<div class="qcard-head"><span class="qn">#' + (i + 1) + '</span>' +
        lampHtml(q.id) +
        '<button class="qsave ' + (saved ? 'saved' : '') + '" data-act="toggleFlag" data-arg=\'' + App.arg({ id: q.id }) + '\'>' + (saved ? 'Saqlangan' : 'Saqlash') + '</button></div>' +
        '<div class="qtext qtext-l"></div>' +
        '<div class="q-opts-l"></div></div>';
    }
    box.insertAdjacentHTML('beforeend', html);
    for (var j = start; j < end; j++) {
      (function (idx) {
        var card = box.querySelector('.qcard[data-idx="' + idx + '"]');
        var qq = l.active[idx];
        var tEl = card.querySelector('.qtext-l'); tEl.innerHTML = mathHtml(qq.text);
        var oEl = card.querySelector('.q-opts-l');
        oEl.innerHTML = Object.keys(qq.options).map(function (k) { return '<button class="qopt" data-key="' + k + '"><b>' + k + ')</b><span class="qopt-t"></span></button>'; }).join('');
        Object.keys(qq.options).forEach(function (k) {
          oEl.querySelector('[data-key="' + k + '"] .qopt-t').innerHTML = mathHtml(qq.options[k]);
        });
        oEl.querySelectorAll('.qopt').forEach(function (btn) {
          btn.onclick = function () { checkListAnswer(card, idx, btn.getAttribute('data-key')); };
        });
        // Lampa belgisi SVG'ga aylanishi uchun (kartalar keyin qo'shilgani
        // sababli core.js ning avtomatik App.icons chaqiruvi ularga tegmaydi)
        App.icons(card);
        typeset(card);
      })(j);
    }
    l.rendered = end;
    var more = App.el('ql-more');
    if (more) more.classList.toggle('hidden', l.rendered >= l.active.length);
  }
  App.actions.listMore = function () { renderListChunk(); };

  function checkListAnswer(card, idx, choice) {
    if (card.classList.contains('answered')) return;
    card.classList.add('answered');
    var q = Q.list.active[idx];
    var opts = card.querySelectorAll('.qopt');
    opts.forEach(function (b) { b.classList.add('disabled'); });
    var chosen = card.querySelector('[data-key="' + choice + '"]');
    if (choice === q.correct) {
      chosen.classList.add('correct'); Q.session.correct++;
      if (Q.data.solved.indexOf(q.id) === -1) Q.data.solved.push(q.id);
      App.call('mark_solved', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      if (Q.list && Q.list.src === 'wrong' && Q.data.wrong[q.id]) {
        delete Q.data.wrong[q.id];
        App.call('clear_wrong', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      }
    } else {
      chosen.classList.add('wrong'); Q.session.wrong++;
      Q.data.wrong[q.id] = (Q.data.wrong[q.id] || 0) + 1;
      App.call('mark_wrong', { id: q.id }, { query: 'db=' + encodeURIComponent(Q.db) }).catch(function () {});
      var c = card.querySelector('[data-key="' + q.correct + '"]'); if (c) c.classList.add('correct');
    }
    // Izohi bor savolda — kartaning yuqorisidagi lampa belgisi paydo bo'ladi
    revealLamp(card, q);
  }

  App.actions.toggleFlag = function (a, btn) {
    var flags = Q.data.flags || {};
    var willSave = flags[a.id] !== 'saved';
    App.call('set_flag', { id: a.id, type: willSave ? 'saved' : '' }, { query: 'db=' + encodeURIComponent(Q.db) }).then(function () {
      if (willSave) flags[a.id] = 'saved'; else delete flags[a.id];
      Q.data.flags = flags;
      if (btn) { btn.classList.toggle('saved', willSave); btn.textContent = willSave ? 'Saqlangan' : 'Saqlash'; }
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* =========================================================
     XATO SAVOLLAR — .md yuklab olish + versiya tarixi

     Lug'atdagi ("Xatolar ustida ishlash") bilan bir xil g'oya: har
     "yuklab olish" bir versiya bo'lib saqlanadi. Versiya O'ZGARMAS —
     savol keyinroq "o'zlashtirildi" deb xatolardan chiqarilsa yoki
     umuman tahrirlansa ham, eski versiyada o'sha paytdagi holicha
     qoladi (savol matni va variantlari nusxaga yozilgan).
     ========================================================= */
  function qwBaseLabel(full) { return String(full || '').split('__')[1] || full || 'Test'; }

  function wrongToMd(questions, dbFull, whenLabel) {
    var lines = ['# Xato savollar — ' + qwBaseLabel(dbFull), '',
      '_' + whenLabel + ' · ' + questions.length + ' ta savol_', ''];
    questions.forEach(function (q, i) {
      lines.push('### ' + (i + 1) + '. ' + String(q.text || '').trim());
      if (q.wrong_count > 1) lines.push('*' + q.wrong_count + ' marta xato qilingan*');
      lines.push('');
      var opts = q.options || {};
      Object.keys(opts).forEach(function (k) {
        var mark = (k === q.correct) ? ' ✅' : '';
        lines.push('- **' + k + ')** ' + opts[k] + mark);
      });
      if (q.explanation && String(q.explanation).trim()) {
        lines.push('', '> ' + String(q.explanation).trim());
      }
      lines.push('');
    });
    return lines.join('\n');
  }

  function qwDateLabel() {
    var d = new Date();
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }

  function fmtSnapDate(iso) {
    var m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
    if (!m) return iso || '';
    var mon = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
    return (+m[3]) + '-' + mon[(+m[2]) - 1] + ', ' + m[4] + ':' + m[5];
  }

  /* Yuklab olish: joriy xato savollar .md bo'lib beriladi VA versiya saqlanadi */
  App.actions.qwDownload = function (a) {
    var full = a.db;
    App.call('save_wrong_snapshot', {}, { query: 'db=' + encodeURIComponent(full) })
      .then(function (saved) {
        /* Faylni nusxaning O'ZIDAN yasaymiz — shunda .md va saqlangan
           versiya bir xil bo'ladi (oradagi o'zgarish farq tug'dirmasin). */
        return App.call('get_wrong_snapshot', null, { query: 'id=' + encodeURIComponent(saved.id) });
      })
      .then(function (j) {
        var label = qwDateLabel();
        App.download('Xato savollar — ' + qwBaseLabel(full) + ' (' + label + ').md',
          wrongToMd(j.questions || [], full, label));
        App.toast('✅ Yuklandi va versiya sifatida saqlandi');
      })
      .catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  App.actions.qwVersions = function (a) {
    var full = a.db;
    var SHEET = App.sheet('<div id="qw-ver-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Xatolar versiyalari' });

    function draw() {
      App.call('list_wrong_snapshots', null, { query: 'db=' + encodeURIComponent(full) }).then(function (j) {
        var body = SHEET.querySelector('#qw-ver-body'); if (!body) return;
        var snaps = j.snapshots || [];
        if (!snaps.length) {
          body.innerHTML = App.empty({
            icon: 'clock', title: 'Versiya yo\'q',
            text: 'Xato savollarni birinchi marta yuklab olganingizda shu yerda versiya paydo bo\'ladi.'
          });
          App.icons(body); return;
        }
        body.innerHTML = snaps.map(function (v) {
          return '<div class="list-row">' +
            '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" ' +
            'data-act="qwVersionOpen" data-arg=\'' + App.arg({ db: full, id: v.id }) + '\'>' +
            '<div class="li-title">' + fmtSnapDate(v.created_at) + '</div>' +
            '<div class="li-sub">' + v.question_count + ' ta savol</div></button>' +
            '<button class="icon-btn ghost" style="width:32px;height:32px;color:var(--danger)" ' +
            'data-act="qwVersionDelete" data-arg=\'' + App.arg({ id: v.id }) + '\' title="O\'chirish">' +
            '<span data-icon="trash" data-icon-size="15"></span></button></div>';
        }).join('');
        App.icons(body);
      }).catch(function (e) {
        var body = SHEET.querySelector('#qw-ver-body');
        if (body) body.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
    }
    draw();
    SHEET._qwVerRedraw = draw;
  };

  App.actions.qwVersionDelete = function (a) {
    App.confirm('Bu versiya butunlay o\'chiriladi.', function () {
      App.call('delete_wrong_snapshot', { id: a.id }).then(function () {
        App.toast('✅ O\'chirildi');
        if (App._sheet && App._sheet.sh._qwVerRedraw) App._sheet.sh._qwVerRedraw();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  App.actions.qwVersionOpen = function (a) {
    var full = a.db;
    var SHEET = App.sheet('<div id="qw-vo-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Versiya' });
    App.call('get_wrong_snapshot', null, { query: 'id=' + encodeURIComponent(a.id) }).then(function (j) {
      var body = SHEET.querySelector('#qw-vo-body'); if (!body) return;
      var qs = j.questions || [], dateLabel = fmtSnapDate(j.created_at);
      body.innerHTML =
        '<p class="muted" style="font-size:13px;margin:-6px 0 12px">' + dateLabel + ' · ' + qs.length + ' ta savol</p>' +
        '<button class="btn" id="qw-vo-play" style="margin-bottom:8px">' +
        '<span data-icon="play" data-icon-size="16"></span>Shu savollar bilan ishlash</button>' +
        '<button class="btn sec" id="qw-vo-dl" style="margin-bottom:16px">' +
        '<span data-icon="download" data-icon-size="16"></span>.md qilib yuklab olish</button>' +
        qs.map(function (q, i) {
          return '<div class="list-row"><div class="li-main">' +
            '<div class="li-title" style="font-size:13.5px">' + (i + 1) + '. ' + App.esc(String(q.text || '').slice(0, 90)) + '</div>' +
            '<div class="li-sub">To\'g\'ri javob: ' + App.esc(q.correct || '') +
            (q.wrong_count > 1 ? ' · ' + q.wrong_count + ' marta xato' : '') + '</div></div></div>';
        }).join('');
      App.icons(body);

      body.querySelector('#qw-vo-play').onclick = function () {
        if (!qs.length) { App.toast('Savol yo\'q'); return; }
        App.closeSheet();
        /* Nusxadagi savollar bilan oddiy sessiya. `src='wrong'` — to'g'ri
           javob berilganda savol xatolar ro'yxatidan chiqadi (mark/clear
           chaqiruvlari savol ID si bo'yicha ishlaydi, ular o'zgarmagan).
           `Q.db` ni aniq qo'yamiz: versiya boshqa sahifadan ochilgan
           bo'lsa u hali o'rnatilmagan bo'lishi mumkin. */
        Q.db = full;
        Q.session = { correct: 0, wrong: 0, total: qs.length, startedAt: Date.now(), mode: 'wrong' };
        Q.quiz = { active: qs.map(shuffleOptions), index: 0, score: 0, answered: false, src: 'wrong' };
        App.go('quiz_play', { db: full });
      };
      body.querySelector('#qw-vo-dl').onclick = function () {
        App.download('Xato savollar — ' + qwBaseLabel(full) + ' (' + dateLabel + ').md',
          wrongToMd(qs, full, dateLabel));
      };
    }).catch(function (e) {
      var body = SHEET.querySelector('#qw-vo-body');
      if (body) body.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
    });
  };
})();
