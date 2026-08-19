"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Wallet } from "lucide-react";

export default function WithdrawalForm({
  balance,
  minAmount,
}: {
  balance: number;
  minAmount: number;
}) {
  const router = useRouter();
  const [amount, setAmount] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setLoading(true);
    try {
      const res = await fetch("/api/seller/withdrawals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount: Number(amount),
          cardNumber: cardNumber.replace(/\s+/g, ""),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error ?? "Xatolik yuz berdi");
      setSuccess(true);
      setAmount("");
      setCardNumber("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  }

  const fmt = (n: number) => n.toLocaleString("en-US").replace(/,/g, " ");

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div>
        <label className="mb-1.5 block text-sm text-muted">Summa (so&apos;m)</label>
        <input
          type="number"
          min={minAmount}
          max={balance}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder={`Kamida ${fmt(minAmount)}`}
          required
          className="w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
        />
      </div>
      <div>
        <label className="mb-1.5 block text-sm text-muted">
          Karta raqami (Uzcard/Humo, 16 xonali)
        </label>
        <input
          type="text"
          inputMode="numeric"
          value={cardNumber}
          onChange={(e) => setCardNumber(e.target.value)}
          placeholder="8600 1234 5678 9012"
          maxLength={19}
          required
          className="w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-fg outline-none focus:border-accent"
        />
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {success && (
        <p className="text-xs text-green-400">
          So&apos;rov yuborildi. Admin qo&apos;lda ko&apos;rib chiqib to&apos;laydi.
        </p>
      )}
      <button
        disabled={loading || balance < minAmount}
        className="flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading ? <Loader2 size={15} className="animate-spin" /> : <Wallet size={15} />}
        Pul yechib olishni so&apos;rash
      </button>
      {balance < minAmount && (
        <p className="text-xs text-muted">
          Yechib olish uchun balansingizda kamida {fmt(minAmount)} so&apos;m bo&apos;lishi kerak.
        </p>
      )}
    </form>
  );
}
