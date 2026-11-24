"""Rate limit (A-03: PostgreSQL bazasiga asoslangan rate-limit) testlari."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch
import pytest

from app import security
from app.config import settings
from app.errors import ApiError
from conftest import make_request


def test_no_global_mutable_state_in_security():
    """Konstitutsiya Ustun 4: Modulda global mutable holat bo'lmasligi shart."""
    assert not hasattr(security, "_login_attempts"), "Global _login_attempts xotirada qolmasligi kerak"
    assert not hasattr(security, "_req_hits"), "Global _req_hits xotirada qolmasligi kerak"
    assert not hasattr(security, "_last_sweep"), "Global _last_sweep xotirada qolmasligi kerak"


def test_check_login_rate_limit_under_limit(user_request):
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with patch.object(security.db, "fetch_value", return_value=3):
        with patch.object(security.db, "execute", side_effect=fake_execute):
            security.check_login_rate_limit(user_request)

    assert len(executed) == 1
    sql, params = executed[0]
    assert "INSERT INTO rate_limit_hits" in sql
    assert params["ip"] == "203.0.113.9"


def test_check_login_rate_limit_exceeded(user_request, caplog):
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with caplog.at_level(logging.WARNING, logger="yordamchi.security"):
        with patch.object(security.db, "fetch_value", return_value=settings.LOGIN_MAX_ATTEMPTS):
            with patch.object(security.db, "execute", side_effect=fake_execute):
                with pytest.raises(ApiError) as exc:
                    security.check_login_rate_limit(user_request)

    assert exc.value.status == 429
    assert "Juda ko'p urinish" in exc.value.message
    # Cheklov oshganda jadvalni to'ldirib tashlamaslik uchun INSERT chaqirilmasligi shart
    assert len(executed) == 0
    # Xavfsizlik jurnaliga yozilgan bo'lishi shart
    assert any("LOGIN_RATE_LIMIT" in r.message for r in caplog.records)


def test_clear_login_rate_limit(user_request):
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with patch.object(security.db, "execute", side_effect=fake_execute):
        security.clear_login_rate_limit(user_request)

    assert len(executed) == 1
    sql, params = executed[0]
    assert "DELETE FROM rate_limit_hits WHERE bucket = 'login'" in sql
    assert params["ip"] == "203.0.113.9"


def test_check_request_rate_disabled_when_zero(user_request):
    with patch.object(settings, "RATE_LIMIT_REQUESTS", 0):
        with patch.object(security.db, "fetch_value") as mock_fetch:
            with patch.object(security.db, "execute") as mock_exec:
                security.check_request_rate(user_request)
    mock_fetch.assert_not_called()
    mock_exec.assert_not_called()


def test_check_request_rate_under_limit(user_request):
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with patch.object(settings, "RATE_LIMIT_REQUESTS", 100):
        with patch.object(security.db, "fetch_value", return_value=50):
            with patch.object(security.db, "execute", side_effect=fake_execute):
                security.check_request_rate(user_request)

    assert len(executed) == 1
    sql, params = executed[0]
    assert "INSERT INTO rate_limit_hits (bucket, client_ip) VALUES ('req', :ip)" in sql
    assert params["ip"] == "203.0.113.9"


def test_check_request_rate_exceeded(user_request, caplog):
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with caplog.at_level(logging.WARNING, logger="yordamchi.security"):
        with patch.object(settings, "RATE_LIMIT_REQUESTS", 100):
            with patch.object(security.db, "fetch_value", return_value=100):
                with patch.object(security.db, "execute", side_effect=fake_execute):
                    with pytest.raises(ApiError) as exc:
                        security.check_request_rate(user_request)

    assert exc.value.status == 429
    assert len(executed) == 0
    assert any("REQUEST_RATE_LIMIT" in r.message for r in caplog.records)
