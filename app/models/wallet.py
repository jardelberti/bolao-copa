from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00")
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="wallet"
    )

    transactions: Mapped[list["WalletTransaction"]] = relationship(
        "WalletTransaction",
        back_populates="wallet"
    )
