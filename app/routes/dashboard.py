from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.bet import Bet
from app.models.wallet_transaction import WalletTransaction
from app.services.auth_service import require_current_user

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    current_user = require_current_user(request, db)
    user = db.merge(current_user)

    wallet = user.wallet if user else None
    total_bets = _total_bets(db, user.id)
    total_bet_amount = _money(
        db.query(func.coalesce(func.sum(Bet.amount), 0))
        .filter(Bet.user_id == user.id)
        .scalar()
    )

    total_prizes = _transaction_sum(db, wallet.id, "PRIZE") if wallet else Decimal("0.00")
    total_refunds = _transaction_sum(db, wallet.id, "REFUND") if wallet else Decimal("0.00")
    transactions = _latest_transactions(db, wallet.id) if wallet else []

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Dashboard",
            "current_user": current_user,
            "user": user,
            "wallet": wallet,
            "total_bets": total_bets,
            "total_bet_amount": total_bet_amount,
            "total_prizes": total_prizes,
            "total_refunds": total_refunds,
            "transactions": transactions,
        },
    )


def _total_bets(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(Bet.id))
        .filter(Bet.user_id == user_id)
        .scalar()
        or 0
    )


def _transaction_sum(db: Session, wallet_id: int, transaction_type: str) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .filter(
            WalletTransaction.wallet_id == wallet_id,
            WalletTransaction.transaction_type == transaction_type,
        )
        .scalar()
    )
    return _money(total)


def _latest_transactions(db: Session, wallet_id: int) -> list[WalletTransaction]:
    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.wallet_id == wallet_id)
        .order_by(WalletTransaction.created_at.desc(), WalletTransaction.id.desc())
        .limit(10)
        .all()
    )


def _money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))
