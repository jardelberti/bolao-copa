from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/users")
async def users(request: Request, db: Session = Depends(get_db)):
    users_list = db.query(User).order_by(User.created_at.desc(), User.id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context={
            "title": "Admin - Usuários",
            "users": users_list,
        },
    )


@router.post("/users/{user_id}/approve")
async def approve_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user:
        user.is_approved = True
        db.commit()

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/users/{user_id}/revoke-approval")
async def revoke_user_approval(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)

    if user:
        user.is_approved = False
        db.commit()

    return RedirectResponse(
        url="/admin/users",
        status_code=status.HTTP_303_SEE_OTHER,
    )
