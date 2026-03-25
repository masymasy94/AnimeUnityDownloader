from __future__ import annotations

from .base import SiteProvider


class ProviderRegistry:
    """Simple registry of available site providers."""

    def __init__(self) -> None:
        self._providers: dict[str, SiteProvider] = {}

    def register(self, provider: SiteProvider) -> None:
        self._providers[provider.site_id] = provider

    def get(self, site_id: str) -> SiteProvider:
        if site_id not in self._providers:
            raise ValueError(f"Unknown site provider: {site_id}")
        return self._providers[site_id]

    def list_sites(self) -> list[dict]:
        return [
            {"id": p.site_id, "name": p.site_name}
            for p in self._providers.values()
        ]

    @property
    def default(self) -> SiteProvider:
        return next(iter(self._providers.values()))

    async def close_all(self) -> None:
        for p in self._providers.values():
            await p.close()
