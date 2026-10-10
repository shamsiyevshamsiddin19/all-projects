/**
 * Zenith Audio Engine — Pure Web Audio API Synthesizer
 * 100% Offline, Zero External MP3 Dependencies, High-Fidelity Audio Synthesis
 */

class ZenithAudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.ambientGain = null;
    this.ambientSources = [];
    this.volume = 0.8;
    this.currentAmbientType = 'none';
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);

      this.ambientGain = this.ctx.createGain();
      this.ambientGain.gain.setValueAtTime(0, this.ctx.currentTime);
      this.ambientGain.connect(this.masterGain);
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  setVolume(percent) {
    this.volume = Math.max(0, Math.min(1, percent / 100));
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.05);
    }
  }

  // --- ALARM SOUNDS ---

  playAlarm(type) {
    this.init();
    if (type === 'mute' || this.volume <= 0) return;

    switch (type) {
      case 'zen_bowl':
        this.playZenBowl();
        break;
      case 'soft_bell':
        this.playSoftBell();
        break;
      case 'digital_chime':
        this.playDigitalChime();
        break;
      case 'crystal':
        this.playCrystalGong();
        break;
      default:
        this.playZenBowl();
    }
  }

  /**
   * Zen Tibetan Singing Bowl (Harmonic overtone synthesis)
   */
  playZenBowl() {
    const fundamental = 261.63; // C4
    const partials = [
      { f: fundamental, g: 0.6, d: 4.5 },
      { f: fundamental * 2.76, g: 0.35, d: 3.8 },
      { f: fundamental * 5.4, g: 0.18, d: 2.8 },
      { f: fundamental * 8.9, g: 0.08, d: 1.8 }
    ];

    const now = this.ctx.currentTime;
    partials.forEach(({ f, g, d }) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(f, now);

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(g * 0.7, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + d);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(now);
      osc.stop(now + d);
    });
  }

  /**
   * Soft Bell (Clean modern acoustic bell)
   */
  playSoftBell() {
    const freqs = [880, 1760, 2640];
    const now = this.ctx.currentTime;

    freqs.forEach((f, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(f, now);

      const amp = idx === 0 ? 0.5 : 0.2 / (idx + 1);
      const dur = 2.5 - idx * 0.5;

      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(amp, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + dur);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(now);
      osc.stop(now + dur);
    });
  }

  /**
   * Digital Chime (Delightful ascending arpeggio)
   */
  playDigitalChime() {
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    const now = this.ctx.currentTime;

    notes.forEach((freq, idx) => {
      const noteTime = now + idx * 0.12;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, noteTime);

      gain.gain.setValueAtTime(0.0001, noteTime);
      gain.gain.exponentialRampToValueAtTime(0.35, noteTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteTime + 1.2);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(noteTime);
      osc.stop(noteTime + 1.2);
    });
  }

  /**
   * Crystal Gong (Metallic shimmer)
   */
  playCrystalGong() {
    const now = this.ctx.currentTime;
    const osc1 = this.ctx.createOscillator();
    const osc2 = this.ctx.createOscillator();
    const gain = this.ctx.createGain();

    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(440, now);

    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(445, now);

    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.4, now + 0.03);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 3.0);

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(this.masterGain);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + 3.0);
    osc2.stop(now + 3.0);
  }

  /**
   * Gentle Reminder Chime (Dual harmonic bell)
   */
  playReminderChime() {
    this.init();
    if (this.volume <= 0) return;
    const now = this.ctx.currentTime;
    [659.25, 880.0].forEach((freq, idx) => {
      const t = now + idx * 0.16;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0.0001, t);
      gain.gain.exponentialRampToValueAtTime(0.22, t + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.9);
      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start(t);
      osc.stop(t + 0.9);
    });
  }

  // --- AMBIENT FOCUS BACKGROUND GENERATOR ---

  setAmbient(type) {
    this.stopAmbient();
    this.currentAmbientType = type;
    if (type === 'none' || this.volume <= 0) return;

    this.init();

    switch (type) {
      case 'rain':
        this.startRainAmbient();
        break;
      case 'binaural':
        this.startBinauralAmbient();
        break;
      case 'space':
        this.startSpaceAmbient();
        break;
    }
  }

  stopAmbient() {
    if (this.ambientSources.length > 0 && this.ctx) {
      const now = this.ctx.currentTime;
      this.ambientGain.gain.setTargetAtTime(0, now, 0.3);
      setTimeout(() => {
        this.ambientSources.forEach(src => {
          try { src.stop(); src.disconnect(); } catch (_) {}
        });
        this.ambientSources = [];
      }, 400);
    }
  }

  /**
   * Soft rain generated via brown noise filter
   */
  startRainAmbient() {
    const bufferSize = 2 * this.ctx.sampleRate;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      output[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = output[i];
      output[i] *= 3.5;
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(800, this.ctx.currentTime);

    whiteNoise.connect(filter);
    filter.connect(this.ambientGain);

    this.ambientGain.gain.setTargetAtTime(0.25, this.ctx.currentTime, 0.5);
    whiteNoise.start();
    this.ambientSources.push(whiteNoise);
  }

  /**
   * 432Hz Deep Focus Binaural Beat (Alpha/Theta state)
   */
  startBinauralAmbient() {
    const oscLeft = this.ctx.createOscillator();
    const oscRight = this.ctx.createOscillator();
    const merger = this.ctx.createChannelMerger(2);

    oscLeft.type = 'sine';
    oscLeft.frequency.setValueAtTime(432, this.ctx.currentTime);

    oscRight.type = 'sine';
    oscRight.frequency.setValueAtTime(436, this.ctx.currentTime); // 4Hz difference = Theta waves

    oscLeft.connect(merger, 0, 0);
    oscRight.connect(merger, 0, 1);
    merger.connect(this.ambientGain);

    this.ambientGain.gain.setTargetAtTime(0.08, this.ctx.currentTime, 0.6);
    oscLeft.start();
    oscRight.start();
    this.ambientSources.push(oscLeft, oscRight);
  }

  /**
   * Cosmic Deep Space Drone
   */
  startSpaceAmbient() {
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
    filter.connect(this.ambientGain);

    this.ambientGain.gain.setTargetAtTime(0.07, this.ctx.currentTime, 0.5);
    osc1.start();
    osc2.start();
    this.ambientSources.push(osc1, osc2);
  }
}

// Global audio singleton
window.zenithAudio = new ZenithAudioEngine();
