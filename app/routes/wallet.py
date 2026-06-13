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
from app.models.deposit_request import DepositRequest
from app.models.user import User
from app.models.wallet import Wallet
from app.services.auth_service import require_current_user
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
    admin_user = _get_admin_user(db)

    return templates.TemplateResponse(
        request=request,
        name="wallet/deposit.html",
        context={
            "title": "Solicitar depósito",
            "current_user": current_user,
            "wallet": wallet,
            "admin_user": admin_user,
            "form": {},
            "error": None,
            "success": success,
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
    admin_user = _get_admin_user(db)
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
                "admin_user": admin_user,
                "form": form_data,
                "error": error.message,
                "success": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/wallet/deposit?success=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _get_admin_user(db: Session) -> User | None:
    return db.query(User).filter(User.is_admin.is_(True)).order_by(User.id.asc()).first()
