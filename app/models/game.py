from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id")
    )

    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id")
    )

    match_datetime: Mapped[datetime] = mapped_column(
        DateTime
    )

    bet_price: Mapped[float] = mapped_column(
        Numeric(10, 2)
    )

    jackpot_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0
    )

    home_score: Mapped[int | None] = mapped_column(
        nullable=True
    )

    away_score: Mapped[int | None] = mapped_column(
        nullable=True
    )

    home_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="home_games",
        foreign_keys=[home_team_id]
    )

    away_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="away_games",
        foreign_keys=[away_team_id]
    )

    bets: Mapped[list["Bet"]] = relationship(
        "Bet",
        back_populates="game"
    )
