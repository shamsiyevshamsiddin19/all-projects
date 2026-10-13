'use client';

import React from 'react';
import { Compass, RotateCw, ZoomIn, ZoomOut, Radio, Globe } from 'lucide-react';
import { Country } from '@/types';

interface GlobeHUDProps {
  onRotateToggle: () => void;
  isRotating: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onCountrySelect: (slug: string) => void;
  quickCountries: Country[];
}

export default function GlobeHUD({
  onRotateToggle,
  isRotating,
  onZoomIn,
  onZoomOut,
  onCountrySelect,
  quickCountries,
}: GlobeHUDProps) {
  return (
    <>
      {/* Top HUD Stats */}
      <div className="absolute top-20 left-4 z-20 pointer-events-none hidden sm:block">
        <div className="bg-space-950/70 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-3.5 shadow-glass space-y-2 pointer-events-auto">
          <div className="flex items-center gap-2 text-cyan-400">
            <Radio className="w-4 h-4 animate-pulse" />
            <span className="text-xs font-mono tracking-wider uppercase font-semibold">
              Live Satellite Feed
            </span>
          </div>
          <div className="text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex justify-between gap-4">
              <span>Projection:</span>
              <span className="text-cyan-300">MapLibre 3D Globe</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Resolution:</span>
              <span className="text-cyan-300">110m Vector GeoJSON</span>
            </div>
            <div className="flex justify-between gap-4">
              <span>Stream Protocol:</span>
              <span className="text-emerald-400">HTTP/Icecast Proxy</span>
            </div>
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="absolute bottom-24 right-4 z-20 flex flex-col gap-2">
        <button
          onClick={onZoomIn}
          className="w-10 h-10 rounded-xl bg-space-900/80 backdrop-blur-md border border-space-700/80 hover:border-cyan-400 text-slate-300 hover:text-cyan-400 flex items-center justify-center transition-all duration-200 shadow-glass"
          title="Yaqinlashtirish"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={onZoomOut}
          className="w-10 h-10 rounded-xl bg-space-900/80 backdrop-blur-md border border-space-700/80 hover:border-cyan-400 text-slate-300 hover:text-cyan-400 flex items-center justify-center transition-all duration-200 shadow-glass"
          title="Uzoqlashtirish"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={onRotateToggle}
          className={`w-10 h-10 rounded-xl backdrop-blur-md border flex items-center justify-center transition-all duration-200 shadow-glass ${
            isRotating
              ? 'bg-cyan-950/80 border-cyan-500/50 text-cyan-400 shadow-cyan-glow'
              : 'bg-space-900/80 border-space-700/80 text-slate-400 hover:text-white hover:border-space-600'
          }`}
          title={isRotating ? 'Aylanishni to\'xtatish' : 'Globusni aylantirish'}
        >
          <RotateCw className={`w-4 h-4 ${isRotating ? 'animate-spin-slow' : ''}`} />
        </button>
      </div>

      {/* Quick Countries Strip */}
      {quickCountries.length > 0 && (
        <div className="absolute top-20 right-4 z-20 hidden md:block">
          <div className="bg-space-950/70 backdrop-blur-md border border-space-800 rounded-2xl p-2.5 shadow-glass space-y-1.5 max-w-[200px]">
            <p className="text-[10px] font-mono uppercase text-slate-400 px-2 tracking-wider">
              Tezkor tanlov
            </p>
            <div className="flex flex-col gap-1">
              {quickCountries.slice(0, 6).map((c) => (
                <button
                  key={c.iso2}
                  onClick={() => onCountrySelect(c.slug)}
                  className="flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:text-cyan-300 hover:bg-space-850/80 transition-colors text-left"
                >
                  <span className="flex items-center gap-1.5 truncate">
                    <span>{c.flag_emoji || '🌍'}</span>
                    <span className="truncate">{c.name_uz || c.name_en}</span>
                  </span>
                  <span className="text-[10px] font-mono text-cyan-400 ml-1">
                    {c.radio_count}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
