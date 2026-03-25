from fastapi import APIRouter, Depends, HTTPException

from ..schemas.tracked import (
    TrackAnimeRequest,
    TrackedAnimeResponse,
    TrackedAnimeUpdate,
    TrackedListResponse,
)
from ..services.tracker_service import TrackerService
from .deps import get_tracker_service

router = APIRouter()


@router.get("/tracked", response_model=TrackedListResponse)
async def list_tracked(svc: TrackerService = Depends(get_tracker_service)):
    tracked = await svc.list_tracked()
    return TrackedListResponse(
        tracked=[TrackedAnimeResponse.model_validate(t) for t in tracked]
    )


@router.post("/tracked", response_model=TrackedAnimeResponse, status_code=201)
async def track_anime(
    request: TrackAnimeRequest,
    svc: TrackerService = Depends(get_tracker_service),
):
    try:
        tracked = await svc.add_tracked(request)
        return TrackedAnimeResponse.model_validate(tracked)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tracked/check-status")
async def check_tracked_status(
    anime_id: int,
    source_site: str = "animeunity",
    svc: TrackerService = Depends(get_tracker_service),
):
    tracked = await svc.is_tracked(anime_id, source_site)
    if tracked:
        return {"tracked": True, "id": tracked.id}
    return {"tracked": False}


@router.put("/tracked/{tracked_id}", response_model=TrackedAnimeResponse)
async def update_tracked(
    tracked_id: int,
    update: TrackedAnimeUpdate,
    svc: TrackerService = Depends(get_tracker_service),
):
    tracked = await svc.update_tracked(tracked_id, update)
    if not tracked:
        raise HTTPException(status_code=404, detail="Tracked anime not found")
    return TrackedAnimeResponse.model_validate(tracked)


@router.delete("/tracked/{tracked_id}", status_code=204)
async def untrack_anime(
    tracked_id: int,
    svc: TrackerService = Depends(get_tracker_service),
):
    deleted = await svc.remove_tracked(tracked_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tracked anime not found")


@router.post("/tracked/{tracked_id}/check")
async def check_now(
    tracked_id: int,
    svc: TrackerService = Depends(get_tracker_service),
):
    new_episodes = await svc.check_now(tracked_id)
    return {"new_episodes": new_episodes}
