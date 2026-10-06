"use client";

import { Check } from "lucide-react";
import { Product, ReviewItem } from "@/lib/types";
import { useT } from "@/components/Providers";
import ReviewForm from "@/components/ReviewForm";
import ReviewList from "@/components/ReviewList";
import ProductCard from "@/components/ProductCard";

// Mahsulot sahifasining pastki qismi: tavsif -> xususiyatlar -> izohlar -> tavsiya.
export default function ProductBody({
  product,
  reviews,
  recommended,
  loggedIn,
  wishlistIds = [],
}: {
  product: Product;
  reviews: ReviewItem[];
  recommended: Product[];
  loggedIn: boolean;
  wishlistIds?: string[];
}) {
  const wishlistSet = new Set(wishlistIds);
  const t = useT();

  return (
    <div className="mt-10 flex flex-col divide-y divide-border">
      {/* Mahsulot haqida */}
      {product.description && (
        <section className="pb-8">
          <h2 className="mb-3 text-lg font-semibold text-fg">
            {t("about")}
          </h2>
          <p className="whitespace-pre-line text-sm leading-7 text-muted">
            {product.description}
          </p>
        </section>
      )}

      {/* Xususiyatlar */}
      {product.features && product.features.length > 0 && (
        <section className="py-8 first:pt-0">
          <h2 className="mb-3 text-lg font-semibold text-fg">
            {t("features")}
          </h2>
          <ul className="grid gap-2 sm:grid-cols-2">
            {product.features.map((f, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent">
                  <Check size={13} />
                </span>
                <span className="text-sm leading-6 text-fg/90">{f}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Izohlar */}
      <section className="py-8 first:pt-0">
        <h2 className="mb-4 text-lg font-semibold text-fg">
          {t("reviews")}
          {reviews.length > 0 && (
            <span className="ml-2 text-sm font-normal text-muted">
              ({reviews.length})
            </span>
          )}
        </h2>

        <div className="mb-5">
          <ReviewForm productId={product.id} loggedIn={loggedIn} />
        </div>

        {reviews.length === 0 ? (
          <p className="rounded-card border border-dashed border-border p-6 text-center text-sm text-muted">
            {t("noReviews")}
          </p>
        ) : (
          <ReviewList reviews={reviews} />
        )}
      </section>

      {/* Tavsiya etamiz — eng yuqori reytingli mahsulotlar */}
      {recommended.length > 0 && (
        <section className="pt-8">
          <h2 className="mb-4 text-lg font-semibold text-fg">
            {t("recommended")}
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
            {recommended.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                wishlisted={wishlistSet.has(p.id)}
                loggedIn={loggedIn}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
