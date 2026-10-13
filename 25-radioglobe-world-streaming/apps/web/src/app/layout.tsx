import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/Navigation/Header';
import PersistentPlayer from '@/components/Player/PersistentPlayer';

export const metadata: Metadata = {
  title: 'RadioGlobe — World Radio & TV Streaming',
  description:
    'Interaktiv 3D globus orqali butun dunyo radiostansiyalarini kashf qilish va bir zumda tinglash platformasi.',
  keywords: ['radio', 'world radio', '3D globe', 'internet radio', 'stream', 'live radio', 'MapLibre'],
  authors: [{ name: 'Shamsiddin Shamsiyev' }],
  openGraph: {
    title: 'RadioGlobe — World Radio & TV Streaming',
    description: 'Interaktiv 3D globus orqali butun dunyo radiostansiyalarini tinglang.',
    url: 'https://radio.shamsiyev.uz',
    siteName: 'RadioGlobe',
    locale: 'uz_UZ',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className="dark">
      <body className="bg-void-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-crimson selection:text-white">
        <Header />
        <main className="flex-1 pt-14 pb-20">{children}</main>
        <PersistentPlayer />
      </body>
    </html>
  );
}
