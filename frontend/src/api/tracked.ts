import type { TrackAnimeRequest, TrackedAnime, TrackedAnimeUpdate, TrackedListResponse } from '../types/tracked';
import { apiFetch } from './client';

export function getTrackedAnimes(): Promise<TrackedListResponse> {
  return apiFetch<TrackedListResponse>('/tracked');
}

export function trackAnime(request: TrackAnimeRequest): Promise<TrackedAnime> {
  return apiFetch<TrackedAnime>('/tracked', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export function untrackAnime(id: number): Promise<void> {
  return apiFetch<void>(`/tracked/${id}`, { method: 'DELETE' });
}

export function updateTracking(id: number, update: TrackedAnimeUpdate): Promise<TrackedAnime> {
  return apiFetch<TrackedAnime>(`/tracked/${id}`, {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}

export function checkNow(id: number): Promise<{ new_episodes: number }> {
  return apiFetch<{ new_episodes: number }>(`/tracked/${id}/check`, { method: 'POST' });
}

export function checkTrackedStatus(animeId: number, sourceSite = 'animeunity'): Promise<{ tracked: boolean; id?: number }> {
  return apiFetch<{ tracked: boolean; id?: number }>(`/tracked/check-status?anime_id=${animeId}&source_site=${encodeURIComponent(sourceSite)}`);
}
