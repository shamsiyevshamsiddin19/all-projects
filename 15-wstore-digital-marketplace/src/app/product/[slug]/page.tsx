import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowLeft, ShieldCheck, MessageCircle, Flame } from "lucide-react";
import Navbar from "@/components/Navbar";
import Price from "@/components/Price";
import StarRating from "@/components/StarRating";
import BuyOnlineButton from "@/components/BuyOnlineButton";
import WishlistButton from "@/components/WishlistButton";
import ReportButton from "@/components/ReportButton";
import ProductGallery from "@/components/ProductGallery";
import ProductBody from "@/components/ProductBody";
import {
  getProductBySlug,
  getProductReviews,
  getTopProducts,
} from "@/lib/products";
import { orderTelegramLink } from "@/lib/telegram";
import { auth } from "@/lib/auth";
import { getWishlistIds } from "@/lib/wishlist";

const APP_URL = process.env.APP_URL || "https://wstore.uz";

function initials(name: string): string {
  return name.trim().charAt(0).toUpperCase() || "?";
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) return {};

  const title = `${product.title} — wstore.uz`;
  const description =
    product.description?.slice(0, 160) ||
    `${product.title} — $${product.price}. wstore.uz'da tayyor kod, botlar, saytlar va ilovalar.`;
  const url = `${APP_URL}/product/${product.slug}`;

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      siteName: "wstore.uz",
      images: product.coverImage ? [{ url: product.coverImage }] : undefined,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: product.coverImage ? [product.coverImage] : undefined,
    },
  };
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await getProductBySlug(slug);
  if (!product) notFound();

  const session = await auth().catch(() => null);
  const [reviews, recommended, wishlistIds] = await Promise.all([
    getProductReviews(product.id),
    getTopProducts(product.id, 4),
    getWishlistIds(session?.user?.id),
  ]);

  const reviewCount = product.reviewCount ?? reviews.length;
  const loggedIn = Boolean(session?.user);

  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-[1100px] px-6 pb-28 pt-8 sm:pb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-accent"
        >
          <ArrowLeft size={15} /> Katalogga qaytish
        </Link>

        <div className="mt-6 grid gap-8 md:grid-cols-2 md:items-start">
          <ProductGallery
            coverImage={product.coverImage}
            screenshots={product.screenshots ?? []}
            title={product.title}
          />

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent">
                {product.categoryLabel}
              </span>
              <div className="flex items-center gap-2">
                {product.salesCount > 50 && (
                  <span className="flex items-center gap-1 rounded-full bg-gold/10 px-2.5 py-1 text-[11px] font-medium text-gold">
                    <Flame size={12} /> Ommabop
                  </span>
                )}
                <ReportButton productId={product.id} loggedIn={loggedIn} />
              </div>
            </div>

            {/* Nom */}
            <h1 className="mt-2 text-[1.7rem] font-bold leading-tight text-fg sm:text-3xl">
              {product.title}
            </h1>

            {/* Yulduzchalar orqali baholash */}
            <div className="mt-2.5 flex flex-wrap items-center gap-2 text-sm text-muted">
              <StarRating value={product.rating} />
              <span className="font-medium text-fg">
                {product.rating.toFixed(1)}
              </span>
              <span className="text-border-strong">·</span>
              <span>{reviewCount} izoh</span>
              <span className="text-border-strong">·</span>
              <span>{product.salesCount} sotuv</span>
            </div>

            {/* Sotuvchi */}
            <div className="mt-4 flex items-center gap-2 border-y border-border py-3">
              {product.sellerImage ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={product.sellerImage}
                  alt={product.seller}
                  className="h-8 w-8 rounded-full object-cover"
                />
              ) : (
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-2 text-xs font-semibold text-muted">
                  {initials(product.seller)}
                </span>
              )}
              <div className="leading-tight">
                <div className="text-sm font-medium text-fg/90">
                  {product.seller}
                </div>
                <div className="text-xs text-muted">Sotuvchi</div>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {product.techStack.map((tech) => (
                <span
                  key={tech}
                  className="rounded-full border border-border bg-surface-2 px-2.5 py-1 text-xs text-muted"
                >
                  {tech}
                </span>
              ))}
            </div>

            {/* Narx — barcha o'lchamlarda ko'rinadi */}
            <div className="mt-6 flex items-end justify-between">
              <div>
                <p className="text-xs text-muted">Narxi</p>
                <Price
                  usd={product.price}
                  className="text-[2.25rem] font-bold leading-none text-fg"
                />
              </div>
              <div className="flex items-center gap-3">
                <div className="hidden items-center gap-1.5 text-xs text-muted sm:flex">
                  <ShieldCheck size={14} className="text-accent" />
                  Xavfsiz to&apos;lov
                </div>
                <WishlistButton
                  productId={product.id}
                  initialWishlisted={wishlistIds.includes(product.id)}
                  loggedIn={loggedIn}
                  size="lg"
                />
              </div>
            </div>

            {/* Tugmalar — faqat sm+ (mobilda pastdagi qotib turuvchi panel ishlatiladi) */}
            <div className="mt-4 hidden flex-col gap-4 sm:flex">
              <BuyOnlineButton
                productId={product.id}
                loggedIn={loggedIn}
              />

              <a
                href={orderTelegramLink(product)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium text-muted transition hover:text-fg"
              >
                <MessageCircle size={15} />
                Sotuvchi bilan bog&apos;lanish
              </a>

              <p className="-mt-1 text-center text-xs text-muted">
                Fayl to&apos;lovdan so&apos;ng avtomatik yuklab olinadi
              </p>
            </div>
          </div>
        </div>

        {/* Tavsif -> Xususiyatlar -> Izohlar -> Tavsiya */}
        <ProductBody
          product={product}
          reviews={reviews}
          recommended={recommended}
          loggedIn={loggedIn}
          wishlistIds={wishlistIds}
        />
      </main>

      {/* Mobil: to'lov + bog'lanish tugmalari ekran pastida qotib turadi */}
      <div
        className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-bg/95 px-4 pt-3 shadow-[0_-8px_24px_rgba(0,0,0,0.35)] backdrop-blur sm:hidden"
        style={{ paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom))" }}
      >
        <div className="flex items-center gap-2.5">
          <a
            href={orderTelegramLink(product)}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Sotuvchi bilan bog'lanish"
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-border-strong bg-surface text-fg transition hover:border-accent"
          >
            <MessageCircle size={19} />
          </a>
          <div className="flex-1">
            <BuyOnlineButton
              productId={product.id}
              loggedIn={loggedIn}
              compact
            />
          </div>
        </div>
      </div>
    </>
  );
}
