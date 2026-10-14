import React from 'react';
import Link from 'next/link';
import { Globe, Radio } from 'lucide-react';

import type { Country } from '@/types';

interface Props {
  countries: Country[];
  heading?: string;
  note?: string;
}

/**
 * Davlatlar katalogi — oddiy HTML havolalar.
 *
 * Bu komponent ikki vazifani bajaradi:
 *   1. WebGL ishlamaydigan qurilmalarda globus o'rnini bosadi;
 *   2. Qidiruv tizimlari uchun yagona kirish nuqtasi — globus WebGL canvas
 *      bo'lgani uchun Google uchun butunlay bo'sh, shuning uchun saytdagi
 *      barcha davlat sahifalariga shu yerdan havola bo'lishi SHART.
 */
export default function FallbackCountryList({ countries, heading, note }: Props) {
  const withStations = countries.filter((c) => c.radio_count > 0);
  const list = withStations.length > 0 ? withStations : countries;

  return (
    <section className="bg-void-950 py-12 px-4 lg:px-8 border-t border-void-800 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="flex items-center gap-2 text-crimson mb-2">
              <Globe className="w-4 h-4" />
              <span className="text-xs uppercase tracking-widest font-bold">
                Davlatlar katalogi
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wider uppercase">
              {heading ?? 'Barcha davlatlar'}
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              {note ?? "Globusdan tashqari to'g'ridan-to'g'ri istalgan davlat radiolarini oching."}
            </p>
          </div>
          <div className="text-xs text-slate-400">
            Davlatlar: <span className="text-crimson font-bold">{list.length}</span>
          </div>
        </div>

        {list.length === 0 ? (
          <div className="text-center py-12 bg-void-900 border border-void-800">
            <Radio className="w-10 h-10 text-slate-700 mx-auto mb-3" />
            <p className="text-sm text-slate-300 font-bold uppercase">Katalog yuklanmadi</p>
            <p className="text-xs text-slate-500 mt-1">
              Server bilan bog'lanishda muammo bo'ldi. Sahifani yangilab ko'ring.
            </p>
          </div>
        ) : (
          <nav
            aria-label="Davlatlar katalogi"
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3"
          >
            {list.map((c) => (
              <Link
                key={c.iso2}
                href={`/radio/${c.slug}`}
                className="group flex items-center justify-between p-3 bg-void-900/90 border border-void-800 hover:border-crimson/50 hover:bg-void-850 transition-all duration-200"
              >
                <span className="flex items-center gap-2.5 min-w-0">
                  <span className="text-lg flex-shrink-0" aria-hidden="true">
                    {c.flag_emoji || '⌖'}
                  </span>
                  <span className="text-xs font-semibold text-slate-300 group-hover:text-white uppercase truncate transition-colors">
                    {c.name_uz || c.name_en}
                  </span>
                </span>
                <span className="text-[10px] px-1.5 py-0.5 bg-void-950 text-crimson-bright border border-void-750 flex-shrink-0 ml-1">
                  {c.radio_count}
                </span>
              </Link>
            ))}
          </nav>
        )}
      </div>
    </section>
  );
}
