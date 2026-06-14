from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import func

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Base


class PaymentSettings(Base):
    __tablename__ = "payment_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    pix_key: Mapped[str] = mapped_column(
        String(255)
    )

    pix_key_type: Mapped[str] = mapped_column(
        String(30)
    )

    recipient_name: Mapped[str] = mapped_column(
        String(100)
    )

    recipient_city: Mapped[str] = mapped_column(
        String(100)
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
