'use client';

import React from 'react';
import Link from 'next/link';
import { Heart, Radio, ArrowLeft } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import StationCard from '@/components/Country/StationCard';

export default function FavoritesPage() {
  const { favorites } = usePlayerStore();

  return (
    <div className="min-h-screen bg-space-950 py-8 px-4 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors py-1.5 px-3 rounded-xl bg-space-900 border border-space-800"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Globusga qaytish</span>
          </Link>
        </div>

        <div className="flex items-center gap-4 mb-8">
          <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
            <Heart className="w-6 h-6 fill-rose-500 text-rose-500" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Sevimli Radiostansiyalar
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
              Siz saqlagan barcha sevimli radiolar ro'yxati (jami {favorites.length} ta).
            </p>
          </div>
        </div>

        {favorites.length === 0 ? (
          <div className="text-center py-20 rounded-3xl bg-space-900/40 border border-space-850 p-6">
            <Radio className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">Hozircha sevimlilar yo'q</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Globusdan yoki davlatlar ro'yxatidan o'zingizga yoqqan stansiyalarning yurakcha tugmasini bosing.
            </p>
            <Link
              href="/"
              className="inline-block mt-4 text-xs font-bold px-4 py-2 rounded-xl bg-cyan-500 text-space-950 hover:bg-cyan-400 transition-colors"
            >
              Globusga o'tish
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {favorites.map((st) => (
              <StationCard key={st.id} station={st} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
