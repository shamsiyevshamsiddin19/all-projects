'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Heart, Loader2, Radio, Search, X } from 'lucide-react';

import StationLogo from '@/components/Country/StationLogo';
import { searchStations } from '@/lib/api';
import { usePlayerStore } from '@/stores/playerStore';
import type { Channel, Country } from '@/types';

const DEBOUNCE_MS = 250;

export default function Header() {
  const router = useRouter();
  const favorites = usePlayerStore((s) => s.favorites);
  const hydrated = usePlayerStore((s) => s.hydrated);
  const hydrate = usePlayerStore((s) => s.hydrate);
  const playStation = usePlayerStore((s) => s.playStation);

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<{ countries: Country[]; stations: Channel[] }>({
    countries: [],
    stations: [],
  });
  const [loading, setLoading] = useState(false);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
    setResults({ countries: [], stations: [] });
  }, []);

  // "/" — qidiruvni ochadi, Esc — yopadi. Klaviatura bilan ishlaydiganlar uchun.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typingElsewhere =
        e.target instanceof HTMLElement &&
        ['INPUT', 'TEXTAREA'].includes(e.target.tagName);

      if (e.key === '/' && !typingElsewhere) {
        e.preventDefault();
        setOpen(true);
        requestAnimationFrame(() => inputRef.current?.focus());
      }
      if (e.key === 'Escape') close();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [close]);

  // Har harfda so'rov yubormaymiz: debounce + oldingi so'rovni bekor qilish
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

  const hasResults = results.countries.length > 0 || results.stations.length > 0;

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-ink-800 bg-ink-950/85 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-2.5" onClick={close}>
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-signal text-white">
            <Radio className="h-4 w-4" />
          </span>
          <span className="font-display text-base font-semibold tracking-tight text-text-primary">
            RadioGlobe
          </span>
        </Link>

        <div className="flex-1" />

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
            setOpen(true);
            requestAnimationFrame(() => inputRef.current?.focus());
          }}
          className="flex h-9 items-center gap-2 rounded-lg border border-ink-700 bg-ink-900 px-3
                     text-sm text-text-muted transition-colors hover:border-ink-600 hover:text-text-secondary"
          aria-label="Qidiruvni ochish"
        >
          <Search className="h-4 w-4" />
          <span className="hidden sm:inline">Qidirish</span>
          <kbd className="hidden rounded border border-ink-700 px-1.5 font-mono text-[10px] sm:inline">
            /
          </kbd>
        </button>
      </div>

      {/* ── Qidiruv paneli ── */}
      {open ? (
        <>
          <div
            className="fixed inset-0 -z-10 bg-ink-950/70"
            onClick={close}
            aria-hidden="true"
          />
          <div className="border-t border-ink-800 bg-ink-950">
            <div className="mx-auto max-w-3xl px-4 py-4">
              <div className="flex items-center gap-3 rounded-xl border border-ink-700 bg-ink-900 px-3.5">
                <Search className="h-4 w-4 shrink-0 text-text-muted" />
                <input
                  ref={inputRef}
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Stansiya yoki davlat nomi…"
                  className="h-12 flex-1 bg-transparent text-sm text-text-primary
                             placeholder:text-text-muted focus:outline-none"
                  aria-label="Qidiruv so'rovi"
                />
                {loading ? (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-text-muted" />
                ) : null}
                <button
                  type="button"
                  onClick={close}
                  className="shrink-0 text-text-muted transition-colors hover:text-text-primary"
                  aria-label="Qidiruvni yopish"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              {query.trim().length >= 2 && !loading && !hasResults ? (
                <p className="px-1 py-6 text-center text-sm text-text-muted">
                  «{query.trim()}» bo'yicha hech narsa topilmadi
                </p>
              ) : null}

              {hasResults ? (
                <div className="mt-3 max-h-[60vh] space-y-4 overflow-y-auto pb-2">
                  {results.countries.length > 0 ? (
                    <div>
                      <p className="eyebrow mb-2 px-1">Davlatlar</p>
                      <div className="flex flex-wrap gap-2">
                        {results.countries.map((c) => (
                          <button
                            key={c.iso2}
                            type="button"
                            onClick={() => {
                              router.push(`/radio/${c.slug}`);
                              close();
                            }}
                            className="flex items-center gap-2 rounded-lg border border-ink-700
                                       bg-ink-900 px-3 py-2 text-sm text-text-secondary
                                       transition-colors hover:border-ink-600 hover:text-text-primary"
                          >
                            <span aria-hidden="true">{c.flag_emoji || '🌐'}</span>
                            {c.name_uz || c.name_en}
                            <span className="font-mono text-xs text-text-muted">
                              {c.radio_count}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {results.stations.length > 0 ? (
                    <div>
                      <p className="eyebrow mb-2 px-1">Stansiyalar</p>
                      <ul className="space-y-1">
                        {results.stations.map((s) => (
                          <li key={s.id}>
                            <button
                              type="button"
                              onClick={() => {
                                playStation(s);
                                close();
                              }}
                              className="flex w-full items-center gap-3 rounded-lg px-2 py-2
                                         text-left transition-colors hover:bg-ink-850"
                            >
                              <StationLogo src={s.logo_url} alt={s.name} size={36} />
                              <span className="min-w-0 flex-1">
                                <span className="block truncate text-sm text-text-primary">
                                  {s.name}
                                </span>
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
              ) : null}
            </div>
          </div>
        </>
      ) : null}
    </header>
  );
}
