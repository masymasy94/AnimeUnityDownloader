import type { AnimeDetail, EpisodesResponse } from '../types/anime';
import { apiFetch } from './client';

export function getAnimeDetail(id: number, slug: string): Promise<AnimeDetail> {
  return apiFetch<AnimeDetail>(`/anime/${id}-${slug}`);
}

export function getEpisodes(
  id: number,
  slug: string,
  start: number = 1,
  end?: number,
): Promise<EpisodesResponse> {
  const params = new URLSearchParams({ start: String(start) });
  if (end) params.set('end', String(end));
  return apiFetch<EpisodesResponse>(`/anime/${id}-${slug}/episodes?${params}`);
}
