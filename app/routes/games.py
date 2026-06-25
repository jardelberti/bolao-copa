from datetime import datetime
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
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.bet import Bet
from app.models.game import Game
from app.models.wallet import Wallet
from app.services.auth_service import require_current_user
from app.services.bet_service import BetServiceError
from app.services.bet_service import create_bet

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_game_summaries(db: Session, games: list[Game], now: datetime) -> dict[int, dict]:
    bet_counts = dict(
        db.query(Bet.game_id, func.count(Bet.id))
        .group_by(Bet.game_id)
        .all()
    )

    summaries = {}

    for game in games:
        has_result = (
            game.home_score is not None
            and game.away_score is not None
        )

        is_started = now >= game.match_datetime
        is_open = not is_started and not has_result

        if has_result:
            status_label = "Finalizado"
            status_class = "status-approved"
        elif is_started:
            status_label = "Aguardando resultado do jogo"
            status_class = "status-pending"
        else:
            status_label = "Aberto para apostas"
            status_class = "status-prize"

        summaries[game.id] = {
            "bets_count": int(bet_counts.get(game.id, 0)),
            "has_result": has_result,
            "is_started": is_started,
            "is_open": is_open,
            "status_label": status_label,
            "status_class": status_class,
        }

    return summaries


@router.get("/games")
async def games(request: Request, db: Session = Depends(get_db)):
    current_user = require_current_user(request, db)
    now = datetime.now()

    games_list = (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .order_by(Game.match_datetime.asc(), Game.id.asc())
        .all()
    )

    game_summaries = build_game_summaries(db, games_list, now)

    featured_game = next(
        (
            game
            for game in games_list
            if game_summaries[game.id]["is_open"]
        ),
        None,
    )

    open_games = [
        game
        for game in games_list
        if game_summaries[game.id]["is_open"]
        and (not featured_game or game.id != featured_game.id)
    ]

    closed_games = [
        game
        for game in sorted(games_list, key=lambda item: item.match_datetime, reverse=True)
        if not game_summaries[game.id]["is_open"]
    ]

    return templates.TemplateResponse(
        request=request,
        name="games/list.html",
        context={
            "title": "Jogos",
            "current_user": current_user,
            "games": games_list,
            "featured_game": featured_game,
            "open_games": open_games,
            "closed_games": closed_games,
            "game_summaries": game_summaries,
            "now": now,
        },
    )


@router.get("/games/{game_id}")
async def game_detail(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
    error: str | None = None,
):
    current_user = require_current_user(request, db)
    now = datetime.now()
    game = _get_game(db, game_id)

    if not game:
        return RedirectResponse(
            url="/games",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()

    bet_count = (
        db.query(func.count(Bet.id))
        .filter(Bet.game_id == game.id)
        .scalar()
        or 0
    )

    has_result = (
        game.home_score is not None
        and game.away_score is not None
    )

    is_started = now >= game.match_datetime
    is_open = not is_started and not has_result

    return templates.TemplateResponse(
        request=request,
        name="games/detail.html",
        context={
            "title": "Apostar",
            "current_user": current_user,
            "game": game,
            "wallet": wallet,
            "bet_count": int(bet_count),
            "has_result": has_result,
            "is_started": is_started,
            "is_open": is_open,
            "error": error,
            "now": now,
        },
    )


@router.get("/games/{game_id}/bets")
async def game_bets(
    request: Request,
    game_id: int,
    db: Session = Depends(get_db),
):
    current_user = require_current_user(request, db)
    now = datetime.now()
    game = _get_game_with_bets(db, game_id)

    if not game:
        return RedirectResponse(
            url="/games",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    has_result = game.home_score is not None and game.away_score is not None
    can_show_bets = now >= game.match_datetime
    bets = sorted(
        game.bets,
        key=lambda bet: (bet.created_at, bet.id),
        reverse=True,
    ) if can_show_bets else []

    return templates.TemplateResponse(
        request=request,
        name="games/bets.html",
        context={
            "title": "Apostas do jogo",
            "current_user": current_user,
            "game": game,
            "bets": bets,
            "has_result": has_result,
            "can_show_bets": can_show_bets,
            "now": now,
        },
    )


@router.post("/games/{game_id}/bet")
async def place_bet(
    request: Request,
    game_id: int,
    db: Annotated[Session, Depends(get_db)],
    home_score_guess: Annotated[int, Form()],
    away_score_guess: Annotated[int, Form()],
):
    user = require_current_user(request, db)

    try:
        create_bet(
            db=db,
            user_id=user.id,
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
    current_user = require_current_user(request, db)
    now = datetime.now()

    bets = (
        db.query(Bet)
        .options(
            joinedload(Bet.game).joinedload(Game.home_team),
            joinedload(Bet.game).joinedload(Game.away_team),
        )
        .filter(Bet.user_id == current_user.id)
        .order_by(Bet.created_at.desc(), Bet.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="games/my_bets.html",
        context={
            "title": "Minhas apostas",
            "current_user": current_user,
            "bets": bets,
            "now": now,
        },
    )


def _get_game(db: Session, game_id: int) -> Game | None:
    return (
        db.query(Game)
        .options(joinedload(Game.home_team), joinedload(Game.away_team))
        .filter(Game.id == game_id)
        .first()
    )


def _get_game_with_bets(db: Session, game_id: int) -> Game | None:
    return (
        db.query(Game)
        .options(
            joinedload(Game.home_team),
            joinedload(Game.away_team),
            joinedload(Game.bets).joinedload(Bet.user),
        )
        .filter(Game.id == game_id)
        .first()
    )
