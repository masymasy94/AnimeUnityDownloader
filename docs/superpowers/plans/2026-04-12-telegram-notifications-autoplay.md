# Telegram Notifications + Auto-play Next Episode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Plex integration with Telegram notifications for scheduled downloads, and add Netflix-style countdown auto-play in the streaming player.

**Architecture:** Two independent features. (1) New `NotificationService` sends a Telegram summary after each scheduled download cycle via the Bot API. (2) `VideoPlayer` gains an `onEnded` countdown overlay that auto-advances to the next episode. Both features are additive except the Plex removal which is a clean delete.

**Tech Stack:** Python/FastAPI (httpx for Telegram API), React/TypeScript (hls.js player), SQLite settings table.

**Spec:** `docs/superpowers/specs/2026-04-12-telegram-notifications-autoplay-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/services/plex_service.py` | Delete | Remove Plex integration |
| `backend/app/services/download_service.py` | Modify | Remove Plex references |
| `backend/app/services/notification_service.py` | Create | Telegram Bot API integration |
| `backend/app/services/scheduled_download_service.py` | Modify | Send notification after tick |
| `backend/app/services/settings_service.py` | Modify | Replace plex_* with telegram_* |
| `backend/app/schemas/setting.py` | Modify | Replace plex_* with telegram_* |
| `backend/app/api/settings.py` | Modify | Add Telegram test endpoint |
| `backend/app/api/deps.py` | Modify | Add notification_service getter |
| `backend/app/main.py` | Modify | Wire NotificationService |
| `frontend/src/types/settings.ts` | Modify | Replace plex_* with telegram_* |
| `frontend/src/pages/SettingsPage.tsx` | Modify | Telegram section replaces Plex |
| `frontend/src/api/settings.ts` | Modify | Add testTelegram function |
| `frontend/src/components/VideoPlayer.tsx` | Modify | Countdown overlay + auto-play |
| `frontend/src/pages/AnimeDetailPage.tsx` | Modify | Track current episode, compute next |

---

## Task 1: Remove Plex Integration from Backend

**Files:**
- Delete: `backend/app/services/plex_service.py`
- Modify: `backend/app/services/download_service.py:17,76,321-335,511`
- Modify: `backend/app/services/settings_service.py:12-18,26-39,41-57`
- Modify: `backend/app/schemas/setting.py:4-18`

- [ ] **Step 1: Delete plex_service.py**

```bash
rm backend/app/services/plex_service.py
```

- [ ] **Step 2: Remove Plex from download_service.py**

In `backend/app/services/download_service.py`, remove the import on line 17:

```python
# DELETE this line:
from .plex_service import PlexService
```

Remove `self._plex = PlexService(db_session_factory)` on line 76. The `__init__` body becomes:

```python
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        provider_registry: ProviderRegistry,
        metadata_service: MetadataService,
        ws_manager: WebSocketManager,
        nas_queue: NasIOQueue,
        download_dir: Path,
        max_concurrent: int = 2,
    ):
        self._db = db_session_factory
        self._registry = provider_registry
        self._worker = DownloadWorker(provider_registry, metadata_service)
        self._ws = ws_manager
        self._nas_queue = nas_queue
        self._download_dir = download_dir
        self._local_temp = LOCAL_TEMP_DIR
        self._default_max_concurrent = max_concurrent
        self._active_tasks: dict[int, asyncio.Task] = {}
        self._worker_task: asyncio.Task | None = None
```

Delete the entire `_maybe_trigger_plex_scan` method (lines 321-335):

```python
# DELETE this entire method:
    async def _maybe_trigger_plex_scan(self) -> None:
        """Trigger Plex library scan when no more active items remain."""
        try:
            async with self._db() as session:
                result = await session.execute(
                    select(Download).where(
                        Download.status.in_(["queued", "downloading", "finalizing"])
                    ).limit(1)
                )
                if result.scalars().first() is not None:
                    return  # Still active
            if await self._plex.is_configured():
                await self._plex.trigger_library_scan()
        except Exception as exc:
            logger.error("Plex scan trigger failed: %s", exc)
```

Remove the call `await self._maybe_trigger_plex_scan()` on line 511 inside `on_move_success`. The method becomes:

