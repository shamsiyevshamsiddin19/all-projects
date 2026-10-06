"""Payme (checkout.paycom.uz / business.payme.uz) to'lov integratsiyasi.

Click'dan farqi: bitta prepare/complete o'rniga OLTITA JSON-RPC metod
(CheckPerformTransaction, CreateTransaction, PerformTransaction,
CancelTransaction, CheckTransaction, GetStatement) va imzo o'rniga
HTTP Basic Auth ishlatiladi.

Tez boshlash:

    from payme_payment import PaymeConfig, checkout_url, som_to_tiyin, handle_request

    url = checkout_url({"order_id": 42}, som_to_tiyin(5000))
    # foydalanuvchini `url` ga yuboring

    # endpoint'ingizda (bitta manzil — hamma metod shu yerga tushadi):
    response = handle_request(request_json, authorization_header)
    # `response` ni JSON qilib qaytaring
"""

from .payme_auth import check_auth
from .payme_checkout import checkout_url, som_to_tiyin
from .payme_config import ConfigError, PaymeConfig, get_config, set_config
from .payme_errors import PaymeError
from .payme_methods import handle_request
from .payme_orders import (
    REASON_DEBIT_OPERATION_ERROR,
    REASON_RECEIVER_NOT_FOUND,
    REASON_REFUND,
    REASON_TIMEOUT,
    REASON_TRANSACTION_ERROR,
    REASON_UNKNOWN,
    STATE_CANCELLED,
    STATE_CANCELLED_AFTER_PAID,
    STATE_PAID,
    STATE_PENDING,
    PaymeAccount,
    PaymeTransaction,
)

__version__ = "1.0.0"

__all__ = [
    "PaymeConfig",
    "ConfigError",
    "get_config",
    "set_config",
    "checkout_url",
    "som_to_tiyin",
    "check_auth",
    "PaymeError",
    "handle_request",
    "PaymeAccount",
    "PaymeTransaction",
    "STATE_PENDING",
    "STATE_PAID",
    "STATE_CANCELLED",
    "STATE_CANCELLED_AFTER_PAID",
    "REASON_RECEIVER_NOT_FOUND",
    "REASON_DEBIT_OPERATION_ERROR",
    "REASON_TRANSACTION_ERROR",
    "REASON_TIMEOUT",
    "REASON_REFUND",
    "REASON_UNKNOWN",
]
