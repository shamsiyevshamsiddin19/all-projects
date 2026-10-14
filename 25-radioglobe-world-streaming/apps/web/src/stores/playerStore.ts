import { create } from 'zustand';

import type { Channel, Country, StreamInfo } from '@/types';

const FAVORITES_KEY = 'rg_favorites';
const VOLUME_KEY = 'rg_volume';

/**
 * localStorage har doim try/catch ichida o'qiladi: private rejim, o'chirilgan
 * site data yoki buzilgan JSON butun ilovani qulatmasligi kerak.
 */
function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

function writeStorage(key: string, value: unknown): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* kvota to'lgan yoki yozish taqiqlangan — jim o'tamiz */
  }
}

interface PlayerState {
  currentStation: Channel | null;
  currentStream: StreamInfo | null;
  /** Shu kanal uchun hali sinab ko'rilmagan zaxira oqimlar */
  pendingFallbacks: StreamInfo[];
  isPlaying: boolean;
  isLoading: boolean;
  volume: number;
  isMuted: boolean;
  error: string | null;
  nowPlaying: string | null;
  favorites: Channel[];
  history: Channel[];
  selectedCountry: Country | null;
  /** localStorage faqat mijozda o'qilgandan keyin true bo'ladi */
  hydrated: boolean;

  hydrate: () => void;
  playStation: (station: Channel, stream?: StreamInfo) => void;
  /** Joriy oqim ishlamadi — keyingi zaxiraga o'tadi. Zaxira tugasa false. */
  advanceToFallback: () => boolean;
  togglePlay: () => void;
  pause: () => void;
  stop: () => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  setIsPlaying: (value: boolean) => void;
  setIsLoading: (value: boolean) => void;
  setError: (message: string | null) => void;
  setNowPlaying: (value: string | null) => void;
  toggleFavorite: (station: Channel) => void;
  isFavorite: (stationId: number) => boolean;
  selectCountry: (country: Country | null) => void;
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  currentStation: null,
  currentStream: null,
  pendingFallbacks: [],
  isPlaying: false,
  isLoading: false,
  volume: 0.8,
  isMuted: false,
  error: null,
  nowPlaying: null,
  // Boshlang'ich qiymat serverdagi bilan BIR XIL bo'lishi shart — aks holda
  // React hydration mismatch beradi. localStorage `hydrate()` da o'qiladi.
  favorites: [],
  history: [],
  selectedCountry: null,
  hydrated: false,

  hydrate: () => {
    if (get().hydrated) return;
    set({
      favorites: readStorage<Channel[]>(FAVORITES_KEY, []),
      volume: readStorage<number>(VOLUME_KEY, 0.8),
      hydrated: true,
    });
  },

  playStation: (station, stream) => {
    const all: StreamInfo[] = [
      ...(station.primary_stream ? [station.primary_stream] : []),
      ...(station.fallback_streams ?? []),
      ...(station.streams ?? []),
    ].filter((s, i, arr) => arr.findIndex((x) => x.id === s.id) === i);

    const chosen = stream ?? all[0];
    if (!chosen?.play_url) {
      set({ error: 'Bu stansiyada faol oqim topilmadi' });
      return;
    }

    set({
      currentStation: station,
      currentStream: chosen,
      pendingFallbacks: all.filter((s) => s.id !== chosen.id),
      isPlaying: true,
      isLoading: true,
      error: null,
      nowPlaying: null,
      history: [station, ...get().history.filter((s) => s.id !== station.id)].slice(0, 20),
    });
  },

  advanceToFallback: () => {
    const { pendingFallbacks } = get();
    const [next, ...rest] = pendingFallbacks;
    if (!next?.play_url) {
      set({
        isPlaying: false,
        isLoading: false,
        error: 'Bu stansiya hozir javob bermayapti',
      });
      return false;
    }
    set({
      currentStream: next,
      pendingFallbacks: rest,
      isLoading: true,
      isPlaying: true,
      error: null,
    });
    return true;
  },

  togglePlay: () => {
    if (!get().currentStation) return;
    set((state) => ({ isPlaying: !state.isPlaying }));
  },

  pause: () => set({ isPlaying: false }),

  stop: () =>
    set({
      currentStation: null,
      currentStream: null,
      pendingFallbacks: [],
      isPlaying: false,
      isLoading: false,
      nowPlaying: null,
    }),

  setVolume: (volume) => {
    const clamped = Math.max(0, Math.min(1, volume));
    writeStorage(VOLUME_KEY, clamped);
    set({ volume: clamped, isMuted: clamped === 0 });
  },

  toggleMute: () => set((state) => ({ isMuted: !state.isMuted })),

  setIsPlaying: (value) => set({ isPlaying: value }),
  setIsLoading: (value) => set({ isLoading: value }),
  setError: (message) => set({ error: message, isLoading: false }),
  setNowPlaying: (value) => set({ nowPlaying: value }),

  toggleFavorite: (station) => {
    const { favorites } = get();
    const exists = favorites.some((s) => s.id === station.id);
    const updated = exists
      ? favorites.filter((s) => s.id !== station.id)
      : [station, ...favorites];
    writeStorage(FAVORITES_KEY, updated);
    set({ favorites: updated });
  },

  isFavorite: (stationId) => get().favorites.some((s) => s.id === stationId),

  selectCountry: (country) => set({ selectedCountry: country }),
}));
