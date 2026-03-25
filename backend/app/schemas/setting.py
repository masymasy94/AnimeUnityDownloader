from pydantic import BaseModel


class SettingsResponse(BaseModel):
    download_dir: str
    host_download_path: str
    max_concurrent_downloads: int


class SettingsUpdate(BaseModel):
    download_dir: str | None = None
    max_concurrent_downloads: int | None = None
