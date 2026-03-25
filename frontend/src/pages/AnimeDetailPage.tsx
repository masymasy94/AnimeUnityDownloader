import { useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAnimeDetail, getEpisodes } from '../api/anime';
import { startDownloads } from '../api/downloads';
import { EpisodeList } from '../components/EpisodeList';
import type { Episode } from '../types/anime';

export function AnimeDetailPage() {
  const { animePath } = useParams<{ animePath: string }>();
  const queryClient = useQueryClient();
  const [episodeEnd, setEpisodeEnd] = useState(120);

  // Parse anime path
  const match = animePath?.match(/^(\d+)-(.+)$/);
  const animeId = match ? parseInt(match[1]) : 0;
  const slug = match ? match[2] : '';

  const { data: anime, isLoading: animeLoading } = useQuery({
    queryKey: ['anime', animeId, slug],
    queryFn: () => getAnimeDetail(animeId, slug),
    enabled: !!animeId,
  });

  const {
    data: episodesData,
    isLoading: episodesLoading,
    isFetching: episodesFetching,
  } = useQuery({
    queryKey: ['episodes', animeId, slug, episodeEnd],
    queryFn: () => getEpisodes(animeId, slug, 1, episodeEnd),
    enabled: !!animeId,
  });

  const handleDownload = useCallback(
    async (episode: Episode) => {
      if (!anime) return;
      await startDownloads({
        anime_id: anime.id,
        anime_title: anime.title,
        anime_slug: anime.slug,
        cover_url: anime.cover_url,
        genres: anime.genres,
        plot: anime.plot,
        year: anime.year,
        episodes: [{ episode_id: episode.id, episode_number: episode.number }],
      });
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
    },
    [anime, queryClient],
  );

  const handleDownloadAll = useCallback(async () => {
    if (!anime || !episodesData) return;
    const downloadable = episodesData.episodes.filter(
      (ep) => !ep.download_status || ep.download_status === 'failed',
    );
    if (downloadable.length === 0) return;

    await startDownloads({
      anime_id: anime.id,
      anime_title: anime.title,
      anime_slug: anime.slug,
      cover_url: anime.cover_url,
      genres: anime.genres,
      plot: anime.plot,
      year: anime.year,
      episodes: downloadable.map((ep) => ({
        episode_id: ep.id,
        episode_number: ep.number,
      })),
    });
    queryClient.invalidateQueries({ queryKey: ['episodes'] });
  }, [anime, episodesData, queryClient]);

  const handleDownloadRange = useCallback(
    async (from: number, to: number) => {
      if (!anime) return;
      // Fetch episodes in the requested range from the API
      const rangeData = await getEpisodes(animeId, slug, from, to);
      const downloadable = rangeData.episodes.filter(
        (ep) => !ep.download_status || ep.download_status === 'failed',
      );
      if (downloadable.length === 0) return;

      await startDownloads({
        anime_id: anime.id,
        anime_title: anime.title,
        anime_slug: anime.slug,
        cover_url: anime.cover_url,
        genres: anime.genres,
        plot: anime.plot,
        year: anime.year,
        episodes: downloadable.map((ep) => ({
          episode_id: ep.id,
          episode_number: ep.number,
        })),
      });
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
    },
    [anime, animeId, slug, queryClient],
  );

  const handleLoadMore = useCallback(() => {
    setEpisodeEnd((prev) => prev + 120);
  }, []);

  if (animeLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="inline-block w-8 h-8 border-3 border-accent/30 border-t-accent rounded-full animate-spin" />
      </div>
    );
  }

  if (!anime) {
    return <div className="text-center py-20 text-error">Anime non trovato</div>;
  }

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative rounded-2xl overflow-hidden bg-bg-secondary">
        {anime.banner_url && (
          <div className="absolute inset-0">
            <img
              src={anime.banner_url}
              alt=""
              className="w-full h-full object-cover opacity-30 blur-sm"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-bg-secondary via-bg-secondary/80 to-transparent" />
          </div>
        )}
        <div className="relative flex gap-6 p-6">
          {anime.cover_url && (
            <img
              src={anime.cover_url}
              alt={anime.title}
              className="w-40 h-56 object-cover rounded-xl shadow-lg flex-shrink-0"
            />
          )}
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-start gap-2 flex-wrap">
              <h1 className="text-2xl font-bold">{anime.title}</h1>
              {anime.dub && (
                <span className="px-2 py-0.5 bg-warning/90 text-black text-xs font-bold rounded mt-1">
                  ITA
                </span>
              )}
            </div>
            {anime.title_eng && anime.title_eng !== anime.title && (
              <p className="text-sm text-text-secondary">{anime.title_eng}</p>
            )}
            <div className="flex flex-wrap gap-2">
              {anime.type && (
                <span className="px-2 py-0.5 bg-accent/20 text-accent text-xs rounded font-medium">
                  {anime.type}
                </span>
              )}
              {anime.year && (
                <span className="px-2 py-0.5 bg-bg-card text-text-secondary text-xs rounded">
                  {anime.year}
                </span>
              )}
              {anime.status && (
                <span className="px-2 py-0.5 bg-bg-card text-text-secondary text-xs rounded">
                  {anime.status}
                </span>
              )}
              {anime.episodes_count != null && (
                <span className="px-2 py-0.5 bg-bg-card text-text-secondary text-xs rounded">
                  {anime.episodes_count} episodi
                </span>
              )}
            </div>
            {anime.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {anime.genres.map((genre) => (
                  <span
                    key={genre}
                    className="px-2 py-0.5 bg-bg-card border border-border text-text-secondary text-xs rounded-full"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            )}
            {anime.plot && (
              <p className="text-sm text-text-secondary leading-relaxed line-clamp-4">
                {anime.plot}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Episodes */}
      {episodesLoading ? (
        <div className="flex items-center justify-center py-10">
          <span className="inline-block w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
        </div>
      ) : episodesData ? (
        <EpisodeList
          episodes={episodesData.episodes}
          total={episodesData.total}
          hasMore={episodesData.has_more}
          onLoadMore={handleLoadMore}
          onDownload={handleDownload}
          onDownloadAll={handleDownloadAll}
          onDownloadRange={handleDownloadRange}
          isLoadingMore={episodesFetching}
        />
      ) : null}
    </div>
  );
}
