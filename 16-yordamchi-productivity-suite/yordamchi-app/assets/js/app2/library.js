/* Materiallar — Ingliz/Rus tillaridagi Reading/Listening/Writing/Speaking kabi
   bo'limlar uchun CHEKSIZ ICHMA-ICH papkali .md kutubxonasi.

   Bu bo'limlarda test va o'yin YO'Q — faqat papka va matn (foydalanuvchi
   so'rovi: ".md larni o'zim kerakligidek taxlab yuklayman").

   Saqlash: mavjud `language_topics` jadvali qayta ishlatiladi —
     lang    = bo'lim kaliti ('en_reading', 'ru_speaking', ...)
     folder  = TO'LIQ ichma-ich yo'l ('Level 1/Unit 2'), frontenddan ANIQ uzatiladi
     name    = fayl nomi (nom ichida "/" bo'lsa ham buzilmaydi — backend
               `folder` aniq berilganda nomni umuman bo'lmaydi)
     content = .md matni
   Bo'sh papka ham ko'rinib tursin deb har papka uchun MARKER qator yoziladi:
   name = '__folder__' (ro'yxatda ko'rsatilmaydi, faqat papka borligini bildiradi). */
(function () {
  'use strict';

  var FOLDER_MARK = '__folder__';

  /* Bo'lim reyestri — languages.js va boost.js ham shundan foydalanadi.
     Kalitlar `language_topics.lang` ustuniga yoziladi.
     `doc` — fayl bosilganda ochiladigan ko'rinish (standarti `library_doc`).
     Reading bo'limlari `reading_doc`ni ishlatadi: u bir xil `.md` matnini
     o'qiydi, lekin so'z/gap tarjimasi va tinglash bilan (reading.js). */
  var SECTIONS = {
    en_reading:   { n: 'Reading',   parent: 'english', parentName: 'Ingliz tili', ic: 'book', doc: 'reading_doc' },
    en_listening: { n: 'Listening', parent: 'english', parentName: 'Ingliz tili', ic: 'headphones' },
    en_writing:   { n: 'Writing',   parent: 'english', parentName: 'Ingliz tili', ic: 'edit' },
    en_speaking:  { n: 'Speaking',  parent: 'english', parentName: 'Ingliz tili', ic: 'mic' },
    ru_reading:   { n: 'Чтение',      parent: 'russian', parentName: 'Русский язык', ic: 'book', doc: 'reading_doc' },
    ru_listening: { n: 'Аудирование', parent: 'russian', parentName: 'Русский язык', ic: 'headphones' },
    ru_speaking:  { n: 'Говорение',   parent: 'russian', parentName: 'Русский язык', ic: 'mic' },
    ru_writing:   { n: 'Письмо',      parent: 'russian', parentName: 'Русский язык', ic: 'edit' },
    ru_shadowing: { n: 'Шэдоуинг',    parent: 'russian', parentName: 'Русский язык', ic: 'refresh' }
  };
  function secInfo(k) { return SECTIONS[k] || { n: 'Materiallar', parent: 'languages', parentName: '', ic: 'book' }; }

  /* ---------- Yo'l yordamchilari ---------- */
  function joinPath(base, name) { return base ? base + '/' + name : name; }
  function parentPath(p) { var i = String(p || '').lastIndexOf('/'); return i < 0 ? '' : p.slice(0, i); }
  function lastSeg(p) { var i = String(p || '').lastIndexOf('/'); return i < 0 ? p : p.slice(i + 1); }
  /* `path` ning bevosita farzandi bo'lgan papka nomi (bo'lmasa null) */
  function childFolder(path, folderPath) {
    if (path) {
      if (folderPath.indexOf(path + '/') !== 0) return null;
      folderPath = folderPath.slice(path.length + 1);
    }
    if (!folderPath) return null;
    var i = folderPath.indexOf('/');
    return i < 0 ? folderPath : folderPath.slice(0, i);
  }

  /* Tekis ro'yxatdan joriy papkadagi ko'rinishni yig'adi. */
  function viewOf(topics, path) {
    var folders = {}, files = [];
    (topics || []).forEach(function (t) {
      var f = (t.folder || '').trim();
      if (t.name === FOLDER_MARK) {
        // Marker: shu YO'L papka ekanini bildiradi
        var c = childFolder(path, f);
        if (c) folders[c] = folders[c] || { n: c, files: 0, subs: 0 };
        return;
      }
      if (f === path) { files.push(t); return; }
      var ch = childFolder(path, f);
      if (ch) {
        folders[ch] = folders[ch] || { n: ch, files: 0, subs: 0 };
        // Bevosita shu papkadagi fayl bo'lsa — hisoblaymiz
        if (f === joinPath(path, ch)) folders[ch].files++;
        else folders[ch].subs++;
      }
    });
    var list = Object.keys(folders).sort(function (a, b) { return a.localeCompare(b); })
      .map(function (k) { return folders[k]; });
    return { folders: list, files: files };
  }

  function topbar(title, backView, backParams, right) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: backView, p: backParams || {} }) + '\'>' +
      '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(title) + '</h1>' + (right || '') + '</div>';
  }

  /* =========================================================
     VIEW: library — papka brauzeri
     ========================================================= */
  App.view('library', {
    nav: 'languages',
    render: function (page, params) {
      var sec = params.sec || 'en_reading';
      var path = params.path || '';
      var si = secInfo(sec);
      var back = path ? 'library' : si.parent;
      var backP = path ? { sec: sec, path: parentPath(path) } : {};

      page.innerHTML = topbar(path ? lastSeg(path) : si.n, back, backP,
        '<button class="icon-btn ghost" data-act="libNew" data-arg=\'' + App.arg({ sec: sec, path: path }) +
        '\' style="margin-left:auto" aria-label="Qo\'shish"><span data-icon="plus" data-icon-size="20"></span></button>') +
        (path ? '<div class="lib-crumb">' + crumbHtml(sec, path) + '</div>' : '') +
        '<div id="lib-list"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<input type="file" id="lib-files" hidden multiple accept=".md,.markdown,.txt,text/markdown,text/plain">' +
        '<input type="file" id="lib-dir" hidden webkitdirectory directory multiple>';
      App.icons(page);
      bindUploads(sec, path);
      load(sec, path);
    }
  });

  function crumbHtml(sec, path) {
    var parts = path.split('/'), acc = '', out = [];
    out.push('<button class="lib-cr" data-act="go" data-arg=\'' + App.arg({ v: 'library', p: { sec: sec } }) + '\'>' +
      App.esc(secInfo(sec).n) + '</button>');
    parts.forEach(function (p, i) {
      acc = joinPath(acc, p);
      out.push('<span>/</span>');
      if (i === parts.length - 1) out.push('<b>' + App.esc(p) + '</b>');
      else out.push('<button class="lib-cr" data-act="go" data-arg=\'' +
        App.arg({ v: 'library', p: { sec: sec, path: acc } }) + '\'>' + App.esc(p) + '</button>');
    });
    return out.join('');
  }

  function load(sec, path) {
    App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(sec) }).then(function (j) {
      var box = App.el('lib-list'); if (!box) return;
      var v = viewOf(j.topics || [], path);
      if (!v.folders.length && !v.files.length) {
        box.innerHTML = App.empty({
          icon: 'book', title: path ? 'Bo\'sh papka' : 'Hali material yo\'q',
          text: 'Tepadagi + tugmasi bilan papka oching yoki .md fayllarni yuklang.'
        });
        App.icons(box); return;
      }
      var html = v.folders.map(function (f) {
        var sub = [];
        if (f.files) sub.push(f.files + ' ta fayl');
        if (f.subs) sub.push(f.subs + ' ta ichkarida');
        return '<div class="list-row">' +
          '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="archive" data-icon-size="15"></span>' +
          '<button class="li-main li-btn" data-act="go" data-arg=\'' +
          App.arg({ v: 'library', p: { sec: sec, path: joinPath(path, f.n) } }) + '\'>' +
          '<div class="li-title">' + App.esc(f.n) + '</div>' +
          '<div class="li-sub">' + (sub.join(' · ') || 'bo\'sh') + '</div></button>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="libFolderMenu" data-arg=\'' +
          App.arg({ sec: sec, path: path, n: f.n }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
      }).join('');

      if (v.files.length) {
        if (v.folders.length) html += '<div class="list-label">Fayllar</div>';
        var docView = secInfo(sec).doc || 'library_doc';
        html += v.files.map(function (t) {
          return '<div class="list-row">' +
            '<span class="li-ic" data-icon="book" data-icon-size="15"></span>' +
            '<button class="li-main li-btn" data-act="go" data-arg=\'' +
            App.arg({ v: docView, p: { sec: sec, id: t.id } }) + '\'>' +
            '<div class="li-title">' + App.esc(t.name) + '</div>' +
            (t.has_content ? '' : '<div class="li-sub">matn hali yo\'q</div>') + '</button>' +
            '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="libFileMenu" data-arg=\'' +
            App.arg({ sec: sec, path: path, id: t.id, n: t.name }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
        }).join('');
      }
      box.innerHTML = html;
      App.icons(box);
    }).catch(function (e) {
      var box = App.el('lib-list');
      if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  /* ---------- Qo'shish menyusi ---------- */
  App.actions.libNew = function (a) {
    var html =
      '<button class="list-row" data-act="libAddFolder" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="archive" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Yangi papka</div>' +
      '<div class="li-sub">Ichida yana papka ochish mumkin</div></div></button>' +
      '<button class="list-row" id="lib-pick-files">' +
      '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">.md fayllarni yuklash</div>' +
      '<div class="li-sub">Bir vaqtda bir nechtasini tanlash mumkin</div></div></button>' +
      '<button class="list-row" id="lib-pick-dir">' +
      '<span class="li-ic" data-icon="archive" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Butun papkani yuklash</div>' +
      '<div class="li-sub">Kompyuterdagi papka tuzilishi aynan saqlanadi</div></div></button>' +
      '<button class="list-row" data-act="libAddDoc" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Bo\'sh material</div>' +
      '<div class="li-sub">Matnni keyin o\'zingiz yozasiz</div></div></button>' +
      /* Reading bo'limida matn maxsus formatda (so'z/gap tarjimasi bilan)
         yoziladi — foydalanuvchi formatni namunadan ko'rib oladi. */
      ((window.Reading && Reading.isReadingSec(a.sec))
        ? '<button class="list-row" data-act="rdSample" data-arg=\'' + App.arg({ sec: a.sec }) + '\'>' +
          '<span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">Namuna fayl</div>' +
          '<div class="li-sub">So\'z va gap tarjimasi qanday yozilishi</div></div></button>'
        : '');
    var sh = App.sheet(html, { title: 'Qo\'shish' });
    App.icons(sh);
    sh.querySelector('#lib-pick-files').onclick = function () { App.closeSheet(); App.el('lib-files').click(); };
    sh.querySelector('#lib-pick-dir').onclick = function () { App.closeSheet(); App.el('lib-dir').click(); };
  };

  App.actions.libAddFolder = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Yangi papka', label: 'Papka nomi', ok: 'Ochish' }, function (name) {
      name = (name || '').trim().replace(/\//g, '-');   // "/" yo'l ajratgichi — nomda bo'lmaydi
      if (!name) return;
      App.call('add_topic', { lang: a.sec, name: FOLDER_MARK, folder: joinPath(a.path, name) })
        .then(function () { App.go('library', { sec: a.sec, path: joinPath(a.path, name) }); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };

  App.actions.libAddDoc = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Yangi material', label: 'Nomi', ok: 'Qo\'shish' }, function (name) {
      name = (name || '').trim();
      if (!name) return;
      App.call('add_topic', { lang: a.sec, name: name, folder: a.path })
        .then(function (j) { App.go(secInfo(a.sec).doc || 'library_doc', { sec: a.sec, id: j.id }); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };

  /* ---------- Yuklash (ko'p fayl / butun papka) ---------- */
  function readText(file) {
    return new Promise(function (res, rej) {
      var fr = new FileReader();
      fr.onload = function () { res(String(fr.result || '')); };
      fr.onerror = function () { rej(new Error(file.name + ' o\'qilmadi')); };
      fr.readAsText(file);
    });
  }
  function baseName(n) { return String(n).replace(/\.(md|markdown|txt)$/i, ''); }
  function isText(f) { return /\.(md|markdown|txt)$/i.test(f.name); }

  /* Fayllarni KETMA-KET yuklaydi (serverni bir vaqtda ko'p so'rov bilan
     bosmaslik uchun) va jarayonni ko'rsatib turadi. */
  function uploadAll(sec, basePath, files, useRelPath) {
    var list = Array.prototype.slice.call(files).filter(isText);
    if (!list.length) { App.toast('.md fayl topilmadi'); return; }

    var sh = App.sheet('<div id="lib-up" style="text-align:center;padding:6px 0 12px">' +
      '<div class="spinner" style="margin:0 auto 12px"></div>' +
      '<b id="lib-up-n">0 / ' + list.length + '</b>' +
      '<div class="muted" id="lib-up-f" style="font-size:12px;margin-top:6px">Boshlanmoqda...</div></div>',
      { title: 'Yuklanmoqda' });
    App.icons(sh);

    var done = 0, failed = 0, madeFolders = {};
    function step(i) {
      if (i >= list.length) {
        App.closeSheet();
        App.toast(failed ? ('✅ ' + done + ' ta yuklandi, ' + failed + ' tasi bo\'lmadi')
                         : ('✅ ' + done + ' ta material yuklandi'));
        App.go('library', { sec: sec, path: basePath });
        return;
      }
      var f = list[i];
      var nEl = App.el('lib-up-n'), fEl = App.el('lib-up-f');
      if (nEl) nEl.textContent = (i + 1) + ' / ' + list.length;
      if (fEl) fEl.textContent = f.name;

      // Papka yo'li: butun papka yuklashda kompyuterdagi tuzilish saqlanadi
      var rel = useRelPath ? (f.webkitRelativePath || f.name) : f.name;
      var dirs = rel.split('/').slice(0, -1).filter(Boolean);
      var folder = basePath;
      dirs.forEach(function (d) { folder = joinPath(folder, d); });

      // Har papka uchun marker (bir marta)
      var ensure = Promise.resolve();
      if (folder && folder !== basePath && !madeFolders[folder]) {
        madeFolders[folder] = true;
        var acc = basePath;
        dirs.forEach(function (d) {
          acc = joinPath(acc, d);
          var p = acc;
          ensure = ensure.then(function () {
            return App.call('add_topic', { lang: sec, name: FOLDER_MARK, folder: p }).catch(function () {});
          });
        });
      }

      ensure
        .then(function () { return readText(f); })
        .then(function (text) {
          return App.call('add_topic', { lang: sec, name: baseName(f.name), folder: folder })
            .then(function (j) {
              return App.call('upload_topic_content', { id: j.id, part: 'content', content: text });
            });
        })
        .then(function () { done++; })
        .catch(function () { failed++; })
        .then(function () { step(i + 1); });
    }
    step(0);
  }

  function bindUploads(sec, path) {
    var fEl = App.el('lib-files'), dEl = App.el('lib-dir');
    if (fEl) fEl.onchange = function () { if (fEl.files.length) uploadAll(sec, path, fEl.files, false); fEl.value = ''; };
    if (dEl) dEl.onchange = function () { if (dEl.files.length) uploadAll(sec, path, dEl.files, true); dEl.value = ''; };
  }

  /* ---------- Papka / fayl menyusi ---------- */
  App.actions.libFolderMenu = function (a) {
    var full = joinPath(a.path, a.n);
    var html =
      '<button class="list-row" data-act="libFolderRename" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Nomini o\'zgartirish</div>' +
      '<div class="li-sub">Ichidagilar ham ko\'chadi</div></div></button>' +
      '<button class="list-row" data-act="libFolderDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)">' +
      '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title" style="color:var(--danger)">Papkani o\'chirish</div>' +
      '<div class="li-sub">Ichidagi hamma narsa bilan</div></div></button>';
    App.sheet(html, { title: full });
  };

  /* Papka amallari butun SHOXNI qamraydi: `folder` ustuni yo'l bo'lgani uchun
     "Level 1" va "Level 1/..." bilan boshlanadigan hamma qator tegishli. */
  function branchRows(topics, full) {
    return (topics || []).filter(function (t) {
      var f = (t.folder || '').trim();
      return f === full || f.indexOf(full + '/') === 0;
    });
  }
  function eachSeq(items, fn) {
    return items.reduce(function (p, it) { return p.then(function () { return fn(it); }); }, Promise.resolve());
  }

  App.actions.libFolderRename = function (a) {
    App.closeSheet();
    var full = joinPath(a.path, a.n);
    App.prompt({ title: 'Papka nomi', label: 'Yangi nom', value: a.n, ok: 'Saqlash' }, function (name) {
      name = (name || '').trim().replace(/\//g, '-');
      if (!name || name === a.n) return;
      var next = joinPath(a.path, name);
      App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(a.sec) }).then(function (j) {
        var rows = branchRows(j.topics, full);
        return eachSeq(rows, function (t) {
          var f = (t.folder || '').trim();
          var moved = next + f.slice(full.length);
          return App.call('rename_topic', { id: t.id, name: t.name, folder: moved });
        });
      }).then(function () { App.go('library', { sec: a.sec, path: a.path }); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };

  App.actions.libFolderDelete = function (a) {
    var full = joinPath(a.path, a.n);
    App.confirm('"' + a.n + '" papkasi va ichidagi BARCHA materiallar o\'chiriladi.', function () {
      App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(a.sec) }).then(function (j) {
        return eachSeq(branchRows(j.topics, full), function (t) {
          return App.call('delete_topic', { id: t.id });
        });
      }).then(function () {
        App.closeSheet(); App.toast('O\'chirildi');
        App.go('library', { sec: a.sec, path: a.path });
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  App.actions.libFileMenu = function (a) {
    var html =
      '<button class="list-row" data-act="libFileRename" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="libFileDownload" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">.md faylni yuklab olish</div>' +
      '<div class="li-sub">Kompyuterga saqlab qo\'yish</div></div></button>' +
      '<button class="list-row" data-act="libFileDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)">' +
      '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
    App.sheet(html, { title: a.n });
  };
  App.actions.libFileRename = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Nomini o\'zgartirish', label: 'Yangi nom', value: a.n, ok: 'Saqlash' }, function (name) {
      name = (name || '').trim(); if (!name) return;
      App.call('rename_topic', { id: a.id, name: name, folder: a.path })
        .then(function () { App.go('library', { sec: a.sec, path: a.path }); })
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };
  App.actions.libFileDelete = function (a) {
    App.confirm('"' + a.n + '" o\'chiriladi.', function () {
      App.call('delete_topic', { id: a.id }).then(function () {
        App.closeSheet(); App.go('library', { sec: a.sec, path: a.path });
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* =========================================================
     VIEW: library_doc — bitta material (matn). Test/o'yin YO'Q.
     ========================================================= */
  App.view('library_doc', {
    nav: 'languages',
    render: function (page, params) {
      var sec = params.sec || 'en_reading', id = params.id;
      page.innerHTML = topbar('Material', 'library', { sec: sec },
        '<button class="icon-btn ghost" id="lib-doc-menu" style="margin-left:auto"><span data-icon="edit" data-icon-size="18"></span></button>') +
        '<div id="lib-doc"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<input type="file" id="lib-doc-file" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">';
      App.icons(page);
      loadDoc(page, sec, id);
    }
  });

  function loadDoc(page, sec, id) {
    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(id) }).then(function (t) {
      var box = App.el('lib-doc'); if (!box) return;
      var folder = (t.folder || '').trim();
      var h1 = page.querySelector('.topbar h1');
      if (h1) h1.textContent = t.name;
      var back = page.querySelector('.topbar .icon-btn');
      if (back) back.setAttribute('data-arg', App.arg({ v: 'library', p: { sec: sec, path: folder } }));

      box.innerHTML = (folder ? '<div class="lib-crumb" style="margin-bottom:12px">' + crumbHtml(sec, folder) + '</div>' : '') +
        (t.content
          ? '<div class="md-content">' + App.md(t.content) + '</div>'
          : App.empty({ icon: 'book', title: 'Matn hali yo\'q', text: 'Tepadagi ✏ tugma orqali .md yuklang yoki yozing.' }));
      App.icons(box);
      if (App.typeset) App.typeset(box);

      App.el('lib-doc-menu').onclick = function () {
        var html =
          '<button class="list-row" id="ld-up"><span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + (t.content ? '.md faylni almashtirish' : '.md fayl yuklash') + '</div></div></button>' +
          '<button class="list-row" id="ld-ed"><span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + (t.content ? 'Tahrirlash' : 'Yozish') + '</div></div></button>' +
          (t.content
            ? '<button class="list-row" id="ld-dl"><span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
              '<div class="li-main"><div class="li-title">.md faylni yuklab olish</div>' +
              '<div class="li-sub">Kompyuterga saqlab qo\'yish</div></div></button>'
            : '');
        var sh = App.sheet(html, { title: t.name });
        App.icons(sh);
        sh.querySelector('#ld-up').onclick = function () { App.closeSheet(); App.el('lib-doc-file').click(); };
        sh.querySelector('#ld-ed').onclick = function () { App.closeSheet(); editDoc(page, sec, id, t); };
        var dl = sh.querySelector('#ld-dl');
        if (dl) dl.onclick = function () { App.closeSheet(); downloadTopic(t); };
      };
      App.el('lib-doc-file').onchange = function (e) {
        var f = e.target.files[0]; if (!f) return;
        readText(f).then(function (text) {
          return App.call('upload_topic_content', { id: id, part: 'content', content: text });
        }).then(function () { App.toast('✅ Yuklandi'); loadDoc(page, sec, id); })
          .catch(function (err) { App.toast('⚠️ ' + err.message); });
      };
    }).catch(function (e) {
      var box = App.el('lib-doc');
      if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  /* Tahrirlash oynasi ATAYLAB katta (`editor-sheet`): .md matnlar uzun
     bo'ladi, kichik oynada tahrirlash qiyin edi. Matn maydoni ekran
     balandligiga moslashadi (app.css `.editor-sheet .textarea`). */
  function editDoc(page, sec, id, t) {
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">Markdown: <code># Sarlavha</code>, <code>**qalin**</code>, <code>- ro\'yxat</code></p>' +
      '<label class="field"><span>Matn</span><textarea class="textarea" id="ld-text" spellcheck="false">' +
      App.esc(t.content || '') + '</textarea></label>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="ld-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: t.name, cls: 'editor-sheet' });
    sh.querySelector('#ld-save').onclick = function () {
      App.call('upload_topic_content', { id: id, part: 'content', content: sh.querySelector('#ld-text').value })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); loadDoc(page, sec, id); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  /* ---------- .md yuklab olish ---------- */
  function downloadTopic(t) {
    if (!t || !t.content) { App.toast('Bu materialda matn yo\'q'); return; }
    App.download(t.name + '.md', t.content);
  }
  App.actions.libFileDownload = function (a) {
    App.closeSheet();
    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(a.id) })
      .then(downloadTopic)
      .catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* Tashqi modullar uchun (languages.js ro'yxati, boost.js vazifa tanlagichi) */
  window.Library = {
    SECTIONS: SECTIONS,
    FOLDER_MARK: FOLDER_MARK,
    info: secInfo,
    viewOf: viewOf,
    joinPath: joinPath,
    /* Bo'lim daraxtini olib keladi (tekis ro'yxat) */
    topics: function (sec) {
      return App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(sec) })
        .then(function (j) { return j.topics || []; })
        .catch(function () { return []; });
    },
    /* Bo'limdagi BARCHA materiallar (papka markerlarisiz) — to'liq yo'li bilan */
    allDocs: function (sec) {
      return window.Library.topics(sec).then(function (list) {
        return list.filter(function (t) { return t.name !== FOLDER_MARK; });
      });
    }
  };
})();
