/* ============================================================
   Yordamchi — Bosh sahifa (Wstore uslubidagi mukammal filtr va Reels Feed)
   Aynan wstore.uz kabi: Filtr tugmasi, qidiruv, modal panel, 
   bo'limlar, saralash, tozalash va "Ko'rsatish (N)" amallari
   ============================================================ */
(function () {
  'use strict';

  /* Stories ro'yxati */
  /* Kategoriya nomlari — bir necha joyda ishlatiladi, shuning uchun
     bitta joyda e'lon qilinadi. Ilgari ular satr sifatida qo'lda
     takrorlanardi va shartlar `indexOf` bilan yozilgani uchun begona
     kategoriyalarni ham tortib olardi. */
  var CAT_229  = 'Глаголы настоящего времени';
  var CAT_TEMA = 'Тематический 9000';

  var STORIES = [
    {
      id: 'ru_229',
      title: '229 ta fe\'l',
      sub: 'Hozirgi zamon',
      type: 'vocab',
      lang: 'russian',
      category: 'Глаголы настоящего времени',
      color: 'linear-gradient(135deg, #f59e0b, #ef4444)',
      badge: '229',
      desc: 'Rus tilida eng ko\'p ishlatiladigan 229 ta fe\'lning hozirgi zamon (я) shakllari va tarjimalari.',
      sampleWord: {
        w: 'я изучаю',
        tr: 'men o\'rganyapman',
        forms: 'Hozirgi zamon · 1-shaxs (я)',
        conj: 'Fe\'l: изучать (o\'rganmoq)',
        ex: 'Я изучаю русский язык каждый день.',
        exTr: 'Men har kuni rus tilini o\'rganyapman.'
      },
      quiz: {
        q: '«я изучаю» so\'zining o\'zbekcha ma\'nosi nima?',
        opts: ['men o\'rganyapman', 'men uxlayapman', 'men ishlayapman', 'men ketyapman'],
        correct: 0
      }
    },
    {
      id: 'ru_1000',
      title: 'Rus tili 1000',
      sub: 'Asosiy so\'zlar',
      type: 'vocab',
      lang: 'russian',
      category: '1-8000/1-1000/1-100',
      color: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
      badge: '1K',
      desc: 'Eng ko\'p uchraydigan 1000 ta ruscha so\'z, talaffuz va jonli misollar.',
      sampleWord: {
        w: 'достижение',
        tr: 'yutuq, natija, muvaffaqiyat',
        forms: 'Ot · средний род · ko\'pligi: достижения',
        conj: 'Синонимы: успех, победа, результат',
        ex: 'Каждый выученный урок — это ваше личное достижение.',
        exTr: 'Har bir o\'rganilgan dars — bu sizning shaxsiy yutug\'ingizdir.'
      },
      quiz: {
        q: '«достижение» so\'zining o\'zbekcha tarjimasi nima?',
        opts: ['yutuq, natija', 'muammo, to\'siq', 'vaqt, soat', 'kitob, darslik'],
        correct: 0
      }
    },
    {
      id: 'en_8000',
      title: 'Ingliz tili',
      sub: '8000 ta so\'z',
      type: 'vocab',
      lang: 'english',
      category: '1-8000/1-1000/1-100',
      color: 'linear-gradient(135deg, #10b981, #3b82f6)',
      badge: 'EN',
      desc: 'Oxford va Cambridge standartidagi 8000 ta eng kerakli inglizcha so\'zlar.',
      sampleWord: {
        w: 'perseverance',
        tr: 'matonat, qat\'iyatlilik, sabot',
        forms: 'Noun · Uncountable · Pronunciation: /ˌpɜːsɪˈvɪərəns/',
        conj: 'Synonyms: persistence, dedication, tenacity',
        ex: 'Success is the result of hard work and perseverance.',
        exTr: 'Muvaffaqiyat — mashaqqatli mehnat va matonat natijasidir.'
      },
      quiz: {
        q: 'What is the synonym of «perseverance»?',
        opts: ['persistence', 'laziness', 'hesitation', 'weakness'],
        correct: 0
      }
    },
    {
      id: 'ru_grammar',
      title: 'Grammatika',
      sub: 'Rus tili',
      type: 'grammar',
      lang: 'russian',
      folder: '05. Времена глагола (Zamonlar)',
      color: 'linear-gradient(135deg, #6366f1, #a855f7)',
      badge: 'GR',
      desc: 'Rus tili fe\'l zamonlari: Hozirgi (Настоящее), O\'tgan (Прошедшее) va Kelasi (Будущее).',
      sampleWord: {
        w: 'Fe\'l turlari (НСВ va СВ)',
        tr: 'Tugallanmagan va Tugallangan harakat',
        forms: 'НСВ: делать, читать, писать (jarayon)',
        conj: 'СВ: сделать, прочитать, написать (natija)',
        ex: 'Я читал книгу 2 часа (НСВ) vs Я прочитал книгу (СВ).',
        exTr: 'Men 2 soat kitob o\'qidim (jarayon) vs Men kitobni o\'qib bo\'ldim (natija).'
      },
      quiz: {
        q: 'Qaysi fe\'l tugallangan turga (СВ) tegishli?',
        opts: ['написать', 'писать', 'читать', 'делать'],
        correct: 0
      }
    },
    {
      id: 'cs_python',
      title: 'Python',
      sub: 'Darslik',
      type: 'coding',
      tech: 'python',
      color: 'linear-gradient(135deg, #3776AB, #FFD43B)',
      badge: 'PY',
      desc: 'Python dasturlash tili: List comprehensions, dekoratorlar, generatorlar va OOP.',
      codeSnippet: {
        title: 'List Comprehension & Dict Merge',
        code: '# Kvadratlarni hisoblash va dict birlashtirish\nsquares = [x**2 for x in range(1, 6)]\nuser = {"name": "Ali", "role": "Dev"}\nmeta = {**user, "status": "active"}\nprint(squares, meta)',
        tip: 'List comprehension oddiy for tsiklidan 2 barobar tezroq ishlaydi!'
      },
      quiz: {
        q: '[x*2 for x in range(3)] kodi qanday ro\'yxat qaytaradi?',
        opts: ['[0, 2, 4]', '[2, 4, 6]', '[0, 1, 2]', '[1, 2, 3]'],
        correct: 0
      }
    },
    {
      id: 'cs_fastapi',
      title: 'FastAPI',
      sub: 'Darslik',
      type: 'coding',
      tech: 'fastapi',
      color: 'linear-gradient(135deg, #009688, #059669)',
      badge: 'API',
      desc: 'Zamonaviy asinxron REST API va Pydantic model validatsiyasi.',
      codeSnippet: {
        title: 'Asinxron Endpoint va Validatsiya',
        code: 'from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\napp = FastAPI()\n\n@app.get("/items/{id}")\nasync def get_item(id: int):\n    return {"id": id, "status": "active"}',
        tip: 'FastAPI avtomatik ravishda /docs ostida Swagger UI yaratadi!'
      },
      quiz: {
        q: 'FastAPI da qaysi kutubxona ma\'lumotlar turlarini tekshiradi (validatsiya)?',
        opts: ['Pydantic', 'Django ORM', 'Flask-Validator', 'Requests'],
        correct: 0
      }
    },
    {
      id: 'cs_git',
      title: 'Git & GitHub',
      sub: 'Darslik',
      type: 'coding',
      tech: 'git',
      color: 'linear-gradient(135deg, #F05032, #EA4C89)',
      badge: 'GIT',
      desc: 'Versiyalar nazorati, branchlar bilan ishlash va jamoaviy dasturlash.',
      codeSnippet: {
        title: 'Foydali Git buyruqlari',
        code: '# Yangi branch ochib unga o\'tish\ngit checkout -b feature/auth\n\n# Barcha o\'zgarishlarni commit qilish\ngit add -A && git commit -m "feat: login"\n\n# Serverga yuborish\ngit push -u origin feature/auth',
        tip: 'git status bilan qaysi fayllar o\'zgarganini doim tekshirib turing.'
      },
      quiz: {
        q: 'Barcha o\'zgargan fayllarni indeksga (staging) qo\'shish buyrug\'i qaysi?',
        opts: ['git add -A', 'git push all', 'git stage -f', 'git save'],
        correct: 0
      }
    },
    {
      id: 'cs_linux',
      title: 'Linux',
      sub: 'Darslik',
      type: 'coding',
      tech: 'linux',
      color: 'linear-gradient(135deg, #FCC624, #222)',
      badge: 'LNX',
      desc: 'Linux buyruqlari, server sozlash, ruxsatlar (chmod) va terminal.',
      codeSnippet: {
        title: 'Server monitoringi',
        code: '# Resurslarni real vaqtda kuzatish\nhtop\n\n# Disk xotirasini inson o\'qiydigan formatda ko\'rish\ndf -h\n\n# Servis loglarini jonli kuzatish\njournalctl -u yordamchi -f',
        tip: 'Linux da barcha jarayonlar va qurilmalar fayl ko\'rinishida ifodalanadi.'
      },
      quiz: {
        q: 'Fayl ruxsatlarini (permissions) o\'zgartirish uchun qaysi buyruq ishlatiladi?',
        opts: ['chmod', 'chown', 'touch', 'mkdir'],
        correct: 0
      }
    },
    {
      id: 'cs_postgres',
      title: 'PostgreSQL',
      sub: 'Darslik',
      type: 'coding',
      tech: 'postgresql',
      color: 'linear-gradient(135deg, #336791, #4169E1)',
      badge: 'SQL',
      desc: 'SQL so\'rovlar, indekslash, agregat funksiyalar va tranzaksiyalar.',
      codeSnippet: {
        title: 'JOIN va GROUP BY so\'rovi',
        code: 'SELECT u.name, COUNT(o.id) AS total_orders\nFROM users u\nLEFT JOIN orders o ON u.id = o.user_id\nWHERE u.status = \'active\'\nGROUP BY u.id, u.name\nHAVING COUNT(o.id) >= 3\nORDER BY total_orders DESC;',
        tip: 'Tez-tez qidiriladigan ustunlarga B-Tree indeks qo\'shish tezlikni 100x oshiradi!'
      },
      quiz: {
        q: 'Guruhlangan (GROUP BY) natijalarni filtrlash uchun nima ishlatiladi?',
        opts: ['HAVING', 'WHERE', 'LIMIT', 'FILTER BY'],
        correct: 0
      }
    }
  ];

  /* Fallback so'zlar */
  var FALLBACK_WORDS = [
    {
      ru: "я играю",
      uz: "men o'ynayapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Sport yoki kompyuter o'yinlarini o'ynash, musiqa asboblarini chalish hamda sahnada rol ijro etishda qo'llaniladi.\nShakl: hozirgi zamon (я) — я играю, infinitivi — играть, o'tgan zamon — я играл\nVid: NCV — играть, CV — сыграть / поиграть\nMa'nodosh: развлекаться, резвиться",
      ex: "Я каждый вечер с удовольствием играю в шахматы с дедушкой. (Men har oqshom bobom bilan maroq bilan shaxmat o'ynayman.)"
    },
    {
      ru: "я пишу",
      uz: "men yozyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Qalam, ruchka yoki klaviatura orqali matn, xat, ariza yaratishda ishlatiladi.\nShakl: hozirgi zamon (я) — я пишу, infinitivi — писать, o'tgan zamon — я писал\nVid: NCV — писать, CV — написать\nMa'nodosh: сочинять, записывать",
      ex: "Я сейчас пишу важное электронное письмо преподавателю. (Men hozir o'qituvchiga muhim elektron xat yozyapman.)"
    },
    {
      ru: "я говорю",
      uz: "men gapiryapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Nutq tovushlarini chiqarish, suhbatlashish yoki biror tilda muloqot qilishda qo'llaniladi.\nShakl: hozirgi zamon (я) — я говорю, infinitivi — говорить, o'tgan zamon — я говорил\nVid: NCV — говорить, CV — сказать / поговорить\nMa'nodosh: беседовать, произносить",
      ex: "Я свободно говорю на двух иностранных языках. (Men ikkita chet tilida erkin gapiraman.)"
    },
    {
      ru: "я учу",
      uz: "men o'rganyapman / o'rgatyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: 1) Yod olish, o'rganish; 2) Boshqalarga ta'lim berish.\nShakl: hozirgi zamon (я) — я учу, infinitivi — учить, o'tgan zamon — я учил\nVid: NCV — учить, CV — выучить / научить\nMa'nodosh: обучать, зубрить",
      ex: "Я каждый день учу двадцать новых русских слов. (Men har kuni 20 ta yangi ruscha so'z yodlayapman.)"
    },
    {
      ru: "accomplish",
      uz: "amalga oshirmoq, erishmoq",
      lang: "english",
      cat: "Ingliz tili 8000",
      note: "Qayerda: Murakkab vazifa, reja yoki maqsadni muvaffaqiyatli uddalashda ishlatiladi.\nMa'nodosh: achieve, complete, fulfill",
      ex: "She accomplished all her goals this year. (U bu yil o'zining barcha maqsadlariga erishdi.)"
    },
    {
      ru: "я мечтаю",
      uz: "men orzu qilyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Kelajakdagi ezgu niyatlar, istaklar haqida xayol surishda ishlatiladi.\nShakl: hozirgi zamon (я) — я мечтаю, infinitivi — мечтать, o'tgan zamon — я мечтал\nVid: NCV — мечтать, CV — помечтать\nMa'nodosh: грезить, фантазировать",
      ex: "Я мечтаю стать высококлассным разработчиком программного обеспечения. (Men yuqori malakali dasturchi bo'lishni orzu qilaman.)"
    },
    {
      ru: "resilience",
      uz: "bardoshlilik, moslashuvchanlik, chidamlilik",
      lang: "english",
      cat: "Ingliz tili 8000",
      note: "Qayerda: Qiyinchiliklar va stressdan tezda tiklanish qobiliyati haqida ishlatiladi.\nMa'nodosh: toughness, flexibility, endurance",
      ex: "Building resilience helps you overcome unexpected life challenges. (Chidamlilikni rivojlantirish kutilmagan qiyinchiliklarni yengishga yordam beradi.)"
    }
  ];

  /* Wstore uslubidagi kategoriyalar */
  var WSTORE_CATEGORIES = [
    { key: 'all', label: 'Barcha so\'zlar', icon: 'globe' },
    { key: 'ru_229', label: 'Hozirgi zamon (229)', icon: 'zap' },
    { key: 'ru_1000', label: 'Rus tili 1000', icon: 'book' },
    { key: 'en_8000', label: 'Ingliz tili 8000', icon: 'globe' },
    { key: 'ru_8000', label: 'Katta ruscha lug\'at (8000)', icon: 'book' }
  ];

  var WSTORE_COLLECTIONS = [
    { key: 'liked', label: 'Sevimli so\'zlarim', icon: 'heartFill', color: '#ef4444' },
    { key: 'saved', label: 'Saqlanganlar', icon: 'bookmarkFill', color: '#3b82f6' },
    { key: 'mastered', label: 'O\'rganilgan so\'zlar', icon: 'check', color: '#10b981' }
  ];

  /* JOIN — so'zlarni qanday BOG'LASH kerakligi. Saralashdan alohida
     bo'lim: saralash tartibni belgilaydi, join esa qaysi so'zlar bir
     guruhga tushishini. Ikki mantiq butunlay boshqacha ishlaydi. */
  var WSTORE_JOINS = [
    { key: '', label: 'O\'chiq', sub: 'So\'zlar bog\'lanmaydi' },
    { key: 'words', label: 'So\'zlarni juftlash',
      sub: 'Yozilishi o\'xshash: храню / храплю' },
    { key: 'meaning', label: 'Ma\'noni juftlash',
      sub: 'Ma\'nosi bog\'liq: иду / хожу / еду' }
  ];

  var WSTORE_SORTS = [
    { key: 'popular', label: 'Ommabop / Tasodifiy' },
    { key: 'alpha', label: 'Alifbo bo\'yicha (A–Z)' },
    { key: 'recent', label: 'Eng yangi so\'zlar' }
    /* Juftlash bandlari BU YERDAN olib tashlandi: ular saralash emas,
       GURUHLASH edi. Endi ular "Join" bo'limida — u yerda mantiq
       (so'z/ma'no) va ko'rinish (karusel/rangli) alohida tanlanadi. */
  ];

  var FEED_WORDS = [];
  var LOADED_WORDS_POOL = [];
  var SEARCH_QUERY = '';
  var STORY_VIEWER_STATE = null;

  /* Filter holatini boshqarish */
  function getFilterState() {
    try {
      var s = JSON.parse(localStorage.getItem('wstore_filter_v3') || '{}');
      return {
        category: s.category || 'all',
        collections: Array.isArray(s.collections) ? s.collections : [],
        sort: s.sort || 'popular',
        join: s.join || '',
        joinColor: !!s.joinColor,
        /* AI .md faylda yozgan "Turkum:" qatoridan kelgan qiymatlar.
           Qattiq ro'yxat EMAS — qaysi turkumlar mavjud bo'lsa, filtrda
           o'shalar chiqadi (getAvailablePos() ga qarang). */
        partsOfSpeech: Array.isArray(s.partsOfSpeech) ? s.partsOfSpeech : []
      };
    } catch (e) {
      return { category: 'all', collections: [], sort: 'popular', join: '', joinColor: false, partsOfSpeech: [] };
    }
  }

  function saveFilterState(st) {
    try { localStorage.setItem('wstore_filter_v3', JSON.stringify(st)); } catch (e) {}
  }

  function getActiveFilterCount(st) {
    var count = 0;
    if (st.category && st.category !== 'all') count++;
    if (st.collections && st.collections.length > 0) count += st.collections.length;
    if (st.sort && st.sort !== 'popular') count++;
    if (st.join) count++;
    if (st.partsOfSpeech && st.partsOfSpeech.length > 0) count += st.partsOfSpeech.length;
    return count;
  }

  App.view('home', {
    nav: 'home',
    render: function (page) {
      var st = getFilterState();
      var activeCount = getActiveFilterCount(st);

      page.innerHTML =
        '<div class="ig-home-wrap">' +
          /* Instagram Top Bar */
          '<header class="ig-header">' +
            '<div class="ig-brand">' +
              '<span class="ig-logo-text">Yordamchi</span>' +
              '<span class="ig-sparkle" data-icon="sparkles" data-icon-size="16"></span>' +
            '</div>' +
            '<div class="ig-actions">' +
              /* Test o'rniga TIZIM HOLATI: oflayn/onlayn, versiya, kesh va
                 xotira sinxronizatsiyasi bir joyda ko'rinsin. Nosozlik
                 chiqqanda "nima bo'lyapti" degan savolga javob shu yerda. */
              '<button class="ig-btn-icon" data-act="igSystemStatus" title="Tizim holati">' +
                '<span data-icon="activity" data-icon-size="20"></span>' +
              '</button>' +
              '<button class="ig-btn-icon" data-act="igShuffleFeed" title="Tasodifiy yangilash">' +
                '<span data-icon="shuffle" data-icon-size="20"></span>' +
              '</button>' +
              '<div id="nt-bell-host">' + (window.Notify ? Notify.bellHtml() : '') + '</div>' +
            '</div>' +
          '</header>' +

          /* Instagram Stories Carousel */
          '<div class="ig-stories-carousel">' +
            '<div class="ig-stories-track" id="ig-stories-track">' +
              renderStoriesHtml() +
            '</div>' +
          '</div>' +

          /* Wstore uslubidagi boshqaruv paneli (Filtr + Qidiruv yonma-yon) */
          '<div class="ws-ctrl-bar">' +
            '<button class="ws-filter-trigger-btn" data-act="wsOpenFilterModal">' +
              '<span data-icon="sliders" data-icon-size="16"></span>' +
              '<span>Filtr</span>' +
              (activeCount > 0 ? '<span class="ws-badge" id="ws-filter-badge">' + activeCount + '</span>' : '<span class="ws-badge" id="ws-filter-badge" style="display:none">0</span>') +
            '</button>' +
            '<div class="ws-search-wrap">' +
              '<span class="ws-search-ic" data-icon="search" data-icon-size="15"></span>' +
              '<input type="text" id="ws-search-input" class="ws-search-input" placeholder="So\'zlarni qidirish..." value="' + App.esc(SEARCH_QUERY) + '">' +
              '<button class="ws-search-clear" id="ws-search-clear" style="display:' + (SEARCH_QUERY ? 'flex' : 'none') + '" data-act="wsClearSearch">&times;</button>' +
            '</div>' +
          '</div>' +

          /* Instagram Reels Feed */
          '<div class="ig-feed" id="ig-feed-list">' +
            '<div class="ig-feed-loader"><div class="spinner"></div><span>Lug\'atlar yuklanmoqda...</span></div>' +
          '</div>' +

          /* Infinite Scroll Sentinel */
          '<div class="ig-infinite-sentinel" id="ig-infinite-sentinel">' +
            '<div class="ig-infinite-spinner"><div class="spinner"></div><span>Yangi so\'zlar yuklanmoqda...</span></div>' +
          '</div>' +
        '</div>' +
        
        /* Story Viewer Modal Container */
        '<div id="ig-story-modal" class="ig-story-modal"></div>';

      App.icons(page);
      bindSearchEvents(page);
      initFeed();
      initInfiniteScroll();
      mountDrawer();
    },
    leave: function () {
      closeStoryViewer();
      disconnectInfiniteScroll();
      unmountDrawer();
    }
  });

  /* Search Input Live Binding */
  function bindSearchEvents(page) {
    var inp = page.querySelector('#ws-search-input');
    var clr = page.querySelector('#ws-search-clear');
    if (!inp) return;

    var debounceTimer = null;
    inp.addEventListener('input', function () {
      SEARCH_QUERY = inp.value;
      if (clr) clr.style.display = SEARCH_QUERY ? 'flex' : 'none';
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        renderFeedItems(6, false);
      }, 250);
    });
  }

  App.actions.wsClearSearch = function () {
    SEARCH_QUERY = '';
    var inp = document.getElementById('ws-search-input');
    var clr = document.getElementById('ws-search-clear');
    if (inp) { inp.value = ''; inp.focus(); }
    if (clr) clr.style.display = 'none';
    renderFeedItems(6, false);
  };

  /* Horizontal Sub Chips */
  function updateControlsUI() {
    var st = getFilterState();
    var count = getActiveFilterCount(st);
    var badge = document.getElementById('ws-filter-badge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
    /* Tez chiplar OLIB TASHLANDI (foydalanuvchi so'rovi): ular uchun
       `ws-chips-row` elementi HTML'da umuman yasalmagan edi, ya'ni kod
       hech qachon ishlamagan o'lik qism edi. */
  }

  /* Mini Stats Bar HTML */
  function renderStatsBarHtml() {
    var liked = getLikedWords().length;
    var saved = getBookmarkedWords().length;
    var mastered = getMasteredWords().length;
    return '<div class="ig-stat-pill"><span data-icon="flame" data-icon-size="14" style="color:#f59e0b"></span> <b>' + mastered + '</b> ta o\'rganildi</div>' +
      '<div class="ig-stat-pill"><span data-icon="heartFill" data-icon-size="14" style="color:#ef4444"></span> <b>' + liked + '</b> sevimli</div>' +
      '<div class="ig-stat-pill"><span data-icon="bookmarkFill" data-icon-size="14" style="color:#3b82f6"></span> <b>' + saved + '</b> saqlangan</div>';
  }

  function updateStatsBar() {
    var bar = document.getElementById('ig-stats-bar');
    if (bar) {
      bar.innerHTML = renderStatsBarHtml();
      App.icons(bar);
    }
  }

  /* Stories HTML generator */
  function renderStoriesHtml() {
    return STORIES.map(function (s) {
      return '<div class="ig-story-bubble" data-act="igOpenStory" data-arg=\'' + App.arg({ id: s.id }) + '\'>' +
        '<div class="ig-story-ring">' +
          '<div class="ig-story-avatar" style="background:' + s.color + '">' +
            '<span>' + App.esc(s.badge) + '</span>' +
          '</div>' +
        '</div>' +
        '<span class="ig-story-name">' + App.esc(s.title) + '</span>' +
      '</div>';
    }).join('');
  }

  /* Load all dictionary words from API or fallback */
  /* `__remote_storage_` PREFIKSI ATAYLAB: shu prefiksli kalitlar serverga
     sinxronlanmaydi (remote-storage.js -> isInternalKey), ya'ni kesh faqat
     shu qurilmada qoladi.

     NIMA UCHUN SHART: prefiksiz bu kesh app_storage'ga yozilardi va 2.26 MB
     ga yetgan edi — butun xotiraning 80 foizi. `storage_bootstrap` esa uni
     har ochilishda tortib olishi kerak va 4.5 soniyalik chegaradan o'tolmay
     yiqilardi. Bootstrap yiqilsa `state.cache` bo'sh qoladi, ya'ni HAMMA
     sozlama (o'rgangan so'zlar, xatcho'plar, bildirishnomalar) o'qilmay
     "default holatga tushib" ko'rinardi.

     Kesh baribir 3 soatda eskiradi va qaytadan yasaladi — uni qurilmalar
     orasida sinxronlashning ma'nosi yo'q. */
  /* v3: keshdagi so'zlarda `meaningGroup`/`pairWith` YO'Q edi. Kalit
     yangilanmasa 3 soat davomida eski shakldagi havza ishlatilib,
     "Ma'noni juftlash" bo'sh chiqaverardi. */
  /* v4: kesh shakli siqildi (compactForCache). v3 keshlar xom shaklda va
     juda katta — ular eskirishini kutmasdan darhol tashlanadi, aks holda
     yangi 8847 so'z 3 soatgacha ko'rinmasdi. */
  var FEED_CACHE_KEY = '__remote_storage_feed_cache_v4';
  var FEED_CACHE_TTL = 3 * 60 * 60 * 1000; /* 3 soat — shundan keyin yangilaydi */

  /* Eski, sinxronlanadigan kalit qoldig'ini tozalaymiz — u bo'lmasa ham
     bootstrap'ni yana og'irlashtirib turardi. */
  try { localStorage.removeItem('yordamchi_feed_cache_v2'); } catch (e) {}
  try { localStorage.removeItem('__remote_storage_feed_cache_v3'); } catch (e) {}

  /* Keshga SIQILGAN shakl tushadi, serverdan kelgan xom qator EMAS.

     Server har so'z uchun 15 ta maydon qaytaradi (pronunciation, forms,
     synonyms, antonyms, collocations, mnemonic, formation...), lekin lenta
     ulardan FAQAT 8 tasini o'qiydi — qolgani keshda bekorga yotardi.
     Ustiga maydon NOMLARI har qatorda takrorlanadi, ya'ni "word_ru" 25 ming
     marta yozilardi.

     O'lchandi: xom shaklda ru 5493 kB + en 2202 kB = 7.7 MB. localStorage
     chegarasi odatda ~5 MB, ya'ni `setItem` xato berardi, xato yutilardi va
     kesh HECH QACHON saqlanmasdi — natijada ilova har ochilganda 7.7 MB ni
     qaytadan tortardi. Sekin internetda aynan shu sezilardi.

     `applyFeedItems` ikkala shaklni ham o'qiydi (`it.word_ru || it.ru`),
     shuning uchun eski kesh ham buzilmaydi. */
  function compactForCache(items) {
    return (items || []).map(function (it) {
      var o = {
        ru: it.word_ru || it.ru || '',
        uz: it.word_uz || it.uz || '',
        cat: it.category || it.cat || ''
      };
      /* Bo'sh maydon yozilmaydi — hozircha so'zlarning katta qismida
         izoh/misol yo'q, ular uchun bu keshni yana ancha kichraytiradi. */
      var note = it.note || '';                     if (note) o.note = note;
      var ex = it.example || it.ex || '';            if (ex) o.ex = ex;
      var mg = it.meaning_group || it.meaningGroup || ''; if (mg) o.meaning_group = mg;
      var pw = it.pair_with || '';                   if (pw) o.pair_with = pw;
      var pos = it.part_of_speech || '';             if (pos) o.part_of_speech = pos;
      return o;
    });
  }

  function saveFeedCache(ruItems, enItems) {
    try {
      localStorage.setItem(FEED_CACHE_KEY, JSON.stringify({
        ts: Date.now(),
        ru: compactForCache(ruItems),
        en: compactForCache(enItems)
      }));
    } catch (e) {
      /* Baribir sig'masa — eski keshni tashlaymiz, aks holda u eskirib
         yotaveradi va yangilanish hech qachon ko'rinmaydi. */
      try { localStorage.removeItem(FEED_CACHE_KEY); } catch (e2) {}
    }
  }

  function loadFeedCache() {
    try {
      var raw = JSON.parse(localStorage.getItem(FEED_CACHE_KEY) || 'null');
      if (!raw || !raw.ts || !raw.ru) return null;
      if (Date.now() - raw.ts > FEED_CACHE_TTL) return null; /* eskirgan */
      return raw;
    } catch (e) { return null; }
  }

  function applyFeedItems(ruItems, enItems) {
    LOADED_WORDS_POOL = [];
    ruItems.forEach(function (it) {
      LOADED_WORDS_POOL.push({
        ru: it.word_ru || it.ru,
        uz: it.word_uz || it.uz,
        lang: 'russian',
        cat: it.category || it.cat || 'Rus tili',
        note: it.note || '',
        ex: it.example || it.ex || '',
        /* Juftlash uchun kerakli maydonlar. Ilgari bu yerda ko'chirilmasdi
           va lentaga yetib bormasdi — natijada "Ma'noni juftlash" hech
           qachon guruh topolmasdi, chunki havzadagi so'zlarda yorliq
           umuman yo'q edi. */
        meaningGroup: (it.meaning_group || it.meaningGroup || '').trim(),
        pairWith: (it.pair_with || '').split(',').map(function (x) { return x.trim(); }).filter(Boolean),
        /* AI .md yozganda to'ldiradi — "Turkum bo'yicha" filtr shundan
           dinamik ro'yxat yasaydi (qattiq kodlangan ro'yxat emas). */
        partOfSpeech: (it.part_of_speech || '').trim()
      });
    });
    enItems.forEach(function (it) {
      LOADED_WORDS_POOL.push({
        ru: it.word_ru || it.ru,
        uz: it.word_uz || it.uz,
        lang: 'english',
        cat: it.category || it.cat || 'Ingliz tili',
        note: it.note || '',
        ex: it.example || it.ex || '',
        meaningGroup: (it.meaning_group || it.meaningGroup || '').trim(),
        pairWith: (it.pair_with || '').split(',').map(function (x) { return x.trim(); }).filter(Boolean),
        partOfSpeech: (it.part_of_speech || '').trim()
      });
    });

    /* QULF — bitta joyda. Lenta, qidiruv, filtrlar, juftlash, Reels
       hammasi shu havzadan oladi, shuning uchun qulflangan bo'limlarni
       shu yerda olib tashlash yetarli.

       Filtr KESHDAN KEYIN turadi (kesh to'liq saqlanadi): bo'lim ochilganda
       so'zlar darhol paydo bo'ladi, qaytadan tortib olish shart emas. */
    if (window.WordLock) {
      LOADED_WORDS_POOL.forEach(function (w) { WordLock.note(w.cat); });
      LOADED_WORDS_POOL = WordLock.filterWords(LOADED_WORDS_POOL);
    }
  }

  function initFeed() {
    FEED_WORDS = [];
    LOADED_WORDS_POOL = [];

    /* 1. Cache dan darhol ko'rsatish (kutish yo'q) */
    var cached = loadFeedCache();
    if (cached) {
      applyFeedItems(cached.ru, cached.en);
      renderFeedItems(6);
    }

    /* 2. Fon rejimida yangi ma'lumot yuklab, cache ni yangilash */
    App.call('get_dict_data', null, { query: 'lang=russian' })
      .then(function (res) {
        var ruItems = (res && res.items) ? res.items : [];
        return App.call('get_dict_data', null, { query: 'lang=english' })
          .catch(function () { return null; })
          .then(function (enRes) {
            var enItems = (enRes && enRes.items) ? enRes.items : [];
            saveFeedCache(ruItems, enItems);
            /* Agar oldin cache bo'lmagan bo'lsa — yangi ma'lumot bilan render qilamiz */
            if (!cached) {
              applyFeedItems(ruItems, enItems);
              if (LOADED_WORDS_POOL.length === 0) {
                LOADED_WORDS_POOL = FALLBACK_WORDS.slice();
              }
              renderFeedItems(6);
            }
          });
      })
      .catch(function () {
        if (!cached) {
          LOADED_WORDS_POOL = FALLBACK_WORDS.slice();
          renderFeedItems(6);
        }
      });
  }

  /* AI yozgan "Turkum:" matnidan sof yorliqni ajratadi. AI ba'zan qavs
     ichida qo'shimcha (masalan "fe'l (NSV) — mukammal juft: ...") yozadi
     — filtr uchun faqat asosiy so'z kerak, aks holda "fe'l (NSV)" va
     "fe'l (SV)" IKKI XIL guruh bo'lib qolardi. */
  function normalizePos(raw) {
    return String(raw || '').split('(')[0].split('—')[0].trim().toLowerCase();
  }

  /* Havzadagi so'zlarni skanerlab, HOZIR nechta va qanday turkum borligini
     topadi. Qattiq ro'yxat emas: AI yangi turkum yozsa (masalan "undov"),
     bu yerda o'zi paydo bo'ladi — kodga tegilmaydi. */
  function getAvailablePos() {
    var pool = LOADED_WORDS_POOL.length > 0 ? LOADED_WORDS_POOL : FALLBACK_WORDS;
    var counts = {}, labels = {};
    pool.forEach(function (w) {
      var key = normalizePos(w.partOfSpeech);
      if (!key) return;
      counts[key] = (counts[key] || 0) + 1;
      if (!labels[key]) labels[key] = key.charAt(0).toUpperCase() + key.slice(1);
    });
    return Object.keys(counts)
      .map(function (key) { return { key: key, label: labels[key], count: counts[key] }; })
      .sort(function (a, b) { return b.count - a.count; });
  }

  /* Filter and Sort pool */
  function getFilteredWordsPool() {
    var pool = LOADED_WORDS_POOL.length > 0 ? LOADED_WORDS_POOL : FALLBACK_WORDS;
    var st = getFilterState();
    var liked = getLikedWords();
    var saved = getBookmarkedWords();
    var mastered = getMasteredWords();

    // 1. Qidiruv
    if (SEARCH_QUERY.trim()) {
      var q = SEARCH_QUERY.trim().toLowerCase();
      pool = pool.filter(function (w) {
        return (w.ru && w.ru.toLowerCase().indexOf(q) >= 0) ||
               (w.uz && w.uz.toLowerCase().indexOf(q) >= 0) ||
               (w.note && w.note.toLowerCase().indexOf(q) >= 0);
      });
    }

    /* 2. Kategoriya.

       Kategoriya nomlari `1-8000/1001-2000/1001-1100` ko'rinishida, 229 lik
       ro'yxat esa alohida: `Глаголы настоящего времени`.

       Ilgari bu shartlar NOTO'G'RI edi va o'lchab tasdiqlandi:
         - `ru_1000` "rus va 229 emas" derdi -> 1000 emas, 8000 ta so'z
           qaytarardi, ya'ni `ru_8000` dan farq qilmasdi;
         - `ru_8000` "hamma rus" derdi -> 8229 ta, ya'ni 229 lik ro'yxatni
           ham o'z ichiga olardi.
       Endi ikkalasi ham yo'l bo'yicha aniq ajratiladi. */
    function inTree(w) { return w.cat && w.cat.indexOf('1-8000') === 0; }

    /* ANIQ nom bo'yicha. Ilgari `indexOf('Глаголы') >= 0` edi — bu
       "Тематический 9000" ichidagi `252. Глаголы А-Е` ... `257. Глаголы У-Я`
       mavzularini ham tortib olardi, ya'ni 229 lik ro'yxatga begona
       so'zlar aralashardi. */
    if (st.category === 'ru_229') {
      pool = pool.filter(function (w) {
        return w.lang === 'russian' && w.cat === CAT_229;
      });
    } else if (st.category === 'ru_1000') {
      pool = pool.filter(function (w) {
        return w.lang === 'russian' && w.cat && w.cat.indexOf('/1-1000/') >= 0;
      });
    } else if (st.category === 'ru_8000') {
      pool = pool.filter(function (w) { return w.lang === 'russian' && inTree(w); });
    } else if (st.category === 'en_8000') {
      pool = pool.filter(function (w) { return w.lang === 'english' && inTree(w); });
    }

    // 2.6 Turkum (so'z turi) — bir nechtasi tanlansa, ULARDAN BIRIGA mos
    // so'zlar qoladi (OR, Kategoriya bilan esa AND).
    if (st.partsOfSpeech && st.partsOfSpeech.length > 0) {
      pool = pool.filter(function (w) {
        return st.partsOfSpeech.indexOf(normalizePos(w.partOfSpeech)) >= 0;
      });
    }

    // 2.5 "O'rgandim" belgilangan so'zlar lentada CHIQMAYDI.
    // Istisno: foydalanuvchi ataylab "O'rganilganlar" to'plamini tanlagan
    // bo'lsa — u holda maqsad aynan o'shalarni ko'rish.
    var wantsMastered = st.collections && st.collections.indexOf('mastered') >= 0;
    if (!wantsMastered && window.WordState) {
      pool = WordState.forPractice(pool);
    }

    // 3. Shaxsiy to'plamlar
    if (st.collections && st.collections.length > 0) {
      pool = pool.filter(function (w) {
        var match = false;
        if (st.collections.indexOf('liked') >= 0 && liked.indexOf(w.ru) >= 0) match = true;
        if (st.collections.indexOf('saved') >= 0 && saved.indexOf(w.ru) >= 0) match = true;
        if (st.collections.indexOf('mastered') >= 0 && mastered.indexOf(w.ru) >= 0) match = true;
        return match;
      });
    }

    /* Natija bo'sh bo'lsa.

       ESKI XATO: bu yerda `pool = FALLBACK_WORDS` qilinardi — ya'ni filtr
       hech narsa topmasa, lentaga BEGONA so'zlar chiqardi. Foydalanuvchiga
       bu "filtr umuman ishlamayapti" bo'lib ko'rinardi, aslida filtr
       ishlagan, faqat natijasi bo'sh edi va tizim buni yashirardi.

       Endi FILTR YOQILGAN bo'lsa hech qachon zaxira so'zlarga tushmaymiz —
       bo'shligini ochiq aytamiz. Zaxira faqat FILTRSIZ holatda ishlaydi
       (masalan lug'at hali yuklanmagan). */
    if (pool.length === 0) {
      var filterOn = !!SEARCH_QUERY.trim() ||
        st.category !== 'all' ||
        (st.collections && st.collections.length > 0) ||
        (st.partsOfSpeech && st.partsOfSpeech.length > 0) ||
        !!st.join;

      if (SEARCH_QUERY.trim()) {
        return [{ ru: "Topilmadi", uz: "«" + SEARCH_QUERY.trim() + "» bo'yicha so'z yo'q. Boshqa so'z kiriting yoki filtrni tozalang.", lang: "russian", cat: "Natija yo'q", note: "", ex: "" }];
      }
      if (filterOn) {
        return [{ ru: "Natija yo'q", uz: "Tanlangan filtrlarga mos so'z topilmadi. Filtrni o'zgartiring yoki «Tozalash» bosing.", lang: "russian", cat: "Bo'sh", note: "", ex: "" }];
      }
      pool = FALLBACK_WORDS;
    }

    return pool;
  }

  /* ---------- Juftlash saralashi: o'xshash/adashtiriladigan so'zlarni yonma-yon qo'yish ----------
     vocab.js dagi buildPairGroups bilan bir xil mantiq (rus fe'l oilalari + imlosi
     yaqin so'zlar). Bu yerda til aralash bo'lishi mumkinligi uchun ru/en alohida
     guruhlanadi, keyin natija bitta lentaga birlashtiriladi. */
  /* Juftlash algoritmi `assets/js/core/paircore.js` da — YAGONA manba.
     Ilgari aynan shu kod bu yerda ham, home.js da ham nusxa bo'lib turardi;
     biri tuzatilib, ikkinchisi eskirib qolish xavfi bor edi. */
  function buildHomePairGroups(words, lang) {
    return window.PairCore ? PairCore.build(words, lang) : [];
  }

  var PAIRS_SORT_CACHE = { key: null, list: null };
  var pairGroupSeq = 0;
  /* Guruh a'zolarini "_pairGroupId" bilan belgilaydi — renderFeedItems shu orqali
     ularni bitta karusel kartaga birlashtiradi (o'rniga alohida-alohida kartalar). */
  /* `mode`: 'words' — yozilishi o'xshashlar (imlo/o'zak);
              'meaning' — ma'nosi bog'liqlar (.md dagi "Ma'no guruhi").
     Ikkalasi ham bir xil natija shaklini qaytaradi: guruh a'zolari
     ketma-ket, `_pairGroupId` bilan belgilangan holda. */
  function buildPairsSortedList(pool, mode) {
    /* Ma'no guruhi TILGA BOG'LIQ EMAS: yorliq o'zbekcha ("bormoq"),
       so'zlar esa rus yoki ingliz bo'lishi mumkin. Shuning uchun bu
       yerda tillarga bo'linmaydi. */
    if (mode === 'meaning') {
      var ordered2 = [], used2 = {};
      (window.PairCore ? PairCore.buildMeaning(pool) : []).forEach(function (g) {
        var fresh = g.filter(function (w) { return !used2[w.ru + '|' + w.uz]; });
        if (fresh.length < 2) return;
        pairGroupSeq++;
        fresh.forEach(function (w) {
          used2[w.ru + '|' + w.uz] = true;
          w._pairGroupId = pairGroupSeq;
          w._pairGroupSize = fresh.length;
          ordered2.push(w);
        });
      });
      pool.forEach(function (w) {
        var k = w.ru + '|' + w.uz;
        if (!used2[k]) { used2[k] = true; w._pairGroupId = null; ordered2.push(w); }
      });
      return ordered2;
    }

    var byLang = {};
    pool.forEach(function (w) {
      var l = w.lang === 'russian' ? 'russian' : 'english';
      (byLang[l] = byLang[l] || []).push(w);
    });
    var ordered = [], used = {};
    Object.keys(byLang).forEach(function (l) {
      buildHomePairGroups(byLang[l], l).forEach(function (g) {
        var fresh = g.filter(function (w) { return !used[w.ru + '|' + w.uz]; });
        if (fresh.length < 2) return;
        pairGroupSeq++;
        fresh.forEach(function (w) {
          used[w.ru + '|' + w.uz] = true;
          w._pairGroupId = pairGroupSeq;
          w._pairGroupSize = fresh.length;
          ordered.push(w);
        });
      });
    });
    pool.forEach(function (w) {
      var k = w.ru + '|' + w.uz;
      if (!used[k]) {
        used[k] = true;
        w._pairGroupId = null;
        ordered.push(w);
      }
    });
    return ordered;
  }

  /* Guruhdagi so'zlarning umumiy boshi/oxirini o'chirib, farq qiladigan qismini <b> bilan ajratadi */
  function highlightPairDiff(list) {
    if (list.length < 2) return list.map(function (w) { return App.esc(w); });
    var minLen = Math.min.apply(null, list.map(function (w) { return w.length; }));
    var pre = 0;
    while (pre < minLen && list.every(function (w) { return w[pre] === list[0][pre]; })) pre++;
    var suf = 0;
    while (suf < minLen - pre && list.every(function (w) { return w[w.length - 1 - suf] === list[0][list[0].length - 1 - suf]; })) suf++;
    return list.map(function (w) {
      var p = App.esc(w.slice(0, pre));
      var mid = App.esc(w.slice(pre, w.length - suf));
      var s = App.esc(w.slice(w.length - suf));
      return p + (mid ? '<b class="ig-pair-diff">' + mid + '</b>' : '') + s;
    });
  }

  /* Rangli rejim: har bir o'xshash so'zlar oilasi o'z rangini oladi, shu oiladagi
     barcha kartalar bir xil rangda ko'rinadi — bir qarashda qaysi so'z qaysi
     oilaga tegishli ekani bilinadi. */
  var PAIR_PALETTE = [
    { color: 'linear-gradient(135deg, #6366f1, #a855f7)', glow: 'linear-gradient(90deg, #6366f1, #a855f7, #ec4899)', accent: '#8b5cf6' },
    { color: 'linear-gradient(135deg, #0284c7, #06b6d4)', glow: 'linear-gradient(90deg, #0284c7, #06b6d4, #22d3ee)', accent: '#0891b2' },
    { color: 'linear-gradient(135deg, #059669, #10b981)', glow: 'linear-gradient(90deg, #059669, #10b981, #34d399)', accent: '#10b981' },
    { color: 'linear-gradient(135deg, #f59e0b, #f97316)', glow: 'linear-gradient(90deg, #f59e0b, #f97316, #ef4444)', accent: '#f97316' },
    { color: 'linear-gradient(135deg, #ec4899, #f43f5e)', glow: 'linear-gradient(90deg, #ec4899, #f43f5e, #fb7185)', accent: '#f43f5e' },
    { color: 'linear-gradient(135deg, #7c3aed, #6366f1)', glow: 'linear-gradient(90deg, #7c3aed, #6366f1, #818cf8)', accent: '#7c3aed' }
  ];
  function pairThemeFor(groupId, size) {
    var t = PAIR_PALETTE[Math.abs(groupId - 1) % PAIR_PALETTE.length];
    return {
      color: t.color, glow: t.glow, accent: t.accent,
      label: 'O\'xshash so\'zlar guruhi · ' + size + ' ta'
    };
  }

  /* Bir guruhdagi o'xshash so'zlar — har biri to'liq Reel karta, chapga/o'ngga
     surilganda guruhdagi keyingi so'zga o'tadi (lentaning o'zi tik suriladi). */
  function renderPairCarouselCard(words, baseIdx) {
    var ruList = words.map(function (w) { return String(w.ru || ''); });
    var highlighted = highlightPairDiff(ruList);

    var slidesHtml = words.map(function (w, i) {
      return '<div class="ig-pair-slide">' + renderReelCard(w, baseIdx + i, highlighted[i]) + '</div>';
    }).join('');

    var dotsHtml = words.map(function (w, i) {
      return '<span class="ig-pair-dot' + (i === 0 ? ' active' : '') + '"></span>';
    }).join('');

    return '<div class="ig-pair-carousel">' +
      '<div class="ig-pair-track">' + slidesHtml + '</div>' +
      '<div class="ig-pair-dots">' + dotsHtml + '</div>' +
    '</div>';
  }

  /* Surilganda faol nuqtani yangilab turadi */
  function bindPairCarouselEvents(host) {
    host.querySelectorAll('.ig-pair-carousel').forEach(function (car) {
      var track = car.querySelector('.ig-pair-track');
      var dots = car.querySelectorAll('.ig-pair-dot');
      if (!track || !dots.length) return;
      var raf = null;
      track.addEventListener('scroll', function () {
        if (raf) return;
        raf = requestAnimationFrame(function () {
          raf = null;
          var i = Math.round(track.scrollLeft / track.clientWidth);
          dots.forEach(function (d, di) { d.classList.toggle('active', di === i); });
        });
      }, { passive: true });
    });
  }

  /* Pick next batch of words from loaded pool based on current filter & offset */
  function getNextWords(count, offset) {
    var pool = getFilteredWordsPool();
    var st = getFilterState();

    if (!pool || pool.length === 0) return [];
    if (pool.length <= 1) return pool;

    if (st.sort === 'alpha') {
      var sorted = pool.slice().sort(function (a, b) { return (a.ru || '').localeCompare(b.ru || ''); });
      var start = offset % sorted.length;
      var end = start + count;
      if (end <= sorted.length) return sorted.slice(start, end);
      return sorted.slice(start).concat(sorted.slice(0, end - sorted.length));
    } else if (st.sort === 'recent') {
      var start = offset % pool.length;
      var end = start + count;
      if (end <= pool.length) return pool.slice(start, end);
      return pool.slice(start).concat(pool.slice(0, end - pool.length));
    } else if (st.join) {
      /* Join yoqilgan bo'lsa saralash ORNIGA guruhlash ishlaydi: guruh
         a'zolari yonma-yon turishi kerak, aks holda ularni bitta
         karuselga yig'ib bo'lmaydi. */
      var cacheKey = st.join + ':' + pool.length + ':' + (pool[0] ? pool[0].ru : '') + ':' + (pool[pool.length - 1] ? pool[pool.length - 1].ru : '');
      if (PAIRS_SORT_CACHE.key !== cacheKey) {
        PAIRS_SORT_CACHE.key = cacheKey;
        PAIRS_SORT_CACHE.list = buildPairsSortedList(pool, st.join);
      }
      var sorted = PAIRS_SORT_CACHE.list;
      if (!sorted.length) return [];
      var start = offset % sorted.length;
      var end = start + count;
      if (end <= sorted.length) return sorted.slice(start, end);
      return sorted.slice(start).concat(sorted.slice(0, end - sorted.length));
    } else {
      var selected = [];
      var poolCopy = pool.slice();
      for (var i = 0; i < count && poolCopy.length > 0; i++) {
        var rIdx = Math.floor(Math.random() * poolCopy.length);
        selected.push(poolCopy.splice(rIdx, 1)[0]);
      }
      return selected;
    }
  }

  /* Card Theme & Unique Gradient Resolver */
  function getCardTheme(w) {
    var cat = w.cat || '';
    var isRu = (w.lang === 'russian');
    /* Тематический 9000 — ikkinchi katta to'plam. Sharti BIRINCHI
       tekshiriladi: uning ichida `252. Глаголы А-Е` kabi mavzular bor,
       pastdagi 229 shartiga tushib qolmasligi kerak. */
    if (cat.indexOf(CAT_TEMA + '/') === 0) {
      return {
        badge: '9K',
        title: 'Rus tili · Mavzulashtirilgan (9000)',
        color: 'linear-gradient(135deg, #0d9488, #10b981)',
        glow: 'linear-gradient(90deg, #0d9488, #10b981, #84cc16)',
        accent: '#10b981'
      };
    }
    if (cat === CAT_229) {
      return {
        badge: '229',
        title: 'Rus tili · Hozirgi zamon (229)',
        color: 'linear-gradient(135deg, #f59e0b, #ef4444)',
        glow: 'linear-gradient(90deg, #f59e0b, #ef4444, #ec4899)',
        accent: '#ef4444'
      };
    }
    if (isRu && (cat.indexOf('1000') >= 0 || cat.indexOf('1-1000') >= 0)) {
      return {
        badge: '1K',
        title: 'Rus tili · 1000 ta asosiy so\'z',
        color: 'linear-gradient(135deg, #0284c7, #06b6d4)',
        glow: 'linear-gradient(90deg, #0284c7, #06b6d4, #3b82f6)',
        accent: '#0284c7'
      };
    }
    if (isRu) {
      return {
        badge: 'RU',
        title: 'Rus tili lug\'ati',
        color: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
        glow: 'linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7)',
        accent: '#6366f1'
      };
    }
    return {
      badge: 'EN',
      title: 'Ingliz tili · 8000 ta so\'z',
      color: 'linear-gradient(135deg, #059669, #10b981)',
      glow: 'linear-gradient(90deg, #059669, #10b981, #06b6d4)',
      accent: '#059669'
    };
  }

  /* Render a single Reel card. `titleHtml` berilsa sarlavha o'rniga ishlatiladi
     (juftlash karuselida farq qiluvchi harflarni ajratib ko'rsatish uchun). */
  function renderReelCard(w, idx, titleHtml, themeOverride) {
    var cardId = 'ig_card_' + idx + '_' + Math.floor(Math.random() * 10000);
    var isRu = (w.lang === 'russian' || /[а-яёА-ЯЁ]/.test(w.ru || ''));
    var ttsLang = isRu ? 'ru-RU' : 'en-US';
    var likes = getLikedWords();
    var isLiked = likes.indexOf(w.ru) >= 0;
    var bms = getBookmarkedWords();
    var isBookmarked = bms.indexOf(w.ru) >= 0;
    var isMastered = !!(window.WordState && WordState.isMastered(w.ru));

    var theme = getCardTheme(w);
    // Juftlash (rangli) rejimida rang oilaga qarab almashtiriladi, qolgani o'z holicha.
    if (themeOverride) {
      theme = {
        badge: theme.badge, title: theme.title,
        color: themeOverride.color, glow: themeOverride.glow, accent: themeOverride.accent
      };
    }

    return '<div class="ig-post-card' + (themeOverride ? ' ig-pair-tinted' : '') + '" id="' + cardId + '"' +
      (themeOverride ? ' style="--pair-accent:' + themeOverride.accent + '"' : '') + '>' +
      /* Card Ambient Top Glow */
      '<div class="ig-card-ambient" style="background:' + theme.glow + '"></div>' +

      /* Post Header */
      '<div class="ig-post-header">' +
        '<div class="ig-post-author">' +
          '<div class="ig-post-avatar" style="background:' + theme.color + '">' +
            '<span>' + App.esc(theme.badge) + '</span>' +
          '</div>' +
          '<div class="ig-post-meta">' +
            '<div class="ig-post-name">' +
              '<span>' + App.esc(theme.title) + '</span>' +
              '<span class="ig-verified" title="Tasdiqlangan">✓</span>' +
            '</div>' +
            '<div class="ig-post-sub">' + (themeOverride && themeOverride.label ? App.esc(themeOverride.label) : 'Lug\'at Reels · O\'rganish') + '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +

      /* Post Main Reel Body (Double tap to speak) */
      '<div class="ig-post-body" data-dbl-word="' + App.esc(w.ru) + '" data-dbl-lang="' + ttsLang + '" data-card-id="' + cardId + '">' +
        '<div class="ig-tap-speak-pop" id="pop_' + cardId + '"><span data-icon="volume" data-icon-size="44"></span></div>' +
        
        '<div class="vr-screen-flow">' +
          '<div class="vr-md-header">' +
            '<div class="vr-title-row">' +
              '<h1 class="vr-md-title">' + (titleHtml || App.esc(w.ru)) + '</h1>' +
            '</div>' +
            '<div class="vr-md-sub">' + App.esc(w.uz) + '</div>' +
            '<div class="vr-md-divider" style="background:' + theme.color + '"></div>' +
          '</div>' +
        '</div>' +
      '</div>' +

      /* Post Action Bar (Instagram style) */
      '<div class="ig-post-actions">' +
        '<div class="ig-actions-left">' +
          '<button class="ig-act-btn ' + (isLiked ? 'active liked' : '') + '" data-act="igToggleLike" data-arg=\'' + App.arg({ word: w.ru, id: cardId }) + '\' title="Yoqdi">' +
            '<span data-icon="' + (isLiked ? 'heartFill' : 'heart') + '" data-icon-size="24"></span>' +
          '</button>' +
          /* "Test" o'rniga "O'rgandim": lentada so'z ko'rilganda eng kerakli
             amal — uni bir bosishda hamma mashqdan chiqarish. Test uchun
             alohida bo'lim bor, lentada u kamdan-kam ishlatilardi. */
          '<button class="ig-act-btn ig-quiz-act-btn' + (isMastered ? ' active mastered' : '') + '" ' +
            'data-act="igToggleMastered" data-arg=\'' + App.arg({ ru: w.ru, id: cardId }) + '\' ' +
            'title="O\'rgandim — hech qayerda chiqmaydi">' +
            '<span data-icon="check" data-icon-size="20"></span>' +
            '<span class="ig-act-badge-text">' + (isMastered ? 'Bildim' : 'O\'rgandim') + '</span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igCopyWord" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz, ex: w.ex }) + '\' title="Nusxa olish">' +
            '<span data-icon="share" data-icon-size="22"></span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ru, lang: ttsLang, id: cardId }) + '\' title="Talaffuz">' +
            '<span data-icon="volume" data-icon-size="22"></span>' +
          '</button>' +
        '</div>' +
        '<div class="ig-actions-right">' +
          '<button class="ig-act-btn ' + (isBookmarked ? 'active saved' : '') + '" data-act="igToggleBookmark" data-arg=\'' + App.arg({ word: w.ru, uz: w.uz, id: cardId }) + '\' title="Saqlash">' +
            '<span data-icon="' + (isBookmarked ? 'bookmarkFill' : 'bookmark') + '" data-icon-size="24"></span>' +
          '</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  /* Educational Courses Pool for In-Feed Suggested Carousel */
  var COURSES_POOL = [
    {
      id: 'python_core',
      logo: 'assets/icons/tech/python-original.svg',
      title: 'Python Dasturlash',
      sub: 'Noldan professional darajagacha amaliy darslar',
      badge: 'Python',
      lessons: '32 dars',
      level: 'Boshlang\'ich',
      color: 'linear-gradient(135deg, #0284c7, #38bdf8)',
      icon: 'code',
      view: 'coding',
      params: { cat: 'python' }
    },
    {
      id: 'fastapi_backend',
      logo: 'assets/icons/tech/fastapi-original.svg',
      title: 'FastAPI Backend',
      sub: 'Zamonaviy REST API va Microservice arxitekturasi',
      badge: 'FastAPI',
      lessons: '24 dars',
      level: 'O\'rta',
      color: 'linear-gradient(135deg, #059669, #10b981)',
      icon: 'zap',
      view: 'coding',
      params: { cat: 'fastapi' }
    },
    {
      id: 'ru_grammar_229',
      logo: 'assets/icons/tech/flag-ru.png',
      title: 'Rus tili: 229 Fe\'l',
      sub: 'Hozirgi zamon tuslanishi, audio va misollar',
      badge: '229 Fe\'l',
      lessons: '229 fe\'l',
      level: 'Barcha darajalar',
      color: 'linear-gradient(135deg, #f59e0b, #ef4444)',
      icon: 'book',
      view: 'grammar',
      params: {}
    },
    {
      id: 'ru_tenses',
      logo: 'assets/icons/tech/flag-ru.png',
      title: 'Rus tili: Zamonlar',
      sub: 'O\'tgan, hozirgi va kelasi zamon qoidalari',
      badge: 'Grammatika',
      lessons: '18 mavzu',
      level: 'A2-B1',
      color: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
      icon: 'bookOpen',
      view: 'grammar',
      params: {}
    },
    {
      id: 'en_vocab_8000',
      logo: 'assets/icons/tech/flag-gb.png',
      title: 'Ingliz tili: 8000 So\'z',
      sub: 'Oxford 8000 eng faol va kerakli so\'zlar',
      badge: '8K So\'z',
      lessons: '8000 so\'z',
      level: 'A1-C1',
      color: 'linear-gradient(135deg, #06b6d4, #3b82f6)',
      icon: 'globe',
      view: 'languages',
      params: { lang: 'english' }
    },
    {
      id: 'postgres_db',
      logo: 'assets/icons/tech/postgresql-original.svg',
      title: 'PostgreSQL & SQL',
      sub: 'Ma\'lumotlar bazasi, jadvallar va murakkab so\'rovlar',
      badge: 'SQL',
      lessons: '20 dars',
      level: 'Amaliy',
      color: 'linear-gradient(135deg, #336791, #6366f1)',
      icon: 'layers',
      view: 'coding',
      params: { cat: 'postgresql' }
    },
    {
      id: 'linux_terminal',
      logo: 'assets/icons/tech/linux-original.svg',
      title: 'Linux & Terminal',
      sub: 'Server boshqaruvi, bash script va buyruqlar',
      badge: 'Linux',
      lessons: '16 dars',
      level: 'Amaliy',
      color: 'linear-gradient(135deg, #e11d48, #f43f5e)',
      icon: 'terminal',
      view: 'coding',
      params: { cat: 'linux' }
    },
    {
      id: 'git_github',
      logo: 'assets/icons/tech/git-original.svg',
      title: 'Git & GitHub',
      sub: 'Versiyalarni boshqarish va jamoaviy loyihalar',
      badge: 'Git',
      lessons: '12 dars',
      level: 'Muhim',
      color: 'linear-gradient(135deg, #f97316, #ea580c)',
      icon: 'gitBranch',
      view: 'coding',
      params: { cat: 'git' }
    },
    {
      id: 'books_library',
      logo: 'assets/img/vocab/book.jpg',
      title: 'Kutubxona & Kitoblar',
      sub: 'Badiiy va ilmiy kitoblar, audio kitoblar',
      badge: 'Kitoblar',
      lessons: '50+ kitob',
      level: 'Barchaga',
      color: 'linear-gradient(135deg, #8b5cf6, #d946ef)',
      icon: 'book',
      view: 'library',
      params: {}
    },
    {
      id: 'sport_workout',
      logo: 'assets/img/nav/sport.svg',
      title: 'Sport & Kunlik Mashq',
      sub: 'Kunlik qomat va salomatlik mashg\'ulotlari',
      badge: 'Workout',
      lessons: '30+ mashq',
      level: 'Barchaga',
      color: 'linear-gradient(135deg, #10b981, #059669)',
      icon: 'flame',
      view: 'sport',
      params: {}
    }
  ];

  /* Render Instagram/Threads style Suggested Courses Carousel */
  function renderCoursesCarouselCard(idx) {
    // Har safar har xil tasodifiy tartibda aralashtirish (Shuffle)
    var shuffled = COURSES_POOL.slice();
    for (var i = shuffled.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = shuffled[i];
      shuffled[i] = shuffled[j];
      shuffled[j] = temp;
    }
    var selected = shuffled.slice(0, 5);

    var itemsHtml = selected.map(function (c) {
      return '<div class="ig-course-snap-item">' +
        '<div class="ig-course-snap-card">' +
          /* Kursning O'Z logosi. Ilgari bu yerda faqat gradient va umumiy
             ikonka turardi — Python ham, Git ham bir xil ko'rinardi.
             Logo bo'lmasa eski gradient qoladi (zaxira sifatida). */
          '<div class="ig-course-snap-top' + (c.logo ? ' has-logo' : '') + '"' +
            (c.logo ? '' : ' style="background:' + c.color + '"') + '>' +
            (c.logo
              ? '<img class="ig-course-snap-logo" src="' + c.logo + '" alt="" loading="lazy">'
              : '<span class="ig-course-snap-icon" data-icon="' + (c.icon || 'book') + '" data-icon-size="28"></span>') +
            '<span class="ig-course-snap-badge">' + App.esc(c.badge) + '</span>' +
          '</div>' +
          '<div class="ig-course-snap-body">' +
            '<div class="ig-course-snap-title">' + App.esc(c.title) + '</div>' +
            '<div class="ig-course-snap-sub">' + App.esc(c.sub) + '</div>' +
            '<div class="ig-course-snap-meta">' +
              '<span class="ig-course-meta-tag">' + App.esc(c.lessons) + '</span>' +
              '<span class="ig-course-meta-tag">' + App.esc(c.level) + '</span>' +
            '</div>' +
            '<button class="ig-course-snap-cta" data-act="go" data-arg=\'' + App.arg({ v: c.view, p: c.params || {} }) + '\'>' +
              '<span>Boshlash</span> <span data-icon="arrowRight" data-icon-size="14"></span>' +
            '</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    }).join('');

    return '<div class="ig-courses-carousel-card">' +
      '<div class="ig-courses-card-header">' +
        '<div class="ig-courses-header-left">' +
          '<div class="ig-courses-header-icon">' +
            '<span data-icon="sparkles" data-icon-size="16"></span>' +
          '</div>' +
          '<div class="ig-courses-header-titles">' +
            '<div class="ig-courses-header-title">Siz uchun tavsiya etilgan kurslar</div>' +
            '<div class="ig-courses-header-sub">Interaktiv darslar va amaliyotlar</div>' +
          '</div>' +
        '</div>' +
        '<button class="ig-courses-see-all-btn" data-act="go" data-arg=\'' + App.arg({ v: 'coding' }) + '\'>' +
          '<span>Barchasi</span> <span data-icon="arrowRight" data-icon-size="12"></span>' +
        '</button>' +
      '</div>' +
      '<div class="ig-courses-track">' +
        itemsHtml +
      '</div>' +
    '</div>';
  }

  /* Render batch of items into feed */
  function renderFeedItems(count, append) {
    var host = document.getElementById('ig-feed-list');
    if (!host) return;

    if (!append) FEED_WORDS = [];
    var offset = FEED_WORDS.length;
    var newWords = getNextWords(count, offset);
    if (!newWords || newWords.length === 0) return;

    var startIdx = FEED_WORDS.length;
    FEED_WORDS = FEED_WORDS.concat(newWords);
    var fst = getFilterState();
    var colorMode = !!(fst.join && fst.joinColor);

    var htmlArr = [];
    for (var i = 0; i < newWords.length; i++) {
      var w = newWords[i];
      var globalIdx = startIdx + i;
      // Har 13 ta so'zdan keyin (2.5 baravar kamroq) tavsiya etilgan kurslar karuseli chiqsin
      if (globalIdx > 0 && globalIdx % 13 === 0) {
        htmlArr.push(renderCoursesCarouselCard(globalIdx));
      }
      // Juftlash saralashida ketma-ket kelgan bir guruh a'zolari yig'iladi.
      if (w._pairGroupId) {
        var run = [w];
        var j = i + 1;
        while (j < newWords.length && newWords[j]._pairGroupId === w._pairGroupId) {
          run.push(newWords[j]); j++;
        }
        if (colorMode) {
          // Rangli rejim: kartalar odatdagidek tik lentada qoladi, faqat bitta
          // oiladagilar bir xil rangda bo'ladi.
          var hl = highlightPairDiff(run.map(function (x) { return String(x.ru || ''); }));
          var grpTheme = pairThemeFor(w._pairGroupId, run.length);
          for (var k = 0; k < run.length; k++) {
            htmlArr.push(renderReelCard(run[k], globalIdx + k, hl[k], grpTheme));
          }
        } else {
          // Karusel rejimi: bitta surib ko'riladigan karuselga birlashtiriladi.
          htmlArr.push(renderPairCarouselCard(run, globalIdx));
        }
        i = j - 1;
        continue;
      }
      htmlArr.push(renderReelCard(w, globalIdx));
    }
    var html = htmlArr.join('');

    if (append) {
      var tmp = document.createElement('div');
      tmp.innerHTML = html;
      App.icons(tmp);
      bindDoubleTapEvents(tmp);
      bindPairCarouselEvents(tmp);
      while (tmp.firstChild) host.appendChild(tmp.firstChild);
    } else {
      host.innerHTML = html;
      App.icons(host);
      bindDoubleTapEvents(host);
      bindPairCarouselEvents(host);
    }
  }

  /* Infinite Scroll Logic */
  var INFINITE_OBSERVER = null;
  var IS_LOADING_MORE = false;
  var infiniteScrollThrottle = null;

  function initInfiniteScroll() {
    disconnectInfiniteScroll();
    var sentinel = document.getElementById('ig-infinite-sentinel');
    if (!sentinel) return;

    if ('IntersectionObserver' in window) {
      INFINITE_OBSERVER = new IntersectionObserver(function (entries) {
        if (entries[0] && entries[0].isIntersecting) {
          triggerInfiniteLoad();
        }
      }, {
        root: null,
        rootMargin: '700px',
        threshold: 0.05
      });
      INFINITE_OBSERVER.observe(sentinel);
    }

    window.addEventListener('scroll', onInfiniteWindowScroll, { passive: true });
  }

  function disconnectInfiniteScroll() {
    if (INFINITE_OBSERVER) {
      INFINITE_OBSERVER.disconnect();
      INFINITE_OBSERVER = null;
    }
    window.removeEventListener('scroll', onInfiniteWindowScroll);
  }

  function onInfiniteWindowScroll() {
    if (infiniteScrollThrottle) return;
    infiniteScrollThrottle = setTimeout(function () {
      infiniteScrollThrottle = null;
      var scrollPos = window.innerHeight + window.pageYOffset;
      var totalHeight = document.documentElement.offsetHeight || document.body.offsetHeight;
      if (totalHeight - scrollPos < 800) {
        triggerInfiniteLoad();
      }
    }, 120);
  }

  function triggerInfiniteLoad() {
    if (IS_LOADING_MORE) return;
    if (!FEED_WORDS || FEED_WORDS.length === 0) return;
    IS_LOADING_MORE = true;
    setTimeout(function () {
      renderFeedItems(6, true);
      IS_LOADING_MORE = false;
    }, 100);
  }

  /* Double Tap to Speak & Like */
  function bindDoubleTapEvents(container) {
    container.querySelectorAll('.ig-post-body').forEach(function (body) {
      var lastTap = 0;
      body.addEventListener('touchend', function (e) {
        if (e.target.closest('.vr-details-btn') || e.target.closest('.vr-quote-audio-btn')) return;
        var now = Date.now();
        if (now - lastTap < 350) {
          e.preventDefault();
          var word = body.getAttribute('data-dbl-word');
          var lang = body.getAttribute('data-dbl-lang') || 'ru-RU';
          var cardId = body.getAttribute('data-card-id');
          triggerDoubleTap(word, lang, cardId);
        }
        lastTap = now;
      });
      body.addEventListener('dblclick', function (e) {
        if (e.target.closest('.vr-details-btn') || e.target.closest('.vr-quote-audio-btn')) return;
        var word = body.getAttribute('data-dbl-word');
        var lang = body.getAttribute('data-dbl-lang') || 'ru-RU';
        var cardId = body.getAttribute('data-card-id');
        triggerDoubleTap(word, lang, cardId);
      });
    });
  }

  function triggerDoubleTap(word, lang, cardId) {
    if (!word) return;

    // 1. Ovoz chiqarish (TTS speak automatically)
    if (window.TTS && TTS.speak) {
      TTS.speak(word, lang || 'ru-RU');
    }

    // 2. Audio speaker pulse animatsiyasi
    if (cardId) {
      var pop = document.getElementById('pop_' + cardId);
      if (pop) {
        pop.classList.remove('animate');
        void pop.offsetWidth;
        pop.classList.add('animate');
        setTimeout(function () { pop.classList.remove('animate'); }, 600);
      }
    }
  }

  /* Storage Helpers */
  function getLikedWords() {
    try { return JSON.parse(localStorage.getItem('vocab_likes_v1') || '[]'); } catch (e) { return []; }
  }
  function saveLikedWords(list) {
    try { localStorage.setItem('vocab_likes_v1', JSON.stringify(list)); } catch (e) {}
  }

  /* Bu ikkisi endi FAQAT `WordState` orqali o'qiladi/yoziladi.
     Ilgari home.js o'sha kalitlarga to'g'ridan-to'g'ri yozardi, WordState
     esa ularni XOTIRADA keshlaydi — natijada bosh sahifada xatcho'p
     bosilsa, o'sha seansda lug'at ko'rgichi ESKI holatni ko'rsatardi.
     Bitta manba bo'lgach bunday ajralish mumkin emas. */
  function getBookmarkedWords() {
    return window.WordState ? WordState.savedList() : [];
  }
  function getMasteredWords() {
    return window.WordState ? WordState.masteredList() : [];
  }

  /* =========================================================
     WSTORE USLUBIDAGI MUKAMMAL FILTR MODAL (BOTTOM SHEET)
     ========================================================= */
  App.actions.wsOpenFilterModal = function () {
    var st = getFilterState();
    var activeCount = getActiveFilterCount(st);
    var filteredCount = getFilteredWordsPool().length;
    var posOptions = getAvailablePos();

    var html =
      '<div class="ws-filter-modal-wrap">' +
        /* Wstore Filter Sidebar Card */
        '<div class="ws-filter-card">' +
          '<div class="ws-filter-card-inner">' +
            /* Bo'lim 1: Saralash (Sort) */
            '<div class="ws-sec first">' +
              '<h3 class="ws-sec-title"><span class="ws-sec-bar"></span> Saralash</h3>' +
              '<div class="ws-sec-body">' +
                WSTORE_SORTS.map(function (s) {
                  var isChecked = (st.sort === s.key);
                  return '<label class="ws-radio-row" data-act="wsSelectSort" data-arg=\'' + App.arg({ s: s.key }) + '\'>' +
                    '<span class="ws-radio-circle ' + (isChecked ? 'checked' : '') + '">' +
                      (isChecked ? '<span class="ws-radio-dot"></span>' : '') +
                    '</span>' +
                    '<span class="ws-row-label">' + App.esc(s.label) + '</span>' +
                  '</label>';
                }).join('') +
              '</div>' +
            '</div>' +

            /* Bo'lim: Join — so'zlarni bog'lash mantiqi */
            '<div class="ws-sec">' +
              '<h3 class="ws-sec-title"><span class="ws-sec-bar"></span> Join</h3>' +
              '<div class="ws-sec-body">' +
                WSTORE_JOINS.map(function (j) {
                  var on = (st.join || '') === j.key;
                  return '<label class="ws-radio-row" data-act="wsSelectJoin" data-arg=\'' + App.arg({ j: j.key }) + '\'>' +
                    '<span class="ws-radio-circle ' + (on ? 'checked' : '') + '">' +
                      (on ? '<span class="ws-radio-dot"></span>' : '') +
                    '</span>' +
                    '<span class="ws-row-label">' + App.esc(j.label) +
                      '<i class="ws-row-hint">' + App.esc(j.sub) + '</i></span>' +
                  '</label>';
                }).join('') +
                (st.join
                  ? '<label class="ws-check-row" data-act="wsToggleJoinColor">' +
                    '<span class="ws-check-box ' + (st.joinColor ? 'checked' : '') + '">' +
                      (st.joinColor ? '<svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L20 6" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' : '') +
                    '</span>' +
                    '<span class="ws-row-label">Rangli kartalar' +
                      '<i class="ws-row-hint">Karusel o\'rniga: bir guruh — bir rang</i></span>' +
                  '</label>'
                  : '') +
              '</div>' +
            '</div>' +

            /* Bo'lim 2: Tillar va Lug'atlar (Category) */
            '<div class="ws-sec">' +
              '<h3 class="ws-sec-title"><span class="ws-sec-bar"></span> Tillar va Lug\'atlar</h3>' +
              '<div class="ws-sec-body">' +
                WSTORE_CATEGORIES.map(function (c) {
                  var isChecked = (st.category === c.key);
                  return '<label class="ws-check-row" data-act="wsSelectCategory" data-arg=\'' + App.arg({ c: c.key }) + '\'>' +
                    '<span class="ws-check-box ' + (isChecked ? 'checked' : '') + '">' +
                      (isChecked ? '<svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L20 6" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' : '') +
                    '</span>' +
                    '<span class="ws-row-icon" data-icon="' + c.icon + '" data-icon-size="15"></span>' +
                    '<span class="ws-row-label">' + App.esc(c.label) + '</span>' +
                  '</label>';
                }).join('') +
              '</div>' +
            '</div>' +

            /* Bo'lim: Turkum (AI .md dan) — DINAMIK, qattiq ro'yxat emas.
               Hech qanday so'zda part_of_speech bo'lmasa, bo'lim
               umuman chizilmaydi (bo'sh joy qoldirmaslik uchun). */
            (posOptions.length
              ? '<div class="ws-sec">' +
                '<h3 class="ws-sec-title"><span class="ws-sec-bar"></span> Turkum</h3>' +
                '<div class="ws-sec-body">' +
                  posOptions.map(function (p) {
                    var isChecked = st.partsOfSpeech.indexOf(p.key) >= 0;
                    return '<label class="ws-check-row" data-act="wsTogglePos" data-arg=\'' + App.arg({ k: p.key }) + '\'>' +
                      '<span class="ws-check-box ' + (isChecked ? 'checked' : '') + '">' +
                        (isChecked ? '<svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L20 6" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' : '') +
                      '</span>' +
                      '<span class="ws-row-label">' + App.esc(p.label) +
                        '<i class="ws-row-hint">' + p.count + ' ta so\'z</i></span>' +
                    '</label>';
                  }).join('') +
                '</div>' +
              '</div>'
              : '') +

            /* Bo'lim 3: Shaxsiy To'plamlar (Collections) */
            '<div class="ws-sec last">' +
              '<h3 class="ws-sec-title"><span class="ws-sec-bar"></span> Shaxsiy To\'plamlar</h3>' +
              '<div class="ws-sec-body">' +
                WSTORE_COLLECTIONS.map(function (col) {
                  var isChecked = (st.collections && st.collections.indexOf(col.key) >= 0);
                  return '<label class="ws-check-row" data-act="wsToggleCollection" data-arg=\'' + App.arg({ col: col.key }) + '\'>' +
                    '<span class="ws-check-box ' + (isChecked ? 'checked' : '') + '">' +
                      (isChecked ? '<svg width="10" height="10" viewBox="0 0 24 24" fill="none"><path d="M5 12l5 5L20 6" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>' : '') +
                    '</span>' +
                    '<span class="ws-row-icon" data-icon="' + col.icon + '" data-icon-size="15" style="color:' + col.color + '"></span>' +
                    '<span class="ws-row-label">' + App.esc(col.label) + '</span>' +
                  '</label>';
                }).join('') +
              '</div>' +
            '</div>' +
          '</div>' +

          /* Wstore pastki urg'u chizig'i */
          '<div class="ws-accent-line"></div>' +
        '</div>' +

        /* Wstore Pastki Sticky Tugmalar */
        '<div class="ws-modal-footer">' +
          '<button class="ws-clear-btn" data-act="wsClearAllFilters">' +
            '<span data-icon="refresh" data-icon-size="13"></span> Tozalash' +
          '</button>' +
          '<button class="ws-apply-btn" data-act="wsApplyFilters">' +
            'Ko\'rsatish (' + filteredCount + ')' +
          '</button>' +
        '</div>' +
      '</div>';

    App.sheet(html, {
      title: 'Filtr ' + (activeCount > 0 ? '(' + activeCount + ')' : '')
    });
  };

  /* Filter Modal Actions */
  App.actions.wsSelectSort = function (a) {
    var st = getFilterState();
    st.sort = a.s || 'popular';
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsSelectJoin = function (a) {
    var st = getFilterState();
    st.join = a.j || '';
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsToggleJoinColor = function () {
    var st = getFilterState();
    st.joinColor = !st.joinColor;
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsSelectCategory = function (a) {
    var st = getFilterState();
    st.category = a.c || 'all';
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsToggleCollection = function (a) {
    var st = getFilterState();
    var idx = st.collections.indexOf(a.col);
    if (idx >= 0) st.collections.splice(idx, 1);
    else st.collections.push(a.col);
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsTogglePos = function (a) {
    var st = getFilterState();
    var idx = st.partsOfSpeech.indexOf(a.k);
    if (idx >= 0) st.partsOfSpeech.splice(idx, 1);
    else st.partsOfSpeech.push(a.k);
    saveFilterState(st);
    App.actions.wsOpenFilterModal();
  };

  App.actions.wsClearAllFilters = function () {
    /* Ilgari bu yerda `join`/`joinColor` unutilgan edi — "Tozalash"
       bosilsa ular eskicha qolib ketardi. Endi HAMMASI asl holatiga
       qaytadi. */
    var st = { category: 'all', collections: [], sort: 'popular', join: '', joinColor: false, partsOfSpeech: [] };
    saveFilterState(st);
    SEARCH_QUERY = '';
    var inp = document.getElementById('ws-search-input');
    var clr = document.getElementById('ws-search-clear');
    if (inp) inp.value = '';
    if (clr) clr.style.display = 'none';

    updateControlsUI();
    renderFeedItems(6, false);
    App.closeSheet();
    App.toast('Barcha filtrlar tozalandi 🔄');
  };

  App.actions.wsApplyFilters = function () {
    updateControlsUI();
    renderFeedItems(6, false);
    App.closeSheet();
    App.toast('Filtrlar muvaffaqiyatli qo\'llandi ✨');
  };

  App.actions.igShuffleFeed = function () {
    renderFeedItems(6, false);
    App.toast('Tasodifiy yangi so\'zlar yuklandi! 🎲');
  };

  App.actions.igLoadMoreWords = function () {
    renderFeedItems(4, true);
  };

  App.actions.igSpeakWord = function (a) {
    if (!a || !a.text) return;
    var detectedLang = (/[а-яёА-ЯЁ]/.test(a.text)) ? 'ru-RU' : ((/[a-zA-Z]/.test(a.text)) ? 'en-US' : (a.lang || 'ru-RU'));
    if (window.TTS && TTS.speak) {
      TTS.speak(a.text, { lang: detectedLang });
    }
  };

  App.actions.igToggleLike = function (a) {
    var likes = getLikedWords();
    var idx = likes.indexOf(a.word);
    var el = document.getElementById(a.id);
    var btn = el ? el.querySelector('.ig-act-btn[data-act="igToggleLike"]') : null;

    if (idx >= 0) {
      likes.splice(idx, 1);
      if (btn) {
        btn.classList.remove('active', 'liked');
        btn.innerHTML = '<span data-icon="heart" data-icon-size="24"></span>';
        App.icons(btn);
      }
      App.toast('Sevimlilardan olib tashlandi');
    } else {
      likes.push(a.word);
      if (btn) {
        btn.classList.add('active', 'liked');
        btn.innerHTML = '<span data-icon="heartFill" data-icon-size="24"></span>';
        App.icons(btn);
      }
      App.toast('Sevimlilarga saqlandi! ❤️');
    }
    saveLikedWords(likes);
    updateStatsBar();
  };

  App.actions.igToggleBookmark = function (a) {
    if (!window.WordState) return;
    /* `WordState` orqali: u "o'rgandim" bilan ziddiyatni ham o'zi hal
       qiladi (bir so'z bir vaqtda ikkalasida turolmaydi) va keshini
       yangilaydi. Ilgari bu yerda localStorage'ga to'g'ridan-to'g'ri
       yozilardi va WordState keshi eskirib qolardi. */
    var on = WordState.toggleSaved(a.word);
    var el = document.getElementById(a.id);
    var btn = el ? el.querySelector('.ig-act-btn[data-act="igToggleBookmark"]') : null;
    if (btn) {
      btn.classList.toggle('active', on);
      btn.classList.toggle('saved', on);
      btn.innerHTML = '<span data-icon="' + (on ? 'bookmarkFill' : 'bookmark') + '" data-icon-size="24"></span>';
      App.icons(btn);
    }
    App.toast(on ? 'Saqlanganlarga qo\'shildi 🔖' : 'Saqlanganlardan olib tashlandi');
    updateStatsBar();
  };

  App.actions.igToggleMastered = function (a) {
    if (!window.WordState) return;
    var on = WordState.toggleMastered(a.ru);
    var card = document.getElementById(a.id);
    var btn = card && card.querySelector('[data-act="igToggleMastered"]');
    if (btn) {
      btn.classList.toggle('active', on);
      btn.classList.toggle('mastered', on);
      var t = btn.querySelector('.ig-act-badge-text');
      if (t) t.textContent = on ? 'Bildim' : 'O\'rgandim';
    }
    App.toast(on ? '✓ O\'rgandim — endi mashqlarda chiqmaydi' : 'Belgi olib tashlandi');
  };

  /* ================= TIZIM HOLATI =================
     Nosozlik chiqqanda birinchi savol — "nima bo'lyapti?". Ilgari buni
     faqat brauzer konsolidan bilish mumkin edi. Bu panel o'sha
     tekshiruvlarni bir joyga yig'adi va MUAMMONI ODDIY TIL bilan aytadi.

     Tekshiriladigan narsalar aynan shu kunlarda nosozlik bergan joylar:
       - ulanish va serverga javob vaqti
       - sahifa versiyasi serverdagidan orqada emasmi (eski kesh)
       - xotira sinxronizatsiyasi (`storage_bootstrap`) ishladimi —
         u yiqilsa HAMMA sozlama "saqlanmagandek" ko'rinardi
       - navbatda yuborilmagan yozuv qolmadimi
       - kesh hajmi */

  function stRow(id, label, hint) {
    return '<div class="st-row" id="st-' + id + '">' +
      '<span class="st-dot wait"></span>' +
      '<div class="st-main"><div class="st-lbl">' + App.esc(label) + '</div>' +
      '<div class="st-val">tekshirilyapti…</div></div>' +
      (hint ? '<div class="st-hint">' + App.esc(hint) + '</div>' : '') +
    '</div>';
  }

  /* state: 'ok' | 'warn' | 'bad' */
  function stSet(id, state, value, problem) {
    var el = document.getElementById('st-' + id);
    if (!el) return;
    var dot = el.querySelector('.st-dot');
    dot.className = 'st-dot ' + state;
    el.querySelector('.st-val').textContent = value;
    var old = el.querySelector('.st-problem');
    if (old) old.remove();
    if (problem) {
      var p = document.createElement('div');
      p.className = 'st-problem';
      p.textContent = problem;
      el.appendChild(p);
    }
    stSummary();
  }

  /* Yuqoridagi bitta qatorli xulosa. Panelda 12 ta qator bor — ularni
     birma-bir o'qimasdan ham "hammasi joyidami yoki yo'q" degan javob
     darhol ko'rinishi kerak. */
  function stSummary() {
    var box = document.getElementById('st-sum');
    if (!box) return;
    var rows = document.querySelectorAll('.st-row');
    var bad = 0, warn = 0, wait = 0, firstBad = '';
    rows.forEach(function (r) {
      var c = r.querySelector('.st-dot').className;
      if (c.indexOf('bad') >= 0) {
        bad++;
        if (!firstBad) firstBad = r.querySelector('.st-lbl').textContent;
      } else if (c.indexOf('warn') >= 0) warn++;
      else if (c.indexOf('wait') >= 0) wait++;
    });
    if (wait) { box.className = 'st-sum wait'; box.textContent = 'Tekshirilyapti…'; return; }
    if (bad) {
      box.className = 'st-sum bad';
      box.textContent = bad + ' ta jiddiy muammo' + (warn ? ' va ' + warn + ' ta ogohlantirish' : '') +
        ' — birinchisi: ' + firstBad;
    } else if (warn) {
      box.className = 'st-sum warn';
      box.textContent = warn + ' ta ogohlantirish, jiddiy muammo yo\'q';
    } else {
      box.className = 'st-sum ok';
      box.textContent = 'Hammasi joyida';
    }
  }

  App.actions.igSystemStatus = function () {
    var html =
      '<div class="st-sum" id="st-sum">Tekshirilyapti…</div>' +

      '<div class="st-grp">Server bilan aloqa</div>' +
      '<div class="st-wrap">' +
        stRow('net', 'Ulanish') +
        stRow('auth', 'Kirish') +
        stRow('api', 'Ma\'lumot o\'qish tezligi') +
      '</div>' +

      '<div class="st-grp">Ilova</div>' +
      '<div class="st-wrap">' +
        stRow('ver', 'Versiya') +
        stRow('mod', 'Modullar') +
        stRow('sw', 'Oflayn rejim') +
      '</div>' +

      '<div class="st-grp">Ma\'lumot saqlash</div>' +
      '<div class="st-wrap">' +
        stRow('sync', 'Xotira sinxronizatsiyasi') +
        stRow('size', 'Server xotirasi hajmi') +
        stRow('queue', 'Yuborilmagan o\'zgarishlar') +
        stRow('data', 'Yuklangan lug\'at') +
        stRow('cache', 'Qurilma keshi') +
      '</div>' +

      '<div class="st-grp">Yaqin xatolar</div>' +
      '<div class="st-wrap">' + stRow('err', 'JS xatolari') + '</div>' +
      '<div id="st-errlist"></div>' +

      '<div class="btn-row" style="margin-top:16px">' +
        '<button class="btn sec" id="st-again">Qayta tekshirish</button>' +
        '<button class="btn sec" id="st-copy">Hisobotni nusxalash</button>' +
      '</div>' +
      '<button class="btn" id="st-fix" style="margin-top:8px">Keshni tozalab yangilash</button>';

    var sh = App.sheet(html, { title: 'Tizim holati' });
    App.icons(sh);
    sh.querySelector('#st-again').onclick = runChecks;
    /* Hisobotni matn qilib nusxalash — nosozlikni boshqa birovga
       (yoki o'ziga keyinroq) yuborish uchun eng tez yo'l. */
    sh.querySelector('#st-copy').onclick = function () {
      var lines = ['Yordamchi — tizim holati', new Date().toLocaleString(), ''];
      sh.querySelectorAll('.st-row').forEach(function (r) {
        var dot = r.querySelector('.st-dot').className.replace('st-dot ', '');
        var mark = dot === 'ok' ? '[ok]  ' : dot === 'warn' ? '[!]   ' : dot === 'bad' ? '[XATO]' : '[?]   ';
        lines.push(mark + ' ' + r.querySelector('.st-lbl').textContent + ': ' +
                   r.querySelector('.st-val').textContent);
        var p = r.querySelector('.st-problem');
        if (p) lines.push('        -> ' + p.textContent);
      });
      var el = sh.querySelector('#st-errlist');
      if (el && el.textContent.trim()) lines.push('', 'Xatolar:', el.innerText);
      lines.push('', 'UA: ' + navigator.userAgent);
      try {
        navigator.clipboard.writeText(lines.join('\n'))
          .then(function () { App.toast('✅ Nusxa olindi'); })
          .catch(function () { App.toast('⚠️ Nusxa olinmadi'); });
      } catch (e) { App.toast('⚠️ Nusxa olinmadi'); }
    };
    sh.querySelector('#st-fix').onclick = function () {
      App.confirm('Barcha kesh tozalanadi va sahifa qaytadan yuklanadi. Saqlangan ma\'lumotlaringizga tegilmaydi.', function () {
        var jobs = [];
        if (window.caches) {
          jobs.push(caches.keys().then(function (k) {
            return Promise.all(k.map(function (x) { return caches.delete(x); }));
          }));
        }
        if (navigator.serviceWorker) {
          jobs.push(navigator.serviceWorker.getRegistrations().then(function (rs) {
            return Promise.all(rs.map(function (r) { return r.unregister(); }));
          }));
        }
        Promise.all(jobs).catch(function () {}).then(function () { location.reload(); });
      });
    };
    runChecks();
  };

  /* Har so'rov CHEGARALANGAN vaqtda tugaydi. Usiz sekin tarmoqda qator
     "tekshirilyapti…" holatida abadiy osilib qolardi — ya'ni panel
     aynan kerak bo'lgan paytda javob bermasdi. */
  function withTimeout(promise, ms) {
    return new Promise(function (resolve, reject) {
      var done = false;
      var t = setTimeout(function () {
        if (!done) { done = true; reject(new Error('timeout')); }
      }, ms);
      promise.then(function (v) {
        if (!done) { done = true; clearTimeout(t); resolve(v); }
      }, function (e) {
        if (!done) { done = true; clearTimeout(t); reject(e); }
      });
    });
  }

  function runChecks() {
    /* --- Ulanish ---
       `navigator.onLine` ga TAYANMAYMIZ: u faqat tarmoq interfeysi
       borligini biladi, server javob berishini emas, va ba'zi muhitlarda
       noto'g'ri `false` qaytaradi. Shuning uchun har doim HAQIQIY so'rov
       yuboriladi; `onLine` esa qo'shimcha izoh sifatida ishlatiladi. */
    var t0 = Date.now();
    withTimeout(
      fetch('version.json?t=' + Date.now(), { cache: 'no-store' })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('http')); }),
      6000
    ).then(function (j) {
      var ms = Date.now() - t0;
      stSet('net', ms > 1500 ? 'warn' : 'ok', 'Ulangan · server ' + ms + ' ms',
        ms > 1500 ? 'Server sekin javob beryapti — sahifa ochilishi cho\'zilishi mumkin.' : '');
      checkVersion(j.build);
    }).catch(function () {
      if (!navigator.onLine) {
        stSet('net', 'bad', 'Internet yo\'q',
          'Ilova oflayn ishlayapti. O\'zgarishlar shu qurilmada saqlanadi va ulanish qaytganda serverga yuboriladi.');
      } else {
        stSet('net', 'bad', 'Server javob bermadi',
          'Internet bor ko\'rinadi, lekin serverga ulanib bo\'lmadi.');
      }
      stSet('ver', 'warn', 'tekshirib bo\'lmadi',
        'Server bilan aloqa yo\'q — ilova eng so\'nggi versiyadami, bilib bo\'lmadi.');
    });

    /* --- Versiya --- */
    function checkVersion(serverBuild) {
      var m = document.querySelector('meta[name="app-build"]');
      var mine = m ? m.getAttribute('content') : '';
      if (!mine || mine === 'dev') { stSet('ver', 'ok', 'mahalliy (dev)'); return; }
      if (mine === serverBuild) stSet('ver', 'ok', mine + ' — eng so\'nggisi');
      else stSet('ver', 'bad', mine + ' (serverda ' + serverBuild + ')',
        'Ilova ESKI versiyada ishlayapti. Pastdagi "Keshni tozalab yangilash" tugmasini bosing.');
    }

    /* --- Kirish --- */
    withTimeout(fetch('/api', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amal: 'sessiya_tekshir' })
    }).then(function (r) { return r.json(); }), 6000).then(function (j) {
      if (j.kirganmi) stSet('auth', 'ok', 'Kirilgan');
      else if (j.himoya) stSet('auth', 'bad', 'Kirilmagan',
        'Sayt qulflangan. O\'zgarishlar SERVERGA SAQLANMAYDI — qaytadan kiring.');
      else stSet('auth', 'warn', 'Kirilmagan (sayt ochiq)');
    }).catch(function () {
      stSet('auth', 'warn', 'tekshirib bo\'lmadi', 'Server javob bermadi.');
    });

    /* --- Xotira sinxronizatsiyasi --- */
    var B = window.RemoteStorageBridge;
    if (!B) {
      stSet('sync', 'bad', 'modul yuklanmagan',
        'remote-storage.js ishga tushmagan — sozlamalar saqlanmaydi.');
      stSet('queue', 'warn', '—');
    } else {
      var st = B.state || {};
      var keys = st.cache ? Object.keys(st.cache).length : 0;
      if (st.ready) {
        stSet('sync', 'ok', 'Ishlayapti · ' + keys + ' ta yozuv');
      } else {
        stSet('sync', 'bad', 'Yuklanmadi',
          'Server xotirasi o\'qilmadi. Shu sababli sozlamalar (o\'rgangan so\'zlar, xatcho\'plar) BO\'SH ko\'rinishi mumkin. Ulanishni tekshiring va qayta yuklang.');
      }
      var q = st.queue ? Object.keys(st.queue).length : 0;
      if (!q) stSet('queue', 'ok', 'Hammasi yuborilgan');
      else stSet('queue', 'warn', q + ' ta kutmoqda',
        'Bu o\'zgarishlar hali serverga yetmagan. Ulanish tiklanganda o\'zi yuboriladi.');
    }

    /* --- Service worker --- */
    if (!navigator.serviceWorker) {
      stSet('sw', 'warn', 'qo\'llab-quvvatlanmaydi', 'Bu brauzerda oflayn rejim ishlamaydi.');
    } else {
      navigator.serviceWorker.getRegistrations().then(function (rs) {
        if (!rs.length) stSet('sw', 'warn', 'ro\'yxatdan o\'tmagan', 'Oflayn rejim yoqilmagan.');
        else if (!navigator.serviceWorker.controller) {
          stSet('sw', 'warn', 'faol emas', 'Sahifa bir marta yangilangach ishga tushadi.');
        } else stSet('sw', 'ok', 'Faol · oflayn ishlaydi');
      }).catch(function () { stSet('sw', 'warn', 'tekshirib bo\'lmadi'); });
    }

    /* --- Kesh hajmi --- */
    if (navigator.storage && navigator.storage.estimate) {
      navigator.storage.estimate().then(function (e) {
        var mb = (e.usage || 0) / 1048576;
        var qmb = (e.quota || 0) / 1048576;
        stSet('cache', mb > 300 ? 'warn' : 'ok',
          mb.toFixed(1) + ' MB' + (qmb ? ' / ' + qmb.toFixed(0) + ' MB' : ''),
          mb > 300 ? 'Kesh kattalashib ketdi — tozalash foydali bo\'lishi mumkin.' : '');
      }).catch(function () { stSet('cache', 'warn', 'tekshirib bo\'lmadi'); });
    } else {
      stSet('cache', 'warn', 'qo\'llab-quvvatlanmaydi');
    }

    /* --- Modullar ---
       Bitta JS fayl yuklanmasa (masalan yarim yozilgan fayl keshlanib
       qolsa) ilova jimgina buziladi: xato konsolda qoladi, ekranda esa
       shunchaki "nimadir ishlamaydi". Har modul o'z global nomini
       qo'yadi — yo'qi qaysi fayl yiqilganini aniq ko'rsatadi. */
    var MODULES = [
      ['App', 'core.js'], ['Auth', 'auth.js'], ['TTS', 'tts.js'],
      ['AppLogger', 'logger.js'], ['RemoteStorageBridge', 'remote-storage.js'],
      ['WordState', 'wordstate.js'], ['PairCore', 'paircore.js'],
      ['RDCore', 'reading.js'], ['Notify', 'notify.js']
    ];
    var missing = MODULES.filter(function (m) { return !window[m[0]]; });
    if (!missing.length) {
      stSet('mod', 'ok', MODULES.length + ' tadan ' + MODULES.length + ' ta yuklandi');
    } else {
      stSet('mod', 'bad', missing.length + ' ta yuklanmadi',
        'Bu fayllar ishga tushmadi: ' + missing.map(function (m) { return m[1]; }).join(', ') +
        '. Odatda sabab — buzuq keshlangan fayl. "Keshni tozalab yangilash" ni bosing.');
    }

    /* --- Server xotirasi hajmi ---
       Ikki marta nosozlik shu yerdan chiqqan: bitta yozuv haddan tashqari
       kattalashib, `storage_bootstrap` vaqt chegarasidan chiqib ketgan va
       BARCHA sozlama bo'sh ko'ringan. Endi hajm ko'rinib turadi, ya'ni
       muammo yuzaga chiqishidan oldin bilinadi. */
    var Bs = window.RemoteStorageBridge && RemoteStorageBridge.state;
    if (Bs && Bs.cache) {
      /* `__remote_storage_` prefiksli kalitlar HISOBGA OLINMAYDI: ular
         qurilmada qoladi va serverga hech qachon yuborilmaydi. Ilgari
         ular ham qo'shilib, o'lchov "server xotirasi" deb noto'g'ri
         katta ko'rsatardi. */
      var total = 0, biggest = null;
      Object.keys(Bs.cache).forEach(function (k) {
        if (k.indexOf('__remote_storage_') === 0) return;
        var len = (Bs.cache[k] || '').length;
        total += len;
        if (!biggest || len > biggest.n) biggest = { k: k, n: len };
      });
      var mb = total / 1048576;
      var big = biggest ? (biggest.k + ' — ' + Math.round(biggest.n / 1024) + ' KB') : '';
      if (mb > 1.5) {
        stSet('size', 'bad', mb.toFixed(2) + ' MB',
          'Juda katta. Eng kattasi: ' + big + '. Shu sababli sozlamalar yuklanmay qolishi mumkin.');
      } else if (mb > 0.8) {
        stSet('size', 'warn', mb.toFixed(2) + ' MB',
          'Kattalashib boryapti. Eng kattasi: ' + big);
      } else {
        stSet('size', 'ok', mb.toFixed(2) + ' MB' + (big ? ' · eng kattasi: ' + big : ''));
      }
    } else {
      stSet('size', 'warn', 'tekshirib bo\'lmadi');
    }

    /* --- Ma'lumot o'qish tezligi --- */
    var a0 = Date.now();
    withTimeout(
      fetch('/api?action=get_topics&lang=russian').then(function (r) {
        return r.ok ? r.json() : Promise.reject(new Error(String(r.status)));
      }), 8000
    ).then(function () {
      var ms = Date.now() - a0;
      stSet('api', ms > 2500 ? 'warn' : 'ok', ms + ' ms',
        ms > 2500 ? 'Server sekin javob beryapti — bo\'limlar kech ochiladi.' : '');
    }).catch(function (e) {
      var msg = String(e && e.message || '');
      if (msg === '401') stSet('api', 'bad', 'ruxsat yo\'q (401)', 'Tizimga kirilmagan.');
      else stSet('api', 'bad', msg === 'timeout' ? 'javob bermadi (8 s)' : 'xato',
        'Ma\'lumot o\'qib bo\'lmadi.');
    });

    /* --- Yaqin xatolar --- */
    var box = document.getElementById('st-errlist');
    var log = window.AppLogger && AppLogger.recent ? AppLogger.recent() : null;
    if (!log) {
      stSet('err', 'warn', 'jurnal mavjud emas');
    } else if (!log.length) {
      stSet('err', 'ok', 'Xato yo\'q');
      if (box) box.innerHTML = '';
    } else {
      var errs = log.filter(function (x) { return x.level === 'error'; });
      stSet('err', errs.length ? 'bad' : 'warn',
        log.length + ' ta yozuv' + (errs.length ? ' (' + errs.length + ' xato)' : ''),
        errs.length ? 'Quyida oxirgilari ko\'rsatilgan.' : '');
      if (box) {
        box.innerHTML = log.slice(-6).reverse().map(function (x) {
          var m = x.meta || {};
          var where = m.file ? String(m.file).split('/').pop() + (m.line ? ':' + m.line : '') : '';
          var t = new Date(x.at);
          return '<div class="st-err ' + x.level + '">' +
            '<b>' + App.esc(x.message) + '</b>' +
            (m.message ? '<span>' + App.esc(String(m.message)) + '</span>' : '') +
            (m.reason ? '<span>' + App.esc(String(m.reason)) + '</span>' : '') +
            '<i>' + App.esc(where) + ' · ' +
            ('0' + t.getHours()).slice(-2) + ':' + ('0' + t.getMinutes()).slice(-2) + '</i>' +
          '</div>';
        }).join('');
      }
    }

    /* --- Ma'lumot --- */
    var n = (LOADED_WORDS_POOL || []).length;
    var cached = loadFeedCache();
    var age = cached && cached.ts ? Math.round((Date.now() - cached.ts) / 60000) : null;
    if (!n) {
      stSet('data', 'bad', 'so\'zlar yuklanmagan',
        'Lug\'at o\'qilmadi. Ulanishni tekshiring yoki sahifani yangilang.');
    } else {
      stSet('data', 'ok', n + ' ta so\'z' +
        (age === null ? '' : ' · kesh ' + (age < 60 ? age + ' daqiqa' : Math.round(age / 60) + ' soat') + ' oldin'));
    }
  }

  /* Interactive Quick Quiz Sheet */
  App.actions.igOpenQuiz = function (a) {
    var correct = a.uz;
    var allUz = LOADED_WORDS_POOL.map(function (w) { return w.uz; }).filter(function (u) { return u && u !== correct; });
    var opts = [correct];
    for (var i = 0; i < 3; i++) {
      if (allUz.length > 0) {
        var r = Math.floor(Math.random() * allUz.length);
        opts.push(allUz.splice(r, 1)[0]);
      } else {
        opts.push('Boshqa ma\'no ' + (i + 1));
      }
    }
    opts.sort(function () { return Math.random() - 0.5; });

    var html =
      '<div class="ig-quiz-sheet">' +
        '<div class="ig-quiz-head">' +
          '<div class="ig-quiz-word-badge">' + App.esc(a.ru) + '</div>' +
          '<h3>Ushbu so\'zning to\'g\'ri tarjimasi qaysi?</h3>' +
        '</div>' +
        '<div class="ig-quiz-options">' +
          opts.map(function (opt) {
            var isRight = (opt === correct);
            return '<button class="ig-quiz-opt" data-act="igAnswerQuiz" data-arg=\'' + App.arg({ right: isRight, word: a.ru, id: a.id }) + '\'>' +
              '<span class="opt-bullet"></span>' +
              '<span>' + App.esc(opt) + '</span>' +
            '</button>';
          }).join('') +
        '</div>' +
      '</div>';

    App.sheet(html, { title: 'Tezkor test' });
  };

  App.actions.igAnswerQuiz = function (a, e) {
    var btn = e.target.closest('.ig-quiz-opt');
    if (!btn) return;
    if (a.right) {
      btn.style.background = 'var(--green, #10b981)';
      btn.style.borderColor = 'var(--green, #10b981)';
      btn.style.color = '#fff';
      App.toast('To\'g\'ri topdingiz! (+5 XP) 🎉');
      if (window.Activity && Activity.log) {
        Activity.log('quiz_pass', { word: a.word, xp: 5 });
      }
      setTimeout(function () { App.closeSheet(); }, 900);
    } else {
      btn.style.background = 'var(--red, #ef4444)';
      btn.style.borderColor = 'var(--red, #ef4444)';
      btn.style.color = '#fff';
      App.toast('Noto\'g\'ri, qayta urinib ko\'ring ❌');
    }
  };

  App.actions.igQuickPractice = function () {
    var pool = LOADED_WORDS_POOL.length > 0 ? LOADED_WORDS_POOL : FALLBACK_WORDS;
    var randomWord = pool[Math.floor(Math.random() * pool.length)];
    if (randomWord) {
      App.actions.igOpenQuiz({ ru: randomWord.ru, uz: randomWord.uz, id: 'quick_practice' });
    }
  };

  /* =========================================================
     INSTAGRAM STORY VIEWER ENGINE
     ========================================================= */
  App.actions.igOpenStory = function (a) {
    var story = STORIES.find(function (s) { return s.id === a.id; });
    if (!story) return;

    var modal = document.getElementById('ig-story-modal');
    if (!modal) return;

    STORY_VIEWER_STATE = {
      story: story,
      step: 0,
      totalSteps: 3,
      timer: null,
      isPaused: false
    };

    modal.classList.add('open');
    renderStoryModalContent();
    startStoryTimer();
    bindStoryTouchEvents();
  };

  function startStoryTimer() {
    if (STORY_VIEWER_STATE && STORY_VIEWER_STATE.timer) {
      clearInterval(STORY_VIEWER_STATE.timer);
    }
    if (!STORY_VIEWER_STATE) return;

    STORY_VIEWER_STATE.timer = setTimeout(function () {
      if (STORY_VIEWER_STATE && !STORY_VIEWER_STATE.isPaused) {
        App.actions.igNextStoryStep();
      }
    }, 6000);
  }

  function closeStoryViewer() {
    if (STORY_VIEWER_STATE && STORY_VIEWER_STATE.timer) {
      clearTimeout(STORY_VIEWER_STATE.timer);
    }
    STORY_VIEWER_STATE = null;
    var modal = document.getElementById('ig-story-modal');
    if (modal) modal.classList.remove('open');
  }

  App.actions.igCloseStory = function () {
    closeStoryViewer();
  };

  App.actions.igNextStoryStep = function () {
    if (!STORY_VIEWER_STATE) return;
    if (STORY_VIEWER_STATE.step < STORY_VIEWER_STATE.totalSteps - 1) {
      STORY_VIEWER_STATE.step++;
      renderStoryModalContent();
      startStoryTimer();
    } else {
      var curIdx = STORIES.findIndex(function (s) { return s.id === STORY_VIEWER_STATE.story.id; });
      if (curIdx >= 0 && curIdx < STORIES.length - 1) {
        App.actions.igOpenStory({ id: STORIES[curIdx + 1].id });
      } else {
        closeStoryViewer();
      }
    }
  };

  App.actions.igPrevStoryStep = function () {
    if (!STORY_VIEWER_STATE) return;
    if (STORY_VIEWER_STATE.step > 0) {
      STORY_VIEWER_STATE.step--;
      renderStoryModalContent();
      startStoryTimer();
    } else {
      var curIdx = STORIES.findIndex(function (s) { return s.id === STORY_VIEWER_STATE.story.id; });
      if (curIdx > 0) {
        App.actions.igOpenStory({ id: STORIES[curIdx - 1].id });
      }
    }
  };

  App.actions.igStoryAnswer = function (a, e) {
    var btn = e.target.closest('.ig-story-quiz-btn');
    if (!btn) return;
    if (a.right) {
      btn.classList.add('correct');
      App.toast('Ajoyib! To\'g\'ri javob (+5 XP) 🎉');
      if (window.Activity && Activity.log) {
        Activity.log('story_quiz', { topic: a.topic, xp: 5 });
      }
      setTimeout(function () { App.actions.igNextStoryStep(); }, 1200);
    } else {
      btn.classList.add('wrong');
      App.toast('Noto\'g\'ri tanlov ❌');
    }
  };

  App.actions.igGoStoryModule = function (a) {
    closeStoryViewer();
    if (a.type === 'vocab') {
      App.go('vocab', { lang: a.lang });
    } else if (a.type === 'grammar') {
      App.go('grammar', { lang: a.lang, folder: a.folder });
    } else if (a.type === 'coding') {
      App.go('coding', { tech: a.tech });
    }
  };

  function bindStoryTouchEvents() {
    var modal = document.getElementById('ig-story-modal');
    if (!modal) return;

    modal.onpointerdown = function () {
      if (STORY_VIEWER_STATE) {
        STORY_VIEWER_STATE.isPaused = true;
        if (STORY_VIEWER_STATE.timer) clearTimeout(STORY_VIEWER_STATE.timer);
      }
    };
    modal.onpointerup = function () {
      if (STORY_VIEWER_STATE) {
        STORY_VIEWER_STATE.isPaused = false;
        startStoryTimer();
      }
    };
  }

  function renderStoryStepBody(story, step) {
    if (step === 0) {
      return '<div class="ig-story-center-card">' +
        '<div class="ig-story-card-badge">' + App.esc(story.badge) + '</div>' +
        '<h2 class="ig-story-card-title">' + App.esc(story.title) + '</h2>' +
        '<div class="ig-story-card-sub">' + App.esc(story.sub) + '</div>' +
        '<p class="ig-story-card-desc">' + App.esc(story.desc) + '</p>' +
        '<div class="ig-story-card-hint">💡 Davom etish uchun o\'ng tomonga bosing</div>' +
      '</div>';
    }

    if (step === 1) {
      if (story.codeSnippet) {
        return '<div class="ig-story-center-card code-card">' +
          '<div class="ig-story-code-head">' +
            '<span>💻 ' + App.esc(story.codeSnippet.title) + '</span>' +
          '</div>' +
          '<pre class="ig-story-code-body"><code>' + App.esc(story.codeSnippet.code) + '</code></pre>' +
          '<div class="ig-story-code-tip">💡 ' + App.esc(story.codeSnippet.tip) + '</div>' +
        '</div>';
      } else if (story.sampleWord) {
        var isRu = (story.lang === 'russian');
        var ttsLang = isRu ? 'ru-RU' : 'en-US';
        return '<div class="ig-story-center-card word-card">' +
          '<div class="ig-story-word-hero">' +
            '<h3>' + App.esc(story.sampleWord.w) + '</h3>' +
            '<button class="ig-story-audio-btn" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: story.sampleWord.w, lang: ttsLang }) + '\'>' +
              '<span data-icon="volume" data-icon-size="16"></span> Tinglash' +
            '</button>' +
          '</div>' +
          '<div class="ig-story-word-tr">' + App.esc(story.sampleWord.tr) + '</div>' +
          '<div class="ig-story-word-forms">' + App.esc(story.sampleWord.forms) + '</div>' +
          '<div class="ig-story-word-conj">' + App.esc(story.sampleWord.conj) + '</div>' +
          '<div class="ig-story-word-ex">' +
            '💬 ' + App.esc(story.sampleWord.ex) + '<br>' +
            '<small>' + App.esc(story.sampleWord.exTr) + '</small>' +
          '</div>' +
        '</div>';
      }
    }

    if (step === 2 && story.quiz) {
      return '<div class="ig-story-center-card quiz-card">' +
        '<div class="ig-story-quiz-badge">🎯 Tezkor sinov</div>' +
        '<h3 class="ig-story-quiz-q">' + App.esc(story.quiz.q) + '</h3>' +
        '<div class="ig-story-quiz-opts">' +
          story.quiz.opts.map(function (opt, idx) {
            var isRight = (idx === story.quiz.correct);
            return '<button class="ig-story-quiz-btn" data-act="igStoryAnswer" data-arg=\'' + App.arg({ right: isRight, topic: story.title }) + '\'>' +
              App.esc(opt) +
            '</button>';
          }).join('') +
        '</div>' +
      '</div>';
    }

    return '<div class="ig-story-center-card">' +
      '<h2 class="ig-story-card-title">' + App.esc(story.title) + '</h2>' +
      '<p class="ig-story-card-desc">' + App.esc(story.desc) + '</p>' +
    '</div>';
  }

  function renderStoryModalContent() {
    var modal = document.getElementById('ig-story-modal');
    if (!modal || !STORY_VIEWER_STATE) return;

    var s = STORY_VIEWER_STATE.story;
    var step = STORY_VIEWER_STATE.step;
    var total = STORY_VIEWER_STATE.totalSteps;

    var barsHtml = '';
    for (var i = 0; i < total; i++) {
      var fillClass = (i < step) ? 'full' : (i === step ? 'active' : '');
      barsHtml += '<div class="ig-story-prog-seg"><div class="ig-story-prog-fill ' + fillClass + '"></div></div>';
    }

    modal.innerHTML =
      '<div class="ig-story-container" style="background:' + s.color + '">' +
        '<div class="ig-story-top">' +
          '<div class="ig-story-progress-bar">' + barsHtml + '</div>' +
          '<div class="ig-story-hdr">' +
            '<div class="ig-story-hdr-left">' +
              '<div class="ig-story-mini-av">' + App.esc(s.badge) + '</div>' +
              '<div><b>' + App.esc(s.title) + '</b> <span>' + App.esc(s.sub) + '</span></div>' +
            '</div>' +
            '<button class="ig-story-close-btn" data-act="igCloseStory">&times;</button>' +
          '</div>' +
        '</div>' +

        '<div class="ig-story-middle">' +
          renderStoryStepBody(s, step) +
        '</div>' +

        '<div class="ig-story-tap-left" data-act="igPrevStoryStep" title="Oldingi"></div>' +
        '<div class="ig-story-tap-right" data-act="igNextStoryStep" title="Keyingi"></div>' +

        '<div class="ig-story-footer">' +
          '<button class="btn primary full ig-story-open-btn" data-act="igGoStoryModule" data-arg=\'' + App.arg(s) + '\'>' +
            'Bo\'limni to\'liq ochish &rarr;' +
          '</button>' +
        '</div>' +
      '</div>';

    App.icons(modal);
  }

  /* =========================================================
     O'NG TOMONDAGI TEZKOR TORTMA (BARCHA BO'LIMLAR)
     ========================================================= */
  var DRAWER_SECTIONS = [
    { t: 'Maqsadlar', s: 'Kunlik vazifalar va odatlar', img: 'goals', ic: 'check', c: '#10b981', go: { v: 'goals' } },
    { t: 'Statistika', s: 'Rivojlanish ko\'rsatkichlari', img: 'stats', ic: 'chart', c: '#3b82f6', go: { v: 'stats' } },
    { t: 'Tarix', s: 'Faollik va o\'rganishlar arxivi', img: 'tarix', ic: 'clock', c: '#8b5cf6', go: { v: 'tarix' } },
    { t: 'Testlar', s: 'Bilimni sinash uchun testlar', img: 'fanlar', ic: 'book', c: '#f59e0b', go: { v: 'fanlar' } },
    { t: 'Coding', s: 'Dasturlash darsliklari va amaliyot', img: 'coding', ic: 'code', c: '#06b6d4', go: { v: 'coding' } },
    { t: 'Boostday', s: 'Intensiv rivojlanish rejasi', img: 'boost', ic: 'message', c: '#ec4899', go: { v: 'boost' } },
    { t: 'Arxiv', s: 'Bajarilgan maqsadlar ombori', img: 'arxiv', ic: 'archive', c: '#64748b', go: { v: 'arxiv' } },
    { t: 'Qoidalar', s: 'Hayotiy qoidalar va tamoyillar', img: 'qoidalar', ic: 'file', c: '#14b8a6', go: { v: 'qoidalar' } },
    { t: 'Grammatika', s: 'Rus tili zamonlari va qoidalari', img: 'languages', ic: 'book', c: '#a855f7', go: { v: 'grammar', p: { lang: 'russian', folder: '05. Времена глагола (Zamonlar)' } } },
    { t: 'Lug\'at', s: '1-8000 so\'zlar to\'liq bazasi', img: 'languages', ic: 'globe', c: '#0ea5e9', go: { v: 'vocab', p: { lang: 'russian' } } },
    { t: 'Profil', s: 'Rivojlanish profili va faollik', img: 'profile', ic: 'user', c: '#6366f1', go: { v: 'profile' } }
  ];

  var DW = null;

  function unmountDrawer() {
    if (!DW) return;
    document.removeEventListener('click', DW.onDocClick, true);
    DW.el.remove();
    DW = null;
  }

  function mountDrawer() {
    unmountDrawer();
    var el = document.createElement('div');
    el.className = 'hdw';
    el.innerHTML =
      '<button class="hdw-handle" id="hdw-handle" aria-label="Barcha bo\'limlar" title="Barcha bo\'limlar">' +
        '<span class="hdw-handle-glow"></span>' +
        '<div class="hdw-handle-inner">' +
          '<span class="hdw-arrow-ic" data-icon="arrowLeft" data-icon-size="14"></span>' +
          '<i class="hdw-pill"></i>' +
        '</div>' +
      '</button>' +
      '<div class="hdw-panel">' +
        '<div class="hdw-title">' +
          '<span>Barcha bo\'limlar</span>' +
          '<span data-icon="sparkles" data-icon-size="14" style="color:var(--accent)"></span>' +
        '</div>' +
        DRAWER_SECTIONS.map(function (x) {
          return '<button class="hdw-row" data-act="go" data-arg=\'' + App.arg(x.go) + '\'>' +
            '<img src="assets/img/nav/' + x.img + '.svg?v=20260820v10" alt="" width="26" height="26" style="width:26px;height:26px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
            '<span class="hdw-m"><b>' + App.esc(x.t) + '</b><span>' + App.esc(x.s) + '</span></span>' +
            '</button>';
        }).join('') +
      '</div>';
    document.body.appendChild(el);
    App.icons(el);

    var handle = el.querySelector('#hdw-handle');
    var W = function () { return parseFloat(getComputedStyle(el).getPropertyValue('--hdw-w')) || 244; };

    function setOpen(on) { el.classList.toggle('open', !!on); }
    function isOpen() { return el.classList.contains('open'); }

    var drag = null;
    handle.addEventListener('pointerdown', function (e) {
      drag = { x: e.clientX, base: isOpen() ? 0 : W(), moved: 0 };
      el.classList.add('drag');
      try { handle.setPointerCapture(e.pointerId); } catch (err) {}
    });
    handle.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x;
      drag.moved = Math.max(drag.moved, Math.abs(dx));
      var off = Math.max(0, Math.min(W(), drag.base + dx));
      el.style.transform = 'translateY(-50%) translateX(' + off + 'px)';
    });
    function endDrag(e) {
      if (!drag) return;
      var dx = (e.clientX || 0) - drag.x;
      var off = Math.max(0, Math.min(W(), drag.base + dx));
      el.classList.remove('drag');
      el.style.transform = '';
      setOpen(drag.moved < 6 ? !isOpen() : off < W() / 2);
      drag = null;
    }
    handle.addEventListener('pointerup', endDrag);
    handle.addEventListener('pointercancel', endDrag);

    function onDocClick(e) {
      if (!DW || !isOpen()) return;
      if (el.contains(e.target)) return;
      setOpen(false);
    }
    document.addEventListener('click', onDocClick, true);

    DW = { el: el, onDocClick: onDocClick };
  }

})();
