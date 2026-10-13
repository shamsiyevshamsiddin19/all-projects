'use client';

import React from 'react';
import { RotateCw, ZoomIn, ZoomOut, Radio, Target, Crosshair, Activity, Disc } from 'lucide-react';
import { Country } from '@/types';
import { usePlayerStore } from '@/stores/playerStore';

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
  const { isPlaying, currentStation } = usePlayerStore();

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none">
      {/* 1. TOP CENTER: Samolevsky BROADCAST DESIGN Badge */}
      <div className="absolute top-16 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono tracking-[0.25em] text-slate-400 uppercase font-semibold">
            SUITABLE FOR
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 bg-crimson rounded-full animate-ping" />
          <div className="px-3.5 py-1 bg-crimson border border-crimson-bright shadow-crimson-glow text-white text-[11px] font-mono font-black tracking-[0.2em] uppercase flex items-center gap-2">
            <span>BROADCAST DESIGN</span>
          </div>
          <div className="w-1.5 h-1.5 bg-crimson rounded-full animate-ping" />
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-slate-400">
          <span>FREQ: 104.2 MHZ</span>
          <span>•</span>
          <span className="text-crimson-bright font-bold">LIVE TELEMETRY</span>
          <span>•</span>
          <span>GLOBAL SAT-FEED</span>
        </div>
      </div>

      {/* 2. TOP LEFT: Tactical Target Reticle & Coordinates */}
      <div className="absolute top-20 left-6 z-20 hidden lg:block pointer-events-auto">
        <div className="tactical-box p-3.5 max-w-[240px] space-y-2.5">
          <div className="flex items-center justify-between border-b border-void-700/80 pb-2">
            <div className="flex items-center gap-1.5 text-crimson">
              <Crosshair className="w-4 h-4" />
              <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-white">
                TARGET GRID
              </span>
            </div>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-crimson/20 text-crimson-bright border border-crimson/40">
              SYS::OK
            </span>
          </div>

          <div className="space-y-1.5 font-mono text-[10px] text-slate-400">
            <div className="flex justify-between">
              <span>ORBIT:</span>
              <span className="text-white font-bold">GEO-STATIONARY</span>
            </div>
            <div className="flex justify-between">
              <span>SCANNER:</span>
              <span className="text-crimson-bright">VECTOR 110M</span>
            </div>
            <div className="flex justify-between">
              <span>STATUS:</span>
              <span className="text-white">{isPlaying ? 'STREAMING' : 'STANDBY'}</span>
            </div>
          </div>

          {/* Dotted matrix block from reference */}
          <div className="pt-2 border-t border-void-700/80">
            <div className="grid grid-cols-8 gap-1 opacity-80">
              {[...Array(24)].map((_, i) => (
                <div
                  key={i}
                  className={`w-1.5 h-1.5 rounded-[1px] ${
                    i % 3 === 0
                      ? 'bg-crimson shadow-crimson-glow'
                      : i % 2 === 0
                      ? 'bg-white'
                      : 'bg-void-700'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Left Telemetry Dials: 25 & 40 */}
        <div className="flex items-center gap-4 mt-4">
          <div className="flex items-center gap-2 font-mono text-xs text-white">
            <div className="relative w-10 h-10 rounded-full border-2 border-void-700 border-t-white flex items-center justify-center">
              <span className="text-[11px] font-bold">25</span>
            </div>
            <span className="text-[9px] text-slate-400 uppercase">SIGNAL</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs text-white">
            <div className="relative w-10 h-10 rounded-full border-2 border-void-700 border-t-crimson flex items-center justify-center">
              <span className="text-[11px] font-bold text-crimson-bright">40</span>
            </div>
            <span className="text-[9px] text-slate-400 uppercase">SAT-RF</span>
          </div>
        </div>
      </div>

      {/* 3. TOP RIGHT: Right Telemetry Dials & Quick Country Selector */}
      <div className="absolute top-20 right-6 z-20 hidden lg:block pointer-events-auto">
        <div className="flex items-center gap-4 justify-end mb-4">
          <div className="flex items-center gap-2 font-mono text-xs text-white">
            <span className="text-[9px] text-slate-400 uppercase">QUALITY</span>
            <div className="relative w-10 h-10 rounded-full border-2 border-void-700 border-t-white flex items-center justify-center">
              <span className="text-[11px] font-bold">60</span>
            </div>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs text-white">
            <span className="text-[9px] text-slate-400 uppercase">RATE</span>
            <div className="relative w-10 h-10 rounded-full border-2 border-void-700 border-t-crimson flex items-center justify-center">
              <span className="text-[11px] font-bold text-crimson-bright">75</span>
            </div>
          </div>
        </div>

        {/* Tactical Quick Country list */}
        {quickCountries.length > 0 && (
          <div className="tactical-box p-3 min-w-[210px] space-y-1.5">
            <div className="flex items-center justify-between border-b border-void-700/80 pb-1.5 mb-2">
              <span className="text-[10px] font-mono uppercase text-crimson-bright font-bold tracking-widest flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5" />
                SECTOR SELECT
              </span>
              <span className="text-[9px] font-mono text-slate-400">NODES</span>
            </div>
            <div className="space-y-1">
              {quickCountries.slice(0, 5).map((c) => (
                <button
                  key={c.iso2}
                  onClick={() => onCountrySelect(c.slug)}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded text-[11px] font-mono text-slate-300 hover:text-white hover:bg-void-800 border border-transparent hover:border-crimson/40 transition-colors text-left"
                >
                  <span className="flex items-center gap-2 truncate">
                    <span>{c.flag_emoji || '⌖'}</span>
                    <span className="truncate">{c.name_uz || c.name_en}</span>
                  </span>
                  <span className="text-[10px] font-mono text-crimson-bright font-bold">
                    {c.radio_count}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 4. CENTER ORBITAL & TICK RING (Visible around the globe) */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {/* Orbital Ellipse Ring (Angled like the Samolevsky image) */}
        <div
          className="w-[620px] h-[340px] sm:w-[740px] sm:h-[400px] border border-dashed border-slate-600/40 rounded-[50%] pointer-events-none rotate-[-25deg] animate-pulse"
          style={{ boxShadow: '0 0 35px rgba(255, 26, 53, 0.08)' }}
        >
          {/* Orbital Satellite Dot Indicator */}
          <div className="absolute top-1/2 left-0 w-2.5 h-2.5 rounded-full bg-crimson shadow-crimson-glow animate-ping" />
        </div>

        {/* Circular Compass Radial Tick Ring */}
        <div
          className="w-[490px] h-[490px] sm:w-[560px] sm:h-[560px] rounded-full border border-void-700/50 pointer-events-none flex items-center justify-center"
        >
          <div className="w-full h-full rounded-full border border-dashed border-crimson/25 rotate-45" />
        </div>
      </div>

      {/* 5. BOTTOM SPECTRUM EQUALIZER BARS (Directly matching bottom of reference image) */}
      <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-1.5 pointer-events-auto">
        <div className="flex items-end gap-[3px] h-9 px-4 py-1.5 rounded-xl bg-void-950/80 border border-void-800 backdrop-blur-md">
          {[
            15, 30, 60, 45, 90, 75, 40, 100, 85, 50, 70, 30, 95, 60, 40, 80,
            20, 65, 85, 40, 100, 75, 55, 90, 35, 70, 50, 85, 60, 40, 95, 30,
            50, 75, 60, 90, 45, 80, 100, 65, 40, 85, 30, 70, 90, 55, 75, 40,
          ].map((h, idx) => {
            const isRed = idx % 5 === 0 || idx % 7 === 0;
            return (
              <span
                key={idx}
                className={`w-[2px] rounded-[1px] transition-all duration-200 ${
                  isPlaying
                    ? isRed
                      ? 'bg-crimson shadow-crimson-glow animate-pulse'
                      : 'bg-white'
                    : 'bg-void-700 h-1'
                }`}
                style={{
                  height: isPlaying ? `${Math.max(15, h)}%` : '4px',
                  animationDelay: `${(idx % 10) * 80}ms`,
                }}
              />
            );
          })}
        </div>
        <div className="flex items-center gap-3 text-[9px] font-mono text-slate-400">
          <span>AUDIO FREQUENCY SPECTRUM ANALYZER</span>
          <span className="text-crimson">•</span>
          <span>{currentStation ? currentStation.name : 'STANDBY'}</span>
        </div>
      </div>

      {/* 6. CONTROL BUTTONS (Zoom & Rotate) */}
      <div className="absolute bottom-24 right-6 z-20 flex flex-col gap-2 pointer-events-auto">
        <button
          onClick={onZoomIn}
          className="w-10 h-10 rounded-lg bg-void-900 border border-void-750 hover:border-crimson text-slate-300 hover:text-crimson flex items-center justify-center transition-all duration-200 shadow-tactical-glass"
          title="Yaqinlashtirish"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={onZoomOut}
          className="w-10 h-10 rounded-lg bg-void-900 border border-void-750 hover:border-crimson text-slate-300 hover:text-crimson flex items-center justify-center transition-all duration-200 shadow-tactical-glass"
          title="Uzoqlashtirish"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={onRotateToggle}
          className={`w-10 h-10 rounded-lg border flex items-center justify-center transition-all duration-200 shadow-tactical-glass ${
            isRotating
              ? 'bg-crimson text-white border-crimson-bright shadow-crimson-glow'
              : 'bg-void-900 border-void-750 text-slate-400 hover:text-white hover:border-slate-500'
          }`}
          title={isRotating ? 'Aylanishni to\'xtatish' : 'Globusni aylantirish'}
        >
          <RotateCw className={`w-4 h-4 ${isRotating ? 'animate-spin-slow' : ''}`} />
        </button>
      </div>
    </div>
  );
}
