/**
 * Saqlash qatlami: sxema validatsiyasi, migratsiya, debounce, server sinxronizatsiyasi.
 *
 * Qoidalar:
 *  - Yagona localStorage kaliti (eski kalitlar bir marta ko'chiriladi va o'chiriladi).
 *  - Har bir yozuv sxema bo'yicha tekshiriladi va chegaralarga siqiladi.
 *  - Yozish debounce qilinadi (slayderni sudraganda tarmoq/disk bosilmaydi).
 *  - Server ombori ham o'qiladi (GET), nafaqat yoziladi.
 */
import {
  STORAGE_KEY, LEGACY_STORAGE_KEYS, SCHEMA_VERSION, SAVE_DEBOUNCE_MS, MAX_HISTORY,
  API_ENDPOINT, API_TIMEOUT_MS, THEMES, FONTS, ALARM_SOUNDS, AMBIENT_SOUNDS,
  REMINDER_INTERVALS, LANGS, MODES, DEFAULT_VOLUME, POMODORO_DEFAULTS, POMODORO_LIMITS,
  MINUTE
} from './constants.js';
import { dayKey } from './format.js';

const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
const oneOf = (v, list, fallback) => (list.includes(v) ? v : fallback);
const bool = (v, fallback) => (typeof v === 'boolean' ? v : fallback);
const int = (v, fallback) => (Number.isFinite(Number(v)) ? Math.floor(Number(v)) : fallback);

/** Standart holat */
export function defaultState() {
  return {
    version: SCHEMA_VERSION,
    savedAt: null,
    settings: {
      lang: 'uz',
      theme: THEMES[0],
      font: FONTS[0],
      volume: DEFAULT_VOLUME,
      alarmSound: ALARM_SOUNDS[0],
      ambientSound: AMBIENT_SOUNDS[0],
      showDays: true,
      wakeLockEnabled: true,
      autoRotatePortrait: true,
      edgeHoverEnabled: true,
      isRotated90: false,
      eventTitle: '',
      intervalReminderMinutes: 0,
      preEndWarning: true,
      browserNotify: false,
      pomodoro: { ...POMODORO_DEFAULTS }
    },
    timerState: null,
    statistics: {
      totalFocusMinutes: 0,
      completedSessionsCount: 0,
      byDay: {},
      history: []
    }
  };
}

/**
 * Har qanday kirishni xavfsiz, normallashtirilgan holatga aylantiradi.
 * Noto'g'ri qiymatlar standartga qaytadi — buzilgan JSON ilovani o'ldirmaydi.
 */
