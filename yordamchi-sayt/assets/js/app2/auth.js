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
  window.Auth = {
    data: Auth,
    /* bootstrap.js shu orqali ishga tushadi */
    gate: function (onReady) {
      startApp = onReady;
      post({ amal: 'sessiya_tekshir' }).then(function (j) {
        Auth.checked = true;
        if (j.kirganmi) { Auth.user = j; onReady(); return; }
        // Hali akkaunt yo'q — himoya yoqilgan/yoqilmaganidan qat'i nazar ilk sozlash ko'rsatiladi.
        if (!j.sozlanganmi) { hideSplash(); setupScreen(); return; }
        if (!j.himoya) { onReady(); return; }        // himoya o'chirilgan — ochiq rejim
        hideSplash(); loginScreen();
      }).catch(function () { onReady(); });          // server javob bermasa bloklab qo'ymaymiz
    }
  };

  function hideSplash() {
    var sp = document.getElementById('splash');
    if (sp) { sp.classList.add('gone'); setTimeout(function () { sp.remove(); }, 350); }
  }
})();
