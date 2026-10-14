import type { Metadata, Viewport } from 'next';
import './globals.css';

import Header from '@/components/Navigation/Header';
import PersistentPlayer from '@/components/Player/PersistentPlayer';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

export const metadata: Metadata = {
  // metadataBase bo'lmasa OG va canonical nisbiy manzillari noto'g'ri chiqadi
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'RadioGlobe — dunyo radiolarini onlayn tinglash',
    template: '%s | RadioGlobe',
  },
  description:
    'Interaktiv 3D globus orqali 240 dan ortiq davlatning jonli radiostansiyalarini '
    + 'bepul va ro\'yxatdan o\'tmasdan tinglang.',
  keywords: ['radio', 'onlayn radio', 'jonli radio', 'dunyo radiolari', 'internet radio'],
  authors: [{ name: 'Shamsiddin Shamsiyev' }],
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: 'RadioGlobe',
    locale: 'uz_UZ',
    url: SITE_URL,
    title: 'RadioGlobe — dunyo radiolarini onlayn tinglash',
    description: 'Globusdan davlat tanlang va o\'sha yerdagi radioni bir bosishda tinglang.',
  },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: '#05070d',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="uz" className="dark">
      <body className="bg-void-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-crimson selection:text-white">
        <Header />
        <main className="flex-1 pt-14 pb-24">{children}</main>
        <PersistentPlayer />
      </body>
    </html>
  );
}