export function normalizeState(raw) {
  const base = defaultState();
  if (!raw || typeof raw !== 'object') return base;

  // Eski (v1) format: sozlamalar ildizda yotgan
  const src = raw.settings && typeof raw.settings === 'object' ? raw : { settings: raw };
  const s = src.settings || {};
  const out = base;

  out.savedAt = typeof raw.savedAt === 'string' ? raw.savedAt : null;
  out.settings.lang = oneOf(s.lang, LANGS, base.settings.lang);
  out.settings.theme = oneOf(s.theme, THEMES, base.settings.theme);
  out.settings.font = oneOf(s.font, FONTS, base.settings.font);
  out.settings.volume = clamp(int(s.volume, DEFAULT_VOLUME), 0, 100);
  out.settings.alarmSound = oneOf(s.alarmSound, ALARM_SOUNDS, base.settings.alarmSound);
  out.settings.ambientSound = oneOf(s.ambientSound, AMBIENT_SOUNDS, base.settings.ambientSound);
  out.settings.showDays = bool(s.showDays, true);
  out.settings.wakeLockEnabled = bool(s.wakeLockEnabled, true);
  out.settings.autoRotatePortrait = bool(s.autoRotatePortrait, true);
  out.settings.edgeHoverEnabled = bool(s.edgeHoverEnabled, true);
  out.settings.isRotated90 = bool(s.isRotated90, false);
  out.settings.eventTitle = typeof s.eventTitle === 'string' ? s.eventTitle.slice(0, 60) : '';
  out.settings.intervalReminderMinutes = REMINDER_INTERVALS.includes(int(s.intervalReminderMinutes, 0))
    ? int(s.intervalReminderMinutes, 0) : 0;
  out.settings.preEndWarning = bool(s.preEndWarning, true);
  out.settings.browserNotify = bool(s.browserNotify, false);

  const p = s.pomodoro && typeof s.pomodoro === 'object' ? s.pomodoro : {};
  out.settings.pomodoro = {
    work: clamp(int(p.work, POMODORO_DEFAULTS.work), POMODORO_LIMITS.minPhase, POMODORO_LIMITS.maxPhase),
    shortBreak: clamp(int(p.shortBreak, POMODORO_DEFAULTS.shortBreak), POMODORO_LIMITS.minPhase, POMODORO_LIMITS.maxPhase),
    longBreak: clamp(int(p.longBreak, POMODORO_DEFAULTS.longBreak), POMODORO_LIMITS.minPhase, POMODORO_LIMITS.maxPhase),
    cyclesPerLongBreak: clamp(int(p.cyclesPerLongBreak, POMODORO_DEFAULTS.cyclesPerLongBreak),
      POMODORO_LIMITS.minCycles, POMODORO_LIMITS.maxCycles),
    autoStartNext: bool(p.autoStartNext, POMODORO_DEFAULTS.autoStartNext)
  };

  // Taymer holati: yurib turgan seansni tiklash uchun (engine o'zi tekshiradi)
  const ts = raw.timerState;
  if (ts && typeof ts === 'object') {
    out.timerState = {
      mode: oneOf(ts.mode, Object.values(MODES), MODES.DURATION),
      duration: ts.duration && typeof ts.duration === 'object' ? ts.duration : null,
      pomodoro: ts.pomodoro && typeof ts.pomodoro === 'object' ? ts.pomodoro : null,
      pomoPhase: typeof ts.pomoPhase === 'string' ? ts.pomoPhase : 'work',
      pomoCycles: Math.max(0, int(ts.pomoCycles, 0)),
      pomodoroConfig: out.settings.pomodoro,
      targetAt: Number.isFinite(Number(ts.targetAt)) ? Number(ts.targetAt) : null,
      targetFinished: bool(ts.targetFinished, false),
      stopwatch: ts.stopwatch && typeof ts.stopwatch === 'object' ? ts.stopwatch : null
    };
  }

  const st = raw.statistics && typeof raw.statistics === 'object' ? raw.statistics : {};
  out.statistics.totalFocusMinutes = Math.max(0, int(st.totalFocusMinutes, 0));
  out.statistics.completedSessionsCount = Math.max(0, int(st.completedSessionsCount, 0));
  out.statistics.byDay = {};
  if (st.byDay && typeof st.byDay === 'object') {
    for (const [key, val] of Object.entries(st.byDay)) {
      if (/^\d{4}-\d{2}-\d{2}$/.test(key)) out.statistics.byDay[key] = Math.max(0, int(val, 0));
    }
  }
  out.statistics.history = Array.isArray(st.history)
    ? st.history
      .filter((h) => h && typeof h === 'object')
      .slice(-MAX_HISTORY)
      .map((h) => ({
        id: int(h.id, Date.now()),
        timestamp: typeof h.timestamp === 'string' ? h.timestamp : new Date().toISOString(),
        type: typeof h.type === 'string' ? h.type.slice(0, 24) : 'duration',
        title: typeof h.title === 'string' ? h.title.slice(0, 120) : '',
        durationMinutes: Math.max(0, int(h.durationMinutes, 0))
      }))
    : [];

  out.version = SCHEMA_VERSION;
  return out;
}

/** Zenith zaxira fayliga o'xshaydimi? (import uchun) */
export function looksLikeBackup(raw) {
  if (!raw || typeof raw !== 'object') return false;
  return Boolean(raw.settings || raw.statistics || raw.timerState ||
    raw.theme || raw.font || raw.alarmSound);
}

export class Storage {
  /**
   * @param {{storage?:Storage, fetchFn?:Function, locationProtocol?:string, now?:()=>number}} [opts]
   */
  constructor(opts = {}) {
    this.ls = opts.storage !== undefined ? opts.storage : safeLocalStorage();
    this.fetchFn = opts.fetchFn !== undefined ? opts.fetchFn
      : (typeof fetch === 'function' ? fetch.bind(globalThis) : null);
    this.protocol = opts.locationProtocol ||
      (typeof location !== 'undefined' ? location.protocol : 'file:');
    this.now = opts.now || (() => Date.now());
    this._timer = null;
    this._pending = null;
    this.lastError = null;
    /**
     * Statik hostingda (masalan, nginx) `/api/data` yo'q.
     * Birinchi 404/405 dan keyin so'rovlar to'xtatiladi — har saqlashda
     * behuda so'rov yuborilmaydi va konsol xatolarga to'lmaydi.
     */
    this.serverAvailable = true;
  }

  get serverSyncEnabled() {
    return Boolean(this.fetchFn) && this.protocol.startsWith('http') && this.serverAvailable;
  }

  /** Server API'si yo'qligini bildiradigan javob kodlari */
  _noteResponse(res) {
    if (res && (res.status === 404 || res.status === 405 || res.status === 501)) {
      this.serverAvailable = false;
    }
    return res;
  }

