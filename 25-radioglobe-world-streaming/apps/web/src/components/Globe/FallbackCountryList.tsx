import React from 'react';
import Link from 'next/link';
import { Country } from '@/types';
import { Globe, Radio, ChevronRight } from 'lucide-react';

interface FallbackCountryListProps {
  countries: Country[];
}

export default function FallbackCountryList({ countries }: FallbackCountryListProps) {
  return (
    <section className="bg-space-950 py-12 px-4 lg:px-8 border-t border-space-850">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 mb-2">
              <Globe className="w-4 h-4" />
              <span className="text-xs uppercase font-mono tracking-widest font-semibold">
                Dunyo Radiostansiyalari Katalogi
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Barcha Davlatlar Bo'yicha Qidiruv
            </h2>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Globusdan tashqari to'g'ridan-to'g'ri istalgan davlat sahifasiga o'tib, uning
              jonli radiostansiyalarini yuqori sifatda tinglashingiz mumkin.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400">
            Jami: <span className="text-cyan-400 font-bold">{countries.length}</span> ta davlat
          </div>
        </div>

        {/* SEO Grid of HTML Links */}
        <nav aria-label="Davlatlar katalogi" className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {countries.map((c) => (
            <Link
              key={c.iso2}
              href={`/radio/${c.slug}`}
              className="group flex items-center justify-between p-3 rounded-xl bg-space-900/60 border border-space-800/80 hover:border-cyan-500/40 hover:bg-space-850/80 transition-all duration-200"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="text-lg flex-shrink-0">{c.flag_emoji || '🌍'}</span>
                <span className="text-xs font-medium text-slate-200 group-hover:text-cyan-300 truncate transition-colors">
                  {c.name_uz || c.name_en}
                </span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-space-800 text-cyan-400 border border-space-700 flex-shrink-0 ml-1">
                {c.radio_count}
              </span>
            </Link>
          ))}
        </nav>
      </div>
    </section>
  );
}
