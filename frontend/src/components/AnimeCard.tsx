import { Link } from 'react-router-dom';
import type { AnimeSearchResult } from '../types/anime';

interface AnimeCardProps {
  anime: AnimeSearchResult;
  site?: string;
}

const SITE_BADGE: Record<string, { label: string; className: string }> = {
  animeunity: { label: 'AU', className: 'bg-accent text-white' },
  animeworld: { label: 'AW', className: 'bg-emerald-500 text-white' },
};

export function AnimeCard({ anime, site }: AnimeCardProps) {
  const sourceSite = site || anime.source_site || 'animeunity';
  const siteParam = sourceSite !== 'animeunity' ? `?site=${sourceSite}` : '';
  const badge = SITE_BADGE[sourceSite] || { label: sourceSite.toUpperCase().slice(0, 2), className: 'bg-gray-500 text-white' };

  return (
    <Link
      to={`/anime/${anime.id}-${anime.slug}${siteParam}`}
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
        <div className="absolute top-2 left-2 flex gap-1">
          <span className={`px-2 py-0.5 text-[10px] font-bold rounded ${badge.className}`}>
            {badge.label}
          </span>
          {anime.type && (
            <span className="px-2 py-0.5 bg-black/60 text-white text-[10px] font-bold rounded">
              {anime.type}
            </span>
          )}
        </div>
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
