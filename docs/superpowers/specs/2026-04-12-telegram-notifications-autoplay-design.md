# Notifiche Telegram + Auto-play Episodio Successivo

**Data**: 2026-04-12
**Scope**: Due feature indipendenti — notifiche Telegram per download programmati e auto-play nel player streaming.

---

## Feature 1: Notifiche Telegram

### Obiettivo

Inviare un riepilogo Telegram alla fine di ogni ciclo di download programmati, con la lista degli episodi accodati con successo. Sostituisce l'integrazione Plex che viene rimossa.

### Rimozione Plex

Eliminare completamente:
- `backend/app/services/plex_service.py`
- Riferimenti a Plex in `download_service.py` (`PlexService` import, `self._plex`, `_maybe_trigger_plex_scan()`, chiamata in `on_move_success`)
- Settings `plex_url`, `plex_token`, `plex_library_id` da: `settings_service.py` (DEFAULTS, get/update), `schemas/setting.py` (SettingsResponse, SettingsUpdate)
- Sezione "Integrazione Plex" da `SettingsPage.tsx`
- Campi plex da `frontend/src/types/settings.ts`

### NotificationService

Nuovo file: `backend/app/services/notification_service.py`

```python
class NotificationService:
    def __init__(self, db_session_factory):
        self._db = db_session_factory

    async def _get_telegram_config(self) -> tuple[str, str]:
        """Return (bot_token, chat_id) from DB settings."""
        # Read settings "telegram_bot_token" and "telegram_chat_id"

    async def is_configured(self) -> bool:
        token, chat_id = await self._get_telegram_config()
        return bool(token and chat_id)

    async def send_telegram(self, text: str) -> bool:
        """Send message via Telegram Bot API. Returns True on success."""
        token, chat_id = await self._get_telegram_config()
        # POST https://api.telegram.org/bot{token}/sendMessage
        # body: { chat_id, text, parse_mode: "HTML" }
        # Uses httpx.AsyncClient (already a dependency)

    async def notify_scheduled_downloads(self, results: list[dict]) -> None:
        """Send summary of scheduled download results.
        results: [{"anime_title": str, "episodes": list[str]}]
        Only called if len(results) > 0.
        """
        # Format message and call send_telegram
```

Nessuna nuova dipendenza — `httpx` è già in `requirements.txt`.

### Formato messaggio

```
📥 Download programmati avviati

Naruto Shippuden — EP 301, 302, 303
One Piece — EP 1100

Totale: 4 episodi
```

### Integrazione in ScheduledDownloadService

In `_tick()`, dopo il loop su tutti gli schedule abilitati:

```python
# Collect results for notification
results = []
for row in rows:
    try:
        enqueued, reason = await self._execute(row.id)
        if enqueued > 0:
            results.append({
                "anime_title": row.anime_title,
                "episode_count": enqueued,
            })
    except Exception as exc:
        ...

# Send notification summary
if results:
    await self._notification.notify_scheduled_downloads(results)
```

Il `ScheduledDownloadService.__init__` riceve un `NotificationService` come parametro aggiuntivo. Viene istanziato in `main.py`.

**Nota**: la notifica dice "avviati" perché viene inviata quando gli episodi sono stati accodati per il download, non quando sono completati. Questo perché il ciclo scheduled crea le richieste di download che poi procedono in background.

### Endpoint test

Aggiungere a `backend/app/api/settings.py`:

```
POST /api/settings/telegram/test
```

Invia un messaggio di test ("Hasasiero: connessione Telegram OK") usando il token e chat_id attualmente salvati. Restituisce `{"success": true/false, "error": "..."}`.

### Settings Backend

In `settings_service.py`:
- Aggiungere `telegram_bot_token` e `telegram_chat_id` ai DEFAULTS (stringa vuota)
- Aggiungere campi a `get_settings()` e `update_settings()`

In `schemas/setting.py`:
- Aggiungere `telegram_bot_token: str` e `telegram_chat_id: str` a `SettingsResponse`
- Aggiungere `telegram_bot_token: str | None = None` e `telegram_chat_id: str | None = None` a `SettingsUpdate`

### Settings Frontend

In `types/settings.ts`:
- Aggiungere `telegram_bot_token: string` e `telegram_chat_id: string` a `Settings`
- Aggiungere `telegram_bot_token?: string` e `telegram_chat_id?: string` a `SettingsUpdate`

In `SettingsPage.tsx`:
- Sostituire la sezione "Integrazione Plex" con "Notifiche Telegram"
- Campi: Bot Token (password input), Chat ID (text input)
- Pulsante "Invia test" che chiama `POST /api/settings/telegram/test`
- Descrizione in italiano su come creare un bot Telegram e ottenere il chat ID

