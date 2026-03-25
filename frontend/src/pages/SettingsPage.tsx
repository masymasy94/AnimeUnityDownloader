import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings } from '../api/settings';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  const [maxConcurrent, setMaxConcurrent] = useState(2);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setMaxConcurrent(settings.max_concurrent_downloads);
    }
  }, [settings]);

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  const handleSave = () => {
    mutation.mutate({
      max_concurrent_downloads: maxConcurrent,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="inline-block w-6 h-6 border-2 border-accent/30 border-t-accent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold text-text-white">Impostazioni</h1>

      <div className="bg-bg-secondary border border-border rounded-[5px] p-6 space-y-5">
        {/* Download directory */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-text-white">
            Cartella di destinazione
          </label>
          <div className="flex items-center gap-3 px-4 py-3 bg-bg-primary border border-border rounded-[5px]">
            <svg className="w-5 h-5 text-accent flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <span className="text-sm text-text-white font-mono">
              {settings?.host_download_path || settings?.download_dir || '/downloads'}
            </span>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            Per cambiare la cartella, ferma il container e modifica <code className="px-1.5 py-0.5 bg-bg-hover rounded text-accent text-[11px]">DOWNLOAD_PATH</code> nel file <code className="px-1.5 py-0.5 bg-bg-hover rounded text-accent text-[11px]">.env</code> o avvia con:
          </p>
          <pre className="text-xs text-accent bg-bg-primary border border-border rounded-[5px] px-3 py-2 overflow-x-auto">
            DOWNLOAD_PATH=/percorso/desiderato docker-compose up -d
          </pre>
        </div>

        {/* Max concurrent */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-text-white">
            Download simultanei
          </label>
          <input
            type="number"
            min={1}
            max={5}
            value={maxConcurrent}
            onChange={(e) => setMaxConcurrent(parseInt(e.target.value) || 1)}
            className="w-32 px-4 py-2.5 bg-bg-primary border border-border rounded-[5px] text-text-white text-sm focus:outline-none focus:border-accent transition-colors"
          />
        </div>

        {/* Save */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleSave}
            disabled={mutation.isPending}
            className="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-[5px] hover:bg-accent-hover disabled:opacity-50 transition-colors"
          >
            {mutation.isPending ? 'Salvataggio...' : 'Salva'}
          </button>
          {saved && (
            <span className="text-sm text-success font-medium">Salvato!</span>
          )}
        </div>
      </div>
    </div>
  );
}
