"""Uzum Bank sozlamalari — hammasi .env dan o'qiladi.

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
            f"qiymatlarni Uzum Bank kabinetidan (merchants.uzumbank.uz) to'ldiring."
        )
    return value


@dataclass(frozen=True)
class UzumConfig:
    """Uzum Bank kabinetidan olinadigan sozlamalar.

    `service_id` — kabinetda xizmatingizga berilgan raqam. Uzum Bank
    ilovasida foydalanuvchilar aynan shu ID orqali xizmatingizni topadi
    (Click/Payme'dagidek to'lov havolasi YO'Q — pastga qarang).

    `webhook_login` / `webhook_secret` — webhook so'rovlarini tasdiqlash
    uchun kabinetda o'zingiz belgilaydigan login/parol juftligi (Payme'dagi
    doim "Paycom" bo'ladigan login'dan farqli, bu yerda ikkalasi ham
    o'zingiznikidir).
    """

    service_id: int
    webhook_login: str
    webhook_secret: str

    @classmethod
    def from_env(cls) -> "UzumConfig":
        return cls(
            service_id=int(_require("UZUM_SERVICE_ID")),
            webhook_login=_require("UZUM_WEBHOOK_LOGIN"),
            webhook_secret=_require("UZUM_WEBHOOK_SECRET"),
        )


_config: UzumConfig | None = None


def get_config() -> UzumConfig:
    """Sozlamalarni bir marta o'qib, keyin keshdan beradi."""
    global _config
    if _config is None:
        _config = UzumConfig.from_env()
    return _config


def set_config(config: UzumConfig | None) -> None:
    """Sozlamani qo'lda o'rnatish (.env ishlatmasangiz yoki testlarda).

    `None` bersangiz kesh tozalanadi.
    """
    global _config
    _config = config
