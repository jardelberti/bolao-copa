from sqlalchemy.orm import Session

from app.models.payment_settings import PaymentSettings

DEFAULT_PIX_KEY = "+5547999283466"
DEFAULT_PIX_KEY_TYPE = "PHONE"
DEFAULT_RECIPIENT_NAME = "Jardel Berti"
DEFAULT_RECIPIENT_CITY = "RIO NEGRINHO"


class PaymentSettingsServiceError(Exception):
    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__(", ".join(messages))


def get_or_create_payment_settings(db: Session) -> PaymentSettings:
    settings = db.query(PaymentSettings).order_by(PaymentSettings.id.asc()).first()

    if settings:
        return settings

    settings = PaymentSettings(
        pix_key=DEFAULT_PIX_KEY,
        pix_key_type=DEFAULT_PIX_KEY_TYPE,
        recipient_name=DEFAULT_RECIPIENT_NAME,
        recipient_city=DEFAULT_RECIPIENT_CITY,
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)

    return settings


def update_payment_settings(
    db: Session,
    pix_key: str,
    pix_key_type: str,
    recipient_name: str,
    recipient_city: str,
) -> PaymentSettings:
    errors = _validate_settings(
        pix_key=pix_key,
        pix_key_type=pix_key_type,
        recipient_name=recipient_name,
        recipient_city=recipient_city,
    )

    if errors:
        raise PaymentSettingsServiceError(errors)

    settings = get_or_create_payment_settings(db)

    try:
        settings.pix_key = pix_key.strip()
        settings.pix_key_type = pix_key_type.strip().upper()
        settings.recipient_name = recipient_name.strip()
        settings.recipient_city = recipient_city.strip().upper()
        db.commit()
        db.refresh(settings)
    except Exception:
        db.rollback()
        raise

    return settings


def _validate_settings(
    pix_key: str,
    pix_key_type: str,
    recipient_name: str,
    recipient_city: str,
) -> list[str]:
    errors = []

    if not pix_key.strip():
        errors.append("Informe a chave PIX.")

    if not pix_key_type.strip():
        errors.append("Informe o tipo da chave PIX.")

    if not recipient_name.strip():
        errors.append("Informe o nome do recebedor.")

    if not recipient_city.strip():
        errors.append("Informe a cidade do recebedor.")

    return errors
