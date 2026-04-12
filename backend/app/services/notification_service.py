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
