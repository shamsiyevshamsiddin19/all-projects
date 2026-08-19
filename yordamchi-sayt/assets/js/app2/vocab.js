/* Lug'at (Vocabulary) — Ingliz/Rus: kategoriyalar, flashcard (svayp), oddiy ro'yxat. */
(function () {
  'use strict';

  var LABEL = {
    english: { hub: "Lug'at", side1: 'Ingliz tili', side2: "O'zbek tili", tts1: 'en-US', tts2: 'uz-UZ' },
    russian: { hub: "Lug'at", side1: 'Rus tili', side2: "O'zbek tili", tts1: 'ru-RU', tts2: 'uz-UZ' }
  };

  var V = { lang: 'english', order: [], data: {}, loaded: false };
  var FC = null; // flashcard session state

  function parseWords(text) {
    var list = [];
    String(text || '').split('\n').forEach(function (line) {
      var m = line.match(/^\s*\d+[).]\s*(.+?)\s*[-–—]\s*(.+?)\s*$/);
      if (m) list.push({ ru: m[1].trim(), uz: m[2].trim() });
    });
    return list;
  }

  function loadDict(lang) {
    return App.call('get_dict_data', null, { query: 'lang=' + lang }).then(function (j) {
      V.lang = lang; V.order = j.order || []; V.data = {};
      (j.items || []).forEach(function (it) {
        (V.data[it.category] = V.data[it.category] || []).push({ ru: it.word_ru, uz: it.word_uz });
      });
      V.order.forEach(function (c) { if (!V.data[c]) V.data[c] = []; });
      V.loaded = true;
      return V;
    });
  }

  /* ---------- Kategoriyalarni yashirish ----------
     Yuzlab kategoriya to'planganda kerak bo'lmaganlarini ro'yxatdan olib
     qo'yish. O'CHIRISH EMAS — so'zlar joyida qoladi, faqat ko'rinmaydi
     va istalgan payt qaytariladi. localStorage (remote-storage sinxronlaydi). */
  function hiddenKey(lang) { return 'vocab_hidden_v1_' + lang; }
  function hiddenCats(lang) {
    try {
      var v = JSON.parse(localStorage.getItem(hiddenKey(lang)) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function setHidden(lang, list) {
    try { localStorage.setItem(hiddenKey(lang), JSON.stringify(list)); } catch (e) {}
  }

  /* Butun PAPKA ni yashirish — ichidagi hamma lug'at bilan birga.
     Alohida ro'yxat: papkaga keyin yangi lug'at qo'shilsa ham u avtomatik
     yashirin bo'ladi (har birini qo'lda belgilash shart emas). */
  function hiddenFoldersKey(lang) { return 'vocab_hidden_folders_v1_' + lang; }
  function hiddenFolders(lang) {
    try {
      var v = JSON.parse(localStorage.getItem(hiddenFoldersKey(lang)) || '[]');
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function setHiddenFolders(lang, list) {
    try { localStorage.setItem(hiddenFoldersKey(lang), JSON.stringify(list)); } catch (e) {}
  }
  /* ---------- Ichma-ich papka yo'llari ----------
     Kategoriya to'liq nomi yo'l bo'lib ishlaydi: "курс/чтение/05.08.2026".
     Oxirgi bo'lak — lug'atning O'Z nomi, oldingilari — papkalar zanjiri. */

  /* "курс/чтение/05.08.2026" -> "курс/чтение" (papkasiz bo'lsa '') */
  function catParent(cat) {
    var s = String(cat);
    var i = s.lastIndexOf('/');
    return i < 0 ? '' : s.slice(0, i).trim();
  }
  /* Yo'lning oxirgi bo'lagi: "курс/чтение" -> "чтение" */
  function lastSeg(p) {
    var s = String(p || '');
    var i = s.lastIndexOf('/');
    return (i < 0 ? s : s.slice(i + 1)).trim();
  }
  /* `base` ichidagi BEVOSITA keyingi bo'lak. base='курс', path='курс/чтение/x'
     -> 'чтение'. Ichida bo'lmasa null. */
  function childSeg(base, path) {
    var p = String(path || '');
    if (base) {
      if (p !== base && p.indexOf(base + '/') !== 0) return null;
      p = p.slice(base.length + 1);
    }
    if (!p) return null;
    var i = p.indexOf('/');
    return (i < 0 ? p : p.slice(0, i)).trim() || null;
  }
  /* Kategoriya yashiringan papkalardan birining ICHIDAMI (istalgan chuqurlikda) */
  /* --- MD fayllar (kitoblar) qaysi papkada turishi ---------------------
     Ilgari MD fayllar `{nom: matn}` ko'rinishida, papkasiz saqlanardi —
     shuning uchun ular HAR BIR papka ichida ko'rinardi. Endi alohida
     xarita nomni papkaga bog'laydi. Eski fayllar (xaritada yo'q) ildizda
     qoladi — ular haqiqatan ildizga yuklangan. */
  function mdFolderKey(lang) { return 'vocab_md_folders_v1_' + lang; }
  function mdFolders(lang) {
    try {
      var v = JSON.parse(localStorage.getItem(mdFolderKey(lang)) || '{}');
      return (v && typeof v === 'object') ? v : {};
    } catch (e) { return {}; }
  }
  function setMdFolders(lang, map) {
    try { localStorage.setItem(mdFolderKey(lang), JSON.stringify(map)); } catch (e) {}
  }
  function mdFolderOf(lang, name) { return mdFolders(lang)[name] || ''; }

  function underHiddenFolder(cat, hidF) {
    if (!hidF || !hidF.length) return false;
    var p = catParent(cat);
    if (!p) return false;
    return hidF.some(function (f) { return p === f || p.indexOf(f + '/') === 0; });
  }

  App.actions.vocabFolderHide = function (a) {
    var list = hiddenFolders(a.lang);
    if (list.indexOf(a.folder) < 0) list.push(a.folder);
    setHiddenFolders(a.lang, list);
    App.closeSheet();
    App.toast('"' + a.folder + '" papkasi yashirildi');
    App.reload();
  };
  App.actions.vocabFolderUnhide = function (a) {
    setHiddenFolders(a.lang, hiddenFolders(a.lang).filter(function (f) { return f !== a.folder; }));
    App.closeSheet();
    App.toast('Qaytarildi');
    App.reload();
  };
  /* Papka ustidagi menyu (uzun bosish emas — yonidagi tugma) */
  App.actions.vocabFolderMenu = function (a) {
    var html =
      '<button class="list-row" data-act="vocabFolderHide" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="close" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Papkani yashirish</div>' +
      '<div class="li-sub">Ichidagi barcha lug\'atlar bilan birga</div></div></button>';
    App.sheet(html, { title: a.folder });
  };

  App.actions.vocabCatHide = function (a) {
    var list = hiddenCats(a.lang);
    if (list.indexOf(a.cat) < 0) list.push(a.cat);
    setHidden(a.lang, list);
    App.closeSheet();
    App.toast('Yashirildi');
    App.reload();
  };
  App.actions.vocabCatUnhide = function (a) {
    setHidden(a.lang, hiddenCats(a.lang).filter(function (c) { return c !== a.cat; }));
    App.closeSheet();
    App.toast('Qaytarildi');
    App.reload();
  };
  App.actions.vocabHiddenSheet = function (a) {
    /* FAQAT shu papkada yashirilganlar. `a.folder` berilmasa (eski
       havolalar) — hammasi, avvalgidek. */
    var folder = a.folder;
    var byFolder = function (p) { return folder === undefined || catParent(p) === folder; };
    var cats = hiddenCats(a.lang).filter(byFolder);
    var folders = hiddenFolders(a.lang).filter(byFolder);
    var html = '';

    if (folders.length) {
      html += '<div class="list-label">Papkalar</div>' + folders.map(function (f) {
        // Papkadagi lug'atlar soni (yashiringan bo'lsa ham bazada turadi)
        // Papka ICHIDAGI hamma lug'at (ichma-ich papkalar bilan birga)
        var inside = V.order.filter(function (c) {
          var p = catParent(c);
          return p === f || p.indexOf(f + '/') === 0;
        });
        var words = inside.reduce(function (s, c) { return s + (V.data[c] || []).length; }, 0);
        return '<div class="list-row">' +
          '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="archive" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + App.esc(f) + '</div>' +
          '<div class="li-sub">' + inside.length + ' bo\'lim · ' + words + ' so\'z</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" aria-label="Qaytarish" ' +
          'data-act="vocabFolderUnhide" data-arg=\'' + App.arg({ lang: a.lang, folder: f }) + '\'>' +
          '<span data-icon="refresh" data-icon-size="14"></span></button></div>';
      }).join('');
    }

    if (cats.length) {
      if (folders.length) html += '<div class="list-label">Alohida lug\'atlar</div>';
      html += cats.map(function (c) {
        return '<div class="list-row"><span class="li-ic" data-icon="list" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + App.esc(c) + '</div>' +
          '<div class="li-sub">' + (V.data[c] || []).length + ' so\'z</div></div>' +
          '<button class="icon-btn ghost" style="width:30px;height:30px" aria-label="Qaytarish" ' +
          'data-act="vocabCatUnhide" data-arg=\'' + App.arg({ lang: a.lang, cat: c }) + '\'>' +
          '<span data-icon="refresh" data-icon-size="14"></span></button></div>';
      }).join('');
    }

    if (!html) html = App.empty({ icon: 'list', title: 'Yashiringan narsa yo\'q', text: '' });
    var sh = App.sheet(html, { title: 'Yashiringanlar' });
    App.icons(sh);
  };

  function topbar(title, back, backParams, rightHtml) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: back, p: backParams || {} }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + App.esc(title) + '</h1>' + (rightHtml || '') + '</div>';
  }

  /* "Tugatish" tugmasi — barcha mashq rejimlarida bir xil ko'rinishda. */
  function finishBtnHtml(action) {
    return '<button class="icon-btn ghost" style="margin-left:auto" data-act="' + action + '" aria-label="Tugatish"><span data-icon="check" data-icon-size="18"></span></button>';
  }

  /* Sessiya oxirigacha borilmasa ham ("Tugatish" bosilsa) hozirgacha ko'rilgan
     so'zlar activity_log'ga yoziladi — statistika/streak yangilanishi uchun.
     `count` 0 bo'lsa yozilmaydi (hali hech narsa qilinmagan sessiya). */
  function logVocabProgress(lang, cat, count, mode, startedAt, extraMeta) {
    if (!count) return;
    if (window.Activity) Activity.mark();
    var meta = { lang: lang, mode: mode };
    if (extraMeta) { for (var k in extraMeta) meta[k] = extraMeta[k]; }
    App.call('log_activity', {
      section: 'vocab', object: cat || '—', amount: count, unit: 'so\'z',
      duration: startedAt ? Math.round((Date.now() - startedAt) / 1000) : null,
      meta: meta
    }).catch(function () {});
  }

  /* ---------- Lug'at hub: kategoriyalar ---------- */
  App.view('vocab', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english';
      /* Papka yo'li ("курс/чтение" kabi ichma-ich bo'lishi mumkin).
         Ortga — bir daraja YUQORIGA (ildizda bo'lsa til bo'limiga). */
      var inFolder = params.folder || '';
      var up = inFolder.indexOf('/') < 0 ? '' : inFolder.slice(0, inFolder.lastIndexOf('/'));
      var backView = inFolder ? 'vocab' : (lang === 'russian' ? 'russian' : 'english');
      var backParams = inFolder ? { lang: lang, folder: up } : null;

      /* Tugmalar BITTA ixcham qatorda — yozuvsiz, faqat belgi.
         Foydalanuvchi qaysi tugma nima qilishini biladi, ekran joyi esa
         ro'yxatga kerak. */
      page.innerHTML = topbar(inFolder ? lastSeg(inFolder) : LABEL[lang].hub, backView, backParams,
        '<div class="voc-acts">' +
        '<button class="icon-btn ghost" data-act="vocabAddCat" data-arg=\'' + App.arg({ lang: lang, folder: inFolder }) + '\' aria-label="Yangi kategoriya" title="Yangi kategoriya"><span data-icon="plus" data-icon-size="19"></span></button>' +
        /* `folder` ham uzatiladi — MD fayl JORIY papkaga yuklanadi */
        '<button class="icon-btn ghost" data-act="vocabDbOptions" data-arg=\'' + App.arg({ lang: lang, folder: params.folder || '' }) + '\' aria-label="Baza qo\'shish" title="Baza qo\'shish"><span data-icon="upload" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="vocabSendSheet" data-arg=\'' + App.arg({ lang: lang }) + '\' aria-label="Boostdayga yuborish" title="Boostdayga yuborish"><span data-icon="message" data-icon-size="18"></span></button>' +
        '</div>') +
        (inFolder ? '<div class="lib-crumb" id="voc-crumb"></div>' : '') +
        '<div id="vocab-mis-entry"></div>' +
        '<div id="vocab-list"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      // Yo'l ko'rsatkichi (breadcrumb) — chuqur papkada qayerdaligi bilinsin
      if (inFolder) {
        var cb = App.el('voc-crumb');
        if (cb) {
          var acc = '', parts = inFolder.split('/');
          cb.innerHTML = '<button class="lib-cr" data-act="go" data-arg=\'' +
            App.arg({ v: 'vocab', p: { lang: lang } }) + '\'>' + App.esc(LABEL[lang].hub) + '</button>' +
            parts.map(function (p, i) {
              acc = acc ? acc + '/' + p : p;
              if (i === parts.length - 1) return '<span>/</span><b>' + App.esc(p) + '</b>';
              return '<span>/</span><button class="lib-cr" data-act="go" data-arg=\'' +
                App.arg({ v: 'vocab', p: { lang: lang, folder: acc } }) + '\'>' + App.esc(p) + '</button>';
            }).join('');
          App.icons(cb);
        }
      }

      // Xatolar bo'limi — faqat xato so'zlar bo'lsa ko'rinadi
      loadMistakes(lang).then(function (list) {
        var box = App.el('vocab-mis-entry'); if (!box || !list.length) return;
        box.innerHTML = '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_mistakes', p: { lang: lang } }) + '\' style="margin-bottom:12px">' +
          '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="alert" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">Xatolar ustida ishlash</div>' +
          '<div class="li-sub">' + list.length + ' ta so\'z takrorlashni kutmoqda</div></div>' +
          '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
        App.icons(box);
      }).catch(function () {});

      loadDict(lang).then(function () {
        var box = App.el('vocab-list'); if (!box) return;

        /* ICHMA-ICH PAPKALAR. Kategoriya nomidagi har "/" bitta daraja:
           "курс/чтение/05.08.2026" -> курс > чтение papkalari ichida
           "05.08.2026" lug'ati. Chuqurlik cheklanmagan.
           Ilgari faqat BIRINCHI "/" hisobga olinardi, shuning uchun ichma-ich
           papka yasab bo'lmasdi — qolgan qismi uzun nom bo'lib ko'rinardi. */
        var folder = params.folder || '';
        var order = [], map = {}, root = [];
        var hid = hiddenCats(lang);
        var hidF = hiddenFolders(lang);

        V.order.forEach(function (cat) {
          if (hid.indexOf(cat) >= 0) return;              // lug'at yashiringan
          if (underHiddenFolder(cat, hidF)) return;        // papkasi (yoki yuqorigi) yashiringan

          var parent = catParent(cat);                     // to'liq papka yo'li
          if (parent === folder) {                         // shu darajadagi lug'at
            root.push({ full: cat, name: lastSeg(cat), count: (V.data[cat] || []).length });
            return;
          }
          // Ichkaridami? Bevosita KEYINGI bo'lakni papka sifatida olamiz
          var sub = childSeg(folder, parent);
          if (!sub) return;
          var path = folder ? folder + '/' + sub : sub;
          if (!map[path]) { map[path] = { name: sub, items: 0, words: 0 }; order.push(path); }
          map[path].items++;
          map[path].words += (V.data[cat] || []).length;
        });

        function catRow(it) {
          return '<div class="list-row">' +
            '<span class="li-ic" data-icon="list" data-icon-size="15"></span>' +
            '<button class="li-main li-btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: { lang: lang, cat: it.full } }) + '\'>' +
            '<div class="li-title">' + App.esc(it.name) + '</div><div class="li-sub">' + it.count + ' so\'z</div></button>' +
            '<button class="icon-btn ghost" style="width:30px;height:30px" data-act="vocabCatManage" data-arg=\'' + App.arg({ lang: lang, cat: it.full }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
        }

        /* Papka qatori: asosiy qismi ichkariga kiradi, yonidagi tugma menyu
           (button ichida button bo'lmaydi — shuning uchun o'ram div). */
        var html = order.map(function (path) {
          var f = map[path];
          return '<div class="list-row">' +
            '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="archive" data-icon-size="15"></span>' +
            '<button class="li-main li-btn" data-act="go" data-arg=\'' +
            App.arg({ v: 'vocab', p: { lang: lang, folder: path } }) + '\'>' +
            '<div class="li-title">' + App.esc(f.name) + '</div>' +
            '<div class="li-sub">' + f.items + ' bo\'lim · ' + f.words + ' so\'z</div></button>' +
            '<button class="icon-btn ghost" style="width:30px;height:30px" aria-label="Papka menyusi" ' +
            'data-act="vocabFolderMenu" data-arg=\'' + App.arg({ lang: lang, folder: path }) + '\'>' +
            '<span data-icon="edit" data-icon-size="14"></span></button></div>';
        }).join('');
        if (root.length) {
          if (order.length) html += '<div class="list-label">Lug\'atlar</div>';
          html += root.map(catRow).join('');
        }
        if (!order.length && !root.length && folder) {
          html = App.empty({ icon: 'list', title: 'Bo\'sh papka', text: '' });
        }
        
        /* MD fayllar FAQAT o'z papkasida ko'rinadi (ilgari hamma papkada
           chiqib turardi — ichma-ich papka ochilganda ham). */
        var mdFiles = {};
        try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + lang) || '{}'); } catch(ex) {}
        var mdKeys = Object.keys(mdFiles).filter(function (n) {
          return mdFolderOf(lang, n) === folder;
        });
        if (mdKeys.length) {
          html += '<div class="list-label" style="margin-top:16px">MD Fayllar (Kitoblar)</div>';
          html += mdKeys.map(function(fname) {
             return '<div class="list-row">' +
              '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="fileText" data-icon-size="15"></span>' +
              '<button class="li-main li-btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_md_read', p: { lang: lang, mdId: fname } }) + '\'>' +
              '<div class="li-title">' + App.esc(fname) + '</div><div class="li-sub">MD bazasi</div></button>' +
              '<button class="icon-btn ghost" style="width:30px;height:30px;color:var(--danger)" data-act="vocabDeleteMD" data-arg=\'' + App.arg({ lang: lang, mdId: fname }) + '\'><span data-icon="trash" data-icon-size="14"></span></button></div>';
          }).join('');
        }
        
        /* Yashiringanlar — FAQAT o'sha narsa yashirilgan papkada ko'rinadi.
           Ilgari global ro'yxat ishlatilgani uchun bu qator har bir papkada,
           hatto hech narsa yashirilmagan ichki papkalarda ham chiqardi. */
        var hidHere = hid.filter(function (c) { return catParent(c) === folder; });
        var hidFHere = hidF.filter(function (f) { return catParent(f) === folder; });
        if (hidHere.length || hidFHere.length) {
          var parts = [];
          if (hidFHere.length) parts.push(hidFHere.length + ' papka');
          if (hidHere.length) parts.push(hidHere.length + ' lug\'at');
          html += '<button class="list-row" data-act="vocabHiddenSheet" data-arg=\'' +
            App.arg({ lang: lang, folder: folder }) + '\' style="margin-top:14px">' +
            '<span class="li-ic" data-icon="close" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">Yashiringanlar</div>' +
            '<div class="li-sub">' + parts.join(' · ') + ' · qaytarish mumkin</div></div>' +
            '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
        }

        box.innerHTML = html || App.empty({ icon: 'list', title: 'Kategoriya yo\'q', text: 'Yuqoridagi tugma bilan birinchi kategoriyani qo\'shing.' });
        App.icons(box);
      }).catch(function (e) {
        var box = App.el('vocab-list'); if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
    }
  });

  function bulkSheetHtml(nameValue, textValue) {
    return '<label class="field"><span>Kategoriya nomi</span><input class="input" id="vc-name" value="' + App.esc(nameValue || '') + '" placeholder="Masalan: Hayvonlar"></label>' +
      '<label class="field"><span>So\'zlar (har biri: <code>1) so\'z - tarjima</code>)</span>' +
      '<textarea class="textarea" id="vc-text" rows="9" placeholder="1) cat - mushuk&#10;2) dog - it">' + App.esc(textValue || '') + '</textarea></label>' +
      '<button class="btn" id="vc-save">Saqlash</button>';
  }

  App.actions.vocabDbOptions = function(a) {
    var sh = App.sheet(
      '<button class="list-row" data-act="vocabUploadMD" data-arg=\'' + App.arg(a) + '\'>' +
        '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">MD fayl yuklash</div><div class="li-sub">Matn formatidagi bazani o\'qish</div></div>' +
      '</button>',
      { title: 'Baza qo\'shish' }
    );
  };

  App.actions.vocabUploadMD = function (a) {
    if (App._sheetNode) App.closeSheet();
    var inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = '.md';
    inp.onchange = function (e) {
      var file = e.target.files[0];
      if (!file) return;
      var defaultName = file.name.replace(/\.md$/i, '');
      var customName = prompt('Baza uchun nom kiriting:', defaultName);
      if (!customName || customName.trim() === '') return;
      var finalName = customName.trim();
      var reader = new FileReader();
      reader.onload = function (evt) {
        var text = evt.target.result;
        var mdFiles = {};
        try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + a.lang) || '{}'); } catch(ex) {}
        mdFiles[finalName] = text;
        localStorage.setItem('vocab_md_files_v1_' + a.lang, JSON.stringify(mdFiles));
        /* Fayl QAYSI papkada yuklangan bo'lsa o'sha yerda qoladi */
        var fmap = mdFolders(a.lang);
        fmap[finalName] = a.folder || '';
        setMdFolders(a.lang, fmap);
        App.toast('Baza yuklandi!');
        App.go('vocab', { lang: a.lang, folder: a.folder || '' });
      };
      reader.readAsText(file);
    };
    inp.click();
  };

  App.actions.vocabDeleteMD = function (a) {
    if (confirm(a.mdId + ' ni o\'chirishni xohlaysizmi?')) {
      var mdFiles = {};
      try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + a.lang) || '{}'); } catch(ex) {}
      var wasIn = mdFolderOf(a.lang, a.mdId);
      delete mdFiles[a.mdId];
      localStorage.setItem('vocab_md_files_v1_' + a.lang, JSON.stringify(mdFiles));
      // Papka yozuvi ham tozalansin — aks holda xarita asta-sekin axlat to'playdi
      var fmap = mdFolders(a.lang);
      delete fmap[a.mdId];
      setMdFolders(a.lang, fmap);
      App.go('vocab', { lang: a.lang, folder: wasIn });
    }
  };

  App.view('vocab_md_read', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang || 'english';
      var fname = params.mdId;
      var mdFiles = {};
      try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + lang) || '{}'); } catch(ex) {}
      var content = mdFiles[fname];
      var contentHtml = content ? App._mdToHtml(content) : 'Fayl topilmadi yoki yuklanmadi.';
      var title = fname || 'MD Fayl';
      page.innerHTML = topbar(title, 'vocab', { lang: lang }) +
        '<div style="overflow-x:auto; padding-bottom:30px;">' +
          '<div class="md-content">' + contentHtml + '</div>' +
        '</div>';
      App.icons(page);
    }
  });

  /* Boostdayga yuborish — kategoriyalardan bir nechtasini tanlash (mavjud
     "mashg'ulotlar" ro'yxatidan) yoki pastdagi "Boshqa" maydoniga erkin matn
     yozish. Sport'dagi kabi tanlangan nomlar tegishli mavzu (english/russian)
     kanaliga bitta har-kungi rejaga vazifa sifatida qo'shiladi. */
  App.actions.vocabSendSheet = function (a) {
    var lang = a.lang === 'russian' ? 'russian' : 'english';
    loadDict(lang).then(function () {
      var cats = V.order.slice();
      var selected = {};
      var today = new Date();
      var todayStr = today.getFullYear() + '-' + ('0' + (today.getMonth() + 1)).slice(-2) + '-' + ('0' + today.getDate()).slice(-2);
      var html = '<p class="muted" style="font-size:12.5px;margin:0 0 12px">Kategoriyalardan birini (yoki bir nechtasini) tanlang, yoki pastda "Boshqa"ga o\'zingiz yozing.</p>' +
        '<div id="vs-list">' + (cats.length ? cats.map(function (c) {
          return '<button class="list-row vs-row" data-cat="' + App.esc(c) + '">' +
            '<span class="li-ic vs-check" style="border:1px solid var(--border);background:none"></span>' +
            '<div class="li-main"><div class="li-title">' + App.esc(c) + '</div></div></button>';
        }).join('') : '<p class="muted" style="font-size:13px">Kategoriya yo\'q.</p>') + '</div>' +
        '<label class="field" style="margin-top:12px"><span>Boshqa (ixtiyoriy, erkin matn)</span>' +
        '<input class="input" id="vs-other" placeholder="Masalan: 20 ta yangi so\'z yodlash"></label>' +
        '<div class="flex" style="gap:8px">' +
        '<label class="field" style="flex:1"><span>Qaysi sanaga</span><input class="input" type="date" id="vs-date" value="' + todayStr + '" min="' + todayStr + '"></label>' +
        '<label class="field" style="width:110px"><span>Vaqt</span><input class="input" type="time" id="vs-time" value="08:00"></label>' +
        '</div>' +
        '<button class="btn" id="vs-send" style="margin-top:4px">Yuborish</button>';
      var sh = App.sheet(html, { title: (lang === 'russian' ? '🇷🇺 Rus tili' : '🇬🇧 Ingliz tili') + ' — yuborish' });
      App.icons(sh);

      sh.querySelectorAll('.vs-row').forEach(function (row) {
        row.onclick = function () {
          var cat = row.getAttribute('data-cat');
          var on = !selected[cat];
          selected[cat] = on;
          var chk = row.querySelector('.vs-check');
          chk.style.background = on ? 'var(--accent)' : 'none';
          chk.innerHTML = on ? '<span data-icon="check" data-icon-size="13" style="color:#fff"></span>' : '';
          App.icons(chk);
        };
      });

      sh.querySelector('#vs-send').onclick = function () {
        var items = Object.keys(selected).filter(function (c) { return selected[c]; }).map(function (c) { return { text: c }; });
        var other = sh.querySelector('#vs-other').value.trim();
        if (other) items.push({ text: other });
        if (!items.length) return App.toast('Kamida bittasini tanlang yoki yozing');
        var date = sh.querySelector('#vs-date').value;
        if (!date) return App.toast('Sanani tanlang');
        var time = sh.querySelector('#vs-time').value || '08:00';
        if (!window.BoostPush) return App.toast('Boostday moduli yuklanmagan');
        var btn = sh.querySelector('#vs-send'); btn.disabled = true; btn.textContent = 'Yuborilmoqda...';
        var title = (lang === 'russian' ? '🇷🇺 Rus tili' : '🇬🇧 Ingliz tili') + ' mashg\'ulotlari';
        BoostPush.pushTasks(lang, title, items, { date: date, time: time }).then(function () {
          App.closeSheet(); App.toast('✅ ' + items.length + ' ta narsa ' + date + ' kuniga yuborildi');
        }).catch(function (e) {
          btn.disabled = false; btn.textContent = 'Yuborish';
          App.toast('⚠️ ' + e.message);
        });
      };
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  App.actions.vocabAddCat = function (a) {
    /* Papka ichida turgan bo'lsak nom maydoni "курс/чтение/" bilan
       to'ldiriladi — foydalanuvchi faqat oxirini yozadi va lug'at
       o'sha papkada paydo bo'ladi. Yangi ichma-ich papka ochish uchun
       yana "/" qo'shsa bo'ladi. */
    var pre = a.folder ? a.folder + '/' : '';
    var sh = App.sheet(bulkSheetHtml(pre, ''), { title: 'Yangi kategoriya' });
    var nameEl = sh.querySelector('#vc-name');
    if (pre) setTimeout(function () {
      nameEl.focus();
      try { nameEl.setSelectionRange(pre.length, pre.length); } catch (e) {}
    }, 350);
    sh.querySelector('#vc-save').onclick = function () {
      var name = nameEl.value.trim().replace(/\/+$/, '');
      var words = parseWords(sh.querySelector('#vc-text').value);
      if (!name) return App.toast('Kategoriya nomini kiriting');
      if (!words.length) return App.toast('Kamida bitta so\'z kerak — formatni tekshiring');
      App.call('save_dict_cat', { lang: a.lang, category: name, words: words }).then(function () {
        App.closeSheet(); App.toast('✅ ' + words.length + ' ta so\'z saqlandi'); App.reload();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
  };

  App.actions.vocabCatManage = function (a) {
    var html =
      '<button class="list-row" data-act="vocabCatReplace" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="upload" data-icon-size="15"></span><div class="li-main"><div class="li-title">So\'zlarni yangilash</div></div></button>' +
      '<button class="list-row" data-act="vocabCatRename" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="edit" data-icon-size="15"></span><div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="vocabCatHide" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="close" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Yashirish</div>' +
      '<div class="li-sub">Ro\'yxatdan olinadi, so\'zlar saqlanadi</div></div></button>' +
      '<button class="list-row" data-act="vocabCatDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)"><span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span><div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
    App.sheet(html, { title: a.cat });
  };
  App.actions.vocabCatReplace = function (a) {
    App.closeSheet();
    var existing = (V.data[a.cat] || []).map(function (w, i) { return (i + 1) + ') ' + w.ru + ' - ' + w.uz; }).join('\n');
    var sh = App.sheet(bulkSheetHtml(a.cat, existing), { title: 'So\'zlarni yangilash' });
    sh.querySelector('#vc-name').setAttribute('disabled', 'disabled');
    sh.querySelector('#vc-save').onclick = function () {
      var words = parseWords(sh.querySelector('#vc-text').value);
      if (!words.length) return App.toast('Kamida bitta so\'z kerak');
      App.call('save_dict_cat', { lang: a.lang, category: a.cat, words: words }).then(function () {
        App.closeSheet(); App.toast('✅ ' + words.length + ' ta so\'z saqlandi'); App.reload();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
  };
  App.actions.vocabCatRename = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Nomini o\'zgartirish', label: 'Yangi nom', value: a.cat }, function (name) {
      App.call('rename_dict_cat', { lang: a.lang, old_name: a.cat, new_name: name }).then(App.reload).catch(function (e) { App.toast('⚠️ ' + e.message); });
    });
  };
  App.actions.vocabCatDelete = function (a) {
    App.confirm('"' + a.cat + '" kategoriyasi va undagi barcha so\'zlar o\'chiriladi.', function () {
      App.call('delete_dict_cat', { lang: a.lang, category: a.cat }).then(function () { App.closeSheet(); App.reload(); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Oraliq (batch) tanlash — barcha metodlar shu oraliqda ishlaydi ---------- */
  function rangeKey(lang, cat) { return lang + '::' + cat; }
  function rangeAll() { try { return JSON.parse(localStorage.getItem('vocab_range_v1') || '{}') || {}; } catch (e) { return {}; } }
  function getRange(lang, cat, total) {
    var r = rangeAll()[rangeKey(lang, cat)];
    if (!r) return { from: 1, to: total };
    return { from: Math.max(1, Math.min(r.from, total)), to: Math.max(1, Math.min(r.to, total)) };
  }
  function setRange(lang, cat, from, to) {
    var all = rangeAll(); all[rangeKey(lang, cat)] = { from: from, to: to };
    localStorage.setItem('vocab_range_v1', JSON.stringify(all));
  }
  /* Tanlangan oraliqdagi so'zlar (asl tartibda — aralashtirilmaydi) */
  function rangedWords(lang, cat) {
    var words = V.data[cat] || [];
    if (!words.length) return [];
    var r = getRange(lang, cat, words.length);
    return words.slice(r.from - 1, r.to);
  }

  App.actions.vocabRange = function (a) {
    var total = (V.data[a.cat] || []).length;
    var r = getRange(a.lang, a.cat, total);
    var html =
      '<p class="muted" style="font-size:13px;margin:0 0 12px">Jami ' + total + ' ta so\'z. Mashqlar faqat shu oraliqda ishlaydi.</p>' +
      '<div class="flex" style="gap:8px;margin-bottom:12px">' +
      '<label class="field" style="flex:1;margin:0"><span>Dan</span><input class="input" type="number" id="vr-from" min="1" max="' + total + '" value="' + r.from + '"></label>' +
      '<label class="field" style="flex:1;margin:0"><span>Gacha</span><input class="input" type="number" id="vr-to" min="1" max="' + total + '" value="' + r.to + '"></label>' +
      '</div>' +
      '<div class="flex" style="flex-wrap:wrap;gap:6px;margin-bottom:14px" id="vr-quick"></div>' +
      '<button class="btn" id="vr-save">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Oraliqni tanlash' });
    var quick = sh.querySelector('#vr-quick');
    var chunks = '<button class="chip-btn" data-f="1" data-t="' + total + '">Barchasi</button>';
    for (var i = 0; i < total; i += 20) {
      chunks += '<button class="chip-btn" data-f="' + (i + 1) + '" data-t="' + Math.min(total, i + 20) + '">' + (i + 1) + '-' + Math.min(total, i + 20) + '</button>';
    }
    quick.innerHTML = chunks;
    quick.querySelectorAll('button').forEach(function (b) {
      b.onclick = function () {
        sh.querySelector('#vr-from').value = b.getAttribute('data-f');
        sh.querySelector('#vr-to').value = b.getAttribute('data-t');
      };
    });
    sh.querySelector('#vr-save').onclick = function () {
      var f = parseInt(sh.querySelector('#vr-from').value, 10) || 1;
      var t = parseInt(sh.querySelector('#vr-to').value, 10) || total;
      f = Math.max(1, Math.min(f, total)); t = Math.max(1, Math.min(t, total));
      if (f > t) { var tmp = f; f = t; t = tmp; }
      setRange(a.lang, a.cat, f, t);
      App.closeSheet(); App.reload();
    };
  };

  /* ---------- Amaliyot tanlash ---------- */
  function methodBtn(v, lang, cat, icon, label, cls) {
    return '<button class="btn ' + (cls || 'sec') + '" data-act="go" data-arg=\'' + App.arg({ v: v, p: { lang: lang, cat: cat } }) +
      '\'><span data-icon="' + icon + '" data-icon-size="16"></span>' + label + '</button>';
  }
  App.view('vocab_practice', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var loaded = V.lang === lang && V.data[cat];
      var total = loaded ? V.data[cat].length : null;
      var r = loaded ? getRange(lang, cat, total) : null;
      var full = r && r.from === 1 && r.to === total;

      var due = loaded ? srsDue(lang, cat).length : 0;
      var prog = loaded ? srsProgress(lang, cat) : null;

      page.innerHTML = topbar(cat, 'vocab', { lang: lang }) +
        (loaded
          ? '<div class="srs-bar"><div class="srs-top"><span>O\'zlashtirildi</span>' +
            '<b>' + prog.learned + '/' + prog.total + '</b></div>' +
            '<div class="bar"><i style="width:' + (prog.total ? Math.round(prog.learned * 100 / prog.total) : 0) + '%"></i></div></div>' +
            '<button class="list-row" data-act="vocabRange" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' style="margin-bottom:14px">' +
            '<span class="li-ic" data-icon="list" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">Oraliq: ' + r.from + '–' + r.to + (full ? ' (barchasi)' : '') + '</div>' +
            '<div class="li-sub">' + (r.to - r.from + 1) + ' ta so\'z · jami ' + total + '</div></div>' +
            '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>'
          : '') +
        '<div class="btn-row" style="flex-direction:column;gap:10px">' +
        (due
          ? '<button class="btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_flash', p: { lang: lang, cat: cat, src: 'due' } }) +
            '\'><span data-icon="clock" data-icon-size="16"></span>Bugun takrorlash (' + due + ')</button>'
          : (loaded ? '<p class="muted" style="font-size:12.5px;margin:0 0 2px;text-align:center">✅ Bugungi takrorlash tugagan</p>' : '')) +
        methodBtn('vocab_flash', lang, cat, 'refresh', 'Flashcardlar', 'sec') +
        methodBtn('vocab_memo', lang, cat, 'check', 'Yodlash (svayp)') +
        methodBtn('vocab_speaker', lang, cat, 'volume', 'Tinglash (Speaker)') +
        methodBtn('vocab_speech', lang, cat, 'mic', 'Ovozli lug\'at') +
        methodBtn('vocab_quiz', lang, cat, 'check', 'Test (4 variantdan)') +
        methodBtn('vocab_list', lang, cat, 'list', 'So\'zlar ro\'yxati') +
        '</div>';
      App.icons(page);
      if (!loaded) loadDict(lang).then(App.reload);
    }
  });

  /* ---------- Yodlash (svayp ro'yxati) — chapga: bilmadim, o'ngga: bildim ---------- */
  var MEMO = { good: 0, bad: 0, startedAt: 0, lang: '', cat: '', logged: false };
  var QZ = null;   // vocab_quiz joriy sessiyasi — "Tugatish" tugmasi shundan o'qiydi

  App.view('vocab_memo', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var start = function () {
        var words = rangedWords(lang, cat);
        if (!words.length) { App.toast('Bu oraliqda so\'z yo\'q'); App.go('vocab_practice', { lang: lang, cat: cat }); return; }
        MEMO = { good: 0, bad: 0, startedAt: Date.now(), lang: lang, cat: cat, logged: false };
        page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }, finishBtnHtml('vocabMemoFinish')) +
          '<p class="muted" style="font-size:12.5px;margin:-6px 0 12px" id="mt-count">' + words.length + ' ta qoldi</p>' +
          '<p class="muted" style="font-size:11.5px;margin:0 0 12px">Chapga suring — bilmadim, o\'ngga — bildim. Bosilsa ovozda o\'qiydi.</p>' +
          '<div id="mt-list"></div>' +
          '<div id="mt-done" class="hidden">' + App.empty({ icon: 'trophy', title: 'Tugadi!', text: 'Bu oraliqdagi barcha so\'zlar ko\'rib chiqildi.' }) +
          '<button class="btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: { lang: lang, cat: cat } }) + '\'>Ortga</button></div>';
        App.icons(page);
        var box = App.el('mt-list');
        box.innerHTML = words.map(function (w, i) {
          return '<div class="mt-item" data-i="' + i + '">' +
            '<div class="mt-bg"><span class="mt-no">✕ Bilmadim</span><span class="mt-yes">Bildim ✓</span></div>' +
            '<div class="mt-content"><span class="mt-w">' + App.esc(w.ru) + '</span><span class="mt-t">' + App.esc(w.uz) + '</span></div></div>';
        }).join('');
        box.querySelectorAll('.mt-item').forEach(function (el) {
          attachMemoSwipe(el, words[+el.getAttribute('data-i')], lang, cat);
        });
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  function memoLeft() {
    var box = App.el('mt-list'); if (!box) return;
    var left = box.querySelectorAll('.mt-item').length;
    var cnt = App.el('mt-count');
    if (cnt) cnt.textContent = left + ' ta qoldi';
    if (left === 0) {
      box.classList.add('hidden'); if (cnt) cnt.classList.add('hidden');
      App.el('mt-done').classList.remove('hidden');
      if (!MEMO.logged) {
        logVocabProgress(MEMO.lang, MEMO.cat, MEMO.good + MEMO.bad, 'memo', MEMO.startedAt, { good: MEMO.good, bad: MEMO.bad });
        MEMO.logged = true;
      }
    }
  }

  App.actions.vocabMemoFinish = function () {
    if (!MEMO.logged) {
      logVocabProgress(MEMO.lang, MEMO.cat, MEMO.good + MEMO.bad, 'memo', MEMO.startedAt, { good: MEMO.good, bad: MEMO.bad });
      MEMO.logged = true;
    }
    App.go('vocab_practice', { lang: MEMO.lang, cat: MEMO.cat });
  };

  function attachMemoSwipe(el, word, lang, cat) {
    var startX = 0, dx = 0, dragging = false, moved = false;
    var bg = el.querySelector('.mt-bg');
    function begin(x) { startX = x; dragging = true; moved = false; el.style.transition = 'none'; }
    function move(x) {
      if (!dragging) return;
      dx = x - startX;
      if (Math.abs(dx) > 6) moved = true;
      el.style.transform = 'translateX(' + dx + 'px)';
      bg.classList.toggle('right', dx > 0);
      bg.classList.toggle('left', dx < 0);
      bg.style.opacity = Math.min(Math.abs(dx) / 100, 1);
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      el.style.transition = 'transform .28s ease, opacity .28s ease';
      if (Math.abs(dx) > 80) finishMemo(el, dx > 0, word, lang, cat);
      else { el.style.transform = 'translateX(0)'; bg.style.opacity = 0; }
      dx = 0;
    }
    el.addEventListener('touchstart', function (e) { begin(e.touches[0].clientX); }, { passive: true });
    el.addEventListener('touchmove', function (e) { move(e.touches[0].clientX); }, { passive: true });
    el.addEventListener('touchend', end);
    el.addEventListener('mousedown', function (e) { begin(e.clientX); });
    window.addEventListener('mousemove', function (e) { if (dragging) move(e.clientX); });
    window.addEventListener('mouseup', end);
    el.addEventListener('click', function () { if (!moved) speakWord(word.ru, lang); });
  }

  function finishMemo(el, known, word, lang, cat) {
    el.style.transform = 'translateX(' + (known ? '120%' : '-120%') + ')';
    el.style.opacity = '0';
    srsUpdate(lang, cat, word.ru, known);
    if (known) { MEMO.good++; App.call('remove_mistake', { lang: lang, category: cat, ru: word.ru }).catch(function () {}); }
    else { MEMO.bad++; App.call('add_mistake', { lang: lang, category: cat, ru: word.ru, uz: word.uz }).catch(function () {}); }
    setTimeout(function () { el.remove(); memoLeft(); }, 300);
  }

  function speakWord(txt, lang) {
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(txt);
      u.lang = LABEL[lang].tts1; u.rate = 0.95;
      window.speechSynthesis.speak(u);
    } catch (e) {}
  }

  /* ---------- Tinglash (Speaker): bosilsa o'qiydi, Auto Play ketma-ket ---------- */
  var SPK = { playing: false, idx: -1, timer: null, list: [], lang: 'russian', cat: '', startedAt: 0, logged: false };
  App.view('vocab_speaker', {
    nav: 'languages',
    /* Auto Play zanjiri (utterance -> setTimeout -> keyingi so'z) bo'limdan
       chiqilganda ham davom etib ketmasligi uchun aniq to'xtatiladi. */
    leave: function () { try { spkStop(); } catch (e) {} },
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var start = function () {
        var words = rangedWords(lang, cat);
        if (!words.length) { App.toast('Bu oraliqda so\'z yo\'q'); App.go('vocab_practice', { lang: lang, cat: cat }); return; }
        SPK = { playing: false, idx: -1, timer: null, list: words, lang: lang, cat: cat, startedAt: Date.now(), logged: false };
        page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }, finishBtnHtml('vocabSpeakerFinish')) +
          '<div class="flex" style="gap:10px;margin-bottom:12px">' +
          '<button class="btn" id="spk-toggle" style="flex:1"><span data-icon="play" data-icon-size="16"></span><span id="spk-txt">Auto Play</span></button>' +
          '<label class="field" style="margin:0;width:110px"><span>Oraliq (s)</span><input class="input" type="number" id="spk-int" min="1" max="10" value="2"></label>' +
          '</div>' +
          '<p class="muted" style="font-size:11.5px;margin:0 0 10px">' + words.length + ' ta so\'z · so\'zga bosing — o\'qiydi</p>' +
          '<div id="spk-list"></div>';
        App.icons(page);
        var box = App.el('spk-list');
        box.innerHTML = words.map(function (w, i) {
          return '<button class="list-row spk-item" data-i="' + i + '">' +
            '<div class="li-main"><div class="li-title">' + App.esc(w.ru) + '</div><div class="li-sub">' + App.esc(w.uz) + '</div></div>' +
            '<span class="li-chev" data-icon="volume" data-icon-size="16"></span></button>';
        }).join('');
        App.icons(box);
        box.querySelectorAll('.spk-item').forEach(function (b) {
          b.onclick = function () { spkStop(); spkHighlight(+b.getAttribute('data-i')); speakWord(words[+b.getAttribute('data-i')].ru, lang); };
        });
        App.el('spk-toggle').onclick = function () { SPK.playing ? spkStop() : spkStart(); };
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  function spkHighlight(i) {
    document.querySelectorAll('.spk-item.active').forEach(function (e) { e.classList.remove('active'); });
    var el = document.querySelector('.spk-item[data-i="' + i + '"]');
    if (el) { el.classList.add('active'); el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  }
  function spkStart() {
    SPK.playing = true;
    var t = App.el('spk-txt'); if (t) t.textContent = 'To\'xtatish';
    var b = App.el('spk-toggle'); if (b) b.classList.add('danger');
    if (SPK.idx < 0 || SPK.idx >= SPK.list.length - 1) SPK.idx = -1;
    spkNext();
  }
  function spkStop() {
    SPK.playing = false;
    try { window.speechSynthesis.cancel(); } catch (e) {}
    if (SPK.timer) clearTimeout(SPK.timer);
    var t = App.el('spk-txt'); if (t) t.textContent = 'Auto Play';
    var b = App.el('spk-toggle'); if (b) b.classList.remove('danger');
  }
  App.actions.vocabSpeakerFinish = function () {
    spkStop();
    if (!SPK.logged) {
      var count = SPK.idx >= 0 ? SPK.idx + 1 : 0;
      logVocabProgress(SPK.lang, SPK.cat, count, 'speaker', SPK.startedAt, {});
      SPK.logged = true;
    }
    App.go('vocab_practice', { lang: SPK.lang, cat: SPK.cat });
  };
  function spkNext() {
    if (!SPK.playing) return;
    SPK.idx++;
    if (SPK.idx >= SPK.list.length) {
      spkStop();
      if (!SPK.logged) {
        logVocabProgress(SPK.lang, SPK.cat, SPK.list.length, 'speaker', SPK.startedAt, {});
        SPK.logged = true;
      }
      return;
    }
    if (!App.el('spk-list')) { SPK.playing = false; return; } // sahifa almashgan
    spkHighlight(SPK.idx);
    var u = new SpeechSynthesisUtterance(SPK.list[SPK.idx].ru);
    u.lang = LABEL[SPK.lang].tts1; u.rate = 0.9;
    u.onend = function () {
      if (!SPK.playing) return;
      var inp = App.el('spk-int');
      var delay = (parseInt(inp && inp.value, 10) || 2) * 1000;
      SPK.timer = setTimeout(spkNext, delay);
    };
    try { window.speechSynthesis.speak(u); } catch (e) { spkStop(); }
  }

  /* ---------- Ovozli lug'at: tarjimasi ko'rsatiladi, so'zni ovoz bilan aytasiz ---------- */
  var SR = { list: [], idx: 0, good: 0, bad: 0, rec: null, lang: 'russian', cat: '', busy: false, startedAt: 0, logged: false };
  App.view('vocab_speech', {
    nav: 'languages',
    /* `App._stopSpeech()` faqat OVOZ CHIQARISHNI (speechSynthesis) to'xtatadi —
       mikrofonli TANISH (SpeechRecognition) undan mustaqil ishlaydi. Ilgak
       bo'lmagani uchun mashqni tark etganda mikrofon ochiq qolib ketardi va
       keyingi bo'limlarda ham eshitib turardi. Endi aniq to'xtatiladi. */
    leave: function () {
      try { if (SR.rec) SR.rec.abort ? SR.rec.abort() : SR.rec.stop(); } catch (e) {}
      SR.busy = false;
    },
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var start = function () {
        var words = rangedWords(lang, cat);
        if (!words.length) { App.toast('Bu oraliqda so\'z yo\'q'); App.go('vocab_practice', { lang: lang, cat: cat }); return; }
        var Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
        SR = { list: words, idx: 0, good: 0, bad: 0, rec: null, lang: lang, cat: cat, busy: false, startedAt: Date.now(), logged: false };
        page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }, finishBtnHtml('vocabSpeechFinish')) +
          (Rec ? '' : '<p class="muted" style="font-size:13px;margin:0 0 12px">⚠️ Brauzeringiz mikrofonli tanishni qo\'llamaydi — javobni yozib ham tekshirsangiz bo\'ladi.</p>') +
          '<div class="stat-strip" style="margin:0 0 14px">' +
          '<div class="s"><div class="n" id="sr-idx">1/' + words.length + '</div><div class="l">Progress</div></div>' +
          '<div class="s"><div class="n" style="color:var(--success)" id="sr-good">0</div><div class="l">To\'g\'ri</div></div>' +
          '<div class="s"><div class="n" style="color:var(--danger)" id="sr-bad">0</div><div class="l">Xato</div></div>' +
          '</div>' +
          '<div class="card" style="text-align:center;padding:22px 16px">' +
          '<div class="muted" style="font-size:11.5px;letter-spacing:1px;text-transform:uppercase">O\'zbek tili</div>' +
          '<div id="sr-uz" style="font-size:22px;font-weight:800;margin:8px 0 4px"></div>' +
          '<div id="sr-hint" class="muted" style="font-size:12.5px;min-height:18px"></div>' +
          '</div>' +
          '<div style="text-align:center;margin:18px 0">' +
          '<button class="ls-speaker" id="sr-mic" aria-label="Gapirish"><span data-icon="mic" data-icon-size="32"></span></button></div>' +
          '<input class="input" id="sr-typed" placeholder="Yoki javobni yozing..." autocomplete="off" style="text-align:center">' +
          '<div class="btn-row"><button class="btn sec" id="sr-show">Javobni ko\'rish</button>' +
          '<button class="btn" id="sr-next">Keyingisi</button></div>';
        App.icons(page);
        if (Rec) {
          var rec = new Rec();
          rec.lang = LABEL[lang].tts1; rec.continuous = false; rec.interimResults = false;
          rec.onresult = function (e) {
            var said = (e.results[0][0].transcript || '').trim();
            App.el('sr-mic').classList.remove('listening');
            srCheck(said);
          };
          rec.onerror = function () { App.el('sr-mic').classList.remove('listening'); SR.busy = false; };
          rec.onend = function () { App.el('sr-mic').classList.remove('listening'); SR.busy = false; };
          SR.rec = rec;
        }
        App.el('sr-mic').onclick = function () {
          if (!SR.rec) return App.toast('Mikrofonli tanish mavjud emas');
          if (SR.busy) { try { SR.rec.stop(); } catch (e) {} return; }
          SR.busy = true; this.classList.add('listening');
          try { SR.rec.start(); } catch (e) { SR.busy = false; this.classList.remove('listening'); }
        };
        App.el('sr-typed').onkeydown = function (e) { if (e.key === 'Enter') { srCheck(this.value); this.value = ''; } };
        App.el('sr-show').onclick = function () {
          App.el('sr-hint').innerHTML = '<b style="color:var(--text)">' + App.esc(SR.list[SR.idx].ru) + '</b>';
          speakWord(SR.list[SR.idx].ru, SR.lang);
        };
        App.el('sr-next').onclick = function () { srAdvance(); };
        srRender();
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  function srNorm(s) { return String(s || '').toLowerCase().replace(/[^\wа-яё]/gi, ''); }
  
  function levenshtein(a, b) {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    var matrix = [];
    for (var i = 0; i <= b.length; i++) matrix[i] = [i];
    for (var j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (var i = 1; i <= b.length; i++) {
      for (var j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1));
        }
      }
    }
    return matrix[b.length][a.length];
  }
  function srSimilarity(said, target) {
    var a = srNorm(said), b = srNorm(target);
    if (!a && !b) return 100;
    if (!a || !b) return 0;
    var dist = levenshtein(a, b);
    var maxLen = Math.max(a.length, b.length);
    return Math.max(0, Math.round((1 - dist / maxLen) * 100));
  }

  function srRender() {
    if (!App.el('sr-uz')) return;
    App.el('sr-uz').textContent = SR.list[SR.idx].uz;
    App.el('sr-hint').textContent = '';
    App.el('sr-idx').textContent = (SR.idx + 1) + '/' + SR.list.length;
    App.el('sr-good').textContent = SR.good;
    App.el('sr-bad').textContent = SR.bad;
    var t = App.el('sr-typed'); if (t) t.value = '';
  }

  function srCheck(said) {
    if (!App.el('sr-hint')) return;
    var target = SR.list[SR.idx].ru;
    var sim = srSimilarity(said, target);
    var ok = sim >= 75; // 75% o'xshasa qabul qilinadi
    var color = sim >= 75 ? 'var(--success)' : (sim >= 40 ? 'var(--warning, #eab308)' : 'var(--danger)');
    
    if (ok) {
      SR.good++;
      App.el('sr-hint').innerHTML = '<span style="color:' + color + ';font-weight:700">✓ Qabul qilindi (' + sim + '%): ' + App.esc(target) + '</span>';
      setTimeout(srAdvance, 900);
    } else {
      SR.bad++;
      App.el('sr-hint').innerHTML = '<span style="color:' + color + ';font-weight:700">✕ ' + App.esc(said || '—') + ' (' + sim + '%)</span> → <b style="color:var(--text)">' + App.esc(target) + '</b>';
    }
    App.el('sr-good').textContent = SR.good;
    App.el('sr-bad').textContent = SR.bad;
  }
  function srAdvance() {
    SR.idx++;
    if (SR.idx >= SR.list.length) {
      SR.idx = SR.list.length - 1;
      App.toast('✅ Tugadi: ' + SR.good + ' to\'g\'ri, ' + SR.bad + ' xato');
      if (!SR.logged) {
        logVocabProgress(SR.lang, SR.cat, SR.good + SR.bad, 'speech', SR.startedAt, { good: SR.good, bad: SR.bad });
        SR.logged = true;
      }
      return;
    }
    srRender();
  }
  App.actions.vocabSpeechFinish = function () {
    if (!SR.logged) {
      logVocabProgress(SR.lang, SR.cat, SR.good + SR.bad, 'speech', SR.startedAt, { good: SR.good, bad: SR.bad });
      SR.logged = true;
    }
    App.go('vocab_practice', { lang: SR.lang, cat: SR.cat });
  };

  /* ---------- So'zlar ro'yxati: qidiruv + bitta so'zni tahrirlash ---------- */
  function saveWords(lang, cat, words) {
    return App.call('save_dict_cat', { lang: lang, category: cat, words: words }).then(function () {
      V.data[cat] = words.slice();
    });
  }

  App.view('vocab_list', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }) +
        '<div class="flex" style="gap:8px;margin-bottom:12px">' +
        '<input class="input" id="vl-q" placeholder="Qidirish..." style="flex:1">' +
        '<button class="icon-btn" id="vl-add" title="So\'z qo\'shish"><span data-icon="plus" data-icon-size="18"></span></button>' +
        '</div>' +
        '<p class="muted" id="vl-count" style="font-size:12.5px;margin:0 0 8px"></p>' +
        '<div id="vl-items"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      var render = function () {
        var box = App.el('vl-items'); if (!box) return;
        var words = V.data[cat] || [];
        var q = (App.el('vl-q').value || '').trim().toLowerCase();
        var shown = q ? words.filter(function (w) {
          return (w.ru + ' ' + w.uz).toLowerCase().indexOf(q) >= 0;
        }) : words;

        App.el('vl-count').textContent = q
          ? shown.length + ' ta topildi (jami ' + words.length + ')'
          : words.length + ' ta so\'z';

        if (!shown.length) {
          box.innerHTML = App.empty({ icon: 'list', title: q ? 'Topilmadi' : 'So\'z yo\'q', text: q ? 'Boshqa so\'z bilan qidiring.' : '+ tugmasi bilan qo\'shing.' });
          App.icons(box);
          return;
        }
        box.innerHTML = shown.map(function (w) {
          var i = words.indexOf(w);
          return '<button class="list-row" data-i="' + i + '"><div class="li-main">' +
            '<div class="li-title">' + App.esc(w.ru) + '</div><div class="li-sub">' + App.esc(w.uz) + '</div></div>' +
            '<span class="li-chev" data-icon="edit" data-icon-size="15"></span></button>';
        }).join('');
        App.icons(box);
        box.querySelectorAll('.list-row').forEach(function (b) {
          b.onclick = function () { wordSheet(page, lang, cat, +b.getAttribute('data-i'), render); };
        });
      };

      App.el('vl-q').oninput = render;
      App.el('vl-add').onclick = function () { wordSheet(page, lang, cat, -1, render); };
      if (V.lang === lang && V.data[cat]) render(); else loadDict(lang).then(render);
    }
  });

  /* ---------- Test rejimi: 4 variantdan to'g'risini tanlash ---------- */
  App.view('vocab_quiz', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var start = function () {
        var pool = V.data[cat] || [];
        var words = rangedWords(lang, cat);
        if (words.length < 4) { App.toast('Kamida 4 ta so\'z kerak'); App.go('vocab_practice', { lang: lang, cat: cat }); return; }
        var st = { list: shuffleArr(words), pool: pool, i: 0, good: 0, bad: 0, dir: 'l1', startedAt: Date.now(), lang: lang, cat: cat };
        QZ = st;

        function draw() {
          if (st.i >= st.list.length) {
            var pct = Math.round(st.good * 100 / st.list.length);
            page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }) +
              '<div style="text-align:center;padding-top:8px"><div class="res-circle"><span>' + pct + '%</span></div>' +
              '<h2 style="margin:0 0 20px">' + (pct >= 80 ? 'Ajoyib!' : pct >= 50 ? 'Yaxshi' : 'Takrorlang') + '</h2>' +
              '<div class="stat-strip" style="max-width:280px;margin:0 auto 24px">' +
              '<div class="s"><div class="n" style="color:var(--success)">' + st.good + '</div><div class="l">To\'g\'ri</div></div>' +
              '<div class="s"><div class="n" style="color:var(--danger)">' + st.bad + '</div><div class="l">Xato</div></div>' +
              '<div class="s"><div class="n">' + st.list.length + '</div><div class="l">Jami</div></div></div>' +
              '<button class="btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: { lang: lang, cat: cat } }) + '\'>Ortga</button></div>';
            App.icons(page);
            if (window.Activity) Activity.mark();
            App.call('log_activity', {
              section: 'vocab', object: cat, amount: st.list.length, unit: 'so\'z',
              duration: Math.round((Date.now() - st.startedAt) / 1000),
              meta: { lang: lang, good: st.good, bad: st.bad, mode: 'quiz' }
            }).catch(function () {});
            return;
          }
          var w = st.list[st.i];
          var isL1 = st.dir === 'l1';
          var ask = isL1 ? w.ru : w.uz;
          var answer = isL1 ? w.uz : w.ru;
          // Chalg'ituvchi variantlar — shu kategoriyaning boshqa so'zlaridan
          var others = st.pool.filter(function (x) { return x.ru !== w.ru; });
          var wrongs = shuffleArr(others).slice(0, 3).map(function (x) { return isL1 ? x.uz : x.ru; });
          var opts = shuffleArr([answer].concat(wrongs));

          page.innerHTML = '<div class="topbar" style="margin:-16px -15px 12px">' +
            '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: { lang: lang, cat: cat } }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
            '<h1>' + (st.i + 1) + ' / ' + st.list.length + '</h1>' +
            '<span class="sub" style="font-weight:700;color:var(--success);margin-right:8px">' + st.good + '</span>' +
            finishBtnHtml('vocabQuizFinish') + '</div>' +
            '<div class="card" style="text-align:center;padding:24px 16px;margin-bottom:16px">' +
            '<div class="muted" style="font-size:11.5px;text-transform:uppercase;letter-spacing:1px">' + (isL1 ? LABEL[lang].side1 : LABEL[lang].side2) + '</div>' +
            '<div style="font-size:23px;font-weight:800;margin-top:8px">' + App.esc(ask) + '</div></div>' +
            '<div id="vq-opts">' + opts.map(function (o) {
              return '<button class="qopt" data-v="' + App.esc(o) + '">' + App.esc(o) + '</button>';
            }).join('') + '</div>';
          App.icons(page);

          var box = App.el('vq-opts');
          box.querySelectorAll('.qopt').forEach(function (b) {
            b.onclick = function () {
              if (box._done) return; box._done = true;
              var ok = b.getAttribute('data-v') === answer;
              b.classList.add(ok ? 'correct' : 'wrong');
              if (!ok) {
                box.querySelectorAll('.qopt').forEach(function (x) {
                  if (x.getAttribute('data-v') === answer) x.classList.add('correct');
                });
              }
              box.querySelectorAll('.qopt').forEach(function (x) { x.classList.add('disabled'); });
              if (ok) st.good++; else st.bad++;
              srsUpdate(lang, cat, w.ru, ok);
              if (!ok) App.call('add_mistake', { lang: lang, category: cat, ru: w.ru, uz: w.uz }).catch(function () {});
              setTimeout(function () { st.i++; draw(); }, ok ? 650 : 1400);
            };
          });
        }
        draw();
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  App.actions.vocabQuizFinish = function () {
    if (!QZ) return;
    logVocabProgress(QZ.lang, QZ.cat, QZ.good + QZ.bad, 'quiz', QZ.startedAt, { good: QZ.good, bad: QZ.bad });
    var lang = QZ.lang, cat = QZ.cat;
    QZ = null;
    App.go('vocab_practice', { lang: lang, cat: cat });
  };

  function shuffleArr(a) {
    var x = a.slice();
    for (var i = x.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = x[i]; x[i] = x[j]; x[j] = t; }
    return x;
  }

  /* Bitta so'zni qo'shish / tahrirlash / o'chirish */
  function wordSheet(page, lang, cat, idx, onDone) {
    var words = (V.data[cat] || []).slice();
    var isNew = idx < 0;
    var w = isNew ? { ru: '', uz: '' } : words[idx];
    var l = LABEL[lang];
    var html =
      '<label class="field"><span>' + l.side1 + '</span><input class="input" id="w-ru" value="' + App.esc(w.ru) + '"></label>' +
      '<label class="field"><span>' + l.side2 + '</span><input class="input" id="w-uz" value="' + App.esc(w.uz) + '"></label>' +
      (isNew ? '<button class="btn" id="w-save">Qo\'shish</button>'
        : '<div class="btn-row"><button class="btn danger" id="w-del">O\'chirish</button><button class="btn" id="w-save">Saqlash</button></div>');
    var sh = App.sheet(html, { title: isNew ? 'Yangi so\'z' : 'So\'zni tahrirlash' });

    sh.querySelector('#w-save').onclick = function () {
      var ru = sh.querySelector('#w-ru').value.trim();
      var uz = sh.querySelector('#w-uz').value.trim();
      if (!ru || !uz) return App.toast('Ikkala maydonni to\'ldiring');
      if (isNew) words.push({ ru: ru, uz: uz }); else words[idx] = { ru: ru, uz: uz };
      saveWords(lang, cat, words).then(function () {
        App.closeSheet(); App.toast('✅ Saqlandi'); onDone();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
    if (!isNew) {
      sh.querySelector('#w-del').onclick = function () {
        App.confirm('"' + w.ru + '" o\'chirilsinmi?', function () {
          words.splice(idx, 1);
          saveWords(lang, cat, words).then(function () {
            App.closeSheet(); App.toast('O\'chirildi'); onDone();
          }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        }, { danger: true, yes: 'O\'chirish' });
      };
    }
  }

  /* ---------- Flashcard (svayp) ---------- */
  App.view('vocab_flash', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;

      // Xatolar rejimi: kategoriya emas, to'plangan xato so'zlar bilan mashq
      // `src=snapshot` — SAQLANGAN versiyadagi so'zlar (o'shanda xato bo'lganlar).
      if (params.src === 'mistakes' || params.src === 'snapshot') {
        var isSnap = params.src === 'snapshot';
        page.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
        var load = isSnap
          ? App.call('get_mistake_snapshot', null, { query: 'id=' + encodeURIComponent(params.id) })
              .then(function (j) { return j.words || []; })
          : loadMistakes(lang);
        load.then(function (list) {
          if (!list.length) { App.toast('So\'z yo\'q'); App.go('vocab_mistakes', { lang: lang }); return; }
          FC = {
            lang: lang, cat: null, src: params.src, list: list.slice(), idx: 0, flipped: false,
            good: 0, bad: 0, mistakes: [], mode: 'l1', muted: ls('vocab_muted', '0') === '1',
            startedAt: Date.now(), logged: false
          };
          renderFlashPage(page);
        }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        return;
      }

      var start = function () {
        // src=due — faqat bugun takrorlash kerak bo'lganlar
        var words = params.src === 'due' ? srsDue(lang, cat) : rangedWords(lang, cat);
        if (!words.length) {
          App.toast(params.src === 'due' ? 'Bugun takrorlanadigan so\'z yo\'q' : 'Bu oraliqda so\'z yo\'q');
          App.go('vocab_practice', { lang: lang, cat: cat }); return;
        }
        FC = {
          lang: lang, cat: cat, src: params.src === 'due' ? 'due' : '', list: words.slice(), idx: 0, flipped: false,
          good: 0, bad: 0, mistakes: [], mode: 'l1', muted: ls('vocab_muted', '0') === '1',
          startedAt: Date.now(), logged: false
        };
        renderFlashPage(page);
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  /* ---------- Takrorlash jadvali (SRS) ----------
     Bilgan so'z tobora uzoq oraliqda, bilmagani ertasiga qaytadan chiqadi.
     Holat localStorage'da (server bilan sinxron), schema o'zgarishi shart emas. */
  var SRS_KEY = 'vocab_srs_v1';
  var SRS_STEPS = [1, 3, 7, 16, 35, 90]; // kunlar

  function srsAll() {
    try { var v = JSON.parse(localStorage.getItem(SRS_KEY) || '{}'); return v && typeof v === 'object' ? v : {}; }
    catch (e) { return {}; }
  }
  function srsSave(o) { try { localStorage.setItem(SRS_KEY, JSON.stringify(o)); } catch (e) {} }
  function srsKey(lang, cat, ru) { return lang + '::' + cat + '::' + ru; }
  function dayStr(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function addDays(n) { var d = new Date(); d.setDate(d.getDate() + n); return dayStr(d); }

  /* Javobdan keyin so'zning keyingi takrorlash sanasini yangilaydi */
  function srsUpdate(lang, cat, ru, known) {
    if (!cat) return;
    var all = srsAll();
    var k = srsKey(lang, cat, ru);
    var cur = all[k] || { n: 0 };
    var n = known ? Math.min((cur.n || 0) + 1, SRS_STEPS.length) : 0;
    all[k] = { n: n, due: addDays(known ? SRS_STEPS[n - 1] : 1) };
    srsSave(all);
  }

  /* Bugun takrorlash kerak bo'lgan so'zlar (hech ko'rilmaganlar ham kiradi) */
  function srsDue(lang, cat) {
    var all = srsAll(), today = dayStr(new Date());
    return (V.data[cat] || []).filter(function (w) {
      var s = all[srsKey(lang, cat, w.ru)];
      return !s || !s.due || s.due <= today;
    });
  }

  /* Kategoriya bo'yicha o'zlashtirish darajasi (3+ marta to'g'ri = o'zlashtirilgan) */
  function srsProgress(lang, cat) {
    var all = srsAll(), words = V.data[cat] || [], learned = 0;
    words.forEach(function (w) {
      var s = all[srsKey(lang, cat, w.ru)];
      if (s && s.n >= 3) learned++;
    });
    return { learned: learned, total: words.length };
  }

  /* ---------- Xatolar ustida ishlash ---------- */
  var MIS = { lang: 'english', list: [] };

  /* Flashcard qaysi manbadan ochilgan bo'lsa o'shanga qaytadi. Xatolar va
     saqlangan versiya — ikkalasi ham "Xatolar" sahifasidan keladi. */
  function isMistakeSrc(src) { return src === 'mistakes' || src === 'snapshot'; }

  function loadMistakes(lang) {
    return App.call('get_mistakes', null, { query: 'lang=' + lang }).then(function (j) {
      MIS.lang = lang;
      MIS.list = (j.mistakes || []).map(function (m) {
        return { ru: m.word_ru, uz: m.word_uz, cat: m.category };
      });
      return MIS.list;
    });
  }

  App.view('vocab_mistakes', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english';
      var rightHtml =
        '<button class="icon-btn ghost" data-act="misVersions" data-arg=\'' + App.arg({ lang: lang }) + '\' ' +
        'aria-label="Versiyalar" title="Versiyalar"><span data-icon="clock" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="misDownload" data-arg=\'' + App.arg({ lang: lang }) + '\' ' +
        'aria-label=".md yuklab olish" title=".md yuklab olish"><span data-icon="download" data-icon-size="18"></span></button>';
      page.innerHTML = topbar('Xatolar', 'vocab', { lang: lang }, rightHtml) +
        '<div id="mis-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      loadMistakes(lang).then(function () { renderMistakes(page, lang); })
        .catch(function (e) {
          var b = App.el('mis-body'); if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
        });
    }
  });

  /* ---------- .md yuklab olish + GitHub'dagi kabi versiya tarixi ----------
     Har "yuklab olish" bosilganda: (1) joriy ro'yxat .md fayl qilib beriladi,
     (2) AYNI shu ro'yxat serverga versiya sifatida saqlanadi. So'z keyinroq
     "o'rgandim" deb o'chirilsa ham, eski versiyada saqlanib qoladi — GitHub
     commit kabi, istalgan eski versiyani ochib o'sha so'zlar bilan yana
     mashq qilish mumkin. */
  function misLabel(lang) { return lang === 'russian' ? 'Rus tili' : 'Ingliz tili'; }

  function mistakesToMd(list, lang, whenLabel) {
    var byCat = {};
    list.forEach(function (w) { (byCat[w.cat] = byCat[w.cat] || []).push(w); });
    var lines = ['# Xato so\'zlar — ' + misLabel(lang), '',
      '_' + whenLabel + ' · ' + list.length + ' ta so\'z_', ''];
    Object.keys(byCat).forEach(function (cat) {
      lines.push('## ' + cat, '');
      byCat[cat].forEach(function (w) { lines.push('- **' + w.ru + '** — ' + w.uz); });
      lines.push('');
    });
    return lines.join('\n');
  }

  App.actions.misDownload = function (a) {
    var lang = a.lang;
    loadMistakes(lang).then(function (list) {
      if (!list.length) { App.toast('⚠️ Xato so\'z yo\'q'); return; }
      var today = new Date();
      var dateLabel = today.getFullYear() + '-' + ('0' + (today.getMonth() + 1)).slice(-2) + '-' + ('0' + today.getDate()).slice(-2);
      App.download('Xatolar — ' + misLabel(lang) + ' (' + dateLabel + ').md', mistakesToMd(list, lang, dateLabel));
      App.call('save_mistake_snapshot', { lang: lang })
        .then(function () { App.toast('✅ Yuklandi va versiya sifatida saqlandi'); })
        .catch(function (e) { App.toast('⚠️ Yuklandi, lekin versiya saqlanmadi: ' + e.message); });
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  function fmtSnapDate(iso) {
    // "2026-08-10 14:32:05" -> "10-avg, 14:32"
    var m = String(iso || '').match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
    if (!m) return iso || '';
    var mon = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
    return (+m[3]) + '-' + mon[(+m[2]) - 1] + ', ' + m[4] + ':' + m[5];
  }

  App.actions.misVersions = function (a) {
    var lang = a.lang;
    var SHEET = App.sheet('<div id="mis-ver-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Versiyalar — ' + misLabel(lang) });

    function draw() {
      App.call('list_mistake_snapshots', null, { query: 'lang=' + lang }).then(function (j) {
        var body = SHEET.querySelector('#mis-ver-body'); if (!body) return;
        var snaps = j.snapshots || [];
        if (!snaps.length) {
          body.innerHTML = App.empty({
            icon: 'clock', title: 'Versiya yo\'q',
            text: '"Xatolar" ro\'yxatini birinchi marta yuklab olganingizda shu yerda versiya paydo bo\'ladi.'
          });
          App.icons(body); return;
        }
        body.innerHTML = snaps.map(function (v) {
          return '<div class="list-row">' +
            '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" ' +
            'data-act="misVersionOpen" data-arg=\'' + App.arg({ lang: lang, id: v.id }) + '\'>' +
            '<div class="li-title">' + fmtSnapDate(v.created_at) + '</div>' +
            '<div class="li-sub">' + v.word_count + ' ta so\'z</div></button>' +
            '<button class="icon-btn ghost" style="width:32px;height:32px;color:var(--danger)" ' +
            'data-act="misVersionDelete" data-arg=\'' + App.arg({ lang: lang, id: v.id }) + '\' title="O\'chirish">' +
            '<span data-icon="trash" data-icon-size="15"></span></button></div>';
        }).join('');
        App.icons(body);
      });
    }
    draw();
    SHEET._misVerRedraw = draw;
  };

  App.actions.misVersionDelete = function (a) {
    App.confirm('Bu versiya butunlay o\'chiriladi.', function () {
      App.call('delete_mistake_snapshot', { id: a.id }).then(function () {
        App.toast('✅ O\'chirildi');
        if (App._sheet && App._sheet.sh._misVerRedraw) App._sheet.sh._misVerRedraw();
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    }, { danger: true, yes: 'O\'chirish' });
  };

  App.actions.misVersionOpen = function (a) {
    var lang = a.lang, id = a.id;
    var SHEET = App.sheet('<div id="mis-vo-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Versiya' });
    App.call('get_mistake_snapshot', null, { query: 'id=' + encodeURIComponent(id) }).then(function (j) {
      var body = SHEET.querySelector('#mis-vo-body'); if (!body) return;
      var words = j.words || [];
      var dateLabel = fmtSnapDate(j.created_at);
      body.innerHTML =
        '<p class="muted" style="font-size:13px;margin:-6px 0 12px">' + dateLabel + ' · ' + words.length + ' ta so\'z</p>' +
        '<button class="btn" id="mis-vo-play" style="margin-bottom:8px">' +
        '<span data-icon="refresh" data-icon-size="16"></span>Flashcard bilan mashq qilish</button>' +
        '<button class="btn sec" id="mis-vo-dl" style="margin-bottom:16px">' +
        '<span data-icon="download" data-icon-size="16"></span>.md qilib yuklab olish</button>' +
        words.map(function (w) {
          return '<div class="list-row"><div class="li-main"><div class="li-title">' + App.esc(w.ru) + '</div>' +
            '<div class="li-sub">' + App.esc(w.uz) + ' · <span class="muted">' + App.esc(w.cat) + '</span></div></div></div>';
        }).join('');
      App.icons(body);
      body.querySelector('#mis-vo-play').onclick = function () {
        App.closeSheet();
        App.go('vocab_flash', { lang: lang, src: 'snapshot', id: id });
      };
      body.querySelector('#mis-vo-dl').onclick = function () {
        App.download('Xatolar — ' + misLabel(lang) + ' (' + dateLabel + ').md', mistakesToMd(words, lang, dateLabel));
      };
    }).catch(function (e) {
      var body = SHEET.querySelector('#mis-vo-body');
      if (body) body.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
    });
  };

  function renderMistakes(page, lang) {
    var box = App.el('mis-body'); if (!box) return;
    if (!MIS.list.length) {
      box.innerHTML = App.empty({
        icon: 'trophy', title: 'Xato so\'z yo\'q',
        text: 'Mashqlarda "Bilmadim" degan so\'zlaringiz shu yerda to\'planadi.'
      });
      App.icons(box);
      return;
    }
    box.innerHTML =
      '<p class="muted" style="font-size:13px;margin:-6px 0 12px" id="mis-count">' + MIS.list.length + ' ta so\'z ustida ishlash kerak</p>' +
      '<button class="btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_flash', p: { lang: lang, src: 'mistakes' } }) + '\' style="margin-bottom:16px">' +
      '<span data-icon="refresh" data-icon-size="16"></span>Flashcard bilan mashq qilish</button>' +
      '<p class="muted" style="font-size:11.5px;margin:0 0 10px">So\'zga bosing — o\'qib beradi. O\'rgangan bo\'lsangiz ✓ tugmasini bosing.</p>' +
      '<div id="mis-list"></div>';
    var list = App.el('mis-list');
    list.innerHTML = MIS.list.map(function (w, i) {
      return '<div class="list-row mis-item" data-i="' + i + '">' +
        '<div class="li-main" style="cursor:pointer"><div class="li-title">' + App.esc(w.ru) + '</div>' +
        '<div class="li-sub">' + App.esc(w.uz) + ' · <span class="muted">' + App.esc(w.cat) + '</span></div></div>' +
        '<button class="icon-btn ghost mis-ok" style="width:32px;height:32px;color:var(--success)" title="O\'rgandim">' +
        '<span data-icon="check" data-icon-size="17"></span></button></div>';
    }).join('');
    App.icons(list);
    list.querySelectorAll('.mis-item').forEach(function (el) {
      var w = MIS.list[+el.getAttribute('data-i')];
      el.querySelector('.li-main').onclick = function () { speakWord(w.ru, lang); };
      el.querySelector('.mis-ok').onclick = function () {
        el.style.transition = 'opacity .25s ease, transform .25s ease';
        el.style.opacity = '0'; el.style.transform = 'translateX(60px)';
        App.call('remove_mistake', { lang: lang, category: w.cat, ru: w.ru }).catch(function () {});
        setTimeout(function () {
          el.remove();
          MIS.list = MIS.list.filter(function (x) { return !(x.ru === w.ru && x.cat === w.cat); });
          var c = App.el('mis-count');
          if (!MIS.list.length) renderMistakes(page, lang);
          else if (c) c.textContent = MIS.list.length + ' ta so\'z ustida ishlash kerak';
        }, 260);
      };
    });
  }

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }

  /* Topbar bilan bottom-nav orasidagi haqiqiy bo'sh joyni o'lchab, #fc-body'ga beradi —
     shu orqali karta (flex:1) na kesilib qoladi, na ortiqcha bo'sh joy qoldiradi. */
  function fitFlashLayout(page) {
    var body = App.el('fc-body'), topbar = page.querySelector('.topbar');
    if (!body || !topbar) return;
    var nav = document.querySelector('.botnav');
    var top = topbar.getBoundingClientRect().bottom;
    var navVisible = nav && getComputedStyle(nav).display !== 'none';
    var bottom = navVisible ? nav.getBoundingClientRect().top : window.innerHeight;
    var avail = bottom - top - 24;
    body.style.height = Math.max(avail, 280) + 'px';
  }

  function renderFlashPage(page) {
    var l = LABEL[FC.lang];
    page.innerHTML =
      '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="go" data-arg=\'' +
      (isMistakeSrc(FC.src)
        ? App.arg({ v: 'vocab_mistakes', p: { lang: FC.lang } })
        : App.arg({ v: 'vocab_practice', p: { lang: FC.lang, cat: FC.cat } })) +
      '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>' + (FC.src === 'snapshot' ? 'Saqlangan versiya'
        : FC.src === 'mistakes' ? 'Xatolar' : FC.src === 'due' ? 'Takrorlash' : 'Flashcardlar') + '</h1>' +
      '<button class="icon-btn ghost" id="fc-mute" style="margin-left:auto"><span data-icon="volume" data-icon-size="18"></span></button>' +
      finishBtnHtml('vocabFlashFinish').replace('margin-left:auto', 'margin-left:4px') + '</div>' +

      '<div id="fc-body" style="display:flex;flex-direction:column">' +
      '<div class="between" style="margin-bottom:8px">' +
      '<div class="seg" id="fc-mode" style="flex:1"><button class="active" data-m="l1">' + l.side1 + ' → ' + l.side2 + '</button><button data-m="l2">' + l.side2 + ' → ' + l.side1 + '</button></div>' +
      '</div>' +
      '<div class="stat-strip" style="margin:0 0 10px">' +
      '<div class="s"><div class="n" id="fc-idx">1/' + FC.list.length + '</div><div class="l">Progress</div></div>' +
      '<div class="s"><div class="n" style="color:var(--success)" id="fc-good">0</div><div class="l">Bildim</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)" id="fc-bad">0</div><div class="l">Bilmadim</div></div>' +
      '</div>' +

      '<div id="fc-card-wrap" style="flex:1;min-height:0;display:flex;justify-content:center;perspective:1200px">' +
      '<div class="fc-card" id="fc-card"><div class="fc-inner" id="fc-inner">' +
      '<div class="fc-face fc-front"><span class="fc-lbl" id="fc-lbl-f"></span><span class="fc-word" id="fc-word-f"></span></div>' +
      '<div class="fc-face fc-back"><span class="fc-lbl" id="fc-lbl-b"></span><span class="fc-word" id="fc-word-b"></span></div>' +
      '</div></div>' +
      '</div>' +
      '<p class="muted" style="text-align:center;font-size:11.5px;margin:8px 0 12px">Kartaga bosing — aylantiradi, surib yoki tugma bilan javob bering.</p>' +

      '<div class="btn-row" style="margin-top:0">' +
      '<button class="btn danger" id="fc-bad-btn">✕ Bilmadim</button>' +
      '<button class="btn" id="fc-good-btn" style="background:var(--success)">✓ Bildim</button>' +
      '</div>' +
      '</div>';
    App.icons(page);
    fitFlashLayout(page);
    requestAnimationFrame(function () { fitFlashLayout(page); });
    if (!page._fcResizeBound) {
      page._fcResizeBound = true;
      window.addEventListener('resize', function () { if (App.el('fc-body')) fitFlashLayout(page); });
    }

    page.querySelectorAll('#fc-mode button').forEach(function (b) {
      b.onclick = function () {
        page.querySelectorAll('#fc-mode button').forEach(function (x) { x.classList.remove('active'); });
        b.classList.add('active'); FC.mode = b.getAttribute('data-m');
        renderCard(page);
      };
    });
    App.el('fc-mute').onclick = function () {
      FC.muted = !FC.muted; localStorage.setItem('vocab_muted', FC.muted ? '1' : '0');
      App.toast(FC.muted ? '🔇 Ovoz o\'chirildi' : '🔊 Ovoz yoqildi');
    };
    App.el('fc-card').onclick = function () { flipCard(page); };
    App.el('fc-good-btn').onclick = function () { swipe(page, true); };
    App.el('fc-bad-btn').onclick = function () { swipe(page, false); };
    initSwipeDrag(page);

    renderCard(page);
  }

  function currentWord() { return FC.list[FC.idx]; }

  function renderCard(page) {
    if (FC.idx >= FC.list.length) { showFlashResult(page); return; }
    var l = LABEL[FC.lang];
    var w = currentWord();
    var isL1 = FC.mode === 'l1';
    var card = App.el('fc-card'), inner = App.el('fc-inner');
    card.style.transition = 'none'; inner.style.transition = 'none';
    card.style.transform = 'translate(0,0) rotate(0deg)';
    card.classList.remove('flipped');
    void card.offsetWidth;
    inner.style.transition = ''; card.style.transition = '';
    FC.flipped = false;

    App.el('fc-lbl-f').textContent = isL1 ? l.side1 : l.side2;
    App.el('fc-word-f').textContent = isL1 ? w.ru : w.uz;
    App.el('fc-lbl-b').textContent = isL1 ? l.side2 : l.side1;
    App.el('fc-word-b').textContent = isL1 ? w.uz : w.ru;
    App.el('fc-idx').textContent = (FC.idx + 1) + '/' + FC.list.length;

    speakSide(page);
  }

  function speakSide(page) {
    if (FC.muted) { window.speechSynthesis.cancel(); return; }
    if (FC.idx >= FC.list.length) return;
    var l = LABEL[FC.lang], w = currentWord(), isL1 = FC.mode === 'l1';
    var text, ttsLang;
    if (!FC.flipped) { text = isL1 ? w.ru : w.uz; ttsLang = isL1 ? l.tts1 : l.tts2; }
    else { text = isL1 ? w.uz : w.ru; ttsLang = isL1 ? l.tts2 : l.tts1; }
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text); u.lang = ttsLang; u.rate = 0.9;
    window.speechSynthesis.speak(u);
  }

  function flipCard(page) {
    if (page._dragged) { page._dragged = false; return; }
    FC.flipped = !FC.flipped;
    App.el('fc-card').classList.toggle('flipped', FC.flipped);
    speakSide(page);
  }

  function swipe(page, known) {
    var card = App.el('fc-card');
    var endX = known ? window.innerWidth : -window.innerWidth;
    card.style.transition = 'transform .35s ease';
    card.style.transform = 'translateX(' + endX + 'px) rotate(' + (endX * 0.05) + 'deg)';
    var w = currentWord();
    // Xatolar rejimida har bir so'z o'z kategoriyasini olib yuradi (turli jildlardan yig'ilgan).
    var cat = w.cat || FC.cat;
    srsUpdate(FC.lang, cat, w.ru, known);
    if (known) {
      FC.good++;
      App.call('remove_mistake', { lang: FC.lang, category: cat, ru: w.ru }).catch(function () {});
    } else {
      FC.bad++; FC.mistakes.push(w);
      App.call('add_mistake', { lang: FC.lang, category: cat, ru: w.ru, uz: w.uz }).catch(function () {});
    }
    App.el('fc-good').textContent = FC.good;
    App.el('fc-bad').textContent = FC.bad;
    setTimeout(function () { FC.idx++; renderCard(page); }, 260);
  }

  function initSwipeDrag(page) {
    var card = App.el('fc-card');
    var startX = 0, dx = 0, dragging = false, isTap = true;
    function start(e) { startX = (e.touches ? e.touches[0].clientX : e.clientX); dragging = true; isTap = true; dx = 0; card.style.transition = 'none'; }
    function move(e) {
      if (!dragging) return;
      var x = (e.touches ? e.touches[0].clientX : e.clientX);
      dx = x - startX;
      if (Math.abs(dx) > 10) isTap = false;
      card.style.transform = 'translateX(' + dx + 'px) rotate(' + (dx * 0.05) + 'deg)';
    }
    function end() {
      if (!dragging) return;
      dragging = false;
      card.style.transition = 'transform .3s ease';
      if (isTap) { card.style.transform = ''; return; }
      page._dragged = true;
      if (dx > 80) swipe(page, true);
      else if (dx < -80) swipe(page, false);
      else card.style.transform = '';
      dx = 0;
    }
    card.addEventListener('mousedown', start);
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', end);
    card.addEventListener('touchstart', start, { passive: true });
    window.addEventListener('touchmove', move, { passive: true });
    window.addEventListener('touchend', end);
  }

  function showFlashResult(page) {
    var total = FC.good + FC.bad;
    var pct = total ? Math.round((FC.good / total) * 100) : 0;
    page.innerHTML =
      '<div style="text-align:center;padding-top:8px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 22px">Sessiya tugadi</h2>' +
      '<div class="stat-strip" style="max-width:280px;margin:0 auto 26px">' +
      '<div class="s"><div class="n" style="color:var(--success)">' + FC.good + '</div><div class="l">Bildim</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)">' + FC.bad + '</div><div class="l">Bilmadim</div></div>' +
      '<div class="s"><div class="n">' + total + '</div><div class="l">Jami</div></div>' +
      '</div>' +
      (FC.mistakes.length
        ? '<button class="btn" id="fc-retry">⚠ Bilmagan (' + FC.mistakes.length + ') so\'zlarni qaytarish</button>'
        : '<p class="muted">Barchasini bildingiz! 🎉</p>') +
      '<button class="btn ' + (FC.mistakes.length ? 'ghost' : '') + '" style="margin-top:10px" id="fc-finish">Tugatish</button>' +
      '</div>';
    App.icons(page);
    if (total > 0 && !FC.logged) {
      if (window.Activity) Activity.mark();
      App.call('log_activity', {
        section: 'vocab', object: FC.cat || 'Xatolar', amount: total, unit: 'so\'z',
        duration: FC.startedAt ? Math.round((Date.now() - FC.startedAt) / 1000) : null,
        meta: { lang: FC.lang, good: FC.good, bad: FC.bad, mode: 'flashcard' }
      }).catch(function () {});
      FC.logged = true;
    }
    var retry = App.el('fc-retry');
    if (retry) retry.onclick = function () {
      var mistakes = FC.mistakes;
      FC.list = mistakes; FC.idx = 0; FC.good = 0; FC.bad = 0; FC.mistakes = []; FC.logged = false;
      renderFlashPage(page);
    };
    App.el('fc-finish').onclick = function () {
      App.go(isMistakeSrc(FC.src) ? 'vocab_mistakes' : 'vocab_practice', { lang: FC.lang, cat: FC.cat });
    };
  }

  /* Topbardagi "Tugatish" — sessiya oxirigacha bormasdan chiqib ketish
     (hozirgacha ko'rilgan kartalar hisobga olinadi). */
  App.actions.vocabFlashFinish = function () {
    if (!FC.logged) {
      logVocabProgress(FC.lang, FC.cat || 'Xatolar', FC.good + FC.bad, 'flashcard', FC.startedAt, { good: FC.good, bad: FC.bad });
      FC.logged = true;
    }
    App.go(isMistakeSrc(FC.src) ? 'vocab_mistakes' : 'vocab_practice', { lang: FC.lang, cat: FC.cat });
  };
})();
