'use client';

import React from 'react';
import Link from 'next/link';
import { Minus, Pause, Plus, RotateCw, Shuffle } from 'lucide-react';

import AudioVisualizer from '@/components/Player/AudioVisualizer';
import { usePlayerStore } from '@/stores/playerStore';
import type { Country } from '@/types';

interface GlobeHUDProps {
  onRotateToggle: () => void;
  isRotating: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRandom: () => void;
  isRandomLoading: boolean;
  topCountries: Country[];
}

/**
 * Globus ustidagi interfeys.
 *
 * QOIDA: bu yerda ko'rsatilgan HAR BIR raqam bazadan keladi.
 *
 * Oldingi versiyada "FREQ: 104.2 MHZ", "ORBIT: GEO-STATIONARY",
 * "SCANNER: VECTOR 110M" va 25/40/60/75 degan o'lchagichlar bor edi — ularning
 * hech biri hech narsani anglatmasdi. Shuningdek "SUITABLE FOR — BROADCAST
 * DESIGN" yozuvi ham qolib ketgandi; u ilhom olingan stock shablonning o'z
 * yozuvi. Bunday bezak mahsulotni jiddiy ko'rinishdan mahrum qiladi, shuning
 * uchun hammasi olib tashlandi.
 */
export default function GlobeHUD({
  onRotateToggle,
  isRotating,
  onZoomIn,
  onZoomOut,
  onRandom,
  isRandomLoading,
  topCountries,
}: GlobeHUDProps) {
  const currentStation = usePlayerStore((s) => s.currentStation);
  const isPlaying = usePlayerStore((s) => s.isPlaying);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {/* ── O'ng yuqori: eng ko'p stansiyali davlatlar ── */}
      {topCountries.length > 0 ? (
        <div className="pointer-events-auto absolute right-4 top-4 hidden w-[216px] lg:block">
          <div className="panel p-2">
            <p className="eyebrow px-2 pb-2 pt-1">Eng ko'p stansiyali</p>
            <ul>
              {topCountries.slice(0, 6).map((c) => (
                <li key={c.iso2}>
                  <Link
                    href={`/radio/${c.slug}`}
                    className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5
                               text-sm text-text-secondary transition-colors
                               hover:bg-ink-850 hover:text-text-primary"
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <span aria-hidden="true">{c.flag_emoji || '🌐'}</span>
                      <span className="truncate">{c.name_uz || c.name_en}</span>
                    </span>
                    <span className="font-mono text-xs text-text-muted">{c.radio_count}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}

      {/* ── Pastki markaz: faqat ijro ketayotganda ── */}
      {currentStation ? (
        <div className="pointer-events-none absolute bottom-6 left-1/2 -translate-x-1/2 animate-fade-up">
          <div className="panel flex items-center gap-3 px-4 py-2.5">
            <span className="live-dot" aria-hidden="true" />
            <span className="text-sm font-medium text-text-primary">
              {currentStation.name}
            </span>
            {/* Haqiqiy spektr — soxta ekvalayzer emas */}
            <AudioVisualizer isPlaying={isPlaying} bars={18} height={18} />
          </div>
        </div>
      ) : null}

      {/* ── Pastki o'ng: boshqaruv ── */}
      <div className="pointer-events-auto absolute bottom-6 right-4 flex flex-col gap-1.5">
        <button
          type="button"
          onClick={onRandom}
          disabled={isRandomLoading}
          className="mb-1.5 flex h-10 w-10 items-center justify-center rounded-lg border
                     border-signal/40 bg-signal/10 text-signal-bright transition-colors
                     hover:bg-signal/20 disabled:opacity-50"
          title="Tasodifiy stansiya"
          aria-label="Tasodifiy stansiyani tinglash"
        >
          <Shuffle className={`h-4 w-4 ${isRandomLoading ? 'animate-pulse' : ''}`} />
        </button>

        <button
          type="button"
          onClick={onZoomIn}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-ink-700
                     bg-ink-900/80 text-text-secondary backdrop-blur transition-colors
                     hover:border-ink-600 hover:text-text-primary"
          aria-label="Yaqinlashtirish"
        >
          <Plus className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onZoomOut}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-ink-700
                     bg-ink-900/80 text-text-secondary backdrop-blur transition-colors
                     hover:border-ink-600 hover:text-text-primary"
          aria-label="Uzoqlashtirish"
        >
          <Minus className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onRotateToggle}
          className={`flex h-10 w-10 items-center justify-center rounded-lg border backdrop-blur
                      transition-colors ${
                        isRotating
                          ? 'border-ink-700 bg-ink-900/80 text-text-secondary hover:text-text-primary'
                          : 'border-signal/40 bg-signal/10 text-signal-bright'
                      }`}
          aria-label={isRotating ? "Aylanishni to'xtatish" : 'Globusni aylantirish'}
          aria-pressed={!isRotating}
        >
          {isRotating ? <Pause className="h-4 w-4" /> : <RotateCw className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
