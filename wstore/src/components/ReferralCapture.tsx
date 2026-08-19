"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

const KEY = "wstore_ref_code";

// Sahifada ?ref=CODE bo'lsa saqlab qo'yamiz; login qilingandan so'ng
// (yoki allaqachon kirgan bo'lsa) serverga yuborib bog'laymiz.
// Auth holatini bilish shart emas — API 401 qaytarsa keyinroq qayta uriladi.
export default function ReferralCapture() {
  const params = useSearchParams();

  useEffect(() => {
    const ref = params.get("ref");
    if (ref) localStorage.setItem(KEY, ref);
  }, [params]);

  useEffect(() => {
    const code = localStorage.getItem(KEY);
    if (!code) return;
    fetch("/api/referral/link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    })
      .then((res) => {
        if (res.status !== 401) localStorage.removeItem(KEY);
      })
      .catch(() => {});
  }, []);

  return null;
}
