from decimal import Decimal

from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegistrationError(Exception):
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__(", ".join(messages))


def create_user(db: Session, user_data: UserCreate) -> User:
    errors = _validate_user_data(db, user_data)

    if errors:
        raise UserRegistrationError(errors)

    email = user_data.email.strip().lower()
    user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=pwd_context.hash(user_data.password),
        pix_type=user_data.pix_type.strip(),
        pix_key=user_data.pix_key.strip(),
        is_active=True,
        is_approved=False,
        is_admin=False,
    )

    try:
        db.add(user)
        db.flush()

        wallet = Wallet(
            user_id=user.id,
            balance=Decimal("0.00"),
        )
        db.add(wallet)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise UserRegistrationError(["Este email já está cadastrado."]) from exc
    except Exception:
        db.rollback()
        raise

    return user


def _validate_user_data(db: Session, user_data: UserCreate) -> list[str]:
    errors = []
    name = user_data.name.strip()
    email = user_data.email.strip().lower()
    pix_type = user_data.pix_type.strip()
    pix_key = user_data.pix_key.strip()

    if not name:
        errors.append("Informe seu nome.")

    if not email:
        errors.append("Informe seu email.")

    if not pix_type:
        errors.append("Informe o tipo da chave Pix.")

    if not pix_key:
        errors.append("Informe a chave Pix.")

    if len(user_data.password) < 8:
        errors.append("A senha deve ter no mínimo 8 caracteres.")

    if user_data.password != user_data.password_confirmation:
        errors.append("A confirmação de senha não confere.")

    if email and _email_exists(db, email):
        errors.append("Este email já está cadastrado.")

    return errors


def _email_exists(db: Session, email: str) -> bool:
    return db.query(User).filter(func.lower(User.email) == email).first() is not None
