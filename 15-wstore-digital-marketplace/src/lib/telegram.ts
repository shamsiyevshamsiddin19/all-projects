import { Product } from "@/lib/types";

// Admin Telegram username (buyurtma va "loyiha qo'shish" uchun standart).
export const ADMIN_TELEGRAM =
  (process.env.NEXT_PUBLIC_ADMIN_TELEGRAM || "shamsiyev_shamsiddin").replace(
    /^@/,
    "",
  );

function clean(u?: string): string {
  return (u || "").replace(/^@/, "").trim();
}

// Mahsulot uchun Telegram buyurtma havolasi (xabar loyiha ma'lumoti bilan to'ldiriladi).
export function orderTelegramLink(product: Product): string {
  const user = clean(product.telegram) || ADMIN_TELEGRAM;
  const msg =
    `Salom! wstore.uz dan "${product.title}" loyihasini ko'rdim ($${product.price}).\n` +
    `Havola: https://wstore.uz/product/${product.slug}\n` +
    `Buyurtma bermoqchiman.`;
  return `https://t.me/${user}?text=${encodeURIComponent(msg)}`;
}

// "Loyihangizni qo'shmoqchimisiz?" — adminga murojaat havolasi.
export function submitProjectLink(): string {
  const msg =
    "Salom! Men wstore.uz platformasiga o'z loyihamni qo'ymoqchiman.";
  return `https://t.me/${ADMIN_TELEGRAM}?text=${encodeURIComponent(msg)}`;
}
