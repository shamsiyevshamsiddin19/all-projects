"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import {
  useApp,
  useT,
  CURRENCIES,
  CURRENCY_META,
  type Currency,
} from "@/components/Providers";

export default function CurrencyToggle() {
  const { currency, setCurrency } = useApp();
  const [open, setOpen] = useState(false);
  const t = useT();

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs font-medium text-fg transition hover:border-border-strong"
        aria-label={t("currency")}
      >
        {CURRENCY_META[currency].code}
        <ChevronDown size={13} className="text-muted" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-full z-50 mt-1.5 w-32 rounded-lg border border-border bg-surface p-1 shadow-xl">
            {CURRENCIES.map((c: Currency) => (
              <button
                key={c}
                type="button"
                onClick={() => {
                  setCurrency(c);
                  setOpen(false);
                }}
                className={`flex w-full items-center justify-between rounded px-3 py-2 text-left text-xs transition ${
                  currency === c
                    ? "bg-surface-2 text-fg"
                    : "text-muted hover:text-fg"
                }`}
              >
                <span>{CURRENCY_META[c].code}</span>
                <span className="text-[10px] text-muted">
                  {CURRENCY_META[c].suffix}
                </span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
