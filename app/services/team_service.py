from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.team import Team
from app.schemas.team import TeamCreate


class TeamRegistrationError(Exception):
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__(", ".join(messages))


def create_team(db: Session, team_data: TeamCreate) -> Team:
    errors = _validate_team_data(db, team_data)

    if errors:
        raise TeamRegistrationError(errors)

    team = Team(
        name=team_data.name.strip(),
        code=team_data.code.strip().upper(),
        flag_url=team_data.flag_url.strip(),
    )

    try:
        db.add(team)
        db.commit()
        db.refresh(team)
    except IntegrityError as exc:
        db.rollback()
        raise TeamRegistrationError(["Nome ou código FIFA já cadastrado."]) from exc
    except Exception:
        db.rollback()
        raise

    return team


def _validate_team_data(db: Session, team_data: TeamCreate) -> list[str]:
    errors = []
    name = team_data.name.strip()
    code = team_data.code.strip().upper()
    flag_url = team_data.flag_url.strip()

    if not name:
        errors.append("Informe o nome da seleção.")

    if not code:
        errors.append("Informe o código FIFA.")

    if not flag_url:
        errors.append("Informe a URL da bandeira.")

    if name and _name_exists(db, name):
        errors.append("Este nome já está cadastrado.")

    if code and _code_exists(db, code):
        errors.append("Este código FIFA já está cadastrado.")

    return errors


def _name_exists(db: Session, name: str) -> bool:
    return db.query(Team).filter(func.lower(Team.name) == name.lower()).first() is not None


def _code_exists(db: Session, code: str) -> bool:
    return db.query(Team).filter(func.upper(Team.code) == code.upper()).first() is not None
