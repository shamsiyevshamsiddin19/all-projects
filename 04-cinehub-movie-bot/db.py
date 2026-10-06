"""PostgreSQL qatlami — asyncpg pool va yordamchi funksiyalar."""
import asyncpg

import config

pool: asyncpg.Pool | None = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id     BIGINT PRIMARY KEY,
    first_name  TEXT,
    username    TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS movies (
    id          SERIAL PRIMARY KEY,
    code        INTEGER NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    group_name  TEXT,
    file_id     TEXT NOT NULL,
    views       INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_movies_group ON movies (group_name);
CREATE INDEX IF NOT EXISTS idx_movies_name  ON movies (lower(name));

CREATE TABLE IF NOT EXISTS series (
    id          SERIAL PRIMARY KEY,
    code        INTEGER NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    views       INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_series_name ON series (lower(name));

CREATE TABLE IF NOT EXISTS episodes (
    id             SERIAL PRIMARY KEY,
    series_id      INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    episode_number INTEGER NOT NULL,
    file_id        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes (series_id);

CREATE TABLE IF NOT EXISTS channels (
    id          SERIAL PRIMARY KEY,
    channel_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    link        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    id               INTEGER PRIMARY KEY,
    signature        TEXT,
    force_sub_status SMALLINT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS social_links (
    id          SERIAL PRIMARY KEY,
    platform    TEXT NOT NULL,
    url         TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);
"""


async def init(dsn: str | None = None):
    """Pool ochish va jadvallarni yaratish."""
    global pool
    pool = await asyncpg.create_pool(dsn or config.DATABASE_URL, min_size=1, max_size=10)
    async with pool.acquire() as con:
        await con.execute(SCHEMA)
        # Standart signature
        row = await con.fetchrow("SELECT id FROM settings WHERE id = 1")
        if not row:
            await con.execute(
                "INSERT INTO settings (id, signature, force_sub_status) VALUES (1, $1, 1)",
                "@" + config.BOT_USERNAME,
            )
    return pool


async def close():
    if pool:
        await pool.close()


# ---- Qisqa yordamchilar ----
async def fetch(query: str, *args):
    async with pool.acquire() as con:
        return await con.fetch(query, *args)


async def fetchrow(query: str, *args):
    async with pool.acquire() as con:
        return await con.fetchrow(query, *args)


async def fetchval(query: str, *args):
    async with pool.acquire() as con:
        return await con.fetchval(query, *args)


async def execute(query: str, *args):
    async with pool.acquire() as con:
        return await con.execute(query, *args)


# ---- Domen funksiyalari ----
async def register_user(chat_id: int, first_name: str = "", username: str = ""):
    await execute(
        """INSERT INTO users (chat_id, first_name, username, is_active)
           VALUES ($1, $2, $3, TRUE)
           ON CONFLICT (chat_id) DO UPDATE
             SET first_name = EXCLUDED.first_name,
                 username   = EXCLUDED.username,
                 is_active  = TRUE""",
        chat_id, first_name, username,
    )


async def get_signature() -> str:
    val = await fetchval("SELECT signature FROM settings WHERE id = 1")
    return val or ("@" + config.BOT_USERNAME)


async def get_force_sub() -> int:
    val = await fetchval("SELECT force_sub_status FROM settings WHERE id = 1")
    return int(val or 0)


async def get_last_code() -> int:
    m = await fetchval("SELECT COALESCE(MAX(code), 0) FROM movies")
    s = await fetchval("SELECT COALESCE(MAX(code), 0) FROM series")
    return max(int(m), int(s))


async def is_code_busy(code: int) -> bool:
    m = await fetchval("SELECT 1 FROM movies WHERE code = $1", code)
    s = await fetchval("SELECT 1 FROM series WHERE code = $1", code)
    return bool(m or s)
