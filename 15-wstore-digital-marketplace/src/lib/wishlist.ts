import { prisma } from "@/lib/prisma";

/** Foydalanuvchining sevimli mahsulot id'lari (bo'sh sessiya bo'lsa — bo'sh to'plam). */
export async function getWishlistIds(userId?: string | null): Promise<string[]> {
  if (!userId) return [];
  try {
    const rows = await prisma.wishlist.findMany({
      where: { userId },
      select: { productId: true },
    });
    return rows.map((r) => r.productId);
  } catch {
    return [];
  }
}
