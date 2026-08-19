"use client";

import { useState } from "react";
import { Flag, X, Loader2, CheckCircle2 } from "lucide-react";

const REASONS = [
  "Mahsulot tavsifga mos emas",
  "Fayl yuklanmagan / ishlamaydi",
  "Firibgarlik / aldash",
  "Boshqa muallifning ishi (plagiat)",
  "Boshqa sabab",
];

export default function ReportButton({
  productId,
  loggedIn,
}: {
  productId: string;
  loggedIn: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState(REASONS[0]);
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openModal() {
    if (!loggedIn) {
      window.location.href = "/login";
      return;
    }
    setOpen(true);
  }

  async function submit() {
    setSending(true);
    setError(null);
    try {
      const res = await fetch("/api/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ productId, reason, comment }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? "Xatolik");
      }
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik yuz berdi");
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <button
        onClick={openModal}
        className="flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[11px] text-muted transition hover:border-red-500/40 hover:text-red-400"
      >
        <Flag size={11} /> Shikoyat
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <div className="relative w-full max-w-sm rounded-2xl border border-border bg-surface p-5 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-semibold text-fg">Shikoyat qilish</h3>
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg p-1 text-muted hover:text-fg"
              >
                <X size={18} />
              </button>
            </div>

            {sent ? (
              <div className="flex flex-col items-center gap-2 py-4 text-center">
                <CheckCircle2 size={32} className="text-green-400" />
                <p className="text-sm text-fg">Shikoyatingiz qabul qilindi.</p>
                <p className="text-xs text-muted">Admin ko&apos;rib chiqadi.</p>
              </div>
            ) : (
              <>
                <label className="mb-1.5 block text-xs text-muted">Sabab</label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="mb-3 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-fg outline-none focus:border-accent"
                >
                  {REASONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
                <label className="mb-1.5 block text-xs text-muted">
                  Izoh (ixtiyoriy)
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={3}
                  className="mb-3 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-fg outline-none focus:border-accent"
                  placeholder="Batafsilroq yozing..."
                />
                {error && <p className="mb-3 text-xs text-red-400">{error}</p>}
                <button
                  onClick={submit}
                  disabled={sending}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
                >
                  {sending && <Loader2 size={15} className="animate-spin" />}
                  Yuborish
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
