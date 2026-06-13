from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.bet import Bet
from app.models.game import Game
from app.models.wallet import Wallet
from app.services.bet_service import BetServiceError
from app.services.bet_service import create_bet

BASE_DIR = Path(__file__).resolve().parents[1]
CURRENT_USER_ID = 1

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/games")
async def games(request: Request, db: Session = Depends(get_db)):
    games_list = (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .order_by(Game.match_datetime.asc(), Game.id.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="games/list.html",
        context={
            "title": "Jogos",
            "games": games_list,
        },
    )


@router.get("/games/{game_id}")
async def game_detail(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
    error: str | None = None,
):
    game = _get_game(db, game_id)

    if not game:
        return RedirectResponse(
            url="/games",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    wallet = db.query(Wallet).filter(Wallet.user_id == CURRENT_USER_ID).first()

    return templates.TemplateResponse(
        request=request,
        name="games/detail.html",
        context={
            "title": "Apostar",
            "game": game,
            "wallet": wallet,
            "error": error,
        },
    )


@router.post("/games/{game_id}/bet")
async def place_bet(
    game_id: int,
    db: Annotated[Session, Depends(get_db)],
    home_score_guess: Annotated[int, Form()],
    away_score_guess: Annotated[int, Form()],
):
    try:
        create_bet(
            db=db,
            user_id=CURRENT_USER_ID,
            game_id=game_id,
            home_score_guess=home_score_guess,
            away_score_guess=away_score_guess,
        )
    except BetServiceError as error:
        return RedirectResponse(
            url=f"/games/{game_id}?error={quote(error.message)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url="/my-bets",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/my-bets")
async def my_bets(request: Request, db: Session = Depends(get_db)):
    bets = (
        db.query(Bet)
        .options(
            joinedload(Bet.game).joinedload(Game.home_team),
            joinedload(Bet.game).joinedload(Game.away_team),
        )
        .filter(Bet.user_id == CURRENT_USER_ID)
        .order_by(Bet.created_at.desc(), Bet.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="games/my_bets.html",
        context={
            "title": "Minhas apostas",
            "bets": bets,
        },
    )


def _get_game(db: Session, game_id: int) -> Game | None:
    return (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .filter(Game.id == game_id)
        .first()
    )
