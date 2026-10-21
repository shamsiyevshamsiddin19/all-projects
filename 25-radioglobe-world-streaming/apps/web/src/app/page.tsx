import Link from 'next/link';

import FallbackCountryList from '@/components/Globe/FallbackCountryList';
import GlobeClientWrapper from '@/components/Globe/GlobeClientWrapper';
import { fetchCountries, fetchStats } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Sahifa har 10 daqiqada qayta generatsiya qilinadi
export const revalidate = 600;

export default async function HomePage() {
  const [countries, stats] = await Promise.all([fetchCountries(300, false), fetchStats()]);
  const withStations = countries.filter((c) => c.radio_count > 0);

  // Raqamlar yagona manbadan (API /stats). Agar API javob bermasa, mavjud
  // ro'yxatdan hisoblaymiz — sahifada "0" turib qolmasligi uchun.
  const totalStations =
    stats.stations || withStations.reduce((sum, c) => sum + c.radio_count, 0);
  const totalCountries = stats.countries || withStations.length;

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'RadioGlobe',
    url: SITE_URL,
    inLanguage: 'uz',
    description: `${totalCountries} davlatdan ${totalStations} ta jonli radiostansiya.`,
    potentialAction: {
      '@type': 'SearchAction',
      target: { '@type': 'EntryPoint', urlTemplate: `${SITE_URL}/qidiruv?q={search_term_string}` },
      'query-input': 'required name=search_term_string',
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/*
        Sarlavha SSR HTML'da bo'lishi shart: globus WebGL canvas, ya'ni qidiruv
        tizimlari uchun butunlay bo'sh. Shu blok bir vaqtda LCP elementi ham —
        canvas emas, matn.
      */}
      <section className="mx-auto w-full max-w-7xl px-4 pb-4 pt-8 lg:px-8">
        <p className="eyebrow flex items-center gap-2">
          <span className="live-dot" aria-hidden="true" />
          Jonli efir
        </p>

        <h1 className="mt-2.5 max-w-2xl font-display text-3xl font-semibold leading-[1.1] tracking-tight text-text-primary sm:text-5xl">
          Dunyoning istalgan nuqtasidagi radioni tinglang
        </h1>

        <p className="mt-3 max-w-xl text-sm leading-relaxed text-text-secondary sm:text-base">
          Globusni aylantiring, davlatni tanlang va efirni bir bosishda oching.
          Ro'yxatdan o'tish ham, reklama ham yo'q.
        </p>

        <dl className="mt-5 flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <dt className="text-xs text-text-muted">Stansiyalar</dt>
            <dd className="font-display text-2xl font-semibold text-text-primary">
              {totalStations.toLocaleString('uz-UZ')}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-text-muted">Davlatlar</dt>
            <dd className="font-display text-2xl font-semibold text-text-primary">
              {totalCountries}
            </dd>
          </div>
          {stats.top_genres.length > 0 ? (
            <div className="min-w-0">
              <dt className="text-xs text-text-muted">Mashhur janrlar</dt>
              <dd className="mt-1.5 flex flex-wrap gap-1.5">
                {stats.top_genres.slice(0, 6).map((g) => (
                  <Link
                    key={g.tag}
                    href={`/janr/${encodeURIComponent(g.tag)}`}
                    className="chip transition-colors hover:border-signal/50 hover:text-signal-bright"
                  >
                    {g.tag}
                  </Link>
                ))}
              </dd>
            </div>
          ) : null}
        </dl>
      </section>

      <section className="w-full" aria-label="Interaktiv globus">
        <GlobeClientWrapper
          countries={countries}
          geojsonUrl={`${API_BASE}/map/countries.geojson`}
        />
      </section>

      {/* Qidiruv tizimlari uchun asosiy kirish nuqtasi — haqiqiy <a> havolalar */}
      <FallbackCountryList countries={countries} />
    </>
  );
}
