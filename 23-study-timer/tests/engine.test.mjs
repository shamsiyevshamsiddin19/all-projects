/**
 * Taymer mantig'ining xulq-atvor testlari (node:test — tashqi paketsiz).
 * Bu yerda "element bormi" emas, "natija to'g'rimi" tekshiriladi.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import { Countdown } from '../js/engine/countdown.js';
import { TimerEngine } from '../js/engine/timer-engine.js';
import { MODES, POMODORO_PHASES, MINUTE, MS } from '../js/constants.js';

const T0 = 1_700_000_000_000;

/** Boshqariladigan soat bilan dvigatel */
function makeEngine(extra = {}) {
  const clock = { now: T0 };
  const engine = new TimerEngine({ now: () => clock.now, ...extra });
  return { engine, clock, advance: (ms) => { clock.now += ms; } };
}

test('fon tabda sekinlashgan tick ham vaqtni to\'g\'ri hisoblaydi', () => {
  const cd = new Countdown(5 * MINUTE * MS);
  cd.start(T0);
  // Brauzer 10 daqiqa davomida bitta ham tick bermadi
  const events = cd.tick(T0 + 10 * MINUTE * MS, { preEndWarning: true });
  assert.equal(events.length, 1, 'faqat bitta hodisa bo\'lishi kerak');
  assert.equal(events[0].type, 'finished');
  assert.equal(cd.remaining(T0 + 10 * MINUTE * MS), 0);
  // Qayta tick hech narsa qaytarmaydi — tugash ikki marta ishlamaydi
  assert.deepEqual(cd.tick(T0 + 11 * MINUTE * MS, { preEndWarning: true }), []);
});

test('tick chastotasi natijaga ta\'sir qilmaydi', () => {
  const a = new Countdown(60 * MS).start(T0);
  const b = new Countdown(60 * MS).start(T0);
  for (let i = 1; i <= 60; i += 1) a.tick(T0 + i * 1000, {});
  b.tick(T0 + 60_000, {});
  assert.equal(a.remaining(T0 + 60_000), b.remaining(T0 + 60_000));
});

test('preset qo\'yilganda bironta soniya yo\'qolmaydi', () => {
  const { engine } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(1500, { applyNow: true });
  engine.start();
  assert.equal(engine.sample().remainingMs, 1500 * MS, '25:00 ko\'rinishi kerak, 24:59 emas');
});

test('"1 daqiqa qoldi" ogohlantirishi har bir yangi seansda qayta ishlaydi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.reminders.preEndWarning = true;

  const runSession = () => {
    engine.setConfiguredDuration(2 * 60, { applyNow: true });
    engine.start();
    const fired = [];
    for (let i = 0; i < 130; i += 1) {
      advance(1000);
      fired.push(...engine.tick());
    }
    return fired;
  };

  const first = runSession();
  assert.equal(first.filter((e) => e.type === 'preEnd').length, 1);
  // Regressiya: ilgari warnedPreEnd tiklanmagani uchun ikkinchi seansda chalinmasdi
  const second = runSession();
  assert.equal(second.filter((e) => e.type === 'preEnd').length, 1,
    'ikkinchi seansda ham aynan bir marta chalinishi kerak');
});

test('oraliq eslatmalar seanslar orasida qayta hisoblanadi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.reminders.intervalMinutes = 1;

  engine.setConfiguredDuration(150, { applyNow: true });
  engine.start();
  let fired = [];
  for (let i = 0; i < 150; i += 1) { advance(1000); fired.push(...engine.tick()); }
  assert.equal(fired.filter((e) => e.type === 'interval').length, 2, '1 va 2 daqiqada');

  engine.setConfiguredDuration(70, { applyNow: true });
  engine.start();
  fired = [];
  for (let i = 0; i < 70; i += 1) { advance(1000); fired.push(...engine.tick()); }
  assert.equal(fired.filter((e) => e.type === 'interval').length, 1,
    'yangi seans noldan sanaydi');
});

