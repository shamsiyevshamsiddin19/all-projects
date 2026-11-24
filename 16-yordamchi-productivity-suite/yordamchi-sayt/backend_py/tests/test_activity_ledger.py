"""Activity log (A-05: Append-only ledger va compensating entries) testlari."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.errors import ApiError
from app.handlers import activity, sport
from conftest import make_request


def test_unlog_activity_missing_fields(user_request):
    with pytest.raises(ApiError) as exc:
        activity.unlog_activity(user_request, {"section": "sport"})
    assert exc.value.message == "Nomi berilmadi."

    with pytest.raises(ApiError) as exc:
        activity.unlog_activity(user_request, {"section": "invalid_sec", "object": "Test"})
    assert exc.value.message == "Noma'lum bo'lim."


def test_unlog_activity_inserts_compensating_entry_without_delete(user_request):
    """A-05: unlog_activity hard DELETE qilmasligi, o'rniga unit='undo' INSERT qilishi shart."""
    executed = []

    def fake_execute(sql, params=None):
        executed.append((sql, params))
        return 1

    with patch.object(activity.db, "execute", side_effect=fake_execute):
        res = activity.unlog_activity(user_request, {"section": "sport", "object": "Turnik"})

    assert len(executed) == 1
    sql, params = executed[0]

    # Hech qanday DELETE bo'lmasligi shart!
    assert "DELETE FROM activity_log" not in sql
    # Append-only INSERT bo'lishi shart
    assert "INSERT INTO activity_log" in sql
    assert params["sec"] == "sport"
    assert params["obj"] == "Turnik"
    assert params["unit"] == "undo"
    assert json.loads(params["meta"]) == {"undo": True}

    assert res.status_code == 200
    body = json.loads(res.body.decode("utf-8"))
    assert body["success"] is True
    assert body["removed"] == 1


def test_get_activity_log_filters_undos_at_sql_level(user_request):
    """A-05: get_activity_log SQL so'rovi undos CTE orqali juftlangan undo'larni filtrlaydi."""
    captured = []

    def fake_fetch_all(sql, params=None):
        captured.append((sql, params))
        return []

    with patch.object(activity.db, "fetch_all", side_effect=fake_fetch_all):
        res = activity.get_activity_log(user_request, {}, date_from="2026-11-01", date_to="2026-11-24", section="sport")

    assert len(captured) == 1
    sql, params = captured[0]

    assert "WITH undos AS" in sql
    assert "ranked_positives AS" in sql
    assert "unit = 'undo'" in sql
    assert "unit != 'undo'" in sql
    assert "rp.rn > COALESCE(u.undo_count, 0)" in sql


def test_sport_today_boost_done_sql_filters_undos():
    """A-05: sport._today_boost_done HAVING orqali undos chiqarilganini tekshiradi."""
    captured = []

    def fake_fetch_all(sql, params=None):
        captured.append((sql, params))
        return [{"name": "Turnik"}]

    with patch.object(sport.db, "fetch_all", side_effect=fake_fetch_all):
        names = sport._today_boost_done({"owner_type": "user", "owner_key": "test@example.com"})

    assert len(captured) == 1
    sql, params = captured[0]
    assert "GROUP BY e.name" in sql
    assert "HAVING COUNT(*) FILTER (WHERE a.unit != 'undo') > COUNT(*) FILTER (WHERE a.unit = 'undo')" in sql
    assert names == ["Turnik"]
