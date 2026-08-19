"use client";

import { useState } from "react";
import Link from "next/link";
import { signIn, signOut } from "next-auth/react";
import { ChevronDown, RefreshCw, LogOut, Shield, LayoutDashboard, Store, Heart } from "lucide-react";

export default function AccountMenu({
  name,
  image,
  role,
}: {
  name?: string | null;
  image?: string | null;
  role?: string;
}) {
  const [open, setOpen] = useState(false);
  const item =
    "flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm transition";

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg border border-border px-2 py-1.5 transition hover:border-border-strong"
      >
        {image && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={image}
            alt=""
            className="h-7 w-7 rounded-full border border-border-strong"
          />
        )}
        <span className="hidden max-w-[130px] truncate text-sm text-fg sm:inline">
          {name}
        </span>
        <ChevronDown
          size={14}
          className={`text-muted transition ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-2 w-56 rounded-xl border border-border bg-surface p-1.5 shadow-xl">
            <div className="border-b border-border px-3 py-2 text-xs text-muted">
              {name}
            </div>
            <Link
              href="/dashboard"
              onClick={() => setOpen(false)}
              className={`${item} text-muted hover:bg-surface-2 hover:text-fg`}
            >
              <LayoutDashboard size={15} /> Kabinet
            </Link>
            <Link
              href="/wishlist"
              onClick={() => setOpen(false)}
              className={`${item} text-muted hover:bg-surface-2 hover:text-fg`}
            >
              <Heart size={15} /> Sevimlilar
            </Link>
            <Link
              href="/seller"
              onClick={() => setOpen(false)}
              className={`${item} text-muted hover:bg-surface-2 hover:text-fg`}
            >
              <Store size={15} /> Sotuvchi paneli
            </Link>
            {role === "ADMIN" && (
              <Link
                href="/admin"
                onClick={() => setOpen(false)}
                className={`${item} text-accent hover:bg-surface-2`}
              >
                <Shield size={15} /> Admin panel
              </Link>
            )}
            <button
              onClick={() => signIn("google")}
              className={`${item} text-muted hover:bg-surface-2 hover:text-fg`}
            >
              <RefreshCw size={15} /> Akkauntni almashtirish
            </button>
            <button
              onClick={() => signOut()}
              className={`${item} text-red-400 hover:bg-surface-2`}
            >
              <LogOut size={15} /> Chiqish
            </button>
          </div>
        </>
      )}
    </div>
  );
}
