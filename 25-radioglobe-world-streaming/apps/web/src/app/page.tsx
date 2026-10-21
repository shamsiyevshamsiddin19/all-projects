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
        Birinchi ekran (hero).

        Ikki narsa hal qilingan:

        1. TO'LIQ EKRANGA SIG'ISH (faqat xl: va undan katta): bo'lim balandligi
           header'ni ayirib `100dvh` ga tenglashtiriladi — sahifa ochilganda
           foydalanuvchi ikkinchi bo'lim (davlatlar katalogi)ni ko'rmaydi,
           pastga aylantirganda ko'radi. `overflow-hidden` kontent hech qachon
           bo'lim balandligidan OSHIB ketmasligini kafolatlaydi. Mobil/planshet
           kichik balandliklarda bu majburlanmaydi — hammasini bitta ekranga
           siqish u yerda matnni ezib tashlardi, shuning uchun u yerda tabiiy
           oqim (scroll) qoladi.

        2. GLOBUS HAQIQIY EKRAN CHEKKASIGA TEGADI: tashqi `<section>` ENDI
           `max-w-7xl` bilan cheklanmagan (to'liq kenglikda). Faqat MATN
           ustuni o'zining ichki konteyneri bilan sahifaning qolgan qismi
           bilan bir xil chegaraga tekislanadi; globus ustuni esa hech qanday
           o'ng padding olmaydi va haqiqiy brauzer oynasining chekkasigacha
           cho'ziladi. Shu bilan GlobeHUD'dagi panel va +/- tugmalari ham
           (ular globus konteyneriga nisbatan joylashgan) avtomatik haqiqiy
           o'ng chekkaga boradi — monitor qancha keng bo'lishidan qat'i nazar.

        Sarlavha SSR HTML'da bo'lishi shart: globus WebGL canvas, ya'ni qidiruv
        tizimlari uchun butunlay bo'sh. Shu blok bir vaqtda LCP elementi ham —
        canvas emas, matn.
      */}
      <section className="w-full xl:h-[calc(100dvh-3.5rem)] xl:overflow-hidden">
        <div className="grid grid-cols-1 gap-6 xl:h-full xl:grid-cols-[420px_1fr] xl:items-center xl:gap-10">
          <div className="mx-auto w-full max-w-7xl px-4 pb-0 pt-8 lg:px-8 xl:mx-0 xl:w-auto xl:max-w-none xl:py-0 xl:pl-8 xl:pr-0">
            <p className="eyebrow flex items-center gap-2">
              <span className="live-dot" aria-hidden="true" />
              Jonli efir
            </p>

            <h1 className="mt-2.5 font-display text-3xl font-semibold leading-[1.1] tracking-tight text-text-primary sm:text-5xl xl:text-4xl">
              Dunyoning istalgan nuqtasidagi radioni tinglang
            </h1>

            <p className="mt-3 text-sm leading-relaxed text-text-secondary sm:text-base">
              Globusni aylantiring, davlatni tanlang va efirni bir bosishda oching.
              Ro'yxatdan o'tish ham, reklama ham yo'q.
            </p>

            <dl className="mt-5 flex flex-wrap items-center gap-x-8 gap-y-3 xl:flex-col xl:items-start xl:gap-y-5">
              <div className="flex items-center gap-8 xl:gap-6">
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
          </div>

          <div className="pb-8 xl:h-full xl:pb-0" aria-label="Interaktiv globus">
            <GlobeClientWrapper
              countries={countries}
              geojsonUrl={`${API_BASE}/map/countries.geojson`}
            />
          </div>
        </div>
      </section>

      {/* Qidiruv tizimlari uchun asosiy kirish nuqtasi — haqiqiy <a> havolalar */}
      <FallbackCountryList countries={countries} />
    </>
  );
}
