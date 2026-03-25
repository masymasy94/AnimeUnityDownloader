import { apiFetch } from './client';

export interface Site {
  id: string;
  name: string;
}

export interface SitesResponse {
  sites: Site[];
}

export function getSites(): Promise<SitesResponse> {
  return apiFetch<SitesResponse>('/sites');
}
