from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.anime import SearchResponse
from ..services.providers import ProviderRegistry
from .deps import get_provider_registry

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_anime(
    title: str = Query(..., min_length=1),
    site: str = Query("animeunity"),
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    try:
        provider = registry.get(site)
        results = await provider.search(title)
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}") from exc


@router.get("/latest", response_model=SearchResponse)
async def latest_anime(
    site: str = Query("animeunity"),
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    try:
        provider = registry.get(site)
        results = await provider.get_latest()
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Latest fetch failed: {exc}") from exc
