from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class TrackedAnime(Base):
    __tablename__ = "tracked_animes"
    __table_args__ = (UniqueConstraint("anime_id", "source_site"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    anime_id: Mapped[int] = mapped_column(Integer, nullable=False)
    anime_slug: Mapped[str] = mapped_column(Text, nullable=False)
    anime_title: Mapped[str] = mapped_column(Text, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    genres: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    plot: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_site: Mapped[str] = mapped_column(Text, nullable=False, default="animeunity")
    last_known_episode: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # SQLite bool
    check_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
