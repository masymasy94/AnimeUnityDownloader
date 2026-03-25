from datetime import datetime

from pydantic import BaseModel


class TrackAnimeRequest(BaseModel):
    anime_id: int
    anime_slug: str
    anime_title: str
    cover_url: str | None = None
    genres: list[str] = []
    plot: str | None = None
    year: str | None = None
    source_site: str = "animeunity"
    check_interval_minutes: int = 60


class TrackedAnimeResponse(BaseModel):
    id: int
    anime_id: int
    anime_slug: str
    anime_title: str
    cover_url: str | None
    source_site: str
    last_known_episode: int
    enabled: bool
    check_interval_minutes: int
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrackedAnimeUpdate(BaseModel):
    enabled: bool | None = None
    check_interval_minutes: int | None = None


class TrackedListResponse(BaseModel):
    tracked: list[TrackedAnimeResponse]
