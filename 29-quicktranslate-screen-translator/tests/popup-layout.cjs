// Karta tartibi qoidalari: o'lcham QAT'IY (480x300), matn sig'masa
// SHRIFT kichrayadi, manba matn tepada va hech qachon kesilmaydi.
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
    // Sinovda balandlikni boshqarib turamiz: `_heightFn` matn balandligini
    // joriy shrift miqyosiga bog'lash uchun ishlatiladi.
    get_preferred_height(forWidth) {
        return [0, this._heightFn ? this._heightFn(forWidth) : (this._naturalHeight ?? 0)];
    }
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
    'this.CARD_HEIGHT=CARD_HEIGHT;this.MIN_FONT_SCALE=MIN_FONT_SCALE;' +
    'this.PADDING_Y=PADDING_Y;this.TEXT_STYLES=TEXT_STYLES;', context);

const {CARD_WIDTH, CARD_HEIGHT, MIN_FONT_SCALE, PADDING_Y, TEXT_STYLES} = context;

/** Matn uchun qoladigan balandlik (sarlavha va pastki qator mockda 0). */
const AVAILABLE = CARD_HEIGHT - PADDING_Y * 2;

/** bodyBox — ScrollView ichidagi yagona bola. */
function bodyOf(popup) {
    for (const child of popup.actor.children) {
        if (child.children.length === 1 && child.children[0].children.length > 1)
            return child.children[0];
    }
    throw new Error('bodyBox topilmadi');
}

/**
 * Matni berilgan "tabiiy" balandlikka ega karta yasaydi.
 * Balandlik shrift miqyosiga proporsional — haqiqiy holatdagidek.
 */
function popupNeeding(baseHeight, text = 'sinov') {
    const popup = new context.Popup(500, 500, text);
    popup._bodyBox._heightFn = () => baseHeight * popup._fontScale;
    popup._fitTextToCard();
    return popup;
}

// --- 1. O'lcham QAT'IY: 480x300, matn uzunligidan qat'i nazar ---

const short = new context.Popup(500, 500, 'Только дыхание переведу.');
const longText = ('Господи, души. Они были нашими друзьями и мы должны были защитить их ' +
    'любой ценой, но всё пошло совсем не так как планировалось. ').repeat(4).trim();
const long = new context.Popup(500, 500, longText);

for (const [name, p] of [['qisqa', short], ['uzun', long]]) {
    assert.equal(p.actor.width, CARD_WIDTH, `${name}: kenglik o'zgarmasligi kerak`);
    assert.equal(p.actor.height, CARD_HEIGHT, `${name}: balandlik o'zgarmasligi kerak`);
    assert.ok(p.actor.style.includes(`min-height: ${CARD_HEIGHT}px`), `${name}: min-height`);
    assert.ok(p.actor.style.includes(`max-height: ${CARD_HEIGHT}px`), `${name}: max-height`);
    assert.ok(p.actor.style.includes(`max-width: ${CARD_WIDTH}px`), `${name}: max-width`);
}

// --- 2. Manba matn eng tepada va kesilmaydi ---

const body = bodyOf(short);
assert.equal(body.children[0], short.origLabel,
    'Tarjima qilinayotgan matn kartaning eng tepasida turishi kerak');
assert.ok(body.children.indexOf(short.row1) > body.children.indexOf(short.origLabel),
    'Birinchi tarjima satri manba matndan KEYIN kelishi kerak');

assert.equal(long.origLabel.text, longText.replace(/\s+/g, ' '),
    'Manba matn to\'liq ko\'rsatilishi kerak — kesilmasin va "..." qo\'shilmasin');
assert.ok(!long.origLabel.text.endsWith('...'), 'Matn oxiriga "..." qo\'yilmasligi kerak');

for (const [name, label] of [['origLabel', long.origLabel],
    ['trans1', long.trans1], ['trans2', long.trans2]]) {
    assert.equal(label.clutter_text.line_wrap, true, `${name}: o'ralishi kerak`);
    assert.equal(label.clutter_text.ellipsize, context.Pango.EllipsizeMode.NONE,
        `${name}: ellipsize o'chirilgan bo'lishi kerak`);
}

// --- 3. Sig'adigan matnda shrift ASL o'lchamida qoladi ---

const fits = popupNeeding(AVAILABLE - 20);
assert.equal(fits._fontScale, 1, 'Sig\'adigan matnda shrift kichraymasligi kerak');

// Chegaraviy holat: aynan sig'adi.
const exact = popupNeeding(AVAILABLE);
assert.equal(exact._fontScale, 1, 'Aynan sig\'adigan matn ham kichraymasligi kerak');

// --- 4. Sig'magan matnda shrift kichrayadi, lekin kerakli miqdorda ---

// Aynan 0.9 miqyosda sig'adigan balandlik: 1.0 da sig'maydi, 0.9 da sig'adi.
const needs90 = popupNeeding(Math.floor(AVAILABLE / 0.9));
assert.ok(needs90._fontScale < 1, 'Sig\'magan matnda shrift kichrayishi kerak');
assert.equal(needs90._fontScale, 0.9,
    `Kerakli darajadagina kichrayishi kerak (kutilgan 0.9, olingan ${needs90._fontScale})`);

const needs75 = popupNeeding(Math.floor(AVAILABLE / 0.75));
assert.equal(needs75._fontScale, 0.75,
    `Kutilgan 0.75, olingan ${needs75._fontScale}`);

// --- 5. Pastki chegaradan o'tmaydi ---
// Aks holda juda uzun matnda yozuv o'qib bo'lmas holga kelardi.

const huge = popupNeeding(AVAILABLE * 10);
assert.equal(huge._fontScale, MIN_FONT_SCALE,
    `Juda uzun matnda shrift ${MIN_FONT_SCALE} dan pastga tushmasligi kerak`);
assert.ok(huge._fontScale > 0.4, 'Pastki chegara o\'qilarli bo\'lishi kerak');

// --- 6. Miqyos haqiqatan uslubga qo'llanadi ---

assert.ok(huge.trans1.style.includes(
    `font-size: ${Math.round(TEXT_STYLES.trans1.size * MIN_FONT_SCALE)}px`),
    `trans1 uslubida kichraygan shrift bo'lishi kerak: ${huge.trans1.style}`);
assert.ok(fits.trans1.style.includes(`font-size: ${TEXT_STYLES.trans1.size}px`),
    'Sig\'adigan matnda asl shrift o\'lchami qolishi kerak');
// Rang va bo'shliqlar tegilmaydi.
assert.ok(huge.trans1.style.includes('color: #ffffff'), 'Rang saqlanishi kerak');
assert.ok(huge.origLabel.style.includes('margin-bottom: 14px'), 'Bo\'shliq saqlanishi kerak');

// --- 7. Joylashuv qat'iy o'lchamga tayanadi va ekrandan chiqmaydi ---

const corner = new context.Popup(1900, 1060, 'matn');
const [posX, posY] = corner.actor.position;
assert.ok(posX + CARD_WIDTH <= MONITOR.width - 20, `O'ngdan chiqmasligi kerak (x=${posX})`);
assert.ok(posY + CARD_HEIGHT <= MONITOR.height - 20, `Pastdan chiqmasligi kerak (y=${posY})`);
assert.ok(posX >= MONITOR.x + 20 && posY >= MONITOR.y + 36, 'Chap/tepadan ham chiqmasligi kerak');

console.log('PASS: o\'lcham qat\'iy, shrift sig\'guncha kichrayadi, manba matn tepada va kesilmaydi');
