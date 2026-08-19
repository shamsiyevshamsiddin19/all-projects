import type { MetadataRoute } from "next";

const APP_URL = process.env.APP_URL || "https://wstore.uz";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/admin", "/dashboard", "/seller", "/order/"],
      },
    ],
    sitemap: `${APP_URL}/sitemap.xml`,
  };
}
