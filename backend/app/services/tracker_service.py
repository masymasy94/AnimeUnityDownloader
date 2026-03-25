"""Tracker service — monitors followed series and auto-downloads new episodes."""

import asyncio
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models.tracked_anime import TrackedAnime
from ..schemas.download import DownloadRequest, EpisodeDownloadRequest
from ..schemas.tracked import TrackAnimeRequest, TrackedAnimeUpdate
from .download_service import DownloadService
from .providers import ProviderRegistry

logger = logging.getLogger(__name__)


class TrackerService:
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        provider_registry: ProviderRegistry,
        download_service: DownloadService,
    ):
        self._db = db_session_factory
        self._registry = provider_registry
        self._download_service = download_service
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Tracker service started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Tracker service stopped")

    # ── CRUD ──

    async def add_tracked(self, request: TrackAnimeRequest) -> TrackedAnime:
        async with self._db() as session:
            tracked = TrackedAnime(
                anime_id=request.anime_id,
                anime_slug=request.anime_slug,
                anime_title=request.anime_title,
                cover_url=request.cover_url,
                genres=json.dumps(request.genres) if request.genres else None,
                plot=request.plot,
                year=request.year,
                source_site=request.source_site,
                check_interval_minutes=request.check_interval_minutes,
            )
            session.add(tracked)
            await session.commit()
            await session.refresh(tracked)
            return tracked

    async def remove_tracked(self, tracked_id: int) -> bool:
        async with self._db() as session:
            tracked = await session.get(TrackedAnime, tracked_id)
            if tracked:
                await session.delete(tracked)
                await session.commit()
                return True
            return False

    async def update_tracked(self, tracked_id: int, update_data: TrackedAnimeUpdate) -> TrackedAnime | None:
        async with self._db() as session:
            tracked = await session.get(TrackedAnime, tracked_id)
            if not tracked:
                return None
            if update_data.enabled is not None:
                tracked.enabled = int(update_data.enabled)
            if update_data.check_interval_minutes is not None:
                tracked.check_interval_minutes = update_data.check_interval_minutes
            tracked.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(tracked)
            return tracked

    async def list_tracked(self) -> list[TrackedAnime]:
        async with self._db() as session:
            result = await session.execute(
                select(TrackedAnime).order_by(TrackedAnime.anime_title)
            )
            return list(result.scalars().all())

    async def is_tracked(self, anime_id: int, source_site: str) -> TrackedAnime | None:
        async with self._db() as session:
            result = await session.execute(
                select(TrackedAnime).where(
                    TrackedAnime.anime_id == anime_id,
                    TrackedAnime.source_site == source_site,
                )
            )
            return result.scalars().first()

    # ── Check for new episodes ──

    async def check_now(self, tracked_id: int) -> int:
        """Force-check a single tracked anime. Returns number of new episodes enqueued."""
        async with self._db() as session:
            tracked = await session.get(TrackedAnime, tracked_id)
            if not tracked:
                return 0
            return await self._check_one(tracked, session)

    async def _check_loop(self) -> None:
        """Background loop — every 60s checks which series are due for checking."""
        while True:
            try:
                await self._check_all_due()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Tracker loop error: %s", exc)
            await asyncio.sleep(60)

    async def _check_all_due(self) -> None:
        now = datetime.utcnow()
        async with self._db() as session:
            result = await session.execute(
                select(TrackedAnime).where(TrackedAnime.enabled == 1)
            )
            all_tracked = list(result.scalars().all())

        for tracked in all_tracked:
            if tracked.last_checked_at:
                next_check = tracked.last_checked_at + timedelta(minutes=tracked.check_interval_minutes)
                if now < next_check:
                    continue

            try:
                async with self._db() as session:
                    # Re-fetch to avoid detached instance
                    fresh = await session.get(TrackedAnime, tracked.id)
                    if fresh:
                        await self._check_one(fresh, session)
            except Exception as exc:
                logger.error("Check failed for %s: %s", tracked.anime_title, exc)

    async def _check_one(self, tracked: TrackedAnime, session: AsyncSession) -> int:
        """Check one anime for new episodes and enqueue if found."""
        provider = self._registry.get(tracked.source_site)
        episodes, total = await provider.get_episodes(
            tracked.anime_id, tracked.anime_slug,
            start=tracked.last_known_episode + 1,
        )

        new_count = 0
        if episodes:
            request = DownloadRequest(
                anime_id=tracked.anime_id,
                anime_title=tracked.anime_title,
                anime_slug=tracked.anime_slug,
                cover_url=tracked.cover_url,
                genres=json.loads(tracked.genres) if tracked.genres else [],
                plot=tracked.plot,
                year=tracked.year,
                source_site=tracked.source_site,
                episodes=[
                    EpisodeDownloadRequest(
                        episode_id=ep.id,
                        episode_number=ep.number,
                        episode_title=ep.title,
                    )
                    for ep in episodes
                ],
            )
            downloads = await self._download_service.enqueue(request)
            new_count = len(downloads)

            # Update last known episode to total
            tracked.last_known_episode = total
            logger.info(
                "Auto-download: %d new episodes for %s",
                new_count, tracked.anime_title,
            )

        tracked.last_checked_at = datetime.utcnow()
        tracked.updated_at = datetime.utcnow()
        await session.commit()

        return new_count
