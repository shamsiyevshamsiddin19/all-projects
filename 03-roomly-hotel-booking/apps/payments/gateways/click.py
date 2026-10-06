"""Click Merchant API (Prepare/Complete) integratsiyasi.

Hujjat: https://docs.click.uz/click-api-request/
Webhook: POST /payments/webhook/click/  (config/urls.py)
"""

import hashlib
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone

from apps.bookings.models import Booking

from ..models import ClickTransaction, PaymentMethod, PaymentState, PaymentStatus

ERROR_SUCCESS = 0
ERROR_SIGN_FAILED = -1
ERROR_TRANS_NOT_FOUND = -6
ERROR_ALREADY_PAID = -4
ERROR_BOOKING_NOT_FOUND = -5
ERROR_TRANS_CANCELLED = -9
ERROR_INVALID_AMOUNT = -2

ACTION_PREPARE = 0
ACTION_COMPLETE = 1


class ClickError(Exception):
    def __init__(self, code: int, note: str):
        self.code = code
        self.note = note
        super().__init__(note)


def _sign_string(*parts) -> str:
    return hashlib.md5("".join(str(p) for p in parts).encode()).hexdigest()


def verify_signature(data: dict) -> bool:
    action = data.get("action")
    sign_time = data.get("sign_time", "")
    if str(action) == str(ACTION_COMPLETE):
        expected = _sign_string(
            data.get("click_trans_id", ""),
            data.get("service_id", ""),
            settings.CLICK_SECRET_KEY,
            data.get("merchant_trans_id", ""),
            data.get("merchant_prepare_id", ""),
            data.get("amount", ""),
            action,
            sign_time,
        )
    else:
        expected = _sign_string(
            data.get("click_trans_id", ""),
            data.get("service_id", ""),
            settings.CLICK_SECRET_KEY,
            data.get("merchant_trans_id", ""),
            data.get("amount", ""),
            action,
            sign_time,
        )
    return expected == data.get("sign_string")


def format_amount(amount) -> str:
    d = Decimal(str(amount))
    if d == d.to_integral_value():
        return str(int(d))
    return f"{d:.2f}"


def payment_url(booking: Booking) -> str:
    """Mehmonga yuboriladigan Click to'lov havolasini quradi.

    `transaction_param` sifatida booking_code ishlatiladi — Click prepare/complete
    so'rovlarida shu qiymatni merchant_trans_id sifatida qaytaradi.
    """
    pay_base_url = getattr(settings, "CLICK_PAY_BASE_URL", "https://my.click.uz/services/pay")
    return_url = getattr(settings, "CLICK_RETURN_URL", "")

    params = {
        "service_id": settings.CLICK_SERVICE_ID,
        "merchant_id": settings.CLICK_MERCHANT_ID,
        "amount": format_amount(booking.total_price),
        "transaction_param": booking.booking_code,
        "merchant_user_id": settings.CLICK_MERCHANT_USER_ID,
    }
    if return_url:
        params["return_url"] = return_url
    return f"{pay_base_url}?{urlencode(params)}"


def get_booking_for_payment(merchant_trans_id: str) -> Booking:
    try:
        return Booking.objects.get(booking_code=merchant_trans_id)
    except Booking.DoesNotExist as exc:
        raise ClickError(ERROR_BOOKING_NOT_FOUND, "Booking not found") from exc


def prepare(data: dict) -> dict:
    if not verify_signature(data):
        raise ClickError(ERROR_SIGN_FAILED, "SIGN CHECK FAILED!")

    booking = get_booking_for_payment(data["merchant_trans_id"])
    amount = Decimal(str(data["amount"]))

    if amount != booking.total_price:
        raise ClickError(ERROR_INVALID_AMOUNT, "Incorrect parameter amount")

    payment, _ = PaymentStatus.objects.get_or_create(
        booking=booking,
        method=PaymentMethod.CLICK,
        status=PaymentState.PENDING,
        defaults={"amount": amount, "currency": booking.room_type.currency},
    )

    ClickTransaction.objects.create(
        payment=payment,
        click_trans_id=data["click_trans_id"],
        merchant_trans_id=data["merchant_trans_id"],
        action=ACTION_PREPARE,
        raw_request=data,
    )

    return {
        "click_trans_id": data["click_trans_id"],
        "merchant_trans_id": data["merchant_trans_id"],
        "merchant_prepare_id": payment.id,
        "error": ERROR_SUCCESS,
        "error_note": "Success",
    }


def complete(data: dict) -> dict:
    if not verify_signature(data):
        raise ClickError(ERROR_SIGN_FAILED, "SIGN CHECK FAILED!")

    booking = get_booking_for_payment(data["merchant_trans_id"])
    merchant_prepare_id = data.get("merchant_prepare_id")

    try:
        payment = PaymentStatus.objects.get(id=merchant_prepare_id, booking=booking, method=PaymentMethod.CLICK)
    except PaymentStatus.DoesNotExist as exc:
        raise ClickError(ERROR_TRANS_NOT_FOUND, "Transaction not found") from exc

    error = int(data.get("error", 0))

    ClickTransaction.objects.create(
        payment=payment,
        click_trans_id=data["click_trans_id"],
        click_paydoc_id=str(data.get("click_paydoc_id", "")),
        merchant_trans_id=data["merchant_trans_id"],
        action=ACTION_COMPLETE,
        error_code=error,
        raw_request=data,
    )

    if error < 0:
        payment.status = PaymentState.FAILED
        payment.save(update_fields=["status"])
        raise ClickError(error, "Payment failed on Click side")

    if payment.status != PaymentState.PAID:
        payment.status = PaymentState.PAID
        payment.transaction_id = data["click_trans_id"]
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "transaction_id", "paid_at"])

    return {
        "click_trans_id": data["click_trans_id"],
        "merchant_trans_id": data["merchant_trans_id"],
        "merchant_confirm_id": payment.id,
        "error": ERROR_SUCCESS,
        "error_note": "Success",
    }
