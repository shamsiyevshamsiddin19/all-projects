/**
 * Zenith Chrono — yagona konstantalar manbasi.
 * Loyihada "sehrli raqam" ishlatilmaydi: hamma qiymat shu yerda nomlanadi.
 */

export const SEC = 1;
export const MINUTE = 60 * SEC;
export const HOUR = 60 * MINUTE;
export const DAY = 24 * HOUR;

export const MS = 1000;

/** Taymer yurish rejimlari */
export const MODES = Object.freeze({
  DURATION: 'duration',
  POMODORO: 'pomodoro',
  STOPWATCH: 'stopwatch',
  CLOCK: 'clock'
});

export const ALL_MODES = Object.freeze(Object.values(MODES));

export const POMODORO_PHASES = Object.freeze({
  WORK: 'work',
  SHORT_BREAK: 'shortBreak',
  LONG_BREAK: 'longBreak'
});

/** Pomodoro standart qiymatlari (soniyada) — sozlamalardan o'zgartiriladi */
export const POMODORO_DEFAULTS = Object.freeze({
  work: 25 * MINUTE,
  shortBreak: 5 * MINUTE,
  longBreak: 15 * MINUTE,
  cyclesPerLongBreak: 4,
  autoStartNext: true
});

export const POMODORO_LIMITS = Object.freeze({
  minPhase: 1 * MINUTE,
  maxPhase: 180 * MINUTE,
  minCycles: 2,
  maxCycles: 12
});

/** Standart davomiylik: foydalanuvchi hech narsa kiritmasa */
export const DEFAULT_DURATION = 25 * MINUTE;
export const MAX_DURATION = 999 * DAY;

/** Tugashdan oldin ogohlantirish chegarasi */
export const PRE_END_WARNING_SEC = 1 * MINUTE;

/** Oraliq eslatma variantlari (daqiqa) */
export const REMINDER_INTERVALS = Object.freeze([0, 10, 15, 20, 30, 45]);

/** UI vaqtlari */
export const IDLE_HIDE_MS = 3500;
export const TOAST_VISIBLE_MS = 3500;
export const TOAST_FADE_MS = 300;
export const EDGE_HOVER_PX = 28;
export const EDGE_CLOSE_MARGIN_PX = 60;
export const RESIZE_DEBOUNCE_MS = 150;
export const ORIENTATION_SETTLE_MS = 150;
export const MOBILE_MAX_WIDTH = 900;

/** Taymer yuragi: timestamp asosida hisoblanadi, shu sabab chastota aniqlikka ta'sir qilmaydi */
export const TICK_INTERVAL_MS = 250;

/** Saqlash */
export const STORAGE_KEY = 'zenith_timer_data';
export const LEGACY_STORAGE_KEYS = Object.freeze(['zenith_timer_config']);
export const SCHEMA_VERSION = 2;
export const SAVE_DEBOUNCE_MS = 400;
export const MAX_HISTORY = 200;
export const API_ENDPOINT = '/api/data';
export const API_TIMEOUT_MS = 4000;

/** Mavzular va shriftlar — CSS klasslari bilan bir xil */
export const THEMES = Object.freeze([
  'theme-obsidian',
  'theme-midnight',
  'theme-emerald',
  'theme-amber',
  'theme-violet',
  'theme-aurora'
]);

export const FONTS = Object.freeze([
  'font-urbanist',
  'font-inter',
  'font-montserrat',
  'font-mono',
  'font-serif'
]);

export const ALARM_SOUNDS = Object.freeze([
  'zen_bowl',
  'soft_bell',
  'digital_chime',
  'crystal',
  'mute'
]);

export const AMBIENT_SOUNDS = Object.freeze(['none', 'rain', 'binaural', 'space']);

export const LANGS = Object.freeze(['uz', 'en']);

/** Kiritish maydonlari chegaralari */
export const INPUT_LIMITS = Object.freeze({
  days: { min: 0, max: 999 },
  hours: { min: 0, max: 23 },
  minutes: { min: 0, max: 59 },
  seconds: { min: 0, max: 59 }
});

export const DEFAULT_VOLUME = 80;
export const MAX_LAPS = 50;
