"use client";

import { RotateCcw } from "lucide-react";
import { CATEGORIES, PRICE_RANGES, TECH_OPTIONS } from "@/lib/mock-data";
import { ProductCategory } from "@/lib/types";
import { categoryIcon } from "@/lib/icons";
import {
  useApp,
  useT,
  formatPrice,
  CURRENCIES,
  CURRENCY_META,
  type Currency,
} from "@/components/Providers";

export type SortKey = "popular" | "price-asc" | "price-desc" | "rating";

interface Props {
  sort: SortKey;
  onSort: (s: SortKey) => void;
  selectedCats: ProductCategory[];
  selectedPrices: number[]; // PRICE_RANGES indekslari
  selectedTech: string[];
  onToggleCat: (c: ProductCategory) => void;
  onTogglePrice: (i: number) => void;
  onToggleTech: (t: string) => void;
  onClear: () => void;
}

export default function FilterSidebar({
  sort,
  onSort,
  selectedCats,
  selectedPrices,
  selectedTech,
  onToggleCat,
  onTogglePrice,
  onToggleTech,
  onClear,
}: Props) {
  const t = useT();
  const { currency, setCurrency } = useApp();

  const activeCount =
    selectedCats.length + selectedPrices.length + selectedTech.length;

  const SORTS: { v: SortKey; label: string }[] = [
    { v: "popular", label: t("sortPopular") },
    { v: "price-asc", label: t("sortCheap") },
    { v: "price-desc", label: t("sortExpensive") },
    { v: "rating", label: t("sortRating") },
  ];

  return (
    <aside className="w-full shrink-0 md:w-64 md:sticky md:top-20 md:self-start">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-fg">
            {t("filter")}
          </h2>
          {activeCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-xs font-medium text-white">
              {activeCount}
            </span>
          )}
        </div>
        <button
          onClick={onClear}
          className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted transition hover:bg-surface-2 hover:text-fg"
        >
          <RotateCcw size={12} />
          {t("clear")}
        </button>
      </div>

      {/* Barcha filtr bo'limlari — bitta kartada */}
      <div className="rounded-2xl border border-border bg-surface shadow-lg shadow-black/10">
        <div className="p-4">
          {/* Valyuta — eng birinchi bo'lim */}
          <Section title={t("currency")} first>
            <div className="grid grid-cols-4 gap-1.5">
              {CURRENCIES.map((c: Currency) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCurrency(c)}
                  className={`rounded-lg border py-1.5 text-xs font-medium transition ${
                    currency === c
                      ? "border-accent bg-accent text-white shadow-sm shadow-accent/30"
                      : "border-border-strong bg-surface-2 text-muted hover:border-border-strong hover:text-fg"
                  }`}
                >
                  {CURRENCY_META[c].code}
                </button>
              ))}
            </div>
          </Section>

          <Section title={t("sort")}>
            {SORTS.map((s) => (
              <Radio
                key={s.v}
                label={s.label}
                checked={sort === s.v}
                onChange={() => onSort(s.v)}
              />
            ))}
          </Section>

          <Section title={t("priceRange")}>
            {PRICE_RANGES.map((r, i) => {
              const label =
                r.max === Infinity
                  ? `${formatPrice(r.min, currency)} +`
                  : `${formatPrice(r.min, currency)} – ${formatPrice(r.max, currency)}`;
              return (
                <Check
                  key={r.label}
                  label={label}
                  checked={selectedPrices.includes(i)}
                  onChange={() => onTogglePrice(i)}
                />
              );
            })}
          </Section>

          <Section title={t("category")}>
            {CATEGORIES.map((c) => {
              const Icon = categoryIcon(c.key);
              return (
                <Check
                  key={c.key}
                  label={c.label}
                  icon={<Icon size={15} className="text-muted" />}
                  checked={selectedCats.includes(c.key)}
                  onChange={() => onToggleCat(c.key)}
                />
              );
            })}
          </Section>

          <Section title={t("technology")} last>
            {TECH_OPTIONS.map((tech) => (
              <Check
                key={tech}
                label={tech}
                checked={selectedTech.includes(tech)}
                onChange={() => onToggleTech(tech)}
              />
            ))}
          </Section>
        </div>

        {/* pastki urg'u chizig'i */}
        <div className="h-1 w-full bg-gradient-to-r from-accent/0 via-accent/40 to-accent/0" />
      </div>
    </aside>
  );
}

function Section({
  title,
  children,
  first,
  last,
}: {
  title: string;
  children: React.ReactNode;
  first?: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={`${first ? "" : "mt-4 border-t border-border pt-4"} ${
        last ? "" : ""
      }`}
    >
      <h3 className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
        <span className="h-3 w-0.5 rounded-full bg-accent/50" />
        {title}
      </h3>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

function Radio({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label className="-mx-2 flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-muted transition hover:bg-surface-2 hover:text-fg">
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition ${
          checked
            ? "border-accent ring-2 ring-accent/20"
            : "border-border-strong"
        }`}
      >
        {checked && <span className="h-2 w-2 rounded-full bg-accent" />}
      </span>
      <input
        type="radio"
        className="sr-only"
        checked={checked}
        onChange={onChange}
      />
      {label}
    </label>
  );
}

function Check({
  label,
  checked,
  onChange,
  icon,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
  icon?: React.ReactNode;
}) {
  return (
    <label className="-mx-2 flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm text-muted transition hover:bg-surface-2 hover:text-fg">
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition ${
          checked
            ? "border-accent bg-accent text-white ring-2 ring-accent/20"
            : "border-border-strong bg-transparent"
        }`}
      >
        {checked && <Check2 />}
      </span>
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={onChange}
      />
      {icon}
      <span className="truncate">{label}</span>
    </label>
  );
}

function Check2() {
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
      <path
        d="M5 12l5 5L20 6"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
