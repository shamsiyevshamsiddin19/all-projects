'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useRouter } from 'next/navigation';

import GlobeHUD from '@/components/Globe/GlobeHUD';
import { fetchRandomStation } from '@/lib/api';
import { usePlayerStore } from '@/stores/playerStore';
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
const ROTATION_DEG_PER_SEC = 2.5;
// ~20 fps yetarli: 60 fps da butun xarita qayta chizilib, noutbuk ventilyatori
// ishlab ketadi va mobil batareya tez tugaydi
const ROTATION_FRAME_MS = 50;
// Teginishdan keyin (touchend) aylanish darhol emas, bir oz keyin qaytadi —
// aks holda bosish/qisqa sudrash tugashi bilan globus foydalanuvchi barmog'i
// ostidayoq sirpanib keta boshlaydi
const RESUME_AFTER_TOUCH_MS = 1200;

export default function GlobeMap({ countries, geojsonUrl, onUnsupported }: GlobeMapProps) {
  const router = useRouter();
  const playStation = usePlayerStore((s) => s.playStation);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);
  const rotatingRef = useRef(true);
  const hoverRafRef = useRef<number | null>(null);
  /*
    Avtomatik aylanishni VAQTGA EMAS, SICHQONCHA/BARMOQ HOLATIGA qarab
    to'xtatamiz: foydalanuvchi globus ustida ("pointerInside") yoki uni
    sudrayotgan bo'lsa ("dragging"), aylanish darhol to'xtaydi va faqat
    ikkisi ham yo'qolgandan keyin qayta boshlanadi.

    Oldin bu "5 soniya kutish" (vaqt asosida) qilingan edi — bu ikkita
    muammoga olib kelardi: (1) foydalanuvchi sudrab turganda ham interval
    globusni O'ZINING joyiga surib, haqiqiy sudrash bilan "kurashardi";
    (2) globus avtomatik aylanganda sichqoncha qimirlamagani uchun
    hover tooltipi 'mousemove' kelmaguncha ESKI joyida qotib qolardi —
    natijada davlat nomi globusdan "uzoqda osilib" qolgandek ko'rinardi.
  */
  const pointerInsideRef = useRef(false);
  const draggingRef = useRef(false);
  const touchResumeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [isRotating, setIsRotating] = useState(true);
  const [hovered, setHovered] = useState<HoverInfo | null>(null);
  const [ready, setReady] = useState(false);
  const [isRandomLoading, setRandomLoading] = useState(false);

  const goToCountry = useCallback(
    (slug: string) => {
      if (slug) router.push(`/radio/${slug}`);
    },
    [router],
  );

  const handleRandom = useCallback(async () => {
    setRandomLoading(true);
    try {
      const station = await fetchRandomStation();
      if (station) playStation(station);
    } finally {
      setRandomLoading(false);
    }
  }, [playStation]);

  useEffect(() => {
    rotatingRef.current = isRotating;
  }, [isRotating]);

  useEffect(() => {
    if (!containerRef.current) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
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
              // Jonli hisoblagichli GeoJSON (statik fayl emas — undagi
              // barcha radio_count nol edi)
              data: geojsonUrl,
              // Barqaror id: generateId har yuklashda o'zgaradi va
              // feature-state (hover) ishlamay qoladi
              promoteId: 'm49',
            },
          },
          sky: {
            'sky-color': '#06070d',
            'sky-horizon-blend': 0.5,
            'horizon-color': '#151824',
            'horizon-fog-blend': 0.6,
            'fog-color': '#0a0c14',
            'fog-ground-blend': 0.3,
            'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 0.85, 5, 0.3],
          },
          layers: [
            {
              // Globus sferasining "okeani"
              id: 'ocean',
              type: 'background',
              paint: { 'background-color': '#0a0c14' },
            },
            {
              id: 'countries-fill',
              type: 'fill',
              source: 'countries',
              paint: {
                /*
                  Chiziqli shkala bu ma'lumotga mos kelmaydi: bir davlatda 2 ta,
                  boshqasida 500 ta stansiya bor. Chiziqli bo'lsa deyarli hamma
                  joy bir xil qora bo'lib qolardi. Shuning uchun bosqichli
                  (step) shkala — har bosqich ko'zga seziladi.
                */
                'fill-color': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  '#ff5276',
                  [
                    'step',
                    ['coalesce', ['get', 'radio_count'], 0],
                    '#12141d',   // stansiya yo'q — fondan deyarli farq qilmaydi
                    1, '#2b1a26',
                    5, '#45192c',
                    20, '#6d1d38',
                    60, '#9c2145',
                    150, '#d32752',
                    350, '#ff3d63',
                  ],
                ],
                'fill-opacity': 1,
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
                  'rgba(233, 235, 242, 0.14)',
                ],
                'line-width': [
                  'case',
                  ['boolean', ['feature-state', 'hover'], false],
                  1.5,
                  0.4,
                ],
              },
            },
          ],
        },
        center: [64.5, 41.3],
        zoom: 1.75,
        minZoom: 1,
        maxZoom: 6,
        attributionControl: false,
        /*
          G'ildirak bilan zoom O'CHIRILGAN. Globus sahifaning bir bo'lagi,
          shuning uchun u sichqoncha g'ildiragini o'ziga olsa, foydalanuvchi
          sahifani pastga aylantira olmay qoladi — quyidagi davlatlar
          katalogiga umuman yetib bormaydi. Zoom uchun +/− tugmalari bor.
        */
        scrollZoom: false,
        /*
          Sichqoncha bilan sudrab aylantirish — ANIQ yoqilgan (MapLibre
          standarti ham yoqiq, lekin buni qasddan yozib qo'yamiz: kodni
          o'qigan kishi "nega aylanmayapti" deb o'ylab tekshirmasin).

          dragRotate (o'ng tugma yoki Ctrl+sudrash bilan kamera burchagini
          — pitch/bearing — o'zgartirish) ATAYLAB o'chirilgan: bu globusni
          "yon tomondan" yoki "teskari" qilib ko'rsatib yuborishi mumkin,
          foydalanuvchi esa buni tasodifan bosib, globus "buzilib qoldi"
          deb o'ylashi mumkin. Bizga faqat tekis aylanish (lng/lat bo'ylab
          sudrash) kerak, uni dragPan allaqachon beradi.
        */
        dragPan: true,
        dragRotate: false,
        pitchWithRotate: false,
        touchZoomRotate: true,
        touchPitch: false,
      });

      // touchZoomRotate'da ham burilish (bearing) o'chiriladi — ikki barmoq
      // bilan burab yuborish mobil foydalanuvchini ham chalkashtiradi
      map.touchZoomRotate.disableRotation();
    } catch (err) {
      // WebGL yo'q yoki GPU kontekst bermadi — ro'yxatga tushamiz
      console.error('[globe] MapLibre ishga tushmadi:', err);
      onUnsupported?.();
      return;
    }

    mapRef.current = map;

    /*
      Yuklanish qoplamasini olib tashlash bitta hodisaga bog'lanmaydi.
      `load` ba'zan umuman kelmaydi (tab fonda bo'lsa requestAnimationFrame
      to'xtaydi, MapLibre esa uslubni aynan shu orqali yuklaydi) — bunday
      paytda qoplama ishlayotgan globusni butunlay yopib turardi.
    */
    const reveal = () => setReady(true);
    map.on('load', reveal);
    map.once('idle', reveal);
    const revealTimer = setTimeout(reveal, 4000);

    map.on('error', (e) => {
      console.error('[globe] xato:', e?.error?.message || e);
    });

    /*
      Kursor: globus "ushlab sudrash mumkin" ekanini ko'rsatadi.

      Boshlang'ich holat — "grab" (qo'l). Sudrash boshlanganda "grabbing"ga
      o'tadi, tugaganda yana "grab"ga qaytadi. Davlat ustida esa "pointer"
      (bosish mumkin). Busiz sichqoncha oddiy strelka bo'lib qolaveradi va
      foydalanuvchi globusni sudrab bo'lishini sezmasligi mumkin edi.
    */
    map.getCanvas().style.cursor = 'grab';

    // ── Hover (aylanish/drag handlerlaridan OLDIN e'lon qilinadi — ular
    //    sudrash boshlanganda tooltipni tozalash uchun shuni chaqiradi) ──
    const clearHover = () => {
      if (hoveredIdRef.current !== null) {
        map.setFeatureState({ source: 'countries', id: hoveredIdRef.current }, { hover: false });
        hoveredIdRef.current = null;
      }
    };

    // ── Aylanish: faqat sichqoncha/barmoq globusda BO'LMAGANDA ishlaydi ──
    const canRotateNow = () =>
      rotatingRef.current &&
      !pointerInsideRef.current &&
      !draggingRef.current &&
      !document.hidden;

    let lastTick = performance.now();
    const timer = setInterval(() => {
      const now = performance.now();
      const deltaSec = (now - lastTick) / 1000;
      lastTick = now;

      if (!canRotateNow()) return;

      const center = map.getCenter();
      center.lng += ROTATION_DEG_PER_SEC * deltaSec;
      map.setCenter(center);
    }, ROTATION_FRAME_MS);

    const clearTouchResumeTimer = () => {
      if (touchResumeTimerRef.current !== null) {
        clearTimeout(touchResumeTimerRef.current);
        touchResumeTimerRef.current = null;
      }
    };

    // Sichqoncha: globusga kirganda aylanish to'xtaydi, chiqqanda qaytadi
    const canvas = map.getCanvas();
    const onPointerEnter = () => {
      pointerInsideRef.current = true;
    };
    const onPointerLeave = () => {
      pointerInsideRef.current = false;
      if (!draggingRef.current) map.getCanvas().style.cursor = 'grab';
    };
    canvas.addEventListener('mouseenter', onPointerEnter);
    canvas.addEventListener('mouseleave', onPointerLeave);

    // Teginish: boshlanganda to'xtaydi, tugaganda BIROZDAN KEYIN qaytadi —
    // aks holda bosish tugashi bilanoq globus barmoq ostida sirpanib ketadi
    const onTouchStart = () => {
      clearTouchResumeTimer();
      pointerInsideRef.current = true;
    };
    const onTouchEnd = () => {
      clearTouchResumeTimer();
      touchResumeTimerRef.current = setTimeout(() => {
        pointerInsideRef.current = false;
      }, RESUME_AFTER_TOUCH_MS);
    };
    canvas.addEventListener('touchstart', onTouchStart, { passive: true });
    canvas.addEventListener('touchend', onTouchEnd, { passive: true });
    canvas.addEventListener('touchcancel', onTouchEnd, { passive: true });

    map.on('dragstart', () => {
      draggingRef.current = true;
      map.getCanvas().style.cursor = 'grabbing';
      /*
        Sudrash boshlanishi bilan tooltip tozalanadi. Aks holda sudrash
        tugaganda, agar yangi 'mousemove' hali kelmagan bo'lsa, tooltip
        ESKI davlat nomi bilan YANGI (noto'g'ri) joyda osilib qolaveradi —
        chunki globus siljidi, lekin ko'rsatilgan matn hali eski.
      */
      clearHover();
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      setHovered(null);
    });
    map.on('dragend', () => {
      draggingRef.current = false;
      // Keyingi 'mousemove' cursor'ni (pointer/grab) to'g'ri hisoblab beradi;
      // bu yerda faqat "grabbing"dan chiqib ketishni kafolatlaymiz
      map.getCanvas().style.cursor = 'grab';
    });

    // ── Hover ──

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

      const props = feature.properties || {};
      const hasStations = Number(props.radio_count) > 0;
      // Stansiyasi bor davlat — bosish mumkin (pointer). Qolgani — baribir
      // sudrab aylantirish mumkin, shuning uchun 'default' emas 'grab'.
      map.getCanvas().style.cursor = hasStations ? 'pointer' : 'grab';

      // React holatini har piksel harakatida emas, kadrga bir marta
      // yangilaymiz — aks holda render bo'roni bo'ladi
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
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
      map.getCanvas().style.cursor = 'grab';
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      setHovered(null);
    });

    // ── Bosish ──
    map.on('click', 'countries-fill', (e) => {
      const props = e.features?.[0]?.properties;
      // Stansiyasi yo'q davlatga o'tish — bo'sh sahifa, foydasi yo'q
      if (!props?.slug || Number(props.radio_count) === 0) return;
      goToCountry(String(props.slug));
    });

    return () => {
      clearTimeout(revealTimer);
      clearInterval(timer);
      clearTouchResumeTimer();
      canvas.removeEventListener('mouseenter', onPointerEnter);
      canvas.removeEventListener('mouseleave', onPointerLeave);
      canvas.removeEventListener('touchstart', onTouchStart);
      canvas.removeEventListener('touchend', onTouchEnd);
      canvas.removeEventListener('touchcancel', onTouchEnd);
      if (hoverRafRef.current !== null) cancelAnimationFrame(hoverRafRef.current);
      map.remove();
      mapRef.current = null;
    };
  }, [geojsonUrl, goToCountry, onUnsupported]);

  const withStations = countries.filter((c) => c.radio_count > 0);

  return (
    <div className="relative h-[60vh] min-h-[420px] xl:h-full w-full overflow-hidden bg-ink-950">
      <div ref={containerRef} className="h-full w-full" />

      {!ready ? (
        <div className="absolute inset-0 flex items-center justify-center bg-ink-950">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-ink-700 border-t-signal" />
        </div>
      ) : null}

      <GlobeHUD
        isRotating={isRotating}
        onRotateToggle={() => setIsRotating((v) => !v)}
        onZoomIn={() => mapRef.current?.zoomIn({ duration: 300 })}
        onZoomOut={() => mapRef.current?.zoomOut({ duration: 300 })}
        onRandom={handleRandom}
        isRandomLoading={isRandomLoading}
        topCountries={withStations.slice(0, 6)}
      />

      {hovered ? (
        <div
          className="pointer-events-none absolute z-30 -translate-x-1/2 -translate-y-[calc(100%+14px)]"
          style={{ left: hovered.x, top: hovered.y }}
        >
          <div className="panel whitespace-nowrap px-3 py-2">
            <div className="flex items-center gap-2">
              <span aria-hidden="true">{hovered.flag || '🌐'}</span>
              <span className="text-sm font-medium text-text-primary">{hovered.name}</span>
            </div>
            <p className="mt-0.5 text-xs text-text-muted">
              {hovered.radioCount > 0
                ? `${hovered.radioCount} ta stansiya`
                : 'Stansiya topilmadi'}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
