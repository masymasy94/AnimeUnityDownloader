from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ...schemas.anime import AnimeDetail, AnimeSearchResult, Episode


@dataclass
class VideoSource:
    url: str
    type: str  # "direct_mp4" or "m3u8"
    headers: dict | None = None


class SiteProvider(ABC):
    """Interface that every anime site provider must implement."""

    @property
    @abstractmethod
    def site_id(self) -> str:
        """Unique identifier, e.g. 'animeunity', 'animeworld'."""

    @property
    @abstractmethod
    def site_name(self) -> str:
        """Human-readable name, e.g. 'AnimeUnity'."""

    @abstractmethod
    async def search(self, title: str) -> list[AnimeSearchResult]:
        ...

    @abstractmethod
    async def get_latest(self) -> list[AnimeSearchResult]:
        ...

    @abstractmethod
    async def get_anime_info(self, anime_id: int, slug: str) -> AnimeDetail:
        ...

    @abstractmethod
    async def get_episodes(
        self, anime_id: int, slug: str, start: int = 1, end: int | None = None
    ) -> tuple[list[Episode], int]:
        ...

    @abstractmethod
    async def resolve_download_url(self, episode_id: int) -> VideoSource:
        ...

    @abstractmethod
    async def get_http_session(self):
        """Return an HTTP session for file downloads (e.g. curl_cffi AsyncSession)."""
        ...

    @abstractmethod
    async def close(self) -> None:
        ...
