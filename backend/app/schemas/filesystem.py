from pydantic import BaseModel


class FolderEntry(BaseModel):
    name: str
    path: str  # relative to /downloads
    is_dir: bool


class BrowseResponse(BaseModel):
    current_path: str  # relative to /downloads ("" == root)
    parent_path: str | None
    entries: list[FolderEntry]


class MkdirRequest(BaseModel):
    parent_path: str  # relative to /downloads
    name: str
