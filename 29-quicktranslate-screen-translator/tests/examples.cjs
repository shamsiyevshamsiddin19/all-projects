// Til almashtirish, eski javobni rad etish va misol keshini tekshirish.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../popup.js'), 'utf8');
const utilities = fs.readFileSync(path.join(__dirname, '../example-utils.js'), 'utf8');
let nextId = 0;
const timers = new Map(), requests = [];
class Cancellable {
    cancel() { this.cancelled = true; }
    is_cancelled() { return Boolean(this.cancelled); }
}
const context = {
    Gio: {Cancellable}, GLib: {PRIORITY_DEFAULT: 0, SOURCE_REMOVE: false,
        timeout_add: (_priority, _ms, fn) => {timers.set(++nextId, fn); return nextId;},
        source_remove: id => timers.delete(id)},
    fetchDictionaryExample: (text, tag, callback, request) => requests.push({text, tag, callback, request}),
};
vm.createContext(context);
vm.runInContext(utilities.replace(/export /g, '') +
    source.slice(source.indexOf('class QuickTranslatePopup')) +
    ';this.Popup=QuickTranslatePopup;', context);
assert.equal(context.chooseExample({definitions: [{entry: [{example: 'She was <b>determined</b> to win.'}]}]}),
    'She was determined to win.');
assert.equal(context.chooseExample({examples: {example: [{text: 'short'}]}}), '');
assert.equal(context.englishLookup('was determined'), 'determined');
assert.equal(context.englishLookup('was determined to finish the project'), 'was determined to finish the project');
const p = Object.create(context.Popup.prototype);
Object.assign(p, {_items: [{tag:'RU', text:'решительный'}, {tag:'EN', text:'determined'}],
    _exampleCache: new Map(), tag1:{set_label(){}}, tag2:{set_label(){}},
    exampleLabel:{set_text(value){this.text=value;}}, _startAutoClose(){}});
p._showExample(0);
p._showExample(1);
assert(requests[0].request.is_cancelled());
requests[0].callback('Старый ответ.', false);
assert(!p.exampleLabel.text.includes('Старый'));
requests[1].callback('She was determined to win.', false);
assert.equal(p.exampleLabel.text, 'EN — She was determined to win.');
assert.equal(timers.size, 0);
p._showExample(1);
assert.equal(requests.length, 2, 'Cached result must not start another request');
p._showExample(0);
const timer = [...timers.values()][0];
timer();
assert.equal(p._exampleLoading, false);
assert(p._exampleRequest.is_cancelled());
assert(p.exampleLabel.text.includes('Qayta'));
console.log('PASS: clean examples, bounded phrase lookup, language race, cache, timeout');
