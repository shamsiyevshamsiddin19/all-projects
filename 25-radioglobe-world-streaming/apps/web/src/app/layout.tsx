import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono, Space_Grotesk } from 'next/font/google';

import './globals.css';

import Header from '@/components/Navigation/Header';
import PersistentPlayer from '@/components/Player/PersistentPlayer';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://radio.shamsiyev.uz';

// Sarlavhalar uchun — texnik xarakterli, lekin o'qishga qulay grotesk
const display = Space_Grotesk({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-display',
  display: 'swap',
});

// Asosiy matn
const sans = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

// Faqat raqamlar, kodlar va o'lchovlar uchun
const mono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'RadioGlobe — dunyo radiolarini onlayn tinglash',
    template: '%s · RadioGlobe',
  },
  description:
    'Globusdan davlat tanlang va o\'sha yerdagi jonli radiostansiyani bir bosishda '
    + 'tinglang. 240 dan ortiq davlat, bepul, ro\'yxatdan o\'tmasdan.',
  keywords: ['radio', 'onlayn radio', 'jonli radio', 'dunyo radiolari', 'internet radio'],
  authors: [{ name: 'Shamsiddin Shamsiyev' }],
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    siteName: 'RadioGlobe',
    locale: 'uz_UZ',
    url: SITE_URL,
    title: 'RadioGlobe — dunyo radiolarini onlayn tinglash',
    description: 'Globusdan davlat tanlang va radioni bir bosishda tinglang.',
  },
  robots: { index: true, follow: true },
  // Favicon/ilova ikonkasi — bir nechta o'lcham, har xil qurilma va kontekst
  // uchun (brauzer tabi, Android/iOS bosh ekrani, PWA).
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon-16.png', sizes: '16x16', type: 'image/png' },
      { url: '/icon-32.png', sizes: '32x32', type: 'image/png' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [{ url: '/apple-icon-180.png', sizes: '180x180', type: 'image/png' }],
  },
  manifest: '/manifest.webmanifest',
};

export const viewport: Viewport = {
  themeColor: '#06070d',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="uz"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="min-h-screen flex flex-col">
        {/* Klaviatura foydalanuvchisi navigatsiyani o'tkazib yuborishi uchun */}
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50
                     focus:rounded-lg focus:bg-signal focus:px-4 focus:py-2 focus:text-sm focus:text-white"
        >
          Asosiy qismga o'tish
        </a>

        <Header />
        {/* pb-28 — pastdagi doimiy pleyer kontentni to'smasligi uchun */}
        <main id="main" className="flex-1 pt-14 pb-28">
          {children}
        </main>
        <PersistentPlayer />
      </body>
    </html>
  );
}
