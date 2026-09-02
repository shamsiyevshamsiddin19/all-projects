/* Lug'at (Vocabulary) — Ingliz/Rus: kategoriyalar, flashcard (svayp), oddiy ro'yxat. */
(function () {
  'use strict';

  var LABEL = {
    english: { hub: "Lug'at", side1: 'Ingliz tili', side2: "O'zbek tili", tts1: 'en-US', tts2: 'uz-UZ' },
    russian: { hub: "Lug'at", side1: 'Rus tili', side2: "O'zbek tili", tts1: 'ru-RU', tts2: 'uz-UZ' }
  };

  var V = { lang: 'english', order: [], data: {}, loaded: false };

  /* T&P Books "Русско-узбекский тематический словарь" (2014) tuzilishi.
     257 mavzu, 6 katta bo'lim. Nomi BITTA joyda turadi — u uch joyda
     ishlatiladi (nishon, karta ko'rinishi, yorliq), qo'lda takrorlansa
     biri o'zgarib qolishi aniq edi. */
  var TEMA_ROOT = 'Тематический 9000';
  var FC = null; // flashcard session state

    function vocabBadgeHtml(name) {
    name = String(name || '').trim();

    // Master 1-8000 badge
    if (name === '1-8000') {
      return '<span class="chat-av" style="background:linear-gradient(135deg,#6366f1,#a855f7,#ec4899);color:#fff;font-size:14.5px;font-weight:900;box-shadow:0 4px 14px rgba(168,85,247,0.45);letter-spacing:-0.5px">8K</span>';
    }

    /* Тематический 9000 — 1-8000 ning yonidagi ikkinchi katta to'plam.
       Rangi ATAYLAB butunlay boshqa: 8K binafsha-pushti, bu esa
       ko'kish-yashil. Ikkalasi yonma-yon turadi, farqi bir qarashda
       bilinishi kerak. Qizil olinmadi — u xato/o'chirish rangi. */
    if (name === TEMA_ROOT) {
      return '<span class="chat-av" style="background:linear-gradient(135deg,#0d9488,#10b981,#84cc16);color:#fff;font-size:14.5px;font-weight:900;box-shadow:0 4px 14px rgba(16,185,129,0.45);letter-spacing:-0.5px">9K</span>';
    }

    // 1-1000 folder badge
    if (name === '1-1000') {
      return '<span class="chat-av" style="background:linear-gradient(135deg,#2563eb,#38bdf8);color:#fff;font-size:14px;font-weight:900;box-shadow:0 4px 12px rgba(37,99,235,0.35);letter-spacing:-0.5px">1K</span>';
    }

    // 1001-2000 ... 7001-8000 folders
    var thousandMatch = name.match(/^(\d+)[-–—](\d{4,})$/);
    if (thousandMatch) {
      var toK = thousandMatch[2];
      var kLabel = (parseInt(toK, 10) / 1000) + 'K';
      return '<span class="chat-av chat-av-num" style="background:#fff;color:var(--accent,#007aff);font-size:14.5px;font-weight:800">' + App.esc(kLabel) + '</span>';
    }

    // 1. Range format like 1-100, 101-200, 901-1000, 1001-1100
    var rangeMatch = name.match(/^(\d+)[-–—](\d+)$/);
    if (rangeMatch) {
      var toNum = rangeMatch[2];
      var fs = toNum.length >= 4 ? 12.5 : (toNum.length === 3 ? 14.5 : 17);
      return '<span class="chat-av chat-av-num" style="background:#fff;color:var(--accent,#007aff);font-size:' + fs + 'px;font-weight:800;letter-spacing:-0.5px">' + App.esc(toNum) + '</span>';
    }

    // 2. Numbered like 01. ... or 1. ... or 100
    var numMatch = name.match(/^(\d+)[.)]?/);
    if (numMatch && numMatch[1].length <= 4) {
      var n = numMatch[1];
      var fs = n.length >= 4 ? 12.5 : (n.length === 3 ? 14.5 : 18);
      return '<span class="chat-av chat-av-num" style="background:#fff;color:var(--accent,#007aff);font-size:' + fs + 'px;font-weight:800">' + App.esc(n) + '</span>';
    }

    // 3. Text format (like "Глаголы настоящего времени", "Animals", etc.) -> Birinchi harf
    var letter = name.charAt(0).toUpperCase();
    return '<span class="chat-av chat-av-num" style="background:#fff;color:var(--accent,#007aff);font-size:20px;font-weight:800">' + App.esc(letter) + '</span>';
  }

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
        (V.data[it.category] = V.data[it.category] || []).push({
          ru: it.word_ru,
          uz: it.word_uz,
          note: it.note || '',
          ex: it.example || it.ex || '',
          /* .md dagi "Chalkashadi:" qatoridan kelgan qo'lda ko'rsatilgan
             juftliklar. Ilgari bu yerda tashlab yuborilardi — ya'ni faylga
             yozilgan juftlik hech qachon ishlatilmasdi. */
          pairWith: (it.pair_with || '').split(',')
            .map(function (x) { return x.trim(); })
            .filter(Boolean),
          /* Ma'no guruhi yorlig'i — bir xil yorliqli so'zlar bitta guruh.
             Yozilishi o'xshash bo'lishi shart emas (иду / хожу / еду). */
          meaningGroup: (it.meaning_group || '').trim(),
          /* Boyitilgan maydonlar — hammasi oddiy bir qatorlik matn.
             Server ustunlarining nomi bilan bir xil, faqat camelCase. */
          partOfSpeech: (it.part_of_speech || '').trim(),
          pronunciation: (it.pronunciation || '').trim(),
          forms: (it.forms || '').trim(),
          formation: (it.formation || '').trim(),
          synonyms: (it.synonyms || '').trim(),
          antonyms: (it.antonyms || '').trim(),
          collocations: (it.collocations || '').trim(),
          mnemonic: (it.mnemonic || '').trim()
        });
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
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_md_list', p: { lang: lang } }) + '\' aria-label="MD Kitoblar" title="MD Kitoblar" style="font-weight:800;font-size:16.5px;color:var(--accent,#007aff);width:34px;height:34px;line-height:1">D</button>' +
        /* C va V — butun lug'atni bir ekranda ko'rish (vocab_browse).
           Ilgari bu yerda "+" (yangi kategoriya) turardi; u endi
           "Baza qo'shish" varag'iga ko'chirildi, chunki kundalik ish
           yangi kategoriya ochish emas, so'zlarni ko'rib chiqish. */
        /* Faqat JORIY tilning harfi: rus lug'atida C, ingliz lug'atida V.
           Ikkalasini yonma-yon qo'yish chalkash edi — bu sahifa allaqachon
           bitta tilga tegishli. */
        '<button class="icon-btn ghost voc-key" data-act="go" data-arg=\'' +
          App.arg({ v: 'vocab_browse', p: { lang: lang } }) + '\' aria-label="Butun lug\'at" title="Butun lug\'at">' +
          (lang === 'russian' ? 'C' : 'V') + '</button>' +
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
        box.innerHTML = '<div class="chat-list" style="margin-bottom:12px">' +
          '<button class="chat-row" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_mistakes', p: { lang: lang } }) + '\'>' +
          '<span class="chat-av chat-av-num" style="background:#fff;color:var(--danger,#ef4444);font-size:18px;font-weight:800"><span data-icon="alert" data-icon-size="20"></span></span>' +
          '<span class="chat-main"><span class="chat-title">Xatolar ustida ishlash</span>' +
          '<span class="chat-sub">' + list.length + ' ta so\'z takrorlashni kutmoqda</span></span>' +
          '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button></div>';
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
          return '<div class="chat-item">' +
            '<button class="chat-row" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: { lang: lang, cat: it.full } }) + '\'>' +
            vocabBadgeHtml(it.name) +
            '<span class="chat-main">' +
              '<span class="chat-title">' + App.esc(it.name) + '</span>' +
              '<span class="chat-sub">' + it.count + ' so\'z</span>' +
            '</span>' +
            '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>' +
            '</div>';
        }

        /* Papka qatori: asosiy qismi ichkariga kiradi, yonidagi tugma menyu
           (button ichida button bo'lmaydi — shuning uchun o'ram div). */
        var html = '';
        if (order.length) {
          html += '<div class="chat-list">' + order.map(function (path) {
            var f = map[path];
            var isTema  = (f.name === TEMA_ROOT);
            var isMagic = (f.name === '1-8000' || (f.name === '1-1000' && !folder));
            /* Ichki tugma har ikkala holatda ham shaffof bo'ladi — rang
               o'ram `div` da, aks holda ikki fon ustma-ust tushardi. */
            var magicClass = (isMagic || isTema) ? ' chat-row-magic' : '';
            var itemClass = isTema ? ' chat-item-tema' : (isMagic ? ' chat-item-magic' : '');
            var titleExtra = isTema
              ? ' <span class="tag-tema">9 000 So\'z · 257 mavzu</span>'
              : (f.name === '1-8000' ? ' <span class="tag-magic">✨ 8 000 So\'z</span>'
                : (isMagic ? ' <span class="tag-magic">✨ 1 000 So\'z</span>' : ''));
            return '<div class="chat-item' + itemClass + '">' +
              '<button class="chat-row' + magicClass + '" data-act="go" data-arg=\'' +
              App.arg({ v: 'vocab', p: { lang: lang, folder: path } }) + '\'>' +
              vocabBadgeHtml(f.name) +
              '<span class="chat-main">' +
                '<span class="chat-title">' + App.esc(f.name) + titleExtra + '</span>' +
                '<span class="chat-sub">' + f.items + ' bo\'lim · ' + f.words + ' so\'z</span>' +
              '</span>' +
              '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>' +
              '</div>';
          }).join('') + '</div>';
        }
        if (root.length) {
          if (order.length) html += '<div class="list-label" style="margin-top:16px">Lug\'atlar</div>';
          html += '<div class="chat-list">' + root.map(catRow).join('') + '</div>';
        }
        if (!order.length && !root.length && folder) {
          html = App.empty({ icon: 'list', title: 'Bo\'sh papka', text: '' });
        }
        
        /* MD fayllar alohida 'vocab_md_list' (D tugmasi) sahifasiga ko'chirildi */
        
        /* Yashiringanlar — FAQAT o'sha narsa yashirilgan papkada ko'rinadi.
           Ilgari global ro'yxat ishlatilgani uchun bu qator har bir papkada,
           hatto hech narsa yashirilmagan ichki papkalarda ham chiqardi. */
        var hidHere = hid.filter(function (c) { return catParent(c) === folder; });
        var hidFHere = hidF.filter(function (f) { return catParent(f) === folder; });
        if (hidHere.length || hidFHere.length) {
          var parts = [];
          if (hidFHere.length) parts.push(hidFHere.length + ' papka');
          if (hidHere.length) parts.push(hidHere.length + ' lug\'at');
          html += '<div class="chat-list" style="margin-top:14px">' +
            '<button class="chat-row" data-act="vocabHiddenSheet" data-arg=\'' +
            App.arg({ lang: lang, folder: folder }) + '\'>' +
            '<span class="chat-av" style="background:#fff"><span class="chat-av-ic" data-icon="close" data-icon-size="20"></span></span>' +
            '<span class="chat-main"><span class="chat-title">Yashiringanlar</span>' +
            '<span class="chat-sub">' + parts.join(' · ') + ' · qaytarish mumkin</span></span>' +
            '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button></div>';
        }

        box.innerHTML = html || App.empty({ icon: 'list', title: 'Kategoriya yo\'q', text: 'Yuqoridagi tugma bilan birinchi kategoriyani qo\'shing.' });
        App.icons(box);
      }).catch(function (e) {
        var box = App.el('vocab-list'); if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
    }
  });

  /* ---------- MD Lug'at Generator & Parser ---------- */
  function categoryToMd(catName, words, lang) {
    var lines = [
      '# ' + catName,
      '',
      '> Til: ' + (lang === 'russian' ? 'Rus tili' : 'Ingliz tili') + ' · Jami ' + (words ? words.length : 0) + ' ta so\'z',
      '',
      '---',
      ''
    ];
    (words || []).forEach(function (w, idx) {
      lines.push('## ' + (idx + 1) + '. ' + w.ru + ' — ' + w.uz);
      if (w.partOfSpeech) {
        lines.push('');
        lines.push('> Turkum: ' + w.partOfSpeech);
      }
      if (w.formation) {
        lines.push('');
        lines.push('> Yasalishi: ' + w.formation);
      }
      if (w.pronunciation) {
        lines.push('');
        lines.push('> Talaffuz: ' + w.pronunciation);
      }
      if (w.forms) {
        lines.push('');
        lines.push('> Shakllar: ' + w.forms);
      }
      if (w.note) {
        lines.push('');
        var noteLines = String(w.note).trim().split('\n');
        noteLines.forEach(function (nl) {
          lines.push('> ' + nl);
        });
      }
      if (w.synonyms) {
        lines.push('');
        lines.push('> Sinonim: ' + w.synonyms);
      }
      if (w.antonyms) {
        lines.push('');
        lines.push('> Antonim: ' + w.antonyms);
      }
      if (w.collocations) {
        lines.push('');
        lines.push('> Birikma: ' + w.collocations);
      }
      if (w.mnemonic) {
        lines.push('');
        lines.push('> Eslab qolish: ' + w.mnemonic);
      }
      if (w.meaningGroup) {
        lines.push('');
        lines.push('> **Ma\'no guruhi:** ' + w.meaningGroup);
      }
      if (w.pairWith && w.pairWith.length) {
        lines.push('');
        lines.push('> **Chalkashadi:** ' + w.pairWith.join(', '));
      }
      var ex = (w.ex || w.example || '').trim();
      if (ex) {
        lines.push('');
        lines.push('> **Misol:** ' + ex);
      }
      lines.push('');
      lines.push('---');
      lines.push('');
    });
    return lines.join('\n');
  }

  function parseMdToDictCategories(text, defaultCategory) {
    var categories = [];
    var currentCat = defaultCategory || 'Yangi lug\'at';
    var currentWords = [];
    var lines = text.split(/\r?\n/);

    var curWord = null;

    function flushWord() {
      if (curWord && curWord.ru && curWord.uz) {
        currentWords.push({
          ru: curWord.ru.trim(),
          uz: curWord.uz.trim(),
          note: (curWord.note || '').trim(),
          ex: (curWord.ex || '').trim(),
          pairWith: curWord.pairWith || [],
          meaningGroup: curWord.meaningGroup || '',
          partOfSpeech: (curWord.partOfSpeech || '').trim(),
          pronunciation: (curWord.pronunciation || '').trim(),
          forms: (curWord.forms || '').trim(),
          formation: (curWord.formation || '').trim(),
          synonyms: (curWord.synonyms || '').trim(),
          antonyms: (curWord.antonyms || '').trim(),
          collocations: (curWord.collocations || '').trim(),
          mnemonic: (curWord.mnemonic || '').trim()
        });
      }
      curWord = null;
    }

    function flushCat() {
      flushWord();
      if (currentWords.length > 0) {
        categories.push({
          category: currentCat,
          words: currentWords
        });
      }
      currentWords = [];
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (!line || line === '---' || line === '===') {
        continue;
      }

      // Check for Category Header (# Category)
      var h1Match = line.match(/^#\s+([^#].*)$/);
      if (h1Match) {
        flushCat();
        currentCat = h1Match[1].trim();
        continue;
      }

      // Check for Word Header (## [1.] ru — uz  or  ## ru - uz)
      var h2Match = line.match(/^##\s+(?:\d+[.)]\s*)?(.+?)\s*[—–\-:]\s*(.+)$/);
      if (h2Match) {
        flushWord();
        curWord = {
          ru: h2Match[1].trim(), uz: h2Match[2].trim(), note: '', ex: '',
          pairWith: [], meaningGroup: '',
          partOfSpeech: '', pronunciation: '', forms: '', formation: '',
          synonyms: '', antonyms: '', collocations: '', mnemonic: ''
        };
        continue;
      }

      /* Bitta qatorlik boyitilgan maydonlar ("**Label:** qiymat" yoki
         "Label: qiymat"). Barchasi bir xil qoliplanadi, shuning uchun
         bitta yordamchi funksiya orqali o'qiladi — 7 marta bir xil kodni
         takrorlash o'rniga. */
      function matchLabel(text, label) {
        var bold = new RegExp('^\\*\\*' + label + ':\\*\\*\\s*');
        var plain = new RegExp('^' + label + ':\\s*');
        if (bold.test(text)) return text.replace(bold, '').trim();
        if (plain.test(text)) return text.replace(plain, '').trim();
        return null;
      }

      // Check for Blockquote note or example
      if (line.startsWith('>')) {
        var bq = line.replace(/^>+\s*/, '').trim();
        if (bq.startsWith('**Misol:**')) {
          var exText = bq.replace(/^\*\*Misol:\*\*\s*/, '').trim();
          if (curWord) curWord.ex = exText;
        } else if (bq.startsWith('Misol:')) {
          var exText = bq.replace(/^Misol:\s*/, '').trim();
          if (curWord) curWord.ex = exText;
        } else if (bq.startsWith('**Ma\'no guruhi:**') || bq.startsWith('Ma\'no guruhi:')) {
          /* MA'NO bo'yicha guruh. `Chalkashadi:` dan farqi: u yozilishi
             o'xshash so'zlarni bog'laydi, bu esa MA'NOSI bog'liqlarni.
             Bir xil yorliq yozilgan so'zlar bitta oila bo'ladi, ya'ni
             har so'zga qolganlarini sanab chiqish shart emas. */
          var mgText = bq.replace(/^\*?\*?Ma'no guruhi:\*?\*?\s*/, '').trim();
          if (curWord) curWord.meaningGroup = mgText;
        } else if (bq.startsWith('**Chalkashadi:**') || bq.startsWith('Chalkashadi:')) {
          // Adashtiriladigan so'zlar — AI (yoki qo'lda) .md ichida yozib qoldirgan bo'lsa,
          // Juftlash rejimi shu ro'yxatni birinchi navbatda ishonchli manba sifatida oladi.
          var pairText = bq.replace(/^\*?\*?Chalkashadi:\*?\*?\s*/, '').trim();
          if (curWord) curWord.pairWith = pairText.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
        } else if (curWord && matchLabel(bq, 'Turkum') !== null) {
          curWord.partOfSpeech = matchLabel(bq, 'Turkum');
        } else if (curWord && matchLabel(bq, 'Yasalishi') !== null) {
          /* So'z QANDAY yasalgan / qayerdan kelib chiqqan.
             Rus tilida so'zlarning katta qismi prefiks+o'zak: `приходить`
             ni "при- + ходить" deb ko'rsatish o'nlab qarindosh so'zni bir
             yo'la ochib beradi. O'zlashgan so'zlar uchun esa manba tili
             (`вокзал` <- ingliz "Vauxhall") eslab qolishga yordam beradi.
             Ikkisi bitta maydonda: ko'p so'zda javob AYNAN BIR XIL gap. */
          curWord.formation = matchLabel(bq, 'Yasalishi');
        } else if (curWord && matchLabel(bq, 'Talaffuz') !== null) {
          curWord.pronunciation = matchLabel(bq, 'Talaffuz');
        } else if (curWord && matchLabel(bq, 'Shakllar') !== null) {
          curWord.forms = matchLabel(bq, 'Shakllar');
        } else if (curWord && matchLabel(bq, 'Sinonim') !== null) {
          curWord.synonyms = matchLabel(bq, 'Sinonim');
        } else if (curWord && matchLabel(bq, 'Antonim') !== null) {
          curWord.antonyms = matchLabel(bq, 'Antonim');
        } else if (curWord && matchLabel(bq, 'Birikma') !== null) {
          curWord.collocations = matchLabel(bq, 'Birikma');
        } else if (curWord && matchLabel(bq, 'Eslab qolish') !== null) {
          /* Bu qator ATAYLAB alohida maydon: mashqda eng ko'p ko'rinishi
             kerak bo'lgan yordam aynan shu — tovush o'xshashligi, tasvir
             yoki o'zak parchalash orqali eslab qolish yo'li. */
          curWord.mnemonic = matchLabel(bq, 'Eslab qolish');
        } else {
          if (curWord) {
            curWord.note = (curWord.note ? curWord.note + '\n' : '') + bq;
          }
        }
        continue;
      }

      // Check for standard 1) word - trans # note | ex  or  - word - trans
      var stdMatch = line.match(/^(?:\d+[.)]|[-*+])?\s*([^-—–#|]+?)\s*[-—–:]\s*([^#|]+)(?:#(.*))?$/);
      if (stdMatch) {
        flushWord();
        var ruPart = stdMatch[1].trim();
        var uzPart = stdMatch[2].trim();
        var rest = stdMatch[3] ? stdMatch[3].trim() : '';
        var notePart = '';
        var exPart = '';
        if (rest) {
          var pipeIdx = rest.indexOf('|');
          if (pipeIdx >= 0) {
            notePart = rest.substring(0, pipeIdx).trim();
            exPart = rest.substring(pipeIdx + 1).trim();
          } else {
            notePart = rest;
          }
        }
        currentWords.push({ ru: ruPart, uz: uzPart, note: notePart, ex: exPart });
        continue;
      }

      // Table row support: | ru | uz | note | ex |
      if (line.startsWith('|') && line.endsWith('|')) {
        var cols = line.split('|').map(function (c) { return c.trim(); }).filter(function (c, idx, arr) { return idx > 0 && idx < arr.length - 1; });
        if (cols.length >= 2 && !cols[0].includes('---') && cols[0].toLowerCase() !== 'ruscha' && cols[0].toLowerCase() !== 'so\'z') {
          flushWord();
          currentWords.push({
            ru: cols[0],
            uz: cols[1],
            note: cols[2] || '',
            ex: cols[3] || ''
          });
        }
      }
    }

    flushCat();
    return categories;
  }

  function bulkSheetHtml(nameValue, textValue) {
    return '<label class="field"><span>Kategoriya nomi</span><input class="input" id="vc-name" value="' + App.esc(nameValue || '') + '" placeholder="Masalan: 01. Hayvonlar"></label>' +
      '<p class="muted" style="font-size:12px;margin:4px 0 8px">Format: <code>1) so\'z - tarjima</code> yoki izoh/misol bilan: <code>1) so\'z - tarjima # izoh | misol gap</code></p>' +
      '<label class="field"><span>So\'zlar</span>' +
      '<textarea class="textarea" id="vc-text" rows="9" placeholder="1) cat - mushuk # Uy hayvoni | I have a black cat.&#10;2) dog - it # Vafodor do\'st | The dog barked.">' + App.esc(textValue || '') + '</textarea></label>' +
      '<button class="btn" id="vc-save">Saqlash</button>';
  }

  App.actions.vocabDbOptions = function(a) {
    var sh = App.sheet(
      '<button class="list-row" data-act="vocabAddCat" data-arg=\'' + App.arg(a) + '\'>' +
        '<span class="li-ic" data-icon="plus" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Yangi kategoriya</div><div class="li-sub">Bo\'sh lug\'at bo\'limi ochish</div></div>' +
      '</button>' +
      '<button class="list-row" data-act="vocabImportMDToDict" data-arg=\'' + App.arg(a) + '\'>' +
        '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Lug\'atga MD fayl yuklash (Import)</div><div class="li-sub">.md fayldagi so\'zlarni to\'g\'ridan-to\'g\'ri lug\'at bazasiga qo\'shish</div></div>' +
      '</button>' +
      '<button class="list-row" data-act="vocabExportAllMD" data-arg=\'' + App.arg(a) + '\'>' +
        '<span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Barcha lug\'atlarni MD qilib yuklab olish (Export)</div><div class="li-sub">To\'liq lug\'at bazasini bitta .md fayl sifatida yuklash</div></div>' +
      '</button>' +
      '<button class="list-row" data-act="vocabUploadMD" data-arg=\'' + App.arg(a) + '\'>' +
        '<span class="li-ic" data-icon="book" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">MD Kitoblar bo\'limiga yuklash</div><div class="li-sub">Interaktiv kitob formatida o\'qish uchun yuklash</div></div>' +
      '</button>',
      { title: 'Lug\'at va MD amallari' }
    );
  };

  App.actions.vocabExportCatMD = function (a) {
    if (App._sheetNode) App.closeSheet();
    var lang = a.lang || 'russian';
    var cat = a.cat || '';
    var words = (V.data && V.data[cat]) || [];
    if (!words.length) {
      App.toast('⚠️ Ushbu kategoriyada so\'zlar mavjud emas');
      return;
    }
    var mdText = categoryToMd(cat, words, lang);
    var safeCat = cat.replace(/[\\/:*?"<>|]/g, '_');
    App.download(safeCat + '.md', mdText);
    App.toast('✅ ' + safeCat + '.md yuklab olindi');
  };

  App.actions.vocabExportAllMD = function (a) {
    if (App._sheetNode) App.closeSheet();
    var lang = a.lang || 'russian';
    var cats = Object.keys(V.data || {});
    if (!cats.length) {
      App.toast('⚠️ Lug\'atda ma\'lumotlar mavjud emas');
      return;
    }
    var totalWords = 0;
    var allMd = [
      '# ' + (lang === 'russian' ? 'Rus tili lug\'at bazasi' : 'Ingliz tili lug\'at bazasi'),
      '',
      '> Jami kategoriyalar: ' + cats.length,
      '',
      '========================================',
      ''
    ];
    cats.forEach(function (cat) {
      var words = V.data[cat] || [];
      totalWords += words.length;
      allMd.push(categoryToMd(cat, words, lang));
      allMd.push('\n\n========================================\n\n');
    });
    var fileName = (lang === 'russian' ? 'Rus_tili_lugat' : 'Ingliz_tili_lugat') + '_toʻliq.md';
    App.download(fileName, allMd.join('\n'));
    App.toast('✅ ' + totalWords + ' ta so\'z .md qilib yuklandi');
  };

  App.actions.vocabImportMDToDict = function (a) {
    if (App._sheetNode) App.closeSheet();
    var inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = '.md,.txt';
    inp.onchange = function (e) {
      var file = e.target.files[0];
      if (!file) return;
      var defaultName = file.name.replace(/\.(md|txt)$/i, '');
      var reader = new FileReader();
      reader.onload = function (evt) {
        var text = evt.target.result;
        var parsed = parseMdToDictCategories(text, defaultName);
        if (!parsed.length) {
          App.toast('⚠️ MD fayldan so\'zlar topilmadi. Formatni tekshiring.');
          return;
        }
        var promises = parsed.map(function (item) {
          var catName = (a.folder ? a.folder + '/' : '') + item.category;
          return App.call('save_dict_cat', { lang: a.lang, category: catName, words: item.words });
        });
        Promise.all(promises).then(function () {
          App.toast('✅ ' + parsed.length + ' ta kategoriya lug\'atga saqlandi');
          App.reload();
        }).catch(function (err) {
          App.toast('⚠️ Xatolik: ' + err.message);
        });
      };
      reader.readAsText(file);
    };
    inp.click();
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
        App.go('vocab_md_list', { lang: a.lang });
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
      App.go('vocab_md_list', { lang: a.lang });
    }
  };

  /* ---------- MD Kitoblar alohida sahifasi ---------- */
    var SYSTEM_MD_BOOKS = {
    russian: [
      { id: '229_ta_fel_MUKAMMAL', title: '🔥 229 ta Rus tili Fe\'llari (Mukammal AI Lug\'at)', file: '229_ta_fel_MUKAMMAL.md', desc: '229 ta asosiy fe\'llar: Infinitiv, Shakl, Vid juftligi, Sinonimlar va Misollar bilan', isSys: true },
      { id: 'Rus_tili_1000_soz_MUKAMMAL', title: '⭐ Rus tili 1000 so\'z (Mukammal Tavsifli AI Lug\'at)', file: 'Rus_tili_1000_soz_MUKAMMAL.md', desc: '1 000 ta so\'z: Qayerda, Shakl, Vid juftligi, Ma\'nodosh va Misollar bilan', isSys: true },
      { id: 'Rus_tili_8000_soz_TARJIMA', title: 'Rus tili 8000 so\'z (Tarjima bilan)', file: 'Rus_tili_8000_soz_TARJIMA.md', desc: '8 000 ta ruscha so\'z o\'zbekcha tarjimalari bilan', isSys: true },
      { id: 'Rus_tili_8000_soz', title: 'Rus tili 8000 so\'z (Asl ro\'yxat)', file: 'Rus_tili_8000_soz.md', desc: '8 000 ta eng faol ruscha so\'zlar ro\'yxati', isSys: true }
    ],
    english: [
      { id: 'Ingliz_tili_8000_soz_TARJIMA', title: 'Ingliz tili 8000 so\'z (Tarjima bilan)', file: 'Ingliz_tili_8000_soz_TARJIMA.md', desc: '8 000 ta inglizcha so\'z o\'zbekcha tarjimalari bilan', isSys: true },
      { id: 'Ingliz_tili_8000_soz', title: 'Ingliz tili 8000 so\'z (Asl ro\'yxat)', file: 'Ingliz_tili_8000_soz.md', desc: '8 000 ta eng faol inglizcha so\'zlar ro\'yxati', isSys: true }
    ]
  };

  App.actions.vocabDownloadMDFile = function (a) {
    if (a.isSys) {
      fetch('assets/md_books/' + a.file).then(function (r) {
        if (!r.ok) throw new Error('Faylni yuklab bo\'lmadi');
        return r.text();
      }).then(function (txt) {
        App.download(a.file, txt);
        App.toast('✅ ' + a.file + ' yuklab olindi');
      }).catch(function (e) {
        App.toast('⚠️ ' + e.message);
      });
    } else {
      var mdFiles = {};
      try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + a.lang) || '{}'); } catch(ex) {}
      var txt = mdFiles[a.mdId] || '';
      if (txt) {
        App.download(a.mdId + '.md', txt);
        App.toast('✅ ' + a.mdId + '.md yuklab olindi');
      }
    }
  };
  App.view('vocab_md_list', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang || 'english';
      var backView = 'vocab';
      var backParams = { lang: lang };

      page.innerHTML = topbar('MD Kitoblar', backView, backParams,
        '<div class="voc-acts">' +
        '<button class="icon-btn ghost" data-act="vocabUploadMD" data-arg=\'' + App.arg({ lang: lang }) + '\' aria-label="MD yuklash" title="MD kitob yuklash"><span data-icon="plus" data-icon-size="19"></span></button>' +
        '</div>') +
        '<div class="flex" style="gap:8px;margin-bottom:12px">' +
        '<input class="input" id="vmd-q" placeholder="Kitob qidirish..." style="flex:1">' +
        '</div>' +
        '<div id="vmd-items"><div class="load-wrap"><div class="spinner"></div></div></div>';

      App.icons(page);

      var render = function () {
        var box = App.el('vmd-items'); if (!box) return;
        var mdFiles = {};
        try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + lang) || '{}'); } catch(ex) {}
        var mdKeys = Object.keys(mdFiles);

        var sysBooks = SYSTEM_MD_BOOKS[lang] || [];
        var allItems = [];
        sysBooks.forEach(function (b) {
          allItems.push({
            id: b.id,
            title: b.title,
            desc: b.desc,
            file: b.file,
            isSys: true
          });
        });
        mdKeys.forEach(function (k) {
          allItems.push({
            id: k,
            title: k,
            desc: 'Foydalanuvchi fayli · .md',
            file: k + '.md',
            isSys: false
          });
        });

        var q = (App.el('vmd-q').value || '').trim().toLowerCase();
        var shown = q ? allItems.filter(function (it) {
          return it.title.toLowerCase().indexOf(q) >= 0 || it.desc.toLowerCase().indexOf(q) >= 0;
        }) : allItems;

        if (!shown.length) {
          box.innerHTML = App.empty({
            icon: 'list',
            title: q ? 'Kitob topilmadi' : 'MD Kitoblar yo\'q',
            text: q ? 'Boshqa nom bilan qidiring.' : 'Yuqoridagi + tugmasi orqali .md faylini yuklang.'
          });
          App.icons(box);
          return;
        }

        box.innerHTML = '<div class="chat-list">' + shown.map(function (it) {
          var char = it.title.charAt(0).toUpperCase() || 'D';
          var delBtn = !it.isSys
            ? '<button class="icon-btn ghost" style="width:34px;height:34px;color:var(--danger);flex-shrink:0" data-act="vocabDeleteMD" data-arg=\'' + App.arg({ lang: lang, mdId: it.id }) + '\' title="O\'chirish"><span data-icon="trash" data-icon-size="15"></span></button>'
            : '';
          var dlBtn = '<button class="icon-btn ghost" style="width:34px;height:34px;color:var(--accent,#007aff);flex-shrink:0" data-act="vocabDownloadMDFile" data-arg=\'' + App.arg({ lang: lang, mdId: it.id, file: it.file, isSys: it.isSys }) + '\' title="Yuklab olish"><span data-icon="download" data-icon-size="16"></span></button>';

          return '<div class="chat-item">' +
            '<button class="chat-row" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_md_read', p: { lang: lang, mdId: it.id, file: it.file, isSys: it.isSys, title: it.title } }) + '\'>' +
            '<span class="chat-av chat-av-num" style="background:' + (it.isSys ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#fff') + ';color:' + (it.isSys ? '#fff' : 'var(--accent,#007aff)') + ';font-size:18px;font-weight:800">' + App.esc(char) + '</span>' +
            '<span class="chat-main">' +
              '<span class="chat-title">' + App.esc(it.title) + (it.isSys ? ' <span class="tag-magic">✨ Asosiy</span>' : '') + '</span>' +
              '<span class="chat-sub">' + App.esc(it.desc) + '</span>' +
            '</span>' +
            '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>' +
            dlBtn +
            delBtn +
            '</div>';
        }).join('') + '</div>';

        App.icons(box);
      };

      App.el('vmd-q').oninput = render;
      render();
    }
  });

  App.view('vocab_md_read', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang || 'english';
      var fname = params.mdId;
      var isSys = params.isSys === '1' || params.isSys === true;
      var file = params.file;
      var title = params.title || fname || 'MD Fayl';

      var topActs = '<button class="icon-btn ghost" data-act="vocabDownloadMDFile" data-arg=\'' +
        App.arg({ lang: lang, mdId: fname, file: file, isSys: isSys }) + '\' aria-label="Yuklab olish" title=".md faylni yuklab olish"><span data-icon="download" data-icon-size="18"></span></button>';

      page.innerHTML = topbar(title, 'vocab_md_list', { lang: lang }, topActs) +
        '<div id="vmd-read-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);

      function showContent(txt) {
        var box = App.el('vmd-read-body');
        if (!box) return;
        var contentHtml = txt ? App._mdToHtml(txt) : 'Fayl topilmadi yoki yuklanmadi.';
        box.innerHTML = '<div style="overflow-x:auto; padding-bottom:30px;"><div class="md-content">' + contentHtml + '</div></div>';
        App.icons(box);
      }

      if (isSys && file) {
        fetch('assets/md_books/' + file).then(function (r) {
          if (!r.ok) throw new Error('Fayl topilmadi');
          return r.text();
        }).then(function (txt) {
          showContent(txt);
        }).catch(function (e) {
          showContent('Fayl yuklashda xatolik: ' + e.message);
        });
      } else {
        var mdFiles = {};
        try { mdFiles = JSON.parse(localStorage.getItem('vocab_md_files_v1_' + lang) || '{}'); } catch(ex) {}
        showContent(mdFiles[fname]);
      }
    }
  });

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


  /* ---------- AI uchun qo'llanma (lug'at .md formati) ----------
     Asosiy maqsad — `Chalkashadi:` qatorini tushuntirish. Juftlash rejimi
     o'xshash so'zlarni O'ZI ham topadi, lekin avtomatik topilgani faqat
     yozilishiga qaraydi: ma'nosi bo'yicha chalkashtiriladigan so'zlarni
     (masalan "снимать/убирать") u bilolmaydi. Shuni faylda ko'rsatib
     qo'yish mumkin va u avtomatik topilganidan ustun turadi. */
  var VOCAB_AI_GUIDE = [
    '# Lug\'at .md formati — AI uchun qo\'llanma',
    '',
    'Quyidagi formatda lug\'at tayyorla. Har so\'z `##` sarlavhasi bilan boshlanadi.',
    '',
    '```markdown',
    '# Kategoriya nomi',
    '',
    '## 1. слово — tarjimasi',
    '',
    '> Qayerda: so\'z qanday holatda ishlatilishi — bir qatorda, aniq',
    '',
    '> Turkum: fe\'l',
    '',
    '> Yasalishi: при- (yaqinlashmoq) + ходить (yurmoq)',
    '',
    '> **Ma\'no guruhi:** bormoq',
    '',
    '> **Chalkashadi:** похожее1, похожее2',
    '',
    '> **Misol:** Rus tilidagi gap. (o\'zbekcha tarjimasi)',
    '',
    '## 2. другое — boshqa tarjima',
    '```',
    '',
    'Faqat shu maydonlar. Boshqa qator QO\'SHMA — ilova ularni ko\'rsatmaydi.',
    '',
    '## Har maydon nima uchun',
    '',
    '- `Qayerda:` — so\'z qanday vaziyatda ishlatilishini bir qatorda tushuntir.',
    '  Bu asosiy izoh, Reels\'da ham shu ko\'rinadi.',
    '- `**Misol:**` — rus/ingliz gap, qavs ichida o\'zbekcha tarjimasi.',
    '  Qavs ATAYLAB kerak: ilova undan tarjimani ajratib oladi.',
    '- `Yasalishi:` — so\'z qanday yasalgan yoki qayerdan kelib chiqqan.',
    '  Reels\'da "Batafsil" bosilganda ko\'rinadi (pastda).',
    '- Qolgan ikkitasi — FILTR TIZIMI uchun (pastda).',
    '',
    '## `Turkum:` — filtr uchun',
    '',
    'Bosh sahifadagi "Turkum" filtri shu qatordan yasaladi. Ro\'yxat qattiq',
    'belgilanmagan: sen qanday yozsang, filtrda o\'sha paydo bo\'ladi.',
    '',
    'Bitta so\'z bilan yoz, qavs va qo\'shimchasiz:',
    '',
    '    fe\'l · ot · sifat · son · ravish · olmosh',
    '    predlog · bog\'lovchi · yuklama · undov',
    '',
    'Yangi tur uchrasa o\'zing nom ber (masalan `undov` — "ого", "yeah").',
    'MUHIM: bir turkum uchun HAR DOIM bir xil so\'z yoz, aks holda filtrda',
    'ikkita alohida qator bo\'lib chiqadi.',
    '',
    '## `Yasalishi:` — so\'z qayerdan kelib chiqqan',
    '',
    'BITTA qator. Ikki xil savolga javob beradi va odatda ikkalasi bir gapda',
    'birlashadi: so\'z qanday QISMLARDAN yasalgan, va u qayerdan PAYDO',
    'bo\'lgan.',
    '',
    '**1) Qismlarga ajraladigan so\'z** — eng ko\'p uchraydigani. Rus tilida',
    'so\'zlarning katta qismi prefiks + o\'zak. Har bo\'lakning ma\'nosini',
    'qavsda ko\'rsat:',
    '',
    '    > Yasalishi: при- (yaqinlashmoq) + ходить (yurmoq)',
    '    > Yasalishi: пере- (qaytadan) + писать (yozmoq)',
    '    > Yasalishi: учить (o\'rgatmoq) + -тель (ish bajaruvchi shaxs)',
    '',
    'Bu eng foydali qism: bitta prefiksni tushungan odam o\'nlab qarindosh',
    'so\'zni birdaniga ochadi. `Chalkashadi:` ro\'yxatidagi bir o\'zakli',
    'fe\'llarga aynan shu qator izoh beradi.',
    '',
    '**2) O\'zlashgan so\'z** — qaysi tildan kirgani va asl ma\'nosi:',
    '',
    '    > Yasalishi: ingliz "Vauxhall" — Londondagi bekat nomi',
    '    > Yasalishi: lotin "computare" (hisoblamoq)',
    '    > Yasalishi: turkiy "qarpuz" — tarvuz',
    '',
    '**3) Ajralmaydigan tub so\'z** (`дом`, `вода`, `рука`) — bu qatorni',
    'umuman YOZMA. Zo\'rma-zo\'raki tarix o\'ylab topilgani yolg\'on bo\'ladi.',
    '',
    'Qoidalar:',
    '- Bir qatordan oshirma, ensiklopediya kerak emas.',
    '- Tushuntirish O\'ZBEKCHA, so\'z bo\'laklari asl tilida.',
    '- ISHONCHING KOMIL bo\'lmasa yozma. Noto\'g\'ri yasalish noto\'g\'ri',
    '  o\'rganishga olib keladi — bo\'sh qoldirish undan yaxshi.',
    '',
    '## `Chalkashadi:` — YOZILISHI o\'xshash so\'zlar',
    '',
    'O\'rganuvchi adashtiradigan so\'zlarni ko\'rsatadi. Dastur o\'xshash so\'zlarni',
    'o\'zi ham topadi, lekin u faqat YOZILISHIGA qaraydi. Sen esa MA\'NOSINI',
    'bilasan — shuning uchun quyidagilarni albatta yoz:',
    '',
    '1. **Bir o\'zakdan, prefiksi boshqa fe\'llar** — ma\'no aynan prefiksda:',
    '   `давать / отдавать / передавать / раздавать / выдавать / продавать`',
    '2. **Yozilishi deyarli bir xil, ma\'nosi butunlay boshqa**:',
    '   `предавать` (xiyonat qilmoq) va `придавать` (qo\'shmoq)',
    '3. **Ma\'nosi yaqin, ishlatilishi boshqa** — buni FAQAT sen bilasan,',
    '   dastur hech qachon topolmaydi: `оплатить / уплатить / заплатить`',
    '',
    'Qoidalar:',
    '- Faqat SHU faylda mavjud so\'zlarni yoz, aks holda e\'tiborsiz qoladi.',
    '- Vergul bilan ajrat.',
    '- Chalkashtirmaydigan so\'zni yozma — ortiqcha juftlik mashqni buzadi.',
    '- Bir so\'z uchun 1-7 tagacha yetarli.',
    '',
    '## `Ma\'no guruhi:` — MA\'NOSI bog\'liq so\'zlar',
    '',
    '`Chalkashadi:` yozilishi o\'xshashlar uchun.',
    '`Ma\'no guruhi:` esa ma\'nosi bog\'liqlar uchun — ular bir-biriga umuman',
    'o\'xshamasligi mumkin.',
    '',
    'Misol: "bormoq" tushunchasiga rus tilida bir nechta so\'z kiradi:',
    '',
    '```markdown',
    '## 1. иду — ketyapman (piyoda, hozir)',
    '',
    '> **Ma\'no guruhi:** bormoq',
    '',
    '## 2. хожу — yuraman (odatda, takroriy)',
    '',
    '> **Ma\'no guruhi:** bormoq',
    '',
    '## 3. еду — ketyapman (transportda)',
    '',
    '> **Ma\'no guruhi:** bormoq',
    '```',
    '',
    'Bir xil yorliq yozilgan so\'zlar BITTA guruh bo\'ladi. Har so\'zga',
    'qolganlarini sanab chiqish SHART EMAS — bitta yorliq yetarli.',
    '',
    'Qanday yorliq tanlash kerak:',
    '- Yorliq — O\'ZBEKCHA tushuncha nomi: `bormoq`, `gapirmoq`, `ko\'rmoq`,',
    '  `vaqt`, `oila a\'zolari`, `ranglar`.',
    '- Bir tushuncha uchun HAR DOIM bir xil yorliq yoz, aks holda guruh',
    '  ikkiga bo\'linib ketadi (`bormoq` va `borish` — ikki xil guruh).',
    '- Guruhda kamida 2 ta so\'z bo\'lsin, aks holda u ko\'rsatilmaydi.',
    '- Eng foydalisi — o\'zbekchada BITTA so\'z, rus tilida esa bir nechta:',
    '  aynan shunda o\'rganuvchi qaysi birini qachon ishlatishni bilmaydi.',
    '',
    '## Umumiy qoidalar',
    '',
    '- `Qayerda:` va `**Misol:**` — HAR so\'zga yoz.',
    '- `Turkum:` — HAR so\'zga yoz, filtr shunga tayanadi.',
    '- `Yasalishi:`, `Ma\'no guruhi:`, `**Chalkashadi:**` — faqat O\'RINLI',
    '  bo\'lsa yoz. Majburlama: ko\'p so\'zda ular bo\'lmaydi va bu normal.',
    '- Har faylda 20-40 so\'zdan oshirma — katta faylda AI charchab,',
    '  oxirgi so\'zlarga sayoz yozadi.',
    ''
  ].join('\n');

  App.actions.vocabAiGuide = function (a) {
    var html =
      '<p class="muted" style="font-size:12.5px;margin:0 0 12px">' +
      'Bu matnni AI ga bering (ChatGPT, Claude va h.k.) — u to\'g\'ri formatda, ' +
      'juftliklari ko\'rsatilgan .md tayyorlab beradi. Keyin uni "So\'zlarni yangilash" orqali yuklang.</p>' +
      '<div class="btn-row" style="margin-bottom:12px">' +
      '<button class="btn" id="vg-copy"><span data-icon="copy" data-icon-size="15"></span>Nusxa olish</button>' +
      '<button class="btn sec" id="vg-dl"><span data-icon="download" data-icon-size="15"></span>.md yuklab olish</button>' +
      '</div>' +
      '<pre class="md-pre" style="white-space:pre-wrap;font-size:11.5px;line-height:1.5;max-height:50vh;overflow:auto">' +
      App.esc(VOCAB_AI_GUIDE) + '</pre>';
    var sh = App.sheet(html, { title: 'AI uchun qo\'llanma' });
    App.icons(sh);
    sh.querySelector('#vg-copy').onclick = function () {
      try {
        navigator.clipboard.writeText(VOCAB_AI_GUIDE)
          .then(function () { App.toast('✅ Nusxa olindi'); })
          .catch(function () { App.toast('⚠️ Nusxa olinmadi'); });
      } catch (e) { App.toast('⚠️ Nusxa olinmadi'); }
    };
    sh.querySelector('#vg-dl').onclick = function () {
      App.download('Lugat-AI-qollanma.md', VOCAB_AI_GUIDE);
    };
  };

  App.actions.vocabCatManage = function (a) {
    var html =
      '<button class="list-row" data-act="vocabExportCatMD" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" data-icon="download" data-icon-size="15"></span><div class="li-main"><div class="li-title">MD fayl qilib yuklab olish (.md)</div><div class="li-sub">Ushbu kategoriyadagi so\'zlarni .md fayl sifatida yuklash</div></div></button>' +
      '<button class="list-row" data-act="vocabAiGuide" data-arg=\'' + App.arg(a) + '\'><span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="file" data-icon-size="15"></span><div class="li-main"><div class="li-title">AI uchun qo\'llanma</div><div class="li-sub">Shu matnni AI ga bering — juftliklari bilan to\'g\'ri .md tayyorlab beradi</div></div></button>' +
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
    var existing = (V.data[a.cat] || []).map(function (w, i) {
      var line = (i + 1) + ') ' + w.ru + ' - ' + w.uz;
      if (w.note || w.ex) {
        line += ' # ' + (w.note || '') + (w.ex ? ' | ' + w.ex : '');
      }
      return line;
    }).join('\n');
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
    var slice = words.slice(r.from - 1, r.to);
    /* "O'rgandim" deb belgilangan so'z mashqqa TUSHMAYDI. Flashcard,
       svayp, reels, test, tinglash, juftlash — hammasi shu funksiyadan
       so'z oladi, shuning uchun filtr shu yerda. Ilgari bu belgi faqat
       bosh sahifadagi filtr edi va o'rganilgan so'z mashqda chiqaverardi. */
    return window.WordState ? WordState.forPractice(slice) : slice;
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
      var inFolder = catParent(cat);
      var backParams = inFolder ? { lang: lang, folder: inFolder } : { lang: lang };

      if (!cat) {
        App.go('vocab', { lang: lang });
        return;
      }

      var loaded = V.lang === lang && V.data[cat];
      if (!loaded) {
        var rightTopHtml =
        '<button class="icon-btn ghost" data-act="vocabExportCatMD" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' aria-label="MD yuklab olish" title=".md qilib yuklab olish"><span data-icon="download" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="vocabCatManage" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' aria-label="Boshqarish" title="Kategoriyani boshqarish"><span data-icon="settings" data-icon-size="18"></span></button>';

      page.innerHTML = topbar(lastSeg(cat), 'vocab', backParams, rightTopHtml) +
          '<div class="load-wrap"><div class="spinner"></div></div>';
        App.icons(page);
        loadDict(lang).then(function () { App.reload(); });
        return;
      }

      var total = V.data[cat].length;
      var r = getRange(lang, cat, total);
      var full = r && r.from === 1 && r.to === total;

      var practiceLeft = rangedWords(lang, cat).length;
      var prog = srsProgress(lang, cat);
      var due = srsDue(lang, cat).length;

      var srsActionHtml = '';
      if (due > 0) {
        srsActionHtml = '<button class="srs-due-btn" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_flash', p: { lang: lang, cat: cat, src: 'due' } }) + '\'><span data-icon="clock" data-icon-size="13"></span>Bugun takrorlash <b>(' + due + ')</b></button>';
      } else if (prog.total > 0) {
        srsActionHtml = '<span class="srs-done-tag"><span data-icon="check" data-icon-size="13"></span>Takrorlash tugagan</span>';
      }

      var rightTopHtml =
        '<button class="icon-btn ghost" data-act="vocabExportCatMD" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' aria-label="MD yuklab olish" title=".md qilib yuklab olish"><span data-icon="download" data-icon-size="18"></span></button>' +
        '<button class="icon-btn ghost" data-act="vocabCatManage" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' aria-label="Boshqarish" title="Kategoriyani boshqarish"><span data-icon="settings" data-icon-size="18"></span></button>';

      page.innerHTML = topbar(lastSeg(cat), 'vocab', backParams, rightTopHtml) +
        '<div class="srs-bar">' +
        '<div class="srs-top">' +
        '<div class="srs-left"><span>O\'zlashtirildi</span> <b>' + prog.learned + '/' + prog.total + '</b></div>' +
        srsActionHtml +
        '</div>' +
        '<div class="bar"><i style="width:' + (prog.total ? Math.round(prog.learned * 100 / prog.total) : 0) + '%"></i></div></div>' +
        '<button class="list-row" data-act="vocabRange" data-arg=\'' + App.arg({ lang: lang, cat: cat }) + '\' style="margin-bottom:14px">' +
        '<span class="li-ic" data-icon="list" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Oraliq: ' + r.from + '–' + r.to + (full ? ' (barchasi)' : '') + '</div>' +
        /* Mashqda NECHTA so'z qolganini ham ko'rsatamiz: oraliq 150 bo'lsa
           ham, o'rganilganlar chiqarilgach 40 ta qolishi mumkin. Ilgari
           yorliq faqat oraliq kengligini aytardi va bu chalg'itardi. */
        '<div class="li-sub">' + (r.to - r.from + 1) + ' ta so\'z' +
        (practiceLeft < (r.to - r.from + 1)
          ? ' · mashqda ' + practiceLeft + ' ta'
          : '') +
        ' · jami ' + total + '</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +
        '<div class="btn-row" style="flex-direction:column;gap:10px">' +
        methodBtn('vocab_reels', lang, cat, 'play', 'Reels', 'btn-reels-ig') +
        methodBtn('vocab_flash', lang, cat, 'refresh', 'Flashcardlar', 'sec') +
        methodBtn('vocab_pair', lang, cat, 'copy', 'Juftlash (o\'xshash so\'zlar)') +
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
          var extraHtml = '';
          if (w.note || w.ex) {
            extraHtml = '<div style="font-size:11.5px;color:var(--text-3);margin-top:2px">' +
              (w.note ? '<span style="color:var(--accent)">💡 ' + App.esc(w.note) + '</span> ' : '') +
              (w.ex ? '<i>📝 ' + App.esc(w.ex) + '</i>' : '') +
              '</div>';
          }
          return '<button class="list-row" data-i="' + i + '"><div class="li-main">' +
            '<div class="li-title">' + App.esc(w.ru) + '</div><div class="li-sub">' + App.esc(w.uz) + '</div>' +
            extraHtml +
            '</div>' +
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
      /* Mavjud so'zning boshqa maydonlari (izoh, misol, sinonim, eslab
         qolish va h.k.) SAQLANIB QOLADI — faqat ru/uz almashadi. Ilgari
         bu yerda butun obyekt yangisiga almashtirilardi, ya'ni tez
         tahrirlashning o'zi AI yozgan boy ma'lumotni jimgina o'chirib
         yuborardi. */
      if (isNew) {
        words.push({ ru: ru, uz: uz });
      } else {
        var merged = {}; var k;
        for (k in words[idx]) { if (words[idx].hasOwnProperty(k)) merged[k] = words[idx][k]; }
        merged.ru = ru; merged.uz = uz;
        words[idx] = merged;
      }
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
    var due = (V.data[cat] || []).filter(function (w) {
      var s = all[srsKey(lang, cat, w.ru)];
      return !s || !s.due || s.due <= today;
    });
    /* Takrorlash ro'yxatiga ham tushmasin — aks holda "o'rgandim" bosilgan
       so'z ertasiga "bugun takrorlash" bo'lib qaytib kelardi. */
    return window.WordState ? WordState.forPractice(due) : due;
  }

  /* Kategoriya bo'yicha o'zlashtirish darajasi (3+ marta to'g'ri = o'zlashtirilgan) */
  /* O'zlashtirish darajasi. IKKALA manba ham hisoblanadi:
       - SRS: 3+ marta to'g'ri javob berilgan (tizim o'zi qaror qiladi);
       - "O'rgandim": foydalanuvchi o'zi belgilagan.
     Ilgari faqat SRS sanalardi va 100 ta so'zni qo'lda belgilasangiz ham
     progress qatori qimirlamasdi — bu ikki xil "o'rganilgan" tushunchasi
     bir-birini ko'rmasligini bildirardi. */
  function srsProgress(lang, cat) {
    var all = srsAll(), words = V.data[cat] || [], learned = 0;
    var ws = window.WordState;
    words.forEach(function (w) {
      if (ws && ws.isMastered(w.ru)) { learned++; return; }
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
      /* "O'rgandim" belgisi BU YERDA ham amal qiladi. Ilgari filtr yo'q
         edi: butunlay o'rganilgan deb belgilangan so'z Xatolar ro'yxatida
         turaverardi va u yerdan flashcard mashqiga tushardi — ya'ni
         "hech qayerda chiqmaydi" va'dasi buzilardi. */
      var raw = (j.mistakes || []).map(function (m) {
        return { ru: m.word_ru, uz: m.word_uz, cat: m.category };
      });
      MIS.list = window.WordState ? WordState.forPractice(raw) : raw;
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
      '<div class="fc-face fc-front"><span class="fc-lbl" id="fc-lbl-f"></span><span class="fc-word" id="fc-word-f"></span>' +
        '<span class="fc-pron" id="fc-pron"></span></div>' +
      '<div class="fc-face fc-back"><span class="fc-lbl" id="fc-lbl-b"></span><span class="fc-word" id="fc-word-b"></span>' +
        '<div class="fc-extra" id="fc-extra"></div></div>' +
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

    /* Talaffuz — FAQAT asl so'z tomonida ko'rsatiladi (tarjima tomonida
       ma'nosiz). O'qishdan oldin qanday aytilishini ko'rsatib qo'yadi. */
    var pronEl = App.el('fc-pron');
    if (pronEl) pronEl.textContent = (isL1 && w.pronunciation) ? w.pronunciation : '';

    renderFcExtra(w, isL1);
    speakSide(page);
  }

  /* Orqa tomondagi qo'shimcha panel. "Eslab qolish" ATAYLAB birinchi va
     eng ko'zga tashlanadigan — mashqning butun ma'nosi shu yordamda.
     Qolganlari (turkum/sinonim/antonim/shakllar/birikma) bo'lsa qo'shiladi,
     bo'lmasa panelning o'zi ko'rinmaydi (bo'sh joy qoldirmaslik uchun). */
  function renderFcExtra(w, isL1) {
    var el = App.el('fc-extra'); if (!el) return;
    /* Faqat ASL so'z tomonida chiqadi — tarjima tomonida bu ma'lumotlar
       o'rinsiz (masalan "Eslab qolish" rus so'zi haqida gapiradi). */
    if (!isL1) { el.innerHTML = ''; el.hidden = true; return; }

    var rows = [];
    if (w.mnemonic) {
      rows.push('<div class="fc-mnemonic"><span data-icon="bulb" data-icon-size="14"></span>' +
        App.esc(w.mnemonic) + '</div>');
    }
    var tags = [];
    if (w.partOfSpeech) tags.push(App.esc(w.partOfSpeech));
    if (w.forms) tags.push(App.esc(w.forms));
    if (tags.length) rows.push('<div class="fc-tags">' + tags.join(' · ') + '</div>');

    if (w.synonyms) rows.push('<div class="fc-extra-row"><b>Sinonim:</b> ' + App.esc(w.synonyms) + '</div>');
    if (w.antonyms) rows.push('<div class="fc-extra-row"><b>Antonim:</b> ' + App.esc(w.antonyms) + '</div>');
    if (w.collocations) rows.push('<div class="fc-extra-row"><b>Birikma:</b> ' + App.esc(w.collocations) + '</div>');

    if (!rows.length) { el.innerHTML = ''; el.hidden = true; return; }
    el.hidden = false;
    el.innerHTML = rows.join('');
    App.icons(el);
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

  /* ---------- Juftlash: o'zaro o'xshash/adashtiriladigan so'zlarni birga ko'rsatish ----------
     Uchta manbadan guruh topiladi (eng ishonchlisidan boshlab):
     0) .md faylda AI/qo'lda yozilgan "Chalkashadi:" qatori — so'z.pairWith massivi
        (parseMdToDictCategories shu yerda to'ldiradi).
     1) Rus fe'llarida umumiy o'zak — prefiks olib tashlansa qolgan qism bir xil bo'lgan
        so'zlar (Давать/Отдавать/Передавать/Раздавать... — hammasi "-давать" bilan tugaydi).
     2) Imlosi bir-biriga juda yaqin so'zlar (1-2 harf farqi) — masalan Предавать/Придавать.
     Svayp mexanizmi Flashcard bilan bir xil: bitta kart ko'rinadi, chapga/o'ngga surib
     keyingi guruhga o'tiladi. */
  var PS = null; // pairing session state

  /* Juftlash algoritmi `assets/js/core/paircore.js` da — YAGONA manba.
     Ilgari aynan shu kod bu yerda ham, home.js da ham nusxa bo'lib turardi;
     biri tuzatilib, ikkinchisi eskirib qolish xavfi bor edi. */
  function buildPairGroups(words, lang) {
    return window.PairCore ? PairCore.build(words, lang) : [];
  }

  /* Guruhdagi so'zlarning umumiy boshi/oxirini o'chirib, farq qiladigan qismini <b> bilan ajratadi */
  function highlightDiff(list) {
    if (list.length < 2) return list.map(function (w) { return App.esc(w); });
    var minLen = Math.min.apply(null, list.map(function (w) { return w.length; }));
    var pre = 0;
    while (pre < minLen && list.every(function (w) { return w[pre] === list[0][pre]; })) pre++;
    var suf = 0;
    while (suf < minLen - pre && list.every(function (w) { return w[w.length - 1 - suf] === list[0][list[0].length - 1 - suf]; })) suf++;
    return list.map(function (w) {
      var p = App.esc(w.slice(0, pre));
      var mid = App.esc(w.slice(pre, w.length - suf));
      var s = App.esc(w.slice(w.length - suf));
      return p + (mid ? '<b class="pc-diff">' + mid + '</b>' : '') + s;
    });
  }

  /* Bo'limlar ekrani holati — har bir o'xshash-so'zlar oilasi alohida bo'lim sifatida
     ko'rsatiladi (avval hammasi bitta uzun svayp navbatida edi). */
  var PAIR_STATE = { lang: null, cat: null, mode: 'list', groups: [] };

  function groupPreview(g) {
    var names = g.map(function (w) { return w.ru; });
    if (names.length <= 3) return names.join(', ');
    return names.slice(0, 3).join(', ') + ' va yana ' + (names.length - 3) + ' ta';
  }

  App.view('vocab_pair', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english', cat = params.cat;
      var isFreshEntry = (PAIR_STATE.lang !== lang || PAIR_STATE.cat !== cat);
      var start = function () {
        var words = rangedWords(lang, cat);
        if (!words.length) { App.toast('Bu oraliqda so\'z yo\'q'); App.go('vocab_practice', { lang: lang, cat: cat }); return; }
        var groups = buildPairGroups(words, lang);
        if (!groups.length) {
          App.toast('Bu oraliqda adashtiriladigan o\'xshash so\'zlar topilmadi');
          App.go('vocab_practice', { lang: lang, cat: cat }); return;
        }
        if (isFreshEntry) { PAIR_STATE = { lang: lang, cat: cat, mode: 'list', groups: groups }; }
        else { PAIR_STATE.groups = groups; }
        if (PAIR_STATE.mode === 'swipe' && PS) renderPairPage(page);
        else renderPairSections(page);
      };
      if (V.lang === lang && V.data[cat]) start(); else loadDict(lang).then(start);
    }
  });

  function renderPairSections(page) {
    var groups = PAIR_STATE.groups;
    page.innerHTML = topbar('Juftlash', 'vocab_practice', { lang: PAIR_STATE.lang, cat: PAIR_STATE.cat }) +
      '<p class="muted" style="font-size:11.5px;margin:-6px 0 12px">' + groups.length + ' ta o\'xshash so\'zlar oilasi topildi. Bo\'limni oching — so\'zlar ro\'yxati chiqadi.</p>' +
      (groups.length > 1
        ? '<button class="btn sec" data-act="vocabPairStartAll" style="margin-bottom:14px"><span data-icon="refresh" data-icon-size="16"></span>Hammasini svayp bilan mashq qilish</button>'
        : '') +
      '<div id="pcs-list"></div>';
    App.icons(page);
    var box = App.el('pcs-list');
    box.innerHTML = groups.map(function (g, i) {
      return '<button class="list-row" data-act="vocabPairOpenGroup" data-arg=\'' + App.arg({ i: i }) + '\'>' +
        '<span class="li-ic" data-icon="copy" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + App.esc(groupPreview(g)) + '</div>' +
        '<div class="li-sub">' + g.length + ' ta so\'z</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
    }).join('');
    App.icons(box);
  }

  App.actions.vocabPairOpenGroup = function (a) {
    var g = PAIR_STATE.groups[+a.i];
    if (!g) return;
    var html =
      '<p class="muted" style="font-size:12.5px;margin:-6px 0 12px">' + g.length + ' ta o\'xshash so\'z. Bosilsa ovozda o\'qiydi.</p>' +
      '<div id="pcs-words"></div>' +
      '<button class="btn" data-act="vocabPairPracticeGroup" data-arg=\'' + App.arg({ i: a.i }) + '\' style="margin-top:14px">' +
      '<span data-icon="refresh" data-icon-size="16"></span>Shu guruhni svayp bilan mashq qilish</button>';
    var sh = App.sheet(html, { title: 'O\'xshash so\'zlar' });
    App.icons(sh);
    var box = sh.querySelector('#pcs-words');
    box.innerHTML = g.map(function (w, wi) {
      return '<div class="list-row pcs-word-row" data-i="' + wi + '"><div class="li-main">' +
        '<div class="li-title">' + App.esc(w.ru) + '</div><div class="li-sub">' + App.esc(w.uz) + '</div></div></div>';
    }).join('');
    box.querySelectorAll('.pcs-word-row').forEach(function (row) {
      row.onclick = function () { speakWord(g[+row.getAttribute('data-i')].ru, PAIR_STATE.lang); };
    });
  };

  App.actions.vocabPairStartAll = function () {
    PS = { lang: PAIR_STATE.lang, cat: PAIR_STATE.cat, list: PAIR_STATE.groups.slice(), idx: 0, good: 0, bad: 0, mistakes: [], startedAt: Date.now(), logged: false };
    PAIR_STATE.mode = 'swipe';
    App.reload();
  };

  App.actions.vocabPairPracticeGroup = function (a) {
    var g = PAIR_STATE.groups[+a.i];
    if (!g) return;
    App.closeSheet();
    PS = { lang: PAIR_STATE.lang, cat: PAIR_STATE.cat, list: [g], idx: 0, good: 0, bad: 0, mistakes: [], startedAt: Date.now(), logged: false };
    PAIR_STATE.mode = 'swipe';
    App.reload();
  };

  App.actions.vocabPairBackToList = function () {
    PAIR_STATE.mode = 'list';
    App.reload();
  };

  function fitPairLayout(page) {
    var body = App.el('pc-body'), topbar = page.querySelector('.topbar');
    if (!body || !topbar) return;
    var nav = document.querySelector('.botnav');
    var top = topbar.getBoundingClientRect().bottom;
    var navVisible = nav && getComputedStyle(nav).display !== 'none';
    var bottom = navVisible ? nav.getBoundingClientRect().top : window.innerHeight;
    var avail = bottom - top - 24;
    body.style.height = Math.max(avail, 280) + 'px';
  }

  function renderPairPage(page) {
    page.innerHTML =
      '<div class="topbar" style="margin:-16px -15px 12px">' +
      '<button class="icon-btn ghost" data-act="vocabPairBackToList"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
      '<h1>Juftlash</h1>' +
      finishBtnHtml('vocabPairFinish') + '</div>' +

      '<div id="pc-body" style="display:flex;flex-direction:column">' +
      '<p class="muted" style="font-size:11.5px;margin:0 0 10px">O\'xshash so\'zlar birga ko\'rsatiladi. Farqini bilsangiz o\'ngga, hali chalkashtirsangiz chapga suring. So\'zga bosilsa ovozda o\'qiydi.</p>' +
      '<div class="stat-strip" style="margin:0 0 10px">' +
      '<div class="s"><div class="n" id="pc-idx">1/' + PS.list.length + '</div><div class="l">Progress</div></div>' +
      '<div class="s"><div class="n" style="color:var(--success)" id="pc-good">0</div><div class="l">Bilaman</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)" id="pc-bad">0</div><div class="l">Chalkashtiraman</div></div>' +
      '</div>' +

      '<div id="pc-card-wrap" style="flex:1;min-height:0;display:flex;justify-content:center">' +
      '<div class="pc-card" id="pc-card"><div class="pc-lbl" id="pc-lbl"></div><div class="pc-list" id="pc-list"></div></div>' +
      '</div>' +

      '<div class="btn-row" style="margin-top:12px">' +
      '<button class="btn danger" id="pc-bad-btn">✕ Chalkashtiraman</button>' +
      '<button class="btn" id="pc-good-btn" style="background:var(--success)">✓ Farqini bilaman</button>' +
      '</div>' +
      '</div>';
    App.icons(page);
    fitPairLayout(page);
    requestAnimationFrame(function () { fitPairLayout(page); });
    if (!page._pcResizeBound) {
      page._pcResizeBound = true;
      window.addEventListener('resize', function () { if (App.el('pc-body')) fitPairLayout(page); });
    }

    App.el('pc-good-btn').onclick = function () { swipePair(page, true); };
    App.el('pc-bad-btn').onclick = function () { swipePair(page, false); };
    initSwipeDragPair(page);

    renderPairCard(page);
  }

  function currentGroup() { return PS.list[PS.idx]; }

  function renderPairCard(page) {
    if (PS.idx >= PS.list.length) { showPairResult(page); return; }
    var group = currentGroup();
    var card = App.el('pc-card');
    card.style.transition = 'none';
    card.style.transform = 'translate(0,0) rotate(0deg)';
    void card.offsetWidth;
    card.style.transition = '';

    var ruWords = group.map(function (w) { return String(w.ru || ''); });
    var highlighted = highlightDiff(ruWords);
    App.el('pc-lbl').textContent = group.length + ' ta o\'xshash so\'z';
    App.el('pc-list').innerHTML = group.map(function (w, i) {
      return '<div class="pc-row" data-i="' + i + '"><span class="pc-w">' + highlighted[i] + '</span>' +
        '<span class="pc-t">' + App.esc(w.uz) + '</span></div>';
    }).join('');
    App.el('pc-idx').textContent = (PS.idx + 1) + '/' + PS.list.length;

    App.el('pc-list').querySelectorAll('.pc-row').forEach(function (row) {
      row.onclick = function (e) {
        e.stopPropagation();
        var w = group[+row.getAttribute('data-i')];
        speakWord(w.ru, PS.lang);
      };
    });
  }

  function swipePair(page, known) {
    var card = App.el('pc-card');
    var endX = known ? window.innerWidth : -window.innerWidth;
    card.style.transition = 'transform .35s ease';
    card.style.transform = 'translateX(' + endX + 'px) rotate(' + (endX * 0.05) + 'deg)';
    var group = currentGroup();
    group.forEach(function (w) {
      var cat = w.cat || PS.cat;
      srsUpdate(PS.lang, cat, w.ru, known);
      if (known) App.call('remove_mistake', { lang: PS.lang, category: cat, ru: w.ru }).catch(function () {});
      else App.call('add_mistake', { lang: PS.lang, category: cat, ru: w.ru, uz: w.uz }).catch(function () {});
    });
    if (known) PS.good++; else { PS.bad++; PS.mistakes.push(group); }
    App.el('pc-good').textContent = PS.good;
    App.el('pc-bad').textContent = PS.bad;
    setTimeout(function () { PS.idx++; renderPairCard(page); }, 260);
  }

  function initSwipeDragPair(page) {
    var card = App.el('pc-card');
    var startX = 0, dx = 0, dragging = false, isTap = true;
    function start(e) {
      if (e.target.closest('.pc-row')) return;
      startX = (e.touches ? e.touches[0].clientX : e.clientX); dragging = true; isTap = true; dx = 0; card.style.transition = 'none';
    }
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
      if (dx > 80) swipePair(page, true);
      else if (dx < -80) swipePair(page, false);
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

  function showPairResult(page) {
    var total = PS.good + PS.bad;
    var pct = total ? Math.round((PS.good / total) * 100) : 0;
    page.innerHTML =
      '<div style="text-align:center;padding-top:8px">' +
      '<div class="res-circle"><span>' + pct + '%</span></div>' +
      '<h2 style="margin:0 0 22px">Juftlash tugadi</h2>' +
      '<div class="stat-strip" style="max-width:280px;margin:0 auto 26px">' +
      '<div class="s"><div class="n" style="color:var(--success)">' + PS.good + '</div><div class="l">Bilaman</div></div>' +
      '<div class="s"><div class="n" style="color:var(--danger)">' + PS.bad + '</div><div class="l">Chalkashtiraman</div></div>' +
      '<div class="s"><div class="n">' + total + '</div><div class="l">Jami</div></div>' +
      '</div>' +
      (PS.mistakes.length
        ? '<button class="btn" id="pc-retry">⚠ Hali chalkashtirgan (' + PS.mistakes.length + ') juftlikni qaytarish</button>'
        : '<p class="muted">Barcha juftliklarni ajrata olasiz! 🎉</p>') +
      '<button class="btn ' + (PS.mistakes.length ? 'ghost' : '') + '" style="margin-top:10px" id="pc-finish">Tugatish</button>' +
      '</div>';
    App.icons(page);
    if (total > 0 && !PS.logged) {
      logVocabProgress(PS.lang, PS.cat || '', total, 'pairing', PS.startedAt, { good: PS.good, bad: PS.bad });
      PS.logged = true;
    }
    var retry = App.el('pc-retry');
    if (retry) retry.onclick = function () {
      var mistakes = PS.mistakes;
      PS.list = mistakes; PS.idx = 0; PS.good = 0; PS.bad = 0; PS.mistakes = []; PS.logged = false;
      renderPairPage(page);
    };
    App.el('pc-finish').onclick = function () {
      App.actions.vocabPairBackToList();
    };
  }

  App.actions.vocabPairFinish = function () {
    if (!PS.logged) {
      logVocabProgress(PS.lang, PS.cat || '', PS.good + PS.bad, 'pairing', PS.startedAt, { good: PS.good, bad: PS.bad });
      PS.logged = true;
    }
    App.actions.vocabPairBackToList();
  };

  /* ---------- Reels rejimi: TikTok / Instagram uslubidagi tik lenta ---------- */
  App.view('vocab_reels', {
    nav: 'languages',
    leave: function () {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    },
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english';
      var cat = params.cat;
      var loaded = V.lang === lang && V.data[cat];

      if (!loaded) {
        page.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
        loadDict(lang).then(function () { App.reload(); });
        return;
      }

      var words = rangedWords(lang, cat);
      if (!words.length) {
        page.innerHTML = topbar(cat, 'vocab_practice', { lang: lang, cat: cat }) +
          App.empty({ icon: 'list', title: 'So\'zlar yo\'q', text: 'Bu bo\'limda hali so\'zlar mavjud emas.' });
        App.icons(page);
        return;
      }

      var i = 0;
      var inFolder = catParent(cat);
      var backParams = { lang: lang, cat: cat };

      page.innerHTML =
        '<div class="lm-reels vr-reels">' +
        '<div class="vr-header">' +
        '<div class="vr-header-left"><span class="vr-header-tag">Reels</span></div>' +
        '<div class="vr-header-right">' +
        '<span class="vr-header-title">' + App.esc(lastSeg(cat)) + '</span>' +
        '<button class="lm-r-x" aria-label="Yopish" data-act="go" data-arg=\'' + App.arg({ v: 'vocab_practice', p: backParams }) + '\'><span data-icon="close" data-icon-size="20"></span></button>' +
        '</div>' +
        '</div>' +
        '<div class="lm-r-scroll vr-scroll"></div>' +
        '<div class="lm-r-rail vr-rail">' +
        '<button class="lm-r-a" id="vr-btn-speak" aria-label="Talaffuz"><span data-icon="volume" data-icon-size="19"></span><b>Ovoz</b></button>' +
        '<button class="lm-r-a" id="vr-btn-info" aria-label="Batafsil"><span data-icon="list" data-icon-size="19"></span><b>Batafsil</b></button>' +
        '<button class="lm-r-a" id="vr-btn-srs" aria-label="Yodlandi"><span data-icon="check" data-icon-size="19"></span><b>Yodlandi</b></button>' +
        '<button class="lm-r-a" id="vr-btn-edit" aria-label="Tahrirlash"><span data-icon="edit" data-icon-size="19"></span><b>Tahrir</b></button>' +
        '<button class="lm-r-a danger" id="vr-btn-del" aria-label="O\'chirish"><span data-icon="trash" data-icon-size="19"></span><b>O\'chir</b></button>' +
        '</div>' +
        '</div>';

      App.icons(page);

      var scroll = page.querySelector('.vr-scroll');

      /* "Batafsil" bosilganda ko'rinadigan TO'LIQ panel — Reels'ning
         o'zi (Izoh+Misol) yengil qoladi, bu yerda esa AI yozgan HAMMA
         narsa: Turkum, Yasalishi, Talaffuz, Shakllar, Sinonim, Antonim,
         Birikma, Eslab qolish, so'ng Izoh/Misol. Bo'sh maydon tashlanadi. */
      function buildReelsDetailHtml(w) {
        var rows = [];
        function row(label, value) {
          if (!value) return;
          rows.push(
            '<div class="vr-md-item"><span class="vr-md-badge">' + App.esc(label) + '</span>' +
            '<span class="vr-md-text">' + App.esc(value) + '</span></div>'
          );
        }
        row('Turkum', w.partOfSpeech);
        /* Yasalish turkumdan keyin: avval "bu nima", keyin "qayerdan". */
        row('Yasalishi', w.formation);
        row('Talaffuz', w.pronunciation);
        row('Shakllar', w.forms);
        row('Eslab qolish', w.mnemonic);
        row('Sinonim', w.synonyms);
        row('Antonim', w.antonyms);
        row('Birikma', w.collocations);
        if (w.note) row('Izoh', w.note);
        var ex = (w.ex || w.example || '').trim();
        if (ex) row('Misol', ex);

        if (!rows.length) {
          return '<div class="vr-detail-empty">Bu so\'z uchun qo\'shimcha ma\'lumot hali yo\'q.</div>';
        }
        return rows.join('');
      }

      function formatReelsMarkdown(w) {
        var html = '';
        if (w.note) {
          var rawNote = String(w.note || '').trim();
          rawNote = rawNote.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B50}\u{2B55}\u{200D}\u{FE0F}\u{1F000}-\u{1FFFF}]/gu, '');
          html +=
            '<div class="vr-md-story">' +
            '<div class="vr-story-text">' + App.esc(rawNote) + '</div>' +
            '</div>';
        }

        var ex = (w.ex || w.example || '').trim();
        if (ex) {
          ex = ex.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B50}\u{2B55}\u{200D}\u{FE0F}\u{1F000}-\u{1FFFF}]/gu, '');
          var m = ex.match(/^(.*?)\s*\((.*?)\)$/);
          if (m) {
            var ruSent = m[1].trim();
            var uzSent = m[2].trim();
            html +=
              '<div class="vr-md-quote">' +
              '<div class="vr-quote-ru">«' + App.esc(ruSent.replace(/^[«"'\s]+|[»"'\s]+$/g, '')) + '»</div>' +
              '<div class="vr-quote-uz">' + App.esc(uzSent) + '</div>' +
              '</div>';
          } else {
            html +=
              '<div class="vr-md-quote">' +
              '<div class="vr-quote-ru">«' + App.esc(ex.replace(/^[«"'\s]+|[»"'\s]+$/g, '')) + '»</div>' +
              '</div>';
          }
        }
        return html;
      }

      function buildSlides() {
        scroll.innerHTML = '';
        words.forEach(function (w, k) {
          var sl = document.createElement('div');
          sl.className = 'lm-r-slide' + (k === i ? ' on' : '');
          
          sl.innerHTML =
            '<div class="vr-screen-flow">' +
            '<div class="vr-summary">' +
            '<div class="vr-md-header">' +
            '<h1 class="vr-md-title">' + App.esc(w.ru) + '</h1>' +
            '<div class="vr-md-sub">' + App.esc(w.uz) + '</div>' +
            '<div class="vr-md-divider"></div>' +
            '</div>' +
            '<div class="vr-md-content">' +
            formatReelsMarkdown(w) +
            '</div>' +
            '</div>' +
            /* "Batafsil" bosilganda YUQORIDAGI o'rniga shu ko'rinadi (CSS
               orqali, .vr-detail-on klassiga qarab) — element yasab-buzib
               o'tirilmaydi, ikkalasi ham oldindan tayyor turadi. */
            '<div class="vr-detail-panel">' + buildReelsDetailHtml(w) + '</div>' +
            '</div>';

          scroll.appendChild(sl);
        });
        App.icons(scroll);
        markActive();
      }

      var autoSpeak = localStorage.getItem('vocab_reels_autospeak') === '1';
      var speakTimer = null;

      function playAutoSpeak() {
        if (!autoSpeak || !words[i]) return;
        clearTimeout(speakTimer);
        speakTimer = setTimeout(function () {
          speakWord(words[i].ru, lang);
        }, 180);
      }

      function markActive() {
        [].forEach.call(scroll.children, function (c, k) {
          c.classList.toggle('on', k === i);
        });
        playAutoSpeak();
      }

      var tick = null;
      scroll.addEventListener('scroll', function () {
        if (tick) return;
        tick = requestAnimationFrame(function () {
          tick = null;
          var h = scroll.clientHeight || 1;
          var k = Math.round(scroll.scrollTop / h);
          if (k !== i && k >= 0 && k < words.length) {
            i = k;
            markActive();
          }
        });
      }, { passive: true });

      function goTo(k, smooth) {
        k = Math.max(0, Math.min(words.length - 1, k));
        i = k; markActive();
        scroll.scrollTo({ top: k * scroll.clientHeight, behavior: smooth ? 'smooth' : 'auto' });
      }

      buildSlides();

      // Ekranni ikki marta bosganda (Double Tap / Double Click) ovoz chiqarish
      function showDoubleTapPulse(x, y) {
        var pulse = document.createElement('div');
        pulse.className = 'vr-tap-pulse';
        pulse.innerHTML = '<span data-icon="volume" data-icon-size="34"></span>';
        if (x !== undefined && y !== undefined) {
          pulse.style.left = x + 'px';
          pulse.style.top = y + 'px';
        } else {
          pulse.style.left = '50%';
          pulse.style.top = '50%';
        }
        page.appendChild(pulse);
        App.icons(pulse);
        setTimeout(function () { pulse.remove(); }, 500);
      }

      function triggerSpeak(x, y) {
        if (words[i]) {
          speakWord(words[i].ru, lang);
          showDoubleTapPulse(x, y);
        }
      }

      var lastTap = 0;
      scroll.addEventListener('touchend', function (e) {
        var now = Date.now();
        if (now - lastTap < 320) {
          e.preventDefault();
          var touch = e.changedTouches ? e.changedTouches[0] : null;
          var x = touch ? touch.clientX : window.innerWidth / 2;
          var y = touch ? touch.clientY : window.innerHeight / 2;
          triggerSpeak(x, y);
          lastTap = 0;
        } else {
          lastTap = now;
        }
      });

      scroll.addEventListener('dblclick', function (e) {
        triggerSpeak(e.clientX, e.clientY);
      });

      // Avto-ovoz tugmasi
      var btnSpeak = page.querySelector('#vr-btn-speak');
      function updateSpeakBtn() {
        if (!btnSpeak) return;
        btnSpeak.classList.toggle('active', autoSpeak);
        var b = btnSpeak.querySelector('b');
        if (b) b.textContent = autoSpeak ? 'Ovoz yoqiq' : 'Avto ovoz';
      }
      updateSpeakBtn();

      if (btnSpeak) {
        btnSpeak.onclick = function () {
          autoSpeak = !autoSpeak;
          localStorage.setItem('vocab_reels_autospeak', autoSpeak ? '1' : '0');
          updateSpeakBtn();
          if (autoSpeak) {
            App.toast('🔊 Avto ovoz yoqildi');
            if (words[i]) speakWord(words[i].ru, lang);
          } else {
            App.toast('🔇 Avto ovoz o\'chirildi');
            try { window.speechSynthesis.cancel(); } catch (e) {}
          }
        };
      }

      /* Batafsil rejimi: butun sessiya davomida yoqiq qoladi (scroll
         ustiga klass qo'yiladi), ya'ni keyingi so'zga o'tilganda ham
         batafsil ko'rinishda qoladi — foydalanuvchi bir marta yoqib,
         hammasini shu rejimda ko'rib chiqishi mumkin. */
      var detailOn = false;
      var btnInfo = page.querySelector('#vr-btn-info');
      function updateInfoBtn() {
        if (!btnInfo) return;
        btnInfo.classList.toggle('active', detailOn);
        var b = btnInfo.querySelector('b');
        if (b) b.textContent = detailOn ? 'Qisqa' : 'Batafsil';
      }
      if (btnInfo) {
        btnInfo.onclick = function () {
          detailOn = !detailOn;
          scroll.classList.toggle('vr-detail-on', detailOn);
          updateInfoBtn();
        };
      }

      var btnSrs = page.querySelector('#vr-btn-srs');
      if (btnSrs) {
        btnSrs.onclick = function () {
          var w = words[i];
          if (!w) return;
          srsUpdate(lang, cat, w.ru, true);
          App.toast('✅ Yodlandi deb belgilandi');
          if (i < words.length - 1) goTo(i + 1, true);
        };
      }

      var btnEdit = page.querySelector('#vr-btn-edit');
      if (btnEdit) {
        btnEdit.onclick = function () {
          var w = words[i];
          if (!w) return;
          var rawList = V.data[cat] || [];
          var wordIdx = rawList.indexOf(w);
          wordSheet(page, lang, cat, wordIdx, function () {
            buildSlides();
            goTo(i, false);
          });
        };
      }

      var btnDel = page.querySelector('#vr-btn-del');
      if (btnDel) {
        btnDel.onclick = function () {
          var w = words[i];
          if (!w) return;
          App.confirm('"' + w.ru + '" so\'zi o\'chirilsinmi?', function () {
            var rawList = V.data[cat] || [];
            var matchIdx = rawList.indexOf(w);
            if (matchIdx >= 0) rawList.splice(matchIdx, 1);
            saveWords(lang, cat, rawList).then(function () {
              words.splice(i, 1);
              App.toast('🗑 O\'chirildi');
              if (!words.length) {
                App.go('vocab_practice', backParams);
                return;
              }
              if (i >= words.length) i = words.length - 1;
              buildSlides();
              goTo(i, false);
            });
          }, { danger: true, yes: 'O\'chirish' });
        };
      }

      function onKey(e) {
        if (e.key === 'ArrowDown' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); goTo(i + 1, true); }
        else if (e.key === 'ArrowUp' || e.key === 'PageUp') { e.preventDefault(); goTo(i - 1, true); }
      }
      document.addEventListener('keydown', onKey);
    }
  });

})();
