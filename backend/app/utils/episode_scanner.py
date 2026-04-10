"""Scan a folder for existing episode files and return the highest number."""
import re
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}

# Ordered by specificity — most specific patterns first.
_PATTERNS = [
    # S01E010, S1E10, s01e010
    re.compile(r"[Ss]\d{1,2}[Ee](\d{1,4})"),
    # Ep_01, EP.05, Ep 3, Episode 12, Episodio 3
    re.compile(r"(?:[Ee]pisod(?:e|io)|[Ee][Pp])[\s_.\-]*(\d{1,4})"),
    # " - 01 ", " - 01.", " - 01[" — fansub style: [Group] Show - 01 [1080p].mp4
    re.compile(r"[\s_]-[\s_](\d{1,4})(?=[\s_.\[\]])"),
    # _03_ or .03. — surrounded by separators: ShowName_03_ITA.mp4
    re.compile(r"[\s_.\-](\d{1,4})[\s_.\-]"),
    # Trailing number before extension: Show 07.mp4
    re.compile(r"(\d{1,4})(?=\s*\.[^.]+$)"),
]


def highest_episode(folder: Path) -> int:
    """Return the highest episode number found under `folder` (recursive).

    Returns 0 when the folder is missing or no episodes are detected.
    Only files with video extensions are considered.
    """
    if not folder.exists() or not folder.is_dir():
        return 0

    highest = 0
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        number = _extract_episode_number(path.name)
        if number is not None and number > highest:
            highest = number

    return highest


def _extract_episode_number(filename: str) -> int | None:
    for regex in _PATTERNS:
        match = regex.search(filename)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None
