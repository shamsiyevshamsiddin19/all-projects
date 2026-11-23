// Tesseract TSV tahlilchisini sinaydi: avval sintetik chegaraviy holatlar,
// keyin HAQIQIY tesseract chiqishi (rasm generatsiya qilinib o'qitiladi).
//
// Ishga tushirish: node tests/tsv-parser.cjs

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const vm = require('node:vm');
const path = require('node:path');
const {execFileSync} = require('node:child_process');

let source = fs.readFileSync(path.join(__dirname, '../tsv-parser.js'), 'utf8')
    .replace(/export function /g, 'function ')
    .replace(/export const /g, 'const ');
source += '\nmodule.exports = { parseTsv, joinWords, MIN_CONFIDENCE };';
const sandbox = {module: {exports: {}}, Map, JSON, Error, String, Number, parseInt, parseFloat};
vm.runInNewContext(source, sandbox, {filename: 'tsv-parser.js'});
const {parseTsv, joinWords} = sandbox.module.exports;

// vm sandbox boshqa realm: undagi massivning prototipi boshqa, deepStrictEqual
// esa prototipni ham tekshiradi. Shuning uchun natijani host massiviga ko'chiramiz.
const host = iterable => [...iterable];

const HEADER = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext';
const row = (level, block, par, line, word, left, top, w, h, conf, text) =>
    [level, 1, block, par, line, word, left, top, w, h, conf, text].join('\t');

// --- 1. Chegaraviy holatlar (Black-box: BVA) ---

assert.deepEqual(host(parseTsv('')), [], "Bo'sh kirish bo'sh ro'yxat berishi kerak");
assert.deepEqual(host(parseTsv(null)), [], 'null yiqitmasligi kerak');
assert.deepEqual(host(parseTsv(HEADER)), [], 'Faqat sarlavha — so\'z yo\'q');

// Sarlavha qatori hech qachon so'z sifatida o'qilmasin.
assert.equal(parseTsv(`${HEADER}\n${row(5, 1, 1, 1, 1, 10, 20, 50, 18, 96, 'salom')}`).length, 1);

// level != 5 (blok, satr darajalari) tashlanadi.
assert.deepEqual(host(parseTsv(`${HEADER}\n${row(2, 1, 1, 1, 1, 0, 0, 500, 200, -1, '')}`)), []);

// Past ishonch tashlanadi, yuqorisi qoladi.
const confCases = parseTsv([HEADER,
    row(5, 1, 1, 1, 1, 10, 10, 40, 16, 39, 'shovqin'),
    row(5, 1, 1, 1, 2, 60, 10, 40, 16, 40, 'chegara'),
].join('\n'));
assert.deepEqual(host(confCases).map(w => w.text), ['chegara'], 'conf<40 tashlanadi, 40 qoladi');

// Nol yoki manfiy o'lchamli to'rtburchak tashlanadi (bo'linishga yo'l qo'ymaslik).
assert.deepEqual(host(parseTsv(`${HEADER}\n${row(5, 1, 1, 1, 1, 10, 10, 0, 16, 90, 'nol')}`)), []);

// Matn ichida tab bo'lsa ham yo'qolmasin.
assert.equal(parseTsv(`${HEADER}\n${row(5, 1, 1, 1, 1, 1, 1, 10, 10, 90, 'a\tb')}`)[0].text, 'a\tb');

// Bo'sh matnli so'z tashlanadi (tesseract ko'p beradi).
assert.deepEqual(host(parseTsv(`${HEADER}\n${row(5, 1, 1, 1, 1, 1, 1, 10, 10, 90, '   ')}`)), []);

// --- 2. Satr guruhlash va o'qish tartibi ---

const twoLines = parseTsv([HEADER,
    row(5, 1, 1, 1, 1, 10, 10, 40, 16, 90, 'birinchi'),
    row(5, 1, 1, 1, 2, 60, 10, 40, 16, 90, 'satr'),
    row(5, 1, 1, 2, 1, 10, 40, 40, 16, 90, 'ikkinchi'),
].join('\n'));
assert.deepEqual(host(twoLines).map(w => w.line), [0, 0, 1], 'block:par:line bir satrni aniqlaydi');
assert.deepEqual(host(twoLines).map(w => w.index), [0, 1, 2], "index o'qish tartibida ketadi");
assert.equal(joinWords(twoLines), 'birinchi satr\nikkinchi',
    'Satr ichi bo\'sh joy, satrlar orasi yangi qator');
