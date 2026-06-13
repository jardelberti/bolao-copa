from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

#from app.models.base import Base
#from app.models.user import User
#from app.core.database import engine
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.game_admin import router as game_admin_router
from app.routes.team_admin import router as team_admin_router
from app.routes.web import router as web_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Bolão da Copa"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.include_router(web_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(team_admin_router)
app.include_router(game_admin_router)
