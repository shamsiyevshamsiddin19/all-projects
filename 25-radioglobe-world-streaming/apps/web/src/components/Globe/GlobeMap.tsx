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

    // Create MapLibre map instance
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
              'background-color': '#040711',
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
                '#00f2fe',
                [
                  'interpolate',
                  ['linear'],
                  ['coalesce', ['get', 'radio_count'], 0],
                  0, '#0c1527',
                  1, '#13284c',
                  10, '#0284c7',
                  30, '#00f2fe',
                ],
              ],
              'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.9,
                0.75,
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
                '#38bdf8',
              ],
              'line-width': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                2,
                0.6,
              ],
              'line-opacity': 0.8,
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
        // MapLibre GL v5 Globe projection
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
        center.lng = (center.lng + 0.12) % 360;
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

        map.getCanvas().style.cursor = 'pointer';

        setHoveredCountry({
          name: props.name_uz || props.name_en || 'Davlat',
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
    <div className="relative w-full h-[calc(100vh-60px)] min-h-[580px] bg-space-950 overflow-hidden select-none">
      {/* 3D Map canvas container */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Cyber atmospheric overlay */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-transparent via-transparent to-space-950/80" />

      {/* Futuristic HUD overlay */}
      <GlobeHUD
        isRotating={isRotating}
        onRotateToggle={handleRotateToggle}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onCountrySelect={handleCountrySelect}
        quickCountries={countries}
      />

      {/* Hover cyber tooltip */}
      {hoveredCountry && (
        <div
          className="absolute z-30 pointer-events-none -translate-x-1/2 -translate-y-full mb-3 px-3 py-2 rounded-xl bg-space-900/90 backdrop-blur-md border border-cyan-400/50 shadow-cyan-glow text-white animate-in fade-in zoom-in-95 duration-100"
          style={{ left: `${hoveredCountry.x}px`, top: `${hoveredCountry.y}px` }}
        >
          <div className="flex items-center gap-2">
            <span className="text-base">{hoveredCountry.flag || '🌍'}</span>
            <span className="text-xs font-bold tracking-tight">{hoveredCountry.name}</span>
          </div>
          <p className="text-[10px] font-mono text-cyan-300 mt-0.5">
            {hoveredCountry.radioCount} ta radiostansiya
          </p>
        </div>
      )}
    </div>
  );
}
