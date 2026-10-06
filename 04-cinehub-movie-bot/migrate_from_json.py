"""export.php chiqargan JSON'ni PostgreSQL'ga import qiladi.

Ishlatish:
    python migrate_from_json.py kino_export.json

Bir necha marta ishga tushirsa bo'ladi (kodlar takrorlanmaydi)."""
import asyncio
import json
import sys

import db


def _int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


async def migrate(path: str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    tables = data.get("tables", data)  # {"tables": {...}} yoki to'g'ridan-to'g'ri

    await db.init()
    con = db.pool

    async with con.acquire() as c:
        # users
        us = tables.get("users", [])
        for u in us:
            await c.execute(
                "INSERT INTO users (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING",
                _int(u["chat_id"]),
            )
        print(f"✅ users: {len(us)}")

        # movies
        ms = tables.get("movies", [])
        for m in ms:
            await c.execute(
                "INSERT INTO movies (code, name, group_name, file_id, views) "
                "VALUES ($1,$2,$3,$4,$5) ON CONFLICT (code) DO NOTHING",
                _int(m["code"]), m["name"], m.get("group_name"), m["file_id"], _int(m.get("views")),
            )
        print(f"✅ movies: {len(ms)}")

        # series (eski id -> yangi id)
        id_map = {}
        ss = tables.get("series", [])
        for s in ss:
            new_id = await c.fetchval(
                "INSERT INTO series (code, name, views) VALUES ($1,$2,$3) "
                "ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                _int(s["code"]), s["name"], _int(s.get("views")),
            )
            id_map[_int(s["id"])] = new_id
        print(f"✅ series: {len(ss)}")

        # episodes
        es = tables.get("episodes", [])
        cnt = 0
        for e in es:
            sid = id_map.get(_int(e["series_id"]))
            if not sid:
                continue
            await c.execute(
                "INSERT INTO episodes (series_id, episode_number, file_id) VALUES ($1,$2,$3)",
                sid, _int(e["episode_number"]), e["file_id"],
            )
            cnt += 1
        print(f"✅ episodes: {cnt}")

        # channels
        cs = tables.get("channels", [])
        for ch in cs:
            await c.execute(
                "INSERT INTO channels (channel_id, title, link) VALUES ($1,$2,$3)",
                str(ch["channel_id"]), ch["title"], ch["link"],
            )
        print(f"✅ channels: {len(cs)}")

        # social_links
        sl = tables.get("social_links", [])
        for s in sl:
            await c.execute(
                "INSERT INTO social_links (platform, url) VALUES ($1,$2)", s["platform"], s["url"]
            )
        print(f"✅ social_links: {len(sl)}")

        # settings
        st = tables.get("settings", [])
        for s in st:
            await c.execute(
                "INSERT INTO settings (id, signature, force_sub_status) VALUES (1,$1,$2) "
                "ON CONFLICT (id) DO UPDATE SET signature=EXCLUDED.signature, "
                "force_sub_status=EXCLUDED.force_sub_status",
                s.get("signature"), _int(s.get("force_sub_status"), 1),
            )
        print(f"✅ settings: {len(st)}")

    await db.close()
    print("\n🎉 Import tugadi!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ishlatish: python migrate_from_json.py kino_export.json")
        sys.exit(1)
    asyncio.run(migrate(sys.argv[1]))
