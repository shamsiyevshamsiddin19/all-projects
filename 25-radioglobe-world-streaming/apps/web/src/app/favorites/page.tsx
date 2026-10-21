'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { Heart, Radio, ArrowLeft } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import StationCard from '@/components/Country/StationCard';

export default function FavoritesPage() {
  const favorites = usePlayerStore((s) => s.favorites);
  const hydrated = usePlayerStore((s) => s.hydrated);
  const hydrate = usePlayerStore((s) => s.hydrate);

  // Sevimlilar localStorage'da — ular faqat mijozda o'qiladi
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-ink-700 border-t-signal" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Globusga qaytish
      </Link>

      <header className="mt-6 border-b border-ink-800 pb-8">
        <p className="eyebrow">Shaxsiy</p>
        <h1 className="mt-1.5 font-display text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
          Sevimli radiolar
        </h1>
        <p className="mt-1.5 text-sm text-text-muted">
          {favorites.length > 0
            ? `${favorites.length} ta stansiya saqlangan`
            : "Hozircha bo'sh"}
        </p>
      </header>

      {favorites.length === 0 ? (
        <div className="surface mt-6 px-6 py-16 text-center">
          <Heart className="mx-auto h-8 w-8 text-ink-600" />
          <p className="mt-4 text-sm font-medium text-text-primary">
            Sevimli stansiyalar yo'q
          </p>
          <p className="mx-auto mt-1.5 max-w-sm text-sm text-text-muted">
            Istalgan stansiyadagi yurakcha belgisini bosing — u shu yerda
            saqlanadi va keyingi safar tezda topiladi.
          </p>
          <Link
            href="/"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-signal px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
          >
            <Radio className="h-4 w-4" />
            Stansiya topish
          </Link>
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-3">
          {favorites.map((station) => (
            <StationCard key={station.id} station={station} />
          ))}
        </div>
      )}
    </div>
  );
}
