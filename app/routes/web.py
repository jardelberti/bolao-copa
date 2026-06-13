from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.bet import Bet
from app.models.game import Game
from app.services.auth_service import get_current_user

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    now = datetime.now()
    games = (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .order_by(Game.match_datetime.asc(), Game.id.asc())
        .all()
    )
    bet_counts = dict(
        db.query(Bet.game_id, func.count(Bet.id))
        .group_by(Bet.game_id)
        .all()
    )
    total_bets = db.query(func.count(Bet.id)).scalar() or 0
    total_jackpot = sum(
        (game.jackpot_amount or Decimal("0.00"))
        for game in games
    )

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "title": "Bolão da Copa",
            "current_user": current_user,
            "games": games,
            "bet_counts": bet_counts,
            "total_games": len(games),
            "total_bets": total_bets,
            "total_jackpot": total_jackpot,
            "now": now,
        }
    )
