import { Radio } from 'lucide-react';

import GlobeClientWrapper from '@/components/Globe/GlobeClientWrapper';
import FallbackCountryList from '@/components/Globe/FallbackCountryList';
import { fetchCountries } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Sahifa har 10 daqiqada qayta generatsiya qilinadi. Oldin build paytida bir
// marta prerender bo'lib muzlab qolgandi va "0 davlat" ko'rsatib turardi.
export const revalidate = 600;

export default async function HomePage() {
  const countries = await fetchCountries(300, false);
  const withStations = countries.filter((c) => c.radio_count > 0);
  const totalStations = countries.reduce((sum, c) => sum + c.radio_count, 0);

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'RadioGlobe',
    url: SITE_URL,
    inLanguage: 'uz',
    description: `${withStations.length} davlatdan ${totalStations} ta jonli radiostansiya.`,
    potentialAction: {
      '@type': 'SearchAction',
      target: { '@type': 'EntryPoint', urlTemplate: `${SITE_URL}/?q={search_term_string}` },
      'query-input': 'required name=search_term_string',
    },
  };

  return (
    <div className="flex flex-col">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/*
        Sarlavha SSR HTML'da bo'lishi SHART: globus WebGL canvas, ya'ni qidiruv
        tizimlari uchun butunlay bo'sh. Oldin sahifada bitta ham <h1> yo'q edi.
        Bu blok shu bilan birga LCP elementi ham — canvas emas, matn.
      */}
      <section className="px-4 lg:px-8 pt-8 pb-4 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2 text-crimson mb-2 font-mono">
          <Radio className="w-4 h-4" />
          <span className="text-xs uppercase tracking-widest font-bold">Jonli efir</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight uppercase font-mono">
          Dunyo radiolari bir bosishda
        </h1>
        <p className="text-sm text-slate-400 mt-3 max-w-2xl">
          Globusdan davlatni tanlang —{' '}
          <strong className="text-slate-200">{withStations.length} davlatdan</strong>{' '}
          <strong className="text-slate-200">{totalStations.toLocaleString('uz-UZ')} ta</strong>{' '}
          jonli radiostansiya. Bepul, ro'yxatdan o'tmasdan.
        </p>
      </section>

      <section className="relative w-full">
        <GlobeClientWrapper
          countries={countries}
          geojsonUrl={`${API_BASE}/map/countries.geojson`}
        />
      </section>

      {/* Qidiruv tizimlari uchun asosiy kirish nuqtasi — haqiqiy <a> havolalar */}
      <FallbackCountryList countries={countries} />
    </div>
  );
}
