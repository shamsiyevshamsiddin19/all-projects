"""Payme to'lov havolasini (checkout link) qurish.

Click'dan farqli — Payme havolasi query-string emas, parametrlarni
`key=value;key=value` shaklida yig'ib, BUTUN satrni base64 qiladi:

    https://checkout.paycom.uz/<base64("m=MERCHANT_ID;ac.order_id=42;a=500000")>

Bu faylga tegishingiz shart emas.
"""

from __future__ import annotations

import base64
from decimal import Decimal

from .payme_config import PaymeConfig, get_config


def som_to_tiyin(som: Decimal | int | float | str) -> int:
    """So'mni tiyinga o'giradi (1 so'm = 100 tiyin). Payme SUMMA TIYINDA kutadi."""
    return int(round(Decimal(str(som)) * 100))


def checkout_url(
    account: dict[str, str | int],
    amount_tiyin: int,
    *,
    return_url: str | None = None,
    lang: str | None = None,
    config: PaymeConfig | None = None,
) -> str:
    """Foydalanuvchi yuboriladigan Payme to'lov havolasini quradi.

    `account` — Payme'ga yuboriladigan hisob maydonlari (masalan
    `{"order_id": "42"}`). Shu maydonlar `payme_orders.py`dagi
    `find_account()` ga qaytib keladi — ular orqali buyurtmani topasiz.

    `amount_tiyin` — summa TIYINDA (so'm emas!). `som_to_tiyin()` bilan
    o'giring: `checkout_url({"order_id": 42}, som_to_tiyin(5000))`.

    Namuna:
        url = checkout_url({"order_id": 42}, som_to_tiyin(5000))
        # foydalanuvchini shu havolaga yuboring
    """
    cfg = config or get_config()

    parts = [f"m={cfg.merchant_id}"]
    for key, value in account.items():
        parts.append(f"ac.{key}={value}")
    parts.append(f"a={int(amount_tiyin)}")

    if return_url:
        parts.append(f"c={return_url}")
    if lang:
        parts.append(f"l={lang}")

    raw = ";".join(parts)
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")

    return f"{cfg.checkout_base_url}/{encoded}"
