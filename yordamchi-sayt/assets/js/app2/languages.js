/* Tillar: Ingliz, Rus, Coding — hublar + foydalanuvchi qo'shgan tillar (CRUD). */
(function () {
  'use strict';

  /* ---------- Til logolari (devicon CDN) ---------- */
  /* Logolar SERVERDA (assets/icons/tech) — CDN'ga bog'liq emas,
     shuning uchun oflaynda ham ko'rinadi va tezroq yuklanadi.
     Manba: Devicon (MIT). Yuklab olingan: 138 ta. */
  var DEVICON = 'assets/icons/tech/';
  /* Ikonka manzillarida versiya. Sabab: bu fayllar (bayroqlar, devicon SVG'lari)
     `?v=` siz so'ralardi, nginx esa ularni uzoq keshlar edi — almashtirilgan
     ikonka foydalanuvchiga yetib bormasdi (2026-08-17 da bayroqlar shu sababdan
     ko'rinmadi). Ikonka almashtirilsa SHU raqamni oshirish kifoya. */
  var ICON_V = '?v=20260819v2';
  /* Texnologiya logolari — nomdan avtomatik topiladi (Devicon).
     Taxalluslar ham bor: 'js' -> javascript, 'k8s' -> kubernetes.
     Logo yuklanmasa (404) — rangli harf plitkasi ko'rsatiladi. */
  var LANG_ICONS = {
    'aiogram': { img: DEVICON + 'aiogram-original.svg', color: '#24A1DE' },
    'aiogram3': { img: DEVICON + 'aiogram-original.svg', color: '#24A1DE' },
    'aiogram 3': { img: DEVICON + 'aiogram-original.svg', color: '#24A1DE' },
    'telegram': { img: DEVICON + 'telegram-original.svg', color: '#24A1DE' },
    'telegram bot': { img: DEVICON + 'aiogram-original.svg', color: '#24A1DE' },
    'python': { img: DEVICON + 'python-original.svg', color: '#3776AB' },
    'py': { img: DEVICON + 'python-original.svg', color: '#3776AB' },
    'javascript': { img: DEVICON + 'javascript-original.svg', color: '#F7DF1E' },
    'js': { img: DEVICON + 'javascript-original.svg', color: '#F7DF1E' },
    'typescript': { img: DEVICON + 'typescript-original.svg', color: '#3178C6' },
    'ts': { img: DEVICON + 'typescript-original.svg', color: '#3178C6' },
    'java': { img: DEVICON + 'java-original.svg', color: '#E76F00' },
    'c++': { img: DEVICON + 'cplusplus-original.svg', color: '#00599C' },
    'cpp': { img: DEVICON + 'cplusplus-original.svg', color: '#00599C' },
    'cplusplus': { img: DEVICON + 'cplusplus-original.svg', color: '#00599C' },
    'c#': { img: DEVICON + 'csharp-original.svg', color: '#68217A' },
    'csharp': { img: DEVICON + 'csharp-original.svg', color: '#68217A' },
    'c tili': { img: DEVICON + 'c-original.svg', color: '#A8B9CC' },
    'c language': { img: DEVICON + 'c-original.svg', color: '#A8B9CC' },
    'go': { img: DEVICON + 'go-original.svg', color: '#00ADD8' },
    'golang': { img: DEVICON + 'go-original.svg', color: '#00ADD8' },
    'rust': { img: DEVICON + 'rust-original.svg', color: '#DEA584' },
    'swift': { img: DEVICON + 'swift-original.svg', color: '#FA7343' },
    'kotlin': { img: DEVICON + 'kotlin-original.svg', color: '#7F52FF' },
    'dart': { img: DEVICON + 'dart-original.svg', color: '#0175C2' },
    'ruby': { img: DEVICON + 'ruby-original.svg', color: '#CC342D' },
    'php': { img: DEVICON + 'php-original.svg', color: '#777BB4' },
    'r tili': { img: DEVICON + 'r-original.svg', color: '#276DC3' },
    'rlang': { img: DEVICON + 'r-original.svg', color: '#276DC3' },
    'scala': { img: DEVICON + 'scala-original.svg', color: '#DC322F' },
    'lua': { img: DEVICON + 'lua-original.svg', color: '#2C2D72' },
    'perl': { img: DEVICON + 'perl-original.svg', color: '#39457E' },
    'matlab': { img: DEVICON + 'matlab-original.svg', color: '#E16737' },
    'haskell': { img: DEVICON + 'haskell-original.svg', color: '#5D4F85' },
    'elixir': { img: DEVICON + 'elixir-original.svg', color: '#4B275F' },
    'erlang': { img: DEVICON + 'erlang-original.svg', color: '#A90533' },
    'clojure': { img: DEVICON + 'clojure-original.svg', color: '#5881D8' },
    'julia': { img: DEVICON + 'julia-original.svg', color: '#9558B2' },
    'objective-c': { img: DEVICON + 'objectivec-original.svg', color: '#438EFF' },
    'objectivec': { img: DEVICON + 'objectivec-original.svg', color: '#438EFF' },
    'solidity': { img: DEVICON + 'solidity-original.svg', color: '#363636' },
    'fortran': { img: DEVICON + 'fortran-original.svg', color: '#734F96' },
    'groovy': { img: DEVICON + 'groovy-original.svg', color: '#4298B8' },
    'ocaml': { img: DEVICON + 'ocaml-original.svg', color: '#EC6813' },
    'crystal': { img: DEVICON + 'crystal-original.svg', color: '#000000' },
    'nix': { img: DEVICON + 'nixos-original.svg', color: '#5277C3' },
    'html': { img: DEVICON + 'html5-original.svg', color: '#E34F26' },
    'html5': { img: DEVICON + 'html5-original.svg', color: '#E34F26' },
    'css': { img: DEVICON + 'css3-original.svg', color: '#1572B6' },
    'css3': { img: DEVICON + 'css3-original.svg', color: '#1572B6' },
    'react': { img: DEVICON + 'react-original.svg', color: '#61DAFB' },
    'reactjs': { img: DEVICON + 'react-original.svg', color: '#61DAFB' },
    'react native': { img: DEVICON + 'react-original.svg', color: '#61DAFB' },
    'vue': { img: DEVICON + 'vuejs-original.svg', color: '#4FC08D' },
    'vuejs': { img: DEVICON + 'vuejs-original.svg', color: '#4FC08D' },
    'vue.js': { img: DEVICON + 'vuejs-original.svg', color: '#4FC08D' },
    'angular': { img: DEVICON + 'angularjs-original.svg', color: '#DD0031' },
    'angularjs': { img: DEVICON + 'angularjs-original.svg', color: '#DD0031' },
    'svelte': { img: DEVICON + 'svelte-original.svg', color: '#FF3E00' },
    'sveltekit': { img: DEVICON + 'svelte-original.svg', color: '#FF3E00' },
    'next': { img: DEVICON + 'nextjs-original.svg', color: '#FFFFFF' },
    'nextjs': { img: DEVICON + 'nextjs-original.svg', color: '#FFFFFF' },
    'next.js': { img: DEVICON + 'nextjs-original.svg', color: '#FFFFFF' },
    'nuxt': { img: DEVICON + 'nuxtjs-original.svg', color: '#00DC82' },
    'nuxtjs': { img: DEVICON + 'nuxtjs-original.svg', color: '#00DC82' },
    'jquery': { img: DEVICON + 'jquery-original.svg', color: '#0769AD' },
    'bootstrap': { img: DEVICON + 'bootstrap-original.svg', color: '#7952B3' },
    'tailwind': { img: DEVICON + 'tailwindcss-original.svg', color: '#06B6D4' },
    'tailwindcss': { img: DEVICON + 'tailwindcss-original.svg', color: '#06B6D4' },
    'sass': { img: DEVICON + 'sass-original.svg', color: '#CC6699' },
    'scss': { img: DEVICON + 'sass-original.svg', color: '#CC6699' },
    'webpack': { img: DEVICON + 'webpack-original.svg', color: '#8DD6F9' },
    'vite': { img: DEVICON + 'vitejs-original.svg', color: '#646CFF' },
    'vitejs': { img: DEVICON + 'vitejs-original.svg', color: '#646CFF' },
    'babel': { img: DEVICON + 'babel-original.svg', color: '#F9DC3E' },
    'redux': { img: DEVICON + 'redux-original.svg', color: '#764ABC' },
    'three.js': { img: DEVICON + 'threejs-original.svg', color: '#FFFFFF' },
    'threejs': { img: DEVICON + 'threejs-original.svg', color: '#FFFFFF' },
    'electron': { img: DEVICON + 'electron-original.svg', color: '#47848F' },
    'node': { img: DEVICON + 'nodejs-original.svg', color: '#539E43' },
    'nodejs': { img: DEVICON + 'nodejs-original.svg', color: '#539E43' },
    'node.js': { img: DEVICON + 'nodejs-original.svg', color: '#539E43' },
    'express': { img: DEVICON + 'express-original.svg', color: '#FFFFFF' },
    'expressjs': { img: DEVICON + 'express-original.svg', color: '#FFFFFF' },
    'nest': { img: DEVICON + 'nestjs-original.svg', color: '#E0234E' },
    'nestjs': { img: DEVICON + 'nestjs-original.svg', color: '#E0234E' },
    'django': { img: DEVICON + 'django-original.svg', color: '#092E20' },
    'flask': { img: DEVICON + 'flask-original.svg', color: '#FFFFFF' },
    'fastapi': { img: DEVICON + 'fastapi-original.svg', color: '#009688' },
    'laravel': { img: DEVICON + 'laravel-original.svg', color: '#FF2D20' },
    'spring': { img: DEVICON + 'spring-original.svg', color: '#6DB33F' },
    'spring boot': { img: DEVICON + 'spring-original.svg', color: '#6DB33F' },
    'rails': { img: DEVICON + 'rails-original.svg', color: '#CC0000' },
    'ruby on rails': { img: DEVICON + 'rails-original.svg', color: '#CC0000' },
    'symfony': { img: DEVICON + 'symfony-original.svg', color: '#FFFFFF' },
    '.net': { img: DEVICON + 'dot-net-original.svg', color: '#512BD4' },
    'dotnet': { img: DEVICON + 'dot-net-original.svg', color: '#512BD4' },
    'asp.net': { img: DEVICON + 'dot-net-original.svg', color: '#512BD4' },
    'graphql': { img: DEVICON + 'graphql-original.svg', color: '#E10098' },
    'socket.io': { img: DEVICON + 'socketio-original.svg', color: '#FFFFFF' },
    'socketio': { img: DEVICON + 'socketio-original.svg', color: '#FFFFFF' },
    'prisma': { img: DEVICON + 'prisma-original.svg', color: '#2D3748' },
    'deno': { img: DEVICON + 'deno-original.svg', color: '#FFFFFF' },
    'bun': { img: DEVICON + 'bun-original.svg', color: '#FBF0DF' },
    'postgres': { img: DEVICON + 'postgresql-original.svg', color: '#4169E1' },
    'postgresql': { img: DEVICON + 'postgresql-original.svg', color: '#4169E1' },
    'psql': { img: DEVICON + 'postgresql-original.svg', color: '#4169E1' },
    'mysql': { img: DEVICON + 'mysql-original.svg', color: '#4479A1' },
    'sqlite': { img: DEVICON + 'sqlite-original.svg', color: '#003B57' },
    'mongo': { img: DEVICON + 'mongodb-original.svg', color: '#47A248' },
    'mongodb': { img: DEVICON + 'mongodb-original.svg', color: '#47A248' },
    'redis': { img: DEVICON + 'redis-original.svg', color: '#DC382D' },
    'mariadb': { img: DEVICON + 'mariadb-original.svg', color: '#003545' },
    'oracle': { img: DEVICON + 'oracle-original.svg', color: '#F80000' },
    'cassandra': { img: DEVICON + 'cassandra-original.svg', color: '#1287B1' },
    'elasticsearch': { img: DEVICON + 'elasticsearch-original.svg', color: '#005571' },
    'elastic': { img: DEVICON + 'elasticsearch-original.svg', color: '#005571' },
    'neo4j': { img: DEVICON + 'neo4j-original.svg', color: '#4581C3' },
    'firebase': { img: DEVICON + 'firebase-original.svg', color: '#FFCA28' },
    'supabase': { img: DEVICON + 'supabase-original.svg', color: '#3ECF8E' },
    'sql server': { img: DEVICON + 'microsoftsqlserver-original.svg', color: '#CC2927' },
    'mssql': { img: DEVICON + 'microsoftsqlserver-original.svg', color: '#CC2927' },
    'docker': { img: DEVICON + 'docker-original.svg', color: '#2496ED' },
    'kubernetes': { img: DEVICON + 'kubernetes-original.svg', color: '#326CE5' },
    'k8s': { img: DEVICON + 'kubernetes-original.svg', color: '#326CE5' },
    'nginx': { img: DEVICON + 'nginx-original.svg', color: '#009639' },
    'apache': { img: DEVICON + 'apache-original.svg', color: '#D22128' },
    'linux': { img: DEVICON + 'linux-original.svg', color: '#FCC624' },
    'ubuntu': { img: DEVICON + 'ubuntu-original.svg', color: '#E95420' },
    'debian': { img: DEVICON + 'debian-original.svg', color: '#A81D33' },
    'bash': { img: DEVICON + 'bash-original.svg', color: '#4EAA25' },
    'shell': { img: DEVICON + 'bash-original.svg', color: '#4EAA25' },
    'git': { img: DEVICON + 'git-original.svg', color: '#F05032' },
    'github': { img: DEVICON + 'github-original.svg', color: '#FFFFFF' },
    'gitlab': { img: DEVICON + 'gitlab-original.svg', color: '#FC6D26' },
    'bitbucket': { img: DEVICON + 'bitbucket-original.svg', color: '#0052CC' },
    'jenkins': { img: DEVICON + 'jenkins-original.svg', color: '#D24939' },
    'ansible': { img: DEVICON + 'ansible-original.svg', color: '#EE0000' },
    'terraform': { img: DEVICON + 'terraform-original.svg', color: '#7B42BC' },
    'vagrant': { img: DEVICON + 'vagrant-original.svg', color: '#1868F2' },
    'aws': { img: DEVICON + 'amazonwebservices-original.svg', color: '#FF9900' },
    'amazon': { img: DEVICON + 'amazonwebservices-original.svg', color: '#FF9900' },
    'azure': { img: DEVICON + 'azure-original.svg', color: '#0078D4' },
    'gcp': { img: DEVICON + 'googlecloud-original.svg', color: '#4285F4' },
    'google cloud': { img: DEVICON + 'googlecloud-original.svg', color: '#4285F4' },
    'heroku': { img: DEVICON + 'heroku-original.svg', color: '#430098' },
    'vercel': { img: DEVICON + 'vercel-original.svg', color: '#FFFFFF' },
    'netlify': { img: DEVICON + 'netlify-original.svg', color: '#00C7B7' },
    'cloudflare': { img: DEVICON + 'cloudflare-original.svg', color: '#F38020' },
    'tensorflow': { img: DEVICON + 'tensorflow-original.svg', color: '#FF6F00' },
    'pytorch': { img: DEVICON + 'pytorch-original.svg', color: '#EE4C2C' },
    'torch': { img: DEVICON + 'pytorch-original.svg', color: '#EE4C2C' },
    'pandas': { img: DEVICON + 'pandas-original.svg', color: '#150458' },
    'numpy': { img: DEVICON + 'numpy-original.svg', color: '#013243' },
    'jupyter': { img: DEVICON + 'jupyter-original.svg', color: '#F37626' },
    'notebook': { img: DEVICON + 'jupyter-original.svg', color: '#F37626' },
    'anaconda': { img: DEVICON + 'anaconda-original.svg', color: '#44A833' },
    'conda': { img: DEVICON + 'anaconda-original.svg', color: '#44A833' },
    'keras': { img: DEVICON + 'keras-original.svg', color: '#D00000' },
    'opencv': { img: DEVICON + 'opencv-original.svg', color: '#5C3EE8' },
    'scikit-learn': { img: DEVICON + 'scikitlearn-original.svg', color: '#F7931E' },
    'sklearn': { img: DEVICON + 'scikitlearn-original.svg', color: '#F7931E' },
    'matplotlib': { img: DEVICON + 'matplotlib-original.svg', color: '#11557C' },
    'flutter': { img: DEVICON + 'flutter-original.svg', color: '#02569B' },
    'android': { img: DEVICON + 'android-original.svg', color: '#3DDC84' },
    'ios': { img: DEVICON + 'apple-original.svg', color: '#FFFFFF' },
    'apple': { img: DEVICON + 'apple-original.svg', color: '#FFFFFF' },
    'macos': { img: DEVICON + 'apple-original.svg', color: '#FFFFFF' },
    'ionic': { img: DEVICON + 'ionic-original.svg', color: '#3880FF' },
    'xamarin': { img: DEVICON + 'xamarin-original.svg', color: '#3498DB' },
    'unity': { img: DEVICON + 'unity-original.svg', color: '#FFFFFF' },
    'vs code': { img: DEVICON + 'vscode-original.svg', color: '#007ACC' },
    'vscode': { img: DEVICON + 'vscode-original.svg', color: '#007ACC' },
    'visual studio code': { img: DEVICON + 'vscode-original.svg', color: '#007ACC' },
    'intellij': { img: DEVICON + 'intellij-original.svg', color: '#000000' },
    'idea': { img: DEVICON + 'intellij-original.svg', color: '#000000' },
    'pycharm': { img: DEVICON + 'pycharm-original.svg', color: '#21D789' },
    'webstorm': { img: DEVICON + 'webstorm-original.svg', color: '#00CDD7' },
    'vim': { img: DEVICON + 'vim-original.svg', color: '#019733' },
    'neovim': { img: DEVICON + 'neovim-original.svg', color: '#57A143' },
    'nvim': { img: DEVICON + 'neovim-original.svg', color: '#57A143' },
    'figma': { img: DEVICON + 'figma-original.svg', color: '#F24E1E' },
    'photoshop': { img: DEVICON + 'photoshop-original.svg', color: '#31A8FF' },
    'illustrator': { img: DEVICON + 'illustrator-original.svg', color: '#FF9A00' },
    'blender': { img: DEVICON + 'blender-original.svg', color: '#E87D0D' },
    'postman': { img: DEVICON + 'postman-original.svg', color: '#FF6C37' },
    'jira': { img: DEVICON + 'jira-original.svg', color: '#0052CC' },
    'slack': { img: DEVICON + 'slack-original.svg', color: '#4A154B' },
    'trello': { img: DEVICON + 'trello-original.svg', color: '#0052CC' },
    'npm': { img: DEVICON + 'npm-original.svg', color: '#CB3837' },
    'yarn': { img: DEVICON + 'yarn-original.svg', color: '#2C8EBB' },
    'markdown': { img: DEVICON + 'markdown-original.svg', color: '#FFFFFF' },
    'md': { img: DEVICON + 'markdown-original.svg', color: '#FFFFFF' },
    'jest': { img: DEVICON + 'jest-original.svg', color: '#C21325' },
    'mocha': { img: DEVICON + 'mocha-original.svg', color: '#8D6748' },
    'selenium': { img: DEVICON + 'selenium-original.svg', color: '#43B02A' },
    'windows': { img: DEVICON + 'windows11-original.svg', color: '#0078D4' },
  };

  /* Rang palitrasi (ikonka topilmasa, harf + rang) */
  var PALETTE = ['#3B82F6','#EF4444','#10B981','#F59E0B','#8B5CF6','#EC4899','#06B6D4','#F97316','#14B8A6','#6366F1'];
  function hashColor(s) { var h = 0; for(var i=0;i<s.length;i++) h = s.charCodeAt(i) + ((h<<5)-h); return PALETTE[Math.abs(h)%PALETTE.length]; }

  function findIcon(name) {
    var low = (name || '').toLowerCase().trim();
    if (!low) return null;
    if (LANG_ICONS[low]) return LANG_ICONS[low];

    /* Qisman moslik. MUHIM: kalitlar UZUNLIGI bo'yicha kamayish tartibida
       tekshiriladi va so'z chegarasi talab qilinadi — aks holda qisqa
       kalitlar ('c', 'r', 'go') deyarli har qanday nomga mos kelib,
       noto'g'ri logo chiqarardi (masalan "Scala" -> 'c'). */
    var keys = Object.keys(LANG_ICONS).sort(function (a, b) { return b.length - a.length; });
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var re = new RegExp('(^|[^a-z0-9+#.])' + k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '($|[^a-z0-9+#.])');
      if (re.test(low)) return LANG_ICONS[k];
    }
    return null;
  }


  function iconHtml(name, size) {
    var s = size || 28;
    var fs = Math.round(s * 0.5);
    var rad = Math.max(6, Math.round(s * 0.28));
    var ic = findIcon(name);
    var harf = App.esc((name || '?').charAt(0).toUpperCase());
    if (ic) {
      return '<img src="' + ic.img + ICON_V + '" style="width:' + s + 'px;height:' + s + 'px" onerror="this.style.display=\'none\';this.nextSibling.style.display=\'flex\'">' +
        '<span style="display:none;width:' + s + 'px;height:' + s + 'px;border-radius:' + rad + 'px;background:' + ic.color + ';color:#fff;font-weight:700;font-size:' + fs + 'px;align-items:center;justify-content:center">' + harf + '</span>';
    }
    var c = hashColor(name || '');
    return '<span style="width:' + s + 'px;height:' + s + 'px;border-radius:' + rad + 'px;background:' + c + ';color:#fff;font-weight:700;font-size:' + fs + 'px;display:inline-flex;align-items:center;justify-content:center">' + harf + '</span>';
  }

  /* Logo aniqlash boshqa modullarga ham kerak (masalan Testlar bo'limi —
     fan/baza nomidan logo). Bitta nusxada qoladi: ~190 talik LANG_ICONS
     jadvali faqat shu yerda. */
  window.TechIcon = { find: findIcon, html: iconHtml, color: hashColor };

  /* ---------- Tillar sahifasi ---------- */
  App.view('languages', {
    nav: 'languages',
    render: function (page) {
      var customLangs = '';
      try {
        var arr = JSON.parse(localStorage.getItem('custom_langs') || '[]');
        customLangs = arr.map(function(l) {
          return customLangCard(l);
        }).join('');
      } catch(e){}

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<div style="display:flex;align-items:center;gap:9px;flex:1;min-width:0">' +
        '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:28px;height:28px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
        '<h1>Learn</h1></div>' +
        '<button class="icon-btn ghost" data-act="langAdd" style="margin-left:auto"><span data-icon="plus" data-icon-size="20"></span></button></div>' +
        '<div class="chat-list">' +
        langCard('english', 'assets/icons/tech/flag-gb.png', 'Ingliz tili', 'Listening, Reading, Grammar, Vocabulary') +
        langCard('russian', 'assets/icons/tech/flag-ru.png', 'Русский язык', 'Грамматика, Словарь, Чтение, Аудирование') +
        langCard('grammar', 'assets/icons/tech/vscode-original.svg', 'Dasturlash', 'Mavzular, testlar va o\'yinlar', { lang: 'coding' }) +
        customLangs +
        '</div>';
      App.icons(page);
    }
  });

  /* Built-in tillar uchun karta (data-icon yoki URL rasm bilan) */
  /* Learn hub kartalari ham ko'nikma ro'yxati bilan BIR XIL Telegram-chat
     uslubida (`.chat-*`) — chapda dumaloq rasm, o'ngda nom + izoh. */
  function langCard(v, ic, n, s, params) {
    // Rasmmi yoki chiziqli ikonami — KENGAYTMA bo'yicha aniqlanadi.
    // Ilgari 'http' bilan boshlanishiga qaralardi; logolar serverga
    // ko'chirilgach ular lokal yo'lga aylandi va bu tekshiruv buzilardi.
    var iconHtml = /\.(svg|png|jpe?g|webp)$/i.test(ic)
      ? '<img src="' + ic + ICON_V + '" alt="">'
      : '<span class="chat-av-ic" data-icon="' + ic + '" data-icon-size="22"></span>';

    return '<button class="chat-row" data-act="go" data-arg=\'' + App.arg({ v: v, p: params || {} }) + '\'>' +
      '<span class="chat-av">' + iconHtml + '</span>' +
      '<span class="chat-main">' +
        '<span class="chat-title">' + App.esc(n) + '</span>' +
        '<span class="chat-sub">' + App.esc(s) + '</span>' +
      '</span>' +
      '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>';
  }

  /* Custom til — xuddi shu chat uslubi, lekin yonida boshqarish tugmasi bor.
     Tugma qatorning ICHIDA bo'lolmaydi (button ichida button), shuning uchun
     ikkalasi `.chat-item` o'ramida yonma-yon turadi. */
  /* Custom til — xuddi asosiy tillar kabi yagona chat uslubida (`.chat-row` + `.chat-arrow`) */
  function customLangCard(l) {
    return '<button class="chat-row" data-act="go" data-arg=\'' + App.arg({ v: 'grammar', p: { lang: l.id } }) + '\'>' +
      '<span class="chat-av">' + iconHtml(l.name) + '</span>' +
      '<span class="chat-main">' +
        '<span class="chat-title">' + App.esc(l.name) + '</span>' +
        '<span class="chat-sub">Mavzular, testlar va o\'yinlar</span>' +
      '</span>' +
      '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span></button>';
  }

  /* ---------- CRUD ---------- */
  /* CREATE */
  App.actions.langAdd = function () {
    App.prompt({ title: 'Yangi til', label: 'Til nomi (Masalan: Python, C++, HTML)', ok: 'Qo\'shish' }, function (name) {
      if (!name || !name.trim()) return;
      name = name.trim();
      var id = 'lang_' + Date.now();
      try {
        var arr = JSON.parse(localStorage.getItem('custom_langs') || '[]');
        // Dublikatni tekshirish
        var exists = arr.some(function(x) { return x.name.toLowerCase() === name.toLowerCase(); });
        if (exists) { App.toast('⚠️ "' + name + '" allaqachon mavjud'); return; }
        arr.push({ id: id, name: name });
        localStorage.setItem('custom_langs', JSON.stringify(arr));
        App.reload();
      } catch(e) {}
    });
  };

  /* MANAGE (sheet: Rename + Delete) */
  App.actions.langManage = function (a) {
    var html =
      '<button class="list-row" data-act="langRename" data-arg=\'' + App.arg(a) + '\'>' +
      '<span class="li-ic" data-icon="edit" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title">Nomini o\'zgartirish</div></div></button>' +
      '<button class="list-row" data-act="langDelete" data-arg=\'' + App.arg(a) + '\' style="color:var(--danger)">' +
      '<span class="li-ic" style="background:var(--danger-soft);color:var(--danger)" data-icon="trash" data-icon-size="15"></span>' +
      '<div class="li-main"><div class="li-title" style="color:var(--danger)">O\'chirish</div></div></button>';
    App.sheet(html, { title: a.name });
  };

  /* UPDATE (Rename) */
  App.actions.langRename = function (a) {
    App.closeSheet();
    App.prompt({ title: 'Nomini o\'zgartirish', label: 'Yangi nom', value: a.name, ok: 'Saqlash' }, function (name) {
      if (!name || !name.trim()) return;
      name = name.trim();
      try {
        var arr = JSON.parse(localStorage.getItem('custom_langs') || '[]');
        var exists = arr.some(function(x) { return x.id !== a.id && x.name.toLowerCase() === name.toLowerCase(); });
        if (exists) { App.toast('⚠️ "' + name + '" allaqachon mavjud'); return; }
        arr = arr.map(function(x) {
          if (x.id === a.id) x.name = name;
          return x;
        });
        localStorage.setItem('custom_langs', JSON.stringify(arr));
        App.reload();
      } catch(e){}
    });
  };

  /* DELETE */
  App.actions.langDelete = function (a) {
    App.closeSheet();
    App.confirm('"' + a.name + '" va uning barcha mavzulari o\'chiriladi.', function () {
      try {
        var arr = JSON.parse(localStorage.getItem('custom_langs') || '[]');
        arr = arr.filter(function(x) { return x.id !== a.id; });
        localStorage.setItem('custom_langs', JSON.stringify(arr));
      } catch(e){}
      // Serverdan ham mavzularni o'chirish (agar API mavjud bo'lsa)
      try {
        App.call('delete_lang_topics', { lang: a.id }).catch(function(){});
      } catch(e){}
      App.reload();
    }, { danger: true, yes: 'O\'chirish' });
  };

  /* ---------- Yordamchi funksiyalar ---------- */
  function header(title, back) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      (back ? '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: back }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' : '') +
      '<h1>' + App.esc(title) + '</h1></div>';
  }

  /* Ko'nikma qatorlari Telegram chat ro'yxati uslubida: chapda dumaloq
     rasm, o'ngda nom + qisqa izoh. Rasmlar `assets/img/skills/` da
     LOKAL turadi (oflaynda ham ko'rinsin va tashqi xostga bog'lanib
     qolmasin) — `sk.img` fayl nomining o'zagi. */
  function skillList(page, title, back, skills) {
    page.innerHTML = header(title, back) +
      '<div class="chat-list">' + skills.map(function (sk) {
        var soon = !sk.ready;
        var act = soon
          ? 'data-act="skillSoon" data-arg=\'' + App.arg({ n: sk.n }) + '\''
          : 'data-act="go" data-arg=\'' + App.arg({ v: sk.v, p: sk.p || {} }) + '\'';
        return '<button class="chat-row" ' + act + '>' +
          '<span class="chat-av">' +
            (sk.img
              ? '<img src="assets/img/skills/' + sk.img + '.jpg" alt="" loading="lazy">'
              : '<span class="chat-av-ic" data-icon="' + sk.ic + '" data-icon-size="22"></span>') +
          '</span>' +
          '<span class="chat-main">' +
            '<span class="chat-title">' + App.esc(sk.n) + '</span>' +
            '<span class="chat-sub">' + App.esc(soon ? 'Tez orada' : (sk.d || '')) + '</span>' +
          '</span>' +
          (soon
            ? '<span class="chip-btn" style="pointer-events:none;padding:4px 10px;font-size:11px">Tez orada</span>'
            : '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16"></span>') +
          '</button>';
      }).join('') + '</div>';
    App.icons(page);
  }

  App.actions.skillSoon = function (a) {
    App.toast('\u201c' + a.n + '\u201d tez orada tayyor bo\'ladi');
  };

  /* Ilgari "Tez orada" bo'lgan bo'limlar endi MATERIALLAR kutubxonasi
     (library.js): ichma-ich papka + .md yuklash. Test/o'yin yo'q \u2014 bu
     bo'limlarga foydalanuvchi materiallarini o'zi taxlab yuklaydi. */
  App.view('english', {
    nav: 'languages',
    render: function (page) {
      skillList(page, 'Ingliz tili', 'languages', [
        { n: 'Listening', ic: 'headphones', img: 'listening', d: 'Eshitib tushunish materiallari', ready: true, v: 'library', p: { sec: 'en_listening' } },
        { n: 'Reading', ic: 'book', img: 'reading', d: 'Matn o\'qish — so\'z va gap tarjimasi bilan', ready: true, v: 'library', p: { sec: 'en_reading' } },
        { n: 'Grammar', ic: 'edit', img: 'grammar', d: 'Qoidalar, testlar va o\'yinlar', ready: true, v: 'grammar', p: { lang: 'english' } },
        { n: 'Vocabulary', ic: 'list', img: 'vocabulary', d: 'Lug\'at, flashcard va takrorlash', ready: true, v: 'vocab', p: { lang: 'english' } },
        { n: 'Writing', ic: 'edit', img: 'writing', d: 'Yozish namunalari va mashqlari', ready: true, v: 'library', p: { sec: 'en_writing' } },
        { n: 'Speaking', ic: 'mic', img: 'speaking', d: 'Gapirish uchun material va iboralar', ready: true, v: 'library', p: { sec: 'en_speaking' } },
        { n: 'Mashqlar', ic: 'play', img: 'practice', d: 'Raqam, harf, ism eshitib yozish', ready: true, v: 'practice', p: { lang: 'english' } }
      ]);
    }
  });

  App.view('russian', {
    nav: 'languages',
    render: function (page) {
      /* Rus tili bo'limida NOMLAR VA IZOHLAR ham ruscha (foydalanuvchi so'rovi) \u2014
         til muhitiga to'liq kirish uchun. Ingliz bo'limi o'zbekcha izohda qoladi. */
      skillList(page, '\u0420\u0443\u0441\u0441\u043a\u0438\u0439 \u044f\u0437\u044b\u043a', 'languages', [
        { n: '\u0413\u0440\u0430\u043c\u043c\u0430\u0442\u0438\u043a\u0430', ic: 'edit', img: 'grammar', d: '\u041f\u0440\u0430\u0432\u0438\u043b\u0430, \u0442\u0435\u0441\u0442\u044b \u0438 \u0438\u0433\u0440\u044b', ready: true, v: 'grammar', p: { lang: 'russian' } },
        { n: '\u0421\u043b\u043e\u0432\u0430\u0440\u044c', ic: 'list', img: 'vocabulary', d: '\u0421\u043b\u043e\u0432\u0430, \u043a\u0430\u0440\u0442\u043e\u0447\u043a\u0438 \u0438 \u043f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u0435', ready: true, v: 'vocab', p: { lang: 'russian' } },
        { n: '\u0427\u0442\u0435\u043d\u0438\u0435', ic: 'book', img: 'reading', d: '\u0422\u0435\u043a\u0441\u0442 \u0441 \u043f\u0435\u0440\u0435\u0432\u043e\u0434\u043e\u043c \u0441\u043b\u043e\u0432 \u0438 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0439', ready: true, v: 'library', p: { sec: 'ru_reading' } },
        { n: '\u0410\u0443\u0434\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435', ic: 'headphones', img: 'listening', d: '\u041c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u043d\u0430 \u0441\u043b\u0443\u0445', ready: true, v: 'library', p: { sec: 'ru_listening' } },
        { n: '\u0413\u043e\u0432\u043e\u0440\u0435\u043d\u0438\u0435', ic: 'mic', img: 'speaking', d: '\u041c\u0430\u0442\u0435\u0440\u0438\u0430\u043b\u044b \u0438 \u0444\u0440\u0430\u0437\u044b \u0434\u043b\u044f \u0440\u0435\u0447\u0438', ready: true, v: 'library', p: { sec: 'ru_speaking' } },
        { n: '\u041f\u0438\u0441\u044c\u043c\u043e', ic: 'edit', img: 'writing', d: '\u041e\u0431\u0440\u0430\u0437\u0446\u044b \u0438 \u0443\u043f\u0440\u0430\u0436\u043d\u0435\u043d\u0438\u044f \u043f\u043e \u043f\u0438\u0441\u044c\u043c\u0443', ready: true, v: 'library', p: { sec: 'ru_writing' } },
        { n: '\u0428\u044d\u0434\u043e\u0443\u0438\u043d\u0433', ic: 'refresh', img: 'shadowing', d: '\u041f\u043e\u0432\u0442\u043e\u0440\u0435\u043d\u0438\u0435 \u0432\u0441\u043b\u0435\u0434 \u0437\u0430 \u0434\u0438\u043a\u0442\u043e\u0440\u043e\u043c', ready: true, v: 'library', p: { sec: 'ru_shadowing' } },
        { n: '\u0423\u043f\u0440\u0430\u0436\u043d\u0435\u043d\u0438\u044f', ic: 'play', img: 'practice', d: '\u0427\u0438\u0441\u043b\u0430, \u0431\u0443\u043a\u0432\u044b \u0438 \u0438\u043c\u0435\u043d\u0430 \u043d\u0430 \u0441\u043b\u0443\u0445', ready: true, v: 'practice', p: { lang: 'russian' } }
      ]);
    }
  });
})();
