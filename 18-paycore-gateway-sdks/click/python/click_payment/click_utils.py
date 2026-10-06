"""Kichik yordamchilar. Bu faylga tegishingiz shart emas."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

# Summalarni solishtirishda ruxsat etilgan farq (tiyin yaxlitlashlari uchun).
AMOUNT_TOLERANCE = Decimal("0.01")


def missing_fields(data: Mapping[str, Any], required: tuple[str, ...]) -> list[str]:
    """So'rovda yetishmayotgan majburiy maydonlar ro'yxati."""
    return [f for f in required if data.get(f) in (None, "")]


def as_int(value: Any) -> int:
    """Xavfsiz int'ga o'girish — bo'lmasa 0."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def amounts_match(received: Any, expected: Decimal) -> bool:
    """Click yuborgan summa bazadagiga mos keladimi?

    Click "5000", "5000.00" yoki "5000.0" yuborishi mumkin — hammasi bir xil
    summa. Shuning uchun satrni Decimal qilib, kichik farq bilan solishtiramiz.
    """
    try:
        got = Decimal(str(received).strip())
    except (InvalidOperation, AttributeError, TypeError):
        return False
    return abs(got - expected) < AMOUNT_TOLERANCE