  /** localStorage'dan o'qish + eski kalitlardan migratsiya */
  load() {
    if (!this.ls) return defaultState();
    let raw = null;
    try {
      raw = this.ls.getItem(STORAGE_KEY);
      if (!raw) {
        for (const legacy of LEGACY_STORAGE_KEYS) {
          const old = this.ls.getItem(legacy);
          if (old) { raw = old; break; }
        }
      }
    } catch (err) {
      this.lastError = err;
      return defaultState();
    }
    if (!raw) return defaultState();
    try {
      const state = normalizeState(JSON.parse(raw));
      this._dropLegacyKeys();
      return state;
    } catch (err) {
      this.lastError = err;
      return defaultState();
    }
  }

  _dropLegacyKeys() {
    if (!this.ls) return;
    for (const legacy of LEGACY_STORAGE_KEYS) {
      try { this.ls.removeItem(legacy); } catch { /* ahamiyatsiz */ }
    }
  }

  /** Darhol yozish (debounce'siz) */
  saveNow(state) {
    const payload = normalizeState(state);
    payload.savedAt = new Date(this.now()).toISOString();
    const json = JSON.stringify(payload);
    if (this.ls) {
      try { this.ls.setItem(STORAGE_KEY, json); } catch (err) { this.lastError = err; }
    }
    if (this.serverSyncEnabled) {
      this._postToServer(json);
    }
    return payload;
  }

  /** Debounce bilan yozish — tez-tez chaqirish xavfsiz */
  save(state) {
    this._pending = state;
    if (this._timer) return;
    this._timer = setTimeout(() => {
      this._timer = null;
      const pending = this._pending;
      this._pending = null;
      if (pending) this.saveNow(pending);
    }, SAVE_DEBOUNCE_MS);
  }

  /** Sahifa yopilishidan oldin kutayotgan yozuvni tashlab ketmaslik uchun */
  flush(state) {
    if (this._timer) {
      clearTimeout(this._timer);
      this._timer = null;
    }
    const data = state || this._pending;
    this._pending = null;
    if (data) this.saveNow(data);
  }

  _postToServer(json) {
    if (!this.fetchFn) return;
    const ctrl = typeof AbortController === 'function' ? new AbortController() : null;
    const timer = ctrl ? setTimeout(() => ctrl.abort(), API_TIMEOUT_MS) : null;
    Promise.resolve()
      .then(() => this.fetchFn(API_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json,
        signal: ctrl ? ctrl.signal : undefined
      }))
      .then((res) => this._noteResponse(res))
      .catch(() => { /* tarmoq uzilgan — keyingi safar qayta uriniladi */ })
      .finally(() => { if (timer) clearTimeout(timer); });
  }

  /**
   * Server omboridan o'qish. Server nusxasi yangiroq bo'lsa qaytaradi, aks holda null.
   * @param {string|null} localSavedAt
   */
  async fetchRemote(localSavedAt) {
    if (!this.serverSyncEnabled) return null;
    try {
      const ctrl = typeof AbortController === 'function' ? new AbortController() : null;
      const timer = ctrl ? setTimeout(() => ctrl.abort(), API_TIMEOUT_MS) : null;
      const res = await this.fetchFn(API_ENDPOINT, {
        headers: { Accept: 'application/json' },
        signal: ctrl ? ctrl.signal : undefined
      });
      if (timer) clearTimeout(timer);
      this._noteResponse(res);
      if (!res || !res.ok) return null;
      const raw = await res.json();
      if (!looksLikeBackup(raw)) return null;
      const remote = normalizeState(raw);
      if (!remote.savedAt) return null;
      if (localSavedAt && new Date(remote.savedAt) <= new Date(localSavedAt)) return null;
      return remote;
    } catch {
      return null;
    }
  }
}

/** localStorage mavjud bo'lmasa (private rejim, file://) ilovani yiqitmaydi */
export function safeLocalStorage() {
  try {
    if (typeof localStorage === 'undefined') return null;
    const probe = '__zenith_probe__';
    localStorage.setItem(probe, '1');
    localStorage.removeItem(probe);
    return localStorage;
  } catch {
    return null;
  }
}

/** Statistikaga bitta yakunlangan seansni qo'shadi */
export function recordSession(statistics, { focusMs, type, title, when = new Date() }) {
  const minutes = Math.round(focusMs / (MINUTE * 1000));
  if (minutes <= 0) return statistics;
  const key = dayKey(when);
  const next = {
    totalFocusMinutes: statistics.totalFocusMinutes + minutes,
    completedSessionsCount: statistics.completedSessionsCount + 1,
    byDay: { ...statistics.byDay, [key]: (statistics.byDay[key] || 0) + minutes },
    history: [
      ...statistics.history,
      {
        id: when.getTime(),
        timestamp: when.toISOString(),
        type,
        title,
        durationMinutes: minutes
      }
    ].slice(-MAX_HISTORY)
  };
  return next;
}

export function emptyStatistics() {
  return defaultState().statistics;
}
