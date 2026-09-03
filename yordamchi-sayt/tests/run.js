#!/usr/bin/env node
/*
 * Sof mantiq uchun testlar — `node tests/run.js`.
 *
 * NIMA UCHUN KERAK
 * ================
 * 2026-08-29 da uchta nuqson topildi va UCHALASI HAM XATO BERMAGAN edi —
 * ular shunchaki jimgina ishlamagan:
 *
 *   1. Juftlash 400 dan ortiq so'zli lug'atda butunlay o'chib qolardi
 *      (ya'ni 8000 so'zlik lug'atda hech qachon ishlamagan).
 *   2. `.md` dagi "Chalkashadi:" qatori o'qilardi, keyin yo'qolardi.
 *   3. Bir so'z 12 ta "oila"ga tushib ketardi, natijada "я пишу / я сижу"
 *      kabi umuman o'xshamagan juftlar chiqardi.
 *
 * Bunday nuqsonni qo'lda ko'rish qiyin: ekranda nimadir ko'rinadi, xato
 * yo'q, lekin natija noto'g'ri. Shuning uchun eng qimmatli joylar —
 * juftlash algoritmi va o'qish intonatsiyasi — shu yerda qulflab qo'yildi.
 *
 * Brauzer kutubxonasi yo'q: fayllar `window` soxta obyekti bilan yuklanadi.
 */
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
let pass = 0, fail = 0;
const failures = [];

function check(name, cond, detail) {
  if (cond) { pass++; return; }
  fail++;
  failures.push(name + (detail ? '  ->  ' + detail : ''));
}

function eq(name, got, want) {
  check(name, JSON.stringify(got) === JSON.stringify(want),
    'kutilgan ' + JSON.stringify(want) + ', kelgan ' + JSON.stringify(got));
}

/* ---------- Brauzer fayllarini yuklash ---------- */
function loadIntoWindow(relPath) {
  const win = {};
  const code = fs.readFileSync(path.join(ROOT, relPath), 'utf8');
  new Function('window', 'self', code)(win, win);
  return win;
}

/* `reading.js` butun App/TTS ilovasiga bog'liq, shuning uchun undan faqat
   sof intonatsiya qismini ajratib olamiz. */
function loadProsody() {
  const src = fs.readFileSync(path.join(ROOT, 'assets/js/app2/reading.js'), 'utf8');
  // `PROSODY` jadvalidan boshlaymiz — `prosodyParts` unga tayanadi.
  const a = src.indexOf('  var PROSODY = {');
  const b = src.indexOf("  /* Bitta bo'lakni");
  if (a < 0 || b < 0) throw new Error('reading.js ichidagi intonatsiya bloki topilmadi');
  const scope = {};
  new Function('exports', src.slice(a, b) + '\nexports.prosodyParts = prosodyParts;')(scope);
  return scope.prosodyParts;
}

/* `vocab.js` da .md faylni so'zlarga aylantiruvchi sof funksiya bor —
   uni ham ajratib olamiz. */
function loadMdParser() {
  const src = fs.readFileSync(path.join(ROOT, 'assets/js/app2/vocab.js'), 'utf8');
  const a = src.indexOf('  function parseMdToDictCategories(');
  const b = src.indexOf('  function bulkSheetHtml(');
  if (a < 0 || b < 0) throw new Error('vocab.js ichidagi .md parser topilmadi');
  const scope = {};
  new Function('exports', src.slice(a, b) + '\nexports.parseMdToDictCategories = parseMdToDictCategories;')(scope);
  return scope.parseMdToDictCategories;
}

/* =========================================================
   1. Juftlash (paircore.js)
   ========================================================= */
const PairCore = loadIntoWindow('assets/js/core/paircore.js').PairCore;
const ru = (list) => list.map((r) => (typeof r === 'string' ? { ru: r, uz: '' } : r));
const names = (groups) => groups.map((g) => g.map((w) => w.ru).join('|'));

{
  // O'zak oilasi — ma'no prefiksda farq qiladi
  const g = PairCore.build(ru([
    'давать', 'отдавать', 'передавать', 'раздавать', 'играть'
  ]), 'russian');
  check('o\'zak oilasi topiladi', g.length === 1 && g[0].length === 4, names(g).join(' ; '));
  check('begona so\'z oilaga qo\'shilmaydi',
    !names(g).join('').includes('играть'), names(g).join(' ; '));
}

