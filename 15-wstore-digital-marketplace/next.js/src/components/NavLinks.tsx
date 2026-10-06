"use client";

import Link from "next/link";
import { useT } from "@/components/Providers";

// Desktop markaziy menyu — tarjima qilinadigan havolalar.
export default function NavLinks() {
  const t = useT();
  return (
    <nav className="hidden items-center gap-6 text-sm text-muted md:flex">
      <Link href="/" className="transition hover:text-fg">
        {t("catalog")}
      </Link>
      <Link href="/seller" className="transition hover:text-fg">
        {t("seller")}
      </Link>
      <Link href="/dashboard" className="transition hover:text-fg">
        {t("cabinet")}
      </Link>
    </nav>
  );
}
