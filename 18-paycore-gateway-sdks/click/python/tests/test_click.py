"""click_prepare va click_complete testlari.

Ishga tushirish (loyiha ildizidan):

    pip install pytest
    python -m pytest -v
"""

from __future__ import annotations

import hashlib
import os
from decimal import Decimal

import pytest

os.environ.setdefault("CLICK_DB_PATH", ":memory:")

from click_payment import click_orders  # noqa: E402
from click_payment import click_errors as err  # noqa: E402
from click_payment.click_complete import handle_complete  # noqa: E402
from click_payment.click_config import ClickConfig, payment_url, set_config  # noqa: E402
from click_payment.click_prepare import handle_prepare  # noqa: E402

SERVICE_ID = "12345"
SECRET_KEY = "test_secret_key"
SIGN_TIME = "2026-07-17 12:00:00"
CLICK_TRANS_ID = "987654321"


@pytest.fixture(autouse=True)
def setup():
    """Har bir test uchun toza baza va sozlama."""
    set_config(
        ClickConfig(
            service_id=SERVICE_ID,
            merchant_id="54321",
            secret_key=SECRET_KEY,
            merchant_user_id="67890",
        )
    )
    os.environ["CLICK_DB_PATH"] = ":memory:"
    click_orders.reset_db_for_tests()
    yield
    click_orders.reset_db_for_tests()


@pytest.fixture
def paid(monkeypatch) -> list:
    """on_paid chaqiruvlarini yozib boradi."""
    calls: list[str] = []
    monkeypatch.setattr(
        click_orders, "on_paid", lambda order: calls.append(order.merchant_trans_id)
    )
    return calls


@pytest.fixture
def cancelled(monkeypatch) -> list:
    calls: list[str] = []
    monkeypatch.setattr(
        click_orders, "on_cancelled", lambda order: calls.append(order.merchant_trans_id)
    )
    return calls


def sign(*parts: str) -> str:
    """Imzoni "qo'lda" hisoblaymiz — kutubxona kodidan mustaqil tekshirish uchun."""
    return hashlib.md5("".join(parts).encode()).hexdigest()


def prepare_req(merchant_trans_id: str, amount: str, **over) -> dict:
    data = {
        "click_trans_id": CLICK_TRANS_ID,
        "service_id": SERVICE_ID,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": "0",
        "sign_time": SIGN_TIME,
        "sign_string": sign(
            CLICK_TRANS_ID, SERVICE_ID, SECRET_KEY, merchant_trans_id, amount, "0", SIGN_TIME
        ),
    }
    data.update(over)
    return data


def complete_req(merchant_trans_id: str, amount: str, prepare_id: int, **over) -> dict:
    data = {
        "click_trans_id": CLICK_TRANS_ID,
        "service_id": SERVICE_ID,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": str(prepare_id),
        "amount": amount,
        "action": "1",
        "error": "0",
        "sign_time": SIGN_TIME,
        "sign_string": sign(
            CLICK_TRANS_ID,
            SERVICE_ID,
            SECRET_KEY,
            merchant_trans_id,
            str(prepare_id),
            amount,
            "1",
            SIGN_TIME,
        ),
    }
    data.update(over)
    return data


# --- PREPARE ----------------------------------------------------------------


def test_prepare_success():
    order = click_orders.create_order("ORD1", 5000)

    res = handle_prepare(prepare_req("ORD1", "5000"))

    assert res["error"] == err.SUCCESS
    assert res["merchant_prepare_id"] == order.id
    assert res["merchant_trans_id"] == "ORD1"


def test_prepare_amount_with_decimals():
    """Click "5000.00" yuborsa ham imzo va summa mos kelishi kerak."""
    click_orders.create_order("ORD1", 5000)

    res = handle_prepare(prepare_req("ORD1", "5000.00"))

    assert res["error"] == err.SUCCESS


def test_prepare_bad_sign():
    click_orders.create_order("ORD1", 5000)

    res = handle_prepare(prepare_req("ORD1", "5000", sign_string="a" * 32))

    assert res["error"] == err.SIGN_CHECK_FAILED


def test_prepare_wrong_service_id():
    """Boshqa xizmatning so'rovi qabul qilinmaydi."""
    click_orders.create_order("ORD1", 5000)
    data = prepare_req("ORD1", "5000")
    data["service_id"] = "99999"

    res = handle_prepare(data)

    assert res["error"] == err.SIGN_CHECK_FAILED


def test_prepare_missing_field():
    click_orders.create_order("ORD1", 5000)
    data = prepare_req("ORD1", "5000")
    del data["sign_time"]

    res = handle_prepare(data)

    assert res["error"] == err.BAD_REQUEST


def test_prepare_wrong_amount():
    """Imzo to'g'ri, lekin summa bazadagidan farq qiladi."""
    click_orders.create_order("ORD1", 5000)

    res = handle_prepare(prepare_req("ORD1", "100"))

    assert res["error"] == err.INCORRECT_AMOUNT


def test_prepare_unknown_order():
    res = handle_prepare(prepare_req("YOQ404", "5000"))

    assert res["error"] == err.USER_NOT_FOUND


