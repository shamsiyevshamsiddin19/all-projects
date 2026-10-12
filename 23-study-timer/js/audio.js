/**
 * Zenith Audio Engine — Web Audio API sintezatori (tashqi audio fayl ishlatilmaydi).
 *
 * Tuzatilgan muammolar:
 *  - ovoz 0 bo'lganda ambient butunlay o'chib qolmaydi (master gain hal qiladi);
 *  - saqlangan ambient foydalanuvchining birinchi harakatidan keyin tiklanadi;
 *  - fon tabdan qaytganda AudioContext uyqudan chiqariladi (aks holda signal chalinmaydi);
 *  - yomg'ir shovqini uzun bufer + ikki pog'onali filtr bilan (loop artefakti kamayadi, clipping yo'q);
 *  - ambientni tez almashtirishdagi "poyga" generatsiya hisoblagichi bilan oldi olingan.
 */
import { AMBIENT_SOUNDS } from './constants.js';

const RAIN_BUFFER_SEC = 8;
const AMBIENT_LEVELS = { rain: 0.25, binaural: 0.08, space: 0.07 };

export class ZenithAudioEngine {
  constructor(opts = {}) {
    this.ctxFactory = opts.ctxFactory || (() => {
      const Ctor = globalThis.AudioContext || globalThis.webkitAudioContext;
      return Ctor ? new Ctor() : null;
    });
    this.ctx = null;
    this.masterGain = null;
    this.volume = 0.8;
    this.currentAmbientType = 'none';
    /** Avtoijro siyosati tufayli kutib turgan ambient */
    this.pendingAmbient = null;
    this._ambientGeneration = 0;
    this._ambientNodes = [];
    this._ambientGain = null;
    this._rainBuffer = null;
    this.unlocked = false;
  }

  get available() {
    return Boolean(this.ctx);
  }

  /** AudioContext yaratish/uyqudan chiqarish. Faqat foydalanuvchi harakatidan keyin chaqirilsin. */
  init() {
    if (!this.ctx) {
      this.ctx = this.ctxFactory();
      if (!this.ctx) return false;
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    }
    if (this.ctx.state === 'suspended' && typeof this.ctx.resume === 'function') {
      this.ctx.resume();
    }
    return true;
  }

  /** Birinchi foydalanuvchi harakati: kontekstni ochadi va kutayotgan ambientni yoqadi */
  unlock() {
    if (!this.init()) return false;
    this.unlocked = true;
    if (this.pendingAmbient && this.pendingAmbient !== 'none') {
      const type = this.pendingAmbient;
      this.pendingAmbient = null;
      this.setAmbient(type);
    }
    return true;
  }

  /** Sahifa ko'rinadigan holatga qaytganda chaqiriladi */
  resumeIfNeeded() {
    if (this.ctx && this.ctx.state === 'suspended' && typeof this.ctx.resume === 'function') {
      this.ctx.resume();
    }
  }

