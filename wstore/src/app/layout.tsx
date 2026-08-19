import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { cookies } from "next/headers";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
import ReferralCapture from "@/components/ReferralCapture";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "wstore.uz — Tayyor kod, botlar, saytlar va ilovalar",
  description:
    "Tayyor loyihalar, kod bloklari, Telegram botlar, saytlar va ilovalar kodlarini sotib oling.",
  appleWebApp: {
    capable: true,
    title: "wstore.uz",
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: "#0B0B0F",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  // Tema cookie'dan o'qiladi va boshlang'ich HTML'ning o'ziga yoziladi —
  // shunda <a> havolalarda CSS o'zgaruvchisi keyinchalik "jonli" o'zgarishi
  // shart bo'lmaydi (ba'zi brauzerlarda mavjud <a> elementlarida faqat
  // JS orqali keyin qo'yilgan data-theme'ga bog'liq ranglar to'g'ri
  // qayta hisoblanmasligi kuzatildi).
  const cookieStore = await cookies();
  const theme = cookieStore.get("theme")?.value === "light" ? "light" : "dark";

  return (
    <html lang="uz" className={inter.variable} data-theme={theme}>
      <body className="min-h-screen bg-bg font-sans text-fg antialiased">
        <Suspense fallback={null}>
          <ReferralCapture />
        </Suspense>
        <Providers initialTheme={theme}>{children}</Providers>
      </body>
    </html>
  );
}
