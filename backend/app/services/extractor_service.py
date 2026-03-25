import logging
import re
from dataclasses import dataclass

from ..utils.retry import retry
from .animeunity_client import AnimeUnityClient

logger = logging.getLogger(__name__)

DOWNLOAD_URL_PATTERN = re.compile(r"window\.downloadUrl\s*=\s*['\"](.+?)['\"]")
VIDEO_URL_PATTERN = re.compile(r"url:\s*['\"](.+?)['\"]")
TOKEN_PATTERN = re.compile(r"token':\s*['\"](.+?)['\"]")
EXPIRES_PATTERN = re.compile(r"expires':\s*['\"](.+?)['\"]")


@dataclass
class VideoSource:
    url: str
    type: str  # "direct_mp4" or "m3u8"
    headers: dict | None = None


class ExtractorService:
    """Resolves episode IDs to downloadable video URLs via VixCloud."""

    def __init__(self, client: AnimeUnityClient):
        self._client = client

    @retry(max_attempts=3, retryable=(Exception,))
    async def resolve_download_url(self, episode_id: int) -> VideoSource:
        """
        Just-in-time URL resolution. Must be called immediately before download
        because tokens expire within minutes.

        1. GET /embed-url/{episode_id} → VixCloud embed URL
        2. GET embed page → extract window.downloadUrl (direct MP4)
        3. Fallback: extract M3U8 playlist URL
        """
        # Step 1: Get embed URL from AnimeUnity
        embed_url = await self._client.get_text(f"/embed-url/{episode_id}")
        logger.debug("Embed URL for episode %d: %s", episode_id, embed_url)

        if not embed_url or not embed_url.startswith("http"):
            raise ExtractionError(f"Invalid embed URL for episode {episode_id}: {embed_url}")

        # Step 2: Fetch the VixCloud embed page
        session = await self._client._ensure_session()
        response = await session.get(embed_url, headers={"Referer": self._client._base_url})
        embed_html = response.text

        # Step 3: Try direct MP4 download URL
        mp4_match = DOWNLOAD_URL_PATTERN.search(embed_html)
        if mp4_match:
            mp4_url = mp4_match.group(1)
            logger.info("Found direct MP4 URL for episode %d", episode_id)
            return VideoSource(
                url=mp4_url,
                type="direct_mp4",
                headers={"Referer": embed_url},
            )

        # Step 4: Fallback to M3U8 playlist
        url_match = VIDEO_URL_PATTERN.search(embed_html)
        token_match = TOKEN_PATTERN.search(embed_html)
        expires_match = EXPIRES_PATTERN.search(embed_html)

        if url_match and token_match and expires_match:
            playlist_url = (
                f"{url_match.group(1)}"
                f"?token={token_match.group(1)}"
                f"&referer="
                f"&expires={expires_match.group(1)}"
                f"&h=1"
            )
            logger.info("Found M3U8 playlist for episode %d", episode_id)
            return VideoSource(
                url=playlist_url,
                type="m3u8",
                headers={"Referer": embed_url},
            )

        raise ExtractionError(
            f"Could not extract video URL for episode {episode_id}"
        )


class ExtractionError(Exception):
    pass
