import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';

import StationCard from '@/components/Country/StationCard';
import { fetchChannelsByTag } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

interface GenrePageProps {
  params: Promise<{ tag: string }>;
}

export async function generateMetadata({ params }: GenrePageProps): Promise<Metadata> {
  const { tag } = await params;
  const decoded = decodeURIComponent(tag);
  const label = decoded.charAt(0).toUpperCase() + decoded.slice(1);

  return {
    title: `${label} radiolari — onlayn tinglash`,
    description: `${label} janridagi jonli radiostansiyalar. Bepul, ro'yxatdan o'tmasdan.`,
    alternates: { canonical: `/janr/${tag}` },
    openGraph: {
      title: `${label} radiolari · RadioGlobe`,
      url: `${SITE_URL}/janr/${tag}`,
    },
  };
}

/**
 * Janr bo'yicha sahifa.
 *
 * SEO nuqtai nazaridan qimmatli: "jazz radio onlayn", "news radio tinglash"
 * kabi so'rovlar davlat nomisiz ham ko'p qidiriladi.
 */
export default async function GenrePage({ params }: GenrePageProps) {
  const { tag } = await params;
  const decoded = decodeURIComponent(tag).toLowerCase();
  const label = decoded.charAt(0).toUpperCase() + decoded.slice(1);

  const channels = await fetchChannelsByTag(decoded, 60);
  const stations = channels.items ?? [];

  if (stations.length === 0) notFound();

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: `${label} radiolari`,
    url: `${SITE_URL}/janr/${tag}`,
    inLanguage: 'uz',
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

      <header className="mt-6 border-b border-ink-800 pb-8">
        <p className="eyebrow">Janr</p>
        <h1 className="mt-1.5 font-display text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
          {label} radiolari
        </h1>
        <p className="mt-1.5 text-sm text-text-muted">
          Dunyo bo'ylab {channels.total} ta stansiya
        </p>
      </header>

      <div className="mt-6 grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-3">
        {stations.map((station) => (
          <StationCard key={station.id} station={station} />
        ))}
      </div>

      {stations.length < channels.total ? (
        <p className="mt-6 text-center text-sm text-text-muted">
          {channels.total} tadan eng mashhur {stations.length} tasi ko'rsatildi
        </p>
      ) : null}
    </div>
  );
}
