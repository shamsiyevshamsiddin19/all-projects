"use client";

import Link from "next/link";
import { Star } from "lucide-react";
import { Product } from "@/lib/types";
import Price from "@/components/Price";
import WishlistButton from "@/components/WishlistButton";
import { useT } from "@/components/Providers";

export default function ProductCard({
  product,
  wishlisted = false,
  loggedIn = false,
}: {
  product: Product;
  wishlisted?: boolean;
  loggedIn?: boolean;
}) {
  const t = useT();
  return (
    // Rangga bog'liq klasslar (bg-surface, border-border) Link'ning o'zida
    // emas, ichki div'da — <a> uchun :visited maxfiylik cheklovi tufayli
    // brauzer CSS o'zgaruvchilarini <a>'da to'g'ri qayta hisoblamasligi mumkin.
    <Link href={`/product/${product.slug}`} className="group block">
      <div className="flex flex-col overflow-hidden rounded-card border border-border bg-surface transition hover:border-border-strong active:border-border-strong">
      {/* Rasm */}
      <div className="relative aspect-[16/10] overflow-hidden bg-surface-2">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={product.coverImage}
          alt={product.title}
          loading="lazy"
          className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
        />
        {product.badge && (
          <span className="absolute left-2 top-2 rounded-md bg-accent px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-white sm:left-3 sm:top-3 sm:px-2 sm:py-1 sm:text-[10px]">
            {product.badge}
          </span>
        )}
        <span className="absolute right-2 top-2 rounded-md border border-border-strong bg-bg/70 px-1.5 py-0.5 text-[10px] text-muted backdrop-blur sm:right-3 sm:top-3 sm:px-2 sm:py-1 sm:text-[11px]">
          {product.categoryLabel}
        </span>
        <div className="absolute bottom-2 right-2">
          <WishlistButton
            productId={product.id}
            initialWishlisted={wishlisted}
            loggedIn={loggedIn}
          />
        </div>
      </div>

      {/* Matn */}
      <div className="flex flex-1 flex-col p-3 sm:p-4">
        <h3 className="mb-1 line-clamp-1 text-sm font-semibold text-fg sm:text-base">
          {product.title}
        </h3>

        {/* Texnologiya teglari — mobilda faqat 2 ta, kichik ekranda yashirin emas */}
        <div className="mb-3 flex flex-wrap gap-1 sm:gap-1.5">
          {product.techStack.slice(0, 3).map((t) => (
            <span
              key={t}
              className="rounded border border-border px-1.5 py-0.5 text-[10px] text-muted sm:text-[11px]"
            >
              {t}
            </span>
          ))}
        </div>

        <div className="mt-auto flex items-center justify-between gap-1">
          <div className="min-w-0">
            <Price
              usd={product.price}
              className="block text-base font-bold text-fg sm:text-lg"
            />
            <div className="truncate text-[10px] text-muted sm:text-[11px]">
              @{product.seller} · {product.salesCount} sotuv
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1 text-sm">
            <Star size={14} className="fill-gold text-gold" />
            <span className="text-fg">{product.rating.toFixed(1)}</span>
          </div>
        </div>

        <span className="mt-3 flex w-full items-center justify-center rounded-lg bg-accent py-2 text-xs font-medium text-white transition group-hover:bg-accent-hover sm:text-sm">
          {t("order")}
        </span>
      </div>
      </div>
    </Link>
  );
}
