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
    <div className="min-h-screen bg-space-950 py-8 px-4 lg:px-8">
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
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors py-1.5 px-3 rounded-xl bg-space-900 border border-space-800"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Globusga qaytish</span>
          </Link>
        </div>

        {/* Country Hero Header */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-space-900 via-space-850 to-space-900 border border-space-800 p-6 sm:p-8 mb-8 shadow-glass">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <span className="text-5xl sm:text-6xl drop-shadow-md">
                {countryData.flag_emoji || '🌍'}
              </span>
              <div>
                <div className="flex items-center gap-2 text-cyan-400 text-xs font-mono uppercase tracking-wider mb-1">
                  <Globe className="w-3.5 h-3.5" />
                  <span>{countryData.continent}</span>
                </div>
                <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
                  {countryData.name_uz || countryData.name_en} Radiostansiyalari
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  {countryData.name_en} • ISO: {countryData.iso2} • M49: {countryData.m49}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="px-4 py-2.5 rounded-2xl bg-cyan-950/80 border border-cyan-500/30 text-center">
                <span className="block text-xl font-extrabold text-cyan-400 font-mono">
                  {countryData.radio_count}
                </span>
                <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
                  Radiolar
                </span>
              </div>
            </div>
          </div>

          {/* Top Tags bar */}
          {countryData.top_tags && countryData.top_tags.length > 0 && (
            <div className="relative z-10 mt-6 pt-5 border-t border-space-800/80 flex items-center gap-2 flex-wrap">
              <span className="text-xs text-slate-400 mr-1 flex items-center gap-1">
                <Filter className="w-3 h-3" />
                Janrlar:
              </span>
              {countryData.top_tags.map((t) => (
                <Link
                  key={t}
                  href={`/radio/${country}?tag=${t}`}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-colors ${
                    tag === t
                      ? 'bg-cyan-500 text-space-950 border-cyan-400 font-semibold'
                      : 'bg-space-800/80 text-slate-300 border-space-700 hover:border-cyan-500/40'
                  }`}
                >
                  #{t}
                </Link>
              ))}
              {tag && (
                <Link
                  href={`/radio/${country}`}
                  className="text-xs px-2 py-1 rounded-lg bg-rose-950 text-rose-400 border border-rose-800"
                >
                  Filtrni tozalash ✕
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Stations Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-400" />
              <span>Mavjud Stansiyalar ({stations.length})</span>
            </h2>
          </div>

          {stations.length === 0 ? (
            <div className="text-center py-16 rounded-2xl bg-space-900 border border-space-800">
              <Radio className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">Stansiyalar topilmadi</h3>
              <p className="text-xs text-slate-400 mt-1">
                Ushbu davlat yoki filtr bo'yicha hozircha faol oqimlar mavjud emas.
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
