from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import UniqueConstraint
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Bet(Base):
    __tablename__ = "bets"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "game_id",
            "home_score_guess",
            "away_score_guess",
            name="uq_bets_user_game_score_guess",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id")
    )

    home_score_guess: Mapped[int] = mapped_column(
        Integer
    )

    away_score_guess: Mapped[int] = mapped_column(
        Integer
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    is_winner: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=func.now()
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="bets"
    )

    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="bets"
    )
