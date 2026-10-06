/* Maqsadlar (goals) — jild/bo'lim/maqsad, backend: get_data&db=Global_Data + *_goal_* */
(function () {
  'use strict';
  var G = {
    folders: [], sections: [], goals: [],
    curFolder: 'default', curSection: 'default',
    loaded: false, defaulted: false
  };

  function idEq(a, b) { return String(a) === String(b); }

  function sectionsOf(folderId) {
    return G.sections.filter(function (s) { return idEq(s.folder_id, folderId); });
  }

  function load() {
    return App.call('get_data', null, { query: 'db=Global_Data' }).then(function (j) {
      G.folders = [{ id: 'default', name: 'Umumiy' }].concat(
        (j.goal_folders || []).filter(function (f) { return String(f.id) !== 'default'; }));
      G.sections = j.goal_sections || [];
      G.goals = j.goals || [];
      G.loaded = true;
      if (!G.defaulted) {
        G.defaulted = true;
        var customFolders = G.folders.filter(function (f) { return !idEq(f.id, 'default'); });
        if (customFolders.length) {
          G.curFolder = customFolders[0].id;
          var secs = sectionsOf(G.curFolder);
          if (secs.length) G.curSection = secs[0].id;
        }
      }
      return G;
    }).catch(function () { G.loaded = true; return G; });
  }
  function goalsOf(folderId, sectionId) {
    return G.goals.filter(function (g) {
      return idEq(g.folder_id, folderId) && idEq(g.section_id, sectionId);
    });
  }
  function stats() {
    var t = G.goals.length, d = G.goals.filter(function (g) { return +g.completed === 1; }).length;
    return { total: t, done: d, pct: t ? Math.round(d / t * 100) : 0 };
  }

  /* ---------- Maqsad hajmi (LeetCode uslubidagi 3 rangli halqa) ----------
     Eski maqsadlarda `size` bo'lmasligi mumkin — 'orta' deb qabul qilamiz
     (backend ham DEFAULT 'orta' beradi, shuning uchun migratsiya shart emas). */
  var SIZES = [
    { k: 'katta',  n: 'Katta',  c: '#ef4743' },
    { k: 'orta',   n: 'O\'rta',  c: '#ffb700' },
    { k: 'kichik', n: 'Kichik', c: '#00b8a3' }
  ];
  function sizeOf(g) {
    var v = String(g.size || '').toLowerCase();
    return (v === 'katta' || v === 'kichik') ? v : 'orta';
  }
  function sizeInfo(k) {
    for (var i = 0; i < SIZES.length; i++) if (SIZES[i].k === k) return SIZES[i];
    return SIZES[1];
  }

  /* Har hajm bo'yicha bajarilgan/jami */
  function sizeStats() {
    var out = {};
    SIZES.forEach(function (s) { out[s.k] = { done: 0, total: 0, nom: s.n, rang: s.c }; });
    G.goals.forEach(function (g) {
      var b = out[sizeOf(g)];
      b.total++;
      if (+g.completed === 1) b.done++;
    });
    return out;
  }

  /* 3 ta yoydan iborat halqa: har hajm o'z rangi bilan, uzunligi shu hajmdagi
     maqsadlar ULUSHIga, to'ldirilgani esa BAJARILGANiga mos. */
  function sizeRing(size) {
    var s = size || 108, r = s / 2 - 7, cx = s / 2, C = 2 * Math.PI * r;
    var st = sizeStats();
    var total = SIZES.reduce(function (n, x) { return n + st[x.k].total; }, 0);
    var done = SIZES.reduce(function (n, x) { return n + st[x.k].done; }, 0);
    var pct = total ? Math.round(done / total * 100) : 0;

    var GAP = total ? 3 : 0;                 // yoylar orasidagi kichik bo'shliq
    var svg = '<svg viewBox="0 0 ' + s + ' ' + s + '" style="width:' + s + 'px;height:' + s + 'px;transform:rotate(-90deg)">';
    if (!total) {
      svg += '<circle cx="' + cx + '" cy="' + cx + '" r="' + r + '" fill="none" stroke="var(--border-soft)" stroke-width="8"/>';
    } else {
      var offset = 0;
      SIZES.forEach(function (x) {
        var b = st[x.k];
        if (!b.total) return;
        var arc = (b.total / total) * C - GAP;
        if (arc <= 0) return;
        // Orqa fon yoyi (shu hajmning ulushi)
        svg += '<circle cx="' + cx + '" cy="' + cx + '" r="' + r + '" fill="none" stroke="' + x.c +
               '" stroke-opacity=".22" stroke-width="8" stroke-linecap="round" stroke-dasharray="' +
               arc.toFixed(1) + ' ' + (C - arc).toFixed(1) + '" stroke-dashoffset="' + (-offset).toFixed(1) + '"/>';
        // Bajarilgan qismi
        var fill = b.total ? (b.done / b.total) * arc : 0;
        if (fill > 0) {
          svg += '<circle cx="' + cx + '" cy="' + cx + '" r="' + r + '" fill="none" stroke="' + x.c +
                 '" stroke-width="8" stroke-linecap="round" stroke-dasharray="' +
                 fill.toFixed(1) + ' ' + (C - fill).toFixed(1) + '" stroke-dashoffset="' + (-offset).toFixed(1) + '"/>';
        }
        offset += arc + GAP;
      });
    }
    svg += '</svg>';
    return '<div class="ring" style="width:' + s + 'px;height:' + s + 'px;position:relative">' + svg +
      '<div class="ring-mid" style="position:absolute;inset:0;display:flex;flex-direction:column;' +
      'align-items:center;justify-content:center;font-weight:800">' +
      '<span style="font-size:' + Math.round(s * 0.2) + 'px">' + done + '</span>' +
      '<span style="font-size:' + Math.round(s * 0.1) + 'px;color:var(--hint);font-weight:600">/' + total + '</span>' +
      '</div></div>';
  }

  /* Halqa + yon tomonda hajm bo'yicha taqsimot */
  function sizePanelHtml() {
    var st = sizeStats();
    return '<div style="display:flex;align-items:center;gap:18px;margin:2px 1px 16px">' +
      sizeRing(108) +
      '<div style="flex:1;min-width:0">' +
      SIZES.map(function (x) {
        var b = st[x.k];
        var p = b.total ? Math.round(b.done / b.total * 100) : 0;
        return '<div style="margin-bottom:9px">' +
          '<div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:3px">' +
          '<span style="color:' + x.c + ';font-weight:700">' + x.n + '</span>' +
          '<span style="color:var(--hint);font-weight:600">' + b.done + '/' + b.total + '</span></div>' +
          '<div style="height:5px;background:var(--border-soft);border-radius:3px;overflow:hidden">' +
          '<i style="display:block;height:100%;width:' + p + '%;background:' + x.c + ';border-radius:3px"></i></div>' +
          '</div>';
      }).join('') +
      '</div></div>';
  }
  window.GoalSizes = { list: SIZES, of: sizeOf, info: sizeInfo, stats: sizeStats, panel: sizePanelHtml, ring: sizeRing };

  /* Home ichidagi maqsadlar bloki */
  function renderInto(box) {
    if (!G.loaded) { box.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>'; return; }
    var customFolders = G.folders.filter(function (f) { return !idEq(f.id, 'default'); });
    var folderChips = customFolders.map(function (f) {
      return '<button class="chip-btn ' + (idEq(f.id, G.curFolder) ? 'active' : '') +
        '" data-act="goalFolder" data-arg=\'' + App.arg({ id: f.id }) + '\'>' + App.esc(f.name) + '</button>';
    }).join('');

    var secs = sectionsOf(G.curFolder);
    if (idEq(G.curSection, 'default') && secs.length) G.curSection = secs[0].id;
    var sectionChips = secs.map(function (s) {
      return '<button class="chip-btn sect ' + (idEq(s.id, G.curSection) ? 'active' : '') +
        '" data-act="goalSection" data-arg=\'' + App.arg({ id: s.id }) + '\'>' + App.esc(s.name) + '</button>';
    }).join('');

    var list;
    if (idEq(G.curSection, 'default')) {
      // Barcha bo'lim: jilddagi barcha maqsadlar (bo'limsiz + har bo'lim)
      var groups = [];
      groups.push({ name: '', items: goalsOf(G.curFolder, 'default') });
      secs.forEach(function (s) { groups.push({ name: s.name, items: goalsOf(G.curFolder, s.id) }); });
      list = groups.filter(function (gr) { return gr.items.length; }).map(function (gr) {
        return (gr.name ? '<div class="muted" style="grid-column:1/-1;font-size:12px;font-weight:700;margin:6px 2px 0">' + App.esc(gr.name) + '</div>' : '') +
          gr.items.map(goalRow).join('');
      }).join('');
    } else {
      var items = goalsOf(G.curFolder, G.curSection);
      // Bo'lim yaratilishidan oldin qo'shilgan "bo'limsiz" maqsadlar yo'qolib qolmasin —
      // birinchi bo'lim tanlanganda ular ham shu yerda ko'rsatiladi.
      if (secs.length && idEq(G.curSection, secs[0].id)) {
        items = goalsOf(G.curFolder, 'default').concat(items);
      }
      list = items.map(goalRow).join('');
    }

    box.innerHTML =
      '<div class="between" style="margin-bottom:' + (sectionChips ? '8px' : '10px') + '"><div class="flex" style="gap:6px;flex-wrap:wrap">' + folderChips +
      '</div><button class="icon-btn ghost" data-act="goalManage" aria-label="Jild va bo\'limlar" style="width:28px;height:28px;flex-shrink:0"><span data-icon="edit" data-icon-size="14"></span></button></div>' +
      (sectionChips ? '<div class="flex" style="gap:5px;flex-wrap:wrap;margin-bottom:10px">' + sectionChips + '</div>' : '') +
      (list.trim() ? '<div class="goals-grid">' + list + '</div>' : App.empty({ icon: 'trophy', title: 'Maqsad yo\'q', text: 'Yuqoridagi tugma bilan qo\'shing.' }));
    App.icons(box);
  }

  function goalRow(g) {
    var done = +g.completed === 1;
    var si = sizeInfo(sizeOf(g));
    return '<div class="list-row">' +
      '<button class="li-ic" style="border:none;background:' + (done ? 'var(--success-soft)' : 'var(--card-2)') + ';color:' + (done ? 'var(--success)' : 'var(--hint)') + '" data-act="goalToggle" data-arg=\'' + App.arg({ id: g.id }) + '\'>' +
      '<span data-icon="' + (done ? 'check' : 'plus') + '" data-icon-size="15"></span></button>' +
      '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" data-act="goalEdit" data-arg=\'' + App.arg({ id: g.id }) + '\'>' +
      '<div class="li-title" style="' + (done ? 'text-decoration:line-through;color:var(--hint);font-weight:500' : '') + '">' +
      '<i title="' + si.n + '" style="display:inline-block;width:7px;height:7px;border-radius:50%;background:' + si.c +
      ';margin-right:7px;vertical-align:middle;flex-shrink:0"></i>' + App.esc(g.text) + '</div></button>' +
      '</div>';
  }

  /* Actions */
  App.actions.goalFolder = function (a) { G.curFolder = a.id; G.curSection = 'default'; App.reload(); };
  App.actions.goalSection = function (a) { G.curSection = a.id; App.reload(); };

  /* Hajm tanlagich (qo'shish va tahrirlash oynalarida bir xil) */
  function sizePickerHtml(cur) {
    return '<div class="field"><span>Hajmi</span><div class="flex" style="gap:6px" id="gs-pick">' +
      SIZES.map(function (x) {
        var on = x.k === cur;
        return '<button type="button" class="chip-btn" data-s="' + x.k + '" style="flex:1;justify-content:center;' +
          (on ? 'background:' + x.c + '22;color:' + x.c + ';border-color:' + x.c : '') + '">' + x.n + '</button>';
      }).join('') + '</div></div>';
  }
  function bindSizePicker(sh, cur) {
    var sel = { v: cur };
    sh.querySelectorAll('#gs-pick .chip-btn').forEach(function (b) {
      b.onclick = function () {
        sel.v = b.getAttribute('data-s');
        sh.querySelectorAll('#gs-pick .chip-btn').forEach(function (x) {
          var info = sizeInfo(x.getAttribute('data-s'));
          var on = x === b;
          x.style.background = on ? info.c + '22' : '';
          x.style.color = on ? info.c : '';
          x.style.borderColor = on ? info.c : '';
        });
      };
    });
    return sel;
  }

  App.actions.goalAdd = function () {
    var html =
      '<label class="field"><span>Maqsad matni</span><input class="input" id="ga-in" placeholder="Masalan: 100 ta masala yechish"></label>' +
      sizePickerHtml('orta') +
      '<button class="btn" id="ga-save">Qo\'shish</button>';
    var sh = App.sheet(html, { title: 'Yangi maqsad' });
    var sel = bindSizePicker(sh, 'orta');
    var inp = sh.querySelector('#ga-in');
    inp.focus();
    var save = function () {
      var text = inp.value.trim();
      if (!text) return App.toast('Maqsad matnini kiriting');
      var p = { text: text, size: sel.v };
      if (!idEq(G.curFolder, 'default')) p.folder_id = G.curFolder;
      if (!idEq(G.curSection, 'default')) p.section_id = G.curSection;
      App.closeSheet();
      App.call('add_goal', p).then(function () { return load(); }).then(App.reload)
        .catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
    sh.querySelector('#ga-save').onclick = save;
    inp.onkeydown = function (e) { if (e.key === 'Enter') save(); };
  };
  App.actions.goalToggle = function (a) {
    var g = G.goals.find(function (x) { return idEq(x.id, a.id); });
    if (g) g.completed = +g.completed === 1 ? 0 : 1; // optimistik
    App.reload();
    App.call('toggle_goal', { id: a.id }).catch(function (e) { App.toast('⚠️ ' + e.message); load().then(App.reload); });
  };
  App.actions.goalEdit = function (a) {
    var g = G.goals.find(function (x) { return idEq(x.id, a.id); }); if (!g) return;
    var html = '<label class="field"><span>Maqsad matni</span><input class="input" id="ge-in" value="' + App.esc(g.text) + '"></label>' +
      sizePickerHtml(sizeOf(g)) +
      '<div class="btn-row"><button class="btn danger" id="ge-del">O\'chirish</button><button class="btn" id="ge-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: 'Maqsadni tahrirlash' });
    var sel = bindSizePicker(sh, sizeOf(g));
    sh.querySelector('#ge-save').onclick = function () {
      var v = sh.querySelector('#ge-in').value.trim(); if (!v) return App.toast('Bo\'sh bo\'lmasin');
      App.closeSheet();
      App.call('edit_goal', { id: a.id, text: v, size: sel.v }).then(function () { return load(); }).then(App.reload);
    };
    sh.querySelector('#ge-del').onclick = function () {
      App.closeSheet(); App.call('delete_goal', { id: a.id }).then(function () { return load(); }).then(App.reload);
    };
  };

  /* Jild/bo'lim boshqaruvi */
  App.actions.goalManage = function () {
    var html =
      '<div class="btn-row" style="margin-bottom:14px"><button class="btn sec" data-act="goalAddFolder">+ Jild</button>' +
      '<button class="btn sec" data-act="goalAddSection">+ Bo\'lim</button></div>' +
      '<div class="list-label" style="margin-top:2px">Jildlar</div>' +
      (G.folders.filter(function (f) { return !idEq(f.id, 'default'); }).map(function (f) {
        return '<div class="list-row"><div class="li-main"><div class="li-title">' + App.esc(f.name) + '</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="goalDelFolder" data-arg=\'' + App.arg({ id: f.id }) + '\'><span data-icon="trash" data-icon-size="15"></span></button></div>';
      }).join('') || '<p class="muted" style="font-size:13px;margin:2px">Jild yo\'q</p>') +
      '<div class="list-label">Bo\'limlar (joriy jild)</div>' +
      (sectionsOf(G.curFolder).map(function (s) {
        return '<div class="list-row"><div class="li-main"><div class="li-title">' + App.esc(s.name) + '</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="goalDelSection" data-arg=\'' + App.arg({ id: s.id }) + '\'><span data-icon="trash" data-icon-size="15"></span></button></div>';
      }).join('') || '<p class="muted" style="font-size:13px;margin:2px">Bo\'lim yo\'q</p>');
    App.sheet(html, { title: 'Jild va bo\'limlar' });
  };
  App.actions.goalAddFolder = function () {
    App.prompt({ title: 'Yangi jild', label: 'Jild nomi' }, function (name) {
      App.call('add_goal_folder', { name: name }).then(function () { return load(); }).then(function () { App.closeSheet(); App.reload(); });
    });
  };
  App.actions.goalAddSection = function () {
    App.prompt({ title: 'Yangi bo\'lim', label: 'Bo\'lim nomi (joriy jildga)' }, function (name) {
      var p = { name: name };
      if (!idEq(G.curFolder, 'default')) p.folder_id = G.curFolder;
      App.call('add_goal_section', p).then(function () { return load(); }).then(function () { App.closeSheet(); App.reload(); });
    });
  };
  App.actions.goalDelFolder = function (a) {
    App.confirm('Jild va ichidagi barcha maqsadlar o\'chiriladi.', function () {
      App.call('delete_goal_folder', { id: a.id }).then(function () { if (idEq(G.curFolder, a.id)) G.curFolder = 'default'; return load(); }).then(function () { App.closeSheet(); App.reload(); });
    }, { danger: true, yes: 'O\'chirish' });
  };
  App.actions.goalDelSection = function (a) {
    App.confirm('Bo\'lim va ichidagi maqsadlar o\'chiriladi.', function () {
      App.call('delete_goal_section', { id: a.id }).then(function () { if (idEq(G.curSection, a.id)) G.curSection = 'default'; return load(); }).then(function () { App.closeSheet(); App.reload(); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  window.Goals = { load: load, renderInto: renderInto, stats: stats, data: G };
})();
