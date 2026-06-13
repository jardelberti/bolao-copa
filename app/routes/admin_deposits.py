from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import Request
from fastapi import status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.core.database import SessionLocal
from app.models.deposit_request import DepositRequest
from app.services.auth_service import require_admin_user
from app.services.deposit_service import DepositServiceError
from app.services.deposit_service import approve_deposit
from app.services.deposit_service import reject_deposit

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/deposits")
async def deposits(request: Request, db: Session = Depends(get_db), error: str | None = None):
    current_user = require_admin_user(request, db)

    deposits_list = (
        db.query(DepositRequest)
        .options(joinedload(DepositRequest.user))
        .order_by(DepositRequest.created_at.desc(), DepositRequest.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/deposits.html",
        context={
            "title": "Admin - Depósitos",
            "current_user": current_user,
            "deposits": deposits_list,
            "error": error,
        },
    )


@router.post("/deposits/{deposit_id}/approve")
async def approve_deposit_post(
    request: Request,
    deposit_id: int,
    db: Annotated[Session, Depends(get_db)],
    credited_amount: Annotated[str, Form()],
    notes: Annotated[str, Form()] = "",
):
    require_admin_user(request, db)

    try:
        approve_deposit(db, deposit_id, credited_amount, notes)
    except DepositServiceError as error:
        return _redirect_with_error(error.message)

    return RedirectResponse(
        url="/admin/deposits",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/deposits/{deposit_id}/reject")
async def reject_deposit_post(
    request: Request,
    deposit_id: int,
    db: Annotated[Session, Depends(get_db)],
    notes: Annotated[str, Form()] = "",
):
    require_admin_user(request, db)

    try:
        reject_deposit(db, deposit_id, notes)
    except DepositServiceError as error:
        return _redirect_with_error(error.message)

    return RedirectResponse(
        url="/admin/deposits",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _redirect_with_error(message: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"/admin/deposits?error={quote(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
