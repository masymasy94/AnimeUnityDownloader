import { Link } from 'react-router-dom';
import type { AnimeSearchResult } from '../types/anime';

interface AnimeCardProps {
  anime: AnimeSearchResult;
}

export function AnimeCard({ anime }: AnimeCardProps) {
  return (
    <Link
      to={`/anime/${anime.id}-${anime.slug}`}
      className="group block bg-bg-card rounded-[5px] overflow-hidden transition-all hover:shadow-lg hover:shadow-black/30 hover:translate-y-[-2px]"
    >
      <div className="aspect-[3/4] overflow-hidden bg-bg-secondary relative">
        {anime.cover_url ? (
          <img
            src={anime.cover_url}
            alt={anime.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-text-secondary text-sm">
            No Cover
          </div>
        )}
        {anime.type && (
          <span className="absolute top-2 left-2 px-2 py-0.5 bg-accent text-white text-[10px] font-bold rounded">
            {anime.type}
          </span>
        )}
        {anime.dub && (
          <span className="absolute top-2 right-2 px-2 py-0.5 bg-warning text-black text-[10px] font-bold rounded">
            ITA
          </span>
        )}
      </div>
      <div className="p-2.5">
        <h3 className="text-[13px] font-medium text-text-white truncate" title={anime.title}>
          {anime.title}
        </h3>
        <div className="flex items-center gap-2 mt-0.5 text-[11px] text-text-secondary">
          {anime.year && <span>{anime.year}</span>}
          {anime.episodes_count != null && (
            <span>{anime.episodes_count} ep</span>
          )}
        </div>
      </div>
    </Link>
  );
}
