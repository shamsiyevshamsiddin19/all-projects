'use client';

import React from 'react';

export default function AudioVisualizer({ isPlaying }: { isPlaying: boolean }) {
  return (
    <div className="flex items-end gap-1 h-3.5 px-1 font-mono">
      {[35, 75, 55, 95, 60, 85, 45, 100, 70, 50].map((height, i) => (
        <span
          key={i}
          className={`w-1 transition-all duration-300 ${
            isPlaying
              ? 'bg-crimson animate-pulse shadow-crimson-glow'
              : 'bg-void-750 h-1'
          }`}
          style={{
            height: isPlaying ? `${height}%` : '3px',
            animationDelay: `${i * 90}ms`,
            animationDuration: '650ms',
          }}
        />
      ))}
    </div>
  );
}
