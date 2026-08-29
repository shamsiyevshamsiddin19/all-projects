/* Kirish (auth) — ilk sozlash, login, chiqish. Ilova faqat kirilgandan keyin ochiladi. */
(function () {
  'use strict';

  var Auth = { user: null, checked: false };

  function post(payload) {
    return fetch(App.api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store'
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!j || j.holat !== true) throw new Error((j && j.xabar) || 'Xatolik yuz berdi');
        return j;
      });
    });
  }

  function screen(html) {
    var el = document.getElementById('auth-screen');
    if (!el) {
      el = document.createElement('div');
      el.id = 'auth-screen';
      document.body.appendChild(el);
    }
    el.innerHTML = '<div class="auth-box">' + html + '</div>';
    App.icons(el);
    return el;
  }

  function closeScreen() {
    var el = document.getElementById('auth-screen');
    if (el) el.remove();
  }

  function logoHtml() {
    return '<img class="auth-logo-img" data-app-icon src="' + App.appIconSrc() + '" alt="">';
  }

  /* --- Kirish ekrani --- */
  function loginScreen(msg) {
    var el = screen(
      logoHtml() +
      '<h2>Yordamchi</h2>' +
      '<p class="muted">Davom etish uchun tizimga kiring.</p>' +
      (msg ? '<div class="auth-err">' + App.esc(msg) + '</div>' : '') +
      '<label class="field"><span>Email</span><input class="input" id="au-email" type="email" autocomplete="username"></label>' +
      '<label class="field"><span>Parol</span><input class="input" id="au-pass" type="password" autocomplete="current-password"></label>' +
      '<button class="btn" id="au-go">Kirish</button>'
    );
    var submit = function () {
      var email = el.querySelector('#au-email').value.trim();
      var parol = el.querySelector('#au-pass').value;
      if (!email || !parol) return loginScreen('Email va parolni kiriting.');
      var btn = el.querySelector('#au-go'); btn.disabled = true; btn.textContent = 'Tekshirilmoqda...';
      post({ amal: 'kirish', email: email, parol: parol })
        .then(function (j) { Auth.user = j; closeScreen(); resyncThenStart(); })
        .catch(function (e) { loginScreen(e.message); });
    };
    el.querySelector('#au-go').onclick = submit;
    el.querySelector('#au-pass').onkeydown = function (e) { if (e.key === 'Enter') submit(); };
    setTimeout(function () { el.querySelector('#au-email').focus(); }, 100);
  }

  /* --- Google orqali kirish (yagona ruxsat etilgan yo'l) ---
     Google Identity Services (GIS) skripti FAQAT shu ekran kerak bo'lganda
     yuklanadi — oddiy ochilishda tashqi so'rov qo'shilmasin. GIS bizga
     Google IMZOLAGAN ID token beradi; email o'sha tokenning ichida keladi
     va serverda Google'ning o'zida tekshiriladi. Shuning uchun bu yerdan
     email/uid yuborilmaydi — faqat `credential`. */
  function wantsLogin() {
    try { return /[?&]login=1(&|$)/.test(location.search || ''); } catch (e) { return false; }
  }

  var GSI_SRC = 'https://accounts.google.com/gsi/client';

  function loadGsi() {
    if (window.__gsiP) return window.__gsiP;
    window.__gsiP = new Promise(function (resolve, reject) {
      if (window.google && google.accounts && google.accounts.id) { resolve(); return; }
      var sc = document.createElement('script');
      sc.src = GSI_SRC; sc.async = true; sc.defer = true;
      sc.onload = function () { resolve(); };
      sc.onerror = function () { reject(new Error('Google skripti yuklanmadi')); };
      document.head.appendChild(sc);
    });
    return window.__gsiP;
  }

  /* Telegram aloqasi — bo'sh bo'lsa blok umuman chizilmaydi.
     Noto'g'ri havola qo'yilgandan ko'ra ko'rsatmagan yaxshi. */
  var TG_USER = 'shamsiyev_shamsiddin';

  function tgHtml() {
    if (!TG_USER) return '';
    var u = String(TG_USER).replace(/^@/, '');
    return '<a class="agate-tg" href="https://t.me/' + encodeURIComponent(u) + '" ' +
      'target="_blank" rel="noopener noreferrer">' +
      '<span data-icon="send" data-icon-size="15"></span>' +
      '<span>Bog\'lanish — @' + App.esc(u) + '</span></a>';
  }

  function googleScreen(clientId, msg) {
    var el = screen(
      '<div class="agate">' +
        '<div class="agate-mark">' +
          '<span class="agate-glow" aria-hidden="true"></span>' +
          '<img class="agate-logo" data-app-icon src="' + App.appIconSrc() + '" alt="">' +
        '</div>' +

        '<h1 class="agate-title">Yordamchi</h1>' +
        '<p class="agate-sub">Shaxsiy o\'quv maydoni</p>' +

        '<div class="agate-card">' +
          '<div class="agate-lock">' +
            '<span data-icon="lock" data-icon-size="14"></span>' +
            '<span>Faqat egasi kira oladi</span>' +
          '</div>' +

          (msg ? '<div class="agate-err">' +
                   '<span data-icon="alert" data-icon-size="15"></span>' +
                   '<span>' + App.esc(msg) + '</span></div>' : '') +

          '<div id="au-gbtn" class="agate-btnhost"></div>' +
          '<p class="agate-note" id="au-gnote">Google yuklanmoqda…</p>' +
        '</div>' +

        tgHtml() +
      '</div>'
    );

    if (!clientId) {
      el.querySelector('#au-gnote').textContent =
        'Google kirishi hali sozlanmagan (GOOGLE_CLIENT_ID yo\'q).';
      return;
    }

    loadGsi().then(function () {
      var note = el.querySelector('#au-gnote');
      var host = el.querySelector('#au-gbtn');
      if (!host) return;
      if (note) note.textContent = '';

      google.accounts.id.initialize({
        client_id: clientId,
        callback: function (resp) {
          var cred = resp && resp.credential;
          if (!cred) { googleScreen(clientId, 'Google javobi bo\'sh keldi.'); return; }
          if (note) note.textContent = 'Tekshirilmoqda...';
          post({ amal: 'google_kirish', credential: cred })
            .then(function (j) {
              Auth.user = j; gateRemember(true); closeScreen(); resyncThenStart();
            })
            .catch(function (e) { googleScreen(clientId, e.message); });
        }
      });
      google.accounts.id.renderButton(host, {
        theme: 'filled_blue', size: 'large', shape: 'pill',
        text: 'signin_with', width: 280
      });
    }).catch(function () {
      var note = el.querySelector('#au-gnote');
      if (note) note.textContent = 'Google skriptini yuklab bo\'lmadi. Internetni tekshiring.';
    });
  }

  /* --- Ilk sozlash: birinchi (va yagona) akkaunt --- */
  function setupScreen(msg) {
    var el = screen(
      logoHtml() +
      '<h2>Ilk sozlash</h2>' +
      '<p class="muted">Saytni himoyalash uchun o\'z akkauntingizni yarating. Bu bir martalik — keyin ro\'yxatdan o\'tish yopiladi.</p>' +
      (msg ? '<div class="auth-err">' + App.esc(msg) + '</div>' : '') +
      '<label class="field"><span>Ism</span><input class="input" id="au-name" autocomplete="name"></label>' +
      '<label class="field"><span>Email</span><input class="input" id="au-email" type="email" autocomplete="username"></label>' +
      '<label class="field"><span>Parol (kamida 6 belgi)</span><input class="input" id="au-pass" type="password" autocomplete="new-password"></label>' +
      '<button class="btn" id="au-go">Akkaunt yaratish</button>'
    );
    el.querySelector('#au-go').onclick = function () {
      var ism = el.querySelector('#au-name').value.trim();
      var email = el.querySelector('#au-email').value.trim();
      var parol = el.querySelector('#au-pass').value;
      if (!ism || !email || !parol) return setupScreen('Barcha maydonlarni to\'ldiring.');
      if (parol.length < 6) return setupScreen('Parol kamida 6 ta belgidan iborat bo\'lsin.');
      var btn = el.querySelector('#au-go'); btn.disabled = true; btn.textContent = 'Yaratilmoqda...';
      post({ amal: 'royxatdan_otish', ism: ism, email: email, parol: parol })
        .then(function (j) { Auth.user = j; closeScreen(); resyncThenStart(); })
        .catch(function (e) { setupScreen(e.message); });
    };
  }

  /* --- Chiqish --- */
  App.actions.logout = function () {
    App.confirm('Tizimdan chiqasizmi?', function () {
      /* Oflayn rejim uchun API javoblari service worker keshida saqlanadi
         (maqsad, lug'at, mavzular va h.k.). Chiqishda uni ham tozalaymiz —
         aks holda chiqqandan keyin ham internetsiz holatda eski shaxsiy
         ma'lumot ko'rinib qolardi. */
      var clearData = (window.caches && caches.keys)
        ? caches.keys().then(function (keys) {
            return Promise.all(keys
              .filter(function (k) { return k.indexOf('yordamchi-data') === 0; })
              .map(function (k) { return caches.delete(k); }));
          }).catch(function () {})
        : Promise.resolve();

      /* Chiqishda "oxirgi safar kirgan edingiz" eslatmasi ham o'chadi —
         aks holda qayta yuklanganda ilova bir lahza ochilib ko'rinardi. */
      gateRemember(false);

      post({ amal: 'chiqish' }).catch(function () {})
        .then(function () { return clearData; })
        .then(function () { location.reload(); });
    }, { yes: 'Chiqish' });
  };

  var startApp = function () {};

  /* Kirishdan oldingi so'rovlar 401 bilan qaytgani uchun sinxronlash o'chib qolgan
     bo'lishi mumkin — kirgach uni qaytadan ulab, so'ng ilovani ishga tushiramiz. */
  function resyncThenStart() {
    var done = false;
    var go = function () { if (done) return; done = true; startApp(); };
    if (window.RemoteStorageBridge && window.RemoteStorageBridge.reset) {
      window.RemoteStorageBridge.reset().then(go).catch(go);
      setTimeout(go, 4000); // xavfsizlik: server javob bermasa ham ochiladi
    } else { go(); }
  }
  /* ---------- Oxirgi kirish holatini eslab qolish ----------
     `sessiya_tekshir` — ilova ochilishidagi UCHINCHI majburiy kutish edi:
     javob kelmaguncha splash ekran turardi, ya'ni har ochilishda serverga
     bir borib-kelish. Endi oxirgi natija shu qurilmada saqlanadi va ilova
     uni ishonib DARHOL ochiladi; tekshiruv esa orqa fonda ketadi.

     Bu FAQAT ijobiy natija uchun eslab qolinadi (kirgan yoki himoya
     o'chirilgan). Orqa fondagi tekshiruv "kirmagansiz" desa — kirish
     ekrani o'sha zahoti chiqadi va eslatma o'chiriladi. Shu orada ko'ringan
     ma'lumot ayni shu qurilmaning o'z suratidan olinadi, ya'ni yangi
     ma'lumot ochilib qolmaydi. Saqlanadigan narsa — bitta bayroq, hech
     qanday shaxsiy ma'lumot yoki parol emas. */
  var GATE_KEY = 'auth_gate_ok_v1';

  function gateRemember(ok) {
    try {
      if (window.RemoteStorageBridge && window.RemoteStorageBridge.localSet) {
        window.RemoteStorageBridge.localSet(GATE_KEY, ok ? '1' : null);
      }
    } catch (e) {}
  }

  function gateRemembered() {
    try {
      return !!(window.RemoteStorageBridge &&
                window.RemoteStorageBridge.localGet &&
                window.RemoteStorageBridge.localGet(GATE_KEY) === '1');
    } catch (e) { return false; }
  }

  window.Auth = {
    data: Auth,
    /* bootstrap.js shu orqali ishga tushadi */
    gate: function (onReady) {
      startApp = onReady;

      /* Oxirgi safar hammasi joyida bo'lgan bo'lsa — kutmaymiz. */
      var opened = false;
      var open = function () { if (opened) return; opened = true; onReady(); };
      if (gateRemembered()) open();

      post({ amal: 'sessiya_tekshir' }).then(function (j) {
        Auth.checked = true;

        if (j.kirganmi) { Auth.user = j; gateRemember(true); open(); return; }

        /* Google rejimi: parol bilan kirish ham, ro'yxatdan o'tish ham yopiq.
           Akkaunt bor-yo'qligi ahamiyatsiz — ruxsat etilgan email birinchi
           kirganda server o'zi ochib beradi. */
        if (j.kirish_usuli === 'google') {
          /* Himoya hali yoqilmagan bo'lsa sayt ochiq turadi, lekin `?login=1`
             bilan kirish ekranini ataylab chaqirsa bo'ladi. Bu qulflashdan
             OLDIN Google kirishini sinab ko'rish uchun kerak: ishlamasa,
             egasi o'z saytidan tashqarida qolib ketmaydi. */
          if (!j.himoya && !wantsLogin()) { gateRemember(true); open(); return; }
          gateRemember(false);
          showLocked(function () { googleScreen(j.google_client_id); });
          return;
        }

        // Hali akkaunt yo'q — himoya yoqilgan/yoqilmaganidan qat'i nazar ilk sozlash ko'rsatiladi.
        if (!j.sozlanganmi) { gateRemember(false); showLocked(setupScreen); return; }
        if (!j.himoya) { gateRemember(true); open(); return; }   // himoya o'chirilgan — ochiq rejim

        gateRemember(false); showLocked(loginScreen);
      }).catch(function () {
        /* Server javob bermadi (internet yo'q yoki uzilish) — bloklab
           qo'ymaymiz, eskisidek ochamiz. Eslatmaga TEGMAYMIZ: tarmoq
           nosozligi kirish holati haqida hech narsa demaydi. */
        open();
      });
    }
  };

  /* Orqa fondagi tekshiruv "ruxsat yo'q" desa: ilova allaqachon ochilgan
     bo'lsa ham uni yopib, kerakli ekranni ko'rsatamiz. */
  function showLocked(screenFn) {
    hideSplash();
    screenFn();
  }

  function hideSplash() {
    var sp = document.getElementById('splash');
    if (sp) { sp.classList.add('gone'); setTimeout(function () { sp.remove(); }, 350); }
  }
})();
