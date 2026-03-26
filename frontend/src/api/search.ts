import type { SearchResponse } from '../types/anime';
import { apiFetch } from './client';

export function searchAnime(title: string): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/search?title=${encodeURIComponent(title)}`);
}

export function getLatestAnime(): Promise<SearchResponse> {
  return apiFetch<SearchResponse>('/latest');
}
