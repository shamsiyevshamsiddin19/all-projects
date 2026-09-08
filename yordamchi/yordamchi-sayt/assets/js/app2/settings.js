/* Sozlamalar — grouped-list uslubi (iOS/Telegram kabi), cardlarsiz */
(function () {
  'use strict';
  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function dls() { try { return JSON.parse(ls('home_deadlines_v1', '[]')) || []; } catch (e) { return []; } }
  function saveDls(a) { localStorage.setItem('home_deadlines_v1', JSON.stringify(a)); }
  var THEME_LABEL = { auto: 'Avto', dark: 'Qorong\'u', light: 'Yorug\'' };

  function resizeImage(file, max, cb) {
    var r = new FileReader();
    r.onload = function () {
      var img = new Image();
      img.onload = function () {
        var w = img.width, h = img.height, sc = Math.min(1, max / Math.max(w, h));
        var c = document.createElement('canvas'); c.width = Math.round(w * sc); c.height = Math.round(h * sc);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        cb(c.toDataURL('image/jpeg', 0.85));
      };
      img.src = r.result;
    };
    r.readAsDataURL(file);
  }

  App.view('settings', {
    nav: 'settings',
    render: function (page) {
      var theme = ls('app_theme', 'auto');
      var avatar = ls('user_avatar', '') || App.avatarUrl(ls('user_name', 'Yordamchi'));
      var icon = App.appIconSrc();

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 6px"><h1>Sozlamalar</h1></div>' +

        '<button class="list-row" data-act="editProfile" style="padding:10px 1px">' +
        '<img src="' + avatar + '" style="width:46px;height:46px;border-radius:50%;object-fit:cover;flex-shrink:0">' +
        '<div class="li-main"><div class="li-title">' + App.esc(ls('user_name', 'Ism kiritilmagan')) + '</div>' +
        '<div class="li-sub">' + App.esc(ls('user_bio', 'Bio yo\'q')) + '</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="list-label">Ko\'rinish</div>' +
        '<div class="list-row" style="border-bottom:none;padding:9px 1px 15px">' +
        '<div class="seg" style="width:100%">' +
        Object.keys(THEME_LABEL).map(function (v) {
          return '<button class="' + (theme === v ? 'active' : '') + '" data-act="setTheme" data-arg=\'' + App.arg({ v: v }) + '\'>' + THEME_LABEL[v] + '</button>';
        }).join('') + '</div></div>' +


        '<button class="list-row" data-act="pickIcon">' +
        '<img data-app-icon src="' + icon + '" style="width:34px;height:34px;border-radius:10px;object-fit:cover;flex-shrink:0">' +
        '<div class="li-main"><div class="li-title">Ilova belgisi</div><div class="li-sub">Bosh ekran yorlig\'i uchun</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        /* Qulf sozlamasi faqat adminda — boshqalarda qulf umuman yo'q
           (`lock.js`), ya'ni bu qator ularga hech narsa qilmasdi. */
        ((window.Auth && Auth.isReadOnly && Auth.isReadOnly()) ? '' :
        '<div class="list-label">Lug\'at</div>' +
        '<button class="list-row" data-act="vocabLock">' +
        '<span class="li-ic" style="background:#6366f122;color:#6366f1" data-icon="lock" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Lug\'at qulfi</div>' +
        '<div class="li-sub">Qaysi bo\'limlar ochiq bo\'lishini tanlash</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>') +
        '<div class="list-label">Xavfsizlik</div>' +
        ((window.Auth && typeof Auth.isAdmin === 'function' && Auth.isAdmin()) ?
        '<button class="list-row" data-act="manageUsers">' +
        '<span class="li-ic" style="background:#3b82f622;color:#3b82f6" data-icon="users" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Foydalanuvchilar (Ruxsatlar)</div>' +
        '<div class="li-sub">Google akkaunt qo\'shish va bo\'limlarni sozlash</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' : '') +
        '<button class="list-row" data-act="accessCode">' +
        '<span class="li-ic" style="background:#f59e0b22;color:#f59e0b" data-icon="lock" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Favqulodda kirish kodi</div>' +
        '<div class="li-sub">Google ishlamaganda shu kod bilan kiriladi</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="list-label">Ilova (Mobil & Kompyuter)</div>' +
        '<button class="list-row" data-act="downloadApk">' +
        '<span class="li-ic" style="background:#10b98122;color:#10b981" data-icon="download" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Android Ilova (APK yuklab olish)</div>' +
        '<div class="li-sub">Telefonga to\'g\'ridan-to\'g\'ri o\'rnatish uchun (.apk fayl)</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<button class="list-row" data-act="downloadLinuxDeb">' +
        '<span class="li-ic" style="background:#3b82f622;color:#3b82f6" data-icon="download" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Linux Dasturi (DEB yuklab olish)</div>' +
        '<div class="li-sub">Ubuntu/Debian kompyuterlar uchun (.deb fayl)</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="list-label">O\'quv jarayoni</div>' +
        '<button class="list-row" data-act="sessiya">' +
        '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="calendar" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Sessiya</div>' +
        '<div class="li-sub" id="ss-sub">LMS jadvali, semestr va kun sozlamalari</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="between list-label"><span>Deadlinelar</span>' +
        '<button data-act="addDeadline" style="background:none;border:none;color:var(--accent);font-size:12px;font-weight:700;text-transform:none;letter-spacing:0">+ Qo\'shish</button></div>' +
        '<div id="dl-list"></div>' +

        '<button class="list-row" data-act="navConfig">' +
        '<span class="li-ic" data-icon="menu" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Menyu bo\'limlari</div>' +
        '<div class="li-sub">Kerak bo\'lmaganini yashirish</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="list-label">Ma\'lumotlar bazasi (Zaxira va Tiklash)</div>' +
        '<button class="list-row" data-act="dbExport">' +
        '<span class="li-ic" data-icon="upload" data-icon-size="15" style="transform:rotate(180deg)"></span>' +
        '<div class="li-main"><div class="li-title">To\'liq bazani yuklab olish (.sql)</div>' +
        '<div class="li-sub">Barcha jadvallar, darslar, lug\'at va ma\'lumotlar zaxirasi</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<button class="list-row" data-act="dbImportPrompt">' +
        '<span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Ma\'lumotlar bazasini tiklash</div>' +
        '<div class="li-sub">Kompyuterdagi .sql fayldan bazani qayta tiklash</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<button class="list-row" data-act="exportAll">' +
        '<span class="li-ic" data-icon="list" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Lokal sozlamalar zaxirasi (JSON)</div>' +
        '<div class="li-sub">Brauzer sozlamalari va kesh fayli</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

        '<div class="list-label">Xavfsizlik</div>' +
        '<button class="list-row" data-act="logout" style="color:var(--danger)">' +
        '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="lock" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title" style="color:var(--danger)">Tizimdan chiqish</div></div></button>' +

        '<p class="muted" style="text-align:center;font-size:12px;margin:34px 0 8px">Yordamchi</p>' +
        '<input type="file" id="av-file" hidden accept="image/*"><input type="file" id="icon-file" hidden accept="image/*"><input type="file" id="db-restore-file" hidden accept=".sql,.gz,.dump,.db,.txt">';

      App.icons(page);
      renderDeadlines();
      renderSessiyaSub();



      App.el('av-file').onchange = function (e) {
        var f = e.target.files[0]; if (!f) return;
        resizeImage(f, 320, function (data) { localStorage.setItem('user_avatar', data); App.toast('✅ Rasm saqlandi'); App.reload(); });
      };
      var dbInp = App.el('db-restore-file');
      if (dbInp) {
        dbInp.onchange = function (e) {
          var f = e.target.files[0];
          if (!f) return;
          var fd = new FormData();
          fd.append('file', f);
          /* `retries: 0` ATAYLAB: bazani import qilish idempotent EMAS.
             Javob yo'qolgan holatda qayta yuborish bazani ikki marta
             tiklashi mumkin — bu yerda kutish xavfsizroq.
             Timeout uzun, chunki import katta bo'lishi mumkin. */
          App.callForm('db_import', fd, {
            label: 'Baza tiklanmoqda: ' + f.name,
            retries: 0,
            timeout: 300000
          })
          .then(function () {
            App.toast('✅ Ma\'lumotlar bazasi muvaffaqiyatli tiklandi!');
            setTimeout(function () { App.reload(); }, 1200);
          })
          .catch(function (err) {
            App.toast('❌ Xatolik: ' + err.message);
          })
          .finally(function () {
            dbInp.value = '';
          });
        };
      }

      App.el('icon-file').onchange = function (e) {
        var f = e.target.files[0]; if (!f) return;
        resizeImage(f, 512, function (data) {
          localStorage.setItem('app_custom_icon', data);
          // 192px nusxa tayyor bo'lgach hamma joyni (splash, sidebar, favicon, kirish ekrani) yangilaymiz
          resizeImage(f, 192, function (d192) {
            localStorage.setItem('app_custom_icon_192', d192);
            App.applyAppIcon();
            // Serverga ham yozamiz: haqiqiy PNG fayl + manifest yangilanadi. Bu telefon
            // bosh ekraniga yorliq QAYTA qo'shilganda yangi belgi tushishi uchun kerak
            // (Android eski yorliqning belgisini keshda saqlaydi, o'zi yangilamaydi).
            App.call('save_app_icon', { icon: data })
              .then(function (r) {
                /* Server qaytargan versiyani SAQLASH shart: fayl nomi o'zgarmaydi
                   (ustiga yoziladi), shuning uchun kesh faqat `?v=` bilan yangilanadi.
                   Ilgari bu qiymat tashlab yuborilardi va ilova ochilganda avval
                   ESKI keshlangan belgi ko'rinib, keyin yangisiga almashardi. */
                if (r && r.version) localStorage.setItem('app_icon_version', String(r.version));
                App.applyAppIcon();
                App.toast('✅ Belgi yangilandi');
              })
              .catch(function (err) { App.toast('⚠️ Serverga saqlanmadi: ' + err.message); });
            App.reload();
          });
        });
      };
    }
  });

  App.actions.editProfile = function () {
    var html =
      '<div class="flex" style="margin-bottom:16px"><img id="pf-av" src="' + (ls('user_avatar', '') || App.avatarUrl(ls('user_name', 'Y'))) + '" style="width:56px;height:56px;border-radius:50%;object-fit:cover">' +
      '<button class="btn sec sm" data-act="pickAvatar"><span data-icon="camera" data-icon-size="15"></span>Rasm</button></div>' +
      '<label class="field"><span>Ism</span><input class="input" id="set-name" value="' + App.esc(ls('user_name', '')) + '" placeholder="Ismingiz"></label>' +
      '<label class="field"><span>Shior (bio)</span><input class="input" id="set-bio" value="' + App.esc(ls('user_bio', '')) + '" placeholder="Maqsad sari olg\'a!"></label>' +
      '<button class="btn" data-act="saveProfile">Saqlash</button>';
    App.sheet(html, { title: 'Profil' });
  };
  App.actions.pickAvatar = function () { App.el('av-file').click(); };
  App.actions.pickIcon = function () { App.el('icon-file').click(); };
  App.actions.saveProfile = function () {
    localStorage.setItem('user_name', App.el('set-name').value.trim());
    var bio = App.el('set-bio').value.trim();
    if (bio) localStorage.setItem('user_bio', bio); else localStorage.removeItem('user_bio');
    App.closeSheet(); App.toast('✅ Saqlandi'); App.reload();
  };

  /* To'liq PostgreSQL ma'lumotlar bazasini .sql fayl qilib yuklab olish */
  App.actions.dbExport = function () {
    App.toast('📦 Baza zaxirasi tayyorlanmoqda...');
    var a = document.createElement('a');
    a.href = '/api?action=db_export';
    a.download = '';
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { a.remove(); }, 1000);
  };

  /* Bazani .sql fayldan qayta tiklash */
  App.actions.dbImportPrompt = function () {
    App.confirm(
      '⚠️ Diqqat! Ushbu amal kompyuteringizdagi .sql zaxira faylidan ma\'lumotlar bazasini to\'liq qayta tiklaydi. Davom etasizmi?',
      function () {
        var inp = App.el('db-restore-file');
        if (inp) inp.click();
      },
      { danger: true, yes: 'Faylni tanlash' }
    );
  };

  /* To'liq zaxira: serverdagi asosiy ma'lumot + brauzerdagi sozlamalar bitta JSON faylga */
  App.actions.exportAll = function () {
    App.toast('Zaxira tayyorlanmoqda...');
    var dump = {
      version: 1,
      olingan: new Date().toISOString(),
      manba: location.origin,
      local: {},
      server: {}
    };
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        dump.local[k] = localStorage.getItem(k);
      }
    } catch (e) {}

    // Serverdan: maqsadlar, lug'atlar (2 til), test tuzilishi va natijalar tarixi
    var jobs = [
      App.call('get_data', null, { query: 'db=Global_Data' }).then(function (j) { dump.server.goals = j; }),
      App.call('get_dict_data', null, { query: 'lang=english' }).then(function (j) { dump.server.dict_english = j; }),
      App.call('get_dict_data', null, { query: 'lang=russian' }).then(function (j) { dump.server.dict_russian = j; }),
      App.call('get_structure').then(function (j) { dump.server.quiz_structure = j; }),
      App.call('get_quiz_results').then(function (j) { dump.server.quiz_results = j; }),
      App.call('get_mistakes', null, { query: 'lang=english' }).then(function (j) { dump.server.mistakes_english = j; }),
      App.call('get_mistakes', null, { query: 'lang=russian' }).then(function (j) { dump.server.mistakes_russian = j; })
    ].map(function (p) { return p.catch(function () {}); }); // bittasi ishlamasa ham qolgani olinsin

    Promise.all(jobs).then(function () {
      var blob = new Blob([JSON.stringify(dump, null, 2)], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      var d = new Date();
      a.href = url;
      a.download = 'yordamchi-zaxira-' + d.getFullYear() + '-' +
        ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2) + '.json';
      document.body.appendChild(a); a.click();
      setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 1000);
      App.toast('✅ Zaxira yuklab olindi');
    });
  };

  /* Menyu bo'limlarini ko'rsatish/yashirish */
  App.actions.navConfig = function () {
    if (!window.NavConfig) return;
    var hidden = NavConfig.hidden();
    var html =
      '<p class="muted" style="font-size:12.5px;margin:0 0 12px">Yashirilgan bo\'limlar menyudan olib tashlanadi. "Bosh" va "Sozlamalar" doim qoladi.</p>' +
      NavConfig.all.filter(function (i) { return i.v !== 'home' && i.v !== 'settings'; }).map(function (i) {
        var on = hidden.indexOf(i.v) < 0;
        return '<div class="list-row"><span class="li-ic" data-icon="' + i.ic + '" data-icon-size="15"></span>' +
          '<div class="li-main"><div class="li-title">' + i.n + '</div></div>' +
          '<button class="nv-tog' + (on ? ' on' : '') + '" data-v="' + i.v + '">' + (on ? 'Ko\'rinadi' : 'Yashirilgan') + '</button></div>';
      }).join('');
    var sh = App.sheet(html, { title: 'Menyu bo\'limlari' });
    sh.querySelectorAll('.nv-tog').forEach(function (b) {
      b.onclick = function () {
        var v = b.getAttribute('data-v');
        var cur = NavConfig.hidden();
        var i = cur.indexOf(v);
        if (i < 0) cur.push(v); else cur.splice(i, 1);
        localStorage.setItem('nav_hidden_v1', JSON.stringify(cur));
        var on = cur.indexOf(v) < 0;
        b.classList.toggle('on', on);
        b.textContent = on ? 'Ko\'rinadi' : 'Yashirilgan';
        if (window.NavRebuild) NavRebuild();
      };
    });
  };

  App.actions.setTheme = function (a) {
    // Tanlov localStorage'ga yoziladi -> remote-storage uni serverga
    // sinxronlaydi -> boshqa qurilmada bootstrap qaytadan qo'llaydi.
    try { localStorage.setItem('app_theme', a.v); } catch (e) {}
    App.applyTheme();   // data-theme + brauzer paneli rangi
    App.reload();
  };

  /* =========================================================
     SESSIYA — o'quv jarayoni sozlamalari.
     LMS (lms.tuit.uz) hisobi shu yerda ulanadi: parol SERVERDA shifrlangan
     holda saqlanadi va hech qachon qaytarilmaydi (localStorage'ga ham
     yozilmaydi — u brauzerga va sinxronga tushib ketardi).
     Tortilgan darslar Kun hisobi va bosh sahifadagi "Bugungi reja"da
     qo'lda kiritilgan kurs/ish vaqtlari bilan BIRGA ko'rinadi.
     ========================================================= */
  function renderSessiyaSub() {
    var el = App.el('ss-sub'); if (!el) return;
    App.call('lms_status').then(function (j) {
      var e = App.el('ss-sub'); if (!e) return;
      if (!j.connected) { e.textContent = 'LMS ulanmagan — bosib ulang'; return; }
      var bits = [j.semester_name || 'semestr tanlanmagan'];
      if (j.lessons) bits.push(j.lessons + ' ta dars');
      if (j.last_error) bits.push('⚠️ ' + j.last_error);
      e.textContent = bits.join(' · ');
    }).catch(function () {});
  }

  App.actions.sessiya = function () {
    var sh = App.sheet('<div id="ss-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Sessiya' });
    App.icons(sh);
    loadSessiya();
  };

  function loadSessiya() {
    App.call('lms_status').then(drawSessiya).catch(function (e) {
      var b = App.el('ss-body');
      if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  function drawSessiya(st) {
    var box = App.el('ss-body'); if (!box) return;
    var sems = st.semesters || [];

    if (!st.connected) {
      box.innerHTML =
        '<p class="muted" style="font-size:12.5px;margin:0 0 14px;line-height:1.6">' +
        'LMS (lms.tuit.uz) hisobingizni ulasangiz, dars jadvali avtomatik tortiladi va ' +
        'Kun hisobida o\'zingiz qo\'shgan kurs/ish vaqtlari bilan birga chiqadi.<br>' +
        '<b>Parol serverda shifrlanadi</b> va brauzerga hech qachon qaytarilmaydi.</p>' +
        '<label class="field"><span>Login (talaba ID)</span>' +
        '<input class="input" id="ss-login" autocomplete="username" placeholder="masalan: 1BK00000"></label>' +
        '<label class="field"><span>Parol</span>' +
        '<input class="input" id="ss-pass" type="password" autocomplete="current-password"></label>' +
        '<button class="btn" id="ss-connect">Ulash va jadvalni tortish</button>';
      box.querySelector('#ss-connect').onclick = function () {
        var login = box.querySelector('#ss-login').value.trim();
        var pass = box.querySelector('#ss-pass').value;
        if (!login || !pass) return App.toast('Login va parolni kiriting');
        var btn = box.querySelector('#ss-connect');
        btn.disabled = true; btn.textContent = 'Ulanmoqda...';
        App.call('lms_connect', { login: login, password: pass }).then(function (j) {
          App.toast('✅ Ulandi — ' + (j.synced || 0) + ' ta dars');
          drawSessiya(j);
          renderSessiyaSub();
          if (window.LmsDay) { LmsDay.setConnected(true); LmsDay.clear(); }
        }).catch(function (e) {
          App.toast('⚠️ ' + e.message);
          btn.disabled = false; btn.textContent = 'Ulash va jadvalni tortish';
        });
      };
      return;
    }

    box.innerHTML =
      '<div class="list-row" style="border-bottom:none">' +
      '<span class="li-ic" style="background:var(--success-soft);color:var(--success)" data-icon="check" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">' + App.esc(st.student_name || st.login) + '</div>' +
      '<div class="li-sub">' + App.esc(st.login) + ' · ' + (st.lessons || 0) + ' ta dars saqlangan</div></div></div>' +
      (st.last_sync ? '<p class="muted" style="font-size:11.5px;margin:-4px 1px 12px">Oxirgi yangilash: ' + App.esc(st.last_sync) + '</p>' : '') +
      (!st.lessons && !st.last_error
        ? '<p class="muted" style="font-size:12px;margin:-4px 1px 12px;line-height:1.55">' +
          'LMS tizimiga ulangan, ammo hozirda darslar topilmadi (ta\'til bo\'lishi mumkin). ' +
          'O\'zingiz kiritgan mashg\'ulot va ishlar qoladi.</p>'
        : '') +
      (st.last_error ? '<p style="font-size:12px;color:var(--danger);margin:-4px 1px 12px">⚠️ ' + App.esc(st.last_error) + '</p>' : '') +

      '<label class="list-row" style="cursor:pointer">' +
      '<div class="li-main"><div class="li-title">Avtomatik yangilash</div>' +
      '<div class="li-sub">Kun hisobi ochilganda kuniga bir marta jadvalni yangilaydi</div></div>' +
      '<input type="checkbox" id="ss-auto" style="width:20px;height:20px;accent-color:var(--success)"' +
      (st.auto_sync ? ' checked' : '') + '></label>' +

      '<button class="btn" id="ss-sync" style="margin-top:6px">Jadvalni hozir yangilash</button>' +

      '<div class="list-label" style="margin-top:18px">Darsdan tashqari</div>' +
      '<button class="list-row" data-act="sessiyaKun">' +
      '<span class="li-ic" data-icon="calendar" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Kurs va ish vaqtlarini qo\'shish</div>' +
      '<div class="li-sub">Kun hisobida: ish, mustaqil o\'qish, sport, uyqu — vaqti bilan</div></div>' +
      '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>' +

      '<button class="btn ghost" id="ss-off" style="margin-top:14px;color:var(--danger);border-color:var(--danger-soft)">Hisobni uzish</button>';
    App.icons(box);

    var semSel = box.querySelector('#ss-sem');
    box.querySelector('#ss-sync').onclick = function () {
      var btn = box.querySelector('#ss-sync');
      btn.disabled = true; btn.textContent = 'Yangilanmoqda...';
      App.call('lms_sync', semSel ? { semester_id: semSel.value } : {}).then(function (j) {
        App.toast('✅ ' + (j.synced || 0) + ' ta dars yangilandi');
        if (window.LmsDay) { LmsDay.setConnected(true); LmsDay.clear(); }
        drawSessiya(j); renderSessiyaSub();
      }).catch(function (e) {
        App.toast('⚠️ ' + e.message);
        btn.disabled = false; btn.textContent = 'Jadvalni hozir yangilash';
      });
    };
    box.querySelector('#ss-auto').onchange = function () {
      App.call('lms_options', { auto_sync: this.checked }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };
    box.querySelector('#ss-off').onclick = function () {
      App.confirm('LMS hisobi uziladi va tortilgan darslar o\'chiriladi. Qo\'lda kiritgan mashg\'ulotlaringizga tegilmaydi.', function () {
        App.call('lms_disconnect').then(function () {
          // Uzilgach `lmsDup` bayroqlari e'tiborga olinmaydi — qo'lda kiritilgan
          // dars jadvali avvalgidek to'liq qaytadi.
          if (window.LmsDay) { LmsDay.setConnected(false); LmsDay.clear(); }
          App.toast('Uzildi'); loadSessiya(); renderSessiyaSub();
        }).catch(function (e) { App.toast('⚠️ ' + e.message); });
      }, { danger: true, yes: 'Uzish' });
    };
  }

  App.actions.downloadApk = function () {
    App.sheet(
      '<div style="text-align:center;padding:6px 0 16px">' +
      '<div style="font-size:46px;margin-bottom:8px">📱</div>' +
      '<h3 style="margin:0 0 6px">Yordamchi Android Ilovasi</h3>' +
      '<p class="muted" style="font-size:13px;margin:0 0 18px;line-height:1.5">Ilovani to\'g\'ridan-to\'g\'ri telefoningizga o\'rnatish uchun APK faylni yuklab oling.</p>' +
      '<a href="/assets/downloads/yordamchi.apk" download="yordamchi.apk" class="btn" style="display:flex;align-items:center;justify-content:center;text-decoration:none;width:100%;margin-bottom:10px;background:var(--accent);color:#fff">📦 APK yuklab olish (51 MB)</a>' +
      (window._deferredPWAInstallPrompt
        ? '<button class="btn ghost" id="pwa-inst-act-btn" style="width:100%">✨ 1 bosishda o\'rnatish (PWA)</button>'
        : '') +
      '</div>',
      { title: 'Android Ilova' }
    );
    var pb = document.getElementById('pwa-inst-act-btn');
    if (pb && window._deferredPWAInstallPrompt) {
      pb.onclick = function () {
        window._deferredPWAInstallPrompt.prompt();
        App.closeSheet();
      };
    }
  };

  App.actions.downloadLinuxDeb = function () {
    var a = document.createElement('a');
    a.href = '/assets/downloads/yordamchi_1.0.0_amd64.deb';
    a.download = 'yordamchi_1.0.0_amd64.deb';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    App.toast('📥 Linux .deb dasturi yuklanmoqda...');
  };

  App.actions.sessiyaKun = function () { App.closeSheet(); App.go('kun'); };

  /* Qo'shish va tahrirlash bitta oyna: `a.id` bo'lsa — tahrirlash. */
  function deadlineSheet(existing) {
    var d = existing || { name: '', start: '', end: '', status: '' };
    var html =
      '<label class="field"><span>Nomi</span><input class="input" id="dl-n" placeholder="Masalan: IELTS" value="' + App.esc(d.name || '') + '"></label>' +
      '<label class="field"><span>Boshlanish</span><input class="input" type="date" id="dl-s" value="' + App.esc(d.start || '') + '"></label>' +
      '<label class="field"><span>Tugash</span><input class="input" type="date" id="dl-e" value="' + App.esc(d.end || '') + '"></label>' +
      (existing
        ? '<label class="list-row" style="cursor:pointer"><div class="li-main"><div class="li-title">Bajarildi</div>' +
          '<div class="li-sub">Belgilansa, ro\'yxatda va grafikda faol deadline sifatida chiqmaydi</div></div>' +
          '<input type="checkbox" id="dl-done" style="width:20px;height:20px;accent-color:var(--success)"' +
          (d.status === 'done' ? ' checked' : '') + '></label>'
        : '') +
      '<button class="btn" id="dl-save">' + (existing ? 'Saqlash' : 'Qo\'shish') + '</button>' +
      (existing
        ? '<button class="btn ghost" id="dl-del" style="margin-top:10px;color:var(--danger);border-color:var(--danger-soft)">O\'chirish</button>'
        : '');
    var sh = App.sheet(html, { title: existing ? d.name : 'Yangi deadline' });
    App.icons(sh);

    sh.querySelector('#dl-save').onclick = function () {
      var n = sh.querySelector('#dl-n').value.trim();
      var s = sh.querySelector('#dl-s').value, e = sh.querySelector('#dl-e').value;
      if (!n || !e) return App.toast('Nomi va tugash sanasi kerak');
      if (s && e && s > e) return App.toast('Boshlanish sanasi tugashdan keyin bo\'lmasin');
      var doneEl = sh.querySelector('#dl-done');
      var arr = dls();
      if (existing) {
        arr = arr.map(function (x) {
          return x.id === existing.id
            ? { id: x.id, name: n, start: s, end: e, status: (doneEl && doneEl.checked) ? 'done' : '' }
            : x;
        });
      } else {
        arr.push({ id: 'dl_' + Date.now(), name: n, start: s, end: e, status: '' });
      }
      saveDls(arr);
      App.closeSheet(); App.toast('✅ Saqlandi'); App.reload();
    };

    var delBtn = sh.querySelector('#dl-del');
    if (delBtn) delBtn.onclick = function () {
      App.confirm('"' + d.name + '" deadline o\'chiriladi.', function () {
        saveDls(dls().filter(function (x) { return x.id !== existing.id; }));
        App.closeSheet(); App.reload();
      }, { danger: true, yes: 'O\'chirish' });
    };
  }

  App.actions.addDeadline = function () { deadlineSheet(null); };
  App.actions.editDeadline = function (a) {
    var d = dls().filter(function (x) { return x.id === a.id; })[0];
    if (d) deadlineSheet(d);
  };
  /* Eslatma: deadline o'chirish `deadlineSheet` ichidagi "O'chirish" tugmasi
     orqali (tasdiqlash bilan) bajariladi. Ilgari shu yerda tasdiqlashsiz
     `delDeadline` action ham turardi — hech qayerdan chaqirilmasdi, shuning
     uchun olib tashlandi (bitta ish uchun ikkita yo'l qolmasin). */

  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function countdownText(target) {
    var now = new Date();
    if (target <= now) return 'Tugadi';
    var y = target.getFullYear() - now.getFullYear();
    var m = target.getMonth() - now.getMonth();
    var d = target.getDate() - now.getDate();
    var h = target.getHours() - now.getHours();
    var mi = target.getMinutes() - now.getMinutes();
    var s = target.getSeconds() - now.getSeconds();
    if (s < 0) { s += 60; mi--; }
    if (mi < 0) { mi += 60; h--; }
    if (h < 0) { h += 24; d--; }
    if (d < 0) { d += new Date(target.getFullYear(), target.getMonth(), 0).getDate(); m--; }
    if (m < 0) { m += 12; y--; }
    return pad2(y) + ':' + pad2(m) + ':' + pad2(d) + ' ' + pad2(h) + ':' + pad2(mi) + ':' + pad2(s);
  }
  function startCountdown(id, target) {
    function tick() {
      var el = document.getElementById('dlc-' + id);
      if (!el) { clearInterval(timer); return; }
      el.textContent = countdownText(target);
    }
    var timer = setInterval(tick, 1000);
    tick();
  }

  function renderDeadlines() {
    var box = App.el('dl-list'); if (!box) return;
    var arr = dls();
    if (!arr.length) { box.innerHTML = '<p class="muted" style="font-size:13px;margin:0 1px 4px">Deadline yo\'q</p>'; return; }
    box.innerHTML = arr.map(function (d) {
      var done = d.status === 'done';
      return '<div class="list-row"' + (done ? ' style="opacity:.55"' : '') + '>' +
        '<div class="li-ic" style="background:' + (done ? 'var(--success)' : 'var(--warn)') + ';color:#3a2a08">' +
        '<span data-icon="' + (done ? 'check' : 'calendar') + '" data-icon-size="15"></span></div>' +
        '<button class="li-main li-btn" data-act="editDeadline" data-arg=\'' + App.arg({ id: d.id }) + '\'>' +
        '<div class="li-title"' + (done ? ' style="text-decoration:line-through"' : '') + '>' + App.esc(d.name) + '</div>' +
        (done
          ? '<div class="li-sub">Bajarildi</div>'
          : '<div class="li-sub dl-count" id="dlc-' + d.id + '"></div>') +
        '</button>' +
        App.dlDates(d) +
        '<button class="icon-btn ghost" style="width:28px;height:28px" data-act="editDeadline" data-arg=\'' + App.arg({ id: d.id }) + '\'><span data-icon="edit" data-icon-size="14"></span></button></div>';
    }).join('');
    App.icons(box);
    // Sanoq faqat bajarilmaganlarida ketadi (bajarilganida matn o'rnini egallagan)
    arr.forEach(function (d) { if (d.status !== 'done') startCountdown(d.id, new Date(d.end)); });
  }


  /* ---------- Favqulodda kirish kodi ----------
     Kod OCHIQ SAQLANMAYDI: bazada faqat bcrypt xeshi turadi. Shuning uchun
     "kodni ko'rsatish" degan narsa yo'q — faqat YANGISINI yasash mumkin va
     u bir marta, aynan shu oynachada ko'rsatiladi. Yo'qotilsa yangisi
     yasaladi, eskisi shu zahoti ishlamay qoladi. */
  /* Favqulodda kirish kodi.

     Kodni EGASI yozadi, tizim yasamaydi. Ilgari aksincha edi va bu
     ishlamadi: tasodifiy kod eslab qolinmasdi, o'sha zahoti ko'chirib
     olinmasa esa butunlay yo'qolardi — favqulodda yo'l aynan kerak
     bo'lgan paytda ochilmasdi.

     Kod yozilayotganda OCHIQ ko'rinadi (yulduzcha bilan berkitilmaydi):
     bu yerga faqat tizimga kirgan egasi tusha oladi, berkitilsa esa
     xato yozib qo'yish ehtimoli ortardi — keyin uni tekshirib
     bo'lmasdi, chunki bazada faqat xesh qoladi. */
  App.actions.accessCode = function () {
    var LEN = 12;
    var sh = App.sheet('<div id="ac-body"><div class="load-wrap"><div class="spinner"></div></div></div>',
      { title: 'Favqulodda kirish kodi' });

    function draw(st) {
      var body = sh.querySelector('#ac-body'); if (!body) return;
      body.innerHTML =
        '<p class="muted" style="font-size:12.5px;margin:0 0 14px;line-height:1.55">' +
        'Bu kod Google ishlamay qolganda kerak: boshqa qurilmada, boshqa domenda ' +
        'yoki Google xizmati uzilganda. Kodni <b>o\'zingiz</b> tanlaysiz — ' +
        'eslab qoladigan, lekin taxmin qilinmaydigan bo\'lsin.</p>' +

        (st.bor
          ? '<div class="list-row" style="padding:10px 1px"><div class="li-main">' +
            '<div class="li-title">Kod o\'rnatilgan</div>' +
            '<div class="li-sub">O\'rnatilgan: ' + App.esc(st.yaratilgan || '—') +
            (st.oxirgi_ishlatilgan ? ' · Oxirgi ishlatilgan: ' + App.esc(st.oxirgi_ishlatilgan) : '') +
            '</div></div></div>'
          : '<div class="list-row" style="padding:10px 1px"><div class="li-main">' +
            '<div class="li-title">Kod o\'rnatilmagan</div>' +
            '<div class="li-sub">Bu yo\'l hozir YOPIQ — faqat Google bilan kiriladi</div>' +
            '</div></div>') +

        '<label class="field" style="margin:14px 0 6px"><span>' +
          (st.bor ? 'Yangi kod' : 'Kod') + ' (' + LEN + ' belgi)</span>' +
        '<input class="input" id="ac-inp" type="text" autocomplete="off" ' +
          'autocapitalize="characters" spellcheck="false" maxlength="24" ' +
          'placeholder="' + LEN + ' ta belgi kiriting" style="letter-spacing:.06em"></label>' +
        '<div class="muted" id="ac-hint" style="font-size:11.5px;margin:0 0 12px">' +
          'Bo\'shliq va chiziqcha hisobga olinmaydi · 0/' + LEN + '</div>' +

        '<button class="btn" id="ac-save" disabled>' +
        (st.bor ? 'Kodni almashtirish' : 'Kodni o\'rnatish') + '</button>' +
        (st.bor
          ? '<button class="btn ghost" id="ac-del" style="margin-top:8px;color:var(--danger)">Kodni o\'chirish</button>'
          : '');

      App.icons(body);

      var inp  = body.querySelector('#ac-inp');
      var hint = body.querySelector('#ac-hint');
      var save = body.querySelector('#ac-save');

      /* Serverdagi `normalize()` bilan AYNAN bir xil qoida: ajratgichlar
         tashlanadi, qolgani katta harfga o'tadi. Sanoq shu qoida bo'yicha
         ko'rsatilmasa, "12 ta yozdim" deb turib server rad etardi. */
      function clean(v) { return String(v || '').toUpperCase().replace(/[\s\-_]/g, ''); }

      function refresh() {
        var c = clean(inp.value);
        var uniq = 0, seen = {};
        for (var i = 0; i < c.length; i++) if (!seen[c[i]]) { seen[c[i]] = 1; uniq++; }
        var okLen = c.length === LEN;
        var okUniq = uniq >= 5;
        save.disabled = !(okLen && okUniq);
        hint.textContent = okLen && !okUniq
          ? 'Juda oddiy: kamida 5 xil belgi bo\'lsin · ' + c.length + '/' + LEN
          : 'Bo\'shliq va chiziqcha hisobga olinmaydi · ' + c.length + '/' + LEN;
        hint.style.color = okLen && !okUniq ? 'var(--danger)' : '';
      }
      inp.oninput = refresh;
      refresh();

      save.onclick = function () {
        var kod = clean(inp.value);
        App.confirm(st.bor
          ? 'Eski kod DARHOL ishlamay qoladi va yangisi o\'rnatiladi. Davom etamizmi?'
          : 'Shu kod o\'rnatilsinmi? Uni eslab qoling — keyin ko\'rsatib bo\'lmaydi.',
          function () {
            App.call('kirish_kodi_ornatish', { kod: kod }).then(function (j) {
              draw(j);
              App.toast('✅ Kod o\'rnatildi');
            }).catch(function (e) { App.toast('⚠️ ' + e.message); });
          });
      };

      var del = body.querySelector('#ac-del');
      if (del) del.onclick = function () {
        App.confirm('Kod o\'chirilsa faqat Google orqali kirish qoladi. Davom etamizmi?', function () {
          App.call('kirish_kodi_ochirish', {}).then(function () {
            draw({ bor: false });
            App.toast('Kod o\'chirildi');
          }).catch(function (e) { App.toast('⚠️ ' + e.message); });
        }, { danger: true, yes: 'O\'chirish' });
      };
    }

    App.call('kirish_kodi_holati', {}).then(function (j) { draw(j); })
      .catch(function (e) {
        var b = sh.querySelector('#ac-body');
        if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: e.message });
      });
  };

  /* Lug'at qulfi. Ro'yxat QO'LDA yozilmaydi — `WordLock` uni lentaga
     yuklangan kategoriyalardan o'rganadi, ya'ni yangi bo'lim qo'shilsa
     shu yerda o'zi paydo bo'ladi.

     Boshlang'ich ochiq bo'lim (1-1000 va ОСНОВНЫЕ ПОНЯТИЯ) yopilmaydi:
     hammasi yopilsa foydalanuvchi o'zini butunlay tashqarida qoldirardi. */
  App.actions.vocabLock = function () {
    if (!window.WordLock) return;
    var units = WordLock.units();

    if (!units.length) {
      App.sheet('<p class="muted" style="margin:0;font-size:13px">Lug\'at hali yuklanmadi. ' +
        'Bosh sahifani bir marta oching va qaytib keling.</p>', { title: 'Lug\'at qulfi' });
      return;
    }

    var byRoot = {}, roots = [];
    units.forEach(function (u) {
      if (!byRoot[u.root]) { byRoot[u.root] = []; roots.push(u.root); }
      byRoot[u.root].push(u);
    });

    var html =
      '<p class="muted" style="margin:0 0 12px;font-size:13px;line-height:1.5">' +
      'Qulflangan bo\'lim lentada, qidiruvda va mashqlarda chiqmaydi. ' +
      'Bir vaqtda kam bo\'lim ochiq tursa, diqqat tarqalmaydi.</p>';

    roots.forEach(function (r) {
      html += '<div class="list-label">' + App.esc(r) + '</div>';
      byRoot[r].sort(function (a, b) { return a.name.localeCompare(b.name, 'ru'); });
      byRoot[r].forEach(function (u) {
        var fixed = WordLock.isFixedOpen(u.path);
        html +=
          '<label class="list-row" style="cursor:pointer">' +
          '<span class="li-ic" style="background:' + (u.locked ? '#94a3b822' : '#10b98122') +
            ';color:' + (u.locked ? '#94a3b8' : '#10b981') + '" data-icon="' +
            (u.locked ? 'lock' : 'check') + '" data-icon-size="15"></span>' +
          '<span class="li-main"><span class="li-title">' + App.esc(u.name) + '</span>' +
          '<span class="li-sub">' + u.words + ' so\'z' +
          (fixed ? ' · doim ochiq' : '') + '</span></span>' +
          '<input type="checkbox" class="vl-chk" data-path="' + App.esc(u.path) + '"' +
          (u.locked ? '' : ' checked') + (fixed ? ' disabled' : '') + '>' +
          '</label>';
      });
    });

    html += '<button class="btn" id="vl-save" style="margin-top:14px">Saqlash</button>';

    var sh = App.sheet(html, { title: 'Lug\'at qulfi' });
    App.icons(sh);
    var btn = sh.querySelector('#vl-save');
    if (btn) btn.onclick = function () {
      sh.querySelectorAll('.vl-chk').forEach(function (c) {
        if (c.disabled) return;
        WordLock.setOpen(c.getAttribute('data-path'), c.checked);
      });
      /* Havza ilova ochilganda bir marta yig'iladi — o'zgarish ko'rinishi
         uchun sahifani qaytadan yuklaymiz. Bu kamdan-kam bo'ladigan amal. */
      location.reload();
    };
  };

  /* ================= FOYDALANUVCHILAR VA RUXSATLAR =================
     Admin Google akkauntlarni kiritib, tizimga ruxsat beradi.
     Har bir foydalanuvchiga qaysi bo'limlar ko'rinishi alohida belgilanadi.
     Default bo'limlar: bosh sahifa, testlar, learn, statistika.
     Qo'shimcha foydalanuvchilarda bosh sahifadagi o'ng tortma butunlay
     ko'rinmaydi va Learnda hech narsani tahrirlay olmaydi (faqat o'qish). */
  var USER_AVAILABLE_SECTIONS = [
    { key: 'home', title: 'Bosh sahifa', desc: 'Bosh sahifa va umumiy lenta', icon: 'home' },
    { key: 'fanlar', title: 'Testlar', desc: 'Fanlar va test savollari', icon: 'book' },
    { key: 'languages', title: 'Learn', desc: 'Lug\'at va grammatika (read-only)', icon: 'globe' },
    { key: 'stats', title: 'Statistika', desc: 'Natijalar va o\'zlashtirish grafigi', icon: 'chart' },
    { key: 'kun', title: 'Kun tartibi', desc: 'Kunlik reja va vazifalar', icon: 'calendar' },
    { key: 'sport', title: 'Sport', desc: 'Mashqlar va jismoniy hisob', icon: 'trophy' },
    { key: 'coding', title: 'Coding', desc: 'Dasturlash darslari va konsol', icon: 'code' },
    { key: 'goals', title: 'Maqsadlar', desc: 'Maqsad va yutuqlar', icon: 'check' },
    { key: 'tarix', title: 'Tarix', desc: 'Test natijalari tarixi', icon: 'clock' },
    { key: 'boost', title: 'Boostday', desc: 'Rag\'batlantirish va eslatmalar', icon: 'message' },
    { key: 'arxiv', title: 'Arxiv', desc: 'Arxivlangan materiallar', icon: 'archive' },
    { key: 'qoidalar', title: 'Qoidalar', desc: 'Qoidalar va qo\'llanmalar', icon: 'file' }
  ];
  var DEFAULT_USER_SECTIONS = ['home', 'fanlar', 'languages', 'stats'];

  App.actions.manageUsers = function () {
    var sh = App.sheet(
      '<div id="users-modal-body">' +
        '<div class="load-wrap"><div class="spinner"></div></div>' +
      '</div>',
      { title: 'Foydalanuvchilar (Ruxsatlar)', cls: 'wide-sheet' }
    );

    var usersList = [];

    function sectionTitle(key) {
      for (var i = 0; i < USER_AVAILABLE_SECTIONS.length; i++) {
        if (USER_AVAILABLE_SECTIONS[i].key === key) return USER_AVAILABLE_SECTIONS[i].title;
      }
      return key;
    }

    function renderList() {
      var body = sh.querySelector('#users-modal-body');
      if (!body) return;

      var html =
        '<div class="user-list-top">' +
          '<p class="muted" style="margin:0 0 12px;font-size:12.5px;line-height:1.5">' +
            'Google hisobi kiritilgan foydalanuvchilar saytga kira oladi. ' +
            'Har bir foydalanuvchi qaysi bo\'limlarni ko\'rishi mumkinligini quyida sozlang.' +
          '</p>' +
          '<div style="margin-bottom:14px;display:flex;justify-content:flex-end">' +
            '<button class="btn sm" id="btn-open-add-user" style="display:inline-flex;align-items:center;gap:6px">' +
              '<span data-icon="plus" data-icon-size="14"></span> Yangi foydalanuvchi qo\'shish' +
            '</button>' +
          '</div>' +
        '</div>';

      if (!usersList.length) {
        html +=
          '<div class="empty-state" style="padding:32px 16px;text-align:center;background:var(--bg-card);border:1px dashed var(--border);border-radius:14px;margin-bottom:12px">' +
            '<div style="margin-bottom:10px"><span data-icon="users" data-icon-size="36" style="opacity:0.35"></span></div>' +
            '<div style="font-weight:700;font-size:14.5px;margin-bottom:6px">Qo\'shimcha foydalanuvchilar yo\'q</div>' +
            '<div class="muted" style="font-size:12.5px;line-height:1.5;max-width:320px;margin:0 auto 16px">' +
              'Yangi foydalanuvchi qo\'shsangiz, ular o\'z Google hisoblari orqali saytga kira oladi.' +
            '</div>' +
            '<button class="btn sm" id="btn-empty-add-user">+ Foydalanuvchi qo\'shish</button>' +
          '</div>';
      } else {
        html += '<div class="user-list-items">';
        usersList.forEach(function (u) {
          var initial = (u.ism && u.ism.trim() ? u.ism.trim()[0] : (u.email ? u.email[0] : 'U')).toUpperCase();
          var rux = Array.isArray(u.ruxsatlar) ? u.ruxsatlar : [];
          var isFaol = u.holat !== 'nofaol';

          html +=
            '<div class="user-item-card" data-id="' + u.id + '">' +
              '<div class="user-item-header">' +
                '<div class="user-item-avatar">' + App.esc(initial) + '</div>' +
                '<div class="user-item-meta">' +
                  '<div class="user-item-email">' + App.esc(u.email) + '</div>' +
                  (u.ism ? '<div class="user-item-ism">' + App.esc(u.ism) + '</div>' : '') +
                '</div>' +
                '<div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap">' +
                  '<span class="user-status-pill ' + (isFaol ? 'faol' : 'nofaol') + '">' +
                    (isFaol ? 'Faol' : 'Nofaol') +
                  '</span>' +
                  (u.kod_bor ? '<span class="user-status-pill" style="background:rgba(16,185,129,0.12);color:var(--success,#10b981);border:1px solid rgba(16,185,129,0.25)" title="12 belgilik favqulodda kod o\'rnatilgan">🔐 Kod bor</span>' : '') +
                '</div>' +
                '<div class="user-actions">' +
                  '<button class="user-btn-icon u-btn-edit" data-id="' + u.id + '" title="Tahrirlash">' +
                    '<span data-icon="edit" data-icon-size="14"></span>' +
                  '</button>' +
                  '<button class="user-btn-icon danger u-btn-delete" data-id="' + u.id + '" title="O\'chirish">' +
                    '<span data-icon="trash" data-icon-size="14"></span>' +
                  '</button>' +
                '</div>' +
              '</div>' +
              '<div class="user-perms-row">' +
                '<span class="muted" style="font-size:11px;font-weight:600;margin-right:2px">Bo\'limlar (' + rux.length + ' ta):</span>' +
                rux.map(function (k) {
                  return '<span class="user-perm-badge">' + App.esc(sectionTitle(k)) + '</span>';
                }).join('') +
              '</div>' +
              '<div class="muted" style="font-size:11px;border-top:1px solid var(--border);padding-top:6px;margin-top:2px">' +
                '🛡️ Bosh sahifa tortmasi yopiq · Learnda tahrirlash cheklangan' +
              '</div>' +
            '</div>';
        });
        html += '</div>';
      }

      body.innerHTML = html;
      App.icons(body);

      var btnAdd = body.querySelector('#btn-open-add-user');
      if (btnAdd) btnAdd.onclick = function () { renderForm(null); };
      var btnEmptyAdd = body.querySelector('#btn-empty-add-user');
      if (btnEmptyAdd) btnEmptyAdd.onclick = function () { renderForm(null); };

      body.querySelectorAll('.u-btn-edit').forEach(function (b) {
        b.onclick = function () {
          var id = parseInt(b.getAttribute('data-id'), 10);
          var found = null;
          for (var i = 0; i < usersList.length; i++) {
            if (usersList[i].id === id) { found = usersList[i]; break; }
          }
          if (found) renderForm(found);
        };
      });

      body.querySelectorAll('.u-btn-delete').forEach(function (b) {
        b.onclick = function () {
          var id = parseInt(b.getAttribute('data-id'), 10);
          var found = null;
          for (var i = 0; i < usersList.length; i++) {
            if (usersList[i].id === id) { found = usersList[i]; break; }
          }
          if (!found) return;
          App.confirm(
            '<b>' + App.esc(found.email) + '</b> akkauntini o\'chirishni tasdiqlaysizmi?<br>U boshqa tizimga kira olmaydi.',
            function () {
              App.call('user_delete', { id: id })
                .then(function () {
                  App.toast('✅ Foydalanuvchi o\'chirildi');
                  loadUsers();
                })
                .catch(function (err) {
                  App.toast('⚠️ ' + err.message);
                });
            },
            { danger: true, yes: 'O\'chirish' }
          );
        };
      });
    }

    function renderForm(user) {
      var body = sh.querySelector('#users-modal-body');
      if (!body) return;

      var isEdit = !!user;
      var curRuxsatlar = isEdit && Array.isArray(user.ruxsatlar) ? user.ruxsatlar.slice() : DEFAULT_USER_SECTIONS.slice();

      var html =
        '<div class="user-form-top" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px">' +
          '<button class="btn ghost sm" id="u-form-back" style="display:inline-flex;align-items:center;gap:5px;padding:4px 8px">' +
            '<span data-icon="arrowLeft" data-icon-size="14"></span> Ro\'yxat' +
          '</button>' +
          '<span style="font-weight:700;font-size:14px">' +
            (isEdit ? 'Foydalanuvchini tahrirlash' : 'Yangi foydalanuvchi') +
          '</span>' +
          '<span style="width:60px"></span>' +
        '</div>' +

        '<label class="field"><span>Google Email (majburiy)</span>' +
          '<input class="input" id="u-inp-email" type="email" autocomplete="off" spellcheck="false" ' +
          'placeholder="masalan: user@gmail.com" value="' + App.esc(user ? user.email : '') + '" ' +
          (isEdit ? 'readonly style="opacity:0.7;cursor:not-allowed"' : '') + '>' +
        '</label>' +

        '<label class="field"><span>Ism yoki izoh (ixtiyoriy)</span>' +
          '<input class="input" id="u-inp-ism" type="text" placeholder="Foydalanuvchi ismi" value="' +
          App.esc(user && user.ism ? user.ism : '') + '">' +
        '</label>' +

        '<label class="field">' +
          '<span style="display:flex;justify-content:space-between;align-items:center">' +
            '<span>Favqulodda kirish kodi (12 ta belgi)</span>' +
            '<button type="button" class="btn ghost sm" id="btn-gen-user-code" style="font-size:11px;padding:2px 6px">' +
              '🎲 Tasodifiy yaratish' +
            '</button>' +
          '</span>' +
          '<div style="position:relative">' +
            '<input class="input" id="u-inp-code" type="text" maxlength="14" spellcheck="false" autocomplete="off" ' +
              'style="font-family:monospace;letter-spacing:1.5px;font-weight:700;text-transform:uppercase" ' +
              'placeholder="XXXX-XXXX-XXXX" value="">' +
            '<span class="muted" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:11px" id="u-code-len-hint">' +
              '0/12' +
            '</span>' +
          '</div>' +
          '<small class="muted" style="font-size:11px;line-height:1.4;margin-top:4px;display:block">' +
            'Google orqali kirmay qolgan vaziyatda foydalanuvchi ushbu maxfiy kod orqali tizimga kira oladi. ' +
            (isEdit ? (user.kod_bor ? '(Hozir kod o\'rnatilgan. O\'zgartirmaslik uchun bo\'sh qoldiring)' : '(Hozir kod o\'rnatilmagan)') : '(Kiritish ixtiyoriy)') +
          '</small>' +
        '</label>' +

        (isEdit ?
          '<label class="field"><span>Holat</span>' +
            '<select class="input" id="u-inp-holat">' +
              '<option value="faol" ' + (user.holat !== 'nofaol' ? 'selected' : '') + '>Faol (kirish ruxsat etilgan)</option>' +
              '<option value="nofaol" ' + (user.holat === 'nofaol' ? 'selected' : '') + '>Nofaol (kirish bloklangan)</option>' +
            '</select>' +
          '</label>' : '') +

        '<div class="between" style="margin:16px 0 6px">' +
          '<span style="font-weight:700;font-size:13px">Ko\'rinadigan bo\'limlar:</span>' +
          '<div style="display:flex;gap:6px">' +
            '<button type="button" class="btn ghost sm" id="btn-preset-default" style="font-size:11px;padding:2px 8px">Default (4 ta)</button>' +
            '<button type="button" class="btn ghost sm" id="btn-preset-all" style="font-size:11px;padding:2px 8px">Barchasi</button>' +
          '</div>' +
        '</div>' +

        '<div class="user-perm-hint" style="background:var(--accent-soft, rgba(99,102,241,0.08));border:1px solid rgba(99,102,241,0.2);border-radius:10px;padding:9px 12px;font-size:11.5px;line-height:1.45;margin-bottom:12px;color:var(--text)">' +
          '📌 <b>Standart:</b> Bosh sahifa, Testlar, Learn, Statistika.<br>' +
          '🔒 <b>Qat\'iy cheklov:</b> Bosh sahifadagi o\'ng tortma ko\'rinmaydi va Learnda hech qanday narsani yarata/tahrirlay olmaydi (faqat tayyoridan foydalanadi).' +
        '</div>' +

        '<div class="user-sections-grid" id="u-sec-grid">' +
          USER_AVAILABLE_SECTIONS.map(function (s) {
            var checked = curRuxsatlar.indexOf(s.key) >= 0;
            return (
              '<div class="user-sec-card ' + (checked ? 'active' : '') + '" data-key="' + s.key + '">' +
                '<span class="u-sec-check-icon"><span data-icon="check" data-icon-size="12"></span></span>' +
                '<div class="u-sec-info">' +
                  '<div class="u-sec-name"><span data-icon="' + s.icon + '" data-icon-size="13" style="margin-right:5px"></span>' + App.esc(s.title) + '</div>' +
                  '<div class="u-sec-desc">' + App.esc(s.desc) + '</div>' +
                '</div>' +
              '</div>'
            );
          }).join('') +
        '</div>' +

        '<div style="display:flex;gap:10px;margin-top:16px">' +
          '<button class="btn sec" id="u-form-cancel" style="flex:1">Bekor qilish</button>' +
          '<button class="btn" id="u-form-save" style="flex:2"><span data-icon="check" data-icon-size="15"></span> Saqlash</button>' +
        '</div>';

      body.innerHTML = html;
      App.icons(body);

      var codeInp = body.querySelector('#u-inp-code');
      var codeHint = body.querySelector('#u-code-len-hint');
      var btnGen = body.querySelector('#btn-gen-user-code');

      function formatCodeString(val) {
        var raw = (val || '').replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 12);
        var parts = [];
        for (var i = 0; i < raw.length; i += 4) {
          parts.push(raw.slice(i, i + 4));
        }
        return parts.join('-');
      }

      if (codeInp) {
        codeInp.oninput = function () {
          var raw = codeInp.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 12);
          codeInp.value = formatCodeString(raw);
          if (codeHint) codeHint.textContent = raw.length + '/12';
        };
      }

      if (btnGen) {
        btnGen.onclick = function () {
          var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
          var gen = '';
          for (var i = 0; i < 12; i++) {
            gen += chars.charAt(Math.floor(Math.random() * chars.length));
          }
          if (codeInp) {
            codeInp.value = formatCodeString(gen);
            if (codeHint) codeHint.textContent = '12/12';
          }
        };
      }

      var grid = body.querySelector('#u-sec-grid');
      grid.querySelectorAll('.user-sec-card').forEach(function (card) {
        card.onclick = function () {
          var k = card.getAttribute('data-key');
          var idx = curRuxsatlar.indexOf(k);
          if (idx >= 0) {
            curRuxsatlar.splice(idx, 1);
            card.classList.remove('active');
          } else {
            curRuxsatlar.push(k);
            card.classList.add('active');
          }
        };
      });

      var btnPresetDef = body.querySelector('#btn-preset-default');
      if (btnPresetDef) {
        btnPresetDef.onclick = function () {
          curRuxsatlar = DEFAULT_USER_SECTIONS.slice();
          grid.querySelectorAll('.user-sec-card').forEach(function (c) {
            var k = c.getAttribute('data-key');
            if (curRuxsatlar.indexOf(k) >= 0) c.classList.add('active');
            else c.classList.remove('active');
          });
        };
      }

      var btnPresetAll = body.querySelector('#btn-preset-all');
      if (btnPresetAll) {
        btnPresetAll.onclick = function () {
          curRuxsatlar = USER_AVAILABLE_SECTIONS.map(function (s) { return s.key; });
          grid.querySelectorAll('.user-sec-card').forEach(function (c) {
            c.classList.add('active');
          });
        };
      }

      var btnBack = body.querySelector('#u-form-back');
      if (btnBack) btnBack.onclick = function () { renderList(); };
      var btnCancel = body.querySelector('#u-form-cancel');
      if (btnCancel) btnCancel.onclick = function () { renderList(); };

      var btnSave = body.querySelector('#u-form-save');
      if (btnSave) {
        btnSave.onclick = function () {
          var emailInp = body.querySelector('#u-inp-email');
          var ismInp = body.querySelector('#u-inp-ism');
          var holatInp = body.querySelector('#u-inp-holat');

          var email = (emailInp ? emailInp.value : '').trim().toLowerCase();
          var ism = (ismInp ? ismInp.value : '').trim();
          var holat = holatInp ? holatInp.value : 'faol';
          var rawCode = (codeInp ? codeInp.value : '').replace(/[^A-Za-z0-9]/g, '').toUpperCase();

          if (!email) {
            App.toast('⚠️ Google emailini kiriting');
            if (emailInp) emailInp.focus();
            return;
          }
          if (email.indexOf('@') <= 0 || email.indexOf('.') <= 0) {
            App.toast('⚠️ To\'g\'ri email kiriting');
            if (emailInp) emailInp.focus();
            return;
          }
          if (rawCode && rawCode.length !== 12) {
            App.toast('⚠️ Favqulodda kod roppa-rosa 12 ta belgi bo\'lishi kerak');
            if (codeInp) codeInp.focus();
            return;
          }
          if (!curRuxsatlar.length) {
            App.toast('⚠️ Kamida 1 ta bo\'limni tanlang');
            return;
          }

          btnSave.disabled = true;

          if (isEdit) {
            var payload = {
              id: user.id,
              ism: ism,
              holat: holat,
              ruxsatlar: curRuxsatlar
            };
            if (rawCode) {
              payload.kirish_kodi = rawCode;
            }
            App.call('user_update', payload)
            .then(function () {
              App.toast('✅ Foydalanuvchi ma\'lumotlari saqlandi');
              loadUsers();
            })
            .catch(function (err) {
              App.toast('⚠️ ' + err.message);
              btnSave.disabled = false;
            });
          } else {
            var addPayload = {
              email: email,
              ism: ism,
              ruxsatlar: curRuxsatlar
            };
            if (rawCode) {
              addPayload.kirish_kodi = rawCode;
            }
            App.call('user_add', addPayload)
            .then(function () {
              App.toast('✅ Foydalanuvchi muvaffaqiyatli qo\'shildi');
              loadUsers();
            })
            .catch(function (err) {
              App.toast('⚠️ ' + err.message);
              btnSave.disabled = false;
            });
          }
        };
      }
    }

    function loadUsers() {
      var body = sh.querySelector('#users-modal-body');
      if (body) body.innerHTML = '<div class="load-wrap"><div class="spinner"></div></div>';
      App.call('users_list', {})
        .then(function (res) {
          usersList = (res && res.users) || [];
          renderList();
        })
        .catch(function (err) {
          var b = sh.querySelector('#users-modal-body');
          if (b) b.innerHTML = App.empty({ icon: 'alert', title: 'Xatolik', text: err.message });
        });
    }

    loadUsers();
  };

})();