```python
            async def on_move_success(final_path: Path) -> None:
                await _db_execute_with_retry(
                    self._db,
                    update(Download)
                    .where(Download.id == dl_info["id"])
                    .values(
                        status="completed",
                        file_path=str(final_path),
                        completed_at=datetime.utcnow(),
                    ),
                )
                await self._ws.broadcast({
                    "type": "status_change",
                    "download_id": dl_info["id"],
                    "status": "completed",
                    "file_path": str(final_path),
                    "completed_at": datetime.utcnow().isoformat(),
                })
                logger.info(
                    "NAS move completed: %s EP%s -> %s",
                    dl_info["anime_title"],
                    dl_info["episode_number"],
                    final_path,
                )
```

- [ ] **Step 3: Remove Plex from settings schema**

Replace `backend/app/schemas/setting.py` entirely:

```python
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    download_dir: str
    host_download_path: str
    max_concurrent_downloads: int
    telegram_bot_token: str
    telegram_chat_id: str


class SettingsUpdate(BaseModel):
    download_dir: str | None = None
    max_concurrent_downloads: int | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
```

- [ ] **Step 4: Remove Plex from settings service**

In `backend/app/services/settings_service.py`, replace the `DEFAULTS` dict and update `get_settings` / `update_settings`:

```python
DEFAULTS = {
    "download_dir": app_settings.download_dir,
    "max_concurrent_downloads": str(app_settings.max_concurrent_downloads),
    "telegram_bot_token": "",
    "telegram_chat_id": "",
}
```

Update `get_settings`:

```python
    async def get_settings(self) -> SettingsResponse:
        values = dict(DEFAULTS)
        async with self._db() as session:
            result = await session.execute(select(Setting))
            for setting in result.scalars().all():
                values[setting.key] = setting.value

        return SettingsResponse(
            download_dir=values["download_dir"],
            host_download_path=app_settings.host_download_path,
            max_concurrent_downloads=int(values["max_concurrent_downloads"]),
            telegram_bot_token=values.get("telegram_bot_token", ""),
            telegram_chat_id=values.get("telegram_chat_id", ""),
        )
```

Update `update_settings`:

```python
    async def update_settings(self, update: SettingsUpdate) -> SettingsResponse:
        async with self._db() as session:
            if update.download_dir is not None:
                await self._upsert(session, "download_dir", update.download_dir)
            if update.max_concurrent_downloads is not None:
                await self._upsert(
                    session,
                    "max_concurrent_downloads",
                    str(update.max_concurrent_downloads),
                )
            if update.telegram_bot_token is not None:
                await self._upsert(session, "telegram_bot_token", update.telegram_bot_token)
            if update.telegram_chat_id is not None:
                await self._upsert(session, "telegram_chat_id", update.telegram_chat_id)
            await session.commit()

        return await self.get_settings()
```

- [ ] **Step 5: Verify the app starts without import errors**

```bash
cd /Users/marybookpro/IdeaProjects/AnimeUnityDownloaderHasasiero
python -c "from backend.app.services.download_service import DownloadService; print('OK')"
```

Expected: `OK` (no ImportError for plex_service)

- [ ] **Step 6: Commit**

```bash
git add -u backend/app/services/plex_service.py backend/app/services/download_service.py backend/app/services/settings_service.py backend/app/schemas/setting.py
git commit -m "refactor: remove Plex integration from backend"
```

---

## Task 2: Create NotificationService

**Files:**
- Create: `backend/app/services/notification_service.py`

- [ ] **Step 1: Create the notification service**

Create `backend/app/services/notification_service.py`:

```python
"""Notification service — sends Telegram messages via Bot API."""
from __future__ import annotations

import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.setting import Setting

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class NotificationService:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]):
        self._db = db_session_factory

    async def _get_telegram_config(self) -> tuple[str, str]:
        """Return (bot_token, chat_id) from DB settings."""
        async with self._db() as session:
            token_setting = await session.get(Setting, "telegram_bot_token")
            chat_setting = await session.get(Setting, "telegram_chat_id")
        return (
            token_setting.value if token_setting else "",
            chat_setting.value if chat_setting else "",
        )

    async def is_configured(self) -> bool:
        token, chat_id = await self._get_telegram_config()
        return bool(token and chat_id)

    async def send_telegram(self, text: str) -> bool:
        """Send a message via Telegram Bot API. Returns True on success."""
        token, chat_id = await self._get_telegram_config()
        if not token or not chat_id:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{TELEGRAM_API}/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                    },
                )
                response.raise_for_status()
            logger.info("Telegram notification sent successfully")
            return True
        except Exception as exc:
            logger.error("Failed to send Telegram notification: %s", exc)
            return False

    async def notify_scheduled_downloads(
        self, results: list[dict[str, object]]
    ) -> None:
        """Send a summary of scheduled download results.

        results: [{"anime_title": str, "episode_count": int}]
        Only called when len(results) > 0.
        """
        if not await self.is_configured():
            return

        lines = ["\U0001f4e5 <b>Download programmati avviati</b>\n"]
        total = 0
        for r in results:
            title = r["anime_title"]
            count = r["episode_count"]
            total += count
            lines.append(f"{title} — {count} {'episodio' if count == 1 else 'episodi'}")
        lines.append(f"\nTotale: {total} {'episodio' if total == 1 else 'episodi'}")

        await self.send_telegram("\n".join(lines))
```

