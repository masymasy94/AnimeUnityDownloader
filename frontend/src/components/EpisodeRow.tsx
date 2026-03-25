import type { Episode } from '../types/anime';

interface EpisodeRowProps {
  episode: Episode;
  onDownload: (episode: Episode) => void;
}

function formatViews(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

const STATUS_STYLES: Record<string, { label: string; className: string }> = {
  queued: { label: 'In coda', className: 'bg-warning/20 text-warning' },
  downloading: { label: 'Download...', className: 'bg-accent/20 text-accent' },
  completed: { label: 'Completato', className: 'bg-success/20 text-success' },
  failed: { label: 'Fallito', className: 'bg-error/20 text-error' },
  cancelled: { label: 'Annullato', className: 'bg-text-secondary/20 text-text-secondary' },
};

export function EpisodeRow({ episode, onDownload }: EpisodeRowProps) {
  const status = episode.download_status
    ? STATUS_STYLES[episode.download_status]
    : null;

  return (
    <div className="flex items-center justify-between py-2.5 px-4 border-b border-border/50 hover:bg-bg-hover/50 transition-colors gap-3">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <span className="text-sm font-mono text-text-secondary w-10 flex-shrink-0 text-right">
          {episode.number}
        </span>
        <div className="min-w-0 flex-1">
          {episode.title && (
            <p className="text-sm text-text-white truncate">{episode.title}</p>
          )}
          <div className="flex items-center gap-2 text-[11px] text-text-secondary">
            {episode.created_at && (
              <span>{formatDate(episode.created_at)}</span>
            )}
            {episode.views != null && episode.views > 0 && (
              <span>{formatViews(episode.views)} views</span>
            )}
          </div>
        </div>
        {status && (
          <span className={`text-[11px] px-2 py-0.5 rounded font-medium flex-shrink-0 ${status.className}`}>
            {status.label}
          </span>
        )}
      </div>
      <button
        onClick={() => onDownload(episode)}
        disabled={!!episode.download_status && episode.download_status !== 'failed'}
        className="px-3 py-1.5 text-xs font-medium rounded-[5px] bg-accent/10 text-accent hover:bg-accent hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
      >
        {episode.download_status === 'failed' ? 'Riprova' : 'Scarica'}
      </button>
    </div>
  );
}
