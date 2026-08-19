"use client";

import { useState } from "react";
import { CreditCard, Loader2 } from "lucide-react";

export default function ListingPayButton({ productId }: { productId: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`/api/products/${productId}/listing-pay`, {
        method: "POST",
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
    <div className="flex items-center gap-2">
      <button
        onClick={onClick}
        disabled={loading}
        className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <CreditCard size={13} />
        )}
        5000 so&apos;m to&apos;lab e&apos;lon qilish
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}
