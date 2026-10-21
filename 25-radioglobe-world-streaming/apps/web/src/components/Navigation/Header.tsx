'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Heart, Loader2, Search, X } from 'lucide-react';

import StationLogo from '@/components/Country/StationLogo';
import { searchStations } from '@/lib/api';
import { usePlayerStore } from '@/stores/playerStore';
import type { Channel, Country } from '@/types';

const DEBOUNCE_MS = 250;

/**
 * Qidiruv natijalari — ikkala ko'rinish (desktop dropdown va mobil panel)
 * tomonidan baham ko'riladigan bitta blok.
 */
function SearchResults({
  loading,
  query,
  countries,
  stations,
  onSelectCountry,
  onSelectStation,
}: {
  loading: boolean;
  query: string;
  countries: Country[];
  stations: Channel[];
  onSelectCountry: (c: Country) => void;
  onSelectStation: (s: Channel) => void;
}) {
  const hasResults = countries.length > 0 || stations.length > 0;
  const term = query.trim();

  if (term.length < 2) return null;

  if (!loading && !hasResults) {
    return (
      <p className="px-3 py-6 text-center text-sm text-text-muted">
        «{term}» bo'yicha hech narsa topilmadi
      </p>
    );
  }

  if (!hasResults) return null;

  return (
    <div className="max-h-[60vh] space-y-4 overflow-y-auto p-3">
      {countries.length > 0 ? (
        <div>
          <p className="eyebrow mb-2 px-1">Davlatlar</p>
          <div className="flex flex-wrap gap-2">
            {countries.map((c) => (
              <button
                key={c.iso2}
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => onSelectCountry(c)}
                className="flex items-center gap-2 rounded-lg border border-ink-700
                           bg-ink-900 px-3 py-2 text-sm text-text-secondary
                           transition-colors hover:border-ink-600 hover:text-text-primary"
              >
                <span aria-hidden="true">{c.flag_emoji || '🌐'}</span>
                {c.name_uz || c.name_en}
                <span className="font-mono text-xs text-text-muted">{c.radio_count}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {stations.length > 0 ? (
        <div>
          <p className="eyebrow mb-2 px-1">Stansiyalar</p>
          <ul className="space-y-1">
            {stations.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => onSelectStation(s)}
                  className="flex w-full items-center gap-3 rounded-lg px-2 py-2
                             text-left transition-colors hover:bg-ink-850"
                >
                  <StationLogo src={s.logo_url} alt={s.name} size={36} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-text-primary">{s.name}</span>
                    <span className="block truncate text-xs text-text-muted">
                      {s.tags.slice(0, 3).join(' · ') || 'Jonli efir'}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export default function Header() {
  const router = useRouter();
  const favorites = usePlayerStore((s) => s.favorites);
  const hydrated = usePlayerStore((s) => s.hydrated);
  const hydrate = usePlayerStore((s) => s.hydrate);
  const playStation = usePlayerStore((s) => s.playStation);

  // Mobil: tugma bosilganda to'liq ekran paneli ochiladi
  const [mobileOpen, setMobileOpen] = useState(false);
  // Desktop: inputga fokus tushganda takliflar ro'yxati ko'rinadi
  const [desktopFocused, setDesktopFocused] = useState(false);

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{ countries: Country[]; stations: Channel[] }>({
    countries: [],
    stations: [],
  });
  const [loading, setLoading] = useState(false);

  const desktopInputRef = useRef<HTMLInputElement | null>(null);
  const mobileInputRef = useRef<HTMLInputElement | null>(null);
  const desktopBoxRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const closeMobile = useCallback(() => {
    setMobileOpen(false);
    setQuery('');
    setResults({ countries: [], stations: [] });
  }, []);

  const clearDesktop = useCallback(() => {
    setQuery('');
    setResults({ countries: [], stations: [] });
    desktopInputRef.current?.blur();
  }, []);

  // "/" — fokusni qidiruvga o'tkazadi (desktopda inputga, mobilda panelni ochadi).
  // Esc — yopadi/tozalaydi.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typingElsewhere =
        e.target instanceof HTMLElement &&
        ['INPUT', 'TEXTAREA'].includes(e.target.tagName);

      if (e.key === '/' && !typingElsewhere) {
        e.preventDefault();
        if (window.matchMedia('(min-width: 768px)').matches) {
          desktopInputRef.current?.focus();
        } else {
          setMobileOpen(true);
          requestAnimationFrame(() => mobileInputRef.current?.focus());
        }
      }
      if (e.key === 'Escape') {
        closeMobile();
        clearDesktop();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [closeMobile, clearDesktop]);

  // Desktop'da: tashqariga bosilganda takliflar yopiladi
  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (desktopBoxRef.current && !desktopBoxRef.current.contains(e.target as Node)) {
        setDesktopFocused(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  // Har harfda so'rov yubormaymiz: debounce + oldingi so'rovni bekor qilish.
  // Bu haqiqiy "autocomplete" — inputga yozilayotganda natijalar o'zi paydo bo'ladi,
  // alohida qidiruv tugmasini bosish shart emas.
  useEffect(() => {
    const term = query.trim();
    if (term.length < 2) {
      setResults({ countries: [], stations: [] });
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const res = await searchStations(term, controller.signal);
      if (!controller.signal.aborted) {
        setResults({ countries: res.countries, stations: res.stations });
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(timer);
  }, [query]);

  const selectCountry = (c: Country) => {
    router.push(`/radio/${c.slug}`);
    clearDesktop();
    closeMobile();
  };

  const selectStation = (s: Channel) => {
    playStation(s);
    clearDesktop();
    closeMobile();
  };

  const showDesktopDropdown = desktopFocused && query.trim().length >= 2;

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-ink-800 bg-ink-950/85 backdrop-blur-xl">
      {/*
        To'liq kenglikda (max-w bilan cheklanmagan) — bosh sahifadagi hero
        bo'limi bilan bir xil falsafa: logo haqiqiy CHAP chekkada, sevimlilar
        haqiqiy O'NG chekkada turadi. 3 ustunli grid: chap/markaz/o'ng — shu
        bilan qidiruv ekran qanchalik keng bo'lishidan qat'i nazar aniq
        MARKAZDA qoladi (faqat ikki yon ustun orasidagi bo'shliq emas).
      */}
      <div className="grid h-14 grid-cols-[auto_1fr_auto] items-center gap-3 px-4 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2.5" onClick={closeMobile}>
          {/* Brend belgisi — faviconda ishlatilgan xuddi shu rasm, shu bilan
              header va brauzer tabidagi ikonka bir xil bo'ladi */}
          <Image
            src="/icon-192.png"
            alt="RadioGlobe"
            width={32}
            height={32}
            priority
            className="h-8 w-8"
          />
          <span className="font-display text-base font-semibold tracking-tight text-text-primary">
            RadioGlobe
          </span>
        </Link>

        {/* ── Markaz: desktopda doimiy ko'rinadigan qidiruv inputi ── */}
        <div className="hidden justify-center md:flex">
          <div ref={desktopBoxRef} className="relative w-full max-w-md">
            <div
              className={`flex h-9 items-center gap-2 rounded-lg border bg-ink-900 px-3
                          transition-colors ${
                            desktopFocused
                              ? 'border-signal/50'
                              : 'border-ink-700 hover:border-ink-600'
                          }`}
            >
              <Search className="h-4 w-4 shrink-0 text-text-muted" />
              <input
                ref={desktopInputRef}
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setDesktopFocused(true)}
                placeholder="Stansiya yoki davlat qidirish…"
                className="h-full min-w-0 flex-1 bg-transparent text-sm text-text-primary
                           placeholder:text-text-muted focus:outline-none"
                aria-label="Qidiruv so'rovi"
                autoComplete="off"
              />
              {loading ? (
                <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-text-muted" />
              ) : query ? (
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={clearDesktop}
                  className="shrink-0 text-text-muted transition-colors hover:text-text-primary"
                  aria-label="Tozalash"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              ) : (
                <kbd className="shrink-0 rounded border border-ink-700 px-1.5 font-mono text-[10px] text-text-muted">
                  /
                </kbd>
              )}
            </div>

            {/* ── Avtomatik takliflar — inputga qarab osilib tushadi ── */}
            {showDesktopDropdown ? (
              <div className="panel absolute left-0 right-0 top-full mt-2 overflow-hidden">
                <SearchResults
                  loading={loading}
                  query={query}
                  countries={results.countries}
                  stations={results.stations}
                  onSelectCountry={selectCountry}
                  onSelectStation={selectStation}
                />
              </div>
            ) : null}
          </div>
        </div>

        {/* ── O'ng: sevimlilar + mobil qidiruv tugmasi ── */}
        <div className="flex items-center justify-end gap-1.5">
          <Link
            href="/favorites"
            className="relative flex h-9 items-center gap-2 rounded-lg px-3 text-sm
                       text-text-secondary transition-colors hover:bg-ink-850 hover:text-text-primary"
          >
            <Heart className="h-4 w-4" />
            <span className="hidden sm:inline">Sevimlilar</span>
            {hydrated && favorites.length > 0 ? (
              <span className="rounded-full bg-signal px-1.5 py-0.5 text-[10px] font-medium text-white">
                {favorites.length}
              </span>
            ) : null}
          </Link>

          <button
            type="button"
            onClick={() => {
              setMobileOpen(true);
              requestAnimationFrame(() => mobileInputRef.current?.focus());
            }}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-ink-700
                       bg-ink-900 text-text-muted transition-colors hover:border-ink-600
                       hover:text-text-secondary md:hidden"
            aria-label="Qidiruvni ochish"
          >
            <Search className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* ── Mobil qidiruv paneli (to'liq kenglikda, button orqali ochiladi) ── */}
      {mobileOpen ? (
        <>
          <div
            className="fixed inset-0 -z-10 bg-ink-950/70"
            onClick={closeMobile}
            aria-hidden="true"
          />
          <div className="border-t border-ink-800 bg-ink-950 md:hidden">
            <div className="px-4 py-4">
              <div className="flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-900 px-3.5">
                <Search className="h-4 w-4 shrink-0 text-text-muted" />
                <input
                  ref={mobileInputRef}
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Stansiya yoki davlat nomi…"
                  className="h-12 flex-1 bg-transparent text-sm text-text-primary
                             placeholder:text-text-muted focus:outline-none"
                  aria-label="Qidiruv so'rovi"
                  autoComplete="off"
                />
                {loading ? (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-text-muted" />
                ) : null}
                <button
                  type="button"
                  onClick={closeMobile}
                  className="shrink-0 text-text-muted transition-colors hover:text-text-primary"
                  aria-label="Qidiruvni yopish"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <SearchResults
                loading={loading}
                query={query}
                countries={results.countries}
                stations={results.stations}
                onSelectCountry={selectCountry}
                onSelectStation={selectStation}
              />
            </div>
          </div>
        </>
      ) : null}
    </header>
  );
}
