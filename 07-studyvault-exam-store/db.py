"""Ma'lumotlar bazasi qatlami (asyncpg, PostgreSQL).

PHP'dagi db_query/userStep/userTemp/getSettings... funksiyalarining toza,
async muqobillari. Hamma so'rov parametrlangan (SQL-injection xavfsiz).
"""
from __future__ import annotations

import json
import os
from typing import Any

import asyncpg

from config import settings

_pool: asyncpg.Pool | None = None


async def init(apply_schema: bool = True) -> None:
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    if apply_schema:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, encoding="utf-8") as f:
            await _pool.execute(f.read())


async def close() -> None:
    if _pool:
        await _pool.close()


def pool() -> asyncpg.Pool:
    assert _pool is not None, "db.init() chaqirilmagan"
    return _pool


# --------------------------------------------------------------- users (FSM)

async def ensure_user(chat_id: int) -> None:
    await pool().execute(
        "INSERT INTO users (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING",
        chat_id,
    )


async def touch_user(chat_id: int, username: str | None,
                     first_name: str | None, last_name: str | None) -> None:
    """Har bir interaktsiyada profil ma'lumotini yangilab boradi (NULL bilan o'chirmaydi)."""
    await pool().execute(
        """INSERT INTO users (chat_id, username, first_name, last_name)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (chat_id) DO UPDATE SET
             username   = COALESCE(EXCLUDED.username,   users.username),
             first_name = COALESCE(EXCLUDED.first_name, users.first_name),
             last_name  = COALESCE(EXCLUDED.last_name,  users.last_name)""",
        chat_id, username, first_name, last_name,
    )


async def set_phone(chat_id: int, phone: str) -> None:
    await pool().execute(
        """INSERT INTO users (chat_id, phone) VALUES ($1, $2)
           ON CONFLICT (chat_id) DO UPDATE SET phone = EXCLUDED.phone""",
        chat_id, phone,
    )


async def get_step(chat_id: int) -> str:
    row = await pool().fetchrow("SELECT step FROM users WHERE chat_id = $1", chat_id)
    return row["step"] if row else "none"


async def set_step(chat_id: int, step: str) -> None:
    await pool().execute(
        """INSERT INTO users (chat_id, step) VALUES ($1, $2)
           ON CONFLICT (chat_id) DO UPDATE SET step = EXCLUDED.step""",
        chat_id, step,
    )


async def get_temp(chat_id: int, key: str) -> Any:
    row = await pool().fetchrow("SELECT temp_data FROM users WHERE chat_id = $1", chat_id)
    if not row or row["temp_data"] is None:
        return None
    data = row["temp_data"]
    if isinstance(data, str):
        data = json.loads(data)
    return data.get(key)


async def set_temp(chat_id: int, key: str, value: Any) -> None:
    """value=None bo'lsa kalitni o'chiradi."""
    await ensure_user(chat_id)
    async with pool().acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT temp_data FROM users WHERE chat_id = $1 FOR UPDATE", chat_id
            )
            data = row["temp_data"] if row else {}
            if isinstance(data, str):
                data = json.loads(data or "{}")
            data = dict(data or {})
            if value is None:
                data.pop(key, None)
            else:
                data[key] = value
            await conn.execute(
                "UPDATE users SET temp_data = $2 WHERE chat_id = $1",
                chat_id, json.dumps(data, ensure_ascii=False),
            )


async def all_user_ids() -> list[int]:
    rows = await pool().fetch("SELECT chat_id FROM users")
    return [r["chat_id"] for r in rows]


async def count_users() -> int:
    return await pool().fetchval("SELECT COUNT(*) FROM users")


# --------------------------------------------------------------- settings

async def _get_setting(key: str, default: Any) -> Any:
    row = await pool().fetchrow("SELECT value_content FROM settings WHERE key_name = $1", key)
    if not row:
        return default
    val = row["value_content"]
    if isinstance(val, str):
        val = json.loads(val)
    return val if val is not None else default


async def _save_setting(key: str, value: Any) -> None:
    await pool().execute(
        """INSERT INTO settings (key_name, value_content) VALUES ($1, $2)
           ON CONFLICT (key_name) DO UPDATE SET value_content = EXCLUDED.value_content""",
        key, json.dumps(value, ensure_ascii=False),
    )


async def get_settings() -> dict:
    return await _get_setting("config", {})


async def save_settings(data: dict) -> None:
    await _save_setting("config", data)


async def get_base_price() -> int:
    """Joriy baza narxi — admin paneldan sozlanadi (settings.config['base_price']),
    o'rnatilmagan bo'lsa .env BASE_PRICE."""
    try:
        v = int((await get_settings()).get("base_price") or 0)
        return v if v > 0 else settings.base_price
    except (ValueError, TypeError):
        return settings.base_price


