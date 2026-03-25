"""Plex webhook service — triggers library scan after downloads complete."""

import logging

import httpx

from ..models.setting import Setting
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class PlexService:
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession]):
        self._db = db_session_factory

    async def _get_plex_config(self) -> tuple[str, str, str]:
        """Return (plex_url, plex_token, plex_library_id) from DB settings."""
        async with self._db() as session:
            url_setting = await session.get(Setting, "plex_url")
            token_setting = await session.get(Setting, "plex_token")
            lib_setting = await session.get(Setting, "plex_library_id")
        return (
            url_setting.value if url_setting else "",
            token_setting.value if token_setting else "",
            lib_setting.value if lib_setting else "",
        )

    async def is_configured(self) -> bool:
        url, token, _ = await self._get_plex_config()
        return bool(url and token)

    async def trigger_library_scan(self) -> bool:
        """Trigger a Plex library scan. Returns True on success."""
        url, token, library_id = await self._get_plex_config()
        if not url or not token:
            return False

        try:
            scan_url = f"{url.rstrip('/')}/library/sections"
            if library_id:
                scan_url += f"/{library_id}/refresh"
            else:
                scan_url += "/all/refresh"

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    scan_url,
                    headers={"X-Plex-Token": token},
                )
                response.raise_for_status()

            logger.info("Plex library scan triggered successfully")
            return True
        except Exception as exc:
            logger.error("Failed to trigger Plex scan: %s", exc)
            return False