{
  // Tuslangan shakl: "я " olmoshi solishtirishga QO'SHILMASLIGI kerak.
  // Aynan shu narsa "я пишу / я сижу" kabi soxta juftlarni yaratardi.
  const g = PairCore.build(ru(['я пишу', 'я сижу', 'я глажу', 'я плачу']), 'russian');
  eq('o\'xshamagan qisqa so\'zlar juftlanmaydi', names(g), []);
}

{
  // Umumiy boshi bor haqiqiy juft — saqlanishi kerak
  const g = PairCore.build(ru(['я храню', 'я храплю', 'я играю']), 'russian');
  eq('umumiy boshli juft topiladi', names(g), ['я храню|я храплю']);
}

{
  // Har so'z FAQAT BITTA oilada bo'lsin
  const words = ru(['ходить', 'заходить', 'проходить', 'находить', 'уходить', 'выходить']);
  const g = PairCore.build(words, 'russian');
  const seen = {};
  let dup = 0;
  g.forEach((grp) => grp.forEach((w) => { seen[w.ru] = (seen[w.ru] || 0) + 1; if (seen[w.ru] > 1) dup++; }));
  check('bir so\'z bir nechta oilada emas', dup === 0, dup + ' ta takror');
}

{
  // Qo'lda ko'rsatilgan juftlik avtomatikadan USTUN.
  // "снимать/убирать" yozilishi umuman o'xshamaydi — buni faqat odam bog'lay oladi.
  const g = PairCore.build([
    { ru: 'снимать', uz: '', pairWith: ['убирать'] },
    { ru: 'убирать', uz: '' },
    { ru: 'играть', uz: '' }
  ], 'russian');
  eq('qo\'lda ko\'rsatilgan juftlik ishlaydi', names(g), ['снимать|убирать']);
}

{
  // Katta lug'atda ham ishlashi SHART. Ilgari bu yerda `length <= 400`
  // cheklovi bor edi va 8000 so'zlik lug'atda juftlash umuman o'chib qolardi.
  const big = [];
  for (let i = 0; i < 3000; i++) big.push({ ru: 'слово' + i, uz: '' });
  big.push({ ru: 'храню', uz: '' }, { ru: 'храплю', uz: '' });
  const t0 = Date.now();
  const g = PairCore.build(big, 'russian');
  const ms = Date.now() - t0;
  check('katta lug\'atda ham juftlaydi',
    names(g).some((x) => x === 'храню|храплю'), 'topilmadi');
  check('katta lug\'atda tez ishlaydi (<3s)', ms < 3000, ms + ' ms');
}

{
  // Bir xil so'z ikki marta yozilgan bo'lsa "juftlik" yasalmasin
  const g = PairCore.build(ru(['изучаю', 'изучаю']), 'russian');
  eq('bir xil so\'z juftlik emas', names(g), []);
}

/* =========================================================
   2. O'qish intonatsiyasi (reading.js)
   ========================================================= */
const prosodyParts = loadProsody();
const texts = (t) => prosodyParts(t).map((p) => p.text);

{
  eq('gap oxirlari bo\'yicha bo\'linadi',
    texts('Здравствуйте! Как вас зовут?'),
    ['Здравствуйте!', 'Как вас зовут?']);

  const q = prosodyParts('Как вас зовут?')[0];
  check('so\'roqda ohang ko\'tariladi', q.pitch > 1.1, 'pitch=' + q.pitch);

  const d = prosodyParts('Он ушёл.')[0];
  check('nuqtada ohang pasayadi', d.pitch < 1, 'pitch=' + d.pitch);
}

{
  // Qisqartma gap oxiri EMAS, lekin undan keyingi haqiqiy gap chegarasi
  // o'tkazib yuborilmasligi kerak.
  eq('qisqartma bo\'linmaydi, keyingi gap bo\'linadi',
    texts('Он купил хлеб и т. д. Потом ушёл.'),
    ['Он купил хлеб и т. д.', 'Потом ушёл.']);

  eq('unvondan keyin bo\'linmaydi',
    texts('Mr. Smith пришёл.'),
    ['Mr. Smith пришёл.']);
}

{
  // Vergul ATAYLAB chegara emas — har vergulda uzilsa nutq bo'g'iladi
  eq('vergulda bo\'linmaydi',
    texts('Это книга, которую я читал вчера.'),
    ['Это книга, которую я читал вчера.']);
}

