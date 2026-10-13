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
      className={`group relative p-4 rounded-2xl transition-all duration-300 border ${
        isCurrent
          ? 'bg-space-850/90 border-cyan-500/50 shadow-cyan-glow'
          : 'bg-space-900/60 border-space-800/80 hover:border-space-700 hover:bg-space-850/70'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Logo and info */}
        <div className="flex items-center gap-3.5 min-w-0">
          <div className="relative w-12 h-12 rounded-xl bg-space-800 border border-space-700/60 flex items-center justify-center overflow-hidden flex-shrink-0 group-hover:border-cyan-500/40 transition-colors">
            {station.logo_url ? (
              <img
                src={station.logo_url}
                alt={station.name}
                className="w-10 h-10 object-contain rounded"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <Radio className="w-5 h-5 text-cyan-400" />
            )}
            {isCurrentPlaying && (
              <div className="absolute inset-0 bg-cyan-500/20 backdrop-blur-[1px] flex items-center justify-center">
                <span className="w-3 h-3 bg-cyan-400 rounded-full animate-ping" />
              </div>
            )}
          </div>

          <div className="min-w-0">
            <h4 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors truncate">
              {station.name}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              {station.bitrate && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-space-800 text-cyan-400 border border-space-700">
                  {station.bitrate} kbps
                </span>
              )}
              {station.score > 0 && (
                <span className="text-[10px] flex items-center gap-1 text-emerald-400">
                  <Activity className="w-2.5 h-2.5" />
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
            className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-space-800 transition-all duration-200"
            title="Sevimlilarga qo'shish"
          >
            <Heart className={`w-4 h-4 ${favorite ? 'fill-rose-500 text-rose-500' : ''}`} />
          </button>

          <button
            onClick={handlePlayClick}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
              isCurrentPlaying
                ? 'bg-cyan-500 text-space-950 shadow-cyan-glow scale-105'
                : 'bg-space-800 hover:bg-cyan-500 hover:text-space-950 text-cyan-400 border border-space-700 hover:border-cyan-400'
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
        <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-space-800/60 overflow-hidden">
          {station.tags.slice(0, 3).map((tag, idx) => (
            <span
              key={idx}
              className="text-[10px] px-2 py-0.5 rounded-full bg-space-800/80 text-slate-400 border border-space-700/50 truncate"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
