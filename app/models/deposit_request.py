from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class DepositRequest(Base):
    __tablename__ = "deposit_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    credited_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20)
    )

    proof_image: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
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
        back_populates="deposit_requests"
    )
