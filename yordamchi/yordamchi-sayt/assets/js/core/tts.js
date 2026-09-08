/* TTS — matnni ovozga aylantirish qatlami.
 *
 * Brauzerning `speechSynthesis` API si sodda ko'rinadi, lekin amalda
 * bir nechta ma'lum nosozligi bor. Bu modul o'shalarni bir joyda yopadi:
 *
 *  1) OVOZ TANLANMASA eng yomoni ishlaydi. Bir tilda bir nechta ovoz
 *     bo'ladi (Android'da "Google русский" va zaxira robot ovoz).
 *     Standart holatda brauzer BIRINCHISINI oladi — u ko'pincha eng
 *     sifatsizi. Shuning uchun ovozlar baholanadi va eng yaxshisi
 *     tanlanadi (foydalanuvchi o'zi ham tanlashi mumkin).
 *
 *  2) `getVoices()` DARHOL bo'sh qaytadi — ro'yxat asinxron yuklanadi.
 *     Sahifa ochilishida o'qilsa hech qanday ovoz topilmaydi.
 *     `onvoiceschanged` kutiladi (vaqt chegarasi bilan).
 *
 *  3) UZUN MATN yarmida to'xtaydi (Chrome'da ~15 soniyadan keyin).
 *     Matn tinish belgilari bo'yicha bo'laklarga bo'linadi.
 *
 *  4) `cancel()` dan keyin DARHOL `speak()` chaqirilsa yangi matn
 *     yo'qoladi. Navbat bo'shashi kutiladi.
 *
 *  5) `onerror` ushlanmasa zanjir JIMGINA uziladi — bitta gap xato
 *     bersa qolgani umuman o'qilmaydi. Har holatda `done` chaqiriladi.
 *
 *  6) Birinchi matn ba'zan "yutib yuboriladi" (Android). Foydalanuvchi
 *     birinchi bosganda ovoz "isitiladi".
 */