---

## Feature 2: Auto-play Episodio Successivo

### Obiettivo

Quando un episodio in streaming finisce, mostrare un overlay countdown (5 secondi) e avviare automaticamente l'episodio successivo. L'utente puo' annullare o cliccare per partire subito.

### VideoPlayer — nuove props

```typescript
interface VideoPlayerProps {
  url: string;
  type: 'mp4' | 'm3u8';
  title: string;
  onClose: () => void;
  // Nuove:
  onNext?: () => void;           // Callback per avviare episodio successivo
  nextEpisodeLabel?: string;     // Es. "Ep. 302 — Titolo episodio"
}
```

### Logica nel VideoPlayer

1. Listener `onEnded` sull'elemento `<video>`
2. Quando il video finisce:
   - Se `onNext` non e' definito: non succede nulla (ultimo episodio)
   - Se `onNext` e' definito: mostra overlay countdown
3. Overlay countdown (5 secondi):
   - Barra di progresso lineare che si svuota
   - Testo: "Prossimo episodio tra {N}..." + `nextEpisodeLabel`
   - Pulsante "Riproduci ora" (invoca `onNext` immediatamente)
   - Pulsante "Annulla" (chiude l'overlay, resta sul player fermo)
4. Allo scadere del countdown: invoca `onNext()`

### Stato countdown nel VideoPlayer

```typescript
const [showCountdown, setShowCountdown] = useState(false);
const [countdownSeconds, setCountdownSeconds] = useState(5);
const countdownRef = useRef<NodeJS.Timeout | null>(null);
```

- `setInterval` da 1 secondo che decrementa il counter
- Cleanup dell'interval su unmount e su "Annulla"

### AnimeDetailPage — calcolo episodio successivo

In `AnimeDetailPage.tsx`, quando `streamInfo` e' attivo:

```typescript
const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null);

const nextEpisode = useMemo(() => {
  if (!currentEpisode || !episodes) return null;
  const currentNum = parseFloat(currentEpisode.number);
  // Trova il primo episodio con numero > currentNum nella lista caricata
  return episodes.find(ep => parseFloat(ep.number) > currentNum) || null;
}, [currentEpisode, episodes]);

const handleWatch = useCallback(async (episode: Episode) => {
  if (!anime) return;
  setCurrentEpisode(episode);  // Traccia episodio corrente
  // ... fetch stream source e setStreamInfo
}, [anime, site]);

const handleNext = useCallback(() => {
  if (nextEpisode) handleWatch(nextEpisode);
}, [nextEpisode, handleWatch]);
```

E nel JSX:

```tsx
<VideoPlayer
  url={streamInfo.url}
  type={streamInfo.type}
  title={streamInfo.title}
  onClose={() => { setStreamInfo(null); setCurrentEpisode(null); }}
  onNext={nextEpisode ? handleNext : undefined}
  nextEpisodeLabel={nextEpisode ? `Ep. ${nextEpisode.number}${nextEpisode.title ? ` — ${nextEpisode.title}` : ''}` : undefined}
/>
```

### Overlay countdown — stile

- Sfondo semi-trasparente scuro sopra il video
- Centrato verticalmente e orizzontalmente
- Barra di progresso lineare in basso (colore accent, si svuota in 5s)
- Font size grande per il countdown numerico
- Coerente con il design system esistente (colori bg-secondary, text-white, accent)

---

## File modificati — riepilogo

### Backend
| File | Azione |
|------|--------|
| `services/plex_service.py` | Eliminare |
| `services/notification_service.py` | Creare |
| `services/download_service.py` | Rimuovere import/uso PlexService |
| `services/scheduled_download_service.py` | Aggiungere NotificationService, notifica in `_tick()` |
| `services/settings_service.py` | Sostituire plex_* con telegram_* |
| `schemas/setting.py` | Sostituire plex_* con telegram_* |
| `api/settings.py` | Aggiungere endpoint test Telegram |
| `main.py` | Istanziare NotificationService, passare a ScheduledDownloadService |

### Frontend
| File | Azione |
|------|--------|
| `types/settings.ts` | Sostituire plex_* con telegram_* |
| `pages/SettingsPage.tsx` | Sezione Telegram al posto di Plex |
| `components/VideoPlayer.tsx` | Aggiungere countdown + auto-play |
| `pages/AnimeDetailPage.tsx` | Calcolare episodio successivo, passare onNext |
| `api/settings.ts` | Aggiungere chiamata test Telegram |
