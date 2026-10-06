"""Uzum Bank webhook'lari uchun testlar.

Ishga tushirish (loyiha ildizidan):

    pip install pytest
    python -m pytest -v
"""

from __future__ import annotations

import base64
import os

import pytest

os.environ.setdefault("UZUM_DB_PATH", ":memory:")

from uzum_payment import handle_check, handle_confirm, handle_create, handle_reverse, handle_status
from uzum_payment.uzum_config import UzumConfig, set_config
from uzum_payment.uzum_orders import demo_create_order, reset_db_for_tests

SERVICE_ID = 101202
LOGIN = "myLogin"
SECRET = "myPassword"

AUTH = "Basic " + base64.b64encode(f"{LOGIN}:{SECRET}".encode()).decode()
BAD_AUTH = "Basic " + base64.b64encode(b"wrong:wrong").decode()


@pytest.fixture(autouse=True)
def setup():
    set_config(UzumConfig(service_id=SERVICE_ID, webhook_login=LOGIN, webhook_secret=SECRET))
    os.environ["UZUM_DB_PATH"] = ":memory:"
    reset_db_for_tests()
    yield
    reset_db_for_tests()


def check_req(account="42", **over):
    data = {"serviceId": SERVICE_ID, "timestamp": 1, "params": {"account": account}}
    data.update(over)
    return data


def create_req(trans_id, account="42", amount=2500000, **over):
    data = {
        "serviceId": SERVICE_ID,
        "timestamp": 1,
        "transId": trans_id,
        "params": {"account": account},
        "amount": amount,
    }
    data.update(over)
    return data


def confirm_req(trans_id, **over):
    data = {
        "serviceId": SERVICE_ID,
        "timestamp": 1,
        "transId": trans_id,
        "paymentSource": "UZCARD",
        "phone": "998901234567",
    }
    data.update(over)
    return data


def reverse_req(trans_id, **over):
    data = {"serviceId": SERVICE_ID, "timestamp": 1, "transId": trans_id}
    data.update(over)
    return data


# --- AUTH ---------------------------------------------------------------


def test_bad_auth_rejected():
    demo_create_order("42", 2500000)
    status, body = handle_check(check_req(), BAD_AUTH)
    assert status == 400
    assert body["errorCode"] == "10001"


def test_missing_auth_rejected():
    demo_create_order("42", 2500000)
    status, body = handle_check(check_req(), None)
    assert status == 400
    assert body["errorCode"] == "10001"


# --- /check ---------------------------------------------------------------


def test_check_success():
    demo_create_order("42", 2500000)
    status, body = handle_check(check_req(), AUTH)
    assert status == 200
    assert body["status"] == "OK"
    assert body["serviceId"] == SERVICE_ID


