import { useState } from 'react';
import type { Episode } from '../types/anime';
import { EpisodeRow } from './EpisodeRow';

interface EpisodeListProps {
  episodes: Episode[];
  total: number;
  hasMore: boolean;
  onLoadMore: () => void;
  onDownload: (episode: Episode) => void;
  onDownloadAll: () => void;
  onDownloadRange: (from: number, to: number) => void;
  isLoadingMore?: boolean;
}

export function EpisodeList({
  episodes,
  total,
  hasMore,
  onLoadMore,
  onDownload,
  onDownloadAll,
  onDownloadRange,
  isLoadingMore,
}: EpisodeListProps) {
  const [rangeFrom, setRangeFrom] = useState('');
  const [rangeTo, setRangeTo] = useState('');
  const [showRange, setShowRange] = useState(false);

  const downloadableEpisodes = episodes.filter(
    (ep) => !ep.download_status || ep.download_status === 'failed',
  );

  const handleRangeDownload = () => {
    const from = parseInt(rangeFrom);
    const to = parseInt(rangeTo);
    if (!isNaN(from) && !isNaN(to) && from >= 1 && to >= from) {
      onDownloadRange(from, to);
      setRangeFrom('');
      setRangeTo('');
      setShowRange(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="text-lg font-semibold">
          Episodi ({total})
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowRange((v) => !v)}
            className={`px-3 py-2 text-sm font-medium rounded-[5px] border transition-colors ${
              showRange
                ? 'border-accent text-accent bg-accent/10'
                : 'border-border text-text-secondary hover:text-text-white hover:bg-bg-hover'
            }`}
          >
            Range
          </button>
          {downloadableEpisodes.length > 0 && (
            <button
              onClick={onDownloadAll}
              className="px-4 py-2 text-sm font-medium rounded-[5px] bg-accent text-white hover:bg-accent-hover transition-colors"
            >
              Scarica tutti
            </button>
          )}
        </div>
      </div>

      {/* Range selector */}
      {showRange && (
        <div className="flex items-center gap-2 mb-3 p-3 bg-bg-secondary rounded-[5px] border border-border">
          <span className="text-sm text-text-secondary">Da</span>
          <input
            type="number"
            min={1}
            max={total}
            value={rangeFrom}
            onChange={(e) => setRangeFrom(e.target.value)}
            placeholder="1"
            className="w-20 px-3 py-1.5 bg-bg-primary border border-border rounded-[5px] text-sm text-text-white outline-none focus:border-accent transition-colors text-center"
          />
          <span className="text-sm text-text-secondary">a</span>
          <input
            type="number"
            min={1}
            max={total}
            value={rangeTo}
            onChange={(e) => setRangeTo(e.target.value)}
            placeholder={String(total)}
            className="w-20 px-3 py-1.5 bg-bg-primary border border-border rounded-[5px] text-sm text-text-white outline-none focus:border-accent transition-colors text-center"
          />
          <button
            onClick={handleRangeDownload}
            disabled={!rangeFrom || !rangeTo || parseInt(rangeFrom) > parseInt(rangeTo)}
            className="px-4 py-1.5 text-sm font-medium rounded-[5px] bg-accent text-white hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Scarica
          </button>
        </div>
      )}

      <div className="bg-bg-secondary rounded-[5px] border border-border overflow-hidden">
        {episodes.map((ep) => (
          <EpisodeRow key={ep.id} episode={ep} onDownload={onDownload} />
        ))}
      </div>
      {hasMore && (
        <button
          onClick={onLoadMore}
          disabled={isLoadingMore}
          className="w-full mt-3 py-2.5 text-sm font-medium text-accent bg-bg-secondary border border-border rounded-[5px] hover:bg-bg-hover transition-colors disabled:opacity-50"
        >
          {isLoadingMore ? 'Caricamento...' : 'Carica altri episodi'}
        </button>
      )}
    </div>
  );
}
