/* Coding — texnologiyalar ma'lumotnomasi: nima ekani, vazifasi, qayerda ishlatiladi.
   Bu O'RGANISH bo'limi emas (u Tillar > Dasturlash'da) — bu qisqa ma'lumotnoma. */
(function () {
  'use strict';

  var TECH = [
    {
      g: 'Dasturlash tillari', ic: 'code', c: 'var(--accent)', items: [
        { n: 'Python', r: 'Umumiy maqsadli, o\'qishga oson til',
          d: 'Sintaksisi sodda bo\'lgani uchun tez yoziladi. Sun\'iy intellekt, ma\'lumot tahlili, server (backend) va avtomatlashtirish uchun eng ko\'p ishlatiladigan tillardan.',
          u: 'AI/ML, backend, skriptlar, ma\'lumot tahlili',
          p: 'O\'rganish tez, kutubxonalar bazasi ulkan, deyarli har qanday sohada ishlatiladi.',
          k: 'Boshqa kompilyatsiya qilinadigan tillardan (C++, Go) sekinroq ishlaydi.' },
        { n: 'JavaScript', r: 'Brauzerda ishlaydigan yagona til',
          d: 'Veb-sahifani "jonli" qiladi: tugma bosilishi, ma\'lumot yuklash, animatsiya. Node.js orqali serverda ham ishlaydi.',
          u: 'Frontend, backend (Node.js), mobil',
          p: 'Har bir brauzerda ishlaydi, bitta til bilan frontend va backend ham yoziladi.',
          k: 'Tur nazorati yo\'q (kichik xato ishlab turib topiladi) — shu sabab TypeScript ko\'proq tanlanadi.' },
        { n: 'TypeScript', r: 'Tur tekshiruvi qo\'shilgan JavaScript',
          d: 'JavaScript ustiga "bu o\'zgaruvchi son, bu matn" degan qoidalar qo\'shadi. Katta loyihada xatoni yozish paytidayoq ko\'rsatadi.',
          u: 'Katta frontend/backend loyihalar',
          p: 'Xatoni ishga tushirishdan oldin topadi, katta jamoada ishlashni osonlashtiradi.',
          k: 'Qo\'shimcha sozlash (compile) bosqichi kerak, kichik loyihada ortiqcha bo\'lishi mumkin.' },
        { n: 'C++', r: 'Tezlik talab qiladigan tizim tili',
          d: 'Xotira bilan bevosita ishlaydi, shuning uchun juda tez. Almashtirish evaziga — yozish murakkabroq.',
          u: 'O\'yin dvigatellari, drayverlar, olimpiada, embedded',
          p: 'Juda yuqori tezlik, xotirani to\'liq nazorat qilish imkoniyati.',
          k: 'Xotira xatolari qo\'lda boshqariladi — diqqatsizlik dastur qulashiga olib keladi.' },
        { n: 'Java', r: 'Korporativ tizimlar tili',
          d: '"Bir marta yoz, hamma joyda ishlaydi" tamoyili. Yirik banklar va korxonalarda keng tarqalgan.',
          u: 'Korporativ backend, Android',
          p: 'Barqaror, katta va uzoq umr ko\'radigan tizimlar uchun ishonchli.',
          k: 'Kod ko\'p yoziladi (verbose), Python/Go\'ga nisbatan sekinroq ishga tushadi.' },
        { n: 'C#', r: 'Microsoft ekotizimi tili',
          d: '.NET platformasi uchun asosiy til. Unity o\'yin dvigatelida ham ishlatiladi.',
          u: 'Windows ilovalar, o\'yinlar (Unity), backend',
          p: '.NET va Unity bilan chuqur integratsiya, zamonaviy va tartibli sintaksis.',
          k: 'Tarixan Windows\'ga bog\'liq bo\'lgan — hozir kross-platforma bo\'lsada, ekotizim baribir Microsoft atrofida.' },
        { n: 'Go', r: 'Server uchun sodda va tez til',
          d: 'Google yaratgan. Ko\'p vazifani bir vaqtda bajarish (concurrency) juda qulay qilingan.',
          u: 'Mikroservislar, tarmoq xizmatlari, DevOps vositalari',
          p: 'Tez ishga tushadi, sodda sintaksis, ko\'p so\'rovni bir vaqtda qulay boshqaradi.',
          k: 'Tillar orasida kam abstraksiya (masalan generics kech qo\'shildi) — ba\'zi kod takrorlanadi.' },
        { n: 'Rust', r: 'Xavfsiz va tez tizim tili',
          d: 'C++ darajasida tez, lekin xotira xatolarini kompilyatsiya paytidayoq to\'sadi.',
          u: 'Tizim dasturlari, brauzer dvigatellari, WebAssembly',
          p: 'C++ tezligi, lekin xotira xatolari deyarli mumkin emas.',
          k: 'O\'rganish qiyin — "borrow checker" qoidalariga o\'rganish vaqt oladi.' },
        { n: 'PHP', r: 'Veb-server tili',
          d: 'Vebning katta qismi shu tilda yozilgan. WordPress, Laravel shu tilda.',
          u: 'Veb-saytlar, CMS',
          p: 'Deyarli har qanday hostingda ishlaydi, veb uchun maxsus mo\'ljallangan.',
          k: 'Eski kod bazalarida tartibsizlik ko\'p uchraydi — zamonaviy PHP (Laravel) buni tuzatgan.' },
        { n: 'Kotlin', r: 'Android uchun zamonaviy til',
          d: 'Java o\'rnini bosdi — qisqaroq va xavfsizroq yoziladi.',
          u: 'Android ilovalar, backend',
          p: 'Java bilan 100% mos, lekin ancha qisqa va null xatolaridan himoyalangan.',
          k: 'Java\'ga nisbatan hamjamiyat va material kamroq, ba\'zan sekinroq kompilyatsiya bo\'ladi.' },
        { n: 'Swift', r: 'Apple qurilmalari tili',
          d: 'iPhone, iPad, Mac ilovalarini yozish uchun Apple yaratgan til.',
          u: 'iOS/macOS ilovalar',
          p: 'Tez, xavfsiz, Apple platformalari bilan chuqur integratsiya.',
          k: 'Faqat Apple ekotizimida — Windows/Linux uchun ilova yoza olmaysiz.' },
        { n: 'SQL', r: 'Ma\'lumotlar bazasi so\'rov tili',
          d: 'Dasturlash tili emas, so\'rov tili: bazadan ma\'lumot olish, qo\'shish, o\'zgartirish uchun.',
          u: 'Barcha relatsion bazalar',
          p: 'Deyarli barcha relatsion bazalarda bir xil ishlaydi, murakkab so\'rovlarni ixcham yozish mumkin.',
          k: 'Katta hajmli/tez o\'zgaruvchan ma\'lumot uchun har doim ham qulay emas (NoSQL shu sabab kerak bo\'ladi).' }
      ]
    },
    {
      g: 'Frontend (sayt tashqi ko\'rinishi)', ic: 'globe', c: 'var(--purple)', items: [
        { n: 'HTML', r: 'Sahifaning skeleti',
          d: 'Sahifada nima borligini bildiradi: sarlavha, matn, rasm, tugma. Dasturlash tili emas — belgilash tili.',
          u: 'Har qanday veb-sahifa',
          p: 'Juda sodda, har bir brauzer tushunadi, o\'rganish shart emas darajada oson.',
          k: 'Yolg\'iz o\'zi statik — hech qanday "mantiq" yoki interaktivlik bera olmaydi.' },
        { n: 'CSS', r: 'Sahifaning ko\'rinishi',
          d: 'Rang, o\'lcham, joylashuv, animatsiya — hammasi shu yerda. Turli ekranlarga moslash (responsive) ham CSS ishi.',
          u: 'Dizayn, moslashuvchan sahifa',
          p: 'Dizaynni kod va ko\'rinishdan ajratadi, animatsiyalarni JS\'siz yaratish mumkin.',
          k: 'Katta loyihada tartibga solish qiyinlashadi — shu uchun Tailwind kabi vositalar paydo bo\'lgan.' },
        { n: 'React', r: 'Interfeys qurish kutubxonasi',
          d: 'Sahifani mustaqil "komponent"larga bo\'lib yozish imkonini beradi. Eng keng tarqalgan frontend vositasi.',
          u: 'Murakkab veb-ilovalar',
          p: 'Katta hamjamiyat, ko\'p tayyor kutubxona, ish o\'rinlarida eng ko\'p so\'raladi.',
          k: 'Faqat interfeys qatlami — routing, holat boshqaruvi uchun qo\'shimcha vositalar kerak bo\'ladi.' },
        { n: 'Vue', r: 'React\'ga muqobil, o\'rganish osonroq',
          d: 'React bilan bir xil vazifani bajaradi, lekin kirish darajasi pastroq.',
          u: 'Veb-ilovalar',
          p: 'Hujjatlari tushunarli, kichik loyihaga tez kirish mumkin.',
          k: 'Ish e\'lonlarida React\'dan kamroq so\'raladi, ekotizimi biroz kichikroq.' },
        { n: 'Next.js', r: 'React ustiga qurilgan to\'liq karkas',
          d: 'Sahifani serverda tayyorlash (SSR), marshrutlash, optimizatsiya — tayyor holda keladi. SEO uchun qulay.',
          u: 'Ishlab chiqarishga tayyor saytlar',
          p: 'SEO va tezlik uchun eng yaxshi tanlovlardan, deploy qilish (Vercel) juda oson.',
          k: 'React\'ni bilishni talab qiladi, sozlamalari ba\'zan murakkablashadi.' },
        { n: 'Tailwind CSS', r: 'Tayyor CSS sinflari to\'plami',
          d: 'Alohida CSS fayl yozish o\'rniga HTML ichida `p-4 text-lg` kabi sinflar bilan uslub beriladi.',
          u: 'Tez dizayn qilish',
          p: 'Juda tez yoziladi, alohida CSS fayl bilan "nom o\'ylash" muammosi yo\'q.',
          k: 'HTML ichida sinflar ko\'payib, o\'qish qiyinlashishi mumkin.' },
        { n: 'Vite', r: 'Loyihani yig\'uvchi tezkor vosita',
          d: 'Yozgan kodingizni brauzer tushunadigan holga keltiradi va o\'zgarishni bir zumda ko\'rsatadi.',
          u: 'Frontend loyihalar',
          p: 'Ishga tushishi va qayta yuklanishi (hot reload) juda tez.',
          k: 'Eski brauzerlar/loyihalar uchun ba\'zi plagin moslashuvi kerak bo\'lishi mumkin.' }
      ]
    },
    {
      g: 'Backend (server tomoni)', ic: 'file', c: 'var(--teal)', items: [
        { n: 'Node.js', r: 'JavaScript\'ni serverda ishlatish muhiti',
          d: 'Brauzerdan tashqarida JS kodini ishga tushiradi — shu tufayli bitta tilda ham frontend, ham backend yoziladi.',
          u: 'API, real-time xizmatlar',
          p: 'Frontend bilan bitta til, ko\'p so\'rovni bir vaqtda yaxshi ushlaydi (real-time uchun ideal).',
          k: 'Og\'ir hisob-kitob (CPU-intensive) vazifalarda Go/Java\'dan orqada qoladi.' },
        { n: 'Express', r: 'Node.js uchun sodda karkas',
          d: 'Server yo\'llarini (`/api/users`) belgilash va so\'rovlarga javob berishni osonlashtiradi.',
          u: 'REST API',
          p: 'Minimalist, o\'rganish tez, moslashuvchanligi yuqori.',
          k: 'Ko\'p narsa (struktura, validatsiya) qo\'lda qo\'shiladi — Django/Laravel kabi "hammasi tayyor" emas.' },
        { n: 'FastAPI', r: 'Python uchun tezkor API karkasi',
          d: 'Juda tez, avtomatik hujjat yaratadi va kiruvchi ma\'lumotni o\'zi tekshiradi. **Shu sayt shunda yozilgan.**',
          u: 'API, mikroservislar',
          p: 'Avtomatik Swagger hujjat, ma\'lumot validatsiyasi o\'zi ishlaydi, Python\'ning eng tezkorlaridan.',
          k: 'Django\'ga nisbatan yosh — admin panel kabi tayyor qismlar yo\'q, o\'zingiz qurasiz.' },
        { n: 'Django', r: 'Python uchun "hammasi ichida" karkas',
          d: 'Admin panel, autentifikatsiya, baza bilan ishlash — hammasi tayyor keladi.',
          u: 'Yirik veb-loyihalar',
          p: 'Tayyor admin panel va autentifikatsiya — ko\'p narsani noldan yozish shart emas.',
          k: 'Katta va "og\'ir" — kichik API uchun ortiqcha bo\'lishi mumkin.' },
        { n: 'Laravel', r: 'PHP uchun zamonaviy karkas',
          d: 'PHP\'da tartibli va o\'qiladigan kod yozishga imkon beradi.',
          u: 'Veb-ilovalar',
          p: 'Hujjatlari juda yaxshi, PHP hostinglarida ishga tushirish oson.',
          k: 'Node.js/Go\'ga nisbatan sekinroq, katta yukni ko\'tarish uchun optimallashtirish kerak.' },
        { n: 'Spring Boot', r: 'Java uchun asosiy karkas',
          d: 'Korporativ darajadagi xizmatlarni tez yig\'ish uchun.',
          u: 'Korporativ backend',
          p: 'Katta korxona tizimlarida sinovdan o\'tgan, juda barqaror.',
          k: 'Sozlash (konfiguratsiya) ko\'p, kichik loyiha uchun og\'ir tuyuladi.' }
      ]
    },
    {
      g: 'Ma\'lumotlar bazasi', ic: 'archive', c: 'var(--warn)', items: [
        { n: 'PostgreSQL', r: 'Kuchli relatsion baza',
          d: 'Ma\'lumotni jadvallarda saqlaydi, murakkab so\'rovlarni bajaradi, ishonchli. **Shu sayt shundan foydalanadi.**',
          u: 'Deyarli har qanday loyiha',
          p: 'Murakkab so\'rovlarda kuchli, ma\'lumot yaxlitligini qattiq nazorat qiladi, bepul.',
          k: 'MySQL\'ga nisbatan sozlash biroz ko\'proq bilim talab qiladi.' },
        { n: 'MySQL', r: 'Eng keng tarqalgan relatsion baza',
          d: 'PostgreSQL bilan o\'xshash. Veb-hostinglarda ko\'proq uchraydi.',
          u: 'Veb-saytlar, CMS',
          p: 'Deyarli har qanday hostingda tayyor turadi, o\'rganish materiali juda ko\'p.',
          k: 'Ba\'zi murakkab so\'rov turlari va standartlarga rioya qilish PostgreSQL\'dan zaifroq.' },
        { n: 'SQLite', r: 'Bitta fayldagi kichik baza',
          d: 'Server talab qilmaydi — butun baza bitta faylda. Telefon ilovalari va kichik loyihalar uchun ideal.',
          u: 'Mobil ilovalar, prototiplar',
          p: 'O\'rnatish shart emas, bitta faylni ko\'chirish — bazani ko\'chirish demakdir.',
          k: 'Ko\'p foydalanuvchi bir vaqtda yozganda (concurrent write) cheklangan.' },
        { n: 'MongoDB', r: 'Hujjatli (NoSQL) baza',
          d: 'Jadval emas, JSON ko\'rinishidagi hujjatlarni saqlaydi. Tuzilma tez-tez o\'zgaradigan ma\'lumot uchun qulay.',
          u: 'Tez o\'zgaruvchan ma\'lumot',
          p: 'Tuzilmasi moslashuvchan — schema oldindan qat\'iy belgilanmaydi.',
          k: 'Jadvallar orasidagi bog\'liqlik (relation/JOIN) relatsion bazadagidek qulay emas.' },
        { n: 'Redis', r: 'Xotiradagi tezkor ombor',
          d: 'Ma\'lumotni diskda emas, operativ xotirada saqlaydi — shuning uchun juda tez. Kesh va navbat uchun.',
          u: 'Kesh, sessiya, navbat',
          p: 'Millisoniyalarda javob beradi, kesh/navbat vazifalari uchun sanoat standarti.',
          k: 'Xotira (RAM) chegaralangan — asosiy baza sifatida katta hajmli ma\'lumot uchun mos emas.' }
      ]
    },
    {
      g: 'Mobil', ic: 'image', c: 'var(--coral)', items: [
        { n: 'Flutter', r: 'Bitta koddan iOS va Android',
          d: 'Google vositasi, Dart tilida yoziladi. Interfeysni o\'zi chizadi, shuning uchun ikkala platformada bir xil ko\'rinadi.',
          u: 'Kross-platforma ilovalar',
          p: 'Bitta koddan ikkala platforma, ko\'rinishi barcha qurilmada bir xil.',
          k: 'Dart tilini alohida o\'rganish kerak, ilova hajmi native\'dan kattaroq bo\'ladi.' },
        { n: 'React Native', r: 'React bilan mobil ilova',
          d: 'JavaScript/React bilingan bo\'lsangiz, mobil ilovani ham shu bilim bilan yozasiz.',
          u: 'Kross-platforma ilovalar',
          p: 'React bilganlar uchun kirish tez, katta hamjamiyat.',
          k: 'Murakkab animatsiya/native funksiyalarda ba\'zan native kodga tushish kerak bo\'ladi.' },
        { n: 'PWA', r: 'Sayt — ilova ko\'rinishida',
          d: 'Oddiy veb-sayt telefon bosh ekraniga o\'rnatiladi va internetsiz ham ishlaydi. **Shu sayt PWA.**',
          u: 'Do\'konsiz tarqatiladigan ilovalar',
          p: 'Do\'kon (Play Market) talab qilmaydi, bitta kod — sayt ham, ilova ham.',
          k: 'iOS\'da push-bildirishnoma va ba\'zi native imkoniyatlar cheklangan.' }
      ]
    },
    {
      g: 'Infratuzilma va vositalar', ic: 'settings', c: 'var(--success)', items: [
        { n: 'Git', r: 'Kod versiyalarini boshqarish',
          d: 'Har bir o\'zgarishni saqlaydi — istalgan vaqtda orqaga qaytish yoki jamoada birga ishlash mumkin.',
          u: 'Har qanday loyiha',
          p: 'Har bir o\'zgarish tarixi saqlanadi, jamoaviy ishlash uchun standart.',
          k: 'Buyruqlari (rebase, merge conflict) yangi boshlovchi uchun qiyin tuyulishi mumkin.' },
        { n: 'Docker', r: 'Dasturni "quti"ga solish',
          d: 'Dastur va u talab qiladigan hamma narsani bitta konteynerga joylaydi — "menda ishlaydi, sizda ishlamaydi" muammosini yo\'q qiladi.',
          u: 'Deploy, muhitni bir xillashtirish',
          p: 'Har qanday serverda bir xil ishlaydi, muhitni sozlash bosqichini yo\'q qiladi.',
          k: 'Kichik loyihalar uchun qo\'shimcha murakkablik va resurs sarfi qo\'shadi.' },
        { n: 'Nginx', r: 'Veb-server va teskari proksi',
          d: 'Kiruvchi so\'rovlarni qabul qilib, kerakli dasturga uzatadi. Statik fayllarni ham tez tarqatadi. **Shu saytda ishlaydi.**',
          u: 'Sayt tarqatish, HTTPS, yuk taqsimlash',
          p: 'Juda kam resurs bilan ko\'p so\'rovni ko\'taradi, ishonchliligi yuqori.',
          k: 'Sozlamalari (config) matn fayl ko\'rinishida — xato qilish oson, GUI yo\'q.' },
        { n: 'Linux', r: 'Serverlarning asosiy tizimi',
          d: 'Dunyodagi serverlarning katta qismi Linux\'da ishlaydi. Terminal orqali boshqariladi.',
          u: 'Serverlar',
          p: 'Bepul, ochiq manba, barqaror va resurs tejamkor.',
          k: 'Grafik interfeys server versiyalarida yo\'q — terminal buyruqlarini bilish shart.' },
        { n: 'CI/CD', r: 'Avtomatik tekshirish va joylash',
          d: 'Kod o\'zgarganda testlar o\'zi ishga tushadi va tayyor bo\'lsa serverga o\'zi joylanadi.',
          u: 'Jamoaviy ishlab chiqish',
          p: 'Inson xatosini kamaytiradi, har o\'zgarish avtomatik tekshiriladi.',
          k: 'Boshlang\'ich sozlash vaqt oladi, testlar sifatsiz bo\'lsa yolg\'on ishonch beradi.' },
        { n: 'REST API', r: 'Dasturlar orasidagi til',
          d: 'Ilova server bilan qanday gaplashishini belgilaydigan qoidalar: `GET /users` — ro\'yxatni ol, `POST /users` — yangisini qo\'sh.',
          u: 'Frontend ↔ backend aloqasi',
          p: 'Sodda, keng tushuniladi, HTTP\'ning o\'zidan foydalanadi — maxsus vosita kerak emas.',
          k: 'Bir so\'rovda faqat bitta resurs — bog\'liq ma\'lumot uchun bir nechta so\'rov kerak bo\'lishi mumkin (GraphQL shuni hal qiladi).' }
      ]
    },
    {
      g: 'AI va ma\'lumot tahlili', ic: 'trophy', c: 'var(--purple)', items: [
        { n: 'NumPy', r: 'Raqamli hisob-kitob kutubxonasi',
          d: 'Katta massivlar bilan tez ishlaydi. Deyarli barcha Python ma\'lumot vositalarining poydevori.',
          u: 'Matematik hisoblar',
          p: 'Oddiy Python ro\'yxatlaridan o\'nlab marta tezroq, boshqa kutubxonalarning asosi.',
          k: 'O\'zi past darajali — jadval/tahlil uchun Pandas kabi ustki qatlam kerak bo\'ladi.' },
        { n: 'Pandas', r: 'Jadval ko\'rinishidagi ma\'lumot bilan ishlash',
          d: 'Excel jadvaliga o\'xshash ma\'lumotni kod bilan filtrlash, guruhlash, tozalash.',
          u: 'Ma\'lumot tahlili',
          p: 'Excel/CSV bilan ishlash juda qulay, tayyor funksiyalar ko\'p.',
          k: 'Juda katta ma\'lumot (millionlab qator)da xotira sarfi va tezlik muammo bo\'lishi mumkin.' },
        { n: 'PyTorch', r: 'Neyron tarmoq qurish',
          d: 'Chuqur o\'rganish (deep learning) modellarini yozish va o\'qitish uchun. Tadqiqotda eng ko\'p ishlatiladi.',
          u: 'AI modellar',
          p: 'Moslashuvchan, debug qilish oson, tadqiqot hamjamiyatida standart.',
          k: 'Ishlab chiqarishga joylash (production) TensorFlow\'ga nisbatan qo\'shimcha vosita talab qilishi mumkin.' },
        { n: 'scikit-learn', r: 'Klassik mashina o\'rganish',
          d: 'Regressiya, klasterlash, tasniflash kabi an\'anaviy algoritmlar tayyor holda.',
          u: 'Bashorat modellari',
          p: 'Ishlatish juda sodda (bir necha qatorda model o\'qitiladi), hujjatlari a\'lo.',
          k: 'Chuqur o\'rganish (neyron tarmoq) uchun mos emas — u PyTorch/TensorFlow ishi.' }
      ]
    }
  ];

  function techHeader(title, back) {
    return '<div class="topbar" style="margin:-16px -15px 12px">' +
      (back ? '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: back }) + '\'><span data-icon="arrowLeft" data-icon-size="20"></span></button>' : '') +
      '<div style="display:flex;align-items:center;gap:9px;flex:1;min-width:0">' +
      '<img data-app-icon src="' + App.appIconSrc() + '" alt="Yordamchi" style="width:28px;height:28px;border-radius:8px;object-fit:cover;flex-shrink:0">' +
      '<h1>' + App.esc(title) + '</h1></div></div>';
  }

  /* Haqiqiy texnologiya logosi (languages.js'dagi ~190 talik baza orqali,
     `window.TechIcon` — bitta nusxa, band 3'da ulangan). Topilmasa rangli
     harf plitkasi (`TechIcon.html` o'zi shunday qiladi). */
  function techLogo(name, size) {
    return window.TechIcon ? TechIcon.html(name, size) :
      '<span style="width:' + size + 'px;height:' + size + 'px;border-radius:8px;background:var(--accent);' +
      'color:#fff;font-weight:700;display:inline-flex;align-items:center;justify-content:center">' +
      App.esc(name.charAt(0)) + '</span>';
  }

  function findTech(name) {
    for (var i = 0; i < TECH.length; i++) {
      var f = TECH[i].items.find(function (x) { return x.n === name; });
      if (f) return { t: f, g: TECH[i] };
    }
    return null;
  }

  App.view('coding', {
    nav: 'coding',
    render: function (page) {
      page.innerHTML = techHeader('Texnologiyalar', 'home') +
        '<input class="input" id="tc-q" placeholder="Qidirish: React, baza, mobil..." style="margin-bottom:14px">' +
        '<p class="muted" id="tc-count" style="font-size:12.5px;margin:0 0 10px"></p>' +
        '<div id="tc-list"></div>';
      App.icons(page);

      function render() {
        var q = (App.el('tc-q').value || '').trim().toLowerCase();
        var box = App.el('tc-list');
        var total = 0, html = '';

        TECH.forEach(function (grp) {
          var items = q
            ? grp.items.filter(function (x) {
                return (x.n + ' ' + x.r + ' ' + x.d + ' ' + x.u + ' ' + grp.g).toLowerCase().indexOf(q) >= 0;
              })
            : grp.items;
          if (!items.length) return;
          total += items.length;
          html += '<div class="list-label">' + App.esc(grp.g) + '</div>' +
            items.map(function (x) {
              return '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'coding_tech', p: { n: x.n } }) + '\'>' +
                '<span class="li-ic" style="background:none;padding:0">' + techLogo(x.n, 28) + '</span>' +
                '<div class="li-main"><div class="li-title">' + App.esc(x.n) + '</div>' +
                '<div class="li-sub">' + App.esc(x.r) + '</div></div>' +
                '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
            }).join('');
        });

        App.el('tc-count').textContent = q ? total + ' ta topildi' : total + ' ta texnologiya';
        box.innerHTML = html || App.empty({ icon: 'code', title: 'Topilmadi', text: 'Boshqa so\'z bilan qidiring.' });
        App.icons(box);
      }
      App.el('tc-q').oninput = render;
      render();
    }
  });

  App.view('coding_tech', {
    nav: 'coding',
    render: function (page, params) {
      var found = findTech(params.n);
      if (!found) { App.go('coding'); return; }
      var x = found.t, g = found.g;

      page.innerHTML = techHeader(x.n, 'coding') +
        '<div class="tc-hero" style="background:color-mix(in srgb,' + g.c + ' 12%, transparent)">' +
        '<span class="tc-hero-ic" style="background:none">' + techLogo(x.n, 44) + '</span>' +
        '<div class="tc-hero-r">' + App.esc(x.r) + '</div>' +
        '<div class="tc-hero-g">' + App.esc(g.g) + '</div></div>' +

        '<div class="list-label">Nima qiladi</div>' +
        '<p style="font-size:14.5px;line-height:1.65;margin:0 1px 10px">' + mdBold(x.d) + '</p>' +

        '<div class="list-label">Qayerda ishlatiladi</div>' +
        '<div class="flex" style="flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
        x.u.split(',').map(function (t) {
          return '<span class="chip-btn" style="pointer-events:none">' + App.esc(t.trim()) + '</span>';
        }).join('') + '</div>' +

        (x.p ? '<div class="list-label" style="color:var(--success)">Afzalligi</div>' +
          '<p style="font-size:14px;line-height:1.6;margin:0 1px 10px">' + mdBold(x.p) + '</p>' : '') +

        (x.k ? '<div class="list-label" style="color:var(--danger)">Kamchiligi</div>' +
          '<p style="font-size:14px;line-height:1.6;margin:0 1px 10px">' + mdBold(x.k) + '</p>' : '') +

        '<div class="list-label">Shu guruhdagi boshqalar</div>' +
        g.items.filter(function (o) { return o.n !== x.n; }).map(function (o) {
          return '<button class="list-row" data-act="go" data-arg=\'' + App.arg({ v: 'coding_tech', p: { n: o.n } }) + '\'>' +
            '<span class="li-ic" style="background:none;padding:0">' + techLogo(o.n, 26) + '</span>' +
            '<div class="li-main"><div class="li-title">' + App.esc(o.n) + '</div>' +
            '<div class="li-sub">' + App.esc(o.r) + '</div></div>' +
            '<span class="li-chev" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></button>';
        }).join('');
      App.icons(page);
    }
  });

  /* Matn ichidagi **qalin** belgilarini ajratadi (boshqa HTML kirmaydi — avval esc qilinadi) */
  function mdBold(s) {
    return App.esc(s).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/`([^`]+)`/g, '<code>$1</code>');
  }
})();
