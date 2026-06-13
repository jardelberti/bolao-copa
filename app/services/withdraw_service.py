from decimal import Decimal
from decimal import InvalidOperation

from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.models.withdraw_request import WithdrawRequest

PENDING_STATUS = "PENDING"
APPROVED_STATUS = "APPROVED"
REJECTED_STATUS = "REJECTED"


class WithdrawServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def create_withdraw_request(
    db: Session,
    user_id: int,
    requested_amount: str,
    pix_key_type: str,
    pix_key: str,
) -> WithdrawRequest:
    amount = _parse_amount(requested_amount)
    pix_key_type = _clean_required(pix_key_type, "Informe o tipo da chave PIX.")
    pix_key = _clean_required(pix_key, "Informe a chave PIX.")

    if amount <= Decimal("0"):
        raise WithdrawServiceError("O valor solicitado deve ser maior que zero.")

    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

    if not wallet:
        raise WithdrawServiceError("Carteira do usuário não encontrada.")

    if wallet.balance < amount:
        raise WithdrawServiceError("Saldo insuficiente para solicitar o saque.")

    withdraw_request = WithdrawRequest(
        user_id=user_id,
        requested_amount=amount,
        pix_key=pix_key,
        pix_key_type=pix_key_type,
        status=PENDING_STATUS,
        notes=None,
    )

    try:
        db.add(withdraw_request)
        db.commit()
        db.refresh(withdraw_request)
    except Exception:
        db.rollback()
        raise

    return withdraw_request


def approve_withdraw(
    db: Session,
    withdraw_id: int,
    notes: str | None = None,
) -> WithdrawRequest:
    withdraw_request = db.get(WithdrawRequest, withdraw_id)

    if not withdraw_request:
        raise WithdrawServiceError("Solicitação de saque não encontrada.")

    if withdraw_request.status != PENDING_STATUS:
        raise WithdrawServiceError("Somente solicitações pendentes podem ser aprovadas.")

    wallet = db.query(Wallet).filter(Wallet.user_id == withdraw_request.user_id).first()

    if not wallet:
        raise WithdrawServiceError("Carteira do usuário não encontrada.")

    amount = _to_money(withdraw_request.requested_amount)

    if wallet.balance < amount:
        raise WithdrawServiceError("Saldo insuficiente para aprovar o saque.")

    try:
        wallet.balance -= amount
        withdraw_request.status = APPROVED_STATUS
        withdraw_request.notes = _clean_notes(notes)

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type="WITHDRAW",
            amount=-amount,
            description="Saque aprovado",
        )
        db.add(transaction)
        db.commit()
        db.refresh(withdraw_request)
    except Exception:
        db.rollback()
        raise

    return withdraw_request


def reject_withdraw(
    db: Session,
    withdraw_id: int,
    notes: str | None = None,
) -> WithdrawRequest:
    withdraw_request = db.get(WithdrawRequest, withdraw_id)

    if not withdraw_request:
        raise WithdrawServiceError("Solicitação de saque não encontrada.")

    if withdraw_request.status != PENDING_STATUS:
        raise WithdrawServiceError("Somente solicitações pendentes podem ser rejeitadas.")

    try:
        withdraw_request.status = REJECTED_STATUS
        withdraw_request.notes = _clean_notes(notes)
        db.commit()
        db.refresh(withdraw_request)
    except Exception:
        db.rollback()
        raise

    return withdraw_request


def _parse_amount(value: str) -> Decimal:
    try:
        return Decimal(value.strip().replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, AttributeError) as exc:
        raise WithdrawServiceError("Informe um valor solicitado válido.") from exc


def _to_money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))


def _clean_required(value: str | None, error_message: str) -> str:
    if value is None:
        raise WithdrawServiceError(error_message)

    value = value.strip()

    if not value:
        raise WithdrawServiceError(error_message)

    return value


def _clean_notes(notes: str | None) -> str | None:
    if notes is None:
        return None

    notes = notes.strip()
    return notes or None
