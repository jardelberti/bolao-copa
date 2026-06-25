from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.bet import Bet
from app.models.deposit_request import DepositRequest
from app.models.game import Game
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
    now = datetime.now()

    wallet = user.wallet if user else None

    total_bets = _total_bets(db, user.id)

    total_bet_amount = _money(
        db.query(func.coalesce(func.sum(Bet.amount), 0))
        .filter(Bet.user_id == user.id)
        .scalar()
    )

    winning_bets = _winning_bets(db, user.id)
    waiting_result_bets = _waiting_result_bets(db, user.id, now)

    total_prizes = _transaction_sum(
        db, wallet.id, "PRIZE") if wallet else Decimal("0.00")
    total_refunds = _transaction_sum(
        db, wallet.id, "REFUND") if wallet else Decimal("0.00")

    transactions = _latest_transactions(db, wallet.id) if wallet else []

    min_open_bet_price = _minimum_open_bet_price(db, now)
    next_game = _next_open_game(db, now)
    next_game_bet_count = _game_bet_count(db, next_game.id) if next_game else 0

    pending_deposits = _pending_deposits(db, user.id)
    latest_bets = _latest_bets(db, user.id)

    can_bet_next_game = (
        bool(wallet)
        and bool(next_game)
        and wallet.balance >= next_game.bet_price
    )

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
            "winning_bets": winning_bets,
            "waiting_result_bets": waiting_result_bets,
            "total_prizes": total_prizes,
            "total_refunds": total_refunds,
            "transactions": transactions,
            "min_open_bet_price": min_open_bet_price,
            "next_game": next_game,
            "next_game_bet_count": next_game_bet_count,
            "pending_deposits": pending_deposits,
            "latest_bets": latest_bets,
            "can_bet_next_game": can_bet_next_game,
            "now": now,
        },
    )


def _total_bets(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(Bet.id))
        .filter(Bet.user_id == user_id)
        .scalar()
        or 0
    )


def _winning_bets(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(Bet.id))
        .filter(
            Bet.user_id == user_id,
            Bet.is_winner.is_(True),
        )
        .scalar()
        or 0
    )


def _waiting_result_bets(db: Session, user_id: int, now: datetime) -> int:
    return (
        db.query(func.count(Bet.id))
        .join(Game, Game.id == Bet.game_id)
        .filter(
            Bet.user_id == user_id,
            Game.match_datetime <= now,
            Game.home_score.is_(None),
            Game.away_score.is_(None),
        )
        .scalar()
        or 0
    )


def _pending_deposits(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(DepositRequest.id))
        .filter(
            DepositRequest.user_id == user_id,
            DepositRequest.status == "PENDING",
        )
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
        .limit(6)
        .all()
    )


def _latest_bets(db: Session, user_id: int) -> list[Bet]:
    return (
        db.query(Bet)
        .options(
            joinedload(Bet.game).joinedload(Game.home_team),
            joinedload(Bet.game).joinedload(Game.away_team),
        )
        .filter(Bet.user_id == user_id)
        .order_by(Bet.created_at.desc(), Bet.id.desc())
        .limit(4)
        .all()
    )


def _minimum_open_bet_price(db: Session, now: datetime) -> Decimal | None:
    value = (
        db.query(func.min(Game.bet_price))
        .filter(
            Game.match_datetime > now,
            Game.home_score.is_(None),
            Game.away_score.is_(None),
        )
        .scalar()
    )

    if value is None:
        return None

    return _money(value)


def _next_open_game(db: Session, now: datetime) -> Game | None:
    return (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .filter(
            Game.match_datetime > now,
            Game.home_score.is_(None),
            Game.away_score.is_(None),
        )
        .order_by(Game.match_datetime.asc(), Game.id.asc())
        .first()
    )


def _game_bet_count(db: Session, game_id: int) -> int:
    return (
        db.query(func.count(Bet.id))
        .filter(Bet.game_id == game_id)
        .scalar()
        or 0
    )


def _money(value) -> Decimal:
    return Decimal(str(value or "0")).quantize(Decimal("0.01"))
