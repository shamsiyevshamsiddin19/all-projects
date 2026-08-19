/* Arxiv — Nusxalar (copypaste) va Saytlar. localStorage'da (server bilan avto-sinxron).
   QOIDALAR bu yerdan CHIQARILDI — endi alohida "Qoidalar" bo'limi (qoidalar.js).
   Saqlash kaliti (`arxiv_qoidalar`) o'zgarmagani uchun eski qoidalar
   o'sha yerda turibdi, yo'qolmagan. Zaxira eksporti ham ularni qo'shib
   yuboraveradi (eski zaxira fayllari bilan moslik uchun). */
(function () {
  'use strict';

  var TYPES = {
    copy: { key: 'arxiv_copypaste', label: 'Nusxalar', icon: 'copy' },
    site: { key: 'arxiv_saytlar', label: 'Saytlar', icon: 'globe' }
  };
  var RULE_KEY = 'arxiv_qoidalar';   // faqat zaxira eksport/importi uchun
  var state = { tab: 'copy', q: '' };

  function read(type) { try { var v = JSON.parse(localStorage.getItem(TYPES[type].key) || '[]'); return Array.isArray(v) ? v : []; } catch (e) { return []; } }
  function write(type, arr) { localStorage.setItem(TYPES[type].key, JSON.stringify(arr)); }
  function makeId(p) { return p + '_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8); }

  function faviconFor(url) {
    try { return 'https://www.google.com/s2/favicons?sz=64&domain=' + new URL(url).hostname; } catch (e) { return ''; }
  }
  function siteNameFrom(url) {
    try { return new URL(url).hostname.replace(/^www\./, ''); } catch (e) { return url; }
  }

  App.view('arxiv', {
    nav: 'arxiv',
    render: function (page) {
      page.innerHTML = '<div class="topbar" style="margin:-16px -15px 12px"><button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button><h1>Arxiv</h1>' +
        '<button class="icon-btn ghost" data-act="arxivAdd" data-arg=\'{"t":"' + state.tab + '"}\' style="margin-left:auto"><span data-icon="plus" data-icon-size="20"></span></button>' +
        '<button class="icon-btn ghost" data-act="arxivBackup" aria-label="Zaxira"><span data-icon="upload" data-icon-size="18"></span></button></div>' +
        '<div class="flex" style="gap:6px;margin-bottom:16px">' +
        Object.keys(TYPES).map(function (t) {
          return '<button class="chip-btn ' + (t === state.tab ? 'active' : '') + '" style="flex:1;justify-content:center" data-act="arxivTab" data-arg=\'{"t":"' + t + '"}\'>' + TYPES[t].label + '</button>';
        }).join('') + '</div>' +
        '<input class="input" id="ax-q" placeholder="Qidirish..." style="margin-bottom:12px" value="' + App.esc(state.q || '') + '">' +
        '<div id="arxiv-list"></div>';
      App.icons(page);
      App.el('ax-q').oninput = function () { state.q = this.value; renderList(); };
      renderList();
      initSwipe(page);
    }
  });

  var TAB_ORDER = Object.keys(TYPES);   // ['copy','site'] — svayp shu tartibda

  function setTab(t) {
    if (!TYPES[t] || t === state.tab) return;
    state.tab = t; state.q = '';
    App.reload();
  }
  App.actions.arxivTab = function (a) { setTab(a.t); };

  /* Barmoq bilan surib bo'lim almashish. Chiplar bilan bitta manba (state.tab)
     orqali sinxron — svaypdan keyin App.reload() chiplarni ham qayta chizadi.
     Faqat aniq GORIZONTAL harakat qabul qilinadi, aks holda sahifani vertikal
     aylantirish ham bo'lim almashtirib yuborardi. */
  function initSwipe(page) {
    var x0 = null, y0 = null, locked = false;

    page.addEventListener('touchstart', function (e) {
      if (e.touches.length !== 1) { x0 = null; return; }
      // Matn maydoni/tugma ustidan boshlangan harakatga tegmaymiz
      if (e.target.closest('input, textarea, button, a')) { x0 = null; return; }
      x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; locked = false;
    }, { passive: true });

    page.addEventListener('touchmove', function (e) {
      if (x0 === null) return;
      var dx = e.touches[0].clientX - x0, dy = e.touches[0].clientY - y0;
      if (!locked && Math.abs(dy) > Math.abs(dx)) { x0 = null; return; }  // vertikal — bekor
      if (Math.abs(dx) > 12) locked = true;
    }, { passive: true });

    page.addEventListener('touchend', function (e) {
      if (x0 === null || !locked) { x0 = null; return; }
      var dx = e.changedTouches[0].clientX - x0;
      x0 = null;
      if (Math.abs(dx) < 55) return;                       // juda kichik — svayp emas
      var i = TAB_ORDER.indexOf(state.tab);
      var next = dx < 0 ? i + 1 : i - 1;                   // chapga surish -> keyingisi
      if (next < 0 || next >= TAB_ORDER.length) return;    // chetidan nariga o'tmaydi
      setTab(TAB_ORDER[next]);
    }, { passive: true });
  }

  /* Qidiruv — barcha matnli maydonlar bo'yicha */
  function matchesQuery(it, q) {
    if (!q) return true;
    var hay = [it.title, it.text, it.name, it.url, it.desc].filter(Boolean).join(' ').toLowerCase();
    return hay.indexOf(q.toLowerCase()) >= 0;
  }

  function renderList() {
    var box = App.el('arxiv-list'); if (!box) return;
    var q = (state.q || '').trim();
    var all = read(state.tab);
    var items = all.filter(function (it) { return matchesQuery(it, q); });
    if (!items.length) {
      box.innerHTML = App.empty({
        icon: TYPES[state.tab].icon,
        title: q ? 'Topilmadi' : 'Bo\'sh',
        text: q ? '"' + q + '" bo\'yicha natija yo\'q.' : 'Yuqoridagi (+) tugmasi bilan qo\'shing.'
      });
      App.icons(box);
      return;
    }
    if (state.tab === 'site') {
      box.innerHTML = items.map(function (it) {
        return '<div class="list-row">' +
          '<img src="' + App.esc(it.img || faviconFor(it.url)) + '" style="width:29px;height:29px;border-radius:8px;flex-shrink:0;background:var(--card-2)" onerror="this.style.visibility=\'hidden\'">' +
          '<button class="li-main li-btn" data-act="arxivOpenSite" data-arg=\'' + App.arg({ id: it.id }) + '\'>' +
          '<div class="li-title">' + App.esc(it.name) + '</div><div class="li-sub">' + App.esc(it.desc || it.url) + '</div></button>' +
          '<button class="icon-btn ghost" style="width:28px;height:28px" data-act="arxivDelete" data-arg=\'' + App.arg({ t: 'site', id: it.id }) + '\'><span data-icon="trash" data-icon-size="14"></span></button></div>';
      }).join('');
    } else {
      box.innerHTML = items.map(function (it) {
        return '<button class="list-row" data-act="arxivView" data-arg=\'' + App.arg({ t: state.tab, id: it.id }) + '\'>' +
          '<span class="li-ic" data-icon="' + TYPES[state.tab].icon + '" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + App.esc(it.title) + '</div></div>' +
          '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
      }).join('');
    }
    App.icons(box);
  }

  App.actions.arxivAdd = function (a) {
    if (a.t === 'site') {
      var html = '<label class="field"><span>URL</span><input class="input" id="ax-url" placeholder="https://..."></label>' +
        '<label class="field"><span>Izoh (ixtiyoriy)</span><input class="input" id="ax-desc"></label>' +
        '<button class="btn" id="ax-save">Saqlash</button>';
      var sh = App.sheet(html, { title: 'Sayt qo\'shish' });
      sh.querySelector('#ax-save').onclick = function () {
        var url = sh.querySelector('#ax-url').value.trim();
        if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
        try { new URL(url); } catch (e) { return App.toast('URL noto\'g\'ri'); }
        var arr = read('site');
        arr.unshift({ id: makeId('site'), url: url, name: siteNameFrom(url), img: faviconFor(url), desc: sh.querySelector('#ax-desc').value.trim(), created_at: new Date().toISOString() });
        write('site', arr); App.closeSheet(); App.reload();
      };
    } else {
      var html2 =
        '<button class="list-row" id="ax-md-pick" style="margin-bottom:12px">' +
        '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">.md fayl yuklash</div>' +
        '<div class="li-sub" id="ax-md-info">Markdown fayl — jadvallar bilan</div></div></button>' +
        '<input type="file" id="ax-md-file" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">' +
        '<label class="field"><span>Sarlavha</span><input class="input" id="ax-title"></label>' +
        '<label class="field"><span>Matn (Markdown)</span>' +
        '<textarea class="textarea" id="ax-text" rows="7"' +
        ' placeholder="# Sarlavha&#10;&#10;| Ustun | Ustun |&#10;|---|---|&#10;| a | b |"' +
        '></textarea></label>' +
        '<button class="btn" id="ax-save2">Saqlash</button>';
      var sh2 = App.sheet(html2, { title: TYPES[a.t].label + ' qo\'shish' });

      sh2.querySelector('#ax-md-pick').onclick = function () { sh2.querySelector('#ax-md-file').click(); };
      sh2.querySelector('#ax-md-file').onchange = function () {
        var f = this.files && this.files[0]; if (!f) return;
        var rd = new FileReader();
        rd.onload = function () {
          sh2.querySelector('#ax-text').value = String(rd.result || '');
          var ti = sh2.querySelector('#ax-title');
          if (!ti.value.trim()) ti.value = f.name.replace(/\.(md|markdown|txt)$/i, '');
          var info = sh2.querySelector('#ax-md-info');
          if (info) info.textContent = f.name + ' · ' + Math.max(1, Math.round(f.size / 1024)) + ' KB';
        };
        rd.onerror = function () { App.toast('⚠️ Fayl o\'qilmadi'); };
        rd.readAsText(f);
      };

      sh2.querySelector('#ax-save2').onclick = function () {
        var text = sh2.querySelector('#ax-text').value;
        if (!text.trim()) return App.toast('Matn bo\'sh bo\'lmasin');
        var title = sh2.querySelector('#ax-title').value.trim() || (text.length > 40 ? text.slice(0, 37) + '...' : text) || 'Nomsiz';
        var arr = read(a.t);
        arr.unshift({ id: makeId(a.t), title: title, text: text, created_at: new Date().toISOString() });
        write(a.t, arr); App.closeSheet(); App.reload();
      };
    }
  };

  App.actions.arxivView = function (a) {
    App.go('arxiv_doc', { t: a.t, id: a.id });
  };

  App.view('arxiv_doc', {
    nav: 'arxiv',
    render: function (page, params) {
      // Eski havola/zakladka `t=rule` bilan kelishi mumkin — qoidalar endi
      // alohida bo'limda, o'sha yerga yo'naltiramiz (aks holda TYPES['rule']
      // yo'qligi uchun xato bo'lardi).
      if (params.t === 'rule') { App.go('qoida_doc', { id: params.id }); return; }
      var t = TYPES[params.t] ? params.t : 'copy';
      var it = read(t).find(function (x) { return x.id === params.id; });
      if (!it) { App.go('arxiv'); return; }
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"arxiv"}\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(it.title) + '</h1>' +
        '<button class="icon-btn ghost" id="arxiv-doc-menu" style="margin-left:auto"><span data-icon="edit" data-icon-size="18"></span></button>' +
        '</div>' +
        '<div class="md-content">' + App.md(it.text) + '</div>';
      App.icons(page);
      App.el('arxiv-doc-menu').onclick = function () {
        var html =
          '<button class="list-row" data-act="arxivDocEdit" data-arg=\'' + App.arg({ t: t, id: it.id }) + '\'>'+
          '<span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Tahrirlash</div></div></button>' +
          '<button class="list-row" data-act="arxivCopyText" data-arg=\'' + App.arg({ text: it.text }) + '\'>'+
          '<span class="li-ic" data-icon="copy" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nusxalash</div></div></button>' +
          '<button class="list-row" data-act="arxivDelete" data-arg=\'' + App.arg({ t: t, id: it.id, back: 'arxiv' }) + '\' style="color:var(--danger)">'+
          '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span><div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
        var sh = App.sheet(html, { title: it.title });
        App.icons(sh);
      };
    }
  });

  App.actions.arxivDocEdit = function (a) {
    var t = TYPES[a.t] ? a.t : 'copy';
    var it = read(t).find(function (x) { return x.id === a.id; }); if (!it) return;
    var html =
      '<button class="list-row" id="ax-md-pick2" style="margin-bottom:12px">' +
      '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">.md fayl bilan almashtirish</div>' +
      '<div class="li-sub" id="ax-md-info2">Mavjud matn yangisi bilan almashadi</div></div></button>' +
      '<input type="file" id="ax-md-file2" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">' +
      '<label class="field"><span>Sarlavha</span><input class="input" id="ax-t2" value="' + App.esc(it.title) + '"></label>' +
      '<label class="field"><span>Matn (Markdown)</span><textarea class="textarea" id="ax-x2" rows="10"></textarea></label>' +
      '<button class="btn" id="ax-u2">Saqlash</button>';
    var sh = App.sheet(html, { title: TYPES[t].label + ' — tahrirlash' });
    sh.querySelector('#ax-x2').value = it.text;
    sh.querySelector('#ax-md-pick2').onclick = function () { sh.querySelector('#ax-md-file2').click(); };
    sh.querySelector('#ax-md-file2').onchange = function () {
      var f = this.files && this.files[0]; if (!f) return;
      var rd = new FileReader();
      rd.onload = function () {
        sh.querySelector('#ax-x2').value = String(rd.result || '');
        var info = sh.querySelector('#ax-md-info2');
        if (info) info.textContent = f.name + ' · ' + Math.max(1, Math.round(f.size / 1024)) + ' KB';
      };
      rd.onerror = function () { App.toast('⚠️ Fayl o\'qilmadi'); };
      rd.readAsText(f);
    };
    sh.querySelector('#ax-u2').onclick = function () {
      var text = sh.querySelector('#ax-x2').value;
      if (!text.trim()) return App.toast('Matn bo\'sh bo\'lmasin');
      var arr = read(t);
      var ix = arr.findIndex(function (x) { return x.id === a.id; });
      if (ix < 0) return;
      arr[ix].title = sh.querySelector('#ax-t2').value.trim() || arr[ix].title;
      arr[ix].text = text;
      write(t, arr); App.closeSheet(); App.reload();
    };
  };
  App.actions.arxivOpenSite = function (a) {
    var items = read('site'), it = items.find(function (x) { return x.id === a.id; }); if (!it) return;
    window.open(it.url, '_blank', 'noopener');
  };
  App.actions.arxivCopyText = function (a) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(a.text).then(function () { App.toast('✅ Nusxalandi'); }).catch(function () { App.toast('⚠️ Nusxalab bo\'lmadi'); });
    } else { App.toast('⚠️ Brauzer qo\'llamaydi'); }
  };
  App.actions.arxivDelete = function (a) {
    App.closeSheet();
    App.confirm('O\'chirilsinmi?', function () {
      write(a.t, read(a.t).filter(function (x) { return x.id !== a.id; }));
      // Qoida sahifasidan o'chirilsa ro'yxatga qaytamiz (sahifa endi bo'sh)
      if (a.back) App.go(a.back); else App.reload();
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Zaxira: JSON eksport/import ---------- */
  App.actions.arxivBackup = function () {
    var html =
      '<button class="list-row" data-act="arxivExport"><span class="li-ic" data-icon="upload" data-icon-size="15"></span><div class="li-main"><div class="li-title">Zaxira faylini yuklab olish</div><div class="li-sub">Barcha nusxa/sayt/qoidalar JSON fayl</div></div></button>' +
      '<button class="list-row" data-act="arxivImportPick"><span class="li-ic" data-icon="refresh" data-icon-size="15"></span><div class="li-main"><div class="li-title">Fayldan tiklash</div><div class="li-sub">Zaxira JSON faylini yuklash</div></div></button>' +
      '<input type="file" id="ax-import-file" hidden accept="application/json">';
    App.sheet(html, { title: 'Zaxira' });
  };
  function readKey(k) {
    try { var v = JSON.parse(localStorage.getItem(k) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  App.actions.arxivExport = function () {
    // `rule` alohida bo'limga ko'chgan bo'lsa-da, zaxirada qoladi — eski
    // zaxira fayllari bilan bir xil tuzilish saqlanadi.
    var payload = { copy: read('copy'), site: read('site'), rule: readKey(RULE_KEY), exported_at: new Date().toISOString() };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'yordamchi_arxiv_backup.json';
    document.body.appendChild(a); a.click(); a.remove();
    App.toast('✅ Yuklab olindi');
  };
  App.actions.arxivImportPick = function () { App.el('ax-import-file').click(); };
  document.addEventListener('change', function (e) {
    if (e.target && e.target.id === 'ax-import-file') {
      var file = e.target.files[0]; if (!file) return;
      var reader = new FileReader();
      reader.onload = function () {
        try {
          var data = JSON.parse(reader.result);
          ['copy', 'site'].forEach(function (t) {
            if (Array.isArray(data[t])) write(t, data[t]);
          });
          // Qoidalar endi alohida bo'limda — kalitiga to'g'ridan-to'g'ri yoziladi
          if (Array.isArray(data.rule)) localStorage.setItem(RULE_KEY, JSON.stringify(data.rule));
          App.closeSheet(); App.toast('✅ Tiklandi'); App.reload();
        } catch (err) { App.toast('⚠️ Fayl noto\'g\'ri'); }
      };
      reader.readAsText(file);
    }
  });
})();
