"""Eski MySQL bazasidan yangi PostgreSQL bazasiga ma'lumotlarni ko'chirish.

Ishlatish:
    pip install pymysql asyncpg
    # MySQL ma'lumotlarini .env yoki muhit o'zgaruvchilarida bering:
    #   MYSQL_HOST, MYSQL_USER, MYSQL_PASS, MYSQL_DB
    # PostgreSQL uchun asosiy .env (DATABASE_URL) ishlatiladi.
    python migrate_mysql_to_pg.py

Bir necha marta ishga tushirsa bo'ladi: mavjud kodlar o'tkazib yuboriladi
(ON CONFLICT DO NOTHING)."""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

import config
import db

load_dotenv()

try:
    import pymysql
except ImportError:
    raise SystemExit("Avval o'rnating:  pip install pymysql")


def mysql_conn():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASS", ""),
        database=os.getenv("MYSQL_DB", ""),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


async def migrate():
    await db.init()
    my = mysql_conn()
    pg: asyncpg.Pool = db.pool

    def rows(table):
        with my.cursor() as cur:
            try:
                cur.execute(f"SELECT * FROM {table}")
                return cur.fetchall()
            except Exception as e:
                print(f"  ⚠️  {table}: {e}")
                return []

    async with pg.acquire() as con:
        # users
        us = rows("users")
        for u in us:
            await con.execute(
                "INSERT INTO users (chat_id, created_at) VALUES ($1, COALESCE($2, now())) "
                "ON CONFLICT (chat_id) DO NOTHING",
                int(u["chat_id"]), u.get("created_at"),
            )
        print(f"✅ users: {len(us)}")

        # movies
        ms = rows("movies")
        for m in ms:
            await con.execute(
                "INSERT INTO movies (code, name, group_name, file_id, views) "
                "VALUES ($1,$2,$3,$4,$5) ON CONFLICT (code) DO NOTHING",
                int(m["code"]), m["name"], m.get("group_name"), m["file_id"], int(m.get("views") or 0),
            )
        print(f"✅ movies: {len(ms)}")

        # series — eski id -> yangi id moslashuvi
        id_map = {}
        ss = rows("series")
        for s in ss:
            new_id = await con.fetchval(
                "INSERT INTO series (code, name, views) VALUES ($1,$2,$3) "
                "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                int(s["code"]), s["name"], int(s.get("views") or 0),
            )
            id_map[int(s["id"])] = new_id
        print(f"✅ series: {len(ss)}")

        # episodes — series_id ni yangi id ga o'giramiz
        es = rows("episodes")
        cnt = 0
        for e in es:
            new_sid = id_map.get(int(e["series_id"]))
            if not new_sid:
                continue
            await con.execute(
                "INSERT INTO episodes (series_id, episode_number, file_id) VALUES ($1,$2,$3)",
                new_sid, int(e["episode_number"]), e["file_id"],
            )
            cnt += 1
        print(f"✅ episodes: {cnt}")

        # channels
        cs = rows("channels")
        for c in cs:
            await con.execute(
                "INSERT INTO channels (channel_id, title, link) VALUES ($1,$2,$3)",
                str(c["channel_id"]), c["title"], c["link"],
            )
        print(f"✅ channels: {len(cs)}")

        # social_links
        sl = rows("social_links")
        for s in sl:
            await con.execute(
                "INSERT INTO social_links (platform, url) VALUES ($1,$2)", s["platform"], s["url"]
            )
        print(f"✅ social_links: {len(sl)}")

        # settings
        st = rows("settings")
        for s in st:
            await con.execute(
                "INSERT INTO settings (id, signature, force_sub_status) VALUES (1,$1,$2) "
                "ON CONFLICT (id) DO UPDATE SET signature=EXCLUDED.signature, "
                "force_sub_status=EXCLUDED.force_sub_status",
                s.get("signature"), int(s.get("force_sub_status") or 1),
            )
        print(f"✅ settings: {len(st)}")

    my.close()
    await db.close()
    print("\n🎉 Ko'chirish tugadi!")


if __name__ == "__main__":
    asyncio.run(migrate())
