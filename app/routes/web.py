from collections import defaultdict
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

    winner_bets = (
        db.query(Bet)
        .options(joinedload(Bet.user))
        .filter(Bet.is_winner.is_(True))
        .all()
    )

    winner_names_by_game = defaultdict(list)

    for bet in winner_bets:
        user_name = "Usuário"

        if bet.user:
            user_name = (
                getattr(bet.user, "name", None)
                or getattr(bet.user, "email", None)
                or "Usuário"
            )

        if user_name not in winner_names_by_game[bet.game_id]:
            winner_names_by_game[bet.game_id].append(user_name)

    game_summaries = {}

    for game in games:
        bets_count = int(bet_counts.get(game.id, 0))
        jackpot = game.jackpot_amount or Decimal("0.00")

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
            status_label = "Aguardando lançamento do resultado"
            status_class = "status-pending"
        else:
            status_label = "Aberto para apostas"
            status_class = "status-prize"

        game_summaries[game.id] = {
            "bets_count": bets_count,
            "jackpot": jackpot,
            "has_result": has_result,
            "is_started": is_started,
            "is_open": is_open,
            "status_label": status_label,
            "status_class": status_class,
            "winner_names": winner_names_by_game.get(game.id, []),
        }

    featured_game = next(
        (
            game
            for game in games
            if game_summaries[game.id]["is_open"]
        ),
        None,
    )

    if not featured_game and games:
        featured_game = max(games, key=lambda game: game.match_datetime)

    upcoming_games = [
        game
        for game in games
        if game_summaries[game.id]["is_open"]
        and (not featured_game or game.id != featured_game.id)
    ]

    finished_games = [
        game
        for game in sorted(games, key=lambda item: item.match_datetime, reverse=True)
        if (
            game_summaries[game.id]["is_started"]
            or game_summaries[game.id]["has_result"]
        )
        and (not featured_game or game.id != featured_game.id)
    ]

    total_bets = sum(
        summary["bets_count"]
        for summary in game_summaries.values()
    )

    total_jackpot = sum(
        summary["jackpot"]
        for summary in game_summaries.values()
    )

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "title": "Bolão da Copa",
            "current_user": current_user,
            "games": games,
            "featured_game": featured_game,
            "upcoming_games": upcoming_games,
            "finished_games": finished_games,
            "game_summaries": game_summaries,
            "total_games": len(games),
            "total_bets": total_bets,
            "total_jackpot": total_jackpot,
            "now": now,
        },
    )
