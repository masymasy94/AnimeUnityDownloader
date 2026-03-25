import type { Settings, SettingsUpdate } from '../types/settings';
import { apiFetch } from './client';

export function getSettings(): Promise<Settings> {
  return apiFetch<Settings>('/settings');
}

export function updateSettings(update: SettingsUpdate): Promise<Settings> {
  return apiFetch<Settings>('/settings', {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}
