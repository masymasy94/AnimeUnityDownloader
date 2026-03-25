import logging

from curl_cffi.requests import AsyncSession, Response

from ..config import settings

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": settings.animeunity_base_url,
}


class AnimeUnityClient:
    """HTTP client with browser TLS fingerprint impersonation for Cloudflare bypass."""

    def __init__(
        self,
        base_url: str | None = None,
        impersonate: str | None = None,
    ):
        self._base_url = base_url or settings.animeunity_base_url
        self._impersonate = impersonate or settings.impersonate_browser
        self._session: AsyncSession | None = None

    async def _ensure_session(self) -> AsyncSession:
        if self._session is None:
            self._session = AsyncSession(
                impersonate=self._impersonate,
                headers=BROWSER_HEADERS,
                timeout=30,
            )
        return self._session

    async def get(self, path: str, params: dict | None = None) -> Response:
        session = await self._ensure_session()
        url = f"{self._base_url}{path}"
        logger.debug("GET %s params=%s", url, params)
        response = await session.get(url, params=params)
        response.raise_for_status()
        return response

    async def get_html(self, path: str, params: dict | None = None) -> str:
        response = await self.get(path, params)
        return response.text

    async def get_json(self, path: str, params: dict | None = None) -> dict | list:
        response = await self.get(path, params)
        return response.json()

    async def get_text(self, path: str) -> str:
        response = await self.get(path)
        return response.text.strip()

    async def post_json(self, path: str, data: dict | None = None, headers: dict | None = None) -> dict | list:
        session = await self._ensure_session()
        url = f"{self._base_url}{path}"
        logger.debug("POST %s data=%s", url, data)
        response = await session.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_bytes_stream(self, url: str, headers: dict | None = None):
        """Stream a full URL (not a path). Used for file downloads."""
        session = await self._ensure_session()
        response = await session.get(url, headers=headers, stream=True)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
