"use client";

import { useState } from "react";
import { Globe } from "lucide-react";
import { useApp, type Lang } from "@/components/Providers";

const LANGS: { v: Lang; l: string }[] = [
  { v: "uz", l: "UZ" },
  { v: "ru", l: "RU" },
  { v: "en", l: "ENG" },
];

export default function LangSelect() {
  const { lang, setLang } = useApp();
  const [open, setOpen] = useState(false);
  const cur = LANGS.find((x) => x.v === lang) ?? LANGS[0];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 text-sm text-muted transition hover:text-fg"
      >
        <Globe size={15} /> {cur.l}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-2 w-28 rounded-lg border border-border bg-surface p-1 shadow-xl">
            {LANGS.map((x) => (
              <button
                key={x.v}
                onClick={() => {
                  setLang(x.v);
                  setOpen(false);
                }}
                className={`block w-full rounded px-3 py-2 text-left text-sm transition ${
                  lang === x.v
                    ? "bg-surface-2 text-fg"
                    : "text-muted hover:text-fg"
                }`}
              >
                {x.l}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
