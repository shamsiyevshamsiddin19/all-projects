"""Baza qatlami — SQLAlchemy Core orqali (prepared statement'lar bilan, SQL-injection'siz).

PHP versiyasida schema har API so'rovida `SHOW COLUMNS`/`ALTER TABLE` bilan tekshirilardi.
Bu versiyada schema faqat ishga tushishda bir marta yaratiladi (init_schema).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import settings

logger = logging.getLogger("yordamchi")

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
    return _engine


# --- Qulay so'rov yordamchilari ---------------------------------------------

def fetch_all(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(r) for r in rows]


def fetch_one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def fetch_value(sql: str, params: dict[str, Any] | None = None) -> Any:
    with get_engine().connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()


def execute(sql: str, params: dict[str, Any] | None = None) -> int:
    """Yozuv so'rovi. Ta'sirlangan qatorlar sonini qaytaradi."""
    with get_engine().begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount


def execute_returning_id(sql: str, params: dict[str, Any] | None = None) -> int:
    """INSERT so'rovi va yangi qatorning `id` sini qaytaradi.

    PostgreSQL'da `lastrowid` yo'q — shuning uchun `RETURNING id` qo'shamiz.
    """
    with get_engine().begin() as conn:
        result = conn.execute(text(sql.rstrip().rstrip(";") + " RETURNING id"), params or {})
        return int(result.scalar() or 0)


class tx:
    """Tranzaksiya konteksti: `with tx() as conn:` — bir nechta yozuvni atomik bajaradi.

    Ichida conn.execute(text(...), params) ishlating; xatoda avtomatik rollback.
    """

    def __enter__(self):
        self._conn = get_engine().begin()
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc, tb):
        return self._conn.__exit__(exc_type, exc, tb)


# --- Schema init (bir martalik) ---------------------------------------------

def _split_statements(sql: str) -> list[str]:
    """`;` bo'yicha ajratadi. Izohlar OLDIN olib tashlanadi.

    Nega shunday: ilgari avval `;` bo'yicha bo'linib, keyin izoh qatorlari
    filtrlanardi. Agar izoh ichida `;` bo'lsa (o'zbekcha matnda tabiiy),
    izoh qatori o'rtasidan kesilib, ikkinchi bo'lagi endi `--` bilan
    boshlanmasdi va SQL deb bajarilardi. Natijada butun schema init
    sintaksis xatosi bilan yiqilardi — ya'ni ALTER'lar qo'llanmay qolardi.
    """
    lines = []
    for ln in sql.splitlines():
        s = ln.strip()
        if s.startswith("--"):
            continue                       # butun qator izoh
        lines.append(ln)
    clean = "\n".join(lines)

    out: list[str] = []
    for raw in clean.split(";"):
        if raw.strip():
            out.append(raw.strip())
    return out


def init_schema() -> None:
    """Baza jadvallarini yaratadi (agar yo'q bo'lsa). Ishga tushishda bir marta chaqiriladi."""
    schema_path = _resolve_schema_path()
    if schema_path is None:
        logger.warning("schema.sql topilmadi — jadvallar yaratilmadi.")
        return

    sql = schema_path.read_text(encoding="utf-8")
    with get_engine().begin() as conn:
        for stmt in _split_statements(sql):
            conn.execute(text(stmt))
    logger.info("Schema tekshirildi/yaratildi: %s", schema_path)


def _resolve_schema_path() -> Path | None:
    candidates = [
        settings.APP_ROOT / "schema.sql",
        settings.APP_ROOT.parent / "database" / "schema.sql",
        settings.FRONTEND_ROOT / "database" / "schema.sql",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


# --- Owner kalitli app_storage yordamchilari --------------------------------

def storage_set(key: str, value: str | None, context: dict[str, str], conn=None) -> None:
    if value is not None:
        value = str(value)
        if len(value.encode("utf-8")) > settings.STORAGE_MAX_VALUE_BYTES:
            from .errors import ApiError

            raise ApiError("Saqlanayotgan qiymat juda katta.", 413)
    sql = """
        INSERT INTO app_storage (owner_type, owner_key, storage_key, storage_value)
        VALUES (:ot, :ok, :sk, :sv)
        ON CONFLICT (owner_type, owner_key, storage_key)
        DO UPDATE SET storage_value = EXCLUDED.storage_value, updated_at = CURRENT_TIMESTAMP
    """
    params = {
        "ot": context["owner_type"],
        "ok": context["owner_key"],
        "sk": str(key),
        "sv": None if value is None else str(value),
    }
    if conn is not None:
        conn.execute(text(sql), params)
    else:
        execute(sql, params)


def storage_delete(key: str, context: dict[str, str]) -> None:
    execute(
        "DELETE FROM app_storage WHERE owner_type = :ot AND owner_key = :ok AND storage_key = :sk",
        {"ot": context["owner_type"], "ok": context["owner_key"], "sk": str(key)},
    )


def storage_map(context: dict[str, str], prefix: str | None = None) -> dict[str, Any]:
    if prefix:
        rows = fetch_all(
            "SELECT storage_key, storage_value FROM app_storage "
            "WHERE owner_type = :ot AND owner_key = :ok AND storage_key LIKE :pfx ORDER BY storage_key",
            {"ot": context["owner_type"], "ok": context["owner_key"], "pfx": f"{prefix}%"},
        )
    else:
        rows = fetch_all(
            "SELECT storage_key, storage_value FROM app_storage "
            "WHERE owner_type = :ot AND owner_key = :ok ORDER BY storage_key",
            {"ot": context["owner_type"], "ok": context["owner_key"]},
        )
    return {r["storage_key"]: r["storage_value"] for r in rows}


def storage_value(key: str, default: Any, context: dict[str, str]) -> Any:
    val = fetch_value(
        "SELECT storage_value FROM app_storage "
        "WHERE owner_type = :ot AND owner_key = :ok AND storage_key = :sk LIMIT 1",
        {"ot": context["owner_type"], "ok": context["owner_key"], "sk": str(key)},
    )
    return default if val is None else val