{
  // Tire o'qilmaydi, uning o'rniga jimlik qo'yiladi
  const p = prosodyParts('Мама — врач.');
  eq('tire matndan chiqariladi', p.map((x) => x.text), ['Мама', 'врач.']);
  check('tire oldidan jimlik uzayadi', p[0].pause >= 300, 'pause=' + p[0].pause);
}

/* =========================================================
   3. So'z holati (wordstate.js)
   ========================================================= */
{
  /* localStorage Node'da yo'q — eng sodda o'rnini bosuvchi.
     Modul faqat get/set/removeItem ishlatadi. */
  const store = {};
  const fakeLS = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; }
  };
  const win = { localStorage: fakeLS };
  const code = fs.readFileSync(path.join(ROOT, 'assets/js/core/wordstate.js'), 'utf8');
  new Function('window', 'localStorage', code)(win, fakeLS);
  const ws = win.WordState;

  const W = 'слово';
  check('boshida belgi yo\'q', !ws.isMastered(W) && !ws.isSaved(W));

  ws.toggleSaved(W);
  check('saqlash ishlaydi', ws.isSaved(W));

  ws.toggleMastered(W);
  check('o\'rgandim yoqiladi', ws.isMastered(W));
  // Ikkisi bir vaqtda yoqilmasligi kerak: o'rganib bo'lingan so'z
  // "hozir o'rganyapman" ro'yxatida turishi mantiqsiz.
  check('o\'rgandim saqlanganni o\'chiradi', !ws.isSaved(W));

  /* ENG MUHIM SHART: o'rganilgan so'z mashqqa TUSHMAYDI.
     Aynan shu narsa "galichka" ning ma'nosi. */
  const left = ws.forPractice([{ ru: W }, { ru: 'другое' }]).map((x) => x.ru);
  eq('o\'rganilgan so\'z mashqdan chiqadi', left, ['другое']);

  ws.setColor(W, '#ef4444');
  eq('rang saqlanadi', ws.colorOf(W), '#ef4444');
  eq('rang guruhga tushadi', ws.byColor()['#ef4444'], [W]);

  ws.setColor(W, '');
  eq('rang olib tashlanadi', ws.colorOf(W), '');

  // Eski kalit formati saqlanganmi — mavjud ma'lumot yo'qolmasligi uchun
  check('eski localStorage kaliti ishlatiladi',
    'vocab_mastered_v1' in store, Object.keys(store).join(','));
}

/* =========================================================
   3. Lug'at .md parseri — boyitilgan maydonlar (2026-09-01)
   ========================================================= */
{
  const parse = loadMdParser();
  const md = [
    '# Test',
    '',
    '## 1. объяснять — tushuntirmoq',
    '',
    '> Turkum: fe\'l (NSV)',
    '',
    '> Talaffuz: объясня\u0301ть',
    '',
    '> Shakllar: я объясняю, ты объясняешь',
    '',
    '> Sinonim: растолковывать (tushuntirib bermoq)',
    '',
    '> Antonim: скрывать (yashirmoq)',
    '',
    '> Birikma: объяснять материал — mavzuni tushuntirmoq',
    '',
    '> Eslab qolish: "ясно" so\'zi ichida yashiringan',
    '',
    '> Misol: Учитель объяснил тему.',
    '',
    '## 2. для — uchun',
    '',
    '> Turkum: predlog',
    '',
    '> Eslab qolish: otdan oldin keladi',
    ''
  ].join('\n');

  const cats = parse(md, 'Yangi lug\'at');
  const words = cats[0].words;

  check('.md dan 2 ta so\'z o\'qildi', words.length === 2, words.length);

  const w1 = words[0];
  eq('Turkum o\'qildi', w1.partOfSpeech, 'fe\'l (NSV)');
  eq('Talaffuz o\'qildi (urg\'u belgisi bilan)', w1.pronunciation, 'объясня\u0301ть');
  eq('Shakllar o\'qildi', w1.forms, 'я объясняю, ты объясняешь');
  eq('Sinonim o\'qildi (tarjima bilan)', w1.synonyms, 'растолковывать (tushuntirib bermoq)');
  eq('Antonim o\'qildi', w1.antonyms, 'скрывать (yashirmoq)');
  eq('Birikma o\'qildi', w1.collocations, 'объяснять материал — mavzuni tushuntirmoq');
  eq('Eslab qolish o\'qildi', w1.mnemonic, '"ясно" so\'zi ichida yashiringan');
  eq('Misol hamon ishlaydi (eski maydon)', w1.ex, 'Учитель объяснил тему.');

  // Yordamchi so'z: faqat 2 ta maydon yozilgan, qolganlari BO'SH qolishi kerak —
  // "moslashuvchan yoz" qoidasi majburlash emasligini tasdiqlaydi.
  const w2 = words[1];
  eq('Yordamchi so\'zda Turkum bor', w2.partOfSpeech, 'predlog');
  eq('Yordamchi so\'zda Eslab qolish bor', w2.mnemonic, 'otdan oldin keladi');
  check('Yordamchi so\'zda Shakllar BO\'SH (majburlanmagan)', w2.forms === '', w2.forms);
  check('Yordamchi so\'zda Sinonim BO\'SH (majburlanmagan)', w2.synonyms === '', w2.synonyms);
  check('Yordamchi so\'zda Talaffuz BO\'SH (majburlanmagan)', w2.pronunciation === '', w2.pronunciation);
}

