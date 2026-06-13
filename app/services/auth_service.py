from fastapi import HTTPException
from fastapi import status
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email.strip().lower())
        .first()
    )

    if not user or not pwd_context.verify(password, user.password_hash):
        raise AuthServiceError("Email ou senha inválidos.")

    if not user.is_active:
        raise AuthServiceError("Usuário inativo.")

    if not user.is_approved:
        raise AuthServiceError("Seu cadastro ainda aguarda aprovação.")

    return user


def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.get(User, user_id)


def require_current_user(request: Request, db: Session) -> User:
    user = get_current_user(request, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Usuário não autenticado.",
            headers={"Location": "/login"},
        )

    return user


def require_admin_user(request: Request, db: Session) -> User:
    user = require_current_user(request, db)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Acesso administrativo restrito.",
            headers={"Location": "/dashboard"},
        )

    return user
