import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { fetchCountryDetail, fetchCountryChannels } from '@/lib/api';
import StationCard from '@/components/Country/StationCard';
import { Radio, ArrowLeft, Globe, Filter } from 'lucide-react';

interface CountryPageProps {
  params: Promise<{ country: string }>;
  searchParams: Promise<{ tag?: string; sort?: string }>;
}

export async function generateMetadata({ params }: CountryPageProps): Promise<Metadata> {
  const { country } = await params;
  const countryData = await fetchCountryDetail(country);
  if (!countryData) {
    return { title: 'Davlat topilmadi — RadioGlobe' };
  }

  const name = countryData.name_uz || countryData.name_en;
  return {
    title: `${name} Radiostansiyalari (${countryData.radio_count}) — Onlayn Tinglash | RadioGlobe`,
    description: `${name}ning eng mashhur jonli radiostansiyalarini onlayn, yuqori sifatda tinglang. Bepul, reklamasiz va uzluksiz oqim.`,
    openGraph: {
      title: `${name} Radiostansiyalari — RadioGlobe`,
      description: `${name} radiolarini to'g'ridan-to'g'ri tinglang.`,
    },
  };
}

export default async function CountryPage({ params, searchParams }: CountryPageProps) {
  const { country } = await params;
  const { tag, sort } = await searchParams;

  const countryData = await fetchCountryDetail(country);
  if (!countryData) {
    notFound();
  }

  const channelsData = await fetchCountryChannels(country, { tag, sort });
  const stations = channelsData.items || [];

  // JSON-LD schema for SEO
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'RadioStation',
    name: `${countryData.name_uz} Radiolari`,
    areaServed: countryData.name_en,
    numberOfItems: countryData.radio_count,
  };

  return (
    <div className="min-h-screen bg-void-950 py-8 px-4 lg:px-8 font-mono">
      {/* Inject JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto">
        {/* Navigation Breadcrumb */}
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors py-1.5 px-3 bg-void-900 border border-void-750 hover:border-crimson"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-crimson" />
            <span>[ RETURN TO GLOBE COMMAND ]</span>
          </Link>
        </div>

        {/* Country Hero Header */}
        <div className="relative overflow-hidden tactical-box p-6 sm:p-8 mb-8 shadow-tactical-glass">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <span className="text-5xl sm:text-6xl drop-shadow-md">
                {countryData.flag_emoji || '⌖'}
              </span>
              <div>
                <div className="flex items-center gap-2 text-crimson text-xs uppercase tracking-wider mb-1 font-bold">
                  <Globe className="w-3.5 h-3.5" />
                  <span>SECTOR: {countryData.continent}</span>
                </div>
                <h1 className="text-2xl sm:text-4xl font-black text-white tracking-wider uppercase">
                  {countryData.name_uz || countryData.name_en} RADIOLARI
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  {countryData.name_en} • ISO: {countryData.iso2} • M49: {countryData.m49}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="px-5 py-3 bg-crimson-dark border border-crimson/50 text-center">
                <span className="block text-2xl font-black text-crimson-bright font-mono">
                  {countryData.radio_count}
                </span>
                <span className="text-[10px] text-slate-300 uppercase tracking-widest font-bold">
                  BROADCAST NODES
                </span>
              </div>
            </div>
          </div>

          {/* Top Tags bar */}
          {countryData.top_tags && countryData.top_tags.length > 0 && (
            <div className="relative z-10 mt-6 pt-5 border-t border-void-800 flex items-center gap-2 flex-wrap">
              <span className="text-xs text-slate-400 mr-1 flex items-center gap-1 font-semibold">
                <Filter className="w-3 h-3 text-crimson" />
                FREQUENCIES:
              </span>
              {countryData.top_tags.map((t) => (
                <Link
                  key={t}
                  href={`/radio/${country}?tag=${t}`}
                  className={`text-xs px-2.5 py-1 border transition-colors ${
                    tag === t
                      ? 'bg-crimson text-white border-crimson font-bold shadow-crimson-glow'
                      : 'bg-void-900 text-slate-300 border-void-750 hover:border-crimson hover:text-white'
                  }`}
                >
                  #{t}
                </Link>
              ))}
              {tag && (
                <Link
                  href={`/radio/${country}`}
                  className="text-xs px-2 py-1 bg-void-900 text-crimson-bright border border-crimson"
                >
                  RESET FILTER ✕
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Stations Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2 tracking-wider uppercase">
              <Radio className="w-4 h-4 text-crimson" />
              <span>ACTIVE SIGNALS ({stations.length})</span>
            </h2>
          </div>

          {stations.length === 0 ? (
            <div className="text-center py-16 bg-void-900 border border-void-800">
              <Radio className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-white uppercase">SIGNAL NOT FOUND</h3>
              <p className="text-xs text-slate-400 mt-1">
                Ushbu davlat yoki filtr bo'yicha hozircha faol to'lqinlar mavjud emas.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stations.map((st) => (
                <StationCard key={st.id} station={st} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
