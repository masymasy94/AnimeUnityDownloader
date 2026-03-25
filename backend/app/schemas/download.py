from datetime import datetime

from pydantic import BaseModel


class EpisodeDownloadRequest(BaseModel):
    episode_id: int
    episode_number: str


class DownloadRequest(BaseModel):
    anime_id: int
    anime_title: str
    anime_slug: str
    cover_url: str | None = None
    genres: list[str] = []
    plot: str | None = None
    year: str | None = None
    episodes: list[EpisodeDownloadRequest]


class DownloadStatus(BaseModel):
    id: int
    anime_id: int
    anime_title: str
    anime_slug: str
    episode_id: int
    episode_number: str
    status: str
    progress: float
    downloaded_bytes: int
    total_bytes: int
    speed_bps: int
    file_path: str | None
    host_file_path: str | None = None
    file_exists: bool = False
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class DownloadsResponse(BaseModel):
    downloads: list[DownloadStatus]
