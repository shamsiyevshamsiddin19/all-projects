"""Baza qatlami — SQLAlchemy Core (prepared statements). PHP DB klassining o'rnini bosadi.

Bot o'z jadvallarini (users, plans, ...) yaratadi va sayt bilan bitta PostgreSQL bazani ulashadi.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import settings

logger = logging.getLogger("boostday")

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,
            future=True,
        )
    return _engine


def one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def all_(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_engine().connect() as conn:
        return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def value(sql: str, params: dict[str, Any] | None = None) -> Any:
    with get_engine().connect() as conn:
        return conn.execute(text(sql), params or {}).scalar()


def run(sql: str, params: dict[str, Any] | None = None) -> int:
    with get_engine().begin() as conn:
        return conn.execute(text(sql), params or {}).rowcount


def run_returning_id(sql: str, params: dict[str, Any] | None = None) -> int:
    # PostgreSQL'da `lastrowid` yo'q — `RETURNING id` bilan yangi id ni olamiz.
    with get_engine().begin() as conn:
        result = conn.execute(text(sql.rstrip().rstrip(";") + " RETURNING id"), params or {})
        return int(result.scalar() or 0)


def table_exists(table: str) -> bool:
    import re

    if not re.match(r"^[A-Za-z0-9_]+$", table):
        return False
    cnt = value(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = current_schema() AND table_name = :t",
        {"t": table},
    )
    return bool(cnt and int(cnt) > 0)


def table_columns(table: str) -> list[str]:
    if not table_exists(table):
        return []
    rows = all_(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = :t ORDER BY ordinal_position",
        {"t": table},
    )
    return [r["column_name"] for r in rows]


_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGSERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        first_name VARCHAR(191) DEFAULT NULL,
        username VARCHAR(191) DEFAULT NULL,
        birth_date DATE DEFAULT NULL,
        step VARCHAR(191) DEFAULT NULL,
        temp_data TEXT DEFAULT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_boostday_users_chat_id UNIQUE (chat_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_channels (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        channel_id VARCHAR(191) NOT NULL,
        channel_name VARCHAR(255) NOT NULL,
        channel_username VARCHAR(191) DEFAULT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_boostday_user_channel UNIQUE (user_id, channel_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_boostday_user_channels_user ON user_channels (user_id)",
    # ESKI ustun (bitta kanal = bitta mavzu) — endi `topics`ga almashtirildi.
    "ALTER TABLE user_channels ADD COLUMN IF NOT EXISTS topic VARCHAR(32) NOT NULL DEFAULT ''",
    # Vergul bilan ajratilgan mavzular ro'yxati — bitta kanal bir nechta mavzuga
    # tayinlanishi mumkin (masalan "sport,russian").
    "ALTER TABLE user_channels ADD COLUMN IF NOT EXISTS topics VARCHAR(191) NOT NULL DEFAULT ''",
    """
    CREATE TABLE IF NOT EXISTS plans (
        id BIGSERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL,
        channel_id VARCHAR(191) NOT NULL,
        channel_name VARCHAR(255) DEFAULT NULL,
        plan_type VARCHAR(64) NOT NULL,
        content_type VARCHAR(64) DEFAULT NULL,
        file_id VARCHAR(500) DEFAULT NULL,
        caption TEXT DEFAULT NULL,
        items TEXT DEFAULT NULL,
        time VARCHAR(16) DEFAULT NULL,
        date DATE DEFAULT NULL,
        start_date DATE DEFAULT NULL,
        end_date DATE DEFAULT NULL,
        last_run TIMESTAMP DEFAULT NULL,
        next_run_at TIMESTAMP DEFAULT NULL,
        message_id BIGINT DEFAULT NULL,
        report_sent SMALLINT NOT NULL DEFAULT 0,
        tasks TEXT DEFAULT NULL,
        week_mode VARCHAR(16) NOT NULL DEFAULT 'everyday',
        status VARCHAR(32) NOT NULL DEFAULT 'active',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_boostday_plans_owner ON plans (owner_id, status, plan_type)",
    "CREATE INDEX IF NOT EXISTS idx_boostday_plans_next_run ON plans (status, plan_type, next_run_at)",
    "CREATE INDEX IF NOT EXISTS idx_boostday_plans_channel ON plans (channel_id)",
    """
    CREATE TABLE IF NOT EXISTS history (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        year INT NOT NULL,
        month INT NOT NULL,
        day INT NOT NULL,
        total_tasks INT NOT NULL DEFAULT 0,
        completed_tasks INT NOT NULL DEFAULT 0,
        last_channel_id VARCHAR(191) DEFAULT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_boostday_history_day UNIQUE (user_id, year, month, day)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_boostday_history_user ON history (user_id, year, month, day)",
    """
    CREATE TABLE IF NOT EXISTS settings (
        id BIGSERIAL PRIMARY KEY,
        setting_key VARCHAR(191) NOT NULL,
        setting_value TEXT DEFAULT NULL,
        CONSTRAINT uq_boostday_settings_key UNIQUE (setting_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sent_logs (
        id BIGSERIAL PRIMARY KEY,
        plan_id BIGINT NOT NULL,
        sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        note VARCHAR(255) DEFAULT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_boostday_sent_logs_plan_note ON sent_logs (plan_id, note)",
    # Sayt (Yordamchisayt) bilan ulashiladigan faoliyat jurnali — shu yerda ham
    # yaratiladi, chunki bot sayt oldin ishga tushishi mumkin (bir xil jadval shakli).
    """
    CREATE TABLE IF NOT EXISTS activity_log (
        id BIGSERIAL PRIMARY KEY,
        owner_type VARCHAR(32) NOT NULL,
        owner_key VARCHAR(191) NOT NULL,
        section VARCHAR(32) NOT NULL,
        object_name VARCHAR(255) NOT NULL DEFAULT '',
        amount DECIMAL(10,2) DEFAULT NULL,
        unit VARCHAR(32) NOT NULL DEFAULT '',
        duration_seconds INT DEFAULT NULL,
        meta TEXT DEFAULT NULL,
        occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_activity_log_owner_date ON activity_log (owner_type, owner_key, occurred_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_activity_log_owner_section ON activity_log (owner_type, owner_key, section, occurred_at DESC)",

    # --- KUNLIK ODATLAR (habits) ---------------------------------------
    # Har kuni belgilangan VAQTDA takrorlanadigan shaxsiy ishlar
    # (masalan 22:00 yuz yuvish, 23:00 tish yuvish, juft kunlari cho'milish).
    # Bot bazasida turadi, chunki eslatmalarni ham, kunlik xabarni ham BOT
    # yuboradi; sayt ularni `/boost/api` proxysi orqali boshqaradi.
    """
    CREATE TABLE IF NOT EXISTS habits (
        id BIGSERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL,
        name VARCHAR(255) NOT NULL,
        at_time VARCHAR(5) NOT NULL DEFAULT '22:00',
        week_mode VARCHAR(16) NOT NULL DEFAULT 'everyday',
        remind VARCHAR(64) NOT NULL DEFAULT '60,30,15,5',
        note TEXT DEFAULT NULL,
        sort_order INT NOT NULL DEFAULT 0,
        is_active SMALLINT NOT NULL DEFAULT 1,
        is_deleted SMALLINT NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_habits_owner ON habits (owner_id, is_deleted, is_active)",

    # Bajarilgan belgisi. UNIQUE — bir kunda bir marta, qayta bosilsa o'chadi.
    """
    CREATE TABLE IF NOT EXISTS habit_log (
        id BIGSERIAL PRIMARY KEY,
        habit_id BIGINT NOT NULL,
        done_date DATE NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_habit_log UNIQUE (habit_id, done_date)
    )
    """,

    # --- WEB PUSH obunalari ------------------------------------------------
    # Telefondagi HAQIQIY bildirishnoma (Instagram/YouTube kabi) uchun.
    # Brauzer bergan `endpoint` + shifrlash kalitlari saqlanadi. Sayt ham,
    # bot ham shu jadvalga tayanadi (bitta PostgreSQL).
    """
    CREATE TABLE IF NOT EXISTS push_subs (
        id BIGSERIAL PRIMARY KEY,
        owner_id BIGINT NOT NULL DEFAULT 0,
        endpoint TEXT NOT NULL,
        p256dh VARCHAR(255) NOT NULL,
        auth VARCHAR(255) NOT NULL,
        ua VARCHAR(255) DEFAULT NULL,
        is_active SMALLINT NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_ok_at TIMESTAMP DEFAULT NULL,
        CONSTRAINT uq_push_endpoint UNIQUE (endpoint)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_push_subs_owner ON push_subs (owner_id, is_active)",

    # Yuborilgan eslatmalar — bir xil eslatma ikki marta ketmasligi uchun.
    # `offset_min` = 0 bo'lsa "vaqti bo'ldi" xabari.
    """
    CREATE TABLE IF NOT EXISTS habit_sent (
        id BIGSERIAL PRIMARY KEY,
        habit_id BIGINT NOT NULL,
        sent_date DATE NOT NULL,
        offset_min INT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_habit_sent UNIQUE (habit_id, sent_date, offset_min)
    )
    """,

    # Reja BO'LIMI eslatmalari (30/15/5/0 daqiqa qolganda).
    # Bo'lim ID si yo'q — u reja ichidagi JSON, shuning uchun kalit
    # `plan_id + bo'lim tartib raqami`. Bo'lim nomi o'zgarsa ham kalit
    # buzilmaydi (nom bo'yicha kalitlash tahrirdan keyin takror
    # yuborilishiga olib kelardi).
    """
    CREATE TABLE IF NOT EXISTS group_sent (
        id BIGSERIAL PRIMARY KEY,
        plan_id BIGINT NOT NULL,
        group_index INT NOT NULL,
        sent_date DATE NOT NULL,
        offset_min INT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT uq_group_sent UNIQUE (plan_id, group_index, sent_date, offset_min)
    )
    """,
]


def log_activity(section: str, object_name: str = "", amount=None, unit: str = "", meta: str | None = None) -> None:
    """Sayt bilan bir xil jurnalga yozadi (owner_type/owner_key sayt bilan mos: 'global'/'shared')."""
    run(
        "INSERT INTO activity_log (owner_type, owner_key, section, object_name, amount, unit, meta) "
        "VALUES ('global', 'shared', :sec, :obj, :amt, :unit, :meta)",
        {"sec": section, "obj": (object_name or "")[:255], "amt": amount, "unit": (unit or "")[:32], "meta": meta},
    )


def migrate() -> None:
    with get_engine().begin() as conn:
        for stmt in _SCHEMA:
            conn.execute(text(stmt))
    # week_mode ustuni eski bazada bo'lmasa qo'shamiz (PostgreSQL IF NOT EXISTS).
    if table_exists("plans") and "week_mode" not in table_columns("plans"):
        run("ALTER TABLE plans ADD COLUMN IF NOT EXISTS week_mode VARCHAR(16) NOT NULL DEFAULT 'everyday'")
    logger.info("Bot schema tekshirildi/yaratildi")
