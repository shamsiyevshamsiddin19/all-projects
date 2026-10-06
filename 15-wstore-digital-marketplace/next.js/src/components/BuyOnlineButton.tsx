"use client";

import { useState } from "react";
import { CreditCard, Loader2 } from "lucide-react";
import { useT } from "@/components/Providers";

export default function BuyOnlineButton({
  productId,
  loggedIn,
  compact,
}: {
  productId: string;
  loggedIn: boolean;
  compact?: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = useT();

  async function onClick() {
    if (!loggedIn) {
      window.location.href = "/login";
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ productId }),
      });
      const data = await res.json();
      if (!res.ok || !data.url) {
        setError(data.error ?? "Xatolik yuz berdi");
        setLoading(false);
        return;
      }
      window.location.href = data.url;
    } catch {
      setError("Xatolik yuz berdi");
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <button
        onClick={onClick}
        disabled={loading}
        className={`flex w-full items-center justify-center gap-2 rounded-xl bg-accent font-semibold text-white shadow-lg shadow-accent/25 transition hover:bg-accent-hover hover:shadow-accent/35 active:scale-[0.98] disabled:opacity-60 disabled:shadow-none ${
          compact ? "h-12 text-sm" : "py-3.5 text-[15px]"
        }`}
      >
        {loading ? (
          <Loader2 size={16} className="animate-spin" />
        ) : (
          <CreditCard size={16} />
        )}
        {loading ? t("processing") : compact ? t("buyShort") : t("buyOnline")}
      </button>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
