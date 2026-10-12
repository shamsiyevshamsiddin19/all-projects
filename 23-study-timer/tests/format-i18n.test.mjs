/**
 * Formatlash va i18n qatlamlari.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

import { pad2, splitDuration, splitSeconds, formatCompact, formatFocusMinutes, dayKey } from '../js/format.js';
import { t, setLang, getLang, keysOf } from '../js/i18n.js';
import { LANGS } from '../js/constants.js';

test('pad2 manfiy va kasr qiymatlarni ushlaydi', () => {
  assert.equal(pad2(5), '05');
  assert.equal(pad2(-3), '00');
  assert.equal(pad2(9.9), '09');
  assert.equal(pad2(123), '123');
});

test('splitDuration to\'g\'ri ajratadi', () => {
  const p = splitDuration(((2 * 24 + 3) * 3600 + 4 * 60 + 5) * 1000 + 670);
  assert.deepEqual(
    { d: p.days, h: p.hours, m: p.minutes, s: p.seconds, c: p.centis },
    { d: 2, h: 3, m: 4, s: 5, c: 67 }
  );
  assert.equal(splitDuration(-100).totalSec, 0);
});

test('splitSeconds kiritish maydonlari uchun', () => {
  assert.deepEqual(splitSeconds(90061), { days: 1, hours: 1, minutes: 1, seconds: 1 });
});

test('formatCompact kerakli qismlarni ko\'rsatadi', () => {
  assert.equal(formatCompact(25 * 60 * 1000), '25:00');
  assert.equal(formatCompact((3600 + 125) * 1000), '01:02:05');
  assert.equal(formatCompact(26 * 3600 * 1000), '1d 02:00:00');
});

test('formatFocusMinutes soat/daqiqani birlashtiradi', () => {
  assert.equal(formatFocusMinutes(45, t), `45 ${t('unit.min')}`);
  assert.equal(formatFocusMinutes(60, t), `1 ${t('unit.hour')}`);
  assert.equal(formatFocusMinutes(95, t), `1 ${t('unit.hour')} 35 ${t('unit.min')}`);
});

test('dayKey mahalliy sanani beradi', () => {
  assert.equal(dayKey(new Date(2026, 9, 12, 23, 30)), '2026-10-12');
});

test('barcha tillarda kalitlar to\'liq', () => {
  const base = keysOf('uz');
  assert.ok(base.length > 100);
  for (const lang of LANGS) {
    const keys = keysOf(lang);
    assert.deepEqual(base.filter((k) => !keys.includes(k)), [], `${lang} da kalit yetishmaydi`);
    assert.deepEqual(keys.filter((k) => !base.includes(k)), [], `${lang} da ortiqcha kalit`);
  }
});

test('o\'rin egalari to\'ldiriladi', () => {
  setLang('uz');
  assert.match(t('reminder.everyN', { n: 15 }), /15/);
  assert.equal(getLang(), 'uz');
  setLang('en');
  assert.match(t('reminder.everyN', { n: 15 }), /15/);
  setLang('zz');
  assert.equal(getLang(), 'uz', 'noma\'lum til uz ga qaytadi');
});

test('noma\'lum kalit kalitning o\'zini qaytaradi', () => {
  assert.equal(t('yo.q.kalit'), 'yo.q.kalit');
});