async def set_base_price(price: int) -> None:
    s = await get_settings()
    s["base_price"] = int(price)
    await save_settings(s)


async def get_global_tag() -> str:
    return (await get_settings()).get("global_tag", "")


async def set_global_tag(tag: str) -> None:
    s = await get_settings()
    s["global_tag"] = tag
    await save_settings(s)


async def get_stats() -> dict:
    return await _get_setting("stats", {"sales": 0, "revenue": 0})


async def increment_stats(amount: int) -> None:
    s = await get_stats()
    s["sales"] = int(s.get("sales", 0)) + 1
    s["revenue"] = int(s.get("revenue", 0)) + int(amount)
    await _save_setting("stats", s)


# --------------------------------------------------------------- products

async def product_by_code(code: str) -> asyncpg.Record | None:
    return await pool().fetchrow("SELECT * FROM products WHERE code = $1", code)


async def all_products() -> list[asyncpg.Record]:
    return await pool().fetch("SELECT * FROM products ORDER BY id")


async def product_subjects(course: str) -> list[str]:
    rows = await pool().fetch(
        "SELECT DISTINCT subject FROM products WHERE course = $1 ORDER BY subject", course
    )
    return [r["subject"] for r in rows]


async def products_by(course: str, subject: str) -> list[asyncpg.Record]:
    return await pool().fetch(
        "SELECT * FROM products WHERE course = $1 AND subject = $2 ORDER BY id",
        course, subject,
    )


async def all_product_names() -> list[str]:
    rows = await pool().fetch("SELECT name FROM products ORDER BY id")
    return [r["name"] for r in rows]


async def add_product(code: str, name: str, course: str, subject: str,
                      description: str, file_id: str) -> None:
    await pool().execute(
        """INSERT INTO products (code, name, course, subject, description, file_id)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        code, name, course, subject, description, file_id,
    )


async def delete_product_by_name(name: str) -> None:
    await pool().execute("DELETE FROM products WHERE name = $1", name)


async def delete_product(code: str) -> None:
    await pool().execute("DELETE FROM products WHERE code = $1", code)


async def update_product(orig_code: str, code: str, name: str, course: str,
                         subject: str, description: str, file_id: str) -> None:
    await pool().execute(
        """UPDATE products SET code=$2, name=$3, course=$4, subject=$5,
           description=$6, file_id=$7 WHERE code=$1""",
        orig_code, code, name, course, subject, description, file_id,
    )


async def count_products() -> int:
    return await pool().fetchval("SELECT COUNT(*) FROM products")


# --------------------------------------------------------------- payments

async def create_baza_payment(chat_id: int, hwid: str, base_num: str, amount: int) -> int:
    """Eski 'created'/'pending' to'lovlarni 'replaced' qiladi, yangi 'created' yaratadi."""
    async with pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """UPDATE payments SET status = 'replaced'
                   WHERE chat_id = $1 AND hwid = $2 AND base_num = $3
                   AND status IN ('created', 'pending')""",
                chat_id, hwid, base_num,
            )
            return await conn.fetchval(
                """INSERT INTO payments (chat_id, hwid, base_num, amount, status)
                   VALUES ($1, $2, $3, $4, 'created') RETURNING id""",
                chat_id, hwid, base_num, amount,
            )


async def payment_by_id(payment_id: int) -> asyncpg.Record | None:
    return await pool().fetchrow("SELECT * FROM payments WHERE id = $1", payment_id)


async def amount_exists(amount: int) -> bool:
    return bool(await pool().fetchrow("SELECT 1 FROM payments WHERE amount = $1", amount))


# --------------------------------------------------------------- referrals

async def referral_seconds_since_join(chat_id: int) -> float | None:
    val = await pool().fetchval(
        "SELECT EXTRACT(EPOCH FROM (now() - created_at)) FROM users WHERE chat_id = $1",
        chat_id,
    )
    return float(val) if val is not None else None


async def add_referral(referrer_id: int, invited_id: int) -> bool:
    """Yangi referal qo'shadi. True = qo'shildi (dublikat bo'lmasa)."""
    await ensure_user(referrer_id)
    await ensure_user(invited_id)
    result = await pool().execute(
        """INSERT INTO referrals (referrer_id, invited_id) VALUES ($1, $2)
           ON CONFLICT (referrer_id, invited_id) DO NOTHING""",
        referrer_id, invited_id,
    )
    return result.endswith("1")


async def referral_count(referrer_id: int) -> int:
    return await pool().fetchval(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = $1", referrer_id
    )


async def referral_leaderboard() -> list[asyncpg.Record]:
    return await pool().fetch(
        """SELECT referrer_id, COUNT(*) AS total FROM referrals
           GROUP BY referrer_id ORDER BY total DESC"""
    )
