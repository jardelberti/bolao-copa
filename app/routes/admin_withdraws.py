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
from app.models.withdraw_request import WithdrawRequest
from app.services.auth_service import require_admin_user
from app.services.withdraw_service import WithdrawServiceError
from app.services.withdraw_service import approve_withdraw
from app.services.withdraw_service import reject_withdraw

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/withdraws")
async def withdraws(
    request: Request,
    db: Session = Depends(get_db),
    error: str | None = None,
):
    current_user = require_admin_user(request, db)
    withdraws_list = (
        db.query(WithdrawRequest)
        .options(joinedload(WithdrawRequest.user))
        .order_by(WithdrawRequest.created_at.desc(), WithdrawRequest.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/withdraws.html",
        context={
            "title": "Admin - Saques",
            "current_user": current_user,
            "withdraws": withdraws_list,
            "error": error,
        },
    )


@router.post("/withdraws/{withdraw_id}/approve")
async def approve_withdraw_post(
    request: Request,
    withdraw_id: int,
    db: Annotated[Session, Depends(get_db)],
    notes: Annotated[str, Form()] = "",
):
    require_admin_user(request, db)

    try:
        approve_withdraw(db, withdraw_id, notes)
    except WithdrawServiceError as error:
        return _redirect_with_error(error.message)

    return RedirectResponse(
        url="/admin/withdraws",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/withdraws/{withdraw_id}/reject")
async def reject_withdraw_post(
    request: Request,
    withdraw_id: int,
    db: Annotated[Session, Depends(get_db)],
    notes: Annotated[str, Form()] = "",
):
    require_admin_user(request, db)

    try:
        reject_withdraw(db, withdraw_id, notes)
    except WithdrawServiceError as error:
        return _redirect_with_error(error.message)

    return RedirectResponse(
        url="/admin/withdraws",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _redirect_with_error(message: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"/admin/withdraws?error={quote(message)}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
