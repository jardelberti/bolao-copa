from pydantic import BaseModel
from pydantic import Field


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=5)
    flag_url: str = Field(min_length=1, max_length=255)
