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


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    pix_key: Mapped[str] = mapped_column(
        String(255)
    )

    pix_key_type: Mapped[str] = mapped_column(
        String(30)
    )

    status: Mapped[str] = mapped_column(
        String(20)
    )

    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
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

    user: Mapped["User"] = relationship(
        "User",
        back_populates="withdraw_requests"
    )
