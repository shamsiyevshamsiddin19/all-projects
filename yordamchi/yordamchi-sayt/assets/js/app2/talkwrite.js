/* Говорение (Speaking) va Письмо (Writing) — bitta modul, ikki bo'lim.

   NEGA BITTA FAYL. Ikkala bo'lim ham AYNI tuzilishga ega: papka ->
   material (.md) -> ichida savol/mavzular ro'yxati -> bittasiga bosilsa
   uni QANDAY bajarish tushuntiriladi. Farq faqat yorliqlarda va
   qo'llanma matnida. Ikki nusxa kod yozilsa, formatga har o'zgartirish
   ikki joyda takrorlanishi kerak bo'lardi.

   FORMAT (.md):
     # Sarlavha                 -> materialning nomi (ixtiyoriy)
     ## Savol yoki mavzu        -> ro'yxatdagi bitta element
     :: tarjimasi               -> yuqoridagi qatorning o'zbekcha tarjimasi
     ### Blok nomi              -> element ichidagi bo'lim ("Qanday javob berish")
     - ibora :: tarjima         -> ibora juftligi (bosilsa ovoz chiqadi)
     1. qadam                   -> tartibli ro'yxat
     oddiy qator                -> matn; `::` bilan tarjima qo'shsa bo'ladi

   Ma'lumot `language_topics` da (library.js bilan bir xil jadval).
   Ko'rinishlar: `speaking_doc`, `writing_doc`. */