- [ ] **Step 2: Verify import**

```bash
cd /Users/marybookpro/IdeaProjects/AnimeUnityDownloaderHasasiero
python -c "from backend.app.services.notification_service import NotificationService; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/notification_service.py
git commit -m "feat: add NotificationService for Telegram Bot API"
```

---

## Task 3: Wire NotificationService into ScheduledDownloadService and main.py

**Files:**
- Modify: `backend/app/services/scheduled_download_service.py:30-43,186-216`
- Modify: `backend/app/main.py:89-95`
- Modify: `backend/app/api/deps.py`

- [ ] **Step 1: Add NotificationService to ScheduledDownloadService**

In `backend/app/services/scheduled_download_service.py`, add the import after line 21:

```python
from .notification_service import NotificationService
```

Update `__init__` to accept the notification service:

```python
class ScheduledDownloadService:
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        provider_registry: ProviderRegistry,
        download_service: DownloadService,
        notification_service: NotificationService,
    ) -> None:
        self._db = db_session_factory
        self._registry = provider_registry
        self._download_service = download_service
        self._notification = notification_service
        self._task: asyncio.Task | None = None
        self._base_dir = Path(settings.download_dir)
        self._next_run_at: datetime | None = None
```

- [ ] **Step 2: Update `_tick()` to collect results and send notification**

Replace the `_tick` method's schedule-execution loop (lines 195-216) with result collection and notification:

```python
    async def _tick(self) -> None:
        now = datetime.now()
        cron = await self.get_cron()

        if self._next_run_at is None:
            self._next_run_at = self._next_run(cron, now)

        if now < self._next_run_at:
            return

        logger.info("Scheduled cron triggered (%s), checking all schedules...", cron)

        # Run all enabled schedules
        async with self._db() as session:
            result = await session.execute(
                select(ScheduledDownload).where(ScheduledDownload.enabled == 1)
            )
            rows = list(result.scalars().all())

        notification_results = []
        for row in rows:
            try:
                enqueued, reason = await self._execute(row.id)
                logger.info(
                    "Schedule %d (%s): enqueued %d episodes%s",
                    row.id,
                    row.anime_title,
                    enqueued,
                    f" — {reason}" if reason else "",
                )
                if enqueued > 0:
                    notification_results.append({
                        "anime_title": row.anime_title,
                        "episode_count": enqueued,
                    })
            except Exception as exc:
                logger.error("Schedule %d failed: %s", row.id, exc)
                async with self._db() as session:
                    fresh = await session.get(ScheduledDownload, row.id)
                    if fresh:
                        fresh.last_error = str(exc)
                        fresh.last_run_at = datetime.now()
                        await session.commit()

        # Send Telegram notification summary
        if notification_results:
            try:
                await self._notification.notify_scheduled_downloads(notification_results)
            except Exception as exc:
                logger.error("Failed to send scheduled download notification: %s", exc)

        # Advance to next run
        self._next_run_at = self._next_run(cron, datetime.now())
        logger.info("Next scheduled run: %s", self._next_run_at)
```

- [ ] **Step 3: Wire in main.py**

In `backend/app/main.py`, add the import after line 20:

```python
from .services.notification_service import NotificationService
```

Update the `ScheduledDownloadService` instantiation (around lines 89-95) to create and pass `NotificationService`:

```python
    notification_service = NotificationService(async_session)
    app.state.notification_service = notification_service

    scheduled_download_service = ScheduledDownloadService(
        db_session_factory=async_session,
        provider_registry=registry,
        download_service=download_service,
        notification_service=notification_service,
    )
```

- [ ] **Step 4: Add dependency getter in deps.py**

In `backend/app/api/deps.py`, add the import:

```python
from ..services.notification_service import NotificationService
```

Add the getter function at the end:

