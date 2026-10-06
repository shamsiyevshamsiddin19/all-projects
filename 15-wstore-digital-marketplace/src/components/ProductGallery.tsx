"use client";

import { useState } from "react";

export default function ProductGallery({
  coverImage,
  screenshots,
  title,
}: {
  coverImage: string;
  screenshots: string[];
  title: string;
}) {
  const images = [coverImage, ...screenshots.filter((s) => s && s !== coverImage)];
  const [active, setActive] = useState(0);

  return (
    <div>
      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-xl shadow-black/20">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={images[active] ?? coverImage}
          alt={title}
          className="aspect-[16/10] w-full object-cover"
        />
      </div>

      {images.length > 1 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {images.map((src, i) => (
            <button
              key={i}
              onClick={() => setActive(i)}
              className={`h-14 w-20 shrink-0 overflow-hidden rounded-lg border-2 transition ${
                active === i
                  ? "border-accent"
                  : "border-transparent opacity-70 hover:opacity-100"
              }`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={src} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
