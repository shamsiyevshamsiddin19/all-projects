"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Menu, X, LayoutGrid, Store, User, ChevronRight } from "lucide-react";
import { useT } from "@/components/Providers";

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const [panelIn, setPanelIn] = useState(false);
  const [mounted, setMounted] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const t = useT();
  const pathname = usePathname();

  const LINKS = [
    { href: "/", label: t("catalog"), icon: LayoutGrid },
    { href: "/seller", label: t("seller"), icon: Store },
    { href: "/dashboard", label: t("cabinet"), icon: User },
  ];

  useEffect(() => setMounted(true), []);

  function openMenu() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setOpen(true);
    setTimeout(() => setPanelIn(true), 20);
  }
  function closeMenu() {
    setPanelIn(false);
    closeTimer.current = setTimeout(() => setOpen(false), 220);
  }

  return (
    <div className="md:hidden">
      <button
        onClick={openMenu}
        className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted transition hover:border-border-strong hover:text-fg"
        aria-label={t("menu")}
      >
        <Menu size={20} />
      </button>

      {mounted &&
        open &&
        createPortal(
          <div className="fixed inset-0 z-50 md:hidden">
            <div
              className={`absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${
                panelIn ? "opacity-100" : "opacity-0"
              }`}
              onClick={closeMenu}
            />
            <div
              className={`absolute right-0 top-0 flex h-full w-[78%] max-w-xs flex-col border-l border-border bg-bg shadow-2xl transition-transform duration-300 ease-out ${
                panelIn ? "translate-x-0" : "translate-x-full"
              }`}
            >
              <div className="flex items-center justify-between border-b border-border px-4 py-4">
                <Link
                  href="/"
                  onClick={closeMenu}
                  className="flex items-center gap-2"
                >
                  <Image
                    src="/logo-icon.png"
                    alt="wstore.uz"
                    width={26}
                    height={26}
                    className="h-[26px] w-[26px] object-contain"
                  />
                  <span className="font-semibold">
                    wstore<span className="text-muted">.uz</span>
                  </span>
                </Link>
                <button
                  onClick={closeMenu}
                  className="rounded-lg p-1.5 text-muted transition hover:bg-surface-2 hover:text-fg"
                  aria-label={t("close")}
                >
                  <X size={20} />
                </button>
              </div>
              <nav className="flex flex-col gap-1 p-3">
                {LINKS.map((l) => {
                  const active =
                    l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
                  const Icon = l.icon;
                  return (
                    <Link
                      key={l.href}
                      href={l.href}
                      onClick={closeMenu}
                      className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition ${
                        active
                          ? "bg-accent/15 text-accent"
                          : "text-muted hover:bg-surface-2 hover:text-fg"
                      }`}
                    >
                      <Icon size={18} />
                      <span className="flex-1">{l.label}</span>
                      <ChevronRight
                        size={15}
                        className={active ? "text-accent" : "text-border-strong"}
                      />
                    </Link>
                  );
                })}
              </nav>
              <div className="mt-auto border-t border-border px-4 py-4">
                <p className="text-xs text-muted">
                  wstore<span className="text-fg/70">.uz</span> — tayyor
                  kod, botlar, saytlar va ilovalar bozori
                </p>
              </div>
            </div>
          </div>,
          document.body,
        )}
    </div>
  );
}
