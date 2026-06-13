from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("wallets.id")
    )

    transaction_type: Mapped[str] = mapped_column(
        String(30)
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2)
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    wallet: Mapped["Wallet"] = relationship(
        "Wallet",
        back_populates="transactions"
    )
