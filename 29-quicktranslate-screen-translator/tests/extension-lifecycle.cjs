// extension.js ning hayot sikli: yorliqlarni ro'yxatga olish, tarjima
// so'rovi, popup almashinuvi, disable'da tozalash — va qotirish yo'lida
// media pauzasining tarjima kartasi yopilgunicha saqlanishi.
//
// Ishga tushirish: node tests/extension-lifecycle.cjs

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let source = fs.readFileSync(path.join(__dirname, '../extension.js'), 'utf8')
    .replace(/^import .*;$/gm, '')
    .replace('export default class QuickTranslateExtension', 'class QuickTranslateExtension');
source += '\nthis.QuickTranslateExtension = QuickTranslateExtension;';

/** Barcha addKeybinding/removeKeybinding chaqiruvlari — oxirgisi emas. */
const added = [];
const removed = [];
let selectionCallback = null;
let translationCallback = null;
let cancelled = 0;

class Cancellable {
    cancel() { this.cancelled = true; cancelled++; }
    is_cancelled() { return Boolean(this.cancelled); }
}

class Popup {
    constructor(x, y, text) { Object.assign(this, {x, y, text, _destroyed: false}); }
    startRequest(request) { this.request = request; return true; }
    setResult(result) { this.result = result; }
    setError(error) { this.error = error; }
    setOnClosed(callback) {
        if (this._destroyed) { callback?.(); return; }
        this._onClosed = callback;
    }
    destroy() {
        if (this._destroyed) return;
        this._destroyed = true;
        const notify = this._onClosed;
        this._onClosed = null;
        notify?.();
    }
}

/** FreezeOverlay o'rniga: faqat kuzatish uchun. */
class FreezeOverlayMock {
    constructor(onTranslate, getLanguages, getGlowEnabled) {
        Object.assign(this, {onTranslate, getLanguages, getGlowEnabled});
        this.isOpen = false;
        this.resumeCount = 0;
        this.destroyed = false;
    }
    resumeMedia() { this.resumeCount++; }
    destroy() { this.destroyed = true; }
}

class Extension {
    getSettings() {
        return {
            schema: true,
            get_string: key => (key === 'ocr-languages' ? 'rus+eng' : ''),
            get_boolean: () => true,
        };
    }
}

const context = {
    Extension,
    Gio: {Cancellable},
    Meta: {KeyBindingFlags: {NONE: 0}},
    Shell: {ActionMode: {NORMAL: 1, OVERVIEW: 2, POPUP: 4}},
    Main: {wm: {
        addKeybinding: (...args) => { added.push(args); return added.length; },
        removeKeybinding: name => { removed.push(name); },
    }},
    QuickTranslatePopup: Popup,
    FreezeOverlay: FreezeOverlayMock,
    getTruePointerCoords: () => [640, 360],
    getSelection: callback => { selectionCallback = callback; },
    requestMultiTranslation: (_text, callback) => { translationCallback = callback; },
    console: {warn() {}, error() {}},
};
vm.createContext(context);
vm.runInContext(source, context);

const extension = new context.QuickTranslateExtension();
extension.enable();

// --- 1. Ikki yorliq ham ro'yxatga olinadi ---

assert.equal(added.length, 2, 'Ikki yorliq kutilgan: toggle-popup va freeze-ocr');
assert.equal(added[0][0], 'toggle-popup');
assert.equal(added[0][3], 3, 'toggle-popup: NORMAL|OVERVIEW');
assert.equal(added[1][0], 'freeze-ocr');
assert.equal(added[1][3], 7, 'freeze-ocr: NORMAL|OVERVIEW|POPUP — overlay ochiqda ham ishlashi kerak');
assert.ok(extension._freeze, 'FreezeOverlay yaratilgan bo\'lishi kerak');

// Sozlama getter'lari to'g'ri ulangan.
assert.equal(extension._freeze.getLanguages(), 'rus+eng');
assert.equal(extension._freeze.getGlowEnabled(), true);

// --- 2. Ctrl+Alt+Z yo'li: belgilangan matnni tarjima qilish ---

extension._toggle();
assert(extension._selectionPending);
selectionCallback('Мой');
assert.equal(extension._popup.text, 'Мой');
translationCallback({src: 'RU', items: [{tag: 'UZ', text: 'Mening'}, {tag: 'EN', text: 'My'}]}, null);
assert.equal(extension._popup.result.src, 'RU');

// Belgilangan matn yo'lida karta yopilishi mediaga TEGMASLIGI kerak:
// bu yo'lda hech narsa pauzaga qo'yilmagan.
const resumesBefore = extension._freeze.resumeCount;
extension._popup.destroy();
assert.equal(extension._freeze.resumeCount, resumesBefore,
    'Ctrl+Alt+Z yo\'lida karta yopilishi mediani davom ettirmasligi kerak');

// --- 3. Popup almashinuvi ---

extension._popup = null;
extension._toggle();
selectionCallback('тест');
const oldPopup = extension._popup;
extension._toggle();
assert(oldPopup._destroyed, 'Yorliq qayta bosilganda eski karta yopiladi');
assert.equal(extension._popup, null);

// --- 4. OCR yo'li: karta yopilgandagina media davom etadi ---

extension._translateText('Привет мир');
const ocrPopup = extension._popup;
assert.equal(ocrPopup.text, 'Привет мир');
assert.equal(extension._freeze.resumeCount, 0,
    'Karta ochiq turganda media HALI davom etmasligi kerak');

ocrPopup.destroy();
assert.equal(extension._freeze.resumeCount, 1,
    'Karta yopilganda media aynan bir marta davom etishi kerak');

// --- 5. Karta setOnClosed'dan oldin yopilib qolgan holat ---
// Bu teshik bo'lsa video pauzada qolib ketardi.

extension._popup = null;
const stale = new Popup(0, 0, 'matn');
stale.destroy();
let resumedForStale = 0;
stale.setOnClosed(() => resumedForStale++);
assert.equal(resumedForStale, 1,
    'Allaqachon yopilgan kartada callback darhol ishlashi kerak');

// --- 6. disable() hammasini tozalaydi ---

extension._toggle();
const activeRequest = extension._request;
extension.disable();

assert.deepEqual(removed, ['toggle-popup', 'freeze-ocr'],
    'Ikki yorliq ham olib tashlanishi kerak');
assert(activeRequest.cancelled, 'Faol so\'rov bekor qilinadi');
assert.equal(extension._popup, null);
assert.equal(extension._freeze, null);
assert(cancelled >= 1);

console.log('PASS: ikki yorliq, so\'rov, popup almashinuvi, media pauzasi va disable');
