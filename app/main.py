from fastapi import FastAPI

from app.models.base import Base
from app.models.user import User
from app.core.database import engine

app = FastAPI(
    title="Bolão da Copa"
)


@app.get("/")
async def home():
    return {
        "status": "online"
    }
