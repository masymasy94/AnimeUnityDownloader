from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.anime import SearchResponse
from ..services.search_service import SearchService
from .deps import get_search_service

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_anime(
    title: str = Query(..., min_length=1),
    svc: SearchService = Depends(get_search_service),
):
    try:
        results = await svc.search(title)
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Search failed: {exc}") from exc


@router.get("/latest", response_model=SearchResponse)
async def latest_anime(
    svc: SearchService = Depends(get_search_service),
):
    try:
        results = await svc.get_latest()
        return SearchResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Latest fetch failed: {exc}") from exc
