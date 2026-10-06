/* Workout — TURNIKDA BAJARILADIGAN ELEMENTLAR.
 *
 * Ro'yxat foydalanuvchi bergan 10 ta klassik turnik elementi (rus
 * atamalari bilan — voraut muhitida shu nomlar ishlatiladi). Tartib
 * ataylab o'zgartirilmagan: osondan qiyinga qarab boradi.
 *
 * Ko'rinishi ATAYLAB Sport bo'limidagi mashqlar ro'yxati bilan bir xil:
 * chapda rasm, o'rtada nom va qisqa ma'lumot, o'ngda "bajardim" belgisi.
 *
 * Rasm sifatida YouTube darsligining O'Z old ko'rinishi ishlatiladi
 * (img.youtube.com/vi/<id>/hqdefault.jpg) — u har doim aynan o'sha
 * elementni ko'rsatadi va video bilan bir manbadan keladi.
 * Barcha video ID lari oEmbed orqali BITTALAB tekshirilgan.
 */
(function () {
  'use strict';

  var DONE_KEY = 'workout_done_v1';

  function doneList() {
    try { var v = JSON.parse(localStorage.getItem(DONE_KEY) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function saveDone(a) { try { localStorage.setItem(DONE_KEY, JSON.stringify(a)); } catch (e) {} }
  function isDone(id) { return doneList().indexOf(id) >= 0; }

  var LVL = {
    1: { n: 'Oson', c: 'var(--success)' },
    2: { n: 'O\'rta', c: 'var(--warn)' },
    3: { n: 'Qiyin', c: 'var(--danger)' }
  };

  /* `base` — elementga kirishdan oldin kerak bo'lgan ANIQ ko'rsatkichlar.
     Raqamlar to'qib chiqarilmagan — voraut manbalaridan olingan
     (naukaturnika.ru, sportwiki.to, vashsport.com, gogym.fit,
     krasota-zdorove.com, turnikom.ru). `yt` — tekshirilgan darslik. */
  var SKILLS = [
    {
      id: 'detskiy', n: 'Bolalar chiqishi', ru: 'ДЕТСКИЙ ВЫХОД', lvl: 1,
      goal: '3 takror',
      base: [
        { n: 'Tortilish', v: '8-10 ta' },
        { n: 'Brus', v: '15 ta' },
        { n: "Ko'krakkacha tortilish", v: '3 ta' }
      ],
      yt: 'gdShAAess9g',
      md: "**Ishlaydigan mushaklar:** keng orqa mushagi, bitseps, yelka oldi, triseps, panja.\n\n" +
        "Kuch bilan chiqishga (`ВЫХОД СИЛОЙ`) birinchi qadam. Ikkala qo'l birdan " +
        "emas, NAVBAT bilan turnik ustiga o'tadi — shuning uchun yengil. Xalq " +
        "orasida \"сплошные мучения\" deb ataladi, chunki tashqaridan qo'pol ko'rinadi.\n\n" +
        "## Bajarish\n" +
        "**1. Ushlash.** Turnikni ustidan, yelka kengligida. Bosh barmoq turnik " +
        "USTIDA bo'lsin (\"soxta ushlash\") — bilakni aylantirish osonlashadi.\n" +
        "**2. Tortish.** Portlovchi tortilish: maqsad iyak emas, KO'KRAKNING " +
        "pastki qismi turnikga yetishi.\n" +
        "**3. O'tish.** Eng yuqori nuqtada bir tirsakni turnik ustiga aylantiring, " +
        "tanani o'sha tomonga biroz burang.\n" +
        "**4. Ikkinchi qo'l.** Birinchi qo'lga tayanib, ikkinchisini ham chiqaring.\n" +
        "**5. Turish.** Ikkala tirsakni to'g'irlab upor holatiga keling.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Baland tortilish** — turnik ko'krakka tegsin: 4 × 5\n" +
        "2. **Rezina bilan chiqish** — turnikga rezina bog'lab, oyoqni ilmoqqa " +
        "qo'ying: 4 × 3\n" +
        "3. **Past turnikda oyoq yordami bilan** — harakat yo'lini o'rganish uchun: 4 × 5\n" +
        "4. **Negativ chiqish** — yuqoridan sekin tushish: 3 × 3\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Balandlik yetmaydi | Avval \"ko'krakkacha tortilish\" ni 5 taga yetkazing |\n" +
        "| Oyoq bilan qattiq tepish | Oyoqni bir joyda tuting, kuch qo'ldan chiqsin |\n" +
        "| Bilak aylanmaydi | Bosh barmoqni turnik ustiga qo'ying |\n\n" +
        "> **Maslahat:** Bu — o'rganish bosqichi, yakuniy maqsad emas. Harakat " +
        "yo'li o'rnashgach `ВЫХОД СИЛОЙ` ga o'ting.\n\n" +
        "> **Diqqat:** Yelkani 5-10 daqiqa isiting — aylanish paytida bo'g'imga " +
        "keskin yuk tushadi."
    },
    {
      id: 'perevorot', n: "Ag'darilib ko'tarilish", ru: 'ПОДЪЁМ ПЕРЕВОРОТОМ', lvl: 1,
      goal: '3 × 3 takror',
      base: [
        { n: 'Tortilish', v: '10 ta' },
        { n: "To'g'ri oyoq ko'tarish", v: '10 ta' },
        { n: 'Uyoq (L-hang)', v: '10 s' }
      ],
      yt: 'IsFtu8z9poU',
      md: "**Ishlaydigan mushaklar:** qorin, keng orqa mushagi, son bukuvchilari, yelka, bitseps.\n\n" +
        "Turnikning eng klassik elementi. Manbalarda muntazam mashq bilan " +
        "**1-2 oyda** o'zlashtiriladi deb ko'rsatilgan.\n\n" +
        "## Bajarish\n" +
        "**1. Osilish.** Qo'l yelka kengligidan biroz kengroq, tebranishsiz.\n" +
        "**2. Bir vaqtda.** Tortilish VA oyoqni ko'tarish — ikkisi BIRGA. " +
        "(Ikkinchi yo'l ham bor: avval oyoq, keyin tortilish. O'zingizga " +
        "qulayini tanlang.)\n" +
        "**3. Chanoq.** Chanoqni turnikga imkon qadar YAQIN tuting — bu eng " +
        "muhim nuqta. Uzoq bo'lsa og'irlik pastga tortadi va aylanish to'xtaydi.\n" +
        "**4. O'tkazish.** Oyoq turnikdan oshib o'tsin; bel turnik darajasiga " +
        "kelganda tizzani KESKIN buking — bu aylanishni tezlashtiradi.\n" +
        "**5. Yakun.** Tanani aylantirib, to'g'ri qo'lda upor holatiga chiqing.\n\n" +
        "## Tayyorlov mashqlari (shu tartibda)\n" +
        "1. **Tizzani ko'krakka tortish** — 4 set, holdan toyguncha. 20+ takror " +
        "chiqsa keyingisiga o'ting.\n" +
        "2. **Tizza ko'tarib, oyoqni yozish** — 4 set, holdan toyguncha. 20+ da o'ting.\n" +
        "3. **Uyoq (oyoq gorizontal)** — 4 set. Asta-sekin balandroq ko'taring.\n" +
        "4. **Oyoqni turnikga tegizish** — 10-20 takror chiqsa tayyorsiz.\n" +
        "5. Tortilish kam bo'lsa: avstraliya tortilishi, negativ tortilish, rezina.\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Tana ag'darilmaydi | Bel turnik darajasida tizzani keskin buking |\n" +
        "| Chanoq uzoqda | Oyoqni turnikdan OSHIRIB o'tkazing, oldiga emas |\n" +
        "| Panja bo'shab ketadi | Bosh barmoq bilan mahkam o'rab ushlang |\n" +
        "| Oyoq va tortilish alohida | Bir vaqtda: oyoq ko'tarilganda qo'l tortsin |\n\n" +
        "> **Maslahat:** Boshlashda past turnikdan foydalaning — oyoq yerga tegib " +
        "turadi, qo'rquv yo'qoladi.\n\n" +
        "> **Diqqat:** Ushlash kuchsiz bo'lsa ag'darilish paytida tushib ketish " +
        "xavfi bor. Panja charchaganda urinmang."
    },
    {
      id: 'vihod-siloy', n: 'Kuch bilan chiqish', ru: 'ВЫХОД СИЛОЙ', lvl: 2,
      goal: '1 toza takror (silkinishsiz)',
      base: [
        { n: 'Tortilish', v: '12-15 ta' },
        { n: 'Brus', v: '20 ta' },
        { n: "Ko'krakkacha tortilish", v: '5 ta' },
        { n: 'Bolalar chiqishi', v: '3 ta' }
      ],
      yt: '3ZknAy2Zjuo',
      md: "**Ishlaydigan mushaklar:** keng orqa, bitseps, yelka, triseps, ko'krak, qorin.\n\n" +
        "Turnikning eng mashhur elementi. Manbalarda **eng kam** talab: 8-10 ta " +
        "to'liq amplitudali tortilish va 15-20 ta brus. **Qulay** daraja: 12-15 ta " +
        "ko'krakkacha tortilish va 20+ brus.\n\n" +
        "> Muhim: takror soni — boshlang'ich nuqta, KAFOLAT emas. 15-20 ta " +
        "tortiladigan odamda ham chiqmasligi mumkin — sabab odatda texnikada.\n\n" +
        "## Bajarish\n" +
        "**1. Ushlash.** Yelka kengligida, bosh barmoq turnik ustida (\"soxta " +
        "ushlash\") — bilak aylanishi shundan osonlashadi.\n" +
        "**2. Tortish.** Oddiy tortilish emas: butun tanani turnikdan YUQORIGA " +
        "va USTIGA olib chiqish kerak. Turnik ko'mrak suyagi (yoqa) darajasiga kelsin.\n" +
        "**3. O'tish.** Eng qiyin qism. Tana turnik atrofida **S shaklidagi** yo'l " +
        "bo'ylab harakatlanadi — to'g'ri chiziq bo'ylab EMAS. Ko'krak turnikdan " +
        "o'tgach itarish boshlanadi.\n" +
        "**4. Itarish.** Brusdagidek — tirsakni to'liq to'g'irlab yuqoriga turing.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Baland tortilish** — turnik ko'krakka, keyin QORINGA tegsin: 4 × 3-5\n" +
        "2. **Portlovchi tortilish** — maksimal tezlikda: 4 × 5\n" +
        "3. **Plio tortilish** — yuqorida qo'lni turnikdan uzib qarsak: 3 × 3\n" +
        "4. **Negativ chiqish** — upordan sekin tushish: 3 × 3\n" +
        "5. **Rezina bilan chiqish** — texnikani mustahkamlash: 4 × 3\n" +
        "6. **Osilib oyoq ko'tarish** — o'tishda kor kerak: 3 × 10\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Balandlik yetmaydi | Baland tortilishni qoringacha yetkazing |\n" +
        "| To'g'ri chiziq bo'ylab tortish | S yo'li: avval o'zingizga, keyin ustiga |\n" +
        "| O'tishda ikkilanish | Harakat TEZ bo'lsin, sekinlashtirsa kuch yo'qoladi |\n" +
        "| Yuqorida turolmaslik | Brusni 20 taga yetkazing, triseps yetishmayapti |\n" +
        "| Faqat qo'l bilan tortish | Kor va yelkani ham qo'shing |\n\n" +
        "> **Diqqat:** Yelka bo'g'imiga katta yuk tushadi. Yelkada yoki tirsakda " +
        "og'riq bo'lsa bu elementga umuman kirishmang — avval davolang."
    },
    {
      id: 'sklepka', n: "Yozilib ko'tarilish", ru: 'ПОДЪЁМ РАЗГИБОМ (СКЛЁПКА)', lvl: 2,
      goal: '3 toza takror',
      base: [
        { n: 'Tortilish', v: '5-8 ta' },
        { n: "Oyoqni turnikga tegizish", v: '10 ta' },
        { n: 'Barqaror silkinish', v: 'kerak' }
      ],
      yt: 'u__tT8654Mg',
      md: "**Ishlaydigan mushaklar:** qorin, son bukuvchilari, keng orqa, yelka, panja.\n\n" +
        "Gimnastik element. **Kuch emas, TEXNIKA hal qiladi** — manbalarda aniq " +
        "yozilgan: 20 marta tortilish shart emas. Shuning uchun kuchi kam " +
        "bo'lganlar ham o'rganishi mumkin.\n\n" +
        "## Bajarish\n" +
        "**1. Silkinish.** Yengil mah hosil qiling. **Yelka BO'SH bo'lsin** — " +
        "taranglashsa silkinish so'nadi.\n" +
        "**2. Oldinga.** Oldinga silkinishda tik chiziqdan o'tayotib belni biroz buking.\n" +
        "**3. O'lik nuqta.** Silkinishning eng oxirgi nuqtasini kuting — harakat " +
        "bir lahza to'xtaydi.\n" +
        "**4. Yozish.** O'sha lahzada oyoq UCHINI turnikga tortib, belni keskin " +
        "yozing. Oyoqni ERTA olib kelmang — butun sir shunda.\n" +
        "**5. Bosish.** Ayni paytda to'g'ri qo'l bilan turnikni PASTGA bosing. " +
        "Inersiya sizni upor holatiga olib chiqadi.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Toza silkinish** — yelka bo'sh, tana to'g'ri: 5 × 10 mah\n" +
        "2. **Oyoqni turnikga tegizish** — silkinishsiz: 4 × 10\n" +
        "3. **Past turnikda склёпка** — oyoq yerga tegib turadi: 5 × 5\n" +
        "4. **Lyamka (tasma) bilan** — panja charchamaydi, ko'p takrorlash mumkin\n" +
        "5. **Uporda turish** — 4 × 20 s\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Oyoqni erta olib kelish | O'lik nuqtani kuting, keyin yozing |\n" +
        "| Qo'lni bukish | Qo'l TO'G'RI qolsin — bukilsa bosish yo'qoladi |\n" +
        "| Chanoq turnikdan uzoq | Chanoqni turnikga tortib turing |\n" +
        "| Yozish kuchsiz | Past turnikda oyoq yordami bilan mashq qiling |\n" +
        "| Silkinish so'nadi | Yelkani bo'shating, tarang tutmang |\n\n" +
        "> **Maslahat:** Sekin bajarib bo'lmaydi — bir zarb bilan qilinadi. " +
        "Kuch emas, ANIQ LAHZA muhim.\n\n" +
        "> **Diqqat:** Ko'p takrorlaganda panja bo'shab, turnikdan uchib ketish " +
        "mumkin. Lyamka ishlating yoki yumshoq yerda mashq qiling."
    },
    {
      id: 'kapitanskiy', n: "Kapitan ko'tarilishi", ru: 'КАПИТАНСКИЙ ПОДЪЁМ', lvl: 2,
      goal: '3 takror (har ikki tomonga)',
      base: [
        { n: 'Tortilish', v: '10 ta' },
        { n: 'Brus', v: '15 ta' },
        { n: "Ag'darilib ko'tarilish", v: '3 ta' }
      ],
      yt: '_qu9VvYYKKY',
      md: "**Ishlaydigan mushaklar:** keng orqa, bitseps, yelka, qorin qiya mushaklari.\n\n" +
        "Ag'darilib ko'tarilish bilan kuch bilan chiqish oralig'idagi element. " +
        "Yuk ikkala qo'lga TENG tushmaydi: biri tayanch, ikkinchisi aylantiruvchi.\n\n" +
        "## Bajarish\n" +
        "**1. Osilish.** Yelka kengligida, tebranishsiz.\n" +
        "**2. Tortish + burish.** Tortilayotib tanani BIR tomonga burang. " +
        "O'sha tomondagi qo'l tayanch bo'ladi.\n" +
        "**3. Tayanch.** Og'irlikni tayanch qo'lga bering, tirsagini turnik " +
        "ustiga chiqaring.\n" +
        "**4. Ikkinchi qo'l.** Erkin qo'lni turnik ustiga olib o'ting.\n" +
        "**5. Yakun.** Tanani to'g'irlab upor holatiga chiqing.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Bir qo'lga og'irlik berib tortilish** — tanani yon burib: 4 × 5 (har tomon)\n" +
        "2. **Yarim chiqish** — bitta tirsakni turnik ustiga chiqarib ushlab turish: 4 × 5\n" +
        "3. **Ag'darilib ko'tarilish** — 4 × 3\n" +
        "4. **Uporda turish va tushish** — 4 × 20 s\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Ikkala qo'lga teng yuk | Tanani ANIQ bir tomonga burang |\n" +
        "| Tayanch qo'l bukiladi | Tayanch qo'lni to'g'ri tuting |\n" +
        "| Faqat kuchli tomonga mashq | Ikkala tomonga TENG mashq qiling |\n\n" +
        "> **Maslahat:** Bir tomonlama mashq yelkalarni nomutanosib " +
        "rivojlantiradi — har set'da tomonni almashtiring."
    },
    {
      id: 'basket-kip', n: "Ikki oyoqlab ko'tarilish", ru: 'ПОДЪЁМ ДВУМЯ (BASKET KIP)', lvl: 2,
      goal: '3 takror',
      base: [
        { n: 'Yozilib ko\'tarilish', v: '3 ta' },
        { n: "Oyoqni turnikga tegizish", v: '15 ta' },
        { n: 'Uporda turish', v: '20 s' }
      ],
      yt: '0__Yu5qnkv8',
      md: "**Ishlaydigan mushaklar:** qorin, son bukuvchilari, keng orqa, yelka.\n\n" +
        "Gimnastik \"kip\" oilasidan. Silkinish energiyasini ko'tarilishga " +
        "aylantirishni o'rgatadi. `СКЛЁПКА` ning silkinishli, murakkabroq davomi.\n\n" +
        "## Bajarish\n" +
        "**1. Mah.** Osilib yengil silkinish hosil qiling.\n" +
        "**2. Savat.** Oldinga silkinish oxirida oyoqni yig'ib, tanani \"savat\" " +
        "(basket) shakliga keltiring — chanoq turnikga yaqin, oyoq yuqorida.\n" +
        "**3. Kutish.** O'lik nuqtani kuting.\n" +
        "**4. Yozish.** Orqaga qaytishda oyoqni keskin OLDINGA va YUQORIGA yozing.\n" +
        "**5. Bosish.** Ayni paytda turnikni pastga bosing — tana ustiga chiqadi.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Savat holatida ushlab turish** — 4 × 10 s\n" +
        "2. **Savatdan yozish** (upor holatiga chiqmasdan) — 4 × 8\n" +
        "3. **Склёпка** — 4 × 3\n" +
        "4. **Past turnikda to'liq harakat** — 5 × 3\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Silkinish juda kuchli | Kichik mahdan boshlang — nazorat muhimroq |\n" +
        "| Kech yozish | O'lik nuqtada yozing, undan keyin emas |\n" +
        "| Savat holati bo'sh | Chanoqni turnikga tortib, qorinni siqing |\n\n" +
        "> **Maslahat:** Avval `СКЛЁПКА` ni o'zlashtiring — bu element o'shaning " +
        "davomi va tayyorgarliksiz chiqmaydi."
    },
    {
      id: 'oficerskiy', n: 'Ofitser chiqishi', ru: 'ОФИЦЕРСКИЙ ВЫХОД', lvl: 3,
      goal: '3 takror (har ikki tomonga)',
      base: [
        { n: 'Tortilish', v: '12-15 ta' },
        { n: 'Brus', v: '20 ta' },
        { n: 'Kuch bilan chiqish', v: '3 ta' }
      ],
      yt: '283MrPe5LxQ',
      md: "**Ishlaydigan mushaklar:** yelka, bilak, keng orqa, triseps, panja.\n\n" +
        "\"Dembel chiqishi\" deb ham ataladi. Kuch bilan chiqishning bir qo'lli, " +
        "NAZORATLI shakli — qo'llar navbat bilan, lekin sekin va toza o'tadi. " +
        "Boshqa ko'plab chiqish turlariga asos bo'ladi.\n\n" +
        "## Bajarish\n" +
        "**1. Ushlash.** Ikkala qo'l ustidan yoki aralash (biri ustidan, biri " +
        "pastdan) — aralash ushlash osonroq.\n" +
        "**2. Tortish.** Baland tortiling, turnik ko'krakka yaqin kelsin.\n" +
        "**3. Birinchi qo'l.** Bir tirsakni turnik USTIGA chiqaring — silkinishsiz, " +
        "nazorat bilan.\n" +
        "**4. Ushlab turish.** Bir lahza shu holatda turing. **Aynan shu qism " +
        "elementni \"ofitser\" qiladi** — silkinib o'tilsa bu `детский выход`.\n" +
        "**5. Ikkinchi qo'l.** Ikkinchi tirsakni ham chiqarib, upor holatiga turing.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Bir qo'lda upor** (turnik ustida tirsak) ushlab turish: 4 × 10 s har tomon\n" +
        "2. **Brusda oldinga siljib otjimaniya** — 4 × 10\n" +
        "3. **Yerda orqa tayanch** (bilak kuchi uchun) — 4 × 20 s\n" +
        "4. **Kuch bilan chiqish** — 4 × 2\n" +
        "5. **Rezina bilan sekin chiqish** — nazoratni o'rgatadi: 4 × 3\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Silkinib bajarish | Sekinlating — farq TEZLIKDA emas, NAZORATDA |\n" +
        "| Bir qo'lda kuch yetmaydi | \"Bir qo'lda upor\" ushlab turishni ko'paytiring |\n" +
        "| Bilak og'riydi | Bilakni alohida isiting, aralash ushlashga o'ting |\n" +
        "| Faqat bitta tomonga | Har set'da tomonni almashtiring |\n\n" +
        "> **Diqqat:** Bilak va yelka bo'g'imiga katta yuk tushadi — isinmasdan " +
        "urinmang."
    },
    {
      id: 'zamok', n: "Orqaga silkinib ko'tarilish", ru: 'ПОДЪЁМ МАХОМ НАЗАД (ЗАМОК)', lvl: 3,
      goal: '3 takror',
      base: [
        { n: "Ikki oyoqlab ko'tarilish", v: '3 ta' },
        { n: 'Uporda turish', v: '30 s' },
        { n: 'Barqaror silkinish', v: 'kerak' }
      ],
      yt: 'GvJe3MVk6tY',
      md: "**Ishlaydigan mushaklar:** yelka, keng orqa, kor, panja.\n\n" +
        "Silkinishning ORQA nuqtasidan foydalanib ko'tarilish. Manbalarda " +
        "\"qo'lni bukmasdan, tana inersiyasi bilan bajariladigan itarish\" deb " +
        "ta'riflanadi — ya'ni tortilish YO'Q.\n\n" +
        "## Bajarish\n" +
        "**1. Silkinish.** Osilib bir tekis mah hosil qiling.\n" +
        "**2. Orqaga.** ORQAGA silkinishning eng yuqori nuqtasini kuting. " +
        "(Oldinga silkinishda urinsangiz kuch teskari ishlaydi.)\n" +
        "**3. Bosish.** O'sha lahzada to'g'ri qo'l bilan turnikni pastga bosing " +
        "va chanoqni turnikga yaqinlashtiring.\n" +
        "**4. Qulflash.** Tana turnik ustiga chiqadi va upor holatida \"qulflanadi\" " +
        "— nomi shundan.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Past turnikda oyoq yordami bilan** — harakat yo'lini o'rganish: 5 × 5\n" +
        "2. **Uporda turish va sekin tushish** — 4 × 20 s\n" +
        "3. **Orqaga mah nazorati** — faqat silkinish, ko'tarilishsiz: 5 × 10\n" +
        "4. **Turnikni pastga bosish** (to'g'ri qo'lda) — 4 × 8\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Oldinga silkinishda urinish | Faqat ORQA nuqtada bajaring |\n" +
        "| Qo'lni bukish | Qo'l to'g'ri — bu tortilish emas, itarish |\n" +
        "| Chanoq uzoqda | Chanoqni turnikga tortib turing |\n\n" +
        "> **Diqqat:** Panja bo'shasa turnikdan uchib ketish mumkin. Past " +
        "turnikda, yumshoq yerda o'rganing."
    },
    {
      id: 'iz-pod', n: 'Turnik ostidan chiqish', ru: 'ВЫХОД ИЗ-ПОД ТУРНИКА', lvl: 3,
      goal: '1 toza takror',
      base: [
        { n: 'Kuch bilan chiqish', v: '5 ta' },
        { n: 'Yelka harakatchanligi', v: "to'liq" },
        { n: 'Brus', v: '20 ta' }
      ],
      yt: 'ZTbaiTzMRJw',
      md: "**Ishlaydigan mushaklar:** yelka (to'liq aylana), keng orqa, kor, panja.\n\n" +
        "G'ayrioddiy boshlang'ich holatdan chiqish. Yelka harakatchanligini va " +
        "fazoviy tuyg'uni rivojlantiradi.\n\n" +
        "## Bajarish\n" +
        "**1. Boshlang'ich.** Turnikning ORQA tomonidan, tana turnik ostida " +
        "qoladigan qilib osiling.\n" +
        "**2. Mah.** Silkinish bilan tanani turnik ostidan OLDINGA olib chiqing.\n" +
        "**3. Tortish.** Ayni lahzada kuchli tortiling — turnik ko'krakka kelsin.\n" +
        "**4. Aylantirish.** Bilakni turnik ustiga aylantiring.\n" +
        "**5. Itarish.** Tirsakni to'g'irlab upor holatiga chiqing.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Yelka aylanmasi** (tayoq/rezina bilan) — har mashg'ulotdan oldin: 3 × 10\n" +
        "2. **Past turnikda ostidan chiqish** — oyoq yordami bilan: 5 × 3\n" +
        "3. **Kuch bilan chiqish** — 4 × 3\n" +
        "4. **Orqa tayanchda cho'zilish** — yelka ochilishi uchun: 3 × 30 s\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Yelka yetishmaydi | Avval harakatchanlik ustida ishlang, elementga shoshilmang |\n" +
        "| Silkinishni kuch bilan almashtirish | Mah kerak — faqat kuch bilan chiqmaydi |\n" +
        "| Turnikni tor ushlash | Kengroq ushlang, yelkaga joy bo'lsin |\n\n" +
        "> **Diqqat:** Yelka bo'g'imi noqulay burchakda ishlaydi. Yelka " +
        "harakatchanligi yetarli bo'lmasa bu elementga KIRISHMANG — " +
        "bo'g'im shikastlanishi mumkin."
    },
    {
      id: 'cast-monkey', n: 'Upordan manki', ru: 'МАНКИ ИЗ УПОРА (CAST MONKEY)', lvl: 3,
      goal: '1 toza takror',
      base: [
        { n: 'Uporda turish', v: '30 s' },
        { n: 'Kuch bilan chiqish', v: '5 ta' },
        { n: "Ag'darilib ko'tarilish", v: '5 ta' }
      ],
      yt: '6yzDG7AiM-4',
      md: "**Ishlaydigan mushaklar:** yelka, kor, panja, butun tana muvofiqligi.\n\n" +
        "Friston (freestyle) elementlariga kirish. Tana turnikdan BUTUNLAY " +
        "uziladi va qaytadan ushlanadi — shuning uchun ro'yxatdagi eng xavfli " +
        "element.\n\n" +
        "## Bajarish\n" +
        "**1. Upor.** To'g'ri qo'lda barqaror upor holatida turing.\n" +
        "**2. Cast.** Chanoqni orqaga uloqtirib tanani turnikdan uzoqlashtiring — " +
        "bu harakat kuchli bo'lishi kerak, aylanish energiyasi shundan keladi.\n" +
        "**3. Qaytish.** Tana qaytib kelayotganda inersiyani his qiling.\n" +
        "**4. Qo'yib yuborish.** Aniq lahzada turnikni qo'yib yuboring.\n" +
        "**5. Qayta ushlash.** Tana turnik atrofida aylanadi — ushlab osilib qoling.\n\n" +
        "## Tayyorlov mashqlari\n" +
        "1. **Uporda cast** (qo'yib yubormasdan) — 5 × 8\n" +
        "2. **Past turnikda to'liq harakat** — oyoq yerga yetadigan balandlikda: 5 × 3\n" +
        "3. **Qo'yib yuborib qayta ushlash** (osilgan holatda, kichik) — 4 × 5\n" +
        "4. **Uporda turish** — 4 × 30 s\n\n" +
        "## Tipik xatolar va yechimi\n" +
        "| Xato | Yechim |\n" +
        "|---|---|\n" +
        "| Erta qo'yib yuborish | Cast eng yuqori nuqtaga chiqsin, keyin qo'ying |\n" +
        "| Cast kuchsiz | Chanoqni kuchliroq uloqtiring |\n" +
        "| Qayta ushlashda adashish | Past turnikda ko'p takrorlang |\n\n" +
        "> **Diqqat:** RO'YXATDAGI ENG XAVFLI ELEMENT. Tana turnikdan uziladi — " +
        "noto'g'ri tushish jiddiy jarohatga olib keladi. Faqat past turnikda, " +
        "yumshoq yerda (mat yoki qum) va iloji bo'lsa SHERIK bilan o'rganing. " +
        "Charchagan holatda urinmang."
    }
  ];

  function skill(id) { return SKILLS.find(function (s) { return s.id === id; }); }
  function ytThumb(id) { return 'https://img.youtube.com/vi/' + id + '/hqdefault.jpg'; }
  function ytLink(id) { return 'https://www.youtube.com/watch?v=' + id; }

  /* =========================================================
     VIEW: workout — elementlar ro'yxati (Sport uslubida)
     ========================================================= */
  App.view('workout', {
    nav: 'sport',
    render: function (page) {
      var done = doneList().filter(function (id) { return !!skill(id); });
      var pct = Math.round((done.length / SKILLS.length) * 100);

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"sport"}\'>' +
        '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>Workout</h1>' +
        '<div style="flex:1"></div>' +
        '<span class="muted" style="font-size:12px;font-weight:700;font-family:var(--mono)">' +
        done.length + ' / ' + SKILLS.length + '</span></div>' +

        '<div class="wk-intro">' +
        '<b>Turnikda bajariladigan elementlar</b>' +
        '<p>Osondan qiyinga. Har bir elementda texnika, bazaviy kuch talabi va ' +
        'video darslik bor.</p>' +
        '<div class="wk-prog"><i style="width:' + pct + '%"></i></div>' +
        '</div>' +

        SKILLS.map(function (s, i) {
          var d = isDone(s.id), L = LVL[s.lvl] || LVL[1];
          return '<div class="list-row">' +
            '<span class="wk-th"><img src="' + ytThumb(s.yt) + '" alt="" loading="lazy"></span>' +
            '<button class="li-main" style="background:none;border:none;text-align:left;padding:0" ' +
            'data-act="go" data-arg=\'' + App.arg({ v: 'workout_skill', p: { id: s.id } }) + '\'>' +
            '<div class="li-title">' + (i + 1) + '. ' + App.esc(s.n) + '</div>' +
            '<div class="li-sub wk-ru">' + App.esc(s.ru) + '</div>' +
            '<div class="li-sub"><span style="color:' + L.c + ';font-weight:700">' + L.n + '</span>' +
            ' · ' + App.esc(s.goal) + '</div></button>' +
            '<button class="icon-btn ghost sp-log' + (d ? ' done' : '') + '" data-act="wkToggle" ' +
            'data-arg=\'' + App.arg({ id: s.id }) + '\' title="O\'zlashtirdim">' +
            '<span data-icon="check" data-icon-size="17"></span></button>' +
            '</div>';
        }).join('');

      App.icons(page);
    }
  });

  /* =========================================================
     VIEW: workout_skill — bitta element
     ========================================================= */
  App.view('workout_skill', {
    nav: 'sport',
    render: function (page, params) {
      var s = skill(params.id);
      if (!s) { App.go('workout'); return; }
      var d = isDone(s.id), L = LVL[s.lvl] || LVL[1];

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'{"v":"workout"}\'>' +
        '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(s.n) + '</h1></div>' +

        '<div class="wk-badge" style="--wk-c:' + L.c + '">' + App.esc(L.n) + '</div>' +
        '<div class="wk-ru-big">' + App.esc(s.ru) + '</div>' +

        /* Video — bosilgunicha faqat old ko'rinish, YouTube yuklanmaydi */
        '<div class="wk-video" id="wk-video" data-yt="' + s.yt + '">' +
        '<img src="' + ytThumb(s.yt) + '" alt="" loading="lazy">' +
        '<button class="wk-play" data-act="wkPlay" aria-label="Videoni ochish">' +
        '<span data-icon="play" data-icon-size="26"></span></button>' +
        '</div>' +
        '<a class="wk-ytlink" href="' + ytLink(s.yt) + '" target="_blank" rel="noopener">' +
        'YouTube\'da ochish</a>' +

        '<div class="wk-goalbox"><span data-icon="trophy" data-icon-size="16"></span>' +
        '<div><span>Maqsad</span><b>' + App.esc(s.goal) + '</b></div></div>' +

        ((s.base && s.base.length)
          ? '<div class="list-label">Bazaviy kuch</div><div class="wk-base">' +
            s.base.map(function (b) {
              return '<span class="wk-chip"><b>' + App.esc(b.v) + '</b>' + App.esc(b.n) + '</span>';
            }).join('') + '</div>'
          : '') +

        '<div class="list-label">Texnika</div>' +
        '<div class="md-content">' + App.md(s.md) + '</div>' +

        '<button class="btn' + (d ? ' sec' : '') + '" style="margin-top:18px" data-act="wkToggle" ' +
        'data-arg=\'' + App.arg({ id: s.id }) + '\'>' +
        (d ? '✓ O\'zlashtirilgan — bekor qilish' : 'O\'zlashtirdim') + '</button>';

      App.icons(page);
    }
  });

  /* Videoni bosilganda yuklaymiz — sahifa ochilishida YouTube so'ralmaydi. */
  App.actions.wkPlay = function () {
    var box = App.el('wk-video'); if (!box) return;
    var id = box.getAttribute('data-yt');
    box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1" ' +
      'title="Video" frameborder="0" allow="accelerometer; autoplay; clipboard-write; ' +
      'encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>';
    box.classList.add('playing');
  };

  /* Sport bo'limidagi "Workout" plitkasi shu yerdan holatini oladi. */
  window.Workout = {
    progress: function () {
      var d = doneList().filter(function (id) { return !!skill(id); });
      return { done: d.length, total: SKILLS.length };
    }
  };

  App.actions.wkToggle = function (a) {
    var list = doneList();
    var i = list.indexOf(a.id);
    if (i >= 0) list.splice(i, 1); else list.push(a.id);
    saveDone(list);

    if (i < 0) {
      var s = skill(a.id);
      if (s) {
        App.call('log_activity', {
          section: 'sport', object: s.n, amount: 1, unit: 'element',
          meta: { kind: 'workout', ru: s.ru }
        }).catch(function () {});
      }
      App.toast('✅ O\'zlashtirildi!');
    }
    App.reload();
  };
})();
