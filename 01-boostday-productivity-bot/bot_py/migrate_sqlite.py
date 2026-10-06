#!/usr/bin/env python3
"""Eski SQLite bazasini PostgreSQL ga ko'chiradi.

  python migrate_sqlite.py [/path/to/database.sqlite]

Standart yo'l: ../database.sqlite (Boostdaybot papkasidagi).
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from app import db  # noqa: E402

TABLES = {
    "users": {"date": ["birth_date"], "datetime": ["created_at", "updated_at"]},
    "user_channels": {"datetime": ["created_at"]},
    "plans": {"date": ["date", "start_date", "end_date"],
              "datetime": ["last_run", "next_run_at", "created_at", "updated_at"]},
    "history": {"datetime": ["created_at", "updated_at"]},
    "settings": {},
    "sent_logs": {"datetime": ["sent_at"]},
}


def sqlite_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,))
    return cur.fetchone() is not None


def normalize(column: str, value, rules: dict):
    if value == "":
        if column in rules.get("date", []) or column in rules.get("datetime", []):
            return None
    return value


def migrate_table(sconn: sqlite3.Connection, table: str, rules: dict) -> int:
    if not sqlite_table_exists(sconn, table) or not db.table_exists(table):
        return 0

    dest_columns = db.table_columns(table)
    sconn.row_factory = sqlite3.Row
    rows = sconn.execute(f'SELECT * FROM "{table}"').fetchall()
    count = 0

    with db.get_engine().begin() as mconn:
        for row in rows:
            row_keys = row.keys()
            data = {c: normalize(c, row[c], rules) for c in dest_columns if c in row_keys}
            if not data:
                continue
            cols = list(data.keys())
            placeholders = ", ".join(f":{c}" for c in cols)
            # PostgreSQL upsert: id (PK) bo'yicha to'qnashsa yangilaymiz (qayta yugurtirsa bo'ladi).
            updates = [f'"{c}" = EXCLUDED."{c}"' for c in cols if c != "id"]
            conflict = (f"ON CONFLICT (id) DO UPDATE SET {', '.join(updates)}"
                        if updates else "ON CONFLICT (id) DO NOTHING")
            sql = (f'INSERT INTO "{table}" ({", ".join(chr(34) + c + chr(34) for c in cols)}) '
                   f"VALUES ({placeholders}) {conflict}")
            mconn.execute(text(sql), data)
            count += 1

    # BIGSERIAL ketma-ketligini eng katta id dan keyinga surib qo'yamiz.
    max_id = db.value(f'SELECT COALESCE(MAX(id), 0) FROM "{table}"')
    if max_id and int(max_id) > 0:
        db.run(
            "SELECT setval(pg_get_serial_sequence(:tbl, 'id'), :val, true)",
            {"tbl": table, "val": int(max_id)},
        )
    return count


def main() -> None:
    legacy = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent.parent / "database.sqlite")
    if not Path(legacy).is_file():
        print("Legacy SQLite fayl topilmadi:", legacy)
        return

    db.migrate()
    sconn = sqlite3.connect(legacy)
    try:
        for table, rules in TABLES.items():
            print(f"{table}: {migrate_table(sconn, table, rules)}")
    finally:
        sconn.close()
    print("Migratsiya tugadi.")


if __name__ == "__main__":
    main()
