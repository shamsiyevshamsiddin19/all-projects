/* Qoidalar — o'zi uchun yozib qo'yilgan qoidalar/tamoyillar bo'limi.
   Ilgari Arxiv ichida bitta tab edi; endi alohida bo'lim va kengaytirilgan:
     · kategoriyalar (guruhlash + filtr)
     · muhimlar tepada (pin)
     · "Bugungi qoida" — har kuni bittasi almashib turadi
     · matn bo'yicha qidiruv
     · bir nechta .md faylni birdan yuklash
     · ko'rilganlar hisobi (qaysi qoidaga qaytib turasiz)

   Saqlash kaliti ATAYLAB o'zgartirilmadi — `arxiv_qoidalar` (localStorage,
   remote-storage orqali server bilan sinxron). Shu sabab eski qoidalar
   yo'qolmaydi, faqat yangi maydonlar (cat/pin/views) qo'shiladi. */
(function () {
  'use strict';

  var KEY = 'arxiv_qoidalar';
  var UI = { q: '', curFolder: 'default', curSection: 'default', defaulted: false };

  function idEq(a, b) { return String(a) === String(b); }
  function sectionsOf(data, folderId) {
    return (data.sections || []).filter(function (s) { return idEq(s.folder_id, folderId); });
  }

  function read() {
    var raw;
    try { raw = JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch (e) { raw = []; }

    if (Array.isArray(raw)) {
      // Migratsiya: massivdan yangi struktura
      var folders = [{ id: 'default', name: 'Umumiy' }];
      var fMap = {};
      raw.forEach(function (r) {
        var c = (r.cat || '').trim();
        if (c) {
          if (!fMap[c]) {
            fMap[c] = makeId();
            folders.push({ id: fMap[c], name: c });
          }
          r.folder_id = fMap[c];
          r.section_id = 'default';
        } else {
          r.folder_id = 'default';
          r.section_id = 'default';
        }
      });
      raw = { folders: folders, sections: [], rules: raw };
      write(raw);
    }
    
    // UI state ini bitta marta boshlang'ich sozlash
    if (!UI.defaulted) {
      UI.defaulted = true;
      var customFolders = (raw.folders || []).filter(function (f) { return !idEq(f.id, 'default'); });
      if (customFolders.length) {
        UI.curFolder = customFolders[0].id;
        var secs = sectionsOf(raw, UI.curFolder);
        if (secs.length) UI.curSection = secs[0].id;
      }
    }
    return raw;
  }
  function write(data) { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) {} }
  function makeId() { return 'rule_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8); }

  function matches(it, q) {
    if (!q) return true;
    return [it.title, it.text].filter(Boolean).join(' ').toLowerCase().indexOf(q.toLowerCase()) >= 0;
  }

  /* Ro'yxat tartibi: avval muhimlar (pin), keyin qo'shilish tartibida. */
  function sorted(list) {
    return list.slice().sort(function (a, b) {
      if (!!b.pin !== !!a.pin) return b.pin ? 1 : -1;
      return 0;
    });
  }

  /* "Bugungi qoida" — kun bo'yicha barqaror tanlov: bir kun ichida
     sahifani necha marta ochsangiz ham O'ZGARMAYDI, ertasiga almashadi. */
  function ruleOfDay(list) {
    if (!list.length) return null;
    var d = new Date();
    var key = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
    return list[key % list.length];
  }

  function preview(text) {
    return String(text || '').replace(/^#+\s*/gm, '').replace(/[*_>`|-]/g, ' ')
      .replace(/\s+/g, ' ').trim().slice(0, 90);
  }

  function rulesOf(data, folderId, sectionId) {
    return (data.rules || []).filter(function (r) {
      return idEq(r.folder_id, folderId) && idEq(r.section_id, sectionId);
    });
  }

  App.view('qoidalar', {
    nav: 'qoidalar',
    render: function (page) {
      var all = read();
      var folders = all.folders || [];

      var folderChips = folders.filter(function (f) { return !idEq(f.id, 'default'); }).map(function (f) {
        return '<button class="chip-btn ' + (idEq(f.id, UI.curFolder) ? 'active' : '') +
          '" data-act="qoidaFolder" data-arg=\'' + App.arg({ id: f.id }) + '\'>' + App.esc(f.name) + '</button>';
      }).join('');

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>Qoidalar</h1>' +
        '<button class="icon-btn ghost" data-act="qoidaBackup" style="margin-left:auto" aria-label="Zaxira"><span data-icon="upload" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="qoidaAdd" aria-label="Qo\'shish"><span data-icon="plus" data-icon-size="20"></span></button></div>' +
        '<div id="qo-day"></div>' +
        '<input class="input" id="qo-q" placeholder="Qidirish (nom va matn bo\'yicha)..." style="margin-bottom:10px" value="' + App.esc(UI.q) + '">' +
        '<div class="between" style="margin-bottom:10px"><div class="flex" style="gap:6px;flex-wrap:wrap">' + folderChips +
        '</div><button class="icon-btn ghost" data-act="qoidaManage" aria-label="Jild va bo\'limlar" style="width:28px;height:28px;flex-shrink:0"><span data-icon="edit" data-icon-size="14"></span></button></div>' +
        '<div id="qo-list"></div>' +
        '<input type="file" id="qo-files" hidden multiple accept=".md,.markdown,.txt,text/markdown,text/plain">';
      App.icons(page);

      App.el('qo-q').oninput = function () { UI.q = this.value; renderList(); };
      App.el('qo-files').onchange = function () {
        if (this.files && this.files.length) importFiles(this.files);
        this.value = '';
      };
      renderDayCard();
      renderList();
    }
  });

  App.actions.qoidaFolder = function (a) {
    UI.curFolder = a.id; 
    var all = read();
    var secs = sectionsOf(all, a.id);
    UI.curSection = secs.length ? secs[0].id : 'default';
    App.reload(); 
  };
  App.actions.qoidaSection = function (a) { UI.curSection = a.id; App.reload(); };

  function renderDayCard() {
    var box = App.el('qo-day'); if (!box) return;
    var all = read();
    var rules = all.rules || [];
    if (rules.length < 2) { box.innerHTML = ''; return; }
    var r = ruleOfDay(rules);
    if (!r) { box.innerHTML = ''; return; }
    box.innerHTML =
      '<button class="card-tap" data-act="qoidaView" data-arg=\'' + App.arg({ id: r.id }) + '\' ' +
      'style="display:block;width:100%;text-align:left;background:var(--accent-soft);border:none;' +
      'border-radius:14px;padding:13px 14px;margin-bottom:14px">' +
      '<div style="font-size:10.5px;font-weight:800;letter-spacing:.5px;text-transform:uppercase;color:var(--accent)">Bugungi qoida</div>' +
      '<div style="font-size:14.5px;font-weight:700;margin-top:5px">' + App.esc(r.title) + '</div>' +
      '<div style="font-size:11.5px;color:var(--hint);margin-top:3px">' + App.esc(preview(r.text)) + '</div>' +
      '</button>';
  }

  function renderList() {
    var box = App.el('qo-list'); if (!box) return;
    var q = (UI.q || '').trim();
    var all = read();
    var secs = sectionsOf(all, UI.curFolder);

    var sectionChips = '';
    if (secs.length) {
      sectionChips = secs.map(function (s) {
          return '<button class="chip-btn sect ' + (idEq(s.id, UI.curSection) ? 'active' : '') +
            '" data-act="qoidaSection" data-arg=\'' + App.arg({ id: s.id }) + '\'>' + App.esc(s.name) + '</button>';
        }).join('');
    }

    var listHtml = '';
    if (idEq(UI.curSection, 'default')) {
      var groups = [];
      groups.push({ name: '', items: rulesOf(all, UI.curFolder, 'default') });
      secs.forEach(function (s) { groups.push({ name: s.name, items: rulesOf(all, UI.curFolder, s.id) }); });
      listHtml = groups.filter(function (gr) { return gr.items.length; }).map(function (gr) {
        return (gr.name ? '<div class="muted" style="grid-column:1/-1;font-size:12px;font-weight:700;margin:6px 2px 0">' + App.esc(gr.name) + '</div>' : '') +
          gr.items.filter(function(r) { return matches(r, q); }).map(ruleRow).join('');
      }).join('');
    } else {
      var items = rulesOf(all, UI.curFolder, UI.curSection);
      if (secs.length && idEq(UI.curSection, secs[0].id)) {
        items = rulesOf(all, UI.curFolder, 'default').concat(items);
      }
      listHtml = items.filter(function(r) { return matches(r, q); }).map(ruleRow).join('');
    }

    box.innerHTML =
      (sectionChips ? '<div class="flex" style="gap:5px;flex-wrap:wrap;margin-bottom:10px">' + sectionChips + '</div>' : '') +
      (listHtml || App.empty({
        icon: 'file',
        title: q ? 'Topilmadi' : 'Hali qoida yo\'q',
        text: q ? 'Boshqa so\'z bilan qidirib ko\'ring.' : 'Tepadagi + tugmasi bilan qo\'shing yoki .md fayllarni yuklang.'
      }));
    App.icons(box);
  }

  function ruleRow(it) {
    var sub = [];
    if (it.views) sub.push(it.views + ' marta ochilgan');
    return '<div class="list-row">' +
      '<span class="li-ic"' + (it.pin ? ' style="background:var(--warn-soft,var(--accent-soft));color:var(--warn)"' : '') + '>' +
      '<span data-icon="' + (it.pin ? 'star' : 'file') + '" data-icon-size="15"></span></span>' +
      '<button class="li-main li-btn" data-act="qoidaView" data-arg=\'' + App.arg({ id: it.id }) + '\'>' +
      '<div class="li-title">' + App.esc(it.title) + '</div>' +
      '<div class="li-sub">' + App.esc(sub.join(' · ') || preview(it.text)) + '</div></button>' +
      '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="qoidaPin" data-arg=\'' +
      App.arg({ id: it.id }) + '\' aria-label="Muhim"><span data-icon="star" data-icon-size="14"' +
      (it.pin ? ' style="color:var(--warn)"' : '') + '></span></button></div>';
  }

  App.actions.qoidaPin = function (a) {
    var arr = read();
    var i = arr.rules.findIndex(function (x) { return x.id === a.id; });
    if (i < 0) return;
    arr.rules[i].pin = !arr.rules[i].pin;
    write(arr);
    renderList();
  };

  /* ---------- Jild/bo'lim boshqaruvi ---------- */
  App.actions.qoidaManage = function () {
    var all = read();
    var html =
      '<div class="btn-row" style="margin-bottom:14px"><button class="btn sec" data-act="qoidaAddFolder">+ Jild</button>' +
      '<button class="btn sec" data-act="qoidaAddSection">+ Bo\'lim</button></div>' +
      '<div class="list-label" style="margin-top:2px">Jildlar</div>' +
      ((all.folders || []).filter(function (f) { return !idEq(f.id, 'default'); }).map(function (f) {
        return '<div class="list-row"><div class="li-main"><div class="li-title">' + App.esc(f.name) + '</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="qoidaDelFolder" data-arg=\'' + App.arg({ id: f.id }) + '\'><span data-icon="trash" data-icon-size="15"></span></button></div>';
      }).join('') || '<p class="muted" style="font-size:13px;margin:2px">Jild yo\'q</p>') +
      '<div class="list-label">Bo\'limlar (joriy jild)</div>' +
      (sectionsOf(all, UI.curFolder).map(function (s) {
        return '<div class="list-row"><div class="li-main"><div class="li-title">' + App.esc(s.name) + '</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="qoidaDelSection" data-arg=\'' + App.arg({ id: s.id }) + '\'><span data-icon="trash" data-icon-size="15"></span></button></div>';
      }).join('') || '<p class="muted" style="font-size:13px;margin:2px">Bo\'lim yo\'q</p>');
    App.sheet(html, { title: 'Jild va bo\'limlar' });
  };
  App.actions.qoidaAddFolder = function () {
    App.prompt({ title: 'Yangi jild', label: 'Jild nomi' }, function (name) {
      if (!name) return;
      var all = read();
      all.folders.push({ id: makeId(), name: name });
      write(all);
      App.closeSheet(); App.reload();
    });
  };
  App.actions.qoidaAddSection = function () {
    if (idEq(UI.curFolder, 'default')) return App.toast('Avval jild tanlang yoki yarating');
    App.prompt({ title: 'Yangi bo\'lim', label: 'Bo\'lim nomi' }, function (name) {
      if (!name) return;
      var all = read();
      all.sections.push({ id: makeId(), folder_id: UI.curFolder, name: name });
      write(all);
      App.closeSheet(); App.reload();
    });
  };
  App.actions.qoidaDelFolder = function (a) {
    App.confirm('Jild va uning ichidagi qoidalar umuman o\'chib ketadi!', function () {
      var all = read();
      all.folders = all.folders.filter(function(f) { return !idEq(f.id, a.id); });
      all.sections = all.sections.filter(function(s) { return !idEq(s.folder_id, a.id); });
      all.rules = all.rules.filter(function(r) { return !idEq(r.folder_id, a.id); });
      if (idEq(UI.curFolder, a.id)) { UI.curFolder = 'default'; UI.curSection = 'default'; }
      write(all);
      App.closeSheet(); App.reload();
    }, { danger: true, yes: 'O\'chirish' });
  };
  App.actions.qoidaDelSection = function (a) {
    App.confirm('Bo\'lim va undagi qoidalar o\'chadi!', function () {
      var all = read();
      all.sections = all.sections.filter(function(s) { return !idEq(s.id, a.id); });
      all.rules = all.rules.filter(function(r) { return !idEq(r.section_id, a.id); });
      if (idEq(UI.curSection, a.id)) UI.curSection = 'default';
      write(all);
      App.closeSheet(); App.reload();
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Qo'shish ---------- */
  App.actions.qoidaAdd = function () {
    var html =
      '<button class="list-row" id="qo-pick" style="margin-bottom:12px">' +
      '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">.md fayllarni yuklash</div>' +
      '<div class="li-sub">Bir vaqtda bir nechtasini tanlash mumkin — har biri alohida qoida bo\'ladi</div></div></button>' +
      '<label class="field"><span>Sarlavha</span><input class="input" id="qo-t"></label>' +
      '<label class="field"><span>Matn (Markdown)</span>' +
      '<textarea class="textarea" id="qo-x" rows="8" placeholder="# Qoida\n\n- Birinchi band\n- Ikkinchi band"></textarea></label>' +
      '<button class="btn" id="qo-save">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Yangi qoida' });
    App.icons(sh);
    sh.querySelector('#qo-pick').onclick = function () { App.closeSheet(); App.el('qo-files').click(); };
    sh.querySelector('#qo-save').onclick = function () {
      var text = sh.querySelector('#qo-x').value;
      if (!text.trim()) return App.toast('Matn bo\'sh bo\'lmasin');
      var title = sh.querySelector('#qo-t').value.trim() || preview(text).slice(0, 40) || 'Nomsiz';
      var all = read();
      all.rules.unshift({
        id: makeId(), title: title, text: text,
        folder_id: UI.curFolder, section_id: UI.curSection,
        pin: false, views: 0, created_at: new Date().toISOString()
      });
      write(all); App.closeSheet(); App.reload();
    };
  };

  /* Ko'p .md faylni birdan qoida qilib qo'shish — fayl nomi sarlavha bo'ladi. */
  function importFiles(files) {
    var list = Array.prototype.slice.call(files)
      .filter(function (f) { return /\.(md|markdown|txt)$/i.test(f.name); });
    if (!list.length) return App.toast('.md fayl topilmadi');
    var all = read(), done = 0;
    list.forEach(function (f) {
      var rd = new FileReader();
      rd.onload = function () {
        all.rules.unshift({
          id: makeId(), title: f.name.replace(/\.(md|markdown|txt)$/i, ''),
          text: String(rd.result || ''), folder_id: UI.curFolder, section_id: UI.curSection,
          pin: false, views: 0, created_at: new Date().toISOString()
        });
        if (++done === list.length) { write(all); App.toast('✅ ' + done + ' ta qoida qo\'shildi'); App.reload(); }
      };
      rd.onerror = function () { if (++done === list.length) { write(all); App.reload(); } };
      rd.readAsText(f);
    });
  }

  /* ---------- Bitta qoida ---------- */
  App.actions.qoidaView = function (a) { App.go('qoida_doc', { id: a.id }); };

  App.view('qoida_doc', {
    nav: 'qoidalar',
    render: function (page, params) {
      var all = read();
      var arr = all.rules;
      var i = arr.findIndex(function (x) { return x.id === params.id; });
      if (i < 0) { App.go('qoidalar'); return; }
      // Ochilishlar hisobi — qaysi qoidaga tez-tez qaytishingiz ko'rinsin
      arr[i].views = (+arr[i].views || 0) + 1;
      write(all);
      var it = arr[i];
      var fObj = (all.folders || []).find(function(f) { return idEq(f.id, it.folder_id); });
      var fName = fObj && !idEq(fObj.id, 'default') ? fObj.name : '';

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"qoidalar"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(it.title) + '</h1>' +
        '<button class="icon-btn ghost" data-act="qoidaPinDoc" data-arg=\'' + App.arg({ id: it.id }) + '\' style="margin-left:auto" aria-label="Muhim">' +
        '<span data-icon="star" data-icon-size="18"' + (it.pin ? ' style="color:var(--warn)"' : '') + '></span></button>' +
        '<button class="icon-btn ghost" id="qo-menu" aria-label="Menyu"><span data-icon="edit" data-icon-size="18"></span></button></div>' +
        (fName ? '<div class="list-label" style="margin-top:0">' + App.esc(fName) + '</div>' : '') +
        '<div class="md-content">' + App.md(it.text) + '</div>';
      App.icons(page);
      if (App.typeset) App.typeset(page);

      App.el('qo-menu').onclick = function () {
        var html =
          '<button class="list-row" data-act="qoidaEdit" data-arg=\'' + App.arg({ id: it.id }) + '\'>' +
          '<span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Tahrirlash</div></div></button>' +
          '<button class="list-row" data-act="qoidaCopy" data-arg=\'' + App.arg({ id: it.id }) + '\'>' +
          '<span class="li-ic" data-icon="copy" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nusxalash</div></div></button>' +
          '<button class="list-row" data-act="qoidaDelete" data-arg=\'' + App.arg({ id: it.id }) + '\' style="color:var(--danger)">' +
          '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
        App.icons(App.sheet(html, { title: it.title }));
      };
    }
  });

  App.actions.qoidaPinDoc = function (a) { App.actions.qoidaPin(a); App.reload(); };

  App.actions.qoidaEdit = function (a) {
    App.closeSheet();
    var all = read(), it = all.rules.filter(function (x) { return x.id === a.id; })[0];
    if (!it) return;
    
    var html =
      '<button class="list-row" id="qo-rep" style="margin-bottom:12px">' +
      '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">.md fayl bilan almashtirish</div>' +
      '<div class="li-sub" id="qo-rep-i">Mavjud matn yangisi bilan almashadi</div></div></button>' +
      '<input type="file" id="qo-rep-f" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">' +
      '<label class="field"><span>Sarlavha</span><input class="input" id="qo-t2" value="' + App.esc(it.title) + '"></label>' +
      '<label class="field"><span>Matn (Markdown)</span><textarea class="textarea" id="qo-x2" rows="12"></textarea></label>' +
      '<button class="btn" id="qo-u2">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Tahrirlash' });
    App.icons(sh);
    sh.querySelector('#qo-x2').value = it.text;
    sh.querySelector('#qo-rep').onclick = function () { sh.querySelector('#qo-rep-f').click(); };
    sh.querySelector('#qo-rep-f').onchange = function () {
      var f = this.files && this.files[0]; if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        sh.querySelector('#qo-x2').value = String(rd.result || '');
        var i2 = sh.querySelector('#qo-rep-i');
        if (i2) i2.textContent = f.name + ' · ' + Math.max(1, Math.round(f.size / 1024)) + ' KB';
      };
      rd.readAsText(f);
    };
    sh.querySelector('#qo-u2').onclick = function () {
      var text = sh.querySelector('#qo-x2').value;
      if (!text.trim()) return App.toast('Matn bo\'sh bo\'lmasin');
      var cur = read();
      var ix = cur.rules.findIndex(function (x) { return x.id === a.id; });
      if (ix < 0) return;
      cur.rules[ix].title = sh.querySelector('#qo-t2').value.trim() || cur.rules[ix].title;
      cur.rules[ix].text = text;
      write(cur); App.closeSheet(); App.reload();
    };
  };

  App.actions.qoidaCopy = function (a) {
    var it = read().rules.filter(function (x) { return x.id === a.id; })[0]; if (!it) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(it.text)
        .then(function () { App.toast('✅ Nusxalandi'); })
        .catch(function () { App.toast('⚠️ Nusxalab bo\'lmadi'); });
    } else App.toast('⚠️ Brauzer qo\'llamaydi');
  };

  App.actions.qoidaDelete = function (a) {
    App.closeSheet();
    App.confirm('Bu qoida o\'chiriladi.', function () {
      var all = read();
      all.rules = all.rules.filter(function (x) { return x.id !== a.id; });
      write(all);
      App.go('qoidalar');
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Zaxira ---------- */
  App.actions.qoidaBackup = function () {
    var html =
      '<button class="list-row" data-act="qoidaExport">' +
      '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Zaxira faylini yuklab olish</div>' +
      '<div class="li-sub">Barcha qoidalar — JSON</div></div></button>' +
      '<button class="list-row" id="qo-imp">' +
      '<span class="li-ic" data-icon="refresh" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Fayldan qo\'shish</div>' +
      '<div class="li-sub">Zaxira JSON yoki .md fayllar</div></div></button>' +
      '<input type="file" id="qo-imp-f" hidden accept="application/json,.md,.markdown,.txt">';
    var sh = App.sheet(html, { title: 'Zaxira' });
    App.icons(sh);
    sh.querySelector('#qo-imp').onclick = function () { sh.querySelector('#qo-imp-f').click(); };
    sh.querySelector('#qo-imp-f').onchange = function () {
      var f = this.files && this.files[0]; if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        var txt = String(rd.result || '');
        if (/\.json$/i.test(f.name)) {
          try {
            var data = JSON.parse(txt);
            var incomingRules = [];
            var incomingFolders = [];
            var incomingSections = [];
            if (Array.isArray(data)) {
              incomingRules = data;
            } else if (data.rules) {
              incomingRules = data.rules;
              incomingFolders = data.folders || [];
              incomingSections = data.sections || [];
            } else {
              incomingRules = data.rule || data.qoidalar || [];
            }
            if (!Array.isArray(incomingRules) || !incomingRules.length) throw new Error('bo\'sh');
            
            var cur = read(), have = {};
            cur.rules.forEach(function (x) { have[x.id] = true; });
            incomingRules.forEach(function (x) { if (x && x.id && !have[x.id]) cur.rules.push(x); });
            
            var haveF = {}; cur.folders.forEach(function (f) { haveF[f.id] = true; });
            incomingFolders.forEach(function (f) { if (f && f.id && !haveF[f.id]) cur.folders.push(f); });
            
            var haveS = {}; cur.sections.forEach(function (s) { haveS[s.id] = true; });
            incomingSections.forEach(function (s) { if (s && s.id && !haveS[s.id]) cur.sections.push(s); });
            
            write(cur); App.closeSheet(); App.toast('✅ Tiklandi'); App.reload();
          } catch (e) { App.toast('⚠️ Fayl noto\'g\'ri'); }
        } else {
          var all = read();
          all.rules.unshift({ id: makeId(), title: f.name.replace(/\.(md|markdown|txt)$/i, ''), text: txt, folder_id: UI.curFolder, section_id: UI.curSection, pin: false, views: 0, created_at: new Date().toISOString() });
          write(all); App.closeSheet(); App.toast('✅ Qo\'shildi'); App.reload();
        }
      };
      rd.readAsText(f);
    };
  };
  App.actions.qoidaExport = function () {
    var all = read();
    var blob = new Blob([JSON.stringify({ folders: all.folders, sections: all.sections, rules: all.rules, exported_at: new Date().toISOString() }, null, 2)],
      { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'yordamchi_qoidalar.json';
    document.body.appendChild(a); a.click(); a.remove();
    App.toast('✅ Yuklab olindi');
  };
})();
