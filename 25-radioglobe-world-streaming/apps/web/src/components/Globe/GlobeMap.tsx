'use client';

import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useRouter } from 'next/navigation';
import GlobeHUD from './GlobeHUD';
import { Country } from '@/types';

interface GlobeMapProps {
  countries: Country[];
}

export default function GlobeMap({ countries }: GlobeMapProps) {
  const router = useRouter();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [isRotating, setIsRotating] = useState(true);
  const [hoveredCountry, setHoveredCountry] = useState<{
    name: string;
    flag?: string;
    radioCount: number;
    x: number;
    y: number;
  } | null>(null);

  const hoveredStateIdRef = useRef<string | number | null>(null);
  const isRotatingRef = useRef(true);

  useEffect(() => {
    isRotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Create MapLibre map instance with Samolevsky monochrome/crimson theme
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          countries: {
            type: 'geojson',
            data: '/countries.geojson',
            generateId: true,
          },
        },
        layers: [
          {
            id: 'background',
            type: 'background',
            paint: {
              'background-color': '#030305',
            },
          },
          {
            id: 'countries-fill',
            type: 'fill',
            source: 'countries',
            paint: {
              'fill-color': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                '#ff2a4b', // Electric crimson on hover
                [
                  'interpolate',
                  ['linear'],
                  ['coalesce', ['get', 'radio_count'], 0],
                  0, '#0a0b10',       // Deep void dark
                  1, '#1a1820',       // Dark graphite
                  10, '#801020',      // Muted crimson
                  30, '#ff1a35',      // High-vis broadcast red
                ],
              ],
              'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.95,
                0.8,
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
                '#4a4d5e',
              ],
              'line-width': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                2,
                0.6,
              ],
              'line-opacity': 0.85,
            },
          },
        ],
      },
      center: [64.5, 41.3], // Central Asia / Uzbekistan
      zoom: 1.7,
      maxZoom: 6,
      minZoom: 1,
    });

    mapRef.current = map;

    // Set globe projection
    map.on('load', () => {
      try {
        (map as any).setProjection({ type: 'globe' });
      } catch (e) {
        console.warn('MapLibre globe projection notice:', e);
      }
    });

    // Auto-rotate globe
    let animationFrameId: number;
    const rotateGlobe = () => {
      if (isRotatingRef.current && map) {
        const center = map.getCenter();
        center.lng = (center.lng + 0.1) % 360;
        map.setCenter(center);
      }
      animationFrameId = requestAnimationFrame(rotateGlobe);
    };
    animationFrameId = requestAnimationFrame(rotateGlobe);

    // Hover interactions
    map.on('mousemove', 'countries-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const feature = e.features[0];
        const featureId = feature.id;
        const props = feature.properties || {};

        if (hoveredStateIdRef.current !== null && hoveredStateIdRef.current !== featureId) {
          map.setFeatureState(
            { source: 'countries', id: hoveredStateIdRef.current },
            { hover: false }
          );
        }

        hoveredStateIdRef.current = featureId ?? null;
        if (featureId !== undefined) {
          map.setFeatureState(
            { source: 'countries', id: featureId },
            { hover: true }
          );
        }

        map.getCanvas().style.cursor = 'crosshair';

        setHoveredCountry({
          name: props.name_uz || props.name_en || 'Sector',
          flag: props.flag_emoji,
          radioCount: props.radio_count || 0,
          x: e.point.x,
          y: e.point.y,
        });
      }
    });

    map.on('mouseleave', 'countries-fill', () => {
      if (hoveredStateIdRef.current !== null) {
        map.setFeatureState(
          { source: 'countries', id: hoveredStateIdRef.current },
          { hover: false }
        );
      }
      hoveredStateIdRef.current = null;
      map.getCanvas().style.cursor = '';
      setHoveredCountry(null);
    });

    // Click interaction
    map.on('click', 'countries-fill', (e) => {
      if (e.features && e.features.length > 0) {
        const props = e.features[0].properties || {};
        const slug = props.slug || (props.name_en ? props.name_en.toLowerCase().replace(/\s+/g, '-') : '');
        if (slug) {
          router.push(`/radio/${slug}`);
        }
      }
    });

    return () => {
      cancelAnimationFrame(animationFrameId);
      map.remove();
    };
  }, [router]);

  const handleRotateToggle = () => {
    setIsRotating(!isRotating);
  };

  const handleZoomIn = () => {
    if (mapRef.current) mapRef.current.zoomIn({ duration: 300 });
  };

  const handleZoomOut = () => {
    if (mapRef.current) mapRef.current.zoomOut({ duration: 300 });
  };

  const handleCountrySelect = (slug: string) => {
    router.push(`/radio/${slug}`);
  };

  return (
    <div className="relative w-full h-[calc(100vh-60px)] min-h-[620px] bg-void-950 overflow-hidden select-none">
      {/* 3D Map canvas container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Atmospheric radial vignette */}
      <div className="absolute inset-0 pointer-events-none bg-radial from-transparent via-transparent to-void-950/90" />

      {/* Samolevsky HUD overlay (Orbital rings, Broadcast badge, Equalizer spectrum) */}
      <GlobeHUD
        isRotating={isRotating}
        onRotateToggle={handleRotateToggle}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onCountrySelect={handleCountrySelect}
        quickCountries={countries}
      />

      {/* Tactical hover crosshair callout */}
      {hoveredCountry && (
        <div
          className="absolute z-30 pointer-events-none -translate-x-1/2 -translate-y-full mb-3 px-3 py-2 rounded-none tactical-box shadow-crimson-glow text-white animate-in fade-in zoom-in-95 duration-100"
          style={{ left: `${hoveredCountry.x}px`, top: `${hoveredCountry.y}px` }}
        >
          <div className="flex items-center gap-2">
            <span className="text-crimson font-mono font-bold text-sm">⌖</span>
            <span className="text-base">{hoveredCountry.flag || '🌍'}</span>
            <span className="text-xs font-mono font-bold tracking-wider uppercase">
              {hoveredCountry.name}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3 mt-1 pt-1 border-t border-void-700/80 font-mono text-[10px]">
            <span className="text-slate-400">SIGNALS:</span>
            <span className="text-crimson-bright font-bold">
              {hoveredCountry.radioCount} NODES
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
