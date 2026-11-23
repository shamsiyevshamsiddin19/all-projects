const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

let source = fs.readFileSync(path.join(__dirname, '../gemini-utils.js'), 'utf8')
    .replace(/export function /g, 'function ');
source += '\nmodule.exports = { targetsFor, extractFirstJsonObject, buildTranslationPrompt, parseGeminiTranslation, parseClaudeTranslation };';
const sandbox = {module: {exports: {}}, Map, JSON, Error};
vm.runInNewContext(source, sandbox, {filename: 'gemini-utils.js'});
const {targetsFor, extractFirstJsonObject, buildTranslationPrompt, parseGeminiTranslation, parseClaudeTranslation} = sandbox.module.exports;

assert.deepEqual([...targetsFor('UZ')], ['RU', 'EN']);
assert.deepEqual([...targetsFor('EN')], ['UZ', 'RU']);
assert.deepEqual([...targetsFor('RU')], ['UZ', 'EN']);
assert.match(buildTranslationPrompt('salom', 'auto'), /Detect the source language/);
assert.match(buildTranslationPrompt('hello', 'en'), /source language as EN/);
assert.equal(extractFirstJsonObject('before {"text":"brace } inside","nested":{"ok":true}} after {"ignored":1}'),
    '{"text":"brace } inside","nested":{"ok":true}}');
assert.equal(extractFirstJsonObject('no object'), '');

const parsed = parseGeminiTranslation(JSON.stringify({
    src: 'en',
    items: [{tag: 'RU', text: 'привет'}, {tag: 'UZ', text: 'salom'}],
}));
assert.deepEqual(JSON.parse(JSON.stringify(parsed)), {
    src: 'EN',
    items: [{tag: 'UZ', text: 'salom', error: null}, {tag: 'RU', text: 'привет', error: null}],
});
assert.throws(() => parseGeminiTranslation('{bad json}'));
assert.throws(() => parseGeminiTranslation(JSON.stringify({src: 'UZ', items: [{tag: 'RU', text: 'x'}]})));
assert.equal(parseGeminiTranslation(JSON.stringify({src: 'RU', items: [{tag: 'UZ', text: 'salom'}, {tag: 'EN', text: 'hello'}]}), 'ru').src, 'RU');
assert.deepEqual(JSON.parse(JSON.stringify(parseClaudeTranslation('{"source_language":"RU","UZ":"Mening","EN":"My"}'))), {
    src: 'RU', items: [{tag: 'UZ', text: 'Mening', error: null}, {tag: 'EN', text: 'My', error: null}],
});
assert.equal(parseClaudeTranslation('```json\n{"source_language":"RU","UZ":"Mening","EN":"My"}\n```').src, 'RU');

console.log('Gemini response helper tests passed.');
