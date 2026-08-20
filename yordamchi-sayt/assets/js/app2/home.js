/* ============================================================
   Yordamchi — Bosh sahifa (Instagram Stories & Reels Feed)
   Filtrlash paneli va sozlash oynasi bilan
   ============================================================ */
(function () {
  'use strict';

  /* Stories ro'yxati (Lug'atlar, Grammatika va Darsliklar) */
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

  /* Fallback tasodifiy so'zlar zaxirasi */
  var FALLBACK_WORDS = [
    {
      ru: "я играю",
      uz: "men o'ynayapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Sport yoki kompyuter o'yinlarini o'ynash, musiqa asboblarini chalish hamda sahnada rol ijro etishda qo'llaniladi. Birikmalarda: играть в шахматы (shaxmat o'ynamoq), играть на гитаре (gitara chalmoq).\nShakl: hozirgi zamon (я) — я играю, infinitivi — играть, o'tgan zamon — я играл\nVid: NCV — играть (doimiy jarayon), CV — сыграть / поиграть (tugallangan)\nMa'nodosh: развлекаться (ko'ngilxushlik qilmoq), резвиться (sho'xlik qilmoq)",
      ex: "Я каждый вечер с удовольствием играю в шахматы с дедушкой. (Men har oqshom bobom bilan maroq bilan shaxmat o'ynayman.)"
    },
    {
      ru: "я пишу",
      uz: "men yozyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Qalam, ruchka yoki klaviatura orqali matn, xat, ariza yaratishda ishlatiladi.\nShakl: hozirgi zamon (я) — я пишу, infinitivi — писать, o'tgan zamon — я писал\nVid: NCV — писать (yozish jarayoni), CV — написать (yozib tugatmoq)\nMa'nodosh: сочинять (ijod qilmoq), записывать (qayd etmoq)",
      ex: "Я сейчас пишу важное электронное письмо преподавателю. (Men hozir o'qituvchiga muhim elektron xat yozyapman.)"
    },
    {
      ru: "я говорю",
      uz: "men gapiryapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Nutq tovushlarini chiqarish, suhbatlashish yoki biror tilda muloqot qilishda qo'llaniladi.\nShakl: hozirgi zamon (я) — я говорю, infinitivi — говорить, o'tgan zamon — я говорил\nVid: NCV — говорить (davomiy nutq), CV — сказать / поговорить\nMa'nodosh: беседовать (suhbatlashmoq), произносить (talaffuz qilmoq)",
      ex: "Я свободно говорю на двух иностранных языках. (Men ikkita chet tilida erkin gapiraman.)"
    },
    {
      ru: "я учу",
      uz: "men o'rganyapman / o'rgatyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: 1) Yod olish, o'rganish; 2) Boshqalarga ta'lim berish, o'rgatish.\nShakl: hozirgi zamon (я) — я учу, infinitivi — учить, o'tgan zamon — я учил\nVid: NCV — учить (jarayon), CV — выучить (yodlamoq) / научить (o'rgatmoq)\nMa'nodosh: обучать (ta'lim bermoq), зубрить (quruq yodlamoq)",
      ex: "Я каждый день учу двадцать новых русских слов. (Men har kuni 20 ta yangi ruscha so'z yodlayapman.)"
    },
    {
      ru: "accomplish",
      uz: "amalga oshirmoq, erishmoq",
      lang: "english",
      cat: "Ingliz tili 8000",
      note: "Qayerda: Murakkab vazifa, reja yoki maqsadni muvaffaqiyatli uddalashda ishlatiladi.\nMa'nodosh: achieve (erishmoq), complete (yakunlamoq), fulfill (bajarmoq)",
      ex: "She accomplished all her goals this year. (U bu yil o'zining barcha maqsadlariga erishdi.)"
    },
    {
      ru: "я мечтаю",
      uz: "men orzu qilyapman",
      lang: "russian",
      cat: "Hozirgi zamon (229)",
      note: "Qayerda: Kelajakdagi ezgu niyatlar, istaklar haqida xayol surish yoki erishishni xohlashda ishlatiladi.\nShakl: hozirgi zamon (я) — я мечтаю, infinitivi — мечтать, o'tgan zamon — я мечтал\nVid: NCV — мечтать (orzu qilish), CV — помечтать\nMa'nodosh: грезить (xayol surmoq), фантазировать (tasavvur qilmoq)",
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

  /* Filtr ta'riflari va metama'lumotlari */
  var FILTER_LABELS = {
    all: { title: 'Barcha so\'zlar', desc: 'Rus va Ingliz tili lug\'atlari aralash', icon: 'globe', color: '#6366f1' },
    ru_229: { title: 'Hozirgi zamon (229)', desc: '229 ta ruscha fe\'l tuslanishi va tahlili', icon: 'zap', color: '#f59e0b' },
    ru_1000: { title: 'Rus tili 1000', desc: 'Asosiy 1000 ta ruscha lug\'at so\'zlari', icon: 'book', color: '#3b82f6' },
    en_8000: { title: 'Ingliz tili (8000)', desc: 'Oxford va Cambridge 8000 so\'zlar bazasi', icon: 'globe', color: '#10b981' },
    ru_8000: { title: 'Rus tili (8000)', desc: 'Katta 8000 ta ruscha lug\'at bazasi', icon: 'book', color: '#8b5cf6' },
    liked: { title: 'Sevimli so\'zlarim', desc: 'Yurakcha bosilgan so\'zlar to\'plami', icon: 'heartFill', color: '#ef4444' },
    saved: { title: 'Saqlangan xatcho\'plar', desc: 'Xatcho\'pga saqlab qo\'yilgan so\'zlar', icon: 'bookmarkFill', color: '#0ea5e9' },
    mastered: { title: 'O\'rganilgan so\'zlar', desc: 'O\'rgandim deb belgilangan so\'zlar', icon: 'check', color: '#10b981' }
  };

  var FEED_WORDS = [];
  var LOADED_WORDS_POOL = [];
  var STORY_VIEWER_STATE = null;

  /* Filter holatini localStorage dan o'qish / saqlash */
  function getFilterState() {
    try {
      var s = JSON.parse(localStorage.getItem('home_filter_state_v2') || '{}');
      return {
        category: s.category || 'all',
        sort: s.sort || 'random',
        batchSize: s.batchSize || 6
      };
    } catch (e) {
      return { category: 'all', sort: 'random', batchSize: 6 };
    }
  }

  function saveFilterState(st) {
    try { localStorage.setItem('home_filter_state_v2', JSON.stringify(st)); } catch (e) {}
  }

  App.view('home', {
    nav: 'home',
    render: function (page) {
      var st = getFilterState();
      var curInfo = FILTER_LABELS[st.category] || FILTER_LABELS.all;

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

          /* Daily Stats Mini Bar */
          '<div class="ig-stats-bar" id="ig-stats-bar">' +
            renderStatsBarHtml() +
          '</div>' +

          /* Asosiy Filtr Paneli (Button + Quick Chips) */
          '<div class="ig-filter-control-card">' +
            '<div class="ig-filter-header-wrap">' +
              '<div class="ig-filter-head-left">' +
                '<span class="ig-filter-dot" style="background:' + curInfo.color + '"></span>' +
                '<span class="ig-filter-current-label">Filtr: <b id="ig-filter-active-name">' + App.esc(curInfo.title) + '</b></span>' +
              '</div>' +
              '<button class="ig-filter-panel-btn" data-act="igOpenFilterSheet">' +
                '<span data-icon="sliders" data-icon-size="16"></span>' +
                '<span>Filtrlar</span>' +
                '<span class="ig-filter-badge-pill">' + (st.sort === 'alpha' ? 'A-Z' : (st.sort === 'recent' ? 'Yangi' : 'Mix')) + '</span>' +
              '</button>' +
            '</div>' +

            '<div class="ig-filter-quick-chips" id="ig-filter-quick-chips">' +
              renderQuickChipsHtml(st.category) +
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
      initFeed();
      mountDrawer();
    },
    leave: function () {
      closeStoryViewer();
      unmountDrawer();
    }
  });

  /* Quick chips renderer */
  function renderQuickChipsHtml(activeCat) {
    var quickList = [
      { id: 'all', label: 'Barchasi' },
      { id: 'ru_229', label: '229 Fe\'l' },
      { id: 'ru_1000', label: 'Rus 1K' },
      { id: 'en_8000', label: 'Ingliz 8K' },
      { id: 'liked', label: '❤️ Sevimlilar' },
      { id: 'saved', label: '🔖 Xatcho\'plar' }
    ];

    return quickList.map(function (q) {
      var isAct = (q.id === activeCat);
      return '<button class="ig-qchip ' + (isAct ? 'active' : '') + '" data-act="igQuickFilter" data-arg=\'' + App.arg({ f: q.id }) + '\'>' +
        App.esc(q.label) +
      '</button>';
    }).join('') +
    '<button class="ig-qchip ig-qchip-more" data-act="igOpenFilterSheet">' +
      '<span data-icon="sliders" data-icon-size="13"></span> Ko\'proq...' +
    '</button>';
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
        var st = getFilterState();
        renderFeedItems(st.batchSize || 6);
      })
      .catch(function () {
        LOADED_WORDS_POOL = FALLBACK_WORDS.slice();
        var st = getFilterState();
        renderFeedItems(st.batchSize || 6);
      });
  }

  /* Pick random words from loaded pool based on current filter */
  function getRandomWords(count, filterState) {
    filterState = filterState || getFilterState();
    var filter = filterState.category || 'all';
    var pool = LOADED_WORDS_POOL.length > 0 ? LOADED_WORDS_POOL : FALLBACK_WORDS;
    var liked = getLikedWords();
    var saved = getBookmarkedWords();
    var mastered = getMasteredWords();

    if (filter === 'ru_229') {
      pool = pool.filter(function (w) { return w.cat && (w.cat.indexOf('Глаголы') >= 0 || w.cat.indexOf('229') >= 0); });
    } else if (filter === 'ru_1000') {
      pool = pool.filter(function (w) { return w.lang === 'russian' && (!w.cat || (w.cat.indexOf('Глаголы') < 0 && w.cat.indexOf('229') < 0)); });
    } else if (filter === 'ru_8000') {
      pool = pool.filter(function (w) { return w.lang === 'russian'; });
    } else if (filter === 'en_8000') {
      pool = pool.filter(function (w) { return w.lang === 'english'; });
    } else if (filter === 'liked') {
      pool = pool.filter(function (w) { return liked.indexOf(w.ru) >= 0; });
    } else if (filter === 'saved') {
      pool = pool.filter(function (w) { return saved.indexOf(w.ru) >= 0; });
    } else if (filter === 'mastered') {
      pool = pool.filter(function (w) { return mastered.indexOf(w.ru) >= 0; });
    }

    if (pool.length === 0) {
      if (filter === 'liked') return [{ ru: "❤️ Sevimli so'zlar", uz: "Quyidagi postlardagi yurakchani bosib sevimli so'zlar to'plamini yarating.", lang: "russian", cat: "Bo'sh", note: "", ex: "" }];
      if (filter === 'saved') return [{ ru: "🔖 Saqlanganlar", uz: "Xatcho'p tugmasini bosib kerakli so'zlarni saqlab qo'ying.", lang: "russian", cat: "Bo'sh", note: "", ex: "" }];
      if (filter === 'mastered') return [{ ru: "✅ O'rganilganlar", uz: "Postlardagi «O'rgandim» tugmasini bosib bilgan so'zlaringizni belgilang.", lang: "russian", cat: "Bo'sh", note: "", ex: "" }];
      pool = FALLBACK_WORDS;
    }

    var result = pool.slice();
    if (filterState.sort === 'alpha') {
      result.sort(function (a, b) { return (a.ru || '').localeCompare(b.ru || ''); });
      return result.slice(0, count);
    } else if (filterState.sort === 'recent') {
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

    return '<div class="ig-post-card" id="' + cardId + '">' +
      /* Post Header */
      '<div class="ig-post-header">' +
        '<div class="ig-post-author">' +
          '<div class="ig-post-avatar" style="background:' + (isRu ? 'linear-gradient(135deg,#3b82f6,#06b6d4)' : 'linear-gradient(135deg,#10b981,#3b82f6)') + '">' +
            '<span>' + (isRu ? 'RU' : 'EN') + '</span>' +
          '</div>' +
          '<div class="ig-post-meta">' +
            '<div class="ig-post-name">' + App.esc(catTitle) + ' <span class="ig-verified">✓</span></div>' +
            '<div class="ig-post-sub">Lug\'at Reels · Tasodifiy so\'z</div>' +
          '</div>' +
        '</div>' +
        '<div class="ig-post-header-actions">' +
          '<button class="ig-post-more ' + (isMastered ? 'mastered' : '') + '" data-act="igToggleMastered" data-arg=\'' + App.arg({ word: w.ru, id: cardId }) + '\' title="' + (isMastered ? 'O\'rganilgan' : 'O\'rganildi deb belgilash') + '">' +
            '<span data-icon="' + (isMastered ? 'check' : 'circle') + '" data-icon-size="18"></span>' +
            '<span class="ig-master-text">' + (isMastered ? 'O\'rgandim' : 'O\'rganish') + '</span>' +
          '</button>' +
        '</div>' +
      '</div>' +

      /* Post Main Reel Body (Double tap to like) */
      '<div class="ig-post-body" data-dbl-word="' + App.esc(w.ru) + '" data-card-id="' + cardId + '">' +
        '<div class="ig-heart-pop" id="pop_' + cardId + '"><span data-icon="heartFill" data-icon-size="70"></span></div>' +
        '<div class="ig-word-stage">' +
          '<div class="ig-word-main">' + App.esc(w.ru) + '</div>' +
          '<button class="ig-speak-pill" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ru, lang: ttsLang }) + '\'>' +
            '<span data-icon="volume" data-icon-size="14"></span> Tinglash' +
          '</button>' +
        '</div>' +

        '<div class="ig-trans-badge">' +
          '<span class="ig-trans-text">' + App.esc(w.uz) + '</span>' +
        '</div>' +

        (w.note ? '<div class="ig-details-box">' + formatNoteHtml(w.note) + '</div>' : '') +

        (w.ex ? '<div class="ig-example-box">' +
          '<div class="ig-ex-head">💬 Jonli misol:</div>' +
          '<div class="ig-ex-body">' + App.esc(w.ex) + '</div>' +
          '<button class="ig-ex-audio" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ex.split('(')[0], lang: ttsLang }) + '\'>' +
            '<span data-icon="play" data-icon-size="13"></span> Gapni eshitish' +
          '</button>' +
        '</div>' : '') +
      '</div>' +

      /* Post Action Bar (Instagram style) */
      '<div class="ig-post-actions">' +
        '<div class="ig-actions-left">' +
          '<button class="ig-act-btn ' + (isLiked ? 'active liked' : '') + '" data-act="igToggleLike" data-arg=\'' + App.arg({ word: w.ru, id: cardId }) + '\' title="Yoqdi">' +
            '<span data-icon="' + (isLiked ? 'heartFill' : 'heart') + '" data-icon-size="24"></span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igOpenQuiz" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz, id: cardId }) + '\' title="O\'zini tekshirish (Test)">' +
            '<span data-icon="check" data-icon-size="24"></span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igCopyWord" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz, ex: w.ex }) + '\' title="Nusxa olish">' +
            '<span data-icon="share" data-icon-size="22"></span>' +
          '</button>' +
          '<button class="ig-act-btn" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ru, lang: ttsLang }) + '\' title="Talaffuz">' +
            '<span data-icon="volume" data-icon-size="24"></span>' +
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

    var st = getFilterState();
    var newWords = getRandomWords(count, st);
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

  /* Double Tap to Like on Reel Body */
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
     INTERAKTIV FILTR SHEET VA ACTIONS
     ========================================================= */
  App.actions.igQuickFilter = function (a) {
    var st = getFilterState();
    st.category = a.f || 'all';
    saveFilterState(st);

    var curInfo = FILTER_LABELS[st.category] || FILTER_LABELS.all;
    var nameEl = document.getElementById('ig-filter-active-name');
    if (nameEl) nameEl.textContent = curInfo.title;

    var dot = document.querySelector('.ig-filter-dot');
    if (dot) dot.style.background = curInfo.color;

    var chipsHost = document.getElementById('ig-filter-quick-chips');
    if (chipsHost) {
      chipsHost.innerHTML = renderQuickChipsHtml(st.category);
      App.icons(chipsHost);
    }

    renderFeedItems(st.batchSize || 6, false);
    App.toast('Filtr: ' + curInfo.title + ' ✨');
  };

  App.actions.igOpenFilterSheet = function () {
    var s = getFilterState();
    var html =
      '<div class="ig-filter-sheet-body">' +
        '<div class="ig-fs-sec-title">Lug\'at va Mavzu bo\'limi</div>' +
        '<div class="ig-fs-grid">' +
          Object.keys(FILTER_LABELS).map(function (k) {
            var info = FILTER_LABELS[k];
            var isSel = (s.category === k);
            return '<button class="ig-fs-card ' + (isSel ? 'selected' : '') + '" data-act="igSelectFilterCategory" data-arg=\'' + App.arg({ f: k }) + '\'>' +
              '<div class="ig-fs-card-left">' +
                '<span class="ig-fs-icon" style="background:' + info.color + '"><span data-icon="' + info.icon + '" data-icon-size="16"></span></span>' +
                '<div class="ig-fs-info">' +
                  '<div class="ig-fs-name">' + App.esc(info.title) + '</div>' +
                  '<div class="ig-fs-desc">' + App.esc(info.desc) + '</div>' +
                '</div>' +
              '</div>' +
              '<span class="ig-fs-radio ' + (isSel ? 'checked' : '') + '"></span>' +
            '</button>';
          }).join('') +
        '</div>' +

        '<div class="ig-fs-sec-title" style="margin-top:18px">Saralash tartibi</div>' +
        '<div class="seg seg-sm" style="width:100%;margin-bottom:16px" id="ig-fs-sort-seg">' +
          '<button class="' + (s.sort === 'random' ? 'active' : '') + '" data-act="igSelectFilterSort" data-arg=\'{"s":"random"}\'>🎲 Tasodifiy</button>' +
          '<button class="' + (s.sort === 'alpha' ? 'active' : '') + '" data-act="igSelectFilterSort" data-arg=\'{"s":"alpha"}\'>🔤 Alifbo (A-Z)</button>' +
          '<button class="' + (s.sort === 'recent' ? 'active' : '') + '" data-act="igSelectFilterSort" data-arg=\'{"s":"recent"}\'>⏱ Yangilar</button>' +
        '</div>' +

        '<div class="ig-fs-actions">' +
          '<button class="btn sec" data-act="igResetFilters" style="flex:1">Tozalash</button>' +
          '<button class="btn primary" data-act="igApplyFilterSheet" style="flex:2">Filtrni qo\'llash</button>' +
        '</div>' +
      '</div>';

    App.sheet(html, { title: 'Tasmani sozlash va filtrlash' });
  };

  App.actions.igSelectFilterCategory = function (a, e) {
    var card = e.target.closest('.ig-fs-card');
    if (!card) return;
    document.querySelectorAll('.ig-fs-card').forEach(function (c) {
      c.classList.remove('selected');
      var r = c.querySelector('.ig-fs-radio');
      if (r) r.classList.remove('checked');
    });
    card.classList.add('selected');
    var r = card.querySelector('.ig-fs-radio');
    if (r) r.classList.add('checked');

    var st = getFilterState();
    st.category = a.f || 'all';
    saveFilterState(st);
  };

  App.actions.igSelectFilterSort = function (a, e) {
    var seg = document.getElementById('ig-fs-sort-seg');
    if (seg) {
      seg.querySelectorAll('button').forEach(function (b) { b.classList.remove('active'); });
      if (e && e.target) e.target.classList.add('active');
    }
    var st = getFilterState();
    st.sort = a.s || 'random';
    saveFilterState(st);
  };

  App.actions.igResetFilters = function () {
    var st = { category: 'all', sort: 'random', batchSize: 6 };
    saveFilterState(st);
    App.closeSheet();

    var curInfo = FILTER_LABELS.all;
    var nameEl = document.getElementById('ig-filter-active-name');
    if (nameEl) nameEl.textContent = curInfo.title;
    var dot = document.querySelector('.ig-filter-dot');
    if (dot) dot.style.background = curInfo.color;
    var chipsHost = document.getElementById('ig-filter-quick-chips');
    if (chipsHost) {
      chipsHost.innerHTML = renderQuickChipsHtml('all');
      App.icons(chipsHost);
    }
    renderFeedItems(6, false);
    App.toast('Barcha filtrlar tozalandi 🔄');
  };

  App.actions.igApplyFilterSheet = function () {
    var st = getFilterState();
    App.closeSheet();

    var curInfo = FILTER_LABELS[st.category] || FILTER_LABELS.all;
    var nameEl = document.getElementById('ig-filter-active-name');
    if (nameEl) nameEl.textContent = curInfo.title;

    var dot = document.querySelector('.ig-filter-dot');
    if (dot) dot.style.background = curInfo.color;

    var chipsHost = document.getElementById('ig-filter-quick-chips');
    if (chipsHost) {
      chipsHost.innerHTML = renderQuickChipsHtml(st.category);
      App.icons(chipsHost);
    }

    renderFeedItems(st.batchSize || 6, false);
    App.toast('Filtr qo\'llandi: ' + curInfo.title + ' 🎯');
  };

  App.actions.igShuffleFeed = function () {
    var st = getFilterState();
    renderFeedItems(st.batchSize || 6, false);
    App.toast('Tasodifiy yangi so\'zlar yuklandi! 🎲');
  };

  App.actions.igLoadMoreWords = function () {
    renderFeedItems(4, true);
  };

  App.actions.igSpeakWord = function (a) {
    if (!a.text) return;
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
     INSTAGRAM STORY VIEWER ENGINE (FULL SCREEN & MULTI-STEP)
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
        /* Top Progress & Header */
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

        /* Story Middle Dynamic Content */
        '<div class="ig-story-middle">' +
          renderStoryStepBody(s, step) +
        '</div>' +

        /* Story Navigation Tap Zones (Left/Right) */
        '<div class="ig-story-tap-left" data-act="igPrevStoryStep" title="Oldingi"></div>' +
        '<div class="ig-story-tap-right" data-act="igNextStoryStep" title="Keyingi"></div>' +

        /* Story Footer Action Button */
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
