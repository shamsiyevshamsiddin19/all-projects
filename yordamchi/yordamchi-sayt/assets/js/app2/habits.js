/* Kunlik odatlar — har kuni belgilangan VAQTDA takrorlanadigan shaxsiy ishlar.
 *
 * Masalan: 22:00 yuz yuvish, 23:00 tish yuvish, juft kunlari cho'milish.
 *
 * MA'LUMOT BOT BAZASIDA turadi (`/boost/api` proxysi orqali), chunki:
 *   - eslatmalarni ("1 soat qoldi", "vaqti bo'ldi") BOT yuboradi
 *   - kunlik Boostday xabariga ham BOT qo'shadi
 * Shu sabab ro'yxat bitta joyda — sayt va bot hech qachon ajralib qolmaydi.
 *
 * Bosh sahifadagi "Kunlik statistika" panelining CHAP YUQORI burchagida
 * kichik halqa turadi (home.js chizadi, `Habits.ringHtml()` beradi) —
 * bosilsa shu bo'lim ochiladi.
 */
(function () {
  'use strict';

  var H = { items: null, modes: null, loading: null };

  function call(action, payload) {
    return App.call('boost_' + action, payload || {});
  }

  function load(force) {
    if (H.items && !force) return Promise.resolve(H.items);
    if (H.loading && !force) return H.loading;
    H.loading = call('habits_list').then(function (j) {
      H.items = j.habits || [];
      H.modes = j.modes || [];
      H.loading = null;
      return H.items;
    }).catch(function (e) {
      H.loading = null;
      throw e;
    });
    return H.loading;
  }

  /* Bugun bajarilishi kerak bo'lganlar */
  function todayItems(list) {
    return (list || H.items || []).filter(function (x) { return x.today; });
  }

  function stat(list) {
    var t = todayItems(list);
    var done = t.filter(function (x) { return x.done; }).length;
    return { done: done, total: t.length, pct: t.length ? Math.round((done / t.length) * 100) : 0 };
  }

  /* ---------- Bosh sahifadagi kichik halqa ---------- */
  function ringHtml(st) {
    var size = 54, stroke = 9;                    // 100 birlikli viewBox
    var r = (100 - stroke) / 2, c = 2 * Math.PI * r;
    var on = Math.max(0, Math.min(100, st.pct)) / 100 * c;
    return '<button class="hb-ring" data-act="go" data-arg=\'' + App.arg({ v: 'habits' }) + '\'' +
      ' aria-label="Kunlik odatlar">' +
      '<span class="hb-ring-svg">' +
      '<svg viewBox="0 0 100 100">' +
      '<circle cx="50" cy="50" r="' + r + '" fill="none" stroke="var(--border)" stroke-width="' + stroke + '"></circle>' +
      '<circle cx="50" cy="50" r="' + r + '" fill="none" stroke="var(--teal)" stroke-width="' + stroke +
      '" stroke-linecap="round" stroke-dasharray="' + on.toFixed(1) + ' ' + c.toFixed(1) + '"></circle>' +
      '</svg>' +
      '<span class="hb-ring-mid">' + st.pct + '%</span></span>' +
      '<span class="hb-ring-lbl">Odatlar</span>' +
      '<span class="hb-ring-val">' + st.done + '/' + st.total + '</span>' +
      '</button>';
  }

  /* ---------- Ro'yxat sahifasi ---------- */
  var MODE_ORDER = ['everyday', 'odd', 'even', 'weekday', 'weekend'];
  var MODE_NAME = {
    everyday: 'Har kuni', odd: 'Toq kunlari', even: 'Juft kunlari',
    weekday: 'Ish kunlari', weekend: 'Dam olish kunlari'
  };

  App.view('habits', {
    nav: 'home',
    render: function (page) {
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"home"}\'>' +
        '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>Kunlik odatlar</h1>' +
        '<button class="icon-btn ghost" data-act="hbNew" aria-label="Qo\'shish">' +
        '<span data-icon="plus" data-icon-size="20"></span></button></div>' +
        '<div id="hb-body"><div class="load-wrap"><div class="spinner"></div></div></div>';
      App.icons(page);
      paint(true);
    }
  });

  function paint(force) {
    load(force).then(function (list) {
      var box = App.el('hb-body'); if (!box) return;
      if (!list.length) {
        box.innerHTML = App.empty({
          icon: 'clock', title: 'Odat yo\'q',
          text: 'Tepadagi + tugmasi bilan qo\'shing. Masalan: 22:00 — yuzni yuvish.'
        });
        App.icons(box);
        return;
      }

      var st = stat(list);
      var html =
        '<div class="hb-top">' +
        '<div class="hb-top-n"><b>' + st.done + ' / ' + st.total + '</b><span>bugun bajarildi</span></div>' +
        '<div class="hb-bar"><i style="width:' + st.pct + '%"></i></div>' +
        '</div>' +
        '<div id="hb-push"></div>';

      MODE_ORDER.forEach(function (m) {
        var group = list.filter(function (x) { return x.week_mode === m; });
        if (!group.length) return;
        html += '<div class="list-label">' + App.esc(MODE_NAME[m] || m) + '</div>';
        html += group.map(function (h) {
          var off = !h.is_active;
          return '<div class="hb-row' + (h.done ? ' done' : '') + (off ? ' off' : '') + '">' +
            '<button class="hb-check" data-act="hbToggle" data-arg=\'' + App.arg({ id: h.id }) + '\'' +
            (h.today ? '' : ' disabled') + ' aria-label="Belgilash">' +
            (h.done ? '<span data-icon="check" data-icon-size="14"></span>' : '') + '</button>' +
            '<button class="hb-main" data-act="hbEdit" data-arg=\'' + App.arg({ id: h.id }) + '\'>' +
            '<span class="hb-t">' + App.esc(h.time) + '</span>' +
            '<span class="hb-n">' + App.esc(h.name) + '</span>' +
            (h.note ? '<span class="hb-note">' + App.esc(h.note) + '</span>' : '') +
            '<span class="hb-sub">' + App.esc(remindText(h.remind)) +
            (off ? ' · o\'chirilgan' : (h.today ? '' : ' · bugun emas')) + '</span>' +
            '</button></div>';
        }).join('');
      });

      box.innerHTML = html;
      App.icons(box);
      paintPush();
    }).catch(function (e) {
      var box = App.el('hb-body'); if (!box) return;
      box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
      App.icons(box);
    });
  }

  /* Telefon bildirishnomasi holati — Kunlik odatlar sahifasining tepasida.
     Yoqilmagan bo'lsa eslatmalar Telegram orqali keladi (zaxira yo'l),
     shuning uchun holatni ochiq ko'rsatib turamiz. */
  function paintPush() {
    var box = App.el('hb-push'); if (!box || !window.Push) return;
    if (!Push.supported()) {
      box.innerHTML = '<div class="hb-push warn">Bu brauzer telefon bildirishnomasini qo\'llamaydi. ' +
        'Eslatmalar Telegram orqali keladi.</div>';
      return;
    }
    if (Push.state() === 'denied') {
      box.innerHTML = '<div class="hb-push warn">Bildirishnoma <b>bloklangan</b>. ' +
        'Brauzer sozlamalaridan shu sayt uchun ruxsat bering, keyin qayta yoqing.</div>';
      return;
    }
    Push.currentSub().then(function (sub) {
      var b = App.el('hb-push'); if (!b) return;
      if (sub && Push.state() === 'granted') {
        b.innerHTML = '<div class="hb-push on">' +
          '<span data-icon="bell" data-icon-size="15"></span>' +
          '<div>Telefon bildirishnomasi <b>yoqilgan</b></div>' +
          '<button class="chip-btn" data-act="pushTest">Sinash</button>' +
          '<button class="chip-btn" data-act="pushDisable">O\'chirish</button></div>';
      } else {
        b.innerHTML = '<div class="hb-push">' +
          '<span data-icon="bell" data-icon-size="15"></span>' +
          '<div>Eslatmalar telefonga bildirishnoma bo\'lib kelsin</div>' +
          '<button class="chip-btn active" data-act="pushEnable">Yoqish</button></div>';
      }
      App.icons(b);
    }).catch(function () {});
  }
  window.PushUI = { repaint: paintPush };

  function remindText(remind) {
    var parts = String(remind || '').split(',').filter(Boolean);
    if (!parts.length) return 'Eslatmasiz';
    return parts.map(function (m) {
      m = parseInt(m, 10);
      return m >= 60 ? (m / 60) + ' soat' : m + ' daq';
    }).join(' · ') + ' oldin';
  }

  /* ---------- Qo'shish / tahrirlash ---------- */
  var REMIND_CHOICES = [60, 30, 15, 5];

  function formHtml(h) {
    h = h || {};
    var sel = String(h.remind || '60,30,15,5').split(',');
    return '<label class="field"><span>Nomi</span>' +
      '<input class="input" id="hb-name" placeholder="Masalan: Tishni yuvish" value="' +
      App.esc(h.name || '') + '"></label>' +
      '<div class="flex" style="gap:10px">' +
      '<label class="field" style="flex:1"><span>Vaqti</span>' +
      '<input class="input" type="time" id="hb-time" value="' + App.esc(h.time || '22:00') + '"></label>' +
      '<label class="field" style="flex:1.3"><span>Qaysi kunlar</span>' +
      '<select class="input" id="hb-mode">' +
      MODE_ORDER.map(function (m) {
        return '<option value="' + m + '"' + ((h.week_mode || 'everyday') === m ? ' selected' : '') +
          '>' + MODE_NAME[m] + '</option>';
      }).join('') + '</select></label></div>' +
      '<label class="field"><span>Izoh (ixtiyoriy)</span>' +
      '<input class="input" id="hb-note" placeholder="Masalan: maxsus krem surtish" value="' +
      App.esc(h.note || '') + '"></label>' +
      '<div class="list-label" style="margin-top:4px">Ogohlantirish (necha oldin)</div>' +
      '<div class="flex" id="hb-remind" style="gap:7px;flex-wrap:wrap;margin-bottom:14px">' +
      REMIND_CHOICES.map(function (m) {
        var on = sel.indexOf(String(m)) >= 0;
        return '<button type="button" class="chip-btn hb-rm' + (on ? ' active' : '') +
          '" data-m="' + m + '">' + (m >= 60 ? (m / 60) + ' soat' : m + ' daq') + '</button>';
      }).join('') + '</div>' +
      (h.id ? '<button class="btn sec" id="hb-del" style="margin-bottom:8px">O\'chirish</button>' : '') +
      '<button class="btn" id="hb-save">Saqlash</button>';
  }

  function openForm(h) {
    var sh = App.sheet(formHtml(h), { title: h && h.id ? 'Odatni tahrirlash' : 'Yangi odat' });
    App.icons(sh);

    sh.querySelectorAll('.hb-rm').forEach(function (b) {
      b.onclick = function () { b.classList.toggle('active'); };
    });

    sh.querySelector('#hb-save').onclick = function () {
      var name = sh.querySelector('#hb-name').value.trim();
      if (!name) return App.toast('Nomini kiriting');
      var remind = Array.prototype.slice.call(sh.querySelectorAll('.hb-rm.active'))
        .map(function (b) { return b.getAttribute('data-m'); }).join(',');
      call('habits_save', {
        id: (h && h.id) || 0, name: name,
        time: sh.querySelector('#hb-time').value || '22:00',
        week_mode: sh.querySelector('#hb-mode').value,
        note: sh.querySelector('#hb-note').value.trim(),
        remind: remind
      }).then(function (j) {
        H.items = j.habits || H.items;
        App.closeSheet(); App.toast('✅ Saqlandi'); paint(true);
      }).catch(function (e) { App.toast('⚠️ ' + e.message); });
    };

    var del = sh.querySelector('#hb-del');
    if (del) del.onclick = function () {
      App.confirm('"' + h.name + '" o\'chirilsinmi?', function () {
        call('habits_delete', { id: h.id }).then(function (j) {
          H.items = j.habits || H.items;
          App.closeSheet(); App.toast('O\'chirildi'); paint(true);
        }).catch(function (e) { App.toast('⚠️ ' + e.message); });
      });
    };
  }

  App.actions.hbNew = function () { openForm(null); };
  App.actions.hbEdit = function (a) {
    var h = (H.items || []).find(function (x) { return String(x.id) === String(a.id); });
    if (h) openForm(h);
  };
  App.actions.hbToggle = function (a) {
    call('habits_toggle', { id: a.id }).then(function (j) {
      H.items = j.habits || H.items;
      paint(false);
      if (window.Home && Home.refreshHabits) Home.refreshHabits();
    }).catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  window.Habits = {
    load: load, stat: stat, ringHtml: ringHtml,
    ensureLoaded: function () { return load(false); }
  };
})();
