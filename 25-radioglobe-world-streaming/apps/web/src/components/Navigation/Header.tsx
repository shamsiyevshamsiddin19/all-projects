'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Radio, Compass, Heart, Search, Shield, Globe } from 'lucide-react';
import { usePlayerStore } from '@/stores/playerStore';
import { searchStations } from '@/lib/api';
import { Channel, Country } from '@/types';
import { useRouter } from 'next/navigation';

export default function Header() {
  const router = useRouter();
  const { favorites, isPlaying, playStation } = usePlayerStore();
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
      <header className="fixed top-0 left-0 right-0 z-40 bg-space-950/80 backdrop-blur-md border-b border-space-800/80 px-4 lg:px-8 py-3 transition-all duration-300">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-cyan-glow group-hover:scale-105 transition-transform duration-300">
              <Radio className="w-5 h-5 text-space-950" />
              {isPlaying && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-ping" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent">
                  RadioGlobe
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-500/30">
                  LIVE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-wider">World Radio Streaming</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-cyan-400 transition-colors py-1 px-2 rounded-lg hover:bg-space-850/60"
            >
              <Compass className="w-4 h-4 text-cyan-400" />
              <span>Globus</span>
            </Link>
            <Link
              href="/favorites"
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-cyan-400 transition-colors py-1 px-2 rounded-lg hover:bg-space-850/60"
            >
              <Heart className="w-4 h-4 text-rose-400" />
              <span>Sevimlilar</span>
              {favorites.length > 0 && (
                <span className="text-xs px-1.5 py-0.2 rounded-full bg-rose-950/80 text-rose-400 border border-rose-500/30">
                  {favorites.length}
                </span>
              )}
            </Link>
            <Link
              href="/dmca"
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors py-1 px-2"
            >
              <Shield className="w-4 h-4" />
              <span>DMCA</span>
            </Link>
          </nav>

          {/* Search Trigger Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-space-850/80 hover:bg-space-800 border border-space-700/60 text-slate-300 hover:text-cyan-300 text-sm transition-all duration-200 hover:border-cyan-500/40"
            >
              <Search className="w-4 h-4 text-cyan-400" />
              <span className="hidden sm:inline">Qidirish...</span>
              <kbd className="hidden sm:inline-block text-[10px] bg-space-900 border border-space-700 px-1.5 py-0.5 rounded text-slate-400">
                /
              </kbd>
            </button>
          </div>
        </div>
      </header>

      {/* Global Search Modal */}
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 bg-space-950/85 backdrop-blur-md flex items-start justify-center pt-20 px-4">
          <div className="w-full max-w-xl bg-space-900 border border-space-700 rounded-2xl shadow-glass overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            {/* Input bar */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-space-800">
              <Search className="w-5 h-5 text-cyan-400" />
              <input
                type="text"
                autoFocus
                value={query}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Davlat yoki radiostansiya nomini yozing..."
                className="w-full bg-transparent text-white placeholder-slate-500 text-sm focus:outline-none"
              />
              <button
                onClick={() => {
                  setIsSearchOpen(false);
                  setQuery('');
                  setSearchResults({ countries: [], stations: [] });
                }}
                className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded-md bg-space-800 border border-space-700"
              >
                ESC
              </button>
            </div>

            {/* Search Results */}
            <div className="max-h-96 overflow-y-auto p-4 space-y-4">
              {isSearching && (
                <div className="text-center py-6 text-sm text-slate-400 animate-pulse">
                  Qidirilmoqda...
                </div>
              )}

              {!isSearching && query.length >= 2 && searchResults.countries.length === 0 && searchResults.stations.length === 0 && (
                <div className="text-center py-6 text-sm text-slate-400">
                  Hech narsa topilmadi.
                </div>
              )}

              {/* Countries result */}
              {searchResults.countries.length > 0 && (
                <div>
                  <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-2">
                    Davlatlar
                  </h4>
                  <div className="space-y-1">
                    {searchResults.countries.map((c) => (
                      <button
                        key={c.iso2}
                        onClick={() => {
                          setIsSearchOpen(false);
                          router.push(`/radio/${c.slug}`);
                        }}
                        className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-space-800 text-left transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{c.flag_emoji || '🌍'}</span>
                          <div>
                            <p className="text-sm font-medium text-white">{c.name_uz || c.name_en}</p>
                            <p className="text-xs text-slate-400">{c.continent}</p>
                          </div>
                        </div>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                          {c.radio_count} stansiya
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Stations result */}
              {searchResults.stations.length > 0 && (
                <div>
                  <h4 className="text-xs uppercase font-semibold text-slate-400 tracking-wider mb-2">
                    Radiostansiyalar
                  </h4>
                  <div className="space-y-1">
                    {searchResults.stations.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => {
                          setIsSearchOpen(false);
                          playStation(s);
                        }}
                        className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-space-800 text-left transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-space-800 flex items-center justify-center border border-space-700">
                            {s.logo_url ? (
                              <img src={s.logo_url} alt={s.name} className="w-6 h-6 object-contain rounded" />
                            ) : (
                              <Radio className="w-4 h-4 text-cyan-400" />
                            )}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">{s.name}</p>
                            <p className="text-xs text-slate-400">{s.tags.slice(0, 3).join(', ') || 'Radio'}</p>
                          </div>
                        </div>
                        <span className="text-xs text-cyan-400 hover:underline">
                          Tinglash
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