(function () {
  'use strict';

  var SEC = {
    en_speaking: { kind: 'speak', n: 'Speaking', lang: 'en-US' },
    ru_speaking: { kind: 'speak', n: 'Говорение', lang: 'ru-RU' },
    en_writing:  { kind: 'write', n: 'Writing',  lang: 'en-US' },
    ru_writing:  { kind: 'write', n: 'Письмо', lang: 'ru-RU' }
  };

  /* Yorliqlar — kod bir xil, so'zlar boshqa. */
  var WORD = {
    speak: {
      one: 'Savol', many: 'savol',
      listHint: 'Savolni bosing — ma\'nosi, javob rejasi, iboralar va ulagichlar ochiladi.',
      emptyTitle: 'Savollar hali yo\'q',
      practice: 'Ovoz chiqarib javob bering'
    },
    write: {
      one: 'Mavzu', many: 'mavzu',
      listHint: 'Mavzuni bosing — nima haqida va qanday yozish, reja, iboralar va bog\'lovchilar ochiladi.',
      emptyTitle: 'Mavzular hali yo\'q',
      practice: 'Daftarga yozib mashq qiling'
    }
  };

  function info(sec) { return SEC[sec] || SEC.ru_speaking; }
  function words(sec) { return WORD[info(sec).kind]; }
  function isSec(sec) { return !!SEC[sec]; }

  /* ================= Parser ================= */

  /* Bitta qatordan "matn :: tarjima" juftini ajratadi. */
  function splitTr(text) {
    var i = String(text || '').indexOf('::');
    if (i < 0) return { text: String(text || '').trim(), tr: '' };
    return { text: text.slice(0, i).trim(), tr: text.slice(i + 2).trim() };
  }

  function parse(md) {
    var lines = String(md == null ? '' : md).replace(/\r/g, '').split('\n');
    var doc = { title: '', intro: [], items: [] };
    var item = null, block = null;

    function ensureBlock() {
      if (!block) { block = { label: '', rows: [] }; item.blocks.push(block); }
      return block;
    }

    lines.forEach(function (raw) {
      var line = raw.trim();
      if (!line) return;
      var m;

      if ((m = line.match(/^#\s+(.*)$/))) {
        doc.title = m[1].trim(); item = null; block = null; return;
      }
      if ((m = line.match(/^##\s+(.*)$/))) {
        item = { q: m[1].trim(), tr: '', blocks: [] };
        doc.items.push(item); block = null; return;
      }
      if ((m = line.match(/^###+\s+(.*)$/))) {
        if (!item) return;                       // sarlavhadan oldingi blok — tashlanadi
        block = { label: m[1].trim(), rows: [] };
        item.blocks.push(block); return;
      }

      /* Alohida turgan `::` qatori — YUQORIDAGI narsaning tarjimasi. */
      if (/^::/.test(line)) {
        var tr = line.replace(/^::\s?/, '').trim();
        if (!tr) return;
        if (block && block.rows.length) {
          var last = block.rows[block.rows.length - 1];
          if (!last.tr) { last.tr = tr; return; }
        }
        if (item && !block && !item.tr) { item.tr = tr; return; }
        if (item) { ensureBlock().rows.push({ k: 'p', text: '', tr: tr }); return; }
        if (doc.intro.length && !doc.intro[doc.intro.length - 1].tr) {
          doc.intro[doc.intro.length - 1].tr = tr; return;
        }
        doc.intro.push({ k: 'p', text: '', tr: tr });
        return;
      }

      if ((m = line.match(/^[-*•]\s+(.*)$/))) {
        var li = splitTr(m[1]);
        if (!item) { doc.intro.push({ k: 'li', text: li.text, tr: li.tr }); return; }
        ensureBlock().rows.push({ k: 'li', text: li.text, tr: li.tr });
        return;
      }

      if ((m = line.match(/^(\d+)[.)]\s+(.*)$/))) {
        var nu = splitTr(m[2]);
        if (!item) { doc.intro.push({ k: 'n', n: m[1], text: nu.text, tr: nu.tr }); return; }
        ensureBlock().rows.push({ k: 'n', n: m[1], text: nu.text, tr: nu.tr });
        return;
      }

      var pp = splitTr(line);
      if (!item) { doc.intro.push({ k: 'p', text: pp.text, tr: pp.tr }); return; }
      ensureBlock().rows.push({ k: 'p', text: pp.text, tr: pp.tr });
    });

    return doc;
  }

  /* ================= Ovoz =================
     Serverdagi MP3 (Google TTS) brauzerning o'z ovozidan sezilarli
     yaxshiroq — avval o'sha, u ishlamasa brauzer ovoziga qaytamiz. */
  var sayAudio = null;
  var sayGen = 0;

  function say(text, sec) {
    text = String(text || '').trim();
    if (!text) return;
    var lang = info(sec).lang;
    var code = lang.indexOf('ru') === 0 ? 'ru' : 'en';
    var my = ++sayGen;

    if (!sayAudio) sayAudio = new Audio();
    try { sayAudio.pause(); } catch (e) {}
    if (window.TTS) window.TTS.cancel();

    sayAudio.onerror = function () {
      if (my !== sayGen) return;
      if (window.TTS) window.TTS.speak(text, { lang: lang });
    };
    sayAudio.src = '/api?action=tts_audio&text=' + encodeURIComponent(text) + '&lang=' + code;
    var p = sayAudio.play();
    if (p && p.catch) p.catch(function () {
      if (my !== sayGen) return;
      if (window.TTS) window.TTS.speak(text, { lang: lang });
    });
  }

  function stopSay() {
    sayGen++;
    if (sayAudio) { try { sayAudio.pause(); } catch (e) {} }
    if (window.TTS) window.TTS.cancel();
  }

  App.actions.twSay = function (a) { say(a.t, a.sec); };

  /* ================= Chizish ================= */

  function rowHtml(r, sec) {
    var tr = r.tr ? '<div class="tw-tr">' + App.esc(r.tr) + '</div>' : '';
    if (!r.text) return tr ? '<div class="tw-row">' + tr + '</div>' : '';

    if (r.k === 'li') {
      /* TARJIMASI BOR ro'yxat qatori — chet tilidagi ibora: bosilsa ovoz
         chiqarib o'qiladi (Speaking'da asosiy mashq usuli: eshit -> takrorla).

         Tarjimasi YO'Q qator esa oddiy ro'yxat (masalan "G'oyalar" bo'limi
         o'zbekcha yozilgan). Uni ham ovoz tugmasi qilib qo'ysak, o'zbekcha
         matn rus ovozi bilan o'qib berilardi. */
      if (!r.tr) {
        return '<div class="tw-bullet"><span class="tw-bullet-dot"></span>' +
          '<span class="tw-bullet-txt">' + App.esc(r.text) + '</span></div>';
      }
      return '<button class="tw-phrase" data-act="twSay" data-arg=\'' +
        App.arg({ t: r.text, sec: sec }) + '\'>' +
        '<span class="tw-ph-ic" data-icon="volume" data-icon-size="14"></span>' +
        '<span class="tw-ph-body"><span class="tw-ph-txt">' + App.esc(r.text) + '</span>' + tr + '</span></button>';
    }
    if (r.k === 'n') {
      return '<div class="tw-step"><span class="tw-step-n">' + App.esc(r.n) + '</span>' +
        '<div class="tw-step-body">' + App.esc(r.text) + tr + '</div></div>';
    }
    /* Oddiy qator, lekin TARJIMASI BOR — demak bu chet tilidagi gap
       ("Namuna javob" bo'limi shunday yoziladi: har gap alohida qatorda,
       ostida `:: tarjima`). Bu ham bosilib eshitilishi kerak: namunani
       eshitib takrorlash — gapirishni mashq qilishning asosiy usuli.

       Tarjimasi yo'q qator esa o'zbekcha izoh ("Savol nima so'rayapti") —
       unga ovoz tugmasi qo'yilsa, o'zbekcha matn rus ovozi bilan o'qib
       berilardi. Qoida `li` qatorlari bilan bir xil. */
    if (r.tr) {
      return '<button class="tw-say-line" data-act="twSay" data-arg=\'' +
        App.arg({ t: r.text, sec: sec }) + '\'>' +
        '<span class="tw-sl-body"><span class="tw-sl-txt">' + App.esc(r.text) + '</span>' + tr + '</span>' +
        '<span class="tw-sl-ic" data-icon="volume" data-icon-size="13"></span></button>';
    }
    return '<div class="tw-row"><div class="tw-p">' + App.esc(r.text) + '</div></div>';
  }

  function blockHtml(b, sec) {
    var rows = b.rows.map(function (r) { return rowHtml(r, sec); }).join('');
    if (!rows) return '';
    return '<div class="tw-block">' +
      (b.label ? '<div class="tw-block-label">' + App.esc(b.label) + '</div>' : '') +
      rows + '</div>';
  }

  /* ================= VIEW: ro'yxat + bitta element ================= */

  function makeView(name) {
    App.view(name, {
      nav: 'languages',
      leave: stopSay,
      render: function (page, params) {
        var sec = params.sec || (name === 'writing_doc' ? 'ru_writing' : 'ru_speaking');
        var id = params.id;
        /* `q` — ochilgan savol/mavzu tartib raqami. URL da turadi, shuning
           uchun brauzerning "orqaga" tugmasi ro'yxatga qaytaradi. */
        var q = (params.q === undefined || params.q === '') ? -1 : parseInt(params.q, 10);
        if (isNaN(q)) q = -1;

        /* `window.Auth` — bir xil yozuv. Aralash yozilsa (`window.Auth`
           tekshiruvi + yalang'och `Auth` chaqiruvi) brauzerda ishlaydi,
           chunki `Auth` global; lekin bu tasodif — modul boshqa muhitda
           yuklansa darrov yiqiladi. */
        var isRO = !!(window.Auth && window.Auth.isReadOnly && window.Auth.isReadOnly());
        var menuBtn = (isRO || q >= 0) ? '' :
          '<button class="icon-btn ghost" id="tw-menu" style="margin-left:auto">' +
          '<span data-icon="edit" data-icon-size="18"></span></button>';

        page.innerHTML =
          '<div class="topbar" style="margin:-16px -15px 12px">' +
          '<button class="icon-btn ghost" id="tw-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
          '<h1 id="tw-title"></h1>' + menuBtn + '</div>' +
          '<div id="tw-body"><div class="load-wrap"><div class="spinner"></div></div></div>' +
          '<input type="file" id="tw-file" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">';
        App.icons(page);
        load(page, sec, id, q, name);
      }
    });
  }

  function load(page, sec, id, q, viewName) {
    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(id) }).then(function (t) {
      var box = App.el('tw-body'); if (!box) return;
      var folder = (t.folder || '').trim();
      var W = words(sec);
      var doc = parse(t.content || '');

      var back = page.querySelector('#tw-back');
      if (back) {
        back.setAttribute('data-act', 'go');
        /* Savol ichidan — ro'yxatga, ro'yxatdan — papkaga. */
        back.setAttribute('data-arg', q >= 0
          ? App.arg({ v: viewName, p: { sec: sec, id: id } })
          : App.arg({ v: 'library', p: { sec: sec, path: folder } }));
      }

      var h1 = page.querySelector('#tw-title');
      var item = (q >= 0 && doc.items[q]) ? doc.items[q] : null;
      if (h1) h1.textContent = item ? (W.one + ' ' + (q + 1)) : (doc.title || t.name || W.one);

      if (!t.content) {
        box.innerHTML = App.empty({
          icon: 'file', title: W.emptyTitle,
          text: 'Tepadagi ✏ orqali .md yuklang. Format bilan tanishish uchun namunani, AI ga berish uchun qo\'llanmani oling.'
        }) +
        '<div class="btn-row" style="margin-top:12px">' +
        '<button class="btn sec" data-act="twSample" data-arg=\'' + App.arg({ sec: sec }) + '\'>Namuna</button>' +
        '<button class="btn sec" data-act="twGuide" data-arg=\'' + App.arg({ sec: sec }) + '\'>AI qo\'llanma</button></div>';
        App.icons(box);
        bindMenu(page, sec, id, t, q, viewName);
        return;
      }

      box.innerHTML = item ? itemHtml(item, sec, W) : listHtml(doc, sec, id, viewName, W, t);
      App.icons(box);
      bindMenu(page, sec, id, t, q, viewName);
    }).catch(function (e) {
      var box = App.el('tw-body');
      if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  function listHtml(doc, sec, id, viewName, W, t) {
    if (!doc.items.length) {
      return App.empty({
        icon: 'file', title: W.emptyTitle,
        text: 'Faylda `## ' + W.one + '` ko\'rinishidagi sarlavha topilmadi. Namuna faylni ochib formatni ko\'ring.'
      });
    }

    var intro = doc.intro.map(function (r) { return rowHtml(r, sec); }).join('');

    var rows = doc.items.map(function (it, i) {
      /* Har element ichida nechta blok borligi — foydalanuvchi ochishdan
         oldin qanchalik to'liq ekanini ko'rsin. */
      var n = it.blocks.filter(function (b) { return b.rows.length; }).length;
      return '<button class="tw-item" data-act="go" data-arg=\'' +
        App.arg({ v: viewName, p: { sec: sec, id: id, q: i } }) + '\'>' +
        '<span class="tw-item-n">' + (i + 1) + '</span>' +
        '<span class="tw-item-main">' +
          '<span class="tw-item-q">' + App.esc(it.q) + '</span>' +
          (it.tr ? '<span class="tw-item-tr">' + App.esc(it.tr) + '</span>' : '') +
          (n ? '<span class="tw-item-meta">' + n + ' ta bo\'lim</span>' : '') +
        '</span>' +
        '<span class="tw-item-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>';
    }).join('');

    return (intro ? '<div class="tw-intro">' + intro + '</div>' : '') +
      '<p class="tw-hint">' + App.esc(W.listHint) + '</p>' +
      '<div class="tw-list">' + rows + '</div>';
  }

  function itemHtml(item, sec, W) {
    var blocks = item.blocks.map(function (b) { return blockHtml(b, sec); }).join('');
    return '<div class="tw-q-card">' +
        '<button class="tw-q-say" data-act="twSay" data-arg=\'' + App.arg({ t: item.q, sec: sec }) + '\' ' +
          'aria-label="Ovoz chiqarib o\'qish"><span data-icon="volume" data-icon-size="16"></span></button>' +
        '<div class="tw-q-txt">' + App.esc(item.q) + '</div>' +
        (item.tr ? '<div class="tw-q-tr">' + App.esc(item.tr) + '</div>' : '') +
      '</div>' +
      (blocks || App.empty({
        icon: 'file', title: 'Izoh yozilmagan',
        text: 'Bu ' + W.many + ' uchun faylda `### ...` bloklari yo\'q.'
      })) +
      '<p class="tw-hint" style="margin-top:14px">' + App.esc(W.practice) + '</p>';
  }

  /* ================= Tahrir menyusi ================= */

  function bindMenu(page, sec, id, t, q, viewName) {
    var btn = App.el('tw-menu');
    if (!btn) return;
    btn.onclick = function () {
      var html =
        '<button class="list-row" id="tw-up"><span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? '.md faylni almashtirish' : '.md fayl yuklash') + '</div></div></button>' +
        '<button class="list-row" id="tw-ed"><span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? 'Tahrirlash' : 'Yozish') + '</div></div></button>' +
        '<button class="list-row" data-act="twSample" data-arg=\'' + App.arg({ sec: sec }) + '\'>' +
        '<span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Namuna fayl</div>' +
        '<div class="li-sub">Format qanday yozilishi</div></div></button>' +
        '<button class="list-row" data-act="twGuide" data-arg=\'' + App.arg({ sec: sec }) + '\'>' +
        '<span class="li-ic" data-icon="file" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">AI uchun qo\'llanma</div>' +
        '<div class="li-sub">PDF bilan birga AI ga bering</div></div></button>' +
        (t.content
          ? '<button class="list-row" id="tw-dl"><span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">.md faylni yuklab olish</div></div></button>'
          : '');
      var sh = App.sheet(html, { title: t.name });
      App.icons(sh);
      sh.querySelector('#tw-up').onclick = function () { App.closeSheet(); App.el('tw-file').click(); };
      sh.querySelector('#tw-ed').onclick = function () { App.closeSheet(); edit(page, sec, id, t, q, viewName); };
      var dl = sh.querySelector('#tw-dl');
      if (dl) dl.onclick = function () {
        App.closeSheet();
        App.download(t.name + '.md', t.content || '');
      };
    };

    var f = App.el('tw-file');
    if (f) f.onchange = function (e) {
      var file = e.target.files[0]; if (!file) return;
      var fr = new FileReader();
      fr.onload = function () {
        App.call('upload_topic_content', { id: id, part: 'content', content: String(fr.result || '') })
          .then(function () { App.toast('✅ Yuklandi'); load(page, sec, id, q, viewName); })
          .catch(function (err) { App.toast('⚠️ ' + err.message); });
      };
      fr.onerror = function () { App.toast('Fayl o\'qilmadi'); };
      fr.readAsText(file);
    };
  }

  function edit(page, sec, id, t, q, viewName) {
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">' +
      '<code>## ' + words(sec).one + '</code>, <code>:: tarjima</code>, <code>### Blok</code>, <code>- ibora :: tarjima</code></p>' +
      '<label class="field"><span>Matn</span><textarea class="textarea" id="tw-text" spellcheck="false">' +
      App.esc(t.content || '') + '</textarea></label>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="tw-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: t.name, cls: 'editor-sheet' });
    sh.querySelector('#tw-save').onclick = function () {
      App.call('upload_topic_content', { id: id, part: 'content', content: sh.querySelector('#tw-text').value })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); load(page, sec, id, q, viewName); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  makeView('speaking_doc');
  makeView('writing_doc');

  window.TalkWrite = { isSec: isSec, parse: parse, SECTIONS: SEC };
})();

/* ================================================================
   Namuna fayllar va AI uchun qo'llanmalar.

   Foydalanuvchi qo'llanmani yuklab oladi va PDF bilan birga sun'iy
   intellektga beradi; AI shu qoidalar bo'yicha .md tayyorlaydi; .md
   saytga yuklanadi va yuqoridagi ko'rinishlarda ochiladi. Shuning uchun
   qo'llanma ILOVA FAYLNI QANDAY O'QISHINI ham tushuntiradi — AI sababini
   bilsa, format buzilishi kamayadi.
   ================================================================ */
(function () {
  'use strict';

  var SAMPLE_SPEAK = [
    "# Семья и дом",
    "",
    "## Расскажите о своей семье.",
    ":: Oilangiz haqida gapirib bering.",
    "",
    "### Savol nima so'rayapti",
    "Bu savol oila a'zolari, ularning yoshi, kasbi va o'zaro munosabatlar haqida qisqa hikoya kutadi.",
    "Bir-ikki gap emas, 5-7 gapdan iborat bog'langan matn kerak.",
    "",
    "### Javob rejasi",
    "1. Oilangiz katta yoki kichikligini ayting.",
    "2. Har bir a'zoni bir gap bilan tanishtiring: kim, nechchi yoshda, nima qiladi.",
    "3. Bitta qiziq tafsilot qo'shing (birga nima qilasizlar).",
    "4. His-tuyg'u bilan yakunlang.",
    "",
    "### Kerakli iboralar",
    "- У меня большая семья. :: Mening oilam katta.",
    "- Нас пятеро: мама, папа, брат, сестра и я. :: Biz beshtamiz: onam, otam, akam, singlim va men.",
    "- Мой отец работает врачом. :: Otam shifokor bo'lib ishlaydi.",
    "- Мы очень дружные. :: Biz juda ahilmiz.",
    "",
    "### Ulagichlar",
    "- Во-первых... :: Birinchidan...",
    "- Кроме того... :: Bundan tashqari...",
    "- Что касается моего брата... :: Akamga kelsak...",
    "- В общем... :: Umuman olganda...",
    "",
    "### Namuna javob",
    "У меня большая и дружная семья.",
    ":: Mening oilam katta va ahil.",
    "Нас пятеро: мама, папа, старший брат, младшая сестра и я.",
    ":: Biz beshtamiz: onam, otam, katta akam, kichik singlim va men.",
    "Мой отец работает врачом, а мама — учительницей.",
    ":: Otam shifokor, onam esa o'qituvchi bo'lib ishlaydi.",
    "По выходным мы вместе ужинаем и смотрим фильмы.",
    ":: Dam olish kunlari biz birga kechki ovqat qilamiz va kino ko'ramiz.",
    "",
    "## Где вы живёте?",
    ":: Siz qayerda yashaysiz?",
    "",
    "### Savol nima so'rayapti",
    "Shahar yoki qishloq, uy yoki kvartira, qanchadan beri yashayotganingiz va joy sizga yoqadimi.",
    "",
    "### Javob rejasi",
    "1. Shaharni ayting.",
    "2. Uy turini va xonalar sonini ayting.",
    "3. Atrofda nima borligini ayting.",
    "4. Yoqadimi yoki yo'qmi — sababi bilan.",
    "",
    "### Kerakli iboralar",
    "- Я живу в Ташкенте. :: Men Toshkentda yashayman.",
    "- Мы живём в квартире на пятом этаже. :: Biz beshinchi qavatdagi kvartirada yashaymiz.",
    "- Рядом с домом есть парк. :: Uy yonida park bor.",
    "",
    "### Ulagichlar",
    "- Дело в том, что... :: Gap shundaki...",
    "- Например... :: Masalan...",
    "- Поэтому... :: Shuning uchun...",
    "",
    "### Namuna javob",
    "Я живу в Ташкенте, в новом районе.",
    ":: Men Toshkentda, yangi tumanda yashayman.",
    "Мы живём в квартире на пятом этаже: там три комнаты.",
    ":: Biz beshinchi qavatdagi kvartirada yashaymiz: u yerda uchta xona bor.",
    "Мне здесь нравится, потому что рядом есть парк и магазины.",
    ":: Menga bu yer yoqadi, chunki yonida park va do'konlar bor."
  ].join('\n');

  var SAMPLE_WRITE = [
    "# Личные темы",
    "",
    "## Моя мечта",
    ":: Mening orzuyim",
    "",
    "### Mavzu nima haqida",
    "Bu mavzuda bitta ANIQ orzu tanlanadi va u haqida yoziladi: nima, nega, qachon va u ro'yobga chiqsa hayotingiz qanday o'zgaradi.",
    "Umumiy gaplar (men baxtli bo'lishni xohlayman) matnni bo'sh qiladi — aniq tafsilot kerak.",
    "",
    "### G'oyalar",
    "- Kasb bilan bog'liq orzu: shifokor, dasturchi, uchuvchi bo'lish.",
    "- Sayohat orzusi: qaysi shahar va nega aynan u.",
    "- Oila bilan bog'liq orzu.",
    "- Boshqalarga foyda keltiradigan orzu: maktab qurish, kitob yozish.",
    "",
    "### Reja",
    "1. Kirish: orzuyingiz borligini ayting va nomlang.",
    "2. Nega aynan shu orzu — sabab yoki voqea.",
    "3. Uni ro'yobga chiqarish uchun nima qilyapsiz.",
    "4. Yakun: orzu amalga oshsa nima o'zgaradi.",
    "",
    "### Kerakli iboralar",
    "- С детства я мечтаю... :: Bolalikdan orzu qilaman...",
    "- Моя главная мечта — это... :: Mening asosiy orzuyim — bu...",
    "- Для этого я каждый день... :: Buning uchun men har kuni...",
    "- Я уверен, что однажды... :: Ishonchim komilki, bir kun...",
    "",
    "### Bog'lovchilar",
    "- Во-первых / во-вторых :: Birinchidan / ikkinchidan",
    "- Кроме того :: Bundan tashqari",
    "- Именно поэтому :: Aynan shuning uchun",
    "- В заключение :: Xulosa qilib",
    "",
    "### Namuna matn",
    "С детства я мечтаю стать врачом.",
    ":: Bolalikdan shifokor bo'lishni orzu qilaman.",
    "Когда мне было десять лет, моя бабушка тяжело заболела.",
    ":: Men o'n yoshda edim, buvim og'ir kasal bo'lib qoldi.",
    "Именно поэтому я решил помогать людям.",
    ":: Aynan shuning uchun men odamlarga yordam berishga qaror qildim.",
    "Сейчас я каждый день учу биологию и химию.",
    ":: Hozir men har kuni biologiya va kimyo o'qiyman.",
    "",
    "## Первая любовь",
    ":: Birinchi muhabbat",
    "",
    "### Mavzu nima haqida",
    "Bu mavzu his-tuyg'u haqida: qachon bo'lgan, qanday his qilgansiz, nima o'rgangansiz.",
    "Voqeani boshidan oxirigacha aytib bering — ro'yxat emas, hikoya bo'lsin.",
    "",
    "### G'oyalar",
    "- Birinchi uchrashuv va o'sha kungi kayfiyat.",
    "- Nimasi bilan esda qolgan.",
    "- Nima o'zgargan va nima o'rgangan.",
    "",
    "### Reja",
    "1. Qachon va qayerda bo'lganini ayting.",
    "2. O'sha paytdagi hislaringizni tasvirlang.",
    "3. Bitta esda qolarli voqeani aytib bering.",
    "4. Bugun bu haqda nima deb o'ylaysiz.",
    "",
    "### Kerakli iboralar",
    "- Это было, когда мне было... :: Bu men ... yoshda bo'lganimda edi.",
    "- Я до сих пор помню... :: Men hali ham eslayman...",
    "- Тогда я понял, что... :: O'shanda men tushundimki...",
    "",
    "### Bog'lovchilar",
    "- Сначала :: Avvaliga",
    "- Потом :: Keyin",
    "- Однажды :: Bir kuni",
    "- В итоге :: Oxir-oqibat",
    "",
    "### Namuna matn",
    "Это было, когда мне было шестнадцать лет.",
    ":: Bu men o'n olti yoshda bo'lganimda edi.",
    "Сначала мы просто учились в одном классе.",
    ":: Avvaliga biz shunchaki bir sinfda o'qir edik.",
    "Однажды она помогла мне с домашним заданием, и мы разговорились.",
    ":: Bir kuni u menga uy vazifasida yordam berdi va biz gaplashib qoldik.",
    "В итоге я понял, что дружба важнее слов.",
    ":: Oxir-oqibat men do'stlik so'zdan muhimroq ekanini tushundim."
  ].join('\n');

  /* ---------- Qo'llanma matni ----------
     Ikkala bo'lim uchun tuzilishi bir xil; farqi bloklar ro'yxatida va
     misollarda. Shuning uchun bitta yasovchi funksiya. */
  function guide(kind) {
    var speak = kind === 'speak';
    var sekName = speak ? "Говорение (Speaking)" : "Письмо (Writing)";
    var unit = speak ? "savol" : "mavzu";
    var Unit = speak ? "Savol" : "Mavzu";

    var blocks = speak
      ? [
          ["### Savol nima so'rayapti", "Savolning ma'nosi: undan aynan nima kutilyapti, javob qancha uzun bo'lishi kerak."],
          ["### Javob rejasi", "Tartibli ro'yxat (1. 2. 3.) — javobni qanday qurish."],
          ["### Kerakli iboralar", "Tayyor iboralar, har biri `- ibora :: tarjima` ko'rinishida."],
          ["### Ulagichlar", "Gapirayotganda TO'XTAB QOLMASLIK uchun ulovchi so'zlar: во-первых, кроме того, что касается..."],
          ["### Namuna javob", "To'liq javob namunasi; har gapdan keyin `:: tarjima`."],
          ["### Tez-tez qilinadigan xato", "IXTIYORIY. Nimadan ehtiyot bo'lish kerak."]
        ]
      : [
          ["### Mavzu nima haqida", "Mavzuning ma'nosi: nima haqida yozish kerak, qaysi tomonini ochish kerak."],
          ["### G'oyalar", "Nima haqida yozish mumkinligi — bir nechta variant, `- g'oya` ro'yxati."],
          ["### Reja", "Tartibli ro'yxat (1. 2. 3.) — matnni qanday qurish: kirish, asosiy qism, yakun."],
          ["### Kerakli iboralar", "Tayyor iboralar, har biri `- ibora :: tarjima` ko'rinishida."],
          ["### Bog'lovchilar", "Matnni DAVOM ETTIRISH uchun bog'lovchilar: во-первых, кроме того, в заключение..."],
          ["### Namuna matn", "To'liq namuna matn; har gapdan keyin `:: tarjima`."],
          ["### Tez-tez qilinadigan xato", "IXTIYORIY. Nimadan ehtiyot bo'lish kerak."]
        ];

    var out = [];
    out.push("# Yordamchi — " + sekName + " bo'limi uchun material tayyorlash qo'llanmasi");
    out.push("");
    out.push("Bu faylni sun'iy intellektga (ChatGPT, Claude va h.k.) PDF bilan BIRGA bering va");
    out.push("«shu qoidalar bo'yicha .md tayyorla» deng. Quyida formatning to'liq tavsifi");
    out.push("va tayyor so'rov (prompt) bor.");
    out.push("");
    out.push("---");
    out.push("");
    out.push("## 1. Ilova bu faylni QANDAY o'qiydi");
    out.push("");
    out.push("- `## ...` bilan boshlangan har qator — ro'yxatdagi BITTA " + unit + ".");
    out.push("- Foydalanuvchi " + unit + "ni bosadi va ALOHIDA sahifa ochiladi.");
    out.push("- O'sha sahifada `### ...` bloklari ketma-ket ko'rsatiladi.");
    out.push("- `- ibora :: tarjima` qatorlari BOSILADIGAN bo'ladi: bosilsa ovoz chiqarib o'qiladi.");
    out.push("- `:: ` bilan boshlangan qator — undan OLDINGI qatorning o'zbekcha tarjimasi.");
    out.push("");
    out.push("Ya'ni fayl qanchalik to'liq bo'lsa, bo'lim shunchalik foydali bo'ladi.");
    out.push("Ilova hech qanday tarjimonga ULANMAYDI — barcha tarjima faylning ichida bo'lishi shart.");
    out.push("");
    out.push("## 2. Format — beshta belgi");
    out.push("");
    out.push("| Belgi | Ma'nosi |");
    out.push("|---|---|");
    out.push("| `# Sarlavha` | Butun faylning nomi (bir marta, boshida) |");
    out.push("| `## " + Unit + "` | Bitta " + unit + " (ro'yxatda bitta qator) |");
    out.push("| `### Blok nomi` | " + Unit + " ichidagi bo'lim |");
    out.push("| `- matn :: tarjima` | Ibora juftligi (bosilsa o'qiladi) |");
    out.push("| `:: tarjima` | Yuqoridagi qatorning tarjimasi |");
    out.push("");
    out.push("Tartibli ro'yxat uchun `1.` `2.` `3.` ishlatiladi.");
    out.push("");
    out.push("## 3. Har " + unit + " uchun QAYSI bloklar kerak");
    out.push("");
    blocks.forEach(function (b) {
      out.push("**`" + b[0] + "`** — " + b[1]);
      out.push("");
    });
    out.push("Blok nomlarini AYNAN shu holicha yozing — foydalanuvchi hamma");
    out.push(unit + "da bir xil tartibni ko'rsa, o'rganish osonlashadi.");
    out.push("");
    out.push("## 4. Nimalarga e'tibor berish kerak");
    out.push("");
    out.push("1. **Har " + unit + "ga TARJIMA yozing** (`## ...` dan keyingi `:: ...` qatori).");
    out.push("2. **Iboralar qisqa bo'lsin** — bitta gap. Uzun ibora yodlanmaydi.");
    out.push("3. **Har iborada `::` bo'lsin.** Tarjimasiz ibora foydasiz.");
    out.push("4. **Ulagichlar/bog'lovchilar bo'limini tashlab ketmang** — foydalanuvchi aynan");
    out.push("   shu yerda to'xtab qoladi. Kamida 4 tadan yozing.");
    out.push("5. **Namunani to'liq yozing**, 5-8 gap. Har gapdan keyin `:: tarjima`.");
    out.push("6. **Markdown belgilarini ishlatmang**: `**qalin**`, jadval, havola kerak emas.");
    out.push("   Ilova ularni oddiy matn deb o'qiydi va ekranda `**` ko'rinib qoladi.");
    out.push("7. **Bo'sh qator** bloklarni ajratadi — ular ixtiyoriy, lekin faylni o'qishni osonlashtiradi.");
    out.push("");
    out.push("## 5. To'liq namuna");
    out.push("");
    out.push("```markdown");
    /* Namunadan BIRINCHI element to'liq olinadi (ikkinchi `## ` gacha) —
       o'rtasidan kesilgan misol AI ni chalg'itadi. */
    var sample = (speak ? SAMPLE_SPEAK : SAMPLE_WRITE).split('\n');
    var second = -1;
    for (var i = 0; i < sample.length; i++) {
      if (/^##\s/.test(sample[i])) {
        if (second === -1) second = 0;          // birinchisi topildi
        else { second = i; break; }
      }
    }
    (second > 0 ? sample.slice(0, second) : sample).forEach(function (l) { out.push(l.replace(/\s+$/, '')); });
    out.push("```");
    out.push("");
    out.push("(To'liq namunani ilovadagi «Namuna fayl» tugmasi orqali olishingiz mumkin.)");
    out.push("");
    out.push("## 6. AI ga beriladigan tayyor so'rov");
    out.push("");
    out.push("Quyidagini nusxalang va PDF faylni birga biriktiring:");
    out.push("");
    out.push("```");
    out.push("Senga PDF fayl beryapman. Undagi " + (speak ? "savollarni" : "mavzularni") + " olib, quyidagi qoidalar");
    out.push("bo'yicha bitta .md fayl tayyorla.");
    out.push("");
    out.push("TUZILISHI:");
    out.push("# <umumiy sarlavha>");
    out.push("");
    blocks.forEach(function (b, i) {
      if (i === 0) {
        out.push("## <PDF dagi " + unit + " matni, asl tilida>");
        out.push(":: <o'zbekcha tarjimasi>");
        out.push("");
      }
      out.push(b[0]);
      out.push("<" + b[1].replace(/`/g, '') + ">");
      out.push("");
    });
    out.push("QOIDALAR:");
    out.push("- PDF dagi HAR " + unit + " uchun shu bloklarning HAMMASINI yoz");
    out.push("  («Tez-tez qilinadigan xato» ixtiyoriy).");
    out.push("- `## ` va `### ` sarlavhalarini AYNAN yuqoridagidek nomla.");
    out.push("- Har iborani `- ibora :: o'zbekcha tarjima` ko'rinishida yoz.");
    out.push("- " + (speak ? "«Ulagichlar»" : "«Bog'lovchilar»") + " bo'limida kamida 4 ta ifoda bo'lsin.");
    out.push("- Namunada kamida 5 ta gap bo'lsin, har biridan keyin `:: tarjima`.");
    out.push("- Tarjimalar O'ZBEK tilida, tabiiy va qisqa bo'lsin.");
    out.push("- `**`, jadval, havola va boshqa markdown belgilarini ishlatma.");
    out.push("- Javobni faqat .md matn sifatida ber, izohsiz.");
    out.push("");
    out.push("PDF: <shu yerga faylni biriktiring>");
    out.push("```");
    out.push("");
    out.push("## 7. Tayyor bo'lgach");
    out.push("");
    out.push(sekName + " bo'limida `+` tugmasi orqali papka oching (masalan mavzu nomi bilan),");
    out.push("so'ng `.md fayllarni yuklash` bilan faylni joylang. Fayl ustiga bosilganda");
    out.push(unit + "lar ro'yxati chiqadi.");
    out.push("");
    return out.join('\n');
  }

  function kindOf(sec) {
    var s = window.TalkWrite && window.TalkWrite.SECTIONS[sec];
    return (s && s.kind) || 'speak';
  }

  App.actions.twSample = function (a) {
    App.closeSheet();
    var speak = kindOf(a && a.sec) === 'speak';
    App.download(speak ? 'namuna-govorenie.md' : 'namuna-pismo.md', speak ? SAMPLE_SPEAK : SAMPLE_WRITE);
    App.toast('Namuna yuklandi — shu formatda yoziladi');
  };

  App.actions.twGuide = function (a) {
    App.closeSheet();
    var speak = kindOf(a && a.sec) === 'speak';
    App.download(
      speak ? 'yordamchi-govorenie-qollanma.md' : 'yordamchi-pismo-qollanma.md',
      guide(speak ? 'speak' : 'write')
    );
    App.toast("Qo'llanma yuklandi — uni PDF bilan birga AI ga bering");
  };

  window.TalkWriteDocs = { guide: guide, SAMPLE_SPEAK: SAMPLE_SPEAK, SAMPLE_WRITE: SAMPLE_WRITE };
})();
