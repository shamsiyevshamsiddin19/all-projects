// Popup boshqaruvlarini haqiqiy metodlari bilan, mock aktorlarda tekshirish.
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
    set_style() {}
    set_position() {}
    set_policy() {}
    add_constraint() {}
    ease() {}
    grab_key_focus() {}
    contains() { return false; }
    destroy_all_children() { this.children = []; }
}
class Request { cancel() { this.cancelled = true; } is_cancelled() { return !!this.cancelled; } }
let records = [], translation;
const hooks = {connectObject() {}, disconnectObject() {}};
const context = {
    St: {BoxLayout: Actor, Widget: Actor, Button: Actor, Label: Actor, Entry: Actor,
        Icon: Actor, ScrollView: Actor, PolicyType: {NEVER: 0, AUTOMATIC: 1}},
    Clutter: {ActorAlign: {START: 0}, AnimationMode: {EASE_OUT_QUAD: 0},
        BindConstraint: Actor, BindCoordinate: {ALL: 0}},
    Pango: {WrapMode: {WORD_CHAR: 0}, EllipsizeMode: {END: 0}},
    Shell: {ActionMode: {POPUP: 1}},
    GLib: {PRIORITY_DEFAULT: 0, timeout_add: () => 1, source_remove() {}},
    Gio: {Cancellable: Request}, global: {stage: {get_key_focus: () => null}},
    Main: {overview: hooks, sessionMode: hooks, layoutManager: {...hooks,
        primaryMonitor: {x: 0,y: 0,width: 1920,height: 1080}, monitors: [],
        addTopChrome() {}}},
    GrabHelper: class { grab() { return true; } },
    Pronunciation: class { stop() {} },
    VocabularyStore: class { save(record) { records = [{...record,id:'1'}]; } list() { return records; } },
    requestMultiTranslation: (text, callback, request, language) => translation = {text, callback, request, language},
    fetchOne: (text, source, target, callback, request) => translation = {text, source, target, callback, request},
};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('class QuickTranslatePopup')) +
    ';this.Popup=QuickTranslatePopup;', context);
const p = new context.Popup(500, 500, 'sinov');
p.setResult({src:'UZ',items:[{tag:'RU',text:'тест'},{tag:'EN',text:'test'}]});
assert(p.speak1.reactive && p.speak2.reactive);
assert(p.saveBtn.reactive);
p._exampleCache.set('EN','This is a test.');
p._saveWord();
assert.equal(records[0].examples.EN, 'This is a test.');
p._toggleLibrary();
assert(p._libraryScroll.visible && !p._mainScroll.visible);
assert(!p.copyBtn.visible);
assert.equal(p.contextBtn, undefined);
assert.equal(p.wordInfoLabel, undefined);
p._reviewSaved(records[0], 0);
assert.equal(p._libraryBody.children[1].visible,false, 'Review answer starts hidden');
p._libraryBody.children[2].handlers.clicked();
assert.equal(p._libraryBody.children[1].visible,true);
p._toggleLibrary();
p._showMeaning('This is a test.', 'EN');
assert.equal(translation.target, 'uz');
translation.callback('Bu sinov.', 'EN', null);
assert.equal(p.meaningLabel.text, 'Bu sinov.');
assert.equal(p._meaningLoading, false);
assert.equal(records[0].meanings['EN:This is a test.'], 'Bu sinov.');
p._showMeaning('This is a test.', 'EN');
assert.equal(p.meaningLabel.text, 'Bu sinov.');
p._showMeaning('Bu sinov.', 'UZ');
assert.equal(p.meaningLabel.text, 'Bu sinov.');
console.log('PASS: removed context/grammar controls; example meaning, cache and saved meaning; library/reveal');
