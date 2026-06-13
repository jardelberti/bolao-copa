from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

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
