"""Async I/O queue for NAS operations.

All file moves, stat() checks, and disk-usage queries against the NAS go
through this queue so that the main asyncio event loop is never blocked —
even when the NAS is slow, saturated, or temporarily unreachable.
"""

import asyncio
import logging
import shutil
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

MOVE_MAX_RETRIES = 10
MOVE_RETRY_BASE_DELAY = 15  # seconds (15, 30, 45, …)
DISK_USAGE_CACHE_TTL = 30  # seconds
FILE_EXISTS_CACHE_TTL = 60  # seconds


class NasIOQueue:
    """Manages all NAS I/O through an async queue + thread pool."""

    def __init__(self, nas_dir: Path, max_workers: int = 2):
        self._nas_dir = nas_dir
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: list[asyncio.Task] = []
        self._max_workers = max_workers
        # Caches
        self._disk_cache: dict | None = None
        self._disk_cache_ts: float = 0
        self._file_cache: dict[str, tuple[bool, float]] = {}

    # ── Lifecycle ──

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()

    def start(self) -> None:
        for i in range(self._max_workers):
            task = asyncio.create_task(
                self._process_loop(), name=f"nas-worker-{i}"
            )
            self._worker_tasks.append(task)
        logger.info(
            "NAS I/O queue started (%d workers, target: %s)",
            self._max_workers,
            self._nas_dir,
        )

    async def stop(self) -> None:
        for task in self._worker_tasks:
            task.cancel()
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        logger.info("NAS I/O queue stopped")

    # ── File move ──

    async def enqueue_move(
        self,
        local_path: Path,
        nas_path: Path,
        on_success: Callable[[Path], Awaitable[None]],
        on_failure: Callable[[Exception], Awaitable[None]],
    ) -> None:
        """Enqueue a file move from local storage to NAS.

        The move runs in a background thread with automatic retry.
        *on_success(nas_path)* or *on_failure(exc)* is called when done.
        """
        await self._queue.put((local_path, nas_path, on_success, on_failure))
        logger.info(
            "Enqueued NAS move: %s -> %s (queue depth: %d)",
            local_path.name,
            nas_path.parent.name,
            self._queue.qsize(),
        )

    async def _process_loop(self) -> None:
        while True:
            try:
                item = await self._queue.get()
                local_path, nas_path, on_success, on_failure = item
                await self._move_with_retry(
                    local_path, nas_path, on_success, on_failure
                )
                self._queue.task_done()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("NAS queue unexpected error: %s", exc)

    async def _move_with_retry(
        self,
        local_path: Path,
        nas_path: Path,
        on_success: Callable[[Path], Awaitable[None]],
        on_failure: Callable[[Exception], Awaitable[None]],
    ) -> None:
        last_exc: Exception | None = None

        for attempt in range(1, MOVE_MAX_RETRIES + 1):
            try:
                await asyncio.to_thread(
                    self._move_file_sync, local_path, nas_path
                )
                # Invalidate cache for this path
                self._file_cache.pop(str(nas_path), None)
                logger.info("NAS move succeeded: %s", nas_path.name)
                await on_success(nas_path)
                return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < MOVE_MAX_RETRIES:
                    delay = MOVE_RETRY_BASE_DELAY * attempt
                    logger.warning(
                        "NAS move failed (attempt %d/%d): %s — retrying in %ds",
                        attempt,
                        MOVE_MAX_RETRIES,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)

        logger.error(
            "NAS move permanently failed after %d attempts: %s",
            MOVE_MAX_RETRIES,
            last_exc,
        )
        await on_failure(
            last_exc or RuntimeError("NAS move failed after max retries")
        )

    @staticmethod
    def _move_file_sync(local_path: Path, nas_path: Path) -> None:
        """Blocking file move — always runs in a thread."""
        nas_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(local_path), str(nas_path))
        # Try to clean up the now-empty parent dir in local temp
        try:
            local_path.parent.rmdir()
        except OSError:
            pass  # Not empty or already gone

    # ── Cached NAS queries ──

    async def get_disk_usage(self) -> dict:
        """Return NAS disk usage (cached for DISK_USAGE_CACHE_TTL seconds)."""
        now = time.monotonic()
        if self._disk_cache and now - self._disk_cache_ts < DISK_USAGE_CACHE_TTL:
            return self._disk_cache

        try:
            usage = await asyncio.to_thread(shutil.disk_usage, self._nas_dir)
            self._disk_cache = {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "path": str(self._nas_dir),
            }
            self._disk_cache_ts = now
        except Exception as exc:
            logger.error("Failed to get NAS disk usage: %s", exc)
            if not self._disk_cache:
                self._disk_cache = {
                    "total_bytes": 0,
                    "used_bytes": 0,
                    "free_bytes": 0,
                    "path": str(self._nas_dir),
                }
        return self._disk_cache

    async def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists on NAS (cached for FILE_EXISTS_CACHE_TTL seconds)."""
        now = time.monotonic()
        cached = self._file_cache.get(file_path)
        if cached and now - cached[1] < FILE_EXISTS_CACHE_TTL:
            return cached[0]

        try:
            exists = await asyncio.to_thread(Path(file_path).is_file)
            self._file_cache[file_path] = (exists, now)
            return exists
        except Exception:
            return False