def test_prepare_already_paid():
    order = click_orders.create_order("ORD1", 5000)
    click_orders.mark_paid(order, CLICK_TRANS_ID)

    res = handle_prepare(prepare_req("ORD1", "5000"))

    assert res["error"] == err.ALREADY_PAID


def test_prepare_cancelled():
    order = click_orders.create_order("ORD1", 5000)
    click_orders.mark_cancelled(order, CLICK_TRANS_ID)

    res = handle_prepare(prepare_req("ORD1", "5000"))

    assert res["error"] == err.TRANSACTION_CANCELLED


# --- COMPLETE ---------------------------------------------------------------


def test_complete_success(paid):
    order = click_orders.create_order("ORD1", 5000, user_id=7, product="Kitob")
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "5000", order.id))

    assert res["error"] == err.SUCCESS
    assert res["merchant_confirm_id"] == order.id
    assert click_orders.find_order("ORD1").status == click_orders.STATUS_PAID
    assert paid == ["ORD1"]


def test_complete_is_idempotent(paid):
    """Click callback'ni takror yuborsa — OK, lekin mahsulot ikki marta berilmaydi."""
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    first = handle_complete(complete_req("ORD1", "5000", order.id))
    second = handle_complete(complete_req("ORD1", "5000", order.id))

    assert first["error"] == err.SUCCESS
    assert second["error"] == err.SUCCESS
    assert paid == ["ORD1"]  # on_paid FAQAT bir marta


def test_complete_bad_sign(paid):
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "5000", order.id, sign_string="b" * 32))

    assert res["error"] == err.SIGN_CHECK_FAILED
    assert click_orders.find_order("ORD1").status == click_orders.STATUS_PENDING
    assert paid == []


def test_prepare_sign_not_valid_for_complete():
    """prepare uchun olingan imzo complete'da ishlamasligi kerak.

    Sabab: complete imzosiga merchant_prepare_id qo'shiladi va action=1 bo'ladi.
    """
    order = click_orders.create_order("ORD1", 5000)
    p = prepare_req("ORD1", "5000")

    res = handle_complete(
        complete_req("ORD1", "5000", order.id, sign_string=p["sign_string"])
    )

    assert res["error"] == err.SIGN_CHECK_FAILED


def test_complete_wrong_prepare_id():
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "5000", order.id + 777))

    assert res["error"] == err.TRANSACTION_NOT_FOUND


def test_complete_wrong_amount():
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "1", order.id))

    assert res["error"] == err.INCORRECT_AMOUNT
    assert click_orders.find_order("ORD1").status == click_orders.STATUS_PENDING


def test_complete_click_error_cancels(paid, cancelled):
    """Click manfiy `error` yuborsa — to'lov bekor qilinadi."""
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "5000", order.id, error="-5017"))

    assert res["error"] == err.TRANSACTION_CANCELLED
    assert click_orders.find_order("ORD1").status == click_orders.STATUS_CANCELLED
    assert paid == []
    assert cancelled == ["ORD1"]


def test_complete_unknown_order():
    res = handle_complete(complete_req("YOQ404", "5000", 1))

    assert res["error"] == err.USER_NOT_FOUND


def test_on_paid_error_does_not_break_response(monkeypatch):
    """on_paid xato bersa ham Click'ga SUCCESS ketadi va to'lov 'paid' qoladi."""

    def broken(order):
        raise RuntimeError("baza yiqildi")

    monkeypatch.setattr(click_orders, "on_paid", broken)
    order = click_orders.create_order("ORD1", 5000)
    handle_prepare(prepare_req("ORD1", "5000"))

    res = handle_complete(complete_req("ORD1", "5000", order.id))

    assert res["error"] == err.SUCCESS
    assert click_orders.find_order("ORD1").status == click_orders.STATUS_PAID


def test_mark_paid_only_wins_once():
    """mark_paid ikkinchi marta False qaytarishi SHART (on_paid shunga tayanadi)."""
    order = click_orders.create_order("ORD1", 5000)

    assert click_orders.mark_paid(order, CLICK_TRANS_ID) is True
    assert click_orders.mark_paid(order, CLICK_TRANS_ID) is False


# --- To'lov havolasi --------------------------------------------------------


def test_payment_url():
    url = payment_url("ORD1", 5000, return_url="https://a.uz/ok")

    assert url.startswith("https://my.click.uz/services/pay?")
    assert "service_id=12345" in url
    assert "merchant_id=54321" in url
    assert "amount=5000" in url
    assert "transaction_param=ORD1" in url
    assert "merchant_user_id=67890" in url
    assert "return_url=https%3A%2F%2Fa.uz%2Fok" in url
    assert SECRET_KEY not in url  # secret_key hech qachon havolaga tushmasin


def test_amount_stored_as_decimal():
    """Pul float emas, Decimal bo'lib saqlanadi."""
    click_orders.create_order("ORD1", "5000.55")

    assert click_orders.find_order("ORD1").amount == Decimal("5000.55")