(function (root) {
  'use strict';

  var VOICE_KEY = 'tts_voice_v1_';        // + til kodi
  var MAX_CHUNK = 180;                    // bir bo'lakdagi eng ko'p belgi

  var state = { gen: 0, keepAlive: null, primed: false, readyP: null };

  function synth() { return root.speechSynthesis; }
  function ok() { return !!(root.speechSynthesis && root.SpeechSynthesisUtterance); }

  /* ---------- 1. Ovozlar ro'yxati tayyor bo'lishini kutish ---------- */
  function ready() {
    if (!ok()) return Promise.resolve([]);
    if (state.readyP) return state.readyP;
    state.readyP = new Promise(function (resolve) {
      var got = synth().getVoices();
      if (got && got.length) { resolve(got); return; }
      var done = false;
      function finish() {
        if (done) return;
        done = true;
        resolve(synth().getVoices() || []);
      }
      try { synth().addEventListener('voiceschanged', finish); } catch (e) {}
      /* Ba'zi brauzerlarda hodisa umuman kelmaydi — cheksiz kutmaymiz. */
      setTimeout(finish, 2500);
    });
    return state.readyP;
  }

  /* ---------- 2. Ovoz sifatini baholash ----------
     Yuqori ball = yaxshiroq ovoz. Mezonlar amaliy kuzatuvdan:
     "Google"/"Neural"/"Natural"/"Enhanced" nomli ovozlar sezilarli
     tabiiyroq, "eSpeak"/"compact" esa robotsimon. */
  function score(v, lang) {
    var s = 0;
    var name = (v.name || '').toLowerCase();
    var vl = (v.lang || '').replace('_', '-').toLowerCase();
    var want = String(lang || '').replace('_', '-').toLowerCase();

    if (vl === want) s += 100;                       // aniq mos (en-US)
    else if (vl.split('-')[0] === want.split('-')[0]) s += 60;   // til mos (en)
    else return -1;                                   // boshqa til — yaramaydi

    if (/google/.test(name)) s += 40;
    if (/neural|natural|enhanced|premium|wavenet/.test(name)) s += 35;
    if (/siri/.test(name)) s += 20;
    if (/microsoft/.test(name)) s += 10;
    if (/espeak|compact|robot/.test(name)) s -= 50;
    if (v.localService === false) s += 15;            // bulutli ovozlar sifatliroq
    if (v.default) s += 5;
    return s;
  }

  /* Shu til uchun mos ovozlar — eng yaxshisi birinchi. */
  function voicesFor(lang, all) {
    var list = all || (ok() ? synth().getVoices() : []) || [];
    return list
      .map(function (v) { return { v: v, s: score(v, lang) }; })
      .filter(function (x) { return x.s >= 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .map(function (x) { return x.v; });
  }

  function savedVoiceURI(lang) {
    try { return localStorage.getItem(VOICE_KEY + lang) || ''; } catch (e) { return ''; }
  }
  function setVoice(lang, uri) {
    try {
      if (uri) localStorage.setItem(VOICE_KEY + lang, uri);
      else localStorage.removeItem(VOICE_KEY + lang);
    } catch (e) {}
  }

  /* Ishlatiladigan ovoz: foydalanuvchi tanlagani bo'lsa o'sha, aks holda
     eng yuqori ballisi. Tanlangan ovoz yo'qolgan bo'lsa (til paketi
     o'chirilgan) jimgina eng yaxshisiga qaytadi. */
  function pick(lang) {
    var list = voicesFor(lang);
    if (!list.length) return null;
    var uri = savedVoiceURI(lang);
    if (uri) {
      var hit = list.find(function (v) { return v.voiceURI === uri; });
      if (hit) return hit;
    }
    return list[0];
  }

  /* ---------- 3. Matnni ovoz uchun tayyorlash ----------
     Belgilar o'qib yuborilmasin va tabiiy to'xtash bo'lsin. */
  function normalize(text) {
    var t = String(text == null ? '' : text);
    t = t.replace(/[*_`~]+/g, '');                 // markdown belgilarini o'qimasin
    t = t.replace(/\s*[—–]\s*/g, ', ');            // tire -> qisqa to'xtash
    t = t.replace(/\.{3,}|…/g, ', ');              // "nuqta nuqta nuqta" o'qilmasin
    t = t.replace(/[«»"“”]/g, '');                 // qo'shtirnoq nomi aytilmasin
    t = t.replace(/\s*\(\s*\)\s*/g, ' ');          // bo'sh qavs
    t = t.replace(/\s+/g, ' ').trim();
    /* Oxirida tinish belgisi bo'lmasa ovoz "osilib" qoladi — nuqta qo'yamiz,
       shunda jumla oxiri tabiiy pasayadi. */
    if (t && !/[.!?…:;,]$/.test(t)) t += '.';
    return t;
  }

  /* ---------- 4. Uzun matnni bo'laklash ----------
     Chrome uzun matnni yarmida to'xtatadi. Tinish belgisi bo'yicha
     bo'lamiz — so'z o'rtasidan kesilmasin. */
  function chunk(text) {
    if (text.length <= MAX_CHUNK) return [text];
    var parts = [], buf = '';
    /* Tinish belgisigacha bo'lgan bo'laklar. `(?<=...)` ATAYLAB
       ishlatilmadi: eski Safari uni tushunmaydi va bu FAYLNI BUTUNLAY
       yiqitadi (regex literal parse paytida xato beradi, ya'ni modul
       umuman yuklanmaydi). */
    var pieces = text.match(/[^.!?;,]+[.!?;,]*\s*/g) || [text];
    pieces.map(function (p) { return p.trim(); }).filter(Boolean).forEach(function (piece) {
      if ((buf + ' ' + piece).trim().length <= MAX_CHUNK) {
        buf = (buf ? buf + ' ' : '') + piece;
      } else {
        if (buf) parts.push(buf);
        if (piece.length <= MAX_CHUNK) { buf = piece; return; }
        // Bitta bo'lak ham uzun — bo'shliq bo'yicha maydalaymiz
        var words = piece.split(' '), line = '';
        words.forEach(function (w) {
          if ((line + ' ' + w).trim().length <= MAX_CHUNK) line = (line ? line + ' ' : '') + w;
          else { if (line) parts.push(line); line = w; }
        });
        buf = line;
      }
    });
    if (buf) parts.push(buf);
    return parts.filter(Boolean);
  }

  /* ---------- 5. Navbat bo'shashini kutish ----------
     `cancel()` darhol ta'sir qilmaydi; kutmasdan `speak()` chaqirilsa
     yangi matn yo'qoladi. */
  function cancelThen(fn) {
    try { synth().cancel(); } catch (e) {}
    var tries = 0;
    (function wait() {
      var busy = false;
      try { busy = synth().speaking || synth().pending; } catch (e) {}
      if (!busy || tries++ > 20) { setTimeout(fn, 0); return; }
      setTimeout(wait, 25);
    })();
  }

  /* ---------- 6. Chrome "to'xtab qolish" qo'riqchisi ----------
     Uzun o'qishda Chrome o'zi to'xtab qoladi; davriy `resume()` uni
     tirik saqlaydi. Faqat o'qish davomida ishlaydi. */
  function startKeepAlive() {
    stopKeepAlive();
    state.keepAlive = setInterval(function () {
      try {
        if (synth().speaking && !synth().paused) { synth().pause(); synth().resume(); }
      } catch (e) {}
    }, 9000);
  }
  function stopKeepAlive() {
    if (state.keepAlive) { clearInterval(state.keepAlive); state.keepAlive = null; }
  }

  /* Birinchi matn yutib yuborilmasin — jimgina "isitib" qo'yamiz. */
  function prime() {
    if (state.primed || !ok()) return;
    state.primed = true;
    try {
      var u = new root.SpeechSynthesisUtterance(' ');
      u.volume = 0;
      synth().speak(u);
    } catch (e) {}
  }

  /* ---------- Asosiy: o'qish ----------
     `opts`: { lang, rate, pitch, voice }
     `done(err)` — MUVAFFAQIYAT ham, XATO ham bo'lsa chaqiriladi, shunda
     chaqiruvchi zanjiri uzilmaydi. */
  function speak(text, opts, done) {
    if (typeof opts === 'string') opts = { lang: opts };
    opts = opts || {};
    /* `done` FAQAT BIR MARTA chaqirilishi shart: `onend` va `onerror`
       ba'zan ikkalasi ham keladi, ikki marta chaqirilsa o'qish zanjiri
       ikki joydan davom etib ketardi. */
    var cb = done;
    function fire(err) { if (cb) { var f = cb; cb = null; f(err || null); } }

    if (!ok()) { fire(new Error('TTS yo\'q')); return; }

    var clean = normalize(text);
    if (!clean) { fire(null); return; }

    var myGen = ++state.gen;
    var lang = opts.lang;
    if (!lang || lang === 'auto') {
      lang = (/[а-яёА-ЯЁ]/.test(clean)) ? 'ru-RU' : 'en-US';
    } else if (lang === 'russian' || lang === 'ru') {
      lang = 'ru-RU';
    } else if (lang === 'english' || lang === 'en') {
      lang = 'en-US';
    }

    ready().then(function () {
      if (myGen !== state.gen) return;              // orada bekor qilindi
      var voice = opts.voice || pick(lang);
      var parts = chunk(clean);
      var i = 0;

      cancelThen(function next() {
        if (myGen !== state.gen) return;
        if (i >= parts.length) { stopKeepAlive(); fire(null); return; }

        var u = new root.SpeechSynthesisUtterance(parts[i++]);
        u.lang = lang;
        u.rate = opts.rate || 1;
        u.pitch = opts.pitch == null ? 1 : opts.pitch;
        u.volume = opts.volume == null ? 1 : opts.volume;
        if (voice) u.voice = voice;

        u.onend = function () {
          if (myGen !== state.gen) return;
          if (i < parts.length) setTimeout(next, 60);   // bo'laklar orasi
          else { stopKeepAlive(); fire(null); }
        };
        u.onerror = function (e) {
          /* `interrupted`/`canceled` — bu BIZ to'xtatganmiz, xato emas. */
          var err = e && e.error;
          stopKeepAlive();
          if (myGen !== state.gen || err === 'interrupted' || err === 'canceled') return;
          fire(new Error(err || 'tts-error'));
        };

        try { synth().speak(u); startKeepAlive(); }
        catch (e) { stopKeepAlive(); fire(e); }
      });
    }).catch(function (e) { fire(e); });
  }

  function cancel() {
    state.gen++;
    stopKeepAlive();
    try { synth().cancel(); } catch (e) {}
  }

  root.TTS = {
    ok: ok, ready: ready, voicesFor: voicesFor, pick: pick,
    setVoice: setVoice, savedVoiceURI: savedVoiceURI,
    normalize: normalize, chunk: chunk,
    speak: speak, cancel: cancel, prime: prime
  };
})(window);
