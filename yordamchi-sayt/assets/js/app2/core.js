/* ============================================================
   Yordamchi — yangi SPA yadrosi (router + api + ui helpers)
   ============================================================ */
(function () {
  'use strict';

  var views = {};        // name -> { title, icon, render(page, params) }
  var current = null;
  var pageEl = null;

  var App = {
    api: '/api',
    state: {},

    view: function (name, def) { views[name] = def; return App; },

    /* Ko'rinishga o'tish. params ixtiyoriy — oddiy (string/raqam) qiymatlar avtomatik
       URL query-ga yoziladi (chuqur link + sahifa yangilash uchun). */
    go: function (name, params, opts) {
      opts = opts || {};
      if (!views[name]) name = 'home';
      var v = views[name];

      /* Eski ko'rinishni TOZALAB ketamiz. Bu shart: ba'zi bo'limlar
         (Listening mashqi, Lug'at, Reading) TTS ovozi va setTimeout
         zanjirlarini ishga tushiradi — bo'limdan chiqilganda ular o'zidan
         o'zi to'xtamaydi va ovoz boshqa sahifada ham gapiraverardi. */
      App._stopSpeech();
      if (current && views[current] && typeof views[current].leave === 'function') {
        try { views[current].leave(); } catch (e) { console.error('View leave error', current, e); }
      }

      current = name;
      params = params || {};
      App.state._lastParams = params;
      var qs = App._serializeParams(params);
      var hash = '#/' + name + (qs ? '?' + qs : '');
      if (!opts.silent && location.hash !== hash) {
        history.pushState({ view: name, params: params }, '', hash);
      }
      App._renderChrome(name, v);
      pageEl.scrollTop = 0;
      window.scrollTo(0, 0);
      pageEl.innerHTML = '';
      try {
        v.render(pageEl, params || {});
      } catch (e) {
        console.error('View render error', name, e);
        pageEl.innerHTML = '<div class="empty"><b>Xatolik</b><span>' + App.esc(e.message) + '</span></div>';
      }
      App.icons(pageEl);
      App.applyAppIcon();
    },

    _serializeParams: function (params) {
      var parts = [];
      Object.keys(params).forEach(function (k) {
        var v = params[k];
        if (v === null || v === undefined || typeof v === 'object') return;
        parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
      });
      return parts.join('&');
    },

    _renderChrome: function (name, v) {
      document.querySelectorAll('[data-nav]').forEach(function (a) {
        a.classList.toggle('active', a.getAttribute('data-nav') === (v.nav || name));
      });
    },

    reload: function () { App.go(current, App.state._lastParams || {}, { silent: true }); },

    /* Joriy ko'rinish nomi (navigatsiya jestlari qaysi bo'limda turganini
       bilishi uchun). `current` modul ichida yopiq. */
    currentView: function () { return current; },

    /* Barcha TTS ovozini darhol to'xtatadi. Ko'rinish almashganda avtomatik
       chaqiriladi; modullar o'zi ham chaqirishi mumkin. */
    _stopSpeech: function () {
      try { if (window.speechSynthesis) window.speechSynthesis.cancel(); } catch (e) {}
    },

    /* ---- API ---- */
    call: function (action, payload, opts) {
      opts = opts || {};
      var url = App.api + '?action=' + encodeURIComponent(action) + (opts.query ? '&' + opts.query : '');
      var init = { method: opts.method || (payload ? 'POST' : 'GET'), cache: 'no-store' };
      if (payload !== undefined && payload !== null) {
        init.body = JSON.stringify(payload);
        init.headers = { 'Content-Type': 'application/json' };
      }
      return fetch(url, init).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok || (j && j.success === false)) {
            // SW oflayn bo'lganda 503 qaytaradi
            if (r.status === 503) throw new Error('OFFLINE_503');
            throw new Error((j && (j.error || j.message)) || ('HTTP ' + r.status));
          }
          /* Yozuv o'tdi — service worker'dagi o'qish keshi endi eskirdi. */
          App._invalidateData(action);
          return j;
        });
      }).catch(function(e) {
        var offline = e.message === 'OFFLINE_503' ||
                      e.message.indexOf('Failed to fetch') >= 0 || !navigator.onLine;
        /* O'QISH amallari navbatga QO'YILMAYDI. Ilgari shart faqat
           `method === 'POST'` edi; Boostday o'qishlari esa doim POST
           bilan ketardi (boost.js har safar `{}` payload yuboradi), shu
           sabab offline'da ular "keyin yuboriladi" navbatiga tushib,
           chaqiruvchiga ma'lumot o'rniga soxta `{success:true}` qaytardi —
           natijada bosh sahifadagi kunlik statistika jimgina bo'sh
           ko'rinardi. Endi o'qish xatosi chaqiruvchiga yetib boradi. */
        var isRead = (window.READ_ACTIONS || []).indexOf(action) >= 0;
        if (init.method === 'POST' && offline && !isRead) {
          App._enqueueOffline(action, payload, opts);
          App.toast('Oflayn: ma\'lumot saqlandi, keyin yuboriladi');
          return { success: true, offlineSaved: true };
        }
        throw e;
      });
    },

    /* ---- Kesh muvofiqligi (service worker bilan) ----
       SW o'qish javoblarini "avval kesh, keyin yangilash" tartibida beradi
       — bo'limlar shu sabab kutmasdan ochiladi. Ammo biror narsa YOZILGANDAN
       keyin eski kesh noto'g'ri bo'lib qoladi (masalan yangi mavzu ro'yxatda
       ko'rinmasdi), shuning uchun yozuvdan so'ng SW ga "keshni bo'shat"
       deymiz va keyingi o'qish tarmoqdan keladi. */
    _invalidateData: function (action) {
      try {
        if ((window.READ_ACTIONS || []).indexOf(action) >= 0) return;   // o'qish — tegmaymiz
        var sw = navigator.serviceWorker && navigator.serviceWorker.controller;
        if (sw) sw.postMessage({ type: 'invalidate-data' });
      } catch (e) {}
    },

    /* SW orqa fonda yangi ma'lumot topsa shu chaqiriladi. Sahifani
       shovqinsiz qayta chizamiz — lekin faqat foydalanuvchi ish ustida
       bo'lmaganda: ochiq oyna (sheet) yoki matn kiritish jarayonini
       uzib yuborish yaramaydi. */
    _onDataUpdated: function () {
      /* Boshqa qurilmadan yangi ma'lumot keldi. `WordState` ro'yxatlarni
         XOTIRADA keshlaydi, `App.reload()` esa faqat ko'rinishni qayta
         chizadi — modul keshiga tegmaydi. Shuning uchun keshni ATAYLAB
         bekor qilamiz, aks holda telefonda belgilangan so'z kompyuterda
         eski holatda ko'rinaverardi. */
      if (window.WordState && WordState.refresh) WordState.refresh();
      if (App._sheet) return;
      var a = document.activeElement;
      if (a && /^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName)) return;
      clearTimeout(App._duT);
      App._duT = setTimeout(function () {
        try { App.reload(); } catch (e) {}
      }, 60);
    },

    _enqueueOffline: function(action, payload, opts) {
      try {
        var q = JSON.parse(localStorage.getItem('app_offline_q') || '[]');
        q.push({ action: action, payload: payload, opts: opts, ts: Date.now() });
        localStorage.setItem('app_offline_q', JSON.stringify(q));
      } catch(e) {}
    },

    syncOffline: function() {
      try {
        var q = JSON.parse(localStorage.getItem('app_offline_q') || '[]');
        if (!q.length) return;
        var q2 = [];
        var p = Promise.resolve();
        q.forEach(function(item) {
          p = p.then(function() {
            return fetch(App.api + '?action=' + encodeURIComponent(item.action) + (item.opts && item.opts.query ? '&' + item.opts.query : ''), {
              method: 'POST', cache: 'no-store',
              body: item.payload ? JSON.stringify(item.payload) : undefined,
              headers: item.payload ? { 'Content-Type': 'application/json' } : undefined
            }).then(function(r) { if (!r.ok) throw new Error('fail'); }).catch(function() { q2.push(item); });
          });
        });
        p.then(function() {
          localStorage.setItem('app_offline_q', JSON.stringify(q2));
          if (q.length > q2.length) App.toast((q.length - q2.length) + ' ta oflayn o\'zgarish serverga yuborildi!');
        });
      } catch(e) {}
    },

    /* multipart/form-data so'rov (fayl yuklash uchun) — ba'zi action'lar (masalan sport_save_exercise) buni maxsus qabul qiladi */
    callForm: function (action, formData) {
      var url = App.api + '?action=' + encodeURIComponent(action);
      return fetch(url, { method: 'POST', body: formData, cache: 'no-store' }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok || (j && j.success === false)) {
            throw new Error((j && (j.error || j.message)) || ('HTTP ' + r.status));
          }
          return j;
        });
      });
    },

    /* ---- UI: toast ---- */
    toast: function (msg, kind) {
      var t = document.getElementById('toast');
      if (!t) { t = document.createElement('div'); t.id = 'toast'; document.body.appendChild(t); }
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(App._tT);
      App._tT = setTimeout(function () { t.classList.remove('show'); }, 2600);
    },

    /* ---- UI: bottom sheet ----
       open(html, {title}) -> qaytaradi content elementi */
    sheet: function (html, opts) {
      opts = opts || {};
      App.closeSheet();
      var back = document.createElement('div'); back.className = 'sheet-back';
      var sh = document.createElement('div'); sh.className = 'sheet' + (opts.cls ? ' ' + opts.cls : '');
      sh.innerHTML = '<div class="sheet-grip"></div>' + (opts.title ? '<h3>' + App.esc(opts.title) + '</h3>' : '') + html;
      document.body.appendChild(back); document.body.appendChild(sh);
      App.icons(sh);
      back.onclick = App.closeSheet;
      void sh.offsetHeight; // majburiy reflow — keyingi class qo'shilishi CSS transition bilan animatsiya qilinishi uchun
      back.classList.add('show'); sh.classList.add('show');
      App._sheet = { back: back, sh: sh };
      return sh;
    },
    closeSheet: function () {
      if (!App._sheet) return;
      var s = App._sheet; App._sheet = null;
      s.sh.classList.remove('show'); s.back.classList.remove('show');
      /* Yopilayotgan oyna DOM'da yana ~280ms turadi (animatsiya uchun).
         Shu orada YANGI oyna ochilsa, hujjatda bir xil `id` li IKKI element
         bo'lib qoladi va `App.el(id)` O'LAYOTGANINI qaytaradi — natijada
         yangi oynaga chizilgan kontent ko'rinmay qolardi (amalda uchradi).
         Shuning uchun id'lar DARHOL olib tashlanadi: eski oyna endi
         `App.el` uchun umuman mavjud emas. */
      try {
        if (s.sh.id) s.sh.removeAttribute('id');
        s.sh.querySelectorAll('[id]').forEach(function (el) { el.removeAttribute('id'); });
      } catch (e) {}
      setTimeout(function () { s.sh.remove(); s.back.remove(); }, 280);
    },

    /* ---- UI: confirm ---- */
    confirm: function (msg, onYes, opts) {
      opts = opts || {};
      var html = '<p class="muted" style="margin:0 0 18px">' + App.esc(msg) + '</p>' +
        '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
        '<button class="btn ' + (opts.danger ? 'danger' : '') + '" id="cfm-yes">' + App.esc(opts.yes || 'Ha') + '</button></div>';
      var sh = App.sheet(html, { title: opts.title || 'Tasdiqlang' });
      sh.querySelector('#cfm-yes').onclick = function () { App.closeSheet(); onYes && onYes(); };
    },

    /* ---- UI: prompt (bitta matn kiritish) ---- */
    prompt: function (opts, onOk) {
      opts = opts || {};
      var html = '<label class="field"><span>' + App.esc(opts.label || '') + '</span>' +
        (opts.multiline
          ? '<textarea class="textarea" id="pr-in" rows="4"></textarea>'
          : '<input class="input" id="pr-in" />') + '</label>' +
        '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
        '<button class="btn" id="pr-ok">' + App.esc(opts.ok || 'Saqlash') + '</button></div>';
      var sh = App.sheet(html, { title: opts.title || '' });
      var inp = sh.querySelector('#pr-in');
      if (opts.value) inp.value = opts.value;
      setTimeout(function () { inp.focus(); }, 350);
      var submit = function () {
        var v = inp.value.trim();
        if (!v && !opts.allowEmpty) { App.toast('Bo\'sh bo\'lmasin'); return; }
        App.closeSheet(); onOk && onOk(v);
      };
      sh.querySelector('#pr-ok').onclick = submit;
      if (!opts.multiline) inp.onkeydown = function (e) { if (e.key === 'Enter') submit(); };
    },

    /* ---- helpers ---- */
    esc: function (v) { var d = document.createElement('div'); d.textContent = v == null ? '' : String(v); return d.innerHTML; },
    /* --- Ilova belgisi (icon) — bitta manba, hamma joyda bir xil ---
       `data-app-icon` atributi qo'yilgan har qanday <img>/<link> avtomatik yangilanadi:
       splash, sidebar, favicon, apple-touch-icon, kirish ekrani, sozlamalar. */
    appIconSrc: function () {
      try {
        var ic = localStorage.getItem('app_custom_icon_192') ||
                 localStorage.getItem('app_custom_icon');
        if (ic) return ic;
        /* Saqlangan belgi yo'q (yangi qurilma) — serverdagi PNG'ga tushamiz.
           `?v=` SHART: `save_app_icon` faylning USTIGA yozadi, manzil esa
           o'zgarmaydi — versiyasiz brauzer eski keshlangan rasmni qaytaradi. */
        var v = localStorage.getItem('app_icon_version') || '';
        return 'assets/icons/custom-app-icon-192.png' + (v ? '?v=' + v : '');
      } catch (e) { return 'assets/icons/custom-app-icon-192.png'; }
    },
    applyAppIcon: function () {
      var src = App.appIconSrc();
      document.querySelectorAll('[data-app-icon]').forEach(function (el) {
        if (el.tagName === 'LINK') el.setAttribute('href', src);
        else el.src = src;
      });
    },



    /* Mavzuni qo'llaydi (data-theme) va brauzer manzil paneli rangini ham
       moslaydi. MUHIM: yangi qurilmada localStorage dastlab bo'sh bo'ladi —
       tanlangan mavzu serverdan sinxronlangandan KEYIN keladi, shuning uchun
       bootstrap uni sinxron tugagach qaytadan chaqiradi (ilgari faqat ikona
       va shrift qayta qo'llanardi, mavzu esa standart holicha qolib ketardi). */

    /* Avatar bo'lmasa — ism harflaridan yasalgan rasm. Fon rangi QATTIQ
       yozilmaydi: joriy mavzuning aksent rangidan olinadi (qorong'uda
       to'q sariq, yorug'da ko'k), aks holda mavzu o'zgarganda avatar
       yolg'iz ko'k bo'lib ajralib qolardi. */
    avatarUrl: function (name) {
      var bg = '3b91f0', ink = 'ffffff';
      try {
        var cs = getComputedStyle(document.documentElement);
        var a = cs.getPropertyValue('--accent').trim().replace('#', '');
        var i = cs.getPropertyValue('--accent-ink').trim().replace('#', '');
        if (/^[0-9a-fA-F]{6}$/.test(a)) bg = a;
        if (/^[0-9a-fA-F]{6}$/.test(i)) ink = i;
      } catch (e) {}
      return 'https://ui-avatars.com/api/?name=' + encodeURIComponent(name || 'Y') +
             '&background=' + bg + '&color=' + ink + '&size=180';
    },

    applyTheme: function () {
      var t = 'auto';
      try { t = localStorage.getItem('app_theme') || 'auto'; } catch (e) {}
      var root = document.documentElement;
      if (t === 'dark' || t === 'light') root.setAttribute('data-theme', t);
      else root.removeAttribute('data-theme');

      // Mobil brauzer paneli rangi joriy fon bilan bir xil bo'lsin
      try {
        var bg = getComputedStyle(root).getPropertyValue('--bg').trim();
        var m = document.querySelector('meta[name="theme-color"]');
        if (!m) {
          m = document.createElement('meta');
          m.setAttribute('name', 'theme-color');
          document.head.appendChild(m);
        }
        if (bg) m.setAttribute('content', bg);
        
        if (t === 'auto' && !App._themeWatcherInstalled) {
          var mq = window.matchMedia('(prefers-color-scheme: dark)');
          if (mq.addEventListener) mq.addEventListener('change', function() { App.applyTheme(); });
          else if (mq.addListener) mq.addListener(function() { App.applyTheme(); }); // fallback for older browsers
          App._themeWatcherInstalled = true;
        }
      } catch (e) {}
    },

    /* data-arg='...' HTML atributi ichiga xavfsiz joylash uchun — matnda ' (apostrof) bo'lsa
       (masalan "So'z", "Bo'lim") atribut vaqtidan oldin yopilib ketmasligi uchun escape qilinadi. */
    arg: function (obj) { return JSON.stringify(obj).replace(/'/g, '&#39;'); },

    /* "2026-08-30" -> "30-avg" (Chrome'ning uz-locale Intl qo'llabi ishonchsiz,
       shuning uchun oy nomlari qo'lda) */
    uzDate: function (v) {
      if (!v) return '';
      var m = String(v).match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (!m) return String(v);
      var MON = ['yan', 'fev', 'mar', 'apr', 'may', 'iyn', 'iyl', 'avg', 'sen', 'okt', 'noy', 'dek'];
      return parseInt(m[3], 10) + '-' + (MON[parseInt(m[2], 10) - 1] || m[2]);
    },

    /* Deadline satrining o'ng ustuni: tepada boshlanish, pastda tugash sanasi.
       Ilgari tugash sanasi hech qayerda ko'rinmasdi (faqat hisoblagich bor edi). */
    dlDates: function (d) {
      if (!d || (!d.start && !d.end)) return '';
      return '<div class="dl-dates">' +
        '<div class="dl-d"><span>Boshlandi</span><b>' + App.esc(App.uzDate(d.start) || '—') + '</b></div>' +
        '<div class="dl-d"><span>Tugaydi</span><b class="end">' + App.esc(App.uzDate(d.end) || '—') + '</b></div>' +
        '</div>';
    },
    /* Boostday vazifasi bilan Sport mashqini bog'laydigan YAGONA qoida.
       Boostday matni "21:31 - 21:40 | Klassik otjimaniya" ko'rinishida
       bo'ladi, Sport'dagi nom esa "Klassik otjimaniya" — taqqoslashdan
       oldin vaqt prefiksi olib tashlanadi va bo'shliqlar birxillashtiriladi.
       Ayni shu qoida server tomonida ham bor:
         bot_py/app/helpers.py::normalize_task_name
         backend_py/app/handlers/sport.py::_TIME_PREFIX_SQL
       Uchalasi bir xil bo'lishi SHART — aks holda belgilash bir joyda
       ko'rinib, boshqasida ko'rinmay qoladi. */
    normTaskName: function (text) {
      return String(text == null ? '' : text)
        .replace(/^\s*\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}\s*\|\s*/, '')
        /* O'zbekcha matnda apostrof bir necha xil belgi bilan yoziladi
           ("To'pni" / "Toʻpni") — birxillashtirilmasa nom mos kelmay qoladi. */
        .replace(/[ʻʼ‘’`´]/g, "'")
        .replace(/\s+/g, ' ')
        .trim();
    },
    /* Taqqoslash uchun kalit (registrga befarq) */
    taskKey: function (text) { return App.normTaskName(text).toLowerCase(); },

    md: function (text) { return App._mdToHtml(text); },

    /* Matnni fayl qilib yuklab beradi (server so'rovisiz, brauzer ichida).
       Nomdagi fayl tizimi uchun xavfli belgilar almashtiriladi. */
    download: function (filename, text, mime) {
      var name = String(filename || 'fayl').replace(/[\\/:*?"<>|]/g, '-').slice(0, 120);
      var blob = new Blob([text == null ? '' : String(text)],
        { type: (mime || 'text/markdown') + ';charset=utf-8' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    },
    icons: function (root) { if (window.AppIcons) window.AppIcons.render(root || document); },
    el: function (id) { return document.getElementById(id); },
    coming: function (page, o) {
      o = o || {};
      page.innerHTML = '<div class="soon"><div class="soon-ic"><span data-icon="' + (o.icon || 'lock') +
        '" data-icon-size="30"></span></div><b>' + App.esc(o.title || 'Tez orada') + '</b><p>' +
        App.esc(o.text || 'Bu bo\'lim ustida ish olib borilmoqda. Tez orada tayyor bo\'ladi.') +
        '</p><span class="soon-badge">Tez orada</span></div>';
      App.icons(page);
    },
    empty: function (o) {
      o = o || {};
      return '<div class="empty"><span data-icon="' + (o.icon || 'list') + '" data-icon-size="34"></span><b>' +
        App.esc(o.title || 'Bo\'sh') + '</b><span>' + App.esc(o.text || '') + '</span></div>';
    }
  };

  /* Global action delegatsiya: data-act="name" data-arg='json' */
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-act]');
    if (!t) return;
    var name = t.getAttribute('data-act');
    var arg = t.getAttribute('data-arg');
    if (arg) { try { arg = JSON.parse(arg); } catch (x) {} }
    if (name === 'closeSheet') { App.closeSheet(); return; }
    if (name === 'go') { App.go(arg && arg.v, arg && arg.p); return; }
    if (App.actions && App.actions[name]) { e.preventDefault(); App.actions[name](arg, t); }
  });
  App.actions = {};

  function parseCurrentUrl() {
    var view = 'home', params = {};
    var hash = location.hash || '';
    var m = hash.match(/^#\/?([\w-]+)(?:\?(.*))?$/);
    if (m) {
      if (views[m[1]]) view = m[1];
      if (m[2]) {
        m[2].split('&').forEach(function (pair) {
          if (!pair) return;
          var eq = pair.indexOf('=');
          var k = decodeURIComponent(eq >= 0 ? pair.slice(0, eq) : pair);
          var v = eq >= 0 ? decodeURIComponent(pair.slice(eq + 1)) : '';
          params[k] = v;
        });
      }
    } else if (location.search) {
      try {
        var sp = new URLSearchParams(location.search);
        if (sp.get('v') && views[sp.get('v')]) view = sp.get('v');
        sp.forEach(function (v, k) { if (k !== 'v') params[k] = v; });
      } catch (e) {}
    }
    return { view: view, params: params };
  }

  /* Orqaga tugmasi */
  window.addEventListener('popstate', function (e) {
    App.closeSheet();
    var st = e.state;
    if (st && st.view && views[st.view]) {
      App.go(st.view, st.params || {}, { silent: true });
    } else {
      var u = parseCurrentUrl();
      App.go(u.view, u.params, { silent: true });
    }
  });

  App.boot = function () {
    pageEl = document.getElementById('page');
    var u = parseCurrentUrl();
    App.go(u.view, u.params, { silent: true });
  };

  window.App = App;

  /* ================= Markdown -> HTML (tashqi kutubxonasiz) =================
     Avval grammar.js ichida yopiq edi; endi App.md() orqali umumiy —
     Grammar mavzulari ham, Arxiv > Qoidalar ham shuni ishlatadi.
     Qo'llab-quvvatlanadi: sarlavhalar, JADVALLAR (moslashuv bilan),
     ro'yxatlar (ichma-ich va belgilash), kod bloklari, iqtiboslar,
     rasm, havola, qalin/qiya/o'chirilgan matn, ajratuvchi chiziq. */

  /* Havola/rasm manzili xavfsizmi? (javascript: kabi yozuvlarni to'sadi) */
  function safeUrl(u) {
    var s = String(u || '').trim();
    if (/^(https?:|mailto:|tel:|\/|#|data:image\/)/i.test(s)) return s;
    return '';
  }

  function mdInline(s) {
    s = App.esc(s);
    // Kod ichidagi belgilar formatlanmasligi uchun avval ajratib olamiz
    var codes = [];
    s = s.replace(/`([^`]+)`/g, function (_, c) {
      codes.push(c); return '@@C' + (codes.length - 1) + '@@';
    });

    // Rasm havoladan oldin tekshiriladi (![...](...) sintaksisi o'xshash)
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, function (_, alt, url) {
      var u = safeUrl(url);
      return u ? '<img src="' + u + '" alt="' + alt + '" loading="lazy">' : alt;
    });
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, function (_, txt, url) {
      var u = safeUrl(url);
      return u ? '<a href="' + u + '" target="_blank" rel="noopener">' + txt + '</a>' : txt;
    });

    // So'zlar va tarjimalar uchun: {word|translation}
    s = s.replace(/\{([^{|]+)\|([^}]+)\}/g, '<span class="dict-word" data-trans="$2">$1</span>');

    s = s.replace(/\*\*\*([^*]+)\*\*\*/g, '<b><i>$1</i></b>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    s = s.replace(/__([^_]+)__/g, '<b>$1</b>');
    s = s.replace(/~~([^~]+)~~/g, '<s>$1</s>');
    s = s.replace(/\*([^*]+)\*/g, '<i>$1</i>');
    s = s.replace(/(^|[\s(])_([^_]+)_(?=[\s).,!?:;]|$)/g, '$1<i>$2</i>');

    return s.replace(/@@C(\d+)@@/g, function (_, n) { return '<code>' + codes[+n] + '</code>'; });
  }

  /* Jadval qatorini kataklarga bo'ladi */
  function tableCells(line) {
    var t = line.trim().replace(/^\|/, '').replace(/\|$/, '');
    return t.split('|').map(function (c) { return c.trim(); });
  }
  function isTableSep(line) {
    return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(line || '');
  }

  function mdToHtml(md) {
    var lines = String(md || '').replace(/\r/g, '').split('\n');
    var html = '', i = 0, para = [];

    function flushPara() {
      if (para.length) { html += '<p>' + mdInline(para.join(' ')) + '</p>'; para = []; }
    }

    /* Ro'yxatni ichma-ich (indent bo'yicha) yig'adi */
    function readList(ordered) {
      var re = ordered ? /^(\s*)\d+[.)]\s+(.*)$/ : /^(\s*)[-*+]\s+(.*)$/;
      var baseIndent = null, out = '', open = 0;
      while (i < lines.length) {
        var m = lines[i].match(re);
        if (!m) {
          // Ro'yxat ichidagi bo'sh qator — keyingisi ham ro'yxat bo'lsa davom etadi
          if (/^\s*$/.test(lines[i]) && lines[i + 1] && re.test(lines[i + 1])) { i++; continue; }
          break;
        }
        var indent = m[1].replace(/\t/g, '  ').length;
        if (baseIndent === null) baseIndent = indent;
        var level = Math.min(2, Math.floor(Math.max(0, indent - baseIndent) / 2));
        while (open < level) { out += '<' + (ordered ? 'ol' : 'ul') + '>'; open++; }
        while (open > level) { out += '</' + (ordered ? 'ol' : 'ul') + '>'; open--; }

        var text = m[2];
        // Belgilash ro'yxati: - [ ] / - [x]
        var task = text.match(/^\[([ xX])\]\s+(.*)$/);
        if (task) {
          var checked = task[1].toLowerCase() === 'x';
          out += '<li class="md-task' + (checked ? ' done' : '') + '">' +
            '<span class="md-box">' + (checked ? '✓' : '') + '</span>' + mdInline(task[2]) + '</li>';
        } else {
          out += '<li>' + mdInline(text) + '</li>';
        }
        i++;
      }
      while (open > 0) { out += '</' + (ordered ? 'ol' : 'ul') + '>'; open--; }
      return '<' + (ordered ? 'ol' : 'ul') + '>' + out + '</' + (ordered ? 'ol' : 'ul') + '>';
    }

    while (i < lines.length) {
      var line = lines[i];

      // Kod bloki ```til
      if (/^\s*```/.test(line)) {
        flushPara();
        var lang = (line.trim().replace(/^```/, '') || '').trim();
        var code = [];
        i++;
        while (i < lines.length && !/^\s*```/.test(lines[i])) { code.push(lines[i]); i++; }
        html += '<pre' + (lang ? ' data-lang="' + App.esc(lang) + '"' : '') + '><code>' +
          App.esc(code.join('\n')) + '</code></pre>';
        i++; continue;
      }

      if (/^\s*$/.test(line)) { flushPara(); i++; continue; }

      // Jadval: sarlavha qatoridan keyin ajratuvchi kelsa
      if (line.indexOf('|') >= 0 && isTableSep(lines[i + 1])) {
        flushPara();
        var head = tableCells(line);
        var aligns = tableCells(lines[i + 1]).map(function (c) {
          if (/^:.*:$/.test(c)) return 'center';
          if (/:$/.test(c)) return 'right';
          return 'left';
        });
        i += 2;
        var body = '';
        while (i < lines.length && lines[i].indexOf('|') >= 0 && !/^\s*$/.test(lines[i])) {
          var cells = tableCells(lines[i]);
          body += '<tr>' + head.map(function (_, ci) {
            return '<td style="text-align:' + (aligns[ci] || 'left') + '">' + mdInline(cells[ci] || '') + '</td>';
          }).join('') + '</tr>';
          i++;
        }
        html += '<div class="md-table-wrap"><table class="md-table"><thead><tr>' +
          head.map(function (h2, ci) {
            return '<th style="text-align:' + (aligns[ci] || 'left') + '">' + mdInline(h2) + '</th>';
          }).join('') + '</tr></thead><tbody>' + body + '</tbody></table></div>';
        continue;
      }

      var h = line.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        flushPara();
        var lvl = Math.min(6, h[1].length + 1);
        html += '<h' + lvl + '>' + mdInline(h[2]) + '</h' + lvl + '>';
        i++; continue;
      }

      if (/^\s*>\s?/.test(line)) {
        flushPara();
        var quote = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) { quote.push(lines[i].replace(/^\s*>\s?/, '')); i++; }
        html += '<blockquote>' + mdInline(quote.join(' ')) + '</blockquote>';
        continue;
      }

      if (/^\s*([-*_])\s*\1\s*\1[\s\-*_]*$/.test(line)) { flushPara(); html += '<hr>'; i++; continue; }

      if (/^\s*[-*+]\s+/.test(line)) { flushPara(); html += readList(false); continue; }
      if (/^\s*\d+[.)]\s+/.test(line)) { flushPara(); html += readList(true); continue; }

      para.push(line); i++;
    }
    flushPara();
    return html;
  }

  App._mdToHtml = mdToHtml;

  // --- Dictionary Tooltip Logic ---
  window.addEventListener('DOMContentLoaded', function() {
    var tooltip = document.createElement('div');
    tooltip.id = 'dict-tooltip';
    tooltip.className = 'dict-tooltip';
    document.body.appendChild(tooltip);

    var hideTimeout;

    document.body.addEventListener('mouseover', function(e) {
      if (e.target.classList.contains('dict-word')) {
        clearTimeout(hideTimeout);
        var trans = e.target.getAttribute('data-trans');
        if (trans) {
          tooltip.innerHTML = '<div class="dict-trans">' + App.esc(trans).replace(/,/g, '<br>') + '</div>' + 
                              '<div class="dict-actions">' +
                                '<span class="dict-btn dict-check"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg></span>' +
                                '<span class="dict-btn dict-book"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg></span>' +
                              '</div>';
          var rect = e.target.getBoundingClientRect();
          tooltip.style.left = (rect.left + (rect.width / 2)) + 'px';
          tooltip.style.top = (rect.top - 8) + 'px';
          tooltip.classList.add('visible');
        }
      } else if (e.target.closest('#dict-tooltip')) {
        clearTimeout(hideTimeout);
      }
    });

    document.body.addEventListener('mouseout', function(e) {
      if (e.target.classList.contains('dict-word') || e.target.closest('#dict-tooltip')) {
        hideTimeout = setTimeout(function() {
          tooltip.classList.remove('visible');
        }, 200);
      }
    });
  });

  /* ==========================================
     POMODORO TIMER (Global Widget)
     ========================================== */
  App.Pomo = {
    time: 0,
    mode: 'work', // work, rest
    timer: null,
    init: function() {
      this.el = document.createElement('div');
      this.el.id = 'pomo-widget';
      this.el.className = 'work';
      this.el.innerHTML = '<div class="p-icon"><span data-icon="clock" data-icon-size="16"></span></div><div class="p-time">25:00</div>';
      this.el.style.display = 'none';
      document.body.appendChild(this.el);
      App.icons(this.el);
      
      var self = this;
      this.el.onclick = function() { self.toggle(); };
      App.actions.pomoToggle = function() { self.toggle(); };
    },
    toggle: function() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
        if (this.time > 0) return; // paused
      }
      if (this.time <= 0) {
        this.mode = 'work';
        this.time = 25 * 60;
        this.el.className = this.mode;
        this.el.style.display = 'flex';
      }
      var self = this;
      this.timer = setInterval(function() {
        self.time--;
        if (self.time <= 0) {
          clearInterval(self.timer);
          self.timer = null;
          self.notify();
          self.mode = self.mode === 'work' ? 'rest' : 'work';
          self.time = self.mode === 'work' ? 25 * 60 : 5 * 60;
          self.el.className = self.mode;
        }
        self.render();
      }, 1000);
      this.render();
    },
    render: function() {
      if(this.time <= 0) { this.el.style.display = 'none'; return; }
      this.el.style.display = 'flex';
      var m = Math.floor(this.time / 60);
      var s = this.time % 60;
      this.el.querySelector('.p-time').textContent = (m < 10 ? '0'+m : m) + ':' + (s < 10 ? '0'+s : s);
    },
    notify: function() {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(this.mode === 'work' ? 'Vaqt tugadi! Dam oling.' : 'Dam olish tugadi! Ishga qayting.');
      } else if ('Notification' in window && Notification.permission !== 'denied') {
        Notification.requestPermission();
      }
      App.toast(this.mode === 'work' ? 'Vaqt tugadi! 5 daqiqa dam oling.' : 'Dam olish tugadi! Ishga qayting.');
    }
  };
  document.addEventListener('DOMContentLoaded', function() { 
    App.Pomo.init(); 
    App.syncOffline();
  });
  window.addEventListener('online', function() { App.syncOffline(); });

})();
