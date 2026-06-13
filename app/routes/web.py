from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
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
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "title": "Bolão da Copa",
            "current_user": get_current_user(request, db),
        }
    )
