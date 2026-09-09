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
    pendingStop: false,
    repeatCount: 1,       // 1 (oddiy), 2 (2x), 3 (3x) takrorlash
    repeatIdx: 1,         // joriy gap nechanchi marta o'qilyapti (1..repeatCount)
    shadowMode: false,    // Hands-Free Shadowing: gapdan so'ng takrorlash uchun pauza
    shadowSecondsLeft: 0,
    shadowTimer: null
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
  function clearShadowTimer() {
    if (R.shadowTimer) { clearInterval(R.shadowTimer); R.shadowTimer = null; }
    if (R.gapTimer) { clearTimeout(R.gapTimer); R.gapTimer = null; }
    R.shadowSecondsLeft = 0;
  }

  function getShadowPause(text) {
    var words = (text || '').trim().split(/\s+/).filter(Boolean).length;
    return Math.max(3, Math.min(10, Math.round(words * 0.55) + 2));
  }

  /* Ovozni ham, KUTAYOTGAN TAYMERLARNI ham birga to'xtatadi.
     Ikkalasi birga bekor qilinmasa, to'xtatilgandan keyin osilib qolgan
     taymer eski bo'lakni o'qib yuboradi (`R.alive` hamma joyda ham
     o'chirilmaydi — masalan "keyingi gap" bosilganda u ataylab yoqiladi). */
  function haltSpeech() {
    clearShadowTimer();
    /* Yuklanib kelayotgan gap TO'XTATILGANDAN KEYIN yangramasin. */
    audioGen++;
    if (playerAudio) {
      playerAudio.onended = null;
      playerAudio.onerror = null;
      try { playerAudio.pause(); } catch (e) {}
    }
    stopAudioKeepAlive();
    if (R.partTimer) { clearTimeout(R.partTimer); R.partTimer = null; }
    if (window.TTS) TTS.cancel(); else { try { window.speechSynthesis.cancel(); } catch (e) {} }
  }

  /* ---------- Fondagi va Lockscreen Audio Pleyeri ----------
     Mobil qurilmalarda (Android/iOS) ekran qulflanganda yoki foydalanuvchi
     boshqa ilovalarga o'tganda brauzer `speechSynthesis` ni to'xtatib qo'yadi.
     Uzluksiz fon ijrosi uchun HTML5 `<audio>` elementi orqali haqiqiy MP3
     oqimi yangraydi va gaplar orasidagi pauzada ham audio sessiya tirik saqlanadi. */
  var playerAudio = null;
  var audioKeeper = null;
  /* Har ijroga yangi raqam. Yuklash tugaguncha foydalanuvchi boshqa gapga
     o'tsa, kechikib kelgan javob ESKI gapni yangratmasligi kerak. */
  var audioGen = 0;
  var SILENT_AUDIO = 'data:audio/wav;base64,UklGRjIAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAAABmYWN0BAAAAAAAAABkYXRhAAAAAA==';

  function getPlayerAudio() {
    if (!playerAudio) {
      playerAudio = new Audio();
      playerAudio.preload = 'auto';
    }
    return playerAudio;
  }

  /* ---------- Audio bufer ----------
     MUAMMO: saytda ovoz yuklab olingan MP3 dan YOMONROQ eshitilardi. Ovoz
     bir xil (ikkalasi ham serverdagi bir xil Google TTS), farq UZLUKSIZLIKDA
     edi: yuklab olingan fayl bitta yaxlit MP3, saytda esa har gap uchun
     alohida so'rov ketardi va u AYNAN o'sha gap boshlanishi kerak paytda
     boshlanardi. Tarmoq sekin bo'lsa gaplar orasida sukut cho'ziladi;
     so'rov uzilsa esa brauzerning robot ovoziga o'tib ketardi — o'shanda
     "sayt yomon" eshitiladi.

     YECHIM: gaplar OLDINDAN yuklab qo'yiladi (blob sifatida xotirada).
     Navbatdagi gap yangraganda fayl allaqachon tayyor — ijro darhol
     boshlanadi. Bufer chegaralangan: eng eskisi o'chirilib turadi
     (`URL.revokeObjectURL` bo'lmasa xotira oqib ketardi). */
  var AUDIO_BUF_MAX = 14;      // xotirada saqlanadigan gap soni
  var AUDIO_AHEAD = 3;         // oldindan yuklanadigan gap soni
  var audioBuf = {};           // kalit -> { url } yoki { p: Promise }
  var audioOrder = [];         // kalitlar — kelish tartibida (eskisi birinchi)

  function audioSrc(text) {
    var langCode = (R.lang || '').indexOf('ru') === 0 ? 'ru' : 'en';
    return '/api?action=tts_audio&text=' + encodeURIComponent(text) + '&lang=' + langCode;
  }
  function audioKey(text) {
    return ((R.lang || '').indexOf('ru') === 0 ? 'ru|' : 'en|') + text;
  }

  function bufTrim() {
    while (audioOrder.length > AUDIO_BUF_MAX) {
      var k = audioOrder.shift();
      var e = audioBuf[k];
      delete audioBuf[k];
      if (e && e.url) { try { URL.revokeObjectURL(e.url); } catch (err) {} }
    }
  }

  function bufClear() {
    audioOrder.forEach(function (k) {
      var e = audioBuf[k];
      if (e && e.url) { try { URL.revokeObjectURL(e.url); } catch (err) {} }
    });
    audioBuf = {}; audioOrder = [];
  }

  /* Bitta gap uchun MP3 ni oladi. Keshda bo'lsa darhol, bo'lmasa yuklaydi.
     Bir marta QAYTA URINADI: bitta uzilgan so'rov uchun butun o'qishni
     robot ovozga o'tkazish juda qo'pol. */
  function fetchAudio(text, tries) {
    var key = audioKey(text);
    var hit = audioBuf[key];
    if (hit) return hit.p || Promise.resolve(hit.url);

    var p = fetch(audioSrc(text), { credentials: 'same-origin', cache: 'default' })
      .then(function (r) {
        if (!r.ok) throw new Error('tts ' + r.status);
        return r.blob();
      })
      .then(function (b) {
        if (!b || b.size < 200) throw new Error('tts bo\'sh');
        var url = URL.createObjectURL(b);
        /* Kalit `audioOrder` ga QUYIDA, kutish yozuvi bilan birga bir marta
           qo'shiladi. Bu yerda yana qo'shilsa ro'yxatda ikki nusxa paydo
           bo'lardi va `bufTrim` birinchisini o'chirganda endigina yuklangan
           (hatto hozir yangrayotgan) ovozning URL i bekor qilinardi. */
        audioBuf[key] = { url: url };
        bufTrim();
        return url;
      })
      .catch(function (e) {
        delete audioBuf[key];
        var n = tries == null ? 1 : tries;
        if (n > 0) return fetchAudio(text, n - 1);
        throw e;
      });

    audioBuf[key] = { p: p };
    /* Kalit ro'yxatda BIR MARTA turadi. Qayta urinish (`catch` -> `fetchAudio`)
       ham shu yerdan o'tadi — tekshiruvsiz bo'lsa ikki nusxa qolib ketardi. */
    if (audioOrder.indexOf(key) < 0) audioOrder.push(key);
    return p;
  }

  /* Keyingi bir necha gapni jimgina yuklab qo'yadi. */
  function preloadNextSentence(nextIdx) {
    if (!R.sentences) return;
    for (var i = 0; i < AUDIO_AHEAD; i++) {
      var n = nextIdx + i;
      if (n < 0 || n >= R.sentences.length) break;
      var t = R.sentences[n] && R.sentences[n].text;
      if (t) fetchAudio(t).catch(function () {});   // xato bo'lsa ijro paytida qayta uriniladi
    }
  }

  function startAudioKeepAlive() {
    try {
      if (!audioKeeper) {
        audioKeeper = new Audio(SILENT_AUDIO);
        audioKeeper.loop = true;
      }
      var p = audioKeeper.play();
      if (p && p.catch) p.catch(function () {});
    } catch (e) {}
  }

  function stopAudioKeepAlive() {
    if (audioKeeper) {
      try { audioKeeper.pause(); } catch (e) {}
    }
  }

  function keepAudioAliveDuringPause() {
    startAudioKeepAlive();
  }

  function playSentenceAudio(text, done) {
    text = String(text || '').trim();
    if (!text) { if (done) done(200); return; }

    var audio = getPlayerAudio();
    audio.loop = false;
    audio.playbackRate = R.rate || 1;
    /* Tezlik o'zgarganda ovoz "cholg'u"ga aylanmasin (Chrome standarti
       ovoz balandligini ham suradi). */
    try {
      audio.preservesPitch = true;
      audio.mozPreservesPitch = true;
      audio.webkitPreservesPitch = true;
    } catch (e) {}

    var myGen = ++audioGen;
    var finished = false;
    function onFinish(p) {
      if (finished) return;
      finished = true;
      audio.onended = null;
      audio.onerror = null;
      if (done) done(p || 260);
    }
    function fallback() {
      if (myGen !== audioGen) return;
      speakProsody(text, function (p) { onFinish(p); });
    }

    /* Navbatdagi gaplarni ijro BOSHLANISHIDAN oldin so'raymiz — shunda
       ular hozirgi gap yangrayotgan paytda yuklanib ulguradi. */
    preloadNextSentence(R.idx + 1);

    fetchAudio(text).then(function (url) {
      if (myGen !== audioGen) return;               // orada boshqa gapga o'tildi
      audio.onended = function () { onFinish(260); };
      audio.onerror = fallback;
      audio.src = url;
      var p = audio.play();
      if (p && p.catch) p.catch(fallback);
    }).catch(fallback);
  }

  function setupMediaSession() {
    if (!('mediaSession' in navigator)) return;
    try {
      navigator.mediaSession.setActionHandler('play', function () {
        if (!R.playing) App.actions.rdToggle();
      });
      navigator.mediaSession.setActionHandler('pause', function () {
        if (R.playing) App.actions.rdToggle();
      });
      navigator.mediaSession.setActionHandler('previoustrack', function () {
        jump(-1);
      });
      navigator.mediaSession.setActionHandler('nexttrack', function () {
        jump(1);
      });
      navigator.mediaSession.setActionHandler('stop', function () {
        stopAll();
      });
    } catch (e) {}
  }

  function updateMediaSession() {
    if (!('mediaSession' in navigator)) return;
    try {
      var cur = (R.idx >= 0 && R.sentences && R.sentences[R.idx]) ? R.sentences[R.idx] : null;
      var title = cur ? cur.text : (R.name || 'Reading');
      var artist = R.name || (R.sec.indexOf('ru') === 0 ? 'Чтение' : 'Reading');
      var album = R.sec.indexOf('ru') === 0 ? 'Rus tili (Чтение)' : 'Ingliz tili (Reading)';

      if (window.MediaMetadata) {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: title,
          artist: artist,
          album: album,
          artwork: [
            { src: '/assets/icons/custom-app-icon-192.png', sizes: '192x192', type: 'image/png' },
            { src: '/assets/icons/custom-app-icon-512.png', sizes: '512x512', type: 'image/png' }
          ]
        });
      }
      navigator.mediaSession.playbackState = R.playing ? 'playing' : 'paused';
    } catch (e) {}
  }

  function stopAll() {
    R.playing = false;
    R.alive = false;
    R.repeatIdx = 1;
    /* Gaplar orasidagi kutish ham bekor qilinsin — aks holda to'xtatilgandan
       keyin yana bitta gap o'qilib ketardi. */
    haltSpeech();
    stopAudioKeepAlive();
    updateMediaSession();
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
      R.repeatIdx = 1;
      highlight(n);
      updateMediaSession();
      paintPlayer();
      return;
    }

    if (n >= R.sentences.length) {
      R.playing = false; R.idx = -1; R.repeatIdx = 1;
      clearShadowTimer();
      stopAudioKeepAlive();
      updateMediaSession();
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
    updateMediaSession();
    paintPlayer();
    var cur = R.sentences[n];
    /* Sarlavha ham, gaplar ham real MP3 orqali o'qiladi — fonda va lockscreen'da to'xtamaydi */
    if (cur.k === 'h') {
      playSentenceAudio(cur.text, function () {
        R.repeatIdx = 1;
        if (R.stepMode) R.pendingStop = true;
        keepAudioAliveDuringPause();
        R.gapTimer = setTimeout(function () { step(n + 1); }, Math.round(700 / (R.rate || 1)));
      });
      return;
    }
    playSentenceAudio(cur.text, function (endPause) {
      if (!R.alive || !R.playing) return;

      /* Gapni 2-3 marta takrorlash funksiyasi */
      if (R.repeatCount > 1 && R.repeatIdx < R.repeatCount) {
        R.repeatIdx++;
        paintPlayer();
        keepAudioAliveDuringPause();
        var repPause = Math.round(340 / (R.rate || 1));
        R.gapTimer = setTimeout(function () { step(n); }, repPause);
        return;
      }

      /* Barcha takrorlar tugadi */
      R.repeatIdx = 1;
      if (R.stepMode) {
        R.pendingStop = true;   // keyingi qadamda to'xtaydi
        keepAudioAliveDuringPause();
        var pause = Math.round((endPause || 260) / (R.rate || 1));
        R.gapTimer = setTimeout(function () { step(n + 1); }, pause);
        return;
      }

      /* Hands-Free Shadowing rejimi: gapdan keyin takrorlash pauzasi */
      if (R.shadowMode) {
        clearShadowTimer();
        keepAudioAliveDuringPause();
        var waitSec = getShadowPause(cur.text);
        R.shadowSecondsLeft = waitSec;
        paintPlayer();
        R.shadowTimer = setInterval(function () {
          if (!R.alive || !R.playing) { clearShadowTimer(); return; }
          R.shadowSecondsLeft--;
          if (R.shadowSecondsLeft <= 0) {
            clearShadowTimer();
            paintPlayer();
            step(n + 1);
          } else {
            paintPlayerTime();
          }
        }, 1000);
        return;
      }

      keepAudioAliveDuringPause();
      var pause = Math.round((endPause || 260) / (R.rate || 1));
      R.gapTimer = setTimeout(function () { step(n + 1); }, pause);
    });
  }

  /* ================= Pastki pleyer =================
     Yopiq holatda — bitta tugma. Bosilganda videopleyerdagidek boshqaruv
     paneliga ochiladi: oldingi/keyingi gap, play/pause, progress, tezlik,
     2-3x takrorlash va audio yuklab olish. */

  function paintPlayer() {
    var box = App.el('rd-player'); if (!box) return;
    /* Surish davomida panel qayta chizilmaydi — barmoq ostidagi element
       almashsa surish uzilib qolardi. */
    if (R.seeking) return;

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

    var repInfo = '';
    if (R.shadowSecondsLeft > 0) {
      repInfo = ' · <span class="rd-shadow-badge">🗣️ Qaytaring: ' + R.shadowSecondsLeft + 's</span>';
    } else if (R.repeatCount > 1) {
      if (R.playing && cur > 0) {
        repInfo = ' · ' + R.repeatIdx + '/' + R.repeatCount + ' marta';
      } else {
        repInfo = ' · ' + R.repeatCount + 'x takror';
      }
    }

    box.className = 'rd-player open';
    box.innerHTML =
      '<div class="rd-pl-top">' +
        '<div class="rd-pl-time">' + cur + ' / ' + total + ' gap' + repInfo + '</div>' +
        '<div class="rd-pl-top-actions">' +
          '<button class="rd-pl-tool-btn" data-act="rdCheckCurrentPronun" aria-label="Talaffuzni tekshirish" title="Talaffuzni tekshirish (mikrofon)">' +
            '<span data-icon="mic" data-icon-size="15"></span></button>' +
          '<button class="rd-pl-tool-btn" data-act="rdDownloadAudio" aria-label="Audioni yuklab olish" title="Ovozni yuklab olish (.mp3)">' +
            '<span data-icon="download" data-icon-size="15"></span></button>' +
          '<button class="rd-pl-tool-btn" data-act="rdVoice" aria-label="Ovozni tanlash" title="Ovozni tanlash">' +
            '<span data-icon="volume" data-icon-size="15"></span></button>' +
          '<button class="rd-pl-x" data-act="rdCloseBar" aria-label="Yopish">' +
            '<span data-icon="close" data-icon-size="16"></span></button>' +
        '</div>' +
      '</div>' +
      '<div class="rd-pl-seek" id="rd-seek">' +
        '<div class="rd-pl-track"><div class="rd-pl-fill" style="width:' + pct + '%"></div>' +
        '<div class="rd-pl-knob" style="left:' + pct + '%"></div></div></div>' +
      '<div class="rd-pl-ctrls">' +
        '<div class="rd-pl-side left">' +
          '<button class="rd-pl-step' + (R.repeatCount > 1 ? ' on' : '') + '" data-act="rdRepeat" ' +
            'aria-label="Gapni takrorlash" title="Har bir gapni 2 yoki 3 marta takrorlash">' +
            '<span data-icon="repeat" data-icon-size="14"></span>' +
            '<span class="rd-pl-badge">' + R.repeatCount + 'x</span></button>' +
          '<button class="rd-pl-step' + (R.shadowMode ? ' shadow-on' : '') + '" data-act="rdShadow" ' +
            'aria-label="Shadowing rejim" title="Hands-Free Shadowing: gapdan keyin takrorlash pauzasi">' +
            '<span data-icon="headphones" data-icon-size="14"></span>' +
            '<span class="rd-pl-badge">SH</span></button>' +
        '</div>' +
        '<div class="rd-pl-center">' +
          '<button class="rd-pl-b" data-act="rdPrev" aria-label="Oldingi gap">' +
            '<span data-icon="skipBack" data-icon-size="20"></span></button>' +
          '<button class="rd-pl-play" data-act="rdToggle" aria-label="' + (R.playing ? 'To\'xtatish' : 'Boshlash') + '">' +
            '<span data-icon="' + (R.playing ? 'pause' : 'play') + '" data-icon-size="24"></span></button>' +
          '<button class="rd-pl-b" data-act="rdNext" aria-label="Keyingi gap">' +
            '<span data-icon="skipFwd" data-icon-size="20"></span></button>' +
        '</div>' +
        '<div class="rd-pl-side right">' +
          '<button class="rd-pl-step' + (R.stepMode ? ' on' : '') + '" data-act="rdStepMode" ' +
            'aria-label="Gap-ma-gap rejim" title="Gap-ma-gap: har gapdan keyin to\'xtash">' +
            '<span data-icon="pauseDot" data-icon-size="15"></span></button>' +
          '<button class="rd-pl-rate" data-act="rdSpeed" title="O\'qish tezligi">' + rateLabel() + '</button>' +
        '</div>' +
      '</div>';
    App.icons(box);
  }

  function paintPlayerTime() {
    if (R.seeking) return;          // surish paytida raqamni barmoq boshqaradi
    var el = document.querySelector('#rd-player .rd-pl-time');
    if (!el) return;
    var total = R.sentences.length || 1;
    var cur = R.idx < 0 ? 0 : R.idx + 1;
    var repInfo = '';
    if (R.shadowSecondsLeft > 0) {
      repInfo = ' · <span class="rd-shadow-badge">🗣️ Qaytaring: ' + R.shadowSecondsLeft + 's</span>';
    } else if (R.repeatCount > 1) {
      if (R.playing && cur > 0) {
        repInfo = ' · ' + R.repeatIdx + '/' + R.repeatCount + ' marta';
      } else {
        repInfo = ' · ' + R.repeatCount + 'x takror';
      }
    }
    el.innerHTML = cur + ' / ' + total + ' gap' + repInfo;
  }

  function rateLabel() { return String(R.rate).replace(/\.?0+$/, '') + 'x'; }

  App.actions.rdOpenBar = function () {
    R.barOpen = true;
    paintPlayer();
    /* Panel ochilishi — "hozir tinglayman" degani. Birinchi gaplarni shu
       payt yuklab qo'yamiz: ▶ bosilganda kutish bo'lmaydi. */
    preloadNextSentence(R.idx < 0 ? 0 : R.idx);
  };
  App.actions.rdCloseBar = function () {
    if (R.playing) { R.playing = false; haltSpeech(); highlight(-1); }
    R.barOpen = false; paintPlayer();
  };

  App.actions.rdToggle = function () {
    if (R.playing) {
      R.playing = false;
      haltSpeech();
      stopAudioKeepAlive();
      updateMediaSession();
      releaseWake();
      paintPlayer();
      return;
    }
    if (!R.sentences.length) { App.toast('Matnda o\'qiladigan gap yo\'q'); return; }
    /* Birinchi matn ba'zan "yutib yuboriladi" — foydalanuvchi harakatidan
       (aynan shu bosishdan) foydalanib ovozni isitib olamiz. */
    if (window.TTS) TTS.prime();
    requestWake();
    startAudioKeepAlive();
    R.errCount = 0;
    R.playing = true; R.alive = true;
    R.repeatIdx = 1;
    setupMediaSession();
    updateMediaSession();
    step(R.idx >= 0 && R.idx < R.sentences.length ? R.idx : 0);
  };

  App.actions.rdPrev = function () { jump(-1); };
  App.actions.rdNext = function () { jump(1); };
  /* ---------- Surib o'tish (seek) ----------
     Chiziq ilgari faqat KO'RSATKICH edi — bosish ham, surish ham hech
     narsa qilmasdi. Endi u boshqa pleyerlardagidek: barmoqni bosib
     surganda gap raqami jonli o'zgaradi, qo'yib yuborilganda o'sha
     gapdan o'qish davom etadi.

     Surish davomida `R.seeking` yoqiladi va `paintPlayer` panelni QAYTA
     CHIZMAYDI: innerHTML almashsa barmoq ostidagi element yo'qolib,
     surish yarmida uzilib qolardi. */
  function seekTo(n) {
    if (!R.sentences.length) return;
    if (n < 0) n = 0;
    if (n >= R.sentences.length) n = R.sentences.length - 1;
    R.alive = true;
    R.repeatIdx = 1;
    if (R.playing) { haltSpeech(); step(n); }
    else { R.idx = n; highlight(n); updateMediaSession(); paintPlayer(); }
  }

  /* Bosilgan nuqtaning chiziqdagi ulushi -> gap tartib raqami (0 dan). */
  function seekIndexAt(track, clientX) {
    var r = track.getBoundingClientRect();
    if (!r.width) return R.idx < 0 ? 0 : R.idx;
    var ratio = (clientX - r.left) / r.width;
    if (ratio < 0) ratio = 0;
    if (ratio > 1) ratio = 1;
    var total = R.sentences.length;
    /* To'ldirish chizig'i n-gap uchun `(n+1)/total` gacha boradi, ya'ni
       50% — 5-gapning O'NG cheti. Shuning uchun `ceil` — bosilgan nuqta
       qaysi gapning yo'lagiga tushsa, o'sha gap tanlanadi. */
    var n = Math.ceil(ratio * total) - 1;
    if (n < 0) n = 0;
    if (n >= total) n = total - 1;
    return n;
  }

  function paintSeek(n) {
    var box = App.el('rd-player'); if (!box) return;
    var total = R.sentences.length || 1;
    var pct = Math.round(((n + 1) / total) * 100);
    var fill = box.querySelector('.rd-pl-fill');
    var knob = box.querySelector('.rd-pl-knob');
    var time = box.querySelector('.rd-pl-time');
    if (fill) fill.style.width = pct + '%';
    if (knob) knob.style.left = pct + '%';
    if (time) time.innerHTML = (n + 1) + ' / ' + total + ' gap';
  }

  /* Hodisa BIR MARTA, hujjat darajasida bog'lanadi: panel har chizilganda
     qayta bog'lash kerak emas va eski tinglovchilar to'planib qolmaydi. */
  document.addEventListener('pointerdown', function (e) {
    var seek = e.target && e.target.closest && e.target.closest('#rd-seek');
    if (!seek || !R.sentences.length) return;
    var track = seek.querySelector('.rd-pl-track') || seek;

    e.preventDefault();
    R.seeking = true;
    seek.classList.add('dragging');
    var n = seekIndexAt(track, e.clientX);
    paintSeek(n);

    function move(ev) {
      n = seekIndexAt(track, ev.clientX);
      paintSeek(n);
    }
    function up() {
      document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', up);
      document.removeEventListener('pointercancel', up);
      R.seeking = false;
      seek.classList.remove('dragging');
      seekTo(n);
    }
    document.addEventListener('pointermove', move);
    document.addEventListener('pointerup', up);
    document.addEventListener('pointercancel', up);
  });

  function jump(d) {
    if (!R.sentences.length) return;
    /* Hali boshlanmagan (idx = -1) holatda "keyingi" BIRINCHI gapga olib
       boradi — `-1 + 1 = 0` emas, chunki -1 "hali hech qayerda" degani,
       "birinchidan oldin" degani emas (aks holda 1-gap tashlab ketilardi). */
    var n = R.idx < 0 ? 0 : R.idx + d;
    if (n < 0) n = 0;
    if (n >= R.sentences.length) n = R.sentences.length - 1;
    R.alive = true;
    R.repeatIdx = 1;
    if (R.playing) { haltSpeech(); step(n); }
    else { R.idx = n; highlight(n); updateMediaSession(); paintPlayer(); }
  }

  App.actions.rdStepMode = function () {
    R.stepMode = !R.stepMode;
    if (R.stepMode) { R.shadowMode = false; clearShadowTimer(); }
    R.pendingStop = false;
    try { localStorage.setItem('reading_step_mode', R.stepMode ? '1' : '0'); } catch (e) {}
    paintPlayer();
    App.toast(R.stepMode ? 'Gap-ma-gap: har gapdan keyin to\'xtaydi' : 'Uzluksiz o\'qish');
  };

  App.actions.rdRepeat = function () {
    var counts = [1, 2, 3];
    var next = counts[(counts.indexOf(R.repeatCount) + 1) % counts.length];
    R.repeatCount = next;
    R.repeatIdx = 1;
    try { localStorage.setItem('reading_repeat_count', String(R.repeatCount)); } catch (e) {}
    paintPlayer();
    if (R.repeatCount === 1) {
      App.toast('Takrorlash o\'chirildi (1 marta)');
    } else {
      App.toast('Har bir gap ' + R.repeatCount + ' marta takrorlanadi');
    }
  };

  App.actions.rdShadow = function () {
    R.shadowMode = !R.shadowMode;
    if (R.shadowMode) R.stepMode = false;
    clearShadowTimer();
    try { localStorage.setItem('reading_shadow_mode', R.shadowMode ? '1' : '0'); } catch (e) {}
    paintPlayer();
    if (R.shadowMode) {
      App.toast('🗣️ Hands-Free Shadowing yoqildi (gapdan keyin takrorlash uchun pauza beriladi)');
    } else {
      App.toast('Shadowing o\'chirildi');
    }
  };

  /* ---------- Ovozni yuklab olish (MP3) ---------- */
  App.actions.rdDownloadAudio = function () {
    if (!R.sentences || !R.sentences.length) {
      App.toast('Yuklab olish uchun matn topilmadi');
      return;
    }

    var total = R.sentences.length;
    var curIdx = R.idx >= 0 && R.idx < total ? R.idx : 0;
    var curSent = R.sentences[curIdx] ? R.sentences[curIdx].text : '';
    var curShort = curSent.length > 50 ? curSent.slice(0, 47) + '...' : curSent;

    var html =
      '<p class="muted" style="font-size:12px;margin:0 0 14px">' +
      'Matn ovozini yuqori sifatli MP3 formatida yuklab oling. ' +
      'Telefon yoki kompyuterda oflayn tinglash uchun qulay.</p>' +
      '<div class="rd-dl-list">' +
        '<button class="list-row" data-act="rdDoDownloadAudio" data-arg=\'' +
          App.arg({ mode: 'full', repeat: 1 }) + '\'>' +
          '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="download" data-icon-size="16"></span>' +
          '<div class="li-main">' +
            '<div class="li-title">To\'liq matn audiosi (.mp3)</div>' +
            '<div class="li-sub">' + total + ' ta gap · Barcha gaplar ketma-ket</div>' +
          '</div>' +
        '</button>' +
        (R.repeatCount > 1 ?
        '<button class="list-row" data-act="rdDoDownloadAudio" data-arg=\'' +
          App.arg({ mode: 'full', repeat: R.repeatCount }) + '\'>' +
          '<span class="li-ic" style="background:var(--purple-soft,var(--card-2));color:var(--purple,#af52de)" data-icon="repeat" data-icon-size="16"></span>' +
          '<div class="li-main">' +
            '<div class="li-title">Takrorlangan holda yuklab olish (' + R.repeatCount + 'x .mp3)</div>' +
            '<div class="li-sub">Har bir gap ' + R.repeatCount + ' marta takrorlangan MP3</div>' +
          '</div>' +
        '</button>' : '') +
        (curSent ?
        '<button class="list-row" data-act="rdDoDownloadAudio" data-arg=\'' +
          App.arg({ mode: 'current', idx: curIdx, repeat: 1 }) + '\'>' +
          '<span class="li-ic" data-icon="volume" data-icon-size="16"></span>' +
          '<div class="li-main">' +
            '<div class="li-title">Joriy gap audiosi (' + (curIdx + 1) + '-gap .mp3)</div>' +
            '<div class="li-sub">' + App.esc(curShort) + '</div>' +
          '</div>' +
        '</button>' : '') +
      '</div>';

    var sh = App.sheet(html, { title: 'Audioni yuklab olish (.mp3)' });
    App.icons(sh);
  };

  App.actions.rdDoDownloadAudio = function (a) {
    App.closeSheet();
    if (!R.sentences || !R.sentences.length) return;

    var sents = [];
    var title = (R.name || 'reading_audio').trim();
    var rep = parseInt(a && a.repeat, 10) || 1;

    if (a && a.mode === 'current') {
      var idx = parseInt(a.idx, 10);
      if (isNaN(idx) || idx < 0 || idx >= R.sentences.length) idx = R.idx >= 0 ? R.idx : 0;
      var cur = R.sentences[idx];
      if (cur && cur.text) {
        sents = [cur.text];
        title += '_gap_' + (idx + 1);
      }
    } else {
      R.sentences.forEach(function (s) {
        if (s.text) sents.push(s.text);
      });
    }

    if (!sents.length) {
      App.toast('Yuklab olish uchun matn bo\'sh');
      return;
    }

    App.toast('⏳ Audio tayyorlanmoqda, biroz kuting...');

    var langCode = R.lang.indexOf('ru') === 0 ? 'ru' : 'en';

    fetch('/api?action=tts_download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sentences: sents,
        lang: langCode,
        repeat: rep,
        title: title
      })
    }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return {}; }).then(function (j) {
          throw new Error(j.message || j.error || ('HTTP ' + res.status));
        });
      }
      return res.blob();
    }).then(function (blob) {
      var url = window.URL.createObjectURL(blob);
      var link = document.createElement('a');
      link.href = url;
      var safeName = title.replace(/[^\w\sа-яА-ЯёЁўқғҳЎҚҒҲ-]/gi, '_').replace(/\s+/g, '_');
      if (rep > 1) safeName += '_' + rep + 'x';
      link.download = safeName + '.mp3';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      App.toast('✅ Audio yuklab olindi');
    }).catch(function (err) {
      App.toast('⚠️ Yuklab olishda xatolik: ' + err.message);
    });
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
    if (playerAudio) {
      playerAudio.playbackRate = R.rate;
    }
    paintPlayer();
    if (R.playing && !playerAudio) { haltSpeech(); step(R.idx < 0 ? 0 : R.idx); }
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
        '<button class="rd-pop-b" data-act="rdSayRepeat" data-arg=\'' + App.arg({ t: opts.say, count: 2 }) + '\' title="2 marta takrorlab tinglash">' +
        '<span data-icon="repeat" data-icon-size="14"></span>2x</button>' +
        '<button class="rd-pop-b mic" data-act="rdPronunCheck" data-arg=\'' +
          App.arg({ t: opts.say, tr: opts.tr, n: opts.sent }) + '\' title="Talaffuzni tekshirish">' +
        '<span data-icon="mic" data-icon-size="14"></span>Talaffuz</button>' +
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
    playSentenceAudio(a && a.t);
  };

  /* Tanlangan gap/so'zni 2 yoki 3 marta takrorlab o'qish */
  App.actions.rdSayRepeat = function (a) {
    var txt = a && a.t;
    if (!txt) return;
    R.alive = true;
    haltSpeech();
    var count = parseInt(a && a.count, 10) || 2;
    var cur = 1;
    function speakOnce() {
      if (!R.alive) return;
      playSentenceAudio(txt, function () {
        if (!R.alive) return;
        if (cur < count) {
          cur++;
          R.gapTimer = setTimeout(speakOnce, Math.round(350 / (R.rate || 1)));
        }
      });
    }
    speakOnce();
  };

  /* ================= Talaffuz tekshiruvi (Pronunciation Check) ================= */

  function normWord(s) {
    return String(s || '').toLowerCase().replace(/[^\wа-яё]/gi, '');
  }

  function levenshtein(a, b) {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;
    var matrix = [];
    for (var i = 0; i <= b.length; i++) matrix[i] = [i];
    for (var j = 0; j <= a.length; j++) matrix[0][j] = j;
    for (var i = 1; i <= b.length; i++) {
      for (var j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(matrix[i - 1][j - 1] + 1, Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1));
        }
      }
    }
    return matrix[b.length][a.length];
  }

  function wordSimilarity(a, b) {
    var na = normWord(a), nb = normWord(b);
    if (!na && !nb) return 100;
    if (!na || !nb) return 0;
    if (na === nb) return 100;
    var dist = levenshtein(na, nb);
    var maxLen = Math.max(na.length, nb.length);
    return Math.max(0, Math.round((1 - dist / maxLen) * 100));
  }

  function compareSentence(target, said) {
    var targetTokens = String(target || '').trim().split(/\s+/).filter(Boolean);
    var saidTokens = String(said || '').trim().split(/\s+/).filter(Boolean);

    var saidIdx = 0;
    var results = [];
    var totalScore = 0;

    for (var i = 0; i < targetTokens.length; i++) {
      var tw = targetTokens[i];
      var bestSim = 0;
      var bestStep = 1;
      var bestSaidIdx = -1;

      var lookEnd = Math.min(saidTokens.length, saidIdx + 4);
      for (var j = saidIdx; j < lookEnd; j++) {
        var s1 = wordSimilarity(tw, saidTokens[j]);
        if (s1 > bestSim) {
          bestSim = s1;
          bestStep = 1;
          bestSaidIdx = j;
        }
        if (j + 1 < saidTokens.length) {
          var s2 = wordSimilarity(tw, saidTokens[j] + saidTokens[j + 1]);
          if (s2 > bestSim) {
            bestSim = s2;
            bestStep = 2;
            bestSaidIdx = j;
          }
        }
      }

      var status = 'bad';
      if (bestSim >= 80) {
        status = 'good';
        saidIdx = bestSaidIdx + bestStep;
      } else if (bestSim >= 50) {
        status = 'warn';
        saidIdx = bestSaidIdx + bestStep;
      }

      totalScore += bestSim;
      results.push({ word: tw, clean: normWord(tw), status: status, sim: bestSim });
    }

    var score = targetTokens.length ? Math.round(totalScore / targetTokens.length) : 0;
    return { score: score, words: results };
  }

  var activePronunRec = null;

  function stopPronunRec() {
    if (activePronunRec) {
      try {
        if (activePronunRec.abort) activePronunRec.abort();
        else activePronunRec.stop();
      } catch (e) {}
      activePronunRec = null;
    }
  }

  function openPronunModal(targetText, targetTr, sentIdx) {
    targetText = String(targetText || '').trim();
    if (!targetText) { App.toast('Talaffuz uchun matn topilmadi'); return; }

    stopAll();
    stopPronunRec();

    var Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
    var hasNext = (typeof sentIdx === 'number' && sentIdx >= 0 && sentIdx + 1 < R.sentences.length);

    var html =
      '<div class="pr-modal">' +
        '<div class="pr-target-card">' +
          '<div class="pr-target-text">' + App.esc(targetText) + '</div>' +
          (targetTr ? '<div class="pr-trans-text">' + App.esc(targetTr) + '</div>' : '') +
          '<div class="pr-listen-wrap">' +
            '<button class="pr-listen-btn" id="pr-listen-btn">' +
              '<span data-icon="volume" data-icon-size="14"></span>To\'g\'ri talaffuzni tinglash</button>' +
          '</div>' +
        '</div>' +
        '<div class="pr-mic-wrap">' +
          '<button class="pr-mic-btn" id="pr-mic-btn" aria-label="Mikrofon">' +
            '<span data-icon="mic" data-icon-size="34"></span></button>' +
          '<div class="pr-status-text" id="pr-status-text">' +
            (Rec ? 'Mikrofonni bosing va ovoz chiqarib o\'qing' : '⚠️ Brauzeringizda mikrofonli tanish yo\'q — yozib tekshirishingiz mumkin') +
          '</div>' +
        '</div>' +
        '<input class="input" id="pr-typed" placeholder="Yoki yozib tekshiring..." autocomplete="off" style="text-align:center;' + (Rec ? 'display:none;' : 'margin-bottom:12px;') + '">' +
        '<div class="pr-result-box" id="pr-result-box" style="display:none;">' +
          '<div style="text-align:center;"><span class="pr-score-badge" id="pr-score-badge"></span></div>' +
          '<div class="pr-words-feedback" id="pr-words-feedback"></div>' +
          '<div class="pr-said-wrap" id="pr-said-wrap"><span class="muted">Siz aytdingiz:</span> <b id="pr-said-val"></b></div>' +
          '<p class="muted" style="font-size:11.5px;text-align:center;margin:8px 0 0">💡 Xato so\'z ustiga bossangiz, uning to\'g\'ri talaffuzini eshitasiz.</p>' +
        '</div>' +
        '<div class="btn-row" style="margin-top:14px">' +
          '<button class="btn sec" data-act="closeSheet">Yopish</button>' +
          (hasNext ? '<button class="btn" id="pr-next-btn">Keyingi gap ➔</button>' : '') +
        '</div>' +
      '</div>';

    var sh = App.sheet(html, { title: 'Talaffuzni tekshirish' });
    App.icons(sh);

    var micBtn = sh.querySelector('#pr-mic-btn');
    var statusText = sh.querySelector('#pr-status-text');
    var listenBtn = sh.querySelector('#pr-listen-btn');
    var typedInput = sh.querySelector('#pr-typed');
    var resultBox = sh.querySelector('#pr-result-box');
    var scoreBadge = sh.querySelector('#pr-score-badge');
    var wordsBox = sh.querySelector('#pr-words-feedback');
    var saidVal = sh.querySelector('#pr-said-val');
    var nextBtn = sh.querySelector('#pr-next-btn');

    listenBtn.onclick = function () {
      playSentenceAudio(targetText);
    };

    function displayResult(said) {
      if (!said) return;
      var comp = compareSentence(targetText, said);
      resultBox.style.display = 'block';
      saidVal.textContent = '"' + said + '"';

      var badgeCls = 'good';
      var msg = 'A\'lo darajada!';
      if (comp.score < 60) {
        badgeCls = 'bad';
        msg = 'Qaytadan urinib ko\'ring';
      } else if (comp.score < 85) {
        badgeCls = 'warn';
        msg = 'Yaxshi! Qizil so\'zlarga e\'tibor bering';
      }

      scoreBadge.className = 'pr-score-badge ' + badgeCls;
      scoreBadge.innerHTML = '<span data-icon="target" data-icon-size="15"></span>' + comp.score + '% aniqlik · ' + msg;
      App.icons(scoreBadge);

      wordsBox.innerHTML = comp.words.map(function (w) {
        return '<span class="pr-word ' + w.status + '" data-clean="' + App.esc(w.clean) + '" title="Tinglash uchun bosing">' +
          App.esc(w.word) + '</span>';
      }).join('');

      wordsBox.querySelectorAll('.pr-word').forEach(function (el) {
        el.onclick = function () {
          var clean = this.getAttribute('data-clean');
          if (clean) speak(clean);
        };
      });
    }

    var isListening = false;
    if (Rec) {
      var rec = new Rec();
      rec.lang = R.lang;
      rec.continuous = false;
      rec.interimResults = false;

      rec.onstart = function () {
        isListening = true;
        micBtn.classList.add('listening');
        statusText.textContent = '🎙️ Eshitilmoqda... Ovoz chiqarib gapiring';
      };

      rec.onresult = function (e) {
        isListening = false;
        micBtn.classList.remove('listening');
        statusText.textContent = 'Natija tahlil qilindi';
        var said = (e.results && e.results[0] && e.results[0][0] && e.results[0][0].transcript) || '';
        displayResult(said.trim());
      };

      rec.onerror = function () {
        isListening = false;
        micBtn.classList.remove('listening');
        statusText.textContent = '⚠️ Xatolik yoki ovoz eshitilmadi. Qayta urinib ko\'ring.';
      };

      rec.onend = function () {
        isListening = false;
        micBtn.classList.remove('listening');
      };

      activePronunRec = rec;

      micBtn.onclick = function () {
        if (isListening) {
          try { rec.stop(); } catch (e) {}
          return;
        }
        try {
          rec.start();
        } catch (e) {
          try { rec.stop(); setTimeout(function () { rec.start(); }, 150); } catch (e2) {}
        }
      };
    } else {
      micBtn.onclick = function () {
        typedInput.style.display = 'block';
        typedInput.focus();
      };
    }

    typedInput.onkeydown = function (e) {
      if (e.key === 'Enter') {
        displayResult(this.value.trim());
        this.value = '';
      }
    };

    if (nextBtn) {
      nextBtn.onclick = function () {
        App.closeSheet();
        stopPronunRec();
        var nextIdx = sentIdx + 1;
        if (R.sentences[nextIdx]) {
          R.idx = nextIdx;
          highlight(nextIdx);
          paintPlayer();
          openPronunModal(R.sentences[nextIdx].text, R.sentences[nextIdx].tr, nextIdx);
        }
      };
    }
  }

  App.actions.rdPronunCheck = function (a) {
    closePop();
    var text = (a && a.t) || '';
    var tr = (a && a.tr) || '';
    var n = (a && typeof a.n === 'number') ? a.n : -1;
    openPronunModal(text, tr, n);
  };

  App.actions.rdCheckCurrentPronun = function () {
    if (!R.sentences || !R.sentences.length) {
      App.toast('Talaffuzni tekshirish uchun matn yo\'q');
      return;
    }
    var idx = R.idx >= 0 ? R.idx : 0;
    var s = R.sentences[idx];
    if (!s) return;
    openPronunModal(s.text, s.tr, idx);
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
    if (window.Auth && Auth.isReadOnly && Auth.isReadOnly()) { App.toast("Faqat administrator uchun"); return; }
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

  /* ---------- C tugmasi — matndagi so'zlarni mashq qilish ----------
     Matnda `{so'z|tarjima}` bilan belgilangan hamma so'z yig'iladi va
     to'g'ridan-to'g'ri Lug'at bo'limidagi mashqlar sahifasi ochiladi
     (flashcard, test, juftlash — hammasi shu yerdan).

     Bu to'plam SERVERGA yozilmaydi: `save_dict_cat` faqat adminda ishlaydi
     va har matn uchun doimiy lug'at yaratish Lug'at ro'yxatini
     bir martalik yozuvlarga to'ldirib yuborardi. Tafsilot — vocab.js
     dagi `App.vocabText`. */
  function textWords() {
    var seen = {}, out = [];
    (R.blocks || []).forEach(function (b) {
      (b.tokens || []).forEach(function (t) {
        if (t.k === 'x' || !t.t) return;               // belgilanmagan so'z
        var w = String(t.w || '').trim();
        var tr = String(t.t || '').trim();
        if (!w || !tr) return;
        var k = w.toLowerCase();
        if (seen[k]) return;
        seen[k] = 1;
        out.push({
          ru: w, uz: tr, note: '', ex: '',
          pairWith: [], meaningGroup: '',
          partOfSpeech: '', pronunciation: '', forms: '', formation: '',
          synonyms: '', antonyms: '', collocations: '', mnemonic: ''
        });
      });
    });
    return out;
  }

  App.actions.rdPractice = function () {
    var words = textWords();
    if (!words.length) {
      App.toast('Bu matnda {so\'z|tarjima} bilan belgilangan so\'z yo\'q');
      return;
    }
    var lang = dictLang(R.sec);
    /* Nomdagi "/" Lug'at bo'limida PAPKA ajratgichi — uni qoldirsak
       to'plam mavjud bo'lmagan papka ichida qolib ketardi. */
    var cat = 'Matn: ' + String(R.name || 'Matn').replace(/\//g, '-').trim();
    App.vocabText.save(lang, cat, words);
    App.go('vocab_practice', { lang: lang, cat: cat });
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
    leave: function () {
      stopAll();
      stopPronunRec();
      closePop();
      stopAudioKeepAlive();
      bufClear();          // blob URL'lar bo'shatilmasa xotira oqib ketadi
    },
    render: function (page, params) {
      R.sec = params.sec || 'en_reading';
      R.id = params.id;
      R.lang = ttsLang(R.sec);
      R.blocks = []; R.sentences = []; R.idx = -1;
      R.playing = false; R.alive = true; R.barOpen = false; R.seeking = false;
      try { R.rate = parseFloat(localStorage.getItem('reading_rate')) || 1; } catch (e) { R.rate = 1; }
      try { R.stepMode = localStorage.getItem('reading_step_mode') === '1'; } catch (e) { R.stepMode = false; }
      try { R.repeatCount = parseInt(localStorage.getItem('reading_repeat_count'), 10) || 1; } catch (e) { R.repeatCount = 1; }
      if (R.repeatCount < 1 || R.repeatCount > 3) R.repeatCount = 1;
      try { R.shadowMode = localStorage.getItem('reading_shadow_mode') === '1'; } catch (e) { R.shadowMode = false; }
      R.repeatIdx = 1;
      R.shadowSecondsLeft = 0;
      R.shadowTimer = null;
      R.pendingStop = false;

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" id="rd-back"><span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1 id="rd-title"></h1>' +
        /* C / V — "matndagi so'zlarni mashq qilish". Lug'at bo'limidagi
           bir xil belgi bilan bir xil ma'noda (C — Словарь, V — Vocabulary). */
        '<button class="icon-btn ghost rd-voc-btn" data-act="rdPractice" style="margin-left:auto" ' +
          'aria-label="Matndagi so\'zlarni mashq qilish" title="Matndagi so\'zlarni mashq qilish">' +
          (dictLang(R.sec) === 'russian' ? 'C' : 'V') + '</button>' +
        '<button class="icon-btn ghost" id="rd-menu"><span data-icon="edit" data-icon-size="18"></span></button></div>' +
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
      var isRO = window.Auth && Auth.isReadOnly && Auth.isReadOnly();
      var html =
        '<button class="list-row" data-act="rdPickDict">' +
        '<span class="li-ic" style="background:var(--accent-soft);color:var(--accent)" data-icon="list" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">O\'rganish lug\'ati</div>' +
        '<div class="li-sub">' + App.esc(targetCat()) + '</div></div>' +
        '<span class="li-chev" data-icon="arrowLeft" data-icon-size="15" style="transform:rotate(180deg)"></span></button>' +
        (isRO ? '' :
        '<button class="list-row" id="rd-m-ed"><span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? 'Tahrirlash' : 'Yozish') + '</div>' +
        '<div class="li-sub">Tarjimalarni shu yerda qo\'shasiz</div></div></button>' +
        '<button class="list-row" id="rd-m-up"><span class="li-ic" data-icon="upload" data-icon-size="15"></span>' +
        '<div class="li-main"><div class="li-title">' + (t.content ? '.md faylni almashtirish' : '.md fayl yuklash') + '</div></div></button>') +
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
      var upEl = sh.querySelector('#rd-m-up');
      if (upEl) upEl.onclick = function () { App.closeSheet(); App.el('rd-file').click(); };
      var edEl = sh.querySelector('#rd-m-ed');
      if (edEl) edEl.onclick = function () { App.closeSheet(); editDoc(page, t); };
      var dl = sh.querySelector('#rd-m-dl');
      if (dl) dl.onclick = function () { App.closeSheet(); App.download(R.name + '.md', t.content); };
    };

    var fEl = App.el('rd-file');
    if (fEl) fEl.onchange = function (e) {
      var f = e.target.files[0]; if (!f) return;
    if (window.Auth && Auth.isReadOnly && Auth.isReadOnly()) { App.toast("Faqat administrator uchun"); return; }

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
    if (window.Auth && Auth.isReadOnly && Auth.isReadOnly()) { App.toast("Faqat administrator uchun"); return; }
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
    dictLang: dictLang,
    compareSentence: compareSentence
  };

})();
