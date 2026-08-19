"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Loader2, Pause, Play } from "lucide-react";

// Sotuvchi o'z mahsulotini butunlay o'chirishi (tasdiq bilan).
export default function DeleteProductButton({ productId }: { productId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function del() {
    if (!confirm("Mahsulot butunlay o'chirilsinmi? Bu amalni ortga qaytarib bo'lmaydi.")) {
      return;
    }
    setBusy(true);
    const res = await fetch(`/api/products/${productId}`, { method: "DELETE" });
    setBusy(false);
    if (res.ok) router.refresh();
    else alert("O'chirishda xatolik yuz berdi");
  }

  return (
    <button
      onClick={del}
      disabled={busy}
      className="flex items-center gap-1 rounded-md border border-border-strong px-2.5 py-1.5 text-xs text-muted transition hover:border-red-500/40 hover:text-red-400 disabled:opacity-50"
    >
      {busy ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
    </button>
  );
}

// Sotuvchi mahsulotni vaqtincha ko'rinishdan yashirishi/qayta yoqishi
// (moderatsiyaga qaytarilmaydi — REJECTED holatidan farqli).
export function ToggleActiveButton({
  productId,
  status,
}: {
  productId: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const isActive = status === "ACTIVE";

  async function toggle() {
    setBusy(true);
    const res = await fetch(`/api/products/${productId}/toggle-active`, {
      method: "POST",
    });
    setBusy(false);
    if (res.ok) router.refresh();
    else alert("Xatolik yuz berdi");
  }

  return (
    <button
      onClick={toggle}
      disabled={busy}
      className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition disabled:opacity-50 ${
        isActive
          ? "border-border-strong text-muted hover:border-gold/40 hover:text-gold"
          : "border-gold/40 bg-gold/10 text-gold hover:bg-gold/20"
      }`}
    >
      {busy ? (
        <Loader2 size={13} className="animate-spin" />
      ) : isActive ? (
        <Pause size={13} />
      ) : (
        <Play size={13} />
      )}
      {isActive ? "Vaqtincha yashirish" : "Qayta faollashtirish"}
    </button>
  );
}