assert.equal(joinWords([]), '', "Bo'sh tanlov bo'sh matn beradi");

// Turli bloklardagi bir xil line_num aralashmasligi kerak.
const twoBlocks = parseTsv([HEADER,
    row(5, 1, 1, 1, 1, 10, 10, 30, 16, 90, 'A'),
    row(5, 1, 2, 1, 1, 10, 90, 30, 16, 90, 'B'),
].join('\n'));
assert.deepEqual(host(twoBlocks).map(w => w.line), [0, 1], 'Har xil blok — har xil satr');
assert.equal(joinWords(twoBlocks), 'A\nB');

console.log('✓ Sintetik sinovlar: 14/14');

// --- 3. HAQIQIY tesseract (integratsiya sinovi) ---

function hasProgram(name) {
    try {
        execFileSync('sh', ['-c', `command -v ${name}`], {stdio: 'ignore'});
        return true;
    } catch {
        return false;
    }
}

if (!hasProgram('tesseract') || !hasProgram('convert')) {
    console.log('… Integratsiya sinovi tashlandi (tesseract yoki convert yo\'q)');
    process.exit(0);
}

const font = execFileSync('fc-match', ['Noto Sans', '-f', '%{file}'], {encoding: 'utf8'}).trim();
const image = path.join(os.tmpdir(), `qt-tsv-test-${process.pid}.png`);

try {
    // Subtitrga o'xshash ikki satr: ruscha va inglizcha.
    execFileSync('convert', [
        '-size', '900x220', 'xc:white',
        '-font', font, '-pointsize', '40', '-fill', 'black',
        '-annotate', '+40+80', 'Привет мир',
        '-annotate', '+40+170', 'Hello frozen world',
        image,
    ]);

    const tsv = execFileSync('tesseract', [image, 'stdout', '-l', 'rus+eng', '--psm', '3', 'tsv'],
        {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']});

    const words = parseTsv(tsv);
    const joined = joinWords(words);

    assert.ok(words.length >= 4, `Kamida 4 so'z kutilgan, topilgani: ${words.length} (${joined})`);

    // Har bir so'zning to'rtburchagi haqiqiy bo'lishi shart — Live Text
    // belgilash to'g'ridan-to'g'ri shu koordinatalarga tayanadi.
    for (const word of host(words)) {
        assert.ok(word.w > 0 && word.h > 0, `Yaroqsiz o'lcham: ${JSON.stringify(word)}`);
        assert.ok(word.x >= 0 && word.y >= 0, `Manfiy koordinata: ${JSON.stringify(word)}`);
        assert.ok(word.conf >= 40, `Past ishonch o'tib ketdi: ${JSON.stringify(word)}`);
    }

    // Ikki satr aniq ajralgan bo'lishi kerak.
    const lines = new Set(host(words).map(w => w.line));
    assert.ok(lines.size >= 2, `Ikki satr kutilgan, topilgani: ${lines.size} (${joined})`);
    assert.ok(joined.includes('\n'), 'Yig\'ilgan matnda satr ajratgichi bo\'lishi kerak');

    // Matn mazmuni: OCR 100% aniq bo'lmasligi mumkin, shuning uchun
    // kalit so'zlarning borligini yumshoq tekshiramiz.
    const lower = joined.toLowerCase();
    assert.ok(lower.includes('hello'), `Inglizcha so'z o'qilmadi: ${joined}`);
    assert.ok(/мир|привет/.test(lower), `Ruscha so'z o'qilmadi: ${joined}`);

    // Birinchi satr ikkinchisidan yuqorida turishi kerak (tartib to'g'ri).
    const firstLineY = Math.min(...host(words).filter(w => w.line === 0).map(w => w.y));
    const lastLineY = Math.min(...host(words).filter(w => w.line === lines.size - 1).map(w => w.y));
    assert.ok(firstLineY < lastLineY, "O'qish tartibi yuqoridan pastga bo'lishi kerak");

    console.log(`✓ Haqiqiy tesseract: ${words.length} so'z, ${lines.size} satr`);
    console.log(`  o'qilgan matn: ${JSON.stringify(joined)}`);
} finally {
    fs.rmSync(image, {force: true});
}

console.log('✓ Hammasi o\'tdi');
