from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.auth_service import require_admin_user
from app.services.payment_settings_service import PaymentSettingsServiceError
from app.services.payment_settings_service import get_or_create_payment_settings
from app.services.payment_settings_service import update_payment_settings

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/payment-settings")
async def payment_settings(request: Request, db: Session = Depends(get_db), success: str | None = None):
    current_user = require_admin_user(request, db)
    settings = get_or_create_payment_settings(db)

    return templates.TemplateResponse(
        request=request,
        name="admin/payment_settings.html",
        context={
            "title": "Configurações PIX",
            "current_user": current_user,
            "settings": settings,
            "errors": [],
            "success": success,
        },
    )


@router.post("/payment-settings")
async def update_payment_settings_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    pix_key: Annotated[str, Form()],
    pix_key_type: Annotated[str, Form()],
    recipient_name: Annotated[str, Form()],
    recipient_city: Annotated[str, Form()],
):
    current_user = require_admin_user(request, db)

    try:
        settings = update_payment_settings(
            db=db,
            pix_key=pix_key,
            pix_key_type=pix_key_type,
            recipient_name=recipient_name,
            recipient_city=recipient_city,
        )
    except PaymentSettingsServiceError as error:
        return templates.TemplateResponse(
            request=request,
            name="admin/payment_settings.html",
            context={
                "title": "Configurações PIX",
                "current_user": current_user,
                "settings": {
                    "pix_key": pix_key,
                    "pix_key_type": pix_key_type,
                    "recipient_name": recipient_name,
                    "recipient_city": recipient_city,
                },
                "errors": error.messages,
                "success": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return templates.TemplateResponse(
        request=request,
        name="admin/payment_settings.html",
        context={
            "title": "Configurações PIX",
            "current_user": current_user,
            "settings": settings,
            "errors": [],
            "success": "Configurações PIX atualizadas com sucesso.",
        },
    )