  setVolume(percent) {
    this.volume = Math.max(0, Math.min(1, Number(percent) / 100));
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.05);
    }
  }

  /* ----------------------------------------------------------- signal ovozlari */

  playAlarm(type) {
    if (type === 'mute') return false;
    if (!this.init()) return false;
    switch (type) {
      case 'soft_bell': this.playSoftBell(); break;
      case 'digital_chime': this.playDigitalChime(); break;
      case 'crystal': this.playCrystalGong(); break;
      case 'zen_bowl':
      default: this.playZenBowl(); break;
    }
    return true;
  }

  /** Tibet qo'ng'irog'i — overtone sintezi */
  playZenBowl() {
    const fundamental = 261.63; // C4
    const partials = [
      { f: fundamental, g: 0.6, d: 4.5 },
      { f: fundamental * 2.76, g: 0.35, d: 3.8 },
      { f: fundamental * 5.4, g: 0.18, d: 2.8 },
      { f: fundamental * 8.9, g: 0.08, d: 1.8 }
    ];
    const now = this.ctx.currentTime;
    for (const { f, g, d } of partials) {
      this._tone({ freq: f, type: 'sine', peak: g * 0.7, attack: 0.05, duration: d, at: now });
    }
  }

  playSoftBell() {
    const now = this.ctx.currentTime;
    [880, 1760, 2640].forEach((f, idx) => {
      this._tone({
        freq: f,
        type: 'sine',
        peak: idx === 0 ? 0.5 : 0.2 / (idx + 1),
        attack: 0.02,
        duration: 2.5 - idx * 0.5,
        at: now
      });
    });
  }

  playDigitalChime() {
    const now = this.ctx.currentTime;
    [523.25, 659.25, 783.99, 1046.5].forEach((freq, idx) => {
      this._tone({ freq, type: 'triangle', peak: 0.35, attack: 0.02, duration: 1.2, at: now + idx * 0.12 });
    });
  }

  playCrystalGong() {
    const now = this.ctx.currentTime;
    this._tone({ freq: 440, type: 'sine', peak: 0.4, attack: 0.03, duration: 3.0, at: now });
    this._tone({ freq: 445, type: 'triangle', peak: 0.3, attack: 0.03, duration: 3.0, at: now });
  }

  /** Mayin oraliq eslatma */
  playReminderChime() {
    if (!this.init()) return false;
    const now = this.ctx.currentTime;
    [659.25, 880.0].forEach((freq, idx) => {
      this._tone({ freq, type: 'sine', peak: 0.22, attack: 0.02, duration: 0.9, at: now + idx * 0.16 });
    });
    return true;
  }

  /** Bitta ohang — barcha signallar shu yordamchidan foydalanadi */
  _tone({ freq, type = 'sine', peak = 0.3, attack = 0.02, duration = 1, at }) {
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, at);
    gain.gain.setValueAtTime(0.0001, at);
    gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), at + attack);
    gain.gain.exponentialRampToValueAtTime(0.0001, at + duration);
    osc.connect(gain);
    gain.connect(this.masterGain);
    osc.start(at);
    osc.stop(at + duration);
  }

  /* ------------------------------------------------------------------ ambient */

  /**
   * Orqa fon tovushini o'rnatadi. Ovoz 0 bo'lsa ham manbalar ishga tushadi —
   * foydalanuvchi ovozni ko'targanda darhol eshitiladi.
   */
  setAmbient(type) {
    const next = AMBIENT_SOUNDS.includes(type) ? type : 'none';
    this.currentAmbientType = next;
    this.stopAmbient();
    if (next === 'none') {
      this.pendingAmbient = null;
      return false;
    }
    if (!this.unlocked && (!this.ctx || this.ctx.state === 'suspended')) {
      // Avtoijro siyosati: birinchi bosishgacha kutamiz
      this.pendingAmbient = next;
      return false;
    }
    if (!this.init()) {
      this.pendingAmbient = next;
      return false;
    }

    const generation = ++this._ambientGeneration;
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.0001, this.ctx.currentTime);
    gain.connect(this.masterGain);
    this._ambientGain = gain;

    const nodes = [];
    if (next === 'rain') nodes.push(...this._buildRain(gain));
    else if (next === 'binaural') nodes.push(...this._buildBinaural(gain));
    else if (next === 'space') nodes.push(...this._buildSpace(gain));

    if (generation !== this._ambientGeneration) {
      nodes.forEach((n) => { try { n.stop(); n.disconnect(); } catch { /* allaqachon to'xtagan */ } });
      return false;
    }

    gain.gain.setTargetAtTime(AMBIENT_LEVELS[next] || 0.1, this.ctx.currentTime, 0.5);
    nodes.forEach((n) => n.start());
    this._ambientNodes = nodes;
    return true;
  }

  stopAmbient() {
    this._ambientGeneration += 1;
    const nodes = this._ambientNodes;
    const gain = this._ambientGain;
    this._ambientNodes = [];
    this._ambientGain = null;
    if (!this.ctx || (nodes.length === 0 && !gain)) return;
    if (gain) gain.gain.setTargetAtTime(0.0001, this.ctx.currentTime, 0.25);
    setTimeout(() => {
      nodes.forEach((n) => { try { n.stop(); n.disconnect(); } catch { /* allaqachon to'xtagan */ } });
      if (gain) { try { gain.disconnect(); } catch { /* allaqachon uzilgan */ } }
    }, 400);
  }

  /** Uzun brown-noise buferi: normallashtirilgan, clipping yo'q */
  _rainNoiseBuffer() {
    if (this._rainBuffer) return this._rainBuffer;
    const length = Math.floor(RAIN_BUFFER_SEC * this.ctx.sampleRate);
    const buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let last = 0;
    let peak = 0;
    for (let i = 0; i < length; i += 1) {
      const white = Math.random() * 2 - 1;
      last = (last + 0.02 * white) / 1.02;
      data[i] = last;
      const abs = Math.abs(last);
      if (abs > peak) peak = abs;
    }
    // Normalizatsiya: 3.5 ga ko'paytirish clipping berardi
    const norm = peak > 0 ? 0.9 / peak : 1;
    for (let i = 0; i < length; i += 1) data[i] *= norm;
    // Loop chokini yumshatish uchun kichik cross-fade
    const fade = Math.min(2048, Math.floor(length / 10));
    for (let i = 0; i < fade; i += 1) {
      const k = i / fade;
      data[i] = data[i] * k + data[length - fade + i] * (1 - k);
    }
    this._rainBuffer = buffer;
    return buffer;
  }

  _buildRain(target) {
    const src = this.ctx.createBufferSource();
    src.buffer = this._rainNoiseBuffer();
    src.loop = true;

    const lp1 = this.ctx.createBiquadFilter();
    lp1.type = 'lowpass';
    lp1.frequency.setValueAtTime(900, this.ctx.currentTime);
    const lp2 = this.ctx.createBiquadFilter();
    lp2.type = 'lowpass';
    lp2.frequency.setValueAtTime(1800, this.ctx.currentTime);

    src.connect(lp1);
    lp1.connect(lp2);
    lp2.connect(target);
    return [src];
  }

  _buildBinaural(target) {
    const left = this.ctx.createOscillator();
    const right = this.ctx.createOscillator();
    const merger = this.ctx.createChannelMerger(2);
    left.type = 'sine';
    left.frequency.setValueAtTime(432, this.ctx.currentTime);
    right.type = 'sine';
    right.frequency.setValueAtTime(436, this.ctx.currentTime); // 4 Hz farq
    left.connect(merger, 0, 0);
    right.connect(merger, 0, 1);
    merger.connect(target);
    return [left, right];
  }

  _buildSpace(target) {
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(108, this.ctx.currentTime);
    osc2.type = 'sawtooth';
    osc2.frequency.setValueAtTime(162, this.ctx.currentTime);
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(250, this.ctx.currentTime);
    filter.Q.setValueAtTime(3, this.ctx.currentTime);
    osc1.connect(filter);
    osc2.connect(filter);
    filter.connect(target);
    return [osc1, osc2];
  }
}

export const zenithAudio = new ZenithAudioEngine();
if (typeof window !== 'undefined') {
  window.zenithAudio = zenithAudio;
}
