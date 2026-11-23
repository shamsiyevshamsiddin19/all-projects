// Haqiqiy GJS/Gio orqali xususiy fayl, dublikat va buzilgan bazani tekshirish.
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {VocabularyStore, Pronunciation} from '../learning-services.js';
import {wordInfo} from '../example-utils.js';

function check(condition, message) {
    if (!condition) throw new Error(message);
}
const directory = GLib.dir_make_tmp('quick-translate-test-XXXXXX');
const store = new VocabularyStore(directory);
check(store.list().length === 0, 'New store must be empty');
const record = {src: 'UZ', original: 'sinov', items: [{tag: 'EN', text: 'test'}],
    examples: {EN: 'This is a useful test.'}};
const id = store.save(record);
check(store.list().length === 1, 'Record must persist');
store.save({...record, original: 'SINOV', examples: {EN: 'We finished the test.'}});
check(store.list().length === 1, 'Case-insensitive duplicate must update');
check(store.list()[0].examples.EN === 'We finished the test.', 'Examples must update');
const mode = store.file.query_info('unix::mode', Gio.FileQueryInfoFlags.NONE, null)
    .get_attribute_uint32('unix::mode') & 0o777;
check(mode === 0o600, 'Vocabulary must be private');
store.remove(id);
check(store.list().length === 0, 'Only chosen record must be removed');
store.file.replace_contents('{broken', null, false, Gio.FileCreateFlags.PRIVATE, null);
let failed = false;
try { store.save(record); } catch (_error) { failed = true; }
check(failed, 'Corrupt database must not be overwritten');
check(new TextDecoder().decode(store.file.load_contents(null)[1]) === '{broken', 'Original bytes must remain');
check(wordInfo({definitions: [{pos: 'verb', base_form: 'determine'}]}) === 'fe’l · determine',
    'Grammar must come from dictionary fields');
check(wordInfo({}) === '', 'No guessed grammar');
const voice = new Pronunciation();
let errors = 0;
voice.play('test', 'UZ', error => { if (error) errors++; });
voice.play('a'.repeat(201), 'EN', error => { if (error) errors++; });
check(errors === 2 && !voice.process, 'Invalid speech must not launch a process');
print('PASS: real Gio private storage, duplicate update, delete, corruption preservation, grammar, speech validation');
print('Isolated test directory: ' + directory);
