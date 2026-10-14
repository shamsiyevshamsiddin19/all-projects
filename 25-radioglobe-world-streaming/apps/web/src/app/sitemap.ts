import type { MetadataRoute } from 'next';

import { fetchCountries } from '@/lib/api';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

// Sitemap bazadan generatsiya qilinadi — yangi davlat qo'shilsa avtomatik tushadi
export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const countries = await fetchCountries(300, true);
  const now = new Date();

  return [
    { url: SITE_URL, lastModified: now, changeFrequency: 'daily', priority: 1 },
    { url: `${SITE_URL}/favorites`, lastModified: now, changeFrequency: 'monthly', priority: 0.3 },
    { url: `${SITE_URL}/dmca`, lastModified: now, changeFrequency: 'yearly', priority: 0.1 },
    ...countries.map((c) => ({
      url: `${SITE_URL}/radio/${c.slug}`,
      lastModified: now,
      changeFrequency: 'daily' as const,
      // Stansiyasi ko'p davlat muhimroq
      priority: Math.min(0.9, 0.4 + Math.log10(c.radio_count + 1) / 10),
    })),
  ];
}
