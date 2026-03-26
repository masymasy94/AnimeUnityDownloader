import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.anime import SearchResponse
from ..services.providers import ProviderRegistry
from .deps import get_provider_registry

logger = logging.getLogger(__name__)

router = APIRouter()


async def _search_provider(provider, title: str):
    """Search a single provider, returning results with source_site tagged."""
    try:
        results = await provider.search(title)
        for r in results:
            r.source_site = provider.site_id
        return results
    except Exception as exc:
        logger.warning("Search failed for %s: %s", provider.site_id, exc)
        return []


async def _latest_provider(provider):
    """Get latest from a single provider, tagged with source_site."""
    try:
        results = await provider.get_latest()
        for r in results:
            r.source_site = provider.site_id
        return results
    except Exception as exc:
        logger.warning("Latest failed for %s: %s", provider.site_id, exc)
        return []


@router.get("/search", response_model=SearchResponse)
async def search_anime(
    title: str = Query(..., min_length=1),
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    """Search all registered providers in parallel and merge results."""
    providers = registry.all_providers()
    tasks = [_search_provider(p, title) for p in providers]
    all_results = await asyncio.gather(*tasks)

    merged = []
    for results in all_results:
        merged.extend(results)

    return SearchResponse(results=merged)


@router.get("/latest", response_model=SearchResponse)
async def latest_anime(
    registry: ProviderRegistry = Depends(get_provider_registry),
):
    """Get latest from all providers in parallel."""
    providers = registry.all_providers()
    tasks = [_latest_provider(p) for p in providers]
    all_results = await asyncio.gather(*tasks)

    merged = []
    for results in all_results:
        merged.extend(results)

    return SearchResponse(results=merged)
