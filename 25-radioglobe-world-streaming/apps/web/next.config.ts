import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
      {
        protocol: "http",
        hostname: "**",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.LOCAL_API_PROXY_TARGET || "http://127.0.0.1:8000"}/api/v1/:path*`,
        // Eslatma: productionda bu qoida HECH QACHON ishga tushmaydi — nginx
        // /api/ so'rovlarini to'g'ridan-to'g'ri FastAPI'ga (8001-port) yuboradi,
        // Next.js'ga umuman yetib bormaydi. Bu faqat `npm run dev`/`next start`
        // bilan lokal (nginx'siz) sinovda ishlatiladi.
      },
    ];
  },
};

export default nextConfig;
