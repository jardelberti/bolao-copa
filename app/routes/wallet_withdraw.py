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
from app.models.wallet import Wallet
from app.models.withdraw_request import WithdrawRequest
from app.services.auth_service import require_current_user
from app.services.withdraw_service import WithdrawServiceError
from app.services.withdraw_service import create_withdraw_request

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/wallet")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/withdraw")
async def withdraw(
    request: Request,
    db: Session = Depends(get_db),
    success: str | None = None,
):
    current_user = require_current_user(request, db)
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()

    return templates.TemplateResponse(
        request=request,
        name="wallet/withdraw.html",
        context={
            "title": "Solicitar saque",
            "current_user": current_user,
            "wallet": wallet,
            "form": {
                "pix_key_type": current_user.pix_type,
                "pix_key": current_user.pix_key,
            },
            "error": None,
            "success": success,
        },
    )


@router.post("/withdraw")
async def withdraw_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    requested_amount: Annotated[str, Form()],
    pix_key_type: Annotated[str, Form()],
    pix_key: Annotated[str, Form()],
):
    current_user = require_current_user(request, db)
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    form_data = {
        "requested_amount": requested_amount,
        "pix_key_type": pix_key_type,
        "pix_key": pix_key,
    }

    try:
        create_withdraw_request(
            db=db,
            user_id=current_user.id,
            requested_amount=requested_amount,
            pix_key_type=pix_key_type,
            pix_key=pix_key,
        )
    except WithdrawServiceError as error:
        return templates.TemplateResponse(
            request=request,
            name="wallet/withdraw.html",
            context={
                "title": "Solicitar saque",
                "current_user": current_user,
                "wallet": wallet,
                "form": form_data,
                "error": error.message,
                "success": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/wallet/withdraws?success=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/withdraws")
async def withdraws(
    request: Request,
    db: Session = Depends(get_db),
    success: str | None = None,
):
    current_user = require_current_user(request, db)
    withdraw_requests = (
        db.query(WithdrawRequest)
        .filter(WithdrawRequest.user_id == current_user.id)
        .order_by(WithdrawRequest.created_at.desc(), WithdrawRequest.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="wallet/withdraws.html",
        context={
            "title": "Meus saques",
            "current_user": current_user,
            "withdraws": withdraw_requests,
            "success": success,
        },
    )
