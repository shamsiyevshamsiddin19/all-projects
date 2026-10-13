/**
 * Saqlash qatlami: validatsiya, migratsiya, debounce, server sinxronizatsiyasi.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import {
  Storage, normalizeState, defaultState, recordSession, emptyStatistics, looksLikeBackup
} from '../js/storage.js';
import { STORAGE_KEY, LEGACY_STORAGE_KEYS, MAX_HISTORY } from '../js/constants.js';

/** Xotiradagi soxta localStorage */
function makeStorageBackend(initial = {}) {
  const data = { ...initial };
  return {
    data,
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; }
  };
}

test('buzilgan qiymatlar standartga qaytadi', () => {
  const out = normalizeState({
    settings: { theme: '<script>', font: 42, volume: 9999, lang: 'klingon', alarmSound: 'boom' },
    statistics: { totalFocusMinutes: 'ko\'p', history: 'massiv emas' }
  });
  assert.equal(out.settings.theme, defaultState().settings.theme);
  assert.equal(out.settings.font, defaultState().settings.font);
  assert.equal(out.settings.volume, 100);
  assert.equal(out.settings.lang, 'uz');
  assert.equal(out.settings.alarmSound, 'zen_bowl');
  assert.equal(out.statistics.totalFocusMinutes, 0);
  assert.deepEqual(out.statistics.history, []);
});

test('pomodoro qiymatlari chegaraga siqiladi', () => {
  const out = normalizeState({ settings: { pomodoro: { work: 0, longBreak: 10 ** 6, cyclesPerLongBreak: 99 } } });
  assert.equal(out.settings.pomodoro.work, 60);
  assert.equal(out.settings.pomodoro.longBreak, 180 * 60);
  assert.equal(out.settings.pomodoro.cyclesPerLongBreak, 12);
});

test('eski (v1) format o\'qiladi', () => {
  const out = normalizeState({ theme: 'theme-amber', font: 'font-mono', volume: 30 });
  assert.equal(out.settings.theme, 'theme-amber');
  assert.equal(out.settings.font, 'font-mono');
  assert.equal(out.settings.volume, 30);
  assert.equal(out.version, 2);
});

test('tarix MAX_HISTORY bilan cheklanadi', () => {
  const history = Array.from({ length: MAX_HISTORY + 50 }, (_, i) => ({
    id: i, timestamp: new Date().toISOString(), type: 'duration', title: 't', durationMinutes: 1
  }));
  const out = normalizeState({ statistics: { history } });
  assert.equal(out.statistics.history.length, MAX_HISTORY);
});

test('eski localStorage kaliti ko\'chiriladi va o\'chiriladi', () => {
  const backend = makeStorageBackend({
    [LEGACY_STORAGE_KEYS[0]]: JSON.stringify({ theme: 'theme-violet', volume: 11 })
  });
  const storage = new Storage({ storage: backend, fetchFn: null, locationProtocol: 'http:' });
  const loaded = storage.load();
  assert.equal(loaded.settings.theme, 'theme-violet');
  assert.equal(backend.getItem(LEGACY_STORAGE_KEYS[0]), null, 'eski kalit qolmasligi kerak');
});

test('buzilgan JSON ilovani yiqitmaydi', () => {
  const backend = makeStorageBackend({ [STORAGE_KEY]: '{bu json emas' });
  const storage = new Storage({ storage: backend, fetchFn: null });
  assert.doesNotThrow(() => storage.load());
  assert.equal(storage.load().settings.theme, defaultState().settings.theme);
});

test('localStorage mavjud bo\'lmasa ham ishlaydi', () => {
  const storage = new Storage({ storage: null, fetchFn: null });
  assert.doesNotThrow(() => storage.load());
  assert.doesNotThrow(() => storage.saveNow(defaultState()));
});

test('debounce: ko\'p chaqiruv bitta yozuvga aylanadi', async () => {
  const backend = makeStorageBackend();
  let posts = 0;
  const storage = new Storage({
    storage: backend,
    locationProtocol: 'http:',
    fetchFn: async () => { posts += 1; return { ok: true, json: async () => ({}) }; }
  });
  const base = defaultState();
  for (let i = 0; i <= 100; i += 1) {
    storage.save({ ...base, settings: { ...base.settings, volume: i } });
  }
  assert.equal(posts, 0, 'debounce tugamaguncha yozilmaydi');
  await new Promise((r) => setTimeout(r, 600));
  assert.equal(posts, 1, '101 ta chaqiruv — 1 ta POST');
  assert.equal(JSON.parse(backend.getItem(STORAGE_KEY)).settings.volume, 100);
});

