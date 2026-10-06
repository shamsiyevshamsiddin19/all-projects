"""Click COMPLETE so'rovi.

Click bu so'rovni "pul yechildi, endi mahsulotni ber" deb yuboradi
(yoki "foydalanuvchi bekor qildi" deb — `error` maydoniga qarab).

Biz tekshiramiz:
    - so'rov to'liqmi                       -> yo'q bo'lsa -8
    - imzo haqiqiymi                        -> yo'q bo'lsa -1
    - bunday buyurtma bormi                 -> yo'q bo'lsa -5
    - merchant_prepare_id prepare'dagi id'ga mos keladimi -> yo'q bo'lsa -6
    - summa bazadagiga mos keladimi         -> yo'q bo'lsa -2

Hammasi joyida bo'lsa buyurtmani "to'landi" deb belgilaymiz va
click_orders.on_paid() ni chaqiramiz — mahsulot o'sha yerda beriladi.

Bu faylga tegishingiz shart emas — bazangizga ulanish click_orders.py da.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from . import click_errors as err
from . import click_orders
from .click_config import get_config
from .click_signature import ACTION_COMPLETE, check_sign
from .click_utils import amounts_match, as_int, missing_fields

logger = logging.getLogger("click")

# Complete'da prepare'dagilarga qo'shimcha merchant_prepare_id ham keladi.
REQUIRED_FIELDS = (
    "click_trans_id",
    "service_id",
    "merchant_trans_id",
    "merchant_prepare_id",
    "amount",
    "sign_time",
    "sign_string",
)


def handle_complete(data: Mapping[str, Any]) -> dict[str, Any]:
    """Click complete so'rovini qayta ishlaydi va javob dict qaytaradi."""
    missing = missing_fields(data, REQUIRED_FIELDS)
    if missing:
        logger.warning("Click complete: maydon yetishmayapti: %s", missing)
        return _response(data, 0, err.BAD_REQUEST)

    if not check_sign(data, ACTION_COMPLETE, get_config()):
        logger.warning(
            "Click complete: imzo xato (merchant_trans_id=%s)",
            data.get("merchant_trans_id"),
        )
        return _response(data, 0, err.SIGN_CHECK_FAILED)

    merchant_trans_id = str(data["merchant_trans_id"])
    click_trans_id = str(data["click_trans_id"])
    order = click_orders.find_order(merchant_trans_id)

    if order is None:
        logger.warning("Click complete: buyurtma topilmadi (%s)", merchant_trans_id)
        return _response(data, 0, err.USER_NOT_FOUND)

    # prepare'da qaytargan id bilan bir xil bo'lishi shart.
    if as_int(data.get("merchant_prepare_id")) != order.id:
        logger.warning(
            "Click complete: merchant_prepare_id mos emas (kutilgan=%s, kelgan=%s)",
            order.id,
            data.get("merchant_prepare_id"),
        )
        return _response(data, order.id, err.TRANSACTION_NOT_FOUND)

    if not amounts_match(data.get("amount"), order.amount):
        logger.warning(
            "Click complete: summa mos emas (bazada=%s, so'rovda=%s)",
            order.amount,
            data.get("amount"),
        )
        return _response(data, order.id, err.INCORRECT_AMOUNT)

    # Takroriy callback: Click javobni ololmay qayta urgan. Pul allaqachon
    # hisobga olingan — muvaffaqiyat deb javob beramiz, on_paid QAYTA
    # chaqirilmaydi.
    if order.status == click_orders.STATUS_PAID:
        logger.info("Click complete: takroriy callback (%s)", merchant_trans_id)
        return _response(data, order.id, err.SUCCESS)

    if order.status == click_orders.STATUS_CANCELLED:
        return _response(data, order.id, err.TRANSACTION_CANCELLED)

    # Click o'zi bekor qilish/xato haqida xabar bergan.
    click_error = as_int(data.get("error"))
    if click_error != 0:
        click_orders.mark_cancelled(order, click_trans_id)
        order.status = click_orders.STATUS_CANCELLED
        logger.info(
            "Click complete: to'lov bekor qilindi (%s, click error=%s)",
            merchant_trans_id,
            click_error,
        )
        _safe_call(click_orders.on_cancelled, order, "on_cancelled")
        return _response(data, order.id, err.TRANSACTION_CANCELLED)

    # Asosiy holat: to'lov muvaffaqiyatli.
    #
    # mark_paid() faqat HAQIQATAN pending -> paid o'tkazgan bo'lsa True
    # qaytaradi. Parallel kelgan ikkinchi callback False oladi va mahsulot
    # ikki marta berilmaydi.
    if not click_orders.mark_paid(order, click_trans_id):
        logger.info(
            "Click complete: boshqa callback ulgurdi (%s) — on_paid o'tkazib yuborildi",
            merchant_trans_id,
        )
        return _response(data, order.id, err.SUCCESS)

    order.status = click_orders.STATUS_PAID
    logger.info(
        "Click complete OK (buyurtma=%s, id=%s, summa=%s)",
        merchant_trans_id,
        order.id,
        order.amount,
    )
    _safe_call(click_orders.on_paid, order, "on_paid")

    return _response(data, order.id, err.SUCCESS)


def _safe_call(func, order, name: str) -> None:
    """Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.

    Nega xatoni yutamiz? Bu nuqtaga yetganda pul yechilgan va buyurtma
    "paid" deb belgilangan. Click'ga xato qaytarsak u qayta uradi — lekin
    yuqorida "allaqachon to'langan" bo'lib SUCCESS oladi, ya'ni on_paid
    baribir qayta ishlamaydi. Shuning uchun to'g'ri yo'l: xatoni loglab,
    keyin qo'lda hal qilish.
    """
    try:
        func(order)
    except Exception:
        logger.exception(
            "Click %s() xatosi (buyurtma=%s) — to'lov 'paid' holicha qoldi, "
            "qo'lda tekshiring",
            name,
            order.merchant_trans_id,
        )


def _response(
    data: Mapping[str, Any], merchant_confirm_id: int, error: int
) -> dict[str, Any]:
    """Click kutadigan javob shakli.

    Diqqat: prepare'da `merchant_prepare_id`, complete'da esa
    `merchant_confirm_id` deb nomlanadi.
    """
    return {
        "click_trans_id": as_int(data.get("click_trans_id")),
        "merchant_trans_id": str(data.get("merchant_trans_id", "")),
        "merchant_confirm_id": int(merchant_confirm_id),
        "error": int(error),
        "error_note": err.error_note(error),
    }
