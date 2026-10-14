import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Filter, Globe, Radio } from 'lucide-react';

import StationCard from '@/components/Country/StationCard';
import { fetchCountryChannels, fetchCountryDetail } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

interface CountryPageProps {
  params: Promise<{ country: string }>;
  searchParams: Promise<{ tag?: string; sort?: string }>;
}

export async function generateMetadata({ params }: CountryPageProps): Promise<Metadata> {
  const { country } = await params;
  const data = await fetchCountryDetail(country);
  if (!data) return { title: 'Davlat topilmadi' };

  const name = data.name_uz || data.name_en;
  return {
    title: `${name} radiolari — ${data.radio_count} ta jonli stansiya`,
    description:
      `${name}ning eng mashhur jonli radiostansiyalarini onlayn tinglang. `
      + `${data.radio_count} ta ishlaydigan stansiya, bepul va ro'yxatdan o'tmasdan.`,
    alternates: { canonical: `/radio/${data.slug}` },
    openGraph: {
      title: `${name} radiolari | RadioGlobe`,
      description: `${name} radiolarini to'g'ridan-to'g'ri tinglang.`,
      url: `${SITE_URL}/radio/${data.slug}`,
    },
  };
}

export default async function CountryPage({ params, searchParams }: CountryPageProps) {
  const { country } = await params;
  const { tag, sort } = await searchParams;

  const data = await fetchCountryDetail(country);
  if (!data) notFound();

  const channels = await fetchCountryChannels(country, { tag, sort, limit: 60 });
  const stations = channels.items ?? [];
  const name = data.name_uz || data.name_en;

  /*
    JSON-LD: bu sahifa bitta radiostansiya emas, stansiyalar RO'YXATi.
    Oldin unga `@type: RadioStation` berilgan edi — semantik jihatdan noto'g'ri
    va Google uni e'tiborsiz qoldiradi.
  */
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `${name} radiolari`,
    url: `${SITE_URL}/radio/${data.slug}`,
    inLanguage: 'uz',
    about: { '@type': 'Country', name: data.name_en },
    mainEntity: {
      '@type': 'ItemList',
      numberOfItems: channels.total,
      itemListElement: stations.slice(0, 20).map((station, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        item: {
          '@type': 'RadioStation',
          name: station.name,
          url: `${SITE_URL}/stansiya/${station.slug}`,
          ...(station.logo_url ? { logo: station.logo_url } : {}),
        },
      })),
    },
  };

  return (
    <div className="min-h-screen bg-void-950 py-8 px-4 lg:px-8 font-mono">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto">
        <nav className="mb-6" aria-label="Navigatsiya">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors py-1.5 px-3 bg-void-900 border border-void-750 hover:border-crimson"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-crimson" />
            <span>Globusga qaytish</span>
          </Link>
        </nav>

        <header className="relative overflow-hidden tactical-box p-6 sm:p-8 mb-8 shadow-tactical-glass">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <span className="text-5xl sm:text-6xl" aria-hidden="true">
                {data.flag_emoji || '⌖'}
              </span>
              <div>
                <div className="flex items-center gap-2 text-crimson text-xs uppercase tracking-wider mb-1 font-bold">
                  <Globe className="w-3.5 h-3.5" />
                  <span>{data.continent}</span>
                </div>
                <h1 className="text-2xl sm:text-4xl font-black text-white tracking-wider uppercase">
                  {name} radiolari
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  {data.name_en} • ISO: {data.iso2}
                </p>
              </div>
            </div>

            <div className="px-5 py-3 bg-crimson-dark border border-crimson/50 text-center">
              {/*
                Bitta manba: channels.total. Oldin bu yerda countries.radio_count,
                pastda esa stations.length ko'rsatilardi — bir sahifada ikki xil
                raqam chiqib, foydalanuvchini chalkashtirardi.
              */}
              <span className="block text-2xl font-black text-crimson-bright">
                {channels.total}
              </span>
              <span className="text-[10px] text-slate-300 uppercase tracking-widest font-bold">
                stansiya
              </span>
            </div>
          </div>

          {data.top_tags && data.top_tags.length > 0 ? (
            <div className="relative z-10 mt-6 pt-5 border-t border-void-800 flex items-center gap-2 flex-wrap">
              <span className="text-xs text-slate-400 mr-1 flex items-center gap-1 font-semibold">
                <Filter className="w-3 h-3 text-crimson" />
                Janrlar:
              </span>
              {data.top_tags.map((t) => (
                <Link
                  key={t}
                  href={`/radio/${country}?tag=${encodeURIComponent(t)}`}
                  className={`text-xs px-2.5 py-1 border transition-colors ${
                    tag === t
                      ? 'bg-crimson text-white border-crimson font-bold shadow-crimson-glow'
                      : 'bg-void-900 text-slate-300 border-void-750 hover:border-crimson hover:text-white'
                  }`}
                >
                  #{t}
                </Link>
              ))}
              {tag ? (
                <Link
                  href={`/radio/${country}`}
                  className="text-xs px-2 py-1 bg-void-900 text-crimson-bright border border-crimson"
                >
                  Filtrni tozalash ✕
                </Link>
              ) : null}
            </div>
          ) : null}
        </header>

        <section>
          <h2 className="text-base font-bold text-white flex items-center gap-2 tracking-wider uppercase mb-4">
            <Radio className="w-4 h-4 text-crimson" />
            <span>
              {tag ? `#${tag} stansiyalari` : 'Stansiyalar'}
              {stations.length < channels.total ? (
                <span className="text-slate-500 font-normal ml-2 text-xs normal-case">
                  (eng mashhur {stations.length} tasi, jami {channels.total})
                </span>
              ) : null}
            </span>
          </h2>

          {stations.length === 0 ? (
            <div className="text-center py-16 bg-void-900 border border-void-800">
              <Radio className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-white uppercase">Stansiya topilmadi</h3>
              <p className="text-xs text-slate-400 mt-1">
                {tag
                  ? "Bu janr bo'yicha hozircha ishlaydigan stansiya yo'q."
                  : "Bu davlat uchun hozircha ishlaydigan stansiya yo'q."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stations.map((station) => (
                <StationCard key={station.id} station={station} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
