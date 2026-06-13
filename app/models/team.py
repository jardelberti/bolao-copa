from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    code: Mapped[str] = mapped_column(
        String(5),
        unique=True
    )

    flag_url: Mapped[str] = mapped_column(
        String(255)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=func.now()
    )

    home_games: Mapped[list["Game"]] = relationship(
        "Game",
        back_populates="home_team",
        foreign_keys="Game.home_team_id"
    )

    away_games: Mapped[list["Game"]] = relationship(
        "Game",
        back_populates="away_team",
        foreign_keys="Game.away_team_id"
    )