test('o\'tkazib yuborilgan eslatmalar bittaga jamlanadi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.reminders.intervalMinutes = 10;
  engine.setConfiguredDuration(60 * MINUTE, { applyNow: true });
  engine.start();
  advance(35 * MINUTE * MS);
  const events = engine.tick();
  const intervals = events.filter((e) => e.type === 'interval');
  assert.equal(intervals.length, 1, '3 ta o\'tkazib yuborilgan eslatma bitta bo\'lib keladi');
  assert.equal(intervals[0].minutes, 30);
});

test('statistika pauzalarni hisobga oladi (nominal emas, haqiqiy vaqt)', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(10 * MINUTE, { applyNow: true });
  engine.start();
  advance(4 * MINUTE * MS);
  engine.tick();
  engine.pause();
  advance(60 * MINUTE * MS); // uzoq tanaffus
  engine.start();
  advance(6 * MINUTE * MS);
  const events = engine.tick();
  const finished = events.find((e) => e.type === 'finished');
  assert.ok(finished, 'taymer tugashi kerak');
  assert.equal(finished.focusMs, 10 * MINUTE * MS, 'pauzadagi 60 daqiqa qo\'shilmasligi kerak');
});

test('vaqt qo\'shish qolgan va umumiy vaqtni to\'g\'ri o\'zgartiradi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(5 * MINUTE, { applyNow: true });
  engine.start();
  advance(MINUTE * MS);
  engine.adjust(2 * MINUTE * MS);
  assert.equal(engine.sample().remainingMs, 6 * MINUTE * MS);
  engine.adjust(-5 * MINUTE * MS);
  assert.equal(engine.sample().remainingMs, 1 * MINUTE * MS);
});

test('pomodoro: sikllar sanaladi, uzun tanaffus sozlanadi, hisoblagich tozalanadi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.POMODORO);
  engine.setPomodoroConfig({
    work: 60, shortBreak: 30, longBreak: 45, cyclesPerLongBreak: 2, autoStartNext: true
  });

  const finishPhase = () => {
    const total = engine.pomodoro.totalMs;
    advance(total);
    return engine.tick();
  };

  engine.start();
  let ev = finishPhase();                       // 1-dars
  assert.equal(engine.pomoCycles, 1);
  assert.equal(engine.pomoPhase, POMODORO_PHASES.SHORT_BREAK);
  assert.equal(ev.find((e) => e.type === 'finished').focusMs, 60 * MS);

  finishPhase();                                // qisqa tanaffus
  assert.equal(engine.pomoPhase, POMODORO_PHASES.WORK);
  finishPhase();                                // 2-dars
  assert.equal(engine.pomoCycles, 2);
  assert.equal(engine.pomoPhase, POMODORO_PHASES.LONG_BREAK, '2 sikldan keyin uzun tanaffus');

  engine.resetPomoCycles();
  assert.equal(engine.pomoCycles, 0);
});

test('tanaffus fokus statistikasiga qo\'shilmaydi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.POMODORO);
  engine.setPomodoroConfig({ work: 60, shortBreak: 60, cyclesPerLongBreak: 4 });
  engine.switchPomoPhase(POMODORO_PHASES.SHORT_BREAK);
  engine.start();
  advance(engine.pomodoro.totalMs);
  const finished = engine.tick().find((e) => e.type === 'finished');
  assert.equal(finished.focusMs, 0);
});

test('autoStartNext o\'chiq bo\'lsa keyingi bosqich o\'zi boshlanmaydi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.POMODORO);
  engine.setPomodoroConfig({ work: 60, autoStartNext: false });
  engine.start();
  advance(60 * MS);
  engine.tick();
  assert.equal(engine.isRunning, false);
});

test('rejim almashtirish boshqa rejimdagi taymerni o\'chirmaydi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(10 * MINUTE, { applyNow: true });
  engine.start();
  advance(3 * MINUTE * MS);

  engine.setMode(MODES.STOPWATCH);
  engine.start();
  advance(MINUTE * MS);

  engine.setMode(MODES.DURATION);
  assert.equal(engine.sample().remainingMs, 6 * MINUTE * MS,
    'davomiylik rejimi o\'z vaqtini saqlab qolishi kerak');
});

