import type { AnimeDetail, EpisodesResponse } from '../types/anime';
import { apiFetch } from './client';

export function getAnimeDetail(id: number, slug: string, site = 'animeunity'): Promise<AnimeDetail> {
  return apiFetch<AnimeDetail>(`/anime/${id}-${slug}?site=${encodeURIComponent(site)}`);
}

export function getEpisodes(
  id: number,
  slug: string,
  start: number = 1,
  end?: number,
  site = 'animeunity',
): Promise<EpisodesResponse> {
  const params = new URLSearchParams({ start: String(start), site });
  if (end) params.set('end', String(end));
  return apiFetch<EpisodesResponse>(`/anime/${id}-${slug}/episodes?${params}`);
}
