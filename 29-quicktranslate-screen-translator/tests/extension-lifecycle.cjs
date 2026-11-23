const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

let source = fs.readFileSync(path.join(__dirname, '../extension.js'), 'utf8')
    .replace(/^import .*;$/gm, '')
    .replace('export default class QuickTranslateExtension', 'class QuickTranslateExtension');
source += '\nthis.QuickTranslateExtension = QuickTranslateExtension;';

let added = null;
let removed = null;
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
    destroy() { this._destroyed = true; }
}
class Extension { getSettings() { return {schema: true}; } }
const context = {
    Extension,
    Gio: {Cancellable},
    Meta: {KeyBindingFlags: {NONE: 0}},
    Shell: {ActionMode: {NORMAL: 1, OVERVIEW: 2}},
    Main: {wm: {
        addKeybinding: (...args) => { added = args; },
        removeKeybinding: name => { removed = name; },
    }},
    QuickTranslatePopup: Popup,
    getTruePointerCoords: () => [640, 360],
    getSelection: callback => { selectionCallback = callback; },
    requestMultiTranslation: (_text, callback) => { translationCallback = callback; },
};
vm.createContext(context);
vm.runInContext(source, context);

const extension = new context.QuickTranslateExtension();
extension.enable();
assert.equal(added[0], 'toggle-popup');
assert.equal(added[3], 3);

extension._toggle();
assert(extension._selectionPending);
selectionCallback('Мой');
assert.equal(extension._popup.text, 'Мой');
translationCallback({src: 'RU', items: [{tag: 'UZ', text: 'Mening'}, {tag: 'EN', text: 'My'}]}, null);
assert.equal(extension._popup.result.src, 'RU');

const oldPopup = extension._popup;
extension._toggle();
assert(oldPopup._destroyed);
assert.equal(extension._popup, null);

extension._toggle();
const activeRequest = extension._request;
extension.disable();
assert.equal(removed, 'toggle-popup');
assert(activeRequest.cancelled);
assert.equal(extension._popup, null);
assert(cancelled >= 1);

console.log('PASS: standalone keybinding, request, popup and disable lifecycle');
