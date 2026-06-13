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
from app.models.team import Team
from app.schemas.team import TeamCreate
from app.services.team_service import TeamRegistrationError
from app.services.team_service import create_team

BASE_DIR = Path(__file__).resolve().parents[1]

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/teams")
async def teams(request: Request, db: Session = Depends(get_db)):
    teams_list = db.query(Team).order_by(Team.created_at.desc(), Team.id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="admin/teams.html",
        context={
            "title": "Admin - Seleções",
            "teams": teams_list,
        },
    )


@router.get("/teams/new")
async def new_team(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin/team_form.html",
        context={
            "title": "Nova seleção",
            "form": {},
            "errors": [],
        },
    )


@router.post("/teams")
async def create_team_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    code: Annotated[str, Form()],
    flag_url: Annotated[str, Form()],
):
    form_data = {
        "name": name,
        "code": code,
        "flag_url": flag_url,
    }

    try:
        team_data = TeamCreate(
            name=name,
            code=code,
            flag_url=flag_url,
        )
        create_team(db, team_data)
    except (ValidationError, TeamRegistrationError) as error:
        errors = (
            _format_validation_errors(error)
            if isinstance(error, ValidationError)
            else error.messages
        )
        return templates.TemplateResponse(
            request=request,
            name="admin/team_form.html",
            context={
                "title": "Nova seleção",
                "form": form_data,
                "errors": errors,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/admin/teams",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _format_validation_errors(error: ValidationError) -> list[str]:
    messages = []

    for item in error.errors():
        field = item.get("loc", ["campo"])[0]
        field_names = {
            "name": "nome",
            "code": "código FIFA",
            "flag_url": "URL da bandeira",
        }
        messages.append(f"Verifique o campo {field_names.get(field, field)}.")

    return messages or ["Verifique os dados informados."]
