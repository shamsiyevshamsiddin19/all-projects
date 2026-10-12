/**
 * Countdown — timestamp asosidagi orqaga sanash yadrosi.
 *
 * Muhim: qolgan vaqt HECH QACHON tick sanog'i bilan hisoblanmaydi.
 * Har doim `endsAt - now` dan olinadi, shu sabab:
 *   - brauzer fon tabida `setInterval`ni sekinlashtirsa ham vaqt to'g'ri qoladi;
 *   - sahifa yangilansa holat timestamp'dan tiklanadi;
 *   - tick chastotasi aniqlikka ta'sir qilmaydi.
 */
import { MS, MINUTE, PRE_END_WARNING_SEC } from '../constants.js';

export class Countdown {
  constructor(totalMs = 0) {
    this.totalMs = Math.max(0, totalMs);
    this.remainingMs = this.totalMs;
    this.endsAt = null;
    this.running = false;
    /** Shu seansda haqiqatda yurgan vaqt (pauzalar hisobga olinmaydi) */
    this.runMs = 0;
    this.lastRunStart = null;
    this.warnedPreEnd = false;
    this.remindersFired = 0;
  }

  /** Qolgan vaqt (ms) */
  remaining(now) {
    if (this.running && this.endsAt !== null) {
      return Math.max(0, this.endsAt - now);
    }
    return Math.max(0, this.remainingMs);
  }

  /** O'tgan vaqt (ms) — umumiydan qolganini ayirish */
  elapsed(now) {
    return Math.max(0, this.totalMs - this.remaining(now));
  }

  /** Haqiqatda yurgan vaqt (statistika uchun) */
  activeRunMs(now) {
    const live = this.running && this.lastRunStart !== null ? now - this.lastRunStart : 0;
    return Math.min(this.totalMs, Math.max(0, this.runMs + live));
  }

  isFinished(now) {
    return this.totalMs > 0 && this.remaining(now) <= 0;
  }

  /**
   * Yangi davomiylik bilan to'liq tiklash.
   * Eslatma bayroqlari ham tozalanadi — bu 'warnedPreEnd hech qachon tiklanmaydi'
   * xatosining tomiri edi.
   */
  reset(totalMs = this.totalMs) {
    this.totalMs = Math.max(0, totalMs);
    this.remainingMs = this.totalMs;
    this.endsAt = null;
    this.running = false;
    this.runMs = 0;
    this.lastRunStart = null;
    this.warnedPreEnd = false;
    this.remindersFired = 0;
    return this;
  }

  start(now) {
    if (this.running) return this;
    if (this.remainingMs <= 0) this.reset(this.totalMs);
    if (this.totalMs <= 0) return this;
    this.endsAt = now + this.remainingMs;
    this.lastRunStart = now;
    this.running = true;
    return this;
  }

  pause(now) {
    if (!this.running) return this;
    this.remainingMs = this.remaining(now);
    if (this.lastRunStart !== null) {
      this.runMs = Math.min(this.totalMs, this.runMs + (now - this.lastRunStart));
    }
    this.endsAt = null;
    this.lastRunStart = null;
    this.running = false;
    return this;
  }

  toggle(now) {
    return this.running ? this.pause(now) : this.start(now);
  }

  /** +/- vaqt qo'shish. Umumiy vaqt qolganidan kichik bo'lib qolmaydi. */
  adjust(deltaMs, now) {
    const rem = this.remaining(now);
    const nextRem = Math.max(0, rem + deltaMs);
    this.totalMs = Math.max(this.totalMs + deltaMs, nextRem);
    if (this.totalMs <= 0) this.totalMs = nextRem;
    if (this.running) {
      this.endsAt = now + nextRem;
      this.remainingMs = nextRem;
      if (nextRem <= 0) this.endsAt = now;
    } else {
      this.remainingMs = nextRem;
    }
    // Vaqt qo'shilsa, oldin chalingan "1 daqiqa qoldi" yana mazmunli bo'ladi
    if (deltaMs > 0 && nextRem > PRE_END_WARNING_SEC * MS) {
      this.warnedPreEnd = false;
    }
    return this;
  }

  /**
   * Bir tick: o'tgan chegaralarni tekshiradi va hodisalar ro'yxatini qaytaradi.
   * Hodisalar bir martalik — tick qancha kechikkanidan qat'i nazar takrorlanmaydi.
   *
   * @param {number} now
   * @param {{intervalMinutes:number, preEndWarning:boolean}} opts
   */
  tick(now, opts = {}) {
    const events = [];
    if (!this.running) return events;

    const intervalMinutes = Number(opts.intervalMinutes) || 0;
    const remainingMs = this.remaining(now);
    const elapsedMs = this.elapsed(now);

    if (intervalMinutes > 0) {
      const stepMs = intervalMinutes * MINUTE * MS;
      const reached = Math.floor(elapsedMs / stepMs);
      if (reached > this.remindersFired) {
        this.remindersFired = reached;
        events.push({
          type: 'interval',
          minutes: Math.round((reached * stepMs) / (MINUTE * MS)),
          elapsedMs
        });
      }
    }

    if (opts.preEndWarning && !this.warnedPreEnd && remainingMs > 0 &&
        remainingMs <= PRE_END_WARNING_SEC * MS) {
      this.warnedPreEnd = true;
      events.push({ type: 'preEnd', remainingMs });
    }

    if (remainingMs <= 0) {
      const focusMs = this.activeRunMs(now);
      this.pause(now);
      this.remainingMs = 0;
      events.push({ type: 'finished', focusMs, nominalMs: this.totalMs });
    }

    return events;
  }

  serialize() {
    return {
      totalMs: this.totalMs,
      remainingMs: this.remainingMs,
      endsAt: this.endsAt,
      running: this.running,
      runMs: this.runMs,
      lastRunStart: this.lastRunStart,
      warnedPreEnd: this.warnedPreEnd,
      remindersFired: this.remindersFired
    };
  }

  /**
   * Saqlangan holatdan tiklash.
   * Yurib turgan taymer sahifa yangilangandan keyin ham davom etadi —
   * `endsAt` o'tib ketgan bo'lsa "o'tkazib yuborilgan tugash" deb belgilanadi.
   */
  static restore(raw, now) {
    const cd = new Countdown(0);
    if (!raw || typeof raw !== 'object') return { countdown: cd, missedFinish: false };

    cd.totalMs = Math.max(0, Number(raw.totalMs) || 0);
    cd.remainingMs = Math.max(0, Number(raw.remainingMs) || 0);
    cd.runMs = Math.max(0, Number(raw.runMs) || 0);
    cd.warnedPreEnd = Boolean(raw.warnedPreEnd);
    cd.remindersFired = Math.max(0, Number(raw.remindersFired) || 0);

    let missedFinish = false;
    if (raw.running && Number.isFinite(Number(raw.endsAt))) {
      const endsAt = Number(raw.endsAt);
      if (endsAt > now) {
        cd.endsAt = endsAt;
        cd.remainingMs = endsAt - now;
        cd.lastRunStart = now;
        cd.running = true;
      } else {
        cd.remainingMs = 0;
        cd.running = false;
        missedFinish = cd.totalMs > 0;
      }
    }
    return { countdown: cd, missedFinish };
  }
}