```python
def get_notification_service(request: Request) -> NotificationService:
    return request.app.state.notification_service
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scheduled_download_service.py backend/app/main.py backend/app/api/deps.py
git commit -m "feat: wire NotificationService into scheduled downloads and app lifecycle"
```

---

## Task 4: Add Telegram Test Endpoint

**Files:**
- Modify: `backend/app/api/settings.py`

- [ ] **Step 1: Add the test endpoint**

In `backend/app/api/settings.py`, add the import for `NotificationService` and the dep getter at the top:

```python
from ..services.notification_service import NotificationService
from .deps import get_settings_service, get_notification_service
```

(Replace the existing `from .deps import get_settings_service` line.)

Add the endpoint after the `update_settings` endpoint:

```python
@router.post("/settings/telegram/test")
async def test_telegram(
    notification: NotificationService = Depends(get_notification_service),
):
    """Send a test message to verify Telegram configuration."""
    if not await notification.is_configured():
        return {"success": False, "error": "Bot token e Chat ID sono richiesti"}
    success = await notification.send_telegram("Hasasiero: connessione Telegram OK")
    if success:
        return {"success": True}
    return {"success": False, "error": "Invio fallito — controlla token e chat ID"}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/settings.py
git commit -m "feat: add POST /api/settings/telegram/test endpoint"
```

---

## Task 5: Update Frontend Settings Types and API

**Files:**
- Modify: `frontend/src/types/settings.ts`
- Modify: `frontend/src/api/settings.ts`

- [ ] **Step 1: Update types**

Replace `frontend/src/types/settings.ts` entirely:

```typescript
export interface Settings {
  download_dir: string;
  host_download_path: string;
  max_concurrent_downloads: number;
  telegram_bot_token: string;
  telegram_chat_id: string;
}

export interface SettingsUpdate {
  download_dir?: string;
  max_concurrent_downloads?: number;
  telegram_bot_token?: string;
  telegram_chat_id?: string;
}
```

- [ ] **Step 2: Add testTelegram API function**

In `frontend/src/api/settings.ts`, add the function after `updateSettings`:

```typescript
export function testTelegram(): Promise<{ success: boolean; error?: string }> {
  return apiFetch('/settings/telegram/test', { method: 'POST' });
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/settings.ts frontend/src/api/settings.ts
git commit -m "feat: update frontend settings types and API for Telegram"
```

---

## Task 6: Replace Plex UI with Telegram in SettingsPage

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Replace the entire SettingsPage**

Replace `frontend/src/pages/SettingsPage.tsx` with:

```tsx
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, testTelegram } from '../api/settings';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
  });

  const [maxConcurrent, setMaxConcurrent] = useState(2);
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const [saved, setSaved] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string } | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => {
    if (settings) {
      setMaxConcurrent(settings.max_concurrent_downloads);
      setTelegramBotToken(settings.telegram_bot_token || '');
      setTelegramChatId(settings.telegram_chat_id || '');
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
      telegram_bot_token: telegramBotToken,
      telegram_chat_id: telegramChatId,
    });
  };

  const handleTestTelegram = async () => {
    setTestLoading(true);
    setTestResult(null);
    try {
      const result = await testTelegram();
      setTestResult(result);
    } catch {
      setTestResult({ success: false, error: 'Errore di rete' });
    }
    setTestLoading(false);
    setTimeout(() => setTestResult(null), 4000);
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
      </div>

      {/* Telegram Notifications */}
      <div className="bg-bg-secondary border border-border rounded-[5px] p-6 space-y-5">
        <h2 className="text-lg font-semibold text-text-white">Notifiche Telegram</h2>
        <p className="text-xs text-text-secondary">
          Ricevi un riepilogo su Telegram al termine di ogni ciclo di download programmati.
        </p>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-text-white">
            Bot Token
          </label>
          <input
            type="password"
            value={telegramBotToken}
            onChange={(e) => setTelegramBotToken(e.target.value)}
            placeholder="123456:ABC-DEF1234..."
            className="w-full px-4 py-2.5 bg-bg-primary border border-border rounded-[5px] text-text-white text-sm focus:outline-none focus:border-accent transition-colors placeholder:text-text-secondary/50"
          />
          <p className="text-[11px] text-text-secondary">
            Crea un bot con <span className="text-accent">@BotFather</span> su Telegram e copia il token.
          </p>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-text-white">
            Chat ID
          </label>
          <input
            type="text"
            value={telegramChatId}
            onChange={(e) => setTelegramChatId(e.target.value)}
            placeholder="es. 123456789"
            className="w-full px-4 py-2.5 bg-bg-primary border border-border rounded-[5px] text-text-white text-sm focus:outline-none focus:border-accent transition-colors placeholder:text-text-secondary/50"
          />
          <p className="text-[11px] text-text-secondary">
            Invia un messaggio al bot, poi apri <span className="text-accent">https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</span> per trovare il tuo chat ID.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleTestTelegram}
            disabled={testLoading || !telegramBotToken || !telegramChatId}
            className="px-4 py-2 bg-bg-primary border border-border text-text-white text-sm rounded-[5px] hover:border-accent disabled:opacity-50 transition-colors"
          >
            {testLoading ? 'Invio...' : 'Invia test'}
          </button>
          {testResult && (
            <span className={`text-sm font-medium ${testResult.success ? 'text-success' : 'text-error'}`}>
              {testResult.success ? 'Messaggio inviato!' : testResult.error}
            </span>
          )}
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3">
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
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat: replace Plex UI with Telegram notifications in settings"
```

