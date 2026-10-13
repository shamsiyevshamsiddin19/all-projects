'use client';

import React from 'react';
import { Play, Pause, Heart, Radio, Activity } from 'lucide-react';
import { Channel } from '@/types';
import { usePlayerStore } from '@/stores/playerStore';

interface StationCardProps {
  station: Channel;
}

export default function StationCard({ station }: StationCardProps) {
  const { currentStation, isPlaying, playStation, togglePlay, toggleFavorite, isFavorite } = usePlayerStore();

  const isCurrent = currentStation?.id === station.id;
  const isCurrentPlaying = isCurrent && isPlaying;
  const favorite = isFavorite(station.id);

  const handlePlayClick = () => {
    if (isCurrent) {
      togglePlay();
    } else {
      playStation(station);
    }
  };

  return (
    <div
      className={`group relative p-4 transition-all duration-300 border font-mono ${
        isCurrent
          ? 'bg-void-900 border-crimson shadow-crimson-glow'
          : 'bg-void-900/80 border-void-800 hover:border-crimson/40 hover:bg-void-850'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Logo and info */}
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="relative w-12 h-12 bg-void-950 border border-void-750 flex items-center justify-center overflow-hidden flex-shrink-0 group-hover:border-crimson/50 transition-colors">
            {station.logo_url ? (
              <img
                src={station.logo_url}
                alt={station.name}
                className="w-10 h-10 object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <Radio className="w-5 h-5 text-crimson" />
            )}
            {isCurrentPlaying && (
              <div className="absolute inset-0 bg-crimson/20 backdrop-blur-[1px] flex items-center justify-center">
                <span className="w-2.5 h-2.5 bg-crimson rounded-full animate-ping" />
              </div>
            )}
          </div>

          <div className="min-w-0">
            <h4 className="text-sm font-bold text-white group-hover:text-crimson-bright transition-colors truncate uppercase">
              {station.name}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              {station.bitrate && (
                <span className="text-[10px] px-1.5 py-0.5 bg-void-950 text-crimson-bright border border-void-750">
                  {station.bitrate} kbps
                </span>
              )}
              {station.score > 0 && (
                <span className="text-[10px] flex items-center gap-1 text-slate-300">
                  <Activity className="w-2.5 h-2.5 text-crimson" />
                  {station.score}%
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            onClick={() => toggleFavorite(station)}
            className="p-2 text-slate-400 hover:text-crimson hover:bg-void-800 transition-all duration-200"
            title="Sevimlilarga qo'shish"
          >
            <Heart className={`w-4 h-4 ${favorite ? 'fill-crimson text-crimson' : ''}`} />
          </button>

          <button
            onClick={handlePlayClick}
            className={`w-10 h-10 flex items-center justify-center transition-all duration-200 ${
              isCurrentPlaying
                ? 'bg-crimson text-white shadow-crimson-glow scale-105'
                : 'bg-void-850 hover:bg-crimson hover:text-white text-crimson border border-void-700 hover:border-crimson'
            }`}
          >
            {isCurrentPlaying ? (
              <Pause className="w-4 h-4 fill-current" />
            ) : (
              <Play className="w-4 h-4 fill-current ml-0.5" />
            )}
          </button>
        </div>
      </div>

      {/* Tags */}
      {station.tags.length > 0 && (
        <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-void-800/80 overflow-hidden">
          {station.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] px-2 py-0.5 bg-void-950 text-slate-400 border border-void-800 truncate"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
