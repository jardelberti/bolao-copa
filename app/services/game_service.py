from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.team import Team
from app.schemas.game import GameCreate


class GameRegistrationError(Exception):
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__(", ".join(messages))


def create_game(db: Session, game_data: GameCreate) -> Game:
    errors = _validate_game_data(db, game_data)

    if errors:
        raise GameRegistrationError(errors)

    game = Game(
        home_team_id=game_data.home_team_id,
        away_team_id=game_data.away_team_id,
        match_datetime=game_data.match_datetime,
        bet_price=game_data.bet_price,
        jackpot_amount=game_data.jackpot_amount,
    )

    try:
        db.add(game)
        db.commit()
        db.refresh(game)
    except Exception:
        db.rollback()
        raise

    return game


def _validate_game_data(db: Session, game_data: GameCreate) -> list[str]:
    errors = []

    if game_data.home_team_id == game_data.away_team_id:
        errors.append("Time casa e time visitante devem ser diferentes.")

    if game_data.bet_price <= Decimal("0"):
        errors.append("O valor da aposta deve ser maior que zero.")

    if game_data.jackpot_amount < Decimal("0"):
        errors.append("O jackpot inicial não pode ser negativo.")

    if not db.get(Team, game_data.home_team_id):
        errors.append("Selecione um time da casa válido.")

    if not db.get(Team, game_data.away_team_id):
        errors.append("Selecione um time visitante válido.")

    return errors
