"use client";

import { useState } from "react";
import { Heart } from "lucide-react";

export default function WishlistButton({
  productId,
  initialWishlisted,
  loggedIn,
  size = "sm",
}: {
  productId: string;
  initialWishlisted: boolean;
  loggedIn: boolean;
  size?: "sm" | "lg";
}) {
  const [on, setOn] = useState(initialWishlisted);
  const [busy, setBusy] = useState(false);

  async function toggle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!loggedIn) {
      window.location.href = "/login";
      return;
    }
    if (busy) return;
    setBusy(true);
    const next = !on;
    setOn(next); // optimistik
    try {
      const res = await fetch(`/api/wishlist/${productId}`, {
        method: next ? "POST" : "DELETE",
      });
      if (!res.ok) setOn(!next); // xato bo'lsa qaytaramiz
    } catch {
      setOn(!next);
    } finally {
      setBusy(false);
    }
  }

  const dim = size === "lg" ? 20 : 15;

  return (
    <button
      onClick={toggle}
      aria-label="Sevimlilarga qo'shish"
      className={
        size === "lg"
          ? `flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition ${
              on
                ? "border-red-500/40 bg-red-500/10 text-red-400"
                : "border-border-strong bg-surface text-muted hover:text-fg"
            }`
          : `flex h-8 w-8 shrink-0 items-center justify-center rounded-full border backdrop-blur transition ${
              on
                ? "border-red-500/40 bg-red-500/20 text-red-400"
                : "border-border-strong bg-bg/60 text-fg hover:text-red-400"
            }`
      }
    >
      <Heart size={dim} className={on ? "fill-current" : ""} />
    </button>
  );
}
