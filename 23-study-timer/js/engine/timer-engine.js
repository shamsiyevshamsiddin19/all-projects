/**
 * TimerEngine — barcha rejimlarning holati va mantig'i.
 * To'liq sof: DOM, audio va localStorage'ga murojaat qilmaydi (shu sabab test qilinadi).
 *
 * Har bir rejim o'z holatini saqlaydi — rejim almashtirish boshqa rejimdagi
 * yurib turgan taymerni o'chirmaydi.
 */
import {
  MS, MINUTE, MODES, POMODORO_PHASES, POMODORO_DEFAULTS, POMODORO_LIMITS,
  MAX_DURATION, MAX_LAPS, DEFAULT_DURATION
} from '../constants.js';
import { Countdown } from './countdown.js';

const clamp = (v, min, max) => Math.min(max, Math.max(min, v));

export class TimerEngine {
  /**
   * @param {{now?:()=>number, pomodoro?:object, reminders?:object}} [opts]
   */
  constructor(opts = {}) {
    this.now = opts.now || (() => Date.now());
    this.mode = MODES.DURATION;

    this.pomodoroConfig = { ...POMODORO_DEFAULTS, ...(opts.pomodoro || {}) };
    this.reminders = {
      intervalMinutes: 0,
      preEndWarning: true,
      ...(opts.reminders || {})
    };

    /** Davomiylik rejimi */
    this.duration = new Countdown(0);
    /** Pomodoro rejimi */
    this.pomodoro = new Countdown(this.pomodoroConfig.work * MS);
    this.pomoPhase = POMODORO_PHASES.WORK;
    this.pomoCycles = 0;
    /** Sekundomer */
    this.stopwatch = { elapsedMs: 0, startedAt: null, running: false, remindersFired: 0, laps: [] };
  }

  /* ---------------------------------------------------------------- rejimlar */

  setMode(mode) {
    if (!Object.values(MODES).includes(mode)) return this;
    this.mode = mode;
    return this;
  }

  /** Hozirgi rejim orqaga sanaydimi? */
  isCountdownMode(mode = this.mode) {
    return mode === MODES.DURATION || mode === MODES.POMODORO;
  }

  /** Hozirgi rejimning Countdown obyekti (bo'lsa) */
  activeCountdown(mode = this.mode) {
    if (mode === MODES.DURATION) return this.duration;
    if (mode === MODES.POMODORO) return this.pomodoro;
    return null;
  }

  get isRunning() {
    switch (this.mode) {
      case MODES.DURATION: return this.duration.running;
      case MODES.POMODORO: return this.pomodoro.running;
      case MODES.STOPWATCH: return this.stopwatch.running;
      case MODES.CLOCK: return true;
      default: return false;
    }
  }

  /* ------------------------------------------------------- davomiylik rejimi */

  /** Kiritilgan davomiylikni o'rnatadi (soniyada). Yurib turgan taymer buzilmaydi. */
  setConfiguredDuration(totalSec, { applyNow = null } = {}) {
    const total = clamp(Math.floor(Number(totalSec) || 0), 0, MAX_DURATION) * MS;
    const apply = applyNow === null ? !this.duration.running : applyNow;
    if (apply) {
      this.duration.reset(total);
    } else {
      // Yurib turgan taymerning qolgan vaqtiga tegilmaydi — faqat keyingi seans uchun
      this.duration.totalMs = Math.max(total, this.duration.remaining(this.now()));
    }
    return this;
  }

  get configuredDurationSec() {
    return Math.round(this.duration.totalMs / MS);
  }

  /* ---------------------------------------------------------------- pomodoro */