---

## Task 7: Add Countdown Auto-play to VideoPlayer

**Files:**
- Modify: `frontend/src/components/VideoPlayer.tsx`

- [ ] **Step 1: Replace VideoPlayer with auto-play support**

Replace `frontend/src/components/VideoPlayer.tsx` entirely:

```tsx
import { useEffect, useRef, useState, useCallback } from 'react';
import Hls from 'hls.js';

interface VideoPlayerProps {
  url: string;
  type: 'mp4' | 'm3u8';
  onClose: () => void;
  title?: string;
  onNext?: () => void;
  nextEpisodeLabel?: string;
}

const COUNTDOWN_SECONDS = 5;

export function VideoPlayer({ url, type, onClose, title, onNext, nextEpisodeLabel }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearCountdown = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setShowCountdown(false);
    setCountdown(COUNTDOWN_SECONDS);
  }, []);

  const handlePlayNow = useCallback(() => {
    clearCountdown();
    onNext?.();
  }, [clearCountdown, onNext]);

  const handleCancel = useCallback(() => {
    clearCountdown();
  }, [clearCountdown]);

  // Stream setup
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Reset countdown state on new URL
    clearCountdown();
    setError(null);

    if (type === 'm3u8') {
      if (Hls.isSupported()) {
        const hls = new Hls({
          maxBufferLength: 60,
          maxMaxBufferLength: 120,
        });
        hlsRef.current = hls;
        hls.loadSource(url);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          video.play().catch(() => {});
        });
        hls.on(Hls.Events.ERROR, (_event, data) => {
          if (data.fatal) {
            setError(`Errore streaming: ${data.details}`);
          }
        });
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url;
        video.addEventListener('loadedmetadata', () => {
          video.play().catch(() => {});
        });
      } else {
        setError('Il browser non supporta lo streaming HLS');
      }
    } else {
      video.src = url;
      video.addEventListener('loadedmetadata', () => {
        video.play().catch(() => {});
      });
    }

    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [url, type, clearCountdown]);

  // Video ended — start countdown if next episode available
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleEnded = () => {
      if (!onNext) return;
      setShowCountdown(true);
      setCountdown(COUNTDOWN_SECONDS);
    };

    video.addEventListener('ended', handleEnded);
    return () => video.removeEventListener('ended', handleEnded);
  }, [onNext]);

  // Countdown timer
  useEffect(() => {
    if (!showCountdown) return;

    intervalRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearCountdown();
          onNext?.();
          return COUNTDOWN_SECONDS;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [showCountdown, onNext, clearCountdown]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearCountdown();
        onClose();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose, clearCountdown]);

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={onClose}>
      <div
        className="relative w-full max-w-5xl mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          {title && (
            <span className="text-white text-sm font-medium truncate mr-4">{title}</span>
          )}
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors ml-auto"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error ? (
          <div className="bg-bg-secondary rounded-lg p-8 text-center text-error">
            {error}
          </div>
        ) : (
          <div className="relative">
            <video
              ref={videoRef}
              controls
              autoPlay
              className="w-full rounded-lg bg-black"
              style={{ maxHeight: '80vh' }}
            />

            {/* Countdown overlay */}
            {showCountdown && (
              <div className="absolute inset-0 bg-black/80 rounded-lg flex flex-col items-center justify-center gap-4">
                <p className="text-white/70 text-sm">Prossimo episodio tra</p>
                <span className="text-white text-5xl font-bold tabular-nums">{countdown}</span>
                {nextEpisodeLabel && (
                  <p className="text-white/90 text-base font-medium">{nextEpisodeLabel}</p>
                )}
                <div className="flex gap-3 mt-2">
                  <button
                    onClick={handlePlayNow}
                    className="px-5 py-2 bg-accent text-white text-sm font-medium rounded-[5px] hover:bg-accent-hover transition-colors"
                  >
                    Riproduci ora
                  </button>
                  <button
                    onClick={handleCancel}
                    className="px-5 py-2 bg-white/10 text-white text-sm rounded-[5px] hover:bg-white/20 transition-colors"
                  >
                    Annulla
                  </button>
                </div>
                {/* Progress bar */}
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10 rounded-b-lg overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-1000 ease-linear"
                    style={{ width: `${(countdown / COUNTDOWN_SECONDS) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/VideoPlayer.tsx
git commit -m "feat: add Netflix-style countdown auto-play to VideoPlayer"
```

---

## Task 8: Wire Next Episode Logic in AnimeDetailPage

**Files:**
- Modify: `frontend/src/pages/AnimeDetailPage.tsx`

- [ ] **Step 1: Update AnimeDetailPage**

In `frontend/src/pages/AnimeDetailPage.tsx`, add `useMemo` to the React import on line 1:

```typescript
import { useState, useCallback, useMemo } from 'react';
```

Add `currentEpisode` state after `streamInfo` state (line 17):

```typescript
  const [streamInfo, setStreamInfo] = useState<{ url: string; type: 'mp4' | 'm3u8'; title: string } | null>(null);
  const [currentEpisode, setCurrentEpisode] = useState<Episode | null>(null);
```

Update `handleWatch` (line 174) to track the current episode:

```typescript
  const handleWatch = useCallback(
    async (episode: Episode) => {
      if (!anime) return;
      try {
        setCurrentEpisode(episode);
        const resp = await fetch(`/api/stream/source/${episode.id}?site=${encodeURIComponent(site)}`);
        if (!resp.ok) throw new Error('Impossibile ottenere lo stream');
        const data = await resp.json();
        setStreamInfo({
          url: data.url,
          type: data.type,
          title: `${anime.title} — Ep. ${episode.number}`,
        });
      } catch (err) {
        setCurrentEpisode(null);
        alert(`Errore streaming: ${(err as Error).message}`);
      }
    },
    [anime, site],
  );
```

Add the `nextEpisode` computed value and `handleNext` callback after `handleWatch`:

```typescript
  const nextEpisode = useMemo(() => {
    if (!currentEpisode || !episodesData?.episodes) return null;
    const currentNum = parseFloat(currentEpisode.number);
    return episodesData.episodes.find((ep) => parseFloat(ep.number) > currentNum) || null;
  }, [currentEpisode, episodesData?.episodes]);

  const handleNext = useCallback(() => {
    if (nextEpisode) handleWatch(nextEpisode);
  }, [nextEpisode, handleWatch]);
```

Update the `VideoPlayer` JSX (around line 321) to pass the new props:

```tsx
      {/* Video Player Overlay */}
      {streamInfo && (
        <VideoPlayer
          url={streamInfo.url}
          type={streamInfo.type}
          title={streamInfo.title}
          onClose={() => { setStreamInfo(null); setCurrentEpisode(null); }}
          onNext={nextEpisode ? handleNext : undefined}
          nextEpisodeLabel={
            nextEpisode
              ? `Ep. ${nextEpisode.number}${nextEpisode.title ? ` — ${nextEpisode.title}` : ''}`
              : undefined
          }
        />
      )}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AnimeDetailPage.tsx
git commit -m "feat: wire next episode auto-play into AnimeDetailPage"
```

---

## Task 9: Manual Verification

- [ ] **Step 1: Build frontend and check for TypeScript errors**

```bash
cd /Users/marybookpro/IdeaProjects/AnimeUnityDownloaderHasasiero/frontend
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 2: Verify backend starts**

```bash
cd /Users/marybookpro/IdeaProjects/AnimeUnityDownloaderHasasiero
python -c "from backend.app.main import app; print('App created OK')"
```

Expected: `App created OK`

- [ ] **Step 3: Verify no leftover Plex references**

```bash
cd /Users/marybookpro/IdeaProjects/AnimeUnityDownloaderHasasiero
grep -ri "plex" backend/app/ frontend/src/ --include="*.py" --include="*.ts" --include="*.tsx" | grep -v node_modules | grep -v __pycache__
```

Expected: No output (no Plex references remain).
