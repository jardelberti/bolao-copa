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
from app.models.deposit_request import DepositRequest
from app.models.wallet import Wallet
from app.services.auth_service import require_current_user
from app.services.payment_settings_service import get_or_create_payment_settings
from app.services.pix_service import generate_pix_payload
from app.services.pix_service import generate_pix_qrcode_base64
from app.services.wallet_deposit_service import WalletDepositServiceError
from app.services.wallet_deposit_service import create_deposit_request

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/wallet")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/deposit")
async def deposit(request: Request, db: Session = Depends(get_db), success: str | None = None):
    current_user = require_current_user(request, db)
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    payment_settings = get_or_create_payment_settings(db)

    return templates.TemplateResponse(
        request=request,
        name="wallet/deposit.html",
        context={
            "title": "Solicitar depósito",
            "current_user": current_user,
            "wallet": wallet,
            "payment_settings": payment_settings,
            "form": {},
            "error": None,
            "success": success,
            "pix_payload": None,
            "pix_qrcode_base64": None,
        },
    )


@router.get("/deposits")
async def deposits(request: Request, db: Session = Depends(get_db)):
    current_user = require_current_user(request, db)
    deposit_requests = (
        db.query(DepositRequest)
        .filter(DepositRequest.user_id == current_user.id)
        .order_by(DepositRequest.created_at.desc(), DepositRequest.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="wallet/deposits.html",
        context={
            "title": "Meus depósitos",
            "current_user": current_user,
            "deposits": deposit_requests,
        },
    )


@router.post("/deposit")
async def deposit_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    requested_amount: Annotated[str, Form()],
    notes: Annotated[str, Form()] = "",
):
    current_user = require_current_user(request, db)
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    payment_settings = get_or_create_payment_settings(db)
    form_data = {
        "requested_amount": requested_amount,
        "notes": notes,
    }

    try:
        create_deposit_request(
            db=db,
            user_id=current_user.id,
            requested_amount=requested_amount,
            notes=notes,
        )
    except WalletDepositServiceError as error:
        return templates.TemplateResponse(
            request=request,
            name="wallet/deposit.html",
            context={
                "title": "Solicitar depósito",
                "current_user": current_user,
                "wallet": wallet,
                "payment_settings": payment_settings,
                "form": form_data,
                "error": error.message,
                "success": None,
                "pix_payload": None,
                "pix_qrcode_base64": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    pix_payload = generate_pix_payload(
        pix_key=payment_settings.pix_key,
        recipient_name=payment_settings.recipient_name,
        recipient_city=payment_settings.recipient_city,
        amount=requested_amount,
    )
    pix_qrcode_base64 = generate_pix_qrcode_base64(pix_payload)

    return templates.TemplateResponse(
        request=request,
        name="wallet/deposit.html",
        context={
            "title": "Solicitar depósito",
            "current_user": current_user,
            "wallet": wallet,
            "payment_settings": payment_settings,
            "form": {},
            "error": None,
            "success": True,
            "pix_payload": pix_payload,
            "pix_qrcode_base64": pix_qrcode_base64,
        },
    )
