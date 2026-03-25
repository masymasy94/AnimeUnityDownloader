import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getTrackedAnimes, untrackAnime, updateTracking, checkNow } from '../api/tracked';

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Mai';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Adesso';
  if (mins < 60) return `${mins}m fa`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h fa`;
  return `${Math.floor(hours / 24)}g fa`;
}

export function TrackedPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['tracked'],
    queryFn: getTrackedAnimes,
    refetchInterval: 30000,
  });

  const removeMutation = useMutation({
    mutationFn: untrackAnime,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tracked'] }),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      updateTracking(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tracked'] }),
  });

  const checkMutation = useMutation({
    mutationFn: checkNow,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tracked'] });
      if (data.new_episodes > 0) {
        queryClient.invalidateQueries({ queryKey: ['downloads'] });
      }
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="inline-block w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
      </div>
    );
  }

  const tracked = data?.tracked ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-text-white">Serie Seguite</h1>

      {tracked.length === 0 ? (
        <div className="text-center py-16 text-text-secondary space-y-2">
          <p>Nessuna serie seguita.</p>
          <p className="text-sm">
            Vai alla pagina di un anime e clicca "Segui" per aggiungerlo.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {tracked.map((t) => (
            <div
              key={t.id}
              className={`flex items-center gap-4 bg-bg-secondary border border-border rounded-[5px] p-4 transition-opacity ${
                !t.enabled ? 'opacity-50' : ''
              }`}
            >
              {t.cover_url && (
                <img
                  src={t.cover_url}
                  alt={t.anime_title}
                  className="w-12 h-16 object-cover rounded flex-shrink-0"
                />
              )}
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-medium text-text-white truncate">
                  {t.anime_title}
                </h3>
                <div className="flex items-center gap-3 text-[11px] text-text-secondary mt-0.5">
                  <span className="px-1.5 py-0.5 bg-bg-card rounded text-[10px]">
                    {t.source_site}
                  </span>
                  <span>Ultimo EP: {t.last_known_episode}</span>
                  <span>Controllo: ogni {t.check_interval_minutes}m</span>
                  <span>Ultimo check: {timeAgo(t.last_checked_at)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => checkMutation.mutate(t.id)}
                  disabled={checkMutation.isPending}
                  className="px-3 py-1.5 text-xs font-medium rounded-[5px] bg-accent/10 text-accent hover:bg-accent hover:text-white transition-colors disabled:opacity-50"
                >
                  Controlla ora
                </button>
                <button
                  onClick={() => toggleMutation.mutate({ id: t.id, enabled: !t.enabled })}
                  className={`px-3 py-1.5 text-xs font-medium rounded-[5px] border transition-colors ${
                    t.enabled
                      ? 'border-success/50 text-success hover:bg-success/10'
                      : 'border-border text-text-secondary hover:text-text-white hover:bg-bg-hover'
                  }`}
                >
                  {t.enabled ? 'Attivo' : 'Disattivato'}
                </button>
                <button
                  onClick={() => removeMutation.mutate(t.id)}
                  className="px-3 py-1.5 text-xs font-medium rounded-[5px] bg-error/10 text-error hover:bg-error hover:text-white transition-colors"
                >
                  Rimuovi
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
