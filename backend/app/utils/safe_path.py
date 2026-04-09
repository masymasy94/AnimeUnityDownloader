"""Path security helper — resolves user-supplied paths inside a base dir."""
from pathlib import Path


class PathOutsideBaseError(ValueError):
    """Raised when a resolved path falls outside the base directory."""


def resolve_inside(base: Path, user_path: str) -> Path:
    """Resolve `user_path` relative to `base` and verify it stays inside.

    - Empty string resolves to `base` itself.
    - Leading slashes on `user_path` are stripped (treated as relative).
    - Path components are normalized; if the resolved result is not a
      descendant of `base`, `PathOutsideBaseError` is raised.
    - The target does not need to exist.
    """
    base_resolved = base.resolve()
    cleaned = (user_path or "").lstrip("/")
    candidate = (base_resolved / cleaned).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise PathOutsideBaseError(
            f"Path {user_path!r} escapes base {base_resolved}"
        ) from exc
    return candidate
