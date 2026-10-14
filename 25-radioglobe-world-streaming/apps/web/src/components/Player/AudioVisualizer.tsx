'use client';

import React, { useEffect, useRef } from 'react';

import { audioEngine } from '@/lib/audioEngine';

const BAR_COUNT = 10;

/**
 * Haqiqiy audio spektri.
 *
 * Oldin bu komponent qattiq yozilgan balandliklar bilan CSS animatsiya edi —
 * ya'ni ovozga hech qanday aloqasi yo'q bezak. Endi u `AnalyserNode` orqali
 * aynan eshitilayotgan oqimdan o'qiydi.
 *
 * Agar Web Audio ishlamasa (CORS yo'q, eski brauzer), komponent jim ravishda
 * oddiy animatsiyaga tushadi — ijro buzilmaydi.
 */
export default function AudioVisualizer({ isPlaying }: { isPlaying: boolean }) {
  const barsRef = useRef<(HTMLSpanElement | null)[]>([]);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isPlaying) {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      barsRef.current.forEach((bar) => {
        if (bar) bar.style.height = '3px';
      });
      return;
    }

    const reduceMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;

    audioEngine.resumeContext();
    const analyser = audioEngine.getAnalyser();

    if (!analyser) {
      // Zaxira: spektr o'qib bo'lmasa, ijro davom etayotganini bildiruvchi
      // oddiy pulsatsiya
      barsRef.current.forEach((bar, i) => {
        if (bar) {
          bar.style.height = `${30 + ((i * 37) % 60)}%`;
          bar.style.transition = 'height 400ms ease-in-out';
        }
      });
      return;
    }

    const data = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(data);
      const step = Math.max(1, Math.floor(data.length / BAR_COUNT));
      for (let i = 0; i < BAR_COUNT; i += 1) {
        const bar = barsRef.current[i];
        if (!bar) continue;
        const value = data[i * step] ?? 0;
        bar.style.height = `${Math.max(8, (value / 255) * 100)}%`;
      }
      frameRef.current = requestAnimationFrame(draw);
    };

    frameRef.current = requestAnimationFrame(draw);

    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [isPlaying]);

  return (
    <div
      className="flex items-end gap-[2px] h-3.5 px-1"
      aria-hidden="true"
    >
      {Array.from({ length: BAR_COUNT }).map((_, i) => (
        <span
          key={i}
          ref={(el) => {
            barsRef.current[i] = el;
          }}
          className={`w-[3px] ${isPlaying ? 'bg-crimson' : 'bg-void-750'}`}
          style={{ height: '3px', transition: 'height 90ms linear' }}
        />
      ))}
    </div>
  );
}
