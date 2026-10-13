import { Country, Channel, ChannelListResponse, PlayResponse } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export async function fetchCountries(limit: number = 250, hasStations: boolean = false): Promise<Country[]> {
  try {
    const res = await fetch(`${API_BASE}/countries?limit=${limit}&has_stations=${hasStations}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) throw new Error('Davlatlar ro\'yxatini olib bo\'lmadi');
    return await res.json();
  } catch (err) {
    console.error('fetchCountries error:', err);
    return [];
  }
}

export async function fetchCountryDetail(slug: string): Promise<Country | null> {
  try {
    const res = await fetch(`${API_BASE}/countries/${slug}`, {
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error(`fetchCountryDetail error for ${slug}:`, err);
    return null;
  }
}

export async function fetchCountryChannels(
  slug: string,
  options?: { sort?: string; tag?: string; lang?: string; limit?: number }
): Promise<ChannelListResponse> {
  try {
    const params = new URLSearchParams();
    if (options?.sort) params.set('sort', options.sort);
    if (options?.tag) params.set('tag', options.tag);
    if (options?.lang) params.set('lang', options.lang);
    if (options?.limit) params.set('limit', options.limit.toString());

    const res = await fetch(`${API_BASE}/countries/${slug}/channels?${params.toString()}`, {
      next: { revalidate: 600 },
    });
    if (!res.ok) return { total: 0, items: [] };
    return await res.json();
  } catch (err) {
    console.error(`fetchCountryChannels error for ${slug}:`, err);
    return { total: 0, items: [] };
  }
}

export async function fetchChannelDetail(slug: string): Promise<Channel | null> {
  try {
    const res = await fetch(`${API_BASE}/channels/${slug}`, {
      next: { revalidate: 600 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error(`fetchChannelDetail error for ${slug}:`, err);
    return null;
  }
}

export async function reportPlay(streamId: number): Promise<PlayResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/play`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stream_id: streamId }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('reportPlay error:', err);
    return null;
  }
}

export async function searchStations(q: string): Promise<{ countries: Country[]; stations: Channel[] }> {
  try {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) return { countries: [], stations: [] };
    return await res.json();
  } catch (err) {
    console.error('searchStations error:', err);
    return { countries: [], stations: [] };
  }
}