  setPomodoroConfig(patch = {}) {
    const next = { ...this.pomodoroConfig };
    for (const key of ['work', 'shortBreak', 'longBreak']) {
      if (patch[key] !== undefined) {
        next[key] = clamp(Math.floor(Number(patch[key]) || 0), POMODORO_LIMITS.minPhase, POMODORO_LIMITS.maxPhase);
      }
    }
    if (patch.cyclesPerLongBreak !== undefined) {
      next.cyclesPerLongBreak = clamp(
        Math.floor(Number(patch.cyclesPerLongBreak) || 0),
        POMODORO_LIMITS.minCycles, POMODORO_LIMITS.maxCycles
      );
    }
    if (patch.autoStartNext !== undefined) next.autoStartNext = Boolean(patch.autoStartNext);
    this.pomodoroConfig = next;

    if (!this.pomodoro.running) {
      this.pomodoro.reset(this.phaseDurationMs(this.pomoPhase));
    }
    return this;
  }

  phaseDurationMs(phase) {
    const map = {
      [POMODORO_PHASES.WORK]: this.pomodoroConfig.work,
      [POMODORO_PHASES.SHORT_BREAK]: this.pomodoroConfig.shortBreak,
      [POMODORO_PHASES.LONG_BREAK]: this.pomodoroConfig.longBreak
    };
    return (map[phase] || this.pomodoroConfig.work) * MS;
  }

  switchPomoPhase(phase, { autoStart = false } = {}) {
    if (!Object.values(POMODORO_PHASES).includes(phase)) return this;
    this.pomoPhase = phase;
    this.pomodoro.reset(this.phaseDurationMs(phase));
    if (autoStart) this.pomodoro.start(this.now());
    return this;
  }

  resetPomoCycles() {
    this.pomoCycles = 0;
    return this;
  }

  /* -------------------------------------------------------------- sekundomer */

  stopwatchElapsed(now = this.now()) {
    const sw = this.stopwatch;
    const live = sw.running && sw.startedAt !== null ? now - sw.startedAt : 0;
    return Math.max(0, sw.elapsedMs + live);
  }

  addLap(now = this.now()) {
    const sw = this.stopwatch;
    const total = this.stopwatchElapsed(now);
    const prev = sw.laps.length > 0 ? sw.laps[sw.laps.length - 1].totalMs : 0;
    sw.laps.push({ index: sw.laps.length + 1, totalMs: total, splitMs: total - prev });
    if (sw.laps.length > MAX_LAPS) sw.laps.shift();
    return sw.laps[sw.laps.length - 1];
  }

  clearLaps() {
    this.stopwatch.laps = [];
    return this;
  }

  /* -------------------------------------------------------- umumiy boshqaruv */

  start() {
    const now = this.now();
    switch (this.mode) {
      case MODES.DURATION:
        if (this.duration.totalMs <= 0) this.duration.reset(DEFAULT_DURATION * MS);
        this.duration.start(now);
        break;
      case MODES.POMODORO:
        if (this.pomodoro.totalMs <= 0) this.pomodoro.reset(this.phaseDurationMs(this.pomoPhase));
        this.pomodoro.start(now);
        break;
      case MODES.STOPWATCH:
        if (!this.stopwatch.running) {
          this.stopwatch.startedAt = now;
          this.stopwatch.running = true;
        }
        break;
      default:
        break;
    }
    return this;
  }

  pause() {
    const now = this.now();
    switch (this.mode) {
      case MODES.DURATION: this.duration.pause(now); break;
      case MODES.POMODORO: this.pomodoro.pause(now); break;
      case MODES.STOPWATCH:
        if (this.stopwatch.running) {
          this.stopwatch.elapsedMs = this.stopwatchElapsed(now);
          this.stopwatch.startedAt = null;
          this.stopwatch.running = false;
        }
        break;
      default: break;
    }
    return this;
  }

  toggle() {
    return this.isRunning ? this.pause() : this.start();
  }

