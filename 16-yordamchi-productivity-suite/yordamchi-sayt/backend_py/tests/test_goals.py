"""Goals handler (A-10: toggle_goal atomik yangilash) testlari."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.errors import ApiError
from app.handlers import goals
from conftest import make_request


def test_toggle_goal_missing_id(user_request):
    with pytest.raises(ApiError) as exc:
        goals.toggle_goal(user_request, {})
    assert exc.value.message == "Maqsad ID kelmadi."


def test_toggle_goal_not_found(user_request):
    with patch.object(goals.db, "execute_returning", return_value=None):
        with pytest.raises(ApiError) as exc:
            goals.toggle_goal(user_request, {"id": 999})
        assert exc.value.status == 404
        assert exc.value.message == "Maqsad topilmadi."


def test_toggle_goal_atomic_update_executes_single_query(user_request):
    """A-10: Avvalgi SELECT-then-UPDATE o'rniga bitta atomik CTE so'rovi bajariladi."""
    captured = []

    def fake_execute_returning(sql, params=None):
        captured.append((sql, params))
        return {"completed": 1}

    with patch.object(goals.db, "fetch_one") as mock_fetch:
        with patch.object(goals.db, "execute_returning", side_effect=fake_execute_returning):
            res = goals.toggle_goal(user_request, {"id": 15})

    # 1. Alohida SELECT qilinmagan bo'lishi shart
    mock_fetch.assert_not_called()

    # 2. execute_returning ga bitta atomik CTE so'rovi borgan bo'lishi shart
    assert len(captured) == 1
    sql, params = captured[0]
    assert "WITH target AS" in sql
    assert "FOR UPDATE" in sql
    assert "1 - completed" in sql
    assert "lower(btrim(goals.text)) = target.target_text" in sql
    assert params["id"] == 15

    assert res.status_code == 200
    body = json.loads(res.body.decode("utf-8"))
    assert body["success"] is True
    assert body["completed"] == 1
