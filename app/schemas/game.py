from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from pydantic import Field


class GameCreate(BaseModel):
    home_team_id: int
    away_team_id: int
    match_datetime: datetime
    bet_price: Decimal = Field(gt=Decimal("0"))
    jackpot_amount: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0")
    )
