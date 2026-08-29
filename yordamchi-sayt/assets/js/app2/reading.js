/* Reading — interaktiv matn o'qish (Ingliz `en_reading`, Rus `ru_reading`).

   G'oya: tarjimalar matnning O'ZIDA oldindan yozib qo'yiladi, tizim esa
   ularni o'qib interaktiv qiladi. Onlayn tarjimon kerak emas — hamma narsa
   .md faylning ichida, shuning uchun oflaynda ham to'liq ishlaydi.

   FORMAT (.md fayl):
     # Sarlavha                     -> markazda turadigan sarlavha
     Bu {word|tarjima} bo'lgan gap. -> gap; {..|..} — bitta so'z tarjimasi
     :: Butun gapning tarjimasi.    -> oldingi gapga tegishli tarjima
     (ikki bo'sh qator)             -> yangi xatboshi (bitta bo'sh qator matnni bo'lmaydi)

   Ekran tuzilishi (yuqoridan pastga):
     sarlavha (markazda) -> kitobdek toza matn -> pastda tinglash tugmasi.
   Tugma bosilganda videopleyer uslubidagi boshqaruv paneliga aylanadi.
   So'z/gapga bosilganda tarjima o'sha joyning YONIDA kichik oynachada
   (popover) chiqadi va undan to'g'ridan-to'g'ri lug'atga qo'shsa bo'ladi.

   Fayl kutubxonaning O'ZIDA saqlanadi (library.js `language_topics`),
   ya'ni papkalar, yuklash, nomini o'zgartirish — hammasi o'zgarishsiz. */
