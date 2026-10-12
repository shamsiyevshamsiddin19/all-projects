/**
 * DOM integratsiya testi — haqiqiy HTML jsdom ichida yuklanadi.
 * jsdom o'rnatilmagan bo'lsa test o'tkazib yuboriladi (majburiy bog'liqlik emas):
 *     npm install --save-dev jsdom
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

let JSDOM = null;
try {
  ({ JSDOM } = await import('jsdom'));
} catch {
  JSDOM = null;
}

const maybe = JSDOM ? test : test.skip;

async function mountApp() {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf-8');
  const dom = new JSDOM(html, {
    url: 'http://localhost:5050/',
    pretendToBeVisual: true,
    runScripts: 'outside-only'
  });
  const { window } = dom;

  // Brauzer API'lari: jsdom'da yo'q bo'lganlarini qo'shamiz
  window.AudioContext = function AudioContextMock() {
    const param = { setValueAtTime() {}, exponentialRampToValueAtTime() {}, setTargetAtTime() {} };
    const node = { gain: param, frequency: param, Q: param, connect() {}, disconnect() {}, start() {}, stop() {} };
    return {
      state: 'running',
      currentTime: 0,
      sampleRate: 44100,
      destination: node,
      resume() {},
      createGain: () => ({ ...node, gain: { ...param } }),
      createOscillator: () => ({ ...node }),
      createBiquadFilter: () => ({ ...node }),
      createChannelMerger: () => ({ ...node }),
      createBufferSource: () => ({ ...node, buffer: null, loop: false }),
      createBuffer: (ch, len) => ({ getChannelData: () => new Float32Array(len) })
    };
  };
  window.requestAnimationFrame = () => 0;
  window.cancelAnimationFrame = () => {};
  window.fetch = async () => ({ ok: false, json: async () => ({}) });
  window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });

  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.navigator = window.navigator;
  globalThis.localStorage = window.localStorage;
  globalThis.location = window.location;
  globalThis.fetch = window.fetch;
  globalThis.requestAnimationFrame = window.requestAnimationFrame;
  globalThis.cancelAnimationFrame = window.cancelAnimationFrame;
  globalThis.Blob = window.Blob;
  globalThis.FileReader = window.FileReader;
  globalThis.AudioContext = window.AudioContext;

  await import(`../js/app.js?cacheBust=${Date.now()}`);
  return window;
}

maybe('ilova haqiqiy HTML bilan yetishmagan elementsiz ishga tushadi', async () => {
  const window = await mountApp();
  assert.ok(window.zenith, 'window.zenith yaratilishi kerak');
  assert.deepEqual(window.zenith.missingElements, [],
    'HTML da yetishmayotgan element bo\'lmasligi kerak');
});

maybe('boshlash tugmasi taymerni yurgizadi va ekran yangilanadi', async () => {
  const window = await mountApp();
  const doc = window.document;
  doc.getElementById('inputMinutes').value = '2';
  doc.getElementById('inputMinutes').dispatchEvent(new window.Event('input', { bubbles: true }));
  assert.equal(doc.getElementById('minutesValue').textContent, '02');

  doc.getElementById('toggleRunBtn').click();
  assert.equal(window.zenith.engine.isRunning, true);
  doc.getElementById('toggleRunBtn').click();
  assert.equal(window.zenith.engine.isRunning, false);
});

maybe('rejim almashtirish mos panelni ochadi', async () => {
  const window = await mountApp();
  const doc = window.document;
  doc.getElementById('tabPomodoro').click();
  assert.equal(doc.getElementById('panelPomodoro').hidden, false);
  assert.equal(doc.getElementById('panelDuration').hidden, true);
  assert.equal(doc.getElementById('tabPomodoro').getAttribute('aria-selected'), 'true');
});

maybe('til almashtirilsa interfeys tarjima qilinadi', async () => {
  const window = await mountApp();
  const doc = window.document;
  const select = doc.getElementById('langSelect');
  select.value = 'en';
  select.dispatchEvent(new window.Event('change', { bubbles: true }));
  assert.equal(doc.getElementById('labelMinutes').textContent, 'MINUTES');
  assert.equal(doc.documentElement.lang, 'en');
});

maybe('panelni yopish tugmasi ishlaydi, backdrop yopadi', async () => {
  const window = await mountApp();
  const doc = window.document;
  doc.getElementById('hoverZone').click();
  assert.ok(doc.getElementById('settingsDrawer').classList.contains('open'));
  doc.getElementById('drawerBackdrop').click();
  assert.equal(doc.getElementById('settingsDrawer').classList.contains('open'), false);
});
