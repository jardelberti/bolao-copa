from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.user import UserCreate
from app.services.auth_service import get_current_user
from app.services.user_service import UserRegistrationError
from app.services.user_service import create_user

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "title": "Cadastro",
            "form": {},
            "errors": [],
            "current_user": get_current_user(request, db),
        },
    )


@router.post("/register")
async def register_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    pix_type: Annotated[str, Form()],
    pix_key: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirmation: Annotated[str, Form()],
):
    form_data = {
        "name": name,
        "email": email,
        "pix_type": pix_type,
        "pix_key": pix_key,
    }

    try:
        user_data = UserCreate(
            name=name,
            email=email,
            pix_type=pix_type,
            pix_key=pix_key,
            password=password,
            password_confirmation=password_confirmation,
        )
        create_user(db, user_data)
    except (ValidationError, UserRegistrationError) as error:
        errors = (
            _format_validation_errors(error)
            if isinstance(error, ValidationError)
            else error.messages
        )
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "title": "Cadastro",
                "form": form_data,
                "errors": errors,
                "current_user": get_current_user(request, db),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/aguardando-aprovacao",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/aguardando-aprovacao")
async def pending_approval(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="pending_approval.html",
        context={
            "title": "Aguardando aprovação",
            "current_user": get_current_user(request, db),
        },
    )


def _format_validation_errors(error: ValidationError) -> list[str]:
    messages = []

    for item in error.errors():
        field = item.get("loc", ["campo"])[0]
        field_names = {
            "name": "nome",
            "email": "email",
            "pix_type": "tipo da chave Pix",
            "pix_key": "chave Pix",
            "password": "senha",
            "password_confirmation": "confirmação de senha",
        }
        messages.append(f"Verifique o campo {field_names.get(field, field)}.")

    return messages or ["Verifique os dados informados."]
