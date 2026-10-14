'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useRouter } from 'next/navigation';

import GlobeHUD from '@/components/Globe/GlobeHUD';
import type { Country } from '@/types';

interface GlobeMapProps {
  countries: Country[];
  geojsonUrl: string;
  /** MapLibre ishga tusholmasa chaqiriladi — ota komponent ro'yxatga o'tadi */
  onUnsupported?: () => void;
}

interface HoverInfo {
  name: string;
  flag?: string;
  radioCount: number;
  x: number;
  y: number;
}

// Aylanish tezligi: gradus/soniya. Har kadrda emas, vaqtga bog'lab hisoblanadi,
// shunda tez va sekin qurilmalarda bir xil ko'rinadi.
const ROTATION_DEG_PER_SEC = 3;
// Aylanishni ~20 fps da yangilaymiz: 60 fps da butun xarita qayta chizilib,
// noutbuk ventilyatori ishlab ketadi va mobil batareya tez tugaydi.
const ROTATION_FRAME_MS = 50;
// Foydalanuvchi globusga tekkanidan keyin shuncha vaqt aylanmaydi
const RESUME_AFTER_INTERACTION_MS = 4000;

export default function GlobeMap({ countries, geojsonUrl, onUnsupported }: GlobeMapProps) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);
  const rotatingRef = useRef(true);
  const interactionUntilRef = useRef(0);
  const hoverRafRef = useRef<number | null>(null);

  const [isRotating, setIsRotating] = useState(true);
  const [hovered, setHovered] = useState<HoverInfo | null>(null);
  const [ready, setReady] = useState(false);

  const goToCountry = useCallback(
    (slug: string) => {
      if (slug) router.push(`/radio/${slug}`);
    },
    [router],
  );

  useEffect(() => {
    rotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    if (!containerRef.current) return;

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      rotatingRef.current = false;
      setIsRotating(false);
    }

    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style: {
          version: 8,
          // Projeksiya uslubda e'lon qilinadi — `load` hodisasini kutish shart emas
          projection: { type: 'globe' },
          sources: {
            countries: {
              type: 'geojson',
              // Jonli hisoblagichli GeoJSON. Oldin `public/countries.geojson`
              // o'qilardi va unda barcha radio_count = 0 edi — globus doim
              // bo'm-bo'sh ko'rinardi.
              data: geojsonUrl,
              // Barqaror id — har yuklashda o'zgaradigan generateId emas,
              // shunda feature-state (hover) to'g'ri ishlaydi
              promoteId: 'm49',
            },
          },
          sky: {
            'sky-color': '#05070d',
            'sky-horizon-blend': 0.6,
            'horizon-color': '#1a1f33',
            'horizon-fog-blend': 0.6,
            'fog-color': '#0a0f1c',
            'fog-ground-blend': 0.4,
            'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 0.9, 5, 0.4],
          },
          layers: [
            {
              // Globus sferasining "okeani"
              id: 'ocean',
              type: 'background',
              paint: { 'background-color': '#070a12' },
            },
            {
              id: 'countries-fill',
              type: 'fill',
              source: 'countries',
              paint: {
                // Chiziqli shkala ishlamaydi: bitta davlatda 2 ta, boshqasida
                // 500 ta stansiya bo'ladi va deyarli hamma joy bir xil qora
                // bo'lib qoladi. Shuning uchun bosqichli (step) shkala.
                'fill-color': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  '#ff2a4b',
                  [
                    'step',
                    ['coalesce', ['get', 'radio_count'], 0],
                    '#11141c',   // 0 — stansiya yo'q
                    1, '#2a1620',
                    5, '#4a1824',
                    20, '#7a1128',
                    50, '#b01228',
                    150, '#ff1a35',
                  ],
                ],
                'fill-opacity': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  0.95,
                  0.85,
                ],
              },
            },
            {
              id: 'countries-border',
              type: 'line',
              source: 'countries',
              paint: {
                'line-color': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  '#ffffff',
                  'rgba(180, 190, 215, 0.25)',
                ],
                'line-width': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  1.8,
                  0.5,
                ],
              },
            },
          ],
        },
        center: [64.5, 41.3],
        zoom: 1.7,
        minZoom: 1,
        maxZoom: 6,
        attributionControl: false,
      });
    } catch (err) {
      // WebGL yo'q yoki GPU kontekst bermadi — ro'yxatga tushamiz
      console.error('[globe] MapLibre ishga tushmadi:', err);
      onUnsupported?.();
      return;
    }

    mapRef.current = map;
    // Nosozlikni tekshirish uchun: ?debug=globe bilan ochilsa xarita
    // instansiyasi konsoldan ko'rinadi
    if (new URLSearchParams(window.location.search).get('debug') === 'globe') {
      (window as unknown as { __globeMap?: unknown }).__globeMap = map;
    }

    /*
      Yuklanish qoplamasini olib tashlash bitta hodisaga bog'lanmaydi.
      `load` ba'zi holatlarda umuman kelmaydi (uslub manbasi sekin, tab fonda,
      GPU kech tayyor) — bunday paytda qoplama ishlayotgan globusni butunlay
      yopib turardi. Shuning uchun uchta mustaqil signal bor.
    */
    const reveal = () => setReady(true);
    map.on('load', reveal);
    map.once('idle', reveal);
    const revealTimer = setTimeout(reveal, 4000);

    map.on('error', (e) => {
      // Manba yuklanmasa yoki uslubda xato bo'lsa — jim qolmaymiz
      console.error('[globe] xato:', e?.error?.message || e);
    });

    // --- Aylanish ---
    let timer: ReturnType<typeof setInterval> | null = null;
    let lastTick = performance.now();

    const tick = () => {
      const now = performance.now();
      const deltaSec = (now - lastTick) / 1000;
      lastTick = now;

      if (!rotatingRef.current || now < interactionUntilRef.current) return;
      if (document.hidden) return; // ko'rinmayotgan tabda ishlamaymiz

      const center = map.getCenter();
      center.lng += ROTATION_DEG_PER_SEC * deltaSec;
      map.setCenter(center);
    };

    timer = setInterval(tick, ROTATION_FRAME_MS);

    // Foydalanuvchi globusni ushlaganda aylanish to'xtaydi
    const pauseRotation = () => {
      interactionUntilRef.current = performance.now() + RESUME_AFTER_INTERACTION_MS;
    };
    map.on('mousedown', pauseRotation);
    map.on('touchstart', pauseRotation);
    map.on('wheel', pauseRotation);
    map.on('dragstart', pauseRotation);

    // --- Hover ---
    const clearHover = () => {
      if (hoveredIdRef.current !== null) {
        map.setFeatureState({ source: 'countries', id: hoveredIdRef.current }, { hover: false });
        hoveredIdRef.current = null;
      }
    };

    map.on('mousemove', 'countries-fill', (e) => {
      const feature = e.features?.[0];
      if (!feature) return;

      const id = feature.id ?? null;
      if (hoveredIdRef.current !== id) {
        clearHover();
        if (id !== null) {
          map.setFeatureState({ source: 'countries', id }, { hover: true });
          hoveredIdRef.current = id;
        }
      }
      map.getCanvas().style.cursor = 'crosshair';

      // React holatini har piksel harakatida emas, kadrga bir marta
      // yangilaymiz — aks holda render bo'roni bo'ladi
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      const props = feature.properties || {};
      const point = e.point;
      hoverRafRef.current = requestAnimationFrame(() => {
        setHovered({
          name: props.name_uz || props.name_en || '—',
          flag: props.flag_emoji,
          radioCount: Number(props.radio_count) || 0,
          x: point.x,
          y: point.y,
        });
      });
    });

    map.on('mouseleave', 'countries-fill', () => {
      clearHover();
      map.getCanvas().style.cursor = '';
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      setHovered(null);
    });

    // --- Bosish ---
    map.on('click', 'countries-fill', (e) => {
      const props = e.features?.[0]?.properties;
      // slug endi GeoJSON ichida keladi. Oldin u yo'q edi va nomdan yasalardi,
      // natijada ko'p davlatda 404 chiqardi.
      if (props?.slug) goToCountry(String(props.slug));
    });

    return () => {
      clearTimeout(revealTimer);
      if (timer) clearInterval(timer);
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      map.remove();
      mapRef.current = null;
    };
  }, [geojsonUrl, goToCountry]);

  return (
    <div className="relative w-full h-[calc(100vh-7rem)] min-h-[560px] bg-void-950 overflow-hidden select-none">
      <div ref={containerRef} className="w-full h-full" />

      {!ready ? (
        <div className="absolute inset-0 flex items-center justify-center bg-void-950">
          <div className="w-12 h-12 rounded-full border-2 border-crimson/20 border-t-crimson animate-spin" />
        </div>
      ) : null}

      <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-transparent via-transparent to-void-950/80" />

      <GlobeHUD
        isRotating={isRotating}
        onRotateToggle={() => setIsRotating((v) => !v)}
        onZoomIn={() => mapRef.current?.zoomIn({ duration: 300 })}
        onZoomOut={() => mapRef.current?.zoomOut({ duration: 300 })}
        onCountrySelect={goToCountry}
        quickCountries={countries}
      />

      {hovered ? (
        <div
          className="absolute z-30 pointer-events-none -translate-x-1/2 -translate-y-[calc(100%+12px)] px-3 py-2 tactical-box shadow-crimson-glow text-white"
          style={{ left: hovered.x, top: hovered.y }}
        >
          <div className="flex items-center gap-2">
            <span className="text-crimson font-mono font-bold text-sm">⌖</span>
            <span className="text-base">{hovered.flag || '🌍'}</span>
            <span className="text-xs font-mono font-bold tracking-wider uppercase">
              {hovered.name}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3 mt-1 pt-1 border-t border-void-700/80 font-mono text-[10px]">
            <span className="text-slate-400">STANSIYA:</span>
            <span className="text-crimson-bright font-bold">{hovered.radioCount}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
