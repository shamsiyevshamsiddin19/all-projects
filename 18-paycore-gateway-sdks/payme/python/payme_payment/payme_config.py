"""Payme sozlamalari — hammasi .env dan o'qiladi.

Qaysi qiymatlar kerakligi `.env.example` da yozilgan.
Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """.env to'liq to'ldirilmaganda ko'tariladi."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"{name} .env da o'rnatilmagan. `.env.example` dan `.env` yasab, "
            f"qiymatlarni Payme kabinetidan (business.payme.uz) to'ldiring."
        )
    return value


@dataclass(frozen=True)
class PaymeConfig:
    """Payme kabinetidan olinadigan sozlamalar."""

    merchant_id: str
    secret_key: str
    merchant_login: str = "Paycom"
    checkout_base_url: str = "https://checkout.paycom.uz"

    @classmethod
    def from_env(cls) -> "PaymeConfig":
        return cls(
            merchant_id=_require("PAYME_MERCHANT_ID"),
            secret_key=_require("PAYME_SECRET_KEY"),
            merchant_login=os.getenv("PAYME_MERCHANT_LOGIN", "Paycom").strip() or "Paycom",
            checkout_base_url=(
                os.getenv("PAYME_CHECKOUT_BASE_URL", "https://checkout.paycom.uz").strip()
            ),
        )


_config: PaymeConfig | None = None


def get_config() -> PaymeConfig:
    """Sozlamalarni bir marta o'qib, keyin keshdan beradi."""
    global _config
    if _config is None:
        _config = PaymeConfig.from_env()
    return _config


def set_config(config: PaymeConfig | None) -> None:
    """Sozlamani qo'lda o'rnatish (.env ishlatmasangiz yoki testlarda).

    `None` bersangiz kesh tozalanadi.
    """
    global _config
    _config = config
