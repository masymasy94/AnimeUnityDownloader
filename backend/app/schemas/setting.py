from pydantic import BaseModel


class SettingsResponse(BaseModel):
    download_dir: str
    host_download_path: str
    max_concurrent_downloads: int
    plex_url: str
    plex_token: str
    plex_library_id: str


class SettingsUpdate(BaseModel):
    download_dir: str | None = None
    max_concurrent_downloads: int | None = None
    plex_url: str | None = None
    plex_token: str | None = None
    plex_library_id: str | None = None
