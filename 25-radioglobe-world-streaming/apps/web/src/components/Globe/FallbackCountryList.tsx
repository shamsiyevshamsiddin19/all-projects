import React from 'react';
import Link from 'next/link';
import { Country } from '@/types';
import { Globe, Radio, ChevronRight } from 'lucide-react';

interface FallbackCountryListProps {
  countries: Country[];
}

export default function FallbackCountryList({ countries }: FallbackCountryListProps) {
  return (
    <section className="bg-void-950 py-12 px-4 lg:px-8 border-t border-void-800 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-crimson mb-2">
              <Globe className="w-4 h-4" />
              <span className="text-xs uppercase tracking-widest font-bold">
                [ GLOBAL SECTOR DIRECTORY ]
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wider uppercase">
              Barcha Davlatlar Katalogi
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Globusdan tashqari to'g'ridan-to'g'ri istalgan davlat chastotalarini ochish va tinglash.
            </p>
          </div>
          <div className="text-xs text-slate-400">
            JAMI SEKTORLAR: <span className="text-crimson font-bold">{countries.length}</span>
          </div>
        </div>

        {/* SEO Grid of HTML Links */}
        <nav aria-label="Davlatlar katalogi" className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {countries.map((c) => (
            <Link
              key={c.iso2}
              href={`/radio/${c.slug}`}
              className="group flex items-center justify-between p-3 bg-void-900/90 border border-void-800 hover:border-crimson/50 hover:bg-void-850 transition-all duration-200"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="text-lg flex-shrink-0">{c.flag_emoji || '⌖'}</span>
                <span className="text-xs font-semibold text-slate-300 group-hover:text-white uppercase truncate transition-colors">
                  {c.name_uz || c.name_en}
                </span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 bg-void-950 text-crimson-bright border border-void-750 flex-shrink-0 ml-1">
                {c.radio_count}
              </span>
            </Link>
          ))}
        </nav>
      </div>
    </section>
  );
}
