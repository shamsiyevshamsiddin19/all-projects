"""Click PREPARE so'rovi.

Click bu so'rovni "shu to'lovni qabul qila olasanmi?" deb yuboradi.
Bu bosqichda pul HALI YECHILMAGAN.

Biz tekshiramiz:
    - so'rov to'liqmi                    -> yo'q bo'lsa -8
    - imzo haqiqiymi                     -> yo'q bo'lsa -1
    - bunday buyurtma bormi              -> yo'q bo'lsa -5
    - summa bazadagiga mos keladimi      -> yo'q bo'lsa -2
    - allaqachon to'lanmaganmi           -> to'langan bo'lsa -4
    - bekor qilinmaganmi                 -> bekor bo'lsa -9

Hammasi joyida bo'lsa `error: 0` va `merchant_prepare_id` (buyurtma id'si)
qaytaramiz. Click keyin pulni yechib, click_complete.py ga murojaat qiladi.

Bu faylga tegishingiz shart emas — bazangizga ulanish click_orders.py da.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from . import click_errors as err
from . import click_orders
from .click_config import get_config
from .click_signature import ACTION_PREPARE, check_sign
from .click_utils import amounts_match, as_int, missing_fields

logger = logging.getLogger("click")

# Click prepare so'rovida yuboradigan majburiy maydonlar.
REQUIRED_FIELDS = (
    "click_trans_id",
    "service_id",
    "merchant_trans_id",
    "amount",
    "sign_time",
    "sign_string",
)


def handle_prepare(data: Mapping[str, Any]) -> dict[str, Any]:
    """Click prepare so'rovini qayta ishlaydi va javob dict qaytaradi.

    `data` — so'rovdagi maydonlar (POST form yoki JSON — farqi yo'q).
    Javobni Click'ga JSON qilib qaytaring.
    """
    missing = missing_fields(data, REQUIRED_FIELDS)
    if missing:
        logger.warning("Click prepare: maydon yetishmayapti: %s", missing)
        return _response(data, 0, err.BAD_REQUEST)

    if not check_sign(data, ACTION_PREPARE, get_config()):
        logger.warning(
            "Click prepare: imzo xato (merchant_trans_id=%s)",
            data.get("merchant_trans_id"),
        )
        return _response(data, 0, err.SIGN_CHECK_FAILED)

    merchant_trans_id = str(data["merchant_trans_id"])
    order = click_orders.find_order(merchant_trans_id)

    if order is None:
        logger.warning("Click prepare: buyurtma topilmadi (%s)", merchant_trans_id)
        return _response(data, 0, err.USER_NOT_FOUND)

    # Summani HAR DOIM bazadan tekshiramiz — so'rovdagi qiymatga ishonmaymiz.
    if not amounts_match(data.get("amount"), order.amount):
        logger.warning(
            "Click prepare: summa mos emas (bazada=%s, so'rovda=%s)",
            order.amount,
            data.get("amount"),
        )
        return _response(data, order.id, err.INCORRECT_AMOUNT)

    if order.status == click_orders.STATUS_PAID:
        return _response(data, order.id, err.ALREADY_PAID)

    if order.status == click_orders.STATUS_CANCELLED:
        return _response(data, order.id, err.TRANSACTION_CANCELLED)

    logger.info(
        "Click prepare OK (buyurtma=%s, id=%s, click_trans_id=%s)",
        merchant_trans_id,
        order.id,
        data.get("click_trans_id"),
    )
    return _response(data, order.id, err.SUCCESS)


def _response(
    data: Mapping[str, Any], merchant_prepare_id: int, error: int
) -> dict[str, Any]:
    """Click kutadigan javob shakli."""
    return {
        "click_trans_id": as_int(data.get("click_trans_id")),
        "merchant_trans_id": str(data.get("merchant_trans_id", "")),
        "merchant_prepare_id": int(merchant_prepare_id),
        "error": int(error),
        "error_note": err.error_note(error),
    }