{
  // Eski .md fayllar (Chalkashadi/Ma'no guruhi/Misol, yangi maydonlarsiz)
  // yangi parser bilan ham ISHLASHI SHART — orqaga moslik.
  const parse = loadMdParser();
  const md = [
    '# Test',
    '',
    '## 1. слово — so\'z',
    '',
    '> Izoh: eski uslubdagi izoh',
    '',
    '> **Chalkashadi:** boshqa1, boshqa2',
    '',
    '> **Ma\'no guruhi:** namuna',
    ''
  ].join('\n');
  const words = parse(md, 'X')[0].words;
  eq('eski Chalkashadi hamon ishlaydi', words[0].pairWith, ['boshqa1', 'boshqa2']);
  eq('eski Ma\'no guruhi hamon ishlaydi', words[0].meaningGroup, 'namuna');
  /* "Izoh:" hech qachon maxsus ishlanmagan — u boshqa hech qanday
     direktivga mos kelmagani uchun generic "note" ichiga SO'ZMA-SO'Z
     (yorlig'i bilan birga) tushadi. Bu eskidan shunday ishlagan. */
  eq('eski Izoh hamon ishlaydi (yorlig\'i bilan)', words[0].note, 'Izoh: eski uslubdagi izoh');
  check('yangi maydonlar bo\'sh (fayl yozmagan)', words[0].mnemonic === '' && words[0].forms === '',
    JSON.stringify(words[0]));
}

/* =========================================================
   5. `Yasalishi:` — so'z qanday yasalgani (2026-09-02)
   =========================================================
   Bu qator "Batafsil" panelida ko'rsatiladi. Qo'shilishidan OLDIN u
   hech qanday direktivga mos kelmagani uchun generic `note` ichiga
   tushib ketardi — ya'ni Reels'ning asosiy izoh maydonini ifloslantirardi.
   Shuning uchun ikki narsa tekshiriladi: maydonga tushishi VA note'ga
   TUSHMASLIGI. */
{
  const parse = loadMdParser();
  const md = [
    '# Test',
    '',
    '## 1. приходить — kelmoq',
    '',
    '> Qayerda: piyoda kelish haqida',
    '',
    '> Yasalishi: при- (yaqinlashmoq) + ходить (yurmoq)',
    '',
    '## 2. вокзал — vokzal',
    '',
    '> **Yasalishi:** ingliz "Vauxhall" — Londondagi bekat nomi',
    '',
    '## 3. дом — uy',
    '',
    '> Qayerda: turar joy',
    ''
  ].join('\n');

  const words = parse(md, 'X')[0].words;

  eq('Yasalishi o\'qildi (oddiy yorliq)', words[0].formation,
     'при- (yaqinlashmoq) + ходить (yurmoq)');
  eq('Yasalishi o\'qildi (qalin yorliq)', words[1].formation,
     'ingliz "Vauxhall" — Londondagi bekat nomi');

  // Eng muhimi: yorliq note ichiga SIZIB O'TMASLIGI kerak.
  eq('Yasalishi note ichiga tushmadi', words[0].note, 'Qayerda: piyoda kelish haqida');
  eq('faqat Yasalishi bo\'lsa note BO\'SH qoladi', words[1].note, '');

  // Tub so'zda bu qator YO'Q — qo'llanma "yozma" deydi, bo'sh qolishi normal.
  check('yozilmagan bo\'lsa bo\'sh', words[2].formation === '', words[2].formation);
}

