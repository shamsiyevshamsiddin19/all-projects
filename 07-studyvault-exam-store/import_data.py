"""baza_export.json (MySQL eksport) -> PostgreSQL import. Idempotent.

Foydalanish:  python import_data.py baza_export.json "postgresql://..."
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime

import asyncpg


def _dt(v):
    if not v or str(v).startswith("0000-00-00"):
        return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:26], fmt)
        except ValueError:
            continue
    return None


def _jsonb(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, str):
        try:
            return json.dumps(json.loads(v) if v.strip() else {}, ensure_ascii=False)
        except Exception:
            return "{}"
    return "{}"


async def main(path: str, dsn: str) -> None:
    data = json.load(open(path, encoding="utf-8"))
    conn = await asyncpg.connect(dsn)

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    await conn.execute(open(schema_path, encoding="utf-8").read())

    ok = {t: 0 for t in ("products", "users", "settings", "payments", "referrals")}
    err = {t: 0 for t in ok}

    for r in data.get("products", []):
        try:
            await conn.execute(
                """INSERT INTO products (code,name,course,subject,description,file_id,created_at)
                   VALUES ($1,$2,$3,$4,$5,$6,COALESCE($7,now()))
                   ON CONFLICT (code) DO UPDATE SET name=EXCLUDED.name, course=EXCLUDED.course,
                   subject=EXCLUDED.subject, description=EXCLUDED.description, file_id=EXCLUDED.file_id""",
                str(r.get("code") or ""), r.get("name") or "", r.get("course") or "",
                r.get("subject") or "", r.get("description") or "", r.get("file_id") or "",
                _dt(r.get("created_at")))
            ok["products"] += 1
        except Exception as e:
            err["products"] += 1
            print("product xato:", r.get("code"), e)

    for r in data.get("users", []):
        try:
            await conn.execute(
                """INSERT INTO users (chat_id,step,temp_data,created_at)
                   VALUES ($1,$2,$3::jsonb,COALESCE($4,now()))
                   ON CONFLICT (chat_id) DO UPDATE SET step=EXCLUDED.step, temp_data=EXCLUDED.temp_data""",
                int(r["chat_id"]), r.get("step") or "none", _jsonb(r.get("temp_data")),
                _dt(r.get("created_at")))
            ok["users"] += 1
        except Exception as e:
            err["users"] += 1

    for r in data.get("settings", []):
        try:
            await conn.execute(
                """INSERT INTO settings (key_name,value_content) VALUES ($1,$2::jsonb)
                   ON CONFLICT (key_name) DO UPDATE SET value_content=EXCLUDED.value_content""",
                r["key_name"], _jsonb(r.get("value_content")))
            ok["settings"] += 1
        except Exception as e:
            err["settings"] += 1
            print("setting xato:", r.get("key_name"), e)

    for r in data.get("payments", []):
        try:
            cti = (r.get("click_trans_id") or "").strip() or None
            await conn.execute(
                """INSERT INTO payments (id,chat_id,hwid,base_num,amount,status,click_trans_id,created_at,paid_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,COALESCE($8,now()),$9) ON CONFLICT (id) DO NOTHING""",
                int(r["id"]), int(r.get("chat_id") or 0), r.get("hwid") or "", r.get("base_num") or "",
                int(float(r.get("amount") or 0)), r.get("status") or "created", cti,
                _dt(r.get("created_at")), _dt(r.get("paid_at")))
            ok["payments"] += 1
        except Exception as e:
            err["payments"] += 1
            print("payment xato:", r.get("id"), e)

    for r in data.get("referrals", []):
        try:
            await conn.execute(
                """INSERT INTO referrals (referrer_id,invited_id,created_at)
                   VALUES ($1,$2,COALESCE($3,now())) ON CONFLICT (referrer_id,invited_id) DO NOTHING""",
                int(r["referrer_id"]), int(r["invited_id"]), _dt(r.get("created_at")))
            ok["referrals"] += 1
        except Exception as e:
            err["referrals"] += 1

    # serial ketma-ketliklarni tiklash
    for t in ("payments", "products"):
        await conn.execute(
            f"SELECT setval(pg_get_serial_sequence('{t}','id'), "
            f"GREATEST((SELECT COALESCE(MAX(id),1) FROM {t}),1))")

    print("\n=== IMPORT NATIJASI ===")
    for t in ok:
        c = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: bazada {c} | import ok={ok[t]} err={err[t]}")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
