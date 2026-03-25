export interface TrackedAnime {
  id: number;
  anime_id: number;
  anime_slug: string;
  anime_title: string;
  cover_url: string | null;
  source_site: string;
  last_known_episode: number;
  enabled: boolean;
  check_interval_minutes: number;
  last_checked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrackAnimeRequest {
  anime_id: number;
  anime_slug: string;
  anime_title: string;
  cover_url?: string | null;
  genres?: string[];
  plot?: string | null;
  year?: string | null;
  source_site?: string;
  check_interval_minutes?: number;
}

export interface TrackedAnimeUpdate {
  enabled?: boolean;
  check_interval_minutes?: number;
}

export interface TrackedListResponse {
  tracked: TrackedAnime[];
}