/* =========================================================
   6. Lug'at qulfi (2026-09-02)
   =========================================================
   Qulfning ikki tomoni bor va IKKALASI ham to'g'ri bo'lishi shart:
     - qulflangan bo'lim ochilmasin;
     - qoidada YOZILMAGAN lug'at qulflanib QOLMASIN.
   Ikkinchisi muhimroq: "ro'yxatda yo'q hamma narsa qulf" degan qoida
   yangi lug'at qo'shilganda uni jimgina yo'q qilib qo'yardi. */
{
  const path = require('path');
  const prev = { window: global.window, localStorage: global.localStorage,
                 addEventListener: global.addEventListener };
  global.window = global;
  global.localStorage = { _d: {}, getItem(k) { return this._d[k] || null; },
                          setItem(k, v) { this._d[k] = v; }, removeItem(k) { delete this._d[k]; } };
  global.addEventListener = function () {};
  delete require.cache[require.resolve('../assets/js/core/lock.js')];
  require('../assets/js/core/lock.js');
  const L = global.window.WordLock;

  check('1-8000 ildiziga kirsa bo\'ladi (ichida 1-1000 ochiq)', L.isLocked('1-8000') === false);
  check('1-1000 ostidagi lug\'at ochiq', L.isLocked('1-8000/1-1000/301-400') === false);
  check('1001-2000 qulf', L.isLocked('1-8000/1001-2000') === true);
  check('7001-8000 ostidagisi qulf', L.isLocked('1-8000/7001-8000/7101-7200') === true);
  check('Тематический ildiziga kirsa bo\'ladi', L.isLocked('Тематический 9000') === false);
  check('ОСНОВНЫЕ ПОНЯТИЯ ostidagi mavzu ochiq',
        L.isLocked('Тематический 9000/ОСНОВНЫЕ ПОНЯТИЯ/часть 1/14. Цвета') === false);
  check('ЧЕЛОВЕК ostidagi mavzu qulf',
        L.isLocked('Тематический 9000/ЧЕЛОВЕК/питание/44. Продукты') === true);

  // Qoidada yo'q lug'atlar — TEGILMASIN
  check('229 lik lug\'at ochiq qoladi', L.isLocked('Глаголы настоящего времени') === false);
  check('Возвратные глаголы ochiq qoladi', L.isLocked('Возвратные глаголы') === false);
  /* DIQQAT: ingliz lug'ati ham `1-8000/...` yo'lidan foydalanadi, ya'ni
     qoida unga HAM tegadi — ingliz 1001+ boblari ham qulflangan. Qulf yo'l
     bo'yicha ishlaydi, til bo'yicha emas. Buni ochiq yozib qo'yamiz, aks
     holda "ingliz tegilmagan" degan noto'g'ri taassurot qolardi. */
  check('ingliz 1-1000 ham ochiq', L.isLocked('1-8000/1-1000/1-100') === false);
  check('ingliz 1001+ ham qulf (yo\'l bo\'yicha, til emas)',
        L.isLocked('1-8000/2001-3000') === true);
  check('qoidasiz nomdagi lug\'at ochiq', L.isLocked('Yangi lug\'at') === false);

  const pool = [
    { ru: 'a', cat: '1-8000/1-1000/1-100' },
    { ru: 'b', cat: '1-8000/5001-6000/5101-5200' },
    { ru: 'c', cat: 'Тематический 9000/ОСНОВНЫЕ ПОНЯТИЯ/часть 1/14. Цвета' },
    { ru: 'd', cat: 'Тематический 9000/ПРИРОДА/фауна/210. Млекопитающие' },
    { ru: 'e', cat: 'Глаголы настоящего времени' }
  ];
  eq('havzadan qulflanganlar chiqib ketdi', L.filterWords(pool).length, 3);

  L.setOpen('Тематический 9000/ПРИРОДА', true);
  eq('bo\'lim ochilgach havzaga qaytdi', L.filterWords(pool).length, 4);
  L.setOpen('Тематический 9000/ПРИРОДА', false);
  check('qaytib yopildi', L.isLocked('Тематический 9000/ПРИРОДА') === true);

  check('boshlang\'ich ochiq bo\'limni yopib bo\'lmaydi', L.isFixedOpen('1-8000/1-1000') === true);

  global.window = prev.window;
  global.localStorage = prev.localStorage;
  global.addEventListener = prev.addEventListener;
}

