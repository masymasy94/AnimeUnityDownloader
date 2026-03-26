export interface AnimeSearchResult {
  id: number;
  slug: string;
  title: string;
  title_eng: string | null;
  cover_url: string | null;
  type: string | null;
  year: string | null;
  episodes_count: number | null;
  genres: string[];
  dub: boolean;
  source_site: string;
}

export interface AnimeDetail {
  id: number;
  slug: string;
  title: string;
  title_eng: string | null;
  cover_url: string | null;
  banner_url: string | null;
  plot: string | null;
  type: string | null;
  year: string | null;
  episodes_count: number | null;
  genres: string[];
  status: string | null;
  dub: boolean;
  source_site: string;
}

export interface Episode {
  id: number;
  number: string;
  title: string | null;
  created_at: string | null;
  views: number | null;
  download_status: string | null;
}

export interface EpisodesResponse {
  episodes: Episode[];
  total: number;
  has_more: boolean;
}

export interface SearchResponse {
  results: AnimeSearchResult[];
}
