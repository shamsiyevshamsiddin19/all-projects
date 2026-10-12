/**
 * Vaqtni formatlash — sof funksiyalar, DOM'ga bog'liq emas.
 */
import { MS, MINUTE, HOUR, DAY } from './constants.js';

/** Ikki xonali qilib to'ldirish */
export function pad2(n) {
  return String(Math.max(0, Math.floor(n))).padStart(2, '0');
}

/**
 * Millisekundni kun/soat/daqiqa/soniya/yuzinchi ulushga ajratadi.
 * @param {number} ms
 */
export function splitDuration(ms) {
  const safe = Math.max(0, Math.floor(ms));
  const totalSec = Math.floor(safe / MS);
  return {
    days: Math.floor(totalSec / DAY),
    hours: Math.floor((totalSec % DAY) / HOUR),
    minutes: Math.floor((totalSec % HOUR) / MINUTE),
    seconds: totalSec % 60,
    centis: Math.floor((safe % MS) / 10),
    totalSec
  };
}

/** Soniyalarni kun/soat/daqiqa/soniyaga ajratadi (kiritish maydonlari uchun) */
export function splitSeconds(totalSec) {
  const s = Math.max(0, Math.floor(totalSec));
  return {
    days: Math.floor(s / DAY),
    hours: Math.floor((s % DAY) / HOUR),
    minutes: Math.floor((s % HOUR) / MINUTE),
    seconds: s % 60
  };
}

/** Qisqa matnli ko'rinish: "1d 02:05:01" / "25:00" */
export function formatCompact(ms) {
  const { days, hours, minutes, seconds } = splitDuration(ms);
  const dStr = days > 0 ? `${days}d ` : '';
  const hStr = hours > 0 || days > 0 ? `${pad2(hours)}:` : '';
  return `${dStr}${hStr}${pad2(minutes)}:${pad2(seconds)}`;
}

/** Fokus vaqtini odam o'qiydigan ko'rinishga aylantiradi */
export function formatFocusMinutes(totalMinutes, t) {
  const mins = Math.max(0, Math.round(totalMinutes));
  if (mins >= 60) {
    const hrs = Math.floor(mins / 60);
    const rest = mins % 60;
    return rest === 0
      ? `${hrs} ${t('unit.hour')}`
      : `${hrs} ${t('unit.hour')} ${rest} ${t('unit.min')}`;
  }
  return `${mins} ${t('unit.min')}`;
}

/** ISO sanani <input type="datetime-local"> uchun mahalliy vaqtga o'giradi */
export function toLocalInputValue(date) {
  const tzOffset = date.getTimezoneOffset() * MINUTE * MS;
  return new Date(date.getTime() - tzOffset).toISOString().slice(0, 16);
}

/** Sana kalitini (YYYY-MM-DD) mahalliy vaqt bo'yicha qaytaradi */
export function dayKey(date = new Date()) {
  const y = date.getFullYear();
  const m = pad2(date.getMonth() + 1);
  const d = pad2(date.getDate());
  return `${y}-${m}-${d}`;
}