test('ishlab turganda kiritish maydoni qolgan vaqtni buzmaydi', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(10 * MINUTE, { applyNow: true });
  engine.start();
  advance(2 * MINUTE * MS);
  engine.setConfiguredDuration(45 * MINUTE); // foydalanuvchi yozmoqda
  assert.equal(engine.sample().remainingMs, 8 * MINUTE * MS);
});

test('davomiylik chegaradan oshmaydi', () => {
  const { engine } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(10 ** 12, { applyNow: true });
  assert.ok(engine.configuredDurationSec <= 999 * 24 * 3600);
  engine.setConfiguredDuration(-50, { applyNow: true });
  assert.equal(engine.configuredDurationSec, 0);
});

test('sekundomer: yurish, pauza, bosqichlar', () => {
  const { engine, advance } = makeEngine();
  engine.setMode(MODES.STOPWATCH);
  engine.start();
  advance(1500);
  assert.equal(engine.sample().elapsedMs, 1500);
  const lap1 = engine.addLap();
  advance(2500);
  const lap2 = engine.addLap();
  assert.equal(lap1.splitMs, 1500);
  assert.equal(lap2.splitMs, 2500);
  assert.equal(lap2.totalMs, 4000);
  engine.pause();
  advance(10_000);
  assert.equal(engine.sample().elapsedMs, 4000, 'pauzada vaqt o\'smasligi kerak');
  engine.clearLaps();
  assert.equal(engine.stopwatch.laps.length, 0);
});

test('maqsadli sana bir marta tugaydi', () => {
  const { engine, clock, advance } = makeEngine();
  engine.setMode(MODES.TARGET);
  engine.setTarget(new Date(clock.now + 150 * 1000));
  engine.reminders.preEndWarning = true;
  advance(60_000); // qolgani 90 s — hali ogohlantirish yo'q
  assert.deepEqual(engine.tick(), []);
  advance(31_000); // qolgani 59 s
  assert.equal(engine.tick().filter((e) => e.type === 'preEnd').length, 1);
  advance(60_000);
  assert.equal(engine.tick().filter((e) => e.type === 'finished').length, 1);
  assert.deepEqual(engine.tick(), [], 'ikkinchi marta tugamaydi');
});

test('sahifa yangilangandan keyin yurib turgan taymer davom etadi', () => {
  const { engine, advance, clock } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(10 * MINUTE, { applyNow: true });
  engine.start();
  advance(3 * MINUTE * MS);
  const saved = JSON.parse(JSON.stringify(engine.serialize()));

  advance(2 * MINUTE * MS); // sahifa yopiq turgan vaqt
  const fresh = new TimerEngine({ now: () => clock.now });
  const result = fresh.restore(saved);
  assert.equal(result.restoredRunning, true);
  assert.equal(fresh.sample().remainingMs, 5 * MINUTE * MS);
  assert.equal(result.missedFinish, false);
});

test('yo\'q bo\'lgan vaqtda tugagan taymer belgilanadi', () => {
  const { engine, advance, clock } = makeEngine();
  engine.setMode(MODES.DURATION);
  engine.setConfiguredDuration(2 * MINUTE, { applyNow: true });
  engine.start();
  const saved = JSON.parse(JSON.stringify(engine.serialize()));
  advance(30 * MINUTE * MS);
  const fresh = new TimerEngine({ now: () => clock.now });
  const result = fresh.restore(saved);
  assert.equal(result.missedFinish, true);
  assert.equal(fresh.sample().remainingMs, 0);
});

test('buzilgan saqlangan holat dvigatelni yiqitmaydi', () => {
  const { engine } = makeEngine();
  assert.doesNotThrow(() => engine.restore(null));
  assert.doesNotThrow(() => engine.restore({ mode: 'hacked', duration: 'nope', pomoCycles: -5 }));
  assert.ok(Object.values(MODES).includes(engine.mode));
  assert.equal(engine.pomoCycles, 0);
});
