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
  check('ingliz lug\'ati ochiq qoladi', L.isLocked('Ingliz tili') === false);

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
