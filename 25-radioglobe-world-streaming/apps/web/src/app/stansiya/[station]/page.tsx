import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Globe2, Signal } from 'lucide-react';

import StationCard from '@/components/Country/StationCard';
import StationLogo from '@/components/Country/StationLogo';
import { fetchChannelDetail } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

interface StationPageProps {
  params: Promise<{ station: string }>;
}

export async function generateMetadata({ params }: StationPageProps): Promise<Metadata> {
  const { station } = await params;
  const data = await fetchChannelDetail(station);
  if (!data) return { title: 'Stansiya topilmadi' };

  const genres = data.tags.slice(0, 3).join(', ');
  return {
    title: `${data.name} — onlayn tinglash`,
    description:
      `${data.name} radiosini jonli efirda bepul tinglang.`
      + (genres ? ` Janr: ${genres}.` : ''),
    alternates: { canonical: `/stansiya/${data.slug}` },
    openGraph: {
      title: `${data.name} | RadioGlobe`,
      description: `${data.name} radiosini jonli efirda tinglang.`,
      url: `${SITE_URL}/stansiya/${data.slug}`,
      ...(data.logo_url ? { images: [{ url: data.logo_url }] } : {}),
    },
  };
}

/**
 * Alohida stansiya sahifasi.
 *
 * Bu sahifa oldin umuman yo'q edi, `fetchChannelDetail` esa yozilgan bo'lsa-da
 * hech qayerda ishlatilmasdi. SEO nuqtai nazaridan eng ko'p sahifa aynan shu
 * turda bo'ladi — "<stansiya nomi> onlayn tinglash" so'rovlari.
 */
export default async function StationPage({ params }: StationPageProps) {
  const { station } = await params;
  const data = await fetchChannelDetail(station);
  if (!data) notFound();

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'RadioStation',
    name: data.name,
    url: `${SITE_URL}/stansiya/${data.slug}`,
    inLanguage: data.languages?.[0] || 'uz',
    ...(data.logo_url ? { logo: data.logo_url } : {}),
    ...(data.homepage ? { sameAs: [data.homepage] } : {}),
    ...(data.tags.length ? { genre: data.tags } : {}),
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 lg:px-8">
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

      <header className="mt-6 flex flex-col gap-5 border-b border-ink-800 pb-8 sm:flex-row sm:items-center">
        <StationLogo src={data.logo_url} alt={data.name} size={80} />
        <div className="min-w-0">
          <p className="eyebrow">Jonli radio</p>
          <h1 className="mt-1.5 break-words font-display text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
            {data.name}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-text-muted">
            {data.primary_stream?.bitrate ? (
              <span className="flex items-center gap-1.5">
                <Signal className="h-3.5 w-3.5" />
                {data.primary_stream.bitrate} kbps
              </span>
            ) : null}
            {data.primary_stream?.format ? (
              <span className="uppercase">{data.primary_stream.format}</span>
            ) : null}
            {data.homepage ? (
              <a
                href={data.homepage}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="flex items-center gap-1.5 transition-colors hover:text-text-primary"
              >
                <Globe2 className="h-3.5 w-3.5" />
                Rasmiy sayt
              </a>
            ) : null}
          </div>
        </div>
      </header>

      {data.tags.length > 0 ? (
        <nav className="mt-6 flex flex-wrap gap-2" aria-label="Janrlar">
          {data.tags.map((t) => (
            <Link key={t} href={`/janr/${encodeURIComponent(t)}`} className="chip hover:border-ink-600">
              {t}
            </Link>
          ))}
        </nav>
      ) : null}

      <section className="mt-6">
        <h2 className="eyebrow mb-3">Tinglash</h2>
        <StationCard station={data} linkToStation={false} />
        <p className="mt-5 text-sm leading-relaxed text-text-muted">
          Oqim stansiyaning o'z serveridan keladi. RadioGlobe audio fayllarni
          saqlamaydi — faqat ommaviy e'lon qilingan jonli efir manzillarini
          katalog qiladi.
        </p>
      </section>
    </div>
  );
}
