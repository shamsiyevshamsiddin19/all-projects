'use client';

import React, { useEffect, useRef } from 'react';

import { audioEngine } from '@/lib/audioEngine';

interface Props {
  isPlaying: boolean;
  /** Ustunlar soni */
  bars?: number;
  /** Balandligi (px) */
  height?: number;
  className?: string;
}

/**
 * Haqiqiy audio spektri.
 *
 * Bu komponent bezak EMAS: u `AnalyserNode` orqali aynan hozir eshitilayotgan
 * oqimdan chastota ma'lumotini o'qiydi. Oldin shu o'rinda qo'lda yozilgan
 * balandliklar bilan CSS animatsiya turardi — u ovozga umuman bog'liq emasdi.
 *
 * Web Audio ishlamasa (CORS yo'q, eski brauzer) ustunlar jim turadi —
 * soxta harakat ko'rsatilmaydi.
 */
export default function AudioVisualizer({
  isPlaying,
  bars = 10,
  height = 14,
  className = '',
}: Props) {
  const barsRef = useRef<(HTMLSpanElement | null)[]>([]);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const reset = () => {
      barsRef.current.forEach((bar) => {
        if (bar) bar.style.height = '2px';
      });
    };

    if (!isPlaying) {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      reset();
      return;
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    audioEngine.resumeContext();
    const analyser = audioEngine.getAnalyser();
    if (!analyser) return;

    const data = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(data);
      // Past chastotalar eng ko'p energiyaga ega — spektrning faqat pastki
      // uchdan ikki qismini olamiz, aks holda o'ng tomondagi ustunlar
      // doim jim turadi
      const usable = Math.floor(data.length * 0.66);
      const step = Math.max(1, Math.floor(usable / bars));

      for (let i = 0; i < bars; i += 1) {
        const bar = barsRef.current[i];
        if (!bar) continue;
        const value = data[i * step] ?? 0;
        bar.style.height = `${Math.max(2, (value / 255) * height)}px`;
      }
      frameRef.current = requestAnimationFrame(draw);
    };

    frameRef.current = requestAnimationFrame(draw);

    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [isPlaying, bars, height]);

  return (
    <div
      className={`flex items-end gap-[2px] ${className}`}
      style={{ height }}
      aria-hidden="true"
    >
      {Array.from({ length: bars }).map((_, i) => (
        <span
          key={i}
          ref={(el) => {
            barsRef.current[i] = el;
          }}
          className={`w-[2px] rounded-full ${isPlaying ? 'bg-signal' : 'bg-ink-700'}`}
          style={{ height: 2, transition: 'height 80ms linear' }}
        />
      ))}
    </div>
  );
}