test('flush kutayotgan yozuvni yo\'qotmaydi', () => {
  const backend = makeStorageBackend();
  const storage = new Storage({ storage: backend, fetchFn: null, locationProtocol: 'file:' });
  const base = defaultState();
  storage.save({ ...base, settings: { ...base.settings, volume: 7 } });
  storage.flush();
  assert.equal(JSON.parse(backend.getItem(STORAGE_KEY)).settings.volume, 7);
});

test('file:// da serverga yozilmaydi', () => {
  let called = false;
  const storage = new Storage({
    storage: makeStorageBackend(),
    locationProtocol: 'file:',
    fetchFn: () => { called = true; }
  });
  storage.saveNow(defaultState());
  assert.equal(called, false);
});

test('server nusxasi faqat yangiroq bo\'lsa olinadi', async () => {
  const remote = { ...defaultState(), savedAt: '2026-01-02T00:00:00.000Z' };
  remote.settings.volume = 33;
  const storage = new Storage({
    storage: makeStorageBackend(),
    locationProtocol: 'http:',
    fetchFn: async () => ({ ok: true, json: async () => remote })
  });
  const newer = await storage.fetchRemote('2026-01-01T00:00:00.000Z');
  assert.equal(newer.settings.volume, 33);
  const older = await storage.fetchRemote('2026-02-01T00:00:00.000Z');
  assert.equal(older, null, 'eski server nusxasi mahalliyni bosmasligi kerak');
});

test('server javobi buzilgan bo\'lsa null qaytadi', async () => {
  const storage = new Storage({
    storage: makeStorageBackend(),
    locationProtocol: 'http:',
    fetchFn: async () => ({ ok: true, json: async () => ({ random: 'junk' }) })
  });
  assert.equal(await storage.fetchRemote(null), null);
});

test('import uchun fayl tuzilmasi tekshiriladi', () => {
  assert.equal(looksLikeBackup({ settings: {} }), true);
  assert.equal(looksLikeBackup({ theme: 'theme-amber' }), true);
  assert.equal(looksLikeBackup({ shopping: ['non'] }), false);
  assert.equal(looksLikeBackup(null), false);
});

test('seans statistikasi kunlar bo\'yicha yoziladi', () => {
  let stats = emptyStatistics();
  const when = new Date('2026-10-12T10:00:00');
  stats = recordSession(stats, { focusMs: 25 * 60 * 1000, type: 'duration', title: 'A', when });
  stats = recordSession(stats, { focusMs: 5 * 60 * 1000, type: 'pomodoro', title: 'B', when });
  assert.equal(stats.totalFocusMinutes, 30);
  assert.equal(stats.completedSessionsCount, 2);
  assert.equal(stats.byDay['2026-10-12'], 30);
  assert.equal(stats.history.length, 2);
  // Bir daqiqadan kam seans yozilmaydi
  const same = recordSession(stats, { focusMs: 500, type: 'duration', title: 'C', when });
  assert.equal(same.completedSessionsCount, 2);
});

test('statik hostingda API 404 dan keyin so\'rovlar to\'xtaydi', async () => {
  let calls = 0;
  const storage = new Storage({
    storage: makeStorageBackend(),
    locationProtocol: 'https:',
    fetchFn: async () => { calls += 1; return { ok: false, status: 404, json: async () => ({}) }; }
  });
  assert.equal(storage.serverSyncEnabled, true);
  assert.equal(await storage.fetchRemote(null), null);
  assert.equal(calls, 1);
  assert.equal(storage.serverSyncEnabled, false, '404 dan keyin sinxronizatsiya o\'chadi');

  storage.saveNow(defaultState());
  storage.saveNow(defaultState());
  assert.equal(calls, 1, 'keyingi saqlashlar behuda so\'rov yubormaydi');
});

test('vaqtinchalik tarmoq xatosi sinxronizatsiyani o\'chirmaydi', async () => {
  let calls = 0;
  const storage = new Storage({
    storage: makeStorageBackend(),
    locationProtocol: 'http:',
    fetchFn: async () => { calls += 1; throw new Error('network down'); }
  });
  assert.equal(await storage.fetchRemote(null), null);
  assert.equal(storage.serverSyncEnabled, true, 'tarmoq xatosi — qayta urinish mumkin');
});
