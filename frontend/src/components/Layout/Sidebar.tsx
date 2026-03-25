import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getDownloads } from '../../api/downloads';

const NAV_ITEMS = [
  { to: '/search', label: 'Cerca' },
  { to: '/downloads', label: 'Downloads' },
  { to: '/settings', label: 'Impostazioni' },
];

const NAV_ICONS: Record<string, React.ReactNode> = {
  '/search': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  '/downloads': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),
  '/settings': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
};

export function Sidebar() {
  const { data } = useQuery({
    queryKey: ['downloads', 'active'],
    queryFn: () => getDownloads(['queued', 'downloading']),
    refetchInterval: 5000,
  });

  const activeCount = data?.downloads?.length ?? 0;

  return (
    <aside className="w-56 h-screen bg-bg-navbar border-r border-border flex flex-col flex-shrink-0">
      <div className="p-5">
        <h1 className="text-lg font-bold text-accent">AnimeUnity</h1>
        <p className="text-[11px] text-text-secondary tracking-wide">DOWNLOADER</p>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        {NAV_ITEMS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[5px] text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-accent/15 text-accent'
                  : 'text-text-secondary hover:text-text-white hover:bg-bg-hover'
              }`
            }
          >
            {NAV_ICONS[to]}
            <span>{label}</span>
            {to === '/downloads' && activeCount > 0 && (
              <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-accent text-white rounded-full min-w-[18px] text-center">
                {activeCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <p className="text-[10px] text-text-secondary">v0.1.0</p>
      </div>
    </aside>
  );
}
