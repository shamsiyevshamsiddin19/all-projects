export type ProductCategory =
  | "portfolio"
  | "bot"
  | "website"
  | "app"
  | "code"
  | "uikit";

// "Saytlar" (website) tanlanganda ko'rsatiladigan kichik yo'nalishlar.
export type WebsiteSubcat =
  | "portfolio"
  | "teacher"
  | "edu"
  | "pharmacy"
  | "restaurant"
  | "other";

// Chiplar tartibi (yorliqlar i18n orqali — Providers DICT'da).
export const WEBSITE_SUBCATS: WebsiteSubcat[] = [
  "portfolio",
  "teacher",
  "edu",
  "pharmacy",
  "restaurant",
  "other",
];

export interface Product {
  id: string;
  title: string;
  slug: string;
  price: number;
  category: ProductCategory;
  categoryLabel: string;
  subcategory?: WebsiteSubcat | null; // faqat website uchun
  badge?: string; // "TOP SOTUV", "YANGI" ...
  techStack: string[];
  features?: string[]; // mahsulot xususiyatlari (mahsulot sahifasida)
  coverImage: string;
  screenshots?: string[];
  rating: number;
  salesCount: number;
  reviewCount?: number;
  description?: string;
  seller: string;
  sellerImage?: string | null; // sotuvchi avatar (chat/"sotuvchidan so'rash" uchun)
  telegram?: string; // loyiha egasining Telegram username'i (bo'sh bo'lsa — admin)
  createdAt?: string; // "Yangi qo'shilganlar" bo'limi uchun
}

export interface ReviewItem {
  id: string;
  rating: number;
  comment: string;
  userName: string | null;
  userImage: string | null;
  createdAt: string;
}
