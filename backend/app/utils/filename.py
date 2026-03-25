import re
import unicodedata


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Sanitize a string for use as a filesystem name."""
    # Normalize unicode
    name = unicodedata.normalize("NFC", name)
    # Replace invalid chars with underscore
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Strip leading/trailing dots and spaces
    name = name.strip(". ")
    # Collapse multiple underscores/spaces
    name = re.sub(r"[_\s]+", " ", name)
    # Truncate
    if len(name) > max_length:
        name = name[:max_length].rstrip()
    return name or "unknown"


def episode_filename(anime_title: str, episode_number: str, total_episodes: int) -> str:
    """Generate a clean episode filename like 'Naruto Shippuden/EP001.mp4'."""
    folder = sanitize_filename(anime_title)
    # Determine padding based on total episodes
    pad = 3 if total_episodes >= 100 else 2
    # Handle non-numeric episode numbers (OVA, 5.5, etc.)
    try:
        num = int(float(episode_number))
        ep_str = f"EP{num:0{pad}d}"
    except (ValueError, TypeError):
        ep_str = f"EP{sanitize_filename(str(episode_number))}"
    return f"{folder}/{ep_str}.mp4"
