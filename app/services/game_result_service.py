from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.models.bet import Bet
from app.models.game import Game
from app.models.user import User
from app.models.wallet_transaction import WalletTransaction


class GameResultServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def process_game_result(
    db: Session,
    game_id: int,
    home_score: int,
    away_score: int,
) -> Game:
    game = _get_game(db, game_id)

    if not game:
        raise GameResultServiceError("Jogo não encontrado.")

    if home_score < 0 or away_score < 0:
        raise GameResultServiceError("Os placares não podem ser negativos.")

    if game.home_score is not None or game.away_score is not None:
        raise GameResultServiceError("Este jogo já possui resultado processado.")

    bets = list(game.bets)
    winners = [
        bet
        for bet in bets
        if bet.home_score_guess == home_score and bet.away_score_guess == away_score
    ]

    try:
        game.home_score = home_score
        game.away_score = away_score

        if winners:
            _process_prizes(db, game, winners)
        else:
            _process_refunds(db, game, bets)

        game.jackpot_amount = Decimal("0.00")

        db.commit()
        db.refresh(game)
    except Exception:
        db.rollback()
        raise

    return game


def _get_game(db: Session, game_id: int) -> Game | None:
    return (
        db.query(Game)
        .options(
            joinedload(Game.home_team),
            joinedload(Game.away_team),
            joinedload(Game.bets).joinedload(Bet.user).joinedload(User.wallet),
        )
        .filter(Game.id == game_id)
        .first()
    )


def _process_prizes(db: Session, game: Game, winners: list[Bet]) -> None:
    prize_amount = (_to_money(game.jackpot_amount) / len(winners)).quantize(
        Decimal("0.01")
    )
    description = f"Premiação: {_game_name(game)}"

    for bet in game.bets:
        bet.is_winner = bet in winners

    for bet in winners:
        wallet = bet.user.wallet

        if not wallet:
            raise GameResultServiceError("Carteira de ganhador não encontrada.")

        wallet.balance += prize_amount
        db.add(
            WalletTransaction(
                wallet_id=wallet.id,
                transaction_type="PRIZE",
                amount=prize_amount,
                description=description,
            )
        )


def _process_refunds(db: Session, game: Game, bets: list[Bet]) -> None:
    description = f"Estorno: sem ganhadores no jogo {_game_name(game)}"

    for bet in bets:
        wallet = bet.user.wallet

        if not wallet:
            raise GameResultServiceError("Carteira do apostador não encontrada.")

        amount = _to_money(bet.amount)
        bet.is_winner = False
        wallet.balance += amount
        db.add(
            WalletTransaction(
                wallet_id=wallet.id,
                transaction_type="REFUND",
                amount=amount,
                description=description,
            )
        )


def _game_name(game: Game) -> str:
    home_team = game.home_team.name if game.home_team else f"Time {game.home_team_id}"
    away_team = game.away_team.name if game.away_team else f"Time {game.away_team_id}"

    return f"{home_team} x {away_team}"


def _to_money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(Decimal("0.01"))
