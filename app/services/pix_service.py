import base64
import io
import unicodedata
from decimal import Decimal

import qrcode


def generate_pix_payload(
    pix_key,
    recipient_name,
    recipient_city,
    amount,
) -> str:
    amount_value = Decimal(str(amount)).quantize(Decimal("0.01"))
    merchant_account_info = _emv(
        "26",
        _emv("00", "br.gov.bcb.pix")
        + _emv("01", str(pix_key).strip())
    )

    payload_without_crc = (
        _emv("00", "01")
        + merchant_account_info
        + _emv("52", "0000")
        + _emv("53", "986")
        + _emv("54", f"{amount_value:.2f}")
        + _emv("58", "BR")
        + _emv("59", _normalize_text(recipient_name, 25))
        + _emv("60", _normalize_text(recipient_city, 15))
        + _emv("62", _emv("05", "***"))
        + "6304"
    )

    return payload_without_crc + _crc16(payload_without_crc)


def generate_pix_qrcode_base64(payload: str) -> str:
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _emv(identifier: str, value: str) -> str:
    return f"{identifier}{len(value):02d}{value}"


def _normalize_text(value, max_length: int) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_value.upper()[:max_length]


def _crc16(payload: str) -> str:
    crc = 0xFFFF

    for char in payload.encode("ascii"):
        crc ^= char << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF

    return f"{crc:04X}"
