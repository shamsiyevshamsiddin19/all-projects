// Karta tartibi qoidalari: manba matn tepada, matn hech qachon
// qisqartirilmaydi, kenglik matn uzunligiga bog'liq emas, balandlik esa
// ekranga qarab cheklanadi.
//
// Ishga tushirish: node tests/popup-layout.cjs

const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../popup.js'), 'utf8');

class Actor {
    constructor(props = {}) {
        Object.assign(this, {visible: true, children: [], handlers: {}, hover: false}, props);
        this.clutter_text = {connect: (name, callback) => this.handlers[name] = callback};
    }
    connect(name, fn) { this.handlers[name] = fn; return 1; }
    add_child(child) { this.children.push(child); }
    set_child(child) { this.children = [child]; }
    set_text(value) { this.text = value; }
    get_text() { return this.text || ''; }
    set_label(value) { this.label = value; }
    set_size() {}
    set_style(value) { this.style = value; }
    set_position(x, y) { this.position = [x, y]; }
    set_policy() {}
    add_constraint() {}
    ease() {}
    grab_key_focus() {}
    contains() { return false; }
    destroy_all_children() { this.children = []; }
    // Karta o'z balandligini shu orqali so'raydi; sinovda uni boshqarib turamiz.
    get_preferred_height() { return [0, this._naturalHeight ?? 420]; }
}

class Request { cancel() { this.cancelled = true; } is_cancelled() { return !!this.cancelled; } }
const hooks = {connectObject() {}, disconnectObject() {}};
const MONITOR = {x: 0, y: 0, width: 1920, height: 1080};

const context = {
    St: {BoxLayout: Actor, Widget: Actor, Button: Actor, Label: Actor, Entry: Actor,
        Icon: Actor, ScrollView: Actor, PolicyType: {NEVER: 0, AUTOMATIC: 1}},
    Clutter: {ActorAlign: {START: 0}, AnimationMode: {EASE_OUT_QUAD: 0},
        BindConstraint: Actor, BindCoordinate: {ALL: 0}},
    Pango: {WrapMode: {WORD_CHAR: 0}, EllipsizeMode: {NONE: 0, END: 3}},
    Shell: {ActionMode: {POPUP: 1}},
    GLib: {PRIORITY_DEFAULT: 0, timeout_add: () => 1, source_remove() {}},
    Gio: {Cancellable: Request}, global: {stage: {get_key_focus: () => null}},
    Main: {overview: hooks, sessionMode: hooks, layoutManager: {...hooks,
        primaryMonitor: MONITOR, monitors: [MONITOR], addTopChrome() {}}},
    GrabHelper: class { grab() { return true; } },
    Pronunciation: class { stop() {} },
    VocabularyStore: class { save() {} list() { return []; } },
    requestMultiTranslation: () => {},
    fetchOne: () => {},
};
vm.createContext(context);
vm.runInContext(source.replace(/^import .*;$/gm, '').replace('export class', 'class') +
    ';this.Popup=QuickTranslatePopup;this.CARD_WIDTH=CARD_WIDTH;' +
    'this.CARD_MIN_HEIGHT=CARD_MIN_HEIGHT;', context);

const {CARD_WIDTH, CARD_MIN_HEIGHT} = context;

/** bodyBox — ScrollView ichidagi yagona bola. */
function bodyOf(popup) {
    for (const child of popup.actor.children) {
        if (child.children.length === 1 && child.children[0].children.length > 1)
            return child.children[0];
    }
    throw new Error('bodyBox topilmadi');
}

// --- 1. Manba matn eng tepada, tarjima satrlaridan OLDIN ---

const short = new context.Popup(500, 500, 'Только дыхание переведу.');
const body = bodyOf(short);

assert.equal(body.children[0], short.origLabel,
    'Tarjima qilinayotgan matn kartaning eng tepasida turishi kerak');
assert.ok(body.children.indexOf(short.row1) > body.children.indexOf(short.origLabel),
    'Birinchi tarjima satri manba matndan KEYIN kelishi kerak');