(function () {
  'use strict';

  /* Bo'lim kalitidan TTS tili va lug'at tili */
  function ttsLang(sec) { return String(sec || '').indexOf('ru_') === 0 ? 'ru-RU' : 'en-US'; }
  function dictLang(sec) { return String(sec || '').indexOf('ru_') === 0 ? 'russian' : 'english'; }

  var R = {
    sec: '', id: null, name: '', lang: 'en-US',
    blocks: [], sentences: [],
    playing: false, idx: -1, rate: 1, alive: false,
    barOpen: false,
    stepMode: false,      // gap-ma-gap: har gapdan keyin to'xtaydi
    pendingStop: false
  };

  /* ================= Parser ================= */

  /* Gap matnini bo'laklarga ajratadi: {so'z|tarjima} annotatsiyalari va
     oddiy matn. Oddiy matn ichidan ham so'zlar ajratiladi (ular tarjimasiz,
     lekin baribir bosilsa o'qib beradi). */
  function tokenize(raw) {
    var out = [];
    var re = /\{([^{}|]+)\|([^{}]*)\}/g;
    var last = 0, m;
    function plain(s) {
      s.split(/([A-Za-zÀ-ÿА-Яа-яЁё'’-]+)/).forEach(function (part, i) {
        if (!part) return;
        if (i % 2 === 1) out.push({ k: 'w', w: part, t: '' });
        else out.push({ k: 'x', s: part });
      });
    }
    while ((m = re.exec(raw)) !== null) {
      if (m.index > last) plain(raw.slice(last, m.index));
      out.push({ k: 'w', w: m[1], t: (m[2] || '').trim() });
      last = m.index + m[0].length;
    }
    if (last < raw.length) plain(raw.slice(last));
    return out;
  }

  /* Gapning TTS uchun toza matni (annotatsiyalarsiz) */
  function plainText(raw) {
    return raw.replace(/\{([^{}|]+)\|[^{}]*\}/g, '$1').replace(/\s+/g, ' ').trim();
  }

  function parse(md) {
    var lines = String(md || '').replace(/\r/g, '').split('\n');
    var blocks = [], sentences = [];
    var blankRun = 0;

    lines.forEach(function (line) {
      var h = line.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        blankRun = 0;
        /* Sarlavha ham OVOZDA o'qiladi — ilgari u butunlay o'tkazib
           yuborilardi va tinglayotgan odam matnning yangi bo'limga
           o'tganini bilmasdi. `n` beriladi, chunki o'qilayotgan joy
           `data-n` orqali belgilanadi. */
        var hb = { k: 'h', lvl: h[1].length, text: h[2].trim(), n: sentences.length };
        hb.tokens = tokenize(hb.text);
        hb.raw = hb.text;
        hb.tr = '';
        blocks.push(hb);
        if (hb.text) sentences.push(hb);
        return;
      }

      var tr = line.match(/^\s*::\s?(.*)$/);
      if (tr) {
        blankRun = 0;
        for (var i = blocks.length - 1; i >= 0; i--) {
          if (blocks[i].k === 's') { blocks[i].tr = tr[1].trim(); break; }
          if (blocks[i].k === 'h') break;
        }
        return;
      }

      /* BO'SH QATOR — xatboshi faqat IKKI (yoki undan ko'p) bo'sh qatordan
         keyin boshlanadi.
         Sabab: amalda AI har "gap + :: tarjima" juftidan keyin bitta bo'sh
         qator qoldiradi (o'qishga qulay bo'lsin deb). Bitta bo'sh qator ham
         xatboshi deb qabul qilinsa, HAR GAP alohida abzats bo'lib, matn
         kitobdek emas, ro'yxatdek ko'rinardi — haqiqiy faylda 18 gap 18 ta
         xatboshiga bo'linib ketgan edi. */
      if (/^\s*$/.test(line)) {
        blankRun++;
        if (blankRun === 2) blocks.push({ k: 'br' });
        return;
      }
      blankRun = 0;

      var s = { k: 's', raw: line.trim(), tr: '', n: sentences.length };
      s.tokens = tokenize(s.raw);
      s.text = plainText(s.raw);
      blocks.push(s);
      sentences.push(s);
    });
    return { blocks: blocks, sentences: sentences };
  }

  /* ================= TTS ================= */

  /* O'qish `TTS` qatlami orqali ketadi (assets/js/core/tts.js): u eng
     yaxshi ovozni tanlaydi, uzun gapni bo'laklaydi, Chrome'ning to'xtab
     qolishini oldini oladi va XATO bo'lsa ham `done` ni chaqiradi —
     shuning uchun bitta gap yiqilsa matn to'xtab qolmaydi. */
  function speak(text, done) {
    if (!text) { if (done) done(); return; }
    if (!window.TTS || !TTS.ok()) {
      App.toast('Bu brauzerda ovoz mavjud emas');
      if (done) done();
      return;
    }
    TTS.speak(text, { lang: R.lang, rate: R.rate }, function (err) {
      if (!R.alive) return;
      if (err) {
        /* Jimgina to'xtab qolmasin — sabab ko'rinsin, lekin o'qish
           keyingi gapdan davom etaversin. */
        R.errCount = (R.errCount || 0) + 1;
        if (R.errCount <= 2) App.toast('Ovozda uzilish — davom etyapmiz');
      }
      if (done) done();
    });
  }

  /* ================= Intonatsiya (tinish belgilariga qarab) =================
     Ovoz dvigateli butun qatorni bitta bo'lak qilib olsa, ohang tekis
     chiqadi: so'roq ham, xitob ham, nuqta ham bir xil eshitiladi. Shuning
     uchun qator tinish belgilari bo'yicha intonatsion bo'laklarga ajratiladi
     va har bo'lak O'Z ohangi (pitch), tezligi va keyingi jimligi bilan
     o'qiladi.

     VERGUL ataylab bo'lak CHEGARASI qilinmadi: uni dvigatelning o'zi tabiiy
     qisqa to'xtash bilan o'qiydi. Har vergulda uzilsa, nutq bo'g'ib-bo'g'ib,
     sun'iy chiqadi. Chegara — faqat gap oxiri (. ! ? …), nuqtali vergul,
     ikki nuqta va tire. */
  var PROSODY = {
    '.': { pitch: 0.96, rate: 1.00, pause: 340 },   // xabar — ohang pasayadi
    '!': { pitch: 1.15, rate: 1.06, pause: 400 },   // xitob — baland, jonli
    '?': { pitch: 1.20, rate: 0.97, pause: 420 },   // so'roq — ohang ko'tariladi
    '…': { pitch: 0.90, rate: 0.88, pause: 600 },   // tugallanmagan fikr — so'nadi
    ':': { pitch: 1.06, rate: 1.00, pause: 280 },   // izoh kutilyapti
    ';': { pitch: 1.00, rate: 1.00, pause: 300 },
    '—': { pitch: 1.00, rate: 1.00, pause: 300 },   // tire — sezilarli to'xtash
    '':  { pitch: 1.00, rate: 1.00, pause: 200 }
  };

  /* Ismdan oldin keladigan unvonlar — ulardan keyin HECH QACHON gap uzilmaydi */
  var TITLES = ['mr', 'mrs', 'ms', 'dr', 'prof', 'st', 'sr', 'jr'];

  /* Gap OXIRIDA ham kelishi mumkin bo'lgan qisqartmalar — qaror keyingi
     so'zning bosh harfiga qarab chiqariladi */
  var ABBREV = ['т', 'д', 'п', 'е', 'г', 'в', 'гг', 'вв', 'см', 'стр', 'рис',
                'др', 'руб', 'чел', 'ул', 'им', 'etc', 'vs', 'eg', 'ie'];

  var SPLIT = '';

  /* Qatorni intonatsion bo'laklarga ajratadi -> [{ text, pitch, rate, pause }] */
  function prosodyParts(raw) {
    var text = String(raw || '').replace(/\s+/g, ' ').trim();
    if (!text) return [];

    text = text.replace(/\.{3,}/g, '…');

    /* Gap oxiridan keyin ajratamiz.

       QISQARTMA MUAMMOSI: "и т. д. Потом пошёл" da uchta nuqta bor, lekin
       faqat OXIRGISI gap oxiri. Avvalgi qoida sodda edi — "nuqtadan oldin
       bitta harf bo'lsa bo'lma" — va u "д." dan keyingi HAQIQIY gap
       chegarasini ham yutib yuborardi.

       Endi keyingi so'zning bosh harfiga ham qaraladi:
         "т. д."     -> keyingisi kichik harf ("д") => qisqartma, bo'linmaydi
         "д. Потом"  -> keyingisi BOSH harf         => gap oxiri, bo'linadi
       Unvonlar (Mr., Dr.) har doim ism bilan keladi, ya'ni ulardan keyin
       bosh harf normal — shuning uchun ular alohida ro'yxatda va hech
       qachon bo'linmaydi.

       `(?<=)` ISHLATILMAYDI — eski Safari uni tushunmaydi va butun faylni
       yiqitadi (tts.js dagi izohga qarang). */
    text = text.replace(/([.!?…]+)(\s+)/g, function (m, punct, ws, off, str) {
      if (punct === '.') {
        var lastTok = (str.slice(0, off).match(/([^\s.]+)$/) || [])[1] || '';
        var lt = lastTok.toLowerCase();
        var nextIsUpper = /[А-ЯЁA-Z]/.test(str.charAt(off + m.length));
        if (TITLES.indexOf(lt) >= 0) return m;                       // Mr. Smith
        if ((lastTok.length === 1 || ABBREV.indexOf(lt) >= 0) && !nextIsUpper) return m;
      }
      return punct + SPLIT;
    });
    text = text.replace(/([;:])\s+/g, '$1' + SPLIT);
    text = text.replace(/\s*[—–]\s*/g, SPLIT + '— ');

    var parts = [];
    text.split(SPLIT).forEach(function (piece) {
      var t = piece.trim();
      if (!t) return;

      /* Boshidagi tire — o'zi o'qilmaydi, uning o'rniga oldiga jimlik
         qo'yiladi (yuqorida bo'lak chegarasi shu sabab qo'yilgan). */
      var leadDash = /^[—–]\s*/.test(t);
      if (leadDash) t = t.replace(/^[—–]\s*/, '');
      if (!t) return;

      /* Tire oldidagi jimlik — AVVALGI bo'lakdan keyin bo'lishi kerak
         (pauza har doim bo'lakdan KEYIN qo'yiladi, tire esa keyingi
         bo'lakning boshida turadi). */
      if (leadDash && parts.length) {
        var prev = parts[parts.length - 1];
        if (prev.pause < PROSODY['—'].pause) prev.pause = PROSODY['—'].pause;
      }

      var last = t.charAt(t.length - 1);
      var key = PROSODY[last] ? last : '';
      var p = PROSODY[key];
      parts.push({ text: t, pitch: p.pitch, rate: p.rate, pause: p.pause });
    });

    return parts;
  }

  /* Bitta bo'lakni o'z ohangi bilan o'qiydi */
  function speakPart(part, done) {
    if (!window.TTS || !TTS.ok()) { if (done) done(); return; }
    TTS.speak(part.text, {
      lang: R.lang,
      rate: R.rate * part.rate,
      pitch: part.pitch
    }, function (err) {
      if (!R.alive) return;
      if (err) {
        R.errCount = (R.errCount || 0) + 1;
        if (R.errCount <= 2) App.toast('Ovozda uzilish — davom etyapmiz');
      }
      if (done) done();
    });
  }

  /* Qatorni bo'lak-bo'lak, intonatsiya bilan o'qiydi.
     `done(pause)` — oxirgi bo'lakdan keyin qancha jimlik kerakligini beradi
     (nuqtadan keyin qisqa, so'roq/xitobdan keyin uzunroq). */
  function speakProsody(text, done) {
    var parts = prosodyParts(text);
    if (!parts.length) { if (done) done(PROSODY[''].pause); return; }

    var i = 0;
    (function next() {
      if (!R.alive) return;
      var p = parts[i++];
      speakPart(p, function () {
        if (!R.alive) return;
        if (i >= parts.length) { if (done) done(p.pause); return; }
        R.partTimer = setTimeout(next, Math.round(p.pause / (R.rate || 1)));
      });
    })();
  }

  /* Sarlavhani alohida ohangda o'qiydi */
  function speakHeading(text, done) {
    if (!window.TTS || !TTS.ok()) { if (done) done(); return; }
    TTS.speak(text, { lang: R.lang, rate: R.rate * 0.92, pitch: 0.94 }, function () {
      if (!R.alive) return;
      if (done) done();
    });
  }

  function highlight(n) {
    var page = document.getElementById('page'); if (!page) return;
    page.querySelectorAll('.rd-s.reading').forEach(function (el) { el.classList.remove('reading'); });
    if (n < 0) return;
    var el = page.querySelector('.rd-s[data-n="' + n + '"]');
    if (el) {
      el.classList.add('reading');
      el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  /* Ovozni ham, KUTAYOTGAN TAYMERLARNI ham birga to'xtatadi.
     Ikkalasi birga bekor qilinmasa, to'xtatilgandan keyin osilib qolgan
     taymer eski bo'lakni o'qib yuboradi (`R.alive` hamma joyda ham
     o'chirilmaydi — masalan "keyingi gap" bosilganda u ataylab yoqiladi). */
  function haltSpeech() {
    if (R.gapTimer) { clearTimeout(R.gapTimer); R.gapTimer = null; }
    if (R.partTimer) { clearTimeout(R.partTimer); R.partTimer = null; }
    if (window.TTS) TTS.cancel(); else { try { window.speechSynthesis.cancel(); } catch (e) {} }
  }

  function stopAll() {
    R.playing = false;
    R.alive = false;
    /* Gaplar orasidagi kutish ham bekor qilinsin — aks holda to'xtatilgandan
       keyin yana bitta gap o'qilib ketardi. */
    haltSpeech();
    releaseWake();
    highlight(-1);
    paintPlayer();
  }

  /* ---------- Ekran o'chib qolmasin ----------
     Uzoq matn tinglayotganda telefon ekrani o'chsa, ba'zi brauzerlarda
     o'qish ham to'xtaydi. Wake Lock qo'llab-quvvatlanmasa jimgina
     e'tiborsiz qoladi. */
  function requestWake() {
    if (R.wake || !navigator.wakeLock) return;
    navigator.wakeLock.request('screen').then(function (w) {
      R.wake = w;
      w.addEventListener('release', function () { R.wake = null; });
    }).catch(function () {});
  }
  function releaseWake() {
    if (!R.wake) return;
    try { R.wake.release(); } catch (e) {}
    R.wake = null;
  }

  function step(n) {
    if (!R.playing || !R.alive) return;

    /* Gap-ma-gap rejim: bitta gap o'qilgach o'zi to'xtaydi va keyingi gapga
       tayyor turadi. ▶ bosilsa davom etadi. O'rganish uchun qulay —
       har gapdan keyin o'ylab olish/takrorlash imkoni bo'ladi. */
    if (R.stepMode && R.pendingStop) {
      R.pendingStop = false;
      R.playing = false;
      R.idx = n;
      highlight(n);
      paintPlayer();
      return;
    }

    if (n >= R.sentences.length) {
      R.playing = false; R.idx = -1;
      highlight(-1); paintPlayer();
      App.toast('✅ Matn tugadi');
      if (window.Activity) Activity.mark();
      App.call('log_activity', {
        section: 'reading', object: R.name, amount: R.sentences.length,
        unit: 'gap', meta: { sec: R.sec, mode: 'listen' }
      }).catch(function () {});
      return;
    }
    R.idx = n;
    highlight(n);
    paintPlayer();
    var cur = R.sentences[n];
    /* Sarlavha e'lon qilib o'qiladi: sekinroq, pastroq ohangda va undan
       keyin uzunroq jimlik — quloq bilan "yangi bo'lim boshlandi" degani
       bilinsin. */
    if (cur.k === 'h') {
      speakHeading(cur.text, function () {
        if (R.stepMode) R.pendingStop = true;
        R.gapTimer = setTimeout(function () { step(n + 1); }, Math.round(700 / (R.rate || 1)));
      });
      return;
    }
    speakProsody(cur.text, function (endPause) {
      if (R.stepMode) R.pendingStop = true;   // keyingi qadamda to'xtaydi
      /* Gaplar orasidagi jimlik endi TINISH BELGISIGA bog'liq: nuqtadan
         keyin qisqa, so'roq/xitobdan keyin uzunroq, ko'p nuqtadan keyin eng
         uzun. Tezlikka ham bog'liq: sekin o'qilsa pauza ham uzunroq. */
      var pause = Math.round((endPause || 260) / (R.rate || 1));
      R.gapTimer = setTimeout(function () { step(n + 1); }, pause);
    });
  }

  /* ================= Pastki pleyer =================
     Yopiq holatda — bitta tugma. Bosilganda videopleyerdagidek boshqaruv
     paneliga ochiladi: oldingi/keyingi gap, play/pause, progress va tezlik. */

  function paintPlayer() {
    var box = App.el('rd-player'); if (!box) return;

    if (!R.barOpen) {
      box.className = 'rd-player';
      box.innerHTML =
        '<button class="rd-open" data-act="rdOpenBar">' +
        '<span data-icon="volume" data-icon-size="18"></span>Matnni tinglash</button>';
      App.icons(box);
      return;
    }

    var total = R.sentences.length || 1;
    var cur = R.idx < 0 ? 0 : R.idx + 1;
    var pct = Math.round((cur / total) * 100);

    box.className = 'rd-player open';
    box.innerHTML =
      '<div class="rd-pl-top">' +
        '<div class="rd-pl-time">' + cur + ' / ' + total + ' gap</div>' +
        '<button class="rd-pl-x" data-act="rdCloseBar" aria-label="Yopish">' +
        '<span data-icon="close" data-icon-size="16"></span></button>' +
      '</div>' +
      '<div class="rd-pl-track"><div class="rd-pl-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="rd-pl-ctrls">' +
        '<button class="rd-pl-b" data-act="rdPrev" aria-label="Oldingi gap">' +
        '<span data-icon="skipBack" data-icon-size="20"></span></button>' +
        '<button class="rd-pl-play" data-act="rdToggle" aria-label="' + (R.playing ? 'To\'xtatish' : 'Boshlash') + '">' +
        '<span data-icon="' + (R.playing ? 'pause' : 'play') + '" data-icon-size="24"></span></button>' +
        '<button class="rd-pl-b" data-act="rdNext" aria-label="Keyingi gap">' +
        '<span data-icon="skipFwd" data-icon-size="20"></span></button>' +
        '<button class="rd-pl-rate" data-act="rdSpeed">' + rateLabel() + '</button>' +
        '<button class="rd-pl-step' + (R.stepMode ? ' on' : '') + '" data-act="rdStepMode" ' +
        'aria-label="Gap-ma-gap rejim" title="Har gapdan keyin to\'xtash">' +
        '<span data-icon="pauseDot" data-icon-size="16"></span></button>' +
        '<button class="rd-pl-step" data-act="rdVoice" aria-label="Ovozni tanlash" title="Ovozni tanlash">' +
        '<span data-icon="volume" data-icon-size="16"></span></button>' +
      '</div>';
    App.icons(box);
  }

  function rateLabel() { return String(R.rate).replace(/\.?0+$/, '') + 'x'; }

  App.actions.rdOpenBar = function () { R.barOpen = true; paintPlayer(); };
  App.actions.rdCloseBar = function () {
    if (R.playing) { R.playing = false; haltSpeech(); highlight(-1); }
    R.barOpen = false; paintPlayer();
  };

  App.actions.rdToggle = function () {
    if (R.playing) {
      R.playing = false;
      haltSpeech();
      releaseWake();
      paintPlayer();
      return;
    }
    if (!R.sentences.length) { App.toast('Matnda o\'qiladigan gap yo\'q'); return; }
    /* Birinchi matn ba'zan "yutib yuboriladi" — foydalanuvchi harakatidan
       (aynan shu bosishdan) foydalanib ovozni isitib olamiz. */
    if (window.TTS) TTS.prime();
    requestWake();
    R.errCount = 0;
    R.playing = true; R.alive = true;
    step(R.idx >= 0 && R.idx < R.sentences.length ? R.idx : 0);
  };

  App.actions.rdPrev = function () { jump(-1); };
  App.actions.rdNext = function () { jump(1); };
  function jump(d) {
    if (!R.sentences.length) return;
    /* Hali boshlanmagan (idx = -1) holatda "keyingi" BIRINCHI gapga olib
       boradi — `-1 + 1 = 0` emas, chunki -1 "hali hech qayerda" degani,
       "birinchidan oldin" degani emas (aks holda 1-gap tashlab ketilardi). */
    var n = R.idx < 0 ? 0 : R.idx + d;
    if (n < 0) n = 0;
    if (n >= R.sentences.length) n = R.sentences.length - 1;
    R.alive = true;
    if (R.playing) { haltSpeech(); step(n); }
    else { R.idx = n; highlight(n); paintPlayer(); }
  }

  App.actions.rdStepMode = function () {
    R.stepMode = !R.stepMode;
    R.pendingStop = false;
    try { localStorage.setItem('reading_step_mode', R.stepMode ? '1' : '0'); } catch (e) {}
    paintPlayer();
    App.toast(R.stepMode ? 'Gap-ma-gap: har gapdan keyin to\'xtaydi' : 'Uzluksiz o\'qish');
  };

  /* ---------- Ovozni tanlash ----------
     Bir tilda bir nechta ovoz bo'ladi va ular sifati bo'yicha KESKIN
     farq qiladi. Standart holatda eng yaxshisi tanlanadi, lekin
     foydalanuvchi o'zi ham eshitib tanlashi mumkin — tanlovi til
     bo'yicha eslab qolinadi. */
  App.actions.rdVoice = function () {
    if (!window.TTS || !TTS.ok()) { App.toast('Bu brauzerda ovoz mavjud emas'); return; }
    var sh = App.sheet('<div id="rd-voices"><div class="load-wrap"><div class="spinner"></div></div></div>',
                       { title: 'Ovozni tanlash' });
    TTS.ready().then(function () {
      var box = sh.querySelector('#rd-voices'); if (!box) return;
      var list = TTS.voicesFor(R.lang);
      if (!list.length) {
        box.innerHTML = App.empty({
          icon: 'alert', title: 'Ovoz topilmadi',
          text: R.lang + ' uchun qurilmangizda ovoz yo\'q. Telefon sozlamalaridan ' +
                'til paketini yuklab oling.'
        });
        App.icons(box);
        return;
      }
      var cur = TTS.pick(R.lang);
      box.innerHTML =
        '<p class="muted" style="font-size:12px;margin:0 0 12px">Bosilganda namuna o\'qiladi. ' +
        'Eng tepadagisi — tizim eng sifatli deb hisoblagani.</p>' +
        list.map(function (v, i) {
          var on = cur && v.voiceURI === cur.voiceURI;
          return '<button class="list-row" data-act="rdPickVoice" data-arg=\'' +
            App.arg({ uri: v.voiceURI }) + '\'>' +
            '<span class="li-ic" style="background:' + (on ? 'var(--accent-soft)' : 'none') +
            ';color:' + (on ? 'var(--accent)' : 'var(--hint)') + '" data-icon="' +
            (on ? 'check' : 'volume') + '" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">' + App.esc(v.name) + '</div>' +
            '<div class="li-sub">' + App.esc(v.lang) +
            (i === 0 ? ' · tavsiya etiladi' : '') +
            (v.localService === false ? ' · onlayn' : '') + '</div></div></button>';
        }).join('');
      App.icons(box);
    }).catch(function () {});
  };

  App.actions.rdPickVoice = function (a) {
    TTS.setVoice(R.lang, a.uri);
    var v = TTS.voicesFor(R.lang).find(function (x) { return x.voiceURI === a.uri; });
    /* Namuna — tanlangan ovoz bilan darhol eshitiladi, shunda taqqoslash oson */
    var demo = R.lang.indexOf('ru') === 0
      ? 'Это пример голоса. Послушайте, как звучит текст.'
      : 'This is a voice sample. Listen how the text sounds.';
    TTS.speak(demo, { lang: R.lang, rate: R.rate, voice: v }, function () {});
    App.actions.rdVoice();      // ro'yxatni belgisi bilan qayta chizamiz
  };

  App.actions.rdSpeed = function () {
    var opts = [0.6, 0.75, 0.9, 1, 1.15, 1.3];
    R.rate = opts[(opts.indexOf(R.rate) + 1) % opts.length];
    try { localStorage.setItem('reading_rate', String(R.rate)); } catch (e) {}
    paintPlayer();
    if (R.playing) { haltSpeech(); step(R.idx < 0 ? 0 : R.idx); }
  };

  /* ================= Tarjima oynachasi (popover) =================
     Bosilgan so'z/gapning YONIDA chiqadi (tepadagi panel emas) — o'qish
     joyidan ko'z uzilmasin. Ekran chetidan chiqib ketmasligi uchun
     gorizontal holati cheklanadi, joy bo'lmasa pastga tushadi. */

  var POP = null;
  function closePop() {
    if (POP) { POP.remove(); POP = null; }
    var page = document.getElementById('page');
    if (page) page.querySelectorAll('.rd-w.on,.rd-s.on').forEach(function (x) { x.classList.remove('on'); });
  }

  function openPop(anchor, opts) {
    closePop();
    if (anchor) anchor.classList.add('on');

    var p = document.createElement('div');
    p.className = 'rd-pop';
    p.innerHTML =
      '<div class="rd-pop-body">' +
        '<div class="rd-pop-src">' + App.esc(opts.src) + '</div>' +
        '<div class="rd-pop-tr">' + (opts.tr ? App.esc(opts.tr) : '<i>tarjima yozilmagan</i>') + '</div>' +
      '</div>' +
      /* Gap tarjimasi — so'z oynachasida ham bo'lsin (matn zich belgilanganda
         gapning bo'sh joyiga tegib bo'lmaydi). */
      (opts.sent >= 0 && R.sentences[opts.sent] && R.sentences[opts.sent].tr
        ? '<button class="rd-pop-sent" data-act="rdSent" data-arg=\'' +
          App.arg({ n: opts.sent }) + '\'>' +
          '<span data-icon="list" data-icon-size="13"></span>Gap tarjimasi</button>'
        : '') +
      '<div class="rd-pop-acts">' +
        '<button class="rd-pop-b" data-act="rdSay" data-arg=\'' + App.arg({ t: opts.say }) + '\'>' +
        '<span data-icon="volume" data-icon-size="15"></span>Tinglash</button>' +
        (opts.learn
          ? '<button class="rd-pop-b learn" data-act="rdLearn" data-arg=\'' +
            App.arg({ w: opts.src, t: opts.tr }) + '\'>' +
            '<span data-icon="check" data-icon-size="15"></span>O\'rganish</button>'
          : '') +
      '</div>' +
      '<span class="rd-pop-tip"></span>';
    document.body.appendChild(p);
    App.icons(p);

    place(p, anchor);
    POP = p;
  }

  /* Oynachani lange elementning tepasiga (joy bo'lmasa pastiga) qo'yadi */
  function place(p, anchor) {
    if (!anchor) return;
    var r = anchor.getBoundingClientRect();
    var pw = p.offsetWidth, ph = p.offsetHeight;
    var pad = 10;
    var left = r.left + r.width / 2 - pw / 2;
    left = Math.max(pad, Math.min(left, window.innerWidth - pw - pad));

    var top = r.top - ph - 10;
    var below = false;
    if (top < pad) { top = r.bottom + 10; below = true; }
    p.classList.toggle('below', below);

    p.style.left = Math.round(left) + 'px';
    p.style.top = Math.round(top) + 'px';

    // Uchburchak strelka aynan so'zning ustida tursin
    var tip = p.querySelector('.rd-pop-tip');
    if (tip) {
      var tx = r.left + r.width / 2 - left;
      tip.style.left = Math.round(Math.max(14, Math.min(tx, pw - 14))) + 'px';
    }
  }

  /* "Tinglash" — bitta so'z ham, butun gap ham bo'lishi mumkin. Gap bo'lsa
     u ham intonatsiya bilan o'qilsin (so'z uchun natija bir xil). */
  App.actions.rdSay = function (a) {
    R.alive = true;
    haltSpeech();
    speakProsody(a && a.t);
  };

  App.actions.rdWord = function (a, el) {
    R.alive = true;
    /* Gapning tarjimasini ham qo'shib beramiz. Sabab: matn zich
       belgilanganda (bir gapda 5-6 so'z) gapning "bo'sh" joyiga tegish
       deyarli imkonsiz — foydalanuvchi gap tarjimasini umuman ko'ra
       olmasdi. Endi so'z oynachasida "Gap" tugmasi turadi. */
    var sEl = el && el.closest ? el.closest('.rd-s') : null;
    var sn = sEl ? +sEl.getAttribute('data-n') : -1;
    openPop(el, { src: a.w, tr: a.t, say: a.w, learn: true, sent: sn });
    speak(a.w);
  };

  App.actions.rdSent = function (a, el) {
    R.alive = true;
    var s = R.sentences[a.n]; if (!s) return;
    /* Chaqiruv oynacha ICHIDAGI "Gap tarjimasi" tugmasidan kelgan bo'lishi
       mumkin — u zahoti o'chiriladi, shuning uchun tayanch sifatida GAPNING
       o'zini topamiz (aks holda oynacha noto'g'ri joyda chiqardi). */
    var page = document.getElementById('page');
    var anchor = (el && el.closest && el.closest('.rd-s')) ||
                 (page && page.querySelector('.rd-s[data-n="' + a.n + '"]'));
    openPop(anchor, { src: s.text, tr: s.tr, say: s.text, learn: false, sent: -1 });
  };

  /* Tashqariga bosilsa yopiladi; sahifa siljisa joyi yangilanadi */
  document.addEventListener('click', function (e) {
    if (!POP) return;
    if (e.target.closest('.rd-pop') || e.target.closest('.rd-w') || e.target.closest('.rd-s')) return;
    closePop();
  }, true);
  window.addEventListener('resize', function () { if (POP) closePop(); });

  /* ================= "O'rganish" — lug'atga qo'shish =================
     So'zlar QAYSI lug'atga tushishini foydalanuvchi o'zi tanlaydi (qalam
     menyusidagi "O'rganish lug'ati"). Tanlov har matn uchun alohida eslab
     qolinadi; tanlanmagan bo'lsa matnning nomi ishlatiladi.

     `save_dict_cat` kategoriyani BUTUNLAY almashtiradi, shuning uchun avval
     mavjud so'zlar o'qib olinadi va yangisi ustiga qo'shiladi (aks holda
     oldingilari o'chib ketardi). */
  function targetKey() { return 'reading_dict_' + R.sec + '_' + R.id; }
  function targetCat() {
    try {
      var v = (localStorage.getItem(targetKey()) || '').trim();
      if (v) return v;
    } catch (e) {}
    return R.name || 'Reading';
  }
  function setTargetCat(name) {
    try {
      if (name) localStorage.setItem(targetKey(), name);
      else localStorage.removeItem(targetKey());
    } catch (e) {}
  }

  App.actions.rdLearn = function (a, el) {
    var word = String(a.w || '').trim();
    var tr = String(a.t || '').trim();
    if (!word) return;
    if (!tr) { App.toast('Bu so\'zning tarjimasi yozilmagan'); return; }

    var lang = dictLang(R.sec);
    var cat = targetCat();
    if (el) { el.disabled = true; el.textContent = '...'; }

    App.call('get_dict_data', null, { query: 'lang=' + encodeURIComponent(lang) })
      .then(function (j) {
        var words = [];
        (j.items || []).forEach(function (it) {
          if (it.category === cat) words.push({ ru: it.word_ru, uz: it.word_uz });
        });
        var lower = word.toLowerCase();
        if (words.some(function (w) { return String(w.ru).toLowerCase() === lower; })) {
          return { already: true, n: words.length };
        }
        words.push({ ru: word, uz: tr });
        return App.call('save_dict_cat', { lang: lang, category: cat, words: words })
          .then(function () { return { already: false, n: words.length }; });
      })
      .then(function (r) {
        closePop();
        App.toast(r.already
          ? '"' + word + '" allaqachon "' + cat + '" lug\'atida'
          : '✅ "' + word + '" → "' + cat + '" lug\'ati (' + r.n + ' ta so\'z)');
      })
      .catch(function (e) {
        if (el) { el.disabled = false; }
        App.toast('⚠️ ' + e.message);
      });
  };

  /* ---------- "O'rganish lug'ati" tanlash ----------
     Mavjud lug'atlardan birini tanlash yoki yangi nom yozish. Tanlangan
     lug'atga shu matndan bosilgan so'zlar tushadi va uni Lug'at bo'limida
     odatdagidek yodlash mumkin. */
  App.actions.rdPickDict = function () {
    App.closeSheet();
    var lang = dictLang(R.sec);
    var cur = targetCat();

    App.call('get_dict_data', null, { query: 'lang=' + encodeURIComponent(lang) })
      .then(function (j) {
        var counts = {};
        (j.items || []).forEach(function (it) { counts[it.category] = (counts[it.category] || 0) + 1; });
        var cats = (j.order || []).slice();
        Object.keys(counts).forEach(function (c) { if (cats.indexOf(c) < 0) cats.push(c); });

        var html =
          '<p class="muted" style="font-size:12px;margin:0 0 12px">' +
          'Shu matndan "O\'rganish" bilan qo\'shilgan so\'zlar tanlangan lug\'atga tushadi. ' +
          'Uni Lug\'at bo\'limida yodlaysiz.</p>' +
          '<label class="field"><span>Lug\'at nomi</span>' +
          '<input class="input" id="rd-dict-name" value="' + App.esc(cur) + '" placeholder="Masalan: The Old Lighthouse"></label>' +
          (cats.length
            ? '<div class="list-label">Mavjud lug\'atlar</div>' +
              cats.map(function (c) {
                return '<button class="list-row rd-dict-pick" data-name="' + App.esc(c) + '">' +
                  '<span class="li-ic"' + (c === cur ? ' style="background:var(--accent-soft);color:var(--accent)"' : '') +
                  ' data-icon="' + (c === cur ? 'check' : 'list') + '" data-icon-size="15"></span>' +
                  '<div class="li-main"><div class="li-title">' + App.esc(c) + '</div>' +
                  '<div class="li-sub">' + (counts[c] || 0) + ' ta so\'z</div></div></button>';
              }).join('')
            : '<p class="muted" style="font-size:12px">Bu tilda hali lug\'at yo\'q — yuqorida nom yozsangiz yangisi ochiladi.</p>') +
          '<div class="btn-row" style="margin-top:14px">' +
          '<button class="btn sec" data-act="closeSheet">Bekor</button>' +
          '<button class="btn" id="rd-dict-save">Saqlash</button></div>';

        var sh = App.sheet(html, { title: 'O\'rganish lug\'ati' });
        App.icons(sh);
        var inp = sh.querySelector('#rd-dict-name');
        // Ro'yxatdan tanlash — nomni maydonga qo'yadi (darhol saqlamaydi,
        // foydalanuvchi tahrirlashi ham mumkin)
        sh.querySelectorAll('.rd-dict-pick').forEach(function (b) {
          b.onclick = function () { inp.value = b.getAttribute('data-name'); inp.focus(); };
        });
        sh.querySelector('#rd-dict-save').onclick = function () {
          var name = (inp.value || '').trim();
          if (!name) { App.toast('Lug\'at nomini kiriting'); return; }
          setTargetCat(name);
          App.closeSheet();
          App.toast('✅ So\'zlar "' + name + '" lug\'atiga qo\'shiladi');
        };
      })
      .catch(function (e) { App.toast('⚠️ ' + e.message); });
  };

  /* ================= Chizish ================= */

  function bodyHtml(parsed) {
    if (!parsed.blocks.length) return '';
    var html = '', para = '';
    function flush() { if (para) { html += '<p class="rd-p">' + para + '</p>'; para = ''; } }

    parsed.blocks.forEach(function (b) {
      if (b.k === 'br') { flush(); return; }
      if (b.k === 'h') {
        flush();
        // Birinchi darajali sarlavha — MARKAZDA (matn boshlanishi shundan)
        var cls = b.lvl === 1 ? 'rd-h1' : 'rd-h2';
        var tag = b.lvl === 1 ? 'h2' : 'h3';
        /* `rd-s` + `data-n` — o'qilayotganda sarlavha ham belgilanib turishi
           uchun (gaplar bilan bir xil mexanizm). */
        html += '<' + tag + ' class="' + cls + ' rd-s" data-n="' + b.n + '">' +
          App.esc(b.text) + '</' + tag + '>';
        return;
      }

      var inner = b.tokens.map(function (t) {
        if (t.k === 'x') return App.esc(t.s);
        return '<span class="rd-w' + (t.t ? ' has' : '') + '" data-act="rdWord" data-arg=\'' +
          App.arg({ w: t.w, t: t.t }) + '\'>' + App.esc(t.w) + '</span>';
      }).join('');

      para += '<span class="rd-s" data-n="' + b.n +
              '" data-act="rdSent" data-arg=\'' + App.arg({ n: b.n }) + '\'>' + inner + '</span> ';
    });
    flush();
    return html;
  }

  /* ================= Namuna fayl ================= */

  var SAMPLE_EN = [
    '# The Old Lighthouse',
    '',
    'The {old|eski} {lighthouse|mayoq} stood on the {cliff|qoya} above the sea.',
    ':: Eski mayoq dengiz ustidagi qoyada turardi.',
    'Every {night|kecha} its light {guided|yo\'l ko\'rsatardi} the {ships|kemalar} home.',
    ':: Har kecha uning nuri kemalarga uyga yo\'l ko\'rsatardi.',
    '',
    'One {winter|qish} the keeper {fell|kasal bo\'lib qoldi} ill.',
    ':: Bir qishda qorovul kasal bo\'lib qoldi.',
    'His {daughter|qizi} climbed the {stairs|zinapoya} alone and lit the {lamp|chiroq}.',
    ':: Uning qizi zinapoyaga yolg\'iz chiqdi va chiroqni yoqdi.',
    '',
    '# Qanday yoziladi',
    '',
    'Har gap alohida qatorda turadi.',
    ':: Bu qatorning tarjimasi — gapdan keyin `::` bilan yoziladi.',
    'So\'z tarjimasi gap ichida shunday yoziladi: {word|so\'z}.',
    ':: Faqat kerakli so\'zlarni belgilash yetarli, hammasi shart emas.'
  ].join('\n');

  var SAMPLE_RU = [
    '# Старый маяк',
    '',
    '{Старый|eski} {маяк|mayoq} стоял на {скале|qoya} над морем.',
    ':: Eski mayoq dengiz ustidagi qoyada turardi.',
    'Каждую {ночь|kecha} его свет {указывал|yo\'l ko\'rsatardi} путь {кораблям|kemalarga}.',
    ':: Har kecha uning nuri kemalarga yo\'l ko\'rsatardi.',
    '',
    '# Как писать',
    '',
    'Каждое предложение — на отдельной строке.',
    ':: Har gap alohida qatorda turadi.',
    'Перевод слова пишется так: {слово|so\'z}.',
    ':: So\'z tarjimasi shunday yoziladi.'
  ].join('\n');

  /* AI ga beriladigan TO'LIQ qo'llanma. Foydalanuvchi bu faylni istalgan
     sun'iy intellektga beradi, u esa shu qoidalar bo'yicha matn tayyorlaydi.
     Shuning uchun qo'llanma ilova matnni QANDAY o'qishini ham tushuntiradi —
     AI nima uchun shunday yozish kerakligini bilsa, xato kamayadi. */
  var GUIDE = [
    '# Yordamchi — "O\'qish" (Reading) uchun matn tayyorlash qo\'llanmasi',
    '',
    'Bu faylni sun\'iy intellektga (ChatGPT, Claude va h.k.) bering va',
    '"shu qoidalar bo\'yicha menga matn tayyorla" deng. Quyida formatning',
    'to\'liq tavsifi va tayyor so\'rov (prompt) bor.',
    '',
    '---',
    '',
    '## 1. Bu fayl nimaga xizmat qiladi',
    '',
    'Yordamchi ilovasining "O\'qish" bo\'limi chet tilidagi matnni o\'qish uchun.',
    'Ilova matnni kitobdek chiroyli ko\'rsatadi va uni **interaktiv** qiladi:',
    '',
    '- **so\'zga bosilsa** — o\'sha so\'zning tarjimasi yonida kichik oynachada chiqadi;',
    '- **gapga bosilsa** — butun gapning tarjimasi chiqadi;',
    '- **"Matnni tinglash"** — matn ovoz bilan gap-ma-gap o\'qib beriladi,',
    '  o\'qilayotgan gap belgilanib turadi;',
    '- oynachadagi **"O\'rganish"** tugmasi so\'zni lug\'atga qo\'shadi va uni',
    '  keyin flashcard/test bilan yodlash mumkin.',
    '',
    '**Muhim:** ilova internetdagi tarjimondan FOYDALANMAYDI. Barcha tarjimalar',
    'shu faylning ICHIDA oldindan yozilgan bo\'lishi kerak. Shuning uchun fayl',
    'qanchalik to\'g\'ri yozilsa, bo\'lim shunchalik yaxshi ishlaydi.',
    '',
    '## 2. Format — atigi uchta qoida',
    '',
    '### Qoida 1. Har gap ALOHIDA QATORDA',
    '',
    'Bitta gap — bitta qator. Gapni ikkiga bo\'lib tashlamang.',
    '',
    '### Qoida 2. Gap tarjimasi — keyingi qatorda, `::` bilan',
    '',
    '```',
    'The old lighthouse stood on the cliff.',
    ':: Eski mayoq qoya ustida turardi.',
    '```',
    '',
    '### Qoida 3. So\'z tarjimasi — gap ichida `{so\'z|tarjima}`',
    '',
    '```',
    'The {old|eski} {lighthouse|mayoq} stood on the {cliff|qoya}.',
    ':: Eski mayoq qoya ustida turardi.',
    '```',
    '',
    'Ilova `{...}` ni o\'qiganda ekranda faqat **so\'zning o\'zi** ko\'rinadi',
    '(`old`), tarjimasi esa bosilganda chiqadi.',
    '',
    'Qo\'shimcha: `# Sarlavha` — sarlavha (markazda chiqadi).',
    '',
    '**Bo\'sh qator haqida.** Gap va tarjima juftlari orasida bitta bo\'sh',
    'qator qoldirsangiz ham bo\'ladi — matn baribir kitobdek uzluksiz oqadi.',
    'Yangi XATBOSHI boshlash uchun IKKI bo\'sh qator qoldiring.',
    '',
    '## 3. Nimalarga E\'TIBOR berish kerak',
    '',
    '1. **Hamma so\'zni belgilamang.** Faqat foydalanuvchi bilmasligi mumkin',
    '   bo\'lgan so\'zlarni. `the`, `is`, `and` kabilarni belgilash shart emas —',
    '   aks holda matn nuqtali chiziqlarga to\'lib ketadi va o\'qib bo\'lmaydi.',
    '   Bir gapda odatda 2-5 ta so\'z yetarli.',
    '2. **Har gapga tarjima yozing.** Tarjimasi yo\'q gap bosilganda',
    '   "tarjima yozilmagan" deb chiqadi.',
    '3. **`{}` ichida qator ko\'chirmang** va ichiga yana `{` `}` qo\'ymang.',
    '4. **`|` belgisi** faqat so\'z bilan tarjimani ajratadi. So\'zning o\'zida',
    '   `|` bo\'lmasin.',
    '5. **Tarjima qisqa bo\'lsin** — bir-ikki so\'z. Uzun izoh oynachaga sig\'maydi.',
    '6. **So\'zni matndagi shaklida qoldiring** (`stood`, `climbed`), lekin',
    '   tarjimani o\'sha shaklga mos bering.',
    '7. **Tinish belgisi `{}` dan tashqarida qolsin:** `{cliff|qoya}.` — to\'g\'ri,',
    '   `{cliff.|qoya}` — noto\'g\'ri.',
    '',
    '## 4. To\'liq namuna',
    '',
    '```markdown',
    '# The Old Lighthouse',
    '',
    'The {old|eski} {lighthouse|mayoq} stood on the {cliff|qoya} above the sea.',
    ':: Eski mayoq dengiz ustidagi qoyada turardi.',
    'Every night its light {guided|yo\'l ko\'rsatardi} the {ships|kemalar} home.',
    ':: Har kecha uning nuri kemalarga uyga yo\'l ko\'rsatardi.',
    '',
    'One {winter|qish} the keeper {fell ill|kasal bo\'lib qoldi}.',
    ':: Bir qishda qorovul kasal bo\'lib qoldi.',
    '```',
    '',
    '## 5. AI ga beriladigan tayyor so\'rov',
    '',
    'Quyidagini nusxalab, oxiriga o\'z matningizni qo\'shing:',
    '',
    '```',
    'Menga quyidagi qoidalar bo\'yicha .md fayl tayyorla.',
    '',
    'FORMAT:',
    '- Har gap alohida qatorda.',
    '- Har gapdan keyingi qatorda ":: " bilan o\'sha gapning O\'ZBEKCHA tarjimasi.',
    '- Gap ichida qiyin so\'zlarni {so\'z|o\'zbekcha tarjima} ko\'rinishida belgila.',
    '- Bir gapda 2-5 tadan ortiq so\'z belgilama; the/is/and kabi oddiy',
    '  so\'zlarni belgilama.',
    '- Tarjima qisqa (1-2 so\'z) bo\'lsin.',
    '- Tinish belgilari {} dan tashqarida qolsin.',
    '- Boshida "# Sarlavha" bo\'lsin. Yangi xatboshi kerak bo\'lsa IKKI bo\'sh',
    '  qator qoldir (bitta bo\'sh qator matnni bo\'lmaydi).',
    '- Bir gapda 5 tadan ortiq so\'z belgilama — matn nuqtali chiziqqa to\'lib',
    '  ketsa o\'qib bo\'lmaydi.',
    '- Boshqa hech qanday markdown belgisi ishlatma (jadval, ro\'yxat, ** yo\'q).',
    '- Javobni faqat .md matn sifatida ber, izohsiz.',
    '',
    'MATN:',
    '<shu yerga matnni qo\'ying yoki "B1 darajada 200 so\'zlik hikoya yoz" deng>',
    '```',
    '',
    '## 6. Tayyor bo\'lgach',
    '',
    'Faylni "O\'qish" bo\'limida qalam tugmasi -> ".md fayl yuklash" orqali',
    'yuklang. Shu yerdagi **"O\'rganish lug\'ati"** dan so\'zlar qaysi lug\'atga',
    'tushishini tanlab qo\'ying — keyin ularni Lug\'at bo\'limida yodlaysiz.',
    ''
  ].join('\n');

  App.actions.rdGuide = function () {
    App.closeSheet();
    App.download('yordamchi-oqish-qollanma.md', GUIDE);
    App.toast('Qo\'llanma yuklandi — uni AI ga bering');
  };

  App.actions.rdSample = function (a) {
    App.closeSheet();
    var ru = String((a && a.sec) || R.sec).indexOf('ru_') === 0;
    App.download(ru ? 'namuna-chtenie.md' : 'namuna-reading.md', ru ? SAMPLE_RU : SAMPLE_EN);
    App.toast('Namuna fayl yuklandi — shu formatda yozing');
  };

  /* ================= VIEW: reading_doc ================= */

  App.view('reading_doc', {
    nav: 'languages',
    leave: function () { stopAll(); closePop(); },
    render: function (page, params) {
      R.sec = params.sec || 'en_reading';
      R.id = params.id;
      R.lang = ttsLang(R.sec);
      R.blocks = []; R.sentences = []; R.idx = -1;
      R.playing = false; R.alive = true; R.barOpen = false;
      try { R.rate = parseFloat(localStorage.getItem('reading_rate')) || 1; } catch (e) { R.rate = 1; }
      try { R.stepMode = localStorage.getItem('reading_step_mode') === '1'; } catch (e) { R.stepMode = false; }
      R.pendingStop = false;

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="rd-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 id="rd-title"></h1>' +
        '<button class="icon-btn ghost" id="rd-menu" style="margin-left:auto"><span data-icon="edit" data-icon-size="18"></span></button></div>' +
        '<div id="rd-body"><div class="load-wrap"><div class="spinner"></div></div></div>' +
        '<div class="rd-player" id="rd-player"></div>' +
        '<input type="file" id="rd-file" hidden accept=".md,.markdown,.txt,text/markdown,text/plain">';
      App.icons(page);
      loadDoc(page);
    }
  });

  function loadDoc(page) {
    App.call('get_topic', null, { query: 'id=' + encodeURIComponent(R.id) }).then(function (t) {
      var box = App.el('rd-body'); if (!box) return;
      R.name = t.name || 'Matn';
      var folder = (t.folder || '').trim();

      var back = page.querySelector('#rd-back');
      if (back) {
        back.setAttribute('data-act', 'go');
        back.setAttribute('data-arg', App.arg({ v: 'library', p: { sec: R.sec, path: folder } }));
      }

      if (!t.content) {
        box.innerHTML = App.empty({
          icon: 'book', title: 'Matn hali yo\'q',
          text: 'Tepadagi ✏ orqali .md yuklang yoki yozing. Format bilan tanishish uchun namuna faylni oling.'
        }) +
        '<button class="btn sec" data-act="rdSample" data-arg=\'' + App.arg({ sec: R.sec }) + '\' style="margin-top:12px">' +
        '<span data-icon="download" data-icon-size="16"></span>Namuna faylni yuklab olish</button>';
        App.icons(box);
        bindMenu(page, t);
        return;
      }

      var parsed = parse(t.content);
      R.blocks = parsed.blocks;
      R.sentences = parsed.sentences;

      /* Sarlavha: matnning birinchi `#` sarlavhasi bo'lsa o'sha, bo'lmasa
         fayl nomi. Ikki marta chiqmasligi uchun birinchisi bloklardan
         olib tashlanadi. */
      var title = R.name;
      if (parsed.blocks.length && parsed.blocks[0].k === 'h' && parsed.blocks[0].lvl === 1) {
        title = parsed.blocks[0].text;
        parsed.blocks = parsed.blocks.slice(1);
      }

      box.innerHTML =
        '<h1 class="rd-title">' + App.esc(title) + '</h1>' +
        '<div class="rd-text">' + bodyHtml(parsed) + '</div>';
      App.icons(box);

      // Topbar sarlavhasi qisqa qolsin (fayl nomi), asosiysi matn ustida
      var h1 = page.querySelector('#rd-title');
      if (h1) h1.textContent = R.name;

      paintPlayer();
      bindMenu(page, t);
    }).catch(function (e) {
      var box = App.el('rd-body');
      if (box) box.innerHTML = App.empty({ icon: 'alert', title: 'Yuklanmadi', text: e.message });
    });
  }

  function bindMenu(page, t) {
    var btn = page.querySelector('#rd-menu'); if (!btn) return;
    btn.onclick = function () {
      var html =
        '<button class="list-row" data-act="rdPickDict">' +
        '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="list" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">O\'rganish lug\'ati</div>' +
        '<div class="li-sub">' + App.esc(targetCat()) + '</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="15" style="transform:rotate(180deg)"></span></button>' +
        '<button class="list-row" id="rd-m-ed"><span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? 'Tahrirlash' : 'Yozish') + '</div>' +
        '<div class="li-sub">Tarjimalarni shu yerda qo\'shasiz</div></div></button>' +
        '<button class="list-row" id="rd-m-up"><span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? '.md faylni almashtirish' : '.md fayl yuklash') + '</div></div></button>' +
        (t.content
          ? '<button class="list-row" id="rd-m-dl"><span class="li-ic" data-icon="download" data-icon-size="15"></span>' +
            '<div class="li-main"><div class="li-title">.md faylni yuklab olish</div></div></button>'
          : '') +
        '<button class="list-row" data-act="rdGuide">' +
        '<span class="li-ic" style="background:var(--purple-soft,var(--card-2))" data-icon="file" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">AI uchun qo\'llanma</div>' +
        '<div class="li-sub">Shu faylni AI ga bering — to\'g\'ri matn tayyorlab beradi</div></div></button>' +
        '<button class="list-row" data-act="rdSample" data-arg=\'' + App.arg({ sec: R.sec }) + '\'>' +
        '<span class="li-ic" data-icon="book" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">Namuna fayl</div>' +
        '<div class="li-sub">Qisqa misol — format qanday ko\'rinishini ko\'rsatadi</div></div></button>';
      var sh = App.sheet(html, { title: R.name });
      App.icons(sh);
      sh.querySelector('#rd-m-up').onclick = function () { App.closeSheet(); App.el('rd-file').click(); };
      sh.querySelector('#rd-m-ed').onclick = function () { App.closeSheet(); editDoc(page, t); };
      var dl = sh.querySelector('#rd-m-dl');
      if (dl) dl.onclick = function () { App.closeSheet(); App.download(R.name + '.md', t.content); };
    };

    var fEl = App.el('rd-file');
    if (fEl) fEl.onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
      var fr = new FileReader();
      fr.onload = function () {
        App.call('upload_topic_content', { id: R.id, part: 'content', content: String(fr.result || '') })
          .then(function () { App.toast('✅ Yuklandi'); loadDoc(page); })
          .catch(function (err) { App.toast('⚠️ ' + err.message); });
      };
      fr.readAsText(f);
      fEl.value = '';
    };
  }

  function editDoc(page, t) {
    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 10px">' +
      'Har gap alohida qatorda. Gap tarjimasi keyingi qatorda <code>::</code> bilan. ' +
      'So\'z tarjimasi gap ichida <code>{word|so\'z}</code>.</p>' +
      '<label class="field"><span>Matn</span><textarea class="textarea" id="rd-ta" spellcheck="false">' +
      App.esc(t.content || '') + '</textarea></label>' +
      '<div class="btn-row"><button class="btn sec" data-act="closeSheet">Bekor</button>' +
      '<button class="btn" id="rd-ta-save">Saqlash</button></div>';
    var sh = App.sheet(html, { title: R.name, cls: 'editor-sheet' });
    sh.querySelector('#rd-ta-save').onclick = function () {
      App.call('upload_topic_content', { id: R.id, part: 'content', content: sh.querySelector('#rd-ta').value })
        .then(function () { App.closeSheet(); App.toast('✅ Saqlandi'); loadDoc(page); })
        .catch(function (err) { App.toast('⚠️ ' + err.message); });
    };
  }

  /* Kutubxona "Qo'shish" menyusi Reading bo'limida namuna faylni ham taklif qiladi */
  window.Reading = { isReadingSec: function (sec) { return /^(en|ru)_reading$/.test(sec || ''); } };

  /* Audirovaniye (listening-doc.js) AYNAN shu parser va intonatsiya
     dvigatelini ishlatadi — bir xil `.md` format, ikki xil mashq. Kod
     nusxa ko'chirilmasin: formatga o'zgartirish kiritilsa, ikkala bo'lim
     birga yangilanishi kerak. */
  window.RDCore = {
    parse: parse,
    prosodyParts: prosodyParts,
    plainText: plainText,
    ttsLang: ttsLang,
    dictLang: dictLang
  };

})();
