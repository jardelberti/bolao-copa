from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.auth_service import AuthServiceError
from app.services.auth_service import authenticate_user
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


@router.get("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "title": "Entrar",
            "form": {},
            "error": None,
            "current_user": get_current_user(request, db),
        },
    )


@router.post("/login")
async def login_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    form_data = {
        "email": email,
    }

    try:
        user = authenticate_user(db, email, password)
    except AuthServiceError as error:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "title": "Entrar",
                "form": form_data,
                "error": error.message,
                "current_user": get_current_user(request, db),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()

    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
