'use client';

import React, { useState } from 'react';
import { Radio } from 'lucide-react';

interface StationLogoProps {
  src?: string | null;
  alt: string;
  size?: number;
  active?: boolean;
}

/**
 * Stansiya logosi.
 *
 * Logolar uchinchi tomon serverlarida va ularning bir qismi `http://` da
 * joylashgan. HTTPS sahifada bunday rasm mixed-content sifatida bloklanadi va
 * foydalanuvchi buzilgan rasm belgisini ko'radi. Shuning uchun:
 *   - faqat https manzil ko'rsatiladi (ingest ham http logoni saqlamaydi);
 *   - yuklanmasa, jim ravishda belgiga almashadi;
 *   - `referrerPolicy="no-referrer"` — manzilimizni begona serverga oshkor
 *     qilmaslik uchun.
 */
export default function StationLogo({ src, alt, size = 48, active = false }: StationLogoProps) {
  const [failed, setFailed] = useState(false);

  const usable = Boolean(src && src.startsWith('https://') && !failed);

  return (
    <div
      className="relative flex shrink-0 items-center justify-center overflow-hidden rounded-lg border border-ink-700 bg-ink-850"
      style={{ width: size, height: size }}
    >
      {usable ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src as string}
          alt={alt}
          width={size - 8}
          height={size - 8}
          loading="lazy"
          decoding="async"
          referrerPolicy="no-referrer"
          className="object-contain"
          style={{ width: size - 8, height: size - 8 }}
          onError={() => setFailed(true)}
        />
      ) : (
        <Radio className="text-text-muted" style={{ width: size * 0.4, height: size * 0.4 }} />
      )}

      {active ? (
        <span
          className="pointer-events-none absolute inset-0 rounded-lg ring-2 ring-inset ring-signal"
          aria-hidden="true"
        />
      ) : null}
    </div>
  );
}
