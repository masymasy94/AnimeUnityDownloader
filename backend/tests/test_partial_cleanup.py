"""Regression for the orphaned .part/.raw files bug: `_cleanup_partial_files`
must compute the exact same path `DownloadWorker.download_episode` writes to,
including when a scheduled download's `dest_folder_override` / `filename_template`
reroute the file away from the plain Plex layout. See download_service.py.
"""
from pathlib import Path

from app.services.download_service import DownloadService
from app.services.download_worker import resolve_episode_relative_path


def _service(local_temp: Path) -> DownloadService:
    # Bypass __init__ (it wires up DB/providers/ws/etc. we don't need here) —
    # _cleanup_partial_files only touches self._local_temp.
    svc = object.__new__(DownloadService)
    svc._local_temp = local_temp
    return svc


_OVERRIDE_KWARGS = dict(
    anime_title="Test Anime",
    episode_number="5",
    episode_title="A Title",
    dest_folder_override="Scheduled/MyShow",
    filename_template="{anime} - {episode}",
    filename_template_type="preset",
)


def test_cleanup_path_matches_worker_write_path(tmp_path: Path) -> None:
    """The relative path cleanup resolves to must equal the one the worker
    writes to, for a scheduled download with folder/filename overrides."""
    expected_relative = resolve_episode_relative_path(
        anime_title=_OVERRIDE_KWARGS["anime_title"],
        episode_number=_OVERRIDE_KWARGS["episode_number"],
        episode_title=_OVERRIDE_KWARGS["episode_title"],
        dest_folder_override=_OVERRIDE_KWARGS["dest_folder_override"],
        filename_template=_OVERRIDE_KWARGS["filename_template"],
        filename_template_type=_OVERRIDE_KWARGS["filename_template_type"],
    )
    worker_final_path = tmp_path / expected_relative  # what download_episode writes

    partial = worker_final_path.with_suffix(".mp4.raw.part")
    partial.parent.mkdir(parents=True)
    partial.write_bytes(b"partial data")

    svc = _service(tmp_path)
    svc._cleanup_partial_files(**_OVERRIDE_KWARGS)

    assert not partial.exists(), "cleanup did not find the file at the worker's real path"


def test_cleanup_removes_partial_and_raw_files(tmp_path: Path) -> None:
    expected_relative = resolve_episode_relative_path(
        anime_title=_OVERRIDE_KWARGS["anime_title"],
        episode_number=_OVERRIDE_KWARGS["episode_number"],
        episode_title=_OVERRIDE_KWARGS["episode_title"],
        dest_folder_override=_OVERRIDE_KWARGS["dest_folder_override"],
        filename_template=_OVERRIDE_KWARGS["filename_template"],
        filename_template_type=_OVERRIDE_KWARGS["filename_template_type"],
    )
    final_path = tmp_path / expected_relative
    final_path.parent.mkdir(parents=True)

    raw_part = final_path.with_suffix(".mp4.raw.part")
    raw = final_path.with_suffix(".mp4.raw")
    raw_part.write_bytes(b"1")
    raw.write_bytes(b"2")
    decoy = final_path.parent / "Some Other Show - S01E999.mp4.raw"
    decoy.write_bytes(b"3")

    svc = _service(tmp_path)
    svc._cleanup_partial_files(**_OVERRIDE_KWARGS)

    assert not raw_part.exists()
    assert not raw.exists()
    assert decoy.exists(), "cleanup must not touch files outside this episode's stem"


def test_cleanup_never_deletes_outside_local_temp(tmp_path: Path) -> None:
    local_temp = tmp_path / "animehub"
    local_temp.mkdir()

    # A file sitting in local_temp that would be wrongly swept if the escape
    # check were missing and cleanup fell back to scanning local_temp itself.
    decoy = local_temp / "Innocent Show - S01E001.mp4.raw"
    decoy.write_bytes(b"do not touch")

    svc = _service(local_temp)
    svc._cleanup_partial_files(
        anime_title="Escaping Anime",
        episode_number="1",
        dest_folder_override="../../etc",  # escapes local_temp once resolved
        filename_template="{anime} - {episode}",
        filename_template_type="preset",
    )

    assert decoy.exists()
    # Nothing outside local_temp must exist either — best-effort sanity check
    # that the escaping path itself was never created/touched.
    assert not (tmp_path / "etc").exists()
