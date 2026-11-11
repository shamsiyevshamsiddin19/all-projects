"""Maydon darajasida shifrlash uchun kichik, markazlashgan yordamchilar."""

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _fernet() -> Fernet:
    key = settings.FIELD_ENCRYPTION_KEY
    if not key:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY sozlanmagan; maxfiy to'lov ma'lumotini "
            "saqlash mumkin emas."
        )
    try:
        return Fernet(key.encode())
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY noto'g'ri Fernet kaliti."
        ) from exc


def encrypt_card_number(card_number: str) -> str:
    """Faqat raqamlardan iborat karta qiymatini shifrlaydi."""
    return _fernet().encrypt(card_number.encode("utf-8")).decode("utf-8")


def decrypt_card_number(encrypted_value: str) -> str:
    """Xizmat darajasidagi zarur holatlar uchungina ochadi."""
    try:
        return _fernet().decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Karta ma'lumotini ochib bo'lmadi.") from exc


def card_last4(card_number: str) -> str:
    return card_number[-4:]
