export interface Country {
  iso2: string;
  iso3: string;
  m49: number;
  name_uz: string;
  name_en: string;
  slug: string;
  continent: string;
  flag_emoji?: string;
  radio_count: number;
  tv_count: number;
  centroid?: [number, number];        // [lat, lon]
  bbox?: [number, number, number, number];
  top_tags?: string[];
  languages?: string[];
}

export interface StreamInfo {
  id: number;
  format?: string;
  bitrate?: number | null;
  is_https: boolean;
  needs_proxy: boolean;
  score: number;
  play_url?: string;
}

export interface Channel {
  id: number;
  type: 'radio' | 'tv';
  slug: string;
  name: string;
  logo_url?: string | null;
  homepage?: string | null;
  tags: string[];
  languages: string[];
  bitrate?: number | null;
  score: number;
  popularity?: number;
  primary_stream?: StreamInfo | null;
  /** Birinchi oqim ishlamasa navbat bilan sinaladigan zaxiralar */
  fallback_streams?: StreamInfo[];
  streams?: StreamInfo[];
  country_iso2?: string | null;
}

export interface ChannelListResponse {
  /** Bazadagi umumiy son — sahifadagi elementlar soni emas */
  total: number;
  items: Channel[];
  /** Keyset kursori (opaque satr) */
  next_cursor?: string | null;
}

export interface PlayResponse {
  stream_id: number;
  station_name: string;
  play_url: string;
  is_proxied: boolean;
  format?: string;
}

export interface SearchResponse {
  query: string;
  countries: Country[];
  stations: Channel[];
}

export type CountryCounts = Record<string, { radio: number; tv: number }>;
