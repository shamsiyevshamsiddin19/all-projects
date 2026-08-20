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
        '<div class="topbar" style="margin:-16px -15px 6px">' +
        '<div style="display:flex;align-items:center;gap:9px;flex:1;min-width:0">' +
        '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:28px;height:28px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
        '<h1>Sozlamalar</h1></div></div>' +

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
          App.toast('⏳ Baza tiklanmoqda, iltimos kuting...');
          var fd = new FormData();
          fd.append('file', f);
          fetch('/api?action=db_import', {
            method: 'POST',
            body: fd
          })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.success) {
              App.toast('✅ Ma\'lumotlar bazasi muvaffaqiyatli tiklandi!');
              setTimeout(function () { App.reload(); }, 1200);
            } else {
              App.toast('❌ Xatolik: ' + (res.error || 'Tiklab bo\'lmadi'));
            }
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
})();
