import type { SearchResponse } from '../types/anime';
import { apiFetch } from './client';

export function searchAnime(title: string, site = 'animeunity'): Promise<SearchResponse> {
  const params = new URLSearchParams({ title, site });
  return apiFetch<SearchResponse>(`/search?${params}`);
}

export function getLatestAnime(site = 'animeunity'): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/latest?site=${encodeURIComponent(site)}`);
}
