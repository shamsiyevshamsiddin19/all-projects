/* =================================================================
   SCARPION MUSIC — sahifa jonli qismlari
     1. Mobil menyu
     2. Hero slayderi
     3. Qo'shiq namunasini chaluvchi pleyer
     4. Qidiruvda avtoto'ldirish
     5. Ijrochi maydonida avtoto'ldirish
   Kutubxona ishlatilmagan — hammasi sof JavaScript.
   ================================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- 1. MOBIL MENYU ------------------------------------ */
  var burger = document.querySelector('.burger');
  var nav = document.querySelector('.nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('is-open');
    });
  }

  /* ---------- 2. HERO SLAYDERI ---------------------------------- */
  (function () {
    var hero = document.querySelector('[data-hero]');
    if (!hero) return;

    var slides = hero.querySelectorAll('[data-slide]');
    var panels = hero.querySelectorAll('[data-panel]');
    var dots = hero.querySelectorAll('[data-dot]');

    // Bitta albom bo'lsa almashtiradigan narsa yo'q
    if (slides.length < 2) return;

    var joriy = 0;
    var taymer = null;
    var DAVR = 6000;   // millisekund: har 6 soniyada almashadi

    function korsat(n) {
      // Manfiy yoki chegaradan oshgan raqamni aylantirib qo'yamiz:
      // oxirgidan keyin yana birinchisi keladi.
      joriy = (n + slides.length) % slides.length;

      slides.forEach(function (el, i) {
        el.classList.toggle('is-active', i === joriy);
      });
      panels.forEach(function (el, i) {
        el.classList.toggle('is-active', i === joriy);
      });
      dots.forEach(function (el, i) {
        el.classList.toggle('is-active', i === joriy);
      });
    }

    function boshla() {
      toxtat();
      taymer = setInterval(function () { korsat(joriy + 1); }, DAVR);
    }
    function toxtat() {
      if (taymer) { clearInterval(taymer); taymer = null; }
    }

    dots.forEach(function (dot, i) {
      dot.addEventListener('click', function () {
        korsat(i);
        boshla();   // qo'lda tanlangach sanoq yangidan boshlanadi
      });
    });

    // Sichqoncha hero ustida turganda almashmaydi — o'qiyotgan
    // odamning tagidan slayd tortib olinmasin.
    hero.addEventListener('mouseenter', toxtat);
    hero.addEventListener('mouseleave', boshla);

    // Boshqa varaqqa o'tilganda taymerni to'xtatamiz: fonda
    // bekorga ishlab turishi shart emas.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { toxtat(); } else { boshla(); }
    });

    boshla();
  })();

  /* ---------- 2b. PROFIL OYNASI --------------------------------- */
  (function () {
    var quti = document.querySelector('[data-account]');
    if (!quti) return;
    var tugma = quti.querySelector('.avatar');

    function yop() {
      quti.classList.remove('is-open');
      tugma.setAttribute('aria-expanded', 'false');
    }

    tugma.addEventListener('click', function (e) {
      e.stopPropagation();
      var ochiq = quti.classList.toggle('is-open');
      tugma.setAttribute('aria-expanded', ochiq ? 'true' : 'false');
    });

    // Oynaning ICHIGA bosilganda yopilmasin (havolalar ishlasin)
    quti.querySelector('.account__menu').addEventListener('click', function (e) {
      e.stopPropagation();
    });

    document.addEventListener('click', yop);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') yop();
    });
  })();

  /* ---------- 3. PLEYER ----------------------------------------- */
  // DIQQAT: bu blok IIFE (o'zini chaqiruvchi funksiya) ichida.
  // Ichidagi "return" faqat SHU funksiyadan chiqadi. Busiz u butun
  // DOMContentLoaded ni to'xtatib, pastdagi bo'limlarni o'ldirardi.
  (function () {
  // Sahifada preview'li qo'shiq bo'lmasa, umuman ishga tushirmaymiz.
  var buttons = document.querySelectorAll('[data-preview]');
  if (!buttons.length) return;

  var bar = document.querySelector('.player');
  if (!bar) return;

  var audio = new Audio();
  audio.volume = 0.85;

  var elCover = bar.querySelector('.player__cover');
  var elTitle = bar.querySelector('.player__title');
  var elArtist = bar.querySelector('.player__artist');
  var elFill = bar.querySelector('.player__fill');
  var elClose = bar.querySelector('.player__close');

  var current = null;   // hozir bosilgan tugma

  /* Barcha tugmalarni "chalinmayapti" holatiga qaytaradi */
  function reset() {
    // Sahifada ikki xil tugma bor: qo'shiqlar ro'yxatidagi (.play) va
    // albom muqovasidagi (.card__play). Ikkovini ham qamrab olish uchun
    // klass emas, data-preview atributi bo'yicha qidiramiz.
    document.querySelectorAll('[data-preview].is-playing').forEach(function (b) {
      b.classList.remove('is-playing');
      b.innerHTML = '&#9654;';                    // ▶
      var row = b.closest('tr');
      if (row) row.classList.remove('is-playing');
    });
  }

  function open(btn) {
    reset();
    current = btn;

    btn.classList.add('is-playing');
    btn.innerHTML = '&#10073;&#10073;';           // ❙❙ (pauza)
    var row = btn.closest('tr');
    if (row) row.classList.add('is-playing');

    // data-* atributlari shablonda yozilgan
    if (elTitle) elTitle.textContent = btn.dataset.title || '';
    if (elArtist) elArtist.textContent = btn.dataset.artist || '';
    if (elCover) {
      if (btn.dataset.cover) {
        elCover.src = btn.dataset.cover;
        elCover.style.visibility = 'visible';
      } else {
        elCover.removeAttribute('src');
        elCover.style.visibility = 'hidden';
      }
    }

    bar.classList.add('is-open');
    document.body.classList.add('has-player');

    audio.src = btn.dataset.preview;
    audio.play().catch(function () {
      // Brauzer ruxsat bermasa (avtomatik ijro taqiqlangan) — jim qolamiz.
      reset();
    });
  }

  function stop() {
    audio.pause();
    reset();
    current = null;
    bar.classList.remove('is-open');
    document.body.classList.remove('has-player');
    if (elFill) elFill.style.width = '0';
  }

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Shu qo'shiq allaqachon chalinayotgan bo'lsa — to'xtatamiz
      if (current === btn && !audio.paused) {
        audio.pause();
        btn.classList.remove('is-playing');
        btn.innerHTML = '&#9654;';
        return;
      }
      // Shu qo'shiq pauzada turgan bo'lsa — davom ettiramiz
      if (current === btn && audio.paused) {
        audio.play();
        btn.classList.add('is-playing');
        btn.innerHTML = '&#10073;&#10073;';
        return;
      }
      open(btn);
    });
  });

  // Ijro davomida yashil chiziqni siljitamiz
  audio.addEventListener('timeupdate', function () {
    if (!elFill || !audio.duration) return;
    elFill.style.width = (audio.currentTime / audio.duration * 100) + '%';
  });

  // Namuna tugadi (30 soniya)
  audio.addEventListener('ended', function () {
    reset();
    if (elFill) elFill.style.width = '0';
  });

  if (elClose) elClose.addEventListener('click', stop);

  // Probel tugmasi — to'xtatish/davom ettirish.
  // Agar foydalanuvchi inputga yozayotgan bo'lsa — aralashmaymiz.
  document.addEventListener('keydown', function (e) {
    if (e.code !== 'Space' || !current) return;
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    e.preventDefault();
    current.click();
  });
  })();


  /* ---------- 4. QIDIRUVDA AVTOTO'LDIRISH ----------------------- */
  /* Yozilgan matn bo'yicha serverdan taklif so'raydi va pastda
     ro'yxat chiqaradi. Ro'yxatdagi element bosilsa — to'g'ridan
     to'g'ri o'sha albom/ijrochi sahifasiga o'tadi.                */
  (function () {
    var inputlar = document.querySelectorAll('[data-suggest]');
    if (!inputlar.length) return;

    inputlar.forEach(function (input) {
      var oram = input.closest('form');
      if (!oram) return;
      oram.classList.add('has-suggest');

      var quti = document.createElement('div');
      quti.className = 'suggest';
      quti.setAttribute('role', 'listbox');
      oram.appendChild(quti);

      var kutish = null;      // debounce taymeri
      var natijalar = [];     // hozirgi takliflar (klaviatura uchun)
      var tanlangan = -1;
      var oxirgiSorov = 0;    // kechikib kelgan javobni tashlash uchun

      function yop() {
        quti.classList.remove('is-open');
        tanlangan = -1;
      }

      function chiz(data) {
        natijalar = [];
        var html = '';

        if (data.albums.length) {
          html += '<div class="suggest__group">Albomlar</div>';
          data.albums.forEach(function (a) {
            natijalar.push(a.url);
            html += '<a class="suggest__item" href="' + a.url + '">' +
              (a.cover
                ? '<img src="' + a.cover + '" alt="">'
                : '<span class="suggest__blank"></span>') +
              '<span class="suggest__text"><b>' + xavfsiz(a.title) + '</b>' +
              '<small>' + xavfsiz(a.artist) + (a.year ? ' · ' + a.year : '') + '</small></span></a>';
          });
        }

        if (data.artists.length) {
          html += '<div class="suggest__group">Ijrochilar</div>';
          data.artists.forEach(function (ar) {
            natijalar.push(ar.url);
            html += '<a class="suggest__item" href="' + ar.url + '">' +
              (ar.photo
                ? '<img class="is-round" src="' + ar.photo + '" alt="">'
                : '<span class="suggest__blank is-round"></span>') +
              '<span class="suggest__text"><b>' + xavfsiz(ar.name) + '</b>' +
              '<small>' + ar.albums + ' ta albom</small></span></a>';
          });
        }

        if (!html) {
          html = '<div class="suggest__empty">Hech narsa topilmadi</div>';
        }

        quti.innerHTML = html;
        quti.classList.add('is-open');
        tanlangan = -1;
      }

      /* Serverdan kelgan matnni HTML ga qo'yishdan oldin xavfsizlaymiz.
         Busiz albom nomidagi < > belgilari sahifa tuzilishini buzardi. */
      function xavfsiz(matn) {
        var d = document.createElement('div');
        d.textContent = matn;
        return d.innerHTML;
      }

      function sora() {
        var q = input.value.trim();
        if (q.length < 2) { yop(); return; }

        var belgi = ++oxirgiSorov;
        fetch('/takliflar/?q=' + encodeURIComponent(q), {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            // Sekin kelgan eski javob yangisini bosib ketmasin
            if (belgi !== oxirgiSorov) return;
            chiz(data);
          })
          .catch(yop);
      }

      /* debounce: har bosilgan tugmada so'rov yubormaymiz, yozish
         to'xtaganidan 200 ms keyin bitta so'rov ketadi.            */
      input.addEventListener('input', function () {
        clearTimeout(kutish);
        kutish = setTimeout(sora, 200);
      });

      input.addEventListener('focus', function () {
        if (input.value.trim().length >= 2 && quti.innerHTML) {
          quti.classList.add('is-open');
        }
      });

      input.addEventListener('keydown', function (e) {
        if (!quti.classList.contains('is-open')) return;
        var elementlar = quti.querySelectorAll('.suggest__item');
        if (!elementlar.length) return;

        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          tanlangan += (e.key === 'ArrowDown' ? 1 : -1);
          if (tanlangan < 0) tanlangan = elementlar.length - 1;
          if (tanlangan >= elementlar.length) tanlangan = 0;
          elementlar.forEach(function (el, i) {
            el.classList.toggle('is-active', i === tanlangan);
          });
          elementlar[tanlangan].scrollIntoView({ block: 'nearest' });
        } else if (e.key === 'Enter' && tanlangan >= 0) {
          e.preventDefault();
          window.location = natijalar[tanlangan];
        } else if (e.key === 'Escape') {
          yop();
        }
      });

      // Tashqariga bosilganda yopiladi
      document.addEventListener('click', function (e) {
        if (!oram.contains(e.target)) yop();
      });
    });
  })();


  /* ---------- 5. IJROCHI MAYDONIDA AVTOTO'LDIRISH --------------- */
  /* Albom formasidagi <select> uzun ro'yxatda noqulay. Uni qidiruvli
     ro'yxatga aylantiramiz. MUHIM: <select> ning o'zi o'chirilmaydi,
     faqat yashiriladi — forma baribir uning qiymatini yuboradi va
     JavaScript ishlamasa ham forma ishlayveradi.                   */
  (function () {
    var select = document.querySelector('select[name="artist"]');
    if (!select || select.options.length < 6) return;

    var oram = document.createElement('div');
    oram.className = 'combo';
    select.parentNode.insertBefore(oram, select);
    oram.appendChild(select);
    select.classList.add('combo__native');

    var input = document.createElement('input');
    input.type = 'text';
    input.className = 'combo__input field-input';
    input.placeholder = 'Ijrochi nomini yozing...';
    input.autocomplete = 'off';
    input.value = select.selectedIndex > 0 ? select.options[select.selectedIndex].text : '';
    oram.appendChild(input);

    var royxat = document.createElement('div');
    royxat.className = 'suggest';
    oram.appendChild(royxat);

    function variantlar(matn) {
      matn = matn.trim().toLowerCase();
      return Array.prototype.filter.call(select.options, function (o) {
        return o.value && o.text.toLowerCase().indexOf(matn) !== -1;
      }).slice(0, 8);
    }

    function ochib(matn) {
      var list = variantlar(matn);
      if (!list.length) {
        royxat.innerHTML = '<div class="suggest__empty">Topilmadi — yangi ijrochi qo\'shing</div>';
      } else {
        royxat.innerHTML = list.map(function (o) {
          var d = document.createElement('div');
          d.textContent = o.text;
          return '<button type="button" class="suggest__item" data-value="' + o.value + '">' +
                 '<span class="suggest__text"><b>' + d.innerHTML + '</b></span></button>';
        }).join('');
      }
      royxat.classList.add('is-open');
    }

    input.addEventListener('focus', function () { ochib(''); });
    input.addEventListener('input', function () { ochib(input.value); });

    royxat.addEventListener('click', function (e) {
      var tugma = e.target.closest('[data-value]');
      if (!tugma) return;
      select.value = tugma.dataset.value;
      input.value = select.options[select.selectedIndex].text;
      royxat.classList.remove('is-open');
    });

    document.addEventListener('click', function (e) {
      if (!oram.contains(e.target)) royxat.classList.remove('is-open');
    });
  })();
});
