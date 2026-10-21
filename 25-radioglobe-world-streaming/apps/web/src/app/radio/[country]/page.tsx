import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';

import StationCard from '@/components/Country/StationCard';
import { fetchCountryChannels, fetchCountryDetail } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

interface CountryPageProps {
  params: Promise<{ country: string }>;
  searchParams: Promise<{ tag?: string; sort?: string }>;
}

export async function generateMetadata({ params }: CountryPageProps): Promise<Metadata> {
  const { country } = await params;
  const [data, channels] = await Promise.all([
    fetchCountryDetail(country),
    // Sarlavhadagi raqam sahifadagi raqam bilan BIR XIL manbadan olinadi.
    // Oldin sarlavha `countries.radio_count` (ingest yangilaydigan
    // denormalizatsiya) dan, sahifa esa jonli COUNT dan olardi — ikkisi
    // o'rtasida farq paydo bo'lib, sarlavhada 200, sahifada 120 turardi.
    fetchCountryChannels(country, { limit: 1 }),
  ]);
  if (!data) return { title: 'Davlat topilmadi' };

  const name = data.name_uz || data.name_en;
  return {
    title: `${name} radiolari — ${channels.total} ta jonli stansiya`,
    description:
      `${name}ning eng mashhur jonli radiostansiyalarini onlayn tinglang. `
      + `Bepul, ro'yxatdan o'tmasdan.`,
    alternates: { canonical: `/radio/${data.slug}` },
    openGraph: {
      title: `${name} radiolari · RadioGlobe`,
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
    Bu sahifa bitta radiostansiya emas, stansiyalar RO'YXATi — shuning uchun
    CollectionPage + ItemList. Oldin `RadioStation` berilgan edi; bu semantik
    jihatdan noto'g'ri va Google uni e'tiborsiz qoldiradi.
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
    <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Globusga qaytish
      </Link>

      <header className="mt-6 flex flex-wrap items-start justify-between gap-6 border-b border-ink-800 pb-8">
        <div className="flex items-center gap-4">
          <span className="text-5xl leading-none sm:text-6xl" aria-hidden="true">
            {data.flag_emoji || '🌐'}
          </span>
          <div>
            <p className="eyebrow">{data.continent}</p>
            <h1 className="mt-1.5 font-display text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
              {name} radiolari
            </h1>
            <p className="mt-1.5 text-sm text-text-muted">
              {data.name_en}
              {/*
                Raqam yagona manbadan — channels.total. Oldin sarlavhada
                countries.radio_count, pastda esa stations.length turardi va
                bir sahifada ikki xil son ko'rinardi.
              */}
              {' · '}
              <span className="text-text-secondary">{channels.total} ta stansiya</span>
            </p>
          </div>
        </div>
      </header>

      {data.top_tags && data.top_tags.length > 0 ? (
        <nav className="mt-6 flex flex-wrap items-center gap-2" aria-label="Janr bo'yicha filtr">
          <Link
            href={`/radio/${country}`}
            className={`chip ${!tag ? 'chip-active' : 'hover:border-ink-600'}`}
          >
            Hammasi
          </Link>
          {data.top_tags.map((t) => (
            <Link
              key={t}
              href={`/radio/${country}?tag=${encodeURIComponent(t)}`}
              className={`chip ${tag === t ? 'chip-active' : 'hover:border-ink-600'}`}
            >
              {t}
            </Link>
          ))}
        </nav>
      ) : null}

      <section className="mt-6">
        <h2 className="sr-only">Stansiyalar ro'yxati</h2>

        {stations.length === 0 ? (
          <div className="surface px-6 py-16 text-center">
            <p className="text-sm font-medium text-text-primary">Stansiya topilmadi</p>
            <p className="mt-1.5 text-sm text-text-muted">
              {tag
                ? "Bu janr bo'yicha hozircha ishlaydigan stansiya yo'q."
                : "Bu davlat uchun hozircha ishlaydigan stansiya yo'q."}
            </p>
            {tag ? (
              <Link
                href={`/radio/${country}`}
                className="mt-4 inline-block text-sm text-signal-bright hover:underline"
              >
                Filtrni tozalash
              </Link>
            ) : null}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-3">
              {stations.map((station) => (
                <StationCard key={station.id} station={station} />
              ))}
            </div>
            {stations.length < channels.total ? (
              <p className="mt-6 text-center text-sm text-text-muted">
                {channels.total} tadan eng mashhur {stations.length} tasi ko'rsatildi
              </p>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
