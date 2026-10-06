"""Payme metodlarining testlari.

Ishga tushirish (loyiha ildizidan):

    pip install pytest
    python -m pytest -v
"""

from __future__ import annotations

import base64
import os
import time

import pytest

os.environ.setdefault("PAYME_DB_PATH", ":memory:")

from payme_payment import payme_orders as orders  # noqa: E402
from payme_payment.payme_checkout import checkout_url, som_to_tiyin  # noqa: E402
from payme_payment.payme_config import PaymeConfig, set_config  # noqa: E402
from payme_payment.payme_methods import handle_request  # noqa: E402

MERCHANT_ID = "5cd108976ce4a8423da6d5c9"
SECRET_KEY = "test_secret_key"
LOGIN = "Paycom"


def auth_header(login: str = LOGIN, key: str = SECRET_KEY) -> str:
    token = base64.b64encode(f"{login}:{key}".encode()).decode()
    return f"Basic {token}"


@pytest.fixture(autouse=True)
def setup():
    set_config(
        PaymeConfig(
            merchant_id=MERCHANT_ID,
            secret_key=SECRET_KEY,
            merchant_login=LOGIN,
        )
    )
    os.environ["PAYME_DB_PATH"] = ":memory:"
    orders.reset_db_for_tests()
    yield
    orders.reset_db_for_tests()


@pytest.fixture
def paid(monkeypatch) -> list:
    calls: list[str] = []
    monkeypatch.setattr(orders, "on_paid", lambda tx: calls.append(tx.payme_id))
    return calls


@pytest.fixture
def cancelled(monkeypatch) -> list:
    calls: list[str] = []
    monkeypatch.setattr(orders, "on_cancelled", lambda tx: calls.append(tx.payme_id))
    return calls


def rpc(method: str, params: dict, req_id: int = 1, auth: str | None = None) -> dict:
    body = {"method": method, "params": params, "id": req_id}
    return handle_request(body, auth or auth_header())


def now_ms() -> int:
    return int(time.time() * 1000)


# --- Auth ---------------------------------------------------------------------


def test_auth_missing_header_rejected():
    res = handle_request({"method": "CheckTransaction", "params": {}, "id": 1}, None)
    assert res["error"]["code"] == -32504


def test_auth_wrong_password_rejected():
    res = rpc("CheckTransaction", {"id": "x"}, auth=auth_header(key="wrong"))
    assert res["error"]["code"] == -32504


def test_auth_wrong_login_rejected():
    res = rpc("CheckTransaction", {"id": "x"}, auth=auth_header(login="Hacker"))
    assert res["error"]["code"] == -32504


def test_unknown_method():
    res = rpc("SomeOtherMethod", {})
    assert res["error"]["code"] == -32601


# --- CheckPerformTransaction ---------------------------------------------------


def test_check_perform_success():
    orders.demo_create_order("ORD1", 500000)

    res = rpc("CheckPerformTransaction", {"amount": 500000, "account": {"order_id": "ORD1"}})

    assert res["result"]["allow"] is True


def test_check_perform_order_not_found():
    res = rpc("CheckPerformTransaction", {"amount": 500000, "account": {"order_id": "YOQ"}})

    assert res["error"]["code"] == -31050


def test_check_perform_wrong_amount():
    orders.demo_create_order("ORD1", 500000)

    res = rpc("CheckPerformTransaction", {"amount": 100, "account": {"order_id": "ORD1"}})

    assert res["error"]["code"] == -31001


def test_check_perform_already_has_transaction():
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {"id": "tx1", "time": now_ms(), "amount": 500000,
                               "account": {"order_id": "ORD1"}})

    res = rpc("CheckPerformTransaction", {"amount": 500000, "account": {"order_id": "ORD1"}})

    assert res["error"]["code"] == -31099


# --- CreateTransaction ----------------------------------------------------------


def test_create_transaction_success():
    orders.demo_create_order("ORD1", 500000)

    res = rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    assert res["result"]["state"] == orders.STATE_PENDING
    assert res["result"]["transaction"] == "tx1"
    assert isinstance(res["result"]["create_time"], int)


def test_create_transaction_idempotent_replay():
    orders.demo_create_order("ORD1", 500000)
    params = {"id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"}}

    first = rpc("CreateTransaction", params)
    second = rpc("CreateTransaction", params)

    assert first["result"]["create_time"] == second["result"]["create_time"]
    assert second["result"]["state"] == orders.STATE_PENDING


def test_create_transaction_order_not_found():
    res = rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "YOQ"},
    })
    assert res["error"]["code"] == -31050


def test_create_transaction_wrong_amount():
    orders.demo_create_order("ORD1", 500000)

    res = rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 1, "account": {"order_id": "ORD1"},
    })
    assert res["error"]["code"] == -31001


def test_create_transaction_timeout_auto_cancels():
    orders.demo_create_order("ORD1", 500000)
    old_time = now_ms() - orders.TRANSACTION_TIMEOUT_MS - 1000

    rpc("CreateTransaction", {
        "id": "tx1", "time": old_time, "amount": 500000, "account": {"order_id": "ORD1"},
    })

    # Muddati o'tgan holda qayta chaqirilsa -31008 va bekor qilinadi.
    res = rpc("CreateTransaction", {
        "id": "tx1", "time": old_time, "amount": 500000, "account": {"order_id": "ORD1"},
    })

    assert res["error"]["code"] == -31008
    tx = orders.get_transaction("tx1")
    assert tx.state == orders.STATE_CANCELLED
    assert tx.reason == orders.REASON_TIMEOUT