/* =========================================================
   7. "Hammasi" rejimi (2026-09-02)
   =========================================================
   Yoqilganda mashq oraliqni ham, "o'rgandim" belgisini ham e'tiborga
   olmasligi kerak. Ikkalasi bitta `rangedWords()` ichida, shuning uchun
   biri tuzalib ikkinchisi qolib ketishi mumkin edi. */
{
  const L = fs.readFileSync(path.join(ROOT, 'assets/js/app2/vocab.js'), 'utf8').split('\n');
  /* Qator raqamiga bog'lanmaymiz — fayl o'zgarganda test jimgina buzilardi. */
  function grab(head) {
    const a = L.findIndex((l) => l.startsWith(head));
    if (a < 0) throw new Error('topilmadi: ' + head);
    for (let i = a + 1; i < L.length; i++) if (L[i] === '  }') return L.slice(a, i + 1).join('\n');
    throw new Error('oxiri topilmadi: ' + head);
  }
  const parts = [
    "  function rangeKey(lang, cat) { return lang + '::' + cat; }",
    grab('  function allModeAll()'),
    L.find((l) => l.startsWith('  var ALL_KEY')),
    L.find((l) => l.startsWith('  function isAllMode')),
    grab('  function setAllMode('),
    grab('  function rangedWords(')
  ].join('\n');

  const prevLS = global.localStorage;
  global.localStorage = { _d: {}, getItem(k) { return this._d[k] || null; },
                          setItem(k, v) { this._d[k] = v; }, removeItem(k) { delete this._d[k]; } };
  const sc = {};
  new Function('e', 'localStorage',
    'var V = { data: {} };\nvar window = {};\n' +
    'function getRange(){ return { from: 21, to: 100 }; }\n' + parts + '\n' +
    'e.isAllMode=isAllMode; e.setAllMode=setAllMode; e.rangedWords=rangedWords; e.V=V;'
  )(sc, global.localStorage);

  sc.V.data['X'] = Array.from({ length: 229 }, (_, i) => ({ ru: 'w' + i }));

  check('boshida "Hammasi" o\'chiq', sc.isAllMode('russian', 'X') === false);
  eq('o\'chiq: faqat oraliq (21-100)', sc.rangedWords('russian', 'X').length, 80);
  sc.setAllMode('russian', 'X', true);
  eq('yoqiq: butun lug\'at', sc.rangedWords('russian', 'X').length, 229);
  check('boshqa kategoriyaga tegmaydi', sc.isAllMode('russian', 'Y') === false);
  sc.setAllMode('russian', 'X', false);
  eq('qaytib o\'chdi', sc.rangedWords('russian', 'X').length, 80);

  global.localStorage = prevLS;
}

/* =========================================================
   8. Filtrdagi lug'atlar ro'yxati dinamik (2026-09-02)
   =========================================================
   Ro'yxat kodda yozilgan edi: yangi lug'at qo'shilsa filtrda ko'rinmasdi,
   o'chirilgani esa qolib ketardi. Endi u so'zlar havzasidan o'sadi.

   Eng nozik joyi: rus va ingliz lug'atlari BIR XIL `1-8000/...` yo'lidan
   foydalanadi. Kalitga til qo'shilmasa ikkalasi bitta qatorga qo'shilib
   ketardi va "Ingliz 1-1000" ni alohida tanlab bo'lmasdi. */
{
  const L = fs.readFileSync(path.join(ROOT, 'assets/js/app2/home.js'), 'utf8').split('\n');
  function grab(head) {
    const a = L.findIndex((l) => l.startsWith(head));
    if (a < 0) throw new Error('topilmadi: ' + head);
    for (let i = a + 1; i < L.length; i++) if (L[i] === '  }') return L.slice(a, i + 1).join('\n');
    throw new Error('oxiri topilmadi: ' + head);
  }
  const a = L.findIndex((l) => l.startsWith('  var LEGACY_CATEGORIES = {'));
  let legacy = null;
  for (let i = a; i < L.length; i++) if (L[i] === '  };') { legacy = L.slice(a, i + 1).join('\n'); break; }

  const sc = {};
  new Function('e',
    'var LOADED_WORDS_POOL = [];\nvar FALLBACK_WORDS = [];\n' + legacy + '\n' +
    grab('  function getAvailableCats()') + '\n' + grab('  function resolveCatKey(') + '\n' +
    'e.set=function(p){LOADED_WORDS_POOL=p;};e.cats=getAvailableCats;e.resolve=resolveCatKey;'
  )(sc);

  const pool = [];
  for (let i = 0; i < 1000; i++) pool.push({ lang: 'russian', cat: '1-8000/1-1000/1-100' });
  for (let i = 0; i < 500; i++)  pool.push({ lang: 'english', cat: '1-8000/1-1000/1-100' });
  for (let i = 0; i < 229; i++)  pool.push({ lang: 'russian', cat: 'Глаголы настоящего времени' });
  for (let i = 0; i < 300; i++)  pool.push({ lang: 'russian', cat: 'Тематический 9000/ОСНОВНЫЕ ПОНЯТИЯ/часть 1/14. Цвета' });
  sc.set(pool);

  const opts = sc.cats();
  eq('havzadan 4 ta lug\'at topildi', opts.length, 4);
  eq('rus va ingliz 1-1000 ALOHIDA qator', opts.filter((o) => o.name === '1-1000').length, 2);
  eq('eng ko\'p so\'zlisi birinchi', opts[0].count, 1000);
  eq('daraja: ildiz ostidagi birinchi bo\'lak',
     opts.find((o) => o.root === 'Тематический 9000').name, 'ОСНОВНЫЕ ПОНЯТИЯ');

  // Eski saqlangan tanlov yo'qolib ketmasin
  eq('eski ru_1000 tarjima qilindi', sc.resolve('ru_1000'), 'russian|1-8000/1-1000');
  eq('eski en_8000 tarjima qilindi', sc.resolve('en_8000'), 'english|1-8000');
  eq('yangi kalit ochiladi', sc.resolve('cat:russian|X'), 'russian|X');
  check('"all" -> filtrsiz', sc.resolve('all') === null);
  check('notanish kalit -> filtrsiz', sc.resolve('yoq_bunday') === null);

  // Qo'shildi / o'chirildi
  sc.set(pool.concat([{ lang: 'russian', cat: 'Yangi lug\'at' }]));
  check('yangi lug\'at o\'zi chiqdi', sc.cats().some((o) => o.name === 'Yangi lug\'at'));
  sc.set(pool.filter((w) => w.cat !== 'Глаголы настоящего времени'));
  check('o\'chirilgan lug\'at yo\'qoldi',
        sc.cats().some((o) => o.name === 'Глаголы настоящего времени') === false);
}

