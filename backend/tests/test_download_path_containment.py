"""Compito 1: AnimeSaturn IDs must be stable across process restarts
(zlib.crc32, not hash() — the latter is randomized per-process via
PYTHONHASHSEED).

Compito 2: DownloadWorker must reject a dest_folder_override that escapes
download_dir (e.g. via "../"), while a legitimate folder-browser selection
still works.
"""
from __future__ import annotations

import asyncio
import zlib
from pathlib import Path

import pytest

from app.services.download_worker import DownloadError, DownloadWorker
from app.services.providers.animesaturn_provider import AnimeSaturnProvider
from app.services.providers.base import VideoSource

# ── Compito 1: stable AnimeSaturn IDs ──

_CARD_HTML = """
<div class="item-archivio">
  <a href="/anime/mob-psycho-100">
    <img src="https://example.org/cover.jpg">
    <div class="info-archivio"><h3><a>Mob Psycho 100</a></h3></div>
  </a>
</div>
"""

_EPISODES_HTML = """
<a class="bottone-ep" href="/ep/Mob-Psycho-100-ep-1">1</a>
<a class="bottone-ep" href="/ep/Mob-Psycho-100-ep-2">2</a>
"""


def test_parse_card_list_id_is_deterministic_crc32():
    provider = AnimeSaturnProvider()
    results_1 = provider._parse_card_list(_CARD_HTML)
    results_2 = provider._parse_card_list(_CARD_HTML)

    assert results_1[0].id == results_2[0].id
    # Proves the id comes from crc32(slug), not Python's randomized hash():
    # a fixed independent computation must match exactly.
    expected = zlib.crc32("mob-psycho-100".encode()) % 10_000_000
    assert results_1[0].id == expected


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


class _FakeSession:
    async def get(self, *args, **kwargs):
        return _FakeResponse(_EPISODES_HTML)


def test_get_episodes_id_is_deterministic_crc32():
    provider = AnimeSaturnProvider()
    provider._ensure_session = lambda: _async_return(_FakeSession())  # type: ignore[assignment]

    episodes, total = asyncio.run(provider.get_episodes(1, "mob-psycho-100"))

    assert total == 2
    expected_ids = [
        zlib.crc32(f"/ep/Mob-Psycho-100-ep-{n}".encode()) % 10_000_000
        for n in (1, 2)
    ]
    assert [e.id for e in episodes] == expected_ids
    # Fetching again must yield the exact same ids (same process, same slug).
    episodes_again, _ = asyncio.run(provider.get_episodes(1, "mob-psycho-100"))
    assert [e.id for e in episodes_again] == expected_ids


async def _async_return(value):
    return value


# ── Compito 2: dest_folder_override containment ──

def _worker() -> DownloadWorker:
    # Bypass __init__ (provider registry / metadata service DB wiring not
    # needed) — same pattern as test_partial_cleanup.py's _service().
    worker = object.__new__(DownloadWorker)
    worker._registry = _FakeRegistry()
    worker._metadata = _FakeMetadataService()
    return worker


class _FakeProvider:
    async def resolve_download_url(self, episode_id: int) -> VideoSource:
        return VideoSource(url="http://example.org/video.mp4", type="direct_mp4")


class _FakeRegistry:
    def get(self, source_site: str) -> _FakeProvider:
        return _FakeProvider()


class _FakeMetadataService:
    async def embed_metadata(self, **kwargs) -> bool:
        return False  # forces the raw_path.rename(final_path) fallback


def test_dest_folder_override_escaping_download_dir_is_rejected(tmp_path: Path) -> None:
    worker = _worker()
    worker._download_mp4 = lambda *a, **k: _async_return(None)  # type: ignore[assignment]

    with pytest.raises(DownloadError, match="escapes download root"):
        asyncio.run(
            worker.download_episode(
                episode_id=1,
                episode_number="1",
                anime_title="Some Anime",
                anime_slug="some-anime",
                download_dir=tmp_path,
                source_site="animesaturn",
                dest_folder_override="../../etc",
            )
        )

    # Nothing must have been written outside tmp_path.
    assert not (tmp_path.parent / "etc").exists()


def test_dest_folder_override_legitimate_folder_still_works(tmp_path: Path) -> None:
    worker = _worker()

    async def fake_download_mp4(source, dest_path, progress_callback):
        dest_path.write_bytes(b"fake video bytes")

    worker._download_mp4 = fake_download_mp4  # type: ignore[assignment]

    final_path = asyncio.run(
        worker.download_episode(
            episode_id=1,
            episode_number="1",
            anime_title="Some Anime",
            anime_slug="some-anime",
            download_dir=tmp_path,
            source_site="animesaturn",
            dest_folder_override="MyChosenFolder",
        )
    )

    assert final_path.is_relative_to(tmp_path / "MyChosenFolder")
    assert final_path.exists()