  /** Hozirgi rejimni boshlang'ich holatga qaytaradi */
  reset() {
    switch (this.mode) {
      case MODES.DURATION:
        this.duration.reset(this.duration.totalMs);
        break;
      case MODES.POMODORO:
        this.pomodoro.reset(this.phaseDurationMs(this.pomoPhase));
        break;
      case MODES.STOPWATCH:
        this.stopwatch.elapsedMs = 0;
        this.stopwatch.startedAt = null;
        this.stopwatch.running = false;
        this.stopwatch.remindersFired = 0;
        this.stopwatch.laps = [];
        break;
      default: break;
    }
    return this;
  }

  /** Vaqt qo'shish / ayirish (ms) */
  adjust(deltaMs) {
    const now = this.now();
    const cd = this.activeCountdown();
    if (cd) cd.adjust(deltaMs, now);
    return this;
  }

  /* ----------------------------------------------------------------- yuritish */

  /**
   * Bir qadam. Hodisalar ro'yxatini qaytaradi.
   * Chaqirish chastotasi natijaga ta'sir qilmaydi.
   */
  tick() {
    const now = this.now();
    const events = [];

    if (this.mode === MODES.DURATION) {
      for (const ev of this.duration.tick(now, this.reminders)) {
        events.push({ ...ev, mode: MODES.DURATION });
      }
    } else if (this.mode === MODES.POMODORO) {
      for (const ev of this.pomodoro.tick(now, { ...this.reminders, intervalMinutes: 0 })) {
        if (ev.type !== 'finished') {
          events.push({ ...ev, mode: MODES.POMODORO, phase: this.pomoPhase });
          continue;
        }
        const finishedPhase = this.pomoPhase;
        let nextPhase;
        if (finishedPhase === POMODORO_PHASES.WORK) {
          this.pomoCycles += 1;
          nextPhase = this.pomoCycles % this.pomodoroConfig.cyclesPerLongBreak === 0
            ? POMODORO_PHASES.LONG_BREAK
            : POMODORO_PHASES.SHORT_BREAK;
        } else {
          nextPhase = POMODORO_PHASES.WORK;
        }
        events.push({
          ...ev,
          mode: MODES.POMODORO,
          phase: finishedPhase,
          cycles: this.pomoCycles,
          // Faqat ish bosqichi fokus vaqti sifatida hisoblanadi
          focusMs: finishedPhase === POMODORO_PHASES.WORK ? ev.focusMs : 0,
          nextPhase
        });
        this.switchPomoPhase(nextPhase, { autoStart: this.pomodoroConfig.autoStartNext });
        events.push({ type: 'phaseChange', mode: MODES.POMODORO, phase: nextPhase });
      }
    } else if (this.mode === MODES.STOPWATCH && this.stopwatch.running) {
      const elapsed = this.stopwatchElapsed(now);
      const interval = Number(this.reminders.intervalMinutes) || 0;
      if (interval > 0) {
        const stepMs = interval * MINUTE * MS;
        const reached = Math.floor(elapsed / stepMs);
        if (reached > this.stopwatch.remindersFired) {
          this.stopwatch.remindersFired = reached;
          events.push({
            type: 'interval',
            mode: MODES.STOPWATCH,
            minutes: Math.round((reached * stepMs) / (MINUTE * MS)),
            elapsedMs: elapsed
          });
        }
      }
    }

    return events;
  }

