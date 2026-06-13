from pydantic import BaseModel
from pydantic import Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=1, max_length=255)
    pix_type: str = Field(min_length=1, max_length=20)
    pix_key: str = Field(min_length=1, max_length=255)
    password: str = Field(
        min_length=8,
        max_length=72
    )

    password_confirmation: str = Field(
        min_length=8,
        max_length=72
    )
