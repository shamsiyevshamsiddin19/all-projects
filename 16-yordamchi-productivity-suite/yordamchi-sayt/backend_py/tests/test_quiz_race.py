"""Quiz progress (A-09: set_flag poyga holati) testlari."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.handlers import quiz
from conftest import make_request


def test_set_flag_none_uses_atomic_tx_without_select_race(user_request):
    """A-09 poyga holati testi.

    Eski mantiq: SELECT id, is_solved qilib, keyin Python'da tekshirib DELETE qilardi.
    Yangi mantiq: hech qanday SELECT qilmasdan, db.tx() ichida to'g'ridan-to'g'ri
    is_solved=1 uchun UPDATE va is_solved=0 uchun DELETE bajaradi.
    Shu orqali parallel mark_solved so'rovi is_solved=1 qilgan taqdirda ham,
    yechilgan savol DELETE qilib yuborilmaydi.
    """
    executed_statements = []

    class DummyConn:
        def execute(self, stmt, params=None):
            executed_statements.append((str(stmt), params))

    class DummyTx:
        def __enter__(self):
            return DummyConn()
        def __exit__(self, exc_type, exc, tb):
            pass

    with patch.object(quiz, "_require_base", return_value={"id": 10, "full_name": "test_base"}):
        with patch.object(quiz.db, "fetch_one") as mock_fetch_one:
            with patch.object(quiz.db, "tx", return_value=DummyTx()):
                # set_flag('none') chaqiramiz
                res = quiz.set_flag(
                    user_request,
                    {"id": 42, "type": "none"},
                    "test_base",
                )

    # 1. quiz_progress bo'yicha SELECT chaqirilmagan bo'lishi shart
    mock_fetch_one.assert_not_called()

    # 2. Ikkita atomik SQL bayonoti bajarilgan bo'lishi kerak
    assert len(executed_statements) == 2
    update_sql, update_params = executed_statements[0]
    delete_sql, delete_params = executed_statements[1]

    # UPDATE faqat is_solved = 1 bo'lganda flag_type ni tozalaydi
    assert "UPDATE quiz_progress SET flag_type = ''" in update_sql
    assert "is_solved = 1" in update_sql
    assert update_params["q"] == 42
    assert update_params["b"] == 10

    # DELETE faqat is_solved = 0 bo'lganda qatorni o'chiradi (yechilgan savolga tegmaydi!)
    assert "DELETE FROM quiz_progress" in delete_sql
    assert "is_solved = 0" in delete_sql
    assert delete_params["q"] == 42
    assert delete_params["b"] == 10

    assert res.status_code == 200
    assert json.loads(res.body.decode("utf-8"))["success"] is True


def test_set_flag_with_flag_type_sets_flag(user_request):
    """Belgi qo'yilganda INSERT ... ON CONFLICT DO UPDATE SET flag_type chaqiriladi."""
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with patch.object(quiz, "_require_base", return_value={"id": 10, "full_name": "test_base"}):
        with patch.object(quiz.db, "execute", side_effect=fake_execute):
            res = quiz.set_flag(
                user_request,
                {"id": 42, "type": "yellow"},
                "test_base",
            )

    assert len(executed) == 1
    sql, params = executed[0]
    assert "INSERT INTO quiz_progress" in sql
    assert "DO UPDATE SET flag_type = EXCLUDED.flag_type" in sql
    assert params["ft"] == "yellow"
    assert params["q"] == 42
    assert res.status_code == 200
    assert json.loads(res.body.decode("utf-8"))["success"] is True
