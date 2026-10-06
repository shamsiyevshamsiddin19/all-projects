"""Click sozlamalari — hammasi .env dan o'qiladi.

Qaysi qiymat kerakligi `.env.example` da yozilgan.
Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode


class ConfigError(RuntimeError):
    """.env to'ldirilmaganda ko'tariladi."""


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(
            f"{name} .env da yo'q. `.env.example` dan `.env` yasang va "
            f"qiymatlarni Click kabinetidan (merchant.click.uz) to'ldiring."
        )
    return value


@dataclass(frozen=True)
class ClickConfig:
    service_id: str
    merchant_id: str
    secret_key: str
    merchant_user_id: str
    pay_base_url: str = "https://my.click.uz/services/pay"
    return_url: str = ""

    @classmethod
    def from_env(cls) -> "ClickConfig":
        return cls(
            service_id=_require("CLICK_SERVICE_ID"),
            merchant_id=_require("CLICK_MERCHANT_ID"),
            secret_key=_require("CLICK_SECRET_KEY"),
            merchant_user_id=_require("CLICK_MERCHANT_USER_ID"),
            pay_base_url=os.getenv(
                "CLICK_PAY_BASE_URL", "https://my.click.uz/services/pay"
            ).strip(),
            return_url=os.getenv("CLICK_RETURN_URL", "").strip(),
        )


_config: ClickConfig | None = None


def get_config() -> ClickConfig:
    """Sozlamalarni bir marta o'qib, keyin keshdan beradi."""
    global _config
    if _config is None:
        _config = ClickConfig.from_env()
    return _config


def set_config(config: ClickConfig) -> None:
    """Sozlamani qo'lda o'rnatish (.env ishlatmasangiz yoki testlarda)."""
    global _config
    _config = config


def payment_url(
    merchant_trans_id: str,
    amount: Decimal | int | float | str,
    return_url: str | None = None,
) -> str:
    """Foydalanuvchi yuboriladigan Click to'lov havolasini quradi.

    `merchant_trans_id` — sizning to'lov identifikatoringiz (masalan "ORD42").
    Click uni prepare/complete so'rovlarida aynan shu holda qaytarib yuboradi.

    Namuna:
        url = payment_url("ORD42", 5000)
        # foydalanuvchini shu havolaga yuboring
    """
    config = get_config()

    params = {
        "service_id": config.service_id,
        "merchant_id": config.merchant_id,
        "amount": format_amount(amount),
        "transaction_param": str(merchant_trans_id),
        "merchant_user_id": config.merchant_user_id,
    }

    final_return_url = return_url if return_url is not None else config.return_url
    if final_return_url:
        params["return_url"] = final_return_url

    return f"{config.pay_base_url}?{urlencode(params)}"


def format_amount(amount: Decimal | int | float | str) -> str:
    """Summani to'lov havolasi uchun chiqaradi (5000.00 -> "5000").

    Bu faqat HAVOLA uchun — imzo hisoblashda Click yuborgan xom satr
    ishlatiladi (click_signature.py izohiga qarang).
    """
    d = Decimal(str(amount))
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d:.2f}"
