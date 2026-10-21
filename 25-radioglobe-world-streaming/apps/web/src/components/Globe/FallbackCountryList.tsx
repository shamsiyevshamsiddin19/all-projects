import React from 'react';
import Link from 'next/link';

import type { Country } from '@/types';

interface Props {
  countries: Country[];
  heading?: string;
  note?: string;
}

/**
 * Davlatlar katalogi — oddiy HTML havolalar.
 *
 * Ikki vazifani bajaradi:
 *   1. WebGL ishlamaydigan qurilmalarda globus o'rnini bosadi;
 *   2. Qidiruv tizimlari uchun yagona kirish nuqtasi — globus WebGL canvas
 *      bo'lgani uchun Google uchun butunlay bo'sh, shuning uchun barcha davlat
 *      sahifalariga shu yerdan havola bo'lishi shart.
 */
export default function FallbackCountryList({ countries, heading, note }: Props) {
  const withStations = countries.filter((c) => c.radio_count > 0);
  const list = withStations.length > 0 ? withStations : countries;

  // Qit'alar bo'yicha guruhlash — 240 ta havolani bir uyumda berish o'qib
  // bo'lmaydigan devor hosil qiladi
  const byContinent = list.reduce<Record<string, Country[]>>((acc, c) => {
    const key = c.continent && c.continent !== '—' ? c.continent : 'Boshqa';
    (acc[key] ||= []).push(c);
    return acc;
  }, {});

  // Guruhlar hajmi bo'yicha, lekin "Boshqa" har doim oxirida — umumiy
  // chelak ro'yxatning boshida turishi mantiqsiz ko'rinadi
  const continents = Object.entries(byContinent).sort(([aName, a], [bName, b]) => {
    if (aName === 'Boshqa') return 1;
    if (bName === 'Boshqa') return -1;
    return b.length - a.length;
  });

  return (
    <section className="border-t border-ink-800 bg-ink-950 px-4 py-14 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="eyebrow">Katalog</p>
            <h2 className="mt-2 font-display text-2xl font-semibold tracking-tight text-text-primary sm:text-3xl">
              {heading ?? 'Barcha davlatlar'}
            </h2>
            {note ? (
              <p className="mt-2 max-w-2xl text-sm text-text-secondary">{note}</p>
            ) : null}
          </div>
          <p className="text-sm text-text-muted">
            <span className="font-display text-lg font-semibold text-text-primary">
              {list.length}
            </span>{' '}
            davlat
          </p>
        </div>

        {list.length === 0 ? (
          <div className="surface px-6 py-12 text-center">
            <p className="text-sm font-medium text-text-primary">Katalog yuklanmadi</p>
            <p className="mt-1 text-sm text-text-muted">
              Server bilan bog'lanishda muammo bo'ldi. Sahifani yangilab ko'ring.
            </p>
          </div>
        ) : (
          <div className="space-y-9">
            {continents.map(([continent, items]) => (
              <div key={continent}>
                <h3 className="eyebrow mb-3">{continent}</h3>
                <nav
                  aria-label={`${continent} davlatlari`}
                  className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
                >
                  {items.map((c) => (
                    <Link
                      key={c.iso2}
                      href={`/radio/${c.slug}`}
                      className="flex items-center justify-between gap-2 rounded-lg border border-ink-800
                                 bg-ink-900 px-3 py-2.5 transition-colors
                                 hover:border-ink-600 hover:bg-ink-850"
                    >
                      <span className="flex min-w-0 items-center gap-2.5">
                        <span className="shrink-0 text-base" aria-hidden="true">
                          {c.flag_emoji || '🌐'}
                        </span>
                        <span className="truncate text-sm text-text-secondary">
                          {c.name_uz || c.name_en}
                        </span>
                      </span>
                      <span className="shrink-0 font-mono text-xs text-text-muted">
                        {c.radio_count}
                      </span>
                    </Link>
                  ))}
                </nav>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
