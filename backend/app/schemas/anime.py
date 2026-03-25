from pydantic import BaseModel


class AnimeSearchResult(BaseModel):
    id: int
    slug: str
    title: str
    title_eng: str | None = None
    cover_url: str | None = None
    type: str | None = None
    year: str | None = None
    episodes_count: int | None = None
    genres: list[str] = []
    dub: bool = False


class AnimeDetail(BaseModel):
    id: int
    slug: str
    title: str
    title_eng: str | None = None
    cover_url: str | None = None
    banner_url: str | None = None
    plot: str | None = None
    type: str | None = None
    year: str | None = None
    episodes_count: int | None = None
    genres: list[str] = []
    status: str | None = None
    dub: bool = False


class Episode(BaseModel):
    id: int
    number: str
    title: str | None = None
    created_at: str | None = None
    views: int | None = None
    download_status: str | None = None


class EpisodesResponse(BaseModel):
    episodes: list[Episode]
    total: int
    has_more: bool


class SearchResponse(BaseModel):
    results: list[AnimeSearchResult]
