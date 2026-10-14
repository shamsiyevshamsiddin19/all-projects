'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { Heart, Pause, Play } from 'lucide-react';

import StationLogo from '@/components/Country/StationLogo';
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

  // Ijro bosish hodisasining O'ZIDA boshlanadi — oldidan hech qanday
  // tarmoq so'rovi yo'q, shuning uchun mobil autoplay siyosati buzilmaydi
  const handlePlay = () => {
    if (isCurrent) togglePlay();
    else playStation(station);
  };

  const bitrate = station.primary_stream?.bitrate ?? station.bitrate;

  return (
    <article
      className={`group relative p-4 transition-all duration-300 border font-mono ${
        isCurrent
          ? 'bg-void-900 border-crimson shadow-crimson-glow'
          : 'bg-void-900/80 border-void-800 hover:border-crimson/40 hover:bg-void-850'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3.5 min-w-0">
          <StationLogo src={station.logo_url} alt={station.name} size={48} active={isCurrentPlaying} />

          <div className="min-w-0">
            <h3 className="text-sm font-bold text-white truncate uppercase tracking-tight">
              {linkToStation ? (
                <Link
                  href={`/stansiya/${station.slug}`}
                  className="hover:text-crimson-bright transition-colors"
                >
                  {station.name}
                </Link>
              ) : (
                station.name
              )}
            </h3>
            <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-400 flex-wrap">
              {bitrate ? (
                <span className="px-1.5 py-0.5 bg-void-950 border border-void-750 text-crimson-bright">
                  {bitrate} kbps
                </span>
              ) : null}
              <span className="truncate">
                {station.tags.slice(0, 2).join(' • ') || 'Jonli efir'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={() => toggleFavorite(station)}
            className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-crimson transition-colors"
            aria-label={favorite ? 'Sevimlilardan olib tashlash' : "Sevimlilarga qo'shish"}
            aria-pressed={favorite}
          >
            <Heart className={`w-4 h-4 ${favorite ? 'fill-crimson text-crimson' : ''}`} />
          </button>

          <button
            type="button"
            onClick={handlePlay}
            className="w-10 h-10 bg-crimson hover:bg-crimson-light text-white flex items-center justify-center transition-all duration-200 active:scale-95"
            aria-label={isCurrentPlaying ? "To'xtatish" : `${station.name} ni tinglash`}
          >
            {isCurrentPlaying ? (
              <Pause className="w-4 h-4 fill-white" />
            ) : (
              <Play className="w-4 h-4 fill-white ml-0.5" />
            )}
          </button>
        </div>
      </div>
    </article>
  );
}
