"use client";

import { Sun, Moon } from "lucide-react";
import { useApp } from "@/components/Providers";

export default function ThemeToggle() {
  const { theme, setTheme } = useApp();

  return (
    <button
      type="button"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label="Temani almashtirish"
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-muted transition hover:border-border-strong hover:text-fg"
    >
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}
