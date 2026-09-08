/* Mashqlar > Listening — raqam/harf/ism/telefon eshitib yozish (TTS orqali), Ingliz va Rus tili. */
(function () {
  'use strict';

  var CFG = {
    english: {
      title: 'Listening', ttsLang: 'en-US',
      topics: [
        { v: '1-10', n: 'Raqamlar (1-10)' }, { v: '1-100', n: 'Raqamlar (1-100)' }, { v: '100-2100', n: 'Raqamlar (100-2100)' },
        { v: 'az', n: 'Harflar (A-Z)' }, { v: 'vowels', n: 'Unli harflar' }, { v: 'tel', n: 'Telefon raqam' }, { v: 'name', n: 'Ismlar' },
        { v: 'time', n: 'Vaqt (soat)' }, { v: 'date', n: 'Sanalar' }, { v: 'money', n: 'Pul summasi' }
      ],
      alphabet: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', vowels: 'AEIOU',
      names: ['John', 'Mike', 'Sarah', 'Emily', 'Tom', 'David', 'Anna', 'Bob', 'Lisa', 'Alex', 'Mark', 'Kate'],
      cleanRe: /[^a-z0-9]/g,
      introName: 'Listen to the name', introTel: 'Listen to the phone number',
      phoneGen: function () {
        var p1 = '0' + Math.floor(10 + Math.random() * 90);
        var p2 = Math.floor(1000 + Math.random() * 9000);
        var p3 = Math.floor(1000 + Math.random() * 9000);
        return p1 + ' ' + p2 + ' ' + p3;
      }
    },
    russian: {
      title: 'Аудирование', ttsLang: 'ru-RU',
      topics: [
        { v: '1-10', n: 'Числа (1-10)' }, { v: '1-100', n: 'Числа (1-100)' }, { v: '100-2100', n: 'Числа (100-2100)' },
        { v: 'az', n: 'Алфавит (А-Я)' }, { v: 'vowels', n: 'Гласные' }, { v: 'tel', n: 'Номер телефона' }, { v: 'name', n: 'Имена' },
        { v: 'time', n: 'Время (часы)' }, { v: 'date', n: 'Даты' }, { v: 'money', n: 'Сумма денег' }
      ],
      alphabet: 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ', vowels: 'АЕЁИОУЫЭЮЯ',
      names: ['Александр', 'Дмитрий', 'Максим', 'Сергей', 'Андрей', 'Алексей', 'Артём', 'Илья', 'Кирилл', 'Михаил', 'Анна', 'Мария', 'Елена', 'Дарья', 'Алина', 'Ирина', 'Екатерина', 'Арина', 'Полина', 'Ольга'],
      cleanRe: /[^а-яё0-9]/g,
      introName: 'Послушайте имя', introTel: 'Номер телефона',
      phoneGen: function () {
        var code = ['90', '91', '93', '94', '97', '99'][Math.floor(Math.random() * 6)];
        var p1 = Math.floor(100 + Math.random() * 900);
        var p2 = Math.floor(10 + Math.random() * 90);
        var p3 = Math.floor(10 + Math.random() * 90);
        return '998 ' + code + ' ' + p1 + ' ' + p2 + ' ' + p3;
      }
    }
  };

  var L = { lang: 'english', timer: 0, speed: 1, curr: '', cdInterval: null, alive: false, timeouts: [] };

  /* ---------- Hayot sikli ----------
     Mashq TTS ovozi + ketma-ket setTimeout zanjirlari bilan ishlaydi
     (intro -> so'z -> harflab -> taymer). Bo'limdan chiqilganda bular
     o'zidan o'zi to'xtamaydi, shuning uchun `alive` bayrog'i bilan
     boshqariladi: har kechiktirilgan chaqiruv ishga tushishidan oldin
     bo'lim hali ochiqmi — tekshiradi. */
  function lsLater(fn, ms) {
    var id = setTimeout(function () {
      L.timeouts = L.timeouts.filter(function (x) { return x !== id; });
      if (L.alive) fn();
    }, ms);
    L.timeouts.push(id);
    return id;
  }
  function lsStop() {
    L.alive = false;
    L.timeouts.forEach(clearTimeout);
    L.timeouts = [];
    if (L.cdInterval) { clearInterval(L.cdInterval); L.cdInterval = null; }
    try { window.speechSynthesis.cancel(); } catch (e) {}
  }

  function ls(k, d) { try { var v = localStorage.getItem(k); return v == null ? d : v; } catch (e) { return d; } }
  function namesList() {
    var raw = ls('listening_names_' + L.lang, '').trim();
    return raw ? raw.split(/[,\n]/).map(function (s) { return s.trim(); }).filter(Boolean) : CFG[L.lang].names;
  }
  function phonesList() {
    var raw = ls('listening_phones_' + L.lang, '').trim();
    return raw ? raw.split(/[,\n]/).map(function (s) { return s.trim(); }).filter(Boolean) : null;
  }

  /* ---------- Mashqlar hub ---------- */
  App.view('practice', {
    nav: 'languages',
    render: function (page, params) {
      var lang = params.lang === 'russian' ? 'russian' : 'english';
      var backView = lang === 'russian' ? 'russian' : 'english';
      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: backView }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>Mashqlar</h1></div>' +
        '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'listening_practice', p: { lang: lang } }) + '\'>' +
        '<span class="li-ic" data-icon="headphones" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + CFG[lang].title + '</div><div class="li-sub">Eshitib yozish (TTS)</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
      App.icons(page);
    }
  });

  /* ---------- Listening mashqi ---------- */
  App.view('listening_practice', {
    nav: 'languages',
    render: function (page, params) {
      L.lang = params.lang === 'russian' ? 'russian' : 'english';
      var c = CFG[L.lang];
      var savedTopic = ls('listening_topic_' + L.lang, c.topics[0].v);

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: 'practice', p: { lang: L.lang } }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + c.title + '</h1>' +
        '<button class="icon-btn ghost" data-act="lsSettings"><span data-icon="settings" data-icon-size="18"></span></button></div>' +

        '<div class="list-label" style="margin-top:0">Mavzu</div>' +
        '<select class="input" id="ls-topic">' + c.topics.map(function (t) {
          return '<option value="' + t.v + '"' + (t.v === savedTopic ? ' selected' : '') + '>' + t.n + '</option>';
        }).join('') + '</select>' +

        '<div class="list-label">Vaqt (timer)</div>' +
        '<div class="flex" style="gap:6px;flex-wrap:wrap" id="ls-timer-pills">' +
        [0, 2000, 3000, 5000, 7000].map(function (t) {
          return '<button class="chip-btn' + (t === 0 ? ' active' : '') + '" data-t="' + t + '">' + (t === 0 ? 'OFF' : (t / 1000) + 's') + '</button>';
        }).join('') + '</div>' +

        '<div class="list-label">Tezlik</div>' +
        '<div class="flex" style="gap:12px;margin-bottom:8px">' +
        '<input type="range" id="ls-speed" min="0.5" max="1.5" step="0.1" value="1" style="flex:1;accent-color:var(--accent)">' +
        '<span class="muted mono" id="ls-speed-val" style="font-size:13px;width:38px;flex-shrink:0">1.0x</span></div>' +

        '<div style="text-align:center;margin:26px 0 18px">' +
        '<button class="ls-speaker" id="ls-speaker" aria-label="Ovozni eshitish"><span data-icon="volume" data-icon-size="32"></span><div class="ls-countdown" id="ls-cd"></div></button>' +
        '</div>' +
        '<input class="input" id="ls-ans" placeholder="Javob..." autocomplete="off" style="text-align:center;font-size:18px;font-weight:700">' +
        '<div class="btn-row" style="margin-top:14px">' +
        '<button class="btn sec" id="ls-reset"><span data-icon="refresh" data-icon-size="16"></span>Qaytadan</button>' +
        '<button class="btn" id="ls-next">Keyingisi</button>' +
        '</div>';
      App.icons(page);

      App.el('ls-topic').onchange = function () { localStorage.setItem('listening_topic_' + L.lang, this.value); lsNext(); };
      page.querySelectorAll('#ls-timer-pills .chip-btn').forEach(function (b) {
        b.onclick = function () {
          page.querySelectorAll('#ls-timer-pills .chip-btn').forEach(function (x) { x.classList.remove('active'); });
          b.classList.add('active'); L.timer = +b.getAttribute('data-t');
        };
      });
      App.el('ls-speed').oninput = function () { L.speed = +this.value; App.el('ls-speed-val').textContent = (+this.value).toFixed(1) + 'x'; };
      App.el('ls-speaker').onclick = lsPlay;
      App.el('ls-next').onclick = lsNext;
      App.el('ls-reset').onclick = function () { var inp = App.el('ls-ans'); inp.value = ''; inp.style.borderColor = ''; inp.style.color = ''; inp.focus(); lsPlay(); };
      App.el('ls-ans').oninput = function () { lsCheckInput(this); };
      App.el('ls-ans').onkeydown = function (e) { if (e.key === 'Enter') lsCheckForce(this); };

      L.timer = 0; L.speed = 1;
      lsStop();          // eski seansdan qolgan ovoz/taymer bo'lsa tozalanadi
      L.alive = true;
      lsNext();
    },
    leave: lsStop
  });

  App.actions.lsSettings = function () {
    var namesRaw = ls('listening_names_' + L.lang, '');
    var phonesRaw = ls('listening_phones_' + L.lang, '');
    var html =
      '<label class="field"><span>Ismlar ro\'yxati (vergul yoki qator bilan ajrating)</span>' +
      '<textarea class="textarea" id="ls-set-names" rows="3" placeholder="Ali, Vali, Sarvar">' + App.esc(namesRaw) + '</textarea></label>' +
      '<label class="field"><span>Telefon raqamlar ro\'yxati</span>' +
      '<textarea class="textarea" id="ls-set-phones" rows="3" placeholder="901234567, 998887766">' + App.esc(phonesRaw) + '</textarea></label>' +
      '<button class="btn" id="ls-set-save">Saqlash</button>';
    var sh = App.sheet(html, { title: 'Ro\'yxatlar' });
    sh.querySelector('#ls-set-save').onclick = function () {
      localStorage.setItem('listening_names_' + L.lang, sh.querySelector('#ls-set-names').value);
      localStorage.setItem('listening_phones_' + L.lang, sh.querySelector('#ls-set-phones').value);
      App.closeSheet(); App.toast('✅ Saqlandi');
    };
  };

  function lsNext() {
    var c = CFG[L.lang];
    if (L.cdInterval) clearInterval(L.cdInterval);
    var cd = App.el('ls-cd'); if (cd) { cd.classList.remove('active'); cd.textContent = ''; }

    var type = App.el('ls-topic') ? App.el('ls-topic').value : c.topics[0].v;
    var txt = '1';
    if (type === '1-10') txt = Math.floor(Math.random() * 10) + 1;
    else if (type === '1-100') txt = Math.floor(Math.random() * 100) + 1;
    else if (type === '100-2100') txt = Math.floor(Math.random() * 2000) + 100;
    else if (type === 'az') txt = c.alphabet[Math.floor(Math.random() * c.alphabet.length)];
    else if (type === 'vowels') txt = c.vowels[Math.floor(Math.random() * c.vowels.length)];
    else if (type === 'tel') { var phones = phonesList(); txt = phones ? phones[Math.floor(Math.random() * phones.length)] : c.phoneGen(); }
    else if (type === 'name') { var names = namesList(); txt = names[Math.floor(Math.random() * names.length)]; }
    else if (type === 'time') {
      // 08:45 ko'rinishida — javob ham shu formatda yoziladi
      var hh = Math.floor(Math.random() * 24), mm = [0, 5, 10, 15, 20, 30, 40, 45, 50][Math.floor(Math.random() * 9)];
      txt = ('0' + hh).slice(-2) + ':' + ('0' + mm).slice(-2);
    }
    else if (type === 'date') {
      var dd = Math.floor(Math.random() * 28) + 1, mo = Math.floor(Math.random() * 12) + 1;
      txt = ('0' + dd).slice(-2) + '.' + ('0' + mo).slice(-2);
    }
    else if (type === 'money') {
      var amounts = [1500, 12000, 45000, 100000, 250000, 780000, 1200000];
      txt = String(amounts[Math.floor(Math.random() * amounts.length)]);
    }

    L.curr = txt.toString();
    var inp = App.el('ls-ans');
    if (inp) { inp.value = ''; inp.style.borderColor = ''; inp.style.color = ''; inp.focus(); }
    lsPlay();
  }

  function lsSpeak(text, rate, cb) {
    if (!L.alive) return;
    var u = new SpeechSynthesisUtterance(text);
    u.lang = CFG[L.lang].ttsLang; u.rate = rate;
    if (cb) u.onend = function () { if (L.alive) cb(); };
    window.speechSynthesis.speak(u);
  }

  function lsPlay() {
    if (!L.alive) return;
    var c = CFG[L.lang];
    window.speechSynthesis.cancel();
    if (L.cdInterval) clearInterval(L.cdInterval);
    var cd = App.el('ls-cd'); if (cd) { cd.classList.remove('active'); cd.textContent = ''; }

    var type = App.el('ls-topic') ? App.el('ls-topic').value : c.topics[0].v;
    var txt = L.curr;

    if (type === 'name') {
      lsSpeak(c.introName, 1, function () {
        lsLater(function () {
          lsSpeak(txt, L.speed, function () {
            lsLater(function () {
              var spelled = txt.split('').join(L.lang === 'russian' ? '. ' : ', ');
              lsSpeak(spelled, L.speed * (L.lang === 'russian' ? 0.75 : 0.85), function () { if (L.timer > 0) lsStartTimer(); });
            }, 700);
          });
        }, 400);
      });
    } else if (type === 'tel') {
      lsSpeak(c.introTel, 1, function () {
        lsLater(function () {
          var readable = txt.split('').map(function (ch) { return ch === ' ' ? ',' : ch; }).join(' ');
          lsSpeak(readable, L.speed * 0.85, function () { if (L.timer > 0) lsStartTimer(); });
        }, 450);
      });
    } else if (type === 'time') {
      // "08:45" ni "8 45" deb o'qiydi (raqam sifatida emas)
      var p = txt.split(':');
      lsSpeak(parseInt(p[0], 10) + ' ' + parseInt(p[1], 10), L.speed, function () { if (L.timer > 0) lsStartTimer(); });
    } else if (type === 'date') {
      var d = txt.split('.');
      lsSpeak(parseInt(d[0], 10) + ' ' + parseInt(d[1], 10), L.speed, function () { if (L.timer > 0) lsStartTimer(); });
    } else {
      lsSpeak(txt, L.speed, function () { if (L.timer > 0) lsStartTimer(); });
    }
  }

  function lsStartTimer() {
    var cd = App.el('ls-cd'), inp = App.el('ls-ans');
    if (!cd || !inp) return;
    var left = L.timer / 1000;
    cd.classList.add('active'); cd.textContent = left;
    L.cdInterval = setInterval(function () {
      left--;
      if (left > 0) { cd.textContent = left; }
      else {
        clearInterval(L.cdInterval);
        cd.classList.remove('active'); cd.textContent = '';
        inp.value = L.curr; inp.style.borderColor = 'var(--danger)'; inp.style.color = 'var(--danger)';
        lsLater(lsNext, 1300);
      }
    }, 1000);
  }

  function lsCheckInput(el) {
    var re = CFG[L.lang].cleanRe;
    var val = el.value.trim().toLowerCase().replace(re, '');
    var ans = L.curr.toString().toLowerCase().replace(re, '');
    var type = App.el('ls-topic') ? App.el('ls-topic').value : '';

    if (val === ans) {
      el.style.borderColor = 'var(--success)'; el.style.color = 'var(--success)';
      if (L.cdInterval) clearInterval(L.cdInterval);
      var cd = App.el('ls-cd'); if (cd) cd.classList.remove('active');
      if (window.Activity) Activity.mark();
      App.call('log_activity', { section: 'listening', object: CFG[L.lang].title, amount: 1, unit: 'savol', meta: { lang: L.lang, type: type } }).catch(function () {});
      lsLater(lsNext, 550);
      return;
    }
    if (type !== 'tel' && type !== 'name' && val.length >= ans.length) lsCheckForce(el);
  }

  function lsCheckForce(el) {
    var re = CFG[L.lang].cleanRe;
    var val = el.value.trim().toLowerCase().replace(re, '');
    var ans = L.curr.toString().toLowerCase().replace(re, '');
    if (val !== ans) {
      el.style.borderColor = 'var(--danger)'; el.style.color = 'var(--danger)'; el.value = L.curr;
      if (L.cdInterval) clearInterval(L.cdInterval);
      var cd = App.el('ls-cd'); if (cd) cd.classList.remove('active');
      lsLater(lsNext, 1300);
    } else {
      lsCheckInput(el);
    }
  }
})();
