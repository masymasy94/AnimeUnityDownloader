import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from ..models.download import Download
from ..schemas.anime import AnimeDetail, Episode, EpisodesResponse
from ..services.providers import ProviderRegistry
from .deps import get_provider_registry, get_db_session_factory

router = APIRouter()

_PATH_RE = re.compile(r"^(\d+)-(.+)$")


def _parse_anime_path(anime_path: str) -> tuple[int, str]:
    m = _PATH_RE.match(anime_path)
    if not m:
        raise HTTPException(400, "Invalid path, expected {id}-{slug}")
    return int(m.group(1)), m.group(2)


@router.get("/anime/{anime_path:path}/episodes", response_model=EpisodesResponse)
async def get_episodes(
    anime_path: str,
    start: int = Query(1, ge=1),
    end: int | None = Query(None),
    site: str = Query("animeunity"),
    registry: ProviderRegistry = Depends(get_provider_registry),
    db_factory=Depends(get_db_session_factory),
):
    anime_id, slug = _parse_anime_path(anime_path)
    try:
        provider = registry.get(site)
        episodes, total = await provider.get_episodes(anime_id, slug, start, end)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    episode_ids = [ep.id for ep in episodes]
    async with db_factory() as db:
        result = await db.execute(
            select(Download.episode_id, Download.status).where(
                Download.anime_id == anime_id,
                Download.episode_id.in_(episode_ids),
            )
        )
        statuses = {row[0]: row[1] for row in result.all()}

    enriched = [
        Episode(
            id=ep.id,
            number=ep.number,
            title=ep.title,
            created_at=ep.created_at,
            views=ep.views,
            download_status=statuses.get(ep.id),
        )
        for ep in episodes
    ]
    has_more = (end or total) < total if total else False
    return EpisodesResponse(episodes=enriched, total=total, has_more=has_more)


@router.get("/anime/{anime_path:path}", response_model=AnimeDetail)
async def get_anime_detail(
    anime_path: str,
    site: str = Query("animeunity"),
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    anime_id, slug = _parse_anime_path(anime_path)
    try:
        provider = registry.get(site)
        return await provider.get_anime_info(anime_id, slug)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
