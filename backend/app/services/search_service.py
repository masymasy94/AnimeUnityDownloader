import logging
import re

from bs4 import BeautifulSoup

from ..schemas.anime import AnimeSearchResult
from .animeunity_client import AnimeUnityClient

logger = logging.getLogger(__name__)

CSRF_PATTERN = re.compile(r'<meta\s+name="csrf-token"\s+content="([^"]+)"')


class SearchService:
    def __init__(self, client: AnimeUnityClient):
        self._client = client
        self._csrf_token: str | None = None

    async def _get_csrf_token(self) -> str:
        """Fetch CSRF token from the archivio page."""
        if self._csrf_token:
            return self._csrf_token
        html = await self._client.get_html("/archivio")
        match = CSRF_PATTERN.search(html)
        if match:
            self._csrf_token = match.group(1)
            return self._csrf_token
        raise RuntimeError("Could not extract CSRF token from archivio page")

    async def search(self, title: str) -> list[AnimeSearchResult]:
        """Search anime using the POST /archivio/get-animes endpoint (full results)."""
        csrf = await self._get_csrf_token()

        # Fetch both sub and dub results
        all_results: dict[int, AnimeSearchResult] = {}

        # Request without dub filter (gets mixed results, max 30)
        data = await self._client.post_json(
            "/archivio/get-animes",
            data={"title": title, "offset": 0},
            headers={
                "X-CSRF-TOKEN": csrf,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        for item in self._extract_records(data):
            all_results[item.id] = item

        # Request with dub filter to ensure ITA versions are included
        data_dub = await self._client.post_json(
            "/archivio/get-animes",
            data={"title": title, "offset": 0, "dubbed": True},
            headers={
                "X-CSRF-TOKEN": csrf,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        for item in self._extract_records(data_dub):
            all_results[item.id] = item

        return list(all_results.values())

    async def get_latest(self) -> list[AnimeSearchResult]:
        """Fetch currently airing anime (In Corso)."""
        csrf = await self._get_csrf_token()
        data = await self._client.post_json(
            "/archivio/get-animes",
            data={"title": "", "offset": 0, "status": "In Corso"},
            headers={
                "X-CSRF-TOKEN": csrf,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        return self._extract_records(data)

    def _extract_records(self, data: dict | list) -> list[AnimeSearchResult]:
        if isinstance(data, dict):
            items = data.get("records", data.get("data", []))
        else:
            items = data

        results = []
        for item in items:
            genres = []
            if item.get("genres"):
                for g in item["genres"]:
                    if isinstance(g, dict):
                        genres.append(g.get("name", ""))
                    elif isinstance(g, str):
                        genres.append(g)

            results.append(
                AnimeSearchResult(
                    id=item["id"],
                    slug=item.get("slug") or "",
                    title=item.get("title") or item.get("title_eng") or "Senza titolo",
                    title_eng=item.get("title_eng"),
                    cover_url=item.get("imageurl"),
                    type=item.get("type"),
                    year=item.get("date"),
                    episodes_count=item.get("real_episodes_count") or item.get("episodes_count"),
                    genres=genres,
                    dub=bool(item.get("dub", False)),
                )
            )

        return results
