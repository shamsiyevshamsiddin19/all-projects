import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "wstore.uz — Tayyor kod, botlar, saytlar va ilovalar",
    short_name: "wstore.uz",
    description:
      "Tayyor loyihalar, kod bloklari, Telegram botlar, saytlar va ilovalar kodlarini sotib oling.",
    start_url: "/",
    display: "standalone",
    background_color: "#0B0B0F",
    theme_color: "#0B0B0F",
    icons: [
      { src: "/icon.png", sizes: "180x180", type: "image/png" },
      { src: "/logo-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
