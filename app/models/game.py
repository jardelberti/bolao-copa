from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

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