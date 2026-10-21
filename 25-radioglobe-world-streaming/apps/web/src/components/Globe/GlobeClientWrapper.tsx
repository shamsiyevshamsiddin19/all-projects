'use client';

import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';

import FallbackCountryList from '@/components/Globe/FallbackCountryList';
import type { Country } from '@/types';

const GlobeMap = dynamic(() => import('@/components/Globe/GlobeMap'), {
  // WebGL serverda mavjud emas — globus faqat brauzerda yuklanadi
  ssr: false,
  loading: () => (
    <div className="w-full h-[60vh] min-h-[420px] xl:h-full bg-ink-950 flex flex-col items-center justify-center gap-4">
      <div className="w-12 h-12 rounded-full border-2 border-ink-700 border-t-signal animate-spin" />
      <p className="text-xs font-mono text-text-muted tracking-widest uppercase">
        Globus yuklanmoqda…
      </p>
    </div>
  ),
});

const MIN_GLOBE_WIDTH = 640;

interface Props {
  countries: Country[];
  geojsonUrl: string;
}

/**
 * Globusni ko'rsatish yoki ro'yxatga tushish haqida qaror qabul qiladi.
 *
 * Globus quyidagi hollarda YUKLANMAYDI:
 *   - ekran tor (mobilda globusni barmoq bilan boshqarish noqulay)
 *   - foydalanuvchi animatsiyani kamaytirishni so'ragan
 *   - MapLibre ishga tushmadi (WebGL yo'q yoki GPU kontekst bermadi)
 *
 * WebGL OLDINDAN tekshirilmaydi. `canvas.getContext('webgl')` sahifa
 * yuklanayotgan paytda GPU jarayoni hali tayyor bo'lmagani uchun noto'g'ri
 * `false` qaytarishi mumkin va globus bejiz o'chib qolardi. Shuning uchun
 * globusni ishga tushirib ko'ramiz va faqat haqiqatan yiqilsa ro'yxatga
 * tushamiz.
 *
 * Kenglik `window.innerWidth` orqali emas, konteynerning O'Z o'lchami orqali
 * va `ResizeObserver` bilan o'lchanadi. Sababi: hydration paytida oyna
 * o'lchami hali 0 bo'lishi mumkin, keyin esa haqiqiy qiymatga `resize`
 * hodisasisiz o'tadi — bir martalik tekshiruv o'sha nolda qotib qolib,
 * keng ekranli foydalanuvchiga ham ro'yxat ko'rsatilardi.
 */
export default function GlobeClientWrapper({ countries, geojsonUrl }: Props) {
  const probeRef = useRef<HTMLDivElement | null>(null);
  const [decision, setDecision] = useState<'pending' | 'globe' | 'list'>('pending');

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDecision('list');
      return;
    }

    const element = probeRef.current;
    if (!element) {
      setDecision('globe');
      return;
    }

    let decided = false;
    const evaluate = (width: number) => {
      // Kenglik hali o'lchanmagan bo'lsa qaror qabul qilmaymiz — keyingi
      // kuzatuv chaqiruvini kutamiz
      if (width <= 0) return;
      decided = true;
      setDecision(width >= MIN_GLOBE_WIDTH ? 'globe' : 'list');
    };

    evaluate(element.getBoundingClientRect().width);

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) evaluate(entry.contentRect.width);
    });
    observer.observe(element);

    /*
      Xavfsizlik taymeri: ba'zi muhitlarda element o'lchami umuman kelmaydi
      (0 bo'lib qolaveradi). Taymersiz foydalanuvchi aylanuvchi spinnerni
      abadiy ko'rib turardi. Nol kenglik "ekran kichkina" degani emas, shuning
      uchun globusni tanlaymiz — u ishga tushmasa `onUnsupported` baribir
      ro'yxatga qaytaradi.
    */
    const safety = setTimeout(() => {
      if (!decided) setDecision('globe');
    }, 1500);

    return () => {
      clearTimeout(safety);
      observer.disconnect();
    };
  }, []);

  return (
    <div ref={probeRef} className="w-full h-[60vh] min-h-[420px] xl:h-full">
      {decision === 'pending' ? (
        <div className="w-full h-[60vh] min-h-[420px] xl:h-full bg-ink-950 flex items-center justify-center">
          <div className="w-10 h-10 rounded-full border-2 border-ink-700 border-t-signal animate-spin" />
        </div>
      ) : decision === 'list' ? (
        <FallbackCountryList
          countries={countries}
          heading="Davlatni tanlang"
          note="Davlatni ro'yxatdan tanlang — 3D globus kengroq ekranlarda ochiladi."
        />
      ) : (
        <GlobeMap
          countries={countries}
          geojsonUrl={geojsonUrl}
          onUnsupported={() => setDecision('list')}
        />
      )}
    </div>
  );
}
