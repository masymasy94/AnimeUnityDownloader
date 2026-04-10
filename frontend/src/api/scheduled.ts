import type {
  CronValidationResponse,
  RunNowResponse,
  ScheduleCreateRequest,
  ScheduleListResponse,
  ScheduleUpdateRequest,
  ScheduledDownload,
} from '../types/scheduled';
import { apiFetch } from './client';

export function listSchedules(): Promise<ScheduleListResponse> {
  return apiFetch<ScheduleListResponse>('/scheduled');
}

export function createSchedule(
  request: ScheduleCreateRequest,
): Promise<ScheduledDownload> {
  return apiFetch<ScheduledDownload>('/scheduled', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export function updateSchedule(
  id: number,
  update: ScheduleUpdateRequest,
): Promise<ScheduledDownload> {
  return apiFetch<ScheduledDownload>(`/scheduled/${id}`, {
    method: 'PUT',
    body: JSON.stringify(update),
  });
}

export function deleteSchedule(id: number): Promise<void> {
  return apiFetch<void>(`/scheduled/${id}`, { method: 'DELETE' });
}

export function runScheduleNow(id: number): Promise<RunNowResponse> {
  return apiFetch<RunNowResponse>(`/scheduled/${id}/run`, { method: 'POST' });
}

export function validateCron(expr: string): Promise<CronValidationResponse> {
  const params = new URLSearchParams({ expr });
  return apiFetch<CronValidationResponse>(`/scheduled/validate-cron?${params}`);
}
