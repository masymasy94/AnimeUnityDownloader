from pathlib import Path

import pytest

from app.utils.safe_path import PathOutsideBaseError, resolve_inside


def test_empty_path_returns_base(tmp_path: Path) -> None:
    assert resolve_inside(tmp_path, "") == tmp_path.resolve()


def test_simple_relative_path(tmp_path: Path) -> None:
    (tmp_path / "anime" / "one-piece").mkdir(parents=True)
    result = resolve_inside(tmp_path, "anime/one-piece")
    assert result == (tmp_path / "anime" / "one-piece").resolve()


def test_leading_slash_is_treated_as_relative(tmp_path: Path) -> None:
    (tmp_path / "anime").mkdir()
    result = resolve_inside(tmp_path, "/anime")
    assert result == (tmp_path / "anime").resolve()


def test_dotdot_escape_raises(tmp_path: Path) -> None:
    with pytest.raises(PathOutsideBaseError):
        resolve_inside(tmp_path, "../etc")


def test_dotdot_after_subdir_escape_raises(tmp_path: Path) -> None:
    # Combine a fake subdir with `..` segments that climb above base.
    with pytest.raises(PathOutsideBaseError):
        resolve_inside(tmp_path, "anime/../../etc")


def test_nonexistent_subpath_is_ok(tmp_path: Path) -> None:
    # Resolve should succeed even when the path does not yet exist,
    # as long as it resolves inside base.
    result = resolve_inside(tmp_path, "anime/new-folder")
    assert result == (tmp_path / "anime" / "new-folder").resolve()