/* =========================================================
   9. "O'qib bo'ldim" belgilari va navbatdagi bo'lim (2026-09-03)
   =========================================================
   Foydalanuvchining aniq misoli: 1-bob "o'qib bo'ldim" qilinsa, 2-bobning
   birinchi mavzusi navbatdagi bo'lib yonishi kerak. */
{
  const prevLS = global.localStorage, prevW = global.window, prevA = global.addEventListener;
  global.window = global;
  global.localStorage = { _d: {}, getItem(k) { return this._d[k] || null; },
                          setItem(k, v) { this._d[k] = v; }, removeItem(k) { delete this._d[k]; } };
  global.addEventListener = function () {};
  delete require.cache[require.resolve('../assets/js/core/readmark.js')];
  require('../assets/js/core/readmark.js');
  const R = global.ReadMark;

  const bob1 = ['t1', 't2', 't3'], bob2 = ['t4', 't5'], bob3 = ['t6'];
  const chapters = () => [R.folderDone('coding', '01-bob', bob1),
                          R.folderDone('coding', '02-bob', bob2),
                          R.folderDone('coding', '03-bob', bob3)];

  check('boshida hech narsa belgilanmagan', R.isRead('coding', 'folder', '01-bob') === false);

  R.setRead('coding', 'folder', '01-bob', true);
  eq('1-bob o\'qildi, qolgani yo\'q', chapters(), [true, false, false]);
  eq('navbatdagi — 2-bob', R.nextIndex(chapters()), 1);
  eq('2-bobning BIRINCHI mavzusi navbatda',
     R.nextIndex(bob2.map((id) => R.isRead('coding', 'topic', id))), 0);

  /* Mavzular birma-bir belgilansa, bob O'ZI yopilishi kerak — aks holda
     hamma mavzusi o'qilgan bob "tugallanmagan" bo'lib turaverardi. */
  R.setRead('coding', 'topic', 't4', true);
  check('bitta mavzu — bob hali tugamagan', R.folderDone('coding', '02-bob', bob2) === false);
  R.setRead('coding', 'topic', 't5', true);
  check('hamma mavzu — bob tugadi', R.folderDone('coding', '02-bob', bob2) === true);
  eq('navbat 3-bobga o\'tdi', R.nextIndex(chapters()), 2);

  R.setRead('coding', 'folder', '01-bob', false);
  eq('belgi olingach 1-bob yana navbatda', R.nextIndex(chapters()), 0);

  /* Kalitga til/kurs kiradi: bir xil nomli bob ikki kursda bo'lishi mumkin. */
  R.setRead('russian', 'folder', '01-bob', true);
  check('boshqa kursga o\'tmaydi', R.isRead('coding', 'folder', '01-bob') === false);
  check('o\'z kursida turibdi', R.isRead('russian', 'folder', '01-bob') === true);

  eq('hammasi o\'qilgan — navbat yo\'q', R.nextIndex([true, true, true]), -1);
  check('mavzusiz bob tugagan hisoblanmaydi', R.folderDone('coding', 'X', []) === false);

  global.localStorage = prevLS; global.window = prevW; global.addEventListener = prevA;
}

