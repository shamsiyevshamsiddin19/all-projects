/* ============================================================
   Yordamchi — Bosh sahifa (Wstore uslubidagi mukammal filtr va Reels Feed)
   Aynan wstore.uz kabi: Filtr tugmasi, qidiruv, modal panel, 
   bo'limlar, saralash, tozalash va "Ko'rsatish (N)" amallari
   ============================================================ */
(function () {
  'use strict';

  /* Stories ro'yxati */
  var STORIES = [
    {
      id: 'ru_229',
      title: 'Hozirgi zamon',
      sub: '229 ta fe\'l',
      type: 'vocab',
      lang: 'russian',
      category: 'Глаголы настоящего времени',
      color: 'linear-gradient(135deg, #f59e0b, #ef4444)',
      badge: '229',
      desc: 'Rus tilida eng ko\'p ishlatiladigan 229 ta fe\'lning hozirgi zamon tuslanishi, shakllari va ma\'nodoshlari.',
      sampleWord: {
        w: 'я изучаю',
        tr: 'men o\'rganyapman / tadqiq qilyapman',
        forms: 'изучать (NCV) · изучить (CV) · я изучал (o\'tgan zamon)',
        conj: 'я изучаю · ты изучаешь · он изучает · мы изучаем · вы изучаете · они изучают',
        ex: 'Я с большим интересом изучаю веб-разработку и русский язык.',
        exTr: 'Men katta qiziqish bilan veb-dasturlash va rus tilini o\'rganyapman.'
      },
      quiz: {
        q: '«изучать» fe\'lining «мы» (biz) uchun hozirgi zamon shakli qaysi?',
        opts: ['мы изучаем', 'мы изучаете', 'мы изучают', 'мы изучил'],
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
    { key: 'saved', label: 'Saqlangan xatcho\'plar', icon: 'bookmarkFill', color: '#3b82f6' },
    { key: 'mastered', label: 'O\'rganilgan so\'zlar', icon: 'check', color: '#10b981' }
  ];

  var WSTORE_SORTS = [
    { key: 'popular', label: 'Ommabop / Tasodifiy' },
    { key: 'alpha', label: 'Alifbo bo\'yicha (A–Z)' },
    { key: 'recent', label: 'Eng yangi so\'zlar' }
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
        sort: s.sort || 'popular'
      };
    } catch (e) {
      return { category: 'all', collections: [], sort: 'popular' };
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
              '<button class="ig-btn-icon" data-act="igQuickPractice" title="Tezkor amaliyot / Test">' +
                '<span data-icon="zap" data-icon-size="20"></span>' +
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

          /* Load More Bar */
          '<div class="ig-load-more-wrap">' +
            '<button class="btn primary full ig-load-btn" data-act="igLoadMoreWords">' +
              '<span data-icon="refresh" data-icon-size="18"></span> Yana tasodifiy so\'zlar' +
            '</button>' +
          '</div>' +
        '</div>' +
        
        /* Story Viewer Modal Container */
        '<div id="ig-story-modal" class="ig-story-modal"></div>';

      App.icons(page);
      bindSearchEvents(page);
      initFeed();
      mountDrawer();
    },
    leave: function () {
      closeStoryViewer();
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
  function renderSubChipsHtml(st) {
    var quickList = [
      { id: 'all', label: 'Barchasi' },
      { id: 'ru_229', label: '229 Fe\'l' },
      { id: 'ru_1000', label: 'Rus 1K' },
      { id: 'en_8000', label: 'Ingliz 8K' },
      { id: 'liked', label: '❤️ Sevimlilar', isCol: true },
      { id: 'saved', label: '🔖 Xatcho\'plar', isCol: true },
      { id: 'mastered', label: '✅ O\'rganilganlar', isCol: true }
    ];

    return quickList.map(function (q) {
      var isAct = false;
      if (q.isCol) {
        isAct = st.collections && st.collections.indexOf(q.id) >= 0;
      } else {
        isAct = (st.category === q.id) && (!st.collections || st.collections.length === 0);
      }
      return '<button class="ws-chip ' + (isAct ? 'active' : '') + '" data-act="wsToggleQuickChip" data-arg=\'' + App.arg(q) + '\'>' +
        App.esc(q.label) +
      '</button>';
    }).join('');
  }

  App.actions.wsToggleQuickChip = function (a) {
    var st = getFilterState();
    if (a.isCol) {
      var idx = st.collections.indexOf(a.id);
      if (idx >= 0) st.collections.splice(idx, 1);
      else st.collections.push(a.id);
    } else {
      st.category = a.id;
      st.collections = [];
    }
    saveFilterState(st);
    updateControlsUI();
    renderFeedItems(6, false);
  };

  function updateControlsUI() {
    var st = getFilterState();
    var count = getActiveFilterCount(st);
    var badge = document.getElementById('ws-filter-badge');
    if (badge) {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
    var chips = document.getElementById('ws-chips-row');
    if (chips) {
      chips.innerHTML = renderSubChipsHtml(st);
      App.icons(chips);
    }
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
  function initFeed() {
    FEED_WORDS = [];
    LOADED_WORDS_POOL = [];

    App.call('get_dict_data', null, { query: 'lang=russian' })
      .then(function (res) {
        var items = (res && res.items) ? res.items : [];
        if (items.length > 0) {
          items.forEach(function (it) {
            LOADED_WORDS_POOL.push({
              ru: it.word_ru,
              uz: it.word_uz,
              lang: 'russian',
              cat: it.category || 'Rus tili',
              note: it.note || '',
              ex: it.example || ''
            });
          });
        }
        return App.call('get_dict_data', null, { query: 'lang=english' }).catch(function () { return null; });
      })
      .then(function (enRes) {
        var enItems = (enRes && enRes.items) ? enRes.items : [];
        if (enItems.length > 0) {
          enItems.forEach(function (it) {
            LOADED_WORDS_POOL.push({
              ru: it.word_ru,
              uz: it.word_uz,
              lang: 'english',
              cat: it.category || 'Ingliz tili',
              note: it.note || '',
              ex: it.example || ''
            });
          });
        }
        renderFeedItems(6);
      })
      .catch(function () {
        LOADED_WORDS_POOL = FALLBACK_WORDS.slice();
        renderFeedItems(6);
      });
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

    // 2. Kategoriya
    if (st.category === 'ru_229') {
      pool = pool.filter(function (w) { return w.cat && (w.cat.indexOf('Глаголы') >= 0 || w.cat.indexOf('229') >= 0); });
    } else if (st.category === 'ru_1000') {
      pool = pool.filter(function (w) { return w.lang === 'russian' && (!w.cat || (w.cat.indexOf('Глаголы') < 0 && w.cat.indexOf('229') < 0)); });
    } else if (st.category === 'ru_8000') {
      pool = pool.filter(function (w) { return w.lang === 'russian'; });
    } else if (st.category === 'en_8000') {
      pool = pool.filter(function (w) { return w.lang === 'english'; });
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

    // Fallback if empty
    if (pool.length === 0) {
      if (SEARCH_QUERY.trim()) {
        return [{ ru: "Qidiruv natijasi topilmadi", uz: "Boshqa so'z kiritib ko'ring yoki filtrlarni tozalang.", lang: "russian", cat: "Natija yo'q", note: "", ex: "" }];
      }
      if (st.collections && st.collections.length > 0) {
        return [{ ru: "To'plam bo'sh", uz: "Tanlangan filtr bo'yicha hali so'zlar mavjud emas.", lang: "russian", cat: "Bo'sh", note: "", ex: "" }];
      }
      pool = FALLBACK_WORDS;
    }

    return pool;
  }

  /* Pick random words from loaded pool based on current filter */
  function getRandomWords(count) {
    var pool = getFilteredWordsPool();
    var st = getFilterState();

    var result = pool.slice();
    if (st.sort === 'alpha') {
      result.sort(function (a, b) { return (a.ru || '').localeCompare(b.ru || ''); });
      return result.slice(0, count);
    } else if (st.sort === 'recent') {
      return result.slice(0, count);
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

  /* Format note fields into structured HTML */
  function formatNoteHtml(note) {
    if (!note) return '';
    var lines = String(note).split('\n');
    var html = [];
    lines.forEach(function (l) {
      l = l.trim();
      if (!l) return;
      if (l.indexOf('Qayerda:') === 0) {
        html.push('<div class="ig-card-field field-where"><b>💡 Qo\'llanishi:</b> ' + App.esc(l.replace('Qayerda:', '').trim()) + '</div>');
      } else if (l.indexOf('Shakl:') === 0) {
        html.push('<div class="ig-card-field field-form"><b>🔄 Shakllari:</b> ' + App.esc(l.replace('Shakl:', '').trim()) + '</div>');
      } else if (l.indexOf('Vid:') === 0) {
        html.push('<div class="ig-card-field field-vid"><b>⚖️ Vid jufti:</b> ' + App.esc(l.replace('Vid:', '').trim()) + '</div>');
      } else if (l.indexOf('Ma\'nodosh:') === 0) {
        html.push('<div class="ig-card-field field-syn"><b>🌿 Ma\'nodoshlari:</b> ' + App.esc(l.replace('Ma\'nodosh:', '').trim()) + '</div>');
      } else {
        html.push('<div class="ig-card-field">' + App.esc(l) + '</div>');
      }
    });
    return html.join('');
  }

  /* Render a single Reel card */
  function renderReelCard(w, idx) {
    var cardId = 'ig_card_' + idx + '_' + Math.floor(Math.random() * 10000);
    var isRu = (w.lang === 'russian');
    var ttsLang = isRu ? 'ru-RU' : 'en-US';
    var likes = getLikedWords();
    var isLiked = likes.indexOf(w.ru) >= 0;
    var bms = getBookmarkedWords();
    var isBookmarked = bms.indexOf(w.ru) >= 0;
    var mastered = getMasteredWords();
    var isMastered = mastered.indexOf(w.ru) >= 0;

    var catTitle = w.cat || (isRu ? 'Rus tili' : 'Ingliz tili');
    if (catTitle.indexOf('Глаголы') >= 0 || catTitle.indexOf('229') >= 0) catTitle = 'Rus tili · Hozirgi zamon (229)';
    else if (catTitle.indexOf('1-8000') >= 0) catTitle = isRu ? 'Rus tili lug\'ati' : 'Ingliz tili lug\'ati';

    return '<div class="ig-post-card ' + (isRu ? 'theme-ru' : 'theme-en') + '" id="' + cardId + '">' +
      /* Card Ambient Top Glow */
      '<div class="ig-card-ambient"></div>' +

      /* Post Header */
      '<div class="ig-post-header">' +
        '<div class="ig-post-author">' +
          '<div class="ig-post-avatar" style="background:' + (isRu ? 'linear-gradient(135deg,#0088cc,#00c6ff)' : 'linear-gradient(135deg,#059669,#10b981)') + '">' +
            '<span>' + (isRu ? '🇷🇺' : '🇬🇧') + '</span>' +
          '</div>' +
          '<div class="ig-post-meta">' +
            '<div class="ig-post-name">' +
              '<span>' + App.esc(catTitle) + '</span>' +
              '<span class="ig-verified" title="Tasdiqlangan">✓</span>' +
            '</div>' +
            '<div class="ig-post-sub">Reels Lug\'at</div>' +
          '</div>' +
        '</div>' +
        '<div class="ig-post-header-actions">' +
          '<button class="ig-post-more ' + (isMastered ? 'mastered' : '') + '" data-act="igToggleMastered" data-arg=\'' + App.arg({ word: w.ru, id: cardId }) + '\' title="' + (isMastered ? 'O\'rganilgan' : 'O\'rganildi deb belgilash') + '">' +
            '<span data-icon="' + (isMastered ? 'check' : 'circle') + '" data-icon-size="16"></span>' +
            '<span class="ig-master-text">' + (isMastered ? 'O\'rgandim' : 'O\'rganish') + '</span>' +
          '</button>' +
        '</div>' +
      '</div>' +

      /* Post Main Reel Body (Double tap to like) */
      '<div class="ig-post-body" data-dbl-word="' + App.esc(w.ru) + '" data-card-id="' + cardId + '">' +
        '<div class="ig-heart-pop" id="pop_' + cardId + '"><span data-icon="heartFill" data-icon-size="76"></span></div>' +
        
        '<div class="ig-word-stage">' +
          '<div class="ig-word-main">' + App.esc(w.ru) + '</div>' +
          '<button class="ig-sound-wave-btn" id="snd_' + cardId + '" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ru, lang: ttsLang, id: cardId }) + '\' title="Ovoz chiqarish">' +
            '<span class="ig-sound-wave">' +
              '<i class="bar"></i><i class="bar"></i><i class="bar"></i><i class="bar"></i>' +
            '</span>' +
            '<span data-icon="volume" data-icon-size="16"></span>' +
          '</button>' +
        '</div>' +

        '<div class="ig-trans-wrap">' +
          '<div class="ig-trans-badge">' +
            '<span class="ig-trans-spark" data-icon="sparkles" data-icon-size="13"></span>' +
            '<span class="ig-trans-text">' + App.esc(w.uz) + '</span>' +
          '</div>' +
        '</div>' +
      '</div>' +

      /* Post Action Bar (Instagram style) */
      '<div class="ig-post-actions">' +
        '<div class="ig-actions-left">' +
          '<button class="ig-act-btn ' + (isLiked ? 'active liked' : '') + '" data-act="igToggleLike" data-arg=\'' + App.arg({ word: w.ru, id: cardId }) + '\' title="Yoqdi">' +
            '<span data-icon="' + (isLiked ? 'heartFill' : 'heart') + '" data-icon-size="24"></span>' +
          '</button>' +
          '<button class="ig-act-btn ig-quiz-act-btn" data-act="igOpenQuiz" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz, id: cardId }) + '\' title="O\'zini tekshirish (Test)">' +
            '<span data-icon="check" data-icon-size="20"></span>' +
            '<span class="ig-act-badge-text">Test</span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igCopyWord" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz }) + '\' title="Nusxa olish">' +
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

  /* Render batch of items into feed */
  function renderFeedItems(count, append) {
    var host = document.getElementById('ig-feed-list');
    if (!host) return;

    var newWords = getRandomWords(count);
    if (!append) FEED_WORDS = [];
    var startIdx = FEED_WORDS.length;
    FEED_WORDS = FEED_WORDS.concat(newWords);

    var html = newWords.map(function (w, i) {
      return renderReelCard(w, startIdx + i);
    }).join('');

    if (append) {
      var tmp = document.createElement('div');
      tmp.innerHTML = html;
      App.icons(tmp);
      bindDoubleTapEvents(tmp);
      while (tmp.firstChild) host.appendChild(tmp.firstChild);
    } else {
      host.innerHTML = html;
      App.icons(host);
      bindDoubleTapEvents(host);
    }
  }

  /* Double Tap to Like */
  function bindDoubleTapEvents(container) {
    container.querySelectorAll('.ig-post-body').forEach(function (body) {
      var lastTap = 0;
      body.addEventListener('touchend', function (e) {
        var now = Date.now();
        if (now - lastTap < 300) {
          e.preventDefault();
          var word = body.getAttribute('data-dbl-word');
          var cardId = body.getAttribute('data-card-id');
          triggerDoubleTapLike(word, cardId);
        }
        lastTap = now;
      });
      body.addEventListener('dblclick', function () {
        var word = body.getAttribute('data-dbl-word');
        var cardId = body.getAttribute('data-card-id');
        triggerDoubleTapLike(word, cardId);
      });
    });
  }

  function triggerDoubleTapLike(word, cardId) {
    if (!word || !cardId) return;
    var pop = document.getElementById('pop_' + cardId);
    if (pop) {
      pop.classList.remove('animate');
      void pop.offsetWidth;
      pop.classList.add('animate');
      setTimeout(function () { pop.classList.remove('animate'); }, 850);
    }
    var likes = getLikedWords();
    if (likes.indexOf(word) < 0) {
      likes.push(word);
      saveLikedWords(likes);
      var el = document.getElementById(cardId);
      var btn = el ? el.querySelector('.ig-act-btn[data-act="igToggleLike"]') : null;
      if (btn) {
        btn.classList.add('active', 'liked');
        btn.innerHTML = '<span data-icon="heartFill" data-icon-size="24"></span>';
        App.icons(btn);
      }
      updateStatsBar();
      App.toast('Sevimlilarga saqlandi! ❤️');
    }
  }

  /* Storage Helpers */
  function getLikedWords() {
    try { return JSON.parse(localStorage.getItem('vocab_likes_v1') || '[]'); } catch (e) { return []; }
  }
  function saveLikedWords(list) {
    try { localStorage.setItem('vocab_likes_v1', JSON.stringify(list)); } catch (e) {}
  }

  function getBookmarkedWords() {
    try { return JSON.parse(localStorage.getItem('vocab_bookmarks_v1') || '[]'); } catch (e) { return []; }
  }
  function saveBookmarkedWords(list) {
    try { localStorage.setItem('vocab_bookmarks_v1', JSON.stringify(list)); } catch (e) {}
  }

  function getMasteredWords() {
    try { return JSON.parse(localStorage.getItem('vocab_mastered_v1') || '[]'); } catch (e) { return []; }
  }
  function saveMasteredWords(list) {
    try { localStorage.setItem('vocab_mastered_v1', JSON.stringify(list)); } catch (e) {}
  }

  /* =========================================================
     WSTORE USLUBIDAGI MUKAMMAL FILTR MODAL (BOTTOM SHEET)
     ========================================================= */
  App.actions.wsOpenFilterModal = function () {
    var st = getFilterState();
    var activeCount = getActiveFilterCount(st);
    var filteredCount = getFilteredWordsPool().length;

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

  App.actions.wsClearAllFilters = function () {
    var st = { category: 'all', collections: [], sort: 'popular' };
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
    if (!a.text) return;
    if (a.id) {
      var snd = document.getElementById('snd_' + a.id);
      if (snd) {
        snd.classList.add('playing');
        setTimeout(function () { snd.classList.remove('playing'); }, 1800);
      }
    }
    if (window.TTS && TTS.speak) {
      TTS.speak(a.text, a.lang || 'ru-RU');
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
    var bms = getBookmarkedWords();
    var idx = bms.indexOf(a.word);
    var el = document.getElementById(a.id);
    var btn = el ? el.querySelector('.ig-act-btn[data-act="igToggleBookmark"]') : null;

    if (idx >= 0) {
      bms.splice(idx, 1);
      if (btn) {
        btn.classList.remove('active', 'saved');
        btn.innerHTML = '<span data-icon="bookmark" data-icon-size="24"></span>';
        App.icons(btn);
      }
      App.toast('Xatcho\'plardan olib tashlandi');
    } else {
      bms.push(a.word);
      if (btn) {
        btn.classList.add('active', 'saved');
        btn.innerHTML = '<span data-icon="bookmarkFill" data-icon-size="24"></span>';
        App.icons(btn);
      }
      App.toast('Xatcho\'plarga saqlandi! 🔖');
    }
    saveBookmarkedWords(bms);
    updateStatsBar();
  };

  App.actions.igToggleMastered = function (a) {
    var list = getMasteredWords();
    var idx = list.indexOf(a.word);
    var el = document.getElementById(a.id);
    var btn = el ? el.querySelector('.ig-post-more') : null;

    if (idx >= 0) {
      list.splice(idx, 1);
      if (btn) {
        btn.classList.remove('mastered');
        btn.innerHTML = '<span data-icon="circle" data-icon-size="18"></span><span class="ig-master-text">O\'rganish</span>';
        App.icons(btn);
      }
      App.toast('O\'rganilmagan holatga qaytarildi');
    } else {
      list.push(a.word);
      if (btn) {
        btn.classList.add('mastered');
        btn.innerHTML = '<span data-icon="check" data-icon-size="18"></span><span class="ig-master-text">O\'rgandim</span>';
        App.icons(btn);
      }
      if (window.Activity && Activity.log) {
        Activity.log('vocab_master', { word: a.word, xp: 10 });
      }
      App.toast('Ajoyib! So\'z o\'rganildi (+10 XP) 🎉');
    }
    saveMasteredWords(list);
    updateStatsBar();
  };

  App.actions.igCopyWord = function (a) {
    var text = '📖 ' + (a.ru || '') + ' — ' + (a.uz || '') + '\n' +
      (a.ex ? '💬 ' + a.ex + '\n' : '') +
      '✨ Yordamchi ilovasi orqali';
    try {
      navigator.clipboard.writeText(text);
      App.toast('So\'z nusxalandi! 📋');
    } catch (e) {
      App.toast('Nusxalab bo\'lmadi');
    }
  };

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
