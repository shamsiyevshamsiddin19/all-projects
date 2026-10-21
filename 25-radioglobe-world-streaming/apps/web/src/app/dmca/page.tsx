import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, Mail } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Mualliflik huquqi va shikoyatlar',
  description:
    "RadioGlobe audio fayllarni saqlamaydi. Havolani olib tashlash bo'yicha murojaat tartibi.",
  alternates: { canonical: '/dmca' },
  robots: { index: true, follow: false },
};

const EMAIL = 'shamsiyevshamsiddin19@gmail.com';

export default function DmcaPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8 lg:px-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-text-muted transition-colors hover:text-text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        Globusga qaytish
      </Link>

      <header className="mt-6 border-b border-ink-800 pb-8">
        <p className="eyebrow">Huquqiy</p>
        <h1 className="mt-1.5 font-display text-3xl font-semibold tracking-tight text-text-primary sm:text-4xl">
          Mualliflik huquqi va shikoyatlar
        </h1>
      </header>

      <div className="mt-8 space-y-8 text-sm leading-relaxed text-text-secondary">
        <div className="surface border-l-2 border-l-signal p-5">
          <p>
            <strong className="text-text-primary">RadioGlobe audio fayllarni saqlamaydi</strong>{' '}
            va ularni qayta uzatmaydi. Platforma — ommaviy ravishda e&apos;lon qilingan
            jonli efir havolalarining katalogi. Oqim har doim stansiyaning o&apos;z
            serveridan keladi.
          </p>
        </div>

        <section>
          <h2 className="font-display text-lg font-semibold text-text-primary">
            Qanday ishlaydi
          </h2>
          <p className="mt-2">
            Katalog ochiq{' '}
            <a
              href="https://www.radio-browser.info"
              target="_blank"
              rel="noopener noreferrer"
              className="text-signal-bright hover:underline"
            >
              radio-browser.info
            </a>{' '}
            bazasidan yig&apos;iladi. Biz faqat havola, nom, logotip manzili va janr
            kabi metama&apos;lumotni saqlaymiz. Proxy xizmati brauzerning
            mixed-content va CORS cheklovlarini hal qilish uchun ishlatiladi —
            hududiy cheklovlarni aylanib o&apos;tish uchun emas.
          </p>
        </section>

        <section>
          <h2 className="font-display text-lg font-semibold text-text-primary">
            Havolani olib tashlash
          </h2>
          <p className="mt-2">
            Agar siz stansiya egasi bo&apos;lsangiz va havolangiz katalogdan
            olib tashlanishini istasangiz, quyidagi manzilga yozing. Murojaatda
            stansiya nomi va havolasini ko&apos;rsating. So&apos;rovlar{' '}
            <strong className="text-text-primary">48 soat ichida</strong> ko&apos;rib
            chiqiladi.
          </p>

          <a
            href={`mailto:${EMAIL}?subject=RadioGlobe%20—%20havolani%20olib%20tashlash`}
            className="mt-4 inline-flex items-center gap-2.5 rounded-lg border border-ink-700
                       bg-ink-900 px-4 py-3 transition-colors hover:border-ink-600"
          >
            <Mail className="h-4 w-4 text-signal" />
            <span className="font-mono text-sm text-text-primary">{EMAIL}</span>
          </a>
        </section>

        <section>
          <h2 className="font-display text-lg font-semibold text-text-primary">
            Hududiy cheklovlar
          </h2>
          <p className="mt-2">
            Ba&apos;zi stansiyalar faqat o&apos;z davlatidan tinglanadi. Bunday
            oqimlar avtomatik aniqlanadi va ro&apos;yxatdan chiqarib tashlanadi —
            biz ularni ochishga urinmaymiz.
          </p>
        </section>
      </div>
    </div>
  );
}
