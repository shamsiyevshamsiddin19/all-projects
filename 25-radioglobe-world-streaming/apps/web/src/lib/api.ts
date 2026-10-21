import type {
  Channel,
  ChannelListResponse,
  Country,
  CountryCounts,
  HomeStats,
  PlayResponse,
  SearchResponse,
} from '@/types';

/**
 * Server tomonidan (SSR/ISR) chaqirilganda ichki tarmoq manzili ishlatiladi —
 * konteyner ichidan tashqi domenga chiqish shart emas va build paytida ham
 * ishlaydi. Brauzerda esa ommaviy manzil kerak.
 */
const SERVER_BASE =
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:8000/api/v1';

const BROWSER_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

const API_BASE = typeof window === 'undefined' ? SERVER_BASE : BROWSER_BASE;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface RequestOptions extends RequestInit {
  /** ISR qayta generatsiya oralig'i (soniya). 0 = keshlanmaydi. */
  revalidate?: number;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { revalidate, ...init } = options;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    ...(revalidate === 0
      ? { cache: 'no-store' as const }
      : revalidate !== undefined
        ? { next: { revalidate } }
        : {}),
  });

  if (!res.ok) {
    let code: string | undefined;
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      code = body?.error?.code;
      message = body?.error?.message || message;
    } catch {
      /* javob JSON emas — standart xabar qoladi */
    }
    throw new ApiError(message, res.status, code);
  }

  return res.json() as Promise<T>;
}

/**
 * Sahifa qulab tushmasligi uchun zaxira qiymat qaytaradi, LEKIN xatoni
 * albatta logga yozadi.
 *
 * Oldin bu yerda jim `catch { return [] }` bor edi: build paytida API ga
 * ulanib bo'lmaganda sahifa bo'sh ro'yxat bilan prerender bo'lib muzlab
 * qolgandi va bosh sahifada "JAMI SEKTORLAR: 0" yozilib turgandi. Endi xato
 * ko'rinadi va chaqiruvchi uni ajrata oladi.
 */
async function safe<T>(label: string, fn: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await fn();
  } catch (err) {
    const detail = err instanceof ApiError ? `${err.status} ${err.message}` : String(err);
    console.error(`[api] ${label} bajarilmadi: ${detail}`);
    return fallback;
  }
}

export function fetchCountries(limit = 300, hasStations = false): Promise<Country[]> {
  return safe(
    'fetchCountries',
    () =>
      request<Country[]>(`/countries?limit=${limit}&has_stations=${hasStations}`, {
        revalidate: 600,
      }),
    [],
  );
}

export function fetchCountryDetail(slug: string): Promise<Country | null> {
  return safe(
    `fetchCountryDetail(${slug})`,
    () => request<Country>(`/countries/${encodeURIComponent(slug)}`, { revalidate: 600 }),
    null,
  );
}

export function fetchCountryChannels(
  slug: string,
  options: { sort?: string; tag?: string; lang?: string; limit?: number; cursor?: string } = {},
): Promise<ChannelListResponse> {
  const params = new URLSearchParams();
  if (options.sort) params.set('sort', options.sort);
  if (options.tag) params.set('tag', options.tag);
  if (options.lang) params.set('lang', options.lang);
  params.set('limit', String(options.limit ?? 60));
  if (options.cursor) params.set('cursor', options.cursor);

  return safe(
    `fetchCountryChannels(${slug})`,
    () =>
      request<ChannelListResponse>(
        `/countries/${encodeURIComponent(slug)}/channels?${params}`,
        // Javobda imzolangan play_url bor — keshlanmaydi
        { revalidate: 0 },
      ),
    { total: 0, items: [] },
  );
}

export function fetchChannelDetail(slug: string): Promise<Channel | null> {
  return safe(
    `fetchChannelDetail(${slug})`,
    () => request<Channel>(`/channels/${encodeURIComponent(slug)}`, { revalidate: 0 }),
    null,
  );
}

export function fetchMapCounts(): Promise<CountryCounts> {
  return safe('fetchMapCounts', () => request<CountryCounts>('/map/counts', { revalidate: 600 }), {});
}

export function searchStations(q: string, signal?: AbortSignal): Promise<SearchResponse> {
  return safe(
    `searchStations(${q})`,
    () =>
      request<SearchResponse>(`/search?q=${encodeURIComponent(q)}`, {
        revalidate: 0,
        signal,
      }),
    { query: q, countries: [], stations: [] },
  );
}

/**
 * Ijro hodisasini qayd etadi (hisoblagich + radio-browser'ga klik qaytarish).
 *
 * MUHIM: bu chaqiruv ijroni BOSHLAMAYDI va ijro uchun kutilmaydi. Audio
 * foydalanuvchi bosgan zahoti, bosish hodisasining o'z ichida ishga tushadi —
 * aks holda mobil brauzerlarning autoplay siyosati ijroni bloklaydi.
 */
export function reportPlay(streamId: number): Promise<PlayResponse | null> {
  return safe(
    'reportPlay',
    () =>
      request<PlayResponse>('/play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stream_id: streamId }),
        revalidate: 0,
        keepalive: true,
      }),
    null,
  );
}

/** Bosh sahifadagi raqamlar uchun yagona manba — hammasi bazadan. */
export function fetchStats(): Promise<HomeStats> {
  return safe(
    'fetchStats',
    () => request<HomeStats>('/stats', { revalidate: 300 }),
    { stations: 0, countries: 0, top_genres: [], top_countries: [] },
  );
}

/** Tasodifiy stansiya. Javobda imzolangan play_url bor — keshlanmaydi. */
export function fetchRandomStation(tag?: string): Promise<Channel | null> {
  const query = tag ? `?tag=${encodeURIComponent(tag)}` : '';
  return safe(
    'fetchRandomStation',
    () => request<Channel>(`/random${query}`, { revalidate: 0 }),
    null,
  );
}

/** Janr bo'yicha global ro'yxat (barcha davlatlar kesimida). */
export function fetchChannelsByTag(tag: string, limit = 60): Promise<ChannelListResponse> {
  return safe(
    `fetchChannelsByTag(${tag})`,
    () =>
      request<ChannelListResponse>(
        `/channels?tag=${encodeURIComponent(tag)}&limit=${limit}`,
        { revalidate: 0 },
      ),
    { total: 0, items: [] },
  );
}
