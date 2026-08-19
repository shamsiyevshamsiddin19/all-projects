"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// To'lov hali PENDING bo'lsa, Click webhook orqali tasdiqlanguncha
// sahifani har 3s da yangilab turadi (websocket kerak emas — yengil DB-polling).
export default function OrderStatusPoll({ pending }: { pending: boolean }) {
  const router = useRouter();

  useEffect(() => {
    if (!pending) return;
    const id = setInterval(() => router.refresh(), 3000);
    return () => clearInterval(id);
  }, [pending, router]);

  return null;
}
