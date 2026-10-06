"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Star, Loader2 } from "lucide-react";
import { useT } from "@/components/Providers";

export default function ReviewForm({
  productId,
  loggedIn,
}: {
  productId: string;
  loggedIn: boolean;
}) {
  const router = useRouter();
  const t = useT();
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  if (!loggedIn) {
    return (
      <button
        onClick={() => router.push("/login")}
        className="flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
      >
        {t("signInToReview")}
      </button>
    );
  }

  async function submit() {
    setError(null);
    if (!rating) {
      setError(t("yourRating"));
      return;
    }
    if (comment.trim().length < 2) {
      setError(t("reviewPlaceholder"));
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`/api/products/${productId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating, comment }),
      });
      const data = await res.json().catch(() => ({}));
      setLoading(false);
      if (!res.ok) {
        setError(data.error ?? "Xatolik");
        return;
      }
      setDone(true);
      router.refresh();
    } catch {
      setLoading(false);
      setError("Xatolik");
    }
  }

  if (done) {
    return (
      <p className="rounded-lg border border-green-500/40 bg-green-500/10 px-4 py-3 text-sm text-green-400">
        {t("reviewSaved")}
      </p>
    );
  }

  return (
    <div className="rounded-card border border-border bg-surface p-4">
      <div className="mb-2 text-sm text-muted">{t("yourRating")}</div>
      <div className="mb-3 flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <button
            key={i}
            type="button"
            onClick={() => setRating(i)}
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(0)}
            className="p-0.5"
            aria-label={`${i}`}
          >
            <Star
              size={24}
              className={
                i <= (hover || rating)
                  ? "fill-gold text-gold"
                  : "fill-none text-border-strong"
              }
            />
          </button>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        placeholder={t("reviewPlaceholder")}
        className="w-full rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-fg outline-none placeholder:text-muted/60 focus:border-accent"
      />
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
      <button
        onClick={submit}
        disabled={loading}
        className="mt-3 flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:opacity-60"
      >
        {loading && <Loader2 size={16} className="animate-spin" />}
        {t("send")}
      </button>
    </div>
  );
}
