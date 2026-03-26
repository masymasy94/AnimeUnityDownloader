import { create } from 'zustand';
import type { WsMessage } from '../types/download';

interface DownloadProgress {
  progress: number;
  downloaded_bytes: number;
  total_bytes: number;
  speed_bps: number;
}

interface DownloadStore {
  progress: Map<number, DownloadProgress>;
  statusChanges: Map<number, { status: string; file_path?: string }>;
  handleMessage: (msg: WsMessage) => void;
  getProgress: (id: number) => DownloadProgress | undefined;
}

export const useDownloadStore = create<DownloadStore>((set, get) => ({
  progress: new Map(),
  statusChanges: new Map(),

  handleMessage: (msg: WsMessage) => {
    switch (msg.type) {
      case 'progress':
        set((state) => {
          const next = new Map(state.progress);
          next.set(msg.download_id, {
            progress: msg.progress,
            downloaded_bytes: msg.downloaded_bytes,
            total_bytes: msg.total_bytes,
            speed_bps: msg.speed_bps,
          });
          return { progress: next };
        });
        break;

      case 'status_change':
        set((state) => {
          const next = new Map(state.statusChanges);
          next.set(msg.download_id, {
            status: msg.status,
            file_path: msg.file_path,
          });
          // Clear progress for completed/failed/finalizing
          if (msg.status === 'completed' || msg.status === 'failed' || msg.status === 'finalizing') {
            const progressNext = new Map(state.progress);
            progressNext.delete(msg.download_id);
            return { statusChanges: next, progress: progressNext };
          }
          return { statusChanges: next };
        });
        break;

      case 'error':
        set((state) => {
          const next = new Map(state.statusChanges);
          next.set(msg.download_id, { status: 'failed' });
          const progressNext = new Map(state.progress);
          progressNext.delete(msg.download_id);
          return { statusChanges: next, progress: progressNext };
        });
        break;
    }
  },

  getProgress: (id: number) => get().progress.get(id),
}));
