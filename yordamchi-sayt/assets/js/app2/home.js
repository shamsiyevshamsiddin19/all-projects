/* Bosh sahifa — Instagram Stories va Reels uslubidagi tasodifiy lug'at tasmasi. */
(function () {
  'use strict';

  /* Stories ro'yxati (Lug'atlar va Darsliklar) */
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
      icon: 'globe',
      desc: 'Rus tilida eng ko\'p ishlatiladigan 229 ta fe\'lning mukammal tahlili'
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
      icon: 'globe',
      desc: 'Eng ko\'p uchraydigan 1000 ta ruscha so\'z va misollar'
    },
    {
      id: 'ru_8000',
      title: 'Rus tili 8000',
      sub: 'Katta lug\'at',
      type: 'vocab',
      lang: 'russian',
      category: '1-8000',
      color: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
      badge: '8K',
      icon: 'globe',
      desc: 'Rus tilining 8000 ta so\'zdan iborat to\'liq lug\'at bazasi'
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
      icon: 'globe',
      desc: 'Ingliz tilining 8000 ta eng muhim so\'zlari'
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
      icon: 'book',
      desc: 'Rus tili zamonlari, turlari va qoidalari'
    },
    {
      id: 'cs_python',
      title: 'Python',
      sub: 'Darslik',
      type: 'coding',
      tech: 'python',
      color: 'linear-gradient(135deg, #3776AB, #FFD43B)',
      badge: 'PY',
      icon: 'code',
      desc: 'Python dasturlash tili asoslari va loyihalar'
    },
    {
      id: 'cs_fastapi',
      title: 'FastAPI',
      sub: 'Darslik',
      type: 'coding',
      tech: 'fastapi',
      color: 'linear-gradient(135deg, #009688, #059669)',
      badge: 'API',
      icon: 'code',
      desc: 'Zamonaviy asinxron REST API yaratish kursi'
    },
    {
      id: 'cs_git',
      title: 'Git & GitHub',
      sub: 'Darslik',
      type: 'coding',
      tech: 'git',
      color: 'linear-gradient(135deg, #F05032, #EA4C89)',
      badge: 'GIT',
      icon: 'code',
      desc: 'Versiyalar nazorati va GitHub bilan ishlash'
    },
    {
      id: 'cs_linux',
      title: 'Linux',
      sub: 'Darslik',
      type: 'coding',
      tech: 'linux',
      color: 'linear-gradient(135deg, #FCC624, #222)',
      badge: 'LNX',
      icon: 'code',
      desc: 'Linux buyruqlari, server sozlash va terminal'
    },
    {
      id: 'cs_postgres',
      title: 'PostgreSQL',
      sub: 'Darslik',
      type: 'coding',
      tech: 'postgresql',
      color: 'linear-gradient(135deg, #336791, #4169E1)',
      badge: 'SQL',
      icon: 'code',
      desc: 'SQL so\'rovlar va ma\'lumotlar bazasini boshqarish'
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
    }
  ];

  var FEED_WORDS = [];
  var LOADED_WORDS_POOL = [];
  var CURRENT_FILTER = 'all';
  var IS_FETCHING = false;
  var STORY_VIEWER_STATE = null;

  App.view('home', {
    nav: 'home',
    render: function (page) {
      page.innerHTML =
        '<div class="ig-home-wrap">' +
          /* Instagram Top Bar */
          '<header class="ig-header">' +
            '<div class="ig-brand">' +
              '<span class="ig-logo-text">Yordamchi</span>' +
              '<span class="ig-sparkle" data-icon="sparkles" data-icon-size="16"></span>' +
            '</div>' +
            '<div class="ig-actions">' +
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

          /* Filter Chips */
          '<div class="ig-filter-bar">' +
            '<button class="ig-chip active" data-act="igSetFilter" data-arg=\'{"f":"all"}\'>Barchasi</button>' +
            '<button class="ig-chip" data-act="igSetFilter" data-arg=\'{"f":"ru_229"}\'>Hozirgi zamon (229)</button>' +
            '<button class="ig-chip" data-act="igSetFilter" data-arg=\'{"f":"ru_1000"}\'>Rus tili (1000)</button>' +
            '<button class="ig-chip" data-act="igSetFilter" data-arg=\'{"f":"en_8000"}\'>Ingliz tili</button>' +
          '</div>' +

          /* Instagram Reels Feed */
          '<div class="ig-feed" id="ig-feed-list">' +
            '<div class="ig-feed-loader"><div class="spin"></div><span>Lug\'atlar yuklanmoqda...</span></div>' +
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
    },
    leave: function () {
      closeStoryViewer();
    }
  });

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

  /* Load all dictionary words from API or local storage */
  function initFeed() {
    FEED_WORDS = [];
    LOADED_WORDS_POOL = [];

    // Try loading Russian dictionary items
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
        // Also fetch English
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

  /* Pick random words from loaded pool */
  function getRandomWords(count, filter) {
    var pool = LOADED_WORDS_POOL.length > 0 ? LOADED_WORDS_POOL : FALLBACK_WORDS;
    if (filter === 'ru_229') {
      pool = pool.filter(function (w) { return w.cat && w.cat.indexOf('Глаголы') >= 0; });
    } else if (filter === 'ru_1000') {
      pool = pool.filter(function (w) { return w.lang === 'russian' && w.cat && w.cat.indexOf('Глаголы') < 0; });
    } else if (filter === 'en_8000') {
      pool = pool.filter(function (w) { return w.lang === 'english'; });
    }
    if (pool.length === 0) pool = FALLBACK_WORDS;

    var selected = [];
    var poolCopy = pool.slice();
    for (var i = 0; i < count; i++) {
      if (poolCopy.length === 0) poolCopy = pool.slice();
      var rIdx = Math.floor(Math.random() * poolCopy.length);
      selected.push(poolCopy.splice(rIdx, 1)[0]);
    }
    return selected;
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

    var catTitle = w.cat || (isRu ? 'Rus tili' : 'Ingliz tili');
    if (catTitle.indexOf('Глаголы') >= 0) catTitle = 'Rus tili · Hozirgi zamon (229)';
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
            '<div class="ig-post-sub">Lug\'at Reels · Tasodifiy</div>' +
          '</div>' +
        '</div>' +
        '<button class="ig-post-more" data-act="igSpeakWord" data-arg=\'' + App.arg({ text: w.ru, lang: ttsLang }) + '\' title="Ovoz chiqarish">' +
          '<span data-icon="volume" data-icon-size="20"></span>' +
        '</button>' +
      '</div>' +

      /* Post Main Reel Body */
      '<div class="ig-post-body">' +
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
          '<button class="ig-act-btn" data-act="igOpenQuiz" data-arg=\'' + App.arg({ ru: w.ru, uz: w.uz, id: cardId }) + '\' title="O\'zini tekshirish">' +
            '<span data-icon="check" data-icon-size="24"></span>' +
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

    var newWords = getRandomWords(count, CURRENT_FILTER);
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
      while (tmp.firstChild) host.appendChild(tmp.firstChild);
    } else {
      host.innerHTML = html;
      App.icons(host);
    }
  }

  /* Like storage */
  function getLikedWords() {
    try { return JSON.parse(localStorage.getItem('vocab_likes_v1') || '[]'); } catch (e) { return []; }
  }
  function saveLikedWords(list) {
    try { localStorage.setItem('vocab_likes_v1', JSON.stringify(list)); } catch (e) {}
  }

  /* Bookmark storage */
  function getBookmarkedWords() {
    try { return JSON.parse(localStorage.getItem('vocab_bookmarks_v1') || '[]'); } catch (e) { return []; }
  }
  function saveBookmarkedWords(list) {
    try { localStorage.setItem('vocab_bookmarks_v1', JSON.stringify(list)); } catch (e) {}
  }

  /* Actions */
  App.actions.igSetFilter = function (a, e) {
    CURRENT_FILTER = a.f || 'all';
    var chips = document.querySelectorAll('.ig-chip');
    chips.forEach(function (c) { c.classList.remove('active'); });
    if (e && e.target) e.target.classList.add('active');
    renderFeedItems(6, false);
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
  };

  /* Interactive Quiz Action */
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
    // Shuffle options
    opts.sort(function () { return Math.random() - 0.5; });

    var html =
      '<div class="ig-quiz-sheet">' +
        '<div class="ig-quiz-head">' +
          '<h3>«' + App.esc(a.ru) + '» so\'zining tarjimasi qaysi?</h3>' +
        '</div>' +
        '<div class="ig-quiz-options">' +
          opts.map(function (opt) {
            var isRight = (opt === correct);
            return '<button class="ig-quiz-opt" data-act="igAnswerQuiz" data-arg=\'' + App.arg({ right: isRight, id: a.id }) + '\'>' +
              App.esc(opt) +
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
      btn.style.color = '#fff';
      App.toast('To\'g\'ri topdingiz! 🎉');
      setTimeout(function () { App.closeSheet(); }, 900);
    } else {
      btn.style.background = 'var(--red, #ef4444)';
      btn.style.color = '#fff';
      App.toast('Noto\'g\'ri, qayta urinib ko\'ring ❌');
    }
  };

  /* =========================================================
     INSTAGRAM STORY VIEWER (FULL SCREEN)
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
      timer: null
    };

    modal.classList.add('open');
    renderStoryModalContent();
  };

  function closeStoryViewer() {
    if (STORY_VIEWER_STATE && STORY_VIEWER_STATE.timer) {
      clearInterval(STORY_VIEWER_STATE.timer);
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
    } else {
      closeStoryViewer();
    }
  };

  App.actions.igPrevStoryStep = function () {
    if (!STORY_VIEWER_STATE) return;
    if (STORY_VIEWER_STATE.step > 0) {
      STORY_VIEWER_STATE.step--;
      renderStoryModalContent();
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

  function renderStoryModalContent() {
    var modal = document.getElementById('ig-story-modal');
    if (!modal || !STORY_VIEWER_STATE) return;

    var s = STORY_VIEWER_STATE.story;
    var step = STORY_VIEWER_STATE.step;
    var total = STORY_VIEWER_STATE.totalSteps;

    // Progress segments
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

        /* Story Middle Content */
        '<div class="ig-story-middle">' +
          '<div class="ig-story-center-card">' +
            '<div class="ig-story-card-badge">' + App.esc(s.badge) + '</div>' +
            '<h2 class="ig-story-card-title">' + App.esc(s.title) + '</h2>' +
            '<p class="ig-story-card-desc">' + App.esc(s.desc) + '</p>' +
            '<div class="ig-story-card-tip">Qadam ' + (step + 1) + ' / ' + total + '</div>' +
          '</div>' +
        '</div>' +

        /* Story Navigation Tap Zones (Left/Right) */
        '<div class="ig-story-tap-left" data-act="igPrevStoryStep"></div>' +
        '<div class="ig-story-tap-right" data-act="igNextStoryStep"></div>' +

        /* Story Footer Action Button */
        '<div class="ig-story-footer">' +
          '<button class="btn primary full ig-story-open-btn" data-act="igGoStoryModule" data-arg=\'' + App.arg(s) + '\'>' +
            'Bo\'limga o\'tish &rarr;' +
          '</button>' +
        '</div>' +
      '</div>';

    App.icons(modal);
  }

})();
