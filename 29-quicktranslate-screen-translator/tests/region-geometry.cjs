// Maydon geometriyasi: sudrash yo'nalishi, ekran chegarasi va tasodifiy
// bosishni ajratish.
//
// Ishga tushirish: node tests/region-geometry.cjs

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

let source = fs.readFileSync(path.join(__dirname, '../region-geometry.js'), 'utf8')
    .replace(/export function /g, 'function ')
    .replace(/export const /g, 'const ');
source += '\nmodule.exports = { normalizeRect, clampRect, isUsableRegion, MIN_REGION_SIZE };';
const sandbox = {module: {exports: {}}, Math, Number, Boolean};
vm.runInNewContext(source, sandbox, {filename: 'region-geometry.js'});
const {normalizeRect, clampRect, isUsableRegion, MIN_REGION_SIZE} = sandbox.module.exports;

const SCREEN = {width: 1920, height: 1080};

// --- 1. Sudrash har tomonga ishlaydi ---
// Foydalanuvchi o'ngdan chapga yoki pastdan yuqoriga sudrashi mumkin;
// kenglik va balandlik hech qachon manfiy bo'lmasligi kerak.

const expected = {x: 100, y: 200, width: 300, height: 150};
const drags = {
    "chapdan o'ngga, yuqoridan pastga": [100, 200, 400, 350],
    "o'ngdan chapga, pastdan yuqoriga": [400, 350, 100, 200],
    "o'ngdan chapga, yuqoridan pastga": [400, 200, 100, 350],
    "chapdan o'ngga, pastdan yuqoriga": [100, 350, 400, 200],
};
for (const [name, [x1, y1, x2, y2]] of Object.entries(drags)) {
    assert.deepEqual({...normalizeRect(x1, y1, x2, y2)}, expected, `${name}: noto'g'ri`);
}

// Kasr koordinatalar yaxlitlanadi (piksel butun bo'lishi kerak).
assert.deepEqual({...normalizeRect(10.4, 20.6, 30.5, 40.2)},
    {x: 10, y: 21, width: 20, height: 20});

// Bosib qo'yib yuborish — nol o'lchamli maydon, lekin manfiy emas.
assert.deepEqual({...normalizeRect(50, 50, 50, 50)}, {x: 50, y: 50, width: 0, height: 0});

// --- 2. Ekran chegarasidan chiqmaydi ---
// Chegaradan tashqaridagi koordinata bilan rasm kesish xatoga olib kelardi.

assert.deepEqual({...clampRect({x: 1800, y: 1000, width: 500, height: 500}, SCREEN)},
    {x: 1800, y: 1000, width: 120, height: 80}, "O'ng-past burchakda qisilishi kerak");

assert.deepEqual({...clampRect({x: -50, y: -30, width: 200, height: 100}, SCREEN)},
    {x: 0, y: 0, width: 200, height: 100}, 'Manfiy koordinata nolga keltiriladi');

assert.deepEqual({...clampRect({x: 0, y: 0, width: 5000, height: 5000}, SCREEN)},
    {x: 0, y: 0, width: 1920, height: 1080}, 'Butun ekrandan oshmasligi kerak');

// To'liq ekrandan tashqarida: o'lcham nolga tushadi, manfiy bo'lmaydi.
const outside = clampRect({x: 3000, y: 3000, width: 100, height: 100}, SCREEN);
assert.ok(outside.width >= 0 && outside.height >= 0, "O'lcham manfiy bo'lmasligi kerak");

// Chegaraviy holat: aynan ekran chetidan boshlanadi.
assert.deepEqual({...clampRect({x: 1920, y: 1080, width: 10, height: 10}, SCREEN)},
    {x: 1920, y: 1080, width: 0, height: 0});

// --- 3. Tasodifiy bosish maydon deb hisoblanmaydi ---

assert.equal(isUsableRegion(null), false, 'null maydon emas');
assert.equal(isUsableRegion({x: 0, y: 0, width: 0, height: 0}), false, 'Nol maydon emas');
assert.equal(isUsableRegion({x: 0, y: 0, width: 5, height: 100}), false,
    'Juda tor maydon qabul qilinmasligi kerak');
assert.equal(isUsableRegion({x: 0, y: 0, width: 100, height: 5}), false,
    'Juda past maydon qabul qilinmasligi kerak');

// Chegaraviy qiymat: aynan eng kichik o'lcham — qabul qilinadi.
assert.equal(isUsableRegion({x: 0, y: 0, width: MIN_REGION_SIZE, height: MIN_REGION_SIZE}), true);
assert.equal(
    isUsableRegion({x: 0, y: 0, width: MIN_REGION_SIZE - 1, height: MIN_REGION_SIZE}), false);

// --- 4. Haqiqiy oqim: sudrash -> qisish -> tekshirish ---
// Subtitr ustida ekran chetidan tashqariga chiqib ketgan sudrash.

const dragged = clampRect(normalizeRect(1850, 900, 2200, 1200), SCREEN);
assert.deepEqual({...dragged}, {x: 1850, y: 900, width: 70, height: 180});
assert.equal(isUsableRegion(dragged), true, 'Qisilgandan keyin ham yaroqli bo\'lishi kerak');

console.log('PASS: sudrash yo\'nalishi, ekran chegarasi, tasodifiy bosishni ajratish');
