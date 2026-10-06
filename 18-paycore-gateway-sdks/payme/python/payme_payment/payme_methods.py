"""Payme Merchant API'ning 6 metodi va JSON-RPC dispatcher.

Bu modul HECH QANDAY web-framework'ga bog'liq emas: kiruvchi so'rov ma'lumotini
oddiy dict sifatida oladi, javobni ham dict qilib qaytaradi. FastAPI, Flask,
Django — qaysi birida ishlatsangiz ham shu kod o'zgarmaydi.

Oqim (Click'dagi prepare/complete'dan farqli, Payme'da OLTITA metod bor):

    CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?" (pul yo'q hali)
    CreateTransaction       — Payme tranzaksiya ochadi (bizning "prepare"imiz)
    PerformTransaction      — pul yechildi, tasdiqla (bizning "complete"imiz)
    CancelTransaction       — to'lovni yoki tasdiqlangan to'lovni bekor qil
    CheckTransaction        — tranzaksiya holatini so'raydi
    GetStatement            — vaqt oralig'idagi tranzaksiyalar ro'yxati

Bu faylga tegishingiz shart emas — bazangizga ulanish payme_orders.py da.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from . import payme_errors as err
from . import payme_orders as orders
from .payme_auth import check_auth
from .payme_config import PaymeConfig, get_config
from .payme_errors import PaymeError

Handler = Callable[[Mapping[str, Any]], dict]


# =============================================================================
#  1. CheckPerformTransaction — "bu to'lovni qabul qila olasanmi?"
# =============================================================================


def check_perform_transaction(params: Mapping[str, Any]) -> dict:
    account = _require_dict(params, "account")
    amount = _require_int(params, "amount")

    acc = orders.find_account(account)
    if acc is None:
        raise err.order_not_found()

    if not acc.payable:
        raise err.order_not_payable()

    if amount != acc.amount:
        raise err.invalid_amount()

    existing = orders.get_active_transaction_for_account(account)
    if existing is not None:
        raise err.transaction_already_exists()

    return {"allow": True}


# =============================================================================
#  2. CreateTransaction — Payme tranzaksiya ochadi ("prepare")
# =============================================================================


def create_transaction(params: Mapping[str, Any]) -> dict:
    payme_id = _require_str(params, "id")
    payme_time = _require_int(params, "time")
    amount = _require_int(params, "amount")
    account = _require_dict(params, "account")

    existing = orders.get_transaction(payme_id)

    if existing is not None:
        if existing.state != orders.STATE_PENDING:
            # Boshqa holatga o'tib bo'lgan (to'langan/bekor qilingan)
            # tranzaksiyani qayta "yaratib" bo'lmaydi.
            raise err.unable_to_perform()

        if _is_expired(existing.payme_time):
            orders.mark_cancelled(payme_id, orders.REASON_TIMEOUT)
            raise err.unable_to_perform()

        # Idempotent takror so'rov — bir xil natijani qaytaramiz.
        return _create_result(existing)

    # Yangi tranzaksiya — avval CheckPerformTransaction bilan bir xil
    # tekshiruvlarni bajaramiz.
    check_perform_transaction({"account": account, "amount": amount})

    created = orders.create_transaction(payme_id, payme_time, amount, account)
    return _create_result(created)


def _create_result(tx: orders.PaymeTransaction) -> dict:
    return {
        "create_time": tx.create_time,
        "transaction": tx.our_id,
        "state": tx.state,
    }


# =============================================================================
#  3. PerformTransaction — pul yechildi, tasdiqla ("complete")
# =============================================================================


def perform_transaction(params: Mapping[str, Any]) -> dict:
    payme_id = _require_str(params, "id")

    tx = orders.get_transaction(payme_id)
    if tx is None:
        raise err.transaction_not_found()

    if tx.state == orders.STATE_PAID:
        # Takroriy callback — mahsulot allaqachon berilgan, on_paid QAYTA
        # chaqirilmaydi.
        return _perform_result(tx)

    if tx.state != orders.STATE_PENDING:
        raise err.unable_to_perform()

    if _is_expired(tx.payme_time):
        orders.mark_cancelled(payme_id, orders.REASON_TIMEOUT)
        raise err.unable_to_perform()

    updated = orders.mark_performed(payme_id)
    if updated is None:
        # Parallel so'rov bizdan oldin ulgurdi — takroriy deb javob beramiz.
        again = orders.get_transaction(payme_id)
        return _perform_result(again) if again else _perform_result(tx)

    account = orders.find_account(updated.account)
    updated.account_extra = account.extra if account else {}
    _safe_call(orders.on_paid, updated, "on_paid")

    return _perform_result(updated)


def _perform_result(tx: orders.PaymeTransaction) -> dict:
    return {
        "transaction": tx.our_id,
        "perform_time": tx.perform_time,
        "state": tx.state,
    }


# =============================================================================
#  4. CancelTransaction — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
# =============================================================================


def cancel_transaction(params: Mapping[str, Any]) -> dict:
    payme_id = _require_str(params, "id")
    reason = _require_int(params, "reason")

    tx = orders.get_transaction(payme_id)
    if tx is None:
        raise err.transaction_not_found()

    if tx.state in (orders.STATE_CANCELLED, orders.STATE_CANCELLED_AFTER_PAID):
        # Idempotent — mavjud natijani qaytaramiz, sababni yangilamaymiz.
        return _cancel_result(tx)

    if tx.state == orders.STATE_PAID:
        account = orders.find_account(tx.account)
        tx.account_extra = account.extra if account else {}
        if not _safe_call_bool(orders.can_refund, tx, default=True):
            raise err.unable_to_cancel()

    updated = orders.mark_cancelled(payme_id, reason)
    if updated is None:
        # Parallel bekor qilish bizdan oldin ulgurdi.
        again = orders.get_transaction(payme_id)
        return _cancel_result(again) if again else _cancel_result(tx)

    account = orders.find_account(updated.account)
    updated.account_extra = account.extra if account else {}
    _safe_call(orders.on_cancelled, updated, "on_cancelled")

    return _cancel_result(updated)


def _cancel_result(tx: orders.PaymeTransaction) -> dict:
    return {
        "transaction": tx.our_id,
        "cancel_time": tx.cancel_time,
        "state": tx.state,
    }


# =============================================================================
#  5. CheckTransaction — tranzaksiya holatini so'raydi
# =============================================================================


def check_transaction(params: Mapping[str, Any]) -> dict:
    payme_id = _require_str(params, "id")

    tx = orders.get_transaction(payme_id)
    if tx is None:
        raise err.transaction_not_found()

    return {
        "create_time": tx.create_time,
        "perform_time": tx.perform_time,
        "cancel_time": tx.cancel_time,
        "transaction": tx.our_id,
        "state": tx.state,
        "reason": tx.reason,
    }


# =============================================================================
#  6. GetStatement — vaqt oralig'idagi tranzaksiyalar ro'yxati
# =============================================================================


def get_statement(params: Mapping[str, Any]) -> dict:
    from_ms = _require_int(params, "from")
    to_ms = _require_int(params, "to")

    txs = orders.list_transactions(from_ms, to_ms)

    return {
        "transactions": [
            {
                "id": tx.payme_id,
                "time": tx.payme_time,
                "amount": tx.amount,
                "account": tx.account,
                "create_time": tx.create_time,
                "perform_time": tx.perform_time,
                "cancel_time": tx.cancel_time,
                "transaction": tx.our_id,
                "state": tx.state,
                "reason": tx.reason,
            }
            for tx in txs
        ]
    }


# =============================================================================
#  JSON-RPC dispatcher — HTTP qatlami shu bitta funksiyani chaqiradi
# =============================================================================

_METHODS: dict[str, Handler] = {
    "CheckPerformTransaction": check_perform_transaction,
    "CreateTransaction": create_transaction,
    "PerformTransaction": perform_transaction,
    "CancelTransaction": cancel_transaction,
    "CheckTransaction": check_transaction,
    "GetStatement": get_statement,
}


def handle_request(
    body: Mapping[str, Any],
    authorization_header: str | None,
    config: PaymeConfig | None = None,
) -> dict:
    """Payme'dan kelgan JSON-RPC so'rovini to'liq qayta ishlaydi.

    `body` — so'rov JSON'i (`{"method", "params", "id"}`).
    `authorization_header` — HTTP `Authorization` sarlavhasi (Basic ...).

    Har doim `{"result": ...}` yoki `{"error": {...}}` dict qaytaradi —
    bu javobni HTTP 200 bilan qaytaring (Payme boshqa statusni "-32400"
    deb tushunadi).
    """
    cfg = config or get_config()
    request_id = body.get("id") if isinstance(body, Mapping) else None

    try:
        if not check_auth(authorization_header, cfg):
            raise err.unauthorized()

        if not isinstance(body, Mapping):
            raise err.json_parse_error()

        method = body.get("method")
        if not method or not isinstance(method, str):
            raise err.required_field_missing("method")

        handler = _METHODS.get(method)
        if handler is None:
            raise PaymeError(-32601, "Method not found", "method")

        params = body.get("params")
        if params is None or not isinstance(params, Mapping):
            params = {}

        result = handler(params)
        return {"result": result, "id": request_id}

    except PaymeError as e:
        return {"error": e.to_dict(), "id": request_id}


# --- Ichki yordamchilar -------------------------------------------------------


def _is_expired(payme_time: int) -> bool:
    import time

    now_ms = int(time.time() * 1000)
    return (now_ms - payme_time) > orders.TRANSACTION_TIMEOUT_MS


def _require_dict(params: Mapping[str, Any], key: str) -> dict:
    value = params.get(key)
    if not isinstance(value, Mapping):
        raise err.required_field_missing(key)
    return dict(value)


def _require_str(params: Mapping[str, Any], key: str) -> str:
    value = params.get(key)
    if not value or not isinstance(value, str):
        raise err.required_field_missing(key)
    return value


def _require_int(params: Mapping[str, Any], key: str) -> int:
    value = params.get(key)
    if value is None or isinstance(value, bool):
        raise err.required_field_missing(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        raise err.required_field_missing(key)


def _safe_call(func: Callable[[Any], None], transaction: Any, name: str) -> None:
    """Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.

    Bu nuqtaga yetganda pul allaqachon yechilgan/qaytarilgan. Xato bo'lsa
    ham Payme'ga muvaffaqiyat javobi ketadi — chunki holat bazada
    o'zgargan, faqat callback (mahsulot berish/bekor qilish) ishlamay
    qolgan. Buni logdan kuzatib, qo'lda hal qilasiz.
    """
    import logging

    try:
        func(transaction)
    except Exception:
        logging.getLogger("payme").exception(
            "Payme %s() xatosi (payme_id=%s) — holat bazada o'zgargan, "
            "qo'lda tekshiring",
            name,
            getattr(transaction, "payme_id", "?"),
        )


def _safe_call_bool(func: Callable[[Any], bool], transaction: Any, default: bool) -> bool:
    import logging

    try:
        return bool(func(transaction))
    except Exception:
        logging.getLogger("payme").exception(
            "Payme can_refund() xatosi — standart qiymat (%s) ishlatiladi", default
        )
        return default