/* =========================================================
   10. Kod bo'yash (2026-09-03)
   =========================================================
   Ikki narsa muhim va ikkalasi ham jimgina buzilishi mumkin edi:

   1) XAVFSIZLIK — bo'yash xom matn ustida ishlaydi, ya'ni HTML har
      bo'lak uchun ALOHIDA qochirilishi shart. Aks holda darslikdagi
      `<script>` haqiqiy tegga aylanardi.
   2) GURUH RAQAMLARI — qoidalar ichida o'z qamrab oluvchi guruhlari
      bo'lishi mumkin. Ular sanalmasa indekslar suriladi va bo'lakka
      BOSHQA qoida nomi berilardi (`import` "satr" deb bo'yalgandi). */
{
  const prevW = global.window;
  global.window = global;
  delete require.cache[require.resolve('../assets/js/core/hilite.js')];
  require('../assets/js/core/hilite.js');
  const H = global.Hilite;

  // --- Xavfsizlik ---
  const evil = H.code('python', '<script>alert(1)</script>');
  check('kod ichidagi <script> teg bo\'lib qolmaydi', evil.indexOf('<script>') < 0);
  check('u qochirilgan holda ko\'rinadi', evil.indexOf('&lt;script&gt;') >= 0);
  check('satr ichidagi teg ham qochiriladi',
        H.code('python', 'x = "<img onerror=1>"').indexOf('<img') < 0);

  // --- Guruh raqamlari (aynan tutilgan nosozlik) ---
  const py = H.code('python',
    'from django.test import TestCase\nclass T(TestCase):\n' +
    '    def f(self):\n        x = Mahsulot.objects.create(nomi="Non", narxi=5000)  # izoh');
  check('kalit so\'z bo\'yaldi', /class="hl-kw">from</.test(py));
  check('son bo\'yaldi', /class="hl-num">5000/.test(py));
  check('satr bo\'yaldi', /class="hl-str">"Non"/.test(py));
  check('izoh bo\'yaldi', /class="hl-com"># izoh/.test(py));

  // --- Izoh/satr ichida kalit so'z bo'yalmasin ---
  eq('izoh ichidagi kalit so\'z tegilmaydi',
     (H.code('python', '# import bu yerda kalit emas').match(/hl-kw/g) || []).length, 0);
  eq('satr ichidagi kalit so\'z tegilmaydi',
     (H.code('python', 'x = "class def import"').match(/hl-kw/g) || []).length, 0);

  // --- Boshqa tillar ---
  check('bash o\'zgaruvchisi', /hl-var">\$HOME/.test(H.code('bash', 'export P=$HOME/bin')));
  check('sql kichik harfda ham', /hl-kw">select/.test(H.code('sql', 'select * from t')));
  check('sql katta harfda ham', /hl-kw">SELECT/.test(H.code('sql', 'SELECT * FROM t')));
  check('taxallus: py -> python', /hl-kw">import/.test(H.code('py', 'import os')));
  check('notanish til yiqilmaydi', typeof H.code('klingon', 'a = 1 # b') === 'string');
  eq('bo\'sh kod', H.code('python', ''), '');

  // --- Matn yo'qolmasligi ---
  const src = 'def f(x):\n    return x + 1  # qo\'shish\n';
  const back = H.code('python', src).replace(/<[^>]+>/g, '')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
  eq('birorta belgi yo\'qolmadi', back, src);

  global.window = prevW;
}

/* =========================================================
   Natija
   ========================================================= */
console.log('');
if (fail === 0) {
  console.log('  ' + pass + ' ta test o\'tdi.');
  process.exit(0);
}
console.log('  ' + pass + ' o\'tdi, ' + fail + ' YIQILDI:');
failures.forEach((f) => console.log('   - ' + f));
process.exit(1);
