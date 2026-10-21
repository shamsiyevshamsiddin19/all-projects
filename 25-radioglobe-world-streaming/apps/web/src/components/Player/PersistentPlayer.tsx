'use client';

import React, { useEffect, useRef } from 'react';
import Link from 'next/link';
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
      className="fixed inset-x-0 bottom-0 z-40 border-t border-ink-800 bg-ink-950/95 backdrop-blur-xl"
      role="region"
      aria-label="Audio pleyer"
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center gap-4 px-4 lg:px-8">
        {/* Stansiya */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <StationLogo
            src={currentStation.logo_url}
            alt={currentStation.name}
            size={48}
            active={isPlaying}
          />

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Link
                href={`/stansiya/${currentStation.slug}`}
                className="truncate text-sm font-medium text-text-primary transition-colors hover:text-signal-bright"
              >
                {currentStation.name}
              </Link>
              <button
                type="button"
                onClick={() => toggleFavorite(currentStation)}
                className={`shrink-0 transition-colors ${
                  favorite ? 'text-signal' : 'text-text-muted hover:text-text-secondary'
                }`}
                aria-label={favorite ? 'Sevimlilardan olib tashlash' : "Sevimlilarga qo'shish"}
                aria-pressed={favorite}
              >
                <Heart className={`h-3.5 w-3.5 ${favorite ? 'fill-current' : ''}`} />
              </button>
            </div>

            <div className="mt-1 flex items-center gap-2">
              {error ? (
                <span className="flex items-center gap-1.5 text-xs text-warn" role="alert">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {error}
                </span>
              ) : (
                <>
                  <AudioVisualizer isPlaying={isPlaying && !isLoading} bars={7} height={12} />
                  <span className="truncate text-xs text-text-muted">
                    {currentStation.tags.slice(0, 2).join(' · ') || 'Jonli efir'}
                  </span>
                  {currentStream?.bitrate ? (
                    <span className="shrink-0 font-mono text-[11px] text-text-muted">
                      {currentStream.bitrate}k
                    </span>
                  ) : null}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Ijro tugmasi */}
        <button
          type="button"
          onClick={togglePlay}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-signal
                     text-white transition-transform active:scale-95"
          aria-label={isPlaying ? "To'xtatish" : 'Ijro etish'}
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : isPlaying ? (
            <Pause className="h-5 w-5 fill-current" />
          ) : (
            <Play className="ml-0.5 h-5 w-5 fill-current" />
          )}
        </button>

        {/* Ovoz */}
        <div className="hidden w-40 shrink-0 items-center justify-end gap-2.5 sm:flex">
          <button
            type="button"
            onClick={toggleMute}
            className="text-text-muted transition-colors hover:text-text-primary"
            aria-label={isMuted ? 'Ovozni yoqish' : "Ovozni o'chirish"}
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="h-4 w-4" />
            ) : (
              <Volume2 className="h-4 w-4" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="h-1 w-20 cursor-pointer appearance-none rounded-full bg-ink-700 accent-signal"
            aria-label="Ovoz balandligi"
          />
          <button
            type="button"
            onClick={stop}
            className="text-text-muted transition-colors hover:text-text-primary"
            aria-label="Pleyerni yopish"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
