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
  centroid?: [number, number];
  bbox?: [number, number, number, number];
  top_tags?: string[];
  languages?: string[];
}

export interface StreamInfo {
  id: number;
  format?: string;
  bitrate?: number;
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
  logo_url?: string;
  homepage?: string;
  tags: string[];
  languages: string[];
  bitrate?: number;
  score: number;
  popularity?: number;
  primary_stream?: StreamInfo;
  streams?: StreamInfo[];
}

export interface ChannelListResponse {
  total: number;
  items: Channel[];
  next_cursor?: number;
}

export interface PlayResponse {
  stream_id: number;
  station_name: string;
  play_url: string;
  is_proxied: boolean;
  format?: string;
}