  /**
   * Ekranga chiqarish uchun hozirgi holat surati.
   * @returns {{mode:string, running:boolean, remainingMs:number, elapsedMs:number,
   *            totalMs:number, phase:string, cycles:number, progress:number}}
   */
  sample(now = this.now()) {
    const base = {
      mode: this.mode,
      running: this.isRunning,
      phase: this.pomoPhase,
      cycles: this.pomoCycles,
      cyclesPerLongBreak: this.pomodoroConfig.cyclesPerLongBreak,
      laps: this.stopwatch.laps,
      finished: false
    };

    switch (this.mode) {
      case MODES.DURATION: {
        const remaining = this.duration.remaining(now);
        return {
          ...base,
          remainingMs: remaining,
          elapsedMs: this.duration.elapsed(now),
          totalMs: this.duration.totalMs,
          progress: this.duration.totalMs > 0 ? 1 - remaining / this.duration.totalMs : 0,
          finished: this.duration.totalMs > 0 && remaining <= 0 && !this.duration.running
        };
      }
      case MODES.POMODORO: {
        const remaining = this.pomodoro.remaining(now);
        return {
          ...base,
          remainingMs: remaining,
          elapsedMs: this.pomodoro.elapsed(now),
          totalMs: this.pomodoro.totalMs,
          progress: this.pomodoro.totalMs > 0 ? 1 - remaining / this.pomodoro.totalMs : 0
        };
      }
      case MODES.STOPWATCH: {
        const elapsed = this.stopwatchElapsed(now);
        return { ...base, remainingMs: elapsed, elapsedMs: elapsed, totalMs: 0, progress: 0 };
      }
      case MODES.CLOCK:
      default:
        return { ...base, remainingMs: 0, elapsedMs: 0, totalMs: 0, progress: 0 };
    }
  }

  /* ------------------------------------------------------------- saqlash/tiklash */

  serialize() {
    return {
      mode: this.mode,
      duration: this.duration.serialize(),
      pomodoro: this.pomodoro.serialize(),
      pomoPhase: this.pomoPhase,
      pomoCycles: this.pomoCycles,
      pomodoroConfig: { ...this.pomodoroConfig },
      stopwatch: {
        elapsedMs: this.stopwatchElapsed(),
        running: this.stopwatch.running,
        startedAt: this.stopwatch.running ? this.stopwatch.startedAt : null,
        laps: this.stopwatch.laps.slice(-MAX_LAPS)
      }
    };
  }

  /**
   * Saqlangan holatni tiklaydi.
   * @returns {{missedFinish:boolean, restoredRunning:boolean}}
   */
  restore(raw) {
    if (!raw || typeof raw !== 'object') return { missedFinish: false, restoredRunning: false };
    const now = this.now();
    let missedFinish = false;

    if (raw.pomodoroConfig) this.setPomodoroConfig(raw.pomodoroConfig);
    if (Object.values(MODES).includes(raw.mode)) this.mode = raw.mode;
    if (Object.values(POMODORO_PHASES).includes(raw.pomoPhase)) this.pomoPhase = raw.pomoPhase;
    this.pomoCycles = Math.max(0, Number(raw.pomoCycles) || 0);

    const dur = Countdown.restore(raw.duration, now);
    this.duration = dur.countdown;
    missedFinish = missedFinish || (dur.missedFinish && raw.mode === MODES.DURATION);

    const pomo = Countdown.restore(raw.pomodoro, now);
    this.pomodoro = pomo.countdown;
    if (this.pomodoro.totalMs <= 0) this.pomodoro.reset(this.phaseDurationMs(this.pomoPhase));
    missedFinish = missedFinish || (pomo.missedFinish && raw.mode === MODES.POMODORO);

    if (raw.stopwatch && typeof raw.stopwatch === 'object') {
      const swElapsed = Math.max(0, Number(raw.stopwatch.elapsedMs) || 0);
      this.stopwatch.laps = Array.isArray(raw.stopwatch.laps) ? raw.stopwatch.laps.slice(-MAX_LAPS) : [];
      if (raw.stopwatch.running && Number.isFinite(Number(raw.stopwatch.startedAt))) {
        // Sekundomer sahifa yopiq turgan vaqtni ham sanaydi
        this.stopwatch.elapsedMs = swElapsed;
        this.stopwatch.startedAt = Number(raw.stopwatch.startedAt);
        this.stopwatch.running = true;
      } else {
        this.stopwatch.elapsedMs = swElapsed;
        this.stopwatch.running = false;
        this.stopwatch.startedAt = null;
      }
    }

    return { missedFinish, restoredRunning: this.isRunning };
  }
}
