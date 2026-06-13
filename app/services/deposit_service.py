from decimal import Decimal
from decimal import InvalidOperation

from sqlalchemy.orm import Session

from app.models.deposit_request import DepositRequest
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction

PENDING_STATUS = "PENDING"
APPROVED_STATUS = "APPROVED"
REJECTED_STATUS = "REJECTED"


class DepositServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def approve_deposit(
    db: Session,
    deposit_id: int,
    credited_amount: str,
    notes: str | None,
) -> DepositRequest:
    deposit_request = db.get(DepositRequest, deposit_id)

    if not deposit_request:
        raise DepositServiceError("Solicitação de depósito não encontrada.")

    if deposit_request.status != PENDING_STATUS:
        raise DepositServiceError(
            "Somente solicitações pendentes podem ser aprovadas.")

    amount = _parse_amount(credited_amount)

    if amount <= Decimal("0"):
        raise DepositServiceError("O valor creditado deve ser maior que zero.")

    wallet = db.query(Wallet).filter(Wallet.user_id ==
                                     deposit_request.user_id).first()

    if not wallet:
        raise DepositServiceError("Carteira do usuário não encontrada.")

    try:
        deposit_request.status = APPROVED_STATUS
        deposit_request.credited_amount = amount
        deposit_request.notes = _clean_notes(notes)

        wallet.balance += amount

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="DEPOSIT",
            amount=amount,
            description="Depósito aprovado",
        )
        db.add(transaction)
        db.commit()
        db.refresh(deposit_request)
    except Exception:
        db.rollback()
        raise

    return deposit_request


def reject_deposit(
    db: Session,
    deposit_id: int,
    notes: str | None,
) -> DepositRequest:
    deposit_request = db.get(DepositRequest, deposit_id)

    if not deposit_request:
        raise DepositServiceError("Solicitação de depósito não encontrada.")

    if deposit_request.status != PENDING_STATUS:
        raise DepositServiceError(
            "Somente solicitações pendentes podem ser rejeitadas.")

    try:
        deposit_request.status = REJECTED_STATUS
        deposit_request.notes = _clean_notes(notes)
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
        raise DepositServiceError(
            "Informe um valor creditado válido.") from exc


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None

    notes = notes.strip()
    return notes or None
