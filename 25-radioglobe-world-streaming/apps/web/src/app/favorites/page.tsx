'use client';

import React from 'react';
import Link from 'next/link';
import { Heart, Radio, ArrowLeft } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import StationCard from '@/components/Country/StationCard';

export default function FavoritesPage() {
  const { favorites } = usePlayerStore();

  return (
    <div className="min-h-screen bg-void-950 py-8 px-4 lg:px-8 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors py-1.5 px-3 bg-void-900 border border-void-750 hover:border-crimson"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-crimson" />
            <span>[ RETURN TO GLOBE COMMAND ]</span>
          </Link>
        </div>

        <div className="flex items-center gap-4 mb-8">
          <div className="w-12 h-12 bg-void-900 border border-crimson/50 flex items-center justify-center text-crimson shadow-crimson-glow">
            <Heart className="w-6 h-6 fill-crimson text-crimson" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-white tracking-wider uppercase">
              SEVIMLI RADIOLAR [ FAVORITES ]
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
              Siz saqlagan barcha sevimli stansiyalar ro'yxati (jami {favorites.length} ta).
            </p>
          </div>
        </div>

        {favorites.length === 0 ? (
          <div className="text-center py-20 bg-void-900 border border-void-800 p-6">
            <Radio className="w-12 h-12 text-slate-700 mx-auto mb-3" />
            <h3 className="text-base font-bold text-white uppercase">HOZIRCHA SEVIMLILAR YO'Q</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Globusdan yoki davlatlar ro'yxatidan o'zingizga yoqqan stansiyalarning yurakcha tugmasini bosing.
            </p>
            <Link
              href="/"
              className="inline-block mt-4 text-xs font-bold px-4 py-2 bg-crimson hover:bg-crimson-light text-white transition-colors shadow-crimson-glow"
            >
              [ GLOBUSGA O'TISH ]
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
