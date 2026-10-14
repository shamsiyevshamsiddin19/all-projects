/**
 * Yagona audio dvigatel.
 *
 * Nega React komponenti emas, modul darajasidagi singleton:
 *
 * 1. Mobil brauzerlarning autoplay siyosati `play()` ni FAQAT foydalanuvchi
 *    harakati zanjirida ruxsat beradi. Oldin `play()` `fetch(...).then()`
 *    ichida chaqirilardi — zanjir uzilib, mobil qurilmalarda ijro bloklanardi.
 *    Bu yerda `play()` bosish hodisasining o'zida, hech qanday await'siz
 *    bajariladi.
 *
 * 2. `<audio>` elementi React daraxtidan tashqarida yashaydi, shuning uchun
 *    sahifalar orasida yurganda unmount bo'lmaydi va musiqa uzilmaydi.
 */

type Listener = {
  onPlaying?: () => void;
  onWaiting?: () => void;
  onError?: (reason: 'error' | 'stalled') => void;
  onPause?: () => void;
};

// Oqim qotib qolsa brauzer ko'pincha `error` bermaydi — shunchaki jim turadi.
// Shuning uchun o'zimiz vaqt o'lchaymiz.
const STALL_TIMEOUT_MS = 30_000;

class AudioEngine {
  private audio: HTMLAudioElement | null = null;
  private listener: Listener = {};
  private stallTimer: ReturnType<typeof setTimeout> | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private sourceNode: MediaElementAudioSourceNode | null = null;

  private ensureAudio(): HTMLAudioElement {
    if (this.audio) return this.audio;

    const audio = new Audio();
    audio.preload = 'none';
    // Web Audio API bilan spektr o'qish uchun SHART. Busiz cross-origin
    // oqimda AnalyserNode faqat nol qaytaradi.
    audio.crossOrigin = 'anonymous';

    audio.addEventListener('playing', () => {
      this.clearStallTimer();
      this.listener.onPlaying?.();
    });
    audio.addEventListener('waiting', () => {
      this.armStallTimer();
      this.listener.onWaiting?.();
    });
    audio.addEventListener('stalled', () => this.armStallTimer());
    audio.addEventListener('pause', () => {
      this.clearStallTimer();
      this.listener.onPause?.();
    });
    audio.addEventListener('error', () => {
      this.clearStallTimer();
      this.listener.onError?.('error');
    });

    this.audio = audio;
    return audio;
  }

  private armStallTimer(): void {
    this.clearStallTimer();
    this.stallTimer = setTimeout(() => {
      this.listener.onError?.('stalled');
    }, STALL_TIMEOUT_MS);
  }

  private clearStallTimer(): void {
    if (this.stallTimer !== null) {
      clearTimeout(this.stallTimer);
      this.stallTimer = null;
    }
  }

  setListener(listener: Listener): void {
    this.listener = listener;
  }

  /**
   * Oqimni boshlaydi. Bosish hodisasidan SINXRON chaqirilishi kerak —
   * oldidan `await` qo'yilsa mobil autoplay siyosati bloklaydi.
   */
  play(url: string, volume: number): void {
    const audio = this.ensureAudio();
    if (audio.src !== url) {
      audio.src = url;
    }
    audio.volume = volume;
    this.armStallTimer();

    const promise = audio.play();
    if (promise) {
      promise.catch((err: DOMException) => {
        this.clearStallTimer();
        // NotAllowedError = foydalanuvchi harakati yetishmadi (xato emas,
        // shunchaki yana bosish kerak). Qolgani oqim muammosi.
        if (err?.name !== 'NotAllowedError') {
          this.listener.onError?.('error');
        } else {
          this.listener.onPause?.();
        }
      });
    }
  }

  resume(volume: number): void {
    const audio = this.audio;
    if (!audio?.src) return;
    audio.volume = volume;
    this.armStallTimer();
    audio.play()?.catch(() => this.listener.onPause?.());
  }

  pause(): void {
    this.clearStallTimer();
    this.audio?.pause();
  }

  setVolume(volume: number): void {
    if (this.audio) this.audio.volume = volume;
  }

  /**
   * Haqiqiy spektr tahlilchisi.
   *
   * Dizayn muhokamasida kelishilganidek, ekvalayzer bezak emas — u aynan
   * eshitilayotgan ovozdan o'qiydi. AudioContext faqat foydalanuvchi
   * harakatidan keyin yaratiladi (brauzer talabi).
   */
  getAnalyser(): AnalyserNode | null {
    if (!this.audio) return null;
    if (this.analyser) return this.analyser;

    try {
      const Ctx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!Ctx) return null;

      this.audioContext = new Ctx();
      this.sourceNode = this.audioContext.createMediaElementSource(this.audio);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      this.analyser.smoothingTimeConstant = 0.75;

      this.sourceNode.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
      return this.analyser;
    } catch {
      // CORS yo'q yoki Web Audio qo'llab-quvvatlanmaydi — vizualizator
      // oddiy animatsiyaga tushadi, ijro esa davom etaveradi.
      this.analyser = null;
      return null;
    }
  }

  resumeContext(): void {
    if (this.audioContext?.state === 'suspended') {
      void this.audioContext.resume();
    }
  }
}

export const audioEngine = new AudioEngine();