assert.ok(body.children.indexOf(short.row2) > body.children.indexOf(short.row1),
    'Ikkinchi tarjima satri birinchisidan keyin kelishi kerak');

// --- 2. Uzun matn qisqartirilmaydi ---

const longSource = ('Господи, души. Они были нашими друзьями и мы должны были ' +
    'защитить их любой ценой, но всё пошло совсем не так как планировалось. ').repeat(4).trim();
assert.ok(longSource.length > 300, 'Sinov matni yetarlicha uzun bo\'lishi kerak');

const long = new context.Popup(500, 500, longSource);
assert.equal(long.origLabel.text, longSource.replace(/\s+/g, ' '),
    'Manba matn to\'liq ko\'rsatilishi kerak — kesilmasin va "..." qo\'shilmasin');
assert.ok(!long.origLabel.text.endsWith('...'),
    'Matn oxiriga "..." qo\'yilmasligi kerak');
assert.equal(long.origLabel.clutter_text.ellipsize, context.Pango.EllipsizeMode.NONE,
    'Manba matnda ellipsize o\'chirilgan bo\'lishi kerak');
assert.equal(long.origLabel.clutter_text.line_wrap, true,
    'Manba matn satrlarga o\'ralishi kerak');

// --- 3. Tarjima satrlari ham kesilmaydi ---
// Ellipsize line_wrap'dan ustun keladi, shuning uchun aniq NONE bo'lishi shart.

for (const [name, label] of [['trans1', long.trans1], ['trans2', long.trans2]]) {
    assert.equal(label.clutter_text.line_wrap, true, `${name}: o'ralishi kerak`);
    assert.equal(label.clutter_text.ellipsize, context.Pango.EllipsizeMode.NONE,
        `${name}: ellipsize o'chirilgan bo'lishi kerak`);
}

// --- 4. Kenglik matn uzunligiga BOG'LIQ EMAS ---
// Aks holda karta har matnda o'lchamini o'zgartirib, kursor yonida sakrardi.

assert.equal(short.actor.width, CARD_WIDTH);
assert.equal(long.actor.width, CARD_WIDTH, 'Uzun matnda ham kenglik o\'zgarmasligi kerak');
assert.ok(short.actor.style.includes(`max-width: ${CARD_WIDTH}px`));

// --- 5. Balandlik ekranga qarab cheklanadi, 300px ga qotirilmagan ---

const expectedMax = Math.max(CARD_MIN_HEIGHT, Math.round(MONITOR.height * 0.6));
assert.equal(long._maxHeight, expectedMax,
    `Eng katta balandlik monitordan hisoblanishi kerak (${expectedMax}px)`);
assert.ok(long._maxHeight > CARD_MIN_HEIGHT,
    'Karta eng kichik balandlikdan o\'sa olishi kerak');
assert.ok(short.actor.style.includes(`min-height: ${CARD_MIN_HEIGHT}px`));
assert.ok(short.actor.style.includes(`max-height: ${expectedMax}px`));
assert.ok(!short.actor.style.includes('max-height: 300px'),
    'Balandlik 300px ga qotirilmagan bo\'lishi kerak');

// --- 6. Joylashuv kartaning HAQIQIY balandligini hisobga oladi ---
// Qotirilgan 300 bilan hisoblansa, o'sgan karta ekran pastidan chiqib ketardi.

const tall = new context.Popup(960, 1000, 'matn');
tall.actor._naturalHeight = 900;      // max (648) dan baland
tall._positionWidget();
const [, posY] = tall.actor.position;
assert.ok(posY + expectedMax <= MONITOR.height - 20,
    `Karta ekran pastidan chiqmasligi kerak (y=${posY}, h=${expectedMax})`);
assert.ok(posY >= MONITOR.y + 36, 'Karta ekran tepasidan ham chiqmasligi kerak');

console.log('PASS: manba matn tepada, kesilmaydi, kenglik qat\'iy, balandlik moslashuvchan');
