from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased

from app.core.database import SessionLocal
from app.models.game import Game
from app.models.team import Team
from app.schemas.game import GameCreate
from app.services.game_service import GameRegistrationError
from app.services.game_service import create_game

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/games")
async def games(request: Request, db: Session = Depends(get_db)):
    home_team = aliased(Team)
    away_team = aliased(Team)
    games_list = (
        db.query(Game, home_team, away_team)
        .join(home_team, Game.home_team_id == home_team.id)
        .join(away_team, Game.away_team_id == away_team.id)
        .order_by(Game.match_datetime.desc(), Game.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/games.html",
        context={
            "title": "Admin - Jogos",
            "games": games_list,
        },
    )


@router.get("/games/new")
async def new_game(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="admin/game_form.html",
        context={
            "title": "Novo jogo",
            "teams": _get_teams(db),
            "form": {},
            "errors": [],
        },
    )


@router.post("/games")
async def create_game_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    home_team_id: Annotated[str, Form()],
    away_team_id: Annotated[str, Form()],
    match_datetime: Annotated[str, Form()],
    bet_price: Annotated[str, Form()],
    jackpot_amount: Annotated[str | None, Form()] = None,
):
    form_data = {
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "match_datetime": match_datetime,
        "bet_price": bet_price,
        "jackpot_amount": jackpot_amount,
    }

    try:
        game_data = GameCreate(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_datetime=match_datetime,
            bet_price=bet_price,
            jackpot_amount=jackpot_amount or "0",
        )
        create_game(db, game_data)
    except (ValidationError, GameRegistrationError) as error:
        errors = (
            _format_validation_errors(error)
            if isinstance(error, ValidationError)
            else error.messages
        )
        return templates.TemplateResponse(
            request=request,
            name="admin/game_form.html",
            context={
                "title": "Novo jogo",
                "teams": _get_teams(db),
                "form": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/admin/games",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _get_teams(db: Session) -> list[Team]:
    return db.query(Team).order_by(Team.name.asc()).all()


def _format_validation_errors(error: ValidationError) -> list[str]:
    messages = []

    for item in error.errors():
        field = item.get("loc", ["campo"])[0]
        field_names = {
            "home_team_id": "time casa",
            "away_team_id": "time visitante",
            "match_datetime": "data e hora",
            "bet_price": "valor da aposta",
            "jackpot_amount": "jackpot inicial",
        }
        messages.append(f"Verifique o campo {field_names.get(field, field)}.")

    return messages or ["Verifique os dados informados."]
