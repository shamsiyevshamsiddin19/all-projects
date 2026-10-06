"""Talaba parollarini shifrlash (Fernet, simmetrik)."""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .config import settings

_fernet: Fernet | None = None


def _get() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.fernet_key:
            raise RuntimeError(
                "FERNET_KEY o'rnatilmagan. Generatsiya: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        _fernet = Fernet(settings.fernet_key.encode())
    return _fernet


def encrypt(plaintext: str) -> str:
    return _get().encrypt(plaintext.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _get().decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("Parolni ochib bo'lmadi (FERNET_KEY o'zgargan bo'lishi mumkin)")
