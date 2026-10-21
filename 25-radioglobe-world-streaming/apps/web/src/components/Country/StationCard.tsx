'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { Heart, Pause, Play } from 'lucide-react';

import StationLogo from '@/components/Country/StationLogo';
import AudioVisualizer from '@/components/Player/AudioVisualizer';
import { usePlayerStore } from '@/stores/playerStore';
import type { Channel } from '@/types';

interface StationCardProps {
  station: Channel;
  /** Stansiya sahifasida sarlavha havolasi keraksiz */
  linkToStation?: boolean;
}

export default function StationCard({ station, linkToStation = true }: StationCardProps) {
  const currentStation = usePlayerStore((s) => s.currentStation);
  const isPlaying = usePlayerStore((s) => s.isPlaying);
  const favorites = usePlayerStore((s) => s.favorites);
  const hydrated = usePlayerStore((s) => s.hydrated);
  const hydrate = usePlayerStore((s) => s.hydrate);
  const playStation = usePlayerStore((s) => s.playStation);
  const togglePlay = usePlayerStore((s) => s.togglePlay);
  const toggleFavorite = usePlayerStore((s) => s.toggleFavorite);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const isCurrent = currentStation?.id === station.id;
  const isCurrentPlaying = isCurrent && isPlaying;
  // hydrated tekshiruvi SSR va mijoz HTML'i bir xil bo'lishi uchun
  const favorite = hydrated && favorites.some((s) => s.id === station.id);

  // Ijro bosish hodisasining O'ZIDA boshlanadi — oldidan tarmoq so'rovi yo'q,
  // shuning uchun mobil autoplay siyosati buzilmaydi
  const handlePlay = () => {
    if (isCurrent) togglePlay();
    else playStation(station);
  };

  const bitrate = station.primary_stream?.bitrate ?? station.bitrate;

  return (
    <article
      className={`group flex items-center gap-3 rounded-xl border p-3 transition-colors ${
        isCurrent
          ? 'border-signal/50 bg-signal/[0.06]'
          : 'border-ink-700 bg-ink-900 hover:border-ink-600 hover:bg-ink-850'
      }`}
    >
      <StationLogo src={station.logo_url} alt={station.name} size={44} active={isCurrentPlaying} />

      <div className="min-w-0 flex-1">
        <h3 className="truncate text-sm font-medium text-text-primary">
          {linkToStation ? (
            <Link
              href={`/stansiya/${station.slug}`}
              className="transition-colors hover:text-signal-bright"
            >
              {station.name}
            </Link>
          ) : (
            station.name
          )}
        </h3>

        <div className="mt-1 flex items-center gap-2 text-xs text-text-muted">
          {isCurrentPlaying ? (
            <>
              <AudioVisualizer isPlaying bars={5} height={10} />
              <span className="text-signal-bright">Efirda</span>
            </>
          ) : (
            <span className="truncate">
              {station.tags.slice(0, 2).join(' · ') || 'Jonli efir'}
            </span>
          )}
          {bitrate ? (
            <span className="shrink-0 font-mono text-[11px] text-text-muted">
              {bitrate}k
            </span>
          ) : null}
        </div>
      </div>

      <button
        type="button"
        onClick={() => toggleFavorite(station)}
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors
                    ${favorite ? 'text-signal' : 'text-text-muted hover:text-text-secondary'}`}
        aria-label={favorite ? 'Sevimlilardan olib tashlash' : "Sevimlilarga qo'shish"}
        aria-pressed={favorite}
      >
        <Heart className={`h-4 w-4 ${favorite ? 'fill-current' : ''}`} />
      </button>

      <button
        type="button"
        onClick={handlePlay}
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all
                    active:scale-95 ${
                      isCurrentPlaying
                        ? 'bg-signal text-white'
                        : 'bg-ink-800 text-text-primary group-hover:bg-signal group-hover:text-white'
                    }`}
        aria-label={isCurrentPlaying ? "To'xtatish" : `${station.name} ni tinglash`}
      >
        {isCurrentPlaying ? (
          <Pause className="h-4 w-4 fill-current" />
        ) : (
          <Play className="ml-0.5 h-4 w-4 fill-current" />
        )}
      </button>
    </article>
  );
}
