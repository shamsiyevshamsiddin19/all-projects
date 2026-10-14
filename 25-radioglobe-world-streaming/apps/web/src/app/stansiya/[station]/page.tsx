import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowLeft, Globe2, Radio, Signal } from 'lucide-react';

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
    <div className="min-h-screen bg-void-950 py-8 px-4 lg:px-8 font-mono">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-4xl mx-auto">
        <nav className="mb-6" aria-label="Navigatsiya">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors py-1.5 px-3 bg-void-900 border border-void-750 hover:border-crimson"
          >
            <ArrowLeft className="w-3.5 h-3.5 text-crimson" />
            <span>Globusga qaytish</span>
          </Link>
        </nav>

        <header className="tactical-box p-6 sm:p-8 mb-6 shadow-tactical-glass">
          <div className="flex flex-col sm:flex-row sm:items-center gap-5">
            <StationLogo src={data.logo_url} alt={data.name} size={88} />
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-crimson text-xs uppercase tracking-wider mb-1 font-bold">
                <Radio className="w-3.5 h-3.5" />
                <span>Jonli radio</span>
              </div>
              <h1 className="text-2xl sm:text-4xl font-black text-white tracking-wider uppercase break-words">
                {data.name}
              </h1>
              <div className="flex items-center gap-3 mt-2 flex-wrap text-xs text-slate-400">
                {data.primary_stream?.bitrate ? (
                  <span className="flex items-center gap-1">
                    <Signal className="w-3 h-3 text-crimson" />
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
                    className="flex items-center gap-1 hover:text-white transition-colors"
                  >
                    <Globe2 className="w-3 h-3" />
                    Rasmiy sayt
                  </a>
                ) : null}
              </div>
            </div>
          </div>

          {data.tags.length > 0 ? (
            <div className="mt-6 pt-5 border-t border-void-800 flex items-center gap-2 flex-wrap">
              {data.tags.map((t) => (
                <span
                  key={t}
                  className="text-xs px-2.5 py-1 bg-void-900 text-slate-300 border border-void-750"
                >
                  #{t}
                </span>
              ))}
            </div>
          ) : null}
        </header>

        <section>
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3">
            Tinglash
          </h2>
          <StationCard station={data} />
          <p className="text-xs text-slate-500 mt-4 leading-relaxed">
            Oqim stansiyaning o'z serveridan keladi. RadioGlobe audio fayllarni
            saqlamaydi — faqat ommaviy e'lon qilingan jonli efir manzillarini
            katalog qiladi.
          </p>
        </section>
      </div>
    </div>
  );
}
