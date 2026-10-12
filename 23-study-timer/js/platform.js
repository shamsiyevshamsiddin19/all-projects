/**
 * Brauzer platformasi bilan ishlash: to'liq ekran, WakeLock, orientatsiya, bildirishnomalar.
 * Har bir imkoniyat yo'q bo'lsa ham ilova ishlashda davom etadi.
 */
import { MOBILE_MAX_WIDTH } from './constants.js';

/* ------------------------------------------------------------- to'liq ekran */

export function isFullscreen() {
  if (typeof document === 'undefined') return false;
  return Boolean(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.mozFullScreenElement ||
    document.msFullscreenElement ||
    document.body.classList.contains('mobile-pseudo-fullscreen')
  );
}

export async function enterFullscreen() {
  const el = document.documentElement;
  const request = el.requestFullscreen || el.webkitRequestFullscreen ||
    el.mozRequestFullScreen || el.msRequestFullscreen;
  if (request) {
    try {
      await request.call(el);
      return true;
    } catch {
      // iOS Safari va ba'zi brauzerlar rad etadi — pseudo-fullscreen'ga tushamiz
    }
  }
  document.body.classList.add('mobile-pseudo-fullscreen');
  return false;
}

export async function exitFullscreen() {
  document.body.classList.remove('mobile-pseudo-fullscreen');
  const exit = document.exitFullscreen || document.webkitExitFullscreen ||
    document.mozCancelFullScreen || document.msExitFullscreen;
  if (exit) {
    try { await exit.call(document); } catch { /* allaqachon chiqilgan */ }
  }
}

export async function toggleFullscreen() {
  if (isFullscreen()) {
    await exitFullscreen();
    return false;
  }
  await enterFullscreen();
  return true;
}

export function onFullscreenChange(handler) {
  ['fullscreenchange', 'webkitfullscreenchange', 'mozfullscreenchange', 'MSFullscreenChange']
    .forEach((evt) => document.addEventListener(evt, handler));
}

/* ------------------------------------------------------------------ WakeLock */

export class WakeLockManager {
  constructor() {
    this.sentinel = null;
    this.enabled = false;
    this.supported = typeof navigator !== 'undefined' && 'wakeLock' in navigator;
  }

  /** Foydalanuvchi harakatidan keyin chaqirilsin — aks holda brauzer rad etadi */
  async request() {
    if (!this.supported || !this.enabled) return false;
    if (this.sentinel && !this.sentinel.released) return true;
    try {
      this.sentinel = await navigator.wakeLock.request('screen');
      this.sentinel.addEventListener?.('release', () => { this.sentinel = null; });
      return true;
    } catch {
      this.sentinel = null;
      return false;
    }
  }

  async release() {
    if (!this.sentinel) return;
    try { await this.sentinel.release(); } catch { /* allaqachon bo'shatilgan */ }
    this.sentinel = null;
  }

  setEnabled(enabled) {
    this.enabled = Boolean(enabled);
    if (this.enabled) return this.request();
    return this.release();
  }

  /** Sahifa yashirinib qaytganda tizim lock'ni bekor qiladi — qayta so'raymiz */
  async reacquire() {
    if (!this.enabled) return false;
    this.sentinel = null;
    return this.request();
  }
}

/* ------------------------------------------------------------- orientatsiya */

/** Haqiqiy mobil qurilmami? (touch-ekranli noutbuk mobil deb hisoblanmaydi) */
export function isMobileViewport() {
  if (typeof window === 'undefined') return false;
  const coarse = typeof window.matchMedia === 'function'
    ? window.matchMedia('(pointer: coarse)').matches
    : false;
  const narrow = window.innerWidth <= MOBILE_MAX_WIDTH;
  return coarse && narrow;
}

export function isPortrait() {
  if (typeof window === 'undefined') return false;
  return window.innerHeight > window.innerWidth;
}

/* ---------------------------------------------------------- bildirishnomalar */

export const notifications = {
  get supported() {
    return typeof window !== 'undefined' && 'Notification' in window;
  },
  get permission() {
    return this.supported ? Notification.permission : 'unsupported';
  },
  /** Faqat foydalanuvchi sozlamani yoqqanda chaqiriladi */
  async requestPermission() {
    if (!this.supported || Notification.permission !== 'default') return this.permission;
    try {
      return await Notification.requestPermission();
    } catch {
      return this.permission;
    }
  },
  show(title, body) {
    if (!this.supported || Notification.permission !== 'granted') return false;
    try {
      new Notification(title, { body, tag: 'zenith-timer', renotify: false });
      return true;
    } catch {
      return false;
    }
  }
};

/* ------------------------------------------------------------------ yordamchi */

export function debounce(fn, waitMs) {
  let timer = null;
  return (...args) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => { timer = null; fn(...args); }, waitMs);
  };
}

export function prefersReducedMotion() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** Service worker'ni ro'yxatdan o'tkazish (faqat http/https) */
export function registerServiceWorker(path = 'sw.js') {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
  if (!location.protocol.startsWith('http')) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(path).catch(() => { /* PWA ixtiyoriy */ });
  });
}
