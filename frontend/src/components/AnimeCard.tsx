import { Link } from 'react-router-dom';
import type { AnimeSearchResult } from '../types/anime';

interface AnimeCardProps {
  anime: AnimeSearchResult;
  site?: string;
}

const SITE_BADGE: Record<string, { label: string; className: string }> = {
  animeunity: { label: 'AU', className: 'bg-accent text-bg-primary' },
  animeworld: { label: 'AW', className: 'bg-emerald-400 text-bg-primary' },
};

export function AnimeCard({ anime, site }: AnimeCardProps) {
  const sourceSite = site || anime.source_site || 'animeunity';
  const siteParam = sourceSite !== 'animeunity' ? `?site=${sourceSite}` : '';
  const badge = SITE_BADGE[sourceSite] || { label: sourceSite.toUpperCase().slice(0, 2), className: 'bg-gray-300 text-bg-primary' };

  const specParts = [anime.type, anime.year, anime.episodes_count != null ? `${anime.episodes_count} ep` : null].filter(Boolean);

  return (
    <Link
      to={`/anime/${anime.id}-${anime.slug}${siteParam}`}
      className="group block bg-bg-card rounded-md overflow-hidden ring-1 ring-border/70 transition-all duration-300 hover:-translate-y-1 hover:ring-accent/60 hover:shadow-[0_16px_32px_-12px_rgba(0,0,0,0.7)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <div className="aspect-[3/4] overflow-hidden bg-bg-secondary relative">
        {anime.cover_url ? (
          <img
            src={anime.cover_url}
            alt={anime.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.06]"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-text-secondary text-sm">
            No Cover
          </div>
        )}

        {/* Bottom scrim — always present, deepens on hover so the label row below never fights the art */}
        <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/70 to-transparent opacity-80 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

        <div className="absolute top-2 left-2 flex gap-1">
          <span className={`spec-line px-1.5 py-0.5 text-[10px] font-bold rounded-sm shadow-sm ${badge.className}`}>
            {badge.label}
          </span>
          {anime.type && (
            <span className="spec-line px-1.5 py-0.5 bg-black/70 text-white text-[10px] font-bold rounded-sm backdrop-blur-sm">
              {anime.type}
            </span>
          )}
        </div>
        {anime.dub && (
          <span className="spec-line absolute top-2 right-2 px-1.5 py-0.5 bg-warning text-bg-primary text-[10px] font-bold rounded-sm shadow-sm">
            ITA
          </span>
        )}
      </div>
      <div className="p-2.5 space-y-1">
        <h3
          className="text-[13px] font-semibold text-text-white leading-snug line-clamp-2 group-hover:text-accent transition-colors"
          title={anime.title}
        >
          {anime.title}
        </h3>
        {specParts.length > 0 && (
          <p className="spec-line text-[10px] text-text-secondary flex items-center gap-1.5 truncate">
            {specParts.map((part, i) => (
              <span key={i} className="flex items-center gap-1.5">
                {i > 0 && <span className="text-border">/</span>}
                {part}
              </span>
            ))}
          </p>
        )}
      </div>
    </Link>
  );
}
