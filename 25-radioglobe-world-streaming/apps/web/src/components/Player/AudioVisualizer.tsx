'use client';

import React from 'react';

export default function AudioVisualizer({ isPlaying }: { isPlaying: boolean }) {
  return (
    <div className="flex items-end gap-0.5 h-4 px-1">
      {[40, 75, 55, 90, 60, 85, 45, 100, 65, 50].map((height, i) => (
        <span
          key={i}
          className={`w-0.5 rounded-full transition-all duration-300 ${
            isPlaying
              ? 'bg-gradient-to-t from-cyan-500 to-emerald-400 animate-pulse'
              : 'bg-space-700 h-1'
          }`}
          style={{
            height: isPlaying ? `${height}%` : '4px',
            animationDelay: `${i * 100}ms`,
            animationDuration: '800ms',
          }}
        />
      ))}
    </div>
  );
}
