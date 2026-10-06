"use client";

import { useApp, formatPrice } from "@/components/Providers";

export default function Price({
  usd,
  className,
}: {
  usd: number;
  className?: string;
}) {
  const { currency } = useApp();
  return <span className={className}>{formatPrice(usd, currency)}</span>;
}
