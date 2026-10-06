"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, X, Trash2, Loader2, FileArchive } from "lucide-react";

async function post(url: string, body?: unknown, method = "POST") {
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.ok;
}

// Mahsulot holatini o'zgartirish tugmalari (tasdiqlash/rad/faollashtirish).
export function StatusButtons({
  productId,
  status,
}: {
  productId: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function set(next: string) {
    setBusy(true);
    const ok = await post(`/api/admin/products/${productId}/status`, {
      status: next,
    });
    setBusy(false);
    if (ok) router.refresh();
  }

  return (
    <div className="flex items-center gap-1.5">
      {busy && <Loader2 size={14} className="animate-spin text-muted" />}
      {status !== "ACTIVE" && (
        <button
          onClick={() => set("ACTIVE")}
          disabled={busy}
          className="flex items-center gap-1 rounded-md border border-green-500/40 bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-400 transition hover:bg-green-500/20 disabled:opacity-50"
        >
          <Check size={13} /> Tasdiqlash
        </button>
      )}
      {status !== "REJECTED" && (
        <button
          onClick={() => set("REJECTED")}
          disabled={busy}
          className="flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
        >
          <X size={13} /> Rad etish
        </button>
      )}
    </div>
  );
}

// Mahsulotni o'chirish tugmasi (tasdiq bilan).
export function DeleteButton({ productId }: { productId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function del() {
    if (!confirm("Mahsulot butunlay o'chirilsinmi?")) return;
    setBusy(true);
    const ok = await post(`/api/admin/products/${productId}`, undefined, "DELETE");
    setBusy(false);
    if (ok) router.refresh();
  }

  return (
    <button
      onClick={del}
      disabled={busy}
      className="flex items-center gap-1 rounded-md border border-border-strong px-2.5 py-1 text-xs text-muted transition hover:border-red-500/40 hover:text-red-400 disabled:opacity-50"
    >
      {busy ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
    </button>
  );
}

// Moderatsiyadan oldin sotuvchi yuklagan faylni tekshirish (yangi tabda ochiladi).
export function CheckFileButton({ productId }: { productId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function check() {
    setBusy(true);
    setError(null);
    try {
      // Endpoint faylni to'g'ridan-to'g'ri qaytaradi (mavjud bo'lsa) —
      // avval tekshirib, so'ng yangi tabda ochamiz.
      const res = await fetch(`/api/admin/products/${productId}/file`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? "Fayl topilmadi");
      }
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), "_blank", "noopener,noreferrer");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-1.5">
      <button
        onClick={check}
        disabled={busy}
        className="flex items-center gap-1 rounded-md border border-border-strong px-2.5 py-1 text-xs font-medium text-muted transition hover:border-accent hover:text-fg disabled:opacity-50"
      >
        {busy ? <Loader2 size={13} className="animate-spin" /> : <FileArchive size={13} />}
        Faylni tekshirish
      </button>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
}

// Shikoyat holatini almashtirish (OPEN <-> RESOLVED).
export function ReportStatusButton({
  reportId,
  status,
}: {
  reportId: string;
  status: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function set(next: string) {
    setBusy(true);
    const ok = await post(`/api/admin/reports/${reportId}`, { status: next });
    setBusy(false);
    if (ok) router.refresh();
  }

  return (
    <button
      onClick={() => set(status === "OPEN" ? "RESOLVED" : "OPEN")}
      disabled={busy}
      className={`flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium transition disabled:opacity-50 ${
        status === "OPEN"
          ? "border-green-500/40 bg-green-500/10 text-green-400 hover:bg-green-500/20"
          : "border-border-strong text-muted hover:text-fg"
      }`}
    >
      {busy && <Loader2 size={12} className="animate-spin" />}
      {status === "OPEN" ? "Hal qilindi deb belgilash" : "Qayta ochish"}
    </button>
  );
}

// Pul yechib olish so'rovini bajarish/rad etish.
export function WithdrawalActions({ withdrawalId }: { withdrawalId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function set(status: "PAID" | "REJECTED") {
    if (
      status === "REJECTED" &&
      !confirm("Rad etilsinmi? Mablag' sotuvchi balansiga qaytariladi.")
    )
      return;
    setBusy(true);
    const ok = await post(`/api/admin/withdrawals/${withdrawalId}`, { status });
    setBusy(false);
    if (ok) router.refresh();
  }

  return (
    <div className="flex items-center gap-1.5">
      {busy && <Loader2 size={14} className="animate-spin text-muted" />}
      <button
        onClick={() => set("PAID")}
        disabled={busy}
        className="flex items-center gap-1 rounded-md border border-green-500/40 bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-400 transition hover:bg-green-500/20 disabled:opacity-50"
      >
        <Check size={13} /> Kartaga to&apos;ladim
      </button>
      <button
        onClick={() => set("REJECTED")}
        disabled={busy}
        className="flex items-center gap-1 rounded-md border border-red-500/40 bg-red-500/10 px-2.5 py-1 text-xs font-medium text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
      >
        <X size={13} /> Rad etish
      </button>
    </div>
  );
}

// Foydalanuvchi rolini o'zgartirish (select).
export function RoleSelect({
  userId,
  role,
  disabled,
}: {
  userId: string;
  role: string;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [val, setVal] = useState(role);

  async function change(next: string) {
    setVal(next);
    setBusy(true);
    const ok = await post(`/api/admin/users/${userId}/role`, { role: next });
    setBusy(false);
    if (ok) router.refresh();
    else setVal(role);
  }

  return (
    <select
      value={val}
      disabled={disabled || busy}
      onChange={(e) => change(e.target.value)}
      className="rounded-md border border-border bg-surface px-2 py-1 text-xs text-fg outline-none focus:border-accent disabled:opacity-50"
    >
      <option value="BUYER">BUYER</option>
      <option value="SELLER">SELLER</option>
      <option value="ADMIN">ADMIN</option>
    </select>
  );
}
