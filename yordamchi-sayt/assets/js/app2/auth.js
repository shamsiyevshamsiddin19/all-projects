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

  /* `sessiya_tekshir` javobi — kirish ekrani shunga qarab chiziladi */
  var AUTH_INFO = {};

  /* Favqulodda kod ekrani. Google bilan bir xil natija beradi: sessiya
     ochiladi va ilova ishga tushadi. */
      /* --- Zamonaviy Kirish Ekrani (Desktop ijodkorlik + Mobile to'liq ekran) ---
     - Desktopda: chap tomonda boy vitrina va ilhomlantiruvchi brend zonasi, o'ngda karta.
     - Telefondada: 100% to'liq ekranli (edge-to-edge) qora va oq organik dizayn.
     - Google hisobi: Premium ko'rinish va "Tezkor" nishoni.
     - YOKI (OR) ajratgichi.
     - Maxfiy kalit: 4-4-4 guruhlangan "••••  ••••  ••••" format va brauzer parollar oynasini bloklash. */

  function loginScreenModern(clientId, msg) {
    var cId = clientId || (AUTH_INFO && AUTH_INFO.google_client_id) || '';
    var el = screen(
      '<div class="auth-desktop-wrap">' +
        '<!-- Desktop uchun video art paneli (losnhaazpv.mp4) -->' +
        '<div class="desktop-art-side">' +
          '<div class="art-video-box">' +
            '<video id="au-art-vid-1" class="art-bg-video active" autoplay loop muted playsinline preload="auto" src="/assets/video/losnhaazpv.mp4"></video>' +
            '<video id="au-art-vid-2" class="art-bg-video inactive" muted playsinline preload="auto" src="/assets/video/losnhaazpv.mp4"></video>' +
          '</div>' +
          '<div class="art-video-overlay">' +
            '<div class="art-brand">' +
              '<img class="art-brand-img" data-app-icon src="' + App.appIconSrc() + '" alt="Logo">' +
              '<span class="art-brand-name">Yordamchi</span>' +
            '</div>' +
            '<div class="art-footer">' +
              '© ' + (new Date().getFullYear()) + ' Yordamchi • Shaxsiy o\'quv maydoni' +
            '</div>' +
          '</div>' +
        '</div>' +

        '<!-- Kirish kartasi -->' +
        '<div class="auth-form-side">' +
          '<div class="login-card">' +
            '<!-- Yuqori qora qavariq sarlavha (Avatar bilan) -->' +
            '<div class="login-header">' +
              '<svg class="login-avatar-icon" viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round">' +
                '<circle cx="32" cy="20" r="11"/>' +
                '<path d="M14 54c0-11 8-19 18-19s18 8 18 19"/>' +
              '</svg>' +
              '<svg class="login-curve-svg" viewBox="0 0 350 70" preserveAspectRatio="none">' +
                '<path d="M 0 0 C 18 40, 65 67, 150 69 L 350 70 L 350 71 L 0 71 Z" fill="#ffffff"/>' +
              '</svg>' +
            '</div>' +

            '<!-- Pastki oq kontent qismi -->' +
            '<div class="login-body">' +
              '<h1 class="login-title">Kirish</h1>' +
              '<p class="login-sub">Yordamchi — shaxsiy o\'quv maydoni</p>' +

              (msg ? '<div class="login-err" id="au-err-box" style="display:flex;">' +
                       '<span data-icon="alert" data-icon-size="16"></span>' +
                       '<span id="au-err-text">' + App.esc(msg) + '</span>' +
                     '</div>'
                   : '<div class="login-err" id="au-err-box" style="display:none;">' +
                       '<span data-icon="alert" data-icon-size="16"></span>' +
                       '<span id="au-err-text"></span>' +
                     '</div>') +

              '<!-- 1. Google hisobi bilan kirish -->' +
              '<div class="login-field">' +
                '<label class="login-field-label">Google hisobi</label>' +
                '<div class="login-google-slot" id="au-gslot">' +
                  '<div id="au-gbtn"></div>' +
                  '<button type="button" class="login-google-custom" id="au-gcustom">' +
                    '<div class="login-google-left">' +
                      '<svg width="20" height="20" viewBox="0 0 24 24">' +
                        '<path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>' +
                        '<path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"/>' +
                        '<path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.04 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>' +
                        '<path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>' +
                      '</svg>' +
                      '<span>Google bilan kirish</span>' +
                    '</div>' +
                    '<span class="login-google-badge">Tezkor</span>' +
                  '</button>' +
                '</div>' +
              '</div>' +

              '<!-- YOKI ajratgichi -->' +
              '<div class="login-divider">' +
                '<span class="login-divider-line"></span>' +
                '<span class="login-divider-text">yoki</span>' +
                '<span class="login-divider-line"></span>' +
              '</div>' +

              '<!-- 2. Maxfiy kalit bilan kirish (4-4-4 dots) -->' +
              '<div class="login-field">' +
                '<label class="login-field-label">Maxfiy kalit (kirish kodi)</label>' +
                '<div class="login-input-wrap">' +
                  '<input type="text" class="login-input" id="au-code-input" ' +
                         'name="yordamchi_auth_key_' + Math.floor(Math.random()*9999) + '" ' +
                         'placeholder="••••  ••••  ••••" maxlength="18" ' +
                         'autocomplete="off" autocorrect="off" autocapitalize="characters" ' +
                         'spellcheck="false" data-lpignore="true" data-1p-ignore="true">' +
                  '<button type="button" class="login-eye-btn" id="au-eye-toggle" aria-label="Ko\'rsatish">' +
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                      '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>' +
                      '<circle cx="12" cy="12" r="3"/>' +
                    '</svg>' +
                  '</button>' +
                '</div>' +
              '</div>' +

              '<!-- 3. Kalitni unutdingizmi? -->' +
              '<div class="login-meta-row">' +
                '<a class="login-meta-link" href="https://t.me/shamsiyev_shamsiddin" target="_blank" rel="noopener noreferrer">Kalitni unutdingizmi?</a>' +
              '</div>' +

              '<!-- 4. Kirish tugmasi -->' +
              '<button type="button" class="login-btn" id="au-login-btn">Kirish</button>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>'
    );

    var errBox = el.querySelector('#au-err-box');
    var errText = el.querySelector('#au-err-text');
    function setErr(t) {
      if (!errBox || !errText) return;
      if (t) {
        errText.textContent = t;
        errBox.style.display = 'flex';
      } else {
        errBox.style.display = 'none';
        errText.textContent = '';
      }
    }

    var passInp = el.querySelector('#au-code-input');
    var eyeBtn = el.querySelector('#au-eye-toggle');
    var isPass = true;

    /* 4-4-4 guruhlab kiritish formati */
    if (passInp) {
      passInp.addEventListener('input', function () {
        var raw = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
        var parts = [];
        for (var i = 0; i < raw.length; i += 4) {
          parts.push(raw.slice(i, i + 4));
        }
        this.value = parts.join(' - ');
      });
    }

    if (eyeBtn && passInp) {
      eyeBtn.onclick = function () {
        isPass = !isPass;
        if (isPass) {
          passInp.classList.remove('revealed');
          eyeBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
        } else {
          passInp.classList.add('revealed');
          eyeBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
        }
      };
    }

    /* Kalit orqali kirish */
    var loginBtn = el.querySelector('#au-login-btn');
    var submitCode = function () {
      var kod = (passInp.value || '').replace(/[^A-Z0-9]/gi, '').trim();
      if (!kod) {
        setErr('Maxfiy kalitni kiriting yoki Google orqali kiring.');
        passInp.focus();
        return;
      }
      setErr('');
      loginBtn.disabled = true;
      loginBtn.textContent = 'Tekshirilmoqda…';
      post({ amal: 'kod_bilan_kirish', kod: kod })
        .then(function (j) {
          Auth.user = j;
          gateRemember(true);
          closeScreen();
          resyncThenStart();
        })
        .catch(function (e) {
          if (AUTH_INFO && AUTH_INFO.kirish_usuli === 'parol') {
            return post({ amal: 'kirish', email: 'admin', parol: kod })
              .then(function (j) {
                Auth.user = j;
                gateRemember(true);
                closeScreen();
                resyncThenStart();
              })
              .catch(function () {
                throw e;
              });
          }
          throw e;
        })
        .catch(function (e) {
          loginBtn.disabled = false;
          loginBtn.textContent = 'Kirish';
          setErr(e && e.message ? e.message : 'Kod noto\'g\'ri.');
          passInp.focus();
        });
    };

    if (loginBtn) loginBtn.onclick = submitCode;
    if (passInp) {
      passInp.onkeydown = function (e) { if (e.key === 'Enter') submitCode(); };
    }

    /* Google bilan kirish */
    var gCustom = el.querySelector('#au-gcustom');
    var gBtnHost = el.querySelector('#au-gbtn');

    if (!cId) {
      if (gCustom) {
        gCustom.onclick = function () {
          setErr('Google kirishi hali sozlanmagan. Pastdagi Maxfiy kalit bilan kiring.');
        };
      }
      return;
    }

    loadGsi().then(function () {
      google.accounts.id.initialize({
        client_id: cId,
        callback: function (resp) {
          var cred = resp && resp.credential;
          if (!cred) { setErr('Google javobi bo\'sh keldi.'); return; }
          setErr('Tekshirilmoqda...');
          post({ amal: 'google_kirish', credential: cred })
            .then(function (j) {
              Auth.user = j;
              gateRemember(true);
              closeScreen();
              resyncThenStart();
            })
            .catch(function (e) {
              setErr(e && e.message ? e.message : 'Google orqali kirib bo\'lmadi.');
            });
        }
      });

      if (gBtnHost) {
        /* Google tugmasi joylashganda darhol custom tugmani yashirish */
        try {
          var obs = new MutationObserver(function () {
            if (gBtnHost.children && gBtnHost.children.length > 0) {
              if (gCustom) gCustom.style.display = 'none';
              obs.disconnect();
            }
          });
          obs.observe(gBtnHost, { childList: true, subtree: true });
        } catch (_) {}

        var bodyW = (el.querySelector('.login-body') && el.querySelector('.login-body').clientWidth) || 350;
        var btnW = Math.min(390, Math.max(260, bodyW - 2));

        google.accounts.id.renderButton(gBtnHost, {
          theme: 'outline',
          size: 'large',
          shape: 'rectangular',
          text: 'signin_with',
          width: btnW,
          logo_alignment: 'left'
        });

        setTimeout(function () {
          if (gBtnHost.children && gBtnHost.children.length > 0 && gCustom) {
            gCustom.style.display = 'none';
          }
        }, 300);
      }

      if (gCustom) {
        gCustom.onclick = function () {
          try { google.accounts.id.prompt(); } catch (_) {}
        };
      }
    }).catch(function () {
      if (gCustom) {
        gCustom.onclick = function () {
          setErr('Google xizmati yuklanmadi. Internetni tekshiring yoki Maxfiy kalit bilan kiring.');
        };
      }
    });

    /* Desktop fon videosi uchun uzluksiz choksiz (seamless) loop kontrolleri */
    (function initSeamlessVideo() {
      var v1 = el.querySelector('#au-art-vid-1');
      var v2 = el.querySelector('#au-art-vid-2');
      if (!v1 || !v2) return;

      var active = v1;
      var next = v2;
      var isFading = false;
      var crossfadeSec = 0.8;

      function checkLoop() {
        if (active && active.duration && !isFading) {
          if (active.currentTime >= active.duration - crossfadeSec) {
            isFading = true;
            next.currentTime = 0;
            var p = next.play();
            if (p && p.then) {
              p.then(function () {
                next.style.opacity = '1';
                next.style.zIndex = '2';
                active.style.opacity = '0';
                active.style.zIndex = '1';
                setTimeout(function () {
                  try { active.pause(); active.currentTime = 0; } catch (_) {}
                  var tmp = active;
                  active = next;
                  next = tmp;
                  isFading = false;
                }, crossfadeSec * 1000);
              }).catch(function () {
                isFading = false;
              });
            } else {
              isFading = false;
            }
          }
        }
        requestAnimationFrame(checkLoop);
      }

      try { v1.play().catch(function () {}); } catch (_) {}
      requestAnimationFrame(checkLoop);
    })();
  }

  function loginScreen(msg) {
    loginScreenModern(AUTH_INFO.google_client_id, msg);
  }

  function googleScreen(clientId, msg) {
    loginScreenModern(clientId, msg);
  }

  function codeScreen(msg) {
    loginScreenModern(AUTH_INFO.google_client_id, msg);
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
    loginScreen: loginScreenModern,
    showLogin: function (msg) { loginScreenModern(AUTH_INFO.google_client_id, msg); },
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
        AUTH_INFO = j;
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
