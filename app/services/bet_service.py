from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.bet import Bet
from app.models.game import Game
from app.models.user import User
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction


class BetServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def create_bet(
    db: Session,
    user_id: int,
    game_id: int,
    home_score_guess: int,
    away_score_guess: int,
) -> Bet:
    user = db.get(User, user_id)

    if not user:
        raise BetServiceError("Usuário não encontrado.")

    if not user.is_active:
        raise BetServiceError("Usuário inativo.")

    if not user.is_approved:
        raise BetServiceError("Usuário ainda não aprovado.")

    game = db.get(Game, game_id)

    if not game:
        raise BetServiceError("Jogo não encontrado.")

    if game.home_score is not None or game.away_score is not None:
        raise BetServiceError("Este jogo já foi finalizado.")

    if home_score_guess < 0 or away_score_guess < 0:
        raise BetServiceError("Os placares não podem ser negativos.")

    if _bet_exists(db, user_id, game_id, home_score_guess, away_score_guess):
        raise BetServiceError("Este placar já foi apostado para este jogo.")

    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()

    if not wallet:
        raise BetServiceError("Carteira do usuário não encontrada.")

    bet_amount = _to_money(game.bet_price)

    if wallet.balance < bet_amount:
        raise BetServiceError("Saldo insuficiente para realizar a aposta.")

    bet = Bet(
        user_id=user_id,
        game_id=game_id,
        home_score_guess=home_score_guess,
        away_score_guess=away_score_guess,
        amount=bet_amount,
        is_winner=False,
    )

    transaction = WalletTransaction(
        wallet_id=wallet.id,
        transaction_type="BET",
        amount=-bet_amount,
        description=_build_transaction_description(game),
    )

    try:
        wallet.balance -= bet_amount
        game.jackpot_amount = _to_money(game.jackpot_amount) + bet_amount

        db.add(bet)
        db.add(transaction)
        db.commit()
        db.refresh(bet)
    except IntegrityError as exc:
        db.rollback()
        raise BetServiceError(
            "Este placar já foi apostado para este jogo.") from exc
    except Exception:
        db.rollback()
        raise

    return bet


def _bet_exists(
    db: Session,
    user_id: int,
    game_id: int,
    home_score_guess: int,
    away_score_guess: int,
) -> bool:
    return (
        db.query(Bet)
        .filter(
            Bet.user_id == user_id,
            Bet.game_id == game_id,
            Bet.home_score_guess == home_score_guess,
            Bet.away_score_guess == away_score_guess,
        )
        .first()
        is not None
    )


def _build_transaction_description(game: Game) -> str:
    home_team = game.home_team.name if game.home_team else f"Time {game.home_team_id}"
    away_team = game.away_team.name if game.away_team else f"Time {game.away_team_id}"

    return f"Aposta: {home_team} x {away_team}"


def _to_money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(Decimal("0.01"))
