// Haqiqiy GNOME GrabHelper va popup lifecycle: grafik sessiyasiz regressiya testi.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../popup.js'), 'utf8');
const helperSource = execFileSync('gresource', ['extract',
    '/usr/lib/gnome-shell/libshell-14.so', '/org/gnome/shell/ui/grabHelper.js'], {encoding: 'utf8'});
let seat = 3, pushed = 0, popped = 0, focused = null;
class Actor {
    constructor(parent = null) { this.parent = parent; }
    connect(_name, fn) { this.handler = fn; return 1; }
    disconnect() { this.handler = null; }
    get_parent() { return this.parent; }
    contains(target) { for (; target; target = target.parent) if (target === this) return true; return false; }
    grab_key_focus() { focused = this; }
}
const hooks = {connectObject() {}, disconnectObject() {}};
const timers = new Map();
let nextId = 0;
const context = {
    Clutter: {Actor, GrabState: {ALL: 3}, EVENT_STOP: 1, EVENT_PROPAGATE: 0,
        KEY_Escape: 27, EventType: {KEY_PRESS: 1, BUTTON_PRESS: 2, BUTTON_RELEASE: 3,
            TOUCH_BEGIN: 4, TOUCH_END: 5, ENTER: 6, LEAVE: 7}},
    St: {DirectionType: {TAB_FORWARD: 0}},
    Params: {parse: (params, defaults) => ({...defaults, ...params})},
    Main: {pushModal: () => { pushed++; return {get_seat_state: () => seat}; },
        popModal: () => popped++, keyboard: {maybeHandleEvent: () => false},
        overview: hooks, sessionMode: hooks, layoutManager: {...hooks, removeChrome() {}}},
    global: {stage: {key_focus: null, get_event_actor: e => e.target},
        display: {is_pointer_emulating_sequence: () => true}},
    GLib: {PRIORITY_DEFAULT: 0, SOURCE_REMOVE: false,
        timeout_add: (_priority, ms, fn) => { timers.set(++nextId, {ms, fn}); return nextId; },
        source_remove: id => assert(timers.delete(id), 'Timer must be removed only once')},
};
vm.createContext(context);
vm.runInContext(helperSource.replace(/^import .*;$/gm, '').replace('export class', 'class') +
    '\nthis.Helper = GrabHelper;', context);
for (const type of [1, 2, 4]) {
    const owner = new Actor(), card = new Actor(owner), button = new Actor(card);
    const helper = new context.Helper(owner);
    let closed = 0;
    assert(helper.grab({actor: card, focus: card, onUngrab: () => closed++}));
    assert.equal(focused, card);
    assert.equal(helper.onCapturedEvent({type: () => 2, target: button}), 0);
    assert.equal(closed, 0);
    assert.equal(helper.onCapturedEvent({type: () => type, target: owner,
        get_key_symbol: () => 27, get_event_sequence: () => null}), 1);
    assert.equal(closed, 1);
    helper.ungrab({actor: card});
    assert.equal(closed, 1);
    assert.equal(helper.grabbed, false);
}
seat = 0;
assert.equal(new context.Helper(new Actor()).grab({actor: new Actor()}), false);
assert.equal(pushed, popped, 'No input grab may leak');
vm.runInContext(source.slice(source.indexOf('class QuickTranslatePopup')) +
    '\nthis.Popup = QuickTranslatePopup;', context);
const popup = Object.create(context.Popup.prototype);
let cancelled = 0;
Object.assign(popup, {actor: {hover: false, remove_all_transitions() {}},
    _overlay: {destroy() {}}, _destroyed: false, _ready: false});
popup._startAutoClose(8000);
assert.equal(timers.size, 0);
popup.startRequest({cancel: () => cancelled++});
assert.equal([...timers.values()][0].ms, 20000);
popup._clearDeadline();
popup._ready = true;
popup._startAutoClose(8000);
assert.equal(timers.size, 1);
popup.actor.hover = true;
popup._startAutoClose(8000);
assert.equal(timers.size, 0);
popup.actor.hover = false;
popup._startAutoClose(8000);
popup.destroy(true);
popup.destroy(true);
assert.equal(cancelled, 1);
assert.equal(timers.size, 0);
assert.equal(popup.state, 'closed');
console.log('PASS: native GrabHelper inside/outside/Esc/touch/failure; focus; timer pause; request cancellation; idempotent cleanup');
