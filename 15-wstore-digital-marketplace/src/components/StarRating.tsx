"use client";

import { Star } from "lucide-react";

// Faqat ko'rsatish uchun yulduzlar (to'ldirilgan + bo'sh), reyting kasr bo'lsa yaxlitlanadi.
export default function StarRating({
  value,
  size = 15,
}: {
  value: number;
  size?: number;
}) {
  const rounded = Math.round(value);
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          size={size}
          className={
            i <= rounded ? "fill-gold text-gold" : "fill-none text-border-strong"
          }
        />
      ))}
    </span>
  );
}
