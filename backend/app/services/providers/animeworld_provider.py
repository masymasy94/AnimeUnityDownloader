"""AnimeWorld site provider — animeworld.so support.

NOTE: This is a working stub. The actual AnimeWorld API/scraping logic
needs to be implemented by studying the site's structure.
"""

from __future__ import annotations

import logging
import re

from curl_cffi.requests import AsyncSession

from ...schemas.anime import AnimeDetail, AnimeSearchResult, Episode
from .base import SiteProvider, VideoSource

logger = logging.getLogger(__name__)

BASE_URL = "https://www.animeworld.so"


class AnimeWorldProvider(SiteProvider):
    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def _ensure_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(
                impersonate="chrome",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": BASE_URL,
                },
                timeout=30,
            )
        return self._session

    @property
    def site_id(self) -> str:
        return "animeworld"

    @property
    def site_name(self) -> str:
        return "AnimeWorld"

    async def search(self, title: str) -> list[AnimeSearchResult]:
        session = await self._ensure_session()
        response = await session.get(f"{BASE_URL}/search", params={"keyword": title})
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for card in soup.select(".film-list .item"):
            link = card.select_one("a.name")
            if not link:
                continue

            href = link.get("href", "")
            # Extract slug from URL like /play/anime-name.XXXXX
            slug_match = re.search(r"/play/(.+?)(?:\.|$)", href)
            slug = slug_match.group(1) if slug_match else ""

            # Extract ID from URL (last part after dot)
            id_match = re.search(r"\.(\w+)$", href)
            anime_id = hash(href) % 1_000_000 if not id_match else int(id_match.group(1), 36) if id_match else 0

            img = card.select_one("img")
            cover_url = img.get("src") if img else None

            title_text = link.get_text(strip=True)

            # Extract type and year from info
            info = card.select_one(".info")
            anime_type = None
            year = None
            if info:
                type_el = info.select_one(".type")
                if type_el:
                    anime_type = type_el.get_text(strip=True)

            results.append(
                AnimeSearchResult(
                    id=anime_id,
                    slug=slug,
                    title=title_text,
                    cover_url=cover_url,
                    type=anime_type,
                    year=year,
                )
            )

        return results

    async def get_latest(self) -> list[AnimeSearchResult]:
        session = await self._ensure_session()
        response = await session.get(f"{BASE_URL}/updated")
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for card in soup.select(".film-list .item"):
            link = card.select_one("a.name")
            if not link:
                continue

            href = link.get("href", "")
            slug_match = re.search(r"/play/(.+?)(?:\.|$)", href)
            slug = slug_match.group(1) if slug_match else ""
            anime_id = hash(href) % 1_000_000

            img = card.select_one("img")
            cover_url = img.get("src") if img else None
            title_text = link.get_text(strip=True)

            results.append(
                AnimeSearchResult(
                    id=anime_id,
                    slug=slug,
                    title=title_text,
                    cover_url=cover_url,
                )
            )

        return results

    async def get_anime_info(self, anime_id: int, slug: str) -> AnimeDetail:
        session = await self._ensure_session()
        response = await session.get(f"{BASE_URL}/play/{slug}")
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        title = ""
        title_el = soup.select_one("h2.title")
        if title_el:
            title = title_el.get_text(strip=True)

        cover_url = None
        cover_el = soup.select_one(".thumb img")
        if cover_el:
            cover_url = cover_el.get("src")

        plot = None
        plot_el = soup.select_one(".desc")
        if plot_el:
            plot = plot_el.get_text(strip=True)

        genres = []
        for genre_el in soup.select(".info .genre a"):
            genres.append(genre_el.get_text(strip=True))

        return AnimeDetail(
            id=anime_id,
            slug=slug,
            title=title or slug,
            cover_url=cover_url,
            plot=plot,
            genres=genres,
        )

    async def get_episodes(
        self, anime_id: int, slug: str, start: int = 1, end: int | None = None
    ) -> tuple[list[Episode], int]:
        session = await self._ensure_session()
        response = await session.get(f"{BASE_URL}/play/{slug}")
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        episodes = []
        for ep_el in soup.select(".server.active .episodes a"):
            ep_num = ep_el.get("data-num", ep_el.get_text(strip=True))
            ep_id_str = ep_el.get("data-id", "0")
            try:
                ep_id = int(ep_id_str)
            except ValueError:
                ep_id = hash(ep_id_str) % 1_000_000

            episodes.append(
                Episode(
                    id=ep_id,
                    number=str(ep_num),
                )
            )

        total = len(episodes)

        # Apply range filter
        if end is None:
            end = total
        filtered = [ep for ep in episodes if start <= int(ep.number) <= end] if episodes else []

        return filtered, total

    async def resolve_download_url(self, episode_id: int) -> VideoSource:
        session = await self._ensure_session()
        # AnimeWorld has a JSON API endpoint for getting download links
        response = await session.get(
            f"{BASE_URL}/api/episode/info",
            params={"id": str(episode_id)},
        )
        response.raise_for_status()
        data = response.json()

        download_url = data.get("grabber", "")
        if not download_url:
            raise ValueError(f"No download URL found for episode {episode_id}")

        return VideoSource(
            url=download_url,
            type="direct_mp4",
            headers={"Referer": BASE_URL},
        )

    async def get_http_session(self):
        return await self._ensure_session()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
