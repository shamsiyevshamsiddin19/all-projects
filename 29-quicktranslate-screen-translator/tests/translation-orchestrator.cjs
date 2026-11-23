const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

let source = fs.readFileSync(path.join(__dirname, '../translation-orchestrator.js'), 'utf8')
    .replace('export class TranslationOrchestrator', 'class TranslationOrchestrator');
source += '\nmodule.exports = {TranslationOrchestrator};';
const sandbox = {module: {exports: {}}};
vm.runInNewContext(source, sandbox, {filename: 'translation-orchestrator.js'});
const {TranslationOrchestrator} = sandbox.module.exports;

function scenario(order, cancelled = false) {
    const events = [];
    const callbacks = {};
    const coordinator = new TranslationOrchestrator((result, error) => events.push({result, error}), () => cancelled);
    coordinator.start(cb => { callbacks.primary = cb; }, cb => { callbacks.fallback = cb; });
    for (const event of order) callbacks[event.provider](event.result || null, event.error || null);
    return events;
}

const primary = {src: 'RU', items: [{tag: 'UZ', text: 'mening'}, {tag: 'EN', text: 'my'}]};
const fallback = {src: 'RU', items: [{tag: 'UZ', text: 'mening'}, {tag: 'EN', text: 'my'}]};

assert.deepEqual(scenario([
    {provider: 'fallback', result: fallback},
    {provider: 'primary', result: primary},
]), [{result: primary, error: null}], 'primary wins even when fallback is ready first');

assert.deepEqual(scenario([
    {provider: 'primary', error: 'CLAUDE_PARSE'},
    {provider: 'fallback', result: fallback},
]), [{result: fallback, error: null}], 'fallback completes after primary failure');

assert.deepEqual(scenario([
    {provider: 'fallback', result: fallback},
    {provider: 'primary', error: 'CLAUDE_HTTP_503'},
]), [{result: fallback, error: null}], 'prepared fallback completes immediately');

const failed = scenario([
    {provider: 'fallback', error: 'GOOGLE_HTTP_429'},
    {provider: 'primary', error: 'CLAUDE_HTTP_503'},
]);
assert.equal(failed.length, 1);
assert.equal(failed[0].result, null);
assert.match(failed[0].error, /Tarjima xizmatlari/);
assert.doesNotMatch(failed[0].error, /Claude|Google|Gemini/);

assert.deepEqual(scenario([{provider: 'primary', result: primary}], true), [], 'cancelled request is silent');
assert.equal(scenario([
    {provider: 'primary', result: primary},
    {provider: 'primary', result: primary},
    {provider: 'fallback', result: fallback},
]).length, 1, 'duplicate provider callbacks cannot update UI twice');

console.log('PASS: deterministic primary/fallback/cancellation orchestration');
