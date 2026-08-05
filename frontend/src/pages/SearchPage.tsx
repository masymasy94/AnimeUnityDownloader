import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { streamSearch, getLatestAnime } from '../api/search';
import { SearchBar } from '../components/SearchBar';
import { AnimeCard } from '../components/AnimeCard';
import type { AnimeSearchResult } from '../types/anime';

const TYPE_FILTERS = ['Tutti', 'TV', 'Movie', 'OVA', 'ONA', 'Special'] as const;
const DUB_FILTERS = ['Tutti', 'SUB', 'ITA'] as const;

const TYPE_ORDER: Record<string, number> = { TV: 0, Movie: 1, ONA: 2, OVA: 3, Special: 4 };

export function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<AnimeSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [siteFilter, setSiteFilter] = useState<string>('Tutti');
  const [typeFilter, setTypeFilter] = useState<string>('Tutti');
  const [dubFilter, setDubFilter] = useState<string>('Tutti');
  const abortRef = useRef<(() => void) | null>(null);

  const handleSearch = useCallback((q: string) => setQuery(q), []);

  // Stream search: cancel previous, start new
  useEffect(() => {
    // Cancel any in-flight stream
    abortRef.current?.();
    abortRef.current = null;

    if (query.length < 2) {
      setResults([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    setResults([]);
    setIsLoading(true);
    setError(null);

    const abort = streamSearch(
      query,
      (_site, newResults) => {
        setResults((prev) => [...prev, ...newResults]);
      },
      () => {
        setIsLoading(false);
      },
      (err) => {
        setError(err);
        setIsLoading(false);
      },
    );

    abortRef.current = abort;

    return () => {
      abort();
    };
  }, [query]);

  const { data: latestData } = useQuery({
    queryKey: ['latest'],
    queryFn: getLatestAnime,
    staleTime: 5 * 60 * 1000,
  });

  const filtered = useMemo(() => {
    if (!results.length) return [];

    let list = [...results];

    if (siteFilter !== 'Tutti') {
      list = list.filter((a) => a.source_site === siteFilter);
    }

    if (typeFilter !== 'Tutti') {
      list = list.filter((a) => a.type === typeFilter);
    }

    if (dubFilter === 'SUB') {
      list = list.filter((a) => !a.dub);
    } else if (dubFilter === 'ITA') {
      list = list.filter((a) => a.dub);
    }

    list.sort((a, b) => {
      const typeA = TYPE_ORDER[a.type ?? ''] ?? 99;
      const typeB = TYPE_ORDER[b.type ?? ''] ?? 99;
      if (typeA !== typeB) return typeA - typeB;
      return (b.year ?? '').localeCompare(a.year ?? '');
    });

    return list;
  }, [results, siteFilter, typeFilter, dubFilter]);

  const siteCounts = useMemo(() => {
    if (!results.length) return {};
    const counts: Record<string, number> = {};
    for (const r of results) {
      const s = r.source_site ?? 'animeunity';
      counts[s] = (counts[s] || 0) + 1;
    }
    return counts;
  }, [results]);

  const typeCounts = useMemo(() => {
    if (!results.length) return {};
    const counts: Record<string, number> = {};
    for (const r of results) {
      const t = r.type ?? 'Altro';
      counts[t] = (counts[t] || 0) + 1;
    }
    return counts;
  }, [results]);

  const hasResults = query.length >= 2 && results.length > 0;
  const showHero = !hasResults && !isLoading && !error;

  return (
    <div className="space-y-6">
      {/* Hero section with gradient background */}
      <div
        className="relative -m-6 mb-0 overflow-hidden transition-all duration-700"
        style={{ height: showHero ? '280px' : '140px' }}
      >
        <div
          className="absolute inset-0 transition-all duration-700"
          style={{
            background: showHero
              ? `
                radial-gradient(ellipse 70% 55% at 75% 15%, rgba(51,201,176,0.16) 0%, transparent 60%),
                radial-gradient(ellipse 50% 35% at 15% 75%, rgba(51,201,176,0.08) 0%, transparent 55%),
                linear-gradient(to bottom, #0c131c 0%, #0a0e15 100%)
              `
              : 'linear-gradient(to bottom, #0c131c 0%, #0a0e15 100%)',
          }}
        />
        {/* Hairline "on-air" sweep — plays once when the idle hero mounts, then rests */}
        {showHero && (
          <div
            className="signal-sweep absolute inset-y-0 left-0 w-1/3 pointer-events-none"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(51,201,176,0.16), transparent)' }}
          />
        )}
        <div className="relative z-10 flex flex-col items-center justify-center h-full px-6">
          <div className="text-center space-y-2 mb-5">
            <h1
              className={`font-extrabold tracking-tight text-text-white drop-shadow-lg transition-all duration-500 ${showHero ? 'text-4xl' : 'text-lg'}`}
            >
              Cerca un anime
            </h1>
            {showHero && (
              <p className="text-text-secondary text-sm drop-shadow">
                Cerca, guarda e scarica da AnimeUnity, AnimeWorld e AnimeSaturn
              </p>
            )}
          </div>
          <div className={`w-full transition-all duration-500 ${showHero ? 'max-w-xl' : 'max-w-2xl'}`}>
            <SearchBar onSearch={handleSearch} isLoading={isLoading} />
          </div>
        </div>
      </div>

      {error && (
        <div className="text-center py-8 text-error text-sm">
          Errore nella ricerca: {error.message}
        </div>
      )}

      {/* Filters */}
      {hasResults && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-4">
            {/* Site filter */}
            <div className="flex gap-1">
              <button
                onClick={() => setSiteFilter('Tutti')}
                className={`spec-line px-3 py-1.5 text-[11px] font-bold rounded-sm transition-colors ${
                  siteFilter === 'Tutti'
                    ? 'bg-accent text-bg-primary'
                    : 'bg-bg-secondary text-text-secondary hover:text-text-white border border-border'
                }`}
              >
                Tutti
              </button>
              {Object.entries(siteCounts).map(([site]) => (
                <button
                  key={site}
                  onClick={() => setSiteFilter(site)}
                  className={`spec-line px-3 py-1.5 text-[11px] font-bold rounded-sm transition-colors ${
                    siteFilter === site
                      ? 'bg-accent text-bg-primary'
                      : 'bg-bg-secondary text-text-secondary hover:text-text-white border border-border'
                  }`}
                >
                  {site === 'animeunity' ? 'AnimeUnity' : site === 'animeworld' ? 'AnimeWorld' : site === 'animesaturn' ? 'AnimeSaturn' : site}
                </button>
              ))}
            </div>

            {/* Type filter */}
            <div className="flex gap-1">
              {TYPE_FILTERS.map((t) => {
                const count = t === 'Tutti' ? results.length : (typeCounts[t] || 0);
                if (t !== 'Tutti' && count === 0) return null;
                return (
                  <button
                    key={t}
                    onClick={() => setTypeFilter(t)}
                    className={`spec-line px-3 py-1.5 text-[11px] font-bold rounded-sm transition-colors ${
                      typeFilter === t
                        ? 'bg-accent text-bg-primary'
                        : 'bg-bg-secondary text-text-secondary hover:text-text-white border border-border'
                    }`}
                  >
                    {t}
                  </button>
                );
              })}
            </div>

            {/* Dub filter */}
            <div className="flex gap-1">
              {DUB_FILTERS.map((d) => (
                <button
                  key={d}
                  onClick={() => setDubFilter(d)}
                  className={`spec-line px-3 py-1.5 text-[11px] font-bold rounded-sm transition-colors ${
                    dubFilter === d
                      ? 'bg-accent text-bg-primary'
                      : 'bg-bg-secondary text-text-secondary hover:text-text-white border border-border'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* Results */}
      {filtered.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filtered.map((anime) => (
            <AnimeCard key={`${anime.source_site}-${anime.id}`} anime={anime} site={anime.source_site} />
          ))}
        </div>
      )}

      {hasResults && filtered.length === 0 && (
        <div className="text-center py-12 text-text-secondary">
          Nessun risultato con i filtri selezionati
        </div>
      )}

      {query.length >= 2 && !isLoading && results.length === 0 && (
        <div className="text-center py-12 text-text-secondary">
          Nessun risultato per "{query}"
        </div>
      )}

      {/* Latest / In onda ora */}
      {showHero && latestData?.results && latestData.results.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-xl font-bold tracking-tight text-text-white">Ultime uscite</h2>
            <div className="h-px flex-1 bg-border" />
            <span className="spec-line text-[10px] text-text-secondary">{latestData.results.length} titoli</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {latestData.results.map((anime) => (
              <AnimeCard key={`${anime.source_site}-${anime.id}`} anime={anime} site={anime.source_site} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
