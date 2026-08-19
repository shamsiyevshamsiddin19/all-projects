/* Grammar — Tillar uchun mavzular ro'yxati, har biriga .md fayl yuklab tushuntirish. */
(function () {
  'use strict';

  var LANG_LABEL = { english: 'Grammar', russian: 'Grammatika', coding: 'Dasturlash' };
  var BACK_VIEW = { english: 'english', russian: 'russian', coding: 'languages' };

  function normLang(v) { return v || 'english'; }

  function getLangLabel(v) {
    if (LANG_LABEL[v]) return LANG_LABEL[v];
    try {
      var arr = JSON.parse(localStorage.getItem('custom_langs') || '[]');
      var found = arr.filter(function(x) { return x.id === v; })[0];
      if (found) return found.name;
    } catch(e) {}
    return 'Mavzular';
  }

  function getBackView(v) {
    return BACK_VIEW[v] || 'languages';
  }

  function mdToHtml(md) { return App.md(md); }

  function topbar(title, back, backParams, rightBtn) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: back, p: backParams || {} }) + '\'>' +
      '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(title) + '</h1>' +
      (rightBtn || '') +
      '</div>';
  }

  /* ---------- Papkalar (ichma-ich) ----------
     Foydalanuvchi "Zamonlar/Present Simple" deb yozsa, backend uni ajratib,
     papkani ALOHIDA `folder` ustuniga yozadi. Frontend nomni o'zi bo'lmaydi —
     chunki mavzu nomining ichida ham "/" bo'lishi mumkin
     ("идти / ходить", "Этот/эта/это/эти") va bo'lish ularni buzardi.

     `folder` TO'LIQ YO'L: "Grammatika/Zamonlar". vocab.js dagi bilan bir xil
     naqsh — pathParent/lastSeg/childSeg orqali istalgan chuqurlikda navigatsiya. */
  function pathParent(p) {
    var s = String(p || ''); var i = s.lastIndexOf('/');
    return i < 0 ? '' : s.slice(0, i);
  }
  function lastSeg(p) {
    var s = String(p || ''); var i = s.lastIndexOf('/');
    return i < 0 ? s : s.slice(i + 1);
  }
  /* `base` ichidagi BEVOSITA keyingi bo'lak. base='' bo'lsa — ildizdagi 1-bo'lak. */
  function childSeg(base, path) {
    var p = String(path || '');
    if (base) {
      if (p !== base && p.indexOf(base + '/') !== 0) return null;
      p = p.slice(base.length + 1);
    }
    if (!p) return null;
    var i = p.indexOf('/');
    return i < 0 ? p : p.slice(0, i);
  }

  /* Joriy papka (`cur`) ichidagi bevosita ichki papkalar + bevosita mavzular. */
  function groupTopics(topics, cur) {
    var direct = [], subOrder = [], subCount = {};
    topics.forEach(function (t) {
      var f = (t.folder || '').trim();
      if (f === cur) { direct.push({ id: t.id, name: t.name, folder: f }); return; }
      var child = childSeg(cur, f);
      if (!child) return;
      var path = cur ? cur + '/' + child : child;
      if (!subCount[path]) { subCount[path] = 0; subOrder.push(path); }
      subCount[path]++;
    });
    return {
      folders: subOrder.map(function (p) { return { path: p, name: lastSeg(p), count: subCount[p] }; }),
      root: direct
    };
  }

  function topicRow(t, lang) {
    return '<div class="list-row">' +
      '<span class="li-ic" data-icon="book" data-icon-size="15"></span>' +
      '<button class="li-main li-btn" data-act="go" data-arg=\'' + App.arg({ v: 'grammar_topic', p: { id: t.id, lang: lang } }) + '\'>' +
      '<div class="li-title">' + App.esc(t.name) + '</div></button>' +
      '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="topicManage" data-arg=\'' + App.arg({ id: t.id, name: t.name, folder: t.folder || '', lang: lang }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
  }

  /* ---------- Mavzular ro'yxati ---------- */
  App.view('grammar', {
    nav: 'languages',
    render: function (page, params) {
      var lang = normLang(params.lang);
      var folder = params.folder || '';
      var parent = pathParent(folder);
      var backView = folder ? 'grammar' : getBackView(lang);
      var backParams = folder ? (parent ? { lang: lang, folder: parent } : { lang: lang }) : null;
      // Papka ichida bo'lsak, yangi mavzu o'sha papkaga qo'shiladi
      var plusBtn = '<button class="icon-btn ghost" data-act="topicAdd" data-arg=\'' +
        App.arg({ lang: lang, folder: folder }) + '\' style="margin-left:auto"><span data-icon="plus" data-icon-size="20"></span></button>';
      page.innerHTML = topbar(folder ? lastSeg(folder) : getLangLabel(lang), backView, backParams, plusBtn) +
        '<div id="topic-list"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      App.call('get_topics', null, { query: 'lang=' + lang }).then(function (j) {
        var box = App.el('topic-list'); if (!box) return;
        var topics = j.topics || [];
        var g = groupTopics(topics, folder);

        if (!g.folders.length && !g.root.length) {
          box.innerHTML = folder
            ? App.empty({ icon: 'book', title: 'Bo\'sh papka', text: 'Tepadagi + tugma bilan mavzu qo\'shing.' })
            : App.empty({ icon: 'book', title: 'Mavzu yo\'q', text: 'Tepadagi + tugma bilan qo\'shing. Papka uchun: "Zamonlar/Present Simple".' });
          App.icons(box); return;
        }

        var html = '';
        if (g.folders.length) {
          html += g.folders.map(function (f) {
            return '<button class="list-row" data-act="go" data-arg=\'' +
              App.arg({ v: 'grammar', p: { lang: lang, folder: f.path } }) + '\'>' +
              '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="archive" data-icon-size="15"></span>' +
              '<div class="li-main"><div class="li-title">' + App.esc(f.name) + '</div>' +
              '<div class="li-sub">' + f.count + ' ta mavzu</div></div>' +
              '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
          }).join('');
        }
        if (g.root.length) {
          if (g.folders.length) html += '<div class="list-label">' + (folder ? 'Mavzular' : 'Papkasiz') + '</div>';
          html += g.root.map(function (t) { return topicRow(t, lang); }).join('');
        }
        box.innerHTML = html;
        App.icons(box);
      }).catch(function (e) {
        var box = App.el('topic-list'); if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
    }
  });

  App.actions.topicAdd = function (a) {
    var inFolder = a.folder || '';
    App.prompt({
      title: inFolder ? 'Yangi mavzu — ' + inFolder : 'Yangi mavzu',
      label: inFolder ? 'Mavzu nomi' : 'Mavzu nomi (papka uchun: Zamonlar/Present Simple)',
      ok: 'Qo\'shish'
    }, function (name) {
      var payload = { lang: a.lang, name: name };
      // Papka ichida turib qo'shsak — papkani ANIQ ko'rsatamiz (nomni
      // prefikslamaymiz, aks holda nom ichidagi "/" chalkashlik tug'diradi).
      if (inFolder && name.indexOf('/') < 0) payload.folder = inFolder;
      App.call('add_topic', payload).then(function () { App.reload(); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };

  App.actions.topicManage = function (a) {
    var html =
      '<button class="list-row" data-act="topicRename" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="topicDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)"><span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span><div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
    App.sheet(html, { title: a.name });
  };
  App.actions.topicRename = function (a) {
    App.closeSheet();
    App.prompt({
      title: 'Nomini o\'zgartirish',
      label: a.folder ? 'Yangi nom (papka: ' + a.folder + ')' : 'Yangi nom (boshqa papkaga: Papka/Nom)',
      value: a.name
    }, function (name) {
      var payload = { id: a.id, name: name };
      // "/" yozilmagan bo'lsa mavzu o'z papkasida qoladi; yozilsa — ko'chadi
      if (name.indexOf('/') < 0) payload.folder = a.folder || '';
      App.call('rename_topic', payload).then(App.reload).catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };
  App.actions.topicDelete = function (a) {
    App.confirm('"' + a.name + '" mavzusi butunlay o\'chiriladi.', function () {
      App.call('delete_topic', { id: a.id }).then(function () { App.closeSheet(); App.reload(); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Bitta mavzu ---------- */
  App.view('grammar_topic', {
    nav: 'languages',
    render: function (page, params) {
      var lang = normLang(params.lang);
      var id = params.id;
      var menuBtn = '<button class="icon-btn ghost" id="topic-menu-btn" style="margin-left:auto"><span data-icon="edit" data-icon-size="18"></span></button>';
      page.innerHTML = topbar('Mavzu', 'grammar', { lang: lang }, menuBtn) +
        '<div id="topic-body"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<input type="file" id="topic-file" hidden accept=".md,text/markdown,text/plain">';
      App.icons(page);
      App.call('get_topic', null, { query: 'id=' + encodeURIComponent(id) }).then(function (j) {
        renderTopicBody(page, j, lang, id);
      }).catch(function (e) {
        var box = App.el('topic-body'); if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
    }
  });

  var TAB = 'matn';

  function reloadTopic(page, lang, id) {
    return App.call('get_topic', null, { query: 'id=' + encodeURIComponent(id) })
      .then(function (j) { renderTopicBody(page, j, lang, id); });
  }

  function renderTopicBody(page, topic, lang, id) {
    var box = App.el('topic-body'); if (!box) return;
    var folder = (topic.folder || '').trim();
    var titleEl = page.querySelector('.topbar h1');
    if (titleEl) titleEl.textContent = topic.name;
    // "Ortga" tugmasi mavzu turgan papkaga qaytsin (ildizdagi bo'lsa — ro'yxatga)
    var backBtn = page.querySelector('.topbar .icon-btn');
    if (backBtn) {
      backBtn.setAttribute('data-arg', App.arg({
        v: 'grammar', p: folder ? { lang: lang, folder: folder } : { lang: lang }
      }));
    }

    var tests = topic.test_content ? (App.parseTests ? App.parseTests(topic.test_content) : []) : [];
    var game = topic.game_content && window.GrammarGames
      ? GrammarGames.parse(topic.game_type || 'fill', topic.game_content) : null;

    box.innerHTML =
      '<div class="seg" style="margin-bottom:14px">' +
      ['matn', 'test', 'oyin'].map(function (t) {
        var label = t === 'matn' ? 'Matn' : (t === 'test' ? 'Test' + (tests.length ? ' (' + tests.length + ')' : '') : 'O\'yin');
        return '<button class="' + (TAB === t ? 'active' : '') + '" data-tab="' + t + '">' + label + '</button>';
      }).join('') + '</div>' +
      '<div id="topic-tab"></div>';

    box.querySelectorAll('.seg button').forEach(function (b) {
      b.onclick = function () { TAB = b.getAttribute('data-tab'); renderTopicBody(page, topic, lang, id); };
    });

    var t = App.el('topic-tab');
    if (TAB === 'matn') renderMatnTab(t, page, topic, lang, id);
    else if (TAB === 'test') renderTestTab(t, page, topic, lang, id, tests);
    else renderGameTab(t, page, topic, lang, id, game);
    App.icons(box);
  }

  /* --- Matn (markdown) --- */
  function renderMatnTab(t, page, topic, lang, id) {
    t.innerHTML =
      (topic.content
        ? '<div class="md-content">' + mdToHtml(topic.content) + '</div>'
        : App.empty({ icon: 'book', title: 'Matn hali yo\'q', text: 'Tepadagi ✏ tugma orqali fayl yuklang yoki yozing.' }));

    var menuBtn = App.el('topic-menu-btn');
    if (menuBtn) menuBtn.onclick = function () {
      var html =
        '<button class="list-row" data-act="topicUploadPick"><span class="li-ic" data-icon="upload" data-icon-size="15"></span><div class="li-main"><div class="li-title">' + (topic.content ? '.md fayl almashtirish' : 'Fayl yuklash') + '</div></div></button>' +
        '<button class="list-row" id="mt-edit-sh"><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">' + (topic.content ? 'Tahrirlash' : 'Yozish') + '</div></div></button>' +
        (topic.content
          ? '<button class="list-row" id="mt-dl-sh"><span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">.md faylni yuklab olish</div></div></button>'
          : '');
      var sh = App.sheet(html, { title: topic.name });
      App.icons(sh);
      sh.querySelector('#mt-edit-sh').onclick = function () {
        App.closeSheet();
        openMatnEditor(page, topic, lang, id);
      };
      var dl = sh.querySelector('#mt-dl-sh');
      if (dl) dl.onclick = function () { App.closeSheet(); App.download(topic.name + '.md', topic.content); };
    };
    App.el('topic-file').onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
      var reader = new FileReader();
      reader.onload = function () {
        App.call('upload_topic_content', { id: id, part: 'content', content: reader.result })
          .then(function () { App.closeSheet(); App.toast('✅ Yuklandi'); reloadTopic(page, lang, id); })
          .catch(function (err) { App.toast('⚠️ ' + err.message); });
      };
      reader.readAsText(f);
    };
  }

  function openMatnEditor(page, topic, lang, id) {
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">Markdown: <code># Sarlavha</code>, <code>**qalin**</code>, <code>- ro\'yxat</code>, <code>&gt; iqtibos</code></p>' +
      '<label class="field"><span>Mavzu matni</span><textarea class="textarea" id="mt-text" spellcheck="false">' +
      App.esc(topic.content || '') + '</textarea></label>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="mt-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: 'Matnni tahrirlash', cls: 'editor-sheet' });
    sh.querySelector('#mt-save').onclick = function () {
      App.call('upload_topic_content', { id: id, part: 'content', content: sh.querySelector('#mt-text').value })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); reloadTopic(page, lang, id); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  /* --- Test --- */
  function renderTestTab(t, page, topic, lang, id, tests) {
    t.innerHTML =
      (tests.length
        ? '<button class="btn" id="gt-play" style="margin-bottom:10px"><span data-icon="play" data-icon-size="16"></span>Testni boshlash (' + tests.length + ' savol)</button>'
        : App.empty({ icon: 'edit', title: 'Test yo\'q', text: 'Tepadagi ✏ tugma orqali test qo\'shing.' }));
    App.icons(t);

    if (tests.length) App.el('gt-play').onclick = function () { playTopicTest(page, topic, lang, id, tests); };

    var menuBtn = App.el('topic-menu-btn');
    if (menuBtn) menuBtn.onclick = function () {
      var html =
        '<button class="list-row" id="gt-edit-sh"><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">' + (tests.length ? 'Testni tahrirlash' : 'Test qo\'shish') + '</div></div></button>';
      var sh = App.sheet(html, { title: topic.name + ' — Test' });
      App.icons(sh);
      sh.querySelector('#gt-edit-sh').onclick = function () {
        App.closeSheet();
        openTestEditor(page, topic, lang, id);
      };
    };
  }

  function openTestEditor(page, topic, lang, id) {
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">Testlar bo\'limidagi format bilan bir xil:<br>' +
      '<code>1. Savol / A) variant / B) variant / Javob: A</code> yoki <code>#Savol / - noto\'g\'ri / + to\'g\'ri</code></p>' +
      '<label class="field"><span>Savollar matni</span><textarea class="textarea" id="gt-text" spellcheck="false">' +
      App.esc(topic.test_content || '') + '</textarea></label>' +
      '<p class="muted" id="gt-info" style="font-size:12px;margin:-6px 1px 10px"></p>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="gt-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: 'Mavzu testi', cls: 'editor-sheet' });
    var ta = sh.querySelector('#gt-text'), info = sh.querySelector('#gt-info');
    var upd = function () {
      var n = App.parseTests ? App.parseTests(ta.value).length : 0;
      info.textContent = n ? '✅ ' + n + ' ta savol topildi' : '⚠️ Savol topilmadi';
      info.style.color = n ? 'var(--success)' : 'var(--danger)';
    };
    ta.oninput = upd; upd();
    sh.querySelector('#gt-save').onclick = function () {
      App.call('upload_topic_content', { id: id, part: 'test', content: ta.value })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); reloadTopic(page, lang, id); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  /* Mavzu testini o'ynash */
  function playTopicTest(page, topic, lang, id, tests) {
    var st = { i: 0, good: 0, bad: 0, list: tests };
    function draw() {
      if (st.i >= st.list.length) {
        var pct = Math.round(st.good * 100 / st.list.length);
        page.innerHTML = topbar(topic.name, 'grammar', { lang: lang }) +
          '<div style="text-align:center;padding-top:8px"><div class="res-circle"><span>' + pct + '%</span></div>' +
          '<h2 style="margin:0 0 20px">' + (pct >= 80 ? 'Ajoyib!' : pct >= 50 ? 'Yaxshi' : 'Takrorlang') + '</h2>' +
          '<div class="stat-strip" style="max-width:280px;margin:0 auto 24px">' +
          '<div class="s"><div class="n" style="color:var(--success)">' + st.good + '</div><div class="l">To\'g\'ri</div></div>' +
          '<div class="s"><div class="n" style="color:var(--danger)">' + st.bad + '</div><div class="l">Xato</div></div>' +
          '<div class="s"><div class="n">' + st.list.length + '</div><div class="l">Jami</div></div></div>' +
          '<button class="btn" id="gt-back">Mavzuga qaytish</button></div>';
        App.icons(page);
        App.el('gt-back').onclick = function () { TAB = 'test'; reloadTopic(page, lang, id); };
        if (window.Activity) Activity.mark();
        return;
      }
      var q = st.list[st.i];
      var keys = Object.keys(q.options);
      page.innerHTML = '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="gt-exit"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + (st.i + 1) + ' / ' + st.list.length + '</h1>' +
        '<span class="sub" style="font-weight:700;color:var(--success)">' + st.good + '</span></div>' +
        '<div class="qtext">' + App.mathHtml(q.text) + '</div><div id="gt-opts">' +
        keys.map(function (k) { return '<button class="qopt" data-k="' + k + '"><b>' + k + ')</b> ' + App.mathHtml(q.options[k]) + '</button>'; }).join('') +
        '</div><div id="gt-feed"></div>';
      App.icons(page);
      App.typeset(page);
      App.el('gt-exit').onclick = function () { TAB = 'test'; reloadTopic(page, lang, id); };
      var box = App.el('gt-opts');
      box.querySelectorAll('.qopt').forEach(function (b) {
        b.onclick = function () {
          if (box._done) return; box._done = true;
          var ok = b.getAttribute('data-k') === q.correct;
          b.classList.add(ok ? 'correct' : 'wrong');
          if (!ok) { var c = box.querySelector('[data-k="' + q.correct + '"]'); if (c) c.classList.add('correct'); }
          box.querySelectorAll('.qopt').forEach(function (x) { x.classList.add('disabled'); });
          if (ok) st.good++; else st.bad++;
          App.el('gt-feed').innerHTML = '<div class="qfeed ' + (ok ? 'correct' : 'wrong') + '">' +
            (ok ? '✓ To\'g\'ri' : '✗ To\'g\'ri javob: ' + q.correct) + '</div>';
          setTimeout(function () { st.i++; draw(); }, ok ? 700 : 1500);
        };
      });
    }
    draw();
  }

  /* --- O'yin --- */
  function renderGameTab(t, page, topic, lang, id, game) {
    var gt = topic.game_type || 'fill';
    var label = window.GrammarGames ? GrammarGames.guide[gt].label : gt;
    t.innerHTML =
      (game
        ? '<button class="btn" id="gg-play" style="margin-bottom:10px"><span data-icon="play" data-icon-size="16"></span>O\'ynash — ' + App.esc(label) + '</button>'
        : App.empty({ icon: 'trophy', title: 'O\'yin yo\'q', text: 'Tepadagi ✏ tugma orqali o\'yin qo\'shing.' }));
    App.icons(t);

    if (game) App.el('gg-play').onclick = function () {
      GrammarGames.start(page, game, function () { TAB = 'oyin'; reloadTopic(page, lang, id); });
    };

    var menuBtn = App.el('topic-menu-btn');
    if (menuBtn) menuBtn.onclick = function () {
      var html =
        '<button class="list-row" id="gg-edit-sh"><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">' + (game ? 'O\'yinni tahrirlash' : 'O\'yin qo\'shish') + '</div></div></button>';
      var sh = App.sheet(html, { title: topic.name + ' — O\'yin' });
      App.icons(sh);
      sh.querySelector('#gg-edit-sh').onclick = function () {
        App.closeSheet();
        openGameEditor(page, topic, lang, id);
      };
    };
  }

  function openGameEditor(page, topic, lang, id) {
    var cur = topic.game_type || 'fill';
    var html =
      '<div class="seg" id="gg-types" style="margin-bottom:12px">' +
      ['fill', 'sort', 'match', 'order'].map(function (k) {
        return '<button class="' + (cur === k ? 'active' : '') + '" data-k="' + k + '" style="font-size:11.5px">' +
          App.esc(GrammarGames.guide[k].label) + '</button>';
      }).join('') + '</div>' +
      '<div id="gg-guide"></div>' +
      '<label class="field"><span>O\'yin matni</span><textarea class="textarea" id="gg-text" spellcheck="false">' +
      App.esc(topic.game_content || '') + '</textarea></label>' +
      '<p class="muted" id="gg-info" style="font-size:12px;margin:-6px 1px 10px"></p>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="gg-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: 'Mavzu o\'yini', cls: 'editor-sheet' });
    var ta = sh.querySelector('#gg-text'), info = sh.querySelector('#gg-info');
    var type = cur;

    function drawGuide() {
      var g = GrammarGames.guide[type];
      sh.querySelector('#gg-guide').innerHTML =
        '<div class="gg-help"><b>' + App.esc(g.label) + ' — format</b>' +
        '<p>' + App.esc(g.intro) + '</p>' +
        '<code>' + App.esc(g.fields) + '</code>' +
        '<span class="gg-help-eg">Namuna:</span><pre>' + App.esc(g.example) + '</pre></div>';
      ta.placeholder = g.example;
    }
    function check() {
      var parsed = GrammarGames.parse(type, ta.value);
      var n = !parsed ? 0
        : (type === 'sort' ? parsed.items.length : (type === 'match' ? parsed.pairs.length : parsed.rounds.length));
      info.textContent = n ? '✅ ' + n + ' ta element tayyor' : '⚠️ Format mos emas';
      info.style.color = n ? 'var(--success)' : 'var(--danger)';
    }
    sh.querySelectorAll('#gg-types button').forEach(function (b) {
      b.onclick = function () {
        sh.querySelectorAll('#gg-types button').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active'); type = b.getAttribute('data-k');
        drawGuide(); check();
      };
    });
    ta.oninput = check;
    drawGuide(); check();

    sh.querySelector('#gg-save').onclick = function () {
      App.call('upload_topic_content', { id: id, part: 'game', content: ta.value, game_type: type })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); reloadTopic(page, lang, id); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  App.actions.topicUploadPick = function () { App.el('topic-file').click(); };
})();
