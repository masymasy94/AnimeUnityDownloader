"""Dependency injection helpers — extract services from app.state."""

from fastapi import Request

from ..services.search_service import SearchService
from ..services.anime_service import AnimeService
from ..services.download_service import DownloadService
from ..services.settings_service import SettingsService
from ..services.ws_manager import WebSocketManager


def get_search_service(request: Request) -> SearchService:
    return request.app.state.search_service


def get_anime_service(request: Request) -> AnimeService:
    return request.app.state.anime_service


def get_download_service(request: Request) -> DownloadService:
    return request.app.state.download_service


def get_settings_service(request: Request) -> SettingsService:
    return request.app.state.settings_service


def get_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager


def get_db_session_factory(request: Request):
    return request.app.state.db_session_factory
