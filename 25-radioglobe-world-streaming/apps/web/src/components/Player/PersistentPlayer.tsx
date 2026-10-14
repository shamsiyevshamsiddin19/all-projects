'use client';

import React, { useEffect, useRef } from 'react';
import { AlertCircle, Heart, Loader2, Pause, Play, Volume2, VolumeX, X } from 'lucide-react';

import StationLogo from '@/components/Country/StationLogo';
import AudioVisualizer from '@/components/Player/AudioVisualizer';
import { reportPlay } from '@/lib/api';
import { audioEngine } from '@/lib/audioEngine';
import { usePlayerStore } from '@/stores/playerStore';

export default function PersistentPlayer() {
  // Har bir qiymat alohida tanlanadi. Obyekt qaytaruvchi selektor zustand v5 da
  // har renderda yangi havola yaratib, cheksiz qayta render keltirib chiqaradi.
  const currentStation = usePlayerStore((s) => s.currentStation);
  const currentStream = usePlayerStore((s) => s.currentStream);
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const isLoading = usePlayerStore((s) => s.isLoading);
  const volume = usePlayerStore((s) => s.volume);
  const isMuted = usePlayerStore((s) => s.isMuted);
  const error = usePlayerStore((s) => s.error);
  const hydrateDone = usePlayerStore((s) => s.hydrated);
  const favorites = usePlayerStore((s) => s.favorites);

  const hydrate = usePlayerStore((s) => s.hydrate);
  const togglePlay = usePlayerStore((s) => s.togglePlay);
  const setVolume = usePlayerStore((s) => s.setVolume);
  const toggleMute = usePlayerStore((s) => s.toggleMute);
  const setIsPlaying = usePlayerStore((s) => s.setIsPlaying);
  const setIsLoading = usePlayerStore((s) => s.setIsLoading);
  const setError = usePlayerStore((s) => s.setError);
  const toggleFavorite = usePlayerStore((s) => s.toggleFavorite);
  const advanceToFallback = usePlayerStore((s) => s.advanceToFallback);
  const stop = usePlayerStore((s) => s.stop);

  const lastStreamIdRef = useRef<number | null>(null);
  const effectiveVolume = isMuted ? 0 : volume;

  // localStorage faqat mijozda o'qiladi — hydration mismatch bo'lmasligi uchun
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Audio dvigatel hodisalarini do'konga ulash
  useEffect(() => {
    audioEngine.setListener({
      onPlaying: () => {
        setIsLoading(false);
        setIsPlaying(true);
        setError(null);
      },
      onWaiting: () => setIsLoading(true),
      onPause: () => {
        setIsLoading(false);
        setIsPlaying(false);
      },
      onError: () => {
        // Foydalanuvchiga xato ko'rsatishdan OLDIN zaxira oqimlarni sinab
        // ko'ramiz — hujjatdagi "avtomatik fallback" talabi
        const moved = advanceToFallback();
        if (!moved) setIsPlaying(false);
      },
    });
  }, [advanceToFallback, setError, setIsLoading, setIsPlaying]);

  // Oqim o'zgarganda ijroni boshlash.
  //
  // DIQQAT: bu yerda hech qanday `await` yo'q. `play_url` ro'yxat javobida
  // allaqachon kelgan, shuning uchun bosishdan ijrogacha tarmoq so'rovi
  // bo'lmaydi va mobil autoplay siyosati buzilmaydi.
  useEffect(() => {
    if (!currentStream?.play_url || !isPlaying) return;
    if (lastStreamIdRef.current === currentStream.id) return;

    lastStreamIdRef.current = currentStream.id;
    audioEngine.play(currentStream.play_url, effectiveVolume);

    // Statistika va radio-browser'ga klik — ijroga TA'SIR QILMAYDI
    void reportPlay(currentStream.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentStream?.id, currentStream?.play_url]);

  // Play/pause tugmasi
  useEffect(() => {
    if (!currentStream?.play_url) return;
    if (isPlaying) {
      if (lastStreamIdRef.current === currentStream.id) {
        audioEngine.resume(effectiveVolume);
      }
    } else {
      audioEngine.pause();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPlaying]);

  useEffect(() => {
    audioEngine.setVolume(effectiveVolume);
  }, [effectiveVolume]);

  // Mobil lock-screen boshqaruvi
  useEffect(() => {
    if (typeof navigator === 'undefined' || !('mediaSession' in navigator) || !currentStation) {
      return;
    }
    navigator.mediaSession.metadata = new MediaMetadata({
      title: currentStation.name,
      artist: currentStation.tags.slice(0, 2).join(', ') || 'World Radio',
      album: 'RadioGlobe',
      artwork: currentStation.logo_url
        ? [{ src: currentStation.logo_url, sizes: '512x512', type: 'image/png' }]
        : [],
    });
    navigator.mediaSession.setActionHandler('play', () => setIsPlaying(true));
    navigator.mediaSession.setActionHandler('pause', () => setIsPlaying(false));
    navigator.mediaSession.setActionHandler('stop', () => stop());

    return () => {
      navigator.mediaSession.setActionHandler('play', null);
      navigator.mediaSession.setActionHandler('pause', null);
      navigator.mediaSession.setActionHandler('stop', null);
    };
  }, [currentStation, setIsPlaying, stop]);

  if (!currentStation) return null;

  const favorite = hydrateDone && favorites.some((s) => s.id === currentStation.id);

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40 bg-void-950/95 backdrop-blur-xl border-t border-void-800 px-4 py-3 shadow-tactical-glass"
      role="region"
      aria-label="Audio pleyer"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 font-mono">
        <div className="flex items-center gap-3.5 min-w-0 flex-1">
          <StationLogo
            src={currentStation.logo_url}
            alt={currentStation.name}
            size={48}
            active={isPlaying}
          />

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-white truncate uppercase tracking-tight">
                {currentStation.name}
              </h4>
              <button
                type="button"
                onClick={() => toggleFavorite(currentStation)}
                className="text-slate-400 hover:text-crimson transition-colors shrink-0"
                aria-label={favorite ? 'Sevimlilardan olib tashlash' : "Sevimlilarga qo'shish"}
                aria-pressed={favorite}
              >
                <Heart className={`w-4 h-4 ${favorite ? 'fill-crimson text-crimson' : ''}`} />
              </button>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <AudioVisualizer isPlaying={isPlaying && !isLoading} />
              <span className="text-[11px] text-slate-400 truncate">
                {currentStation.tags.slice(0, 2).join(' • ') || 'Live Frequency'}
              </span>
              {currentStream?.bitrate ? (
                <span className="text-[9px] px-1.5 py-0.5 bg-void-850 text-crimson-bright border border-void-700 shrink-0">
                  {currentStream.bitrate} kbps
                </span>
              ) : null}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center gap-1 shrink-0">
          <button
            type="button"
            onClick={togglePlay}
            className="w-11 h-11 bg-crimson hover:bg-crimson-light text-white flex items-center justify-center shadow-crimson-glow hover:scale-105 active:scale-95 transition-all duration-200"
            aria-label={isPlaying ? "To'xtatish" : 'Ijro etish'}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : isPlaying ? (
              <Pause className="w-5 h-5 fill-white" />
            ) : (
              <Play className="w-5 h-5 fill-white ml-0.5" />
            )}
          </button>

          {error ? (
            <div className="flex items-center gap-1 text-[10px] text-crimson-bright" role="alert">
              <AlertCircle className="w-3 h-3" />
              <span>{error}</span>
            </div>
          ) : null}
        </div>

        <div className="hidden sm:flex items-center gap-3 min-w-[160px] justify-end shrink-0">
          <button
            type="button"
            onClick={toggleMute}
            className="text-slate-400 hover:text-white transition-colors"
            aria-label={isMuted ? 'Ovozni yoqish' : "Ovozni o'chirish"}
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="w-4 h-4 text-crimson" />
            ) : (
              <Volume2 className="w-4 h-4 text-crimson" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-20 h-1 bg-void-800 appearance-none cursor-pointer accent-crimson"
            aria-label="Ovoz balandligi"
          />
          <button
            type="button"
            onClick={stop}
            className="text-slate-500 hover:text-white transition-colors"
            aria-label="Pleyerni yopish"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