def test_check_account_not_found():
    status, body = handle_check(check_req(account="999"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10007"


def test_check_wrong_service_id():
    demo_create_order("42", 2500000)
    status, body = handle_check(check_req(serviceId=555), AUTH)
    assert status == 400
    assert body["errorCode"] == "10006"


def test_check_missing_timestamp():
    demo_create_order("42", 2500000)
    data = check_req()
    del data["timestamp"]
    status, body = handle_check(data, AUTH)
    assert status == 400
    assert body["errorCode"] == "10005"


def test_check_already_paid():
    demo_create_order("42", 2500000)
    trans_id = "t1"
    handle_create(create_req(trans_id), AUTH)
    handle_confirm(confirm_req(trans_id), AUTH)

    status, body = handle_check(check_req(), AUTH)
    assert status == 400
    assert body["errorCode"] == "10008"


# --- /create ----------------------------------------------------------------


def test_create_success():
    demo_create_order("42", 2500000)
    status, body = handle_create(create_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "CREATED"
    assert body["transId"] == "t1"
    assert "transTime" in body


def test_create_duplicate_returns_error_not_idempotent():
    """Uzum Bank hujjati: takroriy /create XATO qaytaradi, muvaffaqiyat emas."""
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_create(create_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10010"


def test_create_wrong_amount():
    demo_create_order("42", 2500000)
    status, body = handle_create(create_req("t1", amount=100), AUTH)
    assert status == 400
    assert body["errorCode"] == "10011"


def test_create_account_not_found():
    status, body = handle_create(create_req("t1", account="999"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10007"


def test_create_second_transaction_for_same_order_rejected():
    """Bitta buyurtmaga ikkita PARALLEL faol tranzaksiya ochilmasin."""
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_create(create_req("t2"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10008"


# --- /confirm ---------------------------------------------------------------


def test_confirm_success_calls_on_confirmed(monkeypatch):
    calls = []
    import uzum_payment.uzum_orders as orders_mod

    monkeypatch.setattr(orders_mod, "on_confirmed", lambda tx: calls.append(tx.trans_id))

    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_confirm(confirm_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "CONFIRMED"
    assert calls == ["t1"]


def test_confirm_duplicate_returns_error_not_idempotent():
    """Uzum Bank hujjati: takroriy /confirm XATO qaytaradi."""
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_confirm(confirm_req("t1"), AUTH)

    status, body = handle_confirm(confirm_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10016"


def test_confirm_unknown_transaction():
    status, body = handle_confirm(confirm_req("yoq"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10014"


def test_confirm_missing_payment_source():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    data = confirm_req("t1")
    del data["paymentSource"]
    status, body = handle_confirm(data, AUTH)
    assert status == 400
    assert body["errorCode"] == "10005"


def test_confirm_after_reverse_fails():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_reverse(reverse_req("t1"), AUTH)

    status, body = handle_confirm(confirm_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10015"


def test_confirm_timeout_auto_cancels(monkeypatch):
    """30 daqiqadan keyin /confirm kelsa — avtomatik bekor qilinadi."""
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    import uzum_payment.uzum_methods as methods_mod
    import uzum_payment.uzum_orders as orders_mod

    real_now = methods_mod._now_ms()
    monkeypatch.setattr(
        methods_mod, "_now_ms", lambda: real_now + orders_mod.TRANSACTION_TIMEOUT_MS + 1000
    )

    status, body = handle_confirm(confirm_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10015"

    status, body = handle_status(reverse_req("t1"), AUTH)
    assert body["status"] == "REVERSED"


# --- /reverse -----------------------------------------------------------


def test_reverse_from_created():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_reverse(reverse_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "REVERSED"


def test_reverse_from_confirmed_is_refund(monkeypatch):
    calls = []
    import uzum_payment.uzum_orders as orders_mod

    monkeypatch.setattr(orders_mod, "on_reversed", lambda tx: calls.append(tx.trans_id))

    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_confirm(confirm_req("t1"), AUTH)

    status, body = handle_reverse(reverse_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "REVERSED"
    assert calls == ["t1"]


def test_reverse_duplicate_returns_error():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_reverse(reverse_req("t1"), AUTH)

    status, body = handle_reverse(reverse_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10018"


def test_reverse_unknown_transaction():
    status, body = handle_reverse(reverse_req("yoq"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10014"


def test_reverse_respects_can_reverse_hook(monkeypatch):
    import uzum_payment.uzum_orders as orders_mod

    monkeypatch.setattr(orders_mod, "can_reverse", lambda tx: False)

    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_confirm(confirm_req("t1"), AUTH)

    status, body = handle_reverse(reverse_req("t1"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10017"


# --- /status ------------------------------------------------------------


def test_status_created():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_status(reverse_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "CREATED"
    assert "confirmTime" not in body
    assert "reverseTime" not in body


def test_status_confirmed():
    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)
    handle_confirm(confirm_req("t1"), AUTH)

    status, body = handle_status(reverse_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "CONFIRMED"
    assert "confirmTime" in body


def test_status_unknown_transaction():
    status, body = handle_status(reverse_req("yoq"), AUTH)
    assert status == 400
    assert body["errorCode"] == "10014"


# --- Callback xatosi ----------------------------------------------------


def test_on_confirmed_error_does_not_break_response(monkeypatch):
    """on_confirmed xato bersa ham Uzum'ga CONFIRMED ketadi (pul allaqachon yechilgan)."""
    import uzum_payment.uzum_orders as orders_mod

    def broken(tx):
        raise RuntimeError("baza yiqildi")

    monkeypatch.setattr(orders_mod, "on_confirmed", broken)

    demo_create_order("42", 2500000)
    handle_create(create_req("t1"), AUTH)

    status, body = handle_confirm(confirm_req("t1"), AUTH)
    assert status == 200
    assert body["status"] == "CONFIRMED"
