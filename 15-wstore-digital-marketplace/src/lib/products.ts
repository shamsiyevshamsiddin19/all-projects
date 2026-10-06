import { prisma } from "@/lib/prisma";
import { PRODUCTS as MOCK } from "@/lib/mock-data";
import { Product, ProductCategory, ReviewItem } from "@/lib/types";
import type { Prisma } from "@prisma/client";

type Row = Prisma.ProductGetPayload<{
  include: { category: true; seller: true };
}>;

function mapRow(r: Row): Product {
  return {
    id: r.id,
    title: r.title,
    slug: r.slug,
    price: Number(r.price),
    category: r.category.slug as ProductCategory,
    categoryLabel: r.category.name,
    subcategory: (r.subcategory as Product["subcategory"]) ?? null,
    techStack: r.techStack,
    features: r.features,
    description: r.description,
    coverImage: r.coverImage,
    screenshots: r.screenshots,
    rating: r.rating,
    salesCount: r.salesCount,
    seller: r.seller.name ?? "foydalanuvchi",
    sellerImage: r.seller.image,
    telegram: r.telegramUsername ?? undefined,
    createdAt: r.createdAt.toISOString(),
  };
}

// Katalog ma'lumotini bazadan oladi. Baza ulanmagan yoki bo'sh bo'lsa —
// namunaviy (mock) ro'yxatga qaytadi, shunda UI hamisha ko'rinadi.
export async function getProducts(): Promise<Product[]> {
  try {
    const rows = await prisma.product.findMany({
      where: { status: "ACTIVE" },
      include: { category: true, seller: true },
      orderBy: { salesCount: "desc" },
    });
    return rows.map(mapRow);
  } catch {
    return [];
  }
}

export async function getProductBySlug(slug: string): Promise<Product | null> {
  try {
    const r = await prisma.product.findUnique({
      where: { slug },
      include: { category: true, seller: true },
    });
    if (!r) return null;
    const mapped = mapRow(r);
    const count = await prisma.review.count({ where: { productId: r.id } });
    mapped.reviewCount = count;
    return mapped;
  } catch {
    return null;
  }
}

export async function getProductReviews(productId: string): Promise<ReviewItem[]> {
  try {
    const reviews = await prisma.review.findMany({
      where: { productId },
      orderBy: { createdAt: "desc" },
      include: { user: { select: { name: true, image: true } } },
    });
    return reviews.map((r) => ({
      id: r.id,
      rating: r.rating,
      comment: r.comment,
      userName: r.user.name,
      userImage: r.user.image,
      createdAt: r.createdAt.toISOString(),
    }));
  } catch {
    return [];
  }
}

// Foydalanuvchi sevimlilar ro'yxatidagi mahsulotlar (to'liq ma'lumot bilan).
export async function getWishlistProducts(userId?: string | null): Promise<Product[]> {
  if (!userId) return [];
  try {
    const rows = await prisma.wishlist.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      include: { product: { include: { category: true, seller: true } } },
    });
    return rows.map((r) => mapRow(r.product));
  } catch {
    return [];
  }
}

// Tavsiya — eng yuqori reytingli faol mahsulotlar (joriydan tashqari).
export async function getTopProducts(
  excludeId: string,
  limit = 4,
): Promise<Product[]> {
  try {
    const rows = await prisma.product.findMany({
      where: { status: "ACTIVE", id: { not: excludeId } },
      include: { category: true, seller: true },
      orderBy: [{ rating: "desc" }, { salesCount: "desc" }],
      take: limit,
    });
    return rows.map(mapRow);
  } catch {
    return [];
  }
}
