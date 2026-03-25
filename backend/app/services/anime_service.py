import logging
import re

from ..schemas.anime import AnimeDetail, Episode
from .animeunity_client import AnimeUnityClient

logger = logging.getLogger(__name__)

MAX_EPISODES_PER_REQUEST = 120


def _extract_episode_title(file_name: str | None) -> str | None:
    """Extract human-readable episode title from file_name like
    'One.Piece.S01E01.Il.ragazzo.di.gomma.1080p.AMZN.WEB-DL.JPN.AAC2.0.H.264.mkv'
    """
    if not file_name:
        return None
    # Remove extension
    name = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', file_name)
    # Try to find title after SxxExx pattern
    m = re.search(r'S\d+E\d+[.\s](.+?)(?:[.\s](?:\d{3,4}p|WEB|BDRip|DVDRip|HDTV|BluRay|AMZN|NF))', name, re.IGNORECASE)
    if m:
        return m.group(1).replace('.', ' ').strip()
    # Fallback: try after episode number pattern
    m = re.search(r'(?:E|EP|Episode[.\s]?)\d+[.\s](.+?)(?:[.\s](?:\d{3,4}p|WEB|BDRip|DVDRip|HDTV|BluRay|AMZN|NF))', name, re.IGNORECASE)
    if m:
        return m.group(1).replace('.', ' ').strip()
    return None


class AnimeService:
    def __init__(self, client: AnimeUnityClient):
        self._client = client

    async def get_anime_info(self, anime_id: int, slug: str) -> AnimeDetail:
        """Fetch anime details from info_api."""
        data = await self._client.get_json(f"/info_api/{anime_id}-{slug}")

        genres = []
        if data.get("genres"):
            for g in data["genres"]:
                if isinstance(g, dict):
                    genres.append(g.get("name", ""))
                elif isinstance(g, str):
                    genres.append(g)

        return AnimeDetail(
            id=data.get("id", anime_id),
            slug=data.get("slug") or slug,
            title=data.get("title") or data.get("title_eng") or "Senza titolo",
            title_eng=data.get("title_eng"),
            cover_url=data.get("imageurl"),
            banner_url=data.get("imageurl_cover"),
            plot=data.get("plot"),
            type=data.get("type"),
            year=data.get("date"),
            episodes_count=data.get("episodes_count"),
            genres=genres,
            status=data.get("status"),
            dub=bool(data.get("dub", False)),
        )

    async def get_episodes(
        self, anime_id: int, slug: str, start: int = 0, end: int | None = None
    ) -> tuple[list[Episode], int]:
        """
        Fetch episodes with automatic pagination.
        Returns (episodes, total_count).
        """
        # First get total count
        info = await self._client.get_json(f"/info_api/{anime_id}-{slug}")
        total = info.get("episodes_count", 0)

        if end is None:
            end = total
        if start <= 0:
            start = 1

        episodes: list[Episode] = []
        current_start = start

        while current_start <= end:
            batch_end = min(current_start + MAX_EPISODES_PER_REQUEST - 1, end)
            data = await self._client.get_json(
                f"/info_api/{anime_id}-{slug}/0",
                params={"start_range": current_start, "end_range": batch_end},
            )

            ep_list = data.get("episodes", []) if isinstance(data, dict) else data
            for ep in ep_list:
                episodes.append(
                    Episode(
                        id=ep["id"],
                        number=str(ep.get("number", "")),
                        title=_extract_episode_title(ep.get("file_name")),
                        created_at=ep.get("created_at"),
                        views=ep.get("visite"),
                    )
                )

            current_start = batch_end + 1

        return episodes, total
