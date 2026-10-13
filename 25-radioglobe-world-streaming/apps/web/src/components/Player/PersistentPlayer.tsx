'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Volume2, VolumeX, Heart, Radio, AlertCircle, Loader2 } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import { reportPlay } from '@/lib/api';
import AudioVisualizer from './AudioVisualizer';

export default function PersistentPlayer() {
  const {
    currentStation,
    currentStream,
    isPlaying,
    isLoading,
    volume,
    isMuted,
    error,
    togglePlay,
    setVolume,
    toggleMute,
    setIsPlaying,
    setIsLoading,
    setError,
    toggleFavorite,
    isFavorite,
  } = usePlayerStore();

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  // Sync stream URL and play reporting
  useEffect(() => {
    if (!currentStream) {
      setStreamUrl(null);
      return;
    }

    let isSubscribed = true;

    // Report play to API and obtain resolved play URL
    reportPlay(currentStream.id).then((res) => {
      if (!isSubscribed) return;
      if (res && res.play_url) {
        setStreamUrl(res.play_url);
      } else {
        setStreamUrl(currentStream.play_url || null);
      }
    });

    return () => {
      isSubscribed = false;
    };
  }, [currentStream]);

  // Audio element management
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !streamUrl) return;

    audio.src = streamUrl;
    audio.volume = isMuted ? 0 : volume;

    if (isPlaying) {
      setIsLoading(true);
      audio.play().catch((err) => {
        console.warn('Playback autoplay or load issue:', err);
        setError('Oqimni ijro etib bo\'lmadi');
        setIsLoading(false);
      });
    } else {
      audio.pause();
    }
  }, [streamUrl]);

  // Handle play/pause toggles
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !streamUrl) return;

    if (isPlaying) {
      audio.play().catch(() => {
        setIsPlaying(false);
      });
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  // Volume changes
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  // MediaSession API setup
  useEffect(() => {
    if (typeof window === 'undefined' || !('mediaSession' in navigator) || !currentStation) return;

    navigator.mediaSession.metadata = new MediaMetadata({
      title: currentStation.name,
      artist: currentStation.tags.slice(0, 2).join(', ') || 'World Radio',
      album: 'RadioGlobe',
      artwork: currentStation.logo_url ? [{ src: currentStation.logo_url }] : [],
    });

    navigator.mediaSession.setActionHandler('play', () => setIsPlaying(true));
    navigator.mediaSession.setActionHandler('pause', () => setIsPlaying(false));
  }, [currentStation, setIsPlaying]);

  if (!currentStation) return null;

  const favorite = isFavorite(currentStation.id);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-void-950/95 backdrop-blur-xl border-t border-void-800 px-4 py-3 shadow-tactical-glass transition-all duration-300">
      <audio
        ref={audioRef}
        onWaiting={() => setIsLoading(true)}
        onPlaying={() => {
          setIsLoading(false);
          setIsPlaying(true);
          setError(null);
        }}
        onError={() => {
          setError('Oqim bilan bog\'lanishda xatolik yuz berdi');
          setIsLoading(false);
          setIsPlaying(false);
        }}
        preload="none"
      />

      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 font-mono">
        {/* Station Info */}
        <div className="flex items-center gap-3.5 min-w-0 max-w-[40%]">
          <div className="relative w-12 h-12 bg-void-900 border border-void-750 flex items-center justify-center overflow-hidden flex-shrink-0">
            {currentStation.logo_url ? (
              <img
                src={currentStation.logo_url}
                alt={currentStation.name}
                className="w-10 h-10 object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <Radio className="w-5 h-5 text-crimson" />
            )}
            {isPlaying && (
              <div className="absolute inset-0 bg-crimson/10 border border-crimson/50" />
            )}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-white truncate uppercase tracking-tight">{currentStation.name}</h4>
              <button
                onClick={() => toggleFavorite(currentStation)}
                className="text-slate-400 hover:text-crimson transition-colors"
                title="Sevimlilarga qo'shish"
              >
                <Heart className={`w-4 h-4 ${favorite ? 'fill-crimson text-crimson' : ''}`} />
              </button>
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <AudioVisualizer isPlaying={isPlaying && !isLoading} />
              <span className="text-[11px] text-slate-400 truncate">
                {currentStation.tags.slice(0, 2).join(' • ') || 'Live Frequency'}
              </span>
              {currentStream?.bitrate && (
                <span className="text-[9px] px-1.5 py-0.2 bg-void-850 text-crimson-bright border border-void-700 font-mono">
                  {currentStream.bitrate} kbps
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex flex-col items-center gap-1">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              disabled={isLoading}
              className="w-11 h-11 bg-crimson hover:bg-crimson-light text-white flex items-center justify-center shadow-crimson-glow hover:scale-105 active:scale-95 transition-all duration-200 disabled:opacity-50"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin text-white" />
              ) : isPlaying ? (
                <Pause className="w-5 h-5 fill-white text-white" />
              ) : (
                <Play className="w-5 h-5 fill-white text-white ml-0.5" />
              )}
            </button>
          </div>

          {error && (
            <div className="flex items-center gap-1 text-[10px] text-crimson-bright animate-in fade-in">
              <AlertCircle className="w-3 h-3" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Volume & Details */}
        <div className="hidden sm:flex items-center gap-3 min-w-[140px] justify-end">
          <button
            onClick={toggleMute}
            className="text-slate-400 hover:text-white transition-colors"
            title={isMuted ? 'Ovozni yoqish' : 'Ovozni o\'chirish'}
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
          />
        </div>
      </div>
    </div>
  );
}
