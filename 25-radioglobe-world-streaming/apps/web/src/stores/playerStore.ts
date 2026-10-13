import { create } from 'zustand';
import { Channel, StreamInfo, Country } from '@/types';

interface PlayerState {
  currentStation: Channel | null;
  currentStream: StreamInfo | null;
  isPlaying: boolean;
  isLoading: boolean;
  volume: number;
  isMuted: boolean;
  error: string | null;
  favorites: Channel[];
  history: Channel[];
  selectedCountry: Country | null;

  // Actions
  playStation: (station: Channel, stream?: StreamInfo) => void;
  togglePlay: () => void;
  pause: () => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  setIsPlaying: (isPlaying: boolean) => void;
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  toggleFavorite: (station: Channel) => void;
  isFavorite: (stationId: number) => boolean;
  selectCountry: (country: Country | null) => void;
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  currentStation: null,
  currentStream: null,
  isPlaying: false,
  isLoading: false,
  volume: 0.8,
  isMuted: false,
  error: null,
  favorites: typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('rg_favorites') || '[]') : [],
  history: [],
  selectedCountry: null,

  playStation: (station: Channel, stream?: StreamInfo) => {
    const selectedStream = stream || station.primary_stream || (station.streams && station.streams[0]);
    if (!selectedStream) {
      set({ error: "Ushbu stansiyada faol oqim topilmadi" });
      return;
    }

    // Add to history
    const history = [station, ...get().history.filter((s) => s.id !== station.id)].slice(0, 20);

    set({
      currentStation: station,
      currentStream: selectedStream,
      isPlaying: true,
      isLoading: true,
      error: null,
      history,
    });
  },

  togglePlay: () => {
    const { isPlaying, currentStation } = get();
    if (!currentStation) return;
    set({ isPlaying: !isPlaying });
  },

  pause: () => set({ isPlaying: false }),

  setVolume: (volume: number) => {
    const clamped = Math.max(0, Math.min(1, volume));
    set({ volume: clamped, isMuted: clamped === 0 });
  },

  toggleMute: () => {
    const { isMuted, volume } = get();
    set({ isMuted: !isMuted });
  },

  setIsPlaying: (isPlaying: boolean) => set({ isPlaying }),
  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setError: (error: string | null) => set({ error, isLoading: false }),

  toggleFavorite: (station: Channel) => {
    const { favorites } = get();
    const exists = favorites.some((s) => s.id === station.id);
    const updated = exists ? favorites.filter((s) => s.id !== station.id) : [station, ...favorites];

    if (typeof window !== 'undefined') {
      localStorage.setItem('rg_favorites', JSON.stringify(updated));
    }
    set({ favorites: updated });
  },

  isFavorite: (stationId: number) => {
    return get().favorites.some((s) => s.id === stationId);
  },

  selectCountry: (country: Country | null) => set({ selectedCountry: country }),
}));