def test_create_transaction_duplicate_for_same_order():
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    res = rpc("CreateTransaction", {
        "id": "tx2", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    assert res["error"]["code"] == -31099


# --- PerformTransaction -----------------------------------------------------


def test_perform_transaction_success(paid):
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    res = rpc("PerformTransaction", {"id": "tx1"})

    assert res["result"]["state"] == orders.STATE_PAID
    assert res["result"]["transaction"] == "tx1"
    assert paid == ["tx1"]


def test_perform_transaction_idempotent(paid):
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    first = rpc("PerformTransaction", {"id": "tx1"})
    second = rpc("PerformTransaction", {"id": "tx1"})

    assert first["result"]["perform_time"] == second["result"]["perform_time"]
    assert paid == ["tx1"]  # on_paid FAQAT bir marta


def test_perform_transaction_not_found():
    res = rpc("PerformTransaction", {"id": "yoq"})
    assert res["error"]["code"] == -31003


def test_perform_transaction_after_cancel():
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })
    rpc("CancelTransaction", {"id": "tx1", "reason": 3})

    res = rpc("PerformTransaction", {"id": "tx1"})
    assert res["error"]["code"] == -31008


def test_perform_transaction_expired():
    orders.demo_create_order("ORD1", 500000)
    old_time = now_ms() - orders.TRANSACTION_TIMEOUT_MS - 1000
    rpc("CreateTransaction", {
        "id": "tx1", "time": old_time, "amount": 500000, "account": {"order_id": "ORD1"},
    })

    res = rpc("PerformTransaction", {"id": "tx1"})

    assert res["error"]["code"] == -31008
    assert orders.get_transaction("tx1").state == orders.STATE_CANCELLED


# --- CancelTransaction -----------------------------------------------------


def test_cancel_pending_transaction(cancelled):
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    res = rpc("CancelTransaction", {"id": "tx1", "reason": 3})

    assert res["result"]["state"] == orders.STATE_CANCELLED
    assert cancelled == ["tx1"]


def test_cancel_paid_transaction_is_refund(paid, cancelled):
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })
    rpc("PerformTransaction", {"id": "tx1"})

    res = rpc("CancelTransaction", {"id": "tx1", "reason": 5})

    assert res["result"]["state"] == orders.STATE_CANCELLED_AFTER_PAID
    assert paid == ["tx1"]
    assert cancelled == ["tx1"]


def test_cancel_is_idempotent(cancelled):
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    first = rpc("CancelTransaction", {"id": "tx1", "reason": 3})
    second = rpc("CancelTransaction", {"id": "tx1", "reason": 1})  # boshqa sabab

    assert first["result"]["cancel_time"] == second["result"]["cancel_time"]
    assert cancelled == ["tx1"]  # on_cancelled FAQAT bir marta


def test_cancel_not_found():
    res = rpc("CancelTransaction", {"id": "yoq", "reason": 1})
    assert res["error"]["code"] == -31003


def test_cancel_paid_refused_by_can_refund(monkeypatch):
    monkeypatch.setattr(orders, "can_refund", lambda tx: False)
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })
    rpc("PerformTransaction", {"id": "tx1"})

    res = rpc("CancelTransaction", {"id": "tx1", "reason": 5})

    assert res["error"]["code"] == -31007
    assert orders.get_transaction("tx1").state == orders.STATE_PAID


# --- CheckTransaction -------------------------------------------------------


def test_check_transaction():
    orders.demo_create_order("ORD1", 500000)
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })

    res = rpc("CheckTransaction", {"id": "tx1"})

    assert res["result"]["state"] == orders.STATE_PENDING
    assert res["result"]["perform_time"] == 0
    assert res["result"]["cancel_time"] == 0
    assert res["result"]["reason"] is None


def test_check_transaction_not_found():
    res = rpc("CheckTransaction", {"id": "yoq"})
    assert res["error"]["code"] == -31003


# --- GetStatement ------------------------------------------------------------


def test_get_statement_range():
    orders.demo_create_order("ORD1", 500000)
    orders.demo_create_order("ORD2", 100000)

    t0 = now_ms()
    rpc("CreateTransaction", {
        "id": "tx1", "time": now_ms(), "amount": 500000, "account": {"order_id": "ORD1"},
    })
    rpc("CreateTransaction", {
        "id": "tx2", "time": now_ms(), "amount": 100000, "account": {"order_id": "ORD2"},
    })
    t1 = now_ms() + 1000

    res = rpc("GetStatement", {"from": t0 - 1000, "to": t1})

    ids = {tx["id"] for tx in res["result"]["transactions"]}
    assert ids == {"tx1", "tx2"}


def test_get_statement_empty_range():
    res = rpc("GetStatement", {"from": 0, "to": 1})
    assert res["result"]["transactions"] == []


# --- Checkout havolasi -------------------------------------------------------


def test_checkout_url_format():
    url = checkout_url({"order_id": 42}, som_to_tiyin(5000))

    assert url.startswith("https://checkout.paycom.uz/")
    encoded = url.split("/")[-1]
    decoded = base64.b64decode(encoded).decode()
    assert decoded == f"m={MERCHANT_ID};ac.order_id=42;a=500000"


def test_checkout_url_no_secret_leak():
    url = checkout_url({"order_id": 42}, som_to_tiyin(5000))
    assert SECRET_KEY not in url


def test_som_to_tiyin():
    assert som_to_tiyin(5000) == 500000
    assert som_to_tiyin("123.45") == 12345
