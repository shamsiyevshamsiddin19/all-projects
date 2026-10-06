"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  SlidersHorizontal,
  X,
  RotateCcw,
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Flame,
  Sparkles,
} from "lucide-react";
import FilterSidebar, { type SortKey } from "@/components/FilterSidebar";
import ProductCard from "@/components/ProductCard";
import { useT } from "@/components/Providers";
import { PRICE_RANGES } from "@/lib/mock-data";
import {
  Product,
  ProductCategory,
  WebsiteSubcat,
  WEBSITE_SUBCATS,
} from "@/lib/types";

// Kichik yo'nalish -> i18n kaliti
const SUBCAT_TKEY = {
  portfolio: "subPortfolio",
  teacher: "subTeacher",
  edu: "subEdu",
  pharmacy: "subPharmacy",
  restaurant: "subRestaurant",
  other: "subOther",
} as const;

type SubFilter = WebsiteSubcat | "all";

const PAGE_SIZE = 30;

export default function Catalog({
  products,
  wishlistIds = [],
  loggedIn = false,
}: {
  products: Product[];
  wishlistIds?: string[];
  loggedIn?: boolean;
}) {
  const wishlistSet = useMemo(() => new Set(wishlistIds), [wishlistIds]);
  const [cats, setCats] = useState<ProductCategory[]>([]);
  const [prices, setPrices] = useState<number[]>([]);
  const [tech, setTech] = useState<string[]>([]);
  const [sub, setSub] = useState<SubFilter>("all");
  const [sort, setSort] = useState<SortKey>("popular");
  const [search, setSearch] = useState("");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const observerTarget = useRef<HTMLDivElement>(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [sheetIn, setSheetIn] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const t = useT();
  const router = useRouter();

  const toggle = <T,>(arr: T[], v: T) =>
    arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];

  function openFilter() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setFilterOpen(true);
    // rAF ba'zi holatlarda (fon tab va h.k.) kechikadi — setTimeout ishonchliroq.
    setTimeout(() => setSheetIn(true), 20);
  }
  function closeFilter() {
    setSheetIn(false);
    closeTimer.current = setTimeout(() => setFilterOpen(false), 220);
  }

  function clearAll() {
    setCats([]);
    setPrices([]);
    setTech([]);
    setSub("all");
  }

  // "Saytlar" tanlanганда kichik yo'nalish chiplarini ko'rsatamiz.
  const showSubChips = cats.includes("website");
  const activeCount = cats.length + prices.length + tech.length;

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let list = products.filter((p) => {
      if (cats.length && !cats.includes(p.category)) return false;
      // sayt kichik yo'nalishi bo'yicha filtr (faqat website mahsulotlarga)
      if (
        showSubChips &&
        sub !== "all" &&
        p.category === "website" &&
        p.subcategory !== sub
      )
        return false;
      if (tech.length && !tech.some((tt) => p.techStack.includes(tt)))
        return false;
      if (prices.length) {
        const ok = prices.some((i) => {
          const r = PRICE_RANGES[i];
          return p.price >= r.min && p.price < r.max;
        });
        if (!ok) return false;
      }
      if (q) {
        const hay = `${p.title} ${p.description ?? ""} ${p.techStack.join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    list = [...list].sort((a: Product, b: Product) => {
      switch (sort) {
        case "price-asc":
          return a.price - b.price;
        case "price-desc":
          return b.price - a.price;
        case "rating":
          return b.rating - a.rating;
        default:
          return b.salesCount - a.salesCount;
      }
    });
    return list;
  }, [products, cats, prices, tech, sort, sub, showSubChips, search]);

  // Filtr/qidiruv o'zgarsa sahifalashni boshiga qaytaramiz.
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [cats, prices, tech, sort, sub, search]);

  const hasMore = filtered.length > visibleCount;

  useEffect(() => {
    if (!hasMore) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((v) => v + PAGE_SIZE);
        }
      },
      { rootMargin: "200px" } // trigger loading before it's completely visible
    );
    if (observerTarget.current) observer.observe(observerTarget.current);
    return () => observer.disconnect();
  }, [hasMore]);

  const visible = filtered.slice(0, visibleCount);

  // Filtrsiz — "Ommabop" va "Yangi" qatorlar hamisha butun katalogdan.
  const showHighlights = !search && cats.length === 0 && prices.length === 0 && tech.length === 0;
  // Ko'proq element — keng ekranlarda ham qator to'lib, suriladigan (scrollable) bo'lib qolsin.
  const topSelling = [...products].sort((a, b) => b.salesCount - a.salesCount).slice(0, 20);
  const newArrivals = [...products]
    .filter((p) => p.createdAt)
    .sort((a, b) => new Date(b.createdAt ?? 0).getTime() - new Date(a.createdAt ?? 0).getTime())
    .slice(0, 20);

  const sidebar = (
    <FilterSidebar
      sort={sort}
      onSort={setSort}
      selectedCats={cats}
      selectedPrices={prices}
      selectedTech={tech}
      onToggleCat={(c) => {
        setCats((s) => toggle(s, c));
        if (c === "website") setSub("all"); // website o'chsa/yoqilса — yo'nalishни tiklaymiz
      }}
      onTogglePrice={(i) => setPrices((s) => toggle(s, i))}
      onToggleTech={(tt) => setTech((s) => toggle(s, tt))}
      onClear={clearAll}
    />
  );

  // Gorizontal kichik yo'nalish chiplari (Hammasi + 6 yo'nalish)
  const subChips = showSubChips && (
    <div className="mb-4 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <Chip active={sub === "all"} onClick={() => setSub("all")}>
        {t("subAll")}
      </Chip>
      {WEBSITE_SUBCATS.map((s) => (
        <Chip key={s} active={sub === s} onClick={() => setSub(s)}>
          {t(SUBCAT_TKEY[s])}
        </Chip>
      ))}
    </div>
  );

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-4 sm:px-6 sm:py-6">
      {/* Mobil boshqaruv paneli (sticky): filtr + qidiruv yonma-yon */}
      <div className="sticky top-16 z-20 -mx-4 mb-4 flex items-center gap-2 border-b border-border bg-bg/90 px-4 py-2.5 backdrop-blur md:hidden">
        <button
          onClick={openFilter}
          className="flex shrink-0 items-center gap-2 rounded-lg border border-border-strong bg-surface px-3 py-2 text-sm font-medium text-fg"
        >
          <SlidersHorizontal size={16} />
          {t("filter")}
          {activeCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-xs">
              {activeCount}
            </span>
          )}
        </button>
        <div className="relative flex-1">
          <Search
            size={15}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("searchPlaceholder")}
            className="w-full rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-fg outline-none placeholder:text-muted/70 focus:border-accent"
          />
          {search.length > 0 && (
            <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-60 overflow-y-auto rounded-lg border border-border bg-surface p-1 shadow-xl">
              {filtered.length > 0 ? (
                filtered.slice(0, 5).map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      setSearch("");
                      router.push(`/product/${p.slug}`);
                    }}
                    className="flex w-full items-center gap-3 rounded-md p-2 text-left hover:bg-surface-2 transition"
                  >
                    <div className="h-10 w-10 shrink-0 overflow-hidden rounded bg-surface-2">
                      <Image src={p.coverImage} alt={p.title} width={40} height={40} className="h-full w-full object-cover" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-fg">{p.title}</div>
                      <div className="truncate text-xs text-muted">{p.techStack.join(", ")}</div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="p-3 text-center text-sm text-muted">{t("notFound")}</div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-8 md:flex-row md:items-start">
        {/* Desktop sidebar — filtr eng yuqorida, fixed (qimirlamaydi) va alohida yashirin scroll */}
        <div className="hidden md:block w-64 shrink-0">
          <div className="fixed top-20 w-64 max-h-[calc(100vh-5rem)] overflow-y-auto pb-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {sidebar}
          </div>
        </div>

        <div className="min-w-0 flex-1">
          {/* Desktop: qidiruv + topilgan soni — filtr bilan bir qatorda, eng yuqorida */}
          <div className="mb-6 hidden items-center gap-3 md:flex">
            <div className="relative flex-1">
              <Search
                size={16}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("searchPlaceholder")}
                className="w-full rounded-xl border border-border bg-surface py-2.5 pl-10 pr-4 text-sm text-fg outline-none placeholder:text-muted/70 focus:border-accent"
              />
              {search.length > 0 && (
                <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-60 overflow-y-auto rounded-xl border border-border bg-surface p-1.5 shadow-xl">
                  {filtered.length > 0 ? (
                    filtered.slice(0, 5).map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setSearch("");
                          router.push(`/product/${p.slug}`);
                        }}
                        className="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-surface-2 transition"
                      >
                        <div className="h-10 w-10 shrink-0 overflow-hidden rounded bg-surface-2">
                          <Image src={p.coverImage} alt={p.title} width={40} height={40} className="h-full w-full object-cover" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium text-fg">{p.title}</div>
                          <div className="truncate text-xs text-muted">{p.techStack.join(", ")}</div>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="p-3 text-center text-sm text-muted">{t("notFound")}</div>
                  )}
                </div>
              )}
            </div>
            <span className="shrink-0 text-xs text-muted">
              {filtered.length} {t("available")}
            </span>
          </div>

          {/* Ommabop / Yangi — mahsulotlar bilan bir ustunda, faqat filtrsiz holatda */}
          {showHighlights && (topSelling.length > 0 || newArrivals.length > 0) && (
            <div className="mb-6 flex flex-col gap-6">
              {topSelling.length > 0 && (
                <HighlightRow
                  icon={<Flame size={16} className="text-gold" />}
                  title={t("topSelling")}
                  products={topSelling}
                  wishlistSet={wishlistSet}
                  loggedIn={loggedIn}
                />
              )}
              {newArrivals.length > 0 && (
                <HighlightRow
                  icon={<Sparkles size={16} className="text-accent" />}
                  title={t("newArrivals")}
                  products={newArrivals}
                  wishlistSet={wishlistSet}
                  loggedIn={loggedIn}
                />
              )}
            </div>
          )}

          {/* Sayt kichik yo'nalishlari — gorizontal */}
          {subChips}

          {filtered.length === 0 ? (
            <div className="rounded-card border border-dashed border-border p-12 text-center text-muted">
              {t("notFound")}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3">
                {visible.map((p) => (
                  <ProductCard
                    key={p.id}
                    product={p}
                    wishlisted={wishlistSet.has(p.id)}
                    loggedIn={loggedIn}
                  />
                ))}
              </div>
              {hasMore && (
                <div ref={observerTarget} className="mt-6 flex h-10 items-center justify-center">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" />
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Mobil filter — pastdan chiqadigan bottom sheet */}
      {filterOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* fon */}
          <div
            className={`absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
              sheetIn ? "opacity-100" : "opacity-0"
            }`}
            onClick={closeFilter}
          />
          {/* panel */}
          <div
            className={`absolute inset-x-0 bottom-0 flex max-h-[85vh] flex-col rounded-t-2xl border-t border-border bg-bg shadow-2xl transition-transform duration-300 ease-out ${
              sheetIn ? "translate-y-0" : "translate-y-full"
            }`}
          >
            <div className="flex justify-center pb-1 pt-2.5">
              <span className="h-1 w-10 rounded-full bg-border-strong" />
            </div>
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <SlidersHorizontal size={16} className="text-accent" />
                <span className="font-semibold text-fg">{t("filter")}</span>
                {activeCount > 0 && (
                  <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-xs text-white">
                    {activeCount}
                  </span>
                )}
              </div>
              <button
                onClick={closeFilter}
                className="rounded-lg p-1.5 text-muted hover:text-fg"
                aria-label={t("close")}
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-4 py-4">{sidebar}</div>
            <div
              className="flex items-center gap-2 border-t border-border bg-bg p-4"
              style={{
                paddingBottom: "calc(1rem + env(safe-area-inset-bottom))",
              }}
            >
              <button
                onClick={clearAll}
                className="flex items-center gap-1.5 rounded-lg border border-border-strong px-3.5 py-2.5 text-sm font-medium text-muted transition hover:border-accent hover:text-fg"
              >
                <RotateCcw size={14} />
                {t("clear")}
              </button>
              <button
                onClick={closeFilter}
                className="flex-1 rounded-lg bg-accent py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
              >
                {t("show")} ({filtered.length})
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function HighlightRow({
  icon,
  title,
  products,
  wishlistSet,
  loggedIn,
}: {
  icon: React.ReactNode;
  title: string;
  products: Product[];
  wishlistSet: Set<string>;
  loggedIn: boolean;
}) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  function slide(dir: 1 | -1) {
    const el = scrollerRef.current;
    if (!el) return;
    // "behavior: smooth" ba'zi brauzerlarda "ishonchli" (real) klik bo'lmasa
    // jim e'tiborsiz qoldiriladi — shuning uchun CSS scroll-smooth klassiga
    // tayanamiz (el.className) va bu yerda behavior ko'rsatmaymiz.
    el.scrollLeft += dir * (el.clientWidth * 0.8);
  }

  return (
    <section>
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-fg">
        {icon}
        {title}
      </h2>

      {/* Kompyuterda sichqoncha bilan "surish" uchun strelka tugmalari — qatorga tegishli */}
      <div className="group/row relative">
        <button
          type="button"
          onClick={() => slide(-1)}
          aria-label="Chapga surish"
          className="absolute left-0 top-1/2 z-10 hidden h-9 w-9 -translate-x-1/3 -translate-y-1/2 items-center justify-center rounded-full border border-border-strong bg-surface text-fg opacity-0 shadow-lg transition hover:border-accent group-hover/row:opacity-100 md:flex"
        >
          <ChevronLeft size={18} />
        </button>
        <button
          type="button"
          onClick={() => slide(1)}
          aria-label="O'ngga surish"
          className="absolute right-0 top-1/2 z-10 hidden h-9 w-9 -translate-y-1/2 translate-x-1/3 items-center justify-center rounded-full border border-border-strong bg-surface text-fg opacity-0 shadow-lg transition hover:border-accent group-hover/row:opacity-100 md:flex"
        >
          <ChevronRight size={18} />
        </button>

        <div
          ref={scrollerRef}
          className="flex gap-3 overflow-x-auto pb-2 sm:gap-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          {products.map((p) => (
            <div key={p.id} className="w-[168px] shrink-0 sm:w-[220px]">
              <ProductCard product={p} wishlisted={wishlistSet.has(p.id)} loggedIn={loggedIn} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 whitespace-nowrap rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
        active
          ? "border-accent bg-accent text-white"
          : "border-border bg-surface text-muted hover:border-border-strong hover:text-fg"
      }`}
    >
      {children}
    </button>
  );
}
