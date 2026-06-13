from decimal import Decimal
from decimal import InvalidOperation

from sqlalchemy.orm import Session

from app.models.deposit_request import DepositRequest

PENDING_STATUS = "PENDING"


class WalletDepositServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def create_deposit_request(
    db: Session,
    user_id: int,
    requested_amount: str,
    notes: str | None = None,
) -> DepositRequest:
    amount = _parse_amount(requested_amount)

    if amount <= Decimal("0"):
        raise WalletDepositServiceError("O valor solicitado deve ser maior que zero.")

    deposit_request = DepositRequest(
        user_id=user_id,
        requested_amount=amount,
        credited_amount=None,
        status=PENDING_STATUS,
        proof_image=None,
        notes=_clean_notes(notes),
    )

    try:
        db.add(deposit_request)
        db.commit()
        db.refresh(deposit_request)
    except Exception:
        db.rollback()
        raise

    return deposit_request


def _parse_amount(value: str) -> Decimal:
    try:
        return Decimal(value.strip().replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError) as exc:
        raise WalletDepositServiceError("Informe um valor solicitado válido.") from exc


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None

    notes = notes.strip()
    return notes or None
