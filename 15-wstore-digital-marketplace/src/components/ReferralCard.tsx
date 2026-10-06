"use client";

import { useState } from "react";
import { Gift, Copy, Check } from "lucide-react";

export default function ReferralCard({
  link,
  referralCount,
  bonusEarned,
}: {
  link: string;
  referralCount: number;
  bonusEarned: number;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard ruxsat bo'lmasa jim o'tamiz */
    }
  }

  return (
    <div className="rounded-card border border-border bg-surface p-5">
      <div className="mb-3 flex items-center gap-2">
        <Gift size={18} className="text-accent" />
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
          Do&apos;stlarni taklif qiling
        </h2>
      </div>
      <p className="mb-3 text-sm text-muted">
        Havolangiz orqali kelgan do&apos;stingiz birinchi xaridini qilsa,
        balansingizga bonus tushadi.
      </p>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          readOnly
          value={link}
          className="flex-1 truncate rounded-lg border border-border bg-bg px-3 py-2.5 text-sm text-fg outline-none"
        />
        <button
          onClick={copy}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover"
        >
          {copied ? <Check size={15} /> : <Copy size={15} />}
          {copied ? "Nusxalandi" : "Nusxalash"}
        </button>
      </div>
      <div className="mt-4 flex gap-6 text-sm">
        <div>
          <div className="font-semibold text-fg">{referralCount}</div>
          <div className="text-xs text-muted">taklif qilingan</div>
        </div>
        <div>
          <div className="font-semibold text-fg">
            {bonusEarned.toLocaleString("en-US").replace(/,/g, " ")} so&apos;m
          </div>
          <div className="text-xs text-muted">bonus qo&apos;lga kiritildi</div>
        </div>
      </div>
    </div>
  );
}
