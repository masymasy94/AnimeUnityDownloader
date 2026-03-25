import { useWebSocket } from '../../hooks/useWebSocket';

export function Header() {
  const { status } = useWebSocket();

  return (
    <header className="h-14 bg-bg-secondary border-b border-border flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            status === 'connected'
              ? 'bg-success'
              : status === 'reconnecting'
                ? 'bg-warning animate-pulse'
                : 'bg-error'
          }`}
        />
        <span className="text-xs text-text-secondary">
          {status === 'connected'
            ? 'Connesso'
            : status === 'reconnecting'
              ? 'Riconnessione...'
              : 'Disconnesso'}
        </span>
      </div>
    </header>
  );
}
