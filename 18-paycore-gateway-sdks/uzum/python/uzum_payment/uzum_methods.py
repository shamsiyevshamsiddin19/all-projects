"""Uzum Bank Merchant API'ning 5 webhook'i.

Bu modul HECH QANDAY web-framework'ga bog'liq emas: kiruvchi so'rov
ma'lumotini oddiy dict sifatida oladi, javobni `(http_status, dict)` juft
qilib qaytaradi. FastAPI, Flask, Django — qaysi birida ishlatsangiz ham shu
kod o'zgarmaydi.

Click/Payme'dan FARQI: Uzum Bank BESHTA ALOHIDA manzilga so'rov yuboradi
(bitta JSON-RPC endpoint emas) va xato holatida HTTP 400 kutadi (200 emas):

    POST /check    — "bu to'lovni qabul qila olasanmi?" (pul yo'q hali)
    POST /create   — Uzum Bank tranzaksiya ochadi
    POST /confirm  — PUL ALLAQACHON YECHILGAN, mahsulotni ber
    POST /reverse  — to'lovni yoki tasdiqlangan to'lovni bekor qil
    POST /status   — tranzaksiya holatini so'raydi (confirm javob bermasa,
                      Uzum Bank shu bilan 10 martagacha so'raydi)

Bu faylga tegishingiz shart emas — bazangizga ulanish uzum_orders.py da.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Mapping

from . import uzum_errors as err
from . import uzum_orders as orders
from .uzum_auth import check_auth
from .uzum_config import UzumConfig, get_config
from .uzum_errors import UzumError

logger = logging.getLogger("uzum")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _is_expired(create_time: int) -> bool:
    return (_now_ms() - create_time) > orders.TRANSACTION_TIMEOUT_MS


def _require(data: Mapping[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "":
        raise err.required_field_missing()
    return value


def _require_service_id(data: Mapping[str, Any], cfg: UzumConfig) -> None:
    """serviceId borligini va to'g'riligini tekshiradi."""
    raw = _require(data, "serviceId")
    try:
        service_id = int(raw)
    except (TypeError, ValueError):
        raise err.invalid_service_id()
    if service_id != cfg.service_id:
        raise err.invalid_service_id()


# =============================================================================
#  1. /check — "bu to'lovni qabul qila olasanmi?"
# =============================================================================


def handle_check(
    data: Mapping[str, Any],
    authorization_header: str | None,
    config: UzumConfig | None = None,
) -> tuple[int, dict]:
    cfg = config or get_config()

    def run() -> dict:
        if not check_auth(authorization_header, cfg):
            raise err.access_denied()

        _require_service_id(data, cfg)
        _require(data, "timestamp")
        params = _require(data, "params")
        if not isinstance(params, Mapping):
            raise err.required_field_missing()

        account = orders.find_account(dict(params))
        if account is None:
            raise err.account_not_found()

        if not account.payable:
            raise err.already_paid()

        return {
            "serviceId": cfg.service_id,
            "timestamp": _now_ms(),
            "status": "OK",
        }

    return _wrap(run)


# =============================================================================
#  2. /create — Uzum Bank tranzaksiya ochadi
# =============================================================================


def handle_create(
    data: Mapping[str, Any],
    authorization_header: str | None,
    config: UzumConfig | None = None,
) -> tuple[int, dict]:
    cfg = config or get_config()

    def run() -> dict:
        if not check_auth(authorization_header, cfg):
            raise err.access_denied()

        _require_service_id(data, cfg)
        _require(data, "timestamp")
        trans_id = _require(data, "transId")
        params = _require(data, "params")
        amount = _require(data, "amount")
        if not isinstance(params, Mapping):
            raise err.required_field_missing()

        # DIQQAT: takroriy /create — Uzum Bank hujjati bo'yicha bu XATO,
        # Payme'dagidek "idempotent — bir xil natijani qaytar" emas.
        existing = orders.get_transaction(str(trans_id))
        if existing is not None:
            raise err.transaction_already_created()

        account = orders.find_account(dict(params))
        if account is None:
            raise err.account_not_found()
        if not account.payable:
            raise err.already_paid()

        amount = int(amount)
        if amount != account.amount:
            raise err.invalid_amount()

        # DIQQAT: bu tekshiruv Uzum Bank hujjatida so'zma-so'z yozilmagan —
        # mudofaa uchun qo'shilgan (bitta buyurtmaga ikkita PARALLEL faol
        # tranzaksiya ochilmasin). Eng yaqin mos xato kodi 10008 (already
        # paid) ishlatilgan, chunki jadvalda aynan shu holat uchun alohida
        # kod yo'q.
        active = orders.get_active_transaction_for_account(dict(params))
        if active is not None:
            raise err.already_paid()

        created = orders.create_transaction(str(trans_id), amount, dict(params))

        return {
            "serviceId": cfg.service_id,
            "transId": created.trans_id,
            "status": orders.STATE_CREATED,
            "transTime": created.create_time,
        }

    return _wrap(run, trans_time_on_error=True)


# =============================================================================
#  3. /confirm — PUL ALLAQACHON YECHILGAN, mahsulotni ber
# =============================================================================


def handle_confirm(
    data: Mapping[str, Any],
    authorization_header: str | None,
    config: UzumConfig | None = None,
) -> tuple[int, dict]:
    cfg = config or get_config()

    def run() -> dict:
        if not check_auth(authorization_header, cfg):
            raise err.access_denied()

        _require_service_id(data, cfg)
        _require(data, "timestamp")
        trans_id = str(_require(data, "transId"))
        # Uzum Bank talab qiladigan qo'shimcha maydonlar — biznes
        # mantig'imizda ishlatilmasa ham, so'rov to'liqligini tekshiramiz.
        _require(data, "paymentSource")
        _require(data, "phone")

        tx = orders.get_transaction(trans_id)
        if tx is None:
            raise err.transaction_not_found()

        if tx.state == orders.STATE_REVERSED:
            raise err.transaction_cancelled()

        if tx.state == orders.STATE_CONFIRMED:
            # Uzum Bank hujjati bo'yicha takroriy /confirm — XATO.
            raise err.transaction_already_confirmed()

        # state == CREATED
        if _is_expired(tx.create_time):
            orders.mark_reversed(trans_id)
            raise err.transaction_cancelled()

        updated = orders.mark_confirmed(trans_id)
        if updated is None:
            # Parallel so'rov bizdan oldin ulgurdi.
            again = orders.get_transaction(trans_id)
            if again is not None and again.state == orders.STATE_CONFIRMED:
                raise err.transaction_already_confirmed()
            raise err.internal_error()

        account = orders.find_account(updated.params)
        updated.account_extra = account.extra if account else {}
        _safe_call(orders.on_confirmed, updated, "on_confirmed")

        return {
            "serviceId": cfg.service_id,
            "transId": updated.trans_id,
            "status": orders.STATE_CONFIRMED,
            "confirmTime": updated.confirm_time,
        }

    return _wrap(run, confirm_time_on_error=True)


# =============================================================================
#  4. /reverse — to'lovni (yoki tasdiqlangan to'lovni) bekor qiladi
# =============================================================================


def handle_reverse(
    data: Mapping[str, Any],
    authorization_header: str | None,
    config: UzumConfig | None = None,
) -> tuple[int, dict]:
    cfg = config or get_config()

    def run() -> dict:
        if not check_auth(authorization_header, cfg):
            raise err.access_denied()

        _require_service_id(data, cfg)
        _require(data, "timestamp")
        trans_id = str(_require(data, "transId"))

        tx = orders.get_transaction(trans_id)
        if tx is None:
            raise err.transaction_not_found()

        if tx.state == orders.STATE_REVERSED:
            # Uzum Bank hujjati bo'yicha takroriy /reverse — XATO.
            raise err.transaction_already_cancelled()

        if tx.state == orders.STATE_CONFIRMED:
            account = orders.find_account(tx.params)
            tx.account_extra = account.extra if account else {}
            if not _safe_call_bool(orders.can_reverse, tx, default=True):
                raise err.unable_to_cancel()

        updated = orders.mark_reversed(trans_id)
        if updated is None:
            raise err.transaction_already_cancelled()

        account = orders.find_account(updated.params)
        updated.account_extra = account.extra if account else {}
        _safe_call(orders.on_reversed, updated, "on_reversed")

        return {
            "serviceId": cfg.service_id,
            "transId": updated.trans_id,
            "status": orders.STATE_REVERSED,
            "reverseTime": updated.reverse_time,
        }

    return _wrap(run, reverse_time_on_error=True)


# =============================================================================
#  5. /status — tranzaksiya holatini so'raydi
# =============================================================================


def handle_status(
    data: Mapping[str, Any],
    authorization_header: str | None,
    config: UzumConfig | None = None,
) -> tuple[int, dict]:
    cfg = config or get_config()

    def run() -> dict:
        if not check_auth(authorization_header, cfg):
            raise err.access_denied()

        _require_service_id(data, cfg)
        _require(data, "timestamp")
        trans_id = str(_require(data, "transId"))

        tx = orders.get_transaction(trans_id)
        if tx is None:
            raise err.transaction_not_found()

        # Uzum Bank /confirm javobsiz qolganda aynan shu /status orqali
        # holatni bilib oladi — shuning uchun bu yerda ham 30-daqiqalik
        # muddatni tekshiramiz.
        if tx.state == orders.STATE_CREATED and _is_expired(tx.create_time):
            expired = orders.mark_reversed(trans_id)
            if expired is not None:
                tx = expired

        result: dict[str, Any] = {
            "serviceId": cfg.service_id,
            "transId": tx.trans_id,
            "status": tx.state,
            "transTime": tx.create_time,
        }
        if tx.confirm_time:
            result["confirmTime"] = tx.confirm_time
        if tx.reverse_time:
            result["reverseTime"] = tx.reverse_time

        return result

    return _wrap(run)


# =============================================================================
#  Ichki yordamchilar
# =============================================================================


def _wrap(
    fn: Callable[[], dict],
    *,
    trans_time_on_error: bool = False,
    confirm_time_on_error: bool = False,
    reverse_time_on_error: bool = False,
) -> tuple[int, dict]:
    """Handler'ni chaqiradi va (http_status, body) juftini qaytaradi.

    Muvaffaqiyat -> (200, natija). Xato -> (400, {"errorCode": "..."} +
    tegishli vaqt maydoni, chunki Uzum Bank ba'zi xato javoblarida ham
    transTime/confirmTime/reverseTime maydonini kutadi).
    """
    try:
        return 200, fn()
    except UzumError as e:
        body: dict[str, Any] = dict(e.to_dict())
        now = _now_ms()
        if trans_time_on_error:
            body["transTime"] = now
        if confirm_time_on_error:
            body["confirmTime"] = now
        if reverse_time_on_error:
            body["reverseTime"] = now
        return 400, body
    except Exception:
        logger.exception("Uzum Bank webhook'ida kutilmagan xato")
        return 400, err.internal_error().to_dict()


def _safe_call(func: Callable[[Any], None], transaction: Any, name: str) -> None:
    """Hodisa funksiyasini chaqiradi; xato bo'lsa loglaydi, javobni buzmaydi.

    Bu nuqtaga yetganda pul allaqachon yechilgan. Xato bo'lsa ham Uzum
    Bank'ga muvaffaqiyat javobi ketadi — holat bazada o'zgargan, faqat
    mahsulot berish callback'i ishlamay qolgan. Logdan kuzatib, qo'lda hal
    qilasiz.
    """
    try:
        func(transaction)
    except Exception:
        logger.exception(
            "Uzum %s() xatosi (trans_id=%s) — holat bazada o'zgargan, "
            "qo'lda tekshiring",
            name,
            getattr(transaction, "trans_id", "?"),
        )


def _safe_call_bool(func: Callable[[Any], bool], transaction: Any, default: bool) -> bool:
    try:
        return bool(func(transaction))
    except Exception:
        logger.exception("Uzum can_reverse() xatosi — standart qiymat (%s) ishlatiladi", default)
        return default
