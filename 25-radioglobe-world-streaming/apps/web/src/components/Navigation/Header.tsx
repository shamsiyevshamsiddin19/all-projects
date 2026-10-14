'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Radio, Compass, Heart, Search, Shield, Crosshair } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import { searchStations } from '@/lib/api';
import { Channel, Country } from '@/types';
import { useRouter } from 'next/navigation';

export default function Header() {
  const router = useRouter();
  const favorites = usePlayerStore((s) => s.favorites);
  const hydrated = usePlayerStore((s) => s.hydrated);
  const hydrate = usePlayerStore((s) => s.hydrate);
  const playStation = usePlayerStore((s) => s.playStation);
  const isPlaying = usePlayerStore((s) => s.isPlaying);

  useEffect(() => {
    hydrate();
  }, [hydrate]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<{ countries: Country[]; stations: Channel[] }>({
    countries: [],
    stations: [],
  });
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (val.trim().length < 2) {
      setSearchResults({ countries: [], stations: [] });
      return;
    }
    setIsSearching(true);
    const res = await searchStations(val.trim());
    setSearchResults(res);
    setIsSearching(false);
  };

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-40 bg-void-950/90 backdrop-blur-md border-b border-void-800 px-4 lg:px-8 py-2.5 transition-all duration-300">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo with Tactical Crimson theme */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-9 h-9 bg-crimson flex items-center justify-center shadow-crimson-glow group-hover:scale-105 transition-transform duration-200">
              <Radio className="w-5 h-5 text-white" />
              {isPlaying && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-white rounded-full animate-ping" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-black text-lg tracking-wider text-white">
                  RADIOGLOBE
                </span>
                <span className="text-[9px] font-mono font-bold tracking-widest px-1.5 py-0.5 bg-crimson-dark text-crimson-bright border border-crimson/50 uppercase">
                  SAT-LIVE
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 tracking-wider">
                BROADCAST COMMAND
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-4 font-mono text-xs">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-300 hover:text-white py-1.5 px-3 border border-transparent hover:border-void-700 hover:bg-void-900 transition-all"
            >
              <Compass className="w-3.5 h-3.5 text-crimson" />
              <span>[ GLOBUS ]</span>
            </Link>
            <Link
              href="/favorites"
              className="flex items-center gap-2 text-slate-300 hover:text-white py-1.5 px-3 border border-transparent hover:border-void-700 hover:bg-void-900 transition-all"
            >
              <Heart className="w-3.5 h-3.5 text-crimson" />
              <span>[ SEVIMLILAR ]</span>
              {hydrated && favorites.length > 0 && (
                <span className="text-[10px] font-bold px-1.5 py-0.2 bg-crimson text-white">
                  {favorites.length}
                </span>
              )}
            </Link>
            <Link
              href="/dmca"
              className="flex items-center gap-2 text-slate-400 hover:text-slate-200 py-1.5 px-3"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>[ DMCA ]</span>
            </Link>
          </nav>

          {/* Search Trigger Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-void-900 hover:bg-void-850 border border-void-750 hover:border-crimson text-slate-300 hover:text-white text-xs font-mono transition-all duration-200"
            >
              <Search className="w-3.5 h-3.5 text-crimson" />
              <span className="hidden sm:inline">RADAR SEARCH</span>
              <kbd className="hidden sm:inline-block text-[9px] bg-void-950 border border-void-700 px-1 py-0.5 text-slate-400">
                /
              </kbd>
            </button>
          </div>
        </div>
      </header>

      {/* Global Search Modal */}
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 bg-void-950/90 backdrop-blur-md flex items-start justify-center pt-20 px-4">
          <div className="w-full max-w-xl tactical-box p-0 shadow-tactical-glass overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Input bar */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-void-750">
              <Crosshair className="w-5 h-5 text-crimson" />
              <input
                type="text"
                autoFocus
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Davlat yoki radiostansiya qidirish..."
                className="w-full bg-transparent text-white placeholder-slate-500 font-mono text-sm focus:outline-none"
              />
              <button
                onClick={() => {
                  setIsSearchOpen(false);
                  setQuery('');
                  setSearchResults({ countries: [], stations: [] });
                }}
                className="text-[10px] font-mono text-slate-400 hover:text-white px-2 py-1 bg-void-850 border border-void-700"
              >
                ESC
              </button>
            </div>

            {/* Search Results */}
            <div className="max-h-96 overflow-y-auto p-4 space-y-4 font-mono">
              {isSearching && (
                <div className="text-center py-6 text-xs text-crimson animate-pulse">
                  RADAR SCANNING FREQUENCIES...
                </div>
              )}

              {!isSearching && query.length >= 2 && searchResults.countries.length === 0 && searchResults.stations.length === 0 && (
                <div className="text-center py-6 text-xs text-slate-400">
                  NO SIGNALS ACQUIRED.
                </div>
              )}

              {/* Countries result */}
              {searchResults.countries.length > 0 && (
                <div>
                  <h4 className="text-[10px] uppercase font-bold text-crimson-bright tracking-wider mb-2">
                    SECTORS / COUNTRIES
                  </h4>
                  <div className="space-y-1">
                    {searchResults.countries.map((c) => (
                      <button
                        key={c.iso2}
                        onClick={() => {
                          setIsSearchOpen(false);
                          router.push(`/radio/${c.slug}`);
                        }}
                        className="w-full flex items-center justify-between p-2.5 hover:bg-void-850 border border-transparent hover:border-crimson/30 text-left transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{c.flag_emoji || '⌖'}</span>
                          <div>
                            <p className="text-xs font-bold text-white uppercase">{c.name_uz || c.name_en}</p>
                            <p className="text-[10px] text-slate-400">{c.continent}</p>
                          </div>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 bg-crimson-dark text-crimson-bright border border-crimson/40">
                          {c.radio_count} NODES
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Stations result */}
              {searchResults.stations.length > 0 && (
                <div>
                  <h4 className="text-[10px] uppercase font-bold text-crimson-bright tracking-wider mb-2">
                    BROADCAST CHANNELS
                  </h4>
                  <div className="space-y-1">
                    {searchResults.stations.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => {
                          setIsSearchOpen(false);
                          playStation(s);
                        }}
                        className="w-full flex items-center justify-between p-2.5 hover:bg-void-850 border border-transparent hover:border-crimson/30 text-left transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-void-850 border border-void-750 flex items-center justify-center">
                            {s.logo_url ? (
                              <img src={s.logo_url} alt={s.name} className="w-6 h-6 object-contain" />
                            ) : (
                              <Radio className="w-4 h-4 text-crimson" />
                            )}
                          </div>
                          <div>
                            <p className="text-xs font-bold text-white uppercase">{s.name}</p>
                            <p className="text-[10px] text-slate-400">{s.tags.slice(0, 3).join(', ') || 'LIVE'}</p>
                          </div>
                        </div>
                        <span className="text-[11px] text-crimson-bright font-bold">
                          PLAY ▶
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
