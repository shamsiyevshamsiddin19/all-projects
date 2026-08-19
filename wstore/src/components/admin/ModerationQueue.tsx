"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, X, Loader2 } from "lucide-react";
import { StatusButtons, CheckFileButton } from "@/components/admin/AdminActions";

export interface PendingProduct {
  id: string;
  title: string;
  price: number;
  coverImage: string;
  status: string;
  sellerLabel: string;
}

export default function ModerationQueue({ products }: { products: PendingProduct[] }) {
  const router = useRouter();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);

  function toggle(id: string) {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    setSelected((s) => (s.size === products.length ? new Set() : new Set(products.map((p) => p.id))));
  }

  async function bulk(status: "ACTIVE" | "REJECTED") {
    if (selected.size === 0) return;
    setBusy(true);
    await fetch("/api/admin/products/bulk-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: [...selected], status }),
    });
    setBusy(false);
    setSelected(new Set());
    router.refresh();
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-muted">
          <input
            type="checkbox"
            checked={selected.size > 0 && selected.size === products.length}
            onChange={toggleAll}
            className="h-3.5 w-3.5 accent-accent"
          />
          Hammasini tanlash
        </label>
        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">{selected.size} tanlandi</span>
            <button
              onClick={() => bulk("ACTIVE")}
              disabled={busy}
              className="flex items-center gap-1 rounded-md border border-green-500/40 bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-400 transition hover:bg-green-500/20 disabled:opacity-50"
            >
              {busy ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
              Hammasini tasdiqlash
            </button>
            <button
              onClick={() => bulk("REJECTED")}
              disabled={busy}
              className="flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
            >
              {busy ? <Loader2 size={12} className="animate-spin" /> : <X size={12} />}
              Hammasini rad etish
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        {products.map((p) => (
          <div
            key={p.id}
            className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={selected.has(p.id)}
                onChange={() => toggle(p.id)}
                className="h-3.5 w-3.5 shrink-0 accent-accent"
              />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={p.coverImage}
                alt=""
                className="h-12 w-16 shrink-0 rounded-md border border-border object-cover"
              />
              <div>
                <Link
                  href={`/seller/${p.id}/edit`}
                  className="text-sm font-medium text-fg hover:text-accent"
                >
                  {p.title}
                </Link>
                <div className="text-xs text-muted">
                  ${p.price} · {p.sellerLabel}
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <CheckFileButton productId={p.id} />
              <StatusButtons productId={p.id} status={p.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
